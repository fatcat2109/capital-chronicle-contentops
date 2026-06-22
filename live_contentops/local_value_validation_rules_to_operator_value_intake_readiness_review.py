"""Operator Value Intake Readiness Review.

Part of TASK_CONTENTOPS_0175CC_LOCAL_VALUE_VALIDATION_RULES_TO_OPERATOR_VALUE_INTAKE_READINESS_REVIEW_V0.
Consumes the 0175CB Local Value Validation Rules Contract packet and produces a
local-only Operator Value Intake Readiness Review packet.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Any

TASK_LABEL = "TASK_CONTENTOPS_0175CC_LOCAL_VALUE_VALIDATION_RULES_TO_OPERATOR_VALUE_INTAKE_READINESS_REVIEW_V0"
LEDGER_FAMILY = "local_value_validation_rules_to_operator_value_intake_readiness_review_future"
HASH_ALGORITHM = "sha256"
DOC_REL_DIR = Path("docs") / "automation" / "0175CC"
PACKET_FILENAME = "local_value_validation_rules_to_operator_value_intake_readiness_review_packet.json"
RUNBOOK_FILENAME = "local_value_validation_rules_to_operator_value_intake_readiness_review.md"
NEXT_RECOMMENDED_TASK = "TASK_CONTENTOPS_0175CD_OPERATOR_VALUE_INTAKE_READINESS_REVIEW_TO_SUPERVISED_LOCAL_VALUE_ENTRY_STUB_V0"

SOURCE_GLOBAL_STATUS_REQUIRED = "BLOCKED_LOCAL_VALUE_VALIDATION_RULES_DEFINED_EXECUTION_DISABLED"
GLOBAL_OPERATOR_VALUE_INTAKE_READINESS_REVIEW_STATUS = "BLOCKED_OPERATOR_VALUE_INTAKE_READINESS_REVIEW_COMPLETE_INTAKE_DISABLED"
BLOCKED_BY_LOCAL_VALUE_VALIDATION_RULES_CONTRACT = "BLOCKED_BY_LOCAL_VALUE_VALIDATION_RULES_CONTRACT"
ALLOWED_NEXT_STEP = "stage_operator_value_intake_readiness_review_to_supervised_local_value_entry_stub"

REQUIRED_INPUT_FIELDS = [
    "intended_audience_lane",
    "content_purpose_category",
    "source_review_notes",
    "risk_review_notes",
    "claim_scope_boundary",
    "manual_operator_decision",
]

READINESS_PREREQUISITES = [
    "source_local_value_validation_rules_contract_present",
    "all_required_input_fields_documented",
    "all_required_input_fields_currently_missing",
    "validation_rule_catalog_present",
    "field_validation_rule_map_present",
    "validation_evidence_policy_present",
    "validation_failure_policy_present",
    "redaction_dependency_policy_present",
    "validation_execution_disabled",
    "validation_result_generation_disabled",
    "validation_result_persistence_disabled",
    "redaction_execution_disabled",
    "operator_value_intake_disabled",
    "operator_value_persistence_disabled",
    "evidence_capture_disabled",
    "draft_eligibility_recheck_disabled",
    "draft_generation_disabled",
    "live_dispatch_disabled",
]

FORBIDDEN_CURRENT_ACTIONS = [
    "actual_operator_value_intake",
    "actual_input_capture",
    "real_operator_value_acceptance",
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
    "operator_value_intake_payload",
    "operator_value_readiness_result",
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
    "operator_value_intake_readiness_truth_promoted": False,
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
    "operator_value_intake_readiness_review_schema_only": True,
}


def _source_packet_hash(packet: dict[str, Any]) -> str:
    packet_hash = packet.get("packet_hash")
    if isinstance(packet_hash, str) and packet_hash:
        return packet_hash
    serialized = json.dumps(packet, sort_keys=True, separators=(",", ":"))
    return sha256(serialized.encode("utf-8")).hexdigest()


def _review_prerequisites(packet: dict[str, Any]) -> dict[str, dict[str, Any]]:
    execution_policy = packet.get("validation_execution_policy", {})
    required_fields = packet.get("required_input_fields", [])
    missing_fields = packet.get("missing_required_input_fields", [])
    source_items = packet.get("local_value_validation_rule_items", [])

    return {
        "source_local_value_validation_rules_contract_present": {
            "satisfied": True,
            "current_status": "present",
            "required_for_future_intake": True,
        },
        "all_required_input_fields_documented": {
            "satisfied": required_fields == REQUIRED_INPUT_FIELDS,
            "current_status": "documented" if required_fields == REQUIRED_INPUT_FIELDS else "blocked_unexpected_required_fields",
            "required_fields": REQUIRED_INPUT_FIELDS.copy(),
        },
        "all_required_input_fields_currently_missing": {
            "satisfied": missing_fields == REQUIRED_INPUT_FIELDS,
            "current_status": "missing_as_required_for_schema_only_review" if missing_fields == REQUIRED_INPUT_FIELDS else "blocked_unexpected_present_fields",
            "missing_required_input_fields": REQUIRED_INPUT_FIELDS.copy(),
        },
        "validation_rule_catalog_present": {
            "satisfied": bool(packet.get("validation_rule_catalog")),
            "current_status": "present" if packet.get("validation_rule_catalog") else "missing",
            "rule_count": len(packet.get("validation_rule_catalog", [])),
        },
        "field_validation_rule_map_present": {
            "satisfied": set(packet.get("field_validation_rule_map", {})) == set(REQUIRED_INPUT_FIELDS),
            "current_status": "present" if set(packet.get("field_validation_rule_map", {})) == set(REQUIRED_INPUT_FIELDS) else "missing_or_mismatched",
            "field_count": len(packet.get("field_validation_rule_map", {})),
        },
        "validation_evidence_policy_present": {
            "satisfied": bool(packet.get("validation_evidence_policy")),
            "current_status": "present" if packet.get("validation_evidence_policy") else "missing",
        },
        "validation_failure_policy_present": {
            "satisfied": bool(packet.get("validation_failure_policy")),
            "current_status": "present" if packet.get("validation_failure_policy") else "missing",
        },
        "redaction_dependency_policy_present": {
            "satisfied": bool(packet.get("redaction_dependency_policy")),
            "current_status": "present" if packet.get("redaction_dependency_policy") else "missing",
        },
        "validation_execution_disabled": {
            "satisfied": execution_policy.get("validation_execution_enabled") is False,
            "current_status": "disabled",
        },
        "validation_result_generation_disabled": {
            "satisfied": execution_policy.get("generates_validation_results") is False,
            "current_status": "disabled",
        },
        "validation_result_persistence_disabled": {
            "satisfied": execution_policy.get("validation_result_persistence_enabled") is False,
            "current_status": "disabled",
        },
        "redaction_execution_disabled": {
            "satisfied": execution_policy.get("redaction_execution_enabled") is False,
            "current_status": "disabled",
        },
        "operator_value_intake_disabled": {
            "satisfied": execution_policy.get("accepts_real_operator_values") is False,
            "current_status": "disabled",
        },
        "operator_value_persistence_disabled": {
            "satisfied": execution_policy.get("stores_operator_values") is False,
            "current_status": "disabled",
        },
        "evidence_capture_disabled": {
            "satisfied": packet.get("validation_evidence_policy", {}).get("evidence_capture_enabled_in_this_task") is False,
            "current_status": "disabled",
        },
        "draft_eligibility_recheck_disabled": {
            "satisfied": execution_policy.get("draft_eligibility_recheck_enabled") is False,
            "current_status": "disabled",
        },
        "draft_generation_disabled": {
            "satisfied": execution_policy.get("draft_generation_enabled") is False,
            "current_status": "disabled",
        },
        "live_dispatch_disabled": {
            "satisfied": execution_policy.get("dispatch_ready") is False and execution_policy.get("public_postable") is False,
            "current_status": "disabled",
            "reviewed_item_count": len(source_items),
        },
    }


def _readiness_execution_policy() -> dict[str, bool]:
    return {
        "operator_value_intake_readiness_review_completed": True,
        "operator_value_intake_enabled": False,
        "accepts_real_operator_values": False,
        "captures_operator_values": False,
        "stores_operator_values": False,
        "evidence_capture_enabled": False,
        "validation_execution_enabled": False,
        "validation_result_generation_enabled": False,
        "validation_result_persistence_enabled": False,
        "redaction_execution_enabled": False,
        "policy_scan_enabled": False,
        "redacted_value_generation_enabled": False,
        "redaction_result_persistence_enabled": False,
        "draft_eligibility_recheck_enabled": False,
        "draft_generation_enabled": False,
        "ai_writer_generation_enabled": False,
        "public_postable": False,
        "dispatch_ready": False,
        "local_storage_enabled": False,
        "session_storage_enabled": False,
    }


def _future_intake_boundary() -> dict[str, Any]:
    return {
        "review_only_now": True,
        "future_intake_requires_new_task": True,
        "future_intake_requires_supervised_local_value_entry_stub": True,
        "future_intake_requires_operator_supplied_values": True,
        "future_intake_requires_redaction_before_validation": True,
        "future_intake_requires_validation_before_acceptance": True,
        "future_intake_requires_evidence_before_persistence": True,
        "allowed_next_step": ALLOWED_NEXT_STEP,
    }


def _map_item_status(source_status: str) -> str:
    if source_status == SOURCE_GLOBAL_STATUS_REQUIRED:
        return GLOBAL_OPERATOR_VALUE_INTAKE_READINESS_REVIEW_STATUS
    if source_status.startswith("BLOCKED"):
        return BLOCKED_BY_LOCAL_VALUE_VALIDATION_RULES_CONTRACT
    return BLOCKED_BY_LOCAL_VALUE_VALIDATION_RULES_CONTRACT


def _validate_source_packet(packet: dict[str, Any]) -> None:
    source_global_status = packet.get("global_local_value_validation_rules_contract_status")
    if source_global_status != SOURCE_GLOBAL_STATUS_REQUIRED:
        raise ValueError("global_local_value_validation_rules_contract_status is not blocked with validation execution disabled. Failing closed.")

    source_safety = packet.get("safety_flags", {})
    if source_safety.get("validation_rules_schema_only") is not True:
        raise ValueError("validation_rules_schema_only must be true in source packet. Failing closed.")

    if source_safety.get("operator_value_intake_enabled") is not False:
        raise ValueError("operator_value_intake_enabled must be false in source packet. Failing closed.")

    if source_safety.get("validation_execution_enabled") is not False:
        raise ValueError("validation_execution_enabled must be false in source packet. Failing closed.")

    source_items = packet.get("local_value_validation_rule_items")
    if not isinstance(source_items, list):
        raise ValueError("local_value_validation_rule_items must be a list. Failing closed.")

    if packet.get("required_input_fields") != REQUIRED_INPUT_FIELDS:
        raise ValueError("required_input_fields do not match expected operator value intake fields. Failing closed.")

    if packet.get("missing_required_input_fields") != REQUIRED_INPUT_FIELDS:
        raise ValueError("missing_required_input_fields must include all expected operator value intake fields. Failing closed.")


def create_operator_value_intake_readiness_review(local_value_validation_rules_contract_packet: dict[str, Any]) -> dict[str, Any]:
    """Create deterministic Operator Value Intake Readiness Review from 0175CB packet."""
    _validate_source_packet(local_value_validation_rules_contract_packet)

    source_items = local_value_validation_rules_contract_packet["local_value_validation_rule_items"]
    prerequisite_review = _review_prerequisites(local_value_validation_rules_contract_packet)
    readiness_execution_policy = _readiness_execution_policy()
    future_intake_boundary = _future_intake_boundary()
    all_prerequisites_satisfied = all(review["satisfied"] is True for review in prerequisite_review.values())

    readiness_items = []
    for index, item in enumerate(source_items, start=1):
        source_status = item.get("local_value_validation_rules_contract_status", "")
        source_candidate_id = item.get("source_candidate_id", "unknown_candidate")
        readiness_items.append(
            {
                "readiness_review_item_id": f"operator_value_intake_readiness_review_item_{index:02d}_{source_candidate_id}",
                "source_validation_rule_item_id": item.get("validation_rule_item_id", "unknown_validation_rule_item_id"),
                "source_candidate_id": source_candidate_id,
                "relative_path": item.get("relative_path", ""),
                "evidence_role": item.get("evidence_role", "unknown"),
                "source_family": item.get("source_family", "unknown"),
                "records_count": item.get("records_count", 0),
                "contract_name": item.get("contract_name"),
                "intent_scope_label": item.get("intent_scope_label", "unknown_metadata_review"),
                "source_local_value_validation_rules_contract_status": source_status,
                "operator_value_intake_readiness_review_status": _map_item_status(source_status),
                "required_input_fields": REQUIRED_INPUT_FIELDS.copy(),
                "missing_required_input_fields": REQUIRED_INPUT_FIELDS.copy(),
                "readiness_prerequisites": READINESS_PREREQUISITES.copy(),
                "prerequisite_review": {key: value.copy() for key, value in prerequisite_review.items()},
                "readiness_execution_policy": readiness_execution_policy.copy(),
                "future_intake_boundary": future_intake_boundary.copy(),
                "allowed_next_step": ALLOWED_NEXT_STEP,
                "forbidden_current_actions": FORBIDDEN_CURRENT_ACTIONS.copy(),
                "disallowed_outputs": DISALLOWED_OUTPUTS.copy(),
            }
        )

    raw_packet = {
        "task_label": TASK_LABEL,
        "source_local_value_validation_rules_contract_packet_hash": _source_packet_hash(local_value_validation_rules_contract_packet),
        "source_packet_task_label": local_value_validation_rules_contract_packet.get("task_label", "unknown"),
        "source_local_value_validation_rule_item_count": len(source_items),
        "global_operator_value_intake_readiness_review_status": GLOBAL_OPERATOR_VALUE_INTAKE_READINESS_REVIEW_STATUS,
        "all_prerequisites_satisfied_for_future_intake_design": all_prerequisites_satisfied,
        "operator_value_intake_enabled": False,
        "operator_value_capture_enabled": False,
        "operator_value_persistence_enabled": False,
        "required_input_fields": REQUIRED_INPUT_FIELDS.copy(),
        "missing_required_input_fields": REQUIRED_INPUT_FIELDS.copy(),
        "operator_value_intake_readiness_review_items": readiness_items,
        "readiness_prerequisites": READINESS_PREREQUISITES.copy(),
        "prerequisite_review": prerequisite_review,
        "readiness_execution_policy": readiness_execution_policy,
        "future_intake_boundary": future_intake_boundary,
        "allowed_next_step": ALLOWED_NEXT_STEP,
        "forbidden_current_actions": FORBIDDEN_CURRENT_ACTIONS.copy(),
        "disallowed_outputs": DISALLOWED_OUTPUTS.copy(),
        "truth_protection_flags": TRUTH_PROTECTION_FLAGS.copy(),
        "safety_flags": SAFETY_FLAGS.copy(),
        "next_recommended_task": NEXT_RECOMMENDED_TASK,
        "ledger_family": LEDGER_FAMILY,
        "hash_algorithm": HASH_ALGORITHM,
    }

    packet_serialized = json.dumps(raw_packet, sort_keys=True, separators=(",", ":"))
    packet_hash = sha256(packet_serialized.encode("utf-8")).hexdigest()
    return {"packet_hash": packet_hash, **raw_packet}


def render_runbook(packet: dict[str, Any]) -> str:
    """Render deterministic markdown runbook for Operator Value Intake Readiness Review."""
    lines = [
        "# Operator Value Intake Readiness Review",
        "",
        "> [!IMPORTANT]",
        "> This is a deterministic local readiness review for future operator value intake. Actual value intake, editable UI, evidence capture, validation execution, redaction execution, persistence, draft eligibility recheck, draft generation, AI Writer generation, live dispatch, and API/provider/platform behavior remain disabled.",
        "",
        f"- **Task Label**: `{packet['task_label']}`",
        f"- **Source Local Value Validation Rules Contract Packet Hash**: `{packet['source_local_value_validation_rules_contract_packet_hash']}`",
        f"- **Source Packet Task Label**: `{packet['source_packet_task_label']}`",
        f"- **Packet Hash**: `{packet['packet_hash']}`",
        f"- **Global Status**: `{packet['global_operator_value_intake_readiness_review_status']}`",
        f"- **Source Local Value Validation Rule Item Count**: `{packet['source_local_value_validation_rule_item_count']}`",
        f"- **Readiness Review Item Count**: `{len(packet['operator_value_intake_readiness_review_items'])}`",
        f"- **Ledger Family**: `{packet['ledger_family']}`",
        "",
        "## Required Fields Still Missing",
        "",
    ]
    for field in packet["missing_required_input_fields"]:
        lines.append(f"- `{field}`")

    lines.extend(["", "## Readiness Prerequisites", "", "| Prerequisite | Satisfied | Status |", "|---|---|---|"])
    for prereq in packet["readiness_prerequisites"]:
        review = packet["prerequisite_review"][prereq]
        lines.append(f"| `{prereq}` | `{review['satisfied']}` | `{review['current_status']}` |")

    lines.extend(["", "## Readiness Execution Policy", "", "| Policy Flag | State |", "|---|---|"])
    for key, value in packet["readiness_execution_policy"].items():
        lines.append(f"| `{key}` | `{value}` |")

    lines.extend(["", "## Future Intake Boundary", "", "| Boundary | State |", "|---|---|"])
    for key, value in packet["future_intake_boundary"].items():
        lines.append(f"| `{key}` | `{value}` |")

    lines.extend(["", "## Operator Value Intake Readiness Review Items", "", "| Item ID | Source Validation Rule Item ID | Candidate ID | Status |", "|---|---|---|---|"])
    for item in packet["operator_value_intake_readiness_review_items"]:
        lines.append(
            f"| `{item['readiness_review_item_id']}` | `{item['source_validation_rule_item_id']}` | "
            f"`{item['source_candidate_id']}` | `{item['operator_value_intake_readiness_review_status']}` |"
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

    lines.extend(["", "## Navigation", "", f"- **Allowed Next Step**: `{packet['allowed_next_step']}`", f"- **Next Recommended Task**: `{packet['next_recommended_task']}`", ""])
    return "\n".join(lines)


def write_artifacts(local_value_validation_rules_contract_packet_path: str | Path, repo_root: str | Path = ".") -> dict[str, Any]:
    """Write JSON packet and markdown runbook to docs/automation/0175CC/."""
    root = Path(repo_root).resolve()
    out = (root / DOC_REL_DIR).resolve()
    out.mkdir(parents=True, exist_ok=True)

    with open(local_value_validation_rules_contract_packet_path, "r", encoding="utf-8") as f:
        source_packet = json.load(f)

    packet = create_operator_value_intake_readiness_review(source_packet)
    packet_path = out / PACKET_FILENAME
    runbook_path = out / RUNBOOK_FILENAME

    packet_path.write_text(json.dumps(packet, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    runbook_path.write_text(render_runbook(packet), encoding="utf-8", newline="\n")

    return {"packet": packet, "packet_path": str(packet_path), "runbook_path": str(runbook_path)}
