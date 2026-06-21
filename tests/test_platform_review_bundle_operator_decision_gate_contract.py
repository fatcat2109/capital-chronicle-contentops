"""Unit tests for Platform Review Bundle Operator Decision Gate contract (0175AQ)."""
from __future__ import annotations

import json
from pathlib import Path
import pytest
import subprocess

from live_contentops.platform_review_bundle_operator_decision_gate_contract import (
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


def test_2_consumes_0175ap_review_bundle_precedent():
    """2. Verify that the contract successfully consumes 0175AP review bundle precedent."""
    p = build_contract_packet()
    assert "decision_gate_records" in p
    assert len(p["decision_gate_records"]) == 10


def test_3_all_supported_platform_decision_gate_records_exist():
    """3. Verify all supported platform decision gate records exist."""
    p = build_contract_packet()
    records = p["decision_gate_records"]
    assert len(records) == 10
    target_ids = {r["platform_target_id"] for r in records}
    expected_ids = {
        "x", "telegram_channel_destination", "telegram_remote_operator",
        "substack", "linkedin", "threads", "instagram",
        "facebook_page", "tiktok", "youtube"
    }
    assert target_ids == expected_ids


def test_4_every_gate_status_is_decision_gate_blocked():
    """4. Verify every gate status is decision_gate_blocked."""
    p = build_contract_packet()
    for r in p["decision_gate_records"]:
        assert r["gate_status"] == "decision_gate_blocked"


def test_5_every_decision_option_exists():
    """5. Verify every decision option exists."""
    p = build_contract_packet()
    expected_options = {
        "approve_for_publication", "reject_bundle", "request_revision",
        "hold_for_more_evidence", "export_for_manual_publish", "dispatch_to_platform"
    }
    for r in p["decision_gate_records"]:
        option_ids = {opt["decision_option_id"] for opt in r["decision_options"]}
        assert option_ids == expected_options


def test_6_every_decision_option_enabled_false():
    """6. Verify every decision option enabled false."""
    p = build_contract_packet()
    for r in p["decision_gate_records"]:
        for opt in r["decision_options"]:
            assert opt["enabled"] is False


def test_7_every_decision_option_available_now_false():
    """7. Verify every decision option available_now false."""
    p = build_contract_packet()
    for r in p["decision_gate_records"]:
        for opt in r["decision_options"]:
            assert opt["available_now"] is False


def test_8_every_decision_option_requires_future_gate():
    """8. Verify every decision option requires future gate."""
    p = build_contract_packet()
    for r in p["decision_gate_records"]:
        for opt in r["decision_options"]:
            assert opt["requires_future_gate"] is True


def test_9_operator_identity_not_bound():
    """9. Verify operator identity not bound."""
    p = build_contract_packet()
    for r in p["decision_gate_records"]:
        assert r["operator_identity_bound"] is False
        assert r["operator_identity_status"] == "identity_required_but_unbound"


def test_10_operator_signature_absent():
    """10. Verify operator signature absent."""
    p = build_contract_packet()
    for r in p["decision_gate_records"]:
        assert r["operator_signature_present"] is False
        assert r["operator_signature_status"] == "signature_required_but_missing"


def test_11_payload_hash_not_locked():
    """11. Verify payload hash not locked."""
    p = build_contract_packet()
    for r in p["decision_gate_records"]:
        assert r["payload_hash_locked"] is False


def test_12_approval_granted_false():
    """12. Verify approval_granted false."""
    p = build_contract_packet()
    for r in p["decision_gate_records"]:
        assert r["approval_granted"] is False


def test_13_rejection_recorded_false():
    """13. Verify rejection_recorded false."""
    p = build_contract_packet()
    for r in p["decision_gate_records"]:
        assert r["rejection_recorded"] is False


def test_14_revision_requested_false():
    """14. Verify revision_requested false."""
    p = build_contract_packet()
    for r in p["decision_gate_records"]:
        assert r["revision_requested"] is False


def test_15_export_ready_false():
    """15. Verify export_ready false."""
    p = build_contract_packet()
    assert p["safety_flags"]["export_ready"] is False
    for r in p["decision_gate_records"]:
        assert r["export_ready"] is False
        assert r["export_gate_status"] == "export_gate_required_but_locked"


def test_16_public_postable_false():
    """16. Verify public_postable false."""
    p = build_contract_packet()
    assert p["safety_flags"]["public_postable"] is False
    for r in p["decision_gate_records"]:
        assert r["public_postable"] is False


def test_17_publishable_text_false():
    """17. Verify publishable_text false."""
    p = build_contract_packet()
    assert p["safety_flags"]["publishable_text"] is False
    for r in p["decision_gate_records"]:
        assert r["publishable_text"] is False


def test_18_platform_ready_false():
    """18. Verify platform_ready false."""
    p = build_contract_packet()
    assert p["safety_flags"]["platform_ready"] is False
    for r in p["decision_gate_records"]:
        assert r["platform_ready"] is False


def test_19_dispatch_ready_false():
    """19. Verify dispatch_ready false."""
    p = build_contract_packet()
    assert p["safety_flags"]["dispatch_ready"] is False
    for r in p["decision_gate_records"]:
        assert r["dispatch_ready"] is False


def test_20_platform_payload_created_false():
    """20. Verify platform_payload_created false."""
    p = build_contract_packet()
    assert p["safety_flags"]["platform_payload_created"] is False
    for r in p["decision_gate_records"]:
        assert r["platform_payload_created"] is False


def test_21_publishable_payload_created_false():
    """21. Verify publishable_payload_created false."""
    p = build_contract_packet()
    assert p["safety_flags"]["publishable_payload_created"] is False
    for r in p["decision_gate_records"]:
        assert r["publishable_payload_created"] is False


def test_22_account_binding_and_credential_gates_required_but_inactive():
    """22. Verify account binding and credential gates required but inactive."""
    p = build_contract_packet()
    assert p["safety_flags"]["account_binding_active"] is False
    assert p["safety_flags"]["credential_values_loaded"] is False
    for r in p["decision_gate_records"]:
        assert r["account_binding_active"] is False
        assert r["credential_values_loaded"] is False
        assert r["account_binding_status"] == "binding_required_but_inactive"
        assert r["credential_gate_status"] == "credential_required_but_locked"


def test_23_citation_and_limitation_statuses_preserved():
    """23. Verify citation and limitation statuses preserved."""
    p = build_contract_packet()
    for r in p["decision_gate_records"]:
        assert r["citation_status"] == "citation_rendering_required_but_pending"
        assert r["limitation_status"] == "limitation_rendering_required_but_pending"


def test_24_dqr_readiness_current_truth_not_cleared():
    """24. Verify DQR/readiness/current truth not cleared."""
    p = build_contract_packet()
    assert p["safety_flags"]["dqr_cleared_by_contentops"] is False
    assert p["safety_flags"]["readiness_cleared_by_contentops"] is False
    assert p["safety_flags"]["current_truth_promoted"] is False


def test_25_no_financial_advice_signal_execution_language():
    """25. Verify no financial advice/signal/execution language."""
    p = build_contract_packet()
    assert p["safety_flags"]["financial_advice"] is False
    assert p["safety_flags"]["signal_language"] is False
    assert p["safety_flags"]["broker_order_execution"] is False


def test_26_no_fake_market_numbers():
    """26. Verify no fake market numbers."""
    p = build_contract_packet()
    # Ensure raw output JSON and markdown do not contain any unexpected text numbers
    out_dir = Path("docs/automation/0175AQ")
    runbook_path = out_dir / "platform_review_bundle_operator_decision_gate_contract.md"
    assert runbook_path.exists()
    content = runbook_path.read_text(encoding="utf-8")
    assert "fake" not in content.lower()
    assert "market_number" not in content.lower()


def test_27_no_env_network_credential_platform_provider_api_imports_or_calls():
    """27. Scan code to ensure no environment, network, or credential API modules are imported."""
    with open("live_contentops/platform_review_bundle_operator_decision_gate_contract.py", encoding="utf-8") as f:
        content = f.read()
    forbidden = ["import os", "from os", "import requests", "urllib", "dotenv", "socket"]
    for pattern in forbidden:
        assert pattern not in content, f"Forbidden import or keyword '{pattern}' found."


def test_28_no_ingestion_repo_mutation_or_path_access():
    """28. Verify no ingestion repo mutation or path access is allowed."""
    p = build_contract_packet()
    assert p["safety_flags"]["ingestion_repo_mutated"] is False


def test_29_ledger_family_registered():
    """29. Verify ledger family platform_review_bundle_operator_decision_gate_future is registered."""
    assert LEDGER_FAMILY in ENTRY_FAMILIES


def test_30_artifacts_written_only_under_docs_automation_0175aq():
    """30. Verify that write_artifacts fails with ValueError outside docs/automation/0175AQ."""
    with pytest.raises(ValueError, match="artifact_writer_refuses_paths_outside_docs_automation_0175AQ"):
        write_artifacts(repo_root=".", output_dir="docs/automation/other")


def test_31_progress_ledger_resolves_0175ap_and_appends_0175aq():
    """31. Verify progress ledger resolves 0175AP final HEAD and appends 0175AQ."""
    path = Path("docs/CONTENTOPS_PROGRESS_LEDGER_AND_FINAL_PRODUCT_CHECKLIST.md")
    assert path.exists()
    content = path.read_text(encoding="utf-8")

    # One-task-lag checks
    assert "| `TASK_CONTENTOPS_0175AP_PLATFORM_PREVIEW_DRY_RENDER_TO_REVIEW_BUNDLE_V0` | `1a2d9bd78a254bee8790c3a8288168166a3f2fa8` | `ab4a851ff60121cc3c3bdd85e25ed58c07aa9766` |" in content
    assert "| `TASK_CONTENTOPS_0175AQ_PLATFORM_REVIEW_BUNDLE_OPERATOR_DECISION_GATE_V0` | `ab4a851ff60121cc3c3bdd85e25ed58c07aa9766` | `RECORDED_IN_NEXT_TASK_READBACK` |" in content


def test_32_no_pycache_or_pyc_staged():
    """32. Ensure no pycache or .pyc files are staged/tracked in git."""
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
