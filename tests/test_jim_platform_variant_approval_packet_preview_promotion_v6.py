"""TASK 0084 Jim cockpit promotion guardrails for approval-packet preview."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V5 = ROOT / "ui" / "contentops_v5" / "src"
JIM = V5 / "views" / "JimDailyRun.tsx"
TYPES = V5 / "types.ts"
FIXTURES = V5 / "fixtures.ts"
PROMOTION_DIR = ROOT / "docs" / "automation" / "V6_JIM_PLATFORM_VARIANT_APPROVAL_PACKET_PREVIEW_PROMOTION"
MANIFEST = PROMOTION_DIR / "jim_platform_variant_approval_packet_preview_manifest_v0.json"
HANDOFF = PROMOTION_DIR / "jim_platform_variant_approval_packet_preview_promotion_v0.md"
STATUS = ROOT / "docs" / "status" / "current_project_status.json"


def test_task_0084_promotion_artifacts_exist_and_remain_preview_only() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    handoff = HANDOFF.read_text(encoding="utf-8")

    assert manifest["task"] == "TASK_0084_JIM_PLATFORM_VARIANT_FINAL_REVIEW_TO_APPROVAL_PACKET_PREVIEW_PROMOTION_V0"
    assert manifest["approval_target_count"] == 10
    assert manifest["next_task"] == "TASK_0085_JIM_APPROVAL_PACKET_PREVIEW_TO_DISPATCH_OUTBOX_DRY_RUN_PROMOTION_V0"
    assert manifest["safety_flags"]["ready_for_dispatch"] is False
    assert manifest["safety_flags"]["live_action_allowed"] is False
    assert "No live posting is authorized" in handoff


def test_jim_cockpit_wires_existing_approval_packet_preview_adapter() -> None:
    fixtures = FIXTURES.read_text(encoding="utf-8")
    types = TYPES.read_text(encoding="utf-8")
    jim = JIM.read_text(encoding="utf-8")

    assert "platformVariantApprovalPacketPreviewPacket" in fixtures
    assert "platform_variant_approval_packet_preview: PlatformVariantApprovalPacketPreviewPacket" in types
    assert "Platform Variant Approval Packet Preview" in jim
    assert "approvalPreview.approval_targets" in jim
    assert "actual_operator_approval_recorded=false" in jim
    assert "approval_ledger_entry_created=false" in jim
    assert "dispatch_outbox_ready=false" in jim
    assert "ready_for_dispatch=false" in jim
    assert "live_action_allowed=false" in jim
    assert "public_url_verification_performed=false" in jim
    assert "<button" not in jim.lower()
    assert 'href="http' not in jim.lower()


def test_status_promotes_task_0084_and_next_step_is_dry_run_not_live_posting() -> None:
    status = json.loads(STATUS.read_text(encoding="utf-8"))
    status_text = json.dumps(status, sort_keys=True).lower()

    assert status["latest_accepted_task"] == "TASK_0084_JIM_PLATFORM_VARIANT_FINAL_REVIEW_TO_APPROVAL_PACKET_PREVIEW_PROMOTION_V0"
    assert status["last_updated_by_task"] == status["latest_accepted_task"]
    assert status["next_recommended_task"].startswith("TASK_0085_JIM_APPROVAL_PACKET_PREVIEW_TO_DISPATCH_OUTBOX_DRY_RUN_PROMOTION_V0")
    assert "live posting" not in status_text
    assert "live-post" not in status_text
    assert "dispatch/live write stays locked" in status["dispatch_live_status"].lower() or "live actions locked" in status_text
