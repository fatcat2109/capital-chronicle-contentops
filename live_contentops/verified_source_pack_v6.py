"""V6 Verified Source Pack Schema and Default Missing Creator.

Defines schemas and processes research requirements into blocked missing default source packs.
"""
from __future__ import annotations

from typing import Any


def get_verified_source_pack_schema() -> dict[str, Any]:
    """Returns the verified source pack schema definition."""
    return {
        "title": "VerifiedSourcePack",
        "type": "object",
        "properties": {
            "verified_source_pack_status": {"type": "string"},
            "source_pack_complete": {"type": "boolean"},
            "human_research_required": {"type": "boolean"},
            "source_verification_required": {"type": "boolean"},
            "source_entries": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "source_requirement_id": {"type": "string"},
                        "required_source_type": {"type": "string"},
                        "source_name": {"type": "string"},
                        "source_url": {"type": ["string", "null"]},
                        "source_publisher": {"type": "string"},
                        "retrieval_method": {"type": "string"},
                        "retrieved_at": {"type": ["string", "null"]},
                        "evidence_hash": {"type": ["string", "null"]},
                        "source_excerpt_ref": {"type": "string"},
                        "verification_status": {"type": "string"},
                        "operator_verified_by": {"type": ["string", "null"]},
                        "source_supports_claim_ids": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "limitations": {"type": "string"},
                        "caveats": {"type": "string"},
                        "allowed_for_article_use": {"type": "boolean"},
                        "human_review_required": {"type": "boolean"}
                    },
                    "required": [
                        "source_requirement_id", "required_source_type", "source_name",
                        "source_url", "source_publisher", "retrieval_method", "retrieved_at",
                        "evidence_hash", "source_excerpt_ref", "verification_status",
                        "operator_verified_by", "source_supports_claim_ids", "limitations",
                        "caveats", "allowed_for_article_use", "human_review_required"
                    ]
                }
            }
        },
        "required": [
            "verified_source_pack_status", "source_pack_complete",
            "human_research_required", "source_verification_required", "source_entries"
        ]
    }


def generate_default_missing_source_pack(requirements: list[dict[str, Any]]) -> dict[str, Any]:
    """Constructs a default verified source pack showing missing status from requirements."""
    source_entries = []
    for r in requirements:
        source_entries.append({
            "source_requirement_id": r["research_requirement_id"],
            "required_source_type": r["required_source_type"],
            "source_name": r["source_name_placeholder"],
            "source_url": None,
            "source_publisher": "Unverified Publisher",
            "retrieval_method": "manual_ingestion_pending",
            "retrieved_at": None,
            "evidence_hash": None,
            "source_excerpt_ref": "None: verification pending",
            "verification_status": "missing",
            "operator_verified_by": None,
            "source_supports_claim_ids": [],
            "limitations": "No limitations verified.",
            "caveats": "Verification is missing.",
            "allowed_for_article_use": False,
            "human_review_required": True
        })

    return {
        "verified_source_pack_status": "MISSING_REQUIRED_SOURCE_VERIFICATION",
        "source_pack_complete": False,
        "human_research_required": True,
        "source_verification_required": True,
        "source_entries": source_entries
    }
