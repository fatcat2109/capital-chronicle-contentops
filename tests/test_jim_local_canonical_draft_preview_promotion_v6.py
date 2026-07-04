import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK = "TASK_0082_JIM_LOCAL_CANONICAL_DRAFT_PREVIEW_PROMOTION_V0"


def _read_json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def test_status_promotes_local_canonical_draft_preview_for_jim_cockpit() -> None:
    status = _read_json("docs/status/current_project_status.json")

    assert status["latest_accepted_task"] == TASK
    assert "local canonical draft preview" in status["accepted_baseline_summary"].lower()
    assert "live_contentops/local_canonical_draft_preview_and_review_v6.py" in status["backend_status_modules"]
    assert "Jim local canonical draft preview and operator review cockpit panel" in status["current_loop_components"]
    assert "public URL verification" in status["dispatch_live_status"]
    assert "not claimed" in status["dispatch_live_status"]


def test_manifest_keeps_all_live_and_provider_flags_false() -> None:
    manifest = _read_json(
        "docs/automation/V6_JIM_LOCAL_CANONICAL_DRAFT_PREVIEW_PROMOTION/"
        "jim_local_canonical_draft_preview_manifest_v0.json"
    )

    assert manifest["task_label"] == TASK
    assert "live_contentops/local_canonical_draft_preview_and_review_v6.py" in manifest["source_modules"]
    assert "ui/contentops_v5/src/views/JimDailyRun.tsx" in manifest["ui_surfaces"]
    assert "tests/test_jim_local_canonical_draft_preview_promotion_v6.py" in manifest["tests"]
    assert all(value is False for value in manifest["safety_flags"].values())


def test_ui_source_has_review_only_local_draft_panel_without_controls() -> None:
    ui_source = (ROOT / "ui/contentops_v5/src/views/JimDailyRun.tsx").read_text(encoding="utf-8")

    assert "Local Canonical Draft Preview + Review" in ui_source
    assert "deterministic" in ui_source.lower()
    assert "ready_for_llm_drafting=false" in ui_source
    assert "enabled_publish_send_dispatch_approve_controls=false" in ui_source
    assert "publish now" not in ui_source.lower()
    assert "send now" not in ui_source.lower()
    assert "dispatch live" not in ui_source.lower()


def test_dirty_workspace_audit_is_non_destructive() -> None:
    audit = (ROOT / "docs/status/TASK_0082_UNRELATED_DIRTY_WORKSPACE_AUDIT.md").read_text(encoding="utf-8")

    assert "No files were deleted" in audit
    assert "preserve" in audit.lower()
    assert "live_contentops/operator_browser_lab.py" in audit
