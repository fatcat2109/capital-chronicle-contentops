"""Supervised Manual Input Dry Run Precheck to Operator Value Intake Policy.

Part of TASK_CONTENTOPS_0175BZ_SUPERVISED_MANUAL_INPUT_DRY_RUN_PRECHECK_TO_OPERATOR_VALUE_INTAKE_POLICY_V0.
Consumes the 0175BY Supervised Manual Input Dry Run Precheck packet and produces a
local-only Operator Value Intake Policy packet.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Any

TASK_LABEL = "TASK_CONTENTOPS_0175BZ_SUPERVISED_MANUAL_INPUT_DRY_RUN_PRECHECK_TO_OPERATOR_VALUE_INTAKE_POLICY_V0"
LEDGER_FAMILY = "supervised_manual_input_dry_run_precheck_to_operator_value_intake_policy_future"
HASH_ALGORITHM = "sha256"
DOC_REL_DIR = Path("docs") / "automation" / "0175BZ"
PACKET_FILENAME = "supervised_manual_input_dry_run_precheck_to_operator_value_intake_policy_packet.json"
RUNBOOK_FILENAME = "supervised_manual_input_dry_run_precheck_to_operator_value_intake_policy.md"
NEXT_RECOMMENDED_TASK = "TASK_CONTENTOPS_0175CA_OPERATOR_VALUE_INTAKE_POLICY_TO_LOCAL_VALUE_REDACTION_RULES_CONTRACT_V0"

REQUIRED_INPUT_FIELDS = [
    "intended_audience_lane",
    "content_purpose_category",
    "source_review_notes",
    "risk_review_notes",
    "claim_scope_boundary",
    "manual_operator_decision",
]

GLOBAL_OPERATOR_VALUE_INTAKE_POLICY_STATUS = "BLOCKED_OPERATOR_VALUE_INTAKE_POLICY_DEFINED_INTAKE_DISABLED"
SOURCE_DRY_RUN_STATUS_REQUIRED = "BLOCKED_MANUAL_INPUT_DRY_RUN_PENDING_REAL_OPERATOR_VALUES"
BLOCKED_BY_DRY_RUN_STATUS = "BLOCKED_BY_MANUAL_INPUT_DRY_RUN_PRECHECK"
SOURCE_GLOBAL_STATUS_REQUIRED = "BLOCKED_MANUAL_INPUT_DRY_RUN_PENDING_REAL_OPERATOR_VALUES"
ALLOWED_NEXT_STEP = "stage_operator_value_intake_policy_to_local_value_redaction_rules_contract"

ALLOWED_FUTURE_INTAKE_MODES = [
    "supervised_manual_operator_entry",
    "imported_operator_review_packet",
    "deferred_human_review_session",
]

BLOCKED_REASONS = [
    "operator_value_intake_policy_only_no_values_accepted",
    "actual_operator_value_intake_disabled",
    "real_operator_values_absent",
    "evidence_capture_disabled",
    "redaction_execution_disabled",
    "validation_execution_disabled",
    "persistence_disabled",
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
    "redaction_execution",
    "redacted_value_generation",
    "validation_result_generation",
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
    "accepted_operator_value",
    "validation_result_value",
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
    "validation_result_truth_promoted": False,
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
    "evidence_capture_enabled": False,
    "real_operator_value_acceptance_enabled": False,
    "operator_value_intake_enabled": False,
    "redacted_value_generation_enabled": False,
    "validation_result_generation_enabled": False,
    "local_storage_write_enabled": False,
    "session_storage_write_enabled": False,
    "policy_schema_only": True,
}


def _source_packet_hash(packet: dict[str, Any]) -> str:
    packet_hash = packet.get("packet_hash")
    if isinstance(packet_hash, str) and packet_hash:
        return packet_hash
    serialized = json.dumps(packet, sort_keys=True, separators=(",", ":"))
    return sha256(serialized.encode("utf-8")).hexdigest()


def _value_intake_field_policy() -> dict[str, dict[str, Any]]:
    return {
        field_name: {
            "intake_allowed_in_future": True,
            "intake_enabled_in_this_task": False,
            "current_value": None,
            "current_value_present": False,
            "placeholder_value": "PENDING_OPERATOR_INPUT",
            "expected_value_owner": "human_operator",
            "system_generated_value_forbidden": True,
            "value_required_for_future_capture": True,
            "evidence_required_before_acceptance": True,
            "redaction_required_before_acceptance": True,
            "validation_required_before_acceptance": True,
            "persistence_enabled_in_this_task": False,
            "acceptance_status": "BLOCKED_INTAKE_DISABLED",
            "blocking_reason": "operator_value_intake_policy_only_no_values_accepted",
        }
        for field_name in REQUIRED_INPUT_FIELDS
    }


def _value_shape_policy() -> dict[str, dict[str, Any]]:
    return {
        field_name: {
            "allowed_value_type": "non_empty_string",
            "max_length_policy_label": "FUTURE_POLICY_BOUNDARY_REQUIRED",
            "empty_value_allowed": False,
            "whitespace_only_allowed": False,
            "structured_payload_allowed": False,
            "binary_attachment_allowed": False,
            "executable_content_allowed": False,
            "url_required": False,
            "numeric_value_required": False,
            "market_value_allowed": False,
            "validation_enabled_in_this_task": False,
        }
        for field_name in REQUIRED_INPUT_FIELDS
    }


def _prohibited_value_content_policy() -> dict[str, dict[str, bool]]:
    return {
        field_name: {
            "secrets_forbidden": True,
            "credentials_forbidden": True,
            "raw_vendor_redistribution_forbidden": True,
            "unverified_market_values_forbidden": True,
            "financial_signal_language_forbidden": True,
            "buy_sell_hold_language_forbidden": True,
            "price_target_language_forbidden": True,
            "order_fill_pnl_language_forbidden": True,
            "external_link_required_for_acceptance": False,
            "policy_scan_enabled_in_this_task": False,
        }
        for field_name in REQUIRED_INPUT_FIELDS
    }


def _intake_evidence_policy() -> dict[str, bool]:
    return {
        "operator_identity_or_session_ref_required": True,
        "timestamp_required": True,
        "source_packet_hash_required": True,
        "manual_review_notes_required": True,
        "redaction_check_required": True,
        "validation_check_required": True,
        "no_secret_values_attestation_required": True,
        "no_raw_vendor_redistribution_attestation_required": True,
        "no_unverified_market_values_attestation_required": True,
        "no_financial_signal_language_attestation_required": True,
        "evidence_capture_enabled_in_this_task": False,
    }


def _intake_redaction_dependency_policy() -> dict[str, Any]:
    return {
        "redaction_required_before_acceptance": True,
        "redaction_execution_enabled_in_this_task": False,
        "redacted_value_generation_enabled": False,
        "requires_real_operator_values": True,
        "dependency_status": "BLOCKED_PENDING_OPERATOR_VALUES",
    }


def _intake_validation_dependency_policy() -> dict[str, Any]:
    return {
        "validation_required_before_acceptance": True,
        "validation_execution_enabled_in_this_task": False,
        "validation_result_generation_enabled": False,
        "requires_real_operator_values": True,
        "dependency_status": "BLOCKED_PENDING_OPERATOR_VALUES",
    }


def _intake_execution_policy() -> dict[str, bool]:
    return {
        "operator_value_intake_enabled": False,
        "accepts_real_operator_values": False,
        "stores_operator_values": False,
        "evidence_capture_enabled": False,
        "validation_execution_enabled": False,
        "redaction_execution_enabled": False,
        "redacted_value_generation_enabled": False,
        "validation_result_generation_enabled": False,
        "draft_eligibility_recheck_enabled": False,
        "draft_generation_enabled": False,
        "ai_writer_generation_enabled": False,
        "public_postable": False,
        "dispatch_ready": False,
        "local_storage_enabled": False,
        "session_storage_enabled": False,
    }


def _draft_generation_policy() -> dict[str, Any]:
    return {
        "draft_generation_enabled": False,
        "ai_writer_generation_enabled": False,
        "operator_value_intake_required_before_draft_eligibility": True,
        "redaction_required_before_draft_eligibility": True,
        "validation_required_before_draft_eligibility": True,
        "draft_eligibility_recheck_enabled": False,
        "draft_generation_status": "BLOCKED_OPERATOR_VALUE_INTAKE_DISABLED",
    }


def _map_item_status(source_status: str) -> str:
    if source_status == SOURCE_DRY_RUN_STATUS_REQUIRED:
        return GLOBAL_OPERATOR_VALUE_INTAKE_POLICY_STATUS
    if source_status.startswith("BLOCKED"):
        return BLOCKED_BY_DRY_RUN_STATUS
    return BLOCKED_BY_DRY_RUN_STATUS


def create_operator_value_intake_policy(manual_input_dry_run_precheck_packet: dict[str, Any]) -> dict[str, Any]:
    """Create deterministic Operator Value Intake Policy from 0175BY packet."""
    source_global_status = manual_input_dry_run_precheck_packet.get("global_manual_input_dry_run_status")
    if source_global_status != SOURCE_GLOBAL_STATUS_REQUIRED:
        raise ValueError("global_manual_input_dry_run_status is not blocked pending real operator values. Failing closed.")

    source_items = manual_input_dry_run_precheck_packet.get("dry_run_items")
    if not isinstance(source_items, list):
        raise ValueError("dry_run_items must be a list. Failing closed.")

    value_intake_field_policy = _value_intake_field_policy()
    value_shape_policy = _value_shape_policy()
    prohibited_value_content_policy = _prohibited_value_content_policy()
    intake_evidence_policy = _intake_evidence_policy()
    intake_redaction_dependency_policy = _intake_redaction_dependency_policy()
    intake_validation_dependency_policy = _intake_validation_dependency_policy()
    intake_execution_policy = _intake_execution_policy()
    blocked_reasons = BLOCKED_REASONS.copy()

    policy_items = []
    for index, item in enumerate(source_items, start=1):
        source_status = item.get("dry_run_status") or item.get("supervised_manual_input_dry_run_precheck_status", "")
        source_candidate_id = item.get("source_candidate_id", "unknown_candidate")
        policy_items.append(
            {
                "intake_policy_item_id": f"operator_value_intake_policy_item_{index:02d}_{source_candidate_id}",
                "source_dry_run_item_id": item.get("dry_run_item_id", item.get("dry_run_precheck_item_id", "unknown_dry_run_item_id")),
                "source_candidate_id": source_candidate_id,
                "relative_path": item.get("relative_path", ""),
                "evidence_role": item.get("evidence_role", "unknown"),
                "source_family": item.get("source_family", "unknown"),
                "records_count": item.get("records_count", 0),
                "contract_name": item.get("contract_name"),
                "intent_scope_label": item.get("intent_scope_label", "unknown_metadata_review"),
                "source_manual_input_dry_run_status": source_status,
                "operator_value_intake_policy_status": _map_item_status(source_status),
                "required_input_fields": REQUIRED_INPUT_FIELDS.copy(),
                "missing_required_input_fields": REQUIRED_INPUT_FIELDS.copy(),
                "value_intake_field_policy": value_intake_field_policy.copy(),
                "value_shape_policy": value_shape_policy.copy(),
                "prohibited_value_content_policy": prohibited_value_content_policy.copy(),
                "intake_evidence_policy": intake_evidence_policy.copy(),
                "intake_redaction_dependency_policy": intake_redaction_dependency_policy.copy(),
                "intake_validation_dependency_policy": intake_validation_dependency_policy.copy(),
                "intake_execution_policy": intake_execution_policy.copy(),
                "blocked_reasons": blocked_reasons.copy(),
                "allowed_next_step": ALLOWED_NEXT_STEP,
                "forbidden_current_actions": FORBIDDEN_CURRENT_ACTIONS.copy(),
                "disallowed_outputs": DISALLOWED_OUTPUTS.copy(),
            }
        )

    raw_packet = {
        "task_label": TASK_LABEL,
        "source_manual_input_dry_run_precheck_packet_hash": _source_packet_hash(manual_input_dry_run_precheck_packet),
        "source_packet_task_label": manual_input_dry_run_precheck_packet.get("task_label", "unknown"),
        "source_dry_run_item_count": len(source_items),
        "global_operator_value_intake_policy_status": GLOBAL_OPERATOR_VALUE_INTAKE_POLICY_STATUS,
        "required_input_fields": REQUIRED_INPUT_FIELDS.copy(),
        "missing_required_input_fields": REQUIRED_INPUT_FIELDS.copy(),
        "operator_value_intake_policy_items": policy_items,
        "value_intake_field_policy": value_intake_field_policy,
        "value_shape_policy": value_shape_policy,
        "prohibited_value_content_policy": prohibited_value_content_policy,
        "intake_evidence_policy": intake_evidence_policy,
        "intake_redaction_dependency_policy": intake_redaction_dependency_policy,
        "intake_validation_dependency_policy": intake_validation_dependency_policy,
        "intake_execution_policy": intake_execution_policy,
        "blocked_reasons": blocked_reasons,
        "allowed_future_intake_modes": ALLOWED_FUTURE_INTAKE_MODES.copy(),
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
    """Render deterministic markdown runbook for Operator Value Intake Policy."""
    lines = [
        "# Operator Value Intake Policy",
        "",
        "> [!IMPORTANT]",
        "> This is a deterministic local policy schema for future operator-owned value intake. Actual operator input capture, editable UI, evidence capture, persistence, validation, redaction, draft generation, and live/API behavior remain disabled.",
        "",
        f"- **Task Label**: `{packet['task_label']}`",
        f"- **Source Manual Input Dry Run Precheck Packet Hash**: `{packet['source_manual_input_dry_run_precheck_packet_hash']}`",
        f"- **Source Packet Task Label**: `{packet['source_packet_task_label']}`",
        f"- **Packet Hash**: `{packet['packet_hash']}`",
        f"- **Global Operator Value Intake Policy Status**: `{packet['global_operator_value_intake_policy_status']}`",
        f"- **Source Dry Run Item Count**: `{packet['source_dry_run_item_count']}`",
        f"- **Operator Value Intake Policy Item Count**: `{len(packet['operator_value_intake_policy_items'])}`",
        f"- **Ledger Family**: `{packet['ledger_family']}`",
        "",
        "## Required Fields Still Missing",
        "",
    ]
    for field in packet["missing_required_input_fields"]:
        lines.append(f"- `{field}`")

    lines.extend(["", "## Allowed Future Intake Modes", ""])
    for mode in packet["allowed_future_intake_modes"]:
        lines.append(f"- `{mode}` (enum only; disabled now)")

    lines.extend(["", "## Intake Execution Policy", "", "| Policy Flag | State |", "|---|---|"])
    for key, value in packet["intake_execution_policy"].items():
        lines.append(f"| `{key}` | `{value}` |")

    lines.extend(["", "## Field Intake Policy", "", "| Field | Future Allowed | Enabled Now | Acceptance Status |", "|---|---|---|---|"])
    for field, policy in packet["value_intake_field_policy"].items():
        lines.append(
            f"| `{field}` | `{policy['intake_allowed_in_future']}` | "
            f"`{policy['intake_enabled_in_this_task']}` | `{policy['acceptance_status']}` |"
        )

    lines.extend(["", "## Shape Policy", "", "| Field | Type | Empty | Structured | Binary | Executable | Market Value |", "|---|---|---|---|---|---|---|"])
    for field, policy in packet["value_shape_policy"].items():
        lines.append(
            f"| `{field}` | `{policy['allowed_value_type']}` | `{policy['empty_value_allowed']}` | "
            f"`{policy['structured_payload_allowed']}` | `{policy['binary_attachment_allowed']}` | "
            f"`{policy['executable_content_allowed']}` | `{policy['market_value_allowed']}` |"
        )

    lines.extend(["", "## Prohibited Content Policy", "", "| Field | Secrets | Credentials | Raw Vendor | Unverified Market | Financial Language |", "|---|---|---|---|---|---|"])
    for field, policy in packet["prohibited_value_content_policy"].items():
        lines.append(
            f"| `{field}` | `{policy['secrets_forbidden']}` | `{policy['credentials_forbidden']}` | "
            f"`{policy['raw_vendor_redistribution_forbidden']}` | `{policy['unverified_market_values_forbidden']}` | "
            f"`{policy['financial_signal_language_forbidden']}` |"
        )

    lines.extend(["", "## Intake Evidence Policy", "", "| Requirement | State |", "|---|---|"])
    for key, value in packet["intake_evidence_policy"].items():
        lines.append(f"| `{key}` | `{value}` |")

    lines.extend(["", "## Dependency Policies", "", "### Redaction", ""])
    for key, value in packet["intake_redaction_dependency_policy"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "### Validation", ""])
    for key, value in packet["intake_validation_dependency_policy"].items():
        lines.append(f"- `{key}`: `{value}`")

    lines.extend(["", "## Operator Value Intake Policy Items", "", "| Intake Policy Item ID | Source Dry Run Item ID | Candidate ID | Status |", "|---|---|---|---|"])
    for item in packet["operator_value_intake_policy_items"]:
        lines.append(
            f"| `{item['intake_policy_item_id']}` | `{item['source_dry_run_item_id']}` | "
            f"`{item['source_candidate_id']}` | `{item['operator_value_intake_policy_status']}` |"
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
    manual_input_dry_run_precheck_packet_path: str | Path,
    repo_root: str | Path = ".",
) -> dict[str, Any]:
    """Write JSON packet and markdown runbook to docs/automation/0175BZ/."""
    root = Path(repo_root).resolve()
    out = (root / DOC_REL_DIR).resolve()
    out.mkdir(parents=True, exist_ok=True)

    with open(manual_input_dry_run_precheck_packet_path, "r", encoding="utf-8") as f:
        source_packet = json.load(f)

    packet = create_operator_value_intake_policy(source_packet)
    packet_path = out / PACKET_FILENAME
    runbook_path = out / RUNBOOK_FILENAME

    packet_path.write_text(json.dumps(packet, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    runbook_path.write_text(render_runbook(packet), encoding="utf-8", newline="\n")

    return {
        "packet": packet,
        "packet_path": str(packet_path),
        "runbook_path": str(runbook_path),
    }
