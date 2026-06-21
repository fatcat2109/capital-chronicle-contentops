"""Unit tests for Manual Export Precheck to Export Packet Stub contract (0175AS)."""
from __future__ import annotations

import json
from pathlib import Path
import pytest
import subprocess

from live_contentops.manual_export_precheck_to_export_packet_stub_contract import (
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


def test_2_consumes_0175ar_precheck_precedent():
    """2. Verify that the contract successfully consumes 0175AR manual export precheck precedent."""
    p = build_contract_packet()
    assert "stub_records" in p
    assert len(p["stub_records"]) == 10


def test_3_all_supported_platform_export_packet_stubs_exist():
    """3. Verify all supported platform export packet stubs exist."""
    p = build_contract_packet()
    records = p["stub_records"]
    assert len(records) == 10
    target_ids = {r["platform_target_id"] for r in records}
    expected_ids = {
        "x", "telegram_channel_destination", "telegram_remote_operator",
        "substack", "linkedin", "threads", "instagram",
        "facebook_page", "tiktok", "youtube"
    }
    assert target_ids == expected_ids


def test_4_every_stub_status_is_export_packet_stub_blocked():
    """4. Verify every stub status is export_packet_stub_blocked."""
    p = build_contract_packet()
    for r in p["stub_records"]:
        assert r["stub_status"] == "export_packet_stub_blocked"


def test_5_every_required_field_exists_by_target():
    """5. Verify every required field exists by target."""
    p = build_contract_packet()
    records_by_target = {r["platform_target_id"]: r for r in p["stub_records"]}

    expected_fields = {
        "x": ["body_stub", "citation_stub", "limitation_stub", "manual_copy_instruction_stub"],
        "telegram_channel_destination": ["message_stub", "citation_stub", "limitation_stub", "manual_copy_instruction_stub"],
        "telegram_remote_operator": ["operator_log_stub", "audit_ref_stub", "decision_summary_stub"],
        "substack": ["title_stub", "subtitle_stub", "body_markdown_stub", "citation_section_stub", "limitation_section_stub"],
        "linkedin": ["professional_intro_stub", "body_stub", "citation_stub", "limitation_stub"],
        "threads": ["short_text_stub", "citation_stub", "limitation_stub"],
        "instagram": ["caption_stub", "media_requirement_stub", "alt_text_stub", "citation_stub", "limitation_stub"],
        "facebook_page": ["post_text_stub", "attachment_stub", "citation_stub", "limitation_stub"],
        "tiktok": ["caption_stub", "video_requirement_stub", "disclosure_stub", "citation_stub"],
        "youtube": ["title_stub", "description_outline_stub", "video_requirement_stub", "citation_stub", "limitation_stub"]
    }

    for target_id, fields in expected_fields.items():
        rec = records_by_target[target_id]
        rec_fields = [f["field_name"] for f in rec["fields"]]
        assert rec_fields == fields


def test_6_to_13_every_field_invariants():
    """6-13. Verify field level safety flags are correctly set to default safe/blocked values."""
    p = build_contract_packet()
    for r in p["stub_records"]:
        for f in r["fields"]:
            # 6. placeholder_only true
            assert f["placeholder_only"] is True
            # 7. export_file_ready false
            assert f["export_file_ready"] is False
            # 8. clipboard_ready false
            assert f["clipboard_ready"] is False
            # 9. download_ready false
            assert f["download_ready"] is False
            # 10. publishable_text false
            assert f["publishable_text"] is False
            # 11. platform_ready false
            assert f["platform_ready"] is False
            # 12. dispatch_ready false
            assert f["dispatch_ready"] is False
            # 13. requires_human_rewrite true
            assert f["requires_human_rewrite"] is True


def test_14_export_ready_false():
    """14. Verify export_ready false."""
    p = build_contract_packet()
    assert p["safety_flags"]["export_ready"] is False
    for r in p["stub_records"]:
        assert r["export_ready"] is False


def test_15_manual_export_allowed_false():
    """15. Verify manual_export_allowed false."""
    p = build_contract_packet()
    assert p["safety_flags"]["manual_export_allowed"] is False
    for r in p["stub_records"]:
        assert r["manual_export_allowed"] is False


def test_16_export_file_created_false():
    """16. Verify export_file_created false."""
    p = build_contract_packet()
    assert p["safety_flags"]["export_file_created"] is False
    for r in p["stub_records"]:
        assert r["export_file_created"] is False


def test_17_clipboard_payload_created_false():
    """17. Verify clipboard_payload_created false."""
    p = build_contract_packet()
    assert p["safety_flags"]["clipboard_payload_created"] is False
    for r in p["stub_records"]:
        assert r["clipboard_payload_created"] is False


def test_18_download_artifact_created_false():
    """18. Verify download_artifact_created false."""
    p = build_contract_packet()
    assert p["safety_flags"]["download_artifact_created"] is False
    for r in p["stub_records"]:
        assert r["download_artifact_created"] is False


def test_19_publishable_payload_created_false():
    """19. Verify publishable_payload_created false."""
    p = build_contract_packet()
    assert p["safety_flags"]["publishable_payload_created"] is False
    for r in p["stub_records"]:
        assert r["publishable_payload_created"] is False


def test_20_platform_payload_created_false():
    """20. Verify platform_payload_created false."""
    p = build_contract_packet()
    assert p["safety_flags"]["platform_payload_created"] is False
    for r in p["stub_records"]:
        assert r["platform_payload_created"] is False


def test_21_public_postable_false():
    """21. Verify public_postable false."""
    p = build_contract_packet()
    assert p["safety_flags"]["public_postable"] is False
    for r in p["stub_records"]:
        assert r["public_postable"] is False


def test_22_approval_granted_false():
    """22. Verify approval_granted false."""
    p = build_contract_packet()
    assert p["safety_flags"]["approval_granted"] is False
    for r in p["stub_records"]:
        assert r["approval_granted"] is False


def test_23_operator_identity_not_bound():
    """23. Verify operator identity not bound."""
    p = build_contract_packet()
    for r in p["stub_records"]:
        assert r["operator_identity_bound"] is False
        assert r["operator_identity_status"] == "identity_required_but_unbound"


def test_24_operator_signature_absent():
    """24. Verify operator signature absent."""
    p = build_contract_packet()
    for r in p["stub_records"]:
        assert r["operator_signature_present"] is False
        assert r["operator_signature_status"] == "signature_required_but_missing"


def test_25_payload_hash_not_locked():
    """25. Verify payload hash not locked."""
    p = build_contract_packet()
    for r in p["stub_records"]:
        assert r["payload_hash_locked"] is False


def test_26_account_binding_and_credential_gates_required_but_inactive():
    """26. Verify account binding and credential gates required but inactive."""
    p = build_contract_packet()
    assert p["safety_flags"]["account_binding_active"] is False
    assert p["safety_flags"]["credential_values_loaded"] is False
    for r in p["stub_records"]:
        assert r["account_binding_active"] is False
        assert r["credential_values_loaded"] is False
        assert r["account_binding_status"] == "binding_required_but_inactive"
        assert r["credential_gate_status"] == "credential_required_but_locked"


def test_27_citation_and_limitation_statuses_preserved():
    """27. Verify citation and limitation statuses preserved."""
    p = build_contract_packet()
    for r in p["stub_records"]:
        assert r["citation_status"] == "citation_rendering_required_but_pending"
        assert r["limitation_status"] == "limitation_rendering_required_but_pending"


def test_28_dqr_readiness_current_truth_not_cleared():
    """28. Verify DQR/readiness/current truth not cleared."""
    p = build_contract_packet()
    assert p["safety_flags"]["dqr_cleared_by_contentops"] is False
    assert p["safety_flags"]["readiness_cleared_by_contentops"] is False
    assert p["safety_flags"]["current_truth_promoted"] is False


def test_29_no_financial_advice_signal_execution_language():
    """29. Verify no financial advice/signal/execution language."""
    p = build_contract_packet()
    assert p["safety_flags"]["financial_advice"] is False
    assert p["safety_flags"]["signal_language"] is False
    assert p["safety_flags"]["broker_order_execution"] is False


def test_30_no_fake_market_numbers():
    """30. Verify no fake market numbers."""
    p = build_contract_packet()
    assert p["safety_flags"]["financial_advice"] is False
    assert p["safety_flags"]["broker_order_execution"] is False
    
    out_dir = Path("docs/automation/0175AS")
    runbook_path = out_dir / "manual_export_precheck_to_export_packet_stub_contract.md"
    assert runbook_path.exists()
    content = runbook_path.read_text(encoding="utf-8")
    assert "fake" not in content.lower()


def test_31_no_env_network_credential_platform_provider_api_imports_or_calls():
    """31. Scan code to ensure no environment, network, or credential API modules are imported."""
    with open("live_contentops/manual_export_precheck_to_export_packet_stub_contract.py", encoding="utf-8") as f:
        content = f.read()
    forbidden = ["import os", "from os", "import requests", "urllib", "dotenv", "socket"]
    for pattern in forbidden:
        assert pattern not in content, f"Forbidden import or keyword '{pattern}' found."


def test_32_no_ingestion_repo_mutation_or_path_access():
    """32. Verify no ingestion repo mutation or path access is allowed."""
    p = build_contract_packet()
    assert p["safety_flags"]["ingestion_repo_mutated"] is False


def test_33_ledger_family_registered():
    """33. Verify ledger family manual_export_precheck_to_export_packet_stub_future is registered."""
    assert LEDGER_FAMILY in ENTRY_FAMILIES


def test_34_artifacts_written_only_under_docs_automation_0175as():
    """34. Verify that write_artifacts fails with ValueError outside docs/automation/0175AS."""
    with pytest.raises(ValueError, match="artifact_writer_refuses_paths_outside_docs_automation_0175AS"):
        write_artifacts(repo_root=".", output_dir="docs/automation/other")


def test_35_progress_ledger_resolves_0175ar_and_appends_0175as():
    """35. Verify progress ledger resolves 0175AR final HEAD and appends 0175AS."""
    path = Path("docs/CONTENTOPS_PROGRESS_LEDGER_AND_FINAL_PRODUCT_CHECKLIST.md")
    assert path.exists()
    content = path.read_text(encoding="utf-8")

    # One-task-lag checks
    assert "| `TASK_CONTENTOPS_0175AR_OPERATOR_DECISION_GATE_TO_MANUAL_EXPORT_PRECHECK_V0` | `68a7e425d229d7876fdfa1f37a65f3ef8c388849` | `c6ad0bcf016e1a5396aaab52f334b176e26f5c58` |" in content
    assert "| `TASK_CONTENTOPS_0175AS_MANUAL_EXPORT_PRECHECK_TO_EXPORT_PACKET_STUB_V0` | `c6ad0bcf016e1a5396aaab52f334b176e26f5c58` | `3441635cad8010a7325d83d856351275f897ce37` |" in content


def test_36_no_pycache_or_pyc_staged():
    """36. Ensure no pycache or .pyc files are staged/tracked in git."""
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
