"""V6 Approved Redacted Source Pack Test Fixture.

Defines test-only simulated approved redacted source pack.
"""
from __future__ import annotations

from typing import Any


def make_approved_redacted_source_pack_summary() -> dict[str, Any]:
    """Generates the test-only approved redacted source-pack summary."""
    return {
        "test_only": True,
        "runtime_truth": False,
        "real_operator_approval_created": False,
        "real_jim_approval_created": False,
        "approval_simulation_used": True,
        "approval_valid_for_draft_generation_only_in_test": True,
        "committed_runtime_approval_created": False,
        "operator_signature_persisted": False,
        "source_pack_hash_persisted": False,
        "approved_at_persisted": False,
        "raw_values_persisted": False,
        "raw_source_urls_persisted": False,
        "raw_evidence_hashes_persisted": False,
        "raw_source_excerpts_persisted": False,
        "publication_allowed": False,
        "dispatch_allowed_now": False,
        "public_postable": False
    }
