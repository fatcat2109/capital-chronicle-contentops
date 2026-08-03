"""
Test Wave 01 Master Authority and Metadata Consistency v1

Asserts that authority documents and JSON files agree on Wave 01 status,
commit roles, test counts, next task, and inventory schema across the repo.
"""

import json
import pathlib
import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

EXPECTED_CLASSIFICATION = "PASS_WAVE01_CANONICAL_ORCHESTRATOR_BOUNDARY_ACCEPTED_AND_MERGED"
EXPECTED_COMPLETED_TASK = "TASK_CONTENTOPS_WAVE01_ACCEPTANCE_MASTER_MERGE_AND_CLI_COVERAGE_RECONCILIATION_V1"
EXPECTED_NEXT_TASK = "TASK_CONTENTOPS_DURABLE_OPERATIONAL_STORE_AND_CANONICAL_STATE_MACHINE_V1"
EXPECTED_WAVE01_STATUS = "COMPLETE_ACCEPTED_AND_MERGED"
EXPECTED_WAVE02_STATUS = "NEXT_NOT_STARTED"

EXPECTED_PRE_MERGE_MASTER_SHA = "a0c9d0a67e39c614d5a80cd758f219dcac9b11ff"
EXPECTED_SOURCE_COMMIT_1 = "7300517ca3861c2962df06d443ad0c0916396f9f"
EXPECTED_SOURCE_COMMIT_2 = "7d7d55039a68b4dbaec631ac75af6b7e418f7500"
EXPECTED_MERGE_COMMIT_SHA = "d5c53655435e8340b3b79ddc3779e1f833eeb311"
EXPECTED_ACCEPTANCE_COMMIT_SHA = "5c90e6d243b705f74cac40547083565f4899197b"
EXPECTED_RECONCILIATION_START_HEAD = "5c90e6d243b705f74cac40547083565f4899197b"

EXPECTED_COUNTS = {
    "registry_rows": 15,
    "canonical_rows": 1,
    "delegate_rows": 1,
    "quarantined_rows": 13,
    "operations": 12,
    "cli_families": 12,
    "focused_tests": 38,
    "compatibility_tests": 65,
    "regression_tests": 108,
    "unique_tests": 173,
    "closure_tests": 7,
}


def load_json_any_encoding(path: pathlib.Path) -> dict:
    content = path.read_bytes()
    for encoding in ("utf-8-sig", "utf-8"):
        try:
            return json.loads(content.decode(encoding))
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue
    raise ValueError(f"Could not parse JSON at {path}")


def test_json_status_authority():
    status_path = REPO_ROOT / "docs" / "status" / "current_project_status.json"
    assert status_path.is_file(), "current_project_status.json must exist"

    data = load_json_any_encoding(status_path)

    assert data["last_verified_remote_sha"] == EXPECTED_ACCEPTANCE_COMMIT_SHA
    assert data["pre_merge_master_sha"] == EXPECTED_PRE_MERGE_MASTER_SHA
    assert data["source_commit_1"] == EXPECTED_SOURCE_COMMIT_1
    assert data["source_commit_2"] == EXPECTED_SOURCE_COMMIT_2
    assert data["merge_commit_sha"] == EXPECTED_MERGE_COMMIT_SHA
    assert data["acceptance_commit_sha"] == EXPECTED_ACCEPTANCE_COMMIT_SHA
    assert data["reconciliation_start_head"] == EXPECTED_RECONCILIATION_START_HEAD

    assert data["latest_completed_task"] == EXPECTED_COMPLETED_TASK
    assert data["latest_terminal_task_result"] == EXPECTED_CLASSIFICATION
    assert data["current_task_classification"] == EXPECTED_CLASSIFICATION

    wave_data = data.get("post_v1_canonical_production_entrypoint_and_legacy_quarantine_v1", {})
    assert wave_data.get("classification") == EXPECTED_CLASSIFICATION
    assert wave_data.get("completed_task") == EXPECTED_COMPLETED_TASK
    assert wave_data.get("wave_01_status") == EXPECTED_WAVE01_STATUS
    assert wave_data.get("wave_02_status") == EXPECTED_WAVE02_STATUS
    assert wave_data.get("next_action") == EXPECTED_NEXT_TASK

    assert wave_data.get("registry_entrypoint_count") == EXPECTED_COUNTS["registry_rows"]
    assert wave_data.get("canonical_entrypoint_count") == EXPECTED_COUNTS["canonical_rows"]
    assert wave_data.get("delegated_entrypoint_count") == EXPECTED_COUNTS["delegate_rows"]
    assert wave_data.get("quarantined_entrypoint_count") == EXPECTED_COUNTS["quarantined_rows"]
    assert wave_data.get("canonical_operation_count") == EXPECTED_COUNTS["operations"]
    assert wave_data.get("live_capable_canonical_cli_family_count") == EXPECTED_COUNTS["cli_families"]
    assert wave_data.get("focused_enforcement_test_count") == EXPECTED_COUNTS["focused_tests"]
    assert wave_data.get("canonical_compatibility_test_count") == EXPECTED_COUNTS["compatibility_tests"]
    assert wave_data.get("wave01_regression_matrix_test_count") == EXPECTED_COUNTS["regression_tests"]
    assert wave_data.get("unique_compatibility_and_regression_test_count") == EXPECTED_COUNTS["unique_tests"]


def test_manifest_authority():
    manifest_path = REPO_ROOT / "docs" / "automation" / "CONTENTOPS_CANONICAL_PRODUCTION_ENTRYPOINT_AND_LEGACY_LIVE_PATH_QUARANTINE_V1" / "final_manifest.json"
    assert manifest_path.is_file(), "final_manifest.json must exist"

    data = load_json_any_encoding(manifest_path)
    assert data["schema_version"] == "contentops.wave01_final_manifest.v1"
    assert data["accepted_classification"] == EXPECTED_CLASSIFICATION
    assert data["accepted_task"] == EXPECTED_COMPLETED_TASK

    commit_topo = data.get("commit_topology", {})
    assert commit_topo.get("pre_merge_master") == EXPECTED_PRE_MERGE_MASTER_SHA
    assert commit_topo.get("source_commits") == [EXPECTED_SOURCE_COMMIT_1, EXPECTED_SOURCE_COMMIT_2]
    assert commit_topo.get("merge_commit") == EXPECTED_MERGE_COMMIT_SHA
    assert commit_topo.get("accepted_master_commit_observed_before_reconciliation") == EXPECTED_ACCEPTANCE_COMMIT_SHA
    assert commit_topo.get("reconciliation_start_head") == EXPECTED_RECONCILIATION_START_HEAD
    assert commit_topo.get("completing_commit_sha") is None

    registry = data.get("registry", {})
    assert registry.get("entrypoint_count") == EXPECTED_COUNTS["registry_rows"]
    action_counts = registry.get("action_counts", {})
    assert action_counts.get("CANONICAL") == EXPECTED_COUNTS["canonical_rows"]
    assert action_counts.get("DELEGATE") == EXPECTED_COUNTS["delegate_rows"]
    assert action_counts.get("QUARANTINED") == EXPECTED_COUNTS["quarantined_rows"]

    op_coverage = data.get("canonical_operation_coverage", {})
    assert op_coverage.get("operation_count") == EXPECTED_COUNTS["operations"]
    assert op_coverage.get("live_cli_family_count") == EXPECTED_COUNTS["cli_families"]

    val = data.get("validation", {})
    assert val.get("focused_enforcement_pytest", {}).get("test_count") == EXPECTED_COUNTS["focused_tests"]
    assert val.get("canonical_compatibility_pytest", {}).get("test_count") == EXPECTED_COUNTS["compatibility_tests"]
    assert val.get("wave01_regression_matrix_pytest", {}).get("test_count") == EXPECTED_COUNTS["regression_tests"]
    assert val.get("unique_tests_across_compatibility_and_regression_matrices") == EXPECTED_COUNTS["unique_tests"]
    assert val.get("final_automation_closure_pytest", {}).get("test_count") == EXPECTED_COUNTS["closure_tests"]
    assert val.get("wave01_master_authority_and_metadata_consistency_pytest", {}).get("test_count") == 5


def test_changed_file_inventory_authority():
    inventory_path = REPO_ROOT / "docs" / "automation" / "CONTENTOPS_CANONICAL_PRODUCTION_ENTRYPOINT_AND_LEGACY_LIVE_PATH_QUARANTINE_V1" / "changed_file_inventory.json"
    assert inventory_path.is_file(), "changed_file_inventory.json must exist"

    data = load_json_any_encoding(inventory_path)
    assert data["schema_version"] == "contentops.wave01_phase_aware_changed_file_inventory.v1"
    assert data["reconciliation_start_head"] == EXPECTED_RECONCILIATION_START_HEAD

    assert "source_implementation_delta" in data
    assert "merged_wave01_tree" in data
    assert "post_merge_acceptance_delta" in data
    assert "reconciliation_staged_paths" in data

    assert data["source_implementation_delta"]["path_count"] == 44
    assert data["merged_wave01_tree"]["path_count"] == 44
    assert data["post_merge_acceptance_delta"]["path_count"] == 11
    assert data["reconciliation_staged_paths"]["path_count"] == len(data["reconciliation_staged_paths"]["files"])


def _extract_section(content: str, heading_substr: str) -> str:
    lines = content.splitlines()
    section_lines = []
    recording = False
    for line in lines:
        if line.startswith("#") and heading_substr.lower() in line.lower():
            recording = True
            section_lines.append(line)
            continue
        if recording:
            if line.startswith("#"):
                break
            section_lines.append(line)
    return "\n".join(section_lines)


def test_doc_pointers_agree():
    agents_md = (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8")
    agents_current = _extract_section(agents_md, "10. Current next task")
    assert EXPECTED_CLASSIFICATION in agents_current
    assert EXPECTED_WAVE01_STATUS in agents_current
    assert EXPECTED_WAVE02_STATUS in agents_current
    assert EXPECTED_NEXT_TASK in agents_current

    context_md = (REPO_ROOT / "docs" / "CURRENT_CONTEXT.md").read_text(encoding="utf-8")
    context_current = _extract_section(context_md, "Current next task")
    assert EXPECTED_CLASSIFICATION in context_current
    assert EXPECTED_WAVE01_STATUS in context_current
    assert EXPECTED_WAVE02_STATUS in context_current
    assert EXPECTED_NEXT_TASK in context_current

    bootstrap_md = (REPO_ROOT / "docs" / "AI_BUILDER_BOOTSTRAP.md").read_text(encoding="utf-8")
    bootstrap_current = _extract_section(bootstrap_md, "7. Current next task")
    assert EXPECTED_CLASSIFICATION in bootstrap_current
    assert EXPECTED_WAVE01_STATUS in bootstrap_current
    assert EXPECTED_WAVE02_STATUS in bootstrap_current
    assert EXPECTED_NEXT_TASK in bootstrap_current

    status_md = (REPO_ROOT / "docs" / "status" / "CURRENT_PROJECT_STATUS.md").read_text(encoding="utf-8")
    assert EXPECTED_CLASSIFICATION in status_md
    assert EXPECTED_COMPLETED_TASK in status_md
    assert EXPECTED_NEXT_TASK in status_md

    full_status_md = (REPO_ROOT / "docs" / "status" / "CURRENT_FULL_AUTOMATION_FINAL_PRODUCT_STATUS.md").read_text(encoding="utf-8")
    full_status_current = _extract_section(full_status_md, "Current next task")
    assert EXPECTED_CLASSIFICATION in full_status_current
    assert EXPECTED_WAVE01_STATUS in full_status_current
    assert EXPECTED_WAVE02_STATUS in full_status_current
    assert EXPECTED_NEXT_TASK in full_status_current

    master_plan_md = (REPO_ROOT / "docs" / "automation" / "V6_FINAL_PRODUCT_EXECUTION_PLAN" / "current_v6_master_plan.md").read_text(encoding="utf-8")
    assert EXPECTED_CLASSIFICATION in master_plan_md
    assert "| 01 | Canonical entrypoint and legacy live-path quarantine | COMPLETE_ACCEPTED_AND_MERGED |" in master_plan_md
    assert ("| 02 | Durable operational store/state machine | NEXT_NOT_STARTED |" in master_plan_md or "| 02 | Durable operational store/state machine | COMPLETE_AWAITING_INDEPENDENT_AUDIT |" in master_plan_md)

    maturity_ledger_md = (REPO_ROOT / "docs" / "automation" / "V6_FINAL_PRODUCT_EXECUTION_PLAN" / "post_v1_full_automation_maturity_ledger.md").read_text(encoding="utf-8")
    assert EXPECTED_CLASSIFICATION in maturity_ledger_md
    assert "| 01 | Canonical production entrypoint and legacy live-path quarantine | COMPLETE_ACCEPTED_AND_MERGED |" in maturity_ledger_md

    v6_25_md = (REPO_ROOT / "docs" / "automation" / "V6_FINAL_PRODUCT_EXECUTION_PLAN" / "v6_25_task_ledger.md").read_text(encoding="utf-8")
    v6_25_current = _extract_section(v6_25_md, "Current next route")
    assert EXPECTED_CLASSIFICATION in v6_25_current
    assert EXPECTED_WAVE01_STATUS in v6_25_current
    assert (EXPECTED_WAVE02_STATUS in v6_25_current or "COMPLETE_AWAITING_INDEPENDENT_AUDIT" in v6_25_current)
    assert (EXPECTED_NEXT_TASK in v6_25_current or "TASK_CONTENTOPS_EXACT_APPROVAL_ENVELOPE_TRANSACTIONAL_OUTBOX_AND_EXPIRY_V1" in v6_25_current)

    next_pointer_md = (REPO_ROOT / "docs" / "automation" / "V6_FINAL_PRODUCT_EXECUTION_PLAN" / "next_task_pointer.md").read_text(encoding="utf-8")
    assert EXPECTED_CLASSIFICATION in next_pointer_md
    assert (EXPECTED_NEXT_TASK in next_pointer_md or "TASK_CONTENTOPS_EXACT_APPROVAL_ENVELOPE_TRANSACTIONAL_OUTBOX_AND_EXPIRY_V1" in next_pointer_md)
    assert "Pre-merge target master HEAD:" in next_pointer_md
    assert EXPECTED_PRE_MERGE_MASTER_SHA in next_pointer_md

    wave01_readme = (REPO_ROOT / "docs" / "automation" / "CONTENTOPS_CANONICAL_PRODUCTION_ENTRYPOINT_AND_LEGACY_LIVE_PATH_QUARANTINE_V1" / "README.md").read_text(encoding="utf-8")
    readme_auth = _extract_section(wave01_readme, "Authority")
    assert "Pre-merge target master HEAD:" in readme_auth
    assert EXPECTED_PRE_MERGE_MASTER_SHA in readme_auth
    assert "Merge commit:" in readme_auth
    assert EXPECTED_MERGE_COMMIT_SHA in readme_auth
    assert "Accepted master commit:" in readme_auth
    assert EXPECTED_ACCEPTANCE_COMMIT_SHA in readme_auth
    assert "Reconciliation start HEAD:" in readme_auth
    assert EXPECTED_RECONCILIATION_START_HEAD in readme_auth
    assert "Completing commit SHA: null" in readme_auth
    assert "Target HEAD: `" + EXPECTED_PRE_MERGE_MASTER_SHA not in readme_auth
    assert "Target HEAD: " + EXPECTED_PRE_MERGE_MASTER_SHA not in readme_auth

    # Negative assertions across all current sections
    current_sections = [
        agents_current,
        context_current,
        bootstrap_current,
        full_status_current,
        v6_25_current,
    ]
    disallowed_strings = [
        "PASS_CANONICAL_PRODUCTION_ENTRYPOINT_AND_LEGACY_LIVE_PATH_QUARANTINE_V1_AWAITING_INDEPENDENT_AUDIT",
        "Wave 01 status: COMPLETE_AWAITING_INDEPENDENT_AUDIT",
        "Wave 01 is complete awaiting independent audit",
    ]
    for section_text in current_sections:
        for disallowed in disallowed_strings:
            assert disallowed not in section_text, f"Disallowed string '{disallowed}' found in current section: {section_text}"
        assert "Wave 01 is NEXT_NOT_STARTED" not in section_text
        assert "Wave 01 NEXT_NOT_STARTED" not in section_text


def test_all_docs_json_valid():
    json_paths = list((REPO_ROOT / "docs").rglob("*.json"))
    assert len(json_paths) > 0, "There should be JSON files under docs/"

    for json_path in json_paths:
        load_json_any_encoding(json_path)
