"""Operator Input Capture Gate to Supervised Manual Input Dry Run Precheck.

Part of TASK_CONTENTOPS_0175BY_OPERATOR_INPUT_CAPTURE_GATE_TO_SUPERVISED_MANUAL_INPUT_DRY_RUN_PRECHECK_V0.
Consumes the 0175BX Operator Input Capture Gate Contract packet and produces a local-only,
Supervised Manual Input Dry Run Precheck packet.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Any

TASK_LABEL = "TASK_CONTENTOPS_0175BY_OPERATOR_INPUT_CAPTURE_GATE_TO_SUPERVISED_MANUAL_INPUT_DRY_RUN_PRECHECK_V0"
LEDGER_FAMILY = "operator_input_capture_gate_to_supervised_manual_input_dry_run_precheck_future"
HASH_ALGORITHM = "sha256"
DOC_REL_DIR = Path("docs") / "automation" / "0175BY"
PACKET_FILENAME = "operator_input_capture_gate_to_supervised_manual_input_dry_run_precheck_packet.json"
RUNBOOK_FILENAME = "operator_input_capture_gate_to_supervised_manual_input_dry_run_precheck.md"
NEXT_RECOMMENDED_TASK = "TASK_CONTENTOPS_0175BZ_SUPERVISED_MANUAL_INPUT_DRY_RUN_PRECHECK_TO_OPERATOR_VALUE_INTAKE_POLICY_V0"

REQUIRED_INPUT_FIELDS = [
    "intended_audience_lane",
    "content_purpose_category",
    "source_review_notes",
    "risk_review_notes",
    "claim_scope_boundary",
    "manual_operator_decision",
]

FUTURE_OPERATOR_MANUAL_STEPS = [
    "open_supervised_manual_input_session",
    "review_source_candidate_metadata_only",
    "confirm_required_input_field_list",
    "enter_operator_owned_values_in_future_task_only",
    "attach_operator_identity_or_session_reference",
    "attach_manual_review_notes_evidence",
    "run_local_redaction_scan_after_values_exist",
    "run_local_validation_scan_after_values_exist",
    "recheck_draft_eligibility_after_values_pass",
]

DRY_RUN_CHECKS_WITHOUT_VALUES = [
    "source_gate_packet_status_check",
    "required_input_field_schema_check",
    "missing_required_input_field_count_check",
    "capture_execution_lock_check",
    "evidence_requirement_schema_check",
    "redaction_validation_dependency_lock_check",
    "draft_generation_lock_check",
    "truth_protection_flag_lock_check",
    "safety_flag_lock_check",
    "item_mapping_integrity_check",
]

BLOCKED_UNTIL_VALUES_EXIST = [
    "operator_value_acceptance",
    "operator_value_persistence",
    "evidence_capture",
    "field_non_empty_validation",
    "operator_generated_validation",
    "redaction_scan_execution",
    "validation_execution",
    "draft_eligibility_recheck",
    "draft_generation",
    "ai_writer_generation",
    "public_posting",
    "live_dispatch",
]

FUTURE_EVIDENCE_REQUIREMENTS = [
    "operator_identity_or_session_ref",
    "operator_entry_timestamp",
    "source_packet_hash",
    "manual_review_notes",
    "redaction_check_result",
    "validation_check_result",
    "no_secret_values_attestation",
    "no_raw_vendor_redistribution_attestation",
    "no_unverified_market_values_attestation",
    "no_financial_signal_language_attestation",
]

FORBIDDEN_CURRENT_ACTIONS = [
    "actual_input_capture",
    "real_operator_value_acceptance",
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
    "local_storage_write",
    "session_storage_write",
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
    "dry_run_truth_promoted": False,
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
    "manual_input_dry_run_enabled": False,
    "evidence_capture_enabled": False,
    "local_storage_write_enabled": False,
    "session_storage_write_enabled": False,
}


def _source_packet_hash(packet: dict[str, Any]) -> str:
    packet_hash = packet.get("packet_hash")
    if isinstance(packet_hash, str) and packet_hash:
        return packet_hash
    serialized = json.dumps(packet, sort_keys=True, separators=(",", ":"))
    return sha256(serialized.encode("utf-8")).hexdigest()


def _manual_input_dry_run_policy() -> dict[str, bool | str]:
    return {
        "dry_run_precheck_only": True,
        "manual_input_session_started": False,
        "operator_input_capture_enabled_in_this_task": False,
        "real_operator_value_acceptance_enabled_in_this_task": False,
        "editable_ui_enabled_in_this_task": False,
        "form_submission_enabled_in_this_task": False,
        "evidence_capture_enabled_in_this_task": False,
        "persistence_enabled_in_this_task": False,
        "validation_execution_enabled_in_this_task": False,
        "redaction_execution_enabled_in_this_task": False,
        "draft_eligibility_recheck_enabled_in_this_task": False,
        "pass_status": "BLOCKED_PENDING_REAL_OPERATOR_VALUES",
    }


def _dry_run_check_matrix() -> dict[str, dict[str, bool | str]]:
    return {
        check: {
            "dry_run_check_possible_without_values": True,
            "executes_real_capture": False,
            "executes_validation_or_redaction": False,
            "writes_persistence": False,
            "promotes_truth": False,
            "check_status": "DRY_RUN_SCHEMA_CHECK_ONLY",
        }
        for check in DRY_RUN_CHECKS_WITHOUT_VALUES
    }


def _blocked_execution_matrix() -> dict[str, dict[str, bool | str]]:
    return {
        item: {
            "blocked_now": True,
            "requires_real_operator_values": True,
            "enabled_in_this_task": False,
            "blocking_reason": "real_operator_values_absent_and_capture_disabled",
        }
        for item in BLOCKED_UNTIL_VALUES_EXIST
    }


def _future_evidence_requirement_matrix() -> dict[str, dict[str, bool | str | None]]:
    return {
        requirement: {
            "required_in_future": True,
            "captured_in_this_task": False,
            "current_value_present": False,
            "current_value": None,
            "blocking_reason": "evidence_capture_not_enabled_in_this_task",
        }
        for requirement in FUTURE_EVIDENCE_REQUIREMENTS
    }


def _draft_eligibility_block_reason() -> dict[str, bool | str | list[str]]:
    return {
        "draft_eligibility_status": "BLOCKED_DRAFT_ELIGIBILITY_SUPERVISED_INPUT_REQUIRED",
        "draft_generation_enabled": False,
        "draft_eligibility_recheck_enabled": False,
        "required_operator_values_present": False,
        "redaction_validation_passed": False,
        "evidence_requirements_satisfied": False,
        "blocking_reasons": [
            "missing_required_operator_inputs",
            "manual_input_dry_run_precheck_only",
            "operator_values_not_accepted_or_persisted",
            "redaction_validation_not_executed",
            "draft_eligibility_recheck_not_enabled",
        ],
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
        "local_storage_enabled": False,
        "session_storage_enabled": False,
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
    if source_status == "BLOCKED_OPERATOR_INPUT_CAPTURE_GATE_PENDING_SUPERVISED_ACTIVATION":
        return "BLOCKED_SUPERVISED_MANUAL_INPUT_DRY_RUN_PENDING_REAL_VALUES"
    if source_status.startswith("BLOCKED"):
        return "BLOCKED_BY_OPERATOR_INPUT_CAPTURE_GATE"
    return "BLOCKED_BY_OPERATOR_INPUT_CAPTURE_GATE"


def create_supervised_manual_input_dry_run_precheck(
    operator_input_capture_gate_packet: dict[str, Any],
    next_recommended_task: str | None = None,
) -> dict[str, Any]:
    """Transition Operator Input Capture Gate Contract packet into a manual-input dry-run precheck packet."""
    if not operator_input_capture_gate_packet or not isinstance(operator_input_capture_gate_packet, dict):
        raise ValueError("Operator input capture gate packet is missing or malformed. Failing closed.")

    global_status = operator_input_capture_gate_packet.get("global_operator_input_capture_gate_status")
    if global_status != "BLOCKED_OPERATOR_INPUT_CAPTURE_GATE_PENDING_SUPERVISED_ACTIVATION":
        raise ValueError(f"Invalid global capture gate status '{global_status}'. Failing closed.")

    source_items = operator_input_capture_gate_packet.get("operator_input_capture_gate_items", [])
    if not isinstance(source_items, list):
        raise ValueError("operator_input_capture_gate_items must be a list. Failing closed.")

    dry_run_items = []
    blocked_reasons = [
        "manual_input_dry_run_precheck_only",
        "operator_input_capture_disabled",
        "real_operator_values_absent",
        "validation_redaction_execution_disabled",
        "draft_eligibility_recheck_disabled",
    ]

    manual_policy = _manual_input_dry_run_policy()
    dry_run_matrix = _dry_run_check_matrix()
    blocked_matrix = _blocked_execution_matrix()
    evidence_matrix = _future_evidence_requirement_matrix()
    capture_policy = _capture_execution_policy()
    draft_block = _draft_eligibility_block_reason()

    for index, item in enumerate(source_items, start=1):
        source_status = item.get("operator_input_capture_gate_status", "")
        source_candidate_id = item.get("source_candidate_id", "unknown_candidate")
        dry_run_item = {
            "dry_run_precheck_item_id": f"manual_input_dry_run_item_{index:02d}_{source_candidate_id}",
            "source_capture_gate_item_id": item.get("capture_gate_item_id", "unknown_item_id"),
            "source_precheck_item_id": item.get("source_precheck_item_id", "unknown_precheck_item_id"),
            "source_candidate_id": source_candidate_id,
            "relative_path": item.get("relative_path", ""),
            "evidence_role": item.get("evidence_role", "unknown"),
            "source_family": item.get("source_family", "unknown"),
            "records_count": item.get("records_count", 0),
            "contract_name": item.get("contract_name"),
            "intent_scope_label": item.get("intent_scope_label", "unknown_metadata_review"),
            "source_operator_input_capture_gate_status": source_status,
            "supervised_manual_input_dry_run_precheck_status": _map_item_status(source_status),
            "required_input_fields": REQUIRED_INPUT_FIELDS.copy(),
            "missing_required_input_fields": REQUIRED_INPUT_FIELDS.copy(),
            "future_operator_manual_steps": FUTURE_OPERATOR_MANUAL_STEPS.copy(),
            "dry_run_checks_without_values": DRY_RUN_CHECKS_WITHOUT_VALUES.copy(),
            "blocked_until_values_exist": BLOCKED_UNTIL_VALUES_EXIST.copy(),
            "future_evidence_requirements": FUTURE_EVIDENCE_REQUIREMENTS.copy(),
            "manual_input_dry_run_policy": manual_policy.copy(),
            "dry_run_check_matrix": dry_run_matrix.copy(),
            "blocked_execution_matrix": blocked_matrix.copy(),
            "future_evidence_requirement_matrix": evidence_matrix.copy(),
            "draft_eligibility_block_reason": draft_block.copy(),
            "capture_execution_policy": capture_policy.copy(),
            "blocked_reasons": blocked_reasons.copy(),
            "allowed_next_step": "stage_supervised_manual_input_dry_run_precheck_to_operator_value_intake_policy",
            "forbidden_current_actions": FORBIDDEN_CURRENT_ACTIONS.copy(),
            "disallowed_outputs": DISALLOWED_OUTPUTS.copy(),
        }
        dry_run_items.append(dry_run_item)

    actual_next_task = next_recommended_task or NEXT_RECOMMENDED_TASK
    raw_packet = {
        "task_label": TASK_LABEL,
        "source_operator_input_capture_gate_packet_hash": _source_packet_hash(operator_input_capture_gate_packet),
        "source_packet_task_label": operator_input_capture_gate_packet.get("task_label", "unknown"),
        "source_capture_gate_item_count": len(source_items),
        "global_supervised_manual_input_dry_run_precheck_status": "BLOCKED_SUPERVISED_MANUAL_INPUT_DRY_RUN_PENDING_REAL_VALUES",
        "required_input_fields": REQUIRED_INPUT_FIELDS.copy(),
        "missing_required_input_fields": REQUIRED_INPUT_FIELDS.copy(),
        "supervised_manual_input_dry_run_precheck_items": dry_run_items,
        "future_operator_manual_steps": FUTURE_OPERATOR_MANUAL_STEPS.copy(),
        "dry_run_checks_without_values": DRY_RUN_CHECKS_WITHOUT_VALUES.copy(),
        "blocked_until_values_exist": BLOCKED_UNTIL_VALUES_EXIST.copy(),
        "future_evidence_requirements": FUTURE_EVIDENCE_REQUIREMENTS.copy(),
        "manual_input_dry_run_policy": manual_policy,
        "dry_run_check_matrix": dry_run_matrix,
        "blocked_execution_matrix": blocked_matrix,
        "future_evidence_requirement_matrix": evidence_matrix,
        "draft_eligibility_block_reason": draft_block,
        "blocked_reasons": blocked_reasons.copy(),
        "allowed_next_step": "stage_supervised_manual_input_dry_run_precheck_to_operator_value_intake_policy",
        "forbidden_current_actions": FORBIDDEN_CURRENT_ACTIONS.copy(),
        "disallowed_outputs": DISALLOWED_OUTPUTS.copy(),
        "truth_protection_flags": TRUTH_PROTECTION_FLAGS.copy(),
        "safety_flags": SAFETY_FLAGS.copy(),
        "draft_generation_policy": _draft_generation_policy(),
        "capture_execution_policy": capture_policy.copy(),
        "next_recommended_task": actual_next_task,
        "ledger_family": LEDGER_FAMILY,
        "hash_algorithm": HASH_ALGORITHM,
    }

    packet_serialized = json.dumps(raw_packet, sort_keys=True, separators=(",", ":"))
    packet_hash = sha256(packet_serialized.encode("utf-8")).hexdigest()
    return {"packet_hash": packet_hash, **raw_packet}


def render_runbook(packet: dict[str, Any]) -> str:
    """Render deterministic markdown runbook for supervised manual input dry-run precheck."""
    lines = [
        "# Supervised Manual Input Dry Run Precheck",
        "",
        "> [!IMPORTANT]",
        "> This is a deterministic local dry-run precheck for future supervised manual input staging. Actual operator input capture, evidence capture, validation, redaction, persistence, draft generation, and live/API behavior remain disabled.",
        "",
        f"- **Task Label**: `{packet['task_label']}`",
        f"- **Source Operator Input Capture Gate Packet Hash**: `{packet['source_operator_input_capture_gate_packet_hash']}`",
        f"- **Source Packet Task Label**: `{packet['source_packet_task_label']}`",
        f"- **Packet Hash**: `{packet['packet_hash']}`",
        f"- **Global Supervised Manual Input Dry Run Precheck Status**: `{packet['global_supervised_manual_input_dry_run_precheck_status']}`",
        f"- **Source Capture Gate Item Count**: `{packet['source_capture_gate_item_count']}`",
        f"- **Dry Run Precheck Item Count**: `{len(packet['supervised_manual_input_dry_run_precheck_items'])}`",
        f"- **Ledger Family**: `{packet['ledger_family']}`",
        "",
        "## Future Human Operator Steps",
        "",
    ]
    for step in packet["future_operator_manual_steps"]:
        lines.append(f"- `{step}`")

    lines.extend(["", "## What Remains Blocked Now", ""])
    for item in packet["blocked_until_values_exist"]:
        lines.append(f"- `{item}`")

    lines.extend(["", "## Dry-run Checks Possible Without Values", ""])
    for check in packet["dry_run_checks_without_values"]:
        lines.append(f"- `{check}`")

    lines.extend(["", "## Cannot Run Until Values Exist", ""])
    for item in packet["blocked_until_values_exist"]:
        lines.append(f"- `{item}`")

    lines.extend(["", "## Future Evidence Requirements", ""])
    for requirement in packet["future_evidence_requirements"]:
        lines.append(f"- `{requirement}`")

    lines.extend([
        "",
        "## Manual Input Dry Run Policy",
        "",
        "| Policy Flag | State |",
        "|---|---|",
    ])
    for flag, value in packet["manual_input_dry_run_policy"].items():
        lines.append(f"| `{flag}` | `{value}` |")

    lines.extend([
        "",
        "## Dry-run Check Matrix",
        "",
        "| Check | Possible Without Values | Real Capture | Validation/Redaction | Persistence | Truth Promotion | Status |",
        "|---|---|---|---|---|---|---|",
    ])
    for check, row in packet["dry_run_check_matrix"].items():
        lines.append(
            f"| `{check}` | `{row['dry_run_check_possible_without_values']}` | `{row['executes_real_capture']}` | "
            f"`{row['executes_validation_or_redaction']}` | `{row['writes_persistence']}` | "
            f"`{row['promotes_truth']}` | `{row['check_status']}` |"
        )

    lines.extend([
        "",
        "## Future Evidence Requirement Matrix",
        "",
        "| Requirement | Required Later | Captured Now | Current Value Present | Blocking Reason |",
        "|---|---|---|---|---|",
    ])
    for requirement, row in packet["future_evidence_requirement_matrix"].items():
        lines.append(
            f"| `{requirement}` | `{row['required_in_future']}` | `{row['captured_in_this_task']}` | "
            f"`{row['current_value_present']}` | `{row['blocking_reason']}` |"
        )

    lines.extend([
        "",
        "## Draft Eligibility Remains Blocked Because",
        "",
    ])
    draft_block = packet["draft_eligibility_block_reason"]
    lines.append(f"- **Draft Eligibility Status**: `{draft_block['draft_eligibility_status']}`")
    lines.append(f"- **Draft Generation Enabled**: `{draft_block['draft_generation_enabled']}`")
    lines.append(f"- **Draft Eligibility Recheck Enabled**: `{draft_block['draft_eligibility_recheck_enabled']}`")
    for reason in draft_block["blocking_reasons"]:
        lines.append(f"- `{reason}`")

    lines.extend([
        "",
        "## Supervised Manual Input Dry Run Precheck Items",
        "",
        "| Dry Run Item ID | Source Capture Gate Item ID | Candidate ID | Relative Path | Dry Run Status |",
        "|---|---|---|---|---|",
    ])
    for item in packet["supervised_manual_input_dry_run_precheck_items"]:
        lines.append(
            f"| `{item['dry_run_precheck_item_id']}` | `{item['source_capture_gate_item_id']}` | "
            f"`{item['source_candidate_id']}` | `{item['relative_path']}` | "
            f"`{item['supervised_manual_input_dry_run_precheck_status']}` |"
        )

    lines.extend(["", "## Forbidden Current Actions", ""])
    for action in packet["forbidden_current_actions"]:
        lines.append(f"- `[FORBIDDEN]` {action}")

    lines.extend(["", "## Disallowed Output Enforcement", ""])
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
    operator_input_capture_gate_packet_path: str | Path,
    repo_root: str | Path = ".",
) -> dict[str, Any]:
    """Write JSON packet and markdown runbook to docs/automation/0175BY/."""
    root = Path(repo_root).resolve()
    out = (root / DOC_REL_DIR).resolve()
    out.mkdir(parents=True, exist_ok=True)

    with open(operator_input_capture_gate_packet_path, "r", encoding="utf-8") as f:
        source_packet = json.load(f)

    packet = create_supervised_manual_input_dry_run_precheck(source_packet)
    packet_path = out / PACKET_FILENAME
    runbook_path = out / RUNBOOK_FILENAME

    packet_path.write_text(json.dumps(packet, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    runbook_path.write_text(render_runbook(packet), encoding="utf-8", newline="\n")

    return {
        "packet": packet,
        "packet_path": str(packet_path),
        "runbook_path": str(runbook_path),
    }
