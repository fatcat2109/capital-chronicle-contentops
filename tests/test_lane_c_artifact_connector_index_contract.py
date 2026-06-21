"""Unit tests for Lane C artifact connector index contract."""
from __future__ import annotations

import json
from pathlib import Path
import pytest

from live_contentops.lane_c_artifact_connector_index_contract import (
    build_contract_packet,
    TASK_LABEL,
    MATRIX_VERSION,
    SOURCE_BASELINE_COMMIT,
)
from live_contentops.redacted_immutable_audit_ledger_v2_contract import ENTRY_FAMILIES


def test_connector_index_packet_builds_deterministically():
    """Verify that build_contract_packet creates deterministic hashes."""
    p1 = build_contract_packet()
    p2 = build_contract_packet()
    assert p1["packet_hash"] == p2["packet_hash"]
    assert p1["task_label"] == TASK_LABEL
    assert p1["matrix_version"] == MATRIX_VERSION
    assert p1["source_baseline_commit"] == SOURCE_BASELINE_COMMIT


def test_required_connector_families_present():
    """Ensure all 6 future connector families are represented with correct IDs."""
    p = build_contract_packet()
    families = p["connector_families"]
    assert len(families) == 6

    f_ids = [f["connector_id"] for f in families]
    expected_ids = [
        "local_capital_chronicle_artifact_packet",
        "local_capital_chronicle_lineage_manifest",
        "local_capital_chronicle_dqr_snapshot",
        "local_capital_chronicle_source_health_snapshot",
        "local_capital_chronicle_forecast_readiness_snapshot",
        "local_manual_operator_evidence_packet",
    ]
    assert f_ids == expected_ids

    # Verify key family fields
    for f in families:
        assert "connector_id" in f
        assert "connector_family" in f
        assert f["current_status"] in ["blocked_review_only", "manual_only"]
        assert "allowed_path_pattern" in f
        assert "required_file_kinds" in f
        assert "required_identity_fields" in f
        assert "required_hash_fields" in f
        assert "required_lineage_fields" in f
        assert "freshness_requirement" in f
        assert "dqr_handling" in f
        assert "readiness_handling" in f
        assert "missing_degraded_proxy_label_handling" in f
        assert "allowed_consumer_surfaces" in f
        assert "prohibited_effects" in f
        assert "next_required_gate" in f


def test_safety_flags():
    """Verify that safety flags strictly enforce local-only bounds."""
    p = build_contract_packet()
    safety = p["safety_flags"]

    assert safety["no_live_connector_enabled"] is True
    assert safety["no_ingestion_repo_mutation"] is True
    assert safety["no_env_read"] is True
    assert safety["no_credential_read"] is True
    assert safety["no_network_call"] is True
    assert safety["no_provider_platform_api_call"] is True
    assert safety["no_current_state_mutation"] is True
    assert safety["no_dqr_clear"] is True
    assert safety["no_readiness_clear"] is True
    assert safety["no_public_postable_promotion"] is True
    assert safety["no_dispatch_ready_promotion"] is True
    assert safety["no_fake_market_numbers"] is True
    assert safety["no_raw_vendor_redistribution"] is True
    assert safety["no_autonomous_posting"] is True
    assert safety["no_scheduler"] is True
    assert safety["no_scraping"] is True


def test_no_credential_or_network_imports():
    """Verify that no sensitive environment/network/credential modules are imported."""
    with open("live_contentops/lane_c_artifact_connector_index_contract.py", encoding="utf-8") as f:
        content = f.read()
    forbidden = ["import os", "from os", "import requests", "urllib", "dotenv", "socket"]
    for pattern in forbidden:
        assert pattern not in content, f"Forbidden import or keyword '{pattern}' found."


def test_path_restriction_on_write_artifacts():
    """Verify that write_artifacts refuses to write outside docs/automation/0175AG."""
    from live_contentops.lane_c_artifact_connector_index_contract import write_artifacts
    with pytest.raises(ValueError, match="artifact_writer_refuses_paths_outside_docs_automation_0175AG"):
        write_artifacts(repo_root=".", output_dir="docs/automation/other")


def test_ledger_family_registration():
    """Verify that the ledger contract contains the lane_c_artifact_connector_index_future family."""
    assert "lane_c_artifact_connector_index_future" in ENTRY_FAMILIES
