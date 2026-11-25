"""CC-822: ContentOps consumers admit Main's MANAGED_EXIT outcomes and render 'closed by its plan rule'."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path

import pytest

from live_contentops import call_followups_v1 as followups
from live_contentops import image_template_inputs_v1 as img
from live_contentops import pinned_result_scorecard_v1 as scorecard
from live_contentops import plan_analysis_pages_v1 as pages
from live_contentops import plan_call_cards_v1 as cards
from live_contentops import plan_state_alerts_v1 as alerts
from live_contentops import plan_status_posts_v1 as posts
from live_contentops import secret_store_v1
from live_contentops import weekly_scored_calls_v1 as weekly
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore


PLAN_ID = "plan_add6d62299828744939aafc1"
OUTCOME_CLOSE_ID = "outcome_673db05e49ce248f9c0ff67cb932fbb0"
OUTCOME_HALF_ID = "outcome_0c28ff4adccbb30219bd1abf27dded2d"
REG_HASH = "53680a50e1646312cececafcf345f43144145a246353c987402a2e51c949b2d3"
PAGE_LINK = "https://capitalchronicle.substack.com/p/bitcoin-cc822-test"


def _managed_export(
    *,
    basis: str = "DETERMINISTIC_THESIS_INVALIDATION",
    result_r: float = 0.12025730324168105,
    resolved_at: str = "2026-11-26T16:35:41.547000Z",
    generated_at: str = "2026-11-26T16:36:00Z",
    correction_of: str | None = None,
):
    outcome_id = OUTCOME_HALF_ID if basis == "REDUCE_HALF" else OUTCOME_CLOSE_ID
    if basis == "REDUCE_HALF":
        slices = [
            {"score_basis": "REDUCE_HALF", "resolved_at_utc": "2026-11-26T16:31:43.880000Z",
             "gross_r_contribution": -0.125},
            {"score_basis": "DETERMINISTIC_THESIS_INVALIDATION", "resolved_at_utc": resolved_at,
             "gross_r_contribution": 0.25},
        ]
    else:
        slices = [
            {"score_basis": "DETERMINISTIC_THESIS_INVALIDATION", "resolved_at_utc": resolved_at,
             "gross_r_contribution": 0.5},
        ]
    score = {
        "asset_id": "BTCUSD", "plan_id": PLAN_ID, "outcome_id": outcome_id,
        "public_call_id": "call_9fa9ff9eade1b076c617cb03",
        "decision_record_id": "decision:request-4003b5d99d5beb61:BTCUSD",
        "direction": "BEARISH", "result": "MANAGED_EXIT", "score_basis": basis,
        "exit_slices": slices,
        "frozen_at_utc": "2026-11-25T19:19:27.837424Z",
        "triggered_at_utc": "2026-11-25T19:27:00.527000Z",
        "horizon_end_utc": "2026-12-09T18:00:00Z",
        "resolved_at_utc": resolved_at,
        "scored_at_utc": "2026-11-26T16:35:43.547356Z",
        "source_hash": "3" * 64, "source_plan_hash": REG_HASH,
        "corrects_outcome_id": correction_of, "content_hash": "e" * 64,
    }
    plan = {
        "plan_id": PLAN_ID, "asset_id": "BTCUSD", "direction": "BEARISH", "status": "CLOSED",
        "registration_hash": REG_HASH,
        "zone": {"minimum": 60500.0, "maximum": 61500.0},
        "invalidation_conditions": [{"field": "high", "operator": "GTE", "threshold": 66800.0}],
        "registered_at_utc": "2026-11-25T19:19:27.837424Z",
        "entry_deadline_utc": "2026-11-27T18:00:00Z",
        "expires_at_utc": "2026-12-09T18:00:00Z",
        "horizon_end_utc": "2026-12-09T18:00:00Z",
        "public_instrument": {"kind": "SPOT", "name": "Bitcoin", "symbol": "BTCUSD"},
        "scenario_analysis": {"horizon_end_utc": "2026-12-09T18:00:00Z",
                              "base_case": {"probability_pct": 55},
                              "driver": "Real yields and dollar liquidity."},
        "outcome": {
            "state": "SCORED", "result": "MANAGED_EXIT", "outcome_id": outcome_id,
            "public_call_id": "call_9fa9ff9eade1b076c617cb03",
            "result_r": result_r,
            "result_r_basis": "NET_DEAL_CASH_OVER_FROZEN_INITIAL_RISK",
            "result_r_first_cause": None, "result_r_source_hash": "f" * 64,
            "first_cause": None, "score": score,
        },
    }
    transitions = [
        {"plan_id": PLAN_ID, "status": "WAITING", "at_utc": "2026-11-25T19:19:27.837424Z", "reason_code": "REGISTERED"},
        {"plan_id": PLAN_ID, "status": "FILLED", "at_utc": "2026-11-25T19:27:00.527000Z", "reason_code": "FILLED"},
        {"plan_id": PLAN_ID, "status": "CLOSED", "at_utc": resolved_at, "reason_code": basis},
    ]
    return {
        "status": {
            "schema": "CapitalChroniclePlanStatusV1", "schema_version": "1.0.0",
            "contract_version": "2.0.0", "generated_at_utc": generated_at,
            "content_hash": "c" * 64, "scored_call_count": 1,
            "plans": [plan], "scored_calls": [score],
        },
        "transitions": {
            "schema": "CapitalChroniclePlanTransitionsV1", "schema_version": "1.0.0",
            "generated_at_utc": generated_at, "status_content_hash": "c" * 64,
            "transitions": transitions,
        },
    }


@pytest.mark.parametrize("basis,r_val", [
    ("DETERMINISTIC_THESIS_INVALIDATION", 0.12025730324168105),
    ("REDUCE_HALF", 0.049968762558445574),
])
def test_result_rows_and_compose_result_accept_managed_exit(basis, r_val):
    export = _managed_export(basis=basis, result_r=r_val)
    rows = posts.result_rows_from_export(export)
    assert len(rows) == 1
    row = rows[0]
    assert row["result"] == "MANAGED_EXIT" and row["scored"] is True
    composed = posts.compose_result(row)
    assert composed["status"] == "COMPOSED"
    assert "Bitcoin: plan result — closed by its plan rule at " in composed["text"]
    assert "MANAGED_EXIT" not in composed["text"]
    assert "DETERMINISTIC_THESIS_INVALIDATION" not in composed["text"]
    assert "REDUCE_HALF" not in composed["text"]


def test_result_rows_still_refuse_mismatched_managed_exit_binding():
    export = _managed_export()
    export["status"]["plans"][0]["outcome"]["score"]["result"] = "STOPPED"
    with pytest.raises(posts.PlanPostError, match="PLAN_RESULT_SCORE_BINDING_INVALID"):
        posts.result_rows_from_export(export)


def test_record_line_and_ending_words_render_managed_exit():
    export = _managed_export(basis="REDUCE_HALF")
    assert cards.ending_words({"result": "MANAGED_EXIT", "score_basis": "REDUCE_HALF"}) == "closed by its plan rule"
    assert cards.ending_words({"result": "MANAGED_EXIT", "score_basis": "DETERMINISTIC_THESIS_INVALIDATION"}) == "closed by its plan rule"
    line = cards.record_line(export["status"])
    assert "1 calls judged: 1 closed by its plan rule." in line
    assert "MANAGED_EXIT" not in line


def test_queue_posts_and_state_alerts_render_managed_exit_across_destinations(tmp_path, monkeypatch):
    monkeypatch.setattr(secret_store_v1, "read_secret", lambda name: None)
    monkeypatch.setattr(pages, "confirmed_publication", lambda *args: {
        "plan_id": PLAN_ID, "registration_hash": REG_HASH,
        "canonical_url": PAGE_LINK, "summary": {"macro": "Real yields and dollar liquidity."},
    })
    store = ContentOpsDurableStore(tmp_path / "cc822.sqlite3")

    setup_export = _managed_export(generated_at="2026-11-25T19:19:30Z")
    setup_export["status"]["scored_call_count"] = 0
    setup_export["status"]["scored_calls"] = []
    setup_export["status"]["plans"][0]["status"] = "WAITING"
    setup_export["status"]["plans"][0]["outcome"] = {"state": "PENDING", "result": None, "outcome_id": None, "score": None}
    setup_export["transitions"]["transitions"] = setup_export["transitions"]["transitions"][:1]

    monkeypatch.setattr(posts, "read_export", lambda *a, **k: setup_export)
    r1 = cards.queue_posts(store, tmp_path, now=datetime(2026, 11, 25, 19, 19, 31, tzinfo=timezone.utc))
    assert r1["status"] == "OK" and len(r1["queued"]) == 1
    setup_key = r1["queued"][0]["key"]
    store.set_outbox_status(setup_key, "PUBLISHED")

    closed_export = _managed_export(basis="DETERMINISTIC_THESIS_INVALIDATION", result_r=0.12025730324168105)
    monkeypatch.setattr(posts, "read_export", lambda *a, **k: closed_export)
    r2 = cards.queue_posts(store, tmp_path, now=datetime(2026, 11, 26, 16, 36, 5, tzinfo=timezone.utc))
    assert r2["status"] == "OK"
    result_keys = [q["key"] for q in r2["queued"] if q["key"].startswith("plan-result-post-")]
    assert len(result_keys) == 1
    row = json.loads(store.get_outbox_message(result_keys[0])["payload"])
    alerts.validate(row, store=store)
    assert row["result"] == "MANAGED_EXIT"
    assert row["lead"] == "Bitcoin, plan of 25–26 Nov: closed by its plan rule. Result: +0.1R."
    copies = cards.destination_payloads(row, card_id="btc-chart", chart_credit=True, complete_levels=True)
    for dest, copy in copies.items():
        assert "closed by its plan rule" in copy["full_text"], dest
        assert "MANAGED_EXIT" not in copy["full_text"], dest


def test_pinned_scorecard_and_followups_handle_managed_exit(tmp_path):
    now = datetime(2026, 11, 26, 16, 36, 5, tzinfo=timezone.utc)
    export = _managed_export(basis="REDUCE_HALF")
    record = scorecard.project(export, now=now)
    assert record["counts"]["MANAGED_EXIT"] == 1
    assert record["counts"]["scored"] == 1 and record["counts"]["total"] == 1
    assert "CLOSED BY PLAN RULE: 1" in record["text"]
    assert "| closed by its plan rule" in record["text"]
    assert "MANAGED_EXIT" not in record["text"]

    store = ContentOpsDurableStore(tmp_path / "scorecard.sqlite3")
    store.create_work_item(story_id=scorecard.WORK, title="Scorecard", target_surface="TELEGRAM", work_item_id=scorecard.WORK)
    store.register_outbox_message(
        message_id="rev-1", work_item_id=scorecard.WORK, destination=scorecard.DESTINATION,
        payload=json.dumps(record), status="CONFIRMED",
    )
    store.register_outbox_message(
        message_id=scorecard.OBJECT, work_item_id=scorecard.WORK, destination=scorecard.DESTINATION + "-object",
        payload=json.dumps({"message_id": "201", "public_url": "https://t.me/CapitalChronicle/201"}), status="BOUND",
    )

    class _FakeAPI:
        def call(self, method, **kwargs):
            assert method == "getChat"
            return {"username": "CapitalChronicle", "type": "channel",
                    "pinned_message": {"message_id": 201, "text": record["text"]}}

    obs = followups.observed_record(store, api=_FakeAPI(), now=now)
    assert "1 closed by plan rule" in obs["line"]
    assert obs["counts"]["MANAGED_EXIT"] == 1


def test_weekly_scored_calls_and_image_inputs_handle_managed_exit():
    export = _managed_export(
        basis="DETERMINISTIC_THESIS_INVALIDATION",
        result_r=0.12025730324168105,
        resolved_at="2026-11-26T16:35:41.547000Z",
        generated_at="2026-11-28T12:00:00Z",
    )
    # Cutoff Saturday 28 Nov 2026 12:00 UTC -> week window Mon 23 Nov to Sat 28 Nov ET.
    record = weekly.project(export, cutoff_utc="2026-11-28T12:00:00Z")
    assert record["counts"]["scored_calls"] == 1
    assert record["counts"]["managed_exits"] == 1
    assert "Closed by plan rule: 1." in record["text"]
    assert "closed by its plan rule." in record["text"]
    assert "MANAGED_EXIT" not in record["text"]
    assert record["rows"][0]["image_result"]["outcome_label"] == "Closed by its plan rule"

    plan = export["status"]["plans"][0]
    row = {
        "key": "plan-result-post-test", "symbol": "BTCUSD", "kind": "result", "state": "RESULT",
        "at_utc": "2026-11-26T16:35:41.547000Z", "registered_at_utc": "2026-11-25T19:19:27Z",
        "result": "MANAGED_EXIT", "scored": True, "source_plan": plan,
        "levels": {"direction": "bearish", "zone_low": 60500.0, "zone_high": 61500.0,
                   "invalidation_level": 66800.0, "valid_until_utc": "2026-12-09T18:00:00Z"},
    }
    img_input = img.from_result(row)
    assert img_input["result"]["outcome_label"] == "Closed by its plan rule"
    assert img_input["result"]["r"] == pytest.approx(0.12025730324168105)
    img.validate_binding(img_input)


def test_real_cc822_main_candidate_exports_bind_cleanly_if_present():
    """Verify exact Main CC-822 exported fixtures when present on Scratch."""
    for case in ("candidate-close", "candidate-reduce-half"):
        folder = Path(rf"C:\CapitalChronicleScratch\cc822-rule-close-scoring\{case}\public")
        status_path = folder / "plan-status.public.json"
        trans_path = folder / "plan-transitions.public.json"
        if not (status_path.is_file() and trans_path.is_file()):
            pytest.skip(f"CC-822 fixture absent: {folder}")
        export = {
            "status": json.loads(status_path.read_bytes()),
            "transitions": json.loads(trans_path.read_bytes()),
        }
        rows = posts.result_rows_from_export(export)
        assert len(rows) == 1 and rows[0]["result"] == "MANAGED_EXIT"
        composed = posts.compose_result(rows[0])
        assert "closed by its plan rule" in composed["text"]
        assert "MANAGED_EXIT" not in composed["text"]
