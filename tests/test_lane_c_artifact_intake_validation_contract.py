"""Unit tests for Lane C artifact intake validation contract."""
from __future__ import annotations

import json
from pathlib import Path
import pytest

from live_contentops.lane_c_artifact_intake_validation_contract import (
    build_contract_packet,
    TASK_LABEL,
    MATRIX_VERSION,
    SOURCE_BASELINE_COMMIT,
)
from live_contentops.redacted_immutable_audit_ledger_v2_contract import ENTRY_FAMILIES


def test_intake_packet_builds_deterministically():
    """Verify that build_contract_packet creates deterministic hashes."""
    p1 = build_contract_packet()
    p2 = build_contract_packet()
    assert p1["packet_hash"] == p2["packet_hash"]
    assert p1["task_label"] == TASK_LABEL
    assert p1["matrix_version"] == MATRIX_VERSION
    assert p1["source_baseline_commit"] == SOURCE_BASELINE_COMMIT


def test_three_candidates_modeled():
    """Ensure exactly 3 deterministic candidates are represented with correct IDs."""
    p = build_contract_packet()
    candidates = p["candidates"]
    assert len(candidates) == 3

    c_ids = [c["candidate_id"] for c in candidates]
    expected_ids = [
        "valid_shape_but_blocked_missing_manual_review",
        "stale_or_missing_freshness_metadata",
        "degraded_proxy_or_unverified_lineage",
    ]
    assert c_ids == expected_ids

    # Verify candidate fields
    for c in candidates:
        assert "candidate_id" in c
        assert "artifact_family" in c
        assert "local_artifact_ref" in c
        assert "source_system" in c
        assert c["source_system"] == "capital_chronicle_future_artifact"
        assert "lineage_ref" in c
        assert "freshness_status" in c
        assert "dqr_status" in c
        assert "readiness_status" in c
        assert "missing_or_degraded_labels" in c
        assert "citation_refs" in c
        assert "limitation_notes" in c
        assert c["public_postable"] is False
        assert c["dispatch_ready"] is False
        assert c["review_required"] is True
        assert "blocked_reasons" in c


def test_safety_flags():
    """Verify that safety flags strictly enforce local-only bounds."""
    p = build_contract_packet()
    safety = p["safety_flags"]

    assert safety["local_only"] is True
    assert safety["review_only"] is True
    assert safety["lane_c_enabled_for_review"] is True
    assert safety["live_ingestion_enabled"] is False
    assert safety["ingestion_repo_mutated"] is False
    assert safety["dqr_cleared"] is False
    assert safety["readiness_cleared"] is False
    assert safety["public_postable"] is False
    assert safety["dispatch_ready"] is False
    assert safety["platform_api_called"] is False
    assert safety["provider_api_called"] is False
    assert safety["credential_read"] is False
    assert safety["env_read"] is False
    assert safety["network_performed"] is False
    assert safety["secret_output"] is False
    assert safety["raw_response_logged"] is False
    assert safety["autonomous_posting"] is False


def test_validation_checks_present():
    """Verify that all required validation checks are modeled and passed."""
    p = build_contract_packet()
    checks = p["validation_checks"]
    assert len(checks) == 16

    check_ids = [ch["check_id"] for ch in checks]
    expected_ids = [
        "artifact_identity_present",
        "lineage_present",
        "freshness_present",
        "dqr_not_cleared_by_contentops",
        "readiness_not_cleared_by_contentops",
        "missing_degraded_proxy_labels_preserved",
        "citation_refs_present",
        "limitation_notes_present",
        "no_fake_market_numbers",
        "no_financial_advice",
        "no_signal_language",
        "public_postable_false",
        "dispatch_ready_false",
        "no_ingestion_mutation",
        "no_env_or_credential_read",
        "no_network_or_api_call",
    ]
    for expected in expected_ids:
        assert expected in check_ids

    for ch in checks:
        assert ch["passed"] is True


def test_no_credential_or_network_imports():
    """Verify that no sensitive environment/network/credential modules are imported."""
    with open("live_contentops/lane_c_artifact_intake_validation_contract.py", encoding="utf-8") as f:
        content = f.read()
    forbidden = ["import os", "from os", "import requests", "urllib", "dotenv", "socket"]
    for pattern in forbidden:
        assert pattern not in content, f"Forbidden import or keyword '{pattern}' found."


def test_path_restriction_on_write_artifacts():
    """Verify that write_artifacts refuses to write outside docs/automation/0175AF."""
    from live_contentops.lane_c_artifact_intake_validation_contract import write_artifacts
    with pytest.raises(ValueError, match="artifact_writer_refuses_paths_outside_docs_automation_0175AF"):
        write_artifacts(repo_root=".", output_dir="docs/automation/other")


def test_ledger_family_registration():
    """Verify that the ledger contract contains the lane_c_artifact_intake_validation_future family."""
    assert "lane_c_artifact_intake_validation_future" in ENTRY_FAMILIES
