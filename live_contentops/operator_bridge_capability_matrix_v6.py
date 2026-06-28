"""V6 Operator Bridge Capability Matrix.

Defines operational bridge capabilities across platform families.
"""
from __future__ import annotations

from typing import Any


def generate_capability_matrix() -> list[dict[str, Any]]:
    """Creates the V6 capability matrix mapping live publishing boundaries."""
    platforms = [
        "discord_webhook",
        "telegram_bot_api",
        "substack_browser_compose",
        "x_manual_thread",
        "linkedin_manual_post",
        "manual_fallback_export"
    ]
    
    matrix = []
    for p in platforms:
        is_live_capable = p in ["discord_webhook", "telegram_bot_api", "substack_browser_compose"]
        matrix.append({
            "platform_family": p,
            "capability_mode": "discord_telegram_bridge" if "discord" in p or "telegram" in p else "editorial_publish_compose",
            "live_enabled": False,
            "credential_required": f"{p}_auth" if is_live_capable else "none",
            "credential_present": "unknown_not_checked",
            "official_docs_required_before_live": True if is_live_capable else False,
            "account_binding_required_before_live": True,
            "approval_hash_required": True,
            "outbox_required": True,
            "audit_required": True,
            "manual_fallback_available": True,
            "current_result": "review_only_preview"
        })
        
    return matrix
