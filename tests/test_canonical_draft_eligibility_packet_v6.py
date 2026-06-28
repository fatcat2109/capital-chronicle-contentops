"""Test V6 Canonical Draft Eligibility Packet."""
from __future__ import annotations

from live_contentops import canonical_draft_eligibility_packet_v6 as packet_builder


def test_make_canonical_draft_eligibility_packet():
    packet = packet_builder.make_canonical_draft_eligibility_packet()

    assert packet["eligibility_status"] == "TEST_ONLY_APPROVAL_SIMULATION_REVIEW"
    assert packet["runtime_truth"] is False
    assert packet["real_source_pack_approved"] is False
    assert packet["test_only_approval_simulation"] is True
    assert packet["redacted_source_pack_available"] is True
    assert packet["redacted_claim_bindings_available"] is True
    assert packet["approval_gate_passed_for_runtime"] is False
    assert packet["approval_gate_passed_for_test_only"] is True
    assert packet["canonical_draft_generation_allowed_for_runtime"] is False
    assert packet["canonical_draft_generation_allowed_for_test_only"] is True
    assert packet["article_copy_generated"] is False
    assert packet["draft_markdown_created"] is False
    assert packet["public_postable"] is False
    assert packet["allowed_for_publication"] is False
    assert packet["dispatch_allowed_now"] is False
    assert packet["live_write_allowed_now"] is False
    assert packet["outbox_entry_created"] is False
    assert packet["provider_call_performed"] is False
    assert packet["browser_session_started"] is False
    assert packet["env_read_performed"] is False
    assert packet["credentials_hydrated"] is False
    assert packet["human_review_required"] is True
    assert packet["kill_switch_active"] is True
