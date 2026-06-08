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
from live_contentops import operator_dashboard as dash


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
        "source_fixture_id": "dash_blocked_demo",
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
    registry_records = [reg_clean, reg_blocked]
    ledger = led_clean + led_blocked
    return registry_records, ledger


def test_dashboard_counts_correct_and_fixture_backed(data):
    registry_records, ledger = data
    d = dash.build_dashboard(registry_records, ledger)
    assert d["registry_record_count"] == 2
    assert d["ledger_entry_count"] == len(ledger)
    assert d["blocked_count"] == 1
    assert d["pending_review_count"] == 1
    assert d["manual_export_packet_accept_count"] == 1
    assert d["citation_guardrail_blocked_count"] == 1


def test_dashboard_safety_counts_zero(data):
    registry_records, ledger = data
    d = dash.build_dashboard(registry_records, ledger)
    assert d["publish_ready_count"] == 0
    assert d["approval_granted_count"] == 0
    assert d["provider_call_allowed_count"] == 0
    assert d["search_call_allowed_count"] == 0
    assert d["platform_action_allowed_count"] == 0
    assert d["all_fixture_outputs_not_public_postable"] is True


def test_dashboard_is_deterministic(data):
    registry_records, ledger = data
    d1 = dash.build_dashboard(registry_records, ledger)
    d2 = dash.build_dashboard(registry_records, ledger)
    assert json.dumps(d1, sort_keys=True) == json.dumps(d2, sort_keys=True)


def test_highest_priority_surfaces_blocked_first(data):
    registry_records, ledger = data
    d = dash.build_dashboard(registry_records, ledger)
    assert d["highest_priority_items"][0]["queue_status"] == "BLOCKED"


def test_dashboard_validation_clean(data):
    registry_records, ledger = data
    d = dash.build_dashboard(registry_records, ledger)
    items = rq.build_query_items(registry_records, ledger)
    ids = {r["registry_record_id"] for r in registry_records}
    res = dash.validate_dashboard(d, items, ids)
    assert res["status"] in ("PASS", "WARNING")
    assert res["blockers"] == []


def test_dashboard_cannot_hide_citation_blocked(data):
    registry_records, ledger = data
    d = dash.build_dashboard(registry_records, ledger)
    items = rq.build_query_items(registry_records, ledger)
    ids = {r["registry_record_id"] for r in registry_records}
    d["citation_guardrail_blocked_count"] = 0  # attempt to hide
    res = dash.validate_dashboard(d, items, ids)
    assert res["status"] == "BLOCKED"
    assert any("citation guardrail BLOCKED" in b for b in res["blockers"])


def test_dashboard_validation_blocks_publish_ready(data):
    registry_records, ledger = data
    d = dash.build_dashboard(registry_records, ledger)
    items = rq.build_query_items(registry_records, ledger)
    ids = {r["registry_record_id"] for r in registry_records}
    d["publish_ready_count"] = 1
    res = dash.validate_dashboard(d, items, ids)
    assert res["status"] == "BLOCKED"
    assert any("publish_ready" in b for b in res["blockers"])


def test_markdown_dashboard_has_banners(data):
    registry_records, ledger = data
    md = dash.render_markdown_report(registry_records, ledger)
    for banner in dash.MARKDOWN_BANNERS:
        assert banner in md
    assert "approval_granted=false" in md
    assert "publish_ready=false" in md
    assert "NOT_PUBLIC_POSTABLE" in md
    assert "Next Operator Action" in md


def test_manual_export_accept_not_public_approval(data):
    registry_records, ledger = data
    md = dash.render_markdown_report(registry_records, ledger)
    assert "advisory, not public approval" in md
