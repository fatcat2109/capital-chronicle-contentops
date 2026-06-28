"""V6 Operator Source Pack Review Packet Generator.

Defines the structure and schema for tracking the operator source pack review state.
"""
from __future__ import annotations

from typing import Any


def make_operator_source_pack_review_packet() -> dict[str, Any]:
    """Generates the default unapproved source-pack review packet."""
    return {
        "review_status": "OPERATOR_SOURCE_PACK_REVIEW_REQUIRED",
        "runtime_truth": False,
        "real_source_pack_imported": False,
        "source_pack_approved_by_operator": False,
        "source_pack_complete": False,
        "all_required_sources_verified": False,
        "all_claims_bound_to_sources": False,
        "positive_path_test_passed": True,
        "positive_path_runtime_truth": False,
        "canonical_draft_generation_allowed": False,
        "article_copy_generated_from_real_sources": False,
        "allowed_for_publication": False,
        "public_postable": False,
        "dispatch_allowed_now": False,
        "live_write_allowed_now": False,
        "provider_call_performed": False,
        "browser_session_started": False,
        "env_read_performed": False,
        "credentials_hydrated": False,
        "human_review_required": True,
        "kill_switch_active": True
    }
