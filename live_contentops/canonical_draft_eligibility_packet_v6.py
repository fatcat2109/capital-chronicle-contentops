"""V6 Canonical Draft Eligibility Packet Definition.

Defines schemas for canonical draft eligibility states.
"""
from __future__ import annotations

from typing import Any


def make_canonical_draft_eligibility_packet() -> dict[str, Any]:
    """Generates the unapproved draft eligibility packet state."""
    return {
        "eligibility_status": "TEST_ONLY_APPROVAL_SIMULATION_REVIEW",
        "runtime_truth": False,
        "real_source_pack_approved": False,
        "test_only_approval_simulation": True,
        "redacted_source_pack_available": True,
        "redacted_claim_bindings_available": True,
        "approval_gate_passed_for_runtime": False,
        "approval_gate_passed_for_test_only": True,
        "canonical_draft_generation_allowed_for_runtime": False,
        "canonical_draft_generation_allowed_for_test_only": True,
        "article_copy_generated": False,
        "draft_markdown_created": False,
        "public_postable": False,
        "allowed_for_publication": False,
        "dispatch_allowed_now": False,
        "live_write_allowed_now": False,
        "outbox_entry_created": False,
        "provider_call_performed": False,
        "browser_session_started": False,
        "env_read_performed": False,
        "credentials_hydrated": False,
        "human_review_required": True,
        "kill_switch_active": True
    }
