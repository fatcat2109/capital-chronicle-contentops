"""Test V6 Operator Source Pack Review Packet Generator."""
from __future__ import annotations

from live_contentops import operator_source_pack_review_packet_v6 as packet_builder


def test_make_operator_source_pack_review_packet():
    packet = packet_builder.make_operator_source_pack_review_packet()
    
    assert packet["review_status"] == "OPERATOR_SOURCE_PACK_REVIEW_REQUIRED"
    assert packet["runtime_truth"] is False
    assert packet["real_source_pack_imported"] is False
    assert packet["source_pack_approved_by_operator"] is False
    assert packet["source_pack_complete"] is False
    assert packet["all_required_sources_verified"] is False
    assert packet["all_claims_bound_to_sources"] is False
    assert packet["positive_path_test_passed"] is True
    assert packet["positive_path_runtime_truth"] is False
    assert packet["canonical_draft_generation_allowed"] is False
    assert packet["article_copy_generated_from_real_sources"] is False
    assert packet["allowed_for_publication"] is False
    assert packet["public_postable"] is False
    assert packet["dispatch_allowed_now"] is False
    assert packet["live_write_allowed_now"] is False
    assert packet["provider_call_performed"] is False
    assert packet["browser_session_started"] is False
    assert packet["env_read_performed"] is False
    assert packet["credentials_hydrated"] is False
    assert packet["human_review_required"] is True
    assert packet["kill_switch_active"] is True
