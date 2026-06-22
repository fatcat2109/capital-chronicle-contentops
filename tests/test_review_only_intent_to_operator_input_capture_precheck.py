"""Unit tests for the Review-Only Content Intent to Operator Input Capture Precheck.

Part of TASK_CONTENTOPS_0175BN_REVIEW_ONLY_INTENT_TO_OPERATOR_INPUT_CAPTURE_PRECHECK_V0.
"""
from __future__ import annotations

import json
from pathlib import Path
import pytest

from live_contentops.review_only_intent_to_operator_input_capture_precheck import (
    create_operator_input_capture_precheck,
    write_artifacts
)


@pytest.fixture
def sample_intent_packet() -> dict:
    """Fixture mimicking a valid 0175BL Review-Only Content Intent Packet."""
    return {
        "task_label": "TASK_CONTENTOPS_0175BL_CONTENT_INTENT_GATE_TO_REVIEW_ONLY_INTENT_PACKET_V0",
        "source_content_intent_gate_precheck_packet_hash": "607f1ab0ab7b10ec10d2b4e0cb55154f0b20127c5ca3c6ce25c38dbeefeb3af6",
        "source_packet_task_label": "TASK_CONTENTOPS_0175BJ_EDITORIAL_BRIEF_REVIEW_TO_CONTENT_INTENT_GATE_PRECHECK_V0",
        "source_candidate_count": 2,
        "global_intent_packet_status": "BLOCKED_OPERATOR_INTENT_INPUT_REQUIRED",
        "operator_review_required": True,
        "blocked_reasons": ["operator_intent_input_pending", "intent_drafting_gated"],
        "allowed_next_step": "operator_must_provide_intent_inputs_to_unlock_drafting",
        "disallowed_outputs": [
            "raw_record_contents", "source_extracted_facts", "market_values"
        ],
        "packet_hash": "d2bf5de9b4a6cfc02270638efeff6715f70ad3cb2e80969df35af057fa343f99",
        "review_only_intent_items": [
            {
                "intent_item_id": "intent_item_STEP1_OFFICIAL_TEXT_LIVE_PROBE_MANIFEST_V1",
                "source_candidate_id": "STEP1_OFFICIAL_TEXT_LIVE_PROBE_MANIFEST_V1",
                "relative_path": "docs/research/database_foundation/pre_ia_acceleration/STEP1_OFFICIAL_TEXT_LIVE_PROBE_MANIFEST_V1.json",
                "evidence_role": "manifest",
                "source_family": "Official Text Spine",
                "records_count": 6,
                "contract_name": None,
                "advisory_only": True,
                "candidate_only": True,
                "source_gate_status": "READY_FOR_OPERATOR_INTENT_REVIEW",
                "review_only_intent_status": "REVIEW_ONLY_INTENT_PENDING_OPERATOR_INPUT",
                "operator_review_required": True,
                "required_operator_inputs": {
                    "claim_scope_boundary": "PENDING_OPERATOR_INPUT",
                    "content_purpose_category": "PENDING_OPERATOR_INPUT",
                    "intended_audience_lane": "PENDING_OPERATOR_INPUT",
                    "manual_operator_decision": "PENDING_OPERATOR_INPUT",
                    "risk_review_notes": "PENDING_OPERATOR_INPUT",
                    "source_review_notes": "PENDING_OPERATOR_INPUT"
                },
                "blocked_reasons": ["waiting_for_operator_intent_review"],
                "missing_requirements": [],
                "allowed_next_step": "operator_must_review_metadata_before_intent_drafting",
                "disallowed_outputs": ["raw_record_contents"],
                "intent_scope_label": "official_text_review"
            },
            {
                "intent_item_id": "intent_item_BEA_BLS_CENSUS_NORMALIZED_CONTRACT_V1",
                "source_candidate_id": "BEA_BLS_CENSUS_NORMALIZED_CONTRACT_V1",
                "relative_path": "docs/research/database_foundation/pre_ia_acceleration/BEA_BLS_CENSUS_NORMALIZED_CONTRACT_V1.json",
                "evidence_role": "contract",
                "source_family": "US Macro",
                "records_count": 1,
                "contract_name": "BEA_BLS_CENSUS_NORMALIZED_CONTRACT_V1",
                "advisory_only": True,
                "candidate_only": True,
                "source_gate_status": "BLOCKED_MISSING_METADATA",
                "review_only_intent_status": "BLOCKED_BY_CONTENT_INTENT_GATE",
                "operator_review_required": True,
                "required_operator_inputs": {
                    "claim_scope_boundary": "PENDING_OPERATOR_INPUT",
                    "content_purpose_category": "PENDING_OPERATOR_INPUT",
                    "intended_audience_lane": "PENDING_OPERATOR_INPUT",
                    "manual_operator_decision": "PENDING_OPERATOR_INPUT",
                    "risk_review_notes": "PENDING_OPERATOR_INPUT",
                    "source_review_notes": "PENDING_OPERATOR_INPUT"
                },
                "blocked_reasons": ["candidate_metadata_requirements_incomplete"],
                "missing_requirements": ["missing_source_family"],
                "allowed_next_step": "provide_required_candidate_metadata_fields",
                "disallowed_outputs": ["raw_record_contents"],
                "intent_scope_label": "macro_data_contract_review"
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
        "next_recommended_task": "TASK_CONTENTOPS_0175BM_REVIEW_ONLY_INTENT_PACKET_TO_V5_INTENT_DETAIL_BINDING_V0",
        "ledger_family": "content_intent_gate_to_review_only_intent_packet_future",
        "hash_algorithm": "sha256"
    }


def test_produces_deterministic_precheck_packet(sample_intent_packet):
    """Verify that a valid intent packet produces a deterministic precheck packet."""
    precheck1 = create_operator_input_capture_precheck(sample_intent_packet)
    precheck2 = create_operator_input_capture_precheck(sample_intent_packet)

    assert precheck1["packet_hash"] == precheck2["packet_hash"]
    assert precheck1["task_label"] == "TASK_CONTENTOPS_0175BN_REVIEW_ONLY_INTENT_TO_OPERATOR_INPUT_CAPTURE_PRECHECK_V0"
    assert precheck1["source_packet_task_label"] == "TASK_CONTENTOPS_0175BL_CONTENT_INTENT_GATE_TO_REVIEW_ONLY_INTENT_PACKET_V0"
    assert precheck1["source_intent_item_count"] == 2
    assert len(precheck1["input_capture_precheck_items"]) == 2


def test_gate_status_fail_closed_if_invalid_status(sample_intent_packet):
    """Verify that an invalid global status fails closed."""
    sample_intent_packet["global_intent_packet_status"] = "INVALID_STATUS_XYZ"
    with pytest.raises(ValueError) as exc:
        create_operator_input_capture_precheck(sample_intent_packet)
    assert "Invalid global intent packet status" in str(exc.value)


def test_intent_item_status_transitions(sample_intent_packet):
    """Verify intent item precheck status mapping rules."""
    precheck = create_operator_input_capture_precheck(sample_intent_packet)
    items = precheck["input_capture_precheck_items"]

    # Item 0 was REVIEW_ONLY_INTENT_PENDING_OPERATOR_INPUT
    assert items[0]["operator_input_capture_precheck_status"] == "OPERATOR_INPUT_CAPTURE_PRECHECK_PENDING"

    # Item 1 was BLOCKED_BY_CONTENT_INTENT_GATE
    assert items[1]["operator_input_capture_precheck_status"] == "BLOCKED_BY_REVIEW_ONLY_INTENT_PACKET"


def test_field_policy_assertions(sample_intent_packet):
    """Verify that all fields are schema-only and pending input."""
    precheck = create_operator_input_capture_precheck(sample_intent_packet)
    policy = precheck["field_policy"]

    required_fields = {
        "intended_audience_lane", "content_purpose_category", "source_review_notes",
        "risk_review_notes", "claim_scope_boundary", "manual_operator_decision"
    }

    assert set(precheck["required_input_fields"]) == required_fields
    assert set(policy.keys()) == required_fields

    for field, rule in policy.items():
        assert rule["required"] is True
        assert rule["value_status"] == "PENDING_OPERATOR_INPUT"
        assert rule["capture_enabled"] is False
        assert rule["editable_in_this_task"] is False
        assert rule["generated_by_system"] is False
        assert rule["stored_value"] == "PENDING_OPERATOR_INPUT"
        assert rule["operator_must_provide_later"] is True


def test_metadata_only_rules_and_forbidden_fields(sample_intent_packet):
    """Verify no content-generation or publishable draft fields are present."""
    precheck = create_operator_input_capture_precheck(sample_intent_packet)

    forbidden_keys = [
        "raw_record_contents", "source_extracted_facts", "market_values",
        "narrative_thesis", "headline", "hook", "caption",
        "draft_paragraph", "platform_copy", "prediction"
    ]
    for key in forbidden_keys:
        assert key not in precheck

    # Inspect allowed keys in precheck items
    allowed_keys = {
        "intent_item_id", "source_candidate_id", "relative_path", "evidence_role",
        "source_family", "records_count", "contract_name", "intent_scope_label",
        "source_gate_status", "operator_input_capture_precheck_status",
        "operator_review_required", "required_input_fields", "field_policy",
        "blocked_reasons", "missing_requirements", "allowed_next_step", "disallowed_outputs"
    }

    for item in precheck["input_capture_precheck_items"]:
        assert set(item.keys()) <= allowed_keys


def test_write_artifacts(tmp_path, sample_intent_packet):
    """Verify that write_artifacts successfully generates output runbook and json."""
    input_file = tmp_path / "intent_packet.json"
    with open(input_file, "w", encoding="utf-8") as f:
        json.dump(sample_intent_packet, f)

    res = write_artifacts(intent_packet_path=input_file, repo_root=tmp_path)
    assert Path(res["packet_path"]).exists()
    assert Path(res["runbook_path"]).exists()

    with open(res["packet_path"], "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["global_operator_input_capture_status"] == "BLOCKED_OPERATOR_INPUT_CAPTURE_NOT_ENABLED"
