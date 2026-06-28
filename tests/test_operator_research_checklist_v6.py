"""Test operator research checklist module."""
from __future__ import annotations

from live_contentops import operator_research_checklist_v6 as ch


def test_generate_operator_research_checklist():
    reqs = [
        {"research_requirement_id": "req_1", "required_source_type": "type_1", "source_name_placeholder": "Placeholder 1"}
    ]

    checklist = ch.generate_operator_research_checklist(reqs)
    assert len(checklist) == 1

    item = checklist[0]
    assert item["checklist_item_id"] == "item_req_1"
    assert item["source_requirement_id"] == "req_1"
    assert item["required_source_type"] == "type_1"
    assert item["source_name_placeholder"] == "Placeholder 1"
    assert item["operator_entry_required"] is True
    assert item["source_url_required_for_future_verified_pack"] is True
    assert item["evidence_hash_required_for_future_verified_pack"] is True
    assert item["current_status"] == "missing"
    assert item["blocks_draft_generation"] is True
