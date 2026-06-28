"""Test V6 Canonical Article Studio Draft Shell Packet."""
from __future__ import annotations

from live_contentops import canonical_article_studio_draft_shell_packet_v6 as packet_builder


def test_make_canonical_article_studio_draft_shell_packet():
    packet = packet_builder.make_canonical_article_studio_draft_shell_packet()

    assert packet["shell_status"] == "BROWSERLESS_EDITOR_SHELL_READY_WITH_BLOCKERS"
    assert packet["runtime_truth"] is False
    assert packet["source_review_queue_loaded"] is True
    assert packet["review_item_status"] == "BLOCKED_WAITING_FOR_REAL_SOURCE_APPROVAL"
    assert packet["shell_instance_created"] is True
    assert packet["article_copy_generated"] is False
    assert packet["article_body_generated"] is False
    assert packet["title_generated"] is False
    assert packet["dek_generated"] is False
    assert packet["citations_generated"] is False
    assert packet["seo_metadata_generated"] is False
    assert packet["source_pack_approved"] is False
    assert packet["jim_review_completed"] is False
    assert packet["ready_for_editor_review"] is False
    assert packet["ready_for_jim_approval"] is False
    assert packet["ready_for_publication"] is False
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
