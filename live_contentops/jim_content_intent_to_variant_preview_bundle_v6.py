"""Jim Content Intent to Variant Preview Bundle V6.

Transforms Jim's local daily content run packet into deterministic content intent
and platform-preview placeholders. No final copy, no LLM/provider calls, no
network, browser, env, credential, public URL verification, dispatch, or live
platform action.
"""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from typing import Any

from live_contentops.jim_daily_content_run_packet_v6 import build_jim_daily_content_run_packet

TASK_LABEL = "TASK_0078_HEAVY_BATCH_CONTENT_INTENT_TO_PLATFORM_VARIANT_PREVIEW_BUNDLE_V0"
CONTRACT_VERSION = "jim_content_intent_to_variant_preview_bundle_v6.0"
PLATFORM_TARGETS = ("Substack", "X", "LinkedIn", "Telegram")

FORBIDDEN_TERMS = (
    "buy", "sell", "hold", "long", "short", "price target", "guaranteed",
    "will rally", "will crash", "financial advice", "signal",
)

PLATFORM_CONSTRAINTS = {
    "Substack": {
        "preview_shape": "newsletter_outline_placeholder",
        "constraints": ["needs Jim approval", "needs source confirmation", "not final public copy"],
    },
    "X": {
        "preview_shape": "thread_outline_placeholder",
        "constraints": ["short-form hook only", "no signal language", "not dispatchable"],
    },
    "LinkedIn": {
        "preview_shape": "professional_post_outline_placeholder",
        "constraints": ["context-first framing", "no advice claim", "not dispatchable"],
    },
    "Telegram": {
        "preview_shape": "channel_note_outline_placeholder",
        "constraints": ["manual export only", "no live send", "not dispatchable"],
    },
}

SAFETY_FLAGS = {
    "local_only": True,
    "fixture_only": True,
    "jim_final_review_required": True,
    "content_intent_created": True,
    "platform_preview_placeholders_created": True,
    "final_public_copy_created": False,
    "llm_provider_called": False,
    "provider_api_called": False,
    "network_called": False,
    "browser_or_cdp_used": False,
    "credential_or_env_read": False,
    "platform_api_called": False,
    "platform_dispatch_performed": False,
    "scheduler_enabled": False,
    "public_url_verified": False,
    "public_postable": False,
    "publish_ready": False,
    "dispatch_ready": False,
}


def _stable_hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _contains_forbidden(text: str) -> bool:
    normalized = " ".join(text.lower().split())
    return any(term in normalized for term in FORBIDDEN_TERMS)


def _intent_for_idea(idea: dict[str, Any]) -> dict[str, Any]:
    title = idea["title"]
    source_blocked = idea["lane"] == "B_grounded_news" and bool(idea.get("blockers"))
    artifact_blocked = idea["lane"] == "C_artifact_backed"
    blocked = idea["status"] == "BLOCKED" or source_blocked or artifact_blocked or _contains_forbidden(title)
    blockers = list(idea.get("blockers", []))
    if artifact_blocked and "approved artifact evidence required" not in blockers:
        blockers.append("approved artifact evidence required")
    if _contains_forbidden(title):
        blockers.append("forbidden market signal language detected")

    return {
        "intent_id": f"INTENT-{idea['idea_id']}",
        "source_idea_id": idea["idea_id"],
        "title": title,
        "content_lane": idea["lane"],
        "audience_mode": "operator_review",
        "draft_objective": "turn approved framing into bounded editorial preview only",
        "status": "BLOCKED" if blocked else "READY_FOR_JIM_REVIEW",
        "source_requirement": "approved artifact evidence" if artifact_blocked else ("official-source confirmation" if source_blocked else "operator review"),
        "claim_risk": "artifact_gate" if artifact_blocked else ("source_context_review" if source_blocked else "process_context_low_risk"),
        "forbidden_language_clear": not _contains_forbidden(title),
        "blockers": blockers,
        "next_manual_step": idea["next_allowed_manual_step"],
        "final_public_copy_created": False,
        "public_postable": False,
    }


def _preview_for_intent(intent: dict[str, Any], platform: str) -> dict[str, Any]:
    rules = PLATFORM_CONSTRAINTS[platform]
    blocked = intent["status"] == "BLOCKED"
    status = "BLOCKED_WAITING_FOR_INPUTS" if blocked else "PREVIEW_PLACEHOLDER_READY_FOR_JIM_REVIEW"
    missing_inputs = list(intent["blockers"])
    if not missing_inputs:
        missing_inputs = ["Jim final review"]

    text_excerpt = (
        f"[{platform} placeholder] {intent['title']} — framing only; "
        "no final public copy, no advice, no dispatch."
    )
    return {
        "preview_id": f"PV-{intent['source_idea_id']}-{platform.upper()}",
        "platform": platform,
        "source_intent_id": intent["intent_id"],
        "preview_shape": rules["preview_shape"],
        "preview_status": status,
        "preview_text_excerpt": text_excerpt,
        "constraints": list(rules["constraints"]),
        "missing_inputs": missing_inputs,
        "approval_preconditions": ["Jim final review", "exact payload approval", "manual export decision"],
        "manual_export_ready": False,
        "dispatch_ready": False,
        "public_postable": False,
    }


def build_jim_content_intent_to_variant_preview_bundle(
    daily_run_packet: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build deterministic intent + preview bundle from Jim's daily run packet."""
    source = deepcopy(daily_run_packet if daily_run_packet is not None else build_jim_daily_content_run_packet())
    intents = [_intent_for_idea(idea) for idea in source["ideas"]]
    previews = [
        _preview_for_intent(intent, platform)
        for intent in intents
        for platform in PLATFORM_TARGETS
    ]
    blocked_count = sum(1 for intent in intents if intent["status"] == "BLOCKED")
    packet = {
        "task_label": TASK_LABEL,
        "contract_version": CONTRACT_VERSION,
        "bundle_id": f"variant_preview_bundle_for_{source['run_id']}",
        "source_run_id": source["run_id"],
        "operator_id": source["operator_id"],
        "bundle_status": "JIM_REVIEW_REQUIRED_PREVIEW_ONLY",
        "content_intents": intents,
        "platform_targets": list(PLATFORM_TARGETS),
        "platform_previews": previews,
        "intent_count": len(intents),
        "platform_preview_count": len(previews),
        "blocked_intent_count": blocked_count,
        "manual_export_state": "not_ready_waiting_for_jim_review_and_exact_payload_approval",
        "next_allowed_action": "Jim may review content intent, missing inputs, and preview placeholders.",
        "forbidden_actions": [
            "No LLM/provider generation",
            "No final public copy",
            "No platform API",
            "No live dispatch",
            "No scheduler",
            "No public URL verification",
        ],
        "safety_flags": dict(SAFETY_FLAGS),
    }
    packet["packet_hash"] = _stable_hash(packet)
    packet["packet_hash_algorithm"] = "sha256"
    return packet


if __name__ == "__main__":
    print(json.dumps(build_jim_content_intent_to_variant_preview_bundle(), indent=2, sort_keys=True))
