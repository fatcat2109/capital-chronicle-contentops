"""Lifecycle Intake Bridge to Editorial Brief Review Packet.

Part of TASK_CONTENTOPS_0175BH_LIFECYCLE_INTAKE_BRIDGE_TO_EDITORIAL_BRIEF_REVIEW_PACKET_V0.
This module transitions candidate artifact metadata into a deterministic Editorial Brief Review Packet
without copy generation, trading signals, or truth promotion.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Any

TASK_LABEL = "TASK_CONTENTOPS_0175BH_LIFECYCLE_INTAKE_BRIDGE_TO_EDITORIAL_BRIEF_REVIEW_PACKET_V0"
MATRIX_VERSION = "0175BH_LIFECYCLE_INTAKE_BRIDGE_TO_EDITORIAL_BRIEF_REVIEW_PACKET_V1"
SOURCE_BASELINE_COMMIT = "23e0573c062b63c939040143cfe66830bbfa9c2a"
LEDGER_FAMILY = "lifecycle_intake_bridge_to_editorial_brief_review_packet_future"
HASH_ALGORITHM = "sha256"
DOC_REL_DIR = Path("docs") / "automation" / "0175BH"
PACKET_FILENAME = "lifecycle_intake_bridge_to_editorial_brief_review_packet.json"
RUNBOOK_FILENAME = "lifecycle_intake_bridge_to_editorial_brief_review_packet.md"


def create_editorial_brief_review_packet(
    bridge_packet: dict[str, Any],
    next_recommended_task: str | None = None
) -> dict[str, Any]:
    """Consumes the 0175BG bridge packet shape and produces an editorial brief review packet."""
    if not bridge_packet or not isinstance(bridge_packet, dict):
        raise ValueError("Bridge packet is missing or malformed. Failing closed.")

    required_keys = ["artifacts_scanned_count", "artifact_candidates_count", "artifact_candidate_summaries"]
    for key in required_keys:
        if key not in bridge_packet:
            raise ValueError(f"Bridge packet missing required key '{key}'. Failing closed.")

    # Calculate deterministic hash of input bridge packet
    serialized = json.dumps(bridge_packet, sort_keys=True, separators=(",", ":"))
    source_bridge_packet_hash = sha256(serialized.encode("utf-8")).hexdigest()

    # Map candidate summaries to metadata-only review items
    candidate_review_items = []
    for c in bridge_packet.get("artifact_candidate_summaries", []):
        rel_path = c.get("relative_path", "")
        # Derive a clean candidate_id from path
        candidate_id = Path(rel_path).stem if rel_path else "unknown_candidate"

        # Construct metadata-only review item with strictly allowed fields
        item = {
            "candidate_id": candidate_id,
            "relative_path": rel_path,
            "evidence_role": c.get("evidence_role", "unknown"),
            "source_family": c.get("source_family", "unknown"),
            "records_count": c.get("records_count", 0),
            "contract_name": c.get("contract_name"),
            "advisory_only": c.get("advisory_only", True),
            "candidate_only": c.get("candidate_only", True),
            "operator_review_required": True,
            "blocked_reasons": ["waiting_for_operator_brief_review"],
            "allowed_next_step": "operator_must_inspect_source_artifact_before_brief_generation",
        }
        candidate_review_items.append(item)

    topic_families = sorted(list({item["source_family"] for item in candidate_review_items if item["source_family"]}))
    evidence_roles = sorted(list({item["evidence_role"] for item in candidate_review_items if item["evidence_role"]}))

    required_operator_review_checklist = [
        "Confirm ingestion repository path matches local system",
        "Verify candidates scanned count matches expected count",
        "Ensure all candidate metadata fields are loaded without error",
        "Confirm no public draft copy or market predictions are generated",
        "Inspect source family classification before transitioning to content intent stage"
    ]

    blocked_reasons = ["operator_brief_review_pending", "content_intent_gate_locked_until_operator_review"]

    # Strict protected truth flags (Never promote to truth)
    protected_truth_flags = {
        "dqr_cleared_by_contentops": False,
        "readiness_cleared_by_contentops": False,
        "current_truth_promoted": False,
        "numeric_truth_promoted": False,
        "market_data_promoted": False
    }

    # Strict safety flags (Confirm no live calls or leakages)
    safety_flags = {
        "live_api_called": False,
        "provider_api_called": False,
        "platform_api_called": False,
        "credential_hydrated": False,
        "secret_values_observed": False,
        "env_secret_read": False,
        "scheduler_enabled": False,
        "scraping_performed": False,
        "dispatch_ready": False,
        "public_postable": False
    }

    actual_next_task = next_recommended_task
    if not actual_next_task:
        actual_next_task = bridge_packet.get("next_recommended_task")
    if not actual_next_task:
        actual_next_task = "TASK_CONTENTOPS_0175BI_EDITORIAL_BRIEF_REVIEW_PACKET_TO_V5_BRIEF_QUEUE_BINDING_V0"

    # Multi-stage overlays for integration
    lifecycle_overlays = {
        "artifact_or_brief_intake": {
            "state": "PENDING",
            "operator_action_required": True
        },
        "content_intent": {
            "state": "BLOCKED",
            "operator_action_required": True
        }
    }

    raw_packet = {
        "task_label": TASK_LABEL,
        "source_bridge_task_label": bridge_packet.get("task_label", "unknown"),
        "source_bridge_packet_hash": source_bridge_packet_hash,
        "contentops_source_head": SOURCE_BASELINE_COMMIT,
        "ingestion_repo_path_checked": bridge_packet.get("ingestion_repo_path_checked"),
        "ingestion_repo_branch": bridge_packet.get("ingestion_repo_branch"),
        "ingestion_repo_head": bridge_packet.get("ingestion_repo_head"),
        "ingestion_repo_status": bridge_packet.get("ingestion_repo_status"),
        "candidate_count": len(candidate_review_items),
        "candidate_review_items": candidate_review_items,
        "topic_families": topic_families,
        "evidence_roles": evidence_roles,
        "required_operator_review_checklist": required_operator_review_checklist,
        "blocked_reasons": blocked_reasons,
        "protected_truth_flags": protected_truth_flags,
        "safety_flags": safety_flags,
        "next_recommended_task": actual_next_task,
        # Maintain compat lifecycle overlay fields
        "lifecycle_overlay": {
            "affected_stage_id": "artifact_or_brief_intake",
            "stage_state_after_overlay": "PENDING" if len(candidate_review_items) > 0 else "BLOCKED",
            "operator_review_required": True,
            "downstream_dispatch_ready": False,
            "public_postable": False
        },
        "lifecycle_overlays": lifecycle_overlays,
        "ledger_family": LEDGER_FAMILY,
        "hash_algorithm": HASH_ALGORITHM
    }

    # Deterministic self hash
    packet_serialized = json.dumps(raw_packet, sort_keys=True, separators=(",", ":"))
    packet_hash = sha256(packet_serialized.encode("utf-8")).hexdigest()

    return {
        "packet_hash": packet_hash,
        **raw_packet
    }


def render_runbook(packet: dict[str, Any]) -> str:
    """Renders the markdown runbook for the editorial brief review packet."""
    items = packet["candidate_review_items"]
    checklist = packet["required_operator_review_checklist"]
    safety = packet["safety_flags"]
    truth = packet["protected_truth_flags"]

    lines = [
        "# Editorial Brief Review Packet",
        "",
        "> [!IMPORTANT]",
        "> This is a deterministic local-only Editorial Brief Review Packet.",
        "> It does not compile editorial thesis statements, publishable copy, or public drafts.",
        "> All safety locks are active, and no platform/provider API integrations are initialized.",
        "",
        f"- **Task Label**: `{packet['task_label']}`",
        f"- **Source Bridge Task Label**: `{packet['source_bridge_task_label']}`",
        f"- **Source Bridge Packet Hash**: `{packet['source_bridge_packet_hash']}`",
        f"- **ContentOps Source Head**: `{packet['contentops_source_head']}`",
        f"- **Packet Hash**: `{packet['packet_hash']}`",
        f"- **Ledger Family**: `{packet['ledger_family']}`",
        "",
        "## Ingestion Status",
        "",
        f"- **Ingestion Repo Path Checked**: `{packet['ingestion_repo_path_checked']}`",
        f"- **Ingestion Repo HEAD**: `{packet['ingestion_repo_head']}`",
        f"- **Ingestion Repo Branch**: `{packet['ingestion_repo_branch']}`",
        f"- **Ingestion Repo Status**: `{packet['ingestion_repo_status']}`",
        f"- **Scanned Candidate Count**: `{packet['candidate_count']}`",
        "",
        "## Invariant Validation Safety Flags",
        "",
        "| Safety Lock | State | Status |",
        "|---|---|---|",
    ]

    for k, v in safety.items():
        lines.append(f"| `{k}` | `{v}` | {'✅' if not v else '❌'} |")

    lines.extend([
        "",
        "## Truth Protection Status",
        "",
        "| Truth Flag | State | Status |",
        "|---|---|---|",
    ])

    for k, v in truth.items():
        lines.append(f"| `{k}` | `{v}` | {'✅' if not v else '❌'} |")

    lines.extend([
        "",
        "## Topic Families and Evidence Roles",
        "",
        f"- **Topic Families Detected**: {', '.join(packet['topic_families']) or 'none'}",
        f"- **Evidence Roles Detected**: {', '.join(packet['evidence_roles']) or 'none'}",
        "",
        "## Candidate Review Items (Metadata-Only)",
        "",
        "| Candidate ID | Relative Path | Role | Family | Records | Next Step |",
        "|---|---|---|---|---|---|",
    ])

    for item in items:
        lines.append(
            f"| `{item['candidate_id']}` | `{item['relative_path']}` | `{item['evidence_role']}` | "
            f"`{item['source_family']}` | `{item['records_count']}` | `{item['allowed_next_step']}` |"
        )

    lines.extend([
        "",
        "## Required Operator Review Checklist",
        "",
    ])

    for step in checklist:
        lines.append(f"- [ ] {step}")

    lines.extend([
        "",
        "## Navigation",
        "",
        f"- **Next Recommended Task**: `{packet['next_recommended_task']}`",
    ])

    return "\n".join(lines) + "\n"


def write_artifacts(bridge_packet_path: str | Path, repo_root: str | Path = ".") -> dict[str, Any]:
    """Generates and writes the JSON packet and Markdown runbook to the docs/automation/0175BH/ directory."""
    root = Path(repo_root).resolve()
    out = (root / DOC_REL_DIR).resolve()
    out.mkdir(parents=True, exist_ok=True)

    with open(bridge_packet_path, "r", encoding="utf-8") as f:
        bridge_packet = json.load(f)

    packet = create_editorial_brief_review_packet(bridge_packet)
    packet_path = out / PACKET_FILENAME
    runbook_path = out / RUNBOOK_FILENAME

    packet_path.write_text(json.dumps(packet, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    runbook_path.write_text(render_runbook(packet), encoding="utf-8", newline="\n")

    return {
        "packet": packet,
        "packet_path": str(packet_path),
        "runbook_path": str(runbook_path),
    }
