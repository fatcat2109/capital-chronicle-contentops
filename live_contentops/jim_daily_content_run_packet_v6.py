"""Jim Daily Content Run packet V6.

Local-only deterministic packet for Jim's next operator run. No provider calls,
network, browser, env reads, URL verification, dispatch, or live platform action.
"""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from typing import Any

TASK_LABEL = "TASK_0077_HEAVY_BATCH_JIM_DAILY_CONTENT_RUN_PACKET_AND_V5_PANEL_V0"
CONTRACT_VERSION = "jim_daily_content_run_v6.0"
OPERATOR_ID = "jim"

FORBIDDEN_ACTIONS = [
    "No provider API",
    "No platform dispatch",
    "No browser/CDP action",
    "No credential/env read",
    "No scheduler",
    "No public URL verification",
]

SAFETY_FLAGS = {
    "local_only": True,
    "fixture_only": True,
    "jim_final_review_required": True,
    "manual_export_only": True,
    "public_postable": False,
    "publish_ready": False,
    "dispatch_ready": False,
    "provider_api_called": False,
    "network_called": False,
    "browser_or_cdp_used": False,
    "credential_or_env_read": False,
    "platform_dispatch_performed": False,
    "scheduler_enabled": False,
    "public_url_verified": False,
}

DEFAULT_IDEAS = [
    {
        "idea_id": "JDR-PA-001",
        "title": "Why no forecast can be the correct output",
        "lane": "A_pre_alpha",
        "source_type": "operator_process_note",
        "status": "REVIEW_REQUIRED",
        "allowed_transformations": ["outline", "draft", "platform preview"],
        "forbidden_transformations": ["market call", "forecast authority claim"],
        "blockers": [],
        "next_allowed_manual_step": "Jim may review process framing and request a bounded draft.",
    },
    {
        "idea_id": "JDR-GN-001",
        "title": "CPI print as context, not a signal",
        "lane": "B_grounded_news",
        "source_type": "grounded_news_brief",
        "status": "REVIEW_REQUIRED",
        "allowed_transformations": ["source checklist", "educational angle", "platform preview"],
        "forbidden_transformations": ["buy/sell/hold", "target levels", "watchlist call"],
        "blockers": ["official-source citation must be confirmed by Jim"],
        "next_allowed_manual_step": "Jim may confirm source refs before any copy is drafted.",
    },
    {
        "idea_id": "JDR-CA-001",
        "title": "Artifact-backed macro brief",
        "lane": "C_artifact_backed",
        "source_type": "future_artifact_context",
        "status": "BLOCKED",
        "allowed_transformations": [],
        "forbidden_transformations": ["draft generation", "platform preview", "public-postable claim"],
        "blockers": ["Lane C blocked without approved artifact evidence"],
        "next_allowed_manual_step": "Attach approved artifact evidence before drafting.",
    },
]


def _stable_hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def build_jim_daily_content_run_packet(
    *,
    run_id: str = "jim_daily_run_0077_sample",
    ideas: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build Jim's local daily content run packet.

    The packet is intentionally not publish-ready. It is a review map for Jim:
    lane, blockers, next safe manual step, and hard forbidden actions.
    """
    items = deepcopy(ideas if ideas is not None else DEFAULT_IDEAS)
    lane_counts = {"A_pre_alpha": 0, "B_grounded_news": 0, "C_artifact_backed": 0}
    for item in items:
        lane_counts[item["lane"]] = lane_counts.get(item["lane"], 0) + 1
        if item["lane"] == "C_artifact_backed" and not item.get("blockers"):
            item["blockers"] = ["Lane C blocked without approved artifact evidence"]
            item["status"] = "BLOCKED"

    packet = {
        "task_label": TASK_LABEL,
        "contract_version": CONTRACT_VERSION,
        "run_id": run_id,
        "operator_id": OPERATOR_ID,
        "run_status": "JIM_FINAL_REVIEW_REQUIRED",
        "surface_label": "Jim Daily Content Run",
        "operator_summary": "Jim final review required; review-only daily run packet.",
        "lane_counts": lane_counts,
        "ideas": items,
        "platform_preview_targets": ["Substack", "X", "LinkedIn", "Telegram"],
        "manual_export_state": "manual_export_not_prepared",
        "next_allowed_action": "Jim may review lane classification and source blockers.",
        "forbidden_actions": list(FORBIDDEN_ACTIONS),
        "safety_flags": dict(SAFETY_FLAGS),
    }
    packet["packet_hash"] = _stable_hash(packet)
    packet["packet_hash_algorithm"] = "sha256"
    return packet


if __name__ == "__main__":
    print(json.dumps(build_jim_daily_content_run_packet(), indent=2, sort_keys=True))
