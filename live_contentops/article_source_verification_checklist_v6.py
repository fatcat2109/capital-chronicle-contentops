"""V6 Article Source Verification Checklist.

Builds a checklist for operators to verify sources before finalizing publication drafts.
"""
from __future__ import annotations

import hashlib
from typing import Any


def generate_source_verification_checklist(
    article_packet_id: str, requirements: list[dict[str, Any]]
) -> dict[str, Any]:
    """Generates the review-only source verification checklist based on the requirements."""
    hasher = hashlib.sha256(f"checklist_{article_packet_id}".encode("utf-8"))
    checklist_id = f"checklist_{hasher.hexdigest()[:12]}"

    checklist_items = []
    requirements_validated = True

    for r in requirements:
        is_verified = r.get("source_verification_status") == "verified"
        if not is_verified:
            requirements_validated = False

        checklist_items.append({
            "research_requirement_id": r["research_requirement_id"],
            "required_source_type": r["required_source_type"],
            "source_name_placeholder": r["source_name_placeholder"],
            "verification_status": r["source_verification_status"],
            "operator_verification_performed": False,
            "verification_timestamp": None,
            "verification_evidence_hash": None,
            "verification_audit_pass": is_verified
        })

    return {
        "checklist_id": checklist_id,
        "source_packet_ref_id": article_packet_id,
        "requirements_validated": requirements_validated,
        "checklist_items": checklist_items,
        "human_review_required": True,
        "audit_pass_ready": False
    }
