"""V6 Unified Approval and Outbox Readiness.

Tracks all validation blockers and logs pipeline readiness status matrices.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "6.0.0"


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
        "blockers": blockers
    }
    Path(out_dir / "unified_outbox_readiness_report.json").write_text(
        json.dumps(outbox_readiness, indent=2, sort_keys=True) + "\n",
        encoding="utf-8"
    )
