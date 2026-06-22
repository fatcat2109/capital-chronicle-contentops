"""Supervised Input Stub to Draft Eligibility Gate Precheck.

Part of TASK_CONTENTOPS_0175BS_SUPERVISED_INPUT_STUB_TO_DRAFT_ELIGIBILITY_GATE_PRECHECK_V0.
Consumes the 0175BP Supervised Operator Input Stub Contract packet and produces a local-only,
schema-only Draft Eligibility Gate Precheck packet.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Any

TASK_LABEL = "TASK_CONTENTOPS_0175BS_SUPERVISED_INPUT_STUB_TO_DRAFT_ELIGIBILITY_GATE_PRECHECK_V0"
LEDGER_FAMILY = "supervised_input_stub_to_draft_eligibility_gate_precheck_future"
HASH_ALGORITHM = "sha256"
DOC_REL_DIR = Path("docs") / "automation" / "0175BS"
PACKET_FILENAME = "supervised_input_stub_to_draft_eligibility_gate_precheck_packet.json"
RUNBOOK_FILENAME = "supervised_input_stub_to_draft_eligibility_gate_precheck.md"
NEXT_RECOMMENDED_TASK = "TASK_CONTENTOPS_0175BT_DRAFT_ELIGIBILITY_GATE_PRECHECK_TO_V5_READONLY_PRECHECK_PANEL_BINDING_V0"

FORBIDDEN_CURRENT_ACTIONS = [
    "draft_generation",
    "actual_input_capture",
    "editable_input_fields",
    "form_submission",
    "save_capture_approve_generate_controls",
    "operator_prose_generation",
    "content_generation",
    "headline_hook_caption_generation",
    "platform_copy_generation",
    "live_dispatch",
    "provider_or_platform_api_call",
    "actual_draft_generation",
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
    "actual_draft_copy",
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
    "draft_generation_enabled": False,
}


def _source_packet_hash(packet: dict[str, Any]) -> str:
    packet_hash = packet.get("packet_hash")
    if isinstance(packet_hash, str) and packet_hash:
        return packet_hash
    serialized = json.dumps(packet, sort_keys=True, separators=(",", ":"))
    return sha256(serialized.encode("utf-8")).hexdigest()


def create_draft_eligibility_gate_precheck(
    supervised_input_stub_packet: dict[str, Any],
    next_recommended_task: str | None = None,
) -> dict[str, Any]:
    """Transition supervised input stub packet into a Draft Eligibility Gate Precheck packet."""
    if not supervised_input_stub_packet or not isinstance(supervised_input_stub_packet, dict):
        raise ValueError("Supervised input stub packet is missing or malformed. Failing closed.")

    global_status = supervised_input_stub_packet.get("global_supervised_input_stub_status")
    if global_status != "BLOCKED_SUPERVISED_INPUT_CAPTURE_NOT_ENABLED":
        raise ValueError(f"Invalid global supervised input stub status '{global_status}'. Failing closed.")

    source_items = supervised_input_stub_packet.get("supervised_input_stub_items", [])
    if not isinstance(source_items, list):
        raise ValueError("supervised_input_stub_items must be a list. Failing closed.")

    draft_eligibility_items = []
    blocked_reasons = [
        "supervised_input_capture_not_enabled",
        "operator_values_not_collected",
        "draft_eligibility_blocked_by_pending_inputs",
    ]
    missing_requirements = [
        "operator_must_provide_supervised_inputs",
        "draft_generation_requires_inputs_validation",
    ]

    for index, item in enumerate(source_items, start=1):
        source_status = item.get("supervised_input_stub_status", "")
        source_intent_item_id = item.get("source_intent_item_id", "unknown_intent_item")
        
        eligibility_item = {
            "draft_eligibility_item_id": f"draft_eligibility_item_{index:02d}_{source_intent_item_id}",
            "source_stub_item_id": item.get("stub_item_id", "unknown_stub_item"),
            "source_intent_item_id": source_intent_item_id,
            "source_candidate_id": item.get("source_candidate_id", "unknown_candidate"),
            "relative_path": item.get("relative_path", ""),
            "evidence_role": item.get("evidence_role", "unknown"),
            "source_family": item.get("source_family", "unknown"),
            "records_count": item.get("records_count", 0),
            "contract_name": item.get("contract_name"),
            "intent_scope_label": item.get("intent_scope_label", "unknown_metadata_review"),
            "source_supervised_input_stub_status": source_status,
            "draft_eligibility_status": "BLOCKED_BY_SUPERVISED_INPUT_STUB_CONTRACT",
            "draft_generation_enabled": False,
            "public_postable": False,
            "blocked_reasons": blocked_reasons.copy(),
            "missing_requirements": missing_requirements.copy(),
            "allowed_next_step": "resolve_supervised_input_stub_contract_requirements",
            "forbidden_current_actions": FORBIDDEN_CURRENT_ACTIONS.copy(),
            "disallowed_outputs": DISALLOWED_OUTPUTS.copy(),
        }
        draft_eligibility_items.append(eligibility_item)

    actual_next_task = next_recommended_task or NEXT_RECOMMENDED_TASK
    raw_packet = {
        "task_label": TASK_LABEL,
        "source_supervised_input_stub_packet_hash": _source_packet_hash(supervised_input_stub_packet),
        "source_packet_task_label": supervised_input_stub_packet.get("task_label", "unknown"),
        "source_supervised_input_stub_item_count": len(source_items),
        "global_draft_eligibility_status": "BLOCKED_DRAFT_ELIGIBILITY_PENDING_OPERATOR_INPUT",
        "draft_eligibility_items": draft_eligibility_items,
        "global_draft_generation_enabled": False,
        "global_public_postable": False,
        "validation_rules": [
            "supervised_input_capture_must_be_enabled",
            "operator_inputs_must_be_fully_collected",
            "draft_generation_must_remain_disabled_until_inputs_provided",
            "public_postable_must_remain_disabled_until_signoff",
        ],
        "blocked_reasons": blocked_reasons.copy(),
        "missing_requirements": missing_requirements.copy(),
        "allowed_next_step": "resolve_supervised_input_stub_contract_requirements",
        "disallowed_outputs": DISALLOWED_OUTPUTS.copy(),
        "forbidden_current_actions": FORBIDDEN_CURRENT_ACTIONS.copy(),
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
    """Render deterministic markdown runbook for the draft eligibility gate precheck."""
    lines = [
        "# Draft Eligibility Gate Precheck",
        "",
        "> [!IMPORTANT]",
        "> This is a local-only schema draft eligibility precheck. It does not compile actual drafts, headlines, hooks, or platform copy, nor does it invoke live APIs or authorize publications.",
        "",
        f"- **Task Label**: `{packet['task_label']}`",
        f"- **Source Supervised Input Stub Packet Hash**: `{packet['source_supervised_input_stub_packet_hash']}`",
        f"- **Source Packet Task Label**: `{packet['source_packet_task_label']}`",
        f"- **Packet Hash**: `{packet['packet_hash']}`",
        f"- **Global Draft Eligibility Status**: `{packet['global_draft_eligibility_status']}`",
        f"- **Source Supervised Input Stub Item Count**: `{packet['source_supervised_input_stub_item_count']}`",
        f"- **Draft Eligibility Item Count**: `{len(packet['draft_eligibility_items'])}`",
        f"- **Global Draft Generation Enabled**: `{packet['global_draft_generation_enabled']}`",
        f"- **Global Public Postable**: `{packet['global_public_postable']}`",
        f"- **Ledger Family**: `{packet['ledger_family']}`",
        "",
        "## Draft Eligibility Items",
        "",
        "| Eligibility Item ID | Source Stub Item ID | Candidate ID | Status | Draft Gen Enabled | Public Postable | Allowed Next Step |",
        "|---|---|---|---|---|---|---|",
    ]

    for item in packet["draft_eligibility_items"]:
        lines.append(
            f"| `{item['draft_eligibility_item_id']}` | `{item['source_stub_item_id']}` | "
            f"`{item['source_candidate_id']}` | `{item['draft_eligibility_status']}` | "
            f"`{item['draft_generation_enabled']}` | `{item['public_postable']}` | "
            f"`{item['allowed_next_step']}` |"
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
        "## Missing Requirements",
        "",
    ])
    for req in packet["missing_requirements"]:
        lines.append(f"- `{req}`")

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
    supervised_input_stub_packet_path: str | Path,
    repo_root: str | Path = ".",
) -> dict[str, Any]:
    """Write JSON packet and markdown runbook to docs/automation/0175BS/."""
    root = Path(repo_root).resolve()
    out = (root / DOC_REL_DIR).resolve()
    out.mkdir(parents=True, exist_ok=True)

    with open(supervised_input_stub_packet_path, "r", encoding="utf-8") as f:
        source_packet = json.load(f)

    packet = create_draft_eligibility_gate_precheck(source_packet)
    packet_path = out / PACKET_FILENAME
    runbook_path = out / RUNBOOK_FILENAME

    packet_path.write_text(json.dumps(packet, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    runbook_path.write_text(render_runbook(packet), encoding="utf-8", newline="\n")

    return {
        "packet": packet,
        "packet_path": str(packet_path),
        "runbook_path": str(runbook_path),
    }
