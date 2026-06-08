import json
import os

import pytest

from live_contentops import editorial_packet_export as export
from live_contentops import packet_review_queue as queue
from live_contentops import operator_decision as od


def load_fixture(name):
    path = os.path.join(os.path.dirname(__file__), "fixtures", "editorial", name)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def clean_queue_item():
    req = load_fixture("export_packet_input.json")
    packet = export.build_export_packet(req)
    return queue.build_queue_item(packet)


@pytest.fixture
def blocked_queue_item():
    req = {
        "source_fixture_id": "blocked_decision_demo",
        "prompt": {
            "is_synthetic": True,
            "citation_requirements": "Required for all claims",
            "source_context": {"is_current_events": True, "source_items": []},
        },
    }
    packet = export.build_export_packet(req)
    return queue.build_queue_item(packet)


def test_decision_record_has_all_required_fields(clean_queue_item):
    rec = od.build_decision_record(
        clean_queue_item, {"decision_type": "REQUEST_REVISION", "operator_id": "op1"}
    )
    required = [
        "decision_id", "queue_item_id", "export_packet_id", "source_fixture_id",
        "operator_id", "reviewer_id", "decision_timestamp", "decision_type",
        "decision_status", "operator_notes", "selected_preview_id",
        "blocker_snapshot", "warning_snapshot", "audit_status_snapshot",
        "no_public_post_reason", "advisory_only", "manual_decision_recorded",
        "approval_granted", "publish_ready", "provider_call_allowed",
        "search_call_allowed", "platform_action_allowed",
    ]
    for key in required:
        assert key in rec, f"missing field: {key}"


def test_allowed_decision_types_remain_non_publishing(clean_queue_item):
    for dtype in od.ALLOWED_DECISION_TYPES:
        rec = od.build_decision_record(
            clean_queue_item, {"decision_type": dtype, "operator_id": "op1"}
        )
        assert rec["advisory_only"] is True
        assert rec["manual_decision_recorded"] is True
        assert rec["approval_granted"] is False
        assert rec["publish_ready"] is False
        assert rec["provider_call_allowed"] is False
        assert rec["search_call_allowed"] is False
        assert rec["platform_action_allowed"] is False
        assert rec["no_public_post_reason"]


def test_manual_export_accept_does_not_grant_public_approval(clean_queue_item):
    rec = od.build_decision_record(
        clean_queue_item,
        {"decision_type": "ACCEPT_FOR_MANUAL_EXPORT_PACKET_ONLY", "operator_id": "op1"},
    )
    assert rec["decision_status"] == "ACCEPTED_MANUAL_EXPORT_PACKET_ONLY"
    assert rec["approval_granted"] is False
    assert rec["publish_ready"] is False
    assert rec["platform_action_allowed"] is False
    assert rec["no_public_post_reason"]


def test_forbidden_public_post_decision_is_blocked(clean_queue_item):
    rec = od.build_decision_record(
        clean_queue_item,
        {"decision_type": "ACCEPT_FOR_MANUAL_EXPORT_PACKET_ONLY",
         "approve_public_post": True, "operator_id": "op1"},
    )
    assert rec["decision_status"] == "BLOCKED"
    assert any("approve public posting" in b for b in rec["decision_blockers"])
    assert rec["publish_ready"] is False


def test_forbidden_publish_schedule_send_blocked(clean_queue_item):
    for field in ("publish_ready", "schedule", "platform_action_allowed"):
        rec = od.build_decision_record(
            clean_queue_item,
            {"decision_type": "ACCEPT_FOR_INTERNAL_REVIEW_ONLY", field: True, "operator_id": "op1"},
        )
        assert rec["decision_status"] == "BLOCKED"
        assert rec["publish_ready"] is False
        assert rec["platform_action_allowed"] is False


def test_unknown_decision_type_blocked(clean_queue_item):
    rec = od.build_decision_record(
        clean_queue_item, {"decision_type": "GO_LIVE_NOW", "operator_id": "op1"}
    )
    assert rec["decision_status"] == "BLOCKED"
    assert any("disallowed decision type" in b for b in rec["decision_blockers"])


def test_decision_cannot_accept_blocked_audit(blocked_queue_item):
    rec = od.build_decision_record(
        blocked_queue_item,
        {"decision_type": "ACCEPT_FOR_MANUAL_EXPORT_PACKET_ONLY", "operator_id": "op1"},
    )
    assert rec["decision_status"] == "BLOCKED"
    assert rec["audit_status_snapshot"] == "BLOCKED"
    assert any("BLOCKED" in b for b in rec["decision_blockers"])


def test_decision_record_is_deterministic(clean_queue_item):
    r1 = od.build_decision_record(
        clean_queue_item, {"decision_type": "REQUEST_REVISION", "operator_id": "op1"}
    )
    r2 = od.build_decision_record(
        clean_queue_item, {"decision_type": "REQUEST_REVISION", "operator_id": "op1"}
    )
    assert json.dumps(r1, sort_keys=True) == json.dumps(r2, sort_keys=True)


def test_validate_decision_record_clean(clean_queue_item):
    rec = od.build_decision_record(
        clean_queue_item, {"decision_type": "REQUEST_REVISION", "operator_id": "op1"}
    )
    res = od.validate_decision_record(rec)
    assert res["status"] in ("PASS", "WARNING")
    assert res["blockers"] == []
