"""Unit tests for Operator Audit Summary to Manual Publish Record Precheck contract (0175AU)."""
from __future__ import annotations

import json
from pathlib import Path
import pytest
import subprocess

from live_contentops.operator_audit_summary_to_manual_publish_record_precheck_contract import (
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


def test_2_consumes_0175at_precedent():
    """2. Verify that the contract successfully consumes 0175AT operator audit summary precedent."""
    p = build_contract_packet()
    assert "precheck_records" in p
    assert len(p["precheck_records"]) == 10


def test_3_all_supported_platform_manual_publish_record_prechecks_exist():
    """3. Verify all supported platform manual publish record prechecks exist."""
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


def test_4_every_precheck_status_is_manual_publish_record_precheck_blocked():
    """4. Verify every precheck status is manual_publish_record_precheck_blocked."""
    p = build_contract_packet()
    for r in p["precheck_records"]:
        assert r["precheck_status"] == "manual_publish_record_precheck_blocked"


def test_5_every_invariant_exists():
    """5. Verify every invariant exists."""
    p = build_contract_packet()
    expected_invariants = {
        "no_manual_publish_record_created",
        "no_platform_publication_url_recorded",
        "no_platform_post_id_recorded",
        "no_external_publish_timestamp_recorded",
        "no_public_metrics_recorded",
        "no_export_file_created",
        "no_clipboard_payload_created",
        "no_download_artifact_created",
        "no_publishable_payload_created",
        "no_platform_payload_created",
        "no_platform_api_call",
        "no_credential_or_env_read",
        "no_account_binding_active",
        "no_scheduler",
        "no_autonomous_posting",
        "no_autonomous_reply_or_dm",
        "no_scraping",
        "no_financial_advice",
        "no_signal_language",
        "no_market_number_fabrication",
        "preserve_citation_requirements",
        "preserve_limitations",
        "preserve_dqr_readiness_blocks",
        "require_operator_signature",
        "require_payload_hash_lock",
        "require_manual_export_gate",
        "require_manual_publish_record_gate"
    }
    for r in p["precheck_records"]:
        inv_ids = {inv["invariant_id"] for inv in r["invariants"]}
        assert inv_ids == expected_invariants


def test_6_every_invariant_passed_true_for_blocked_state_preservation():
    """6. Verify every invariant passed true for blocked-state preservation."""
    p = build_contract_packet()
    for r in p["precheck_records"]:
        for inv in r["invariants"]:
            assert inv["passed"] is True


def test_7_manual_publish_record_allowed_false():
    """7. Verify manual_publish_record_allowed false."""
    p = build_contract_packet()
    assert p["safety_flags"]["manual_publish_record_allowed"] is False
    for r in p["precheck_records"]:
        assert r["manual_publish_record_allowed"] is False


def test_8_manual_publish_record_created_false():
    """8. Verify manual_publish_record_created false."""
    p = build_contract_packet()
    assert p["safety_flags"]["manual_publish_record_created"] is False
    for r in p["precheck_records"]:
        assert r["manual_publish_record_created"] is False


def test_9_platform_publication_url_recorded_false():
    """9. Verify platform_publication_url_recorded false."""
    p = build_contract_packet()
    assert p["safety_flags"]["platform_publication_url_recorded"] is False
    for r in p["precheck_records"]:
        assert r["platform_publication_url_recorded"] is False


def test_10_platform_post_id_recorded_false():
    """10. Verify platform_post_id_recorded false."""
    p = build_contract_packet()
    assert p["safety_flags"]["platform_post_id_recorded"] is False
    for r in p["precheck_records"]:
        assert r["platform_post_id_recorded"] is False


def test_11_external_publish_timestamp_recorded_false():
    """11. Verify external_publish_timestamp_recorded false."""
    p = build_contract_packet()
    assert p["safety_flags"]["external_publish_timestamp_recorded"] is False
    for r in p["precheck_records"]:
        assert r["external_publish_timestamp_recorded"] is False


def test_12_public_metrics_recorded_false():
    """12. Verify public_metrics_recorded false."""
    p = build_contract_packet()
    assert p["safety_flags"]["public_metrics_recorded"] is False
    for r in p["precheck_records"]:
        assert r["public_metrics_recorded"] is False


def test_13_export_ready_false():
    """13. Verify export_ready false."""
    p = build_contract_packet()
    assert p["safety_flags"]["export_ready"] is False
    for r in p["precheck_records"]:
        assert r["export_ready"] is False


def test_14_manual_export_allowed_false():
    """14. Verify manual_export_allowed false."""
    p = build_contract_packet()
    assert p["safety_flags"]["manual_export_allowed"] is False
    for r in p["precheck_records"]:
        assert r["manual_export_allowed"] is False


def test_15_export_file_created_false():
    """15. Verify export_file_created false."""
    p = build_contract_packet()
    assert p["safety_flags"]["export_file_created"] is False
    for r in p["precheck_records"]:
        assert r["export_file_created"] is False


def test_16_clipboard_payload_created_false():
    """16. Verify clipboard_payload_created false."""
    p = build_contract_packet()
    assert p["safety_flags"]["clipboard_payload_created"] is False
    for r in p["precheck_records"]:
        assert r["clipboard_payload_created"] is False


def test_17_download_artifact_created_false():
    """17. Verify download_artifact_created false."""
    p = build_contract_packet()
    assert p["safety_flags"]["download_artifact_created"] is False
    for r in p["precheck_records"]:
        assert r["download_artifact_created"] is False


def test_18_publishable_payload_created_false():
    """18. Verify publishable_payload_created false."""
    p = build_contract_packet()
    assert p["safety_flags"]["publishable_payload_created"] is False
    for r in p["precheck_records"]:
        assert r["publishable_payload_created"] is False


def test_19_platform_payload_created_false():
    """19. Verify platform_payload_created false."""
    p = build_contract_packet()
    assert p["safety_flags"]["platform_payload_created"] is False
    for r in p["precheck_records"]:
        assert r["platform_payload_created"] is False


def test_20_public_postable_false():
    """20. Verify public_postable false."""
    p = build_contract_packet()
    assert p["safety_flags"]["public_postable"] is False
    for r in p["precheck_records"]:
        assert r["public_postable"] is False


def test_21_publishable_text_false():
    """21. Verify publishable_text false."""
    p = build_contract_packet()
    assert p["safety_flags"]["publishable_text"] is False
    for r in p["precheck_records"]:
        assert r["publishable_text"] is False


def test_22_platform_ready_false():
    """22. Verify platform_ready false."""
    p = build_contract_packet()
    assert p["safety_flags"]["platform_ready"] is False
    for r in p["precheck_records"]:
        assert r["platform_ready"] is False


def test_23_dispatch_ready_false():
    """23. Verify dispatch_ready false."""
    p = build_contract_packet()
    assert p["safety_flags"]["dispatch_ready"] is False
    for r in p["precheck_records"]:
        assert r["dispatch_ready"] is False


def test_24_approval_granted_false():
    """24. Verify approval_granted false."""
    p = build_contract_packet()
    assert p["safety_flags"]["approval_granted"] is False
    for r in p["precheck_records"]:
        assert r["approval_granted"] is False


def test_25_operator_identity_not_bound():
    """25. Verify operator identity not bound."""
    p = build_contract_packet()
    for r in p["precheck_records"]:
        assert r["operator_identity_bound"] is False
        assert r["operator_identity_status"] == "identity_required_but_unbound"


def test_26_operator_signature_absent():
    """26. Verify operator signature absent."""
    p = build_contract_packet()
    for r in p["precheck_records"]:
        assert r["operator_signature_present"] is False
        assert r["operator_signature_status"] == "signature_required_but_missing"


def test_27_payload_hash_not_locked():
    """27. Verify payload hash not locked."""
    p = build_contract_packet()
    for r in p["precheck_records"]:
        assert r["payload_hash_locked"] is False


def test_28_account_binding_and_credential_gates_required_but_inactive():
    """28. Verify account binding and credential gates required but inactive."""
    p = build_contract_packet()
    assert p["safety_flags"]["account_binding_active"] is False
    assert p["safety_flags"]["credential_values_loaded"] is False
    for r in p["precheck_records"]:
        assert r["account_binding_active"] is False
        assert r["credential_values_loaded"] is False
        assert r["account_binding_status"] == "binding_required_but_inactive"
        assert r["credential_gate_status"] == "credential_required_but_locked"


def test_29_citation_and_limitation_statuses_preserved():
    """29. Verify citation and limitation statuses preserved."""
    p = build_contract_packet()
    for r in p["precheck_records"]:
        assert r["citation_status"] == "citation_rendering_required_but_pending"
        assert r["limitation_status"] == "limitation_rendering_required_but_pending"


def test_30_dqr_readiness_current_truth_not_cleared():
    """30. Verify DQR/readiness/current truth not cleared."""
    p = build_contract_packet()
    assert p["safety_flags"]["dqr_cleared_by_contentops"] is False
    assert p["safety_flags"]["readiness_cleared_by_contentops"] is False
    assert p["safety_flags"]["current_truth_promoted"] is False


def test_31_no_financial_advice_signal_execution_language():
    """31. Verify no financial advice/signal/execution language."""
    p = build_contract_packet()
    assert p["safety_flags"]["financial_advice"] is False
    assert p["safety_flags"]["signal_language"] is False
    assert p["safety_flags"]["broker_order_execution"] is False


def test_32_no_fake_market_numbers():
    """32. Verify no fake market numbers."""
    p = build_contract_packet()
    assert p["safety_flags"]["financial_advice"] is False
    assert p["safety_flags"]["broker_order_execution"] is False
    
    out_dir = Path("docs/automation/0175AU")
    runbook_path = out_dir / "operator_audit_summary_to_manual_publish_record_precheck_contract.md"
    assert runbook_path.exists()
    content = runbook_path.read_text(encoding="utf-8")
    assert "fake" not in content.lower()


def test_33_no_env_network_credential_platform_provider_api_imports_or_calls():
    """33. Scan code to ensure no environment, network, or credential API modules are imported."""
    with open("live_contentops/operator_audit_summary_to_manual_publish_record_precheck_contract.py", encoding="utf-8") as f:
        content = f.read()
    forbidden = ["import os", "from os", "import requests", "urllib", "dotenv", "socket"]
    for pattern in forbidden:
        assert pattern not in content, f"Forbidden import or keyword '{pattern}' found."


def test_34_no_ingestion_repo_mutation_or_path_access():
    """34. Verify no ingestion repo mutation or path access is allowed."""
    p = build_contract_packet()
    assert p["safety_flags"]["ingestion_repo_mutated"] is False


def test_35_ledger_family_registered():
    """35. Verify ledger family operator_audit_summary_to_manual_publish_record_precheck_future is registered."""
    assert LEDGER_FAMILY in ENTRY_FAMILIES


def test_36_artifacts_written_only_under_docs_automation_0175au():
    """36. Verify that write_artifacts fails with ValueError outside docs/automation/0175AU."""
    with pytest.raises(ValueError, match="artifact_writer_refuses_paths_outside_docs_automation_0175AU"):
        write_artifacts(repo_root=".", output_dir="docs/automation/other")


def test_37_progress_ledger_resolves_0175at_and_appends_0175au():
    """37. Verify progress ledger resolves 0175AT final HEAD and appends 0175AU."""
    path = Path("docs/CONTENTOPS_PROGRESS_LEDGER_AND_FINAL_PRODUCT_CHECKLIST.md")
    assert path.exists()
    content = path.read_text(encoding="utf-8")

    # One-task-lag checks
    assert "| `TASK_CONTENTOPS_0175AT_EXPORT_PACKET_STUB_TO_OPERATOR_AUDIT_SUMMARY_V0` | `3441635cad8010a7325d83d856351275f897ce37` | `9cf9d9d545d14ece9fa6239dfc717baac547f3e0` |" in content
    assert "| `TASK_CONTENTOPS_0175AU_OPERATOR_AUDIT_SUMMARY_TO_MANUAL_PUBLISH_RECORD_PRECHECK_V0` | `9cf9d9d545d14ece9fa6239dfc717baac547f3e0` | `RECORDED_IN_NEXT_TASK_READBACK` |" in content


def test_38_no_pycache_or_pyc_staged():
    """38. Ensure no pycache or .pyc files are staged/tracked in git."""
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
