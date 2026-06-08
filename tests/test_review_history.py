import json
import os

import pytest

from live_contentops import editorial_packet_export as export
from live_contentops import packet_review_queue as queue
from live_contentops import operator_decision as od
from live_contentops import review_history as rh


def load_fixture(name):
    path = os.path.join(os.path.dirname(__file__), "fixtures", "editorial", name)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def queue_item():
    req = load_fixture("export_packet_input.json")
    packet = export.build_export_packet(req)
    return queue.build_queue_item(packet)


@pytest.fixture
def decision_inputs():
    return load_fixture("operator_decision_input.json")


def _records(queue_item, decisions):
    return [od.build_decision_record(queue_item, d) for d in decisions]


def test_history_has_required_fields(queue_item, decision_inputs):
    records = _records(queue_item, decision_inputs["decisions"])
    history = rh.build_history(queue_item, records)
    required = [
        "history_id", "queue_item_id", "export_packet_id", "decision_records",
        "latest_decision", "revision_count", "rejection_count", "hold_count",
        "internal_review_accept_count", "manual_export_packet_accept_count",
        "current_review_status", "current_publish_status", "approval_granted",
        "publish_ready", "append_only_semantics_note",
    ]
    for key in required:
        assert key in history, f"missing field: {key}"


def test_history_preserves_prior_decisions(queue_item, decision_inputs):
    records = _records(queue_item, decision_inputs["decisions"])
    history = rh.build_history(queue_item, records)
    assert len(history["decision_records"]) == len(records)
    # Append-only semantics: appending preserves prior records.
    extra = od.build_decision_record(
        queue_item, {"decision_type": "REJECT_PACKET", "operator_id": "op2"}
    )
    history2 = rh.append_decision(history, queue_item, extra)
    assert len(history2["decision_records"]) == len(records) + 1
    assert history2["decision_records"][:len(records)] == history["decision_records"]


def test_latest_decision_summary_correct(queue_item, decision_inputs):
    records = _records(queue_item, decision_inputs["decisions"])
    history = rh.build_history(queue_item, records)
    assert history["latest_decision"] == records[-1]
    assert history["current_review_status"] == records[-1]["decision_status"]
    assert history["revision_count"] == 1
    assert history["hold_count"] == 1
    assert history["manual_export_packet_accept_count"] == 1


def test_history_publish_status_and_authority(queue_item, decision_inputs):
    records = _records(queue_item, decision_inputs["decisions"])
    history = rh.build_history(queue_item, records)
    assert history["current_publish_status"] == "NOT_PUBLIC_POSTABLE"
    assert history["approval_granted"] is False
    assert history["publish_ready"] is False


def test_history_is_deterministic(queue_item, decision_inputs):
    r1 = rh.build_history(queue_item, _records(queue_item, decision_inputs["decisions"]))
    r2 = rh.build_history(queue_item, _records(queue_item, decision_inputs["decisions"]))
    assert json.dumps(r1, sort_keys=True) == json.dumps(r2, sort_keys=True)


def test_validate_history_clean(queue_item, decision_inputs):
    history = rh.build_history(queue_item, _records(queue_item, decision_inputs["decisions"]))
    res = rh.validate_history(history)
    assert res["status"] in ("PASS", "WARNING")
    assert res["blockers"] == []


def test_validate_history_no_decisions_blocks(queue_item):
    history = rh.build_history(queue_item, [])
    res = rh.validate_history(history)
    assert res["status"] == "BLOCKED"
    assert any("no decision records" in b for b in res["blockers"])


def test_forbidden_decision_in_history_blocks(queue_item, decision_inputs):
    bad = od.build_decision_record(queue_item, decision_inputs["forbidden_decision"])
    history = rh.build_history(queue_item, [bad])
    res = rh.validate_history(history)
    assert res["status"] == "BLOCKED"
    # Forbidden decision did not become an effective acceptance.
    assert history["manual_export_packet_accept_count"] == 0


def test_markdown_report_has_banners(queue_item, decision_inputs):
    history = rh.build_history(queue_item, _records(queue_item, decision_inputs["decisions"]))
    md = rh.render_markdown_report(history)
    for banner in rh.MARKDOWN_BANNERS:
        assert banner in md
    assert "approval_granted=false" in md
    assert "publish_ready=false" in md
    assert "NOT_PUBLIC_POSTABLE" in md
