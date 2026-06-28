"""Test V6 Operator Source Pack Checklist and Approval Template Generator."""
from __future__ import annotations

from live_contentops import operator_source_pack_approval_checklist_v6 as checklist_builder


def test_make_review_checklist_and_approval_template():
    scaffold = [
        {
            "checklist_item_id": "item_req_67a5db6704f5",
            "source_requirement_id": "req_67a5db6704f5",
            "required_source_type": "treasury_yield_series"
        }
    ]
    claims = [
        {
            "claim_id": "claim_d474a9fdbcd6",
            "source_requirement_refs": ["req_67a5db6704f5"]
        }
    ]

    checklist = checklist_builder.make_review_checklist(scaffold, claims)

    assert len(checklist) == 1
    item = checklist[0]
    assert item["checklist_item_id"] == "item_req_67a5db6704f5"
    assert item["source_requirement_id"] == "req_67a5db6704f5"
    assert item["required_source_type"] == "treasury_yield_series"
    assert item["source_url_required"] is True
    assert item["evidence_hash_required"] is True
    assert item["retrieved_at_required"] is True
    assert item["operator_verified_by_required"] is True
    assert item["source_excerpt_ref_required"] is True
    assert item["claim_binding_required"] is True
    assert item["current_status"] == "missing"
    assert item["blocks_real_draft_generation"] is True
    assert item["blocks_publication"] is True
    assert item["bound_claim_ids"] == ["claim_d474a9fdbcd6"]
    assert item["review_notes_placeholder"] is None

    template = checklist_builder.make_operator_approval_template()
    assert template["approval_template_status"] == "OPERATOR_SIGNATURE_REQUIRED"
    assert template["operator_id"] is None
    assert template["source_pack_hash"] is None
    assert template["reviewed_source_requirement_ids"] == []
    assert template["approved_claim_ids"] == []
    assert template["approved_at"] is None
    assert template["approval_scope"] == "source_pack_review_only"
    assert template["valid_for_draft_generation"] is False
    assert template["valid_for_publication"] is False
    assert template["valid_for_dispatch"] is False
    assert template["revoked"] is False
    assert template["human_review_required"] is True
    assert template["kill_switch_active"] is True
