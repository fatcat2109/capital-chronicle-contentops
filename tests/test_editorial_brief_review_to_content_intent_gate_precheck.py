"""Unit tests for the Editorial Brief Review to Content Intent Gate Precheck.

Part of TASK_CONTENTOPS_0175BJ_EDITORIAL_BRIEF_REVIEW_TO_CONTENT_INTENT_GATE_PRECHECK_V0.
"""
from __future__ import annotations

import json
from pathlib import Path
import pytest

from live_contentops.editorial_brief_review_to_content_intent_gate_precheck import (
    create_content_intent_gate_precheck,
    write_artifacts,
)


@pytest.fixture
def sample_brief_packet() -> dict:
    """Fixture mimicking a valid 0175BH editorial brief review packet."""
    return {
        "task_label": "TASK_CONTENTOPS_0175BH_LIFECYCLE_INTAKE_BRIDGE_TO_EDITORIAL_BRIEF_REVIEW_PACKET_V0",
        "source_bridge_task_label": "TASK_CONTENTOPS_0175BG_LANE_C_ARTIFACT_INTAKE_BRIDGE_TO_LIFECYCLE_ENGINE_PRECHECK_V0",
        "source_bridge_packet_hash": "17dd4652f4ec4e3e20ade749c68fdad0bf3a854d2a388bff1c25a6cf9842da2a",
        "contentops_source_head": "23e0573c062b63c939040143cfe66830bbfa9c2a",
        "packet_hash": "1a8cf4c01bfbf86fe2928ebb604feae8c59d84f95806709ea44245af89027a5b",
        "ingestion_repo_path_checked": "A:\\Capital Chronicle\\Headline Raw data local json\\capital-chronicle-ingestion",
        "ingestion_repo_branch": "main",
        "ingestion_repo_head": "5d783546da258196cbfcdd37899c23a2100b9acb",
        "ingestion_repo_status": "dirty",
        "candidate_count": 2,
        "candidate_review_items": [
            {
                "candidate_id": "STEP1_OFFICIAL_TEXT_LIVE_PROBE_MANIFEST_V1",
                "relative_path": "docs/research/database_foundation/pre_ia_acceleration/STEP1_OFFICIAL_TEXT_LIVE_PROBE_MANIFEST_V1.json",
                "evidence_role": "manifest",
                "source_family": "Official Text Spine",
                "records_count": 6,
                "contract_name": None,
                "advisory_only": True,
                "candidate_only": True,
                "operator_review_required": True,
                "blocked_reasons": ["waiting_for_operator_brief_review"],
                "allowed_next_step": "operator_must_inspect_source_artifact_before_brief_generation",
            },
            {
                "candidate_id": "BEA_BLS_CENSUS_NORMALIZED_CONTRACT_V1",
                "relative_path": "docs/research/database_foundation/pre_ia_acceleration/BEA_BLS_CENSUS_NORMALIZED_CONTRACT_V1.json",
                "evidence_role": "contract",
                "source_family": "US Macro",
                "records_count": 1,
                "contract_name": "BEA_BLS_CENSUS_NORMALIZED_CONTRACT_V1",
                "advisory_only": True,
                "candidate_only": True,
                "operator_review_required": True,
                "blocked_reasons": ["waiting_for_operator_brief_review"],
                "allowed_next_step": "operator_must_inspect_source_artifact_before_brief_generation",
            }
        ],
        "topic_families": ["Official Text Spine", "US Macro"],
        "evidence_roles": ["contract", "manifest"],
        "required_operator_review_checklist": [
            "Confirm ingestion repository path matches local system",
            "Verify candidates scanned count matches expected count",
        ],
        "blocked_reasons": ["operator_brief_review_pending", "content_intent_gate_locked_until_operator_review"],
        "protected_truth_flags": {
            "dqr_cleared_by_contentops": False,
            "readiness_cleared_by_contentops": False,
            "current_truth_promoted": False,
            "numeric_truth_promoted": False,
            "market_data_promoted": False
        },
        "safety_flags": {
            "live_api_called": False,
            "provider_api_called": False,
            "platform_api_called": False,
            "credential_hydrated": False,
            "secret_values_observed": False,
            "env_secret_read": False,
            "scheduler_enabled": False,
            "scraping_performed": False,
            "dispatch_ready": False,
            "public_postable": False
        },
        "next_recommended_task": "TASK_CONTENTOPS_0175BI_EDITORIAL_BRIEF_REVIEW_PACKET_TO_V5_BRIEF_QUEUE_BINDING_V0",
        "ledger_family": "lifecycle_intake_bridge_to_editorial_brief_review_packet_future",
        "hash_algorithm": "sha256"
    }


def test_produces_deterministic_precheck_packet(sample_brief_packet):
    """Verify that a valid brief review packet produces a deterministic precheck packet."""
    precheck1 = create_content_intent_gate_precheck(sample_brief_packet)
    precheck2 = create_content_intent_gate_precheck(sample_brief_packet)

    assert precheck1["packet_hash"] == precheck2["packet_hash"]
    assert precheck1["task_label"] == "TASK_CONTENTOPS_0175BJ_EDITORIAL_BRIEF_REVIEW_TO_CONTENT_INTENT_GATE_PRECHECK_V0"
    assert precheck1["source_packet_task_label"] == "TASK_CONTENTOPS_0175BH_LIFECYCLE_INTAKE_BRIDGE_TO_EDITORIAL_BRIEF_REVIEW_PACKET_V0"
    assert precheck1["source_candidate_count"] == 2
    assert len(precheck1["candidate_gate_items"]) == 2


def test_missing_metadata_fails_closed(sample_brief_packet):
    """Verify that missing metadata fields cause the item and global status to be blocked."""
    # Modify the second candidate item to miss the source family
    sample_brief_packet["candidate_review_items"][1]["source_family"] = ""

    precheck = create_content_intent_gate_precheck(sample_brief_packet)
    assert precheck["content_intent_gate_status"] == "BLOCKED_MISSING_METADATA"
    assert "metadata_requirements_incomplete_across_candidates" in precheck["blocked_reasons"]

    # Verify candidate specific status
    second_item = precheck["candidate_gate_items"][1]
    assert second_item["content_intent_gate_status"] == "BLOCKED_MISSING_METADATA"
    assert "missing_source_family" in second_item["missing_requirements"]


def test_advisory_only_false_blocks(sample_brief_packet):
    """Verify that advisory_only=False blocks compliance validation."""
    sample_brief_packet["candidate_review_items"][0]["advisory_only"] = False

    precheck = create_content_intent_gate_precheck(sample_brief_packet)
    assert precheck["content_intent_gate_status"] == "BLOCKED_NOT_CANDIDATE_ONLY"
    assert "safety_invariants_violated_in_candidates" in precheck["blocked_reasons"]

    first_item = precheck["candidate_gate_items"][0]
    assert first_item["content_intent_gate_status"] == "BLOCKED_NOT_CANDIDATE_ONLY"
    assert "quarantine_candidate_and_inspect_compliance_bounds" in first_item["allowed_next_step"]


def test_candidate_only_false_blocks(sample_brief_packet):
    """Verify that candidate_only=False blocks compliance validation."""
    sample_brief_packet["candidate_review_items"][1]["candidate_only"] = False

    precheck = create_content_intent_gate_precheck(sample_brief_packet)
    assert precheck["content_intent_gate_status"] == "BLOCKED_NOT_CANDIDATE_ONLY"
    assert "safety_invariants_violated_in_candidates" in precheck["blocked_reasons"]

    second_item = precheck["candidate_gate_items"][1]
    assert second_item["content_intent_gate_status"] == "BLOCKED_NOT_CANDIDATE_ONLY"
    assert "quarantine_candidate_and_inspect_compliance_bounds" in second_item["allowed_next_step"]


def test_metadata_only_rules_and_forbidden_fields(sample_brief_packet):
    """Verify no forbidden draft/market analysis fields are present in the output."""
    precheck = create_content_intent_gate_precheck(sample_brief_packet)

    # Main packet assertions
    forbidden_keys = [
        "raw_record_contents", "source_extracted_facts", "market_values",
        "narrative_thesis", "headline", "hook", "caption",
        "draft_paragraph", "platform_copy", "prediction"
    ]
    for key in forbidden_keys:
        assert key not in precheck

    # Candidate gate items assertions
    allowed_keys = {
        "candidate_id", "relative_path", "evidence_role", "source_family",
        "records_count", "contract_name", "advisory_only", "candidate_only",
        "operator_review_required", "content_intent_gate_status",
        "blocked_reasons", "missing_requirements", "allowed_next_step"
    }

    for item in precheck["candidate_gate_items"]:
        # Verify only allowed keys are present
        assert set(item.keys()) <= allowed_keys


def test_safety_and_truth_flags_remain_false(sample_brief_packet):
    """Verify that safety and truth protection flags are strictly False."""
    precheck = create_content_intent_gate_precheck(sample_brief_packet)

    for val in precheck["truth_protection_flags"].values():
        assert val is False

    for val in precheck["safety_flags"].values():
        assert val is False


def test_next_recommended_task(sample_brief_packet):
    """Verify that next recommended task is correctly set."""
    precheck = create_content_intent_gate_precheck(sample_brief_packet)
    assert precheck["next_recommended_task"] == "TASK_CONTENTOPS_0175BK_CONTENT_INTENT_GATE_PRECHECK_TO_V5_INTENT_QUEUE_BINDING_V0"


def test_write_artifacts(tmp_path, sample_brief_packet):
    """Verify that write_artifacts successfully generates the runbook and json files."""
    input_file = tmp_path / "brief_packet.json"
    with open(input_file, "w", encoding="utf-8") as f:
        json.dump(sample_brief_packet, f)

    res = write_artifacts(brief_review_packet_path=input_file, repo_root=tmp_path)
    assert Path(res["packet_path"]).exists()
    assert Path(res["runbook_path"]).exists()

    # Load generated packet and check keys
    with open(res["packet_path"], "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["content_intent_gate_status"] == "BLOCKED_OPERATOR_REVIEW_REQUIRED"
