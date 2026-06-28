"""Test V6 Canonical Article Studio Placeholder Binding Packet."""
from __future__ import annotations

from live_contentops import canonical_article_studio_placeholder_binding_packet_v6 as packet_builder


def test_make_canonical_article_studio_placeholder_binding_packet():
    packet = packet_builder.make_canonical_article_studio_placeholder_binding_packet()

    assert packet["binding_status"] == "PLACEHOLDER_BINDING_READY_WITH_BLOCKERS"
    assert packet["runtime_truth"] is False
    assert packet["draft_shell_loaded"] is True
    assert packet["slot_schema_loaded"] is True
    assert packet["placeholder_binding_created"] is True
    assert packet["placeholder_binding_review_only"] is True
    assert packet["approved_placeholder_binding_for_runtime"] is False
    assert packet["source_pack_approved"] is False
    assert packet["jim_review_completed"] is False
    assert packet["article_copy_generated"] is False
    assert packet["title_generated"] is False
    assert packet["dek_generated"] is False
    assert packet["body_generated"] is False
    assert packet["citations_generated"] is False
    assert packet["seo_metadata_generated"] is False
    assert packet["slot_values_materialized"] is False
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
