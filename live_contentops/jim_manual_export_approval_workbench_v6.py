"""Jim Manual Export + Approval Packet Workbench V6.

Builds Jim's local-only handoff from variant preview placeholders into
manual export packets and approval record previews. No final public copy,
network, browser/CDP, env, credential, platform API, scheduler, public URL
verification, or live dispatch.
"""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from typing import Any

from live_contentops.jim_content_intent_to_variant_preview_bundle_v6 import (
    build_jim_content_intent_to_variant_preview_bundle,
)

TASK_LABEL = "TASK_0079_HEAVY_BATCH_MANUAL_EXPORT_APPROVAL_PACKET_WORKBENCH_V0"
CONTRACT_VERSION = "jim_manual_export_approval_workbench_v6.0"
EXPORT_PLATFORMS = ("Substack", "X", "LinkedIn", "Telegram")
EXPORT_STATUS_READY = "READY_FOR_MANUAL_COPY_AFTER_JIM_APPROVAL"
EXPORT_STATUS_BLOCKED = "BLOCKED_WAITING_FOR_INPUTS"
APPROVAL_STATUS = "APPROVAL_RECORD_PREVIEW_ONLY_NOT_VALID_FOR_DISPATCH"

SAFETY_FALSE_FLAGS = (
    "final_public_copy_created",
    "llm_provider_called",
    "provider_api_called",
    "network_called",
    "browser_or_cdp_used",
    "credential_or_env_read",
    "platform_api_called",
    "platform_dispatch_performed",
    "scheduler_enabled",
    "public_url_verified",
    "public_postable",
    "publish_ready",
    "dispatch_ready",
    "approval_valid_for_dispatch",
)

MANUAL_EXPORT_CHECKLIST = (
    "Review source intent and blockers",
    "Review placeholder preview text",
    "Confirm missing inputs are resolved by Jim",
    "Copy export markdown manually only after Jim approval",
    "Do not paste into live platform from repo automation",
    "Do not verify or fetch public URL",
    "Keep dispatch/live write locked",
)

FORBIDDEN_PHRASES = (
    "publish-ready",
    "dispatch-ready",
    "ready for dispatch",
    "ready for publish",
    "public url verified",
)
SIGNAL_WORDS = {"buy", "sell", "hold", "long", "short"}


def _json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _stable_hash(data: Any) -> str:
    return hashlib.sha256(_json(data).encode("utf-8")).hexdigest()


def _tokens(text: str) -> set[str]:
    return {"".join(ch for ch in word.lower() if ch.isalnum()) for word in text.split()}


def _contains_forbidden(text: str) -> bool:
    normalized = " ".join(text.lower().split())
    return bool(SIGNAL_WORDS & _tokens(normalized)) or any(phrase in normalized for phrase in FORBIDDEN_PHRASES)


def _safety_flags() -> dict[str, bool]:
    return {flag: False for flag in SAFETY_FALSE_FLAGS} | {
        "local_only": True,
        "manual_export_only": True,
        "jim_final_approval_required": True,
        "approval_record_preview_created": True,
    }


def render_manual_export_markdown(intent: dict[str, Any], preview: dict[str, Any]) -> str:
    """Render bounded markdown handoff. It is not final public copy."""
    lines = [
        f"# Manual export placeholder: {intent['title']}",
        "",
        "## Operator scope",
        "Jim review only. This packet is local manual-export prep, not final public copy.",
        "",
        "## Platform placeholder",
        f"Platform: {preview['platform']}",
        f"Preview shape: {preview['preview_shape']}",
        "",
        "## Preview excerpt",
        preview["preview_text_excerpt"],
        "",
        "## Missing inputs",
        *(f"- {item}" for item in preview["missing_inputs"]),
        "",
        "## Approval preconditions",
        *(f"- {item}" for item in preview["approval_preconditions"]),
        "",
        "## Manual export checklist",
        *(f"- {item}" for item in MANUAL_EXPORT_CHECKLIST),
        "",
        "## Locked actions",
        "- No final public copy created",
        "- No platform API",
        "- No live dispatch",
        "- No scheduler",
        "- No public URL verification",
        "",
    ]
    return "\n".join(lines)


def _export_packet(intent: dict[str, Any], preview: dict[str, Any]) -> dict[str, Any]:
    markdown = render_manual_export_markdown(intent, preview)
    blocked = preview["preview_status"] == "BLOCKED_WAITING_FOR_INPUTS" or _contains_forbidden(markdown)
    blockers = list(dict.fromkeys(preview["missing_inputs"] if blocked else ["Jim final approval required"]))
    packet = {
        "export_packet_id": f"MANUAL-EXPORT-{preview['preview_id']}",
        "source_intent_id": intent["intent_id"],
        "source_preview_id": preview["preview_id"],
        "platform": preview["platform"],
        "title": intent["title"],
        "manual_export_status": EXPORT_STATUS_BLOCKED if blocked else EXPORT_STATUS_READY,
        "markdown_body": markdown,
        "manual_export_checklist": list(MANUAL_EXPORT_CHECKLIST),
        "missing_inputs": list(preview["missing_inputs"]),
        "blocked_reasons": blockers,
        "requires_jim_final_approval": True,
        "manual_copy_allowed_after_approval": not blocked,
        "final_public_copy_created": False,
        "public_postable": False,
        "dispatch_ready": False,
        "public_url_verified": False,
        "safety_flags": _safety_flags(),
    }
    packet["markdown_hash"] = _stable_hash(markdown)
    packet["export_hash"] = _stable_hash({k: v for k, v in packet.items() if k not in {"markdown_hash", "export_hash"}})
    return packet


def _approval_record(export: dict[str, Any]) -> dict[str, Any]:
    record = {
        "approval_record_id": f"APPROVAL-PREVIEW-{export['export_packet_id']}",
        "source_export_packet_id": export["export_packet_id"],
        "source_export_hash": export["export_hash"],
        "operator_id": "Jim",
        "approval_channel": "local_ui_read_only_preview",
        "approval_status": APPROVAL_STATUS,
        "approval_text_redacted": "Jim approval required before manual copy; no secrets captured.",
        "valid_for_dispatch": False,
        "public_postable": False,
        "dispatch_ready": False,
        "blocked_reasons": ["approval_record_preview_only", "dispatch_revalidation_not_built"],
        "safety_flags": _safety_flags(),
    }
    record["approval_record_hash"] = _stable_hash(record)
    return record


def build_jim_manual_export_approval_workbench(
    variant_bundle: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build deterministic manual export workbench from variant preview bundle."""
    source = deepcopy(variant_bundle if variant_bundle is not None else build_jim_content_intent_to_variant_preview_bundle())
    intents = {intent["intent_id"]: intent for intent in source["content_intents"]}
    exports = [
        _export_packet(intents[preview["source_intent_id"]], preview)
        for preview in source["platform_previews"]
        if preview["platform"] in EXPORT_PLATFORMS
    ]
    approvals = [_approval_record(export) for export in exports]
    ready_count = sum(1 for export in exports if export["manual_export_status"] == EXPORT_STATUS_READY)
    blocked_count = len(exports) - ready_count
    workbench = {
        "task_label": TASK_LABEL,
        "contract_version": CONTRACT_VERSION,
        "workbench_id": f"manual_export_workbench_for_{source['bundle_id']}",
        "source_bundle_id": source["bundle_id"],
        "operator_id": source["operator_id"],
        "workbench_status": "JIM_APPROVAL_REQUIRED_MANUAL_EXPORT_ONLY",
        "export_packet_count": len(exports),
        "ready_export_packet_count": ready_count,
        "blocked_export_packet_count": blocked_count,
        "approval_record_preview_count": len(approvals),
        "manual_export_packets": exports,
        "approval_record_previews": approvals,
        "operator_next_action": "Jim reviews export packets and records approval outside any live dispatch path.",
        "forbidden_actions": [
            "No final public copy",
            "No platform API",
            "No live dispatch",
            "No scheduler",
            "No public URL verification",
            "No browser/CDP",
        ],
        "safety_flags": _safety_flags(),
    }
    workbench["workbench_hash"] = _stable_hash(workbench)
    workbench["workbench_hash_algorithm"] = "sha256"
    return workbench


if __name__ == "__main__":
    print(_json(build_jim_manual_export_approval_workbench()))
