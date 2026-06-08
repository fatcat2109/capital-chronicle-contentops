import json
import os

import pytest

from live_contentops import editorial_packet_export as export
from live_contentops import packet_review_queue as queue
from live_contentops import operator_decision as od
from live_contentops import review_history as rh
from live_contentops import packet_registry as pr
from live_contentops import review_ledger as rl


def load_fixture(name):
    path = os.path.join(os.path.dirname(__file__), "fixtures", "editorial", name)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _build_all(packet_input):
    packet = export.build_export_packet(packet_input)
    item = queue.build_queue_item(packet)
    records = [od.build_decision_record(item, d) for d in packet_input.get("decisions", [])]
    history = rh.build_history(item, records)
    registry = pr.build_registry_record(packet, item, history)
    ledger = rl.build_ledger(registry, packet, item, history)
    return packet, item, history, registry, ledger


@pytest.fixture
def built():
    data = load_fixture("packet_registry_input.json")
    return _build_all(data["packets"][0])


def test_ledger_entry_has_all_required_fields(built):
    _, _, _, _, ledger = built
    required = [
        "ledger_entry_id", "registry_record_id", "export_packet_id", "queue_item_id",
        "history_id", "event_type", "event_timestamp", "event_source", "event_summary",
        "blocker_count", "warning_count", "decision_type", "decision_status",
        "publish_status", "approval_granted", "publish_ready", "authority_boundary_note",
    ]
    for entry in ledger:
        for key in required:
            assert key in entry, f"missing field: {key}"


def test_ledger_entry_safety_flags(built):
    _, _, _, _, ledger = built
    for entry in ledger:
        assert entry["approval_granted"] is False
        assert entry["publish_ready"] is False
        assert entry["provider_call_allowed"] is False
        assert entry["search_call_allowed"] is False
        assert entry["platform_action_allowed"] is False
        assert entry["publish_status"] == "NOT_PUBLIC_POSTABLE"
        assert entry["event_type"] in rl.SUPPORTED_EVENT_TYPES


def test_ledger_is_deterministic():
    data = load_fixture("packet_registry_input.json")
    _, _, _, _, l1 = _build_all(data["packets"][0])
    _, _, _, _, l2 = _build_all(data["packets"][0])
    assert json.dumps(l1, sort_keys=True) == json.dumps(l2, sort_keys=True)


def test_ledger_append_only_preserves_prior(built):
    _, _, _, registry, ledger = built
    base_len = len(ledger)
    extra = rl.build_ledger_entry(registry, "REGISTRY_RECORD_UPDATED", seq=999)
    new_ledger = ledger + [extra]
    assert new_ledger[:base_len] == ledger
    assert len(new_ledger) == base_len + 1


def test_ledger_validation_clean(built):
    _, _, _, registry, ledger = built
    res = rl.validate_ledger(ledger, {registry["registry_record_id"]})
    assert res["status"] in ("PASS", "WARNING")
    assert res["blockers"] == []


def test_ledger_unknown_registry_reference_blocks(built):
    _, _, _, _, ledger = built
    res = rl.validate_ledger(ledger, {"some_other_id"})
    assert res["status"] == "BLOCKED"
    assert any("unknown registry record" in b for b in res["blockers"])


def test_ledger_authority_grant_blocks(built):
    _, _, _, registry, ledger = built
    ledger[0]["publish_ready"] = True
    res = rl.validate_ledger(ledger, {registry["registry_record_id"]})
    assert res["status"] == "BLOCKED"
    assert any("approval/publish authority" in b for b in res["blockers"])


def test_manual_export_accept_event_not_public_approval(built):
    _, _, _, _, ledger = built
    accepts = [e for e in ledger if e["event_type"] == "MANUAL_EXPORT_PACKET_ACCEPTED"]
    assert len(accepts) == 1
    entry = accepts[0]
    assert entry["approval_granted"] is False
    assert entry["publish_ready"] is False
    assert entry["platform_action_allowed"] is False
    assert entry["publish_status"] == "NOT_PUBLIC_POSTABLE"


def test_summary_counts_correct(built):
    _, _, _, registry, ledger = built
    summary = rl.summarize_registry([registry], ledger)
    assert summary["registry_record_count"] == 1
    assert summary["ledger_entry_count"] == len(ledger)
    assert summary["publish_ready_count"] == 0
    assert summary["approval_granted_count"] == 0
    assert summary["all_fixture_outputs_not_public_postable"] is True
    assert summary["manual_export_packet_accept_count"] == 1


def test_markdown_report_has_banners(built):
    _, _, _, registry, ledger = built
    md = rl.render_markdown_report([registry], ledger)
    for banner in rl.MARKDOWN_BANNERS:
        assert banner in md
    assert "approval_granted=false" in md
    assert "publish_ready=false" in md
    assert "NOT_PUBLIC_POSTABLE" in md
