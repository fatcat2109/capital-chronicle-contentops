"""Unit tests for the Lane C artifact intake to lifecycle bridge.

Part of TASK_CONTENTOPS_0175BG_LANE_C_ARTIFACT_INTAKE_BRIDGE_TO_LIFECYCLE_ENGINE_PRECHECK_V0.
"""
from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path
from typing import Any

from live_contentops.lane_c_artifact_to_lifecycle_bridge import (
    discover_artifacts,
    build_bridge_packet,
)
from live_contentops.content_lifecycle_engine import (
    build_lifecycle_read_model_with_artifact_intake_bridge,
)


def test_missing_ingestion_repo():
    """Verify bridge behavior when the ingestion repository path does not exist."""
    # Use a non-existent path
    fake_path = "/non_existent_directory_cc_12345"
    discovery = discover_artifacts(fake_path)
    assert discovery["ingestion_repo_detected"] is False
    assert discovery["artifacts_scanned_count"] == 0
    assert discovery["artifact_candidates_count"] == 0
    assert len(discovery["artifact_candidate_summaries"]) == 0
    
    packet = build_bridge_packet(fake_path)
    assert packet["ingestion_repo_detected"] is False
    assert packet["lifecycle_overlay"]["stage_state_after_overlay"] == "BLOCKED"
    assert packet["lifecycle_overlay"]["operator_review_required"] is True
    assert packet["lifecycle_overlay"]["downstream_dispatch_ready"] is False
    assert packet["lifecycle_overlay"]["public_postable"] is False


def test_temporary_fixture_ingestion_repo():
    """Verify bridge scans files correctly with a simulated ingestion repository directory."""
    temp_dir = tempfile.mkdtemp()
    try:
        temp_path = Path(temp_dir)
        
        # Mimic git repo
        (temp_path / ".git").mkdir()
        
        # Create research path
        pre_ia_dir = temp_path / "docs" / "research" / "database_foundation" / "pre_ia_acceleration"
        pre_ia_dir.mkdir(parents=True)
        
        # Create a mock manifest and mock contract
        manifest_content = [
            {
                "url": "https://www.example.gov/manifest",
                "status_code": 200,
                "text_sample_redacted_or_omitted": True
            }
        ]
        contract_content = {
            "advisory_only": True,
            "candidate_only": True,
            "contract_name": "STEP1_OFFICIAL_TEXT_SPINE_CONTRACT_V1",
            "invariants": {"canonical_apply_allowed": False}
        }
        
        with open(pre_ia_dir / "STEP1_OFFICIAL_TEXT_LIVE_PROBE_MANIFEST_V1.json", "w", encoding="utf-8") as f:
            json.dump(manifest_content, f)
            
        with open(pre_ia_dir / "STEP1_OFFICIAL_TEXT_SPINE_CONTRACT_V1.json", "w", encoding="utf-8") as f:
            json.dump(contract_content, f)
            
        discovery = discover_artifacts(temp_path)
        assert discovery["ingestion_repo_detected"] is True
        assert discovery["artifacts_scanned_count"] == 2
        assert discovery["artifact_candidates_count"] == 2
        
        summaries = discovery["artifact_candidate_summaries"]
        roles = {s["evidence_role"] for s in summaries}
        assert "manifest" in roles
        assert "contract" in roles
        
        packet = build_bridge_packet(temp_path)
        assert packet["ingestion_repo_detected"] is True
        assert packet["artifact_candidates_count"] == 2
        assert packet["lifecycle_overlay"]["stage_state_after_overlay"] == "PENDING"
        
        # Verify protected truth flags
        assert packet["protected_truth_flags"]["dqr_cleared_by_contentops"] is False
        assert packet["protected_truth_flags"]["readiness_cleared_by_contentops"] is False
        assert packet["protected_truth_flags"]["current_truth_promoted"] is False
        assert packet["protected_truth_flags"]["numeric_truth_promoted"] is False
        assert packet["protected_truth_flags"]["market_data_promoted"] is False
        
        # Run bridge overlay
        read_model = build_lifecycle_read_model_with_artifact_intake_bridge(packet)
        assert read_model["task_label"] == "TASK_CONTENTOPS_0175BG_LANE_C_ARTIFACT_INTAKE_BRIDGE_TO_LIFECYCLE_ENGINE_PRECHECK_V0"
        
        stages = read_model["stages"]
        assert len(stages) == 16
        
        # Affected stage check
        first_stage = next(s for s in stages if s["stage_id"] == "artifact_or_brief_intake")
        assert first_stage["state"] == "PENDING"
        assert first_stage["operator_action_required"] is True
        
        # Verify that safety locks are preserved (fail closed)
        for s in stages:
            assert s["public_postable"] is False
            assert s["dispatch_ready"] is False
            assert s["live_api_called"] is False
            assert s["provider_api_called"] is False
            assert s["env_read"] is False
            assert s["credential_hydrated"] is False
            assert s["scheduler_enabled"] is False
            assert s["scraping_performed"] is False
            assert s["autonomous_reply_or_dm_enabled"] is False
            assert s["dqr_cleared_by_contentops"] is False
            assert s["readiness_cleared_by_contentops"] is False
            assert s["current_truth_promoted"] is False
            
            # Ensure downstream stages are blocked or non-completed
            if s["stage_id"] != "artifact_or_brief_intake":
                # Original stages 2 and 3 were completed, but downstream stages starting from 4 must not be marked complete/dispatchable
                if s["stage_order"] >= 4:
                    assert s["state"] in ("PENDING", "BLOCKED")
                    
    finally:
        shutil.rmtree(temp_dir)
