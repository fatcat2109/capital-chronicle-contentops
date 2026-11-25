"""Hermetic US holiday & early-close session clock tests for CC-463 / CC-489 / CC-778.

Covers read-only us_session_calendar_v1.json awareness in:
- live_contentops/publication_image_contract_v1.py (comparison_clock / bind_scale / validate_scale)
- live_contentops/call_followups_v1.py (CASH_SESSIONS / cash_session_open_for_bar / move_chart_request)

Zero live writes, zero network/browser calls, zero agy invocations, zero .stop mutations.
"""
from __future__ import annotations

from contextlib import closing
from datetime import date, datetime, time, timedelta, timezone
from hashlib import sha256
import json
from pathlib import Path
import sqlite3

import pytest

from live_contentops import call_followups_v1 as followups
from live_contentops import chart_price_reference_v1 as prices
from live_contentops import public_market_quote_v1 as public_quotes
from live_contentops import publication_image_contract_v1 as contract
from live_contentops import tradingview_snapshot_v1 as tv
from live_contentops.published_images_v1 import SCHEMA as IMAGE_SCHEMA
from scripts.audit_chart_prices_cc489 import audit as audit_chart_prices


US_CALENDAR_2026_2028 = {
    "schema": "IbkrUsSessionCalendarV1",
    "source_url": "https://www.nyse.com/trade/hours-calendars",
    "observed_at_utc": "2026-11-17T18:25:46Z",
    "years": {
        "2026": {
            "closed": [
                "2026-01-01", "2026-01-19", "2026-02-16", "2026-04-03", "2026-05-25",
                "2026-06-19", "2026-07-03", "2026-09-07", "2026-11-26", "2026-12-25",
            ],
            "early_close_13_et": ["2026-11-27", "2026-12-24"],
        },
        "2027": {
            "closed": [
                "2027-01-01", "2027-01-18", "2027-02-15", "2027-03-26", "2027-05-31",
                "2027-06-18", "2027-07-05", "2027-09-06", "2027-11-25", "2027-12-24",
            ],
            "early_close_13_et": ["2027-11-26"],
        },
        "2028": {
            "closed": [
                "2028-01-17", "2028-02-21", "2028-04-14", "2028-05-29", "2028-06-19",
                "2028-07-04", "2028-09-04", "2028-11-23", "2028-12-25",
            ],
            "early_close_13_et": ["2028-07-03", "2028-11-24"],
        },
    },
}


def _et(year: int, month: int, day: int, hour: int, minute: int = 0, second: int = 0) -> datetime:
    return datetime(year, month, day, hour, minute, second, tzinfo=contract.ET).astimezone(timezone.utc)


def _write_calendar(path: Path, payload: dict | str = US_CALENDAR_2026_2028) -> Path:
    text = payload if isinstance(payload, str) else json.dumps(payload, indent=2)
    path.write_text(text, encoding="utf-8")
    return path


def _yahoo_json(symbol: str, value: float, at: datetime, *, prior: float = 100.0) -> bytes:
    return json.dumps({
        "chart": {
            "result": [{
                "meta": {
                    "symbol": symbol,
                    "regularMarketPrice": value,
                    "regularMarketTime": at.timestamp(),
                    "previousClose": prior,
                    "instrumentType": "INDEX",
                }
            }]
        }
    }).encode("utf-8")


def _export_price(path: Path, market: str, price: float, at: datetime, *, generated_at: datetime) -> None:
    row = {"asset_id": market, "last_price": price, "last_price_at_utc": at.isoformat()}
    body = {"schema": "CapitalChroniclePlanStatusV1", "generated_at_utc": generated_at.isoformat(), "plans": [row]}
    body["content_hash"] = sha256(prices._canonical(body)).hexdigest()
    path.write_text(json.dumps(body), encoding="utf-8")


def _init_bar_store(path: Path) -> None:
    with closing(sqlite3.connect(path)) as db, db:
        db.executescript("""
            CREATE TABLE history_sources(source_id TEXT PRIMARY KEY, source_sha256 TEXT,
                path TEXT, market TEXT, timeframe TEXT, series_id TEXT, known_epoch REAL, metadata_json TEXT);
            CREATE TABLE history_bars(source_id TEXT, open_epoch INTEGER, end_epoch INTEGER,
                session_date TEXT, open REAL, high REAL, low REAL, close REAL,
                PRIMARY KEY(source_id, open_epoch));
            CREATE TABLE history_invalid(source_id TEXT, open_epoch INTEGER, reason TEXT);
        """)


def _insert_m1_bar(path: Path, market: str, price: float, end: datetime, known: datetime, sid: str) -> None:
    meta = {"source_instrument": market, "contract_id": f"EXNESS_DEMO:{market}"}
    with closing(sqlite3.connect(path)) as db, db:
        db.execute(
            "INSERT INTO history_sources VALUES(?,?,?,?,?,?,?,?)",
            (sid, "b" * 64, "held-capture.json", market, "M1", "NATIVE_BROKER", known.timestamp(), json.dumps(meta)),
        )
        db.execute(
            "INSERT INTO history_bars VALUES(?,?,?,?,?,?,?,?)",
            (sid, int(end.timestamp()) - 60, int(end.timestamp()), end.date().isoformat(),
             price, price + 1, price - 1, price),
        )


def _followup_row(symbol: str, published: datetime, resolved: datetime) -> dict:
    return {
        "key": f"cc603-followup-{symbol.lower()}-holiday-test",
        "kind": "call_followup",
        "symbol": symbol,
        "cc603_destinations": ["telegram", "discord"],
        "candidate": {
            "published_at_utc": published.isoformat(),
            "zone_low": 100.0,
            "zone_high": 102.0,
            "direction": "bearish",
            "invalidation": {"field": "high", "level": 105.0, "side": "above"},
        },
        "price_check": {"resolved_at_utc": resolved.isoformat()},
    }


@pytest.fixture
def isolated_calendar(tmp_path, monkeypatch) -> Path:
    cal_path = _write_calendar(tmp_path / "us_session_calendar_v1.json")
    monkeypatch.setattr(contract, "CASH_CALENDAR", cal_path)
    return cal_path


# ---------------------------------------------------------------------------
# 1. Calendar schema & deterministic NYSE fallback parity (2026-2028)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("year", [2026, 2027, 2028])
def test_deterministic_fallback_matches_official_nyse_calendar_2026_2028(year):
    closed, early = contract._fallback_us_cash_year(year)
    expected = US_CALENDAR_2026_2028["years"][str(year)]
    assert closed == frozenset(expected["closed"])
    assert early == frozenset(expected["early_close_13_et"])


# ---------------------------------------------------------------------------
# 2. Normal open session strictness preserved (Wed 25 Nov & Mon 30 Nov)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("market", ["US500", "USTEC"])
@pytest.mark.parametrize("captured", [
    _et(2026, 11, 25, 9, 30, 0),
    _et(2026, 11, 25, 13, 0, 0),
    _et(2026, 11, 25, 15, 59, 59),
    _et(2026, 11, 30, 10, 0, 0),
    _et(2026, 11, 30, 15, 30, 0),
])
def test_normal_open_session_stays_strict_at_capture(isolated_calendar, market, captured):
    at, closed = contract.comparison_clock(market, captured)
    assert closed is False
    assert at == captured

    snap = {
        "tv_symbol": tv.SYMBOLS[market],
        "sha256": "1" * 64,
        "page_title": f"{market} 6,000.00",
        "captured_at_utc": captured.isoformat(),
    }
    good_quote = {
        "market": market,
        "instrument": market,
        "price": 6000.0,
        "quoted_at_utc": (captured - timedelta(seconds=15)).isoformat(),
        "known_at_utc": captured.isoformat(),
        "source_path": "export.json",
        "source_sha256": "a" * 64,
    }
    res = contract.compare_scale(market, snap, good_quote)
    assert res["comparison_basis"] == "AT_CAPTURE"
    assert res["difference_pct"] == 0

    # Off-scale (> 0.15%) remains strictly refused during normal open hours.
    off_scale = {**snap, "page_title": f"{market} 6,020.00"}
    with pytest.raises(contract.ImageContractError, match="TRADINGVIEW_PRICE_SCALE_MISMATCH"):
        contract.compare_scale(market, off_scale, good_quote)

    # Stale quote (> 120s) remains strictly refused during normal open hours.
    stale_quote = {**good_quote, "quoted_at_utc": (captured - timedelta(seconds=121)).isoformat()}
    with pytest.raises(contract.ImageContractError, match="TRADINGVIEW_PLAN_QUOTE_STALE"):
        contract.compare_scale(market, snap, stale_quote)


@pytest.mark.parametrize("market", ["US500", "USTEC"])
def test_normal_open_session_followup_allows_cash_hours_and_refuses_after_hours(isolated_calendar, market):
    pub = _et(2026, 11, 25, 10, 0)
    open_req = followups.move_chart_request(_followup_row(market, pub, _et(2026, 11, 25, 16, 0)))
    assert "refusal" not in open_req

    after_req = followups.move_chart_request(_followup_row(market, pub, _et(2026, 11, 25, 16, 15)))
    assert after_req["refusal"] == f"CC778_CHART_MARKET_CLOSED_AT_RESOLUTION:{tv.SYMBOLS[market]}"


@pytest.mark.parametrize("market", ["XAUUSD", "EURUSD", "USDJPY", "USOIL", "BTCUSD"])
@pytest.mark.parametrize("captured", [
    _et(2026, 11, 26, 11, 0),  # Thu Thanksgiving midday ET
    _et(2026, 11, 27, 14, 30), # Fri Black Friday post-13:00 ET
])
def test_non_cash_index_markets_keep_normal_weekday_clock_on_us_equity_holidays(isolated_calendar, market, captured):
    assert contract.comparison_clock(market, captured) == (captured, False)


# ---------------------------------------------------------------------------
# 3. Thu 26 Nov 2026: US Thanksgiving full holiday closure
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("market", ["US500", "USTEC"])
@pytest.mark.parametrize("captured", [
    _et(2026, 11, 26, 0, 5),
    _et(2026, 11, 26, 9, 30),
    _et(2026, 11, 26, 11, 15),
    _et(2026, 11, 26, 15, 59),
    _et(2026, 11, 26, 16, 0),
    _et(2026, 11, 26, 22, 0),
])
def test_thanksgiving_full_closure_anchors_cash_indices_to_wednesday_close(isolated_calendar, market, captured):
    wed_close = _et(2026, 11, 25, 16, 0)  # 2026-11-25T21:00:00Z
    at, closed = contract.comparison_clock(market, captured)
    assert closed is True
    assert at == wed_close


@pytest.mark.parametrize("market,symbol,price", [
    ("US500", "^GSPC", 7201.09),
    ("USTEC", "^NDX", 26214.17),
])
def test_thanksgiving_prevents_false_mismatch_from_moving_cfd_and_validates_wednesday_close(
        tmp_path, monkeypatch, isolated_calendar, market, symbol, price):
    """During Thu 26 Nov 11:00 ET, live Exness CFD drift (+0.8%) never causes a false mismatch vs frozen cash index."""
    captured = _et(2026, 11, 26, 11, 0, 0)
    wed_close = _et(2026, 11, 25, 16, 0, 0)
    wed_settle = _et(2026, 11, 25, 16, 54, 10)  # Yahoo official Wed cash-index settlement print

    export_path = tmp_path / "plan-status.public.json"
    bar_path = tmp_path / "bars.sqlite3"
    _init_bar_store(bar_path)
    # Live Thanksgiving-morning Exness CFD quote drifted +0.80% away from Wed cash close.
    _export_price(export_path, market, price * 1.008, captured - timedelta(seconds=10), generated_at=captured)
    # Held bar store has a Thanksgiving CFD bar (+0.80%) AND no Wed close bar -> must fall through to Wed public close.
    _insert_m1_bar(bar_path, market, price * 1.008, captured, captured, sid="thu-cfd")

    monkeypatch.setattr(public_quotes, "ROOT", tmp_path / "public-quotes")
    monkeypatch.setattr(prices, "PLAN_STATUS_PATH", export_path)
    monkeypatch.setattr(prices, "BAR_STORE", bar_path)
    monkeypatch.setattr(contract, "QUOTE_ROOT", tmp_path / "missing-captures")
    monkeypatch.setattr(public_quotes, "utcnow", lambda: captured - timedelta(seconds=5))
    monkeypatch.setattr(
        public_quotes, "http_read",
        lambda _url: _yahoo_json(symbol, price, wed_settle, prior=price - 15.0),
    )

    prices.prepare_chart_quote(market, now=captured - timedelta(seconds=5))
    snap = {
        "tv_symbol": tv.SYMBOLS[market],
        "sha256": "2" * 64,
        "page_title": f"{symbol.lstrip('^')} {price:,.2f}",
        "captured_at_utc": captured.isoformat(),
    }
    bound = contract.bind_scale(market, snap)
    check = contract.validate_scale(market, bound)
    assert check["comparison_basis"] == "LAST_CLOSE"
    assert check["comparison_at_utc"] == wed_close.isoformat()
    assert check["difference_pct"] == 0
    assert check["quote"]["source_kind"] == "PUBLIC_ON_DEMAND_QUOTE"
    # Live Thanksgiving CFD export was honestly rejected as stale vs Wed close, never causing false mismatch.
    assert check["quote"]["source_attempts"][0]["source_kind"] == "PLAN_STATUS_EXPORT"
    assert check["quote"]["source_attempts"][0]["cause"] == "CHART_REFERENCE_STALE"

    # A genuinely off-scale chart (>0.15% vs Wed close) is STILL strictly refused on Thanksgiving.
    bad_snap = {**snap, "page_title": f"{symbol.lstrip('^')} {price * 1.01:,.2f}"}
    with pytest.raises(contract.ImageContractError, match="TRADINGVIEW_PRICE_SCALE_MISMATCH"):
        contract.bind_scale(market, bad_snap)


@pytest.mark.parametrize("market", ["US500", "USTEC"])
def test_thanksgiving_followup_refuses_closed_cash_market_and_spends_no_capture(tmp_path, isolated_calendar, market):
    pub = _et(2026, 11, 25, 14, 0)
    resolved = _et(2026, 11, 26, 11, 30)  # Thu Thanksgiving midday ET
    row = _followup_row(market, pub, resolved)

    req = followups.move_chart_request(row)
    assert req["refusal"] == f"CC778_CHART_MARKET_CLOSED_AT_RESOLUTION:{tv.SYMBOLS[market]}"

    called = []
    taken = followups.capture_move_chart(row, root=tmp_path, now=resolved, worker=lambda a: called.append(a))
    assert taken["status"] == "MEDIA_PENDING"
    assert taken["attempted"] is False
    assert taken["cause"] == f"CC778_CHART_MARKET_CLOSED_AT_RESOLUTION:{tv.SYMBOLS[market]}"
    assert called == []


# ---------------------------------------------------------------------------
# 4. Fri 27 Nov 2026: Black Friday 13:00 ET early close
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("market", ["US500", "USTEC"])
def test_black_friday_pre_open_open_early_close_and_weekend_clocks(isolated_calendar, market):
    wed_close = _et(2026, 11, 25, 16, 0)   # 2026-11-25T21:00:00Z
    fri_early = _et(2026, 11, 27, 13, 0)   # 2026-11-27T18:00:00Z

    # Pre-open Fri 09:00 ET skips Thanksgiving Thu 26 Nov -> Wed 25 Nov 16:00 ET.
    assert contract.comparison_clock(market, _et(2026, 11, 27, 9, 0)) == (wed_close, True)
    assert contract.comparison_clock(market, _et(2026, 11, 27, 9, 29, 59)) == (wed_close, True)

    # Open window 09:30 <= t < 13:00 ET -> AT_CAPTURE (closed=False).
    for open_ts in (_et(2026, 11, 27, 9, 30, 0), _et(2026, 11, 27, 11, 15, 0), _et(2026, 11, 27, 12, 59, 59)):
        assert contract.comparison_clock(market, open_ts) == (open_ts, False)

    # Post-early-close (>= 13:00 ET) through Sat/Sun/Mon pre-open -> Fri 27 Nov 13:00 ET (18:00Z).
    for closed_ts in (
        _et(2026, 11, 27, 13, 0, 0),
        _et(2026, 11, 27, 14, 30, 0),
        _et(2026, 11, 27, 16, 15, 0),
        _et(2026, 11, 28, 10, 0, 0),
        _et(2026, 11, 29, 15, 0, 0),
        _et(2026, 11, 30, 9, 0, 0),
    ):
        assert contract.comparison_clock(market, closed_ts) == (fri_early, True)


@pytest.mark.parametrize("market,symbol,settle_et_hm,price", [
    ("US500", "^GSPC", (13, 54), 7225.40),
    ("USTEC", "^NDX", (14, 15), 26310.85),
])
def test_black_friday_post_1300_early_close_settlement_print_compares_and_audits(
        tmp_path, monkeypatch, isolated_calendar, market, symbol, settle_et_hm, price):
    """Post-13:00 ET official Yahoo settlement prints (<=90m after 13:00 ET) pass scale checks and CC-489 audit."""
    fri_early = _et(2026, 11, 27, 13, 0, 0)
    settle_utc = _et(2026, 11, 27, settle_et_hm[0], settle_et_hm[1], 10)
    captured = _et(2026, 11, 27, 15, 0, 0)  # During former 13:00-16:00 open window

    export_path = tmp_path / "plan-status.public.json"
    _export_price(export_path, market, price * 1.006, captured - timedelta(seconds=10), generated_at=captured)

    monkeypatch.setattr(public_quotes, "ROOT", tmp_path / "public-quotes")
    monkeypatch.setattr(prices, "PLAN_STATUS_PATH", export_path)
    monkeypatch.setattr(prices, "BAR_STORE", tmp_path / "missing-bars.sqlite3")
    monkeypatch.setattr(contract, "QUOTE_ROOT", tmp_path / "missing-captures")
    monkeypatch.setattr(public_quotes, "utcnow", lambda: captured - timedelta(seconds=5))
    monkeypatch.setattr(
        public_quotes, "http_read",
        lambda _url: _yahoo_json(symbol, price, settle_utc, prior=price - 12.0),
    )

    prices.prepare_chart_quote(market, now=captured - timedelta(seconds=5))
    snap = {
        "tv_symbol": tv.SYMBOLS[market],
        "sha256": "3" * 64,
        "page_title": f"{symbol.lstrip('^')} {price:,.2f}",
        "captured_at_utc": captured.isoformat(),
    }
    bound = contract.bind_scale(market, snap)
    check = contract.validate_scale(market, bound)
    assert check["comparison_basis"] == "LAST_CLOSE"
    assert check["comparison_at_utc"] == fri_early.isoformat()
    assert check["difference_pct"] == 0
    assert check["quote"]["source_kind"] == "PUBLIC_ON_DEMAND_QUOTE"
    assert check["quote"]["source_symbol"] == symbol

    # Audit script validates the early-close LAST_CLOSE check toward 100% coverage.
    day = "2026-11-28"  # 2026-11-27 15:00 ET = 20:00Z = 2026-11-28 03:00 GMT+7 (>= 02:00 GMT+7 prod day)
    reg = tmp_path / "images.jsonl"
    out = tmp_path / "outcomes.jsonl"
    reg.write_text(json.dumps({
        "schema_version": IMAGE_SCHEMA,
        "state": "PUBLISHED",
        "record_id": f"{market}-early-close-tg",
        "piece_id": f"plan-{market}",
        "day": day,
        "destination": "telegram",
        "counts_as_article": False,
        "images": [{
            "sha256": snap["sha256"],
            "image_type": "TRADINGVIEW_MARKET_CHART",
            "price_scale_check": check,
        }],
    }) + "\n", encoding="utf-8")
    out.write_text("", encoding="utf-8")
    report = audit_chart_prices(
        reg, out, day, since=captured - timedelta(hours=1), now=captured + timedelta(days=2),
    )
    assert report["status"] == "PASS"
    assert report["compared_percent"] == 100
    assert report["calibration"]["markets"][market]["closed_market_comparisons"] == 1


def test_black_friday_early_close_guards_beyond_90m_future_and_cfd_quotes(tmp_path, monkeypatch, isolated_calendar):
    """Early-close settlement stays bounded to <=90m past 13:00 ET, never future, and never widens broker quotes."""
    captured = _et(2026, 11, 27, 15, 30, 0)
    monkeypatch.setattr(public_quotes, "ROOT", tmp_path / "public-quotes")
    monkeypatch.setattr(prices, "PLAN_STATUS_PATH", tmp_path / "missing-status.json")
    monkeypatch.setattr(prices, "BAR_STORE", tmp_path / "missing-bars.sqlite3")
    monkeypatch.setattr(contract, "QUOTE_ROOT", tmp_path / "missing-captures")

    # 1. > 90 min past 13:00 ET (14:35 ET = 95 min) must NOT compare.
    too_late = _et(2026, 11, 27, 14, 35, 0)
    monkeypatch.setattr(public_quotes, "utcnow", lambda: captured - timedelta(seconds=5))
    monkeypatch.setattr(
        public_quotes, "http_read",
        lambda _url: _yahoo_json("^GSPC", 7225.40, too_late, prior=7200.0),
    )
    prices.prepare_chart_quote("US500", now=captured - timedelta(seconds=5))
    snap = {
        "tv_symbol": tv.SYMBOLS["US500"],
        "sha256": "4" * 64,
        "page_title": "SPX 7,225.40",
        "captured_at_utc": captured.isoformat(),
    }
    assert contract.bind_scale("US500", snap)["price_scale_check"]["comparison_basis"] == "NOT_COMPARED"

    # 2. Broker/CFD quote at 13:40 ET stays on strict [-2s, +120s] skew and fails compare_scale.
    broker_quote = {
        "market": "US500",
        "instrument": "US500",
        "price": 7225.40,
        "quoted_at_utc": _et(2026, 11, 27, 13, 40, 0).isoformat(),
        "known_at_utc": _et(2026, 11, 27, 13, 40, 0).isoformat(),
        "source_kind": "BAR_STORE_M1_CLOSE",
        "source_path": "bars.sqlite3",
        "source_sha256": "c" * 64,
    }
    with pytest.raises(contract.ImageContractError, match="TRADINGVIEW_PLAN_QUOTE_STALE"):
        contract.compare_scale("US500", snap, broker_quote)

    # 3. Settlement print observed AFTER capture (13:30 ET capture vs 13:45 ET print) is strictly refused.
    future_settle = {
        "market": "US500",
        "instrument": "US500",
        "price": 7225.40,
        "quoted_at_utc": _et(2026, 11, 27, 13, 45, 0).isoformat(),
        "known_at_utc": _et(2026, 11, 27, 13, 29, 0).isoformat(),
        "source_kind": "PUBLIC_ON_DEMAND_QUOTE",
        "instrument_type": "INDEX",
        "source_path": "obs.json",
        "source_sha256": "d" * 64,
    }
    early_capture = {**snap, "captured_at_utc": _et(2026, 11, 27, 13, 30, 0).isoformat()}
    with pytest.raises(contract.ImageContractError, match="TRADINGVIEW_PLAN_QUOTE_STALE"):
        contract.compare_scale("US500", early_capture, future_settle)

    # 4. Pre-13:00 ET Black Friday open session STILL refuses a 10-minute-old quote (strict open rules).
    open_snap = {**snap, "captured_at_utc": _et(2026, 11, 27, 11, 0, 0).isoformat()}
    stale_open = {
        **future_settle,
        "quoted_at_utc": _et(2026, 11, 27, 10, 50, 0).isoformat(),
        "known_at_utc": _et(2026, 11, 27, 10, 55, 0).isoformat(),
    }
    with pytest.raises(contract.ImageContractError, match="TRADINGVIEW_PLAN_QUOTE_STALE"):
        contract.compare_scale("US500", open_snap, stale_open)


@pytest.mark.parametrize("market", ["US500", "USTEC"])
def test_black_friday_followup_allows_pre_1300_and_refuses_post_1300(isolated_calendar, market):
    pub = _et(2026, 11, 27, 9, 45)
    # 12:45 ET and 13:00 ET (bar 12:45-13:00 ET) are inside the 09:30-13:00 ET early session.
    assert "refusal" not in followups.move_chart_request(_followup_row(market, pub, _et(2026, 11, 27, 12, 45)))
    assert "refusal" not in followups.move_chart_request(_followup_row(market, pub, _et(2026, 11, 27, 13, 0)))

    # 13:15 ET (bar 13:00-13:15 ET) and 15:00 ET are past the 13:00 ET early close.
    for resolved in (_et(2026, 11, 27, 13, 15), _et(2026, 11, 27, 15, 0)):
        req = followups.move_chart_request(_followup_row(market, pub, resolved))
        assert req["refusal"] == f"CC778_CHART_MARKET_CLOSED_AT_RESOLUTION:{tv.SYMBOLS[market]}"


# ---------------------------------------------------------------------------
# 5. Authoritative JSON override & missing/corrupt calendar fail-safe fallback
# ---------------------------------------------------------------------------

def test_json_calendar_overrides_custom_holidays_and_reloads_on_same_size_edit(tmp_path, monkeypatch):
    cal_path = tmp_path / "custom_us_session_calendar_v1.json"
    _write_calendar(cal_path, {
        "schema": "IbkrUsSessionCalendarV1",
        "years": {
            "2026": {
                "closed": ["2026-11-18"],
                "early_close_13_et": ["2026-11-18", "2026-11-19"],  # closed must win when listed in both
            }
        },
    })
    monkeypatch.setattr(contract, "CASH_CALENDAR", cal_path)

    # Synthetic full closure (Wed 18 Nov): closed takes precedence over early_close_13_et -> Tue 17 Nov 16:00 ET.
    assert contract.comparison_clock("US500", _et(2026, 11, 18, 11, 0)) == (_et(2026, 11, 17, 16, 0), True)
    req_closed = followups.move_chart_request(_followup_row("US500", _et(2026, 11, 17, 15, 0), _et(2026, 11, 18, 11, 0)))
    assert req_closed["refusal"] == "CC778_CHART_MARKET_CLOSED_AT_RESOLUTION:SP:SPX"

    # Synthetic early close (Thu 19 Nov): open at 11:00 ET, closed at 13:30 ET -> Thu 19 Nov 13:00 ET.
    assert contract.comparison_clock("USTEC", _et(2026, 11, 19, 11, 0)) == (_et(2026, 11, 19, 11, 0), False)
    assert contract.comparison_clock("USTEC", _et(2026, 11, 19, 13, 30)) == (_et(2026, 11, 19, 13, 0), True)
    req_early = followups.move_chart_request(_followup_row("USTEC", _et(2026, 11, 19, 10, 0), _et(2026, 11, 19, 14, 0)))
    assert req_early["refusal"] == "CC778_CHART_MARKET_CLOSED_AT_RESOLUTION:NASDAQ:NDX"

    # Same-byte-length edit moving the synthetic closure from 2026-11-18 to 2026-11-20 must take effect immediately.
    _write_calendar(cal_path, {
        "schema": "IbkrUsSessionCalendarV1",
        "years": {
            "2026": {
                "closed": ["2026-11-20"],
                "early_close_13_et": ["2026-11-20", "2026-11-19"],
            }
        },
    })
    assert contract.comparison_clock("US500", _et(2026, 11, 18, 11, 0)) == (_et(2026, 11, 18, 11, 0), False)
    assert contract.comparison_clock("US500", _et(2026, 11, 20, 11, 0)) == (_et(2026, 11, 19, 13, 0), True)


@pytest.mark.parametrize("bad_mode", [
    "missing",
    "malformed_json",
    "wrong_schema",
    "corrupt_year",
    "missing_year",
])
def test_missing_or_corrupt_calendar_fails_safe_to_deterministic_nyse_rules(tmp_path, monkeypatch, bad_mode):
    cal_path = tmp_path / f"cal-{bad_mode}.json"
    if bad_mode == "malformed_json":
        _write_calendar(cal_path, "{not valid json")
    elif bad_mode == "wrong_schema":
        _write_calendar(cal_path, {
            "schema": "UnexpectedCalendarV99",
            "years": {"2026": {"closed": [], "early_close_13_et": []}},
        })
    elif bad_mode == "corrupt_year":
        _write_calendar(cal_path, {
            "schema": "IbkrUsSessionCalendarV1",
            "years": {"2026": {"closed": "not-a-list", "early_close_13_et": []}},
        })
    elif bad_mode == "missing_year":
        _write_calendar(cal_path, {
            "schema": "IbkrUsSessionCalendarV1",
            "years": {"2025": {"closed": [], "early_close_13_et": []}},
        })

    monkeypatch.setattr(contract, "CASH_CALENDAR", cal_path)

    # Normal Wed 25 Nov stays open.
    wed_open = _et(2026, 11, 25, 11, 0)
    assert contract.comparison_clock("US500", wed_open) == (wed_open, False)

    # Thu 26 Nov Thanksgiving still resolves to Wed 25 Nov 16:00 ET.
    assert contract.comparison_clock("US500", _et(2026, 11, 26, 11, 0)) == (_et(2026, 11, 25, 16, 0), True)
    assert contract.comparison_clock("USTEC", _et(2026, 11, 26, 14, 0)) == (_et(2026, 11, 25, 16, 0), True)

    # Fri 27 Nov Black Friday still opens 09:30-13:00 ET and closes at 13:00 ET.
    fri_open = _et(2026, 11, 27, 11, 0)
    assert contract.comparison_clock("US500", fri_open) == (fri_open, False)
    assert contract.comparison_clock("USTEC", _et(2026, 11, 27, 14, 0)) == (_et(2026, 11, 27, 13, 0), True)

    # Christmas Eve early close + Christmas Day closure + July 3 EDT closure all work in fallback too.
    assert contract.comparison_clock("US500", _et(2026, 12, 25, 11, 0)) == (_et(2026, 12, 24, 13, 0), True)
    assert contract.comparison_clock("US500", _et(2026, 7, 3, 11, 0)) == (_et(2026, 7, 2, 16, 0), True)

    # call_followups_v1 also honors the deterministic fallback cleanly.
    req_thu = followups.move_chart_request(_followup_row("US500", _et(2026, 11, 25, 15, 0), _et(2026, 11, 26, 11, 0)))
    assert req_thu["refusal"] == "CC778_CHART_MARKET_CLOSED_AT_RESOLUTION:SP:SPX"
    req_fri_late = followups.move_chart_request(_followup_row("USTEC", _et(2026, 11, 27, 10, 0), _et(2026, 11, 27, 13, 30)))
    assert req_fri_late["refusal"] == "CC778_CHART_MARKET_CLOSED_AT_RESOLUTION:NASDAQ:NDX"

    # Missing file is never created on disk.
    if bad_mode == "missing":
        assert not cal_path.exists()
