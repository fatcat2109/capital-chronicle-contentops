"""Test V6 Canonical Article Studio Queue Packet."""
from __future__ import annotations

from live_contentops import canonical_article_studio_queue_packet_v6 as packet_builder


def test_make_canonical_article_studio_queue_packet():
    packet = packet_builder.make_canonical_article_studio_queue_packet()

    assert packet["queue_status"] == "REVIEW_QUEUE_READY_WITH_BLOCKERS"
    assert packet["runtime_truth"] is False
    assert packet["canonical_draft_eligibility_loaded"] is True
    assert packet["real_source_pack_approved"] is False
    assert packet["real_operator_approval_created"] is False
    assert packet["article_copy_generated"] is False
    assert packet["draft_markdown_created"] is False
    assert packet["article_studio_item_created"] is True
    assert packet["editor_review_required"] is True
    assert packet["jim_review_required"] is True
    assert packet["source_approval_required"] is True
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
