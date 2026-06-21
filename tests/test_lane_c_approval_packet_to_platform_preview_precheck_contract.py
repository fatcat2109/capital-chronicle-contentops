"""Unit tests for Lane C approval-packet-to-platform-preview-precheck contract (0175AM)."""
from __future__ import annotations

import json
from pathlib import Path
import pytest

from live_contentops.lane_c_approval_packet_to_platform_preview_precheck_contract import (
    build_contract_packet,
    evaluate_precheck_status,
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


def test_2_consumes_0175al_approval_gate_packet_data():
    """2. Verify that the contract successfully consumes approval gate packet data."""
    p = build_contract_packet()
    records = p["precheck_records"]
    stubs = p["payload_stubs"]
    # 8 approval stubs * 10 platform targets = 80 records and 80 stubs
    assert len(records) == 80
    assert len(stubs) == 80


def test_3_all_supported_platform_targets_exist():
    """3. Verify all supported platform targets exist."""
    p = build_contract_packet()
    targets = p["targets"]
    assert len(targets) == 10
    target_ids = {t["target_id"] for t in targets}
    expected_ids = {
        "x", "telegram_channel_destination", "telegram_remote_operator",
        "substack", "linkedin", "threads", "instagram",
        "facebook_page", "tiktok", "youtube"
    }
    assert target_ids == expected_ids


def test_4_only_non_public_approval_gate_stubs_enter_precheck():
    """4. Verify only non-public approval gate stubs enter precheck."""
    valid_stub = {
        "public_postable": False,
        "dispatch_ready": False,
        "platform_payload_allowed": False,
        "platform_payload_created": False,
        "approval_status": "pending_operator_review",
        "operator_approval_required": True,
        "gate_status": "gate_packet_created_pending_operator_review"
    }
    status = evaluate_precheck_status(valid_stub, "substack")
    assert status == "precheck_created_blocked_for_operator_review"

    # Test invalid options
    assert evaluate_precheck_status(dict(valid_stub, public_postable=True), "substack") == "rejected_if_payload_or_dispatch_requested"
    assert evaluate_precheck_status(dict(valid_stub, dispatch_ready=True), "substack") == "rejected_if_payload_or_dispatch_requested"
    assert evaluate_precheck_status(dict(valid_stub, platform_payload_allowed=True), "substack") == "rejected_if_payload_or_dispatch_requested"
    assert evaluate_precheck_status(dict(valid_stub, platform_payload_created=True), "substack") == "rejected_if_payload_or_dispatch_requested"
    assert evaluate_precheck_status(dict(valid_stub, approval_status="approved_for_publication"), "substack") == "rejected_if_payload_or_dispatch_requested"
    assert evaluate_precheck_status(dict(valid_stub, operator_approval_required=False), "substack") == "rejected_if_payload_or_dispatch_requested"


def test_5_to_9_precheck_outputs_and_dry_flags():
    """5-9. Verify precheck outputs do not create or dispatch real payloads."""
    p = build_contract_packet()
    for rec in p["precheck_records"]:
        assert rec["payload_created"] is False
        assert rec["publishable_payload_created"] is False
        assert rec["dispatch_ready"] is False
        assert rec["scheduler_enabled"] is False
        assert rec["platform_api_called"] is False

    for stub in p["payload_stubs"]:
        assert stub["payload_created"] is False
        assert stub["publishable_payload_created"] is False
        assert stub["dispatch_ready"] is False


def test_10_to_13_gates_and_proofs():
    """10-13. Verify credential/account binding only required, operator review required, hash lock missing, DQR un-cleared."""
    p = build_contract_packet()
    safety = p["safety_flags"]

    assert safety["credential_values_loaded"] is False
    assert safety["dqr_cleared_by_contentops"] is False
    assert safety["readiness_cleared_by_contentops"] is False
    assert safety["current_truth_promoted"] is False

    for rec in p["precheck_records"]:
        assert rec["credential_gate_required"] is True
        assert rec["account_binding_required"] is True
        assert rec["operator_review_required"] is True
        assert rec["payload_hash_lock_required"] is True
        if rec["precheck_status"] == "blocked_missing_payload_hash_lock":
            assert "payload_hash_lock_proof" in rec["missing_proofs"]
        elif rec["precheck_status"] == "blocked_missing_account_binding":
            assert "account_binding_proof" in rec["missing_proofs"]
        elif rec["precheck_status"] == "blocked_missing_credential_gate":
            assert "credential_gate_proof" in rec["missing_proofs"]


def test_14_limitations_and_citations_preserved():
    """14. Verify citation requirements and limitations are preserved."""
    p = build_contract_packet()
    for rec in p["precheck_records"]:
        assert "active_limitations_present" in rec["preserved_limitations"]
        assert "unverified_citations" in rec["preserved_citation_requirements"]


def test_15_no_financial_advice_signal_execution_language():
    """15. Verify no financial advice, signal language, or broker order execution flags are set."""
    p = build_contract_packet()
    safety = p["safety_flags"]
    assert safety["financial_advice"] is False
    assert safety["signal_language"] is False
    assert safety["broker_order_execution"] is False
    assert safety["raw_vendor_redistribution"] is False


def test_16_no_env_network_credential_platform_provider_api_imports_or_calls():
    """16. Scan code to ensure no environment, network, or credential API modules are imported."""
    with open("live_contentops/lane_c_approval_packet_to_platform_preview_precheck_contract.py", encoding="utf-8") as f:
        content = f.read()
    forbidden = ["import os", "from os", "import requests", "urllib", "dotenv", "socket"]
    for pattern in forbidden:
        assert pattern not in content, f"Forbidden import or keyword '{pattern}' found."


def test_17_no_ingestion_repo_mutation_or_path_access():
    """17. Verify no ingestion repo mutation or path access is allowed."""
    p = build_contract_packet()
    safety = p["safety_flags"]
    assert safety["ingestion_repo_mutated"] is False


def test_18_ledger_family_registered():
    """18. Verify ledger family is registered."""
    assert LEDGER_FAMILY in ENTRY_FAMILIES


def test_19_artifacts_written_only_under_docs_automation_0175am():
    """19. Verify that write_artifacts fails with ValueError outside docs/automation/0175AM."""
    with pytest.raises(ValueError, match="artifact_writer_refuses_paths_outside_docs_automation_0175AM"):
        write_artifacts(repo_root=".", output_dir="docs/automation/other")


def test_20_progress_ledger_resolves_0175alr3_and_appends_0175am():
    """20. Verify progress ledger is updated with 0175ALR3 final HEAD and 0175AM row."""
    path = Path("docs/CONTENTOPS_PROGRESS_LEDGER_AND_FINAL_PRODUCT_CHECKLIST.md")
    assert path.exists()
    content = path.read_text(encoding="utf-8")

    # One-task-lag check
    assert "| `TASK_CONTENTOPS_0175ALR3_LEDGER_PROTOCOL_ONE_TASK_LAG_REPAIR_V0` | `78385a78f4cc7e910d6311e7401838c90ac38357` | `ba81ce1851c8365cbd00f332daba2e087ea309df` |" in content
    assert (
        "| `TASK_CONTENTOPS_0175AM_LANE_C_APPROVAL_PACKET_TO_PLATFORM_PREVIEW_PRECHECK_V0` | `ba81ce1851c8365cbd00f332daba2e087ea309df` | `RECORDED_IN_NEXT_TASK_READBACK` |" in content
        or "| `TASK_CONTENTOPS_0175AM_LANE_C_APPROVAL_PACKET_TO_PLATFORM_PREVIEW_PRECHECK_V0` | `ba81ce1851c8365cbd00f332daba2e087ea309df` | `4d10a497d0104f5d3acae54097708e9e8b97e5d7` |" in content
    )
