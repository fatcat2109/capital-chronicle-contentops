"""V6 Platform Variant Renderer Packet.

Defines renderer queue packet structure and default status flags.
"""
from __future__ import annotations

from typing import Any


def make_platform_variant_renderer_packet() -> dict[str, Any]:
    """Generates the default platform variant renderer packet."""
    return {
        "platform_variant_renderer_status": "PLATFORM_VARIANT_RENDERER_BLOCKED_WAITING_FOR_APPROVED_INPUTS",
        "runtime_truth": False,
        "platform_variant_queue_loaded": True,
        "platform_variant_input_contract_loaded": True,
        "renderer_input_contract_created": True,
        "approved_canonical_article_available": False,
        "refined_draft_available": False,
        "seo_metadata_available": False,
        "platform_style_rules_available": False,
        "destination_binding_completed": False,
        "exact_payload_approval_completed": False,
        "jim_review_completed": False,
        "renderer_execution_allowed": False,
        "renderer_execution_performed": False,
        "platform_variant_generation_allowed": False,
        "platform_variant_generation_performed": False,
        "platform_copy_generated": False,
        "substack_variant_generated": False,
        "discord_variant_generated": False,
        "telegram_variant_generated": False,
        "x_variant_generated": False,
        "linkedin_variant_generated": False,
        "threads_variant_generated": False,
        "platform_values_materialized": False,
        "platform_payload_hash_created": False,
        "approval_packet_created": False,
        "allowed_for_publication": False,
        "public_postable": False,
        "dispatch_allowed_now": False,
        "live_write_allowed_now": False,
        "outbox_entry_created": False,
        "provider_call_performed": False,
        "browser_session_started": False,
        "env_read_performed": False,
        "credentials_hydrated": False,
        "platform_api_request_performed": False,
        "webhook_request_performed": False,
        "human_review_required": True,
        "kill_switch_active": True
    }
