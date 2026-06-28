"""V6 Platform Variant Constraint Registry.

Provides constraints, limits, and safety properties for all supported platform families.
"""
from __future__ import annotations

from typing import Any

PLATFORM_FAMILIES = [
    "substack_canonical",
    "discord_drop",
    "telegram_operator_post",
    "x_manual_thread",
    "linkedin_manual_post",
    "threads_manual_post",
    "facebook_manual_post",
    "instagram_manual_caption",
    "manual_fallback_export"
]

CONSTRAINTS = {
    "substack_canonical": {
        "platform_family": "substack_canonical",
        "generation_mode": "manual_fallback_export",
        "live_api_supported_now": False,
        "dispatch_supported_now": False,
        "public_postable": False,
        "account_binding_required_before_live": True,
        "approval_required": True,
        "exact_payload_hash_required": True,
        "max_text_length": 100000,
        "supports_threading": False,
        "supports_continuation_comment": False,
        "media_policy_status": "supported_image_embeds",
        "manual_fallback_available": True,
        "official_docs_required_before_live": True
    },
    "discord_drop": {
        "platform_family": "discord_drop",
        "generation_mode": "webhook_dispatch_restricted",
        "live_api_supported_now": False,
        "dispatch_supported_now": False,
        "public_postable": False,
        "account_binding_required_before_live": True,
        "approval_required": True,
        "exact_payload_hash_required": True,
        "max_text_length": 2000,
        "supports_threading": False,
        "supports_continuation_comment": False,
        "media_policy_status": "supported_embeds",
        "manual_fallback_available": True,
        "official_docs_required_before_live": True
    },
    "telegram_operator_post": {
        "platform_family": "telegram_operator_post",
        "generation_mode": "operator_approval_restricted",
        "live_api_supported_now": False,
        "dispatch_supported_now": False,
        "public_postable": False,
        "account_binding_required_before_live": True,
        "approval_required": True,
        "exact_payload_hash_required": True,
        "max_text_length": 4096,
        "supports_threading": False,
        "supports_continuation_comment": False,
        "media_policy_status": "supported_link_preview",
        "manual_fallback_available": True,
        "official_docs_required_before_live": True
    },
    "x_manual_thread": {
        "platform_family": "x_manual_thread",
        "generation_mode": "manual_fallback_export",
        "live_api_supported_now": False,
        "dispatch_supported_now": False,
        "public_postable": False,
        "account_binding_required_before_live": True,
        "approval_required": True,
        "exact_payload_hash_required": True,
        "max_text_length": 280,
        "supports_threading": True,
        "supports_continuation_comment": False,
        "media_policy_status": "none_restricted",
        "manual_fallback_available": True,
        "official_docs_required_before_live": True
    },
    "linkedin_manual_post": {
        "platform_family": "linkedin_manual_post",
        "generation_mode": "manual_fallback_export",
        "live_api_supported_now": False,
        "dispatch_supported_now": False,
        "public_postable": False,
        "account_binding_required_before_live": True,
        "approval_required": True,
        "exact_payload_hash_required": True,
        "max_text_length": 3000,
        "supports_threading": False,
        "supports_continuation_comment": True,
        "media_policy_status": "optional_link",
        "manual_fallback_available": True,
        "official_docs_required_before_live": True
    },
    "threads_manual_post": {
        "platform_family": "threads_manual_post",
        "generation_mode": "manual_fallback_export",
        "live_api_supported_now": False,
        "dispatch_supported_now": False,
        "public_postable": False,
        "account_binding_required_before_live": True,
        "approval_required": True,
        "exact_payload_hash_required": True,
        "max_text_length": 500,
        "supports_threading": True,
        "supports_continuation_comment": False,
        "media_policy_status": "supported_link",
        "manual_fallback_available": True,
        "official_docs_required_before_live": True
    },
    "facebook_manual_post": {
        "platform_family": "facebook_manual_post",
        "generation_mode": "manual_fallback_export",
        "live_api_supported_now": False,
        "dispatch_supported_now": False,
        "public_postable": False,
        "account_binding_required_before_live": True,
        "approval_required": True,
        "exact_payload_hash_required": True,
        "max_text_length": 5000,
        "supports_threading": False,
        "supports_continuation_comment": True,
        "media_policy_status": "supported_embed",
        "manual_fallback_available": True,
        "official_docs_required_before_live": True
    },
    "instagram_manual_caption": {
        "platform_family": "instagram_manual_caption",
        "generation_mode": "manual_fallback_export",
        "live_api_supported_now": False,
        "dispatch_supported_now": False,
        "public_postable": False,
        "account_binding_required_before_live": True,
        "approval_required": True,
        "exact_payload_hash_required": True,
        "max_text_length": 2200,
        "supports_threading": False,
        "supports_continuation_comment": True,
        "media_policy_status": "required_image",
        "manual_fallback_available": True,
        "official_docs_required_before_live": True
    },
    "manual_fallback_export": {
        "platform_family": "manual_fallback_export",
        "generation_mode": "manual_fallback_export",
        "live_api_supported_now": False,
        "dispatch_supported_now": False,
        "public_postable": False,
        "account_binding_required_before_live": True,
        "approval_required": True,
        "exact_payload_hash_required": True,
        "max_text_length": 10000,
        "supports_threading": True,
        "supports_continuation_comment": True,
        "media_policy_status": "any_media",
        "manual_fallback_available": True,
        "official_docs_required_before_live": True
    }
}


def get_constraints(platform_family: str) -> dict[str, Any]:
    """Retrieves standard safety constraints for a platform family."""
    if platform_family not in PLATFORM_FAMILIES:
        raise KeyError(f"Platform family {platform_family} is not registered in V6 constraints.")
    return CONSTRAINTS[platform_family]
