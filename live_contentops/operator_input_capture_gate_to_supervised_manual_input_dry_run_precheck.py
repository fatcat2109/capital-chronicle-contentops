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

GLOBAL_MANUAL_INPUT_DRY_RUN_STATUS = "BLOCKED_MANUAL_INPUT_DRY_RUN_PENDING_REAL_OPERATOR_VALUES"
BLOCKED_BY_CAPTURE_GATE_STATUS = "BLOCKED_BY_OPERATOR_INPUT_CAPTURE_GATE_CONTRACT"
SOURCE_GATE_STATUS_REQUIRED = "BLOCKED_OPERATOR_INPUT_CAPTURE_GATE_PENDING_SUPERVISED_ACTIVATION"

DECLARATION_ONLY_CHECKS = [
    "verify_required_fields_declared",
    "verify_capture_gate_status_blocked",
    "verify_no_current_values_present",
    "verify_evidence_requirements_declared",
    "verify_validation_dependencies_declared",
    "verify_redaction_dependencies_declared",
    "verify_no_persistence_enabled",
    "verify_no_generation_enabled",
    "verify_no_live_api_enabled",
]

VALUE_DEPENDENT_CHECKS = [
    "operator_value_acceptance",
    "operator_value_persistence",
    "evidence_capture",
    "field_non_empty_validation",
    "operator_generated_validation",
    "redaction_scan_execution",
    "validation_execution",
    "draft_eligibility_recheck",
]

BLOCKED_EXECUTION_REASONS = [
    "real_operator_values_absent",
    "operator_input_capture_disabled",
    "evidence_capture_disabled",
    "validation_execution_disabled",
    "redaction_execution_disabled",
    "persistence_disabled",
    "draft_eligibility_recheck_disabled",
    "draft_generation_disabled",
    "live_dispatch_disabled",
]

ALLOWED_FUTURE_MANUAL_INPUT_MODES = [
    "supervised_manual_operator_entry",
    "imported_operator_review_packet",
    "deferred_human_review_session",
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

DRY_RUN_CHECKS_WITHOUT_VALUES = DECLARATION_ONLY_CHECKS.copy()
BLOCKED_UNTIL_VALUES_EXIST = VALUE_DEPENDENT_CHECKS.copy()
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
    "dry_run_operator_value",
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
    "dry_run_value_truth_promoted": False,
}

SAFETY_FLAGS = {
    "dry_run_schema_only": True,
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
    "evidence_capture_enabled": False,
    "real_operator_value_acceptance_enabled": False,
}


def _source_packet_hash(packet: dict[str, Any]) -> str:
    packet_hash = packet.get("packet_hash")
    if isinstance(packet_hash, str) and packet_hash:
        return packet_hash
    serialized = json.dumps(packet, sort_keys=True, separators=(",", ":"))
    return sha256(serialized.encode("utf-8")).hexdigest()


def _manual_input_procedure_plan() -> list[dict[str, Any]]:
    return [
        {
            "future_step_order": index,
            "field_name": field_name,
            "expected_future_operator_action": "provide_supervised_manual_value",
            "current_value": None,
            "current_value_present": False,
            "placeholder_value": "PENDING_OPERATOR_INPUT",
            "dry_run_status": "PROCEDURE_DEFINED_VALUE_ABSENT",
            "operator_identity_required": True,
            "timestamp_required": True,
            "evidence_attachment_required": True,
            "redaction_required_after_entry": True,
            "validation_required_after_entry": True,
            "persistence_enabled_in_this_task": False,
            "capture_enabled_in_this_task": False,
            "validation_execution_enabled_in_this_task": False,
            "redaction_execution_enabled_in_this_task": False,
            "blocking_reason": "real_operator_value_required_before_manual_input_dry_run_can_pass",
        }
        for index, field_name in enumerate(REQUIRED_INPUT_FIELDS, start=1)
    ]


def _dry_run_checklist() -> list[dict[str, bool | str]]:
    declaration_checks = [
        {
            "check_name": check_name,
            "can_execute_without_values": True,
            "dry_run_check_status": "DRY_RUN_DECLARATION_CHECK_PASSED",
            "pass_status": "PASS_SCHEMA_ONLY",
        }
        for check_name in DECLARATION_ONLY_CHECKS
    ]
    value_dependent_checks = [
        {
            "check_name": check_name,
            "can_execute_without_values": False,
            "dry_run_check_status": "BLOCKED_PENDING_OPERATOR_VALUE",
            "pass_status": "BLOCKED_PENDING_OPERATOR_VALUE",
        }
        for check_name in VALUE_DEPENDENT_CHECKS
    ]
    return declaration_checks + value_dependent_checks


def _dry_run_check_matrix() -> dict[str, dict[str, bool | str]]:
    return {row["check_name"]: row for row in _dry_run_checklist()}


def _blocked_execution_matrix() -> dict[str, dict[str, bool | str]]:
    return {
        reason: {
            "blocked_now": True,
            "enabled_in_this_task": False,
            "blocking_reason": reason,
        }
        for reason in BLOCKED_EXECUTION_REASONS
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


def _dry_run_execution_policy() -> dict[str, bool]:
    return {
        "dry_run_enabled_in_this_task": True,
        "accepts_real_operator_values": False,
        "stores_operator_values": False,
        "validates_operator_values": False,
        "redacts_operator_values": False,
        "evidence_capture_enabled": False,
        "operator_identity_capture_enabled": False,
        "timestamp_capture_enabled": False,
        "persistence_enabled": False,
        "draft_eligibility_recheck_enabled": False,
        "draft_generation_enabled": False,
        "ai_writer_generation_enabled": False,
        "public_postable": False,
        "dispatch_ready": False,
    }


def _evidence_requirements() -> dict[str, bool]:
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


def _validation_dependency_summary() -> dict[str, bool]:
    return {
        "pre_capture_validation_contract_present": True,
        "validation_execution_enabled_in_source": False,
        "validation_execution_enabled_in_this_task": False,
        "requires_real_operator_values": True,
    }


def _redaction_dependency_summary() -> dict[str, bool]:
    return {
        "redaction_precheck_required": True,
        "redaction_execution_enabled_in_source": False,
        "redaction_execution_enabled_in_this_task": False,
        "requires_real_operator_values": True,
    }


def _capture_gate_dependency_summary(source_gate_status: str) -> dict[str, bool | str]:
    return {
        "source_gate_status_required": SOURCE_GATE_STATUS_REQUIRED,
        "source_gate_status_observed": source_gate_status,
        "dependency_satisfied_for_procedure_definition": True,
        "dependency_satisfied_for_actual_capture": False,
    }


def _map_item_status(source_status: str) -> str:
    if source_status == SOURCE_GATE_STATUS_REQUIRED:
        return GLOBAL_MANUAL_INPUT_DRY_RUN_STATUS
    return BLOCKED_BY_CAPTURE_GATE_STATUS


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
    blocked_reasons = BLOCKED_EXECUTION_REASONS.copy()

    dry_run_checklist = _dry_run_checklist()
    dry_run_matrix = _dry_run_check_matrix()
    blocked_matrix = _blocked_execution_matrix()
    evidence_matrix = _future_evidence_requirement_matrix()
    execution_policy = _dry_run_execution_policy()
    evidence_requirements = _evidence_requirements()
    validation_summary = _validation_dependency_summary()
    redaction_summary = _redaction_dependency_summary()
    capture_summary = _capture_gate_dependency_summary(global_status)
    manual_procedure_plan = _manual_input_procedure_plan()

    for index, item in enumerate(source_items, start=1):
        source_status = item.get("operator_input_capture_gate_status", "")
        source_candidate_id = item.get("source_candidate_id", "unknown_candidate")
        item_status = _map_item_status(source_status)
        dry_run_item = {
            "dry_run_item_id": f"manual_input_dry_run_item_{index:02d}_{source_candidate_id}",
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
            "dry_run_status": item_status,
            "supervised_manual_input_dry_run_precheck_status": item_status,
            "required_input_fields": REQUIRED_INPUT_FIELDS.copy(),
            "missing_required_input_fields": REQUIRED_INPUT_FIELDS.copy(),
            "manual_input_procedure_plan": manual_procedure_plan.copy(),
            "dry_run_checklist": dry_run_checklist.copy(),
            "dry_run_execution_policy": execution_policy.copy(),
            "blocked_execution_reasons": blocked_reasons.copy(),
            "evidence_requirements": evidence_requirements.copy(),
            "validation_dependency_summary": validation_summary.copy(),
            "redaction_dependency_summary": redaction_summary.copy(),
            "capture_gate_dependency_summary": capture_summary.copy(),
            "dry_run_checks_without_values": DRY_RUN_CHECKS_WITHOUT_VALUES.copy(),
            "blocked_until_values_exist": BLOCKED_UNTIL_VALUES_EXIST.copy(),
            "future_evidence_requirements": FUTURE_EVIDENCE_REQUIREMENTS.copy(),
            "dry_run_check_matrix": dry_run_matrix.copy(),
            "blocked_execution_matrix": blocked_matrix.copy(),
            "future_evidence_requirement_matrix": evidence_matrix.copy(),
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
        "source_gate_status": global_status,
        "global_manual_input_dry_run_status": GLOBAL_MANUAL_INPUT_DRY_RUN_STATUS,
        "global_supervised_manual_input_dry_run_precheck_status": GLOBAL_MANUAL_INPUT_DRY_RUN_STATUS,
        "required_input_fields": REQUIRED_INPUT_FIELDS.copy(),
        "missing_required_input_fields": REQUIRED_INPUT_FIELDS.copy(),
        "dry_run_items": dry_run_items,
        "supervised_manual_input_dry_run_precheck_items": dry_run_items,
        "manual_input_procedure_plan": manual_procedure_plan,
        "dry_run_checklist": dry_run_checklist,
        "dry_run_execution_policy": execution_policy,
        "blocked_execution_reasons": blocked_reasons.copy(),
        "evidence_requirements": evidence_requirements,
        "validation_dependency_summary": validation_summary,
        "redaction_dependency_summary": redaction_summary,
        "capture_gate_dependency_summary": capture_summary,
        "future_operator_manual_steps": FUTURE_OPERATOR_MANUAL_STEPS.copy(),
        "allowed_future_manual_input_modes": ALLOWED_FUTURE_MANUAL_INPUT_MODES.copy(),
        "dry_run_checks_without_values": DRY_RUN_CHECKS_WITHOUT_VALUES.copy(),
        "blocked_until_values_exist": BLOCKED_UNTIL_VALUES_EXIST.copy(),
        "future_evidence_requirements": FUTURE_EVIDENCE_REQUIREMENTS.copy(),
        "dry_run_check_matrix": dry_run_matrix,
        "blocked_execution_matrix": blocked_matrix,
        "future_evidence_requirement_matrix": evidence_matrix,
        "blocked_reasons": blocked_reasons.copy(),
        "allowed_next_step": "stage_supervised_manual_input_dry_run_precheck_to_operator_value_intake_policy",
        "forbidden_current_actions": FORBIDDEN_CURRENT_ACTIONS.copy(),
        "disallowed_outputs": DISALLOWED_OUTPUTS.copy(),
        "truth_protection_flags": TRUTH_PROTECTION_FLAGS.copy(),
        "safety_flags": SAFETY_FLAGS.copy(),
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
        "## Dry Run Execution Policy",
        "",
        "| Policy Flag | State |",
        "|---|---|",
    ])
    for flag, value in packet["dry_run_execution_policy"].items():
        lines.append(f"| `{flag}` | `{value}` |")

    lines.extend([
        "",
        "## Dry-run Checklist",
        "",
        "| Check | Can Execute Without Values | Status | Pass Status |",
        "|---|---|---|---|",
    ])
    for row in packet["dry_run_checklist"]:
        lines.append(
            f"| `{row['check_name']}` | `{row['can_execute_without_values']}` | "
            f"`{row['dry_run_check_status']}` | `{row['pass_status']}` |"
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
        "## Blocked Execution Reasons",
        "",
    ])
    for reason in packet["blocked_execution_reasons"]:
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
