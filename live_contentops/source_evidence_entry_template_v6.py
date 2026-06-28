"""V6 Source Evidence Entry Template.

Builds blank templates for manual operator research entries.
"""
from __future__ import annotations

from typing import Any


def generate_source_evidence_entry_template(req_id: str, source_type: str) -> dict[str, Any]:
    """Generates a blank manual entry template with no fake values or faked evidence hashes."""
    return {
        "source_requirement_id": req_id,
        "required_source_type": source_type,
        "source_name": None,
        "source_url": None,
        "source_publisher": None,
        "retrieval_method": "manual_operator_research_pending",
        "retrieved_at": None,
        "evidence_hash": None,
        "source_excerpt_ref": None,
        "source_excerpt_text_redacted": None,
        "source_supports_claim_ids": [],
        "limitations": None,
        "caveats": None,
        "operator_verified_by": None,
        "verification_status": "missing",
        "allowed_for_article_use": False,
        "human_review_required": True,
        "source_verification_required": True
    }
