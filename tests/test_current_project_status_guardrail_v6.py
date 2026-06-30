from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATUS_MD = ROOT / "docs" / "status" / "CURRENT_PROJECT_STATUS.md"
STATUS_JSON = ROOT / "docs" / "status" / "current_project_status.json"
PROTOCOL_MD = ROOT / "docs" / "status" / "TASK_STATUS_UPDATE_PROTOCOL.md"
DASHBOARD_AUTHORITY_MD = ROOT / "docs" / "status" / "DASHBOARD_SURFACE_AUTHORITY.md"
STALE_UI = ROOT / "ui" / "operator_approval_queue_evidence_vault"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def test_required_status_files_exist() -> None:
    assert STATUS_MD.exists()
    assert STATUS_JSON.exists()
    assert PROTOCOL_MD.exists()
    assert DASHBOARD_AUTHORITY_MD.exists()


def test_status_json_contract() -> None:
    data = json.loads(_read(STATUS_JSON))
    assert data["schema_version"] == "1.0.0"
    assert data["repo_full_name"] == "fatcat2109/capital-chronicle-contentops"
    assert data["branch"] == "master"
    assert data["canonical_dashboard_surface"] == "ui/contentops_v5/"
    assert data["canonical_dashboard_entrypoint"] == "ui/contentops_v5/src/App.tsx"
    assert data["canonical_dashboard_package"] == "ui/contentops_v5/package.json"
    assert "ui/institutional_operator_cockpit_v4/" in data["legacy_reference_surfaces"]
    if STALE_UI.exists():
        assert "ui/operator_approval_queue_evidence_vault/" in data["stale_wrong_surfaces"]
    assert "docs/status/CURRENT_PROJECT_STATUS.md" in data["mandatory_read_before_task"]
    assert "docs/status/current_project_status.json" in data["mandatory_read_before_task"]
    assert re.fullmatch(r"[0-9a-f]{40}", data["last_verified_remote_sha"])
    assert re.fullmatch(r"[0-9a-f]{40}", data["accepted_product_baseline_sha"])
    assert re.fullmatch(r"[0-9a-f]{40}", data["last_status_commit_sha"])
    assert "status-only" in data["accepted_baseline_summary"]
    assert data["accepted_product_baseline_sha"] in data["accepted_baseline_summary"]
    assert data["last_status_commit_sha"] in data["accepted_baseline_summary"]
    assert data["mandatory_update_after_task"]


def test_guardrail_rules_are_explicit() -> None:
    data = json.loads(_read(STATUS_JSON))
    rules = "\n".join(data["guardrail_rules"]).lower()
    required = [
        "read status before work",
        "update status after task",
        "do not target v4 as canonical product ui",
        "do not create standalone dashboard as canonical",
        "stop on status/repo authority conflict",
    ]
    for rule in required:
        assert rule in rules


def test_status_markdown_explicit_authority_statements() -> None:
    text = _read(STATUS_MD)
    lower = text.lower()
    assert "`ui/contentops_v5/` is the canonical" in lower
    assert "`ui/institutional_operator_cockpit_v4/`" in lower
    assert "fallback/reference only" in lower
    assert "github remote commits and fetched repo files remain runtime authority above this status doc" in lower


def test_protocol_and_dashboard_authority_reinforce_v5() -> None:
    protocol = _read(PROTOCOL_MD).lower()
    authority = _read(DASHBOARD_AUTHORITY_MD).lower()
    assert "read `docs/status/current_project_status.md`" in protocol
    assert "update both status files" in protocol
    assert "ui/contentops_v5/` is canonical" in authority
    assert "browser qa target is v5" in authority
    assert "fallback/reference only" in authority


def test_no_secret_or_session_data_terms() -> None:
    combined = "\n".join(
        _read(path) for path in [STATUS_MD, STATUS_JSON, PROTOCOL_MD, DASHBOARD_AUTHORITY_MD]
    )
    forbidden_patterns = [
        r"https://discord(?:app)?\.com/api/webhooks/",
        r"discord(?:_live)?_announcements_webhook\s*[:=]\s*['\"]https?://",
        r"sk-[a-zA-Z0-9]",
        r"xox[baprs]-",
        r"ghp_[A-Za-z0-9]",
        r"bearer\s+[A-Za-z0-9._-]{12,}",
        r"cookie\s*[:=]",
        r"localstorage\s*[:=]",
        r"sessionstorage\s*[:=]",
        r"browser session data\s*[:=]",
    ]
    for pattern in forbidden_patterns:
        assert not re.search(pattern, combined, flags=re.IGNORECASE)


def test_canonical_recon_outputs_point_to_v5() -> None:
    recon_dir = ROOT / "docs" / "automation" / "V6_DASHBOARD_AUTHORITY_RECON_AND_STALE_UI_CLEANUP"
    pointer = _read(recon_dir / "canonical_dashboard_pointer.md").lower()
    plan = json.loads(_read(recon_dir / "stale_ui_cleanup_plan.json"))
    assert plan["canonical_dashboard_surface"] == "ui/contentops_v5/"
    assert plan["v4_surface"]["classification"] == "active_reference"
    assert plan["standalone_stale_surface"]["exists_after_cleanup"] is False
    assert "ui/contentops_v5/" in pointer
    assert "fallback/reference only" in pointer
    assert "ui/operator_approval_queue_evidence_vault/" in pointer


def test_status_sha_model_doc_distinguishes_product_and_status_commits() -> None:
    data = json.loads(_read(STATUS_JSON))
    model = _read(ROOT / "docs" / "status" / "STATUS_LEDGER_SHA_MODEL.md")
    assert re.fullmatch(r"[0-9a-f]{40}", data["accepted_product_baseline_sha"])
    assert re.fullmatch(r"[0-9a-f]{40}", data["last_status_commit_sha"])
    assert "infinite SHA repair loops" in model
    assert "Status-only repair commits must not become product baselines" in model
    assert "ui/contentops_v5/" in model
