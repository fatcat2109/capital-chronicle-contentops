"""Local-only bridge from CC artifact intake draft to rehearsal intent."""
from __future__ import annotations

from typing import Any


def build_rehearsal_intent(internal_draft: dict[str, Any]) -> dict[str, Any]:
    """Create a non-executable rehearsal intent from a rendered internal draft."""
    return {
        "bridge_kind": "cc_artifact_packet_to_contentops_rehearsal_intent_v0",
        "bridge_status": "LOCAL_REHEARSAL_INTENT_READY_INTERNAL_REVIEW_ONLY",
        "packet_id": internal_draft["packet_id"],
        "approval_hash": internal_draft["approval_hash"],
        "topic": internal_draft["topic"],
        "headline_or_catalyst": internal_draft["headline_or_catalyst"],
        "article_angle": internal_draft["article_angle"],
        "accepted_for_internal_draft": True,
        "accepted_for_rehearsal_payload_render": True,
        "public_ready": False,
        "dispatch_allowed_now": False,
        "live_platform_api_called": False,
        "public_write_performed": False,
        "credential_lookup_performed": False,
        "network_call_performed": False,
        "runner_invocation_performed": False,
        "runner_invocation_allowed": False,
        "manual_review_required": True,
        "dqr_blocked_public_gate": True,
        "next_gate": "Separate operator decision and future approved packet/public-candidate task required.",
        "blocked_actions": [
            "public_dispatch",
            "platform_api_call",
            "scheduler_enqueue",
            "retry_enqueue",
            "browser_or_cdp_readback",
            "source_fetch",
            "macro_source_parse",
            "main_repo_mutation",
        ],
        "statement": (
            "Packet accepted for internal draft/rehearsal intent only. DQR BLOCKED "
            "means public-ready remains false unless a future approved schema and gates change."
        ),
    }
