"""Unit tests for Lane C draft-review-to-approval-packet-gate contract (0175AL)."""
from __future__ import annotations

import json
from pathlib import Path
import pytest

from live_contentops.lane_c_draft_review_to_approval_packet_gate_contract import (
    build_contract_packet,
    map_draft_to_approval_stub,
    TASK_LABEL,
    MATRIX_VERSION,
    SOURCE_BASELINE_COMMIT,
    write_artifacts,
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


def test_2_consumes_0175ak_draft_review_only_packet_data():
    """2. Verify that the contract successfully consumes and registers the 7 drafts and 1 rejected from 0175AK."""
    p = build_contract_packet()
    stubs = p["approval_stubs"]
    # 7 drafts + 1 rejected precedent = 8 stubs total
    assert len(stubs) == 8

    candidate_ids = {s["source_candidate_id"] for s in stubs}
    expected_ids = {
        "candidate_shape_valid_but_not_authorized",
        "candidate_missing_lineage_manifest",
        "candidate_stale_or_missing_freshness",
        "candidate_degraded_proxy_label_required",
        "candidate_missing_operator_approval",
        "candidate_local_fixture_only",
        "candidate_quarantined_review_only",
        "candidate_forbidden_public_ready_claim",
    }
    assert candidate_ids == expected_ids


def test_3_only_review_only_non_public_draft_packets_enter_gate():
    """3. Verify only review-only non-public draft packets enter the gate."""
    # Test valid draft mapping
    valid_draft = {
        "source_candidate_id": "test_valid",
        "draft_packet_id": "draft_packet_test_valid",
        "source_brief_id": "brief_packet_test_valid",
        "review_only": True,
        "public_postable": False,
        "dispatch_ready": False,
        "platform_payload_created": False,
        "human_review_required": True,
        "draft_status": "review_only",
        "blocked_reasons": [],
        "missing_proofs": [],
    }
    stub = map_draft_to_approval_stub(valid_draft)
    assert stub.gate_status == "gate_packet_created_pending_operator_review"

    # Test public postable True (should be rejected/blocked)
    invalid_draft_1 = dict(valid_draft, public_postable=True)
    stub_1 = map_draft_to_approval_stub(invalid_draft_1)
    assert stub_1.gate_status == "rejected_if_public_postable_or_dispatch_ready_requested"
    assert stub_1.approval_status == "rejected"

    # Test dispatch ready True
    invalid_draft_2 = dict(valid_draft, dispatch_ready=True)
    stub_2 = map_draft_to_approval_stub(invalid_draft_2)
    assert stub_2.gate_status == "rejected_if_public_postable_or_dispatch_ready_requested"
    assert stub_2.approval_status == "rejected"

    # Test review only False
    invalid_draft_3 = dict(valid_draft, review_only=False)
    stub_3 = map_draft_to_approval_stub(invalid_draft_3)
    assert stub_3.gate_status == "rejected_if_public_postable_or_dispatch_ready_requested"
    assert stub_3.approval_status == "rejected"


def test_4_blocked_rejected_draft_stubs_remain_blocked():
    """4. Verify blocked/rejected draft stubs remain blocked/rejected."""
    p = build_contract_packet()
    stubs = {s["source_candidate_id"]: s for s in p["approval_stubs"]}

    # Precedent rejected
    rejected = stubs["candidate_forbidden_public_ready_claim"]
    assert rejected["gate_status"] == "blocked_rejected_source_candidate"
    assert rejected["approval_status"] == "rejected"

    # Blocked drafts (missing lineage, stale freshness)
    missing_lineage = stubs["candidate_missing_lineage_manifest"]
    assert missing_lineage["gate_status"] == "blocked_unresolved_limitations"
    assert missing_lineage["approval_status"] == "blocked"

    stale_freshness = stubs["candidate_stale_or_missing_freshness"]
    assert stale_freshness["gate_status"] == "blocked_unresolved_limitations"
    assert stale_freshness["approval_status"] == "blocked"


def test_5_all_approval_stubs_public_postable_false():
    """5. All approval stubs public_postable must be false."""
    p = build_contract_packet()
    for s in p["approval_stubs"]:
        assert s["public_postable"] is False


def test_6_all_approval_stubs_dispatch_ready_false():
    """6. All approval stubs dispatch_ready must be false."""
    p = build_contract_packet()
    for s in p["approval_stubs"]:
        assert s["dispatch_ready"] is False


def test_7_platform_payload_allowed_false():
    """7. All approval stubs platform_payload_allowed must be false."""
    p = build_contract_packet()
    for s in p["approval_stubs"]:
        assert s["platform_payload_allowed"] is False


def test_8_platform_payload_created_false():
    """8. All approval stubs platform_payload_created must be false."""
    p = build_contract_packet()
    for s in p["approval_stubs"]:
        assert s["platform_payload_created"] is False


def test_9_approval_status_is_never_approved_for_publication():
    """9. Verify approval status is never approved_for_publication."""
    p = build_contract_packet()
    for s in p["approval_stubs"]:
        assert s["approval_status"] != "approved_for_publication"


def test_10_operator_placeholders_are_symbolic_only():
    """10. Verify operator placeholders are symbolic/empty only."""
    p = build_contract_packet()
    for s in p["approval_stubs"]:
        ops = s["operator_placeholders"]
        assert ops["operator_id_placeholder"] == "operator_id_placeholder"
        assert ops["operator_review_timestamp_placeholder"] == "operator_review_timestamp_placeholder"
        assert ops["manual_approval_note_placeholder"] == "manual_approval_note_placeholder"
        assert ops["evidence_packet_ref_placeholder"] == "evidence_packet_ref_placeholder"


def test_11_dqr_readiness_current_truth_not_cleared():
    """11. Verify DQR, readiness, and current truth are not cleared."""
    p = build_contract_packet()
    safety = p["safety_flags"]
    assert safety["dqr_cleared_by_contentops"] is False
    assert safety["readiness_cleared_by_contentops"] is False
    assert safety["current_truth_promoted"] is False


def test_12_citations_limitations_missing_proofs_preserved():
    """12. Verify citations, limitations, and missing proofs are preserved."""
    p = build_contract_packet()
    stubs = {s["source_candidate_id"]: s for s in p["approval_stubs"]}

    # All stubs must have limitation_block_status and citation_requirement_status, missing proofs
    for s in p["approval_stubs"]:
        assert s["limitation_block_status"] == "active_limitations_present"
        assert s["citation_requirement_status"] == "unverified"
        assert "operator_signature_check" in s["missing_proofs"]


def test_13_no_financial_advice_signal_execution_language():
    """13. Verify no financial advice, signal language, or broker order execution flags are set."""
    p = build_contract_packet()
    safety = p["safety_flags"]
    assert safety["financial_advice"] is False
    assert safety["signal_language"] is False
    assert safety["broker_order_execution"] is False
    assert safety["raw_vendor_redistribution"] is False


def test_14_no_env_network_credential_platform_provider_api_imports_or_calls():
    """14. Scan code to ensure no environment, network, or credential API modules are imported."""
    with open("live_contentops/lane_c_draft_review_to_approval_packet_gate_contract.py", encoding="utf-8") as f:
        content = f.read()
    forbidden = ["import os", "from os", "import requests", "urllib", "dotenv", "socket"]
    for pattern in forbidden:
        assert pattern not in content, f"Forbidden import or keyword '{pattern}' found."


def test_15_no_ingestion_repo_mutation_or_path_access():
    """15. Verify no ingestion repo mutation or path access is allowed."""
    p = build_contract_packet()
    safety = p["safety_flags"]
    assert safety["ingestion_repo_mutated"] is False


def test_16_ledger_family_registered():
    """16. Verify ledger family is registered."""
    assert "lane_c_draft_review_to_approval_packet_gate_future" in ENTRY_FAMILIES


def test_17_artifacts_written_only_under_docs_automation_0175al():
    """17. Verify that write_artifacts fails with ValueError outside docs/automation/0175AL."""
    with pytest.raises(ValueError, match="artifact_writer_refuses_paths_outside_docs_automation_0175AL"):
        write_artifacts(repo_root=".", output_dir="docs/automation/other")


def test_18_progress_ledger_repaired_for_0175ak():
    """18. Verify progress ledger is repaired for 0175AK."""
    path = Path("docs/CONTENTOPS_PROGRESS_LEDGER_AND_FINAL_PRODUCT_CHECKLIST.md")
    assert path.exists()
    content = path.read_text(encoding="utf-8")
    # Verify final HEAD is replaced with actual commit SHA, not pending_commit
    assert "| `TASK_CONTENTOPS_0175AK_LANE_C_EDITORIAL_BRIEF_TO_DRAFT_REVIEW_ONLY_PACKET_V0` | `ea5084684c04915c2261c5cd9e03a51fb2f276f1` | `6ba3bac45f676de8d340b4d3e7383283c5102068` |" in content


def test_19_progress_ledger_updated_with_0175al():
    """19. Verify progress ledger is updated with 0175AL row and next recommended task."""
    path = Path("docs/CONTENTOPS_PROGRESS_LEDGER_AND_FINAL_PRODUCT_CHECKLIST.md")
    assert path.exists()
    content = path.read_text(encoding="utf-8")
    assert "TASK_CONTENTOPS_0175AL" in content
    assert "TASK_CONTENTOPS_0175AM_LANE_C_APPROVAL_PACKET_TO_PLATFORM_PREVIEW_PRECHECK_V0" in content
