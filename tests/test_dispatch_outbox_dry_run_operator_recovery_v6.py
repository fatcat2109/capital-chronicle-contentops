"""Backend tests for V6 Dispatch Outbox Operator Recovery Packet."""
from __future__ import annotations

import json
from pathlib import Path
from live_contentops.dispatch_outbox_dry_run_operator_recovery_v6 import build_recovery_package

ROOT = Path(__file__).resolve().parents[1]
PACKET_PATH = ROOT / "docs" / "automation" / "V6_DISPATCH_OUTBOX_DRY_RUN_OPERATOR_RUNBOOK_AND_RECOVERY" / "dispatch_outbox_dry_run_operator_recovery_packet.json"


def test_operator_recovery_packet_contents() -> None:
    packet = build_recovery_package()
    assert packet["packet_kind"] == "dispatch_outbox_dry_run_operator_runbook_and_recovery_v0"
    assert packet["operator_recovery_status"] == "operator_recovery_runbook_created_for_review"
    assert packet["recovery_runbook_created"] is True
    assert packet["manual_fallback_plan_created"] is True
    assert packet["rollback_plan_created"] is True
    assert packet["dry_run_replay_plan_created"] is True
    assert packet["failure_mode_matrix_created"] is True
    assert packet["evidence_collection_checklist_created"] is True
    assert packet["dispatch_preflight_checklist_created"] is True
    assert packet["executable_outbox_entry_created"] is False
    assert packet["real_outbox_entry_created"] is False
    assert packet["dispatch_outbox_ready"] is False
    assert packet["dispatch_attempted"] is False
    assert packet["dispatch_request_count"] == 0
    assert packet["webhook_request_count"] == 0
    assert packet["platform_api_request_count"] == 0
    assert packet["kill_switch_active"] is True
    assert packet["blocked_until_explicit_live_scope"] is True
    assert len(packet["operator_preflight_checklist"]) > 0
    assert len(packet["manual_dispatch_fallback_steps"]) > 0
    assert len(packet["dry_run_replay_steps"]) > 0
    assert len(packet["rollback_and_stop_conditions"]) > 0
    assert len(packet["failure_mode_matrix"]) > 0
    assert len(packet["evidence_collection_checklist"]) > 0
    assert len(packet["platform_specific_recovery_notes"]) == 10
    
    assert packet["source_dispatch_outbox_dry_run_packet_id"] == "outbox_dry_run_7cfc24c5b0c0eded"
    assert packet["source_dispatch_outbox_dry_run_exact_hash"] == "7cfc24c5b0c0ededb530c3d5ede21490ad49b0d46969e7d7ed3d8c7758769439"


def test_operator_recovery_file_saved_correctly() -> None:
    assert PACKET_PATH.exists()
    data = json.loads(PACKET_PATH.read_text(encoding="utf-8"))
    assert data["operator_recovery_status"] == "operator_recovery_runbook_created_for_review"
    assert data["source_dispatch_outbox_dry_run_packet_id"] == "outbox_dry_run_7cfc24c5b0c0eded"
