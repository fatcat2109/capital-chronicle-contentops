"""Test V6 Canonical Article Studio Review Checklist."""
from __future__ import annotations

from live_contentops import canonical_article_studio_review_checklist_v6 as checklist_builder


def test_make_canonical_article_studio_editor_checklist():
    checklist = checklist_builder.make_canonical_article_studio_editor_checklist()

    assert checklist["checklist_status"] == "EDITOR_REVIEW_BLOCKED_PENDING_SOURCE_APPROVAL"
    items = checklist["items"]
    assert len(items) == 9

    item_ids = [item["item_id"] for item in items]
    expected_ids = [
        "real_source_pack_approval_required",
        "runtime_claim_binding_required",
        "source_name_redaction_required",
        "article_copy_not_generated",
        "no_publication_ready_claim",
        "no_dispatch_ready_claim",
        "no_financial_advice_language",
        "no_fake_metrics_or_citations",
        "jim_final_review_required"
    ]
    assert item_ids == expected_ids

    for item in items:
        assert item["current_status"] in ["blocked", "pending"]
        assert isinstance(item["blocks_article_generation"], bool)
        assert item["blocks_publication"] is True
        assert item["evidence_ref"].endswith(".json")
