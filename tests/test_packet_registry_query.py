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
        "source_fixture_id": "query_blocked_demo",
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
def items_and_ids():
    reg_clean, led_clean = _build(load_fixture("packet_registry_input.json")["packets"][0])
    reg_blocked, led_blocked = _blocked_build()
    registry_records = [reg_clean, reg_blocked]
    ledger = led_clean + led_blocked
    items = rq.build_query_items(registry_records, ledger)
    ids = {r["registry_record_id"] for r in registry_records}
    return items, ids


def test_query_item_has_required_fields(items_and_ids):
    items, _ = items_and_ids
    required = [
        "registry_record_id", "export_packet_id", "queue_item_id", "history_id",
        "content_type", "target_platforms", "packet_status", "queue_status",
        "latest_decision_status", "audit_status", "blocker_count", "warning_count",
        "latest_event_type", "latest_decision_type", "no_public_post_reason",
        "approval_granted", "publish_ready", "provider_call_allowed",
        "search_call_allowed", "platform_action_allowed",
    ]
    for item in items:
        for key in required:
            assert key in item, f"missing field: {key}"
        assert item["approval_granted"] is False
        assert item["publish_ready"] is False
        assert item["platform_action_allowed"] is False


def test_filter_by_queue_status(items_and_ids):
    items, _ = items_and_ids
    blocked = rq.filter_items(items, {"queue_status": "BLOCKED"})
    assert all(i["queue_status"] == "BLOCKED" for i in blocked)
    assert len(blocked) >= 1


def test_filter_by_target_platform(items_and_ids):
    items, _ = items_and_ids
    x_items = rq.filter_items(items, {"target_platform": "x"})
    assert all("x" in i["target_platforms"] for i in x_items)


def test_filter_has_blockers(items_and_ids):
    items, _ = items_and_ids
    with_blockers = rq.filter_items(items, {"has_blockers": True})
    assert all(i["blocker_count"] > 0 for i in with_blockers)


def test_status_severity_sort_is_deterministic(items_and_ids):
    items, _ = items_and_ids
    s1 = rq.sort_items(items, "status_severity")
    s2 = rq.sort_items(items, "status_severity")
    assert [i["registry_record_id"] for i in s1] == [i["registry_record_id"] for i in s2]


def test_highest_priority_surfaces_blocked_first(items_and_ids):
    items, _ = items_and_ids
    hp = rq.highest_priority_items(items)
    assert hp[0]["queue_status"] == "BLOCKED"


def test_grouping_is_deterministic(items_and_ids):
    items, _ = items_and_ids
    g1 = rq.group_items(items, "status_severity")
    g2 = rq.group_items(items, "status_severity")
    assert json.dumps({k: [i["registry_record_id"] for i in v] for k, v in g1.items()},
                      sort_keys=True) == \
        json.dumps({k: [i["registry_record_id"] for i in v] for k, v in g2.items()},
                   sort_keys=True)


def test_validation_clean(items_and_ids):
    items, ids = items_and_ids
    res = rq.validate_query_items(items, ids)
    assert res["status"] in ("PASS", "WARNING")
    assert res["blockers"] == []


def test_validation_blocks_publish_ready(items_and_ids):
    items, ids = items_and_ids
    items[0]["publish_ready"] = True
    res = rq.validate_query_items(items, ids)
    assert res["status"] == "BLOCKED"
    assert any("publish_ready" in b for b in res["blockers"])


def test_validation_blocks_unknown_registry(items_and_ids):
    items, _ = items_and_ids
    res = rq.validate_query_items(items, {"nonexistent"})
    assert res["status"] == "BLOCKED"
    assert any("unknown registry record" in b for b in res["blockers"])


def test_all_items_not_public_postable(items_and_ids):
    items, _ = items_and_ids
    for item in items:
        assert item["no_public_post_reason"]
