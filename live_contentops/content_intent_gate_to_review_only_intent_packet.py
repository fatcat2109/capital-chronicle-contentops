"""Content Intent Gate to Review-Only Content Intent Packet.

Part of TASK_CONTENTOPS_0175BL_CONTENT_INTENT_GATE_TO_REVIEW_ONLY_INTENT_PACKET_V0.
Consumes the Content Intent Gate Precheck packet and produces a Review-Only Content Intent Packet.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Any

TASK_LABEL = "TASK_CONTENTOPS_0175BL_CONTENT_INTENT_GATE_TO_REVIEW_ONLY_INTENT_PACKET_V0"
SOURCE_BASELINE_COMMIT = "1943a1fa9234431263074f48e8f5fabe9f3a1738"
LEDGER_FAMILY = "content_intent_gate_to_review_only_intent_packet_future"
HASH_ALGORITHM = "sha256"
DOC_REL_DIR = Path("docs") / "automation" / "0175BL"
PACKET_FILENAME = "content_intent_gate_to_review_only_intent_packet.json"
RUNBOOK_FILENAME = "content_intent_gate_to_review_only_intent_packet.md"

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
    "buy_sell_hold_sizing_signal_language"
]

CONTROLLED_INTENT_SCOPES = [
    "official_text_review",
    "macro_data_contract_review",
    "broker_proxy_context_review",
    "ttl_freshness_policy_review",
    "schema_contract_review",
    "unknown_metadata_review"
]


def map_intent_scope_label(source_family: str, candidate_id: str) -> str:
    """Deterministically maps source family and candidate ID to non-claim scope label."""
    fam = (source_family or "").lower()
    cid = (candidate_id or "").lower()
    if "official text" in fam:
        return "official_text_review"
    elif "us macro" in fam:
        if "ttl" in cid or "freshness" in cid:
            return "ttl_freshness_policy_review"
        elif "schema" in cid:
            return "schema_contract_review"
        return "macro_data_contract_review"
    elif "broker proxy" in fam:
        return "broker_proxy_context_review"
    else:
        return "unknown_metadata_review"


def create_review_only_intent_packet(
    precheck_packet: dict[str, Any],
    next_recommended_task: str | None = None
) -> dict[str, Any]:
    """Transition precheck packet to a Review-Only Content Intent Packet."""
    if not precheck_packet or not isinstance(precheck_packet, dict):
        raise ValueError("Precheck packet is missing or malformed. Failing closed.")

    global_source_status = precheck_packet.get("content_intent_gate_status")
    allowed_statuses = {"BLOCKED_OPERATOR_REVIEW_REQUIRED", "BLOCKED_MISSING_METADATA", "BLOCKED_NOT_CANDIDATE_ONLY"}
    if global_source_status not in allowed_statuses:
        raise ValueError(f"Invalid content intent gate status '{global_source_status}'. Failing closed.")

    serialized = json.dumps(precheck_packet, sort_keys=True, separators=(",", ":"))
    source_content_intent_gate_precheck_packet_hash = sha256(serialized.encode("utf-8")).hexdigest()

    source_packet_task_label = precheck_packet.get("task_label", "unknown")
    source_candidate_count = precheck_packet.get("source_candidate_count", 0)

    # Scaffolding default operator inputs
    default_inputs = {
        "intended_audience_lane": "PENDING_OPERATOR_INPUT",
        "content_purpose_category": "PENDING_OPERATOR_INPUT",
        "source_review_notes": "PENDING_OPERATOR_INPUT",
        "risk_review_notes": "PENDING_OPERATOR_INPUT",
        "claim_scope_boundary": "PENDING_OPERATOR_INPUT",
        "manual_operator_decision": "PENDING_OPERATOR_INPUT"
    }

    review_only_intent_items = []
    for item in precheck_packet.get("candidate_gate_items", []):
        cid = item.get("candidate_id", "unknown_candidate")
        rel_path = item.get("relative_path", "")
        role = item.get("evidence_role", "unknown")
        family = item.get("source_family", "unknown")
        records_count = item.get("records_count", 0)
        contract_name = item.get("contract_name")
        advisory_only = item.get("advisory_only", True)
        candidate_only = item.get("candidate_only", True)
        source_gate_status = item.get("content_intent_gate_status", "unknown")

        # Map candidate item status
        if source_gate_status == "READY_FOR_OPERATOR_INTENT_REVIEW":
            item_status = "REVIEW_ONLY_INTENT_PENDING_OPERATOR_INPUT"
        elif source_gate_status.startswith("BLOCKED"):
            item_status = "BLOCKED_BY_CONTENT_INTENT_GATE"
        else:
            item_status = "BLOCKED_BY_CONTENT_INTENT_GATE"

        scope_label = map_intent_scope_label(family, cid)

        intent_item = {
            "intent_item_id": f"intent_item_{cid}",
            "source_candidate_id": cid,
            "relative_path": rel_path,
            "evidence_role": role,
            "source_family": family,
            "records_count": records_count,
            "contract_name": contract_name,
            "advisory_only": advisory_only,
            "candidate_only": candidate_only,
            "source_gate_status": source_gate_status,
            "review_only_intent_status": item_status,
            "operator_review_required": True,
            "required_operator_inputs": default_inputs.copy(),
            "blocked_reasons": list(item.get("blocked_reasons", [])),
            "missing_requirements": list(item.get("missing_requirements", [])),
            "allowed_next_step": item.get("allowed_next_step", ""),
            "disallowed_outputs": DISALLOWED_OUTPUTS.copy(),
            "intent_scope_label": scope_label
        }
        review_only_intent_items.append(intent_item)

    # Protect truth flags
    protected_truth_flags = {
        "dqr_cleared_by_contentops": False,
        "readiness_cleared_by_contentops": False,
        "current_truth_promoted": False,
        "numeric_truth_promoted": False,
        "market_data_promoted": False
    }

    # Safety flags
    safety_flags = {
        "live_api_called": False,
        "provider_api_called": False,
        "platform_api_called": False,
        "credential_hydrated": False,
        "secret_values_observed": False,
        "env_secret_read": False,
        "scheduler_enabled": False,
        "scraping_performed": False,
        "dispatch_ready": False,
        "public_postable": False
    }

    actual_next_task = next_recommended_task
    if not actual_next_task:
        actual_next_task = "TASK_CONTENTOPS_0175BM_REVIEW_ONLY_INTENT_PACKET_TO_V5_INTENT_DETAIL_BINDING_V0"

    raw_packet = {
        "task_label": TASK_LABEL,
        "source_content_intent_gate_precheck_packet_hash": source_content_intent_gate_precheck_packet_hash,
        "source_packet_task_label": source_packet_task_label,
        "source_candidate_count": source_candidate_count,
        "review_only_intent_items": review_only_intent_items,
        "global_intent_packet_status": "BLOCKED_OPERATOR_INTENT_INPUT_REQUIRED",
        "operator_review_required": True,
        "blocked_reasons": ["operator_intent_input_pending", "intent_drafting_gated"],
        "allowed_next_step": "operator_must_provide_intent_inputs_to_unlock_drafting",
        "required_operator_inputs": default_inputs.copy(),
        "disallowed_outputs": DISALLOWED_OUTPUTS.copy(),
        "truth_protection_flags": protected_truth_flags,
        "safety_flags": safety_flags,
        "next_recommended_task": actual_next_task,
        "ledger_family": LEDGER_FAMILY,
        "hash_algorithm": HASH_ALGORITHM
    }

    # Deterministic self hash
    packet_serialized = json.dumps(raw_packet, sort_keys=True, separators=(",", ":"))
    packet_hash = sha256(packet_serialized.encode("utf-8")).hexdigest()

    return {
        "packet_hash": packet_hash,
        **raw_packet
    }


def render_runbook(packet: dict[str, Any]) -> str:
    """Renders the markdown runbook for the Content Intent Packet."""
    items = packet["review_only_intent_items"]
    safety = packet["safety_flags"]
    truth = packet["truth_protection_flags"]

    lines = [
        "# Review-Only Content Intent Packet",
        "",
        "> [!IMPORTANT]",
        "> This is a deterministic local-only Review-Only Content Intent Packet.",
        "> It does not compile headlines, hooks, drafts, dispatches, or predictions.",
        "> All safety locks are active, and no platform/provider API integrations are initialized.",
        "",
        f"- **Task Label**: `{packet['task_label']}`",
        f"- **Source Precheck Packet Hash**: `{packet['source_content_intent_gate_precheck_packet_hash']}`",
        f"- **Source Packet Task Label**: `{packet['source_packet_task_label']}`",
        f"- **Packet Hash**: `{packet['packet_hash']}`",
        f"- **Global Intent Status**: `{packet['global_intent_packet_status']}`",
        f"- **Ledger Family**: `{packet['ledger_family']}`",
        "",
        "## Invariant Validation Safety Flags",
        "",
        "| Safety Lock | State | Status |",
        "|---|---|---|",
    ]

    for k, v in safety.items():
        lines.append(f"| `{k}` | `{v}` | {'✅' if not v else '❌'} |")

    lines.extend([
        "",
        "## Truth Protection Status",
        "",
        "| Truth Flag | State | Status |",
        "|---|---|---|",
    ])

    for k, v in truth.items():
        lines.append(f"| `{k}` | `{v}` | {'✅' if not v else '❌'} |")

    lines.extend([
        "",
        "## Review-Only Intent Items (Scaffold Metadata)",
        "",
        "| Intent Item ID | Candidate ID | Status | Scope Label | Allowed Next Step |",
        "|---|---|---|---|---|",
    ])

    for item in items:
        lines.append(
            f"| `{item['intent_item_id']}` | `{item['source_candidate_id']}` | `{item['review_only_intent_status']}` | "
            f"`{item['intent_scope_label']}` | `{item['allowed_next_step']}` |"
        )

    lines.extend([
        "",
        "## Disallowed Output Enforcement",
        "",
        "The following outputs are strictly forbidden from this intent staging phase:",
        "",
    ])

    for out in packet["disallowed_outputs"]:
        lines.append(f"- `[FORBIDDEN]` {out}")

    lines.extend([
        "",
        "## Navigation",
        "",
        f"- **Next Recommended Task**: `{packet['next_recommended_task']}`",
    ])

    return "\n".join(lines) + "\n"


def write_artifacts(precheck_packet_path: str | Path, repo_root: str | Path = ".") -> dict[str, Any]:
    """Generates and writes the JSON packet and Markdown runbook to docs/automation/0175BL/."""
    root = Path(repo_root).resolve()
    out = (root / DOC_REL_DIR).resolve()
    out.mkdir(parents=True, exist_ok=True)

    with open(precheck_packet_path, "r", encoding="utf-8") as f:
        precheck_packet = json.load(f)

    packet = create_review_only_intent_packet(precheck_packet)
    packet_path = out / PACKET_FILENAME
    runbook_path = out / RUNBOOK_FILENAME

    packet_path.write_text(json.dumps(packet, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    runbook_path.write_text(render_runbook(packet), encoding="utf-8", newline="\n")

    return {
        "packet": packet,
        "packet_path": str(packet_path),
        "runbook_path": str(runbook_path),
    }
