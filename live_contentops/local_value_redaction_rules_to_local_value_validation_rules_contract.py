"""Local Value Redaction Rules to Local Value Validation Rules Contract.

Part of TASK_CONTENTOPS_0175CB_LOCAL_VALUE_REDACTION_RULES_TO_LOCAL_VALUE_VALIDATION_RULES_CONTRACT_V0.
Consumes the 0175CA Local Value Redaction Rules Contract packet and produces a
local-only Local Value Validation Rules Contract packet.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Any

TASK_LABEL = "TASK_CONTENTOPS_0175CB_LOCAL_VALUE_REDACTION_RULES_TO_LOCAL_VALUE_VALIDATION_RULES_CONTRACT_V0"
LEDGER_FAMILY = "local_value_redaction_rules_to_local_value_validation_rules_contract_future"
HASH_ALGORITHM = "sha256"
DOC_REL_DIR = Path("docs") / "automation" / "0175CB"
PACKET_FILENAME = "local_value_redaction_rules_to_local_value_validation_rules_contract_packet.json"
RUNBOOK_FILENAME = "local_value_redaction_rules_to_local_value_validation_rules_contract.md"
NEXT_RECOMMENDED_TASK = "TASK_CONTENTOPS_0175CC_LOCAL_VALUE_VALIDATION_RULES_TO_OPERATOR_VALUE_INTAKE_READINESS_REVIEW_V0"

REQUIRED_INPUT_FIELDS = [
    "intended_audience_lane",
    "content_purpose_category",
    "source_review_notes",
    "risk_review_notes",
    "claim_scope_boundary",
    "manual_operator_decision",
]

SOURCE_GLOBAL_STATUS_REQUIRED = "BLOCKED_LOCAL_VALUE_REDACTION_RULES_DEFINED_EXECUTION_DISABLED"
GLOBAL_LOCAL_VALUE_VALIDATION_RULES_CONTRACT_STATUS = "BLOCKED_LOCAL_VALUE_VALIDATION_RULES_DEFINED_EXECUTION_DISABLED"
BLOCKED_BY_LOCAL_VALUE_REDACTION_RULES_CONTRACT = "BLOCKED_BY_LOCAL_VALUE_REDACTION_RULES_CONTRACT"
ALLOWED_NEXT_STEP = "stage_local_value_validation_rules_contract_to_operator_value_intake_readiness_review"

ALLOWED_FUTURE_VALIDATION_MODES = [
    "local_manual_validation_review",
    "local_schema_validation_after_redaction",
    "imported_operator_review_packet_validation",
]

VALIDATION_RULE_DEFINITIONS = [
    ("operator_value_present_validation_rule", "Operator Value Present Validation Rule", "presence"),
    ("non_empty_string_validation_rule", "Non Empty String Validation Rule", "shape"),
    ("whitespace_only_rejection_rule", "Whitespace Only Rejection Rule", "shape"),
    ("system_generated_value_rejection_rule", "System Generated Value Rejection Rule", "provenance"),
    ("evidence_attachment_validation_rule", "Evidence Attachment Validation Rule", "evidence"),
    ("redaction_result_required_validation_rule", "Redaction Result Required Validation Rule", "redaction_dependency"),
    ("secret_absence_validation_rule", "Secret Absence Validation Rule", "prohibited_content_absence"),
    ("credential_absence_validation_rule", "Credential Absence Validation Rule", "prohibited_content_absence"),
    ("raw_vendor_redistribution_absence_validation_rule", "Raw Vendor Redistribution Absence Validation Rule", "prohibited_content_absence"),
    ("unverified_market_value_absence_validation_rule", "Unverified Market Value Absence Validation Rule", "prohibited_content_absence"),
    ("financial_signal_language_absence_validation_rule", "Financial Signal Language Absence Validation Rule", "prohibited_content_absence"),
    ("buy_sell_hold_language_absence_validation_rule", "Buy Sell Hold Language Absence Validation Rule", "prohibited_content_absence"),
    ("price_target_language_absence_validation_rule", "Price Target Language Absence Validation Rule", "prohibited_content_absence"),
    ("order_fill_pnl_language_absence_validation_rule", "Order Fill PnL Language Absence Validation Rule", "prohibited_content_absence"),
    ("executable_content_absence_validation_rule", "Executable Content Absence Validation Rule", "prohibited_content_absence"),
    ("binary_attachment_absence_validation_rule", "Binary Attachment Absence Validation Rule", "prohibited_content_absence"),
    ("structured_payload_absence_validation_rule", "Structured Payload Absence Validation Rule", "prohibited_content_absence"),
]

RULE_IDS = [rule_id for rule_id, _, _ in VALIDATION_RULE_DEFINITIONS]

BLOCKED_REASONS = [
    "local_value_validation_rules_contract_only_no_validation_executed",
    "operator_values_absent",
    "redacted_operator_values_absent",
    "validation_execution_disabled",
    "validation_result_generation_disabled",
    "validation_result_persistence_disabled",
    "redaction_execution_disabled",
    "policy_scan_execution_disabled",
    "redacted_value_generation_disabled",
    "operator_value_intake_disabled",
    "evidence_capture_disabled",
    "draft_eligibility_recheck_disabled",
    "draft_generation_disabled",
    "live_dispatch_disabled",
]

FORBIDDEN_CURRENT_ACTIONS = [
    "actual_input_capture",
    "real_operator_value_acceptance",
    "operator_value_intake",
    "editable_input_fields",
    "form_submission",
    "save_capture_approve_generate_controls",
    "operator_value_persistence",
    "evidence_capture",
    "validation_execution",
    "validation_result_generation",
    "validation_result_persistence",
    "redaction_execution",
    "policy_scan_execution",
    "redacted_value_generation",
    "redaction_result_persistence",
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
    "dry_run_operator_value",
    "accepted_operator_value",
    "redacted_operator_value",
    "redaction_result_value",
    "validation_result_value",
    "validated_operator_value",
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
    "dry_run_value_truth_promoted": False,
    "accepted_operator_value_truth_promoted": False,
    "redaction_result_truth_promoted": False,
    "validation_result_truth_promoted": False,
    "validated_operator_value_truth_promoted": False,
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
    "validation_execution_enabled": False,
    "validation_result_generation_enabled": False,
    "validation_result_persistence_enabled": False,
    "redaction_execution_enabled": False,
    "policy_scan_execution_enabled": False,
    "redacted_value_generation_enabled": False,
    "redaction_result_persistence_enabled": False,
    "draft_eligibility_recheck_enabled": False,
    "evidence_capture_enabled": False,
    "real_operator_value_acceptance_enabled": False,
    "operator_value_intake_enabled": False,
    "local_storage_write_enabled": False,
    "session_storage_write_enabled": False,
    "validation_rules_schema_only": True,
}


def _source_packet_hash(packet: dict[str, Any]) -> str:
    packet_hash = packet.get("packet_hash")
    if isinstance(packet_hash, str) and packet_hash:
        return packet_hash
    serialized = json.dumps(packet, sort_keys=True, separators=(",", ":"))
    return sha256(serialized.encode("utf-8")).hexdigest()


def _validation_rule_catalog() -> list[dict[str, Any]]:
    return [
        {
            "rule_id": rule_id,
            "rule_label": rule_label,
            "rule_type": rule_type,
            "applies_to_fields": REQUIRED_INPUT_FIELDS.copy(),
            "validation_required_before_acceptance": True,
            "rejection_required_if_rule_fails": True,
            "execution_enabled_in_this_task": False,
            "generated_validation_result_enabled": False,
            "evidence_required": True,
            "pass_status": "BLOCKED_PENDING_OPERATOR_VALUE",
        }
        for rule_id, rule_label, rule_type in VALIDATION_RULE_DEFINITIONS
    ]


def _field_validation_rule_map() -> dict[str, dict[str, Any]]:
    return {
        field_name: {
            "field_name": field_name,
            "current_value": None,
            "current_value_present": False,
            "applicable_rule_ids": RULE_IDS.copy(),
            "validation_required_before_acceptance": True,
            "rejection_required_if_rule_fails": True,
            "validation_execution_enabled_in_this_task": False,
            "validation_result_generation_enabled_in_this_task": False,
            "acceptance_status": "BLOCKED_VALIDATION_RULES_DEFINED_EXECUTION_DISABLED",
            "blocking_reason": "operator_values_absent_and_validation_execution_disabled",
        }
        for field_name in REQUIRED_INPUT_FIELDS
    }


def _validation_evidence_policy() -> dict[str, bool]:
    return {
        "source_packet_hash_required": True,
        "operator_value_hash_required_after_future_entry": True,
        "redaction_result_hash_required_after_future_redaction": True,
        "validation_rule_results_required": True,
        "validation_operator_or_session_ref_required": True,
        "timestamp_required": True,
        "no_secret_values_allowed": True,
        "no_credentials_allowed": True,
        "no_raw_vendor_redistribution_allowed": True,
        "no_unverified_market_values_allowed": True,
        "no_financial_signal_language_allowed": True,
        "evidence_capture_enabled_in_this_task": False,
    }


def _validation_execution_policy() -> dict[str, bool]:
    return {
        "validation_execution_enabled": False,
        "accepts_real_operator_values": False,
        "accepts_redacted_operator_values": False,
        "stores_operator_values": False,
        "stores_redacted_values": False,
        "generates_validation_results": False,
        "validation_result_persistence_enabled": False,
        "redaction_execution_enabled": False,
        "policy_scan_enabled": False,
        "draft_eligibility_recheck_enabled": False,
        "draft_generation_enabled": False,
        "ai_writer_generation_enabled": False,
        "public_postable": False,
        "dispatch_ready": False,
        "local_storage_enabled": False,
        "session_storage_enabled": False,
    }


def _validation_failure_policy() -> dict[str, bool]:
    return {
        "fail_closed_on_missing_value": True,
        "fail_closed_on_empty_value": True,
        "fail_closed_on_whitespace_only_value": True,
        "fail_closed_on_system_generated_value": True,
        "fail_closed_on_missing_evidence": True,
        "fail_closed_on_missing_redaction_result": True,
        "fail_closed_on_secret_detected": True,
        "fail_closed_on_credential_detected": True,
        "fail_closed_on_raw_vendor_redistribution_detected": True,
        "fail_closed_on_unverified_market_value_detected": True,
        "fail_closed_on_financial_signal_language_detected": True,
        "fail_closed_on_buy_sell_hold_language_detected": True,
        "fail_closed_on_price_target_language_detected": True,
        "fail_closed_on_order_fill_pnl_language_detected": True,
        "fail_closed_on_executable_content_detected": True,
        "fail_closed_on_binary_attachment_detected": True,
        "fail_closed_on_structured_payload_detected": True,
    }


def _redaction_dependency_policy() -> dict[str, Any]:
    return {
        "depends_on_local_value_redaction_rules_contract": True,
        "source_global_status_required": SOURCE_GLOBAL_STATUS_REQUIRED,
        "source_redaction_rules_schema_only_required": True,
        "requires_future_redaction_result_before_validation": True,
        "redaction_execution_enabled_in_source": False,
        "redaction_execution_enabled_in_this_task": False,
        "dependency_satisfied_for_rule_definition": True,
        "dependency_satisfied_for_validation_execution": False,
    }


def _draft_generation_policy() -> dict[str, Any]:
    return {
        "draft_generation_enabled": False,
        "ai_writer_generation_enabled": False,
        "operator_value_intake_required_before_draft_eligibility": True,
        "redaction_required_before_draft_eligibility": True,
        "validation_required_before_draft_eligibility": True,
        "draft_eligibility_recheck_enabled": False,
        "draft_generation_status": "BLOCKED_LOCAL_VALUE_VALIDATION_RULES_EXECUTION_DISABLED",
    }


def _map_item_status(source_status: str) -> str:
    if source_status == SOURCE_GLOBAL_STATUS_REQUIRED:
        return GLOBAL_LOCAL_VALUE_VALIDATION_RULES_CONTRACT_STATUS
    if source_status.startswith("BLOCKED"):
        return BLOCKED_BY_LOCAL_VALUE_REDACTION_RULES_CONTRACT
    return BLOCKED_BY_LOCAL_VALUE_REDACTION_RULES_CONTRACT


def create_local_value_validation_rules_contract(local_value_redaction_rules_contract_packet: dict[str, Any]) -> dict[str, Any]:
    """Create deterministic Local Value Validation Rules Contract from 0175CA packet."""
    source_global_status = local_value_redaction_rules_contract_packet.get("global_local_value_redaction_rules_contract_status")
    if source_global_status != SOURCE_GLOBAL_STATUS_REQUIRED:
        raise ValueError("global_local_value_redaction_rules_contract_status is not blocked with redaction execution disabled. Failing closed.")

    source_safety = local_value_redaction_rules_contract_packet.get("safety_flags", {})
    if source_safety.get("redaction_rules_schema_only") is not True:
        raise ValueError("redaction_rules_schema_only must be true in source packet. Failing closed.")

    source_items = local_value_redaction_rules_contract_packet.get("local_value_redaction_rule_items")
    if not isinstance(source_items, list):
        raise ValueError("local_value_redaction_rule_items must be a list. Failing closed.")

    validation_rule_catalog = _validation_rule_catalog()
    field_validation_rule_map = _field_validation_rule_map()
    validation_evidence_policy = _validation_evidence_policy()
    validation_execution_policy = _validation_execution_policy()
    validation_failure_policy = _validation_failure_policy()
    redaction_dependency_policy = _redaction_dependency_policy()
    blocked_reasons = BLOCKED_REASONS.copy()

    validation_items = []
    for index, item in enumerate(source_items, start=1):
        source_status = item.get("local_value_redaction_rules_contract_status", "")
        source_candidate_id = item.get("source_candidate_id", "unknown_candidate")
        validation_items.append(
            {
                "validation_rule_item_id": f"local_value_validation_rule_item_{index:02d}_{source_candidate_id}",
                "source_redaction_rule_item_id": item.get("redaction_rule_item_id", "unknown_redaction_rule_item_id"),
                "source_candidate_id": source_candidate_id,
                "relative_path": item.get("relative_path", ""),
                "evidence_role": item.get("evidence_role", "unknown"),
                "source_family": item.get("source_family", "unknown"),
                "records_count": item.get("records_count", 0),
                "contract_name": item.get("contract_name"),
                "intent_scope_label": item.get("intent_scope_label", "unknown_metadata_review"),
                "source_local_value_redaction_rules_contract_status": source_status,
                "local_value_validation_rules_contract_status": _map_item_status(source_status),
                "required_input_fields": REQUIRED_INPUT_FIELDS.copy(),
                "missing_required_input_fields": REQUIRED_INPUT_FIELDS.copy(),
                "validation_rule_catalog": [rule.copy() for rule in validation_rule_catalog],
                "field_validation_rule_map": {key: value.copy() for key, value in field_validation_rule_map.items()},
                "validation_evidence_policy": validation_evidence_policy.copy(),
                "validation_execution_policy": validation_execution_policy.copy(),
                "validation_failure_policy": validation_failure_policy.copy(),
                "redaction_dependency_policy": redaction_dependency_policy.copy(),
                "blocked_reasons": blocked_reasons.copy(),
                "allowed_next_step": ALLOWED_NEXT_STEP,
                "forbidden_current_actions": FORBIDDEN_CURRENT_ACTIONS.copy(),
                "disallowed_outputs": DISALLOWED_OUTPUTS.copy(),
            }
        )

    raw_packet = {
        "task_label": TASK_LABEL,
        "source_local_value_redaction_rules_contract_packet_hash": _source_packet_hash(local_value_redaction_rules_contract_packet),
        "source_packet_task_label": local_value_redaction_rules_contract_packet.get("task_label", "unknown"),
        "source_local_value_redaction_rule_item_count": len(source_items),
        "global_local_value_validation_rules_contract_status": GLOBAL_LOCAL_VALUE_VALIDATION_RULES_CONTRACT_STATUS,
        "required_input_fields": REQUIRED_INPUT_FIELDS.copy(),
        "missing_required_input_fields": REQUIRED_INPUT_FIELDS.copy(),
        "local_value_validation_rule_items": validation_items,
        "validation_rule_catalog": validation_rule_catalog,
        "field_validation_rule_map": field_validation_rule_map,
        "validation_evidence_policy": validation_evidence_policy,
        "validation_execution_policy": validation_execution_policy,
        "validation_failure_policy": validation_failure_policy,
        "redaction_dependency_policy": redaction_dependency_policy,
        "blocked_reasons": blocked_reasons,
        "allowed_future_validation_modes": ALLOWED_FUTURE_VALIDATION_MODES.copy(),
        "allowed_next_step": ALLOWED_NEXT_STEP,
        "forbidden_current_actions": FORBIDDEN_CURRENT_ACTIONS.copy(),
        "disallowed_outputs": DISALLOWED_OUTPUTS.copy(),
        "truth_protection_flags": TRUTH_PROTECTION_FLAGS.copy(),
        "safety_flags": SAFETY_FLAGS.copy(),
        "draft_generation_policy": _draft_generation_policy(),
        "next_recommended_task": NEXT_RECOMMENDED_TASK,
        "ledger_family": LEDGER_FAMILY,
        "hash_algorithm": HASH_ALGORITHM,
    }

    packet_serialized = json.dumps(raw_packet, sort_keys=True, separators=(",", ":"))
    packet_hash = sha256(packet_serialized.encode("utf-8")).hexdigest()
    return {"packet_hash": packet_hash, **raw_packet}


def render_runbook(packet: dict[str, Any]) -> str:
    """Render deterministic markdown runbook for Local Value Validation Rules Contract."""
    lines = [
        "# Local Value Validation Rules Contract",
        "",
        "> [!IMPORTANT]",
        "> This is a deterministic local rules schema for future operator value validation. Actual value intake, redaction execution, validation execution, validation result generation, evidence capture, persistence, draft generation, UI changes, and live/API behavior remain disabled.",
        "",
        f"- **Task Label**: `{packet['task_label']}`",
        f"- **Source Local Value Redaction Rules Contract Packet Hash**: `{packet['source_local_value_redaction_rules_contract_packet_hash']}`",
        f"- **Source Packet Task Label**: `{packet['source_packet_task_label']}`",
        f"- **Packet Hash**: `{packet['packet_hash']}`",
        f"- **Global Status**: `{packet['global_local_value_validation_rules_contract_status']}`",
        f"- **Source Local Value Redaction Rule Item Count**: `{packet['source_local_value_redaction_rule_item_count']}`",
        f"- **Local Value Validation Rule Item Count**: `{len(packet['local_value_validation_rule_items'])}`",
        f"- **Ledger Family**: `{packet['ledger_family']}`",
        "",
        "## Required Fields Still Missing",
        "",
    ]
    for field in packet["missing_required_input_fields"]:
        lines.append(f"- `{field}`")

    lines.extend(["", "## Validation Rule Catalog", "", "| Rule ID | Type | Execution Enabled | Pass Status |", "|---|---|---|---|"])
    for rule in packet["validation_rule_catalog"]:
        lines.append(
            f"| `{rule['rule_id']}` | `{rule['rule_type']}` | "
            f"`{rule['execution_enabled_in_this_task']}` | `{rule['pass_status']}` |"
        )

    lines.extend(["", "## Field Validation Rule Map", "", "| Field | Current Value Present | Rules | Acceptance Status |", "|---|---|---|---|"])
    for field, policy in packet["field_validation_rule_map"].items():
        lines.append(
            f"| `{field}` | `{policy['current_value_present']}` | "
            f"`{len(policy['applicable_rule_ids'])}` | `{policy['acceptance_status']}` |"
        )

    for section_title, key_name, left_label in [
        ("Validation Evidence Policy", "validation_evidence_policy", "Requirement"),
        ("Validation Execution Policy", "validation_execution_policy", "Policy Flag"),
        ("Validation Failure Policy", "validation_failure_policy", "Failure Class"),
        ("Redaction Dependency Policy", "redaction_dependency_policy", "Dependency Flag"),
    ]:
        lines.extend(["", f"## {section_title}", "", f"| {left_label} | State |", "|---|---|"])
        for key, value in packet[key_name].items():
            lines.append(f"| `{key}` | `{value}` |")

    lines.extend(["", "## Allowed Future Validation Modes", ""])
    for mode in packet["allowed_future_validation_modes"]:
        lines.append(f"- `{mode}` (enum only; disabled now)")

    lines.extend(["", "## Local Value Validation Rule Items", "", "| Item ID | Source Redaction Rule Item ID | Candidate ID | Status |", "|---|---|---|---|"])
    for item in packet["local_value_validation_rule_items"]:
        lines.append(
            f"| `{item['validation_rule_item_id']}` | `{item['source_redaction_rule_item_id']}` | "
            f"`{item['source_candidate_id']}` | `{item['local_value_validation_rules_contract_status']}` |"
        )

    lines.extend(["", "## Forbidden Current Actions", ""])
    for action in packet["forbidden_current_actions"]:
        lines.append(f"- `[FORBIDDEN]` {action}")

    lines.extend(["", "## Disallowed Outputs", ""])
    for out in packet["disallowed_outputs"]:
        lines.append(f"- `[FORBIDDEN]` {out}")

    lines.extend(["", "## Truth Protection Flags", "", "| Flag | State |", "|---|---|"])
    for key, value in packet["truth_protection_flags"].items():
        lines.append(f"| `{key}` | `{value}` |")

    lines.extend(["", "## Safety Flags", "", "| Flag | State |", "|---|---|"])
    for key, value in packet["safety_flags"].items():
        lines.append(f"| `{key}` | `{value}` |")

    lines.extend([
        "",
        "## Navigation",
        "",
        f"- **Allowed Next Step**: `{packet['allowed_next_step']}`",
        f"- **Next Recommended Task**: `{packet['next_recommended_task']}`",
        "",
    ])
    return "\n".join(lines)


def write_artifacts(
    local_value_redaction_rules_contract_packet_path: str | Path,
    repo_root: str | Path = ".",
) -> dict[str, Any]:
    """Write JSON packet and markdown runbook to docs/automation/0175CB/."""
    root = Path(repo_root).resolve()
    out = (root / DOC_REL_DIR).resolve()
    out.mkdir(parents=True, exist_ok=True)

    with open(local_value_redaction_rules_contract_packet_path, "r", encoding="utf-8") as f:
        source_packet = json.load(f)

    packet = create_local_value_validation_rules_contract(source_packet)
    packet_path = out / PACKET_FILENAME
    runbook_path = out / RUNBOOK_FILENAME

    packet_path.write_text(json.dumps(packet, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    runbook_path.write_text(render_runbook(packet), encoding="utf-8", newline="\n")

    return {
        "packet": packet,
        "packet_path": str(packet_path),
        "runbook_path": str(runbook_path),
    }
