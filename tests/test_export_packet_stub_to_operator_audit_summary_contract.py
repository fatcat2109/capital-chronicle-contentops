"""Unit tests for Export Packet Stub to Operator Audit Summary contract (0175AT)."""
from __future__ import annotations

import json
from pathlib import Path
import pytest
import subprocess

from live_contentops.export_packet_stub_to_operator_audit_summary_contract import (
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


def test_2_consumes_0175as_precedent():
    """2. Verify that the contract successfully consumes 0175AS export packet stub precedent."""
    p = build_contract_packet()
    assert "audit_records" in p
    assert len(p["audit_records"]) == 10


def test_3_all_supported_platform_audit_summary_records_exist():
    """3. Verify all supported platform audit summary records exist."""
    p = build_contract_packet()
    records = p["audit_records"]
    assert len(records) == 10
    target_ids = {r["platform_target_id"] for r in records}
    expected_ids = {
        "x", "telegram_channel_destination", "telegram_remote_operator",
        "substack", "linkedin", "threads", "instagram",
        "facebook_page", "tiktok", "youtube"
    }
    assert target_ids == expected_ids


def test_4_every_audit_summary_status_is_operator_audit_summary_blocked():
    """4. Verify every audit summary status is operator_audit_summary_blocked."""
    p = build_contract_packet()
    for r in p["audit_records"]:
        assert r["audit_summary_status"] == "operator_audit_summary_blocked"


def test_5_every_manual_export_status_is_manual_export_blocked():
    """5. Verify every manual_export_status is manual_export_blocked."""
    p = build_contract_packet()
    for r in p["audit_records"]:
        assert r["manual_export_status"] == "manual_export_blocked"


def test_6_every_invariant_exists():
    """6. Verify every invariant exists in the record."""
    p = build_contract_packet()
    expected_invariants = {
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
        "require_future_manual_publish_record_precheck"
    }
    for r in p["audit_records"]:
        inv_ids = {inv["invariant_id"] for inv in r["invariants"]}
        assert inv_ids == expected_invariants


def test_7_every_invariant_passed_true_for_blocked_state_preservation():
    """7. Verify every invariant passed true for blocked-state preservation."""
    p = build_contract_packet()
    for r in p["audit_records"]:
        for inv in r["invariants"]:
            assert inv["passed"] is True


def test_8_every_required_finding_exists():
    """8. Verify every required finding exists."""
    p = build_contract_packet()
    expected_findings = {
        "finding_export_stub_blocked",
        "finding_no_publishable_text",
        "finding_no_export_outputs",
        "finding_no_operator_signature",
        "finding_payload_hash_not_locked",
        "finding_citations_unresolved",
        "finding_limitations_unresolved",
        "finding_dqr_readiness_unresolved"
    }
    for r in p["audit_records"]:
        finding_ids = {f["finding_id"] for f in r["findings"]}
        assert finding_ids == expected_findings
        for f in r["findings"]:
            assert f["active"] is True


def test_9_export_ready_false():
    """9. Verify export_ready false."""
    p = build_contract_packet()
    assert p["safety_flags"]["export_ready"] is False
    for r in p["audit_records"]:
        assert r["export_ready"] is False


def test_10_manual_export_allowed_false():
    """10. Verify manual_export_allowed false."""
    p = build_contract_packet()
    assert p["safety_flags"]["manual_export_allowed"] is False
    for r in p["audit_records"]:
        assert r["manual_export_allowed"] is False


def test_11_export_file_created_false():
    """11. Verify export_file_created false."""
    p = build_contract_packet()
    assert p["safety_flags"]["export_file_created"] is False
    for r in p["audit_records"]:
        assert r["export_file_created"] is False


def test_12_clipboard_payload_created_false():
    """12. Verify clipboard_payload_created false."""
    p = build_contract_packet()
    assert p["safety_flags"]["clipboard_payload_created"] is False
    for r in p["audit_records"]:
        assert r["clipboard_payload_created"] is False


def test_13_download_artifact_created_false():
    """13. Verify download_artifact_created false."""
    p = build_contract_packet()
    assert p["safety_flags"]["download_artifact_created"] is False
    for r in p["audit_records"]:
        assert r["download_artifact_created"] is False


def test_14_publishable_payload_created_false():
    """14. Verify publishable_payload_created false."""
    p = build_contract_packet()
    assert p["safety_flags"]["publishable_payload_created"] is False
    for r in p["audit_records"]:
        assert r["publishable_payload_created"] is False


def test_15_platform_payload_created_false():
    """15. Verify platform_payload_created false."""
    p = build_contract_packet()
    assert p["safety_flags"]["platform_payload_created"] is False
    for r in p["audit_records"]:
        assert r["platform_payload_created"] is False


def test_16_public_postable_false():
    """16. Verify public_postable false."""
    p = build_contract_packet()
    assert p["safety_flags"]["public_postable"] is False
    for r in p["audit_records"]:
        assert r["public_postable"] is False


def test_17_publishable_text_false():
    """17. Verify publishable_text false."""
    p = build_contract_packet()
    assert p["safety_flags"]["publishable_text"] is False
    for r in p["audit_records"]:
        assert r["publishable_text"] is False


def test_18_platform_ready_false():
    """18. Verify platform_ready false."""
    p = build_contract_packet()
    assert p["safety_flags"]["platform_ready"] is False
    for r in p["audit_records"]:
        assert r["platform_ready"] is False


def test_19_dispatch_ready_false():
    """19. Verify dispatch_ready false."""
    p = build_contract_packet()
    assert p["safety_flags"]["dispatch_ready"] is False
    for r in p["audit_records"]:
        assert r["dispatch_ready"] is False


def test_20_approval_granted_false():
    """20. Verify approval_granted false."""
    p = build_contract_packet()
    assert p["safety_flags"]["approval_granted"] is False
    for r in p["audit_records"]:
        assert r["approval_granted"] is False


def test_21_operator_identity_not_bound():
    """21. Verify operator identity not bound."""
    p = build_contract_packet()
    for r in p["audit_records"]:
        assert r["operator_identity_bound"] is False
        assert r["operator_identity_status"] == "identity_required_but_unbound"


def test_22_operator_signature_absent():
    """22. Verify operator signature absent."""
    p = build_contract_packet()
    for r in p["audit_records"]:
        assert r["operator_signature_present"] is False
        assert r["operator_signature_status"] == "signature_required_but_missing"


def test_23_payload_hash_not_locked():
    """23. Verify payload hash not locked."""
    p = build_contract_packet()
    for r in p["audit_records"]:
        assert r["payload_hash_locked"] is False


def test_24_account_binding_and_credential_gates_required_but_inactive():
    """24. Verify account binding and credential gates required but inactive."""
    p = build_contract_packet()
    assert p["safety_flags"]["account_binding_active"] is False
    assert p["safety_flags"]["credential_values_loaded"] is False
    for r in p["audit_records"]:
        assert r["account_binding_active"] is False
        assert r["credential_values_loaded"] is False
        assert r["account_binding_status"] == "binding_required_but_inactive"
        assert r["credential_gate_status"] == "credential_required_but_locked"


def test_25_citation_and_limitation_statuses_preserved():
    """25. Verify citation and limitation statuses preserved."""
    p = build_contract_packet()
    for r in p["audit_records"]:
        assert r["citation_status"] == "citation_rendering_required_but_pending"
        assert r["limitation_status"] == "limitation_rendering_required_but_pending"


def test_26_dqr_readiness_current_truth_not_cleared():
    """26. Verify DQR/readiness/current truth not cleared."""
    p = build_contract_packet()
    assert p["safety_flags"]["dqr_cleared_by_contentops"] is False
    assert p["safety_flags"]["readiness_cleared_by_contentops"] is False
    assert p["safety_flags"]["current_truth_promoted"] is False


def test_27_no_financial_advice_signal_execution_language():
    """27. Verify no financial advice/signal/execution language."""
    p = build_contract_packet()
    assert p["safety_flags"]["financial_advice"] is False
    assert p["safety_flags"]["signal_language"] is False
    assert p["safety_flags"]["broker_order_execution"] is False


def test_28_no_fake_market_numbers():
    """28. Verify no fake market numbers."""
    p = build_contract_packet()
    assert p["safety_flags"]["financial_advice"] is False
    assert p["safety_flags"]["broker_order_execution"] is False
    
    out_dir = Path("docs/automation/0175AT")
    runbook_path = out_dir / "export_packet_stub_to_operator_audit_summary_contract.md"
    assert runbook_path.exists()
    content = runbook_path.read_text(encoding="utf-8")
    assert "fake" not in content.lower()


def test_29_no_env_network_credential_platform_provider_api_imports_or_calls():
    """29. Scan code to ensure no environment, network, or credential API modules are imported."""
    with open("live_contentops/export_packet_stub_to_operator_audit_summary_contract.py", encoding="utf-8") as f:
        content = f.read()
    forbidden = ["import os", "from os", "import requests", "urllib", "dotenv", "socket"]
    for pattern in forbidden:
        assert pattern not in content, f"Forbidden import or keyword '{pattern}' found."


def test_30_no_ingestion_repo_mutation_or_path_access():
    """30. Verify no ingestion repo mutation or path access is allowed."""
    p = build_contract_packet()
    assert p["safety_flags"]["ingestion_repo_mutated"] is False


def test_31_ledger_family_registered():
    """31. Verify ledger family export_packet_stub_to_operator_audit_summary_future is registered."""
    assert LEDGER_FAMILY in ENTRY_FAMILIES


def test_32_artifacts_written_only_under_docs_automation_0175at():
    """32. Verify that write_artifacts fails with ValueError outside docs/automation/0175AT."""
    with pytest.raises(ValueError, match="artifact_writer_refuses_paths_outside_docs_automation_0175AT"):
        write_artifacts(repo_root=".", output_dir="docs/automation/other")


def test_33_progress_ledger_resolves_0175as_and_appends_0175at():
    """33. Verify progress ledger resolves 0175AS final HEAD and appends 0175AT."""
    path = Path("docs/CONTENTOPS_PROGRESS_LEDGER_AND_FINAL_PRODUCT_CHECKLIST.md")
    assert path.exists()
    content = path.read_text(encoding="utf-8")

    # One-task-lag checks
    assert "| `TASK_CONTENTOPS_0175AS_MANUAL_EXPORT_PRECHECK_TO_EXPORT_PACKET_STUB_V0` | `c6ad0bcf016e1a5396aaab52f334b176e26f5c58` | `3441635cad8010a7325d83d856351275f897ce37` |" in content
    assert "| `TASK_CONTENTOPS_0175AT_EXPORT_PACKET_STUB_TO_OPERATOR_AUDIT_SUMMARY_V0` | `3441635cad8010a7325d83d856351275f897ce37` | `9cf9d9d545d14ece9fa6239dfc717baac547f3e0` |" in content


def test_34_no_pycache_or_pyc_staged():
    """34. Ensure no pycache or .pyc files are staged/tracked in git."""
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
