"""TASK 0085 Jim cockpit promotion guardrails for dispatch outbox dry-run preview."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V5 = ROOT / "ui" / "contentops_v5" / "src"
JIM = V5 / "views" / "JimDailyRun.tsx"
TYPES = V5 / "types.ts"
FIXTURES = V5 / "fixtures.ts"
ADAPTER = V5 / "data" / "dispatchOutboxDryRunAdapter.ts"
PROMOTION_DIR = ROOT / "docs" / "automation" / "V6_JIM_DISPATCH_OUTBOX_DRY_RUN_PROMOTION"
MANIFEST = PROMOTION_DIR / "jim_dispatch_outbox_dry_run_manifest_v0.json"
HANDOFF = PROMOTION_DIR / "jim_dispatch_outbox_dry_run_promotion_v0.md"
STATUS = ROOT / "docs" / "status" / "current_project_status.json"


def _compact(path: Path) -> str:
    return re.sub(r"\s+", "", path.read_text(encoding="utf-8").lower())


def test_task_0085_promotion_artifacts_exist_and_remain_dry_run_only() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    handoff = HANDOFF.read_text(encoding="utf-8")

    assert manifest["task"] == "TASK_0085_JIM_APPROVAL_PACKET_PREVIEW_TO_DISPATCH_OUTBOX_DRY_RUN_PROMOTION_V0"
    assert manifest["dry_run_entry_count"] == 10
    assert manifest["next_task"] == "TASK_0086_JIM_DISPATCH_OUTBOX_DRY_RUN_TO_OPERATOR_RUNBOOK_RECOVERY_PROMOTION_V0"
    assert manifest["safety_flags"]["executable_outbox_entry_created"] is False
    assert manifest["safety_flags"]["dispatch_attempted"] is False
    assert manifest["safety_flags"]["dispatch_request_count"] == 0
    assert manifest["safety_flags"]["live_action_allowed"] is False
    assert "No live posting is authorized" in handoff


def test_jim_cockpit_wires_existing_dispatch_outbox_dry_run_adapter() -> None:
    fixtures = _compact(FIXTURES)
    types = _compact(TYPES)
    jim = _compact(JIM)
    adapter = _compact(ADAPTER)

    assert "dispatchoutboxdryrunpacket" in fixtures
    assert "dispatch_outbox_dry_run:jimdispatchoutboxdryrunpacket" in types
    assert "dispatchoutboxdryrunpacket" in adapter
    assert "dispatchoutboxdry-runpreview" in jim
    assert "dryrunoutbox.dry_run_entries" in jim
    assert "executable_outbox_entry_created=false" in jim
    assert "real_outbox_entry_created=false" in jim
    assert "dispatch_outbox_ready=false" in jim
    assert "dispatch_attempted=false" in jim
    assert "dispatch_request_count=0" in jim
    assert "webhook_request_count=0" in jim
    assert "platform_api_request_count=0" in jim
    assert "kill_switch_active=true" in jim
    assert "ready_for_dispatch=false" in jim
    assert "live_action_allowed=false" in jim
    assert "public_url_verification_performed=false" in jim


def test_jim_cockpit_has_no_external_urls_or_enabled_live_controls() -> None:
    text = JIM.read_text(encoding="utf-8")
    assert 'href="http' not in text
    assert 'href={' not in text
    assert "verify public url" not in text.lower()
    assert not re.search(r"<button[^>]*(publish|send|dispatch|approve|schedule|retry)", text, re.IGNORECASE)


def test_status_preserves_dry_run_guardrails_after_operator_recovery_promotion() -> None:
    status = json.loads(STATUS.read_text(encoding="utf-8"))
    status_text = json.dumps(status, sort_keys=True).lower()

    assert status["latest_accepted_task"] == "TASK_0086_JIM_DISPATCH_OUTBOX_DRY_RUN_TO_OPERATOR_RUNBOOK_RECOVERY_PROMOTION_V0"
    assert status["last_updated_by_task"] == status["latest_accepted_task"]
    assert status["next_recommended_task"].startswith("TASK_0087_JIM_COCKPIT_FINAL_READINESS_CONSOLIDATION_V0")
    assert "live posting" not in status_text
    assert "live-post" not in status_text
    assert "dry-run" in status_text
    assert "live_action_allowed=false" in status_text
