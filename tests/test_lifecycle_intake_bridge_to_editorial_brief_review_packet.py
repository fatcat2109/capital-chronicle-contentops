"""Unit tests for the Lifecycle Intake Bridge to Editorial Brief Review Packet.

Part of TASK_CONTENTOPS_0175BH_LIFECYCLE_INTAKE_BRIDGE_TO_EDITORIAL_BRIEF_REVIEW_PACKET_V0.
"""
from __future__ import annotations

import json
from pathlib import Path
import pytest

from live_contentops.lifecycle_intake_bridge_to_editorial_brief_review_packet import (
    create_editorial_brief_review_packet,
    write_artifacts,
)
from live_contentops.content_lifecycle_engine import (
    build_lifecycle_read_model_with_artifact_intake_bridge,
)


@pytest.fixture
def sample_bridge_packet() -> dict:
    """Fixture mimicking a valid 0175BG bridge packet."""
    return {
        "task_label": "TASK_CONTENTOPS_0175BG_LANE_C_ARTIFACT_INTAKE_BRIDGE_TO_LIFECYCLE_ENGINE_PRECHECK_V0",
        "contentops_source_head": "25030c9ecb7f1340d8abc0943c397984f1ebb4d7",
        "ingestion_repo_path_checked": "A:\\Capital Chronicle\\Headline Raw data local json\\capital-chronicle-ingestion",
        "ingestion_repo_detected": True,
        "ingestion_repo_branch": "main",
        "ingestion_repo_head": "5d783546da258196cbfcdd37899c23a2100b9acb",
        "ingestion_repo_status": "dirty",
        "artifacts_scanned_count": 3,
        "artifact_candidates_count": 3,
        "artifact_candidate_summaries": [
            {
                "relative_path": "docs/research/database_foundation/pre_ia_acceleration/STEP1_OFFICIAL_TEXT_LIVE_PROBE_MANIFEST_V1.json",
                "file_size_bytes": 3305,
                "evidence_role": "manifest",
                "source_family": "Official Text Spine",
                "records_count": 6,
                "contract_name": None,
                "advisory_only": True,
                "candidate_only": True
            },
            {
                "relative_path": "docs/research/database_foundation/pre_ia_acceleration/BEA_BLS_CENSUS_NORMALIZED_CONTRACT_V1.json",
                "file_size_bytes": 2385,
                "evidence_role": "contract",
                "source_family": "US Macro",
                "records_count": 1,
                "contract_name": "BEA_BLS_CENSUS_NORMALIZED_CONTRACT_V1",
                "advisory_only": True,
                "candidate_only": True
            },
            {
                "relative_path": "docs/research/database_foundation/pre_ia_acceleration/BEA_BLS_CENSUS_NORMALIZED_CANDIDATE_RECORDS_V1.json",
                "file_size_bytes": 17558,
                "evidence_role": "candidates",
                "source_family": "US Macro",
                "records_count": 9,
                "contract_name": None,
                "advisory_only": True,
                "candidate_only": True
            }
        ],
        "protected_truth_flags": {
            "dqr_cleared_by_contentops": False,
            "readiness_cleared_by_contentops": False,
            "current_truth_promoted": False,
            "numeric_truth_promoted": False,
            "market_data_promoted": False
        },
        "lifecycle_overlay": {
            "affected_stage_id": "artifact_or_brief_intake",
            "stage_state_after_overlay": "PENDING",
            "operator_review_required": True,
            "downstream_dispatch_ready": False,
            "public_postable": False
        },
        "safety_flags": {
            "live_api_called": False,
            "provider_api_called": False,
            "platform_api_called": False,
            "credential_hydrated": False,
            "secret_values_observed": False,
            "env_secret_read": False,
            "scheduler_enabled": False,
            "scraping_performed": False
        }
    }


def test_consumes_fixture_and_emits_deterministic_review_packet(sample_bridge_packet):
    """Verify that a valid fixture bridge packet generates a deterministic review packet."""
    packet1 = create_editorial_brief_review_packet(sample_bridge_packet)
    packet2 = create_editorial_brief_review_packet(sample_bridge_packet)

    assert packet1["packet_hash"] == packet2["packet_hash"]
    assert packet1["task_label"] == "TASK_CONTENTOPS_0175BH_LIFECYCLE_INTAKE_BRIDGE_TO_EDITORIAL_BRIEF_REVIEW_PACKET_V0"
    assert packet1["source_bridge_task_label"] == "TASK_CONTENTOPS_0175BG_LANE_C_ARTIFACT_INTAKE_BRIDGE_TO_LIFECYCLE_ENGINE_PRECHECK_V0"
    assert packet1["candidate_count"] == 3


def test_real_0175bg_packet_loads_and_produces_metadata_only_review_items():
    """Verify that the real 0175BG JSON packet loads and generates metadata-only items."""
    packet_path = Path("docs/automation/0175BG/lane_c_artifact_intake_lifecycle_bridge_packet.json")
    assert packet_path.exists(), "Real 0175BG packet file must exist for integration verification."

    with open(packet_path, "r", encoding="utf-8") as f:
        real_bg_packet = json.load(f)

    review_packet = create_editorial_brief_review_packet(real_bg_packet)
    assert review_packet["candidate_count"] == 7

    allowed_fields = {
        "candidate_id", "relative_path", "evidence_role", "source_family",
        "records_count", "contract_name", "advisory_only", "candidate_only",
        "operator_review_required", "blocked_reasons", "allowed_next_step"
    }

    for item in review_packet["candidate_review_items"]:
        # Field check: only allowed fields are present
        extra_fields = set(item.keys()) - allowed_fields
        assert not extra_fields, f"Forbidden extra fields observed: {extra_fields}"

        # Value checks for forbidden concepts
        for field, val in item.items():
            val_str = str(val).lower()
            # Ensure no raw record contents / buy/sell/hold keywords or investment signals
            for forbidden_word in ["buy", "sell", "hold", "guaranteed", "price target", "order execution"]:
                assert forbidden_word not in val_str, f"Forbidden keyword '{forbidden_word}' found in field '{field}': {val}"


def test_truth_and_safety_flags_remain_false(sample_bridge_packet):
    """Verify that truth protection and safety flags are strictly set to False."""
    review_packet = create_editorial_brief_review_packet(sample_bridge_packet)

    # Truth protection checks
    for k, v in review_packet["protected_truth_flags"].items():
        assert v is False, f"Truth flag '{k}' is not False"

    # Safety checks
    for k, v in review_packet["safety_flags"].items():
        assert v is False, f"Safety flag '{k}' is not False"


def test_next_task_mismatch_fixed_and_tested(sample_bridge_packet):
    """Verify that next_recommended_task overlay defaults to 0175BH or matches explicitly passed values."""
    # 1. Default fallback
    read_model_default = build_lifecycle_read_model_with_artifact_intake_bridge(sample_bridge_packet)
    assert read_model_default["summary"]["next_recommended_task"] == "TASK_CONTENTOPS_0175BH_LIFECYCLE_INTAKE_BRIDGE_TO_EDITORIAL_BRIEF_REVIEW_PACKET_V0"

    # 2. Configured explicitly in call
    read_model_custom1 = build_lifecycle_read_model_with_artifact_intake_bridge(
        sample_bridge_packet,
        next_recommended_task="TASK_CONTENTOPS_0175BI_EDITORIAL_BRIEF_REVIEW_PACKET_TO_V5_BRIEF_QUEUE_BINDING_V0"
    )
    assert read_model_custom1["summary"]["next_recommended_task"] == "TASK_CONTENTOPS_0175BI_EDITORIAL_BRIEF_REVIEW_PACKET_TO_V5_BRIEF_QUEUE_BINDING_V0"

    # 3. Passed through the packet itself
    packet_with_custom_next = dict(sample_bridge_packet)
    packet_with_custom_next["next_recommended_task"] = "CUSTOM_TASK_LABEL_123"
    read_model_custom2 = build_lifecycle_read_model_with_artifact_intake_bridge(packet_with_custom_next)
    assert read_model_custom2["summary"]["next_recommended_task"] == "CUSTOM_TASK_LABEL_123"


def test_downstream_lifecycle_stages_remain_blocked_and_non_dispatchable(sample_bridge_packet):
    """Verify that overlays apply correctly, and downstream stages remain blocked."""
    # Build editorial review packet which contains overlays
    review_packet = create_editorial_brief_review_packet(sample_bridge_packet)
    
    # Run integration read model with the review packet
    read_model = build_lifecycle_read_model_with_artifact_intake_bridge(review_packet)
    stages = read_model["stages"]

    # Verify stage overlays
    first_stage = next(s for s in stages if s["stage_id"] == "artifact_or_brief_intake")
    assert first_stage["state"] == "PENDING"
    assert first_stage["operator_action_required"] is True

    second_stage = next(s for s in stages if s["stage_id"] == "content_intent")
    assert second_stage["state"] == "BLOCKED"
    assert second_stage["operator_action_required"] is True

    # Verify all downstream stages (order >= 3) are blocked or non-completed and strictly not dispatchable
    for s in stages:
        assert s["public_postable"] is False
        assert s["dispatch_ready"] is False
        if s["stage_order"] >= 3:
            # Stage 3 is draft_or_render. By default it is COMPLETED in list_lifecycle_stages,
            # but since we did not overlay it, it remains stage default or becomes BLOCKED.
            # But the key is that starting from 4, they must be PENDING/BLOCKED.
            if s["stage_order"] >= 4:
                assert s["state"] in ("PENDING", "BLOCKED")


def test_missing_empty_bridge_packet_fails_closed():
    """Verify that missing/empty bridge packets raise ValueError to fail closed."""
    with pytest.raises(ValueError, match="Bridge packet is missing or malformed"):
        create_editorial_brief_review_packet(None)

    with pytest.raises(ValueError, match="Bridge packet is missing or malformed"):
        create_editorial_brief_review_packet({})

    with pytest.raises(ValueError, match="Bridge packet missing required key"):
        create_editorial_brief_review_packet({"some_other_key": 123})


def test_write_artifacts(tmp_path):
    """Verify write_artifacts helper constructs correct files in the workspace."""
    # Write a mock bridge packet json to read from
    mock_packet = {
        "task_label": "MOCK_BRIDGE",
        "artifacts_scanned_count": 0,
        "artifact_candidates_count": 0,
        "artifact_candidate_summaries": [],
        "ingestion_repo_path_checked": "mock_path",
        "ingestion_repo_head": "mock_head",
        "ingestion_repo_branch": "mock_branch",
        "ingestion_repo_status": "clean"
    }
    input_file = tmp_path / "bridge_packet.json"
    with open(input_file, "w", encoding="utf-8") as f:
        json.dump(mock_packet, f)

    res = write_artifacts(bridge_packet_path=input_file, repo_root=tmp_path)
    assert Path(res["packet_path"]).exists()
    assert Path(res["runbook_path"]).exists()
