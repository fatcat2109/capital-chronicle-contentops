"""V6 Real Source Pack Redaction Policy and Rules.

Defines rules to block raw URLs, evidence hashes, source excerpts, and signatures.
"""
from __future__ import annotations

from typing import Any


def make_redaction_policy() -> dict[str, Any]:
    """Generates the source-pack redaction policy definition."""
    return {
        "never_persist_raw_source_url": True,
        "never_persist_raw_evidence_hash": True,
        "never_persist_raw_source_excerpt": True,
        "never_persist_raw_operator_signature": True,
        "persist_presence_booleans_only": True,
        "persist_redacted_labels_only": True,
        "allowed_redacted_fields": [
            "source_requirement_id",
            "required_source_type",
            "source_name_redacted",
            "source_url_redacted",
            "source_publisher_redacted",
            "retrieval_method",
            "retrieved_at_redacted",
            "evidence_hash_present",
            "evidence_hash_redacted",
            "source_excerpt_ref_redacted",
            "source_excerpt_text_redacted",
            "source_supports_claim_ids",
            "operator_verified_by_redacted",
            "verification_status",
            "allowed_for_article_use",
            "human_review_required",
            "source_verification_required",
            "redaction_status",
            "raw_values_persisted",
            "runtime_truth"
        ],
        "forbidden_raw_fields": [
            "source_url",
            "evidence_hash",
            "source_excerpt",
            "source_excerpt_ref",
            "source_excerpt_text",
            "operator_verified_by",
            "operator_signature"
        ],
        "violation_blockers": [
            "raw_source_url_persisted",
            "raw_evidence_hash_persisted",
            "raw_source_excerpt_persisted",
            "raw_operator_signature_persisted",
            "fake_source_or_hash_detected",
            "public_ready_claim_detected"
        ]
    }
