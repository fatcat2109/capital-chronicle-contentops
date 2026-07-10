from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN"
STATUS_PATH = ROOT / "docs/status/current_project_status.json"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_canonical_authorities_share_current_run_and_next_task() -> None:
    status = json.loads(_read(STATUS_PATH))
    master = _read(PLAN / "current_v6_master_plan.md")
    ledger = _read(PLAN / "v6_25_task_ledger.md")
    pointer = _read(PLAN / "next_task_pointer.md")
    assert status["current_run_id"] in master
    assert status["current_run_id"] in ledger
    assert status["current_run_id"] in pointer
    assert status["next_recommended_task"] in ledger
    assert status["next_recommended_task"] in pointer


def test_all_current_authorities_use_edge_substack_first_community_contract() -> None:
    targets = [
        ROOT / "docs/AI_BUILDER_BOOTSTRAP.md",
        ROOT / "docs/CONTENTOPS_FINAL_AUTOMATION_PIPELINE_READINESS_REPORT.md",
        ROOT / "docs/status/CURRENT_PROJECT_STATUS.md",
        PLAN / "current_v6_master_plan.md",
        ROOT / "docs/automation/OPERATOR_BROWSER_LAB_AND_SOCIAL_CREDENTIAL_SETUP/operator_browser_lab_runbook.md",
    ]
    for path in targets:
        text = _read(path).lower()
        assert "substack" in text, path
        assert "youtube" in text and "community" in text, path
        assert "contentops-social-main" in text, path


def test_current_authorities_do_not_reinstate_stale_blockers() -> None:
    targets = [
        PLAN / "current_v6_master_plan.md",
        PLAN / "next_task_pointer.md",
        ROOT / "docs/status/CURRENT_PROJECT_STATUS.md",
        ROOT / "docs/CONTENTOPS_FINAL_AUTOMATION_PIPELINE_READINESS_REPORT.md",
    ]
    stale = [
        "blocked_requires_chrome_extension_file_url_access",
        "substack not yet public",
        "youtube remains future text/image",
        "hard truncation is acceptable",
    ]
    for path in targets:
        text = _read(path).lower()
        assert not any(fragment in text for fragment in stale), path


def test_platform_registry_matches_status_and_requires_strict_readback() -> None:
    status = json.loads(_read(STATUS_PATH))
    contract = json.loads(_read(PLAN / "platform_delivery_contract_v1.json"))
    assert contract["canonical_runner"] == status["canonical_backend_runner"]
    assert contract["canonical_edge_profile"] == status["canonical_browser_profile"]
    assert set(status["platform_matrix"]).issubset(set(contract["destinations"]))
    assert "public_readback_mismatch" in contract["failure_conditions"]
