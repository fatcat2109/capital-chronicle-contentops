"""V6 Operator Source Pack Checklist and Approval Template Generator.

Binds requirements and claims into structured checklists and blank signature templates.
"""
from __future__ import annotations

from typing import Any


def make_review_checklist(
    research_checklist: list[dict[str, Any]],
    claim_scaffold: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Builds a review-only unpopulated evidence checklist from input scaffolds."""
    checklist = []
    
    # Map requirements to claims
    requirement_to_claims: dict[str, list[str]] = {}
    for c in claim_scaffold:
        claim_id = c.get("claim_id")
        for ref in c.get("source_requirement_refs", []):
            requirement_to_claims.setdefault(ref, []).append(claim_id)

    for item in research_checklist:
        req_id = item.get("source_requirement_id")
        checklist.append({
            "checklist_item_id": item.get("checklist_item_id", f"item_{req_id}"),
            "source_requirement_id": req_id,
            "required_source_type": item.get("required_source_type"),
            "required_operator_fields": [
                "source_name", "source_url", "source_publisher",
                "retrieval_method", "retrieved_at", "evidence_hash", "source_excerpt_ref"
            ],
            "source_url_required": True,
            "evidence_hash_required": True,
            "retrieved_at_required": True,
            "operator_verified_by_required": True,
            "source_excerpt_ref_required": True,
            "claim_binding_required": True,
            "current_status": "missing",
            "blocks_real_draft_generation": True,
            "blocks_publication": True,
            "bound_claim_ids": requirement_to_claims.get(req_id, []),
            "review_notes_placeholder": None
        })
        
    return checklist


def make_operator_approval_template() -> dict[str, Any]:
    """Builds a strictly blank source-pack approval template."""
    return {
        "approval_template_status": "OPERATOR_SIGNATURE_REQUIRED",
        "operator_id": None,
        "source_pack_hash": None,
        "reviewed_source_requirement_ids": [],
        "approved_claim_ids": [],
        "approved_at": None,
        "approval_scope": "source_pack_review_only",
        "valid_for_draft_generation": False,
        "valid_for_publication": False,
        "valid_for_dispatch": False,
        "revoked": False,
        "human_review_required": True,
        "kill_switch_active": True
    }
