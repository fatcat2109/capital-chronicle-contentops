"""Test V6 Real Source Pack Operator Approval Template."""
from __future__ import annotations

from live_contentops import real_source_pack_operator_approval_template_v6 as template_builder


def test_make_operator_approval_template():
    template = template_builder.make_operator_approval_template()
    
    assert template["approval_template_status"] == "BLANK_OPERATOR_APPROVAL_REQUIRED"
    assert template["approval_id"] is None
    assert template["operator_id_redacted"] is None
    assert template["operator_signature_redacted"] is None
    assert template["source_pack_hash_redacted"] is None
    assert template["approved_source_requirement_ids"] == []
    assert template["approved_claim_ids"] == []
    assert template["approval_scope"] == "source_pack_draft_generation_review_only"
    assert template["approved_at_redacted"] is None
    assert template["approval_created"] is False
    assert template["approval_revoked"] is False
    assert template["valid_for_draft_generation"] is False
    assert template["valid_for_article_use"] is False
    assert template["valid_for_publication"] is False
    assert template["valid_for_dispatch"] is False
    assert template["raw_values_persisted"] is False
    assert template["runtime_truth"] is False
    assert template["human_review_required"] is True
    assert template["kill_switch_active"] is True
