"""CC-509 / CC-024: one attributed quote per symbol/minute, shared by replies and charts.

CC-024 (pre-15-Dec FREE unpause cutover): ALL Yahoo Finance scrapers and unguarded
CNBC scrapers for XAUUSD/US2Y/US10Y/DXY are retired.
- Core 7 markets (US500, XAUUSD, EURUSD, USDJPY, USOIL, BTCUSD, USTEC) plus DXY and
  BRENT (UKOIL) resolve from local held SQLite bars (bars.sqlite3, read-only WAL-safe
  immutable URI), deduplicating M15 NATIVE_BROKER rows by open_epoch and excluding
  invalid_bars; DXY and BRENT fail closed when stale (Option C, default-off
  allow_cnbc_dxy_fallback=False).
- US2Y and US10Y resolve from public-domain U.S. Department of the Treasury daily yield
  curve observations (observations.sqlite3 direct_rates, fallback bars.sqlite3
  history_points US_TREASURY:BC_2YEAR / BC_10YEAR) with US business-day freshness.
- Only individual attributed facts may leave this runtime cache (host rule 7).
"""
from __future__ import annotations

from contextlib import contextmanager
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import shutil
import sqlite3
import tempfile
from time import perf_counter
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen
from uuid import uuid4
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")
ROOT = Path(r"A:\Capital Chronicle\Runtime\ContentOps\references\public-quotes-v1")
INTAKE = Path(r"A:\Capital Chronicle\Runtime\OfficialRates\cc-078-20261101\state\intake")
BARS_DB = INTAKE / "completed-bars" / "bars.sqlite3"
RATES_DB = INTAKE / "rates-implied" / "observations.sqlite3"
CASH_CALENDAR = Path(
    r"A:\Capital Chronicle\main-jim-research-dashboard-20261025\config\ibkr_paper\us_session_calendar_v1.json"
)
MIN_INTERVAL = 60
TIMEOUT = 5
# Routing market, provider, local source symbol, reader label, unit, instrument_type.
SYMBOLS = {
    "US500": ("LOCAL_BARS", "US500", "S&P 500 index proxy", "points", "INDEX"),
    "XAUUSD": ("LOCAL_BARS", "XAUUSD", "Gold spot proxy", "USD per troy ounce", "COMMODITY"),
    "EURUSD": ("LOCAL_BARS", "EURUSD", "EUR/USD spot", "USD per EUR", "CURRENCY"),
    "USDJPY": ("LOCAL_BARS", "USDJPY", "USD/JPY spot", "JPY per USD", "CURRENCY"),
    "USOIL": ("LOCAL_BARS", "USOIL", "WTI crude oil proxy", "USD per barrel", "COMMODITY"),
    "BTCUSD": ("LOCAL_BARS", "BTCUSD", "Bitcoin spot", "USD", "CRYPTOCURRENCY"),
    "USTEC": ("LOCAL_BARS", "USTEC", "Nasdaq 100 index proxy", "points", "INDEX"),
    "DXY": ("LOCAL_BARS", "DXY", "US dollar index proxy", "points", "INDEX"),
    "US2Y": ("LOCAL_OFFICIAL_RATES", "US2Y", "US 2-year Treasury yield", "percent", "BOND"),
    "US10Y": ("LOCAL_OFFICIAL_RATES", "US10Y", "US 10-year Treasury yield", "percent", "BOND"),
    "BRENT": ("LOCAL_BARS", "UKOIL", "Brent crude oil proxy", "USD per barrel", "COMMODITY"),
}
ALIASES = {"SPX": "US500", "WTI": "USOIL", "NDX": "USTEC", "UKOIL": "BRENT"}
# Observations frozen before CC-788 / CC-024 keep their immutable readback identities.
LEGACY_MARKETS = {"USTEC": {"NDX"}, "BRENT": {"UKOIL"}}
HISTORICAL_SOURCE_SYMBOLS = {
    "USTEC": frozenset({"^NDX"}),
    "US500": frozenset({"^GSPC"}),
    "BRENT": frozenset({"BZ=F"}),
}
RETIRED_FUTURES_PROXIES = frozenset({"US500_FUTURES", "GOLD_FUTURES", "USTEC_FUTURES"})
CASH_INDEX_CLOSE_SETTLE_SECONDS = 5400
US_TREASURY_MAX_TRADING_DAYS = 2
_SAFE_FAILURE_DETAIL_KEYS = ("requested_symbol", "returned_symbol", "returned_type", "age_seconds", "observed_at_utc")
_LOCAL_BAR_ATTRIBUTION = "Held market data"
_TREASURY_ATTRIBUTION = "U.S. Department of the Treasury"
_OFFICIAL_RATE_HOSTS = ("treasury.gov", "newyorkfed.org", "ecb.europa.eu", "mof.go.jp", "boj.or.jp")
_D1_SERIES_PRIORITY = ("DESK_ODDS:EXNESS_BROKER_D1", "NATIVE_DAILY_ROUTE")


class QuoteError(ValueError):
    def __init__(self, cause, **details):
        super().__init__(cause)
        self.details = details


def utc(value):
    at = value if isinstance(value, datetime) else datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if at.tzinfo is None:
        raise QuoteError("PUBLIC_QUOTE_OBSERVATION_CLOCK_INVALID")
    return at.astimezone(timezone.utc)


def utcnow():
    return datetime.now(timezone.utc)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + "." + uuid4().hex + ".tmp")
    try:
        temp.write_bytes(canonical(value))
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def freeze(observation, *, root=None):
    """An issued fact binds immutable bytes, not a mutable latest-price pointer."""
    root = Path(root or ROOT)
    raw = canonical(observation)
    digest = sha256(raw).hexdigest()
    path = root / "observations" / (digest + ".json")
    if not path.is_file():
        save(path, observation)
    return {**observation, "observation_path": str(path.resolve()), "observation_sha256": digest}


def resolve(path, digest):
    raw = Path(path).read_bytes()
    if sha256(raw).hexdigest() != digest:
        raise QuoteError("PUBLIC_QUOTE_BINDING_CHANGED")
    return json.loads(raw)


@contextmanager
def _open_readonly_sqlite(path: Path, *, timeout: float = 5.0, zero_write: bool = False):
    """WAL-aware read-only SQLite connection.

    - When ``-wal`` is absent or 0 bytes: opens directly with ``?mode=ro&immutable=1``
      so SQLite never creates or mutates ``-wal``/``-shm`` sidecars on an idle/checkpointed
      ``journal_mode=WAL`` DB.
    - When ``-wal`` has active uncheckpointed frames (``wal_bytes > 0``):
      - ``zero_write=True`` copies ``(db, -wal, -shm)`` to a private scratch temp dir
        and opens the copy read-only so audits see 100% of live uncheckpointed WAL rows
        with 0-byte / 0-mtime mutation on the source directory.
      - ``zero_write=False`` (live production fast path) opens directly with ``?mode=ro``
        + ``PRAGMA query_only = ON`` + ``PRAGMA busy_timeout`` so live readers see 100%
        of fresh uncheckpointed ``-wal`` bars immediately without copying a 1.1 GB DB.
    Always closes the connection deterministically in ``finally:``.
    """
    resolved = Path(path).resolve()
    if not resolved.is_file():
        raise FileNotFoundError(str(resolved))
    wal = resolved.with_name(resolved.name + "-wal")
    wal_bytes = wal.stat().st_size if wal.is_file() else 0
    wait_sec = max(0.0, float(timeout))
    busy_ms = int(wait_sec * 1000)

    if wal_bytes == 0:
        con = sqlite3.connect(resolved.as_uri() + "?mode=ro&immutable=1", uri=True, timeout=wait_sec)
        try:
            con.row_factory = sqlite3.Row
            con.execute("PRAGMA query_only = ON")
            con.execute("PRAGMA temp_store = MEMORY")
            yield con
        finally:
            con.close()
        return

    if zero_write:
        with tempfile.TemporaryDirectory(prefix="cc024_ro_wal_") as tmp_dir:
            dst_db = Path(tmp_dir) / resolved.name
            shutil.copy2(resolved, dst_db)
            for suffix in ("-wal", "-shm"):
                src_side = resolved.with_name(resolved.name + suffix)
                if src_side.is_file():
                    shutil.copy2(src_side, dst_db.with_name(dst_db.name + suffix))
            con = sqlite3.connect(dst_db.as_uri() + "?mode=ro", uri=True, timeout=wait_sec)
            try:
                con.row_factory = sqlite3.Row
                con.execute("PRAGMA query_only = ON")
                con.execute(f"PRAGMA busy_timeout = {busy_ms}")
                con.execute("PRAGMA temp_store = MEMORY")
                yield con
            finally:
                con.close()
        return

    con = sqlite3.connect(resolved.as_uri() + "?mode=ro", uri=True, timeout=wait_sec)
    try:
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA query_only = ON")
        con.execute(f"PRAGMA busy_timeout = {busy_ms}")
        con.execute("PRAGMA temp_store = MEMORY")
        yield con
    finally:
        con.close()


def _sqlite_tables(con: sqlite3.Connection) -> set[str]:
    return {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}


def _d1_series_rank(series_id: str) -> int:
    if series_id in _D1_SERIES_PRIORITY:
        return _D1_SERIES_PRIORITY.index(series_id)
    if series_id.startswith("EXNESS:"):
        return len(_D1_SERIES_PRIORITY)
    return len(_D1_SERIES_PRIORITY) + 1


def _us_trading_days_between(older_day: date, newer_day: date, *, calendar_path=None, calendar=None) -> int:
    """Count US cash/bond business days strictly after older_day up to newer_day."""
    if newer_day <= older_day:
        return 0
    from .publication_image_contract_v1 import us_cash_session_bounds

    cal_path = CASH_CALENDAR if calendar_path is None else calendar_path
    count = 0
    cursor = older_day + timedelta(days=1)
    while cursor <= newer_day:
        if us_cash_session_bounds(cursor, calendar_path=cal_path, calendar=calendar) is not None:
            count += 1
        cursor += timedelta(days=1)
    return count


@contextmanager
def _lock(path):
    """Nonblocking process lock; Windows releases it even after a crashed fetch."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+b") as stream:
        if stream.tell() == 0:
            stream.write(b"0")
            stream.flush()
        stream.seek(0)
        try:
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            raise QuoteError("PUBLIC_QUOTE_FETCH_IN_PROGRESS") from None
        try:
            yield
        finally:
            stream.seek(0)
            if os.name == "nt":
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream, fcntl.LOCK_UN)


def _assert_url_allowed(url):
    """Permanently forbid any Yahoo Finance HTTP hostname (CC-024)."""
    host = (urlsplit(str(url)).hostname or "").casefold()
    if host == "yahoo.com" or host.endswith(".yahoo.com"):
        raise QuoteError("CC024_YAHOO_HTTP_FORBIDDEN", host=host)


def http_read(url):
    """Bounded read-only HTTP helper; Yahoo Finance hosts are permanently forbidden (CC-024)."""
    _assert_url_allowed(url)
    # No session, cookie, credentials, terminal, broker API or implicit retries.
    request = Request(url, headers={"User-Agent": "CapitalChronicle/1.0", "Accept": "application/json"})
    with urlopen(request, timeout=TIMEOUT) as response:
        raw = response.read(512 * 1024 + 1)
    if len(raw) > 512 * 1024:
        raise QuoteError("PUBLIC_QUOTE_RESPONSE_TOO_LARGE")
    return raw


def _number(value):
    result = float(value)
    if isinstance(value, bool) or not math.isfinite(result) or result <= 0:
        raise QuoteError("PUBLIC_QUOTE_VALUE_INVALID")
    return result


def source_url(market, *, allow_cnbc_dxy_fallback: bool = False):
    market = ALIASES.get(market, market)
    if market in RETIRED_FUTURES_PROXIES:
        raise QuoteError("CC024_YAHOO_FUTURES_PROXY_RETIRED", market=market)
    if market not in SYMBOLS:
        raise QuoteError("PUBLIC_QUOTE_MARKET_UNSUPPORTED", market=market)
    provider = SYMBOLS[market][0]
    if provider == "YAHOO":
        raise QuoteError("CC024_YAHOO_SCRAPER_RETIRED", market=market)
    if market == "DXY" and allow_cnbc_dxy_fallback:
        return "https://quote.cnbc.com/quote-html-webservice/quote.htm?" + urlencode({
            "symbols": ".DXY", "requestMethod": "quick", "noform": "1", "partnerId": "2",
            "fund": "1", "exthrs": "1", "output": "json"})
    return None


def parse(market, raw, *, received_at, seconds, allow_cnbc_dxy_fallback: bool = False):
    """Parse opt-in CNBC DXY fallback JSON only; Yahoo Finance parsing is permanently retired (CC-024)."""
    market = ALIASES.get(market, market)
    if market in RETIRED_FUTURES_PROXIES:
        raise QuoteError("CC024_YAHOO_FUTURES_PROXY_RETIRED", market=market)
    if market not in SYMBOLS:
        raise QuoteError("PUBLIC_QUOTE_MARKET_UNSUPPORTED", market=market)
    if not (market == "DXY" and allow_cnbc_dxy_fallback):
        raise QuoteError("CC024_YAHOO_SCRAPER_RETIRED", market=market)
    _, _, label, unit, instrument_type = SYMBOLS[market]
    data = json.loads(raw)
    rows = data["QuickQuoteResult"]["QuickQuote"]
    if len(rows) != 1 or str(rows[0].get("code")) != "0":
        raise QuoteError("PUBLIC_QUOTE_PROVIDER_NO_RESULT")
    row = rows[0]
    value, prior = row["last"], row["previous_day_closing"]
    observed = utc(row["last_time"])
    actual_type = row.get("assetType")
    returned_symbol = row.get("symbol")
    if returned_symbol != ".DXY" or actual_type != instrument_type:
        raise QuoteError("PUBLIC_QUOTE_SYMBOL_MISMATCH", requested_symbol=".DXY",
                         returned_symbol=returned_symbol, returned_type=actual_type)
    _number(value)
    _number(prior)
    delta = Decimal(str(value)) - Decimal(str(prior))
    return {
        "schema": "contentops.public_quote.v1",
        "market": market,
        "source": "CNBC",
        "source_exchange": row.get("exchange", row.get("exchangeName")),
        "source_kind": "PUBLIC_ON_DEMAND_QUOTE",
        "source_url": source_url(market, allow_cnbc_dxy_fallback=True),
        "source_symbol": SYMBOLS[market][1],
        "returned_symbol": returned_symbol,
        "instrument_name": label,
        "instrument_type": instrument_type,
        "value": float(value),
        "value_text": str(value),
        "unit": unit,
        "prior_close": float(prior),
        "day_change": float(delta),
        "day_change_text": str(delta),
        "day_change_pct": float(delta / Decimal(str(prior)) * 100),
        "change_unit": unit,
        "observed_at_utc": observed.isoformat(),
        "known_at_utc": utc(received_at).isoformat(),
        "fetch_seconds": seconds,
        "response_sha256": sha256(raw).hexdigest(),
    }


def _prior_close_from_db(con: sqlite3.Connection, tables: set[str], db_symbol: str, obs_day_iso: str,
                         now_ts: float, *, market: str) -> float | None:
    """Find the most recent completed prior-session close strictly before obs_day_iso (non-Yahoo)."""
    best_day: str | None = None
    best_close: float | None = None

    if "history_bars" in tables and "history_sources" in tables:
        has_hist_invalid = "history_invalid" in tables
        sources = con.execute(
            """SELECT source_id, series_id, known_epoch FROM history_sources
               WHERE market = ? AND timeframe = 'D1'
                 AND series_id NOT LIKE 'YAHOO_FINANCE:%'
                 AND known_epoch <= ?""",
            (db_symbol, now_ts),
        ).fetchall()
        sources = sorted(sources, key=lambda s: (_d1_series_rank(str(s["series_id"])), -float(s["known_epoch"])))
        seen_by_day: dict[str, float] = {}
        for src in sources:
            invalid_clause = (
                "AND NOT EXISTS (SELECT 1 FROM history_invalid i "
                "WHERE i.source_id = b.source_id AND i.open_epoch = b.open_epoch)"
                if has_hist_invalid else ""
            )
            row = con.execute(
                f"""SELECT b.session_date, b.high, b.low, b.close
                    FROM history_bars b
                    WHERE b.source_id = ? AND b.session_date < ? AND b.end_epoch <= ?
                      {invalid_clause}
                    ORDER BY b.session_date DESC, b.open_epoch DESC LIMIT 1""",
                (src["source_id"], obs_day_iso, now_ts),
            ).fetchone()
            if not row:
                continue
            try:
                high, low, close = map(_number, (row["high"], row["low"], row["close"]))
            except QuoteError:
                continue
            if low <= close <= high and row["session_date"] not in seen_by_day:
                seen_by_day[row["session_date"]] = close
        if seen_by_day:
            best_day = max(seen_by_day)
            best_close = seen_by_day[best_day]

    # Also inspect deduplicated M15 NATIVE_BROKER bars strictly prior to obs_day_iso so
    # recent sessions after a D1 route pause (Trap 2) supply an accurate prior close.
    if "bars" in tables:
        has_invalid = "invalid_bars" in tables
        obs_d = date.fromisoformat(obs_day_iso)
        if market == "BTCUSD":
            cutoff_ts = datetime.combine(obs_d, time(0, 0), timezone.utc).timestamp()
        elif market in {"US500", "USTEC"}:
            from .publication_image_contract_v1 import _prior_us_cash_close
            cutoff_ts = _prior_us_cash_close(obs_d - timedelta(days=1), calendar_path=CASH_CALENDAR).timestamp()
        else:
            cutoff_ts = datetime.combine(obs_d, time(0, 0), ET).astimezone(timezone.utc).timestamp()
        invalid_clause = (
            "AND NOT EXISTS (SELECT 1 FROM invalid_bars i "
            "WHERE i.source_sha256 = b.source_sha256 AND i.symbol = b.symbol AND i.open_epoch = b.open_epoch)"
            if has_invalid else ""
        )
        m15_row = con.execute(
            f"""SELECT b.open_epoch, b.high, b.low, b.close
                FROM bars b
                WHERE b.symbol = ? AND b.series_id = 'NATIVE_BROKER'
                  AND b.known_epoch <= ? AND (b.open_epoch + 900) <= ?
                  {invalid_clause}
                ORDER BY b.open_epoch DESC, b.known_epoch DESC LIMIT 1""",
            (db_symbol, now_ts, min(now_ts, cutoff_ts)),
        ).fetchone()
        if m15_row:
            try:
                high, low, close = map(_number, (m15_row["high"], m15_row["low"], m15_row["close"]))
                if low <= close <= high:
                    end_dt = datetime.fromtimestamp(int(m15_row["open_epoch"]) + 900, timezone.utc)
                    m15_day = (end_dt.date() if market == "BTCUSD" else end_dt.astimezone(ET).date()).isoformat()
                    if m15_day < obs_day_iso and (best_day is None or m15_day > best_day):
                        best_day = m15_day
                        best_close = close
            except QuoteError:
                pass
    return best_close


def _fetch_local_bar_quote(market: str, *, now: datetime, reference_at=None, closed_cash_index: bool = False,
                           bars_db=None, seconds: float = 0.0, zero_write: bool = False) -> dict:
    """Resolve a market quote from held SQLite bars (M15 NATIVE_BROKER deduped -> non-Yahoo D1)."""
    _, db_symbol, label, unit, instrument_type = SYMBOLS[market]
    db_path = Path(BARS_DB if bars_db is None else bars_db)
    now_ts = now.timestamp()
    ref_dt = utc(reference_at) if reference_at is not None else now
    end_limit = min(now_ts, ref_dt.timestamp())

    try:
        with _open_readonly_sqlite(db_path, zero_write=zero_write) as con:
            tables = _sqlite_tables(con)
            # 1) Prefer deduplicated completed M15 NATIVE_BROKER bars excluding invalid_bars (Trap 1 & Trap 3).
            if "bars" in tables:
                has_invalid = "invalid_bars" in tables
                invalid_clause = (
                    "AND NOT EXISTS (SELECT 1 FROM invalid_bars i "
                    "WHERE i.source_sha256 = b.source_sha256 AND i.symbol = b.symbol AND i.open_epoch = b.open_epoch)"
                    if has_invalid else ""
                )
                row = con.execute(
                    f"""SELECT b.symbol, b.open_epoch, b.open, b.high, b.low, b.close, b.known_epoch,
                               b.source_sha256, b.price_basis, b.series_id
                        FROM bars b
                        WHERE b.symbol = ? AND b.series_id = 'NATIVE_BROKER'
                          AND b.known_epoch <= ? AND (b.open_epoch + 900) <= ?
                          {invalid_clause}
                        ORDER BY b.open_epoch DESC, b.known_epoch DESC LIMIT 1""",
                    (db_symbol, now_ts, end_limit),
                ).fetchone()
                if row is not None:
                    high, low, close = map(_number, (row["high"], row["low"], row["close"]))
                    if not low <= close <= high:
                        raise QuoteError("PUBLIC_QUOTE_VALUE_INVALID", market=market, source_symbol=db_symbol)
                    observed = datetime.fromtimestamp(int(row["open_epoch"]) + 900, timezone.utc)
                    known = datetime.fromtimestamp(float(row["known_epoch"]), timezone.utc)
                    obs_day_iso = (observed.date() if market == "BTCUSD" else observed.astimezone(ET).date()).isoformat()
                    prior = _prior_close_from_db(con, tables, db_symbol, obs_day_iso, now_ts, market=market)
                    delta = Decimal(str(close)) - Decimal(str(prior)) if prior is not None else None
                    meta_digest = sha256(canonical({
                        "db_symbol": db_symbol, "open_epoch": int(row["open_epoch"]),
                        "close": close, "source_sha256": row["source_sha256"], "series_id": row["series_id"],
                    })).hexdigest()
                    return {
                        "schema": "contentops.public_quote.v1",
                        "market": market,
                        "source": _LOCAL_BAR_ATTRIBUTION,
                        "source_exchange": "LOCAL_BARS",
                        "source_kind": "PUBLIC_ON_DEMAND_QUOTE",
                        "source_url": None,
                        "source_symbol": db_symbol,
                        "source_series_id": str(row["series_id"]),
                        "source_bar_sha256": str(row["source_sha256"]),
                        "instrument_name": label,
                        "instrument_type": instrument_type,
                        "value": float(close),
                        "value_text": str(close),
                        "unit": unit,
                        "prior_close": float(prior) if prior is not None else None,
                        "day_change": float(delta) if delta is not None else None,
                        "day_change_text": str(delta) if delta is not None else None,
                        "day_change_pct": float(delta / Decimal(str(prior)) * 100) if delta is not None and prior else None,
                        "change_unit": unit,
                        "observed_at_utc": observed.isoformat(),
                        "known_at_utc": known.isoformat(),
                        "fetch_seconds": seconds,
                        "response_sha256": meta_digest,
                    }

            # 2) Fallback: non-Yahoo D1 history_bars (e.g. DXY, BRENT/UKOIL when M15 absent — Trap 5 Option C).
            if "history_bars" in tables and "history_sources" in tables:
                has_hist_invalid = "history_invalid" in tables
                sources = con.execute(
                    """SELECT source_id, source_sha256, series_id, known_epoch FROM history_sources
                       WHERE market = ? AND timeframe = 'D1'
                         AND series_id NOT LIKE 'YAHOO_FINANCE:%'
                         AND known_epoch <= ?""",
                    (db_symbol, now_ts),
                ).fetchall()
                sources = sorted(sources, key=lambda s: (_d1_series_rank(str(s["series_id"])), -float(s["known_epoch"])))
                by_day: dict[str, tuple[dict, float]] = {}
                for src in sources:
                    invalid_clause = (
                        "AND NOT EXISTS (SELECT 1 FROM history_invalid i "
                        "WHERE i.source_id = b.source_id AND i.open_epoch = b.open_epoch)"
                        if has_hist_invalid else ""
                    )
                    rows = con.execute(
                        f"""SELECT b.open_epoch, b.end_epoch, b.session_date, b.high, b.low, b.close
                            FROM history_bars b
                            WHERE b.source_id = ? AND b.end_epoch <= ?
                              {invalid_clause}
                            ORDER BY b.session_date DESC, b.open_epoch DESC LIMIT 4""",
                        (src["source_id"], end_limit),
                    ).fetchall()
                    for r in rows:
                        try:
                            high, low, close = map(_number, (r["high"], r["low"], r["close"]))
                        except QuoteError:
                            continue
                        if not low <= close <= high:
                            continue
                        sday = str(r["session_date"])
                        if sday not in by_day:
                            by_day[sday] = ({
                                "end_epoch": int(r["end_epoch"]),
                                "open_epoch": int(r["open_epoch"]),
                                "session_date": sday,
                                "close": close,
                                "known_epoch": float(src["known_epoch"]),
                                "source_id": str(src["source_id"]),
                                "source_sha256": str(src["source_sha256"]),
                                "series_id": str(src["series_id"]),
                            }, close)
                if by_day:
                    ordered_days = sorted(by_day, reverse=True)
                    latest, close = by_day[ordered_days[0]]
                    prior = by_day[ordered_days[1]][1] if len(ordered_days) > 1 else None
                    observed = datetime.fromtimestamp(latest["end_epoch"], timezone.utc)
                    known = datetime.fromtimestamp(latest["known_epoch"], timezone.utc)
                    delta = Decimal(str(close)) - Decimal(str(prior)) if prior is not None else None
                    meta_digest = sha256(canonical(latest)).hexdigest()
                    return {
                        "schema": "contentops.public_quote.v1",
                        "market": market,
                        "source": _LOCAL_BAR_ATTRIBUTION,
                        "source_exchange": "LOCAL_BARS",
                        "source_kind": "PUBLIC_ON_DEMAND_QUOTE",
                        "source_url": None,
                        "source_symbol": db_symbol,
                        "source_series_id": latest["series_id"],
                        "source_bar_sha256": latest["source_sha256"],
                        "instrument_name": label,
                        "instrument_type": instrument_type,
                        "value": float(close),
                        "value_text": str(close),
                        "unit": unit,
                        "prior_close": float(prior) if prior is not None else None,
                        "day_change": float(delta) if delta is not None else None,
                        "day_change_text": str(delta) if delta is not None else None,
                        "day_change_pct": float(delta / Decimal(str(prior)) * 100) if delta is not None and prior else None,
                        "change_unit": unit,
                        "observed_at_utc": observed.isoformat(),
                        "known_at_utc": known.isoformat(),
                        "fetch_seconds": seconds,
                        "response_sha256": meta_digest,
                    }
    except FileNotFoundError:
        raise QuoteError("PUBLIC_QUOTE_LOCAL_BAR_UNAVAILABLE", market=market, source_symbol=db_symbol) from None
    except sqlite3.Error as exc:
        raise QuoteError("PUBLIC_QUOTE_LOCAL_BAR_UNREADABLE:" + type(exc).__name__,
                         market=market, source_symbol=db_symbol) from None
    raise QuoteError("PUBLIC_QUOTE_LOCAL_BAR_UNAVAILABLE", market=market, source_symbol=db_symbol)


def _fetch_local_official_rate(market: str, *, now: datetime, rates_db=None, bars_db=None,
                               seconds: float = 0.0, zero_write: bool = False) -> dict:
    """Resolve US2Y/US10Y from local public-domain US Treasury observations (Trap 4)."""
    _, symbol, label, unit, instrument_type = SYMBOLS[market]
    r_path = Path(RATES_DB if rates_db is None else rates_db)
    b_path = Path(BARS_DB if bars_db is None else bars_db)

    # 1) Primary: observations.sqlite3 (family='direct_rates', series='US2Y'|'US10Y').
    if r_path.is_file():
        try:
            with _open_readonly_sqlite(r_path, zero_write=zero_write) as con:
                tables = _sqlite_tables(con)
                if "observations" in tables:
                    rows = con.execute(
                        """SELECT observation_date, known_at, version, payload
                           FROM observations
                           WHERE family = 'direct_rates' AND series = ?
                           ORDER BY observation_date DESC, known_at DESC
                           LIMIT 64""",
                        (symbol,),
                    ).fetchall()
                    by_day: dict[str, dict] = {}
                    for r in rows:
                        try:
                            payload = json.loads(r["payload"])
                            record = payload["record"]
                            known = max(
                                utc(r["known_at"]),
                                utc(payload.get("store_available_at_utc", r["known_at"])),
                            )
                            if known > now:
                                continue
                            official_url = str(record.get("official_url") or "")
                            host = (urlsplit(official_url).hostname or "").casefold()
                            if not any(host == h or host.endswith("." + h) for h in _OFFICIAL_RATE_HOSTS):
                                continue
                            val = _number(record["value"])
                            obs_day = str(record.get("reference_period") or r["observation_date"])
                            date.fromisoformat(obs_day)
                            prev = by_day.get(obs_day)
                            if prev is None or known > prev["known"]:
                                by_day[obs_day] = {
                                    "observation_date": obs_day,
                                    "value": val,
                                    "unit": str(record.get("unit") or unit),
                                    "known": known,
                                    "official_url": official_url,
                                    "attribution": str((record.get("rights") or {}).get("attribution") or _TREASURY_ATTRIBUTION),
                                    "version": str(r["version"]),
                                }
                        except (ValueError, KeyError, TypeError):
                            continue
                    if by_day:
                        ordered = sorted(by_day, reverse=True)
                        latest = by_day[ordered[0]]
                        prior = by_day[ordered[1]]["value"] if len(ordered) > 1 else None
                        obs_day_obj = date.fromisoformat(latest["observation_date"])
                        bench_close = datetime.combine(obs_day_obj, time(16, 0), ET).astimezone(timezone.utc)
                        observed = min(latest["known"], bench_close)
                        delta = Decimal(str(latest["value"])) - Decimal(str(prior)) if prior is not None else None
                        meta_digest = sha256(canonical({
                            "market": market, "observation_date": latest["observation_date"],
                            "value": latest["value"], "version": latest["version"],
                        })).hexdigest()
                        return {
                            "schema": "contentops.public_quote.v1",
                            "market": market,
                            "source": latest["attribution"],
                            "source_exchange": "US_TREASURY",
                            "source_kind": "PUBLIC_ON_DEMAND_QUOTE",
                            "source_url": latest["official_url"],
                            "source_symbol": symbol,
                            "source_version": latest["version"],
                            "observation_date": latest["observation_date"],
                            "freshness_basis": "US_BUSINESS_DAYS",
                            "instrument_name": label,
                            "instrument_type": instrument_type,
                            "value": float(latest["value"]),
                            "value_text": str(latest["value"]),
                            "unit": unit,
                            "prior_close": float(prior) if prior is not None else None,
                            "day_change": float(delta) if delta is not None else None,
                            "day_change_text": str(delta) if delta is not None else None,
                            "day_change_pct": float(delta / Decimal(str(prior)) * 100) if delta is not None and prior else None,
                            "change_unit": "percentage points",
                            "observed_at_utc": observed.isoformat(),
                            "known_at_utc": latest["known"].isoformat(),
                            "fetch_seconds": seconds,
                            "response_sha256": meta_digest,
                        }
        except sqlite3.Error as exc:
            raise QuoteError("PUBLIC_QUOTE_OFFICIAL_RATE_UNREADABLE:" + type(exc).__name__,
                             market=market, source_symbol=symbol) from None

    # 2) Fallback: bars.sqlite3 history_points (US_TREASURY:BC_2YEAR / US_TREASURY:BC_10YEAR).
    if b_path.is_file():
        try:
            with _open_readonly_sqlite(b_path, zero_write=zero_write) as con:
                tables = _sqlite_tables(con)
                if "history_points" in tables and "history_sources" in tables:
                    has_hist_invalid = "history_invalid" in tables
                    invalid_clause = (
                        "AND NOT EXISTS (SELECT 1 FROM history_invalid i "
                        "WHERE i.source_id = hp.source_id AND i.open_epoch = hp.open_epoch)"
                        if has_hist_invalid else ""
                    )
                    rows = con.execute(
                        f"""SELECT hs.source_id, hs.source_sha256, hs.series_id, hs.known_epoch,
                                   hp.open_epoch, hp.end_epoch, hp.session_date, hp.value
                            FROM history_points hp
                            JOIN history_sources hs ON hs.source_id = hp.source_id
                            WHERE hs.market = ? AND hs.series_id LIKE 'US_TREASURY:%'
                              AND hs.known_epoch <= ? AND hp.end_epoch <= ?
                              {invalid_clause}
                            ORDER BY hp.session_date DESC, hs.known_epoch DESC
                            LIMIT 16""",
                        (symbol, now.timestamp(), now.timestamp()),
                    ).fetchall()
                    by_day: dict[str, dict] = {}
                    for r in rows:
                        try:
                            val = _number(r["value"])
                            sday = str(r["session_date"])
                            date.fromisoformat(sday)
                        except (QuoteError, ValueError):
                            continue
                        if sday not in by_day:
                            by_day[sday] = {
                                "session_date": sday,
                                "value": val,
                                "end_epoch": int(r["end_epoch"]),
                                "known_epoch": float(r["known_epoch"]),
                                "series_id": str(r["series_id"]),
                                "source_id": str(r["source_id"]),
                                "source_sha256": str(r["source_sha256"]),
                            }
                    if by_day:
                        ordered = sorted(by_day, reverse=True)
                        latest = by_day[ordered[0]]
                        prior = by_day[ordered[1]]["value"] if len(ordered) > 1 else None
                        known = datetime.fromtimestamp(latest["known_epoch"], timezone.utc)
                        observed = min(known, datetime.fromtimestamp(latest["end_epoch"], timezone.utc))
                        delta = Decimal(str(latest["value"])) - Decimal(str(prior)) if prior is not None else None
                        meta_digest = sha256(canonical(latest)).hexdigest()
                        return {
                            "schema": "contentops.public_quote.v1",
                            "market": market,
                            "source": _TREASURY_ATTRIBUTION,
                            "source_exchange": "US_TREASURY",
                            "source_kind": "PUBLIC_ON_DEMAND_QUOTE",
                            "source_url": "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/pages/xml?data=daily_treasury_yield_curve",
                            "source_symbol": symbol,
                            "source_series_id": latest["series_id"],
                            "observation_date": latest["session_date"],
                            "freshness_basis": "US_BUSINESS_DAYS",
                            "instrument_name": label,
                            "instrument_type": instrument_type,
                            "value": float(latest["value"]),
                            "value_text": str(latest["value"]),
                            "unit": unit,
                            "prior_close": float(prior) if prior is not None else None,
                            "day_change": float(delta) if delta is not None else None,
                            "day_change_text": str(delta) if delta is not None else None,
                            "day_change_pct": float(delta / Decimal(str(prior)) * 100) if delta is not None and prior else None,
                            "change_unit": "percentage points",
                            "observed_at_utc": observed.isoformat(),
                            "known_at_utc": known.isoformat(),
                            "fetch_seconds": seconds,
                            "response_sha256": meta_digest,
                        }
        except sqlite3.Error as exc:
            raise QuoteError("PUBLIC_QUOTE_OFFICIAL_RATE_UNREADABLE:" + type(exc).__name__,
                             market=market, source_symbol=symbol) from None

    raise QuoteError("PUBLIC_QUOTE_OFFICIAL_RATE_UNAVAILABLE", market=market, source_symbol=symbol)


def validate(observation, market, *, now, max_age_seconds=4500, reference_at=None, closed_cash_index=False,
             cash_calendar=None):
    market = ALIASES.get(market, market)
    if market in RETIRED_FUTURES_PROXIES:
        raise QuoteError("CC024_YAHOO_FUTURES_PROXY_RETIRED", market=market)
    if market not in SYMBOLS:
        raise QuoteError("PUBLIC_QUOTE_MARKET_UNSUPPORTED", market=market)
    obs_market = observation.get("market")
    obs_symbol = observation.get("source_symbol")
    expected_symbol = SYMBOLS[market][1]
    legacy_markets = LEGACY_MARKETS.get(market, set())
    allowed_symbols = {expected_symbol}
    if obs_market in legacy_markets:
        allowed_symbols |= set(HISTORICAL_SOURCE_SYMBOLS.get(market, ()))
    if obs_market not in {market, *legacy_markets} or obs_symbol not in allowed_symbols:
        raise QuoteError("PUBLIC_QUOTE_SYMBOL_MISMATCH")
    at, known, observed = utc(reference_at or now), utc(observation["known_at_utc"]), utc(observation["observed_at_utc"])
    _number(observation["value"])
    if known > utc(now) or observed > known:
        raise QuoteError("PUBLIC_QUOTE_FUTURE_CLOCK")

    # Trap 4: US Treasury daily yield curve uses US business-day freshness (<= 2 US trading days).
    if (SYMBOLS[market][0] == "LOCAL_OFFICIAL_RATES"
            and observation.get("freshness_basis") == "US_BUSINESS_DAYS"):
        obs_day = (date.fromisoformat(observation["observation_date"])
                   if observation.get("observation_date")
                   else observed.astimezone(ET).date())
        at_day = at.astimezone(ET).date()
        if obs_day > at_day:
            raise QuoteError("PUBLIC_QUOTE_FUTURE_CLOCK")
        trading_days_age = _us_trading_days_between(obs_day, at_day, calendar_path=cash_calendar)
        if trading_days_age > US_TREASURY_MAX_TRADING_DAYS:
            raise QuoteError("PUBLIC_QUOTE_STALE", age_seconds=(at - observed).total_seconds(),
                             trading_days_age=trading_days_age,
                             observed_at_utc=observed.isoformat(), source=observation.get("source"))
        return observation

    age = (at - observed).total_seconds()
    neg_limit = (CASH_INDEX_CLOSE_SETTLE_SECONDS
                 if closed_cash_index and market in {"US500", "USTEC"} and observation.get("instrument_type") == "INDEX"
                 else 2)
    if not -neg_limit <= age <= max_age_seconds:
        raise QuoteError("PUBLIC_QUOTE_STALE", age_seconds=age,
                         observed_at_utc=observed.isoformat(), source=observation.get("source"))
    return observation


def get(market, *, now=None, root=None, fetch=True, max_age_seconds=4500, reference_at=None,
        reader=None, clock=None, closed_cash_index=False, allow_cnbc_dxy_fallback=False,
        bars_db=None, rates_db=None, cash_calendar=None, zero_write=False):
    """Throttle successes AND failures across callers/processes; no retry loop."""
    market = ALIASES.get(market, market)
    if market in RETIRED_FUTURES_PROXIES:
        raise QuoteError("CC024_YAHOO_FUTURES_PROXY_RETIRED", market=market)
    if market not in SYMBOLS:
        raise QuoteError("PUBLIC_QUOTE_MARKET_UNSUPPORTED", market=market)
    root = Path(root or ROOT)
    clock = clock or utcnow
    started_at = utc(now or clock())
    provider, source_symbol, *_ = SYMBOLS[market]
    key_tuple = (provider, source_symbol, bool(allow_cnbc_dxy_fallback) if market == "DXY" else False)
    key = sha256(canonical(key_tuple)).hexdigest()[:24]
    state_path = root / "latest" / (key + ".json")
    with _lock(root / "locks" / (key + ".lock")):
        try:
            state = json.loads(state_path.read_bytes())
        except (OSError, ValueError):
            state = {}
        elapsed = (started_at - utc(state["attempted_at_utc"])).total_seconds() if state else float("inf")
        if not fetch or elapsed < MIN_INTERVAL:
            details = {"fetch_seconds": 0., "cache_hit": True, "rate_limited": fetch,
                       "retry_after_seconds": max(0, MIN_INTERVAL - elapsed)}
            if not state.get("observation_path"):
                if isinstance(state.get("failure_details"), dict):
                    details.update(state["failure_details"])
                raise QuoteError(state.get("cause", "PUBLIC_QUOTE_NOT_CACHED"), **details)
            observation = resolve(state["observation_path"], state["observation_sha256"])
            try:
                validate(observation, market, now=started_at, max_age_seconds=max_age_seconds,
                         reference_at=reference_at, closed_cash_index=closed_cash_index,
                         cash_calendar=cash_calendar)
            except QuoteError as exc:
                raise QuoteError(str(exc), **{**exc.details, **details}) from None
            return {**observation, **{k: state[k] for k in ("observation_path", "observation_sha256")},
                    "request_seconds": 0., "cache_hit": True}
        # Persist the claim before reading. Even a failed/timed-out attempt consumes its minute.
        state = {"attempted_at_utc": started_at.isoformat(), "cause": "PUBLIC_QUOTE_INTERRUPTED_FETCH"}
        save(state_path, state)
        began = perf_counter()
        try:
            if market == "DXY" and allow_cnbc_dxy_fallback:
                url = source_url("DXY", allow_cnbc_dxy_fallback=True)
                raw = (reader or http_read)(url)
                seconds = perf_counter() - began
                received = max(started_at, utc(clock()))
                observation = parse("DXY", raw, received_at=received, seconds=seconds,
                                    allow_cnbc_dxy_fallback=True)
            elif provider == "LOCAL_OFFICIAL_RATES":
                observation = _fetch_local_official_rate(
                    market, now=started_at, rates_db=rates_db, bars_db=bars_db, seconds=0.0,
                    zero_write=zero_write,
                )
                seconds = perf_counter() - began
                observation["fetch_seconds"] = seconds
                received = max(started_at, utc(clock()))
            else:
                observation = _fetch_local_bar_quote(
                    market, now=started_at, reference_at=reference_at,
                    closed_cash_index=closed_cash_index, bars_db=bars_db, seconds=0.0,
                    zero_write=zero_write,
                )
                seconds = perf_counter() - began
                observation["fetch_seconds"] = seconds
                received = max(started_at, utc(clock()))
            frozen = freeze(observation, root=root)
            save(state_path, {**state, "cause": "PUBLIC_QUOTE_FETCHED", "fetch_seconds": seconds,
                             **{k: frozen[k] for k in ("observation_path", "observation_sha256")}})
            validate(observation, market, now=received, max_age_seconds=max_age_seconds,
                     reference_at=reference_at, closed_cash_index=closed_cash_index,
                     cash_calendar=cash_calendar)
            return {**frozen, "request_seconds": seconds, "cache_hit": False}
        except Exception as exc:
            seconds = perf_counter() - began
            cause = str(exc) if isinstance(exc, QuoteError) else (
                "PUBLIC_QUOTE_HTTP_" + str(exc.code) if hasattr(exc, "code") else "PUBLIC_QUOTE_FETCH_FAILED:" + type(exc).__name__)
            # A stale response stays available for named readback, never as a fresh quote.
            saved = json.loads(state_path.read_bytes())
            safe_details = ({k: v for k, v in exc.details.items() if k in _SAFE_FAILURE_DETAIL_KEYS}
                            if isinstance(exc, QuoteError) else {})
            save(state_path, {**saved, "cause": cause, "fetch_seconds": seconds,
                              **({"failure_details": safe_details} if safe_details else {})})
            raise QuoteError(cause, **{**(exc.details if isinstance(exc, QuoteError) else {}),
                "market": market, "source_symbol": source_symbol, "fetch_seconds": seconds}) from None
