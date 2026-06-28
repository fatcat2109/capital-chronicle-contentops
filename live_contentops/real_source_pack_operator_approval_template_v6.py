"""V6 Real Source Pack Operator Approval Template Definition.

Creates blank approval templates for operator sign-offs.
"""
from __future__ import annotations

from typing import Any


def make_operator_approval_template() -> dict[str, Any]:
    """Generates the blank operator approval template."""
    return {
        "approval_template_status": "BLANK_OPERATOR_APPROVAL_REQUIRED",
        "approval_id": None,
        "operator_id_redacted": None,
        "operator_signature_redacted": None,
        "source_pack_hash_redacted": None,
        "approved_source_requirement_ids": [],
        "approved_claim_ids": [],
        "approval_scope": "source_pack_draft_generation_review_only",
        "approved_at_redacted": None,
        "approval_created": False,
        "approval_revoked": False,
        "valid_for_draft_generation": False,
        "valid_for_article_use": False,
        "valid_for_publication": False,
        "valid_for_dispatch": False,
        "raw_values_persisted": False,
        "runtime_truth": False,
        "human_review_required": True,
        "kill_switch_active": True
    }
