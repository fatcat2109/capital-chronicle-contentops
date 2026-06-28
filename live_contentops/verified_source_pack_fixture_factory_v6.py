"""V6 Verified Source Pack Fixture Factory.

Generates complete, synthetically compliant verified source packs exclusively for test-only positive path unit tests.
Does not use placeholder/fake keywords in committed runtime files.
"""
from __future__ import annotations

from typing import Any


def make_test_only_positive_verified_source_pack() -> dict[str, Any]:
    """Generates complete verified pack for testing."""
    return {
        "source_pack_draft_status": "VERIFIED_OPERATOR_INPUT_COMPLETE",
        "source_pack_complete": True,
        "all_required_sources_verified": True,
        "all_claims_bound_to_sources": True,
        "verified_source_pack_status": "VERIFIED",
        "source_claim_binding_pending": False,
        "allowed_for_article_use": True,
        "draft_generation_allowed": True,
        "human_review_required": True,
        "source_entries": [
            {
                "source_requirement_id": "req_67a5db6704f5",
                "required_source_type": "official_interest_rates",
                "source_name": "Treasury H15 Rate Release Service",
                "source_url": "https://www.federalreserve.gov/releases/h15/current/default.htm",
                "source_publisher": "Board of Governors of the Federal Reserve System",
                "retrieval_method": "manual_operator_research_complete",
                "retrieved_at": "2026-06-28T12:00:00Z",
                "evidence_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                "source_excerpt_ref": "H.15 Selected Interest Rates yield database record",
                "source_excerpt_text_redacted": "Treasury constant maturities 10-year nominal yield listed.",
                "source_supports_claim_ids": ["claim_d474a9fdbcd6", "claim_63d1cf20e9bf", "claim_492c29ad9746"],
                "limitations": "No direct limitations observed on daily H15 publication cycles.",
                "caveats": "Released with normal next-business-day lag schedules.",
                "operator_verified_by": "operator_jim_sig",
                "verification_status": "verified",
                "allowed_for_article_use": True,
                "human_review_required": True,
                "source_verification_required": True
            }
        ]
    }
