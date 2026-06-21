"""Unit tests for Lane C artifact ingestion foundation contract."""
from __future__ import annotations

import json
from pathlib import Path
import pytest

from live_contentops.lane_c_artifact_ingestion_foundation_contract import (
    build_contract_packet,
    TASK_LABEL,
    MATRIX_VERSION,
    SOURCE_BASELINE_COMMIT,
    write_artifacts,
)
from live_contentops.redacted_immutable_audit_ledger_v2_contract import ENTRY_FAMILIES


def test_ingestion_packet_builds_deterministically():
    """Verify that build_contract_packet creates deterministic hashes."""
    p1 = build_contract_packet()
    p2 = build_contract_packet()
    assert p1["packet_hash"] == p2["packet_hash"]
    assert p1["task_label"] == TASK_LABEL
    assert p1["matrix_version"] == MATRIX_VERSION
    assert p1["source_baseline_commit"] == SOURCE_BASELINE_COMMIT


def test_all_candidate_ids_present():
    """Ensure all 8 candidate registry entries are present."""
    p = build_contract_packet()
    candidates = p["candidates"]
    assert len(candidates) == 8

    expected_ids = {
        "candidate_shape_valid_but_not_authorized",
        "candidate_missing_lineage_manifest",
        "candidate_stale_or_missing_freshness",
        "candidate_degraded_proxy_label_required",
        "candidate_missing_operator_approval",
        "candidate_forbidden_public_ready_claim",
        "candidate_local_fixture_only",
        "candidate_quarantined_review_only",
    }
    cand_ids = {c["artifact_id"] for c in candidates}
    assert cand_ids == expected_ids


def test_candidates_are_local_fixture_or_blocked_quarantined():
    """Ensure all candidates have correct classifications."""
    p = build_contract_packet()
    candidates = p["candidates"]
    for c in candidates:
        assert c["classification"] in [
            "shape_valid_but_not_authorized",
            "blocked_missing_lineage",
            "blocked_proxy_or_degraded_label_required",
            "blocked_missing_operator_approval",
            "blocked_public_ready_claim",
            "local_fixture_only",
            "quarantined_review_only",
        ]


def test_public_postable_and_dispatch_ready_false_for_all():
    """Verify that no candidate can ever be promoted to postable or dispatch ready."""
    p = build_contract_packet()
    for c in p["candidates"]:
        assert c["public_postable"] is False
        assert c["dispatch_ready"] is False


def test_dqr_readiness_current_truth_never_cleared():
    """Verify that DQR, readiness, and current truth are never cleared."""
    p = build_contract_packet()
    safety = p["safety_flags"]
    assert safety["dqr_cleared_by_contentops"] is False
    assert safety["readiness_cleared_by_contentops"] is False
    assert safety["current_truth_promoted"] is False


def test_safety_flags_verification():
    """Verify other safety flag invariants."""
    p = build_contract_packet()
    safety = p["safety_flags"]
    assert safety["local_only"] is True
    assert safety["fixture_only"] is True
    assert safety["network_performed"] is False
    assert safety["env_read"] is False
    assert safety["credential_values_loaded"] is False
    assert safety["platform_api_called"] is False
    assert safety["provider_api_called"] is False
    assert safety["ingestion_repo_mutated"] is False
    assert safety["public_postable"] is False
    assert safety["dispatch_ready"] is False
    assert safety["financial_advice"] is False
    assert safety["signal_language"] is False
    assert safety["broker_order_execution"] is False
    assert safety["raw_vendor_redistribution"] is False
    assert safety["approved_internal_alpha_artifacts_available"] is False


def test_forbidden_public_ready_claim_is_rejected():
    """Verify that the negative fixture requesting public readiness is rejected/blocked."""
    p = build_contract_packet()
    candidates = p["candidates"]
    candidate = next(c for c in candidates if c["artifact_id"] == "candidate_forbidden_public_ready_claim")
    assert candidate["readiness_status"] == "ready_for_public_distribution"

    decisions = p["decisions"]
    decision = next(d for d in decisions if d["artifact_id"] == "candidate_forbidden_public_ready_claim")
    assert decision["verdict"] == "blocked"
    assert "forbidden_public_ready_claim" in decision["blocked_reasons"]


def test_blocker_manifests_are_preserved():
    """Verify the lineage, freshness, proxy, and operator approval blocker validations."""
    p = build_contract_packet()
    decisions = {d["artifact_id"]: d for d in p["decisions"]}

    # Lineage Check
    assert "missing_lineage_manifest" in decisions["candidate_missing_lineage_manifest"]["blocked_reasons"]
    # Freshness Check
    assert "stale_or_missing_freshness" in decisions["candidate_stale_or_missing_freshness"]["blocked_reasons"]
    # Proxy / Degraded check
    assert "degraded_proxy_label_required" in decisions["candidate_degraded_proxy_label_required"]["blocked_reasons"]
    # Operator Approval check
    assert "missing_operator_approval" in decisions["candidate_missing_operator_approval"]["blocked_reasons"]


def test_no_credential_network_or_env_imports():
    """Verify that no sensitive environment/network/credential modules are imported."""
    with open("live_contentops/lane_c_artifact_ingestion_foundation_contract.py", encoding="utf-8") as f:
        content = f.read()
    forbidden = ["import os", "from os", "import requests", "urllib", "dotenv", "socket"]
    for pattern in forbidden:
        assert pattern not in content, f"Forbidden import or keyword '{pattern}' found."


def test_write_artifacts_path_restrictions():
    """Verify that write_artifacts fails with ValueError outside docs/automation/0175AI."""
    with pytest.raises(ValueError, match="artifact_writer_refuses_paths_outside_docs_automation_0175AI"):
        write_artifacts(repo_root=".", output_dir="docs/automation/other")


def test_ledger_family_registered():
    """Verify ledger family is correctly registered in entry families."""
    assert "lane_c_artifact_ingestion_foundation_future" in ENTRY_FAMILIES


def test_progress_ledger_file_is_updated():
    """Verify that the progress ledger includes 0175AI and the next recommended task."""
    path = Path("docs/CONTENTOPS_PROGRESS_LEDGER_AND_FINAL_PRODUCT_CHECKLIST.md")
    assert path.exists()
    content = path.read_text(encoding="utf-8")
    assert "TASK_CONTENTOPS_0175AI" in content
    assert "TASK_CONTENTOPS_0175AJ_LANE_C_ARTIFACT_TO_EDITORIAL_BRIEF_REVIEW_PACKET_V0" in content
