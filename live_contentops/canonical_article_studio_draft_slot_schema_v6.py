"""V6 Canonical Article Studio Draft Slot Schema.

Defines schemas for empty draft slots.
"""
from __future__ import annotations

from typing import Any


def make_canonical_article_studio_draft_slot_schema() -> list[dict[str, Any]]:
    """Generates the slot schemas for the empty draft shell."""
    return [
        {
            "slot_id": "slot_title",
            "slot_type": "title",
            "allowed_content_state": "empty_or_placeholder_only",
            "current_value": None,
            "generated": False,
            "source_binding_required": True,
            "blocks_publication": True
        },
        {
            "slot_id": "slot_dek",
            "slot_type": "dek",
            "allowed_content_state": "empty_or_placeholder_only",
            "current_value": None,
            "generated": False,
            "source_binding_required": True,
            "blocks_publication": True
        },
        {
            "slot_id": "slot_thesis",
            "slot_type": "thesis",
            "allowed_content_state": "empty_or_placeholder_only",
            "current_value": None,
            "generated": False,
            "source_binding_required": True,
            "blocks_publication": True
        },
        {
            "slot_id": "slot_claim_summary",
            "slot_type": "claim_summary",
            "allowed_content_state": "empty_or_placeholder_only",
            "current_value": None,
            "generated": False,
            "source_binding_required": True,
            "blocks_publication": True
        },
        {
            "slot_id": "slot_evidence_placeholder",
            "slot_type": "evidence_placeholder",
            "allowed_content_state": "empty_or_placeholder_only",
            "current_value": None,
            "generated": False,
            "source_binding_required": True,
            "blocks_publication": True
        },
        {
            "slot_id": "slot_risk_and_limitations",
            "slot_type": "risk_and_limitations",
            "allowed_content_state": "empty_or_placeholder_only",
            "current_value": None,
            "generated": False,
            "source_binding_required": True,
            "blocks_publication": True
        },
        {
            "slot_id": "slot_conclusion",
            "slot_type": "conclusion",
            "allowed_content_state": "empty_or_placeholder_only",
            "current_value": None,
            "generated": False,
            "source_binding_required": True,
            "blocks_publication": True
        },
        {
            "slot_id": "slot_seo_title",
            "slot_type": "seo_title",
            "allowed_content_state": "empty_or_placeholder_only",
            "current_value": None,
            "generated": False,
            "source_binding_required": False,
            "blocks_publication": True
        },
        {
            "slot_id": "slot_seo_meta_description",
            "slot_type": "seo_meta_description",
            "allowed_content_state": "empty_or_placeholder_only",
            "current_value": None,
            "generated": False,
            "source_binding_required": False,
            "blocks_publication": True
        }
    ]
