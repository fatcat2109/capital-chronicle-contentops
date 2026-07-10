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
    assert status["latest_accepted_task"] in master
    assert status["latest_accepted_task"] in ledger
    assert status["latest_accepted_task"] in pointer
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
    assert "hard_or_mid_sentence_truncation" in contract["failure_conditions"]
    assert contract["overflow_policy"] == "sentence_and_paragraph_aware_balanced_root_reply_chain"
    assert contract["editorial_gate"] == "live_contentops.tier1_editorial_quality_v1"
    assert contract["editorial_gate_policy"] == "deterministic_and_bounded_llm_must_both_pass_llm_cannot_override_deterministic_blockers"


def test_agents_fast_ship_never_authorizes_raw_secret_output() -> None:
    agents = _read(ROOT / "AGENTS.md").lower()
    assert "fast ship" in agents
    assert "never authorizes printing" in agents
    for term in ("raw environment values", "tokens", "cookies", "localstorage", "sessionstorage"):
        assert term in agents
