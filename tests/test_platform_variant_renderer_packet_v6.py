"""Test V6 Platform Variant Renderer Packet."""
from __future__ import annotations

from live_contentops import platform_variant_renderer_packet_v6 as packet_builder


def test_make_platform_variant_renderer_packet():
    packet = packet_builder.make_platform_variant_renderer_packet()

    assert packet["platform_variant_renderer_status"] == "PLATFORM_VARIANT_RENDERER_BLOCKED_WAITING_FOR_APPROVED_INPUTS"
    assert packet["runtime_truth"] is False
    assert packet["platform_variant_queue_loaded"] is True
    assert packet["platform_variant_input_contract_loaded"] is True
    assert packet["renderer_input_contract_created"] is True
    assert packet["approved_canonical_article_available"] is False
    assert packet["refined_draft_available"] is False
    assert packet["seo_metadata_available"] is False
    assert packet["platform_style_rules_available"] is False
    assert packet["destination_binding_completed"] is False
    assert packet["exact_payload_approval_completed"] is False
    assert packet["jim_review_completed"] is False
    assert packet["renderer_execution_allowed"] is False
    assert packet["renderer_execution_performed"] is False
    assert packet["platform_variant_generation_allowed"] is False
    assert packet["platform_variant_generation_performed"] is False
    assert packet["platform_copy_generated"] is False
    assert packet["substack_variant_generated"] is False
    assert packet["discord_variant_generated"] is False
    assert packet["telegram_variant_generated"] is False
    assert packet["x_variant_generated"] is False
    assert packet["linkedin_variant_generated"] is False
    assert packet["threads_variant_generated"] is False
    assert packet["platform_values_materialized"] is False
    assert packet["platform_payload_hash_created"] is False
    assert packet["approval_packet_created"] is False
    assert packet["allowed_for_publication"] is False
    assert packet["public_postable"] is False
    assert packet["dispatch_allowed_now"] is False
    assert packet["live_write_allowed_now"] is False
    assert packet["outbox_entry_created"] is False
    assert packet["provider_call_performed"] is False
    assert packet["browser_session_started"] is False
    assert packet["env_read_performed"] is False
    assert packet["credentials_hydrated"] is False
    assert packet["platform_api_request_performed"] is False
    assert packet["webhook_request_performed"] is False
    assert packet["human_review_required"] is True
    assert packet["kill_switch_active"] is True
