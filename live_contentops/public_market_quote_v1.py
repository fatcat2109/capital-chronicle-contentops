"""CC-509: one public quote per symbol/minute, shared by replies and charts.

The Yahoo symbols/endpoint reuse Data's held YAHOO_FINANCE_CHART imports.
CNBC's public quick quote supplies timed Treasury yields (never note futures).
Only individual attributed facts may leave this runtime cache (host rule 7).
"""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
from decimal import Decimal
from hashlib import sha256
import json
import math
import os
from pathlib import Path
from time import perf_counter
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen
from uuid import uuid4

ROOT = Path(r"A:\Capital Chronicle\Runtime\ContentOps\references\public-quotes-v1")
MIN_INTERVAL = 60
TIMEOUT = 5
# Routing market, actual source instrument, public name and units are separate.
SYMBOLS = {
    "US500": ("YAHOO", "^GSPC", "S&P 500 cash index", "points", "INDEX"),
    "XAUUSD": ("YAHOO", "GC=F", "Gold futures", "USD per troy ounce", "FUTURE"),
    "EURUSD": ("YAHOO", "EURUSD=X", "EUR/USD spot", "USD per EUR", "CURRENCY"),
    "USDJPY": ("YAHOO", "JPY=X", "USD/JPY spot", "JPY per USD", "CURRENCY"),
    "USOIL": ("YAHOO", "CL=F", "WTI crude oil futures", "USD per barrel", "FUTURE"),
    "BTCUSD": ("YAHOO", "BTC-USD", "Bitcoin spot", "USD", "CRYPTOCURRENCY"),
    "NDX": ("YAHOO", "^NDX", "Nasdaq 100 cash index", "points", "INDEX"),
    "DXY": ("YAHOO", "DX-Y.NYB", "US dollar index", "points", "INDEX"),
    "US2Y": ("CNBC", "US2Y", "US 2-year Treasury yield", "percent", "BOND"),
    "US10Y": ("CNBC", "US10Y", "US 10-year Treasury yield", "percent", "BOND"),
    "BRENT": ("YAHOO", "BZ=F", "Brent crude oil futures", "USD per barrel", "FUTURE"),
}
ALIASES = {"SPX": "US500", "WTI": "USOIL"}


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


def http_read(url):
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


def source_url(market):
    provider, symbol, *_ = SYMBOLS[market]
    if provider == "YAHOO":
        return "https://query1.finance.yahoo.com/v8/finance/chart/" + quote(symbol, safe="") + "?range=1d&interval=1m"
    return "https://quote.cnbc.com/quote-html-webservice/quote.htm?" + urlencode({
        "symbols": symbol, "requestMethod": "quick", "noform": "1", "partnerId": "2",
        "fund": "1", "exthrs": "1", "output": "json"})


def parse(market, raw, *, received_at, seconds):
    provider, symbol, label, unit, instrument_type = SYMBOLS[market]
    data = json.loads(raw)
    if provider == "YAHOO":
        rows = data["chart"].get("result") or []
        if len(rows) != 1:
            raise QuoteError("PUBLIC_QUOTE_PROVIDER_NO_RESULT")
        row = rows[0]["meta"]
        value, prior = row["regularMarketPrice"], row.get("previousClose", row.get("chartPreviousClose"))
        observed = datetime.fromtimestamp(row["regularMarketTime"], timezone.utc)
        actual_type = row.get("instrumentType")
    else:
        rows = data["QuickQuoteResult"]["QuickQuote"]
        if len(rows) != 1 or str(rows[0].get("code")) != "0":
            raise QuoteError("PUBLIC_QUOTE_PROVIDER_NO_RESULT")
        row = rows[0]
        value, prior = row["last"], row["previous_day_closing"]
        observed = utc(row["last_time"])
        actual_type = row.get("assetType")
    if row.get("symbol") != symbol or actual_type != instrument_type:
        raise QuoteError("PUBLIC_QUOTE_SYMBOL_MISMATCH", requested_symbol=symbol,
                         returned_symbol=row.get("symbol"), returned_type=actual_type)
    _number(value)
    _number(prior)
    delta = Decimal(str(value)) - Decimal(str(prior))
    return {"schema": "contentops.public_quote.v1", "market": market,
        "source": "Yahoo Finance" if provider == "YAHOO" else "CNBC / Tradeweb",
        "source_kind": "PUBLIC_ON_DEMAND_QUOTE", "source_url": source_url(market),
        "source_symbol": symbol, "instrument_name": label, "instrument_type": instrument_type,
        "value": float(value), "value_text": str(value), "unit": unit,
        "prior_close": float(prior), "day_change": float(delta),
        "day_change_text": str(delta),
        "day_change_pct": float(delta / Decimal(str(prior)) * 100),
        "change_unit": "percentage points" if unit == "percent" else unit,
        "observed_at_utc": observed.isoformat(), "known_at_utc": utc(received_at).isoformat(),
        "fetch_seconds": seconds, "response_sha256": sha256(raw).hexdigest()}


def validate(observation, market, *, now, max_age_seconds=4500, reference_at=None):
    market = ALIASES.get(market, market)
    if observation.get("market") != market or observation.get("source_symbol") != SYMBOLS[market][1]:
        raise QuoteError("PUBLIC_QUOTE_SYMBOL_MISMATCH")
    at, known, observed = utc(reference_at or now), utc(observation["known_at_utc"]), utc(observation["observed_at_utc"])
    _number(observation["value"])
    if known > utc(now) or observed > known:
        raise QuoteError("PUBLIC_QUOTE_FUTURE_CLOCK")
    age = (at - observed).total_seconds()
    if not -2 <= age <= max_age_seconds:
        raise QuoteError("PUBLIC_QUOTE_STALE", age_seconds=age,
                         observed_at_utc=observed.isoformat(), source=observation.get("source"))
    return observation


def get(market, *, now=None, root=None, fetch=True, max_age_seconds=4500, reference_at=None,
        reader=None, clock=None):
    """Throttle successes AND failures across callers/processes; no retry loop."""
    market = ALIASES.get(market, market)
    if market not in SYMBOLS:
        raise QuoteError("PUBLIC_QUOTE_MARKET_UNSUPPORTED", market=market)
    root = Path(root or ROOT)
    clock = clock or utcnow
    started_at = utc(now or clock())
    key = sha256(canonical(SYMBOLS[market][:2])).hexdigest()[:24]
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
                raise QuoteError(state.get("cause", "PUBLIC_QUOTE_NOT_CACHED"), **details)
            observation = resolve(state["observation_path"], state["observation_sha256"])
            try:
                validate(observation, market, now=started_at, max_age_seconds=max_age_seconds, reference_at=reference_at)
            except QuoteError as exc:
                raise QuoteError(str(exc), **{**exc.details, **details}) from None
            return {**observation, **{k: state[k] for k in ("observation_path", "observation_sha256")},
                    "request_seconds": 0., "cache_hit": True}
        # Persist the claim before HTTPS. Even a killed/timed-out attempt consumes its minute.
        state = {"attempted_at_utc": started_at.isoformat(), "cause": "PUBLIC_QUOTE_INTERRUPTED_FETCH"}
        save(state_path, state)
        began = perf_counter()
        try:
            raw = (reader or http_read)(source_url(market))
            seconds = perf_counter() - began
            received = max(started_at, utc(clock()))
            observation = parse(market, raw, received_at=received, seconds=seconds)
            frozen = freeze(observation, root=root)
            save(state_path, {**state, "cause": "PUBLIC_QUOTE_FETCHED", "fetch_seconds": seconds,
                             **{k: frozen[k] for k in ("observation_path", "observation_sha256")}})
            validate(observation, market, now=received, max_age_seconds=max_age_seconds, reference_at=reference_at)
            return {**frozen, "request_seconds": seconds, "cache_hit": False}
        except Exception as exc:
            seconds = perf_counter() - began
            cause = str(exc) if isinstance(exc, QuoteError) else (
                "PUBLIC_QUOTE_HTTP_" + str(exc.code) if hasattr(exc, "code") else "PUBLIC_QUOTE_FETCH_FAILED:" + type(exc).__name__)
            # A stale response stays available for named readback, never as a fresh quote.
            saved = json.loads(state_path.read_bytes())
            save(state_path, {**saved, "cause": cause, "fetch_seconds": seconds})
            raise QuoteError(cause, **{**(exc.details if isinstance(exc, QuoteError) else {}),
                "market": market, "source_symbol": SYMBOLS[market][1], "fetch_seconds": seconds}) from None
