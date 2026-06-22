"""Operator Input Capture Precheck to Supervised Input Stub Contract.

Part of TASK_CONTENTOPS_0175BP_OPERATOR_INPUT_CAPTURE_PRECHECK_TO_SUPERVISED_INPUT_STUB_CONTRACT_V0.
Consumes the 0175BN Operator Input Capture Precheck packet and produces a local-only,
schema-only Supervised Operator Input Stub Contract.
"""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

TASK_LABEL = "TASK_CONTENTOPS_0175BP_OPERATOR_INPUT_CAPTURE_PRECHECK_TO_SUPERVISED_INPUT_STUB_CONTRACT_V0"
LEDGER_FAMILY = "operator_input_capture_precheck_to_supervised_input_stub_contract_future"
HASH_ALGORITHM = "sha256"
DOC_REL_DIR = Path("docs") / "automation" / "0175BP"
PACKET_FILENAME = "operator_input_capture_precheck_to_supervised_input_stub_contract_packet.json"
RUNBOOK_FILENAME = "operator_input_capture_precheck_to_supervised_input_stub_contract.md"
NEXT_RECOMMENDED_TASK = "TASK_CONTENTOPS_0175BQ_SUPERVISED_INPUT_STUB_CONTRACT_TO_V5_READONLY_STUB_PANEL_BINDING_V0"

REQUIRED_INPUT_FIELDS = [
    "intended_audience_lane",
    "content_purpose_category",
    "source_review_notes",
    "risk_review_notes",
    "claim_scope_boundary",
    "manual_operator_decision",
]

ALLOWED_FUTURE_CAPTURE_MODES = [
    "manual_supervised_operator_entry",
    "imported_operator_review_packet",
    "deferred_human_review_session",
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
    "live_dispatch",
    "provider_or_platform_api_call",
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
]

TRUTH_PROTECTION_FLAGS = {
    "dqr_cleared_by_contentops": False,
    "readiness_cleared_by_contentops": False,
    "current_truth_promoted": False,
    "numeric_truth_promoted": False,
    "market_data_promoted": False,
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
}


def _source_packet_hash(packet: dict[str, Any]) -> str:
    packet_hash = packet.get("packet_hash")
    if isinstance(packet_hash, str) and packet_hash:
        return packet_hash
    serialized = json.dumps(packet, sort_keys=True, separators=(",", ":"))
    return sha256(serialized.encode("utf-8")).hexdigest()


def _field_policy() -> dict[str, dict[str, Any]]:
    return {
        field: {
            "required": True,
            "slot_status": "STUB_SLOT_PENDING_SUPERVISED_INPUT",
            "value_status": "PENDING_OPERATOR_INPUT",
            "current_value": None,
            "placeholder_value": "PENDING_OPERATOR_INPUT",
            "capture_enabled_in_this_task": False,
            "editable_in_this_task": False,
            "generated_by_system": False,
            "operator_must_provide_later": True,
            "future_supervised_capture_required": True,
            "persistence_enabled": False,
            "validation_enabled": False,
        }
        for field in REQUIRED_INPUT_FIELDS
    }


def _map_item_status(source_status: str) -> str:
    if source_status == "OPERATOR_INPUT_CAPTURE_PRECHECK_PENDING":
        return "SUPERVISED_INPUT_STUB_PENDING_FUTURE_CAPTURE"
    if source_status.startswith("BLOCKED"):
        return "BLOCKED_BY_OPERATOR_INPUT_CAPTURE_PRECHECK"
    return "BLOCKED_BY_OPERATOR_INPUT_CAPTURE_PRECHECK"


def create_supervised_input_stub_contract(
    operator_input_capture_precheck_packet: dict[str, Any],
    next_recommended_task: str | None = None,
) -> dict[str, Any]:
    """Transition input-capture precheck metadata into supervised-input stub slots."""
    if not operator_input_capture_precheck_packet or not isinstance(operator_input_capture_precheck_packet, dict):
        raise ValueError("Operator input capture precheck packet is missing or malformed. Failing closed.")

    global_status = operator_input_capture_precheck_packet.get("global_operator_input_capture_status")
    if global_status != "BLOCKED_OPERATOR_INPUT_CAPTURE_NOT_ENABLED":
        raise ValueError(f"Invalid operator input capture global status '{global_status}'. Failing closed.")

    source_items = operator_input_capture_precheck_packet.get("input_capture_precheck_items", [])
    if not isinstance(source_items, list):
        raise ValueError("input_capture_precheck_items must be a list. Failing closed.")

    source_policy = operator_input_capture_precheck_packet.get("field_policy", {})
    if set(source_policy.keys()) != set(REQUIRED_INPUT_FIELDS):
        raise ValueError("Required input field policy mismatch. Failing closed.")

    input_stub_field_policy = _field_policy()
    supervised_input_stub_items = []

    for index, item in enumerate(source_items, start=1):
        source_status = item.get("operator_input_capture_precheck_status", "")
        source_intent_item_id = item.get("intent_item_id", "unknown_intent_item")
        stub_item = {
            "stub_item_id": f"supervised_input_stub_{index:02d}_{source_intent_item_id}",
            "source_intent_item_id": source_intent_item_id,
            "source_candidate_id": item.get("source_candidate_id", "unknown_candidate"),
            "relative_path": item.get("relative_path", ""),
            "evidence_role": item.get("evidence_role", "unknown"),
            "source_family": item.get("source_family", "unknown"),
            "records_count": item.get("records_count", 0),
            "contract_name": item.get("contract_name"),
            "intent_scope_label": item.get("intent_scope_label", "unknown_metadata_review"),
            "source_precheck_status": source_status,
            "supervised_input_stub_status": _map_item_status(source_status),
            "required_input_fields": REQUIRED_INPUT_FIELDS.copy(),
            "input_stub_field_policy": deepcopy(input_stub_field_policy),
            "blocked_reasons": list(item.get("blocked_reasons", [])),
            "missing_requirements": list(item.get("missing_requirements", [])),
            "allowed_next_step": "future_task_may_bind_readonly_stub_contract_before_capture_enablement",
            "forbidden_current_actions": FORBIDDEN_CURRENT_ACTIONS.copy(),
            "disallowed_outputs": DISALLOWED_OUTPUTS.copy(),
        }
        supervised_input_stub_items.append(stub_item)

    actual_next_task = next_recommended_task or NEXT_RECOMMENDED_TASK
    raw_packet = {
        "task_label": TASK_LABEL,
        "source_operator_input_capture_precheck_packet_hash": _source_packet_hash(operator_input_capture_precheck_packet),
        "source_packet_task_label": operator_input_capture_precheck_packet.get("task_label", "unknown"),
        "source_input_capture_precheck_item_count": len(source_items),
        "global_supervised_input_stub_status": "BLOCKED_SUPERVISED_INPUT_CAPTURE_NOT_ENABLED",
        "supervised_input_stub_items": supervised_input_stub_items,
        "required_input_fields": REQUIRED_INPUT_FIELDS.copy(),
        "input_stub_field_policy": input_stub_field_policy,
        "allowed_future_capture_modes": ALLOWED_FUTURE_CAPTURE_MODES.copy(),
        "future_capture_modes_enabled_in_this_task": False,
        "forbidden_current_actions": FORBIDDEN_CURRENT_ACTIONS.copy(),
        "validation_rules": [
            "all_stub_slots_must_remain_pending_operator_input",
            "current_value_must_remain_null",
            "placeholder_value_must_remain_pending_operator_input",
            "capture_must_remain_disabled_in_this_task",
            "editable_fields_must_not_be_introduced",
            "persistence_must_remain_disabled",
            "validation_must_remain_disabled_until_supervised_capture_task",
            "future_capture_modes_are_declared_only_not_enabled",
        ],
        "blocked_reasons": [
            "supervised_input_capture_not_enabled",
            "operator_values_not_collected",
            "stub_slots_pending_future_supervised_capture",
        ],
        "allowed_next_step": "bind_supervised_input_stub_contract_to_readonly_v5_panel",
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
    """Render deterministic markdown runbook for the supervised input stub contract."""
    lines = [
        "# Supervised Operator Input Stub Contract",
        "",
        "> [!IMPORTANT]",
        "> This is a local-only schema stub contract. It does not enable actual operator input capture, editable UI, persistence, form submission, save/capture/approve/generate controls, provider/platform APIs, live dispatch, or content generation.",
        "",
        f"- **Task Label**: `{packet['task_label']}`",
        f"- **Source Operator Input Capture Precheck Packet Hash**: `{packet['source_operator_input_capture_precheck_packet_hash']}`",
        f"- **Source Packet Task Label**: `{packet['source_packet_task_label']}`",
        f"- **Packet Hash**: `{packet['packet_hash']}`",
        f"- **Global Supervised Input Stub Status**: `{packet['global_supervised_input_stub_status']}`",
        f"- **Source Input Capture Precheck Item Count**: `{packet['source_input_capture_precheck_item_count']}`",
        f"- **Supervised Input Stub Item Count**: `{len(packet['supervised_input_stub_items'])}`",
        f"- **Future Capture Modes Enabled In This Task**: `{packet['future_capture_modes_enabled_in_this_task']}`",
        f"- **Ledger Family**: `{packet['ledger_family']}`",
        "",
        "## Required Input Stub Field Policy",
        "",
        "| Field | Slot Status | Current Value | Placeholder Value | Capture Enabled | Editable | Generated | Persistence | Validation |",
        "|---|---|---|---|---|---|---|---|---|",
    ]

    for field, policy in packet["input_stub_field_policy"].items():
        current_value = "null" if policy["current_value"] is None else str(policy["current_value"])
        lines.append(
            f"| `{field}` | `{policy['slot_status']}` | `{current_value}` | "
            f"`{policy['placeholder_value']}` | `{policy['capture_enabled_in_this_task']}` | "
            f"`{policy['editable_in_this_task']}` | `{policy['generated_by_system']}` | "
            f"`{policy['persistence_enabled']}` | `{policy['validation_enabled']}` |"
        )

    lines.extend([
        "",
        "## Allowed Future Capture Modes",
        "",
        "These enum labels are declared for later supervised tasks only and are not enabled now.",
        "",
    ])
    for mode in packet["allowed_future_capture_modes"]:
        lines.append(f"- `{mode}`")

    lines.extend([
        "",
        "## Supervised Input Stub Items",
        "",
        "| Stub Item ID | Source Intent Item ID | Candidate ID | Status | Allowed Next Step |",
        "|---|---|---|---|---|",
    ])
    for item in packet["supervised_input_stub_items"]:
        lines.append(
            f"| `{item['stub_item_id']}` | `{item['source_intent_item_id']}` | "
            f"`{item['source_candidate_id']}` | `{item['supervised_input_stub_status']}` | "
            f"`{item['allowed_next_step']}` |"
        )

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
        "## Validation Rules",
        "",
    ])
    for rule in packet["validation_rules"]:
        lines.append(f"- `{rule}`")

    lines.extend([
        "",
        "## Navigation",
        "",
        f"- **Allowed Next Step**: `{packet['allowed_next_step']}`",
        f"- **Next Recommended Task**: `{packet['next_recommended_task']}`",
    ])
    return "\n".join(lines) + "\n"


def write_artifacts(
    operator_input_capture_precheck_packet_path: str | Path,
    repo_root: str | Path = ".",
) -> dict[str, Any]:
    """Write JSON packet and markdown runbook to docs/automation/0175BP/."""
    root = Path(repo_root).resolve()
    out = (root / DOC_REL_DIR).resolve()
    out.mkdir(parents=True, exist_ok=True)

    with open(operator_input_capture_precheck_packet_path, "r", encoding="utf-8") as f:
        source_packet = json.load(f)

    packet = create_supervised_input_stub_contract(source_packet)
    packet_path = out / PACKET_FILENAME
    runbook_path = out / RUNBOOK_FILENAME

    packet_path.write_text(json.dumps(packet, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    runbook_path.write_text(render_runbook(packet), encoding="utf-8", newline="\n")

    return {
        "packet": packet,
        "packet_path": str(packet_path),
        "runbook_path": str(runbook_path),
    }
