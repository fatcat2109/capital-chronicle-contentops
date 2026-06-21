"""Unit tests for the Content Intent Gate to Review-Only Intent Packet.

Part of TASK_CONTENTOPS_0175BL_CONTENT_INTENT_GATE_TO_REVIEW_ONLY_INTENT_PACKET_V0.
"""
from __future__ import annotations

import json
from pathlib import Path
import pytest

from live_contentops.content_intent_gate_to_review_only_intent_packet import (
    create_review_only_intent_packet,
    write_artifacts,
    map_intent_scope_label,
)


@pytest.fixture
def sample_precheck_packet() -> dict:
    """Fixture mimicking a valid 0175BJ Content Intent Gate Precheck packet."""
    return {
        "task_label": "TASK_CONTENTOPS_0175BJ_EDITORIAL_BRIEF_REVIEW_TO_CONTENT_INTENT_GATE_PRECHECK_V0",
        "source_editorial_brief_review_packet_hash": "1b5d799c189af120f7f0b0c668cce3f9442fbebc46f3aa6704581f3e865f9e77",
        "source_packet_task_label": "TASK_CONTENTOPS_0175BH_LIFECYCLE_INTAKE_BRIDGE_TO_EDITORIAL_BRIEF_REVIEW_PACKET_V0",
        "source_candidate_count": 2,
        "content_intent_gate_status": "BLOCKED_OPERATOR_REVIEW_REQUIRED",
        "operator_review_required": True,
        "blocked_reasons": ["operator_brief_review_pending"],
        "allowed_next_step": "operator_must_sign_off_content_intent_gate_precheck_to_unlock_drafting",
        "disallowed_outputs": [
            "raw_record_contents", "source_extracted_facts", "market_values"
        ],
        "packet_hash": "3ecf32419922a98e422b1290c44caf7623010fc06f6f20da2afa266ae2af0dfa",
        "candidate_gate_items": [
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
                "content_intent_gate_status": "READY_FOR_OPERATOR_INTENT_REVIEW",
                "blocked_reasons": ["waiting_for_operator_intent_review"],
                "missing_requirements": [],
                "allowed_next_step": "operator_must_review_metadata_before_intent_drafting",
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
                "content_intent_gate_status": "BLOCKED_MISSING_METADATA",
                "blocked_reasons": ["candidate_metadata_requirements_incomplete"],
                "missing_requirements": ["missing_source_family"],
                "allowed_next_step": "provide_required_candidate_metadata_fields",
            }
        ],
        "truth_protection_flags": {
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
        "next_recommended_task": "TASK_CONTENTOPS_0175BK_CONTENT_INTENT_GATE_PRECHECK_TO_V5_INTENT_QUEUE_BINDING_V0",
        "ledger_family": "editorial_brief_review_to_content_intent_gate_precheck_future",
        "hash_algorithm": "sha256"
    }


def test_produces_deterministic_intent_packet(sample_precheck_packet):
    """Verify that a valid precheck packet produces a deterministic review-only intent packet."""
    intent1 = create_review_only_intent_packet(sample_precheck_packet)
    intent2 = create_review_only_intent_packet(sample_precheck_packet)

    assert intent1["packet_hash"] == intent2["packet_hash"]
    assert intent1["task_label"] == "TASK_CONTENTOPS_0175BL_CONTENT_INTENT_GATE_TO_REVIEW_ONLY_INTENT_PACKET_V0"
    assert intent1["source_packet_task_label"] == "TASK_CONTENTOPS_0175BJ_EDITORIAL_BRIEF_REVIEW_TO_CONTENT_INTENT_GATE_PRECHECK_V0"
    assert intent1["source_candidate_count"] == 2
    assert len(intent1["review_only_intent_items"]) == 2


def test_gate_status_fail_closed_if_invalid_status(sample_precheck_packet):
    """Verify that an invalid content intent gate status fails closed."""
    sample_precheck_packet["content_intent_gate_status"] = "INVALID_STATUS_XYZ"
    with pytest.raises(ValueError) as exc:
        create_review_only_intent_packet(sample_precheck_packet)
    assert "Invalid content intent gate status" in str(exc.value)


def test_candidate_ready_status_transitions(sample_precheck_packet):
    """Verify ready/blocked candidate transitions."""
    intent = create_review_only_intent_packet(sample_precheck_packet)
    items = intent["review_only_intent_items"]

    # Candidate 0 was READY_FOR_OPERATOR_INTENT_REVIEW
    assert items[0]["review_only_intent_status"] == "REVIEW_ONLY_INTENT_PENDING_OPERATOR_INPUT"

    # Candidate 1 was BLOCKED_MISSING_METADATA
    assert items[1]["review_only_intent_status"] == "BLOCKED_BY_CONTENT_INTENT_GATE"


def test_intent_scope_label_mapping():
    """Verify mapping of controlled non-claim labels."""
    assert map_intent_scope_label("Official Text Spine", "c1") == "official_text_review"
    assert map_intent_scope_label("US Macro", "ttl_freshness_policy_contract_v1") == "ttl_freshness_policy_review"
    assert map_intent_scope_label("US Macro", "economic_prints_schema_contract_v1") == "schema_contract_review"
    assert map_intent_scope_label("US Macro", "bea_bls_census_normalized_contract_v1") == "macro_data_contract_review"
    assert map_intent_scope_label("Broker Proxy", "c2") == "broker_proxy_context_review"
    assert map_intent_scope_label("Unknown Family", "c3") == "unknown_metadata_review"


def test_operator_inputs_empty_not_generated_prose(sample_precheck_packet):
    """Verify that operator inputs are scaffold placeholders only."""
    intent = create_review_only_intent_packet(sample_precheck_packet)

    required_keys = {
        "intended_audience_lane", "content_purpose_category", "source_review_notes",
        "risk_review_notes", "claim_scope_boundary", "manual_operator_decision"
    }

    # Packet level inputs
    assert set(intent["required_operator_inputs"].keys()) == required_keys
    for val in intent["required_operator_inputs"].values():
        assert val == "PENDING_OPERATOR_INPUT"

    # Item level inputs
    for item in intent["review_only_intent_items"]:
        assert set(item["required_operator_inputs"].keys()) == required_keys
        for val in item["required_operator_inputs"].values():
            assert val == "PENDING_OPERATOR_INPUT"


def test_metadata_only_rules_and_forbidden_fields(sample_precheck_packet):
    """Verify no forbidden draft/market analysis fields are present in the output."""
    intent = create_review_only_intent_packet(sample_precheck_packet)

    forbidden_keys = [
        "raw_record_contents", "source_extracted_facts", "market_values",
        "narrative_thesis", "headline", "hook", "caption",
        "draft_paragraph", "platform_copy", "prediction"
    ]
    for key in forbidden_keys:
        assert key not in intent

    # Review-only intent items allowed keys
    allowed_keys = {
        "intent_item_id", "source_candidate_id", "relative_path", "evidence_role",
        "source_family", "records_count", "contract_name", "advisory_only",
        "candidate_only", "source_gate_status", "review_only_intent_status",
        "operator_review_required", "required_operator_inputs", "blocked_reasons",
        "missing_requirements", "allowed_next_step", "disallowed_outputs", "intent_scope_label"
    }

    for item in intent["review_only_intent_items"]:
        assert set(item.keys()) <= allowed_keys


def test_write_artifacts(tmp_path, sample_precheck_packet):
    """Verify that write_artifacts successfully generates the runbook and json files."""
    input_file = tmp_path / "precheck_packet.json"
    with open(input_file, "w", encoding="utf-8") as f:
        json.dump(sample_precheck_packet, f)

    res = write_artifacts(precheck_packet_path=input_file, repo_root=tmp_path)
    assert Path(res["packet_path"]).exists()
    assert Path(res["runbook_path"]).exists()

    with open(res["packet_path"], "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["global_intent_packet_status"] == "BLOCKED_OPERATOR_INTENT_INPUT_REQUIRED"
