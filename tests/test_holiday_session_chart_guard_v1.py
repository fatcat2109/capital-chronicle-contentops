"""Hermetic adversarial tests for Dec-2026 / Jan-2027 Holiday & Early-Close Chart & Wrap Guard.

Zero live writes, zero network/browser calls, zero agy/claude/codex invocations, zero .stop edits.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from live_contentops import call_followups_v1 as followups
from live_contentops import daily_trend_board_v1 as trend_board
from live_contentops import holiday_session_chart_guard_v1 as guard
from live_contentops import market_wrap_sources_v1 as wrap_sources
from live_contentops import publication_image_contract_v1 as contract
from live_contentops import tradingview_snapshot_v1 as tv


CANONICAL_CALENDAR_2026_2028 = {
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


class _NullOffsetTz(tzinfo):
    def utcoffset(self, dt):
        return None

    def dst(self, dt):
        return None

    def tzname(self, dt):
        return "NULL"


def _et(year: int, month: int, day: int, hour: int, minute: int = 0, second: int = 0) -> datetime:
    return datetime(year, month, day, hour, minute, second, tzinfo=guard.ET).astimezone(timezone.utc)


def _write_cal(path: Path, payload: dict | str = CANONICAL_CALENDAR_2026_2028) -> Path:
    path.write_text(payload if isinstance(payload, str) else json.dumps(payload, indent=2), encoding="utf-8")
    return path


def _snap(market: str, price: float, captured: datetime, *, title_override: str | None = None, **extra) -> dict:
    places = 5 if market == "EURUSD" else 3 if market == "USDJPY" else 2
    title = title_override if title_override is not None else f"{market} {price:,.{places}f}"
    return {
        "tv_symbol": guard.CORE_MARKETS[market]["tv_symbol"],
        "sha256": "a" * 64,
        "page_title": title,
        "captured_at_utc": captured.isoformat(),
        **extra,
    }


def _cfd_quote(
    market: str,
    price: float,
    quoted_at: datetime,
    *,
    known_at: datetime | None = None,
    source_kind: str = "PLAN_STATUS_EXPORT",
    price_basis: str = "plan_feed",
    **extra,
) -> dict:
    return {
        "market": market,
        "instrument": market,
        "price": price,
        "quoted_at_utc": quoted_at.isoformat(),
        "known_at_utc": (known_at or quoted_at).isoformat(),
        "source_kind": source_kind,
        "price_basis": price_basis,
        "source_path": "plan-status.public.json",
        "source_sha256": "b" * 64,
        **extra,
    }


def _settlement_quote(
    market: str,
    price: float,
    observed_at: datetime,
    *,
    known_at: datetime | None = None,
    source_symbol: str | None = None,
    instrument_type: str = "INDEX",
    **extra,
) -> dict:
    return {
        "market": market,
        "instrument": market,
        "price": price,
        "quoted_at_utc": observed_at.isoformat(),
        "known_at_utc": (known_at or observed_at).isoformat(),
        "source_kind": "PUBLIC_ON_DEMAND_QUOTE",
        "instrument_type": instrument_type,
        "source_symbol": source_symbol or guard.CORE_MARKETS[market]["public_quote_symbol"],
        "price_basis": "public_index",
        "source_path": "public-quotes/obs.json",
        "source_sha256": "c" * 64,
        **extra,
    }


@pytest.fixture
def cal_file(tmp_path) -> Path:
    return _write_cal(tmp_path / "us_session_calendar_v1.json")


# ---------------------------------------------------------------------------
# 1. Calendar Loading, Cache Invalidation, Fail-Closed vs Explicit Fallback
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("year", [2026, 2027, 2028])
def test_deterministic_nyse_rules_match_canonical_calendar_2026_2028(year):
    closed, early = guard.deterministic_nyse_year_dates(year)
    expected = CANONICAL_CALENDAR_2026_2028["years"][str(year)]
    assert closed == frozenset(expected["closed"])
    assert early == frozenset(expected["early_close_13_et"])


def test_live_canonical_calendar_file_loads_when_present():
    if not guard.DEFAULT_CALENDAR_PATH.is_file():
        pytest.skip("Canonical us_session_calendar_v1.json absent in this environment")
    loaded = guard.load_us_session_calendar(calendar_path=guard.DEFAULT_CALENDAR_PATH)
    assert loaded["source"] == "FILE"
    assert loaded["schema"] == "IbkrUsSessionCalendarV1"
    assert len(loaded["sha256"]) == 64
    for year in (2026, 2027, 2028):
        assert loaded["years"][year]["closed"] == frozenset(CANONICAL_CALENDAR_2026_2028["years"][str(year)]["closed"])
        assert loaded["years"][year]["early_close_13_et"] == frozenset(
            CANONICAL_CALENDAR_2026_2028["years"][str(year)]["early_close_13_et"]
        )


def test_calendar_closed_wins_over_early_and_same_size_file_edit_invalidates_cache(tmp_path):
    path = tmp_path / "custom_cal.json"
    _write_cal(path, {
        "schema": "IbkrUsSessionCalendarV1",
        "years": {
            "2026": {
                "closed": ["2026-12-22"],
                "early_close_13_et": ["2026-12-22", "2026-12-24"],
            }
        },
    })
    d22 = guard.classify_us_cash_day("2026-12-22", calendar_path=path)
    assert d22["session_state"] == "CLOSED_HOLIDAY"
    assert d22["is_open_day"] is False
    assert d22["holiday_label"] == "CUSTOM_CALENDAR_HOLIDAY"

    # Same-byte-length edit moving closure from 2026-12-22 to 2026-12-23 must take effect immediately.
    _write_cal(path, {
        "schema": "IbkrUsSessionCalendarV1",
        "years": {
            "2026": {
                "closed": ["2026-12-23"],
                "early_close_13_et": ["2026-12-23", "2026-12-24"],
            }
        },
    })
    assert guard.classify_us_cash_day("2026-12-22", calendar_path=path)["session_state"] == "REGULAR_SESSION"
    assert guard.classify_us_cash_day("2026-12-23", calendar_path=path)["session_state"] == "CLOSED_HOLIDAY"


@pytest.mark.parametrize("mode,expected_cause", [
    ("missing", "HOLIDAY_CALENDAR_UNAVAILABLE"),
    ("malformed_json", "HOLIDAY_CALENDAR_CORRUPT_JSON"),
    ("wrong_schema", "HOLIDAY_CALENDAR_SCHEMA_INVALID"),
    ("empty_years", "HOLIDAY_CALENDAR_SCHEMA_INVALID"),
    ("bad_year_key", "HOLIDAY_CALENDAR_SCHEMA_INVALID"),
    ("bad_date_type", "HOLIDAY_CALENDAR_SCHEMA_INVALID"),
    ("bad_iso_date", "HOLIDAY_CALENDAR_SCHEMA_INVALID"),
    ("cross_year_date", "HOLIDAY_CALENDAR_YEAR_MISMATCH"),
])
def test_calendar_loader_fails_closed_by_default_and_honors_explicit_fallback(tmp_path, mode, expected_cause):
    path = tmp_path / f"bad-{mode}.json"
    if mode == "malformed_json":
        _write_cal(path, "{bad json")
    elif mode == "wrong_schema":
        _write_cal(path, {"schema": "WrongSchemaV9", "years": {"2026": {"closed": [], "early_close_13_et": []}}})
    elif mode == "empty_years":
        _write_cal(path, {"schema": "IbkrUsSessionCalendarV1", "years": {}})
    elif mode == "bad_year_key":
        _write_cal(path, {"schema": "IbkrUsSessionCalendarV1", "years": {"26": {"closed": [], "early_close_13_et": []}}})
    elif mode == "bad_date_type":
        _write_cal(path, {"schema": "IbkrUsSessionCalendarV1", "years": {"2026": {"closed": "2026-12-25", "early_close_13_et": []}}})
    elif mode == "bad_iso_date":
        _write_cal(path, {"schema": "IbkrUsSessionCalendarV1", "years": {"2026": {"closed": ["2026-02-30"], "early_close_13_et": []}}})
    elif mode == "cross_year_date":
        _write_cal(path, {"schema": "IbkrUsSessionCalendarV1", "years": {"2026": {"closed": ["2027-01-01"], "early_close_13_et": []}}})

    with pytest.raises(guard.HolidayChartGuardError, match=expected_cause):
        guard.load_us_session_calendar(calendar_path=path)

    # Explicit allow_fallback=True provides audited NYSE rules without creating missing files.
    fb = guard.classify_us_cash_day("2026-12-25", calendar_path=path, allow_fallback=True)
    assert fb["session_state"] == "CLOSED_HOLIDAY"
    assert fb["holiday_label"] == "CHRISTMAS_DAY"
    assert fb["calendar_source"] == "FALLBACK_NYSE_RULES"
    if mode == "missing":
        assert not path.exists()


def test_missing_year_in_calendar_fails_closed_unless_fallback_enabled(tmp_path):
    path = _write_cal(tmp_path / "only2026.json", {
        "schema": "IbkrUsSessionCalendarV1",
        "years": {"2026": CANONICAL_CALENDAR_2026_2028["years"]["2026"]},
    })
    with pytest.raises(guard.HolidayChartGuardError, match="HOLIDAY_CALENDAR_YEAR_MISSING"):
        guard.classify_us_cash_day("2027-01-01", calendar_path=path)

    fb = guard.classify_us_cash_day("2027-01-01", calendar_path=path, allow_fallback=True)
    assert fb["session_state"] == "CLOSED_HOLIDAY"
    assert fb["holiday_label"] == "NEW_YEARS_DAY"
    assert fb["calendar_source"] == "FALLBACK_NYSE_RULES"


# ---------------------------------------------------------------------------
# 2. All 7 Core Markets Across Dec-2026 / Jan-2027 / Feb-2027 Milestones
# ---------------------------------------------------------------------------

def test_core_markets_match_canonical_tradingview_and_image_contract_specs():
    assert set(guard.CORE_MARKETS) == {"XAUUSD", "US500", "USTEC", "EURUSD", "USDJPY", "USOIL", "BTCUSD"}
    assert set(guard.CORE_MARKET_ORDER) == set(guard.CORE_MARKETS)
    for market, spec in guard.CORE_MARKETS.items():
        assert spec["tv_symbol"] == tv.SYMBOLS[market]
        assert spec["max_difference_pct"] == contract.MAX_DIFFERENCE_PCT[market]


@pytest.mark.parametrize("market", ["US500", "USTEC"])
def test_christmas_eve_early_close_and_christmas_day_stretch_cash_indices(cal_file, market):
    wed_close = _et(2026, 12, 23, 16, 0)
    eve_early = _et(2026, 12, 24, 13, 0)

    # Thu 24 Dec pre-open -> Wed 23 Dec 16:00 ET
    pre = guard.resolve_market_session(market, _et(2026, 12, 24, 9, 29, 59), calendar_path=cal_file)
    assert pre["is_closed"] is True
    assert pre["session_status"] == "CLOSED_PRE_OPEN"
    assert pre["comparison_at_utc"] == wed_close.isoformat()
    assert pre["holiday_label"] == "CHRISTMAS_EVE_EARLY_CLOSE"

    # Thu 24 Dec 09:30 <= t < 13:00 ET -> OPEN_EARLY_CLOSE (AT_CAPTURE)
    for ts in (_et(2026, 12, 24, 9, 30, 0), _et(2026, 12, 24, 11, 15, 0), _et(2026, 12, 24, 12, 59, 59)):
        s = guard.resolve_market_session(market, ts, calendar_path=cal_file)
        assert s["is_closed"] is False
        assert s["session_status"] == "OPEN_EARLY_CLOSE"
        assert s["comparison_basis"] == "AT_CAPTURE"
        assert s["comparison_at_utc"] == ts.isoformat()
        assert s["session_close_et"] == "13:00"
        assert s["settlement_window_allowed"] is False

    # Thu 24 Dec 13:00-15:59 ET -> CLOSED_EARLY_CLOSE with CFD holiday drift risk active
    for ts in (_et(2026, 12, 24, 13, 0, 0), _et(2026, 12, 24, 14, 15, 0), _et(2026, 12, 24, 15, 59, 59)):
        s = guard.resolve_market_session(market, ts, calendar_path=cal_file)
        assert s["is_closed"] is True
        assert s["session_status"] == "CLOSED_EARLY_CLOSE"
        assert s["comparison_basis"] == "LAST_CLOSE"
        assert s["comparison_at_utc"] == eve_early.isoformat()
        assert s["settlement_window_allowed"] is True
        assert s["cfd_holiday_drift_risk"] is True

    # Fri 25 Dec (Christmas Day), Sat 26, Sun 27, Mon 28 pre-open -> Thu 24 Dec 13:00 ET
    for ts, expected_status, expected_drift_risk in (
        (_et(2026, 12, 25, 11, 0), "CLOSED_HOLIDAY", True),
        (_et(2026, 12, 25, 15, 30), "CLOSED_HOLIDAY", True),
        (_et(2026, 12, 26, 12, 0), "CLOSED_WEEKEND", False),
        (_et(2026, 12, 27, 16, 0), "CLOSED_WEEKEND", False),
        (_et(2026, 12, 28, 9, 29), "CLOSED_PRE_OPEN", False),
    ):
        s = guard.resolve_market_session(market, ts, calendar_path=cal_file)
        assert s["is_closed"] is True
        assert s["session_status"] == expected_status
        assert s["comparison_at_utc"] == eve_early.isoformat()
        assert s["cfd_holiday_drift_risk"] is expected_drift_risk


@pytest.mark.parametrize("market", ["US500", "USTEC"])
def test_new_years_eve_regular_session_and_2027_holiday_rollovers(cal_file, market):
    # Thu 31 Dec 2026 is a FULL NYSE regular session (09:30-16:00 ET), NOT an early close!
    nye_mid = _et(2026, 12, 31, 14, 30)
    s_nye = guard.resolve_market_session(market, nye_mid, calendar_path=cal_file)
    assert s_nye["is_closed"] is False
    assert s_nye["session_status"] == "OPEN_REGULAR"
    assert s_nye["session_close_et"] == "16:00"
    assert s_nye["holiday_label"] == "NEW_YEARS_EVE_REGULAR"

    nye_close = _et(2026, 12, 31, 16, 0)
    # Fri 1 Jan 2027 (New Year's Day), Sat 2, Sun 3, Mon 4 pre-open cross 2026->2027 -> Thu 31 Dec 16:00 ET
    for ts, expected_status in (
        (_et(2027, 1, 1, 10, 30), "CLOSED_HOLIDAY"),
        (_et(2027, 1, 1, 15, 0), "CLOSED_HOLIDAY"),
        (_et(2027, 1, 2, 12, 0), "CLOSED_WEEKEND"),
        (_et(2027, 1, 3, 15, 0), "CLOSED_WEEKEND"),
        (_et(2027, 1, 4, 8, 30), "CLOSED_PRE_OPEN"),
    ):
        s = guard.resolve_market_session(market, ts, calendar_path=cal_file)
        assert s["is_closed"] is True
        assert s["session_status"] == expected_status
        assert s["comparison_at_utc"] == nye_close.isoformat()

    # Mon 18 Jan 2027 (MLK Day) -> Fri 15 Jan 2027 16:00 ET
    s_mlk = guard.resolve_market_session(market, _et(2027, 1, 18, 11, 0), calendar_path=cal_file)
    assert s_mlk["is_closed"] is True
    assert s_mlk["session_status"] == "CLOSED_HOLIDAY"
    assert s_mlk["holiday_label"] == "MLK_DAY"
    assert s_mlk["comparison_at_utc"] == _et(2027, 1, 15, 16, 0).isoformat()
    assert s_mlk["cfd_holiday_drift_risk"] is True

    # Mon 15 Feb 2027 (Presidents' Day) -> Fri 12 Feb 2027 16:00 ET
    s_pres = guard.resolve_market_session(market, _et(2027, 2, 15, 11, 0), calendar_path=cal_file)
    assert s_pres["is_closed"] is True
    assert s_pres["session_status"] == "CLOSED_HOLIDAY"
    assert s_pres["holiday_label"] == "PRESIDENTS_DAY"
    assert s_pres["comparison_at_utc"] == _et(2027, 2, 12, 16, 0).isoformat()
    assert s_pres["cfd_holiday_drift_risk"] is True


def test_non_equity_markets_across_christmas_new_year_mlk_presidents_and_2028_dst(cal_file):
    # BTCUSD is 24/7/365 — never closed on Christmas, New Year, weekends, or early closes.
    for ts in (
        _et(2026, 12, 24, 14, 0),
        _et(2026, 12, 25, 11, 0),
        _et(2026, 12, 26, 12, 0),
        _et(2027, 1, 1, 11, 0),
        _et(2027, 1, 18, 11, 0),
        _et(2027, 2, 15, 11, 0),
    ):
        btc = guard.resolve_market_session("BTCUSD", ts, calendar_path=cal_file)
        assert btc["is_closed"] is False
        assert btc["session_status"] == "OPEN_24X7"
        assert btc["comparison_at_utc"] == ts.isoformat()
        assert btc["settlement_window_allowed"] is False

    # XAUUSD & USOIL (CME commodities): closed on Christmas Eve >= 13:45 ET, Christmas Day, New Year's Eve >= 17:00 ET,
    # New Year's Day; open on MLK Day / Presidents' Day daytime with advisory; Sunday evening before Mon Christmas 2028
    # anchors to Fri 22 Dec 2028 17:00 ET (not Sunday!).
    for mkt in ("XAUUSD", "USOIL"):
        assert guard.resolve_market_session(mkt, _et(2026, 12, 24, 11, 0), calendar_path=cal_file)["is_closed"] is False
        eve_closed = guard.resolve_market_session(mkt, _et(2026, 12, 24, 14, 30), calendar_path=cal_file)
        assert eve_closed["is_closed"] is True
        assert eve_closed["session_status"] == "CLOSED_CME_HOLIDAY_EVE"
        assert eve_closed["comparison_at_utc"] == _et(2026, 12, 24, 13, 45).isoformat()

        xmas = guard.resolve_market_session(mkt, _et(2026, 12, 25, 11, 0), calendar_path=cal_file)
        assert xmas["is_closed"] is True
        assert xmas["session_status"] == "CLOSED_CME_FULL_DAY_HOLIDAY"
        assert xmas["comparison_at_utc"] == _et(2026, 12, 24, 13, 45).isoformat()

        xmas_sat = guard.resolve_market_session(mkt, _et(2026, 12, 26, 12, 0), calendar_path=cal_file)
        assert xmas_sat["is_closed"] is True
        assert xmas_sat["comparison_at_utc"] == _et(2026, 12, 24, 13, 45).isoformat()

        nyd = guard.resolve_market_session(mkt, _et(2027, 1, 1, 11, 0), calendar_path=cal_file)
        assert nyd["is_closed"] is True
        assert nyd["session_status"] == "CLOSED_CME_FULL_DAY_HOLIDAY"
        assert nyd["comparison_at_utc"] == _et(2026, 12, 31, 17, 0).isoformat()

        mlk = guard.resolve_market_session(mkt, _et(2027, 1, 18, 11, 0), calendar_path=cal_file)
        assert mlk["is_closed"] is False
        assert mlk["us_equity_holiday_advisory"] is True

        # Sun 24 Dec 2028 19:00 ET (before Mon 25 Dec 2028 Christmas) -> Fri 22 Dec 2028 17:00 ET
        sun_eve_2028 = guard.resolve_market_session(mkt, _et(2028, 12, 24, 19, 0), calendar_path=cal_file)
        assert sun_eve_2028["is_closed"] is True
        assert sun_eve_2028["session_status"] == "CLOSED_CME_HOLIDAY_EVE"
        assert sun_eve_2028["comparison_at_utc"] == _et(2028, 12, 22, 17, 0).isoformat()

    # EURUSD & USDJPY (FX Spot): weekday open with holiday advisories; weekend closed Fri 17:00 ET - Sun 18:00 ET.
    for mkt in ("EURUSD", "USDJPY"):
        xmas_fx = guard.resolve_market_session(mkt, _et(2026, 12, 25, 11, 0), calendar_path=cal_file)
        assert xmas_fx["is_closed"] is False
        assert xmas_fx["fx_global_holiday_advisory"] is True
        assert xmas_fx["settlement_window_allowed"] is False

        wknd_fx = guard.resolve_market_session(mkt, _et(2026, 12, 26, 12, 0), calendar_path=cal_file)
        assert wknd_fx["is_closed"] is True
        assert wknd_fx["session_status"] == "CLOSED_WEEKEND"
        assert wknd_fx["comparison_at_utc"] == _et(2026, 12, 25, 17, 0).isoformat()

    # Summer EDT DST check: Mon 3 Jul 2028 early close 13:00 EDT = 17:00:00Z
    jul3 = guard.resolve_market_session("US500", _et(2028, 7, 3, 14, 0), calendar_path=cal_file)
    assert jul3["is_closed"] is True
    assert jul3["session_status"] == "CLOSED_EARLY_CLOSE"
    assert jul3["comparison_at_utc"] == "2028-07-03T17:00:00+00:00"


# ---------------------------------------------------------------------------
# 3. Price-Scale Discrimination: Lawful Settlement vs CFD Drift vs True Mismatch
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("market,base_price,captured,expected_close,settle_at", [
    ("US500", 7210.50, _et(2026, 12, 24, 14, 20), _et(2026, 12, 24, 13, 0), _et(2026, 12, 24, 13, 55)),
    ("USTEC", 26350.00, _et(2026, 12, 24, 14, 20), _et(2026, 12, 24, 13, 0), _et(2026, 12, 24, 14, 10)),
    ("US500", 7210.50, _et(2026, 12, 25, 11, 0), _et(2026, 12, 24, 13, 0), _et(2026, 12, 24, 13, 55)),
    ("USTEC", 26350.00, _et(2027, 1, 1, 11, 0), _et(2026, 12, 31, 16, 0), _et(2026, 12, 31, 17, 12)),
    ("US500", 7240.00, _et(2027, 1, 18, 11, 30), _et(2027, 1, 15, 16, 0), _et(2027, 1, 15, 16, 58)),
    ("USTEC", 26500.00, _et(2027, 2, 15, 11, 30), _et(2027, 2, 12, 16, 0), _et(2027, 2, 12, 17, 20)),
])
def test_holiday_moving_cfd_suppressed_and_lawful_cash_settlement_passes(
    cal_file, market, base_price, captured, expected_close, settle_at
):
    # Exness CFD moved +0.85% while US cash index chart is frozen at prior close.
    drifting_cfd = _cfd_quote(market, base_price * 1.0085, captured - timedelta(seconds=15), known_at=captured)
    lawful_settle = _settlement_quote(market, base_price, settle_at, known_at=settle_at + timedelta(seconds=5))
    snap = _snap(market, base_price, captured)

    # 1. With both CFD and lawful settlement print: CFD drift skipped cleanly; settlement print passes.
    res = guard.guard_chart_scale(market, snap, [drifting_cfd, lawful_settle], calendar_path=cal_file)
    assert res["allowed"] is True
    assert res["verdict"] == "PASS_CASH_SETTLEMENT"
    assert res["comparison_basis"] == "LAST_CLOSE"
    assert res["comparison_at_utc"] == expected_close.isoformat()
    assert res["settlement_print_lawful"] is True
    assert res["cfd_drift_suppressed"] is True
    assert res["difference_pct"] == 0.0
    assert res["rejected_candidates"][0]["cause"] == "CFD_QUOTE_AFTER_CASH_CLOSE"
    assert res["rejected_candidates"][0]["suppressed_cfd_difference_pct"] > 0.15

    # 2. With ONLY the drifting holiday CFD (no settlement print cached): safe NOT_COMPARED, NO false mismatch!
    res_only_cfd = guard.guard_chart_scale(market, snap, [drifting_cfd], calendar_path=cal_file)
    assert res_only_cfd["allowed"] is True
    assert res_only_cfd["verdict"] == "NOT_COMPARED_HOLIDAY_CFD_DRIFT_SUPPRESSED"
    assert res_only_cfd["comparison_basis"] == "NOT_COMPARED"
    assert res_only_cfd["quote_absent_cause"] == "TRADINGVIEW_LAST_CLOSE_MAIN_QUOTE_UNAVAILABLE"
    assert res_only_cfd["cfd_drift_suppressed"] is True

    # 3. Genuine chart scale error (+0.90% off vs lawful settlement print) STILL fails closed!
    bad_snap = _snap(market, base_price * 1.009, captured)
    with pytest.raises(guard.HolidayChartGuardError, match="TRADINGVIEW_PRICE_SCALE_MISMATCH") as exc_info:
        guard.guard_chart_scale(market, bad_snap, [drifting_cfd, lawful_settle], calendar_path=cal_file)
    assert exc_info.value.details["verdict"] == "FAIL_CLOSED_SESSION_SCALE_MISMATCH"
    assert exc_info.value.details["settlement_print_lawful"] is True


@pytest.mark.parametrize("market,captured,base_price", [
    ("US500", _et(2026, 12, 24, 11, 0), 7210.0),   # Early-close day, LIVE OPEN 09:30-13:00 ET
    ("USTEC", _et(2026, 12, 31, 14, 30), 26400.0), # New Year's Eve, LIVE OPEN 09:30-16:00 ET
    ("BTCUSD", _et(2026, 12, 25, 11, 0), 95000.0), # Christmas Day, BTC 24/7 LIVE OPEN
    ("EURUSD", _et(2026, 12, 24, 14, 30), 1.0850), # FX spot open on Christmas Eve afternoon
    ("USOIL", _et(2027, 1, 18, 11, 0), 71.50),     # WTI open on MLK Day morning
])
def test_live_mid_session_scale_mismatch_always_fails_closed_without_quote_shopping(cal_file, market, captured, base_price):
    tol = guard.CORE_MARKETS[market]["max_difference_pct"]
    live_good = _cfd_quote(market, base_price, captured - timedelta(seconds=10), known_at=captured)
    matching_snap = _snap(market, base_price, captured)
    ok = guard.guard_chart_scale(market, matching_snap, [live_good], calendar_path=cal_file)
    assert ok["allowed"] is True
    assert ok["verdict"] == "PASS_LIVE_SESSION"
    assert ok["comparison_basis"] == "AT_CAPTURE"

    # Exceeds market tolerance -> immediate fail closed even if a 2nd quote agrees with the bad chart!
    off_price = base_price * (1.0 + (tol + 0.25) / 100.0)
    off_snap = _snap(market, off_price, captured)
    convenient_second = _cfd_quote(market, off_price, captured - timedelta(seconds=5), known_at=captured)
    with pytest.raises(guard.HolidayChartGuardError, match="TRADINGVIEW_PRICE_SCALE_MISMATCH") as exc_info:
        guard.guard_chart_scale(market, off_snap, [live_good, convenient_second], calendar_path=cal_file)
    assert exc_info.value.details["verdict"] == "FAIL_LIVE_SCALE_MISMATCH"
    assert exc_info.value.details["allowed"] is False

    # raise_on_mismatch=False returns structured refusal dict cleanly without quote shopping.
    non_raising = guard.guard_chart_scale(
        market, off_snap, [live_good, convenient_second], calendar_path=cal_file, raise_on_mismatch=False
    )
    assert non_raising["allowed"] is False
    assert non_raising["verdict"] == "FAIL_LIVE_SCALE_MISMATCH"
    assert non_raising["cause"] == "TRADINGVIEW_PRICE_SCALE_MISMATCH"


def test_settlement_window_exact_boundaries_anti_abuse_and_causality(cal_file):
    captured = _et(2026, 12, 24, 15, 30)
    snap = _snap("US500", 7200.0, captured)

    # Exact +5400s (14:30:00 ET) PASSES; +5401s (14:30:01 ET) REJECTED.
    at_5400 = _settlement_quote("US500", 7200.0, _et(2026, 12, 24, 14, 30, 0))
    assert guard.guard_chart_scale("US500", snap, [at_5400], calendar_path=cal_file)["verdict"] == "PASS_CASH_SETTLEMENT"

    at_5401 = _settlement_quote("US500", 7200.0, _et(2026, 12, 24, 14, 30, 1))
    res_late = guard.guard_chart_scale("US500", snap, [at_5401], calendar_path=cal_file)
    assert res_late["comparison_basis"] == "NOT_COMPARED"
    assert res_late["rejected_candidates"][0]["cause"] == "SETTLEMENT_PRINT_TOO_LATE"

    # Exact -120s (12:58:00 ET) PASSES; -121s (12:57:59 ET) REJECTED.
    at_m120 = _settlement_quote("US500", 7200.0, _et(2026, 12, 24, 12, 58, 0))
    assert guard.guard_chart_scale("US500", snap, [at_m120], calendar_path=cal_file)["verdict"] == "PASS_CASH_SETTLEMENT"

    at_m121 = _settlement_quote("US500", 7200.0, _et(2026, 12, 24, 12, 57, 59))
    res_old = guard.guard_chart_scale("US500", snap, [at_m121], calendar_path=cal_file)
    assert res_old["rejected_candidates"][0]["cause"] == "SETTLEMENT_PRINT_TOO_OLD"

    # Broker/CFD bar at 13:30 ET (+30m) NEVER gets the +90m settlement window.
    cfd_plus30 = _cfd_quote("US500", 7200.0, _et(2026, 12, 24, 13, 30, 0), source_kind="BAR_STORE_M1_CLOSE")
    res_cfd = guard.guard_chart_scale("US500", snap, [cfd_plus30], calendar_path=cal_file)
    assert res_cfd["comparison_basis"] == "NOT_COMPARED"
    assert res_cfd["rejected_candidates"][0]["cause"] == "CFD_QUOTE_AFTER_CASH_CLOSE"

    # Close-anchored broker bar right at 12:59:30 ET DOES pass cleanly.
    cfd_at_close = _cfd_quote("US500", 7200.0, _et(2026, 12, 24, 12, 59, 30), source_kind="BAR_STORE_M1_CLOSE")
    res_close_bar = guard.guard_chart_scale("US500", snap, [cfd_at_close], calendar_path=cal_file)
    assert res_close_bar["verdict"] == "PASS_LAST_CLOSE"
    assert res_close_bar["settlement_print_lawful"] is False

    # Futures proxy (ES=F / FUTURE) disguised as PUBLIC_ON_DEMAND_QUOTE is strictly forbidden!
    proxy_fut = _settlement_quote("US500", 7200.0, _et(2026, 12, 24, 13, 30), source_symbol="ES=F", instrument_type="FUTURE")
    with pytest.raises(guard.HolidayChartGuardError, match="SETTLEMENT_PROXY_INSTRUMENT_FORBIDDEN"):
        guard.guard_chart_scale("US500", snap, [proxy_fut], calendar_path=cal_file)

    proxy_sym = _settlement_quote("USTEC", 26300.0, _et(2026, 12, 24, 13, 30), source_symbol="NQ=F", instrument_type="INDEX")
    with pytest.raises(guard.HolidayChartGuardError, match="SETTLEMENT_PROXY_INSTRUMENT_FORBIDDEN"):
        guard.guard_chart_scale("USTEC", _snap("USTEC", 26300.0, captured), [proxy_sym], calendar_path=cal_file)

    # Causality violations: observed > known, known > captured, observed > captured.
    early_cap = _et(2026, 12, 24, 13, 30)
    future_obs = _settlement_quote("US500", 7200.0, _et(2026, 12, 24, 13, 45), known_at=_et(2026, 12, 24, 13, 29))
    ev1 = guard.evaluate_quote_for_session("US500", 7200.0, early_cap, future_obs, calendar_path=cal_file)
    assert ev1["usable"] is False and ev1["cause"] == "OBSERVED_AFTER_KNOWN"

    future_known = _settlement_quote("US500", 7200.0, _et(2026, 12, 24, 13, 25), known_at=_et(2026, 12, 24, 13, 31))
    ev2 = guard.evaluate_quote_for_session("US500", 7200.0, early_cap, future_known, calendar_path=cal_file)
    assert ev2["usable"] is False and ev2["cause"] == "FUTURE_KNOWN_CLOCK"


def test_historical_visible_window_and_usoil_level_offset(cal_file):
    captured = _et(2026, 12, 25, 11, 0)
    vis_from = _et(2026, 12, 24, 9, 30)
    vis_to = _et(2026, 12, 24, 12, 0)
    hist_snap = _snap(
        "US500", 7205.0, captured,
        visible_from_utc=vis_from.isoformat(),
        visible_to_utc=vis_to.isoformat(),
        visible_last_price=7205.0,
    )
    bar_q = _cfd_quote("US500", 7205.0, vis_to, known_at=vis_to, source_kind="HELD_M15_RESOLUTION_CLOSE")
    res = guard.guard_chart_scale("US500", hist_snap, [bar_q], calendar_path=cal_file)
    assert res["allowed"] is True
    assert res["comparison_basis"] == "VISIBLE_WINDOW_CLOSE"
    assert res["comparison_at_utc"] == vis_to.isoformat()
    assert res["visible_from_utc"] == vis_from.isoformat()
    assert res["visible_to_utc"] == vis_to.isoformat()

    # Inverted historical window fails closed.
    bad_hist = {**hist_snap, "visible_from_utc": vis_to.isoformat(), "visible_to_utc": vis_from.isoformat()}
    with pytest.raises(guard.HolidayChartGuardError, match="TRADINGVIEW_HISTORICAL_WINDOW_INVALID"):
        guard.guard_chart_scale("US500", bad_hist, [bar_q], calendar_path=cal_file)

    # USOIL level_offset: non-zero for plan_feed, 0.0 for chart_futures.
    oil_cap = _et(2026, 12, 24, 11, 0)
    oil_snap = _snap("USOIL", 70.10, oil_cap)
    oil_plan = _cfd_quote("USOIL", 70.00, oil_cap - timedelta(seconds=10), known_at=oil_cap, price_basis="plan_feed")
    oil_fut = _cfd_quote("USOIL", 70.00, oil_cap - timedelta(seconds=10), known_at=oil_cap, price_basis="chart_futures")
    assert guard.guard_chart_scale("USOIL", oil_snap, [oil_plan], calendar_path=cal_file)["level_offset"] == pytest.approx(0.10)
    assert guard.guard_chart_scale("USOIL", oil_snap, [oil_fut], calendar_path=cal_file)["level_offset"] == 0.0


# ---------------------------------------------------------------------------
# 4. Strict Rejection of Naive Timestamps, NaN / Inf / Bool, Bad Markets
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("bad_ts", [
    datetime(2026, 12, 24, 14, 0),
    datetime(2026, 12, 24, 14, 0, tzinfo=_NullOffsetTz()),
    "2026-12-24T14:00:00",
    "2026-12-24 14:00:00",
    "2026-12-24",
    "",
    None,
    True,
    False,
    1766584800,
    date(2026, 12, 24),
])
def test_rejects_all_naive_and_non_aware_timestamps(cal_file, bad_ts):
    with pytest.raises(guard.HolidayChartGuardError, match="NAIVE_TIMESTAMP_FORBIDDEN"):
        guard.resolve_market_session("US500", bad_ts, calendar_path=cal_file)
    with pytest.raises(guard.HolidayChartGuardError, match="NAIVE_TIMESTAMP_FORBIDDEN"):
        guard.evaluate_wrap_cadence(bad_ts, calendar_path=cal_file)


@pytest.mark.parametrize("bad_num,expected_cause", [
    (True, "BOOL_NUMBER_FORBIDDEN"),
    (False, "BOOL_NUMBER_FORBIDDEN"),
    (float("nan"), "NON_FINITE_NUMBER_FORBIDDEN"),
    (float("inf"), "NON_FINITE_NUMBER_FORBIDDEN"),
    (float("-inf"), "NON_FINITE_NUMBER_FORBIDDEN"),
    ("NaN", "NON_FINITE_NUMBER_FORBIDDEN"),
    ("Infinity", "NON_FINITE_NUMBER_FORBIDDEN"),
    ("-inf", "NON_FINITE_NUMBER_FORBIDDEN"),
    (Decimal("NaN"), "NON_FINITE_NUMBER_FORBIDDEN"),
    (Decimal("Infinity"), "NON_FINITE_NUMBER_FORBIDDEN"),
    (0, "NON_POSITIVE_NUMBER_FORBIDDEN"),
    (-0.0, "NON_POSITIVE_NUMBER_FORBIDDEN"),
    (-50.0, "NON_POSITIVE_NUMBER_FORBIDDEN"),
    ("true", "INVALID_NUMERIC_VALUE"),
    (None, "INVALID_NUMERIC_VALUE"),
    ("not-a-number", "INVALID_NUMERIC_VALUE"),
])
def test_rejects_bool_nan_inf_and_non_positive_prices(cal_file, bad_num, expected_cause):
    ts = _et(2026, 12, 24, 11, 0)
    good_q = _cfd_quote("US500", 7200.0, ts - timedelta(seconds=10), known_at=ts)
    with pytest.raises(guard.HolidayChartGuardError, match=expected_cause):
        guard.evaluate_quote_for_session("US500", bad_num, ts, good_q, calendar_path=cal_file)

    bad_q = {**good_q, "price": bad_num}
    with pytest.raises(guard.HolidayChartGuardError, match=expected_cause):
        guard.evaluate_quote_for_session("US500", 7200.0, ts, bad_q, calendar_path=cal_file)


@pytest.mark.parametrize("bad_tol,expected_cause", [
    (True, "BOOL_NUMBER_FORBIDDEN"),
    (False, "BOOL_NUMBER_FORBIDDEN"),
    (float("nan"), "NON_FINITE_NUMBER_FORBIDDEN"),
    (float("inf"), "NON_FINITE_NUMBER_FORBIDDEN"),
    (-0.01, "NEGATIVE_NUMBER_FORBIDDEN"),
])
def test_rejects_invalid_tolerances(cal_file, bad_tol, expected_cause):
    ts = _et(2026, 12, 24, 11, 0)
    good_q = _cfd_quote("US500", 7200.0, ts - timedelta(seconds=10), known_at=ts)
    with pytest.raises(guard.HolidayChartGuardError, match=expected_cause):
        guard.evaluate_quote_for_session("US500", 7200.0, ts, good_q, calendar_path=cal_file, max_difference_pct=bad_tol)


@pytest.mark.parametrize("bad_market", ["SPX", "NDX", "AAPL", "", None, True, 123, "us500"])
def test_rejects_unsupported_markets(cal_file, bad_market):
    with pytest.raises(guard.HolidayChartGuardError, match="UNSUPPORTED_MARKET"):
        guard.resolve_market_session(bad_market, _et(2026, 12, 24, 11, 0), calendar_path=cal_file)


def test_rejects_bad_quote_metadata_and_snapshot_symbol_mismatch(cal_file):
    ts = _et(2026, 12, 24, 11, 0)
    good_q = _cfd_quote("US500", 7200.0, ts - timedelta(seconds=5), known_at=ts)
    with pytest.raises(guard.HolidayChartGuardError, match="TRADINGVIEW_MARKET_SYMBOL_MISMATCH"):
        guard.guard_chart_scale("US500", {**_snap("US500", 7200.0, ts), "tv_symbol": "NASDAQ:NDX"}, [good_q], calendar_path=cal_file)
    with pytest.raises(guard.HolidayChartGuardError, match="TRADINGVIEW_PLAN_QUOTE_INSTRUMENT_MISMATCH"):
        guard.guard_chart_scale("US500", _snap("US500", 7200.0, ts), [{**good_q, "instrument": "USTEC"}], calendar_path=cal_file)
    with pytest.raises(guard.HolidayChartGuardError, match="TRADINGVIEW_PLAN_QUOTE_SOURCE_REQUIRED"):
        guard.guard_chart_scale("US500", _snap("US500", 7200.0, ts), [{**good_q, "source_sha256": ""}], calendar_path=cal_file)
    with pytest.raises(guard.HolidayChartGuardError, match="NAIVE_TIMESTAMP_FORBIDDEN"):
        guard.guard_chart_scale("US500", _snap("US500", 7200.0, ts), [{**good_q, "quoted_at_utc": "2026-12-24T11:00:00"}], calendar_path=cal_file)


# ---------------------------------------------------------------------------
# 5. Dec-2026 / Jan-2027 / Feb-2027 Wrap Cadence, Follow-Ups & Live Module Parity
# ---------------------------------------------------------------------------

def test_dec_jan_feb_wrap_cadence_audit_matrix_and_parity_with_market_wrap_sources(cal_file):
    matrix = guard.dec_jan_holiday_audit_matrix(calendar_path=cal_file)
    by_day = {row["day_et"]: row for row in matrix}
    assert len(matrix) == 12

    # 24 Dec (Christmas Eve early close): daily wrap DUE (08:00-08:45 ET), prior close = 23 Dec 16:00 ET
    assert by_day["2026-12-24"]["us_cash_session_state"] == "EARLY_CLOSE_13_ET"
    assert by_day["2026-12-24"]["wrap_cadence_status"] == "DUE"
    assert by_day["2026-12-24"]["wrap_slot_id"] == "cc689-daily-2026-12-24"
    assert by_day["2026-12-24"]["last_cash_session_et"] == "2026-12-23"

    # 25 Dec (Christmas Day): daily wrap HOLIDAY_SUPPRESSED, last close = 24 Dec 13:00 ET
    assert by_day["2026-12-25"]["us_cash_session_state"] == "CLOSED_HOLIDAY"
    assert by_day["2026-12-25"]["holiday_label"] == "CHRISTMAS_DAY"
    assert by_day["2026-12-25"]["wrap_cadence_status"] == "HOLIDAY_SUPPRESSED"
    assert by_day["2026-12-25"]["wrap_slot_id"] is None
    assert by_day["2026-12-25"]["last_cash_session_et"] == "2026-12-24"
    assert by_day["2026-12-25"]["last_cash_close_utc"] == "2026-12-24T18:00:00+00:00"

    # 27 Dec (Sun weekly post-Christmas): last = 24 Dec 13:00 ET, prior = 18 Dec 16:00 ET
    assert by_day["2026-12-27"]["wrap_edition"] == "weekly"
    assert by_day["2026-12-27"]["wrap_cadence_status"] == "DUE"
    assert by_day["2026-12-27"]["last_cash_session_et"] == "2026-12-24"
    assert by_day["2026-12-27"]["last_cash_close_utc"] == "2026-12-24T18:00:00+00:00"
    assert by_day["2026-12-27"]["prior_weekly_session_et"] == "2026-12-18"

    # 28 Dec (Mon post-Christmas): daily wrap DUE, morning map settlement window spans 13:00-14:30 ET (24 Dec)
    mon_post_xmas = guard.evaluate_wrap_cadence(_et(2026, 12, 28, 8, 15), calendar_path=cal_file)
    assert mon_post_xmas["last_cash_session_et"] == "2026-12-24"
    assert mon_post_xmas["last_cash_session_early_close"] is True
    mm_opts = mon_post_xmas["morning_map_cash_index_quote_options"]
    assert mm_opts["closed_cash_index"] is True
    assert mm_opts["reference_at_utc"] == "2026-12-24T18:00:00+00:00"
    assert mm_opts["settlement_window_end_utc"] == "2026-12-24T19:30:00+00:00"

    # 31 Dec (NYE regular equity session): daily wrap DUE
    assert by_day["2026-12-31"]["us_cash_session_state"] == "REGULAR_SESSION"
    assert by_day["2026-12-31"]["holiday_label"] == "NEW_YEARS_EVE_REGULAR"
    assert by_day["2026-12-31"]["wrap_cadence_status"] == "DUE"

    # 1 Jan 2027 (New Year's Day): HOLIDAY_SUPPRESSED, crosses year boundary -> 2026-12-31 16:00 ET
    assert by_day["2027-01-01"]["wrap_cadence_status"] == "HOLIDAY_SUPPRESSED"
    assert by_day["2027-01-01"]["holiday_label"] == "NEW_YEARS_DAY"
    assert by_day["2027-01-01"]["last_cash_session_et"] == "2026-12-31"
    assert by_day["2027-01-01"]["last_cash_close_utc"] == "2026-12-31T21:00:00+00:00"

    # 3 Jan 2027 (Sun weekly): crosses year boundary -> last = 2026-12-31 16:00 ET, prior = 2026-12-24 13:00 ET!
    assert by_day["2027-01-03"]["wrap_edition"] == "weekly"
    assert by_day["2027-01-03"]["last_cash_session_et"] == "2026-12-31"
    assert by_day["2027-01-03"]["last_cash_close_utc"] == "2026-12-31T21:00:00+00:00"
    assert by_day["2027-01-03"]["prior_weekly_session_et"] == "2026-12-24"
    assert by_day["2027-01-03"]["prior_weekly_close_utc"] == "2026-12-24T18:00:00+00:00"

    # 18 Jan 2027 (MLK Day) & 15 Feb 2027 (Presidents' Day): HOLIDAY_SUPPRESSED, next-day wraps anchored to Fri!
    assert by_day["2027-01-18"]["wrap_cadence_status"] == "HOLIDAY_SUPPRESSED"
    assert by_day["2027-01-19"]["last_cash_session_et"] == "2027-01-15"
    assert by_day["2027-02-15"]["wrap_cadence_status"] == "HOLIDAY_SUPPRESSED"
    assert by_day["2027-02-16"]["last_cash_session_et"] == "2027-02-12"

    # Exact parity with live market_wrap_sources_v1.slot_at / last_session / cash_close on every milestone date!
    for iso in guard.DEC_JAN_FEB_MILESTONE_DATES:
        day_obj = date.fromisoformat(iso)
        probe = (
            datetime(day_obj.year, day_obj.month, day_obj.day, 15, 30, tzinfo=timezone.utc)
            if day_obj.weekday() == 6
            else _et(day_obj.year, day_obj.month, day_obj.day, 8, 15)
        )
        g_wrap = guard.evaluate_wrap_cadence(probe, calendar=CANONICAL_CALENDAR_2026_2028)
        m_slot = wrap_sources.slot_at(probe, CANONICAL_CALENDAR_2026_2028)
        assert g_wrap["slot"] == m_slot
        if m_slot is not None:
            weekly = m_slot["edition"] == "weekly"
            m_last = wrap_sources.last_session(day_obj - timedelta(days=2 if weekly else 1), CANONICAL_CALENDAR_2026_2028)
            assert g_wrap["last_cash_session_et"] == m_last.isoformat()
            m_close = wrap_sources.cash_close(m_last, CANONICAL_CALENDAR_2026_2028).astimezone(timezone.utc)
            assert g_wrap["last_cash_close_utc"] == m_close.isoformat()


def test_parity_with_publication_image_contract_and_call_followups_and_trend_board(cal_file, monkeypatch):
    monkeypatch.setattr(contract, "CASH_CALENDAR", cal_file)

    # 1. Exact 7-market comparison_clock parity with publication_image_contract_v1
    probes = [
        _et(2026, 12, 24, 8, 30),
        _et(2026, 12, 24, 11, 0),
        _et(2026, 12, 24, 14, 0),
        _et(2026, 12, 25, 11, 0),
        _et(2026, 12, 27, 15, 0),
        _et(2026, 12, 31, 14, 30),
        _et(2027, 1, 1, 11, 0),
        _et(2027, 1, 18, 11, 0),
        _et(2027, 2, 15, 11, 0),
    ]
    for market in guard.CORE_MARKET_ORDER:
        for ts in probes:
            assert guard.comparison_clock(market, ts, calendar_path=cal_file, enforce_cme_full_day_holidays=False) == (
                contract.comparison_clock(market, ts, calendar_path=cal_file)
            )

    # 2. Exact CC-778 follow-up bar window parity with call_followups_v1.cash_session_open_for_bar
    bar_cases = [
        # Dec 24 early close: 15m inside [09:30, 13:00], 15m after 13:00, coarse 4h resolved at 12:30 vs 13:15
        ("US500", _et(2026, 12, 24, 12, 45), _et(2026, 12, 24, 13, 0), _et(2026, 12, 24, 13, 0), True),
        ("USTEC", _et(2026, 12, 24, 13, 0), _et(2026, 12, 24, 13, 15), _et(2026, 12, 24, 13, 15), False),
        ("US500", _et(2026, 12, 24, 11, 0), _et(2026, 12, 24, 15, 0), _et(2026, 12, 24, 12, 30), True),
        ("USTEC", _et(2026, 12, 24, 11, 0), _et(2026, 12, 24, 15, 0), _et(2026, 12, 24, 13, 15), False),
        # Dec 25 Christmas Day closed, Jan 1 closed, Jan 18 MLK closed, Feb 15 Presidents' Day closed
        ("US500", _et(2026, 12, 25, 10, 45), _et(2026, 12, 25, 11, 0), _et(2026, 12, 25, 11, 0), False),
        ("USTEC", _et(2027, 1, 1, 10, 45), _et(2027, 1, 1, 11, 0), _et(2027, 1, 1, 11, 0), False),
        ("US500", _et(2027, 1, 18, 10, 45), _et(2027, 1, 18, 11, 0), _et(2027, 1, 18, 11, 0), False),
        ("USTEC", _et(2027, 2, 15, 10, 45), _et(2027, 2, 15, 11, 0), _et(2027, 2, 15, 11, 0), False),
        # Dec 31 NYE regular session: 14:45-15:00 ET allowed, 16:00-16:15 ET refused
        ("US500", _et(2026, 12, 31, 14, 45), _et(2026, 12, 31, 15, 0), _et(2026, 12, 31, 15, 0), True),
        ("USTEC", _et(2026, 12, 31, 16, 0), _et(2026, 12, 31, 16, 15), _et(2026, 12, 31, 16, 15), False),
        # Non-cash-index always allowed on holiday window
        ("XAUUSD", _et(2026, 12, 25, 10, 45), _et(2026, 12, 25, 11, 0), _et(2026, 12, 25, 11, 0), True),
        ("BTCUSD", _et(2027, 1, 1, 10, 45), _et(2027, 1, 1, 11, 0), _et(2027, 1, 1, 11, 0), True),
    ]
    for market, b_open, b_end, resolved, expected in bar_cases:
        g_res = guard.evaluate_followup_chart_window(
            market, b_open, b_end, resolved_at_utc=resolved, calendar_path=cal_file
        )
        f_res = followups.cash_session_open_for_bar(
            market, b_open, b_end, resolved_at_utc=resolved, calendar_path=cal_file
        )
        assert g_res["allowed"] is expected
        assert f_res is expected
        if not expected:
            assert g_res["refusal"] == f"CC778_CHART_MARKET_CLOSED_AT_RESOLUTION:{tv.SYMBOLS[market]}"
        else:
            assert g_res["refusal"] is None

    # 3. Daily trend board us_trading_age skips Christmas Day, New Year's Day, MLK Day, Presidents' Day cleanly
    assert trend_board.us_trading_age("2026-12-24", "2026-12-28", calendar_path=cal_file) == 1
    assert trend_board.us_trading_age("2026-12-31", "2027-01-04", calendar_path=cal_file) == 1
    assert trend_board.us_trading_age("2027-01-15", "2027-01-19", calendar_path=cal_file) == 1
    assert trend_board.us_trading_age("2027-02-12", "2027-02-16", calendar_path=cal_file) == 1


def test_followup_window_rejects_inverted_bar_and_out_of_bar_resolution(cal_file):
    t1 = _et(2026, 12, 24, 11, 0)
    t2 = _et(2026, 12, 24, 11, 15)
    with pytest.raises(guard.HolidayChartGuardError, match="INVALID_BAR_WINDOW"):
        guard.evaluate_followup_chart_window("US500", t2, t1, calendar_path=cal_file)
    with pytest.raises(guard.HolidayChartGuardError, match="RESOLVED_AT_OUTSIDE_BAR_WINDOW"):
        guard.evaluate_followup_chart_window("US500", t1, t2, resolved_at_utc=t1, calendar_path=cal_file)
    with pytest.raises(guard.HolidayChartGuardError, match="RESOLVED_AT_OUTSIDE_BAR_WINDOW"):
        guard.evaluate_followup_chart_window(
            "US500", t1, t2, resolved_at_utc=t2 + timedelta(seconds=1), calendar_path=cal_file
        )


# ---------------------------------------------------------------------------
# 6. B16 C20b Unified 6M / 4L Hardening Regressions (DA8 + B176 + B175)
# ---------------------------------------------------------------------------

def test_da8_t2b_m1_non_finite_percent_difference_fails_closed_on_all_paths(cal_file):
    # (a) raise_on_mismatch=False with 1e308 vs 1e-300 must fail closed (never leak float('inf')).
    live_ts = _et(2026, 12, 24, 11, 0)
    tiny_q = _cfd_quote("US500", 1e-300, live_ts - timedelta(seconds=5), known_at=live_ts)
    huge_snap = _snap("US500", 1e308, live_ts, chart_price=1e308)
    with pytest.raises(guard.HolidayChartGuardError, match="NON_FINITE_PERCENT_DIFFERENCE"):
        guard.guard_chart_scale("US500", huge_snap, [tiny_q], calendar_path=cal_file, raise_on_mismatch=False)

    # (b) Default raise_on_mismatch=True on Dec-25 holiday CFD drift (1e308 vs 1e-300) must ALSO fail closed
    # instead of returning allowed=True with suppressed_cfd_difference_pct=inf!
    xmas_ts = _et(2026, 12, 25, 11, 0)
    xmas_cfd = _cfd_quote("US500", 1e-300, xmas_ts - timedelta(seconds=10), known_at=xmas_ts)
    xmas_snap = _snap("US500", 1e308, xmas_ts, chart_price=1e308)
    with pytest.raises(guard.HolidayChartGuardError, match="NON_FINITE_PERCENT_DIFFERENCE"):
        guard.guard_chart_scale("US500", xmas_snap, [xmas_cfd], calendar_path=cal_file)

    # (c) Precision overflow on * 100.0 (1e307 / 0.1 == 1e308 finite, * 100.0 == inf) on both live and holiday paths.
    q_tenth = _cfd_quote("US500", 0.1, live_ts - timedelta(seconds=5), known_at=live_ts)
    with pytest.raises(guard.HolidayChartGuardError, match="NON_FINITE_PERCENT_DIFFERENCE"):
        guard.evaluate_quote_for_session("US500", 1e307, live_ts, q_tenth, calendar_path=cal_file)
    xmas_q_tenth = _cfd_quote("US500", 0.1, xmas_ts - timedelta(seconds=5), known_at=xmas_ts)
    xmas_snap_307 = _snap("US500", 1e307, xmas_ts, chart_price=1e307)
    with pytest.raises(guard.HolidayChartGuardError, match="NON_FINITE_PERCENT_DIFFERENCE"):
        guard.guard_chart_scale("US500", xmas_snap_307, [xmas_q_tenth], calendar_path=cal_file)

    # (d) Valid responses across all paths are strictly JSON-serializable with allow_nan=False.
    good_q = _cfd_quote("US500", 7200.0, live_ts - timedelta(seconds=5), known_at=live_ts)
    valid_live = guard.guard_chart_scale("US500", _snap("US500", 7200.0, live_ts), [good_q], calendar_path=cal_file)
    valid_mismatch = guard.guard_chart_scale(
        "US500", _snap("US500", 7300.0, live_ts), [good_q], calendar_path=cal_file, raise_on_mismatch=False
    )
    drifting_cfd = _cfd_quote("US500", 7260.0, xmas_ts - timedelta(seconds=10), known_at=xmas_ts)
    valid_suppressed = guard.guard_chart_scale("US500", _snap("US500", 7200.0, xmas_ts), [drifting_cfd], calendar_path=cal_file)
    for payload in (valid_live, valid_mismatch, valid_suppressed):
        encoded = json.dumps(payload, allow_nan=False, ensure_ascii=False).encode("utf-8")
        assert len(encoded) > 0


def test_da8_t2b_m2_and_l3_deep_copy_cache_private_sentinel_and_explicit_allow_fallback(cal_file, tmp_path):
    # Mutating a loaded bundle must NEVER poison the module-level cache for subsequent callers.
    b1 = guard.load_us_session_calendar(calendar_path=cal_file)
    assert len(b1["years"][2026]["closed"]) == 10
    b1["years"][2026]["closed"] = frozenset()
    b1["years"][2026]["early_close_13_et"] = frozenset()

    b2 = guard.load_us_session_calendar(calendar_path=cal_file)
    assert len(b2["years"][2026]["closed"]) == 10
    assert "2026-12-25" in b2["years"][2026]["closed"]

    b2["years"].clear()
    b3 = guard.load_us_session_calendar(calendar_path=cal_file)
    assert len(b3["years"][2026]["closed"]) == 10
    assert guard.classify_us_cash_day("2026-12-25", calendar_path=cal_file)["session_state"] == "CLOSED_HOLIDAY"

    # Mutating a genuine bundle into a corrupt structure and passing it back fails closed.
    b3["years"] = "CORRUPTED"
    with pytest.raises(guard.HolidayChartGuardError, match="HOLIDAY_CALENDAR_SCHEMA_INVALID"):
        guard.load_us_session_calendar(calendar=b3)

    # Forged _normalized_holiday_calendar marker is rejected unconditionally (both allow_fallback=False and True).
    for forged in (
        {"_normalized_holiday_calendar": True, "years": "NOT_A_DICT"},
        {"_normalized_holiday_calendar": True, "years": {"2026": {"closed": [], "early_close_13_et": []}}},
        {"_normalized_holiday_calendar": object(), "years": {2026: {"closed": frozenset(), "early_close_13_et": frozenset()}}},
    ):
        with pytest.raises(guard.HolidayChartGuardError, match="HOLIDAY_CALENDAR_SCHEMA_INVALID"):
            guard.load_us_session_calendar(calendar=forged, allow_fallback=False)
        with pytest.raises(guard.HolidayChartGuardError, match="HOLIDAY_CALENDAR_SCHEMA_INVALID"):
            guard.load_us_session_calendar(calendar=forged, allow_fallback=True)

    # DA8-T2B-L3: explicit allow_fallback=False overrides a bundle previously loaded with allow_fallback=True.
    fb_bundle = guard.load_us_session_calendar(calendar_path=tmp_path / "absent.json", allow_fallback=True)
    assert fb_bundle["allow_fallback"] is True
    strict_bundle = guard.load_us_session_calendar(calendar=fb_bundle, allow_fallback=False)
    assert strict_bundle["allow_fallback"] is False
    with pytest.raises(guard.HolidayChartGuardError, match="HOLIDAY_CALENDAR_YEAR_MISSING"):
        guard.classify_us_cash_day("2026-12-25", calendar=fb_bundle, allow_fallback=False)

    cached_fb = guard.load_us_session_calendar(calendar_path=cal_file, allow_fallback=True)
    assert cached_fb["allow_fallback"] is True
    cached_strict = guard.load_us_session_calendar(calendar_path=cal_file, allow_fallback=False)
    assert cached_strict["allow_fallback"] is False
    with pytest.raises(guard.HolidayChartGuardError, match="HOLIDAY_CALENDAR_YEAR_MISSING"):
        guard.classify_us_cash_day("2029-12-25", calendar=cached_strict, allow_fallback=False)


def test_da8_t2b_m3_direct_evaluate_quote_rejects_future_visible_to_utc(cal_file):
    captured = datetime(2026, 12, 23, 16, 0, 0, tzinfo=timezone.utc)
    q = _cfd_quote("US500", 6000.0, captured, known_at=captured)
    with pytest.raises(guard.HolidayChartGuardError, match="TRADINGVIEW_HISTORICAL_WINDOW_INVALID"):
        guard.evaluate_quote_for_session(
            "US500",
            6000.0,
            captured,
            q,
            visible_to_utc="2026-12-23T16:00:30Z",
            calendar_path=cal_file,
        )

    # Boundary: visible_to_utc == captured is allowed.
    ok = guard.evaluate_quote_for_session(
        "US500",
        6000.0,
        captured,
        q,
        visible_to_utc="2026-12-23T16:00:00Z",
        calendar_path=cal_file,
    )
    assert ok["usable"] is True
    assert ok["verdict"] == "PASS_LIVE_SESSION"
    assert ok["comparison_basis"] == "VISIBLE_WINDOW_CLOSE"


def test_b176_c20_m1_extreme_utc_et_and_date_shift_overflow_fail_closed(cal_file):
    # Extreme UTC offset conversions in require_aware_utc -> UTC_CLOCK_OUT_OF_RANGE.
    for bad_extreme in (
        "0001-01-01T00:00:00+05:00",
        "9999-12-31T23:59:59-05:00",
        datetime(1, 1, 1, 0, 0, 0, tzinfo=timezone(timedelta(hours=5))),
        datetime(9999, 12, 31, 23, 59, 59, tzinfo=timezone(timedelta(hours=-5))),
    ):
        with pytest.raises(guard.HolidayChartGuardError, match="UTC_CLOCK_OUT_OF_RANGE"):
            guard.require_aware_utc(bad_extreme)

    # Valid UTC "0001-01-01T00:00:00Z" overflows on .astimezone(ET) across all three entrypoints.
    assert guard.require_aware_utc("0001-01-01T00:00:00Z") == datetime(1, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    with pytest.raises(guard.HolidayChartGuardError, match="UTC_CLOCK_OUT_OF_RANGE"):
        guard.resolve_market_session("US500", "0001-01-01T00:00:00Z", calendar_path=cal_file)
    with pytest.raises(guard.HolidayChartGuardError, match="UTC_CLOCK_OUT_OF_RANGE"):
        guard.evaluate_wrap_cadence("0001-01-01T00:00:00Z", calendar_path=cal_file)
    with pytest.raises(guard.HolidayChartGuardError, match="UTC_CLOCK_OUT_OF_RANGE"):
        guard.evaluate_followup_chart_window(
            "US500", "0001-01-01T00:00:00Z", "0001-01-01T00:15:00Z", calendar_path=cal_file
        )
    with pytest.raises(guard.HolidayChartGuardError, match="UTC_CLOCK_OUT_OF_RANGE"):
        guard.evaluate_followup_chart_window(
            "US500",
            "0001-01-01T00:00:00Z",
            "0001-01-01T01:00:00Z",
            resolved_at_utc="0001-01-01T00:30:00Z",
            calendar_path=cal_file,
        )

    # Date-shift +/- timedelta overflow at year 0001 and year 9999 boundaries.
    cal_0001 = {"schema": "IbkrUsSessionCalendarV1", "years": {"0001": {"closed": [], "early_close_13_et": []}}}
    with pytest.raises(guard.HolidayChartGuardError, match="UTC_CLOCK_OUT_OF_RANGE"):
        guard.resolve_market_session("US500", "0001-01-01T06:00:00Z", calendar=cal_0001)
    cal_9999 = {"schema": "IbkrUsSessionCalendarV1", "years": {"9999": {"closed": [], "early_close_13_et": []}}}
    with pytest.raises(guard.HolidayChartGuardError, match="UTC_CLOCK_OUT_OF_RANGE"):
        guard.evaluate_wrap_cadence("9999-12-31T14:00:00Z", calendar=cal_9999)


def test_b176_c20_m2_strict_rfc8259_calendar_json_rejects_dup_keys_nan_infinity_and_bom(tmp_path):
    dup_year = tmp_path / "dup_year.json"
    dup_year.write_text(
        '{"schema":"IbkrUsSessionCalendarV1","years":{'
        '"2026":{"closed":["2026-12-25"],"early_close_13_et":["2026-12-24"]},'
        '"2026":{"closed":[],"early_close_13_et":[]}}}',
        encoding="utf-8",
    )
    dup_closed = tmp_path / "dup_closed.json"
    dup_closed.write_text(
        '{"schema":"IbkrUsSessionCalendarV1","years":{"2026":{'
        '"closed":["2026-12-25"],"closed":[],"early_close_13_et":[]}}}',
        encoding="utf-8",
    )
    nan_cal = tmp_path / "nan_cal.json"
    nan_cal.write_text(
        '{"schema":"IbkrUsSessionCalendarV1","meta_nan":NaN,"years":{"2026":{"closed":["2026-12-25"],"early_close_13_et":[]}}}',
        encoding="utf-8",
    )
    inf_cal = tmp_path / "inf_cal.json"
    inf_cal.write_text(
        '{"schema":"IbkrUsSessionCalendarV1","meta_inf":Infinity,"years":{"2026":{"closed":["2026-12-25"],"early_close_13_et":[]}}}',
        encoding="utf-8",
    )
    bom_cal = tmp_path / "bom_cal.json"
    bom_cal.write_bytes(b"\xef\xbb\xbf" + json.dumps(CANONICAL_CALENDAR_2026_2028).encode("utf-8"))

    for bad_path in (dup_year, dup_closed, nan_cal, inf_cal, bom_cal):
        with pytest.raises(guard.HolidayChartGuardError, match="HOLIDAY_CALENDAR_CORRUPT_JSON"):
            guard.load_us_session_calendar(calendar_path=bad_path)
        # Explicit allow_fallback=True must fall back to audited NYSE rules (Christmas closed), never wiped JSON.
        fb = guard.classify_us_cash_day("2026-12-25", calendar_path=bad_path, allow_fallback=True)
        assert fb["calendar_source"] == "FALLBACK_NYSE_RULES"
        assert fb["session_state"] == "CLOSED_HOLIDAY"


def test_b175_b16c20_m4_rejects_all_hostile_windows_paths_ads_dos_and_junction_even_with_fallback(cal_file, tmp_path):
    abs_str = str(cal_file)
    abs_posix = abs_str.replace("\\", "/")
    unc_tail = abs_str[2:] if len(abs_str) >= 2 and abs_str[1] == ":" else abs_str
    drive_letter = abs_str[0] if len(abs_str) >= 2 and abs_str[1] == ":" else "C"

    hostile_paths: list[object] = [
        f"\\??\\{abs_str}",
        f"/??/{abs_posix}",
        r"\??\C:\nonexistent\cal.json",
        f"\\\\?\\{abs_str}",
        f"//?/{abs_posix}",
        f"\\\\.\\{abs_str}",
        f"//./{abs_posix}",
        f"\\\\localhost\\{drive_letter}${unc_tail}",
        f"//localhost/{drive_letter}${unc_tail.replace(chr(92), '/')}",
        f"///localhost/{drive_letter}${unc_tail.replace(chr(92), '/')}",
        f"  \\\\localhost\\{drive_letter}${unc_tail}",
        f"{drive_letter}:rel_cal.json",
        str(tmp_path / "CON .dir" / "cal.json"),
        str(tmp_path / "CON .json"),
        str(tmp_path / "COM\u00b9.json"),
        str(tmp_path / "NUL.json"),
        f"{abs_str}.",
        f"{abs_str} ",
        str(tmp_path / "staging." / "cal.json"),
        f"{abs_str}:cal.json",
        str(tmp_path / ".." / cal_file.name),
        f"{abs_str}\x00.json",
        f"{abs_str}\ud800.json",
        b"calendar.json",
        tmp_path,
    ]

    # Real NTFS ADS stream on Windows (if filesystem supports ADS).
    ads_host = tmp_path / "host.txt"
    ads_host.write_text("benign", encoding="utf-8")
    ads_stream = f"{ads_host}:cal.json"
    if sys.platform == "win32":
        try:
            with open(ads_stream, "w", encoding="utf-8") as fh:
                fh.write(json.dumps(CANONICAL_CALENDAR_2026_2028))
            hostile_paths.append(ads_stream)
        except OSError:
            pass

    # Oversized regular file (> 2 MiB) must also fail closed as HOLIDAY_CALENDAR_PATH_UNSAFE.
    big_file = tmp_path / "oversized_cal.json"
    big_file.write_bytes(b" " * (guard._MAX_CALENDAR_BYTES + 16))
    hostile_paths.append(big_file)

    for bad_path in hostile_paths:
        with pytest.raises(guard.HolidayChartGuardError, match="HOLIDAY_CALENDAR_PATH_UNSAFE"):
            guard.load_us_session_calendar(calendar_path=bad_path, allow_fallback=False)
        # Unconditional security guard: allow_fallback=True MUST NOT silently mask unsafe paths!
        with pytest.raises(guard.HolidayChartGuardError, match="HOLIDAY_CALENDAR_PATH_UNSAFE"):
            guard.load_us_session_calendar(calendar_path=bad_path, allow_fallback=True)

    # Real Windows NTFS directory junction (mklink /J) must fail closed even with allow_fallback=True.
    if sys.platform == "win32":
        real_dir = tmp_path / "real_cal_dir"
        real_dir.mkdir()
        _write_cal(real_dir / "us_session_calendar_v1.json")
        junc_dir = tmp_path / "junc_cal_dir"
        proc = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(junc_dir), str(real_dir)],
            capture_output=True,
            text=True,
            check=False,
        )
        assert proc.returncode == 0, f"mklink /J failed: {proc.stderr or proc.stdout}"
        assert os.path.isjunction(junc_dir)
        try:
            for target in (junc_dir / "us_session_calendar_v1.json", junc_dir / "missing.json", junc_dir):
                with pytest.raises(guard.HolidayChartGuardError, match="HOLIDAY_CALENDAR_PATH_UNSAFE"):
                    guard.load_us_session_calendar(calendar_path=target, allow_fallback=False)
                with pytest.raises(guard.HolidayChartGuardError, match="HOLIDAY_CALENDAR_PATH_UNSAFE"):
                    guard.load_us_session_calendar(calendar_path=target, allow_fallback=True)
        finally:
            os.rmdir(junc_dir)

    # Positive control: clean regular calendar file loads cleanly.
    loaded = guard.load_us_session_calendar(calendar_path=cal_file)
    assert loaded["source"] == "FILE"
    assert len(loaded["years"][2026]["closed"]) == 10


def test_da8_t2b_l2_l4_l5_clean_utf8_strict_sha256_source_kind_and_all_7_markets_public_quote(cal_file):
    live_ts = _et(2026, 12, 24, 11, 0)
    good_snap = _snap("US500", 7200.0, live_ts)
    good_q = _cfd_quote("US500", 7200.0, live_ts - timedelta(seconds=5), known_at=live_ts)

    # DA8-T2B-L2 & L5: surrogates, control chars, unsafe Windows paths/ADS, and non-64-hex sha256 rejected.
    for bad_sha in ("not-a-sha", "a" * 63, "a" * 65, "g" * 64, "a" * 63 + "\ud800", "a" * 63 + "\x00"):
        with pytest.raises(guard.HolidayChartGuardError, match="TRADINGVIEW_SNAPSHOT_SHA256_REQUIRED"):
            guard.guard_chart_scale("US500", {**good_snap, "sha256": bad_sha}, [good_q], calendar_path=cal_file)
        with pytest.raises(guard.HolidayChartGuardError, match="TRADINGVIEW_PLAN_QUOTE_SOURCE_REQUIRED"):
            guard.evaluate_quote_for_session("US500", 7200.0, live_ts, {**good_q, "source_sha256": bad_sha}, calendar_path=cal_file)

    for bad_source_path in (
        "obs\ud800.json",
        "obs\x00.json",
        "obs\n.json",
        r"\??\C:\obs.json",
        "/??/C:/obs.json",
        r"\\?\C:\obs.json",
        r"\\.\C:\obs.json",
        r"\\localhost\C$\obs.json",
        "//server/share/obs.json",
        "obs.json:secret",
        r"C:\dir\obs.json:stream",
        "C:obs.json",
        "../obs.json",
        "obs.json.",
        "CON .dir/obs.json",
    ):
        with pytest.raises(guard.HolidayChartGuardError, match="TRADINGVIEW_PLAN_QUOTE_SOURCE_REQUIRED"):
            guard.evaluate_quote_for_session(
                "US500", 7200.0, live_ts, {**good_q, "source_path": bad_source_path}, calendar_path=cal_file
            )

    # Uppercase valid 64-hex sha256 normalizes to lowercase; benign paths & source_kind=None remain accepted.
    upper_res = guard.guard_chart_scale(
        "US500",
        {**good_snap, "sha256": "A" * 64},
        [{**good_q, "source_kind": None, "source_path": r"A:\Capital Chronicle\Runtime\plan-status.public.json", "source_sha256": "B" * 64}],
        calendar_path=cal_file,
    )
    assert upper_res["allowed"] is True
    assert upper_res["chart_sha256"] == "a" * 64

    # Unknown non-None source_kind rejected cleanly.
    for bad_kind in ("BOGUS_SOURCE", "", 123):
        with pytest.raises(guard.HolidayChartGuardError, match="TRADINGVIEW_PLAN_QUOTE_SOURCE_KIND_INVALID"):
            guard.evaluate_quote_for_session(
                "US500", 7200.0, live_ts, {**good_q, "source_kind": bad_kind}, calendar_path=cal_file
            )

    # DA8-T2B-L4 backwards-compat with live publication_image_contract_v1.py:315-316:
    # US500/USTEC PUBLIC_ON_DEMAND_QUOTE with instrument_type="INDEX" and source_symbol=None MUST STILL PASS.
    settle_cap = _et(2026, 12, 24, 14, 20)
    settle_obs = _et(2026, 12, 24, 13, 55)
    compat_q = {
        "market": "US500",
        "instrument": "US500",
        "price": 7200.0,
        "quoted_at_utc": settle_obs.isoformat(),
        "known_at_utc": settle_obs.isoformat(),
        "source_kind": "PUBLIC_ON_DEMAND_QUOTE",
        "instrument_type": "INDEX",
        "source_path": "public-quotes/obs.json",
        "source_sha256": "c" * 64,
    }
    compat_res = guard.guard_chart_scale("US500", _snap("US500", 7200.0, settle_cap), [compat_q], calendar_path=cal_file)
    assert compat_res["allowed"] is True
    assert compat_res["verdict"] == "PASS_CASH_SETTLEMENT"

    # DA8-T2B-L4 extended across non-cash markets: wrong source_symbol / instrument_type rejected when supplied,
    # while matching or omitted (None) fields remain allowed.
    for mkt, price, wrong_sym, wrong_type in (
        ("XAUUSD", 2650.0, "GC=F", "FUTURE"),
        ("EURUSD", 1.0850, "GBPUSD=X", "EQUITY"),
        ("USDJPY", 155.20, "EURJPY=X", "EQUITY"),
        ("USOIL", 70.50, "BZ=F", "INDEX"),
        ("BTCUSD", 95000.0, "ETH-USD", "CURRENCY"),
    ):
        spec = guard.CORE_MARKETS[mkt]
        base_pub = {
            "market": mkt,
            "instrument": mkt,
            "price": price,
            "quoted_at_utc": (live_ts - timedelta(seconds=5)).isoformat(),
            "known_at_utc": live_ts.isoformat(),
            "source_kind": "PUBLIC_ON_DEMAND_QUOTE",
            "source_path": "public-quotes/obs.json",
            "source_sha256": "d" * 64,
        }
        # Omitted source_symbol/instrument_type passes.
        assert guard.evaluate_quote_for_session(mkt, price, live_ts, base_pub, calendar_path=cal_file)["verdict"] == "PASS_LIVE_SESSION"
        # Matching source_symbol/instrument_type passes.
        matched_pub = {
            **base_pub,
            "source_symbol": spec["public_quote_symbol"],
            "instrument_type": spec["public_instrument_type"],
        }
        assert guard.evaluate_quote_for_session(mkt, price, live_ts, matched_pub, calendar_path=cal_file)["verdict"] == "PASS_LIVE_SESSION"
        # Wrong source_symbol fails closed.
        with pytest.raises(guard.HolidayChartGuardError, match="SETTLEMENT_PROXY_INSTRUMENT_FORBIDDEN"):
            guard.evaluate_quote_for_session(mkt, price, live_ts, {**base_pub, "source_symbol": wrong_sym}, calendar_path=cal_file)
        # Wrong instrument_type fails closed.
        with pytest.raises(guard.HolidayChartGuardError, match="SETTLEMENT_PROXY_INSTRUMENT_FORBIDDEN"):
            guard.evaluate_quote_for_session(mkt, price, live_ts, {**base_pub, "instrument_type": wrong_type}, calendar_path=cal_file)
