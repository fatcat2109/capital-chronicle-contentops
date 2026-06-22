"""Draft Eligibility Gate to Supervised Input Resolution Plan.

Part of TASK_CONTENTOPS_0175BV_DRAFT_ELIGIBILITY_GATE_TO_SUPERVISED_INPUT_RESOLUTION_PLAN_V0.
Consumes the 0175BS Draft Eligibility Gate Precheck packet and produces a local-only,
Supervised Input Resolution Plan packet.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Any

TASK_LABEL = "TASK_CONTENTOPS_0175BV_DRAFT_ELIGIBILITY_GATE_TO_SUPERVISED_INPUT_RESOLUTION_PLAN_V0"
LEDGER_FAMILY = "draft_eligibility_gate_to_supervised_input_resolution_plan_future"
HASH_ALGORITHM = "sha256"
DOC_REL_DIR = Path("docs") / "automation" / "0175BV"
PACKET_FILENAME = "draft_eligibility_gate_to_supervised_input_resolution_plan_packet.json"
RUNBOOK_FILENAME = "draft_eligibility_gate_to_supervised_input_resolution_plan.md"
NEXT_RECOMMENDED_TASK = "TASK_CONTENTOPS_0175BW_SUPERVISED_INPUT_RESOLUTION_PLAN_TO_LOCAL_REDACTION_AND_VALIDATION_PRECHECK_V0"

REQUIRED_INPUT_FIELDS = [
    "intended_audience_lane",
    "content_purpose_category",
    "source_review_notes",
    "risk_review_notes",
    "claim_scope_boundary",
    "manual_operator_decision",
]

ALLOWED_FUTURE_RESOLUTION_METHODS = [
    "supervised_manual_operator_entry",
    "imported_operator_review_packet",
    "deferred_human_review_session",
]

VALIDATION_REQUIREMENTS = [
    "operator_value_present",
    "operator_value_non_empty",
    "operator_value_not_system_generated",
    "operator_review_evidence_attached",
    "claim_scope_boundary_present",
    "risk_review_notes_present",
    "manual_operator_decision_present",
]

EVIDENCE_REQUIREMENTS = {
    "operator_identity_or_session_ref_required": True,
    "timestamp_required": True,
    "source_packet_hash_required": True,
    "manual_review_notes_required": True,
    "redaction_check_required": True,
    "no_secret_values_allowed": True,
    "no_raw_vendor_redistribution_allowed": True,
}

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
    "persistence_write",
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
]

TRUTH_PROTECTION_FLAGS = {
    "dqr_cleared_by_contentops": False,
    "readiness_cleared_by_contentops": False,
    "current_truth_promoted": False,
    "numeric_truth_promoted": False,
    "market_data_promoted": False,
    "draft_truth_promoted": False,
    "operator_input_truth_promoted": False,
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
    "supervised_input_resolution_enabled": False,
}


def _source_packet_hash(packet: dict[str, Any]) -> str:
    packet_hash = packet.get("packet_hash")
    if isinstance(packet_hash, str) and packet_hash:
        return packet_hash
    serialized = json.dumps(packet, sort_keys=True, separators=(",", ":"))
    return sha256(serialized.encode("utf-8")).hexdigest()


def _field_resolution_plan() -> dict[str, dict[str, Any]]:
    return {
        field: {
            "required": True,
            "current_value": None,
            "placeholder_value": "PENDING_OPERATOR_INPUT",
            "resolution_status": "PENDING_SUPERVISED_OPERATOR_RESOLUTION",
            "resolution_enabled_in_this_task": False,
            "editable_in_this_task": False,
            "generated_by_system": False,
            "persistence_enabled": False,
            "validation_enabled": False,
            "future_resolution_required": True,
            "allowed_future_resolution_methods": ALLOWED_FUTURE_RESOLUTION_METHODS.copy(),
            "evidence_required": True,
            "evidence_requirement_label": "OPERATOR_PROVIDED_REVIEW_EVIDENCE_REQUIRED",
            "blocking_reason": "supervised_input_resolution_required_before_draft_eligibility",
        }
        for field in REQUIRED_INPUT_FIELDS
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
    if source_status == "BLOCKED_DRAFT_ELIGIBILITY_SUPERVISED_INPUT_REQUIRED":
        return "BLOCKED_SUPERVISED_INPUT_RESOLUTION_REQUIRED"
    if source_status.startswith("BLOCKED"):
        return "BLOCKED_BY_DRAFT_ELIGIBILITY_GATE_PRECHECK"
    return "BLOCKED_BY_DRAFT_ELIGIBILITY_GATE_PRECHECK"


def create_supervised_input_resolution_plan(
    draft_eligibility_gate_precheck_packet: dict[str, Any],
    next_recommended_task: str | None = None,
) -> dict[str, Any]:
    """Transition draft eligibility gate precheck packet into a Supervised Input Resolution Plan packet."""
    if not draft_eligibility_gate_precheck_packet or not isinstance(draft_eligibility_gate_precheck_packet, dict):
        raise ValueError("Draft eligibility precheck packet is missing or malformed. Failing closed.")

    global_status = draft_eligibility_gate_precheck_packet.get("global_draft_eligibility_status")
    if global_status != "BLOCKED_DRAFT_ELIGIBILITY_SUPERVISED_INPUT_REQUIRED":
        raise ValueError(f"Invalid global draft eligibility status '{global_status}'. Failing closed.")

    source_items = draft_eligibility_gate_precheck_packet.get("draft_eligibility_items", [])
    if not isinstance(source_items, list):
        raise ValueError("draft_eligibility_items must be a list. Failing closed.")

    supervised_input_resolution_items = []
    blocked_reasons = [
        "supervised_input_resolution_required",
        "missing_required_operator_inputs",
        "draft_eligibility_blocked_by_precheck",
    ]

    field_res_plan = _field_resolution_plan()

    for index, item in enumerate(source_items, start=1):
        source_status = item.get("draft_eligibility_status", "")
        source_candidate_id = item.get("source_candidate_id", "unknown_candidate")
        
        resolution_item = {
            "resolution_item_id": f"resolution_item_{index:02d}_{source_candidate_id}",
            "source_draft_eligibility_item_id": item.get("draft_eligibility_item_id", "unknown_item_id"),
            "source_candidate_id": source_candidate_id,
            "relative_path": item.get("relative_path", ""),
            "evidence_role": item.get("evidence_role", "unknown"),
            "source_family": item.get("source_family", "unknown"),
            "records_count": item.get("records_count", 0),
            "contract_name": item.get("contract_name"),
            "intent_scope_label": item.get("intent_scope_label", "unknown_metadata_review"),
            "source_draft_eligibility_status": source_status,
            "resolution_status": _map_item_status(source_status),
            "required_input_fields": REQUIRED_INPUT_FIELDS.copy(),
            "missing_required_input_fields": REQUIRED_INPUT_FIELDS.copy(),
            "field_resolution_plan": field_res_plan.copy(),
            "validation_requirements": VALIDATION_REQUIREMENTS.copy(),
            "evidence_requirements": EVIDENCE_REQUIREMENTS.copy(),
            "blocked_reasons": blocked_reasons.copy(),
            "allowed_next_step": "stage_supervised_input_resolution_redaction_and_validation",
            "forbidden_current_actions": FORBIDDEN_CURRENT_ACTIONS.copy(),
            "disallowed_outputs": DISALLOWED_OUTPUTS.copy(),
        }
        supervised_input_resolution_items.append(resolution_item)

    actual_next_task = next_recommended_task or NEXT_RECOMMENDED_TASK
    raw_packet = {
        "task_label": TASK_LABEL,
        "source_draft_eligibility_gate_precheck_packet_hash": _source_packet_hash(draft_eligibility_gate_precheck_packet),
        "source_packet_task_label": draft_eligibility_gate_precheck_packet.get("task_label", "unknown"),
        "source_draft_eligibility_item_count": len(source_items),
        "global_resolution_plan_status": "BLOCKED_SUPERVISED_INPUT_RESOLUTION_REQUIRED",
        "required_input_fields": REQUIRED_INPUT_FIELDS.copy(),
        "missing_required_input_fields": REQUIRED_INPUT_FIELDS.copy(),
        "supervised_input_resolution_items": supervised_input_resolution_items,
        "field_resolution_plan": field_res_plan,
        "allowed_future_resolution_methods": ALLOWED_FUTURE_RESOLUTION_METHODS.copy(),
        "validation_requirements": VALIDATION_REQUIREMENTS.copy(),
        "evidence_requirements": EVIDENCE_REQUIREMENTS.copy(),
        "resolution_rules": [
            "supervised_input_resolution_must_be_completed_before_draft_eligibility",
            "validation_requirements_must_be_satisfied_in_future_task",
            "all_missing_fields_must_have_operator_provided_review_evidence",
        ],
        "blocked_reasons": blocked_reasons.copy(),
        "allowed_next_step": "stage_supervised_input_resolution_redaction_and_validation",
        "forbidden_current_actions": FORBIDDEN_CURRENT_ACTIONS.copy(),
        "disallowed_outputs": DISALLOWED_OUTPUTS.copy(),
        "truth_protection_flags": TRUTH_PROTECTION_FLAGS.copy(),
        "safety_flags": SAFETY_FLAGS.copy(),
        "draft_generation_policy": _draft_generation_policy(),
        "next_recommended_task": actual_next_task,
        "ledger_family": LEDGER_FAMILY,
        "hash_algorithm": HASH_ALGORITHM,
    }

    packet_serialized = json.dumps(raw_packet, sort_keys=True, separators=(",", ":"))
    packet_hash = sha256(packet_serialized.encode("utf-8")).hexdigest()
    return {"packet_hash": packet_hash, **raw_packet}


def render_runbook(packet: dict[str, Any]) -> str:
    """Render deterministic markdown runbook for the supervised input resolution plan."""
    lines = [
        "# Draft Eligibility Gate to Supervised Input Resolution Plan",
        "",
        "> [!IMPORTANT]",
        "> This is a deterministic local plan defining validation and evidence requirements for resolving missing operator inputs in a future task. Actual input capture, validation execution, and draft generation remain disabled.",
        "",
        f"- **Task Label**: `{packet['task_label']}`",
        f"- **Source Draft Eligibility Gate Precheck Packet Hash**: `{packet['source_draft_eligibility_gate_precheck_packet_hash']}`",
        f"- **Source Packet Task Label**: `{packet['source_packet_task_label']}`",
        f"- **Packet Hash**: `{packet['packet_hash']}`",
        f"- **Global Resolution Plan Status**: `{packet['global_resolution_plan_status']}`",
        f"- **Source Draft Eligibility Item Count**: `{packet['source_draft_eligibility_item_count']}`",
        f"- **Supervised Input Resolution Item Count**: `{len(packet['supervised_input_resolution_items'])}`",
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
        "## Field Resolution Plan",
        "",
        "| Field | Required | Current Value | Placeholder Value | Resolution Status | Future Resolution Required | Evidence Required |",
        "|---|---|---|---|---|---|---|",
    ])
    for field, plan in packet["field_resolution_plan"].items():
        curr_val = "null" if plan["current_value"] is None else str(plan["current_value"])
        lines.append(
            f"| `{field}` | `{plan['required']}` | `{curr_val}` | `{plan['placeholder_value']}` | "
            f"`{plan['resolution_status']}` | `{plan['future_resolution_required']}` | `{plan['evidence_required']}` |"
        )

    lines.extend([
        "",
        "## Allowed Future Resolution Methods",
        "",
    ])
    for method in packet["allowed_future_resolution_methods"]:
        lines.append(f"- `{method}`")

    lines.extend([
        "",
        "## Validation Requirements (Future Execution)",
        "",
    ])
    for req in packet["validation_requirements"]:
        lines.append(f"- `{req}`")

    lines.extend([
        "",
        "## Evidence Requirements",
        "",
        "| Requirement | Required |",
        "|---|---|",
    ])
    for req, required in packet["evidence_requirements"].items():
        lines.append(f"| `{req}` | `{required}` |")

    lines.extend([
        "",
        "## Resolution Rules",
        "",
    ])
    for rule in packet["resolution_rules"]:
        lines.append(f"- `{rule}`")

    lines.extend([
        "",
        "## Supervised Input Resolution Items",
        "",
        "| Resolution Item ID | Source Draft Eligibility Item ID | Candidate ID | Relative Path | Resolution Status |",
        "|---|---|---|---|---|",
    ])
    for item in packet["supervised_input_resolution_items"]:
        lines.append(
            f"| `{item['resolution_item_id']}` | `{item['source_draft_eligibility_item_id']}` | "
            f"`{item['source_candidate_id']}` | `{item['relative_path']}` | `{item['resolution_status']}` |"
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
        "## Draft Generation Policy",
        "",
        "| Flag | State |",
        "|---|---|",
    ])
    for key, value in packet["draft_generation_policy"].items():
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
    draft_eligibility_gate_precheck_packet_path: str | Path,
    repo_root: str | Path = ".",
) -> dict[str, Any]:
    """Write JSON packet and markdown runbook to docs/automation/0175BV/."""
    root = Path(repo_root).resolve()
    out = (root / DOC_REL_DIR).resolve()
    out.mkdir(parents=True, exist_ok=True)

    with open(draft_eligibility_gate_precheck_packet_path, "r", encoding="utf-8") as f:
        source_packet = json.load(f)

    packet = create_supervised_input_resolution_plan(source_packet)
    packet_path = out / PACKET_FILENAME
    runbook_path = out / RUNBOOK_FILENAME

    packet_path.write_text(json.dumps(packet, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    runbook_path.write_text(render_runbook(packet), encoding="utf-8", newline="\n")

    return {
        "packet": packet,
        "packet_path": str(packet_path),
        "runbook_path": str(runbook_path),
    }
