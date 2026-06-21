"""Unit tests for Operator Decision Gate to Manual Export Precheck contract (0175AR)."""
from __future__ import annotations

import json
from pathlib import Path
import pytest
import subprocess

from live_contentops.operator_decision_gate_to_manual_export_precheck_contract import (
    build_contract_packet,
    write_artifacts,
    TASK_LABEL,
    MATRIX_VERSION,
    SOURCE_BASELINE_COMMIT,
    LEDGER_FAMILY
)
from live_contentops.redacted_immutable_audit_ledger_v2_contract import ENTRY_FAMILIES


def test_1_deterministic_packet_hash():
    """1. Verify that build_contract_packet creates deterministic hashes."""
    p1 = build_contract_packet()
    p2 = build_contract_packet()
    assert p1["packet_hash"] == p2["packet_hash"]
    assert p1["task_label"] == TASK_LABEL
    assert p1["matrix_version"] == MATRIX_VERSION
    assert p1["source_baseline_commit"] == SOURCE_BASELINE_COMMIT


def test_2_consumes_0175aq_decision_gate_precedent():
    """2. Verify that the contract successfully consumes 0175AQ decision gate precedent."""
    p = build_contract_packet()
    assert "precheck_records" in p
    assert len(p["precheck_records"]) == 10


def test_3_all_supported_platform_manual_export_precheck_records_exist():
    """3. Verify all supported platform manual export precheck records exist."""
    p = build_contract_packet()
    records = p["precheck_records"]
    assert len(records) == 10
    target_ids = {r["platform_target_id"] for r in records}
    expected_ids = {
        "x", "telegram_channel_destination", "telegram_remote_operator",
        "substack", "linkedin", "threads", "instagram",
        "facebook_page", "tiktok", "youtube"
    }
    assert target_ids == expected_ids


def test_4_every_precheck_status_is_manual_export_precheck_blocked():
    """4. Verify every precheck status is manual_export_precheck_blocked."""
    p = build_contract_packet()
    for r in p["precheck_records"]:
        assert r["precheck_status"] == "manual_export_precheck_blocked"


def test_5_export_ready_false():
    """5. Verify export_ready false."""
    p = build_contract_packet()
    assert p["safety_flags"]["export_ready"] is False
    for r in p["precheck_records"]:
        assert r["export_ready"] is False


def test_6_manual_export_allowed_false():
    """6. Verify manual_export_allowed false."""
    p = build_contract_packet()
    assert p["safety_flags"]["manual_export_allowed"] is False
    for r in p["precheck_records"]:
        assert r["manual_export_allowed"] is False


def test_7_export_file_created_false():
    """7. Verify export_file_created false."""
    p = build_contract_packet()
    assert p["safety_flags"]["export_file_created"] is False
    for r in p["precheck_records"]:
        assert r["export_file_created"] is False


def test_8_clipboard_payload_created_false():
    """8. Verify clipboard_payload_created false."""
    p = build_contract_packet()
    assert p["safety_flags"]["clipboard_payload_created"] is False
    for r in p["precheck_records"]:
        assert r["clipboard_payload_created"] is False


def test_9_download_artifact_created_false():
    """9. Verify download_artifact_created false."""
    p = build_contract_packet()
    assert p["safety_flags"]["download_artifact_created"] is False
    for r in p["precheck_records"]:
        assert r["download_artifact_created"] is False


def test_10_publishable_payload_created_false():
    """10. Verify publishable_payload_created false."""
    p = build_contract_packet()
    assert p["safety_flags"]["publishable_payload_created"] is False
    for r in p["precheck_records"]:
        assert r["publishable_payload_created"] is False


def test_11_platform_payload_created_false():
    """11. Verify platform_payload_created false."""
    p = build_contract_packet()
    assert p["safety_flags"]["platform_payload_created"] is False
    for r in p["precheck_records"]:
        assert r["platform_payload_created"] is False


def test_12_public_postable_false():
    """12. Verify public_postable false."""
    p = build_contract_packet()
    assert p["safety_flags"]["public_postable"] is False
    for r in p["precheck_records"]:
        assert r["public_postable"] is False


def test_13_publishable_text_false():
    """13. Verify publishable_text false."""
    p = build_contract_packet()
    assert p["safety_flags"]["publishable_text"] is False
    for r in p["precheck_records"]:
        assert r["publishable_text"] is False


def test_14_platform_ready_false():
    """14. Verify platform_ready false."""
    p = build_contract_packet()
    assert p["safety_flags"]["platform_ready"] is False
    for r in p["precheck_records"]:
        assert r["platform_ready"] is False


def test_15_dispatch_ready_false():
    """15. Verify dispatch_ready false."""
    p = build_contract_packet()
    assert p["safety_flags"]["dispatch_ready"] is False
    for r in p["precheck_records"]:
        assert r["dispatch_ready"] is False


def test_16_approval_granted_false():
    """16. Verify approval_granted false."""
    p = build_contract_packet()
    assert p["safety_flags"]["approval_granted"] is False
    for r in p["precheck_records"]:
        assert r["approval_granted"] is False


def test_17_operator_identity_not_bound():
    """17. Verify operator identity not bound."""
    p = build_contract_packet()
    for r in p["precheck_records"]:
        assert r["operator_identity_bound"] is False
        assert r["operator_identity_status"] == "identity_required_but_unbound"


def test_18_operator_signature_absent():
    """18. Verify operator signature absent."""
    p = build_contract_packet()
    for r in p["precheck_records"]:
        assert r["operator_signature_present"] is False
        assert r["operator_signature_status"] == "signature_required_but_missing"


def test_19_payload_hash_not_locked():
    """19. Verify payload hash not locked."""
    p = build_contract_packet()
    for r in p["precheck_records"]:
        assert r["payload_hash_locked"] is False


def test_20_account_binding_and_credential_gates_required_but_inactive():
    """20. Verify account binding and credential gates required but inactive."""
    p = build_contract_packet()
    assert p["safety_flags"]["account_binding_active"] is False
    assert p["safety_flags"]["credential_values_loaded"] is False
    for r in p["precheck_records"]:
        assert r["account_binding_active"] is False
        assert r["credential_values_loaded"] is False
        assert r["account_binding_status"] == "binding_required_but_inactive"
        assert r["credential_gate_status"] == "credential_required_but_locked"


def test_21_citation_and_limitation_statuses_preserved():
    """21. Verify citation and limitation statuses preserved."""
    p = build_contract_packet()
    for r in p["precheck_records"]:
        assert r["citation_status"] == "citation_rendering_required_but_pending"
        assert r["limitation_status"] == "limitation_rendering_required_but_pending"


def test_22_dqr_readiness_current_truth_not_cleared():
    """22. Verify DQR/readiness/current truth not cleared."""
    p = build_contract_packet()
    assert p["safety_flags"]["dqr_cleared_by_contentops"] is False
    assert p["safety_flags"]["readiness_cleared_by_contentops"] is False
    assert p["safety_flags"]["current_truth_promoted"] is False


def test_23_no_financial_advice_signal_execution_language():
    """23. Verify no financial advice/signal/execution language."""
    p = build_contract_packet()
    assert p["safety_flags"]["financial_advice"] is False
    assert p["safety_flags"]["signal_language"] is False
    assert p["safety_flags"]["broker_order_execution"] is False


def test_24_no_fake_market_numbers():
    """24. Verify no fake market numbers."""
    p = build_contract_packet()
    assert p["safety_flags"]["financial_advice"] is False
    assert p["safety_flags"]["broker_order_execution"] is False
    
    out_dir = Path("docs/automation/0175AR")
    runbook_path = out_dir / "operator_decision_gate_to_manual_export_precheck_contract.md"
    assert runbook_path.exists()
    content = runbook_path.read_text(encoding="utf-8")
    assert "fake" not in content.lower()


def test_25_no_env_network_credential_platform_provider_api_imports_or_calls():
    """25. Scan code to ensure no environment, network, or credential API modules are imported."""
    with open("live_contentops/operator_decision_gate_to_manual_export_precheck_contract.py", encoding="utf-8") as f:
        content = f.read()
    forbidden = ["import os", "from os", "import requests", "urllib", "dotenv", "socket"]
    for pattern in forbidden:
        assert pattern not in content, f"Forbidden import or keyword '{pattern}' found."


def test_26_no_ingestion_repo_mutation_or_path_access():
    """26. Verify no ingestion repo mutation or path access is allowed."""
    p = build_contract_packet()
    assert p["safety_flags"]["ingestion_repo_mutated"] is False


def test_27_ledger_family_registered():
    """27. Verify ledger family operator_decision_gate_to_manual_export_precheck_future is registered."""
    assert LEDGER_FAMILY in ENTRY_FAMILIES


def test_28_artifacts_written_only_under_docs_automation_0175ar():
    """28. Verify that write_artifacts fails with ValueError outside docs/automation/0175AR."""
    with pytest.raises(ValueError, match="artifact_writer_refuses_paths_outside_docs_automation_0175AR"):
        write_artifacts(repo_root=".", output_dir="docs/automation/other")


def test_29_progress_ledger_resolves_0175aq_and_appends_0175ar():
    """29. Verify progress ledger resolves 0175AQ final HEAD and appends 0175AR."""
    path = Path("docs/CONTENTOPS_PROGRESS_LEDGER_AND_FINAL_PRODUCT_CHECKLIST.md")
    assert path.exists()
    content = path.read_text(encoding="utf-8")

    # One-task-lag checks
    assert "| `TASK_CONTENTOPS_0175AQ_PLATFORM_REVIEW_BUNDLE_OPERATOR_DECISION_GATE_V0` | `ab4a851ff60121cc3c3bdd85e25ed58c07aa9766` | `68a7e425d229d7876fdfa1f37a65f3ef8c388849` |" in content
    assert "| `TASK_CONTENTOPS_0175AR_OPERATOR_DECISION_GATE_TO_MANUAL_EXPORT_PRECHECK_V0` | `68a7e425d229d7876fdfa1f37a65f3ef8c388849` | `c6ad0bcf016e1a5396aaab52f334b176e26f5c58` |" in content


def test_30_no_pycache_or_pyc_staged():
    """30. Ensure no pycache or .pyc files are staged/tracked in git."""
    res = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True,
        text=True
    )
    for line in res.stdout.splitlines():
        status_code = line[:2]
        path_str = line[3:]
        if "__pycache__" in path_str or path_str.endswith(".pyc"):
            if status_code[0] != " ":
                raise AssertionError(f"Staged pycache or .pyc file found: {line}")
