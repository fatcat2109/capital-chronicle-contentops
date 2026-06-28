"""Test V6 Approved Redacted Source Pack Test Fixture."""
from __future__ import annotations

from live_contentops import approved_redacted_source_pack_test_fixture_v6 as summary_builder


def test_make_approved_redacted_source_pack_summary():
    summary = summary_builder.make_approved_redacted_source_pack_summary()

    assert summary["test_only"] is True
    assert summary["runtime_truth"] is False
    assert summary["real_operator_approval_created"] is False
    assert summary["real_jim_approval_created"] is False
    assert summary["approval_simulation_used"] is True
    assert summary["approval_valid_for_draft_generation_only_in_test"] is True
    assert summary["committed_runtime_approval_created"] is False
    assert summary["operator_signature_persisted"] is False
    assert summary["source_pack_hash_persisted"] is False
    assert summary["approved_at_persisted"] is False
    assert summary["raw_values_persisted"] is False
    assert summary["publication_allowed"] is False
    assert summary["dispatch_allowed_now"] is False
    assert summary["public_postable"] is False
