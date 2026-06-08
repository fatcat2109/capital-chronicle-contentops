import json
import os

import pytest

from live_contentops import editorial_packet_export as export
from live_contentops import packet_review_queue as queue
from live_contentops import operator_decision as od
from live_contentops import review_history as rh
from live_contentops import packet_registry as pr
from live_contentops import review_ledger as rl
from live_contentops import packet_registry_query as rq
from live_contentops import dashboard_handoff as ho


def load_fixture(name):
    path = os.path.join(os.path.dirname(__file__), "fixtures", "editorial", name)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _build(packet_input):
    packet = export.build_export_packet(packet_input)
    item = queue.build_queue_item(packet)
    records = [od.build_decision_record(item, d) for d in packet_input.get("decisions", [])]
    history = rh.build_history(item, records)
    registry = pr.build_registry_record(packet, item, history)
    ledger = rl.build_ledger(registry, packet, item, history)
    return registry, ledger


def _blocked_build():
    packet_input = {
        "source_fixture_id": "handoff_blocked_demo",
        "content_type": "post",
        "target_platforms": ["x"],
        "prompt": {
            "is_synthetic": True,
            "citation_requirements": "Required for all claims",
            "source_context": {"is_current_events": True, "source_items": []},
        },
        "decisions": [],
    }
    return _build(packet_input)


@pytest.fixture
def data():
    reg_clean, led_clean = _build(load_fixture("packet_registry_input.json")["packets"][0])
    reg_blocked, led_blocked = _blocked_build()
    return [reg_clean, reg_blocked], led_clean + led_blocked


def test_handoff_export_has_all_required_fields(data):
    registry_records, ledger = data
    ex = ho.build_handoff_export(registry_records, ledger)
    required = [
        "handoff_id", "generated_at", "dashboard_summary", "registry_query_summary",
        "highest_priority_items", "blocker_summary", "warning_summary",
        "review_status_summary", "decision_history_summary", "ledger_event_summary",
        "next_operator_action_placeholders", "safety_posture",
        "export_formats_supported", "advisory_only", "local_only",
        "human_review_required", "approval_granted", "publish_ready",
        "provider_call_allowed", "search_call_allowed", "platform_action_allowed",
        "all_fixture_outputs_not_public_postable",
    ]
    for key in required:
        assert key in ex, f"missing field: {key}"


def test_fixture_backed_demo_nonzero_counts(data):
    registry_records, ledger = data
    ex = ho.build_handoff_export(registry_records, ledger)
    d = ex["dashboard_summary"]
    assert d["registry_record_count"] >= 1
    assert d["ledger_entry_count"] >= 1
    assert len(ex["highest_priority_items"]) >= 1
    assert len(ex["blocker_summary"]) + len(ex["warning_summary"]) >= 1


def test_handoff_safety_flags(data):
    registry_records, ledger = data
    ex = ho.build_handoff_export(registry_records, ledger)
    assert ex["advisory_only"] is True
    assert ex["local_only"] is True
    assert ex["human_review_required"] is True
    assert ex["approval_granted"] is False
    assert ex["publish_ready"] is False
    assert ex["provider_call_allowed"] is False
    assert ex["search_call_allowed"] is False
    assert ex["platform_action_allowed"] is False
    assert ex["all_fixture_outputs_not_public_postable"] is True


def test_json_export_is_deterministic(data):
    registry_records, ledger = data
    e1 = ho.build_handoff_export(registry_records, ledger)
    e2 = ho.build_handoff_export(registry_records, ledger)
    assert json.dumps(e1, sort_keys=True) == json.dumps(e2, sort_keys=True)


def test_highest_priority_surfaces_blocked_first(data):
    registry_records, ledger = data
    ex = ho.build_handoff_export(registry_records, ledger)
    assert ex["highest_priority_items"][0]["queue_status"] == "BLOCKED"


def test_next_operator_action_placeholders_grant_no_authority(data):
    registry_records, ledger = data
    ex = ho.build_handoff_export(registry_records, ledger)
    for action in ho.NEXT_OPERATOR_ACTION_PLACEHOLDERS:
        assert action in ex["next_operator_action_placeholders"]
    assert ex["publish_ready"] is False
    assert ex["approval_granted"] is False


def test_markdown_report_has_banners(data):
    registry_records, ledger = data
    md = ho.render_markdown_report(registry_records, ledger)
    for banner in ho.MARKDOWN_BANNERS:
        assert banner in md
    assert "approval_granted=false" in md
    assert "publish_ready=false" in md
    assert "NOT PUBLIC POSTABLE" in md
    assert "Next Operator Actions" in md
    assert "Non-Publishing Boundary" in md


def test_markdown_manual_export_not_public_approval(data):
    registry_records, ledger = data
    md = ho.render_markdown_report(registry_records, ledger)
    assert "advisory, not public approval" in md
    assert "does NOT grant public approval" in md


def test_validation_clean_or_warning(data):
    registry_records, ledger = data
    ex = ho.build_handoff_export(registry_records, ledger)
    items = rq.build_query_items(registry_records, ledger)
    ids = {r["registry_record_id"] for r in registry_records}
    res = ho.validate_handoff_export(ex, items, ids)
    assert res["status"] in ("PASS", "WARNING")
    assert res["blockers"] == []


def test_validation_blocks_hidden_citation(data):
    registry_records, ledger = data
    ex = ho.build_handoff_export(registry_records, ledger)
    items = rq.build_query_items(registry_records, ledger)
    ids = {r["registry_record_id"] for r in registry_records}
    ex["dashboard_summary"]["citation_guardrail_blocked_count"] = 0
    res = ho.validate_handoff_export(ex, items, ids)
    assert res["status"] == "BLOCKED"
    assert any("citation guardrail BLOCKED" in b for b in res["blockers"])


def test_validation_blocks_publish_ready(data):
    registry_records, ledger = data
    ex = ho.build_handoff_export(registry_records, ledger)
    items = rq.build_query_items(registry_records, ledger)
    ids = {r["registry_record_id"] for r in registry_records}
    ex["publish_ready"] = True
    res = ho.validate_handoff_export(ex, items, ids)
    assert res["status"] == "BLOCKED"
    assert any("approval/publish authority" in b for b in res["blockers"])


def test_validation_blocks_empty_demo():
    ex = ho.build_handoff_export([], [])
    res = ho.validate_handoff_export(ex, [], set())
    assert res["status"] == "BLOCKED"
    assert any("zero registry records or ledger entries" in b for b in res["blockers"])


def test_all_export_items_not_public_postable(data):
    registry_records, ledger = data
    ex = ho.build_handoff_export(registry_records, ledger)
    for entry in ex["ledger_event_summary"]:
        assert entry["publish_status"] == "NOT_PUBLIC_POSTABLE"
    assert ex["safety_posture"]["all_fixture_outputs_not_public_postable"] is True

