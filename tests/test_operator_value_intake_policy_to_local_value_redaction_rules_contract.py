"""Tests for Operator Value Intake Policy to Local Value Redaction Rules Contract.

Part of TASK_CONTENTOPS_0175CA_OPERATOR_VALUE_INTAKE_POLICY_TO_LOCAL_VALUE_REDACTION_RULES_CONTRACT_V0.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from live_contentops.operator_value_intake_policy_to_local_value_redaction_rules_contract import (
    ALLOWED_FUTURE_REDACTION_MODES,
    DISALLOWED_OUTPUTS,
    FORBIDDEN_CURRENT_ACTIONS,
    GLOBAL_LOCAL_VALUE_REDACTION_RULES_CONTRACT_STATUS,
    NEXT_RECOMMENDED_TASK,
    REQUIRED_INPUT_FIELDS,
    RULE_IDS,
    SAFETY_FLAGS,
    TRUTH_PROTECTION_FLAGS,
    create_local_value_redaction_rules_contract,
)

ROOT = Path(__file__).resolve().parents[1]
SOURCE_PACKET_PATH = ROOT / "docs" / "automation" / "0175BZ" / "supervised_manual_input_dry_run_precheck_to_operator_value_intake_policy_packet.json"

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
    "public_ready_content",
}


@pytest.fixture
def source_packet() -> dict:
    with open(SOURCE_PACKET_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def packet(source_packet) -> dict:
    return create_local_value_redaction_rules_contract(source_packet)


def test_valid_0175bz_packet_produces_deterministic_local_redaction_rules_contract(source_packet):
    first = create_local_value_redaction_rules_contract(source_packet)
    second = create_local_value_redaction_rules_contract(source_packet)

    assert first == second
    assert first["packet_hash"] == second["packet_hash"]
    assert first["task_label"] == "TASK_CONTENTOPS_0175CA_OPERATOR_VALUE_INTAKE_POLICY_TO_LOCAL_VALUE_REDACTION_RULES_CONTRACT_V0"
    assert first["source_packet_task_label"] == "TASK_CONTENTOPS_0175BZ_SUPERVISED_MANUAL_INPUT_DRY_RUN_PRECHECK_TO_OPERATOR_VALUE_INTAKE_POLICY_V0"
    assert first["source_operator_value_intake_policy_packet_hash"] == source_packet["packet_hash"]


def test_every_intake_policy_item_maps_to_one_redaction_rule_item(source_packet, packet):
    assert packet["source_operator_value_intake_policy_item_count"] == len(source_packet["operator_value_intake_policy_items"])
    assert len(packet["local_value_redaction_rule_items"]) == len(source_packet["operator_value_intake_policy_items"])

    for index, (source_item, item) in enumerate(zip(source_packet["operator_value_intake_policy_items"], packet["local_value_redaction_rule_items"]), start=1):
        assert item["redaction_rule_item_id"] == f"local_value_redaction_rule_item_{index:02d}_{source_item['source_candidate_id']}"
        assert item["source_intake_policy_item_id"] == source_item["intake_policy_item_id"]
        assert item["source_candidate_id"] == source_item["source_candidate_id"]
        assert item["relative_path"] == source_item["relative_path"]
        assert item["evidence_role"] == source_item["evidence_role"]
        assert item["source_family"] == source_item["source_family"]
        assert item["records_count"] == source_item["records_count"]
        assert item["contract_name"] == source_item["contract_name"]
        assert item["intent_scope_label"] == source_item["intent_scope_label"]


def test_global_status_and_required_fields_remain_blocked(packet):
    assert packet["global_local_value_redaction_rules_contract_status"] == GLOBAL_LOCAL_VALUE_REDACTION_RULES_CONTRACT_STATUS
    assert packet["required_input_fields"] == list(REQUIRED_INPUT_FIELDS)
    assert packet["missing_required_input_fields"] == list(REQUIRED_INPUT_FIELDS)
    for item in packet["local_value_redaction_rule_items"]:
        assert item["required_input_fields"] == list(REQUIRED_INPUT_FIELDS)
        assert item["missing_required_input_fields"] == list(REQUIRED_INPUT_FIELDS)


def test_redaction_rule_catalog_contains_all_required_rule_ids(packet):
    assert [rule["rule_id"] for rule in packet["redaction_rule_catalog"]] == list(RULE_IDS)
    assert len(packet["redaction_rule_catalog"]) == 12


def test_every_rule_requires_detection_redaction_or_rejection_and_execution_disabled(packet):
    for rule in packet["redaction_rule_catalog"]:
        assert rule["applies_to_fields"] == list(REQUIRED_INPUT_FIELDS)
        assert rule["detection_required_before_acceptance"] is True
        assert rule["redaction_or_rejection_required_before_acceptance"] is True
        assert rule["execution_enabled_in_this_task"] is False
        assert rule["generated_redacted_value_enabled"] is False
        assert rule["evidence_required"] is True
        assert rule["pass_status"] == "BLOCKED_PENDING_OPERATOR_VALUE"

    for item in packet["local_value_redaction_rule_items"]:
        assert [rule["rule_id"] for rule in item["redaction_rule_catalog"]] == list(RULE_IDS)


def test_field_redaction_rule_map_exists_for_all_fields_and_execution_disabled(packet):
    assert set(packet["field_redaction_rule_map"]) == set(REQUIRED_INPUT_FIELDS)
    for field, policy in packet["field_redaction_rule_map"].items():
        assert field in REQUIRED_INPUT_FIELDS
        assert policy["field_name"] == field
        assert policy["current_value"] is None
        assert policy["current_value_present"] is False
        assert policy["applicable_rule_ids"] == list(RULE_IDS)
        assert policy["redaction_required_before_acceptance"] is True
        assert policy["rejection_required_if_rule_matches"] is True
        assert policy["redaction_execution_enabled_in_this_task"] is False
        assert policy["redacted_value_generation_enabled_in_this_task"] is False
        assert policy["policy_scan_enabled_in_this_task"] is False
        assert policy["acceptance_status"] == "BLOCKED_REDACTION_RULES_DEFINED_EXECUTION_DISABLED"
        assert policy["blocking_reason"] == "operator_values_absent_and_redaction_execution_disabled"


def test_redaction_evidence_policy_exists_and_capture_disabled(packet):
    evidence = packet["redaction_evidence_policy"]
    assert evidence["source_packet_hash_required"] is True
    assert evidence["operator_value_hash_required_after_future_entry"] is True
    assert evidence["redaction_rule_results_required"] is True
    assert evidence["redaction_operator_or_session_ref_required"] is True
    assert evidence["timestamp_required"] is True
    assert evidence["no_secret_values_allowed"] is True
    assert evidence["no_credentials_allowed"] is True
    assert evidence["no_raw_vendor_redistribution_allowed"] is True
    assert evidence["no_unverified_market_values_allowed"] is True
    assert evidence["no_financial_signal_language_allowed"] is True
    assert evidence["evidence_capture_enabled_in_this_task"] is False


def test_redaction_execution_policy_has_all_runtime_flags_false(packet):
    for key, value in packet["redaction_execution_policy"].items():
        assert value is False, key

    for item in packet["local_value_redaction_rule_items"]:
        for key, value in item["redaction_execution_policy"].items():
            assert value is False, key


def test_redaction_failure_policy_fail_closes_every_class(packet):
    expected = {
        "fail_closed_on_secret_detected",
        "fail_closed_on_credential_detected",
        "fail_closed_on_raw_vendor_redistribution_detected",
        "fail_closed_on_unverified_market_value_detected",
        "fail_closed_on_financial_signal_language_detected",
        "fail_closed_on_buy_sell_hold_language_detected",
        "fail_closed_on_price_target_language_detected",
        "fail_closed_on_order_fill_pnl_language_detected",
        "fail_closed_on_executable_content_detected",
        "fail_closed_on_binary_attachment_detected",
        "fail_closed_on_structured_payload_detected",
        "fail_closed_on_empty_or_whitespace_value_detected",
    }
    assert set(packet["redaction_failure_policy"]) == expected
    assert all(value is True for value in packet["redaction_failure_policy"].values())


def test_allowed_future_redaction_modes_are_enum_only_and_disabled(packet):
    assert packet["allowed_future_redaction_modes"] == list(ALLOWED_FUTURE_REDACTION_MODES)
    assert packet["redaction_execution_policy"]["redaction_execution_enabled"] is False
    assert packet["redaction_execution_policy"]["policy_scan_enabled"] is False
    for item in packet["local_value_redaction_rule_items"]:
        assert item["redaction_execution_policy"]["redaction_execution_enabled"] is False
        assert item["redaction_execution_policy"]["policy_scan_enabled"] is False


def test_status_mapping_for_pending_blocked_and_unknown_source_statuses(source_packet):
    pending_packet = create_local_value_redaction_rules_contract(source_packet)
    assert all(
        item["local_value_redaction_rules_contract_status"] == GLOBAL_LOCAL_VALUE_REDACTION_RULES_CONTRACT_STATUS
        for item in pending_packet["local_value_redaction_rule_items"]
    )

    blocked_source = copy.deepcopy(source_packet)
    blocked_source["operator_value_intake_policy_items"][0]["operator_value_intake_policy_status"] = "BLOCKED_CUSTOM_REASON"
    blocked_packet = create_local_value_redaction_rules_contract(blocked_source)
    assert blocked_packet["local_value_redaction_rule_items"][0]["local_value_redaction_rules_contract_status"] == "BLOCKED_BY_OPERATOR_VALUE_INTAKE_POLICY"

    unknown_source = copy.deepcopy(source_packet)
    unknown_source["operator_value_intake_policy_items"][0]["operator_value_intake_policy_status"] = "READY_UNEXPECTED"
    unknown_packet = create_local_value_redaction_rules_contract(unknown_source)
    assert unknown_packet["local_value_redaction_rule_items"][0]["local_value_redaction_rules_contract_status"] == "BLOCKED_BY_OPERATOR_VALUE_INTAKE_POLICY"


def test_forbidden_actions_and_disallowed_outputs_include_redaction_boundaries(packet):
    assert packet["forbidden_current_actions"] == list(FORBIDDEN_CURRENT_ACTIONS)
    assert "policy_scan_execution" in packet["forbidden_current_actions"]
    assert "redaction_result_persistence" in packet["forbidden_current_actions"]
    assert "redacted_value_generation" in packet["forbidden_current_actions"]
    assert packet["disallowed_outputs"] == list(DISALLOWED_OUTPUTS)
    assert "redaction_result_value" in packet["disallowed_outputs"]


def test_safety_flags_false_except_redaction_rules_schema_only(packet):
    assert packet["safety_flags"] == SAFETY_FLAGS
    for key, value in packet["safety_flags"].items():
        if key == "redaction_rules_schema_only":
            assert value is True
        else:
            assert value is False, key


def test_truth_flags_remain_false(packet):
    assert packet["truth_protection_flags"] == TRUTH_PROTECTION_FLAGS
    assert packet["truth_protection_flags"]["redaction_result_truth_promoted"] is False
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
    bad_packet["global_operator_value_intake_policy_status"] = "READY_UNEXPECTED"
    with pytest.raises(ValueError, match="global_operator_value_intake_policy_status"):
        create_local_value_redaction_rules_contract(bad_packet)


def test_next_recommended_task_is_set(packet):
    assert packet["next_recommended_task"] == NEXT_RECOMMENDED_TASK
    assert packet["allowed_next_step"] == "stage_local_value_redaction_rules_contract_to_local_value_validation_rules_contract"
