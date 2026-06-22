"""Tests for Supervised Manual Input Dry Run Precheck to Operator Value Intake Policy.

Part of TASK_CONTENTOPS_0175BZ_SUPERVISED_MANUAL_INPUT_DRY_RUN_PRECHECK_TO_OPERATOR_VALUE_INTAKE_POLICY_V0.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from live_contentops.supervised_manual_input_dry_run_precheck_to_operator_value_intake_policy import (
    ALLOWED_FUTURE_INTAKE_MODES,
    DISALLOWED_OUTPUTS,
    FORBIDDEN_CURRENT_ACTIONS,
    GLOBAL_OPERATOR_VALUE_INTAKE_POLICY_STATUS,
    NEXT_RECOMMENDED_TASK,
    REQUIRED_INPUT_FIELDS,
    SAFETY_FLAGS,
    TRUTH_PROTECTION_FLAGS,
    create_operator_value_intake_policy,
)

ROOT = Path(__file__).resolve().parents[1]
SOURCE_PACKET_PATH = ROOT / "docs" / "automation" / "0175BY" / "operator_input_capture_gate_to_supervised_manual_input_dry_run_precheck_packet.json"

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
    "validation_result_value",
    "public_ready_content",
}


@pytest.fixture
def source_packet() -> dict:
    with open(SOURCE_PACKET_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def packet(source_packet) -> dict:
    return create_operator_value_intake_policy(source_packet)


def test_valid_0175by_packet_produces_deterministic_operator_value_intake_policy(source_packet):
    first = create_operator_value_intake_policy(source_packet)
    second = create_operator_value_intake_policy(source_packet)

    assert first == second
    assert first["packet_hash"] == second["packet_hash"]
    assert first["task_label"] == "TASK_CONTENTOPS_0175BZ_SUPERVISED_MANUAL_INPUT_DRY_RUN_PRECHECK_TO_OPERATOR_VALUE_INTAKE_POLICY_V0"
    assert first["source_packet_task_label"] == "TASK_CONTENTOPS_0175BY_OPERATOR_INPUT_CAPTURE_GATE_TO_SUPERVISED_MANUAL_INPUT_DRY_RUN_PRECHECK_V0"
    assert first["source_manual_input_dry_run_precheck_packet_hash"] == source_packet["packet_hash"]


def test_every_dry_run_item_maps_to_one_policy_item(source_packet, packet):
    assert packet["source_dry_run_item_count"] == len(source_packet["dry_run_items"])
    assert len(packet["operator_value_intake_policy_items"]) == len(source_packet["dry_run_items"])

    for index, (source_item, item) in enumerate(zip(source_packet["dry_run_items"], packet["operator_value_intake_policy_items"]), start=1):
        assert item["intake_policy_item_id"] == f"operator_value_intake_policy_item_{index:02d}_{source_item['source_candidate_id']}"
        assert item["source_dry_run_item_id"] == source_item["dry_run_item_id"]
        assert item["source_candidate_id"] == source_item["source_candidate_id"]
        assert item["relative_path"] == source_item["relative_path"]
        assert item["evidence_role"] == source_item["evidence_role"]
        assert item["source_family"] == source_item["source_family"]
        assert item["records_count"] == source_item["records_count"]
        assert item["contract_name"] == source_item["contract_name"]
        assert item["intent_scope_label"] == source_item["intent_scope_label"]


def test_global_status_and_required_fields_remain_blocked(packet):
    assert packet["global_operator_value_intake_policy_status"] == GLOBAL_OPERATOR_VALUE_INTAKE_POLICY_STATUS
    assert packet["required_input_fields"] == list(REQUIRED_INPUT_FIELDS)
    assert packet["missing_required_input_fields"] == list(REQUIRED_INPUT_FIELDS)
    for item in packet["operator_value_intake_policy_items"]:
        assert item["required_input_fields"] == list(REQUIRED_INPUT_FIELDS)
        assert item["missing_required_input_fields"] == list(REQUIRED_INPUT_FIELDS)


def test_value_intake_field_policy_exists_for_all_fields_and_intake_disabled(packet):
    assert set(packet["value_intake_field_policy"]) == set(REQUIRED_INPUT_FIELDS)
    for field, policy in packet["value_intake_field_policy"].items():
        assert field in REQUIRED_INPUT_FIELDS
        assert policy["intake_allowed_in_future"] is True
        assert policy["intake_enabled_in_this_task"] is False
        assert policy["current_value"] is None
        assert policy["current_value_present"] is False
        assert policy["placeholder_value"] == "PENDING_OPERATOR_INPUT"
        assert policy["expected_value_owner"] == "human_operator"
        assert policy["system_generated_value_forbidden"] is True
        assert policy["acceptance_status"] == "BLOCKED_INTAKE_DISABLED"


def test_value_shape_policy_blocks_unsafe_shapes(packet):
    assert set(packet["value_shape_policy"]) == set(REQUIRED_INPUT_FIELDS)
    for policy in packet["value_shape_policy"].values():
        assert policy["allowed_value_type"] == "non_empty_string"
        assert policy["empty_value_allowed"] is False
        assert policy["whitespace_only_allowed"] is False
        assert policy["structured_payload_allowed"] is False
        assert policy["binary_attachment_allowed"] is False
        assert policy["executable_content_allowed"] is False
        assert policy["market_value_allowed"] is False
        assert policy["validation_enabled_in_this_task"] is False


def test_prohibited_value_content_policy_blocks_sensitive_and_financial_content(packet):
    assert set(packet["prohibited_value_content_policy"]) == set(REQUIRED_INPUT_FIELDS)
    for policy in packet["prohibited_value_content_policy"].values():
        assert policy["secrets_forbidden"] is True
        assert policy["credentials_forbidden"] is True
        assert policy["raw_vendor_redistribution_forbidden"] is True
        assert policy["unverified_market_values_forbidden"] is True
        assert policy["financial_signal_language_forbidden"] is True
        assert policy["buy_sell_hold_language_forbidden"] is True
        assert policy["price_target_language_forbidden"] is True
        assert policy["order_fill_pnl_language_forbidden"] is True
        assert policy["external_link_required_for_acceptance"] is False
        assert policy["policy_scan_enabled_in_this_task"] is False


def test_evidence_and_dependency_policies_exist_but_execution_disabled(packet):
    evidence = packet["intake_evidence_policy"]
    assert evidence["operator_identity_or_session_ref_required"] is True
    assert evidence["timestamp_required"] is True
    assert evidence["source_packet_hash_required"] is True
    assert evidence["manual_review_notes_required"] is True
    assert evidence["redaction_check_required"] is True
    assert evidence["validation_check_required"] is True
    assert evidence["evidence_capture_enabled_in_this_task"] is False

    redaction = packet["intake_redaction_dependency_policy"]
    assert redaction["redaction_required_before_acceptance"] is True
    assert redaction["redaction_execution_enabled_in_this_task"] is False
    assert redaction["redacted_value_generation_enabled"] is False
    assert redaction["requires_real_operator_values"] is True
    assert redaction["dependency_status"] == "BLOCKED_PENDING_OPERATOR_VALUES"

    validation = packet["intake_validation_dependency_policy"]
    assert validation["validation_required_before_acceptance"] is True
    assert validation["validation_execution_enabled_in_this_task"] is False
    assert validation["validation_result_generation_enabled"] is False
    assert validation["requires_real_operator_values"] is True
    assert validation["dependency_status"] == "BLOCKED_PENDING_OPERATOR_VALUES"


def test_intake_execution_policy_has_all_runtime_flags_false(packet):
    for key, value in packet["intake_execution_policy"].items():
        assert value is False, key

    for item in packet["operator_value_intake_policy_items"]:
        for key, value in item["intake_execution_policy"].items():
            assert value is False, key


def test_allowed_future_intake_modes_are_enum_only_and_disabled(packet):
    assert packet["allowed_future_intake_modes"] == list(ALLOWED_FUTURE_INTAKE_MODES)
    assert packet["intake_execution_policy"]["operator_value_intake_enabled"] is False
    for item in packet["operator_value_intake_policy_items"]:
        assert item["intake_execution_policy"]["operator_value_intake_enabled"] is False


def test_status_mapping_for_pending_blocked_and_unknown_source_statuses(source_packet):
    pending_packet = create_operator_value_intake_policy(source_packet)
    assert all(
        item["operator_value_intake_policy_status"] == GLOBAL_OPERATOR_VALUE_INTAKE_POLICY_STATUS
        for item in pending_packet["operator_value_intake_policy_items"]
    )

    blocked_source = copy.deepcopy(source_packet)
    blocked_source["dry_run_items"][0]["dry_run_status"] = "BLOCKED_CUSTOM_REASON"
    blocked_packet = create_operator_value_intake_policy(blocked_source)
    assert blocked_packet["operator_value_intake_policy_items"][0]["operator_value_intake_policy_status"] == "BLOCKED_BY_MANUAL_INPUT_DRY_RUN_PRECHECK"

    unknown_source = copy.deepcopy(source_packet)
    unknown_source["dry_run_items"][0]["dry_run_status"] = "READY_UNEXPECTED"
    unknown_packet = create_operator_value_intake_policy(unknown_source)
    assert unknown_packet["operator_value_intake_policy_items"][0]["operator_value_intake_policy_status"] == "BLOCKED_BY_MANUAL_INPUT_DRY_RUN_PRECHECK"


def test_forbidden_actions_and_disallowed_outputs_include_new_value_boundaries(packet):
    assert packet["forbidden_current_actions"] == list(FORBIDDEN_CURRENT_ACTIONS)
    assert "operator_value_intake" in packet["forbidden_current_actions"]
    assert "redacted_value_generation" in packet["forbidden_current_actions"]
    assert "validation_result_generation" in packet["forbidden_current_actions"]
    assert packet["disallowed_outputs"] == list(DISALLOWED_OUTPUTS)
    assert "accepted_operator_value" in packet["disallowed_outputs"]
    assert "validation_result_value" in packet["disallowed_outputs"]


def test_safety_flags_false_except_policy_schema_only(packet):
    assert packet["safety_flags"] == SAFETY_FLAGS
    for key, value in packet["safety_flags"].items():
        if key == "policy_schema_only":
            assert value is True
        else:
            assert value is False, key


def test_truth_flags_remain_false(packet):
    assert packet["truth_protection_flags"] == TRUTH_PROTECTION_FLAGS
    assert packet["truth_protection_flags"]["accepted_operator_value_truth_promoted"] is False
    assert packet["truth_protection_flags"]["validation_result_truth_promoted"] is False
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
    bad_packet["global_manual_input_dry_run_status"] = "READY_UNEXPECTED"
    with pytest.raises(ValueError, match="global_manual_input_dry_run_status"):
        create_operator_value_intake_policy(bad_packet)


def test_next_recommended_task_is_set(packet):
    assert packet["next_recommended_task"] == NEXT_RECOMMENDED_TASK
    assert packet["allowed_next_step"] == "stage_operator_value_intake_policy_to_local_value_redaction_rules_contract"
