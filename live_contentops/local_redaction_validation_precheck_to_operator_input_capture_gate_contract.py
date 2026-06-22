"""Local Redaction and Validation Precheck to Operator Input Capture Gate Contract.

Part of TASK_CONTENTOPS_0175BX_LOCAL_REDACTION_VALIDATION_PRECHECK_TO_OPERATOR_INPUT_CAPTURE_GATE_CONTRACT_V0.
Consumes the 0175BW Local Redaction and Validation Precheck packet and produces a local-only,
Operator Input Capture Gate Contract packet.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Any

TASK_LABEL = "TASK_CONTENTOPS_0175BX_LOCAL_REDACTION_VALIDATION_PRECHECK_TO_OPERATOR_INPUT_CAPTURE_GATE_CONTRACT_V0"
LEDGER_FAMILY = "local_redaction_validation_precheck_to_operator_input_capture_gate_contract_future"
HASH_ALGORITHM = "sha256"
DOC_REL_DIR = Path("docs") / "automation" / "0175BX"
PACKET_FILENAME = "local_redaction_validation_precheck_to_operator_input_capture_gate_contract_packet.json"
RUNBOOK_FILENAME = "local_redaction_validation_precheck_to_operator_input_capture_gate_contract.md"
NEXT_RECOMMENDED_TASK = "TASK_CONTENTOPS_0175BY_OPERATOR_INPUT_CAPTURE_GATE_TO_SUPERVISED_MANUAL_INPUT_DRY_RUN_PRECHECK_V0"

REQUIRED_INPUT_FIELDS = [
    "intended_audience_lane",
    "content_purpose_category",
    "source_review_notes",
    "risk_review_notes",
    "claim_scope_boundary",
    "manual_operator_decision",
]

ALLOWED_FUTURE_CAPTURE_MODES = [
    "supervised_manual_operator_entry",
    "imported_operator_review_packet",
    "deferred_human_review_session",
]

FORBIDDEN_CURRENT_ACTIONS = [
    "actual_input_capture",
    "editable_input_fields",
    "form_submission",
    "save_capture_approve_generate_controls",
    "operator_value_persistence",
    "evidence_capture",
    "validation_execution",
    "redaction_execution",
    "operator_prose_generation",
    "content_generation",
    "draft_generation",
    "headline_hook_caption_generation",
    "platform_copy_generation",
    "ai_writer_generation",
    "draft_storage",
    "public_posting",
    "live_dispatch",
    "provider_or_platform_api_call",
    "draft_eligibility_recheck",
]

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
    "buy_sell_hold_sizing_signal_language",
    "operator_input_value",
    "operator_review_notes_text",
    "captured_operator_value",
    "redacted_operator_value",
]

TRUTH_PROTECTION_FLAGS = {
    "dqr_cleared_by_contentops": False,
    "readiness_cleared_by_contentops": False,
    "current_truth_promoted": False,
    "numeric_truth_promoted": False,
    "market_data_promoted": False,
    "draft_truth_promoted": False,
    "operator_input_truth_promoted": False,
    "redacted_value_truth_promoted": False,
    "captured_value_truth_promoted": False,
}

SAFETY_FLAGS = {
    "live_api_called": False,
    "provider_api_called": False,
    "platform_api_called": False,
    "credential_hydrated": False,
    "secret_values_observed": False,
    "env_secret_read": False,
    "scheduler_enabled": False,
    "scraping_performed": False,
    "dispatch_ready": False,
    "public_postable": False,
    "actual_operator_input_capture_enabled": False,
    "editable_ui_enabled": False,
    "persistence_enabled": False,
    "draft_generation_enabled": False,
    "ai_writer_generation_enabled": False,
    "validation_enabled": False,
    "redaction_execution_enabled": False,
    "draft_eligibility_recheck_enabled": False,
    "operator_input_capture_gate_enabled": False,
    "evidence_capture_enabled": False,
}


def _source_packet_hash(packet: dict[str, Any]) -> str:
    packet_hash = packet.get("packet_hash")
    if isinstance(packet_hash, str) and packet_hash:
        return packet_hash
    serialized = json.dumps(packet, sort_keys=True, separators=(",", ":"))
    return sha256(serialized.encode("utf-8")).hexdigest()


def _capture_field_contract() -> dict[str, dict[str, Any]]:
    return {
        field: {
            "capture_allowed_in_future": True,
            "capture_enabled_in_this_task": False,
            "current_value": None,
            "current_value_present": False,
            "placeholder_value": "PENDING_OPERATOR_INPUT",
            "operator_generated_required": True,
            "system_generated_forbidden": True,
            "evidence_attachment_required": True,
            "redaction_precheck_required": True,
            "validation_precheck_required": True,
            "persistence_enabled_in_this_task": False,
            "capture_status": "BLOCKED_PENDING_SUPERVISED_ACTIVATION",
            "blocking_reason": "operator_input_capture_gate_not_enabled_in_this_task",
        }
        for field in REQUIRED_INPUT_FIELDS
    }


def _capture_evidence_contract() -> dict[str, bool]:
    return {
        "operator_identity_or_session_ref_required": True,
        "timestamp_required": True,
        "source_packet_hash_required": True,
        "manual_review_notes_required": True,
        "redaction_check_required": True,
        "validation_check_required": True,
        "no_secret_values_allowed": True,
        "no_raw_vendor_redistribution_allowed": True,
        "no_unverified_market_values_allowed": True,
        "no_financial_signal_language_allowed": True,
        "evidence_capture_enabled_in_this_task": False,
    }


def _pre_capture_validation_contract() -> dict[str, bool | str]:
    return {
        "field_non_empty_validation_required": True,
        "operator_generated_validation_required": True,
        "system_generated_rejection_required": True,
        "evidence_attachment_validation_required": True,
        "redaction_scan_required_before_acceptance": True,
        "validation_execution_enabled_in_this_task": False,
        "redaction_execution_enabled_in_this_task": False,
        "pass_status": "BLOCKED_PENDING_OPERATOR_CAPTURE",
    }


def _redaction_validation_dependency_contract() -> dict[str, bool | str]:
    return {
        "depends_on_local_redaction_validation_precheck": True,
        "source_global_status_required": "BLOCKED_LOCAL_REDACTION_VALIDATION_PRECHECK_PENDING_OPERATOR_VALUES",
        "source_operator_values_required_before_execution": True,
        "can_execute_without_operator_values": False,
        "dependency_satisfied_in_this_task": False,
    }


def _capture_execution_policy() -> dict[str, bool]:
    return {
        "input_capture_enabled": False,
        "editable_ui_enabled": False,
        "form_submission_enabled": False,
        "operator_value_persistence_enabled": False,
        "evidence_capture_enabled": False,
        "validation_execution_enabled": False,
        "redaction_execution_enabled": False,
        "draft_eligibility_recheck_enabled": False,
        "draft_generation_enabled": False,
        "ai_writer_generation_enabled": False,
        "public_postable": False,
        "dispatch_ready": False,
    }


def _draft_generation_policy() -> dict[str, bool]:
    return {
        "draft_generation_enabled": False,
        "headline_generation_enabled": False,
        "hook_generation_enabled": False,
        "caption_generation_enabled": False,
        "platform_copy_generation_enabled": False,
        "ai_writer_generation_enabled": False,
        "public_postable": False,
        "dispatch_ready": False,
        "draft_storage_enabled": False,
        "operator_input_capture_enabled": False,
        "validation_enabled": False,
        "supervised_input_resolution_enabled": False,
    }


def _map_item_status(source_status: str) -> str:
    if source_status == "BLOCKED_LOCAL_REDACTION_VALIDATION_PRECHECK_PENDING_OPERATOR_VALUES":
        return "BLOCKED_OPERATOR_INPUT_CAPTURE_GATE_PENDING_SUPERVISED_ACTIVATION"
    if source_status.startswith("BLOCKED"):
        return "BLOCKED_BY_LOCAL_REDACTION_VALIDATION_PRECHECK"
    return "BLOCKED_BY_LOCAL_REDACTION_VALIDATION_PRECHECK"


def create_operator_input_capture_gate_contract(
    local_redaction_validation_precheck_packet: dict[str, Any],
    next_recommended_task: str | None = None,
) -> dict[str, Any]:
    """Transition local redaction validation precheck packet into an Operator Input Capture Gate Contract packet."""
    if not local_redaction_validation_precheck_packet or not isinstance(local_redaction_validation_precheck_packet, dict):
        raise ValueError("Local redaction validation precheck packet is missing or malformed. Failing closed.")

    global_status = local_redaction_validation_precheck_packet.get("global_redaction_validation_precheck_status")
    if global_status != "BLOCKED_LOCAL_REDACTION_VALIDATION_PRECHECK_PENDING_OPERATOR_VALUES":
        raise ValueError(f"Invalid global precheck status '{global_status}'. Failing closed.")

    source_items = local_redaction_validation_precheck_packet.get("redaction_validation_precheck_items", [])
    if not isinstance(source_items, list):
        raise ValueError("redaction_validation_precheck_items must be a list. Failing closed.")

    operator_input_capture_gate_items = []
    blocked_reasons = [
        "operator_input_capture_gate_not_enabled_in_this_task",
        "missing_required_operator_inputs",
        "redaction_validation_dependency_prechecks_pending",
    ]

    cap_field_contract = _capture_field_contract()
    cap_evidence_contract = _capture_evidence_contract()
    pre_cap_val_contract = _pre_capture_validation_contract()
    red_val_dep_contract = _redaction_validation_dependency_contract()
    cap_exec_policy = _capture_execution_policy()

    for index, item in enumerate(source_items, start=1):
        source_status = item.get("redaction_validation_precheck_status", "")
        source_candidate_id = item.get("source_candidate_id", "unknown_candidate")
        
        gate_item = {
            "capture_gate_item_id": f"capture_gate_item_{index:02d}_{source_candidate_id}",
            "source_precheck_item_id": item.get("precheck_item_id", "unknown_item_id"),
            "source_candidate_id": source_candidate_id,
            "relative_path": item.get("relative_path", ""),
            "evidence_role": item.get("evidence_role", "unknown"),
            "source_family": item.get("source_family", "unknown"),
            "records_count": item.get("records_count", 0),
            "contract_name": item.get("contract_name"),
            "intent_scope_label": item.get("intent_scope_label", "unknown_metadata_review"),
            "source_redaction_validation_precheck_status": source_status,
            "operator_input_capture_gate_status": _map_item_status(source_status),
            "required_input_fields": REQUIRED_INPUT_FIELDS.copy(),
            "missing_required_input_fields": REQUIRED_INPUT_FIELDS.copy(),
            "capture_field_contract": cap_field_contract.copy(),
            "capture_evidence_contract": cap_evidence_contract.copy(),
            "pre_capture_validation_contract": pre_cap_val_contract.copy(),
            "redaction_validation_dependency_contract": red_val_dep_contract.copy(),
            "capture_execution_policy": cap_exec_policy.copy(),
            "blocked_reasons": blocked_reasons.copy(),
            "allowed_next_step": "stage_operator_input_capture_gate_to_supervised_manual_input_dry_run_precheck",
            "forbidden_current_actions": FORBIDDEN_CURRENT_ACTIONS.copy(),
            "disallowed_outputs": DISALLOWED_OUTPUTS.copy(),
        }
        operator_input_capture_gate_items.append(gate_item)

    actual_next_task = next_recommended_task or NEXT_RECOMMENDED_TASK
    raw_packet = {
        "task_label": TASK_LABEL,
        "source_local_redaction_validation_precheck_packet_hash": _source_packet_hash(local_redaction_validation_precheck_packet),
        "source_packet_task_label": local_redaction_validation_precheck_packet.get("task_label", "unknown"),
        "source_redaction_validation_precheck_item_count": len(source_items),
        "global_operator_input_capture_gate_status": "BLOCKED_OPERATOR_INPUT_CAPTURE_GATE_PENDING_SUPERVISED_ACTIVATION",
        "required_input_fields": REQUIRED_INPUT_FIELDS.copy(),
        "missing_required_input_fields": REQUIRED_INPUT_FIELDS.copy(),
        "operator_input_capture_gate_items": operator_input_capture_gate_items,
        "capture_field_contract": cap_field_contract,
        "capture_evidence_contract": cap_evidence_contract,
        "pre_capture_validation_contract": pre_cap_val_contract,
        "redaction_validation_dependency_contract": red_val_dep_contract,
        "allowed_future_capture_modes": ALLOWED_FUTURE_CAPTURE_MODES.copy(),
        "blocked_reasons": blocked_reasons.copy(),
        "allowed_next_step": "stage_operator_input_capture_gate_to_supervised_manual_input_dry_run_precheck",
        "forbidden_current_actions": FORBIDDEN_CURRENT_ACTIONS.copy(),
        "disallowed_outputs": DISALLOWED_OUTPUTS.copy(),
        "truth_protection_flags": TRUTH_PROTECTION_FLAGS.copy(),
        "safety_flags": SAFETY_FLAGS.copy(),
        "draft_generation_policy": _draft_generation_policy(),
        "capture_execution_policy": cap_exec_policy.copy(),
        "next_recommended_task": actual_next_task,
        "ledger_family": LEDGER_FAMILY,
        "hash_algorithm": HASH_ALGORITHM,
    }

    packet_serialized = json.dumps(raw_packet, sort_keys=True, separators=(",", ":"))
    packet_hash = sha256(packet_serialized.encode("utf-8")).hexdigest()
    return {"packet_hash": packet_hash, **raw_packet}


def render_runbook(packet: dict[str, Any]) -> str:
    """Render deterministic markdown runbook for the operator input capture gate contract."""
    lines = [
        "# Operator Input Capture Gate Contract",
        "",
        "> [!IMPORTANT]",
        "> This is a deterministic local gate contract defining capture, evidence, and validation dependency parameters for a future supervised operator input capture task. Actual capture execution, persistence, and draft generation remain disabled.",
        "",
        f"- **Task Label**: `{packet['task_label']}`",
        f"- **Source Local Redaction and Validation Precheck Packet Hash**: `{packet['source_local_redaction_validation_precheck_packet_hash']}`",
        f"- **Source Packet Task Label**: `{packet['source_packet_task_label']}`",
        f"- **Packet Hash**: `{packet['packet_hash']}`",
        f"- **Global Operator Input Capture Gate Status**: `{packet['global_operator_input_capture_gate_status']}`",
        f"- **Source Redaction Validation Precheck Item Count**: `{packet['source_redaction_validation_precheck_item_count']}`",
        f"- **Operator Input Capture Gate Item Count**: `{len(packet['operator_input_capture_gate_items'])}`",
        f"- **Ledger Family**: `{packet['ledger_family']}`",
        "",
        "## Required Input Fields",
        "",
    ]
    for field in packet["required_input_fields"]:
        lines.append(f"- `{field}`")

    lines.extend([
        "",
        "## Missing Required Input Fields",
        "",
    ])
    for field in packet["missing_required_input_fields"]:
        lines.append(f"- `{field}`")

    lines.extend([
        "",
        "## Capture Field Contract",
        "",
        "| Field | Capture Allowed in Future | Capture Enabled Now | Current Value Present | Placeholder | Operator Gen Required | System Gen Forbidden | Evidence Attachment Required | Persistence Enabled | Capture Status |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ])
    for field, contract in packet["capture_field_contract"].items():
        lines.append(
            f"| `{field}` | `{contract['capture_allowed_in_future']}` | `{contract['capture_enabled_in_this_task']}` | "
            f"`{contract['current_value_present']}` | `{contract['placeholder_value']}` | `{contract['operator_generated_required']}` | "
            f"`{contract['system_generated_forbidden']}` | `{contract['evidence_attachment_required']}` | "
            f"`{contract['persistence_enabled_in_this_task']}` | `{contract['capture_status']}` |"
        )

    lines.extend([
        "",
        "## Capture Evidence Contract",
        "",
        "| Policy Flag | Required |",
        "|---|---|",
    ])
    for flag, value in packet["capture_evidence_contract"].items():
        lines.append(f"| `{flag}` | `{value}` |")

    lines.extend([
        "",
        "## Pre-capture Validation Contract",
        "",
        "| Policy Flag | State |",
        "|---|---|",
    ])
    for flag, value in packet["pre_capture_validation_contract"].items():
        lines.append(f"| `{flag}` | `{value}` |")

    lines.extend([
        "",
        "## Redaction Validation Dependency Contract",
        "",
        "| Policy Flag | State |",
        "|---|---|",
    ])
    for flag, value in packet["redaction_validation_dependency_contract"].items():
        lines.append(f"| `{flag}` | `{value}` |")

    lines.extend([
        "",
        "## Allowed Future Capture Modes",
        "",
    ])
    for mode in packet["allowed_future_capture_modes"]:
        lines.append(f"- `{mode}`")

    lines.extend([
        "",
        "## Capture Execution Policy",
        "",
        "| Policy Flag | State |",
        "|---|---|",
    ])
    for flag, value in packet["capture_execution_policy"].items():
        lines.append(f"| `{flag}` | `{value}` |")

    lines.extend([
        "",
        "## Operator Input Capture Gate Items",
        "",
        "| Capture Gate Item ID | Source Precheck Item ID | Candidate ID | Relative Path | Capture Gate Status |",
        "|---|---|---|---|---|",
    ])
    for item in packet["operator_input_capture_gate_items"]:
        lines.append(
            f"| `{item['capture_gate_item_id']}` | `{item['source_precheck_item_id']}` | "
            f"`{item['source_candidate_id']}` | `{item['relative_path']}` | `{item['operator_input_capture_gate_status']}` |"
        )

    lines.extend([
        "",
        "## Blocked Reasons",
        "",
    ])
    for reason in packet["blocked_reasons"]:
        lines.append(f"- `{reason}`")

    lines.extend([
        "",
        "## Forbidden Current Actions",
        "",
    ])
    for action in packet["forbidden_current_actions"]:
        lines.append(f"- `[FORBIDDEN]` {action}")

    lines.extend([
        "",
        "## Disallowed Output Enforcement",
        "",
    ])
    for out in packet["disallowed_outputs"]:
        lines.append(f"- `[FORBIDDEN]` {out}")

    lines.extend([
        "",
        "## Truth Protection Flags",
        "",
        "| Flag | State |",
        "|---|---|",
    ])
    for key, value in packet["truth_protection_flags"].items():
        lines.append(f"| `{key}` | `{value}` |")

    lines.extend([
        "",
        "## Safety Flags",
        "",
        "| Flag | State |",
        "|---|---|",
    ])
    for key, value in packet["safety_flags"].items():
        lines.append(f"| `{key}` | `{value}` |")

    lines.extend([
        "",
        "## Navigation",
        "",
        f"- **Allowed Next Step**: `{packet['allowed_next_step']}`",
        f"- **Next Recommended Task**: `{packet['next_recommended_task']}`",
    ])
    return "\n".join(lines) + "\n"


def write_artifacts(
    local_redaction_validation_precheck_packet_path: str | Path,
    repo_root: str | Path = ".",
) -> dict[str, Any]:
    """Write JSON packet and markdown runbook to docs/automation/0175BX/."""
    root = Path(repo_root).resolve()
    out = (root / DOC_REL_DIR).resolve()
    out.mkdir(parents=True, exist_ok=True)

    with open(local_redaction_validation_precheck_packet_path, "r", encoding="utf-8") as f:
        source_packet = json.load(f)

    packet = create_operator_input_capture_gate_contract(source_packet)
    packet_path = out / PACKET_FILENAME
    runbook_path = out / RUNBOOK_FILENAME

    packet_path.write_text(json.dumps(packet, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    runbook_path.write_text(render_runbook(packet), encoding="utf-8", newline="\n")

    return {
        "packet": packet,
        "packet_path": str(packet_path),
        "runbook_path": str(runbook_path),
    }
