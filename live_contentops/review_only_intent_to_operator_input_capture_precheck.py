"""Review-Only Content Intent to Operator Input Capture Precheck.

Part of TASK_CONTENTOPS_0175BN_REVIEW_ONLY_INTENT_TO_OPERATOR_INPUT_CAPTURE_PRECHECK_V0.
Consumes the Review-Only Content Intent Packet and produces an Operator Input Capture Precheck packet.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Any

TASK_LABEL = "TASK_CONTENTOPS_0175BN_REVIEW_ONLY_INTENT_TO_OPERATOR_INPUT_CAPTURE_PRECHECK_V0"
SOURCE_BASELINE_COMMIT = "ce6d5d11f2a629b64d5be2d7e8cd158badf5929d"
LEDGER_FAMILY = "review_only_intent_to_operator_input_capture_precheck_future"
HASH_ALGORITHM = "sha256"
DOC_REL_DIR = Path("docs") / "automation" / "0175BN"
PACKET_FILENAME = "review_only_intent_to_operator_input_capture_precheck_packet.json"
RUNBOOK_FILENAME = "review_only_intent_to_operator_input_capture_precheck.md"

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
    "recommendation",
    "buy_sell_hold_sizing_signal_language"
]

REQUIRED_INPUT_FIELDS = [
    "intended_audience_lane",
    "content_purpose_category",
    "source_review_notes",
    "risk_review_notes",
    "claim_scope_boundary",
    "manual_operator_decision"
]


def create_operator_input_capture_precheck(
    intent_packet: dict[str, Any],
    next_recommended_task: str | None = None
) -> dict[str, Any]:
    """Transition intent packet to an Operator Input Capture Precheck packet."""
    if not intent_packet or not isinstance(intent_packet, dict):
        raise ValueError("Intent packet is missing or malformed. Failing closed.")

    global_intent_status = intent_packet.get("global_intent_packet_status")
    allowed_statuses = {"BLOCKED_OPERATOR_INTENT_INPUT_REQUIRED"}
    if global_intent_status not in allowed_statuses:
        raise ValueError(f"Invalid global intent packet status '{global_intent_status}'. Failing closed.")

    serialized = json.dumps(intent_packet, sort_keys=True, separators=(",", ":"))
    source_review_only_intent_packet_hash = sha256(serialized.encode("utf-8")).hexdigest()

    source_packet_task_label = intent_packet.get("task_label", "unknown")
    source_intent_items = intent_packet.get("review_only_intent_items", [])
    source_intent_item_count = len(source_intent_items)

    # Scaffolding default field policy
    field_policy = {}
    for field in REQUIRED_INPUT_FIELDS:
        field_policy[field] = {
            "required": True,
            "value_status": "PENDING_OPERATOR_INPUT",
            "capture_enabled": False,
            "editable_in_this_task": False,
            "generated_by_system": False,
            "stored_value": "PENDING_OPERATOR_INPUT",
            "operator_must_provide_later": True
        }

    input_capture_precheck_items = []
    for item in source_intent_items:
        iid = item.get("intent_item_id", "unknown_intent_item")
        cid = item.get("source_candidate_id", "unknown_candidate")
        rel_path = item.get("relative_path", "")
        role = item.get("evidence_role", "unknown")
        family = item.get("source_family", "unknown")
        records_count = item.get("records_count", 0)
        contract_name = item.get("contract_name")
        scope_label = item.get("intent_scope_label", "unknown_metadata_review")
        intent_status = item.get("review_only_intent_status", "unknown")

        if intent_status == "REVIEW_ONLY_INTENT_PENDING_OPERATOR_INPUT":
            item_status = "OPERATOR_INPUT_CAPTURE_PRECHECK_PENDING"
        elif intent_status.startswith("BLOCKED"):
            item_status = "BLOCKED_BY_REVIEW_ONLY_INTENT_PACKET"
        else:
            item_status = "BLOCKED_BY_REVIEW_ONLY_INTENT_PACKET"

        precheck_item = {
            "intent_item_id": iid,
            "source_candidate_id": cid,
            "relative_path": rel_path,
            "evidence_role": role,
            "source_family": family,
            "records_count": records_count,
            "contract_name": contract_name,
            "intent_scope_label": scope_label,
            "source_gate_status": intent_status,
            "operator_input_capture_precheck_status": item_status,
            "operator_review_required": True,
            "required_input_fields": REQUIRED_INPUT_FIELDS.copy(),
            "field_policy": field_policy.copy(),
            "blocked_reasons": list(item.get("blocked_reasons", [])),
            "missing_requirements": list(item.get("missing_requirements", [])),
            "allowed_next_step": "operator_must_provide_inputs_to_enable_capture",
            "disallowed_outputs": DISALLOWED_OUTPUTS.copy()
        }
        input_capture_precheck_items.append(precheck_item)

    # Protect truth flags
    protected_truth_flags = {
        "dqr_cleared_by_contentops": False,
        "readiness_cleared_by_contentops": False,
        "current_truth_promoted": False,
        "numeric_truth_promoted": False,
        "market_data_promoted": False
    }

    # Safety flags
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
        actual_next_task = "TASK_CONTENTOPS_0175BO_OPERATOR_INPUT_CAPTURE_PRECHECK_TO_V5_READONLY_INPUT_PANEL_BINDING_V0"

    raw_packet = {
        "task_label": TASK_LABEL,
        "source_review_only_intent_packet_hash": source_review_only_intent_packet_hash,
        "source_packet_task_label": source_packet_task_label,
        "source_intent_item_count": source_intent_item_count,
        "global_operator_input_capture_status": "BLOCKED_OPERATOR_INPUT_CAPTURE_NOT_ENABLED",
        "input_capture_precheck_items": input_capture_precheck_items,
        "required_input_fields": REQUIRED_INPUT_FIELDS.copy(),
        "field_policy": field_policy,
        "validation_rules": [
            "all_required_fields_must_be_provided",
            "no_empty_notes_allowed",
            "operator_decision_must_be_approved"
        ],
        "blocked_reasons": ["operator_input_capture_not_enabled", "input_capture_gated_until_operator_action"],
        "allowed_next_step": "operator_must_enable_input_capture_in_later_supervised_task",
        "disallowed_outputs": DISALLOWED_OUTPUTS.copy(),
        "truth_protection_flags": protected_truth_flags,
        "safety_flags": safety_flags,
        "next_recommended_task": actual_next_task,
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
    """Renders the markdown runbook for the Operator Input Capture Precheck Packet."""
    items = packet["input_capture_precheck_items"]
    safety = packet["safety_flags"]
    truth = packet["truth_protection_flags"]

    lines = [
        "# Operator Input Capture Precheck",
        "",
        "> [!IMPORTANT]",
        "> This is a deterministic local-only Operator Input Capture Precheck Packet.",
        "> It does not compile headlines, hooks, drafts, platform copy, or predictions.",
        "> All safety locks are active, and no platform/provider API integrations are initialized.",
        "",
        f"- **Task Label**: `{packet['task_label']}`",
        f"- **Source Intent Packet Hash**: `{packet['source_review_only_intent_packet_hash']}`",
        f"- **Source Packet Task Label**: `{packet['source_packet_task_label']}`",
        f"- **Packet Hash**: `{packet['packet_hash']}`",
        f"- **Global Operator Input Capture Status**: `{packet['global_operator_input_capture_status']}`",
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
        "## Required Input Fields Policy Summary",
        "",
        "| Field | Required | Status | Capture Enabled | Editable | Stored Value |",
        "|---|---|---|---|---|---|",
    ])

    for f, policy in packet["field_policy"].items():
        lines.append(
            f"| `{f}` | `{policy['required']}` | `{policy['value_status']}` | `{policy['capture_enabled']}` | "
            f"`{policy['editable_in_this_task']}` | `{policy['stored_value']}` |"
        )

    lines.extend([
        "",
        "## Input Capture Precheck Items",
        "",
        "| Intent Item ID | Candidate ID | Status | Scope Label | Allowed Next Step |",
        "|---|---|---|---|---|",
    ])

    for item in items:
        lines.append(
            f"| `{item['intent_item_id']}` | `{item['source_candidate_id']}` | `{item['operator_input_capture_precheck_status']}` | "
            f"`{item['intent_scope_label']}` | `{item['allowed_next_step']}` |"
        )

    lines.extend([
        "",
        "## Disallowed Output Enforcement",
        "",
        "The following outputs are strictly forbidden from this intent staging phase:",
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


def write_artifacts(intent_packet_path: str | Path, repo_root: str | Path = ".") -> dict[str, Any]:
    """Generates and writes the JSON packet and Markdown runbook to docs/automation/0175BN/."""
    root = Path(repo_root).resolve()
    out = (root / DOC_REL_DIR).resolve()
    out.mkdir(parents=True, exist_ok=True)

    with open(intent_packet_path, "r", encoding="utf-8") as f:
        intent_packet = json.load(f)

    packet = create_operator_input_capture_precheck(intent_packet)
    packet_path = out / PACKET_FILENAME
    runbook_path = out / RUNBOOK_FILENAME

    packet_path.write_text(json.dumps(packet, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    runbook_path.write_text(render_runbook(packet), encoding="utf-8", newline="\n")

    return {
        "packet": packet,
        "packet_path": str(packet_path),
        "runbook_path": str(runbook_path),
    }
