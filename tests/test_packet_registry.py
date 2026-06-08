import json
import os

import pytest

from live_contentops import editorial_packet_export as export
from live_contentops import packet_review_queue as queue
from live_contentops import operator_decision as od
from live_contentops import review_history as rh
from live_contentops import packet_registry as pr


def load_fixture(name):
    path = os.path.join(os.path.dirname(__file__), "fixtures", "editorial", name)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _build(packet_input):
    packet = export.build_export_packet(packet_input)
    item = queue.build_queue_item(packet)
    records = [od.build_decision_record(item, d) for d in packet_input.get("decisions", [])]
    history = rh.build_history(item, records)
    return packet, item, history


@pytest.fixture
def registry_record():
    data = load_fixture("packet_registry_input.json")
    packet, item, history = _build(data["packets"][0])
    return pr.build_registry_record(packet, item, history)


def test_registry_record_has_all_required_fields(registry_record):
    required = [
        "registry_record_id", "export_packet_id", "queue_item_id", "history_id",
        "source_fixture_id", "content_type", "target_platforms", "packet_status",
        "queue_status", "latest_decision_status", "audit_status", "created_at",
        "updated_at", "no_public_post_reason", "advisory_only", "approval_granted",
        "publish_ready", "provider_call_allowed", "search_call_allowed",
        "platform_action_allowed",
    ]
    for key in required:
        assert key in registry_record, f"missing field: {key}"


def test_registry_record_safety_flags(registry_record):
    assert registry_record["advisory_only"] is True
    assert registry_record["approval_granted"] is False
    assert registry_record["publish_ready"] is False
    assert registry_record["provider_call_allowed"] is False
    assert registry_record["search_call_allowed"] is False
    assert registry_record["platform_action_allowed"] is False
    assert registry_record["no_public_post_reason"]


def test_registry_validation_clean(registry_record):
    res = pr.validate_registry_record(registry_record)
    assert res["status"] in ("PASS", "WARNING")
    assert res["blockers"] == []


def test_registry_missing_reference_blocks(registry_record):
    registry_record["history_id"] = ""
    res = pr.validate_registry_record(registry_record)
    assert res["status"] == "BLOCKED"
    assert any("history_id" in b for b in res["blockers"])


def test_registry_cannot_hide_blocked_audit(registry_record):
    registry_record["audit_status"] = "BLOCKED"
    registry_record["latest_decision_status"] = "ACCEPTED_MANUAL_EXPORT_PACKET_ONLY"
    res = pr.validate_registry_record(registry_record)
    assert res["status"] == "BLOCKED"
    assert any("hides BLOCKED" in b for b in res["blockers"])


def test_registry_authority_grant_blocks(registry_record):
    registry_record["publish_ready"] = True
    res = pr.validate_registry_record(registry_record)
    assert res["status"] == "BLOCKED"
    assert any("approval/publish authority" in b for b in res["blockers"])


def test_registry_record_is_deterministic():
    data = load_fixture("packet_registry_input.json")
    packet, item, history = _build(data["packets"][0])
    r1 = pr.build_registry_record(packet, item, history)
    r2 = pr.build_registry_record(packet, item, history)
    assert json.dumps(r1, sort_keys=True) == json.dumps(r2, sort_keys=True)
