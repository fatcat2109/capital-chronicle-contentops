"""Tests for Operator Value Intake Readiness Review.

Part of TASK_CONTENTOPS_0175CC_LOCAL_VALUE_VALIDATION_RULES_TO_OPERATOR_VALUE_INTAKE_READINESS_REVIEW_V0.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from live_contentops.local_value_validation_rules_to_operator_value_intake_readiness_review import (
    DISALLOWED_OUTPUTS,
    FORBIDDEN_CURRENT_ACTIONS,
    GLOBAL_OPERATOR_VALUE_INTAKE_READINESS_REVIEW_STATUS,
    NEXT_RECOMMENDED_TASK,
    READINESS_PREREQUISITES,
    REQUIRED_INPUT_FIELDS,
    SAFETY_FLAGS,
    SOURCE_GLOBAL_STATUS_REQUIRED,
    TRUTH_PROTECTION_FLAGS,
    create_operator_value_intake_readiness_review,
)

ROOT = Path(__file__).resolve().parents[1]
SOURCE_PACKET_PATH = ROOT / "docs" / "automation" / "0175CB" / "local_value_redaction_rules_to_local_value_validation_rules_contract_packet.json"

FORBIDDEN_OUTPUT_KEYS = {
    "operator_prose",
    "operator_notes_text",
    "draft",
    "draft_text",
    "draft_paragraph",
    "headline",
    "hook",
    "caption",
    "platform_copy",
    "generated_copy",
    "editorial_thesis",
    "thesis",
    "operator_input_value",
    "operator_review_notes_text",
    "captured_operator_value",
    "redacted_operator_value",
    "dry_run_operator_value",
    "accepted_operator_value",
    "redaction_result_value",
    "validation_result_value",
    "validated_operator_value",
    "operator_value_intake_payload",
    "public_ready_content",
}


@pytest.fixture
def source_packet() -> dict:
    with open(SOURCE_PACKET_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def packet(source_packet) -> dict:
    return create_operator_value_intake_readiness_review(source_packet)


def test_valid_0175cb_packet_produces_deterministic_operator_value_intake_readiness_review(source_packet):
    first = create_operator_value_intake_readiness_review(source_packet)
    second = create_operator_value_intake_readiness_review(source_packet)

    assert first == second
    assert first["packet_hash"] == second["packet_hash"]
    assert first["task_label"] == "TASK_CONTENTOPS_0175CC_LOCAL_VALUE_VALIDATION_RULES_TO_OPERATOR_VALUE_INTAKE_READINESS_REVIEW_V0"
    assert first["source_packet_task_label"] == "TASK_CONTENTOPS_0175CB_LOCAL_VALUE_REDACTION_RULES_TO_LOCAL_VALUE_VALIDATION_RULES_CONTRACT_V0"
    assert first["source_local_value_validation_rules_contract_packet_hash"] == source_packet["packet_hash"]


def test_every_validation_rule_item_maps_to_one_readiness_review_item(source_packet, packet):
    source_items = source_packet["local_value_validation_rule_items"]
    assert packet["source_local_value_validation_rule_item_count"] == len(source_items)
    assert len(packet["operator_value_intake_readiness_review_items"]) == len(source_items)

    for index, (source_item, item) in enumerate(zip(source_items, packet["operator_value_intake_readiness_review_items"]), start=1):
        assert item["readiness_review_item_id"] == f"operator_value_intake_readiness_review_item_{index:02d}_{source_item['source_candidate_id']}"
        assert item["source_validation_rule_item_id"] == source_item["validation_rule_item_id"]
        assert item["source_candidate_id"] == source_item["source_candidate_id"]
        assert item["relative_path"] == source_item["relative_path"]
        assert item["evidence_role"] == source_item["evidence_role"]
        assert item["source_family"] == source_item["source_family"]
        assert item["records_count"] == source_item["records_count"]
        assert item["contract_name"] == source_item["contract_name"]
        assert item["intent_scope_label"] == source_item["intent_scope_label"]


def test_global_status_and_all_six_required_fields_remain_missing(packet):
    assert packet["global_operator_value_intake_readiness_review_status"] == GLOBAL_OPERATOR_VALUE_INTAKE_READINESS_REVIEW_STATUS
    assert packet["required_input_fields"] == list(REQUIRED_INPUT_FIELDS)
    assert packet["missing_required_input_fields"] == list(REQUIRED_INPUT_FIELDS)
    assert len(packet["required_input_fields"]) == 6
    assert packet["operator_value_intake_enabled"] is False
    assert packet["operator_value_capture_enabled"] is False
    assert packet["operator_value_persistence_enabled"] is False
    for item in packet["operator_value_intake_readiness_review_items"]:
        assert item["required_input_fields"] == list(REQUIRED_INPUT_FIELDS)
        assert item["missing_required_input_fields"] == list(REQUIRED_INPUT_FIELDS)


def test_readiness_prerequisites_are_complete_and_satisfied_for_future_design(packet):
    assert packet["readiness_prerequisites"] == list(READINESS_PREREQUISITES)
    assert len(packet["readiness_prerequisites"]) == 18
    assert set(packet["prerequisite_review"]) == set(READINESS_PREREQUISITES)
    assert packet["all_prerequisites_satisfied_for_future_intake_design"] is True
    for name, review in packet["prerequisite_review"].items():
        assert name in READINESS_PREREQUISITES
        assert review["satisfied"] is True
        assert review["current_status"] in {"present", "documented", "missing_as_required_for_schema_only_review", "disabled"}


def test_readiness_execution_policy_completes_review_but_keeps_runtime_disabled(packet):
    policy = packet["readiness_execution_policy"]
    assert policy["operator_value_intake_readiness_review_completed"] is True
    for key, value in policy.items():
        if key == "operator_value_intake_readiness_review_completed":
            assert value is True
        else:
            assert value is False, key

    for item in packet["operator_value_intake_readiness_review_items"]:
        assert item["readiness_execution_policy"] == policy
        assert item["readiness_execution_policy"]["operator_value_intake_enabled"] is False
        assert item["readiness_execution_policy"]["captures_operator_values"] is False


def test_future_intake_boundary_points_to_new_stub_task_and_keeps_review_only(packet):
    boundary = packet["future_intake_boundary"]
    assert boundary["review_only_now"] is True
    assert boundary["future_intake_requires_new_task"] is True
    assert boundary["future_intake_requires_supervised_local_value_entry_stub"] is True
    assert boundary["future_intake_requires_operator_supplied_values"] is True
    assert boundary["future_intake_requires_redaction_before_validation"] is True
    assert boundary["future_intake_requires_validation_before_acceptance"] is True
    assert boundary["future_intake_requires_evidence_before_persistence"] is True
    assert boundary["allowed_next_step"] == "stage_operator_value_intake_readiness_review_to_supervised_local_value_entry_stub"


def test_item_status_mapping_for_pending_blocked_and_unknown_source_statuses(source_packet):
    pending_packet = create_operator_value_intake_readiness_review(source_packet)
    assert all(
        item["operator_value_intake_readiness_review_status"] == GLOBAL_OPERATOR_VALUE_INTAKE_READINESS_REVIEW_STATUS
        for item in pending_packet["operator_value_intake_readiness_review_items"]
    )

    blocked_source = copy.deepcopy(source_packet)
    blocked_source["local_value_validation_rule_items"][0]["local_value_validation_rules_contract_status"] = "BLOCKED_CUSTOM_REASON"
    blocked_packet = create_operator_value_intake_readiness_review(blocked_source)
    assert blocked_packet["operator_value_intake_readiness_review_items"][0]["operator_value_intake_readiness_review_status"] == "BLOCKED_BY_LOCAL_VALUE_VALIDATION_RULES_CONTRACT"

    unknown_source = copy.deepcopy(source_packet)
    unknown_source["local_value_validation_rule_items"][0]["local_value_validation_rules_contract_status"] = "READY_UNEXPECTED"
    unknown_packet = create_operator_value_intake_readiness_review(unknown_source)
    assert unknown_packet["operator_value_intake_readiness_review_items"][0]["operator_value_intake_readiness_review_status"] == "BLOCKED_BY_LOCAL_VALUE_VALIDATION_RULES_CONTRACT"


def test_forbidden_actions_and_disallowed_outputs_include_intake_boundaries(packet):
    assert packet["forbidden_current_actions"] == list(FORBIDDEN_CURRENT_ACTIONS)
    assert "actual_operator_value_intake" in packet["forbidden_current_actions"]
    assert "actual_input_capture" in packet["forbidden_current_actions"]
    assert "validation_execution" in packet["forbidden_current_actions"]
    assert "redaction_execution" in packet["forbidden_current_actions"]
    assert packet["disallowed_outputs"] == list(DISALLOWED_OUTPUTS)
    assert "operator_value_intake_payload" in packet["disallowed_outputs"]
    assert "validated_operator_value" in packet["disallowed_outputs"]


def test_safety_flags_false_except_readiness_review_schema_only(packet):
    assert packet["safety_flags"] == SAFETY_FLAGS
    for key, value in packet["safety_flags"].items():
        if key == "operator_value_intake_readiness_review_schema_only":
            assert value is True
        else:
            assert value is False, key


def test_truth_flags_remain_false(packet):
    assert packet["truth_protection_flags"] == TRUTH_PROTECTION_FLAGS
    assert packet["truth_protection_flags"]["operator_value_intake_readiness_truth_promoted"] is False
    assert all(value is False for value in packet["truth_protection_flags"].values())


def test_no_forbidden_public_or_operator_value_fields_are_emitted(packet):
    def walk(value):
        if isinstance(value, dict):
            for key, child in value.items():
                assert key not in FORBIDDEN_OUTPUT_KEYS
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(packet)


def test_invalid_source_global_status_fails_closed(source_packet):
    bad_packet = copy.deepcopy(source_packet)
    bad_packet["global_local_value_validation_rules_contract_status"] = "READY_UNEXPECTED"
    with pytest.raises(ValueError, match="global_local_value_validation_rules_contract_status"):
        create_operator_value_intake_readiness_review(bad_packet)


def test_source_without_schema_only_flag_fails_closed(source_packet):
    bad_packet = copy.deepcopy(source_packet)
    bad_packet["safety_flags"]["validation_rules_schema_only"] = False
    with pytest.raises(ValueError, match="validation_rules_schema_only"):
        create_operator_value_intake_readiness_review(bad_packet)


def test_source_with_operator_value_intake_enabled_fails_closed(source_packet):
    bad_packet = copy.deepcopy(source_packet)
    bad_packet["safety_flags"]["operator_value_intake_enabled"] = True
    with pytest.raises(ValueError, match="operator_value_intake_enabled"):
        create_operator_value_intake_readiness_review(bad_packet)


def test_source_with_validation_execution_enabled_fails_closed(source_packet):
    bad_packet = copy.deepcopy(source_packet)
    bad_packet["safety_flags"]["validation_execution_enabled"] = True
    with pytest.raises(ValueError, match="validation_execution_enabled"):
        create_operator_value_intake_readiness_review(bad_packet)


def test_source_with_unexpected_required_fields_fails_closed(source_packet):
    bad_packet = copy.deepcopy(source_packet)
    bad_packet["required_input_fields"] = REQUIRED_INPUT_FIELDS[:-1]
    with pytest.raises(ValueError, match="required_input_fields"):
        create_operator_value_intake_readiness_review(bad_packet)


def test_next_recommended_task_is_set(packet):
    assert packet["next_recommended_task"] == NEXT_RECOMMENDED_TASK
    assert packet["allowed_next_step"] == "stage_operator_value_intake_readiness_review_to_supervised_local_value_entry_stub"
