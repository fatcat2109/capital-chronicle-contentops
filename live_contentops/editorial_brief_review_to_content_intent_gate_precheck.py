"""Editorial Brief Review to Content Intent Gate Precheck.

Part of TASK_CONTENTOPS_0175BJ_EDITORIAL_BRIEF_REVIEW_TO_CONTENT_INTENT_GATE_PRECHECK_V0.
Consumes the 0175BH Editorial Brief Review Packet shape and emits a Content Intent Gate Precheck packet
without copy generation, trading signals, or truth promotion.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Any

TASK_LABEL = "TASK_CONTENTOPS_0175BJ_EDITORIAL_BRIEF_REVIEW_TO_CONTENT_INTENT_GATE_PRECHECK_V0"
SOURCE_BASELINE_COMMIT = "b6006d21829f55d6a781169104debd2f39b1491e"
LEDGER_FAMILY = "editorial_brief_review_to_content_intent_gate_precheck_future"
HASH_ALGORITHM = "sha256"
DOC_REL_DIR = Path("docs") / "automation" / "0175BJ"
PACKET_FILENAME = "editorial_brief_review_to_content_intent_gate_precheck_packet.json"
RUNBOOK_FILENAME = "editorial_brief_review_to_content_intent_gate_precheck.md"

DISALLOWED_OUTPUTS = [
    "raw_record_contents",
    "source_extracted_facts",
    "market_values",
    "narrative_thesis",
    "headline",
    "hook",
    "caption",
    "draft_paragraph",
    "platform_copy",
    "prediction",
    "buy_sell_hold_sizing_signal_language"
]


def create_content_intent_gate_precheck(
    brief_packet: dict[str, Any],
    next_recommended_task: str | None = None
) -> dict[str, Any]:
    """Consumes the Editorial Brief Review Packet and produces a Content Intent Gate Precheck packet."""
    if not brief_packet or not isinstance(brief_packet, dict):
        raise ValueError("Brief packet is missing or malformed. Failing closed.")

    # Calculate deterministic hash of input brief packet
    serialized = json.dumps(brief_packet, sort_keys=True, separators=(",", ":"))
    source_editorial_brief_review_packet_hash = sha256(serialized.encode("utf-8")).hexdigest()

    source_packet_task_label = brief_packet.get("task_label", "unknown")
    source_candidate_count = brief_packet.get("candidate_count", 0)

    candidate_gate_items = []
    has_missing_metadata = False
    has_unsafe_flags = False

    for item in brief_packet.get("candidate_review_items", []):
        cid = item.get("candidate_id")
        rel_path = item.get("relative_path")
        role = item.get("evidence_role")
        family = item.get("source_family")
        records_count = item.get("records_count", 0)
        contract_name = item.get("contract_name")
        advisory_only = item.get("advisory_only", True)
        candidate_only = item.get("candidate_only", True)

        missing_requirements = []
        blocked_reasons = []

        # 1. Metadata check
        if not cid:
            missing_requirements.append("missing_candidate_id")
        if not rel_path:
            missing_requirements.append("missing_relative_path")
        if not role:
            missing_requirements.append("missing_evidence_role")
        if not family:
            missing_requirements.append("missing_source_family")

        # 2. Safety check
        is_unsafe = not advisory_only or not candidate_only

        if missing_requirements:
            status = "BLOCKED_MISSING_METADATA"
            blocked_reasons.append("candidate_metadata_requirements_incomplete")
            allowed_next = "provide_required_candidate_metadata_fields"
            has_missing_metadata = True
        elif is_unsafe:
            status = "BLOCKED_NOT_CANDIDATE_ONLY"
            blocked_reasons.append("candidate_must_be_advisory_and_candidate_only_for_compliance")
            allowed_next = "quarantine_candidate_and_inspect_compliance_bounds"
            has_unsafe_flags = True
        else:
            status = "READY_FOR_OPERATOR_INTENT_REVIEW"
            blocked_reasons.append("waiting_for_operator_intent_review")
            allowed_next = "operator_must_review_metadata_before_intent_drafting"

        gate_item = {
            "candidate_id": cid or "unknown_candidate",
            "relative_path": rel_path or "",
            "evidence_role": role or "unknown",
            "source_family": family or "unknown",
            "records_count": records_count,
            "contract_name": contract_name,
            "advisory_only": advisory_only,
            "candidate_only": candidate_only,
            "operator_review_required": True,
            "content_intent_gate_status": status,
            "blocked_reasons": blocked_reasons,
            "missing_requirements": missing_requirements,
            "allowed_next_step": allowed_next,
        }
        candidate_gate_items.append(gate_item)

    # Determine global precheck status
    if has_missing_metadata:
        global_status = "BLOCKED_MISSING_METADATA"
        global_blocked_reasons = ["metadata_requirements_incomplete_across_candidates"]
        global_allowed_next = "resolve_missing_metadata_fields_in_ingestion"
    elif has_unsafe_flags:
        global_status = "BLOCKED_NOT_CANDIDATE_ONLY"
        global_blocked_reasons = ["safety_invariants_violated_in_candidates"]
        global_allowed_next = "isolate_non_compliant_candidates_in_quarantine"
    else:
        global_status = "BLOCKED_OPERATOR_REVIEW_REQUIRED"
        global_blocked_reasons = [
            "operator_brief_review_pending",
            "content_intent_gate_locked_until_operator_review"
        ]
        global_allowed_next = "operator_must_sign_off_content_intent_gate_precheck_to_unlock_drafting"

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
        actual_next_task = "TASK_CONTENTOPS_0175BK_CONTENT_INTENT_GATE_PRECHECK_TO_V5_INTENT_QUEUE_BINDING_V0"

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
        "source_editorial_brief_review_packet_hash": source_editorial_brief_review_packet_hash,
        "source_packet_task_label": source_packet_task_label,
        "source_candidate_count": source_candidate_count,
        "candidate_gate_items": candidate_gate_items,
        "content_intent_gate_status": global_status,
        "operator_review_required": True,
        "blocked_reasons": global_blocked_reasons,
        "allowed_next_step": global_allowed_next,
        "disallowed_outputs": DISALLOWED_OUTPUTS,
        "truth_protection_flags": protected_truth_flags,
        "safety_flags": safety_flags,
        "next_recommended_task": actual_next_task,
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
    """Renders the markdown runbook for the Content Intent Gate Precheck packet."""
    items = packet["candidate_gate_items"]
    safety = packet["safety_flags"]
    truth = packet["truth_protection_flags"]

    lines = [
        "# Content Intent Gate Precheck",
        "",
        "> [!IMPORTANT]",
        "> This is a deterministic local-only Content Intent Gate Precheck.",
        "> It does not compile editorial drafts, headlines, hooks, captions, or platform copy.",
        "> All safety locks are active, and no platform/provider API integrations are initialized.",
        "",
        f"- **Task Label**: `{packet['task_label']}`",
        f"- **Source Editorial Brief Review Packet Hash**: `{packet['source_editorial_brief_review_packet_hash']}`",
        f"- **Source Packet Task Label**: `{packet['source_packet_task_label']}`",
        f"- **Packet Hash**: `{packet['packet_hash']}`",
        f"- **Content Intent Gate Status**: `{packet['content_intent_gate_status']}`",
        f"- **Ledger Family**: `{packet['ledger_family']}`",
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
        "## Candidate Gate Items (Metadata-Only)",
        "",
        "| Candidate ID | Path | Role | Family | Status | Allowed Next Step |",
        "|---|---|---|---|---|---|",
    ])

    for item in items:
        lines.append(
            f"| `{item['candidate_id']}` | `{item['relative_path']}` | `{item['evidence_role']}` | "
            f"`{item['source_family']}` | `{item['content_intent_gate_status']}` | `{item['allowed_next_step']}` |"
        )

    lines.extend([
        "",
        "## Disallowed Output Enforcement",
        "",
        "The following outputs are strictly forbidden from this precheck stage:",
        "",
    ])

    for out in packet["disallowed_outputs"]:
        lines.append(f"- `[FORBIDDEN]` {out}")

    lines.extend([
        "",
        "## Navigation",
        "",
        f"- **Next Recommended Task**: `{packet['next_recommended_task']}`",
    ])

    return "\n".join(lines) + "\n"


def write_artifacts(brief_review_packet_path: str | Path, repo_root: str | Path = ".") -> dict[str, Any]:
    """Generates and writes the JSON packet and Markdown runbook to the docs/automation/0175BJ/ directory."""
    root = Path(repo_root).resolve()
    out = (root / DOC_REL_DIR).resolve()
    out.mkdir(parents=True, exist_ok=True)

    with open(brief_review_packet_path, "r", encoding="utf-8") as f:
        brief_packet = json.load(f)

    packet = create_content_intent_gate_precheck(brief_packet)
    packet_path = out / PACKET_FILENAME
    runbook_path = out / RUNBOOK_FILENAME

    packet_path.write_text(json.dumps(packet, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    runbook_path.write_text(render_runbook(packet), encoding="utf-8", newline="\n")

    return {
        "packet": packet,
        "packet_path": str(packet_path),
        "runbook_path": str(runbook_path),
    }
