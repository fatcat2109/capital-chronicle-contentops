"""CC-024 / Batch #129 WS1 + Batch #132 WS2 guard suite.

Verifies:
1. Static AST/regex scan across all live_contentops/ and scripts/ modules:
   - 0 active query1.finance.yahoo.com / query2.finance.yahoo.com / finance.yahoo.com endpoints
   - 0 "Source: Yahoo Finance" strings in renderers
   - 0 "YAHOO" providers in public_market_quote_v1.SYMBOLS
   - 0 "YAHOO_FINANCE:" entries in cpi_reaction_page_v1.LABELS or event_reaction_source_v1.SERIES
2. All 6 real-data traps from Batch #132 WS2:
   - Trap 1: 9x duplicate M15 rows in bars.sqlite3 + invalid_bars exclusion
   - Trap 2: Mandatory M15 -> D1 rollup past paused NATIVE_DAILY_ROUTE (2026-11-22), incl.
             Thanksgiving closed holiday & Black Friday 13:00 ET early close + ATR14 normal_day
   - Trap 3: USTEC resolves freshly via M15 LOCAL_BARS even without plan-status or M1 history_bars
   - Trap 4: US2Y/US10Y route to public-domain US Treasury (observations.sqlite3 & history_points
             fallback) with US business-day freshness (<= 2 US trading days)
   - Trap 5: DXY & BRENT (UKOIL) Option C resolve via LOCAL_BARS and fail closed when stale
             (default-off allow_cnbc_dxy_fallback=False, zero CNBC scrape, never relabel DTWEXBGS)
   - Trap 6: Reaction-table Yahoo filtering, graceful empty USOIL/USTEC bucket handling,
             DUKASCOPY:USATECH.IDX/USD & CC_HELD_CFD:* with 0 "CFD" or "Yahoo" leaks
3. Mandatory SQLite WAL Zero-Write Compliance (B12C37-M1 / CC754-H1):
   - Every touched SQLite reader opens via ?mode=ro&immutable=1 + query_only + close(),
     creating/mutating 0 -wal/-shm sidecars on journal_mode=WAL fixture DBs.
"""
from __future__ import annotations

import ast
from contextlib import closing
from datetime import date, datetime, timedelta, timezone
from hashlib import sha256
import json
from pathlib import Path
import re
import sqlite3
from zoneinfo import ZoneInfo

import pytest

from live_contentops import chart_price_reference_v1 as chart_prices
from live_contentops import cpi_reaction_page_v1 as cpi
from live_contentops import event_reaction_source_v1 as event_reactions
from live_contentops import grounded_search_engine_v6 as grounded
from live_contentops import market_wrap_editorial_v1 as wrap_editorial
from live_contentops import market_wrap_sources_v1 as wrap_sources
from live_contentops import public_market_quote_v1 as quotes
from live_contentops import x_reply_fact_sources_v1 as reply_facts

ET = ZoneInfo("America/New_York")
REPO_ROOT = Path(__file__).resolve().parents[1]

US_CAL_2026 = {
    "schema": "IbkrUsSessionCalendarV1",
    "years": {
        "2026": {
            "closed": ["2026-11-26", "2026-12-25"],
            "early_close_13_et": ["2026-11-27", "2026-12-24"],
        },
    },
}


def _et(year: int, month: int, day: int, hour: int, minute: int = 0) -> datetime:
    return datetime(year, month, day, hour, minute, tzinfo=ET).astimezone(timezone.utc)


def _create_full_bars_db(path: Path, *, wal: bool = False) -> None:
    con = sqlite3.connect(path)
    try:
        if wal:
            con.execute("PRAGMA journal_mode=WAL")
        con.executescript("""
            CREATE TABLE sources(
                sha256 TEXT PRIMARY KEY, path TEXT NOT NULL, capture_hash TEXT NOT NULL,
                known_at_utc TEXT NOT NULL, imported_at_utc TEXT NOT NULL);
            CREATE TABLE bars(
                symbol TEXT NOT NULL, open_epoch INTEGER NOT NULL,
                open REAL NOT NULL, high REAL NOT NULL, low REAL NOT NULL, close REAL NOT NULL,
                known_epoch REAL NOT NULL, source_sha256 TEXT NOT NULL,
                price_basis TEXT NOT NULL, contract_id TEXT NOT NULL,
                series_id TEXT NOT NULL DEFAULT 'NATIVE_BROKER',
                PRIMARY KEY(symbol, open_epoch, source_sha256));
            CREATE TABLE invalid_bars(
                source_sha256 TEXT NOT NULL, symbol TEXT NOT NULL, open_epoch INTEGER NOT NULL,
                reason TEXT NOT NULL, PRIMARY KEY(source_sha256, symbol, open_epoch));
            CREATE TABLE history_sources(
                source_id TEXT PRIMARY KEY, source_sha256 TEXT NOT NULL, path TEXT NOT NULL,
                market TEXT NOT NULL, timeframe TEXT NOT NULL, series_id TEXT NOT NULL,
                known_epoch REAL NOT NULL, metadata_json TEXT NOT NULL);
            CREATE TABLE history_bars(
                source_id TEXT NOT NULL, open_epoch INTEGER NOT NULL, end_epoch INTEGER NOT NULL,
                session_date TEXT NOT NULL, open REAL NOT NULL, high REAL NOT NULL,
                low REAL NOT NULL, close REAL NOT NULL, PRIMARY KEY(source_id, open_epoch));
            CREATE TABLE history_points(
                source_id TEXT NOT NULL, open_epoch INTEGER NOT NULL, end_epoch INTEGER NOT NULL,
                session_date TEXT NOT NULL, value REAL NOT NULL, PRIMARY KEY(source_id, open_epoch));
            CREATE TABLE history_invalid(
                source_id TEXT NOT NULL, open_epoch INTEGER NOT NULL, reason TEXT NOT NULL,
                PRIMARY KEY(source_id, open_epoch));
        """)
        con.commit()
        if wal:
            con.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    finally:
        con.close()


def _create_rates_db(path: Path, *, wal: bool = False) -> None:
    con = sqlite3.connect(path)
    try:
        if wal:
            con.execute("PRAGMA journal_mode=WAL")
        con.execute("""
            CREATE TABLE observations(
                family TEXT NOT NULL, series TEXT NOT NULL, observation_date TEXT NOT NULL,
                known_at TEXT NOT NULL, version TEXT PRIMARY KEY, payload TEXT NOT NULL)
        """)
        con.commit()
        if wal:
            con.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    finally:
        con.close()


# ---------------------------------------------------------------------------
# 1. Static AST / regex regression guard across live_contentops/ & scripts/
# ---------------------------------------------------------------------------

def test_static_zero_active_yahoo_scraper_endpoints_and_renderers():
    endpoint_re = re.compile(r"(?:query[12]\.finance\.yahoo\.com|finance\.yahoo\.com/v\d)", re.I)
    renderer_re = re.compile(r"Source:\s*Yahoo Finance", re.I)

    hits: list[str] = []
    for folder in (REPO_ROOT / "live_contentops", REPO_ROOT / "scripts"):
        for py in sorted(folder.rglob("*.py")):
            text = py.read_text(encoding="utf-8-sig")
            tree = ast.parse(text, filename=str(py))
            # Check string literals in AST so executable code has zero live Yahoo scraper URLs.
            for node in ast.walk(tree):
                if isinstance(node, ast.Constant) and isinstance(node.value, str):
                    if endpoint_re.search(node.value):
                        hits.append(f"{py.relative_to(REPO_ROOT)}:{node.lineno} endpoint={node.value!r}")
                    if renderer_re.search(node.value):
                        hits.append(f"{py.relative_to(REPO_ROOT)}:{node.lineno} renderer={node.value!r}")
    assert hits == [], f"Active Yahoo Finance endpoints/renderers remain: {hits}"

    # Verify runtime tables contain zero Yahoo providers or Yahoo reaction labels.
    assert all(spec[0] != "YAHOO" for spec in quotes.SYMBOLS.values())
    assert not any("YAHOO_FINANCE:" in k for k in cpi.LABELS)
    assert not any("YAHOO_FINANCE:" in k for k in event_reactions.SERIES)
    assert not any("yahoo" in v.casefold() for v in cpi.LABELS.values())
    assert not any("yahoo" in v.casefold() for v in event_reactions.SERIES.values())


def test_yahoo_http_and_retired_futures_proxies_fail_closed():
    for bad_url in (
        "https://query1.finance.yahoo.com/v8/finance/chart/ES=F",
        "https://query2.finance.yahoo.com/v1/finance/search?q=gold",
        "https://finance.yahoo.com/quote/%5EGSPC",
    ):
        with pytest.raises(quotes.QuoteError, match="CC024_YAHOO_HTTP_FORBIDDEN"):
            quotes.http_read(bad_url)

    for retired in ("US500_FUTURES", "GOLD_FUTURES", "USTEC_FUTURES"):
        assert retired not in quotes.SYMBOLS
        with pytest.raises(quotes.QuoteError, match="CC024_YAHOO_FUTURES_PROXY_RETIRED"):
            quotes.get(retired)
        with pytest.raises(quotes.QuoteError, match="CC024_YAHOO_FUTURES_PROXY_RETIRED"):
            quotes.source_url(retired)

    assert grounded.query_yahoo_finance("gold inflation") == []


# ---------------------------------------------------------------------------
# 2. Trap 1: 9x duplicate M15 bars deduplication + invalid_bars exclusion
# ---------------------------------------------------------------------------

def test_trap1_m15_bars_deduplication_and_invalid_bars_exclusion(tmp_path):
    db_path = tmp_path / "bars.sqlite3"
    _create_full_bars_db(db_path)
    now = _et(2026, 11, 27, 12, 0)
    bar_open = int((now - timedelta(minutes=16)).timestamp())

    with closing(sqlite3.connect(db_path)) as con, con:
        # Insert 9 duplicate captures for the same open_epoch (simulating ~9x live duplication).
        for i in range(9):
            sha = f"{i:064x}"
            close_val = 26000.0 + i * 10.0  # Capture #8 is newest valid (26080.0); #9 will be invalid (29999.0).
            con.execute(
                "INSERT INTO bars VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                ("USTEC", bar_open, close_val, close_val + 5, close_val - 5, close_val,
                 (now - timedelta(seconds=20 - i)).timestamp(), sha,
                 "NATIVE_BROKER_OHLC_UNADJUSTED_BASIS_NOT_EXCHANGE_LAST_OR_MID",
                 "EXNESS_DEMO:USTEC", "NATIVE_BROKER"),
            )
        # Insert a newer (higher known_epoch) corrupt capture that is flagged in invalid_bars.
        bad_sha = "f" * 64
        con.execute(
            "INSERT INTO bars VALUES(?,?,?,?,?,?,?,?,?,?,?)",
            ("USTEC", bar_open, 29999.0, 30000.0, 29990.0, 29999.0,
             (now - timedelta(seconds=1)).timestamp(), bad_sha,
             "NATIVE_BROKER_OHLC_UNADJUSTED_BASIS_NOT_EXCHANGE_LAST_OR_MID",
             "EXNESS_DEMO:USTEC", "NATIVE_BROKER"),
        )
        con.execute(
            "INSERT INTO invalid_bars VALUES(?,?,?,?)",
            (bad_sha, "USTEC", bar_open, "BAD_TICK_SPIKE"),
        )

    obs = quotes.get("USTEC", now=now, clock=lambda: now, bars_db=db_path, root=tmp_path / "pq")
    assert obs["value"] == 26080.0  # newest valid capture (#8), NOT invalid #9 (29999.0) or oldest #0 (26000.0)
    assert obs["source_symbol"] == "USTEC"


# ---------------------------------------------------------------------------
# 3. Trap 2: Mandatory M15 -> D1 rollup past 2026-11-22 + holiday/early-close + ATR14
# ---------------------------------------------------------------------------

def test_trap2_m15_to_d1_rollup_fills_paused_daily_route_with_holiday_and_early_close(tmp_path):
    db_path = tmp_path / "bars.sqlite3"
    _create_full_bars_db(db_path)

    # Seed 13 trading days of NATIVE_DAILY_ROUTE D1 ending Fri 2026-11-20 (simulating 2026-11-22 pause).
    d1_days = [
        date(2026, 11, 4), date(2026, 11, 5), date(2026, 11, 6),
        date(2026, 11, 9), date(2026, 11, 10), date(2026, 11, 11),
        date(2026, 11, 12), date(2026, 11, 13), date(2026, 11, 16),
        date(2026, 11, 17), date(2026, 11, 18), date(2026, 11, 19),
        date(2026, 11, 20),
    ]
    with closing(sqlite3.connect(db_path)) as con, con:
        con.execute(
            "INSERT INTO history_sources VALUES(?,?,?,?,?,?,?,?)",
            ("ndr-us500", "a" * 64, "ndr.json", "US500", "D1", "NATIVE_DAILY_ROUTE",
             _et(2026, 11, 22, 18, 0).timestamp(), json.dumps({"provider": "NATIVE_DAILY_ROUTE"})),
        )
        # Also insert a Yahoo D1 source with deliberately wrong prices to prove Yahoo is strictly ignored.
        con.execute(
            "INSERT INTO history_sources VALUES(?,?,?,?,?,?,?,?)",
            ("yf-us500", "b" * 64, "yf.json", "US500", "D1", "YAHOO_FINANCE:ES=F",
             _et(2026, 11, 28, 12, 0).timestamp(), json.dumps({"provider": "YAHOO_FINANCE_CHART"})),
        )
        for idx, d in enumerate(d1_days):
            ep = int(_et(d.year, d.month, d.day, 16, 0).timestamp())
            base = 7000.0 + idx * 10.0
            con.execute(
                "INSERT INTO history_bars VALUES(?,?,?,?,?,?,?,?)",
                ("ndr-us500", ep - 86400, ep, d.isoformat(), base, base + 20.0, base - 20.0, base + 5.0),
            )
            con.execute(
                "INSERT INTO history_bars VALUES(?,?,?,?,?,?,?,?)",
                ("yf-us500", ep - 86400, ep, d.isoformat(), 9999.0, 9999.0, 9999.0, 9999.0),
            )

        # Seed M15 NATIVE_BROKER bars for Mon 23, Tue 24, Wed 25, Thu 26 (Thanksgiving CLOSED!), Fri 27 (early 13:00 ET).
        def add_m15(dt_et: datetime, high: float, low: float, close: float, dup_count: int = 3):
            op = int(dt_et.timestamp())
            for k in range(dup_count):
                con.execute(
                    "INSERT INTO bars VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                    ("US500", op, close, high, low, close, (dt_et + timedelta(minutes=15, seconds=k)).timestamp(),
                     f"{op:x}-{k}", "NATIVE_BROKER_OHLC_UNADJUSTED_BASIS_NOT_EXCHANGE_LAST_OR_MID",
                     "EXNESS_DEMO:US500", "NATIVE_BROKER"),
                )

        # Mon 23 Nov, Tue 24 Nov, Wed 25 Nov (regular 09:30-16:00 ET sessions)
        for d, close in ((date(2026, 11, 23), 7140.0), (date(2026, 11, 24), 7160.0), (date(2026, 11, 25), 7180.0)):
            add_m15(_et(d.year, d.month, d.day, 9, 30), close + 15.0, close - 15.0, close - 5.0)
            add_m15(_et(d.year, d.month, d.day, 15, 45), close + 10.0, close - 10.0, close)
        # Thu 26 Nov Thanksgiving (CLOSED US cash session): CFD bars must NOT produce a US500 D1 session!
        add_m15(_et(2026, 11, 26, 10, 0), 7999.0, 7900.0, 7950.0)
        # Fri 27 Nov Black Friday (early close 13:00 ET): 12:45 bar is the true close (7220.0);
        # 14:30 ET post-close CFD spike (7499.0) MUST be excluded!
        add_m15(_et(2026, 11, 27, 9, 30), 7230.0, 7190.0, 7205.0)
        add_m15(_et(2026, 11, 27, 12, 45), 7225.0, 7200.0, 7220.0)
        add_m15(_et(2026, 11, 27, 14, 30), 7499.0, 7400.0, 7480.0)

    sunday = _et(2026, 11, 29, 10, 0)
    bars, meta = wrap_sources.market_history(
        "US500", [date(2026, 11, 20), date(2026, 11, 27)],
        as_of=sunday, db_path=db_path, cash_calendar=US_CAL_2026,
    )
    assert date(2026, 11, 26) not in bars  # Thanksgiving closed excluded
    assert bars[date(2026, 11, 20)] == (7140.0, 7100.0, 7125.0)  # NATIVE_DAILY_ROUTE, NOT Yahoo 9999.0
    assert bars[date(2026, 11, 25)] == (7195.0, 7165.0, 7180.0)
    assert bars[date(2026, 11, 27)] == (7230.0, 7190.0, 7220.0)  # Black Friday 13:00 ET close, NOT 7480.0 CFD drift
    assert "2026-11-27" in meta["m15_rolled_up_days"]
    assert "YAHOO" not in json.dumps(meta).upper()
    atr = wrap_sources.normal_day(bars, date(2026, 11, 27))
    assert atr is not None and atr > 0


# ---------------------------------------------------------------------------
# 4. Trap 3: USTEC fresh via M15 LOCAL_BARS without plan-status or M1 history_bars
# ---------------------------------------------------------------------------

def test_trap3_ustec_resolves_freshly_via_m15_without_plan_status_or_m1(tmp_path):
    db_path = tmp_path / "bars.sqlite3"
    _create_full_bars_db(db_path)
    now = _et(2026, 11, 27, 11, 0)
    with closing(sqlite3.connect(db_path)) as con, con:
        con.execute(
            "INSERT INTO bars VALUES(?,?,?,?,?,?,?,?,?,?,?)",
            ("USTEC", int(now.timestamp()) - 900, 26700.0, 26750.0, 26680.0, 26720.0,
             now.timestamp(), "u" * 64, "NATIVE_BROKER_OHLC_UNADJUSTED_BASIS_NOT_EXCHANGE_LAST_OR_MID",
             "EXNESS_DEMO:USTEC", "NATIVE_BROKER"),
        )
    obs = quotes.get("USTEC", now=now, clock=lambda: now, bars_db=db_path, root=tmp_path / "pq")
    assert obs["value"] == 26720.0 and obs["source_symbol"] == "USTEC" and obs["source_url"] is None


# ---------------------------------------------------------------------------
# 5. Trap 4: US2Y/US10Y Treasury XML + history_points fallback + business-day freshness
# ---------------------------------------------------------------------------

def test_trap4_us_treasury_business_day_freshness_and_history_points_fallback(tmp_path):
    rates_db = tmp_path / "observations.sqlite3"
    bars_db = tmp_path / "bars.sqlite3"
    _create_rates_db(rates_db)
    _create_full_bars_db(bars_db)
    cal_path = tmp_path / "us_cal.json"
    cal_path.write_text(json.dumps(US_CAL_2026), encoding="utf-8")

    # Seed Wed 2026-11-25 & Tue 2026-11-24 Treasury yields (Thu 26 Nov = Thanksgiving).
    url = "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/pages/xml?data=daily_treasury_yield_curve"
    known = _et(2026, 11, 26, 3, 13)
    with closing(sqlite3.connect(rates_db)) as con, con:
        for day, val in (("2026-11-25", 4.85), ("2026-11-24", 4.91)):
            payload = {"store_available_at_utc": known.isoformat(), "record": {
                "alias": "US10Y", "value": val, "unit": "percent", "reference_period": day,
                "official_url": url, "rights": {"attribution": "U.S. Department of the Treasury"},
            }}
            con.execute("INSERT INTO observations VALUES(?,?,?,?,?,?)",
                        ("direct_rates", "US10Y", day, known.isoformat(), f"v-{day}", json.dumps(payload)))

    # On Sat 2026-11-28: only 1 US trading day (Fri Nov 27) since Wed Nov 25 -> FRESH (<= 2 trading days).
    sat = _et(2026, 11, 28, 9, 0)
    obs = quotes.get("US10Y", now=sat, clock=lambda: sat, rates_db=rates_db, bars_db=bars_db,
                     cash_calendar=cal_path, root=tmp_path / "pq1")
    assert obs["value"] == 4.85 and obs["prior_close"] == 4.91
    assert obs["day_change"] == pytest.approx(-0.06)
    assert obs["source"] == "U.S. Department of the Treasury"
    assert obs["freshness_basis"] == "US_BUSINESS_DAYS"

    # On Wed 2026-12-02: trading days since Nov 25 = Nov 27, Nov 30, Dec 1, Dec 2 (4 > 2) -> STALE!
    wed_next = _et(2026, 12, 2, 12, 0)
    with pytest.raises(quotes.QuoteError, match="PUBLIC_QUOTE_STALE"):
        quotes.get("US10Y", now=wed_next, clock=lambda: wed_next, rates_db=rates_db, bars_db=bars_db,
                   cash_calendar=cal_path, root=tmp_path / "pq2")

    # Fallback: when observations.sqlite3 is absent, US2Y resolves from bars.sqlite3 history_points.
    with closing(sqlite3.connect(bars_db)) as con, con:
        con.execute("INSERT INTO history_sources VALUES(?,?,?,?,?,?,?,?)",
                    ("tr-2y", "t" * 64, "tr.json", "US2Y", "D1", "US_TREASURY:BC_2YEAR",
                     known.timestamp(), json.dumps({"unit": "percent"})))
        con.execute("INSERT INTO history_points VALUES(?,?,?,?,?)",
                    ("tr-2y", int(_et(2026, 11, 24, 16, 0).timestamp()), int(_et(2026, 11, 25, 16, 0).timestamp()),
                     "2026-11-25", 4.61))
    obs_2y = quotes.get("US2Y", now=sat, clock=lambda: sat, rates_db=tmp_path / "missing-obs.sqlite3",
                        bars_db=bars_db, cash_calendar=cal_path, root=tmp_path / "pq3")
    assert obs_2y["value"] == 4.61 and obs_2y["source"] == "U.S. Department of the Treasury"


# ---------------------------------------------------------------------------
# 6. Trap 5: DXY & BRENT (UKOIL) Option C — fail closed when stale, CNBC default-off
# ---------------------------------------------------------------------------

def test_trap5_dxy_and_brent_option_c_fail_closed_when_stale_and_no_unguarded_cnbc(tmp_path):
    db_path = tmp_path / "bars.sqlite3"
    _create_full_bars_db(db_path)
    stale_end = _et(2026, 11, 22, 17, 0)
    now = _et(2026, 11, 28, 10, 0)

    with closing(sqlite3.connect(db_path)) as con, con:
        for sym, val in (("DXY", 106.5), ("UKOIL", 74.2)):
            con.execute("INSERT INTO history_sources VALUES(?,?,?,?,?,?,?,?)",
                        (f"ndr-{sym}", "s" * 64, f"{sym}.json", sym, "D1", "NATIVE_DAILY_ROUTE",
                         stale_end.timestamp(), json.dumps({"provider": "NATIVE_DAILY_ROUTE"})))
            con.execute("INSERT INTO history_bars VALUES(?,?,?,?,?,?,?,?)",
                        (f"ndr-{sym}", int(stale_end.timestamp()) - 86400, int(stale_end.timestamp()),
                         "2026-11-22", val, val + 1, val - 1, val))

    http_calls = []

    def fail_if_called(url):
        http_calls.append(url)
        pytest.fail(f"Unexpected HTTP call under Option C default: {url}")

    # Default allow_cnbc_dxy_fallback=False: DXY & BRENT read LOCAL_BARS and fail closed PUBLIC_QUOTE_STALE.
    assert quotes.source_url("DXY") is None
    assert quotes.source_url("BRENT") is None
    with pytest.raises(quotes.QuoteError, match="PUBLIC_QUOTE_STALE"):
        quotes.get("DXY", now=now, clock=lambda: now, bars_db=db_path, reader=fail_if_called, root=tmp_path / "pq-dxy")
    with pytest.raises(quotes.QuoteError, match="PUBLIC_QUOTE_STALE"):
        quotes.get("BRENT", now=now, clock=lambda: now, bars_db=db_path, reader=fail_if_called, root=tmp_path / "pq-brent")
    assert http_calls == []

    # Opt-in allow_cnbc_dxy_fallback=True explicitly activates CNBC .DXY only for DXY.
    cnbc_url = quotes.source_url("DXY", allow_cnbc_dxy_fallback=True)
    assert cnbc_url and "quote.cnbc.com" in cnbc_url and ".DXY" in cnbc_url
    raw_cnbc = json.dumps({"QuickQuoteResult": {"QuickQuote": [{
        "symbol": ".DXY", "code": "0", "last": "106.8", "previous_day_closing": "106.5",
        "last_time": now.isoformat(), "assetType": "INDEX",
    }]}}).encode("utf-8")
    opt_in = quotes.get("DXY", now=now, clock=lambda: now, reader=lambda _u: raw_cnbc,
                        allow_cnbc_dxy_fallback=True, root=tmp_path / "pq-dxy-opt")
    assert opt_in["value"] == 106.8 and opt_in["source"] == "CNBC"


# ---------------------------------------------------------------------------
# 7. Trap 6: Reaction-table Yahoo filters, empty USOIL/USTEC buckets, 0 "CFD" leaks
# ---------------------------------------------------------------------------

def test_trap6_reaction_tables_filter_yahoo_handle_empty_buckets_and_zero_cfd_leaks(tmp_path):
    # (a) cpi_reaction_page_v1: filters Yahoo rows, omits Yahoo-only USOIL table cleanly, maps CC_HELD_CFD:* & USATECH
    body = (
        "## Gold\n\n"
        "| Release | Market | Series | +5m |\n|---|---|---|---:|\n"
        "| 2024-01-11 | XAUUSD | CC_HELD_CFD:XAUUSD | -0.25% |\n"
        "| 2024-02-13 | USTEC | DUKASCOPY:USATECH.IDX/USD | +0.40% |\n"
        "| 2024-03-12 | US500 | YAHOO_FINANCE:ES=F | +0.10% |\n\n"
        "## WTI oil\n\n"
        "| Release | Market | Series | +5m |\n|---|---|---|---:|\n"
        "| 2024-01-11 | USOIL | YAHOO_FINANCE:CL=F | +0.30% |\n"
    )
    rec = {"binding": {
        "record_id": cpi.RECORD_ID, "export_bytes_sha256": "a" * 64,
        "fields": [{"field_path": "/sections/reaction-tables/body_markdown", "citation": "c#1", "value": body}],
    }}
    proj = cpi.record_projection(rec)
    assert proj["cc024_yahoo_rows_excluded"] == 2
    assert len(proj["tables"]) == 1  # Yahoo-only USOIL table omitted cleanly, no crash
    md = proj["tables"][0]["markdown"]
    assert "Capital Chronicle held gold price proxy" in md
    assert "Dukascopy Nasdaq 100 index" in md
    assert "CFD" not in md and "yahoo" not in md.casefold()

    # (b) event_reaction_source_v1: filters Yahoo rows, handles empty USOIL/USTEC & empty family gracefully
    windows = {h: {"move_bps": 10.0, "missing_reason": None} for h in event_reactions.HORIZONS}
    table = {
        "schema": "EventWeightDecayTableV1",
        "as_of_utc": "2026-11-27T12:00:00Z",
        "events": [{"event_id": "nfp-1", "family": "NFP", "event_date": "2026-11-06"}],
        "rows": [
            {"event_id": "nfp-1", "family": "NFP", "symbol": "XAUUSD", "series_id": "CC_HELD_CFD:XAUUSD",
             "released_at_utc": "2026-11-06T13:30:00Z", "price_basis": "BID", "windows": windows},
            {"event_id": "nfp-1", "family": "NFP", "symbol": "USTEC", "series_id": "DUKASCOPY:USATECH.IDX/USD",
             "released_at_utc": "2026-11-06T13:30:00Z", "price_basis": "BID", "windows": windows},
            {"event_id": "nfp-1", "family": "NFP", "symbol": "USOIL", "series_id": "YAHOO_FINANCE:CL=F",
             "released_at_utc": "2026-11-06T13:30:00Z", "price_basis": "YAHOO_UNADJUSTED_CHART_OHLC:CL=F", "windows": windows},
            {"event_id": "nfp-1", "family": "NFP", "symbol": "EURUSD", "series_id": "YAHOO_FINANCE:EURUSD=X",
             "released_at_utc": "2026-11-06T13:30:00Z", "price_basis": "BID", "windows": windows},
        ],
    }
    ev_proj = event_reactions.project(table, "NFP")
    assert ev_proj["cc024_yahoo_rows_excluded"] == 2
    assert ev_proj["market_rows"] == 2
    assert "Capital Chronicle held gold price proxy" in ev_proj["body_markdown"]
    assert "Dukascopy Nasdaq 100 index" in ev_proj["body_markdown"]
    assert "CFD" not in ev_proj["body_markdown"] and "yahoo" not in ev_proj["body_markdown"].casefold()

    # Every CC_HELD_CFD:* core market label must contain zero "CFD".
    for mkt in event_reactions.MARKETS:
        lbl = event_reactions.SERIES[f"CC_HELD_CFD:{mkt}"]
        assert "CFD" not in lbl and "cfd" not in lbl.casefold()

    # Empty PPI family (0 rows) still renders cleanly without crashing.
    empty_proj = event_reactions.project(table, "PPI")
    assert empty_proj["market_rows"] == 0 and "| 0 | 0 | 0 |" in empty_proj["body_markdown"]

    # (c) x_reply_fact_sources_v1 refuses YAHOO_FINANCE:* in _bar_source and skips Yahoo in _reaction_sources
    pub_json = tmp_path / "publisher.json"
    pub_json.write_text(json.dumps({
        "as_of_utc": "2026-11-27T12:00:00Z",
        "summary": [
            {"symbol": "USOIL", "series_id": "YAHOO_FINANCE:CL=F", "price_basis": "YAHOO_UNADJUSTED_CHART_OHLC:CL=F",
             "window": "5m", "positive_n": 3, "n": 5, "release_dates": ["2026-01-10", "2026-02-10", "2026-03-10", "2026-04-10", "2026-05-10"],
             "measure": "CPI_CORE_MOM", "bucket": "HOT", "consensus_source": "held"},
            {"symbol": "XAUUSD", "series_id": "CC_HELD_CFD:XAUUSD", "price_basis": "BID",
             "window": "5m", "positive_n": 2, "n": 3, "release_dates": ["2026-01-10", "2026-02-10", "2026-03-10"],
             "measure": "CPI_CORE_MOM", "bucket": "HOT", "consensus_source": "held"},
        ],
    }), encoding="utf-8")
    r_sources = reply_facts._reaction_sources(pub_json, through_date="2026-11-26")
    assert len(r_sources) == 1
    assert "Yahoo" not in r_sources[0]["excerpt"] and "CFD" not in r_sources[0]["excerpt"]

    # _bar_source directly refuses YAHOO_FINANCE:*
    bars_db = tmp_path / "bars.sqlite3"
    _create_full_bars_db(bars_db)
    with closing(sqlite3.connect(bars_db)) as con, con:
        con.execute("INSERT INTO history_sources VALUES(?,?,?,?,?,?,?,?)",
                    ("yf-src", "y" * 64, "y.json", "US500", "M1", "YAHOO_FINANCE:ES=F",
                     _et(2026, 11, 27, 10, 0).timestamp(), "{}"))
        con.execute("INSERT INTO history_bars VALUES(?,?,?,?,?,?,?,?)",
                    ("yf-src", 1700000000, 1700000060, "2026-11-27", 7000, 7001, 6999, 7000))
    with reply_facts._connect(bars_db) as con:
        with pytest.raises(ValueError, match="CC024_YAHOO_PUBLIC_SERIES_PROHIBITED"):
            reply_facts._bar_source(con, {"kind": "history_bar", "path": str(bars_db),
                                          "source_id": "yf-src", "open_epoch": 1700000000})


# ---------------------------------------------------------------------------
# 8. Mandatory SQLite WAL Zero-Write Compliance (B12C37-M1 / CC754-H1)
# ---------------------------------------------------------------------------

def test_wal_zero_write_compliance_creates_zero_wal_or_shm_sidecars(tmp_path):
    """Reading WAL-mode bars.sqlite3 and observations.sqlite3 creates 0 -wal/-shm files and 0-byte mutation."""
    intake = tmp_path / "intake"
    bars_db = intake / "completed-bars" / "bars.sqlite3"
    rates_db = intake / "rates-implied" / "observations.sqlite3"
    bars_db.parent.mkdir(parents=True)
    rates_db.parent.mkdir(parents=True)

    _create_full_bars_db(bars_db, wal=True)
    _create_rates_db(rates_db, wal=True)
    now = _et(2026, 11, 27, 12, 0)

    # Populate both WAL DBs, then checkpoint+truncate and close writer so no -wal/-shm exist.
    with closing(sqlite3.connect(bars_db)) as con:
        con.execute("INSERT INTO bars VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                    ("US500", int(now.timestamp()) - 900, 7200.0, 7210.0, 7190.0, 7205.0,
                     now.timestamp(), "a" * 64, "NATIVE_BROKER_OHLC_UNADJUSTED_BASIS_NOT_EXCHANGE_LAST_OR_MID",
                     "EXNESS_DEMO:US500", "NATIVE_BROKER"))
        con.execute("INSERT INTO history_sources VALUES(?,?,?,?,?,?,?,?)",
                    ("m1-us500", "b" * 64, "m1.json", "US500", "M1", "NATIVE_BROKER",
                     now.timestamp(), json.dumps({"source_instrument": "US500", "contract_id": "EXNESS_DEMO:US500"})))
        con.execute("INSERT INTO history_bars VALUES(?,?,?,?,?,?,?,?)",
                    ("m1-us500", int(now.timestamp()) - 60, int(now.timestamp()), "2026-11-27",
                     7200.0, 7210.0, 7190.0, 7205.0))
        con.execute("INSERT INTO history_sources VALUES(?,?,?,?,?,?,?,?)",
                    ("d1-us500", "c" * 64, "d1.json", "US500", "D1", "NATIVE_DAILY_ROUTE",
                     now.timestamp(), json.dumps({"provider": "NATIVE_DAILY_ROUTE"})))
        con.execute("INSERT INTO history_bars VALUES(?,?,?,?,?,?,?,?)",
                    ("d1-us500", int(_et(2026, 11, 24, 16, 0).timestamp()), int(_et(2026, 11, 25, 16, 0).timestamp()),
                     "2026-11-25", 7180.0, 7195.0, 7165.0, 7190.0))
        con.commit()
        con.execute("PRAGMA wal_checkpoint(TRUNCATE)")

    with closing(sqlite3.connect(rates_db)) as con:
        payload = {"store_available_at_utc": now.isoformat(), "record": {
            "alias": "US10Y", "value": 4.85, "unit": "percent", "reference_period": "2026-11-25",
            "official_url": "https://home.treasury.gov/data",
            "rights": {"attribution": "U.S. Department of the Treasury"},
        }}
        con.execute("INSERT INTO observations VALUES(?,?,?,?,?,?)",
                    ("direct_rates", "US10Y", "2026-11-25", now.isoformat(), "v1", json.dumps(payload)))
        con.commit()
        con.execute("PRAGMA wal_checkpoint(TRUNCATE)")

    # Remove any lingering empty -wal/-shm from writer close to verify read paths create ZERO sidecars.
    for db in (bars_db, rates_db):
        for suffix in ("-wal", "-shm"):
            sidecar = db.with_name(db.name + suffix)
            if sidecar.exists():
                sidecar.unlink()
        assert not db.with_name(db.name + "-wal").exists()
        assert not db.with_name(db.name + "-shm").exists()

    before = {
        db: (db.stat().st_size, db.stat().st_mtime_ns, sha256(db.read_bytes()).hexdigest())
        for db in (bars_db, rates_db)
    }

    # Exercise ALL 4 touched read-only SQLite consumers against the WAL-mode DBs!
    q_bar = quotes.get("US500", now=now, clock=lambda: now, bars_db=bars_db, root=tmp_path / "pq-wal")
    assert q_bar["value"] == 7205.0
    q_rate = quotes.get("US10Y", now=now, clock=lambda: now, rates_db=rates_db, bars_db=bars_db, root=tmp_path / "pq-wal")
    assert q_rate["value"] == 4.85
    w_bars, _ = wrap_sources.market_history("US500", [date(2026, 11, 25)], as_of=now, db_path=bars_db, cash_calendar=US_CAL_2026)
    assert w_bars[date(2026, 11, 25)][2] == 7190.0
    ref = chart_prices.bar_store_quote("US500", now, bars_db)
    assert ref["price"] == 7205.0
    f_sources, _ = reply_facts.load(now=now, root=intake)
    assert f_sources

    # Assert ZERO -wal/-shm files were created AND exact 0-byte / 0-mtime mutation on both DB files!
    for db in (bars_db, rates_db):
        assert not db.with_name(db.name + "-wal").exists(), f"-wal created on read of {db.name}"
        assert not db.with_name(db.name + "-shm").exists(), f"-shm created on read of {db.name}"
        after = (db.stat().st_size, db.stat().st_mtime_ns, sha256(db.read_bytes()).hexdigest())
        assert after == before[db], f"DB mutated on read of {db.name}"


def test_wal_aware_ro_reads_live_uncheckpointed_wal_frames_and_supports_zero_write_snapshot(tmp_path):
    """Actively written WAL DBs (wal_bytes > 0) serve 100% fresh uncheckpointed WAL rows AND zero_write=True mutates 0 bytes."""
    intake = tmp_path / "live-intake"
    bars_db = intake / "completed-bars" / "bars.sqlite3"
    rates_db = intake / "rates-implied" / "observations.sqlite3"
    bars_db.parent.mkdir(parents=True)
    rates_db.parent.mkdir(parents=True)

    _create_full_bars_db(bars_db, wal=True)
    _create_rates_db(rates_db, wal=True)
    t_old = _et(2026, 11, 27, 11, 0)
    t_new = _et(2026, 11, 27, 12, 0)

    # Seed baseline rows and checkpoint to main DB file.
    with closing(sqlite3.connect(bars_db)) as con:
        con.execute("INSERT INTO bars VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                    ("US500", int(t_old.timestamp()) - 900, 7100.0, 7110.0, 7090.0, 7100.0,
                     t_old.timestamp(), "1" * 64, "NATIVE_BROKER_OHLC_UNADJUSTED_BASIS_NOT_EXCHANGE_LAST_OR_MID",
                     "EXNESS_DEMO:US500", "NATIVE_BROKER"))
        con.execute("INSERT INTO history_sources VALUES(?,?,?,?,?,?,?,?)",
                    ("m1-old", "2" * 64, "m1.json", "US500", "M1", "NATIVE_BROKER",
                     t_old.timestamp(), json.dumps({"source_instrument": "US500", "contract_id": "EXNESS_DEMO:US500"})))
        con.execute("INSERT INTO history_bars VALUES(?,?,?,?,?,?,?,?)",
                    ("m1-old", int(t_old.timestamp()) - 60, int(t_old.timestamp()), "2026-11-27",
                     7100.0, 7105.0, 7095.0, 7100.0))
        con.commit()
        con.execute("PRAGMA wal_checkpoint(TRUNCATE)")

    with closing(sqlite3.connect(rates_db)) as con:
        old_payload = {"store_available_at_utc": t_old.isoformat(), "record": {
            "alias": "US10Y", "value": 4.80, "unit": "percent", "reference_period": "2026-11-24",
            "official_url": "https://home.treasury.gov/data",
            "rights": {"attribution": "U.S. Department of the Treasury"},
        }}
        con.execute("INSERT INTO observations VALUES(?,?,?,?,?,?)",
                    ("direct_rates", "US10Y", "2026-11-24", t_old.isoformat(), "v-old", json.dumps(old_payload)))
        con.commit()
        con.execute("PRAGMA wal_checkpoint(TRUNCATE)")

    # Keep active writer connections open with wal_autocheckpoint=0 and commit NEW rows ONLY into -wal!
    w_bars = sqlite3.connect(bars_db)
    w_rates = sqlite3.connect(rates_db)
    try:
        w_bars.execute("PRAGMA wal_autocheckpoint=0")
        w_bars.execute("INSERT INTO bars VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                       ("US500", int(t_new.timestamp()) - 900, 7350.0, 7360.0, 7340.0, 7355.55,
                        t_new.timestamp(), "3" * 64, "NATIVE_BROKER_OHLC_UNADJUSTED_BASIS_NOT_EXCHANGE_LAST_OR_MID",
                        "EXNESS_DEMO:US500", "NATIVE_BROKER"))
        w_bars.execute("INSERT INTO history_sources VALUES(?,?,?,?,?,?,?,?)",
                       ("m1-new", "4" * 64, "m1-new.json", "US500", "M1", "NATIVE_BROKER",
                        t_new.timestamp(), json.dumps({"source_instrument": "US500", "contract_id": "EXNESS_DEMO:US500"})))
        w_bars.execute("INSERT INTO history_bars VALUES(?,?,?,?,?,?,?,?)",
                       ("m1-new", int(t_new.timestamp()) - 60, int(t_new.timestamp()), "2026-11-27",
                        7350.0, 7360.0, 7345.0, 7355.55))
        w_bars.commit()

        w_rates.execute("PRAGMA wal_autocheckpoint=0")
        new_payload = {"store_available_at_utc": t_new.isoformat(), "record": {
            "alias": "US10Y", "value": 4.99, "unit": "percent", "reference_period": "2026-11-25",
            "official_url": "https://home.treasury.gov/data",
            "rights": {"attribution": "U.S. Department of the Treasury"},
        }}
        w_rates.execute("INSERT INTO observations VALUES(?,?,?,?,?,?)",
                        ("direct_rates", "US10Y", "2026-11-25", t_new.isoformat(), "v-new", json.dumps(new_payload)))
        w_rates.commit()

        # Verify uncheckpointed -wal files actually exist with wal_bytes > 0!
        bars_wal = bars_db.with_name(bars_db.name + "-wal")
        rates_wal = rates_db.with_name(rates_db.name + "-wal")
        assert bars_wal.is_file() and bars_wal.stat().st_size > 0
        assert rates_wal.is_file() and rates_wal.stat().st_size > 0

        # 1) Audit zero_write=True path: MUST see fresh uncheckpointed -wal rows with 0-byte / 0-mtime mutation!
        tracked = [bars_db, bars_wal, rates_db, rates_wal]
        for db in (bars_db, rates_db):
            shm = db.with_name(db.name + "-shm")
            if shm.is_file():
                tracked.append(shm)
        before_zw = {
            p: (p.stat().st_size, p.stat().st_mtime_ns, sha256(p.read_bytes()).hexdigest())
            for p in tracked
        }
        q_zw_bar = quotes.get("US500", now=t_new, clock=lambda: t_new, bars_db=bars_db,
                              root=tmp_path / "pq-zw", zero_write=True)
        assert q_zw_bar["value"] == 7355.55
        q_zw_rate = quotes.get("US10Y", now=t_new, clock=lambda: t_new, rates_db=rates_db,
                               bars_db=bars_db, root=tmp_path / "pq-zw", zero_write=True)
        assert q_zw_rate["value"] == 4.99
        ref_zw = chart_prices.bar_store_quote("US500", t_new, bars_db, zero_write=True)
        assert ref_zw["price"] == 7355.55
        f_zw, _ = reply_facts.load(now=t_new, root=intake, zero_write=True)
        assert any("7355.55" in s["excerpt"] for s in f_zw)
        assert any("4.99 percent" in s["excerpt"] for s in f_zw)
        # RES-4 compliance check: zero "CFD" or "Exness" anywhere in emitted reply fact excerpts!
        for s in f_zw:
            assert "CFD" not in s["excerpt"] and "Exness" not in s["excerpt"], s["excerpt"]
            assert all("Exness" not in str(a) for a in s.get("source_attribution", []))

        for p in tracked:
            after_zw = (p.stat().st_size, p.stat().st_mtime_ns, sha256(p.read_bytes()).hexdigest())
            assert after_zw == before_zw[p], f"zero_write=True mutated {p.name}"

        # 2) Live fast path (zero_write=False): MUST also see 100% of fresh uncheckpointed -wal rows!
        q_live_bar = quotes.get("US500", now=t_new, clock=lambda: t_new, bars_db=bars_db,
                                root=tmp_path / "pq-live", zero_write=False)
        assert q_live_bar["value"] == 7355.55
        q_live_rate = quotes.get("US10Y", now=t_new, clock=lambda: t_new, rates_db=rates_db,
                                 bars_db=bars_db, root=tmp_path / "pq-live", zero_write=False)
        assert q_live_rate["value"] == 4.99
        ref_live = chart_prices.bar_store_quote("US500", t_new, bars_db, zero_write=False)
        assert ref_live["price"] == 7355.55
        # Verify M15 -> D1 rollup also reads uncheckpointed -wal bars!
        w_live, _ = wrap_sources.market_history(
            "US500", [date(2026, 11, 27)], as_of=_et(2026, 11, 27, 14, 0),
            db_path=bars_db, cash_calendar=US_CAL_2026, zero_write=False,
        )
        assert w_live[date(2026, 11, 27)][2] == 7355.55
    finally:
        w_bars.close()
        w_rates.close()


def test_wrap_chart_uses_clean_attribution_without_yahoo(tmp_path):
    from live_contentops.market_wrap_sources_v1 import slot_at, utc
    now = utc("2026-11-23T13:00Z")
    pack = {
        "slot": slot_at(now, US_CAL_2026),
        "market_close_date": "2026-11-20",
    }
    asset = wrap_editorial.chart_for(pack, {}, tmp_path)
    assert Path(asset["path"]).is_file()
    assert "yahoo" not in json.dumps(asset).casefold()
