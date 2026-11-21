"""Replay the public 19 November gold plan through the minute publisher."""
from datetime import timedelta
import sys

import pytest

from live_contentops import plan_analysis_pages_v1 as pages
from live_contentops import plan_call_cards_v1 as cards
from live_contentops import plan_reader_copy_v1 as reader
from live_contentops import plan_state_alerts_v1 as alerts
from live_contentops import plan_status_posts_v1 as posts
from live_contentops import secret_store_v1
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from test_plan_call_cards_cc399 import rows, write
from test_plan_status_posts_cc306 import event, main_root  # noqa: F401


GOLD_PLAN_ID = "plan_a5749b44e7c886ca7220670f"
GOLD_RESULT_KEY = "plan-result-post-580a244ff31eb610ac567a5f53621814"
GOLD_CANCEL = "Cancel if spot price trades at or above 3,792 before entry"
GOLD_ENDING = "Gold: hit its 3,645 target. Result: +1.6R."
PAGE_LINK = "https://capitalchronicle.substack.com/p/gold-test"


@pytest.fixture
def gold_export():
    # The plan-status.public.json row behind the exact result key. Keep only
    # the public facts needed by the composer. The score exports no fill price.
    return {
        "asset_id": "XAUUSD", "plan_id": GOLD_PLAN_ID, "direction": "BEARISH", "status": "WAITING",
        "registration_hash": "589d566e1f5323ecb3898192ab6c5c646fee80f8d1872b3c58754bed28702982",
        "zone": {"minimum": 3722.0, "maximum": 3752.0},
        "invalidation_conditions": [{"field": "high", "operator": "GTE", "threshold": 3792.0}],
        "registered_at_utc": "2026-11-19T09:42:33.233165Z",
        "entry_deadline_utc": "2026-11-19T13:15:00Z", "expires_at_utc": "2026-11-19T13:15:00Z",
        "target_level": 3645.0,
        "public_instrument": {"kind": "FUT", "name": "Micro gold", "symbol": "MGC",
                              "contract_month": "2026-12"},
        "scenario_analysis": {"horizon_end_utc": "2026-11-20T20:00:00Z",
                              "driver": "Fed path via real yields."},
    }


@pytest.fixture
def replay_gold(gold_export, tmp_path, main_root, monkeypatch):
    monkeypatch.setattr(secret_store_v1, "read_secret", lambda name: None)
    monkeypatch.setattr(pages, "confirmed_publication", lambda *args: {
        "plan_id": GOLD_PLAN_ID, "registration_hash": gold_export["registration_hash"],
        "canonical_url": PAGE_LINK, "summary": {"macro": "Fed path via real yields."},
    })
    store = ContentOpsDurableStore(tmp_path / "replay.sqlite3")
    events = []

    def queue(plan, state, at):
        events.append(event(GOLD_PLAN_ID, state, at))
        now = posts._utc(at) + timedelta(seconds=1)
        folder = write(tmp_path / "export", [plan], events, generated_at_utc=now.isoformat())
        run = posts.queue_posts(store, folder, now=now, main_root=main_root, python=sys.executable)
        assert run["status"] == "OK", run
        key, = [row["key"] for row in run["queued"]]
        row = next(row for row in rows(store) if row["key"] == key)
        alerts.validate(row, store=store)
        return row

    setup = queue(gold_export, "WAITING", gold_export["registered_at_utc"])
    store.set_outbox_status(setup["key"], "PUBLISHED")
    original_bytes = store.get_outbox_message(setup["key"])["payload"]
    filled_at = "2026-11-19T09:44:07.552000Z"
    fill = queue({**gold_export, "status": "FILLED"}, "FILLED", filled_at)
    resolved_at = "2026-11-19T21:24:24.796000Z"
    outcome_id = "outcome_7af1f8a0dfef1cef3779361d8f333c0b"
    score = {"asset_id": "XAUUSD", "plan_id": GOLD_PLAN_ID, "outcome_id": outcome_id,
             "result": "HIT", "score_basis": "BROKER_TAKE_PROFIT",
             "triggered_at_utc": filled_at, "resolved_at_utc": resolved_at}
    outcome = {"state": "SCORED", "result": "HIT", "outcome_id": outcome_id,
               "result_r": 1.5569006129583767, "score": score}
    result = queue({**gold_export, "status": "CLOSED", "outcome": outcome}, "CLOSED", resolved_at)
    assert result["key"] == GOLD_RESULT_KEY
    assert store.get_outbox_message(setup["key"])["payload"] == original_bytes
    return setup, fill, result


def test_gold_plan_fill_and_result_render_for_each_destination(replay_gold):
    for row in replay_gold:
        assert row["level_contract"] == reader.CURRENT_LEVEL_CONTRACT
        copies = cards.destination_payloads(row, card_id="gold-chart", chart_credit=True, complete_levels=True)
        assert set(copies) == set(cards.destinations_for(row))
        for destination, copy in copies.items():
            assert "cancelled" not in copy["full_text"].lower(), destination
            assert GOLD_CANCEL in copy["full_text"], destination
            if row["kind"] == "result":
                assert copy["text"].startswith(GOLD_ENDING), destination
                assert "Macro: Fed path via real yields." in copy["full_text"]
                assert "Target level:" not in copy["full_text"]


def test_phase_wording_preserves_the_close_rule_and_futures_stop(gold_export):
    raw = {**gold_export,
           "invalidation_conditions": [{"field": "close", "operator": "LT", "threshold": 3700}],
           "public_instrument": {**gold_export["public_instrument"], "zone_low": 3723.1, "zone_high": 3753.1,
                                 "invalidation_level": 3832.9, "tick_size": 0.1}}
    terms = reader.thread_terms(raw, level_contract=reader.CURRENT_LEVEL_CONTRACT)
    assert terms["invalidation"] == (
        "Cancel if spot price closes below 3,700 before entry. Wrong above 3,832.9 after entry on MGC"
    )
    legacy = reader.thread_terms(raw, level_contract=reader.LEVEL_CONTRACT)
    assert legacy["invalidation"] == "Spot plan cancelled on close below 3,700 before entry; MGC plan wrong above 3,832.9 after entry"


def test_actual_cancellation_can_say_cancelled(replay_gold):
    _, fill, _ = replay_gold
    cancelled = alerts.compose({**fill, "state": "CANCELLED"})
    assert cancelled["lead"] == "Gold: the plan was cancelled."
    assert GOLD_CANCEL in cancelled["text"]


def test_time_exit_uses_the_public_r_without_substituting_the_plan_target(replay_gold):
    _, _, result = replay_gold
    row = {**result, "score_basis": "BROKER_TIME_EXIT", "direction_correct": True}
    assert alerts.result_headline(row) == "Gold: closed at its time exit, on our side of the entry. Result: +1.6R."
