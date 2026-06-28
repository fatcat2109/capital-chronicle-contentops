"""V6 Canonical Article Studio Review Checklist.

Defines editor review checklists for queue items.
"""
from __future__ import annotations

from typing import Any


def make_canonical_article_studio_editor_checklist() -> dict[str, Any]:
    """Generates the editor review checklist."""
    return {
        "checklist_status": "EDITOR_REVIEW_BLOCKED_PENDING_SOURCE_APPROVAL",
        "items": [
            {
                "item_id": "real_source_pack_approval_required",
                "current_status": "blocked",
                "blocks_article_generation": True,
                "blocks_publication": True,
                "evidence_ref": "source_pack_operator_approval_gate_packet.json"
            },
            {
                "item_id": "runtime_claim_binding_required",
                "current_status": "pending",
                "blocks_article_generation": True,
                "blocks_publication": True,
                "evidence_ref": "canonical_draft_claim_eligibility_matrix.json"
            },
            {
                "item_id": "source_name_redaction_required",
                "current_status": "pending",
                "blocks_article_generation": False,
                "blocks_publication": True,
                "evidence_ref": "canonical_draft_eligibility_validation_report.json"
            },
            {
                "item_id": "article_copy_not_generated",
                "current_status": "blocked",
                "blocks_article_generation": True,
                "blocks_publication": True,
                "evidence_ref": "canonical_draft_eligibility_packet.json"
            },
            {
                "item_id": "no_publication_ready_claim",
                "current_status": "pending",
                "blocks_article_generation": False,
                "blocks_publication": True,
                "evidence_ref": "canonical_draft_eligibility_validation_report.json"
            },
            {
                "item_id": "no_dispatch_ready_claim",
                "current_status": "pending",
                "blocks_article_generation": False,
                "blocks_publication": True,
                "evidence_ref": "canonical_draft_eligibility_validation_report.json"
            },
            {
                "item_id": "no_financial_advice_language",
                "current_status": "pending",
                "blocks_article_generation": False,
                "blocks_publication": True,
                "evidence_ref": "canonical_draft_eligibility_validation_report.json"
            },
            {
                "item_id": "no_fake_metrics_or_citations",
                "current_status": "pending",
                "blocks_article_generation": False,
                "blocks_publication": True,
                "evidence_ref": "canonical_draft_eligibility_validation_report.json"
            },
            {
                "item_id": "jim_final_review_required",
                "current_status": "pending",
                "blocks_article_generation": False,
                "blocks_publication": True,
                "evidence_ref": "source_pack_operator_approval_gate_packet.json"
            }
        ]
    }
