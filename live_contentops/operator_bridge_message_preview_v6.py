"""V6 Operator Bridge Message Previews.

Formats Discord and Telegram operator preview payloads and enforces strict safety filters.
"""
from __future__ import annotations

from typing import Any


def validate_preview_content(text: str) -> list[str]:
    """Scans message preview text for forbidden secrets, tokens, or executable commands."""
    blockers = []
    
    forbidden_substrings = [
        "discord.com/api/webhooks",
        "api.telegram.org/bot",
        "webhook URL",
        "bot token",
        "chat ID",
        "channel ID",
        "Authorization/Bearer",
        "cookie",
        "session",
        "localStorage",
        "sessionStorage",
        "public_postable=true",
        "dispatch_allowed_now=true",
        "live_write_allowed_now=true",
        "approval_valid_for_dispatch=true"
    ]
    
    for fs in forbidden_substrings:
        if fs in text:
            blockers.append("secret_or_destination_material_detected")
            
    # Check for executable looking triggers
    executable_patterns = ["/send", "/post", "/dispatch", "!publish"]
    for p in executable_patterns:
        if p in text.lower():
            blockers.append("executable_dispatch_control_detected")
            
    # Check for live claims
    if "live_write_allowed_now" in text or "dispatch_allowed_now" in text:
        blockers.append("unexpected_live_status_claim")
        
    return list(set(blockers))


def generate_discord_preview(
    redacted_status: dict[str, Any]
) -> dict[str, Any]:
    """Generates the review-only Discord message preview template."""
    title = "ContentOps V6 Operator Status"
    h = redacted_status.get("unified_payload_bundle_hash", "unhashed")
    short_hash = h[:8] if h != "unhashed" else "unhashed"
    
    # Pre-format preview text
    text_lines = [
        f"**{title}**",
        "**[REVIEW-ONLY PREVIEW - PUBLICATION BLOCKED]**",
        f"**Payload Hash**: `{short_hash}` (Full: `{h}`)",
        f"**Platform Families**: {', '.join(redacted_status.get('platform_families', []))}",
        f"**Status**: {redacted_status.get('unified_payload_status')}",
        "**Source Verification Warning**: Source verification is missing. Publication is blocked.",
        "**Approval Required Warning**: Jim must manually sign and review before dispatch.",
        "**Manual Fallback Instructions**: Copy generated variant payload files from `docs/automation/` and publish manually if needed.",
        "**Active Blockers**:"
    ]
    for b in redacted_status.get("blockers", []):
        text_lines.append(f"- `{b}`")
        
    preview_body = "\n".join(text_lines)
    
    return {
        "title": title,
        "content_body": preview_body,
        "review_only": True,
        "raw_text_length": len(preview_body)
    }


def generate_telegram_preview(
    redacted_status: dict[str, Any]
) -> dict[str, Any]:
    """Generates the review-only Telegram message preview template."""
    h = redacted_status.get("unified_payload_bundle_hash", "unhashed")
    
    text_lines = [
        "*ContentOps V6 Operator Status*",
        "*[REVIEW-ONLY PREVIEW - PUBLICATION BLOCKED]*",
        f"Payload Hash: `{h}`",
        f"Draft Status: {redacted_status.get('draft_inspector_status')}",
        "Source Verification Required: TRUE",
        "Approval Not Valid for Dispatch: TRUE",
        "Kill Switch Active: TRUE",
        "Top Blockers:",
    ]
    # Display top 3 blockers
    for b in redacted_status.get("blockers", [])[:3]:
        text_lines.append(f"- `{b}`")
        
    text_lines.extend([
        "Manual Fallback Instructions: Copy variant JSON payloads and perform manual operator post.",
        "Review-Only Label: Pending Verification."
    ])
    
    preview_body = "\n".join(text_lines)
    
    return {
        "content_body": preview_body,
        "review_only": True,
        "raw_text_length": len(preview_body)
    }
