"""Supervised Input Resolution Plan to Local Redaction and Validation Precheck.

Part of TASK_CONTENTOPS_0175BW_SUPERVISED_INPUT_RESOLUTION_PLAN_TO_LOCAL_REDACTION_AND_VALIDATION_PRECHECK_V0.
Consumes the 0175BV Supervised Input Resolution Plan packet and produces a local-only,
Local Redaction and Validation Precheck packet.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Any

TASK_LABEL = "TASK_CONTENTOPS_0175BW_SUPERVISED_INPUT_RESOLUTION_PLAN_TO_LOCAL_REDACTION_AND_VALIDATION_PRECHECK_V0"
LEDGER_FAMILY = "supervised_input_resolution_plan_to_local_redaction_and_validation_precheck_future"
HASH_ALGORITHM = "sha256"
DOC_REL_DIR = Path("docs") / "automation" / "0175BW"
PACKET_FILENAME = "supervised_input_resolution_plan_to_local_redaction_and_validation_precheck_packet.json"
RUNBOOK_FILENAME = "supervised_input_resolution_plan_to_local_redaction_and_validation_precheck.md"
NEXT_RECOMMENDED_TASK = "TASK_CONTENTOPS_0175BX_LOCAL_REDACTION_VALIDATION_PRECHECK_TO_OPERATOR_INPUT_CAPTURE_GATE_CONTRACT_V0"

REQUIRED_INPUT_FIELDS = [
    "intended_audience_lane",
    "content_purpose_category",
    "source_review_notes",
    "risk_review_notes",
    "claim_scope_boundary",
    "manual_operator_decision",
]

ALLOWED_FUTURE_VALIDATION_MODES = [
    "local_manual_redaction_review",
    "local_schema_validation_after_operator_entry",
    "imported_operator_review_packet_validation",
]

FORBIDDEN_CURRENT_ACTIONS = [
    "actual_input_capture",
    "editable_input_fields",
    "form_submission",
    "save_capture_approve_generate_controls",
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
    "validation_execution",
    "redaction_execution",
    "persistence_write",
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
    "supervised_input_resolution_enabled": False,
}


def _source_packet_hash(packet: dict[str, Any]) -> str:
    packet_hash = packet.get("packet_hash")
    if isinstance(packet_hash, str) and packet_hash:
        return packet_hash
    serialized = json.dumps(packet, sort_keys=True, separators=(",", ":"))
    return sha256(serialized.encode("utf-8")).hexdigest()


def _field_redaction_policy() -> dict[str, dict[str, Any]]:
    return {
        field: {
            "redaction_required": True,
            "current_value_present": False,
            "current_value": None,
            "redaction_status": "PENDING_OPERATOR_VALUE",
            "pii_secret_scan_required": True,
            "credential_secret_scan_required": True,
            "raw_vendor_redistribution_scan_required": True,
            "market_value_scan_required": True,
            "prohibited_signal_language_scan_required": True,
            "redaction_execution_enabled_in_this_task": False,
            "pass_status": "BLOCKED_PENDING_OPERATOR_VALUE",
        }
        for field in REQUIRED_INPUT_FIELDS
    }


def _field_validation_policy() -> dict[str, dict[str, Any]]:
    return {
        field: {
            "validation_required": True,
            "current_value_present": False,
            "current_value": None,
            "validation_status": "PENDING_OPERATOR_VALUE",
            "value_non_empty_required": True,
            "operator_generated_required": True,
            "system_generated_forbidden": True,
            "evidence_attachment_required": True,
            "source_packet_hash_required": True,
            "timestamp_required": True,
            "validation_execution_enabled_in_this_task": False,
            "pass_status": "BLOCKED_PENDING_OPERATOR_VALUE",
        }
        for field in REQUIRED_INPUT_FIELDS
    }


def _evidence_validation_policy() -> dict[str, bool]:
    return {
        "operator_identity_or_session_ref_required": True,
        "timestamp_required": True,
        "source_packet_hash_required": True,
        "manual_review_notes_required": True,
        "redaction_check_required": True,
        "no_secret_values_allowed": True,
        "no_raw_vendor_redistribution_allowed": True,
        "no_unverified_market_values_allowed": True,
        "no_financial_signal_language_allowed": True,
        "evidence_validation_enabled_in_this_task": False,
    }


def _validation_execution_policy() -> dict[str, bool]:
    return {
        "redaction_execution_enabled": False,
        "field_validation_enabled": False,
        "evidence_validation_enabled": False,
        "operator_value_persistence_enabled": False,
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
    if source_status == "BLOCKED_SUPERVISED_INPUT_RESOLUTION_REQUIRED":
        return "BLOCKED_LOCAL_REDACTION_VALIDATION_PRECHECK_PENDING_OPERATOR_VALUES"
    if source_status.startswith("BLOCKED"):
        return "BLOCKED_BY_SUPERVISED_INPUT_RESOLUTION_PLAN"
    return "BLOCKED_BY_SUPERVISED_INPUT_RESOLUTION_PLAN"


def create_local_redaction_and_validation_precheck(
    supervised_input_resolution_plan_packet: dict[str, Any],
    next_recommended_task: str | None = None,
) -> dict[str, Any]:
    """Transition supervised input resolution plan packet into a Local Redaction and Validation Precheck packet."""
    if not supervised_input_resolution_plan_packet or not isinstance(supervised_input_resolution_plan_packet, dict):
        raise ValueError("Supervised input resolution plan packet is missing or malformed. Failing closed.")

    global_status = supervised_input_resolution_plan_packet.get("global_resolution_plan_status")
    if global_status != "BLOCKED_SUPERVISED_INPUT_RESOLUTION_REQUIRED":
        raise ValueError(f"Invalid global resolution plan status '{global_status}'. Failing closed.")

    source_items = supervised_input_resolution_plan_packet.get("supervised_input_resolution_items", [])
    if not isinstance(source_items, list):
        raise ValueError("supervised_input_resolution_items must be a list. Failing closed.")

    redaction_validation_precheck_items = []
    blocked_reasons = [
        "local_redaction_validation_precheck_pending_operator_values",
        "missing_required_operator_inputs",
        "redaction_and_validation_scans_not_executed",
    ]

    field_red_policy = _field_redaction_policy()
    field_val_policy = _field_validation_policy()
    ev_val_policy = _evidence_validation_policy()
    val_exec_policy = _validation_execution_policy()

    for index, item in enumerate(source_items, start=1):
        source_status = item.get("resolution_status", "")
        source_candidate_id = item.get("source_candidate_id", "unknown_candidate")
        
        precheck_item = {
            "precheck_item_id": f"precheck_item_{index:02d}_{source_candidate_id}",
            "source_resolution_item_id": item.get("resolution_item_id", "unknown_item_id"),
            "source_candidate_id": source_candidate_id,
            "relative_path": item.get("relative_path", ""),
            "evidence_role": item.get("evidence_role", "unknown"),
            "source_family": item.get("source_family", "unknown"),
            "records_count": item.get("records_count", 0),
            "contract_name": item.get("contract_name"),
            "intent_scope_label": item.get("intent_scope_label", "unknown_metadata_review"),
            "source_resolution_status": source_status,
            "redaction_validation_precheck_status": _map_item_status(source_status),
            "required_input_fields": REQUIRED_INPUT_FIELDS.copy(),
            "missing_required_input_fields": REQUIRED_INPUT_FIELDS.copy(),
            "field_redaction_policy": field_red_policy.copy(),
            "field_validation_policy": field_val_policy.copy(),
            "evidence_validation_policy": ev_val_policy.copy(),
            "validation_execution_policy": val_exec_policy.copy(),
            "blocked_reasons": blocked_reasons.copy(),
            "allowed_next_step": "stage_local_redaction_validation_precheck_to_operator_input_capture_gate",
            "forbidden_current_actions": FORBIDDEN_CURRENT_ACTIONS.copy(),
            "disallowed_outputs": DISALLOWED_OUTPUTS.copy(),
        }
        redaction_validation_precheck_items.append(precheck_item)

    actual_next_task = next_recommended_task or NEXT_RECOMMENDED_TASK
    raw_packet = {
        "task_label": TASK_LABEL,
        "source_supervised_input_resolution_plan_packet_hash": _source_packet_hash(supervised_input_resolution_plan_packet),
        "source_packet_task_label": supervised_input_resolution_plan_packet.get("task_label", "unknown"),
        "source_resolution_item_count": len(source_items),
        "global_redaction_validation_precheck_status": "BLOCKED_LOCAL_REDACTION_VALIDATION_PRECHECK_PENDING_OPERATOR_VALUES",
        "required_input_fields": REQUIRED_INPUT_FIELDS.copy(),
        "missing_required_input_fields": REQUIRED_INPUT_FIELDS.copy(),
        "redaction_validation_precheck_items": redaction_validation_precheck_items,
        "field_redaction_policy": field_red_policy,
        "field_validation_policy": field_val_policy,
        "evidence_validation_policy": ev_val_policy,
        "allowed_future_validation_modes": ALLOWED_FUTURE_VALIDATION_MODES.copy(),
        "blocked_reasons": blocked_reasons.copy(),
        "allowed_next_step": "stage_local_redaction_validation_precheck_to_operator_input_capture_gate",
        "forbidden_current_actions": FORBIDDEN_CURRENT_ACTIONS.copy(),
        "disallowed_outputs": DISALLOWED_OUTPUTS.copy(),
        "truth_protection_flags": TRUTH_PROTECTION_FLAGS.copy(),
        "safety_flags": SAFETY_FLAGS.copy(),
        "draft_generation_policy": _draft_generation_policy(),
        "validation_execution_policy": val_exec_policy.copy(),
        "next_recommended_task": actual_next_task,
        "ledger_family": LEDGER_FAMILY,
        "hash_algorithm": HASH_ALGORITHM,
    }

    packet_serialized = json.dumps(raw_packet, sort_keys=True, separators=(",", ":"))
    packet_hash = sha256(packet_serialized.encode("utf-8")).hexdigest()
    return {"packet_hash": packet_hash, **raw_packet}


def render_runbook(packet: dict[str, Any]) -> str:
    """Render deterministic markdown runbook for the local redaction and validation precheck."""
    lines = [
        "# Local Redaction and Validation Precheck",
        "",
        "> [!IMPORTANT]",
        "> This is a deterministic local precheck defining validation and redaction policies for future operator-provided values before draft eligibility can be reconsidered. Actual redaction, validation, and draft generation remain disabled.",
        "",
        f"- **Task Label**: `{packet['task_label']}`",
        f"- **Source Supervised Input Resolution Plan Packet Hash**: `{packet['source_supervised_input_resolution_plan_packet_hash']}`",
        f"- **Source Packet Task Label**: `{packet['source_packet_task_label']}`",
        f"- **Packet Hash**: `{packet['packet_hash']}`",
        f"- **Global Redaction and Validation Precheck Status**: `{packet['global_redaction_validation_precheck_status']}`",
        f"- **Source Resolution Item Count**: `{packet['source_resolution_item_count']}`",
        f"- **Redaction Validation Precheck Item Count**: `{len(packet['redaction_validation_precheck_items'])}`",
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
        "## Field Redaction Policy",
        "",
        "| Field | Redaction Required | Current Value Present | Redaction Status | PII Secret Scan | Credential Secret Scan | Market Value Scan | Prohibited Signal Language Scan | Pass Status |",
        "|---|---|---|---|---|---|---|---|---|",
    ])
    for field, plan in packet["field_redaction_policy"].items():
        lines.append(
            f"| `{field}` | `{plan['redaction_required']}` | `{plan['current_value_present']}` | "
            f"`{plan['redaction_status']}` | `{plan['pii_secret_scan_required']}` | `{plan['credential_secret_scan_required']}` | "
            f"`{plan['market_value_scan_required']}` | `{plan['prohibited_signal_language_scan_required']}` | `{plan['pass_status']}` |"
        )

    lines.extend([
        "",
        "## Field Validation Policy",
        "",
        "| Field | Validation Required | Current Value Present | Validation Status | Non-empty Required | Operator Generated Required | System Generated Forbidden | Evidence Attachment Required | Pass Status |",
        "|---|---|---|---|---|---|---|---|---|",
    ])
    for field, plan in packet["field_validation_policy"].items():
        lines.append(
            f"| `{field}` | `{plan['validation_required']}` | `{plan['current_value_present']}` | "
            f"`{plan['validation_status']}` | `{plan['value_non_empty_required']}` | `{plan['operator_generated_required']}` | "
            f"`{plan['system_generated_forbidden']}` | `{plan['evidence_attachment_required']}` | `{plan['pass_status']}` |"
        )

    lines.extend([
        "",
        "## Evidence Validation Policy",
        "",
        "| Policy Flag | State |",
        "|---|---|",
    ])
    for flag, value in packet["evidence_validation_policy"].items():
        lines.append(f"| `{flag}` | `{value}` |")

    lines.extend([
        "",
        "## Allowed Future Validation Modes",
        "",
    ])
    for mode in packet["allowed_future_validation_modes"]:
        lines.append(f"- `{mode}`")

    lines.extend([
        "",
        "## Validation Execution Policy",
        "",
        "| Policy Flag | State |",
        "|---|---|",
    ])
    for flag, value in packet["validation_execution_policy"].items():
        lines.append(f"| `{flag}` | `{value}` |")

    lines.extend([
        "",
        "## Redaction Validation Precheck Items",
        "",
        "| Precheck Item ID | Source Resolution Item ID | Candidate ID | Relative Path | Precheck Status |",
        "|---|---|---|---|---|",
    ])
    for item in packet["redaction_validation_precheck_items"]:
        lines.append(
            f"| `{item['precheck_item_id']}` | `{item['source_resolution_item_id']}` | "
            f"`{item['source_candidate_id']}` | `{item['relative_path']}` | `{item['redaction_validation_precheck_status']}` |"
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
    supervised_input_resolution_plan_packet_path: str | Path,
    repo_root: str | Path = ".",
) -> dict[str, Any]:
    """Write JSON packet and markdown runbook to docs/automation/0175BW/."""
    root = Path(repo_root).resolve()
    out = (root / DOC_REL_DIR).resolve()
    out.mkdir(parents=True, exist_ok=True)

    with open(supervised_input_resolution_plan_packet_path, "r", encoding="utf-8") as f:
        source_packet = json.load(f)

    packet = create_local_redaction_and_validation_precheck(source_packet)
    packet_path = out / PACKET_FILENAME
    runbook_path = out / RUNBOOK_FILENAME

    packet_path.write_text(json.dumps(packet, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    runbook_path.write_text(render_runbook(packet), encoding="utf-8", newline="\n")

    return {
        "packet": packet,
        "packet_path": str(packet_path),
        "runbook_path": str(runbook_path),
    }
