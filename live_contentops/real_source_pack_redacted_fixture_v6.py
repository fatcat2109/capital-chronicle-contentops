"""V6 Real Source Pack Operator-Filled Redacted Fixture Generator.

Creates synthetic operator-filled redacted example fixtures.
"""
from __future__ import annotations

from typing import Any

CLAIM_MAPPINGS = {
    "req_67a5db6704f5": ["claim_d474a9fdbcd6"],
    "req_bfcb46cc38cc": ["claim_63d1cf20e9bf"],
    "req_e6edaf8e7750": ["claim_492c29ad9746"],
    "req_af610e135cf8": [],
    "req_91a0125c71fd": []
}


def make_operator_filled_redacted_fixture() -> dict[str, Any]:
    """Creates a synthetic operator-filled fixture that is redacted-only."""
    source_entries = []
    
    requirements = [
        {"id": "req_67a5db6704f5", "type": "treasury_yield_series"},
        {"id": "req_bfcb46cc38cc", "type": "yield_curve_calculation"},
        {"id": "req_e6edaf8e7750", "type": "historical_volatility"},
        {"id": "req_af610e135cf8", "type": "chart_table_data"},
        {"id": "req_91a0125c71fd", "type": "limitations_disclaimer"}
    ]

    for req in requirements:
        source_entries.append({
            "source_requirement_id": req["id"],
            "required_source_type": req["type"],
            "source_name_redacted": "REDACTED_SOURCE_NAME_PRESENT",
            "source_url_redacted": "REDACTED_SOURCE_URL_PRESENT",
            "source_publisher_redacted": "REDACTED_SOURCE_PUBLISHER_PRESENT",
            "retrieval_method": "manual_operator_research_redacted",
            "retrieved_at_redacted": "REDACTED_RETRIEVAL_TIMESTAMP_PRESENT",
            "evidence_hash_present": True,
            "evidence_hash_redacted": "REDACTED_EVIDENCE_HASH_PRESENT",
            "source_excerpt_ref_redacted": "REDACTED_EXCERPT_REF_PRESENT",
            "source_excerpt_text_redacted": "REDACTED_EXCERPT_TEXT_PRESENT",
            "source_supports_claim_ids": CLAIM_MAPPINGS.get(req["id"], []),
            "operator_verified_by_redacted": "REDACTED_OPERATOR_SIGNATURE_PRESENT",
            "verification_status": "redacted_presence_only_not_approved",
            "allowed_for_article_use": False,
            "human_review_required": True,
            "source_verification_required": True,
            "redaction_status": "redacted_presence_only",
            "raw_values_persisted": False,
            "runtime_truth": False
        })

    return {
        "fixture_status": "REDACTED_OPERATOR_FILLED_DRY_RUN_REVIEW",
        "runtime_truth": False,
        "real_source_pack_imported": False,
        "operator_filled_redacted_fixture": True,
        "raw_values_persisted": False,
        "source_pack_complete": False,
        "all_required_sources_verified": False,
        "all_claims_bound_to_sources": False,
        "canonical_draft_generation_allowed": False,
        "allowed_for_article_use": False,
        "allowed_for_publication": False,
        "public_postable": False,
        "dispatch_allowed_now": False,
        "live_write_allowed_now": False,
        "human_review_required": True,
        "kill_switch_active": True,
        "source_entries": source_entries
    }
