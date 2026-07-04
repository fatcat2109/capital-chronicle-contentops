from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JIM = ROOT / "ui/contentops_v5/src/views/JimDailyRun.tsx"
FIXTURES = ROOT / "ui/contentops_v5/src/fixtures.ts"
TYPES = ROOT / "ui/contentops_v5/src/types.ts"
STATUS_JSON = ROOT / "docs/status/current_project_status.json"
STATUS_MD = ROOT / "docs/status/CURRENT_PROJECT_STATUS.md"
PROMO_DIR = ROOT / "docs/automation/V6_JIM_DISPATCH_OUTBOX_OPERATOR_RECOVERY_PROMOTION"


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_operator_recovery_packet_is_wired_through_v5_view_model():
    assert "JimDispatchOutboxOperatorRecoveryPacket" in _text(TYPES)
    fixtures = _text(FIXTURES)
    assert "dispatchOutboxOperatorRecoveryPacket" in fixtures
    assert "dispatch_outbox_operator_recovery" in fixtures


def test_jim_cockpit_surfaces_operator_recovery_runbook_without_execution_path():
    jim = _text(JIM)
    required = [
        "Dispatch Outbox Operator Runbook + Recovery Preview",
        "operatorRecovery.operator_recovery_status",
        "Operator preflight checklist",
        "Dry-run replay plan",
        "Rollback and stop conditions",
        "Failure mode recovery matrix",
        "Evidence collection checklist",
        "platform_specific_recovery_notes",
        "executable_outbox_entry_created=false",
        "blocked_until_explicit_live_scope=true",
        "dispatch_request_count={operatorRecovery.dispatch_request_count}",
        "webhook_request_count={operatorRecovery.webhook_request_count}",
        "platform_api_request_count={operatorRecovery.platform_api_request_count}",
        "scheduler_enabled={String(operatorRecovery.scheduler_enabled)}",
        "retry_enabled={String(operatorRecovery.retry_enabled)}",
        "kill_switch_active={String(operatorRecovery.kill_switch_active)}",
        "live_action_allowed={String(operatorRecovery.live_action_allowed)}",
    ]
    for marker in required:
        assert marker in jim


def test_jim_operator_recovery_panel_does_not_add_live_affordances():
    jim = _text(JIM)
    panel = jim.split('Dispatch Outbox Operator Runbook + Recovery Preview', 1)[1].split('Manual Export + Approval Packet Workbench', 1)[0]
    forbidden = [
        "<a ",
        "href=",
        "<button",
        "onclick=",
        "input",
        "textarea",
        "<button",
        "onclick=",
        "dispatch now",
        "retry now",
        "schedule now",
        "https://",
        "http://",
    ]
    lower = panel.lower()
    for token in forbidden:
        assert token not in lower


def test_status_docs_promote_task_0086_and_next_non_live_task():
    status = _text(STATUS_JSON)
    md = _text(STATUS_MD)
    for text in (status, md):
        assert "TASK_0086_JIM_DISPATCH_OUTBOX_DRY_RUN_TO_OPERATOR_RUNBOOK_RECOVERY_PROMOTION_V0" in text
        assert "TASK_0087_JIM_COCKPIT_FINAL_READINESS_CONSOLIDATION_V0" in text
        assert "operator runbook/recovery" in text
        assert "substack_public_url_verified=false" in text
        assert "live_action_allowed=false" in text


def test_promotion_handoff_exists_and_preserves_local_only_claims():
    handoff = _text(PROMO_DIR / "handoff.md")
    manifest = _text(PROMO_DIR / "manifest.json")
    assert "operator_recovery_e30e17729faebb93" in handoff
    assert "operator_recovery_e30e17729faebb93" in manifest
    assert "No live/provider/platform/browser/network/env/credential/public URL action" in handoff
    assert '"live_action_allowed": false' in manifest
    assert '"dispatch_attempted": false' in manifest
