"""V6 Redacted Operator Status.

Provides redacted status packets for Discord and Telegram status bridges, stripping sensitive info.
"""
from __future__ import annotations

from typing import Any


def generate_redacted_status(
    contract_packet: dict[str, Any]
) -> dict[str, Any]:
    """Builds operator status report without sensitive webhooks or credentials."""
    # Retrieve details from unified contract
    app_readiness = contract_packet.get("approval_readiness", {})
    if not app_readiness:
        # Fallback if nested structure is flat or loaded from sibling report
        app_readiness = contract_packet.get("approval_capture", {})
        
    blockers = contract_packet.get("draft_inspector", {}).get("blockers", [])
    # Also add standard blockers
    blockers.extend([
        "destination_binding_incomplete",
        "kill_switch_active",
        "live_write_authorization_missing",
        "operator_approval_incomplete",
        "operator_signature_missing",
        "outbox_creation_blocked",
        "safety_review_incomplete"
    ])
    blockers = sorted(list(set(blockers)))
    
    variant_pack = contract_packet.get("variant_pack", {})
    platform_families = sorted(list(variant_pack.keys()))
    
    return {
        "unified_payload_status": "READY_FOR_REVIEW_ONLY_HASHED_PAYLOADS",
        "unified_payload_bundle_hash": contract_packet.get("hash_manifest", {}).get("unified_payload_bundle_hash", "unhashed"),
        "per_platform_payload_count": len(platform_families),
        "platform_families": platform_families,
        "draft_inspector_status": contract_packet.get("draft_inspector", {}).get("draft_inspector_status", "BLOCKED_REVIEW_ONLY_ISSUES_FOUND"),
        "source_verification_required": True,
        "publication_allowed": False,
        "approval_valid_for_dispatch": False,
        "operator_signature_valid": False,
        "destination_binding_complete": False,
        "outbox_dispatchable": False,
        "dispatch_allowed_now": False,
        "kill_switch_active": True,
        "blocker_count": len(blockers),
        "blockers": blockers,
        "next_recommended_task": "TASK_CONTENTOPS_V6_SUBSTACK_BROWSER_COMPOSE_DRY_RUN_AND_BROWSER_SAFETY_QA_HEAVY_BATCH_V0",
        "redaction_policy": "NO_SECRET_VALUES_NO_IDS_NO_URLS"
    }
