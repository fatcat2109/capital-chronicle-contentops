"""V6 Operator Research Checklist Generator.

Converts upstream research requirements into structured checklists with verification questions.
"""
from __future__ import annotations

from typing import Any


def generate_operator_research_checklist(requirements: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Builds checklist items requiring operator entries for each research requirement."""
    checklist = []
    for r in requirements:
        req_id = r["research_requirement_id"]
        source_type = r["required_source_type"]
        placeholder = r["source_name_placeholder"]

        checklist.append({
            "checklist_item_id": f"item_{req_id}",
            "source_requirement_id": req_id,
            "required_source_type": source_type,
            "source_name_placeholder": placeholder,
            "official_source_required": True,
            "research_question": f"What is the official source or index reference for {source_type}?",
            "evidence_needed": "Primary official URL, retrieved data excerpt, and verifiable hash.",
            "accepted_evidence_fields": [
                "source_name", "source_url", "source_publisher",
                "retrieval_method", "retrieved_at", "evidence_hash",
                "source_excerpt_ref"
            ],
            "operator_entry_required": True,
            "source_url_required_for_future_verified_pack": True,
            "evidence_hash_required_for_future_verified_pack": True,
            "source_excerpt_ref_required": True,
            "retrieved_at_required": True,
            "operator_verified_by_required": True,
            "current_status": "missing",
            "blocks_draft_generation": True
        })

    return checklist
