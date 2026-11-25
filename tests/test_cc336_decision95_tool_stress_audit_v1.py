"""CC-336 (Decision 95): offline built-tool stress tests & wire-or-retire audit regressions.

Strictly offline, zero network calls, zero live runtime writes, zero public posts, and zero
mutation of any `.stop` / pause control file (Decision 167 respected). All SQLite stores,
feeds, receipts, and artifacts are created inside `tmp_path`.

Complements `tests/test_cc336_remaining_three_tools_stress_v1.py` (which covered the remaining
3 of the original 11 tools) by stress-testing the major post-7-Nov ContentOps tool families
and locking in the P1-P5 / Decision 95 wire-or-retire audit invariants on `ce53947a8`.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from hashlib import sha256
import json
from pathlib import Path
import re

import pytest

from live_contentops import agy_decision_metrics_v1 as agy_metrics
from live_contentops import daily_trend_board_v1 as trend_board
from live_contentops import event_article_guard_v1 as guard
from live_contentops import image_quality_v1 as img_quality
from live_contentops import image_templates_v1 as img_templates
from live_contentops import plan_queue_clock_v1 as queue_clock
from live_contentops import public_decision_checks_v1 as decision_checks
from live_contentops import published_content_v1 as pub_content
from live_contentops import substack_daily_digest_v1 as digest
from live_contentops import tradingview_idea_v1 as tv_idea
from live_contentops import x_reply_trading_dates_v1 as trading_dates
from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore


REPO_ROOT = Path(__file__).resolve().parents[1]


# ---------------------------------------------------------------------------
# 1. x_reply_trading_dates_v1 (2 live callers, previously 0 unit tests!)
# ---------------------------------------------------------------------------


def test_x_reply_trading_dates_weekends_us_equities_rates_and_year_boundary() -> None:
    # Weekends are never trading dates across any market class.
    assert trading_dates.trading_date(date(2026, 11, 21), {"SPX"}) is False
    assert trading_dates.trading_date(date(2026, 11, 22), {"RATES"}) is False
    assert trading_dates.trading_date(date(2026, 11, 22), {"XAUUSD"}) is False

    # Ordinary weekday is open for all market classes.
    assert trading_dates.trading_date(date(2026, 11, 25), {"SPX"}) is True
    assert trading_dates.trading_date(date(2026, 11, 25), {"US10Y"}) is True
    assert trading_dates.trading_date(date(2026, 11, 25), {"EURUSD"}) is True

    # US Thanksgiving (4th Thursday of Nov 2026 = 2026-11-26): equities & rates closed, FX open.
    assert trading_dates.trading_date(date(2026, 11, 26), {"EQUITIES"}) is False
    assert trading_dates.trading_date(date(2026, 11, 26), {"US10Y"}) is False
    assert trading_dates.trading_date(date(2026, 11, 26), {"EURUSD"}) is True

    # Good Friday 2026 (Easter 2026-04-05 -> Good Friday 2026-04-03): equities & rates closed.
    assert trading_dates.trading_date(date(2026, 4, 3), {"SPX"}) is False
    assert trading_dates.trading_date(date(2026, 4, 3), {"RATES"}) is False

    # Rates-only bond holidays (Columbus Day 2026-10-12, Veterans Day 2026-11-11):
    # bond markets closed while US equities stay open.
    for bond_holiday in (date(2026, 10, 12), date(2026, 11, 11)):
        assert trading_dates.trading_date(bond_holiday, {"US10Y"}) is False
        assert trading_dates.trading_date(bond_holiday, {"RATES"}) is False
        assert trading_dates.trading_date(bond_holiday, {"SPX"}) is True

    # Juneteenth observed from 2022 onward, not before.
    assert trading_dates.trading_date(date(2021, 6, 18), {"SPX"}) is True
    assert trading_dates.trading_date(date(2026, 6, 19), {"SPX"}) is False

    # Year-boundary observed New Year's Day: 2028-01-01 is Saturday -> observed Fri 2027-12-31.
    assert trading_dates.trading_date(date(2027, 12, 31), {"SPX"}) is False
    assert trading_dates.trading_date(date(2027, 12, 31), {"EURUSD"}) is False
    # July 4, 2026 is Saturday -> observed Fri 2026-07-03 for equities/rates.
    assert trading_dates.trading_date(date(2026, 7, 3), {"NASDAQ"}) is False


# ---------------------------------------------------------------------------
# 2. plan_queue_clock_v1 (CC-732 / P2 export-to-outbox lag & alarm stress)
# ---------------------------------------------------------------------------


def test_plan_queue_clock_timely_delayed_alarm_replacement_and_dedup(tmp_path: Path) -> None:
    store = ContentOpsDurableStore(tmp_path / "clock.sqlite3")
    runs_dir = tmp_path / "runs"
    runs_dir.mkdir()

    def write_tick(payload: dict, folder: Path, *, now: datetime) -> None:
        path = folder / f"runs-{now:%Y%m%d}.jsonl"
        row = {"at_utc": now.isoformat().replace("+00:00", "Z"), **payload}
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, sort_keys=True) + "\n")

    t0 = datetime(2026, 11, 22, 14, 0, 0, tzinfo=timezone.utc)
    clock_now = [t0]
    row_fast = {
        "key": "plan-post-fast",
        "plan_id": "plan-fast",
        "symbol": "XAUUSD",
        "to": "WAITING",
        "source_transition_id": "tr-fast",
        "at_utc": "2026-11-22T13:59:30Z",
    }
    row_slow = {
        "key": "plan-post-slow",
        "plan_id": "plan-slow",
        "symbol": "EURUSD",
        "to": "TRIGGERED",
        "source_transition_id": "tr-slow",
        "at_utc": "2026-11-22T13:59:40Z",
    }
    row_replaced = {
        "key": "plan-post-replaced",
        "plan_id": "plan-repl",
        "symbol": "USOIL",
        "to": "EXPIRED",
        "source_transition_id": "tr-repl",
        "at_utc": "2026-11-22T13:59:50Z",
    }

    # Tick 1 at t0: observe all three rows; fast registers within 30s -> no alarm, target met.
    clk1 = queue_clock.PlanQueueClock(store, runs_dir, write_tick, clock=lambda: clock_now[0])
    clk1.observe([row_fast, row_slow, row_replaced], "2026-11-22T13:59:55Z", seen_at=t0)
    store.create_work_item(story_id="s1", title="fast", target_surface="MULTI_PLATFORM", work_item_id="w1")
    store.register_outbox_message(
        message_id="plan-post-fast", work_item_id="w1", destination="internal:plan-status-post", payload="{}"
    )
    # Pin created_at to t0 + 30s so gap <= TARGET_SECONDS (120s).
    with store.get_connection() as conn:
        conn.execute(
            "UPDATE outbox_messages SET created_at=? WHERE message_id=?",
            ((t0 + timedelta(seconds=30)).isoformat().replace("+00:00", "Z"), "plan-post-fast"),
        )
    # Replaced row gets a replacement_key registered in outbox.
    store.register_outbox_message(
        message_id="plan-result-repl", work_item_id="w1", destination="internal:plan-status-post", payload="{}"
    )
    with store.get_connection() as conn:
        conn.execute(
            "UPDATE outbox_messages SET created_at=? WHERE message_id=?",
            ((t0 + timedelta(seconds=180)).isoformat().replace("+00:00", "Z"), "plan-result-repl"),
        )
    clk1.refuse(row_replaced, "PLAN_TRANSITION_REPLACED_BY_RESULT", replacement_key="plan-result-repl")
    clock_now[0] = t0 + timedelta(seconds=185)
    clk1.finish({})

    # Tick 2 at t0 + 620s (> ALARM_SECONDS=600s): row_slow is still unqueued and drops from export.
    clock_now[0] = t0 + timedelta(seconds=620)
    clk2 = queue_clock.PlanQueueClock(store, runs_dir, write_tick, clock=lambda: clock_now[0])
    clk2.observe([row_fast], "2026-11-22T14:10:15Z", seen_at=clock_now[0])
    clk2.finish({})

    events = queue_clock.read_queue_events(runs_dir, t0 - timedelta(minutes=1), t0 + timedelta(minutes=15))
    by_id = {(e["source_transition_id"], bool(e["alarm"])): e for e in events}
    assert ("tr-fast", False) in by_id
    assert by_id[("tr-fast", False)]["target_missed"] is False
    assert by_id[("tr-fast", False)]["gap_seconds"] == pytest.approx(30.0)
    assert ("tr-repl", False) in by_id
    assert by_id[("tr-repl", False)]["queued_key"] == "plan-result-repl"
    assert by_id[("tr-repl", False)]["target_missed"] is True
    assert ("tr-slow", True) in by_id
    assert by_id[("tr-slow", True)]["alarm"] is True
    assert by_id[("tr-slow", True)]["first_cause"] == "ROW_ABSENT_FROM_EXPORT"


# ---------------------------------------------------------------------------
# 3. substack_daily_digest_v1 (P5 real 10 Nov CPI cutoff & carryover stress)
# ---------------------------------------------------------------------------


def _sealed_feed_row(
    *,
    content_id: str,
    title: str,
    published_at_utc: str,
    url: str,
    piece_type: str = "ARTICLE",
    event_id: str | None = None,
) -> dict:
    row = {
        "schema_version": pub_content.SCHEMA,
        "content_id": content_id,
        "type": piece_type,
        "title": title,
        "standfirst": "Event preview standfirst with explicit ET clock reference.",
        "published_at_utc": published_at_utc,
        "recorded_at_utc": published_at_utc,
        "outlets": [{"name": "substack", "url": url}],
        "event_id": event_id,
        "conditional_calls": [],
        "rights_class": "CC_OWN_ANALYSIS",
        "visibility": "public",
        "disclaimer": guard.PUBLIC_NOTICE,
        "conflicts_notice": guard.CONFLICTS_NOTICE,
    }
    row["content_sha256"] = sha256(pub_content.canonical(row)).hexdigest()
    return row


def test_substack_daily_digest_reproduces_p5_cpi_cutoff_and_handles_refused_carryover(tmp_path: Path) -> None:
    store = ContentOpsDurableStore(tmp_path / "digest.sqlite3")
    feed_path = tmp_path / "published_content_v1.jsonl"

    # Real 10 Nov 2026 event timing observed in published_content_v1.jsonl:
    # - pre-cutoff morning article at 2026-11-10T11:30:00Z (inside 10 Nov 12:00Z / 19:00 GMT+7 cutoff)
    # - CPI preview `bls-cpi-20261110` published at 2026-11-10T12:09:49Z (9m49s AFTER 12:00Z cutoff,
    #   before the 13:30Z release -> documents P5 still open on ce53947a8!)
    morning = _sealed_feed_row(
        content_id="substack:224000001",
        title="Pre-US Market Wrap, November 10, 2026",
        published_at_utc="2026-11-10T11:30:00Z",
        url="https://capitalchronicle.substack.com/p/pre-us-wrap-nov-10",
    )
    cpi_preview = _sealed_feed_row(
        content_id="substack:224000002",
        title="October Core CPI Preview: Gold and Yields Scenarios",
        published_at_utc="2026-11-10T12:09:49Z",
        url="https://capitalchronicle.substack.com/p/october-cpi-preview",
        piece_type="EVENT_PREVIEW",
        event_id="bls-cpi-20261110",
    )
    feed_path.write_bytes(
        b"".join(pub_content.canonical(r) + b"\n" for r in (morning, cpi_preview))
    )

    # Naive clock fails closed.
    with pytest.raises(ValueError, match="EXPLICIT_DIGEST_CLOCK_REQUIRED"):
        digest.prepare_daily_digest(store, feed_path, now=datetime(2026, 11, 10, 12, 15))

    # Non-digest plan stays WEB_ONLY (never emails subscribers per post).
    assert digest.delivery_mode_for_plan(store, "ordinary-article", {"destinations": []}) == digest.WEB_ONLY

    # At 12:15Z (19:15 GMT+7) on 10 Nov: on pre-P5 ce53947a8 cutoff freezes at 12:00Z (misses 12:09:49Z CPI);
    # once P5 (POST_CUTOFF_MACRO_GRACE) is integrated, 12:15Z includes both the morning wrap and 12:09:49Z CPI.
    nov10 = digest.prepare_daily_digest(
        store, feed_path, now=datetime(2026, 11, 10, 12, 15, tzinfo=timezone.utc)
    )
    assert nov10["digest_id"] == "cc143-digest-2026-11-10"
    assert nov10["public_write_performed"] is False
    expected_nov10 = (
        ["substack:224000001", "substack:224000002"]
        if hasattr(digest, "POST_CUTOFF_MACRO_GRACE")
        else ["substack:224000001"]
    )
    assert [a["content_id"] for a in nov10["packet"]["articles"]] == expected_nov10
    assert digest.delivery_mode_for_plan(store, nov10["digest_id"], nov10["packet"]["plan"]) == digest.EMAIL_DIGEST

    # Simulate DEFINITE_NO_WRITE on 10 Nov digest (no public_object_id/url): on 11 Nov, both the refused
    # 10 Nov morning wrap AND the post-cutoff 10 Nov CPI preview carry cleanly into the 11 Nov digest.
    from live_contentops.publication_coordinator_v1 import DurablePublicationCoordinator

    ids10 = DurablePublicationCoordinator._ids(nov10["digest_id"], nov10["packet"]["plan"]["plan_hash"], "substack")
    store.register_outbox_message(
        message_id=ids10["message_id"],
        work_item_id=nov10["digest_id"],
        destination="substack",
        payload="{}",
        status="DEFINITE_NO_WRITE",
    )
    store.register_platform_dispatch(
        dispatch_id=ids10["dispatch_id"],
        message_id=ids10["message_id"],
        platform="substack",
        status="DEFINITE_NO_WRITE",
        public_object_id=None,
        public_object_url=None,
    )

    nov11 = digest.prepare_daily_digest(
        store, feed_path, now=datetime(2026, 11, 11, 12, 15, tzinfo=timezone.utc)
    )
    assert nov11["digest_id"] == "cc143-digest-2026-11-11"
    assert [a["content_id"] for a in nov11["packet"]["articles"]] == [
        "substack:224000001",
        "substack:224000002",
    ]


# ---------------------------------------------------------------------------
# 4. tradingview_idea_v1 (CC-469 House Rules + Decisions 109/157/158 stress)
# ---------------------------------------------------------------------------


def _sample_idea_payload(symbol: str = "XAUUSD") -> dict:
    return {
        "kind": "setup",
        "plan_id": f"plan-{symbol.lower()}-20261124",
        "symbol": symbol,
        "at_utc": "2026-11-24T13:30:00Z",
        "registered_at_utc": "2026-11-24T13:30:00Z",
        "levels": {
            "direction": "bullish",
            "zone_low": 2610.5,
            "zone_high": 2625.0,
            "invalidation_level": 2585.0,
            "valid_until_utc": "2026-11-26T20:00:00Z",
            "time_exit_utc": "2026-11-30T20:00:00Z",
            "scenario_analysis": {
                "base_case": {
                    "probability_pct": 55,
                    "market_move": "Gold rebounds toward higher resistance as real yields ease across the curve.",
                    "cause": "Softer US macro prints keep the Federal Reserve inflation target debate balanced.",
                },
                "main_alternative": {
                    "probability_pct": 30,
                    "market_move": "Gold breaks lower if Treasury yields climb sharply on hotter inflation data.",
                    "cause": "Renewed front-end rate repricing strengthens the dollar and weighs on bullion.",
                },
                "priced": "Rates markets already price a gradual easing path into year-end.",
                "positioning": "Futures positioning cooled after last month's rally, leaving room for fresh demand.",
                "invalidation_text": "a sustained break below key daily support",
            },
        },
        "source_plan": {"asset_id": symbol, "horizon_lane": "MID"},
        "conditional_calls": [
            {
                "condition": "spot holds inside the entry band after the New York open",
                "invalidation": "A daily close below support cancels the setup.",
            }
        ],
    }


def test_tradingview_idea_builds_clean_pack_and_blocks_house_rule_violations() -> None:
    for symbol in ("XAUUSD", "US500", "EURUSD", "USDJPY", "USOIL", "BTCUSD", "USTEC"):
        entry = tv_idea.idea_entry(_sample_idea_payload(symbol))
        assert entry["status"] == "READY", (symbol, entry)
        assert entry["check"] == "PASS"
        assert entry["chart"]["symbol"] == tv_idea.SYMBOLS[symbol]
        # Policy phrase "inflation target" is explicitly permitted.
        assert "inflation target" in entry["description"].lower()

    valid = tv_idea.build_idea(_sample_idea_payload("XAUUSD"))
    assert tv_idea.check_idea(valid) == "PASS"

    # Reject profit targets, URLs, brand names, contact references, AI labels, relative days, ALL-CAPS, non-English.
    mutations = [
        ("description", valid["description"] + "\n\nProfit target at 2,750.", "TRADINGVIEW_IDEA_TARGET_FORBIDDEN"),
        ("description", valid["description"] + "\n\nRead more at https://example.com/post", "TRADINGVIEW_IDEA_LINK_FORBIDDEN"),
        ("description", valid["description"] + "\n\nPublished by Capital Chronicle.", "TRADINGVIEW_IDEA_BRAND_FORBIDDEN"),
        ("description", valid["description"] + "\n\nJoin our Telegram channel.", "TRADINGVIEW_IDEA_CONTACT_REFERENCE_FORBIDDEN"),
        ("description", valid["description"] + "\n\nDrafted with Gemini assistance.", "TRADINGVIEW_IDEA_AI_LABEL_FORBIDDEN"),
        ("description", valid["description"] + "\n\nWatch price action today.", "TRADINGVIEW_IDEA_RELATIVE_DAY_FORBIDDEN"),
        ("title", "GOLD BULLISH BREAKOUT SETUP ABOVE RESISTANCE", "TRADINGVIEW_IDEA_TITLE_CAPITALS"),
        ("description", valid["description"] + "\n\nGhi chu tieng Viet: giá vàng tăng.", "TRADINGVIEW_IDEA_NOT_ENGLISH"),
    ]
    for field_name, mutated_value, expected_code in mutations:
        bad = {**valid, field_name: mutated_value}
        with pytest.raises(tv_idea.IdeaError, match=expected_code):
            tv_idea.check_idea(bad)


# ---------------------------------------------------------------------------
# 5. daily_trend_board_v1 (CC-537 / CC-788 Nasdaq cutover & fail-closed checks)
# ---------------------------------------------------------------------------


def _sealed_board(*, as_of_utc: str, bar_open_utc: str, include_ustec: bool = False) -> dict:
    symbols = ["XAUUSD", "US500", "EURUSD", "USDJPY", "USOIL", "BTCUSD"]
    if include_ustec:
        symbols.append("USTEC")
    markets = {}
    for sym in symbols:
        markets[sym] = {
            "yardstick": {
                "state": "AVAILABLE",
                "yardstick": "UP",
                "last_completed_bar_utc": bar_open_utc,
                "mean_close_20": 158.60999999999999 if sym == "USDJPY" else 100.123456,
                "mean_close_50": 155.123456 if sym == "USDJPY" else 98.654321,
            },
            "rows_whose_condition_holds_now": [
                {
                    "behaviour": "LONG_WHILE_UP_20",
                    "side": "LONG",
                    "this_side": [42, 0.55, 0.184, 2.1, 0.15, 0.21, "OK"],
                    "sample_period": {"start": "2020-01-02", "end": "2026-11-20"},
                }
            ],
        }
    body = {
        "schema": "CapitalChronicleDeskBoardPublicV1",
        "as_of_utc": as_of_utc,
        "yardstick_rule": "20/50 completed daily closes",
        "markets": markets,
    }
    body["content_hash"] = sha256_of(body)
    return body


def test_daily_trend_board_rounding_nasdaq_cutover_and_fail_closed_guards() -> None:
    # 24 Nov 2026 (post-ROUNDED_FROM_ET, pre-NASDAQ_FROM_ET): 6 markets, USDJPY rounded to 3 places.
    board_nov24 = _sealed_board(as_of_utc="2026-11-24T22:15:00Z", bar_open_utc="2026-11-23T22:00:00Z")
    proj24 = trend_board.project(board_nov24, now="2026-11-24T22:30:00Z")
    assert "USTEC" not in proj24["markets"]
    assert proj24["markets"]["USDJPY"]["means"]["mean_close_20"] == "158.61"
    assert proj24["markets"]["USDJPY"]["rows"][0]["mean_r"] == "+0.18"

    # 26 Nov 2026 (on NASDAQ_FROM_ET): missing USTEC marks UNAVAILABLE rather than guessing.
    board_nov26_no_ndx = _sealed_board(as_of_utc="2026-11-26T22:15:00Z", bar_open_utc="2026-11-25T22:00:00Z")
    proj26 = trend_board.project(board_nov26_no_ndx, now="2026-11-26T22:30:00Z")
    assert proj26["markets"]["USTEC"]["state"] == trend_board.UNAVAILABLE

    # Tampered hash, future clock, stale (>1 trading day), and uncompleted bar all fail closed.
    tampered = {**board_nov24, "yardstick_rule": "tampered"}
    with pytest.raises(trend_board.BoardSourceError, match="BOARD_CONTENT_HASH_CHANGED"):
        trend_board.project(tampered, now="2026-11-24T22:30:00Z")

    with pytest.raises(trend_board.BoardSourceError, match="BOARD_FROM_FUTURE"):
        trend_board.project(board_nov24, now="2026-11-24T22:00:00Z")

    with pytest.raises(trend_board.BoardSourceError, match="BOARD_OLDER_THAN_ONE_TRADING_DAY"):
        trend_board.project(board_nov24, now="2026-11-27T22:30:00Z")

    uncompleted = _sealed_board(as_of_utc="2026-11-24T12:00:00Z", bar_open_utc="2026-11-24T00:00:00Z")
    with pytest.raises(trend_board.BoardSourceError, match="BOARD_BAR_NOT_COMPLETED"):
        trend_board.project(uncompleted, now="2026-11-24T13:00:00Z")


# ---------------------------------------------------------------------------
# 6. public_decision_checks_v1 (Decisions 157, 158, CC-729, pause windows)
# ---------------------------------------------------------------------------


def test_public_decision_checks_targets_scenario_voice_notices_and_pause_windows(tmp_path: Path) -> None:
    # Decision 157: profit target detected; policy inflation target allowed.
    assert decision_checks.plan_target_present("Gold base case: target at 2,750 if support holds.") is True
    assert decision_checks.plan_target_present("The Fed's 2% inflation target remains unchanged.") is False

    # Decision 158: clean scenario copy passes all 5 rules; "net long" / "short covering" not counted as desk position words.
    clean_copy = (
        "Base case: gold rises on macro easing and softer fundamentals while net long positioning builds "
        "and short covering adds momentum. Bear case: hotter yields cap rallies. "
        "Entry zone 2,610–2,625. Invalidation below 2,585."
    )
    assert decision_checks.plan_scenario_flags(clean_copy) == ()
    weak_copy = "Buy gold now, go long into the open, sell dollars later."
    flags = set(decision_checks.plan_scenario_flags(weak_copy))
    assert {"SCENARIO_CASES_MISSING", "POSITION_WORDS_REPEATED", "ENTRY_ZONE_MISSING", "INVALIDATION_LEVEL_MISSING"} <= flags

    # CC-729: single-notice vs duplicate-notice detection.
    body_once = f"Setup note.\n\n{guard.PUBLIC_NOTICE} {guard.CONFLICTS_NOTICE}"
    assert decision_checks.notice_counts(body_once) == {"analysis_notice": 1, "conflicts_notice": 1}
    assert decision_checks.notice_counts(body_once + "\n" + guard.PUBLIC_NOTICE)["analysis_notice"] == 2

    # Pause window classification: delivery absences during Jim's pause classify as PAUSED, never FAIL.
    pause_dir = tmp_path / "control" / "pause-20261123"
    pause_dir.mkdir(parents=True)
    (pause_dir / "manifest.json").write_text(
        json.dumps({"paused_at_utc": "2026-11-23T00:00:00Z", "cause": "JIM_DECISION_167_PAUSE"}),
        encoding="utf-8",
    )
    checks = decision_checks.DecisionChecks(
        {"since_utc": "2026-11-23T00:00:00Z", "until_utc": "2026-11-24T00:00:00Z"},
        tmp_path,
    )
    assert checks.paused_through_window() == "JIM_DECISION_167_PAUSE"
    checks.issue(
        "98",
        "pre-us-wrap-2026-11-23",
        "telegram",
        "WRAP_PLATFORM_MISSING",
        held_at=datetime(2026, 11, 23, 13, 45, tzinfo=timezone.utc),
    )
    assert len(checks.issues) == 1
    assert checks.issues[0]["status"] == "PAUSED"
    assert checks.issues[0]["pause_cause"] == "JIM_DECISION_167_PAUSE"


# ---------------------------------------------------------------------------
# 7. agy_decision_metrics_v1 (Decision 168 Codex takeover & AGY terms-block)
# ---------------------------------------------------------------------------


def test_agy_decision_metrics_separates_terms_block_and_counts_codex_calls(tmp_path: Path) -> None:
    runtime = tmp_path / "rt"
    receipt_dir = runtime / "daily_app_outputs" / "plan_analysis" / "plan-1" / "layer-lines-1"
    receipt_dir.mkdir(parents=True)
    (receipt_dir / "light-call.json").write_text(
        json.dumps(
            {
                "job": "plan_layer_lines",
                "started_at_utc": "2026-11-24T10:00:00Z",
                "ended_at_utc": "2026-11-24T10:00:15Z",
                "result": "PASS",
                "answered_by": "codex",
                "attempts": [
                    {
                        "caller": "antigravity",
                        "status": "NOT_STARTED",
                        "cause": agy_metrics.AGY_TERMS_BLOCK,
                    },
                    {"caller": "codex", "status": "RETURNED", "cause": ""},
                ],
            }
        ),
        encoding="utf-8",
    )
    report = agy_metrics.daily_metrics(
        runtime,
        {"since_utc": "2026-11-24T00:00:00Z", "until_utc": "2026-11-25T00:00:00Z"},
        due={"plan_layer_lines": 1},
    )
    row = next(j for j in report["jobs"] if j["job"] == "plan_layer_lines")
    assert row["calls"] == 1
    assert row["calls_by_caller"] == {"codex": 1, "antigravity": 0}
    assert row["antigravity_refused_by_block"] == 1
    assert row["code_passes"] == 1
    assert row["code_pass_rate_pct"] == 100.0
    assert row["code_pass_rate_meets_90_pct"] is True
    assert row["codex_takeovers"] == 1


# ---------------------------------------------------------------------------
# 8. image_templates_v1 / image_quality_v1 + Decision 95 static audit invariants
# ---------------------------------------------------------------------------


def test_image_templates_fail_closed_and_decision95_wiring_invariants_hold() -> None:
    # image_templates_v1 formatting & fail-closed checks (no ellipsis, no multiline, finite levels only).
    assert img_templates.price(1.11664, "EURUSD") == "1.1166"
    assert img_templates.price(158.609, "USDJPY") == "158.61"
    assert img_templates.price(61941.4, "BTCUSD") == "61,941"
    assert img_templates.r_text(1.5) == "+1.5R"
    assert img_templates.r_text(-0.8) == "−0.8R"
    assert img_templates.r_text(None) == "No entry"
    with pytest.raises(img_templates.LayoutError, match="IMAGE_LEVEL_NOT_FINITE"):
        img_templates.price(float("nan"), "XAUUSD")
    with pytest.raises(img_templates.LayoutError, match="IMAGE_TEXT_CUT_OR_MULTILINE"):
        img_templates.field({"headline": "Truncated..."}, "headline", 40)
    with pytest.raises(img_templates.LayoutError, match="IMAGE_WRITER_REVISION_REQUIRED"):
        img_templates.field({"headline": "x" * 50}, "headline", 20)

    # image_quality_v1 enforces all 10 checklist points and names vision hold policy.
    assert len(img_quality.CHECKLIST) == 10
    assert "IMAGE_LEVELS_OUT_OF_VIEW" in img_quality.TEMPLATE_FIT_CAUSES
    assert "IMAGE_R_RESULT_NOT_EXPORTED" in img_quality.TEMPLATE_FIT_CAUSES

    # Decision 95 wiring invariants verified on the live ContentOps tree:
    # 1) P1 permanently closed: no LOW_MEMORY_FALLBACK free-RAM gate in tradingview_snapshot_v1.py.
    tv_src = (REPO_ROOT / "live_contentops" / "tradingview_snapshot_v1.py").read_text(encoding="utf-8")
    assert "LOW_MEMORY_FALLBACK" not in tv_src

    # 2) P3 notice stays wired in event_article_guard_v1.py.
    guard_src = (REPO_ROOT / "live_contentops" / "event_article_guard_v1.py").read_text(encoding="utf-8")
    assert "retrospective_notice" in guard_src

    # 3) CC-459 parked renderer `plan_call_card_media_v1` has 0 production callers.
    prod_files = [
        p
        for folder in (REPO_ROOT / "live_contentops", REPO_ROOT / "scripts")
        if folder.is_dir()
        for p in folder.rglob("*.py")
        if p.name != "plan_call_card_media_v1.py"
    ]
    callers = [
        p.relative_to(REPO_ROOT).as_posix()
        for p in prod_files
        if re.search(r"\bplan_call_card_media_v1\b", p.read_text(encoding="utf-8", errors="ignore"))
    ]
    assert callers == []
