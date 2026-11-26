"""Hermetic BF-M2 regression tests for live_contentops/call_followups_v1.py.

Covers:
1. Coarse chart bar (60m / 240m / D) US cash-session resolution checks on
   Black Friday 13:00 ET early close, Thanksgiving full closure, normal sessions,
   and summer EDT early close — without loosening genuine closed-session refusals.
2. Scheduled broker/exchange closure gaps in check_path() (Mon-Thu daily break,
   weekends, Thanksgiving CME halt, Black Friday early close, Christmas Eve +
   Christmas Day, Good Friday, DST fall-back) — without weakening genuine
   intraday or reopen missing-bar rejection (CC603_HELD_PRICE_GAP*).

Zero live writes, zero network/browser calls, zero A:\\ mutations.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path

import pytest

from live_contentops import call_followups_v1 as f
from live_contentops import plan_status_posts_v1 as posts
from live_contentops import publication_image_contract_v1 as contract
from live_contentops import tradingview_snapshot_v1 as tv


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


def _followup_row(symbol: str, published: datetime, resolved: datetime) -> dict:
    return {
        "key": f"cc603-followup-bfm2-{symbol.lower()}",
        "kind": "call_followup",
        "symbol": symbol,
        "cc603_destinations": ["telegram", "discord"],
        "candidate": {
            "published_at_utc": published.isoformat(),
            "zone_low": 5950.0,
            "zone_high": 5960.0,
            "direction": "bearish",
            "invalidation": {"field": "high", "level": 6050.0, "side": "above"},
        },
        "price_check": {"resolved_at_utc": resolved.isoformat()},
    }


def _candidate(symbol: str, start: datetime, end: datetime, *, direction: str = "bearish") -> dict:
    terms = {
        "market": posts.TITLES.get(symbol, symbol),
        "condition": "price trades into 110–112",
        "direction": direction,
        "horizon": "end of window",
        "invalidation": "price moves above 120" if direction == "bearish" else "price moves below 80",
    }
    quote = posts.conditional_call_text(terms)
    return {
        "call_id": f"bfm2-{symbol.lower()}-{int(start.timestamp())}",
        "plan_id": f"plan-{symbol.lower()}",
        "symbol": symbol,
        "source_kind": "AS_WRITTEN",
        "short_id": "a0380280",
        "terms": terms,
        "quote": quote,
        "original_text": quote,
        "original_url": "https://t.me/CapitalChronicle/169",
        "published_at_utc": start.isoformat(),
        "valid_until_utc": end.isoformat(),
        "zone_low": 110.0,
        "zone_high": 112.0,
        "reference_price": 115.0,
        "resolution_level": 90.0 if direction == "bearish" else 130.0,
        "direction": direction,
        "invalidation": (
            {"field": "high", "level": 120.0, "side": "above"}
            if direction == "bearish"
            else {"field": "low", "level": 80.0, "side": "below"}
        ),
        "destinations": ["telegram", "discord"],
    }


def _bar(open_at: datetime, *, open_p: float = 115.0, high_p: float = 116.0,
         low_p: float = 113.0, close_p: float = 114.0) -> dict:
    return {
        "open_epoch": int(open_at.timestamp()),
        "open": open_p,
        "high": high_p,
        "low": low_p,
        "close": close_p,
        "source_sha256": "bfm2-held-bars",
    }


def _bar_run(start_open: datetime, end_open_inclusive: datetime, *,
             entry_at: datetime | None = None,
             resolve_at: datetime | None = None,
             invalidate_at: datetime | None = None) -> list[dict]:
    out = []
    cur = start_open
    while cur <= end_open_inclusive:
        low_p = 113.0
        high_p = 116.0
        if entry_at is not None and cur == entry_at:
            low_p = 111.0
        if resolve_at is not None and cur == resolve_at:
            low_p = 89.0
        if invalidate_at is not None and cur == invalidate_at:
            high_p = 121.0
        out.append(_bar(cur, low_p=low_p, high_p=high_p))
        cur += timedelta(minutes=15)
    return out


@pytest.fixture
def isolated_calendar(tmp_path, monkeypatch) -> Path:
    cal_path = tmp_path / "us_session_calendar_v1.json"
    cal_path.write_text(json.dumps(US_CALENDAR_2026_2028, indent=2), encoding="utf-8")
    monkeypatch.setattr(contract, "CASH_CALENDAR", cal_path)
    return cal_path


# ---------------------------------------------------------------------------
# 1. BF-M2(a): Coarse chart bars (60m / 240m / D) on Black Friday & holidays
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("market", ["US500", "USTEC"])
@pytest.mark.parametrize("span_days,expected_interval", [
    (1, "15"),
    (10, "60"),
    (30, "240"),
    (75, "D"),
])
@pytest.mark.parametrize("hour,minute", [
    (9, 45),
    (11, 0),
    (11, 30),
    (12, 45),
    (13, 0),
])
def test_black_friday_in_session_resolution_accepted_across_all_intervals(
        isolated_calendar, market, span_days, expected_interval, hour, minute):
    resolved = _et(2026, 11, 27, hour, minute)
    published = resolved - timedelta(days=span_days)
    req = f.move_chart_request(_followup_row(market, published, resolved))
    assert req["interval"] == expected_interval
    assert "refusal" not in req


@pytest.mark.parametrize("market", ["US500", "USTEC"])
@pytest.mark.parametrize("span_days,expected_interval", [
    (1, "15"),
    (10, "60"),
    (30, "240"),
    (75, "D"),
])
@pytest.mark.parametrize("hour,minute", [
    (9, 15),   # Pre-open inside 09:00-10:00 (60m) / 07:00-11:00 (240m) / D
    (9, 30),   # End of 09:15-09:30 pre-open M15 bar
    (13, 1),   # 1 min past Black Friday 13:00 ET close (still inside 11:00-15:00 4h bar!)
    (13, 5),   # 5 min past early close (inside 11:00-15:00 4h bar)
    (13, 15),  # 13:00-13:15 post-close bar
    (14, 45),  # Still inside 11:00-15:00 4h bar!
    (15, 30),  # Post-close afternoon
])
def test_black_friday_closed_resolution_strictly_refused_across_all_intervals(
        isolated_calendar, market, span_days, expected_interval, hour, minute):
    resolved = _et(2026, 11, 27, hour, minute)
    published = resolved - timedelta(days=span_days)
    req = f.move_chart_request(_followup_row(market, published, resolved))
    assert req["interval"] == expected_interval
    assert req["refusal"] == f"CC778_CHART_MARKET_CLOSED_AT_RESOLUTION:{tv.SYMBOLS[market]}"


@pytest.mark.parametrize("market", ["US500", "USTEC"])
@pytest.mark.parametrize("span_days,expected_interval", [
    (1, "15"),
    (10, "60"),
    (30, "240"),
    (75, "D"),
])
def test_thanksgiving_and_weekend_refused_across_all_intervals(
        isolated_calendar, market, span_days, expected_interval):
    for closed_at in (_et(2026, 11, 26, 11, 30), _et(2026, 11, 28, 11, 0)):
        req = f.move_chart_request(_followup_row(market, closed_at - timedelta(days=span_days), closed_at))
        assert req["interval"] == expected_interval
        assert req["refusal"] == f"CC778_CHART_MARKET_CLOSED_AT_RESOLUTION:{tv.SYMBOLS[market]}"


@pytest.mark.parametrize("market", ["US500", "USTEC"])
def test_daily_and_4h_bars_work_on_normal_monday_and_wednesday_and_summer_edt_early_close(
        isolated_calendar, market):
    # Monday 11:00 ET on interval="D": UTC daily bar opens Sun 19:00 ET, must anchor to Monday ET!
    mon_open = _et(2026, 11, 30, 11, 0)
    req_mon_d = f.move_chart_request(_followup_row(market, mon_open - timedelta(days=75), mon_open))
    assert req_mon_d["interval"] == "D" and "refusal" not in req_mon_d

    # Normal Wed 15:30 ET on interval="240" (UTC 20:00-24:00Z = 15:00-19:00 ET) accepted; 16:15 ET refused.
    wed_open = _et(2026, 11, 25, 15, 30)
    req_wed_open = f.move_chart_request(_followup_row(market, wed_open - timedelta(days=30), wed_open))
    assert req_wed_open["interval"] == "240" and "refusal" not in req_wed_open

    wed_after = _et(2026, 11, 25, 16, 15)
    req_wed_after = f.move_chart_request(_followup_row(market, wed_after - timedelta(days=30), wed_after))
    assert req_wed_after["refusal"] == f"CC778_CHART_MARKET_CLOSED_AT_RESOLUTION:{tv.SYMBOLS[market]}"

    # Normal Wed 19:30 ET (next UTC day 00:30Z!) on interval="D" is closed -> strictly refused.
    wed_night = _et(2026, 11, 25, 19, 30)
    req_wed_night = f.move_chart_request(_followup_row(market, wed_night - timedelta(days=75), wed_night))
    assert req_wed_night["refusal"] == f"CC778_CHART_MARKET_CLOSED_AT_RESOLUTION:{tv.SYMBOLS[market]}"

    # Summer EDT early close (Mon 3 Jul 2028, 13:00 EDT): 4h bar 16:00Z..20:00Z = 12:00..16:00 EDT.
    jul3_open = _et(2028, 7, 3, 12, 30)
    req_edt_open = f.move_chart_request(_followup_row(market, jul3_open - timedelta(days=30), jul3_open))
    assert req_edt_open["interval"] == "240" and "refusal" not in req_edt_open

    jul3_closed = _et(2028, 7, 3, 13, 15)
    req_edt_closed = f.move_chart_request(_followup_row(market, jul3_closed - timedelta(days=30), jul3_closed))
    assert req_edt_closed["refusal"] == f"CC778_CHART_MARKET_CLOSED_AT_RESOLUTION:{tv.SYMBOLS[market]}"


def test_direct_cash_session_open_for_bar_keeps_strict_full_bar_containment_and_bounds_checks(isolated_calendar):
    # Without resolved_at_utc, coarse bar extending past 13:00 ET remains False (backwards compatible).
    assert f.cash_session_open_for_bar("US500", _et(2026, 11, 27, 11, 0), _et(2026, 11, 27, 15, 0)) is False
    assert f.cash_session_open_for_bar("US500", _et(2026, 11, 27, 12, 45), _et(2026, 11, 27, 13, 0)) is True
    assert f.cash_session_open_for_bar("US500", _et(2026, 11, 27, 13, 0), _et(2026, 11, 27, 13, 15)) is False
    # Reversed or zero-width bar fails closed.
    assert f.cash_session_open_for_bar("US500", _et(2026, 11, 27, 12, 0), _et(2026, 11, 27, 12, 0)) is False
    assert f.cash_session_open_for_bar("US500", _et(2026, 11, 27, 12, 15), _et(2026, 11, 27, 12, 0)) is False
    # resolved_at_utc outside (open, end] fails closed.
    assert f.cash_session_open_for_bar(
        "US500", _et(2026, 11, 27, 11, 0), _et(2026, 11, 27, 15, 0),
        resolved_at_utc=_et(2026, 11, 27, 11, 0),
    ) is False
    assert f.cash_session_open_for_bar(
        "US500", _et(2026, 11, 27, 11, 0), _et(2026, 11, 27, 15, 0),
        resolved_at_utc=_et(2026, 11, 27, 11, 30),
    ) is True
    assert f.cash_session_open_for_bar(
        "US500", _et(2026, 11, 27, 11, 0), _et(2026, 11, 27, 15, 0),
        resolved_at_utc=_et(2026, 11, 27, 13, 15),
    ) is False


def test_capture_move_chart_240m_refuses_closed_black_friday_without_calling_worker(tmp_path, isolated_calendar):
    resolved = _et(2026, 11, 27, 13, 15)
    row = _followup_row("US500", resolved - timedelta(days=30), resolved)
    called = []
    taken = f.capture_move_chart(row, root=tmp_path, now=resolved, worker=lambda a: called.append(a))
    assert taken["status"] == "MEDIA_PENDING"
    assert taken["attempted"] is False
    assert taken["cause"] == "CC778_CHART_MARKET_CLOSED_AT_RESOLUTION:SP:SPX"
    assert called == []


@pytest.mark.parametrize("symbol", ["XAUUSD", "EURUSD", "USDJPY", "USOIL", "BTCUSD"])
def test_non_cash_markets_keep_unrestricted_240m_and_daily_requests(isolated_calendar, symbol):
    resolved = _et(2026, 11, 27, 14, 0)
    for span in (30, 75):
        req = f.move_chart_request(_followup_row(symbol, resolved - timedelta(days=span), resolved))
        assert "refusal" not in req


# ---------------------------------------------------------------------------
# 2. BF-M2(b): check_path() scheduled closure gaps vs real data gaps
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("symbol", ["US500", "USTEC", "XAUUSD", "USOIL"])
def test_check_path_allows_thanksgiving_and_black_friday_scheduled_closures(isolated_calendar, symbol):
    # Full span from Wed 16:00 ET across daily break, Thanksgiving halt, Black Friday early close + weekend, to Mon.
    start = _et(2026, 11, 25, 16, 0)
    end = _et(2026, 11, 30, 12, 0)
    c = _candidate(symbol, start, end)

    wed_late = _bar_run(_et(2026, 11, 25, 16, 15), _et(2026, 11, 25, 16, 45))
    # Daily CME maintenance break: Wed 17:00-18:00 ET
    thu_morning = _bar_run(_et(2026, 11, 25, 18, 0), _et(2026, 11, 26, 12, 45),
                           entry_at=_et(2026, 11, 26, 10, 0))
    # Thanksgiving CME halt: Thu 13:00-18:00 ET
    fri_morning = _bar_run(_et(2026, 11, 26, 18, 0), _et(2026, 11, 27, 12, 45))
    # Black Friday early close + weekend: Fri 13:00 ET -> Sun 18:00 ET
    sun_to_mon = _bar_run(_et(2026, 11, 29, 18, 0), _et(2026, 11, 30, 11, 15),
                          resolve_at=_et(2026, 11, 30, 11, 15))
    bars = wed_late + thu_morning + fri_morning + sun_to_mon

    result = f.check_path(c, bars)
    assert result["eligible"] is True
    assert result["entry_traded"] is True
    assert result["resolved_at_utc"] == _et(2026, 11, 30, 11, 30).isoformat()
    assert result["bar_count"] == len(bars)


@pytest.mark.parametrize("symbol,last_fri_bar_hm", [
    ("US500", (12, 45)),   # 13:00 ET cash/early close
    ("US500", (13, 0)),    # 13:15 ET CME equity futures close
    ("USTEC", (13, 0)),    # 13:15 ET CME Nasdaq futures close
    ("XAUUSD", (13, 30)),  # 13:45 ET CME metals early close
    ("USOIL", (14, 15)),   # 14:30 ET CME energy early close
])
def test_check_path_allows_cme_black_friday_early_close_boundaries(isolated_calendar, symbol, last_fri_bar_hm):
    start = _et(2026, 11, 27, 11, 0)
    end = _et(2026, 11, 29, 20, 0)
    c = _candidate(symbol, start, end)
    fri_bars = _bar_run(
        _et(2026, 11, 27, 11, 15),
        _et(2026, 11, 27, last_fri_bar_hm[0], last_fri_bar_hm[1]),
        entry_at=_et(2026, 11, 27, 11, 30),
    )
    sun_bars = _bar_run(
        _et(2026, 11, 29, 18, 0),
        _et(2026, 11, 29, 18, 30),
        resolve_at=_et(2026, 11, 29, 18, 30),
    )
    res = f.check_path(c, fri_bars + sun_bars)
    assert res["eligible"] is True and res["entry_traded"] is True


def test_check_path_allows_christmas_eve_to_sunday_and_good_friday_and_dst_fallback(isolated_calendar):
    # 1. Christmas Eve Thu 24 Dec 2026 early close -> Christmas Day Fri 25 Dec full closure -> Sun 27 Dec 18:00 ET.
    c_xmas = _candidate("US500", _et(2026, 12, 24, 11, 0), _et(2026, 12, 27, 20, 0))
    xmas_bars = (
        _bar_run(_et(2026, 12, 24, 11, 15), _et(2026, 12, 24, 12, 45), entry_at=_et(2026, 12, 24, 11, 30))
        + _bar_run(_et(2026, 12, 27, 18, 0), _et(2026, 12, 27, 18, 30), resolve_at=_et(2026, 12, 27, 18, 30))
    )
    assert f.check_path(c_xmas, xmas_bars)["eligible"] is True

    # 2. Good Friday Fri 3 Apr 2026 full-day CME closure: Thu 2 Apr 16:45 EDT -> Sun 5 Apr 18:00 EDT.
    c_gf = _candidate("XAUUSD", _et(2026, 4, 2, 16, 0), _et(2026, 4, 5, 20, 0))
    gf_bars = (
        _bar_run(_et(2026, 4, 2, 16, 15), _et(2026, 4, 2, 16, 45), entry_at=_et(2026, 4, 2, 16, 15))
        + _bar_run(_et(2026, 4, 5, 18, 0), _et(2026, 4, 5, 18, 30), resolve_at=_et(2026, 4, 5, 18, 30))
    )
    assert f.check_path(c_gf, gf_bars)["eligible"] is True

    # 3. DST Fall-Back weekend (Fri 30 Oct 2026 EDT -> Sun 1 Nov 2026 EST).
    c_dst = _candidate("US500", _et(2026, 10, 30, 16, 0), _et(2026, 11, 1, 20, 0))
    dst_bars = (
        _bar_run(_et(2026, 10, 30, 16, 15), _et(2026, 10, 30, 16, 45), entry_at=_et(2026, 10, 30, 16, 30))
        + _bar_run(_et(2026, 11, 1, 18, 0), _et(2026, 11, 1, 18, 30), resolve_at=_et(2026, 11, 1, 18, 30))
    )
    assert f.check_path(c_dst, dst_bars)["eligible"] is True


def test_check_path_allows_publication_just_before_black_friday_close_reopening_sunday(isolated_calendar):
    # Published Fri 12:50 ET -> expected_first is Fri 13:00 ET (closed), first open bar is Sun 18:00 ET.
    c = _candidate("US500", _et(2026, 11, 27, 12, 50), _et(2026, 11, 29, 20, 0))
    bars = _bar_run(
        _et(2026, 11, 29, 18, 0), _et(2026, 11, 29, 18, 45),
        entry_at=_et(2026, 11, 29, 18, 0), resolve_at=_et(2026, 11, 29, 18, 30),
    )
    assert f.check_path(c, bars)["eligible"] is True

    # Missing the Sun 18:00 ET reopen bar must still fail with CC603_HELD_PRICE_GAP_AFTER_PUBLICATION.
    assert f.check_path(c, bars[1:])["cause"] == "CC603_HELD_PRICE_GAP_AFTER_PUBLICATION"


@pytest.mark.parametrize("symbol", ["EURUSD", "USDJPY"])
def test_check_path_fx_allows_weekend_but_rejects_daily_break_and_black_friday_early_close(isolated_calendar, symbol):
    # Weekend Fri 16:45 -> Sun 17:00 ET is scheduled-closed for FX.
    c_wknd = _candidate(symbol, _et(2026, 11, 20, 16, 0), _et(2026, 11, 22, 19, 0))
    wknd_bars = (
        _bar_run(_et(2026, 11, 20, 16, 15), _et(2026, 11, 20, 16, 45), entry_at=_et(2026, 11, 20, 16, 15))
        + _bar_run(_et(2026, 11, 22, 17, 0), _et(2026, 11, 22, 17, 30), resolve_at=_et(2026, 11, 22, 17, 30))
    )
    assert f.check_path(c_wknd, wknd_bars)["eligible"] is True

    # FX has NO Mon-Thu 17:00-18:00 ET daily break -> missing bars there must fail!
    c_daily = _candidate(symbol, _et(2026, 11, 25, 16, 0), _et(2026, 11, 25, 20, 0))
    daily_gap = (
        _bar_run(_et(2026, 11, 25, 16, 15), _et(2026, 11, 25, 16, 45), entry_at=_et(2026, 11, 25, 16, 15))
        + _bar_run(_et(2026, 11, 25, 18, 0), _et(2026, 11, 25, 18, 30), resolve_at=_et(2026, 11, 25, 18, 30))
    )
    assert f.check_path(c_daily, daily_gap)["cause"] == "CC603_HELD_PRICE_GAP"

    # FX does NOT close early on Black Friday 13:00 ET -> missing 13:00-16:45 ET must fail!
    c_bf = _candidate(symbol, _et(2026, 11, 27, 11, 0), _et(2026, 11, 29, 19, 0))
    bf_gap = (
        _bar_run(_et(2026, 11, 27, 11, 15), _et(2026, 11, 27, 12, 45), entry_at=_et(2026, 11, 27, 11, 30))
        + _bar_run(_et(2026, 11, 29, 17, 0), _et(2026, 11, 29, 17, 30), resolve_at=_et(2026, 11, 29, 17, 30))
    )
    assert f.check_path(c_bf, bf_gap)["cause"] == "CC603_HELD_PRICE_GAP"


@pytest.mark.parametrize("drop_at", [
    _et(2026, 11, 25, 16, 45),  # Last open bar before daily break
    _et(2026, 11, 25, 18, 0),   # First reopen bar after daily break
    _et(2026, 11, 26, 10, 15),  # Thanksgiving morning open bar
    _et(2026, 11, 26, 12, 45),  # Last open bar before Thanksgiving 13:00 ET halt
    _et(2026, 11, 26, 18, 0),   # First reopen bar after Thanksgiving halt
    _et(2026, 11, 27, 11, 15),  # Black Friday morning open bar
    _et(2026, 11, 27, 12, 45),  # Last open bar before Black Friday 13:00 ET early close
    _et(2026, 11, 29, 18, 0),   # First reopen bar after Black Friday + weekend
])
def test_check_path_still_rejects_every_single_dropped_open_or_reopen_bar(isolated_calendar, drop_at):
    start = _et(2026, 11, 25, 16, 0)
    end = _et(2026, 11, 30, 12, 0)
    c = _candidate("US500", start, end)
    bars = (
        _bar_run(_et(2026, 11, 25, 16, 15), _et(2026, 11, 25, 16, 45))
        + _bar_run(_et(2026, 11, 25, 18, 0), _et(2026, 11, 26, 12, 45), entry_at=_et(2026, 11, 26, 10, 0))
        + _bar_run(_et(2026, 11, 26, 18, 0), _et(2026, 11, 27, 12, 45))
        + _bar_run(_et(2026, 11, 29, 18, 0), _et(2026, 11, 30, 11, 15), resolve_at=_et(2026, 11, 30, 11, 15))
    )
    drop_epoch = int(drop_at.timestamp())
    broken = [b for b in bars if b["open_epoch"] != drop_epoch]
    assert len(broken) == len(bars) - 1
    assert f.check_path(c, broken)["cause"] == "CC603_HELD_PRICE_GAP"


def test_check_path_rejects_mid_early_close_hole_btc_gaps_unknown_symbol_and_invalidation(isolated_calendar):
    # 1. Missing 13:15 ET between active 13:00 ET and 13:30 ET bars on Black Friday -> gap_end is NOT a reopen!
    c_mid = _candidate("XAUUSD", _et(2026, 11, 27, 12, 30), _et(2026, 11, 27, 15, 0))
    mid_bars = _bar_run(_et(2026, 11, 27, 12, 45), _et(2026, 11, 27, 13, 45),
                        entry_at=_et(2026, 11, 27, 12, 45), resolve_at=_et(2026, 11, 27, 13, 45))
    mid_broken = [b for b in mid_bars if b["open_epoch"] != int(_et(2026, 11, 27, 13, 15).timestamp())]
    assert f.check_path(c_mid, mid_broken)["cause"] == "CC603_HELD_PRICE_GAP"

    # 2. BTCUSD is 24/7 -> Black Friday 13:00 -> Sun 18:00 gap MUST fail!
    c_btc = _candidate("BTCUSD", _et(2026, 11, 27, 11, 0), _et(2026, 11, 29, 20, 0))
    btc_bars = (
        _bar_run(_et(2026, 11, 27, 11, 15), _et(2026, 11, 27, 12, 45), entry_at=_et(2026, 11, 27, 11, 30))
        + _bar_run(_et(2026, 11, 29, 18, 0), _et(2026, 11, 29, 18, 30), resolve_at=_et(2026, 11, 29, 18, 30))
    )
    assert f.check_path(c_btc, btc_bars)["cause"] == "CC603_HELD_PRICE_GAP"

    # 3. Unknown or missing symbol fails closed.
    c_unknown = {**_candidate("US500", _et(2026, 11, 27, 11, 0), _et(2026, 11, 29, 20, 0)), "symbol": "UNKNOWN"}
    assert f.check_path(c_unknown, btc_bars)["cause"] == "CC603_HELD_PRICE_GAP"

    # 4. Synthetic closed-weekend stream jumping from Fri 19:30 ET to Sun 18:00 ET fails closed.
    c_fake_wknd = _candidate("XAUUSD", _et(2026, 11, 13, 19, 0), _et(2026, 11, 15, 20, 0))
    fake_wknd_bars = (
        _bar_run(_et(2026, 11, 13, 19, 15), _et(2026, 11, 13, 19, 30), entry_at=_et(2026, 11, 13, 19, 15))
        + _bar_run(_et(2026, 11, 15, 18, 0), _et(2026, 11, 15, 18, 30), resolve_at=_et(2026, 11, 15, 18, 30))
    )
    assert f.check_path(c_fake_wknd, fake_wknd_bars)["cause"] == "CC603_HELD_PRICE_GAP"

    # 5. Invalidation across a valid Black Friday early-close gap still refuses with CC603_INVALIDATION_FIRST.
    c_inv = _candidate("US500", _et(2026, 11, 27, 11, 0), _et(2026, 11, 29, 20, 0))
    inv_bars = (
        _bar_run(_et(2026, 11, 27, 11, 15), _et(2026, 11, 27, 12, 45), entry_at=_et(2026, 11, 27, 11, 30))
        + _bar_run(_et(2026, 11, 29, 18, 0), _et(2026, 11, 29, 18, 30),
                   invalidate_at=_et(2026, 11, 29, 18, 15), resolve_at=_et(2026, 11, 29, 18, 30))
    )
    assert f.check_path(c_inv, inv_bars)["cause"] == "CC603_INVALIDATION_FIRST"
