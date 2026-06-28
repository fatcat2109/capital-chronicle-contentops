"""Test V6 Canonical Article Studio Renderer Gate Packet."""
from __future__ import annotations

from live_contentops import canonical_article_studio_renderer_gate_packet_v6 as packet_builder


def test_make_canonical_article_studio_renderer_gate_packet():
    packet = packet_builder.make_canonical_article_studio_renderer_gate_packet()

    assert packet["renderer_gate_status"] == "SOURCE_APPROVED_RENDERER_BLOCKED_WAITING_FOR_REAL_APPROVAL"
    assert packet["runtime_truth"] is False
    assert packet["placeholder_binding_loaded"] is True
    assert packet["renderer_input_contract_created"] is True
    assert packet["real_source_pack_approved"] is False
    assert packet["real_operator_approval_created"] is False
    assert packet["jim_review_completed"] is False
    assert packet["source_approval_hash_present"] is False
    assert packet["renderer_execution_allowed"] is False
    assert packet["renderer_execution_performed"] is False
    assert packet["blocked_renderer_output_created"] is True
    assert packet["article_copy_generated"] is False
    assert packet["title_generated"] is False
    assert packet["dek_generated"] is False
    assert packet["body_generated"] is False
    assert packet["citations_generated"] is False
    assert packet["seo_metadata_generated"] is False
    assert packet["source_values_materialized"] is False
    assert packet["placeholder_values_materialized"] is False
    assert packet["canonical_draft_generation_allowed"] is False
    assert packet["allowed_for_publication"] is False
    assert packet["public_postable"] is False
    assert packet["dispatch_allowed_now"] is False
    assert packet["live_write_allowed_now"] is False
    assert packet["outbox_entry_created"] is False
    assert packet["provider_call_performed"] is False
    assert packet["browser_session_started"] is False
    assert packet["env_read_performed"] is False
    assert packet["credentials_hydrated"] is False
    assert packet["human_review_required"] is True
    assert packet["kill_switch_active"] is True
