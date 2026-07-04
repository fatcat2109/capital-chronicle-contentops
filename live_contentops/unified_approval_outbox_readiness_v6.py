"""V6 Unified Approval and Outbox Readiness.

Tracks validation blockers and local-only pipeline readiness status matrices.
No network, browser, provider, env, credential, scheduler, retry, or platform action.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "6.0.0"

READINESS_STATES = (
    "approved_manual_ready",
    "held_for_revision",
    "rejected_blocked",
    "blocked_no_decision",
    "blocked_live_scope_required",
)


def _readiness_state(payload: dict[str, Any], decision: dict[str, Any] | None) -> str:
    if decision and decision.get("decision") == "approve" and payload.get("dispatch_gate") == "manual_review_only":
        return "approved_manual_ready"
    if decision and decision.get("decision") == "hold":
        return "held_for_revision"
    if decision and decision.get("decision") == "reject":
        return "rejected_blocked"
    if payload.get("dispatch_gate") != "manual_review_only":
        return "blocked_live_scope_required"
    return "blocked_no_decision"


def _manual_next_action(state: str) -> str:
    if state == "approved_manual_ready":
        return "Manual export evidence may be prepared by operator; no executable outbox exists."
    if state == "held_for_revision":
        return "Revise or re-review the exact payload hash before manual export evidence."
    if state == "rejected_blocked":
        return "Keep this payload blocked; regenerate or archive after operator review."
    if state == "blocked_live_scope_required":
        return "Future explicit live/platform scope is required before this lane can progress."
    return "Collect an operator approve/hold/reject packet bound to this payload hash."


def reconcile_operator_decisions_to_local_outbox_readiness(
    payload_rows: list[dict[str, Any]],
    decision_packets: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build local-only readiness rows from hash-bound operator decisions."""
    decisions_by_hash = {packet.get("payload_hash"): packet for packet in decision_packets if packet.get("payload_hash")}
    counts = {state: 0 for state in READINESS_STATES}
    counts.update({"total": 0, "dispatchable": 0})
    rows = []

    for payload in payload_rows:
        decision = decisions_by_hash.get(payload.get("payload_hash"))
        state = _readiness_state(payload, decision)
        counts[state] += 1
        counts["total"] += 1
        rows.append({
            "row_id": f"readiness_{payload.get('platform_id', 'unknown')}",
            "platform_id": payload.get("platform_id"),
            "platform": payload.get("platform"),
            "source_variant_key": payload.get("variant_key"),
            "payload_hash": payload.get("payload_hash"),
            "decision": decision.get("decision") if decision else None,
            "decision_packet_id": decision.get("decision_packet_id") if decision else None,
            "decision_packet_hash": decision.get("decision_packet_hash") if decision else None,
            "readiness_state": state,
            "manual_next_action": _manual_next_action(state),
            "outbox_entry_created": False,
            "outbox_dispatchable": False,
            "dispatch_allowed_now": False,
            "live_write_allowed_now": False,
            "scheduler_or_retry_wired": False,
            "public_url_fetch_made": False,
            "provider_or_api_call_made": False,
            "browser_or_cdp_used": False,
            "approval_ledger_live_write_made": False,
        })

    return {
        "schema_version": SCHEMA_VERSION,
        "reconciliation_mode": "local_review_only_non_executable",
        "counts": counts,
        "readiness_rows": rows,
        "blocked_actions": [
            "execute_outbox",
            "dispatch",
            "publish",
            "schedule",
            "retry",
            "verify_public_url",
            "call_provider_or_api",
            "use_browser_or_cdp",
            "download_media",
            "write_live_approval_ledger",
        ],
    }


def generate_readiness_reports(
    out_dir: Path,
    contract_packet: dict[str, Any],
    manifest_data: dict[str, Any]
) -> None:
    # Build list of active blockers
    blockers = []

    # Check source verification
    draft_inspector = contract_packet.get("draft_inspector", {})
    if "source_verification_required" in draft_inspector.get("blockers", []):
        blockers.append("source_verification_required")
    if "publication_blocked_until_source_verification" in draft_inspector.get("blockers", []):
        blockers.append("publication_blocked_until_source_verification")

    # Append other V6 pipeline blockers
    blockers.extend([
        "destination_binding_incomplete",
        "kill_switch_active",
        "live_write_authorization_missing",
        "operator_approval_incomplete",
        "operator_signature_missing",
        "outbox_creation_blocked",
        "safety_review_incomplete"
    ])

    # Merge any other blockers from variant inspector or quality QA
    for b in draft_inspector.get("blockers", []):
        if b not in blockers:
            blockers.append(b)

    blockers = sorted(list(set(blockers)))

    # Unified blocker matrix with detailed fields
    blocker_matrix = []
    for b in blockers:
        severity = "CRITICAL" if b in ["kill_switch_active", "live_write_authorization_missing", "source_verification_required"] else "HIGH"
        source_ref = "draft_inspector_v2" if b in draft_inspector.get("blockers", []) else "pipeline_governance"
        required_next_action = "Awaiting manual operator verify actions"
        if b == "kill_switch_active":
            required_next_action = "Release kill switch config once fully reviewed"

        blocker_matrix.append({
            "blocker_id": b,
            "severity": severity,
            "source_ref": source_ref,
            "required_next_action": required_next_action,
            "dispatch_blocking": True
        })

    Path(out_dir / "unified_blocker_matrix.json").write_text(
        json.dumps(blocker_matrix, indent=2, sort_keys=True) + "\n",
        encoding="utf-8"
    )

    # Approval Readiness Report
    approval_readiness = {
        "schema_version": SCHEMA_VERSION,
        "unified_payload_status": "READY_FOR_REVIEW_ONLY_HASHED_PAYLOADS",
        "allowed_for_drafting": True,
        "allowed_for_publication": False,
        "public_postable": False,
        "approval_valid_for_dispatch": False,
        "operator_signature_valid": False,
        "kill_switch_active": True,
        "human_review_required": True,
        "next_recommended_task": "TASK_CONTENTOPS_V6_DISCORD_TELEGRAM_OPERATOR_BRIDGE_AND_REDACTED_STATUS_HEAVY_BATCH_V0",
        "blockers": blockers
    }
    Path(out_dir / "unified_approval_readiness_report.json").write_text(
        json.dumps(approval_readiness, indent=2, sort_keys=True) + "\n",
        encoding="utf-8"
    )

    decision_reconciliation = reconcile_operator_decisions_to_local_outbox_readiness(
        manifest_data.get("platform_payload_rows", []),
        manifest_data.get("operator_decision_packets", []),
    )

    # Outbox Readiness Report
    outbox_readiness = {
        "schema_version": SCHEMA_VERSION,
        "outbox_entry_created": False,
        "outbox_dispatchable": False,
        "dispatch_allowed_now": False,
        "live_write_allowed_now": False,
        "destination_binding_complete": False,
        "credentials_hydrated": False,
        "browser_session_started": False,
        "scheduler_or_retry_wired": False,
        "public_url_fetch_made": False,
        "provider_or_api_call_made": False,
        "approval_ledger_live_write_made": False,
        "operator_decision_reconciliation": decision_reconciliation,
        "blockers": blockers
    }
    Path(out_dir / "unified_outbox_readiness_report.json").write_text(
        json.dumps(outbox_readiness, indent=2, sort_keys=True) + "\n",
        encoding="utf-8"
    )
