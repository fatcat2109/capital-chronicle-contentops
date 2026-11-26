"""CC-537 US holiday board guard regression tests (Thanksgiving, Black Friday, Christmas).

Covers scenarios S1..S11 plus morning_map_sources() holiday age resilience and open-session skew refusal.
All stores, clocks, and transports here are isolated fixtures (0 writes to production state).
"""
from __future__ import annotations

from copy import deepcopy
from datetime import date, datetime, timedelta, timezone
from hashlib import sha256
import json

import pytest

from live_contentops import daily_trend_board_v1 as board
from live_contentops import market_wrap_sources_v1 as wrap_sources
from live_contentops import plan_analysis_pages_v1 as pages
from live_contentops import publication_image_contract_v1 as pic
from live_contentops import tradingview_snapshot_v1 as tv
from live_contentops.capital_chronicle_latest_report_consumer_v1 import canonical_bytes, sha256_of
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.publication_coordinator_v1 import DurablePublicationCoordinator as Coordinator
from test_publication_coordinator_v1 import FixtureTransport, _set_mode


class HolidayBoardTransport(FixtureTransport):
    def publish(self, *, destination, intent, authorization_context):
        result = super().publish(destination=destination, intent=intent, authorization_context=authorization_context)
        result.update(
            id=sha256(intent["work_item_id"].encode()).hexdigest()[:16],
            public_url="https://example.test/" + destination + "/" + intent["work_item_id"],
        )
        return result


def bar_open_for_est_session(day: str) -> str:
    """Exness EST D1 bar open (22:00Z prior day -> completes 22:00Z = 17:00 ET on `day`)."""
    prior = date.fromisoformat(day) - timedelta(days=1)
    return prior.isoformat() + "T22:00:00Z"


def bar_open_for_main_utc_session(day: str) -> str:
    """Main midnight-UTC D1 bar open (00:00Z `day` -> completes next 00:00Z = 19:00 ET on `day`)."""
    return day + "T00:00:00Z"


def seal(value: dict) -> dict:
    value.pop("content_hash", None)
    value["content_hash"] = sha256_of(value)
    return value


def build_board(
    session_day: str,
    *,
    as_of_utc: str,
    overrides: dict[str, str] | None = None,
    states: dict[str, str] | None = None,
    sample_end: str = "2026-11-20",
    bar_open_fn=bar_open_for_est_session,
) -> dict:
    overrides = overrides or {}
    states = states or {}
    markets = {}
    for index, symbol in enumerate(board.MARKETS):
        sym_day = overrides.get(symbol, session_day)
        markets[symbol] = {
            "yardstick": {
                "state": "AVAILABLE",
                "yardstick": states.get(symbol, "DOWN"),
                "last_completed_bar_utc": bar_open_fn(sym_day),
                "mean_close_20": 100 + index,
                "mean_close_50": 120 + index,
            },
            "rows_whose_condition_holds_now": [
                {
                    "behaviour": "SHORT_WHILE_DOWN_20",
                    "side": "SHORT",
                    "this_side": [42 + index, 0.31, -0.195, -1.1, 0.09, -0.51, "LOST"],
                    "sample_period": {"start": "2016-11-01", "end": sample_end},
                }
            ],
        }
    return seal(
        {
            "schema": "CapitalChronicleDeskBoardPublicV1",
            "as_of_utc": as_of_utc,
            "yardstick_rule": (
                "UP when 20-session and 60-session changes are positive and price is above its "
                "20-session and 50-session mean; DOWN when all four are negative; otherwise MIXED."
            ),
            "measured_table": {"state": "AVAILABLE", "table_content_hash": "a" * 64},
            "markets": markets,
        }
    )


def no_snapshot(*args, **kwargs):
    raise tv.SnapshotError("CONTROLLED_SNAPSHOT_UNAVAILABLE")


def write_board(tmp_path, value: dict, name: str = "desk-board.public.json"):
    path = tmp_path / name
    path.write_bytes(canonical_bytes(value))
    return path


def pin_clock(monkeypatch, now: datetime) -> None:
    class Fixed(datetime):
        @classmethod
        def now(cls, tz=None):
            return now.astimezone(tz) if tz else now.replace(tzinfo=None)

    monkeypatch.setattr(pages, "datetime", Fixed)


def delivery(runtime, now: datetime):
    def send(store, value, *, command="resume", **kwargs):
        coordinator = Coordinator(
            store=store,
            transport_runtime=runtime,
            readiness_provider=lambda _d: {"readiness_state": "READY_AUTHENTICATED"},
            clock=lambda: now,
        )
        coordinator.allow_prior_confirmed_distribution = True
        coordinator.recovery_scope = {
            "work_item_id": value["link_id"],
            "plan": value["plan"],
            "exact_work_item_only": True,
        }
        if command == "readback":
            ids = coordinator._ids(value["link_id"], value["plan"]["plan_hash"], value["destination"])
            return coordinator.readback_existing_dispatch(ids["dispatch_id"])
        return coordinator.publish_plan(value["link_id"], value["plan"])

    return send


@pytest.fixture
def ready(tmp_path, monkeypatch):
    store = ContentOpsDurableStore(tmp_path / "store.sqlite3")
    _set_mode(store, "AUTONOMOUS_DEFAULT")
    reference = {
        "identity": "cc536-measured-odds-1",
        "plan_hash": "b" * 64,
        "canonical_url": "https://capitalchronicle.substack.com/p/method-and-limits",
        "table_hash": "c" * 64,
    }
    from live_contentops import measured_odds_series_v1 as series

    monkeypatch.setattr(series, "confirmed_method_page", lambda _s: deepcopy(reference))
    monkeypatch.setattr(tv, "OUTCOMES", tmp_path / "snapshot-outcomes.jsonl")
    return store, tmp_path / "posts"


def test_us_trading_age_and_latest_close_preserve_holiday_and_early_close_semantics(tmp_path, monkeypatch):
    # Thanksgiving Thu 2026-11-26 is NYSE full-closed; Black Friday Fri 2026-11-27 is 13:00 ET early close (open).
    assert board.us_trading_age("2026-11-25", "2026-11-26") == 0
    assert board.trading_age("2026-11-25", "2026-11-26") == 1
    assert board.us_trading_age("2026-11-25", "2026-11-27") == 1
    assert board.us_trading_age("2026-11-25", "2026-11-28") == 1
    assert board.us_trading_age("2026-11-25", "2026-11-29") == 1
    assert board.us_trading_age("2026-11-25", "2026-11-30") == 2

    # Christmas Fri 2026-12-25 & New Year's Day Fri 2027-01-01 are NYSE full-closed.
    assert board.us_trading_age("2026-12-24", "2026-12-25") == 0
    assert board.us_trading_age("2026-12-24", "2026-12-27") == 0
    assert board.us_trading_age("2026-12-24", "2026-12-28") == 1
    assert board.us_trading_age("2026-12-31", "2027-01-01") == 0
    assert board.us_trading_age("2026-12-31", "2027-01-04") == 1

    # BF-H1: latest_close(now) skips NYSE full-closed holidays (e.g. Thanksgiving 2026-11-26) while keeping
    # the 17:00 ET rollover so Wed 2026-11-25 stays active through Thu 17:01 ET, Fri 12:59 ET, and Fri 13:01 ET.
    assert board.latest_close("2026-11-26T21:59:59Z") == "2026-11-25"  # Thu 16:59:59 ET
    assert board.latest_close("2026-11-26T22:00:00Z") == "2026-11-25"  # Thu 17:00:00 ET (Thanksgiving skipped)
    assert board.latest_close("2026-11-26T22:01:00Z") == "2026-11-25"  # Thu 17:01:00 ET
    assert board.latest_close("2026-11-27T17:59:00Z") == "2026-11-25"  # Fri 12:59:00 ET (Black Friday pre-close)
    assert board.latest_close("2026-11-27T18:01:00Z") == "2026-11-25"  # Fri 13:01:00 ET (Black Friday post-early-close)
    assert board.latest_close("2026-11-27T21:59:59Z") == "2026-11-25"  # Fri 16:59:59 ET
    assert board.latest_close("2026-11-27T22:00:00Z") == "2026-11-27"  # Fri 17:00:00 ET (Black Friday NY rollover)
    assert board.latest_close("2026-11-27T22:05:00Z") == "2026-11-27"
    assert board.latest_close("2026-12-25T22:01:00Z") == "2026-12-24"  # Christmas Day skipped
    assert board.latest_close("2027-01-01T22:01:00Z") == "2026-12-31"  # New Year's Day skipped

    # Deterministic fallback matches when us_session_calendar_v1.json is absent.
    monkeypatch.setattr(pic, "CASH_CALENDAR", tmp_path / "absent-calendar.json")
    monkeypatch.setattr(pic, "_US_CASH_CALENDAR_CACHE", None)
    assert board.us_trading_age("2026-11-25", "2026-11-26") == 0
    assert board.us_trading_age("2026-11-25", "2026-11-27") == 1
    assert board.us_trading_age("2026-12-24", "2026-12-25") == 0
    assert board.latest_close("2026-11-26T22:01:00Z") == "2026-11-25"
    assert board.latest_close("2026-11-27T17:59:00Z") == "2026-11-25"
    assert board.latest_close("2026-11-27T18:01:00Z") == "2026-11-25"
    assert board.latest_close("2026-11-27T22:00:00Z") == "2026-11-27"


@pytest.mark.parametrize(
    "label,clock_utc,expected_markets",
    [
        ("S1_wed_1905_et", "2026-11-26T00:05:00Z", 6),
        ("S2_thu_0700_et", "2026-11-26T12:00:00Z", 7),
    ],
)
def test_s1_s2_thanksgiving_before_1700_et_prepares_wednesday_25_board(ready, tmp_path, label, clock_utc, expected_markets):
    store, root = ready
    now = board.utc(clock_utc)
    doc = build_board("2026-11-25", as_of_utc=clock_utc)
    projected = board.project(doc, now=now)
    assert projected["day_et"] == "2026-11-25"
    assert len(projected["markets"]) == expected_markets
    result = board.run_due(
        store,
        board_path=write_board(tmp_path, doc, f"{label}.json"),
        output_root=root,
        now=now,
        publish=False,
        snapshot=no_snapshot,
    )
    assert result["state"] == "BOARD_PREPARED", result
    assert result["day_et"] == "2026-11-25"


@pytest.mark.parametrize(
    "label,clock_utc,bar_open_fn",
    [
        ("S3a_thu_1705_et_est_bar", "2026-11-26T22:05:00Z", bar_open_for_est_session),
        ("S3b_thu_1905_et_main_utc_bar", "2026-11-27T00:05:00Z", bar_open_for_main_utc_session),
    ],
)
def test_s3a_s3b_thanksgiving_btcusd_holiday_bar_accepted_without_session_skew(
    ready, tmp_path, label, clock_utc, bar_open_fn
):
    store, root = ready
    now = board.utc(clock_utc)
    doc = build_board("2026-11-25", as_of_utc=clock_utc, overrides={"BTCUSD": "2026-11-26"}, bar_open_fn=bar_open_fn)
    projected = board.project(doc, now=now)
    assert projected["day_et"] == "2026-11-25"
    assert projected["markets"]["BTCUSD"]["session_date_et"] == "2026-11-26"
    assert "USTEC" in projected["markets"]
    copy = board.compose(projected)
    assert copy["dated"] == "25 Nov 2026 close, ET (Bitcoin through 26 Nov 2026, ET)"

    # BF-H1: Thu 17:05 ET / 19:05 ET keep latest_close == 2026-11-25, so the clean Wed 25 board
    # (with BTCUSD holiday bar 2026-11-26) prepares cleanly instead of locking out for 24 hours.
    result = board.run_due(
        store,
        board_path=write_board(tmp_path, doc, f"{label}.json"),
        output_root=root,
        now=now,
        publish=False,
        snapshot=no_snapshot,
    )
    assert result["state"] == "BOARD_PREPARED", result
    assert result["day_et"] == "2026-11-25"


def test_s4_all_seven_on_wednesday_stays_valid_past_thu_1700_and_s5_fx_cfd_split_still_refuses(ready, tmp_path):
    store, root = ready
    # S4 / BF-H1: Thu 17:01 ET, all 7 on 2026-11-25 -> prepares cleanly & unsent 25 Nov links do NOT expire.
    s4_now = board.utc("2026-11-26T22:01:00Z")  # Thu 26 Nov 17:01 ET
    s4_doc = build_board("2026-11-25", as_of_utc="2026-11-26T22:01:00Z")
    assert board.project(s4_doc, now=s4_now)["day_et"] == "2026-11-25"
    s4_res = board.run_due(
        store,
        board_path=write_board(tmp_path, s4_doc, "s4.json"),
        output_root=root,
        now=s4_now,
        publish=False,
        snapshot=no_snapshot,
    )
    assert s4_res["state"] == "BOARD_PREPARED", s4_res
    assert s4_res["day_et"] == "2026-11-25"

    # Verify validate_link() keeps the unsent 2026-11-25 board valid at Thu 17:01 ET, Fri 12:59 ET, and Fri 13:01 ET,
    # and expires only once Black Friday 17:00 ET rolls latest_close to 2026-11-27.
    issued = json.loads(store.get_outbox_message(s4_res["board_id"])["payload"])
    first_link = issued["links"][0]
    for valid_utc in ("2026-11-26T22:01:00Z", "2026-11-27T17:59:00Z", "2026-11-27T18:01:00Z"):
        assert board.validate_link(store, first_link, now=board.utc(valid_utc))["board_id"] == s4_res["board_id"]
    with pytest.raises(board.BoardSourceError, match="BOARD_PUBLIC_DAY_EXPIRED"):
        board.validate_link(store, first_link, now=board.utc("2026-11-27T22:00:00Z"))

    # S5: FX (EURUSD, USDJPY) + BTCUSD on 2026-11-26 while US500/USTEC/XAUUSD/USOIL stay 2026-11-25 -> MUST refuse.
    s5_now = board.utc("2026-11-27T00:05:00Z")
    s5_doc = build_board(
        "2026-11-25",
        as_of_utc="2026-11-27T00:05:00Z",
        overrides={"EURUSD": "2026-11-26", "USDJPY": "2026-11-26", "BTCUSD": "2026-11-26"},
    )
    with pytest.raises(board.BoardSourceError, match="BOARD_MARKET_SESSIONS_DIFFER"):
        board.project(s5_doc, now=s5_now)


def test_s6_wednesday_board_delivers_on_thanksgiving_evening_and_closed_holiday_day_is_not_due(ready, tmp_path, monkeypatch):
    store, root = ready
    runtime = HolidayBoardTransport()
    now = board.utc("2026-11-27T00:05:00Z")  # Thu 26 Nov 19:05 ET / Fri 27 Nov 07:05 GMT+7
    # BF-H1: Clean Wed 2026-11-25 board (with BTCUSD on 2026-11-26) publishes cleanly on Thanksgiving evening.
    doc = build_board("2026-11-25", as_of_utc="2026-11-27T00:05:00Z", overrides={"BTCUSD": "2026-11-26"})
    pin_clock(monkeypatch, now)
    result = board.run_due(
        store,
        board_path=write_board(tmp_path, doc, "s6.json"),
        output_root=root,
        now=now,
        snapshot=no_snapshot,
        deliver=delivery(runtime, now),
    )
    assert result["state"] == "BOARD_COORDINATOR_RETURNED", result
    assert result["day_et"] == "2026-11-25"
    assert all(o["readback"]["confirmed"] for o in result["outcomes"])

    # A synthetic Thanksgiving closed-holiday board ("2026-11-26") is refused as not due while latest_close == "2026-11-25".
    holiday_doc = build_board("2026-11-26", as_of_utc="2026-11-27T00:05:00Z")
    with pytest.raises(board.BoardSourceError, match="BOARD_NEW_YORK_CLOSE_NOT_DUE"):
        board.project(holiday_doc, now=now)


def test_s7_s7b_s7c_black_friday_1300_et_early_close_behavior(ready, tmp_path):
    store, root = ready
    for clock_utc in ("2026-11-27T17:59:00Z", "2026-11-27T18:01:00Z"):  # Fri 12:59 ET & Fri 13:01 ET
        assert board.latest_close(clock_utc) == "2026-11-25"

    now = board.utc("2026-11-27T18:01:00Z")  # Fri 27 Nov 13:01 ET / Sat 28 Nov 01:01 GMT+7
    # S7 / BF-H1: All 7 on 2026-11-25 remain due and publishable past 13:00 ET until 17:00 ET NY close.
    s7_doc = build_board("2026-11-25", as_of_utc="2026-11-27T18:01:00Z")
    assert board.project(s7_doc, now=now)["day_et"] == "2026-11-25"
    s7_res = board.run_due(
        store,
        board_path=write_board(tmp_path, s7_doc, "s7.json"),
        output_root=root,
        now=now,
        publish=False,
        snapshot=no_snapshot,
    )
    assert s7_res["state"] == "BOARD_PREPARED", s7_res
    assert s7_res["day_et"] == "2026-11-25"

    # S7c: Premature 2026-11-27 D1 bar (completes 22:00Z > 18:01Z) still fails BOARD_BAR_NOT_COMPLETED.
    s7c_doc = build_board("2026-11-27", as_of_utc="2026-11-27T18:01:00Z")
    with pytest.raises(board.BoardSourceError, match="BOARD_BAR_NOT_COMPLETED"):
        board.project(s7c_doc, now=now)


def test_s8_s9_holiday_staleness_guards_pass_while_true_staleness_refuses(ready, tmp_path):
    store, root = ready
    # S8: Fri 27 Nov 17:05 ET (pre-Fri bar completion), bars still Wed 25 Nov, fresh as_of.
    s8_now = board.utc("2026-11-27T22:05:00Z")
    s8_doc = build_board("2026-11-25", as_of_utc="2026-11-27T22:05:00Z")
    assert board.project(s8_doc, now=s8_now)["day_et"] == "2026-11-25"
    s8_res = board.run_due(
        store,
        board_path=write_board(tmp_path, s8_doc, "s8.json"),
        output_root=root,
        now=s8_now,
        publish=False,
        snapshot=no_snapshot,
    )
    assert s8_res["state"] == "BOARD_NEXT_CLOSE_NOT_AVAILABLE"
    assert s8_res["latest_close_et"] == "2026-11-27"

    # True bar staleness: Mon 30 Nov 17:05 ET with bars still Wed 25 Nov (us_trading_age=2 > 1).
    stale_bar_now = board.utc("2026-11-30T22:05:00Z")
    stale_bar_doc = build_board("2026-11-25", as_of_utc="2026-11-30T22:05:00Z")
    with pytest.raises(board.BoardSourceError, match="BOARD_MARKET_DATA_OLDER_THAN_ONE_TRADING_DAY"):
        board.project(stale_bar_doc, now=stale_bar_now)

    # S9: Fri 27 Nov 00:00 ET, bars Wed 25 Nov, frozen as_of_utc Wed 25 Nov 23:00Z (us_trading_age=1 <= 1).
    s9_now = board.utc("2026-11-27T05:00:00Z")
    s9_doc = build_board("2026-11-25", as_of_utc="2026-11-25T23:00:00Z")
    assert board.project(s9_doc, now=s9_now)["day_et"] == "2026-11-25"

    # True as_of staleness: Mon 30 Nov 00:00 ET with as_of_utc Wed 25 Nov 23:00Z (us_trading_age=2 > 1).
    stale_asof_now = board.utc("2026-11-30T05:00:00Z")
    with pytest.raises(board.BoardSourceError, match="BOARD_OLDER_THAN_ONE_TRADING_DAY"):
        board.project(s9_doc, now=stale_asof_now)


def test_s10_holiday_skipped_preserves_comparison_and_three_day_acceptance_streak(ready, tmp_path, monkeypatch):
    store, root = ready
    runtime = HolidayBoardTransport()
    # Publish 24 Nov -> 25 Nov -> 27 Nov (Thanksgiving Thu 26 Nov skipped).
    schedule = [
        ("2026-11-24", "2026-11-25T00:05:00Z", {}),
        ("2026-11-25", "2026-11-26T00:05:00Z", {}),
        ("2026-11-27", "2026-11-28T00:05:00Z", {"EURUSD": "UP"}),
    ]
    projected_by_day = {}
    for day, clock_utc, state_overrides in schedule:
        now = board.utc(clock_utc)
        doc = build_board(day, as_of_utc=clock_utc, states=state_overrides)
        projected_by_day[day] = board.project(doc, now=now)
        pin_clock(monkeypatch, now)
        res = board.run_due(
            store,
            board_path=write_board(tmp_path, doc, f"s10-{day}.json"),
            output_root=root,
            now=now,
            snapshot=no_snapshot,
            deliver=delivery(runtime, now),
        )
        assert res["state"] == "BOARD_COORDINATOR_RETURNED", res
        assert all(o["readback"]["confirmed"] for o in res["outcomes"])

    # Previous-session comparison on Fri 27 compares cleanly to Wed 25.
    copy = board.compose(projected_by_day["2026-11-27"], projected_by_day["2026-11-25"])
    assert copy["headline"] == "EUR/USD turns UP"
    assert "Changed since the previous session: EUR/USD DOWN to UP." == copy["changes"]

    # Acceptance preserves 3-day consecutive streak across Thanksgiving (24 -> 25 -> 27).
    acc = board.acceptance(store)
    assert acc["observed_consecutive_trading_days"] == 3
    assert acc["passed"] is True

    # Real skipped open session (Tue 24 -> Fri 27, or Tue 24 -> holiday Thu 26) must NOT claim consecutive.
    thu_26 = board.project(build_board("2026-11-26", as_of_utc="2026-11-27T22:05:00Z"), now=board.utc("2026-11-27T22:05:00Z"))
    assert "not available" in board.compose(projected_by_day["2026-11-27"], projected_by_day["2026-11-24"])["changes"]
    assert "not available" in board.compose(thu_26, projected_by_day["2026-11-24"])["changes"]

    # Publishing holiday Thu 26 alongside Wed 25 & Fri 27 also stays consecutive (25 -> 26 -> 27).
    assert "No state changes" in board.compose(thu_26, projected_by_day["2026-11-25"])["changes"]
    assert "EUR/USD DOWN to UP" in board.compose(projected_by_day["2026-11-27"], thu_26)["changes"]


def test_s11_weekend_control_and_christmas_2026_holiday_btcusd(ready, tmp_path, monkeypatch):
    store, root = ready
    runtime = HolidayBoardTransport()

    # S11: Saturday control (Fri 27 weekday vs Sat 28 BTCUSD).
    s11_now = board.utc("2026-11-29T00:05:00Z")  # Sat 28 Nov 19:05 ET
    s11_doc = build_board("2026-11-27", as_of_utc="2026-11-29T00:05:00Z", overrides={"BTCUSD": "2026-11-28"})
    pin_clock(monkeypatch, s11_now)
    s11_res = board.run_due(
        store,
        board_path=write_board(tmp_path, s11_doc, "s11.json"),
        output_root=root,
        now=s11_now,
        snapshot=no_snapshot,
        deliver=delivery(runtime, s11_now),
    )
    assert s11_res["state"] == "BOARD_COORDINATOR_RETURNED", s11_res
    assert s11_res["day_et"] == "2026-11-27"
    issued = json.loads(store.get_outbox_message(s11_res["board_id"])["payload"])
    assert issued["current"]["markets"]["BTCUSD"]["session_date_et"] == "2026-11-28"
    assert "27 Nov 2026 close, ET (Bitcoin through 28 Nov 2026, ET)" in issued["links"][0]["native_payload"]["full_text"]

    # Christmas 2026 (Fri 2026-12-25 NYSE closed): weekday 2026-12-24 vs BTCUSD 2026-12-25 and Sun 2026-12-27.
    xmas_now = board.utc("2026-12-26T00:05:00Z")  # Fri 25 Dec 19:05 ET
    xmas_doc = build_board("2026-12-24", as_of_utc="2026-12-26T00:05:00Z", overrides={"BTCUSD": "2026-12-25"})
    xmas_proj = board.project(xmas_doc, now=xmas_now)
    assert xmas_proj["day_et"] == "2026-12-24"
    assert xmas_proj["markets"]["BTCUSD"]["session_date_et"] == "2026-12-25"
    assert board.compose(xmas_proj)["dated"] == "24 Dec 2026 close, ET (Bitcoin through 25 Dec 2026, ET)"

    xmas_sun_now = board.utc("2026-12-28T00:05:00Z")  # Sun 27 Dec 19:05 ET
    xmas_sun_doc = build_board("2026-12-24", as_of_utc="2026-12-28T00:05:00Z", overrides={"BTCUSD": "2026-12-27"})
    xmas_sun_proj = board.project(xmas_sun_doc, now=xmas_sun_now)
    assert xmas_sun_proj["markets"]["BTCUSD"]["session_date_et"] == "2026-12-27"
    assert board.compose(xmas_sun_proj)["dated"] == "24 Dec 2026 close, ET (Bitcoin through 27 Dec 2026, ET)"

    # Post-Christmas Monday 28 Dec compares cleanly to Christmas Eve Thu 24 Dec.
    mon_28 = board.project(
        build_board("2026-12-28", as_of_utc="2026-12-29T00:05:00Z", states={"XAUUSD": "UP"}),
        now=board.utc("2026-12-29T00:05:00Z"),
    )
    assert board.compose(mon_28, xmas_proj)["headline"] == "Gold turns UP"


@pytest.mark.parametrize(
    "case_name,weekday_day,btc_day,clock_utc",
    [
        # Black Friday 2026-11-27 is an OPEN US session (13:00 ET early close): skew vs Wed 25 MUST refuse.
        ("black_friday_open_skew", "2026-11-25", "2026-11-27", "2026-11-28T00:05:00Z"),
        # Regular open weekday skew (Tue 24 vs Mon 23) MUST refuse.
        ("regular_weekday_open_skew", "2026-11-23", "2026-11-24", "2026-11-25T00:05:00Z"),
        # Missed open Wed 25 before holiday Thu 26 (us_trading_age("2026-11-24", "2026-11-26") == 1 != 0) MUST refuse.
        ("skipped_open_session_before_holiday", "2026-11-24", "2026-11-26", "2026-11-27T00:05:00Z"),
        # Bitcoin behind weekday (bitcoin_day < day) MUST refuse.
        ("btcusd_behind_holiday_weekday", "2026-11-26", "2026-11-25", "2026-11-27T00:05:00Z"),
        ("btcusd_behind_regular_weekday", "2026-11-25", "2026-11-24", "2026-11-26T00:05:00Z"),
    ],
)
def test_open_session_skew_and_bitcoin_behind_weekday_refuse(case_name, weekday_day, btc_day, clock_utc):
    doc = build_board(weekday_day, as_of_utc=clock_utc, overrides={"BTCUSD": btc_day})
    with pytest.raises(board.BoardSourceError, match="BOARD_MARKET_SESSIONS_DIFFER"):
        board.project(doc, now=board.utc(clock_utc))


def test_morning_map_sources_survives_thanksgiving_on_black_friday_and_monday(tmp_path):
    # Black Friday 2026-11-27 07:30 ET with board as_of_utc frozen at Wed 2026-11-25 18:00 ET (23:00Z).
    fri_now = wrap_sources.utc("2026-11-27T12:30:00Z")
    wed_close = wrap_sources.utc("2026-11-25T21:00:00Z")
    doc = build_board("2026-11-25", as_of_utc="2026-11-25T23:00:00Z")
    board_path = write_board(tmp_path, doc, "fri-morning-board.json")

    def fake_quote(market, **options):
        return {
            "source_symbol": wrap_sources.quotes.SYMBOLS[market][1],
            "value": 102.0,
            "prior_close": 100.0,
            "observed_at_utc": (wed_close if market in {"US500", "USTEC"} else fri_now).isoformat(),
            "known_at_utc": fri_now.isoformat(),
            "source": "Attributed test quote",
            "source_url": "https://example.test/quote",
            "observation_sha256": market.lower(),
        }

    snapshots = {m: wrap_sources.wrap_quote(fake_quote(m)) for m in wrap_sources.MARKETS}
    gaps = {}
    result = wrap_sources.morning_map_sources(
        snapshots,
        board_path,
        now=fri_now,
        last_close=wed_close,
        quote=fake_quote,
        clock=lambda: fri_now,
        gaps=gaps,
    )
    assert gaps == {}
    assert set(result["rows"]) == set(wrap_sources.MARKETS)

    # Monday 2026-11-30 07:30 ET (last_close = Fri 27 13:00 ET), bars still Wed 25 (1 US session old) -> OK.
    mon_now = wrap_sources.utc("2026-11-30T12:30:00Z")
    fri_close = wrap_sources.utc("2026-11-27T18:00:00Z")
    mon_doc = build_board("2026-11-25", as_of_utc="2026-11-28T00:00:00Z")
    mon_path = write_board(tmp_path, mon_doc, "mon-morning-board.json")
    mon_snaps = {
        m: wrap_sources.wrap_quote(
            {
                "source_symbol": wrap_sources.quotes.SYMBOLS[m][1],
                "value": 103.0,
                "prior_close": 100.0,
                "observed_at_utc": (fri_close if m in {"US500", "USTEC"} else mon_now).isoformat(),
                "known_at_utc": mon_now.isoformat(),
                "source": "Attributed test quote",
                "source_url": "https://example.test/quote",
                "observation_sha256": m.lower(),
            }
        )
        for m in wrap_sources.MARKETS
    }
    mon_gaps = {}
    mon_res = wrap_sources.morning_map_sources(
        mon_snaps,
        mon_path,
        now=mon_now,
        last_close=fri_close,
        quote=fake_quote,
        clock=lambda: mon_now,
        gaps=mon_gaps,
    )
    assert mon_gaps == {}
    assert set(mon_res["rows"]) == set(wrap_sources.MARKETS)

    # Genuine staleness on Mon 30 Nov (board as_of_utc Wed 25 Nov -> us_trading_age=2 > 1) MUST still raise.
    with pytest.raises(ValueError, match="BOARD_OLDER_THAN_ONE_TRADING_DAY"):
        wrap_sources.morning_map_sources(
            mon_snaps,
            board_path,
            now=mon_now,
            last_close=fri_close,
            quote=fake_quote,
            clock=lambda: mon_now,
            gaps={},
        )

    # Genuine bar staleness on Mon 30 Nov (bar Tue 24 Nov vs last_close Fri 27 Nov -> us_trading_age=2 > 1).
    stale_bars_doc = build_board("2026-11-24", as_of_utc="2026-11-28T00:00:00Z")
    stale_bars_path = write_board(tmp_path, stale_bars_doc, "mon-stale-bars.json")
    stale_gaps = {}
    wrap_sources.morning_map_sources(
        mon_snaps,
        stale_bars_path,
        now=mon_now,
        last_close=fri_close,
        quote=fake_quote,
        clock=lambda: mon_now,
        gaps=stale_gaps,
    )
    assert len(stale_gaps) == len(wrap_sources.MARKETS)
    assert all(v == "BOARD_MARKET_DATA_OLDER_THAN_ONE_TRADING_DAY" for v in stale_gaps.values())
