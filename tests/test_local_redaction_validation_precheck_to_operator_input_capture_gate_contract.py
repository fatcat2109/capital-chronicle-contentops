"""Tests for Local Redaction Validation Precheck to Operator Input Capture Gate Contract.

Part of TASK_CONTENTOPS_0175BX_LOCAL_REDACTION_VALIDATION_PRECHECK_TO_OPERATOR_INPUT_CAPTURE_GATE_CONTRACT_V0.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from live_contentops.local_redaction_validation_precheck_to_operator_input_capture_gate_contract import (
    REQUIRED_INPUT_FIELDS,
    ALLOWED_FUTURE_CAPTURE_MODES,
    FORBIDDEN_CURRENT_ACTIONS,
    DISALLOWED_OUTPUTS,
    NEXT_RECOMMENDED_TASK,
    create_operator_input_capture_gate_contract,
    write_artifacts,
)

ROOT = Path(__file__).resolve().parents[1]
SOURCE_PACKET_PATH = ROOT / "docs" / "automation" / "0175BW" / "supervised_input_resolution_plan_to_local_redaction_and_validation_precheck_packet.json"
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
}


@pytest.fixture
def source_packet() -> dict:
    with open(SOURCE_PACKET_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def test_valid_0175bw_packet_produces_deterministic_capture_gate_contract(source_packet):
    first = create_operator_input_capture_gate_contract(source_packet)
    second = create_operator_input_capture_gate_contract(source_packet)

    assert first == second
    assert first["packet_hash"] == second["packet_hash"]
    assert first["task_label"] == "TASK_CONTENTOPS_0175BX_LOCAL_REDACTION_VALIDATION_PRECHECK_TO_OPERATOR_INPUT_CAPTURE_GATE_CONTRACT_V0"
    assert first["source_packet_task_label"] == "TASK_CONTENTOPS_0175BW_SUPERVISED_INPUT_RESOLUTION_PLAN_TO_LOCAL_REDACTION_AND_VALIDATION_PRECHECK_V0"
    assert first["global_operator_input_capture_gate_status"] == "BLOCKED_OPERATOR_INPUT_CAPTURE_GATE_PENDING_SUPERVISED_ACTIVATION"


def test_every_redaction_validation_precheck_item_maps_to_one_operator_input_capture_gate_item(source_packet):
    packet = create_operator_input_capture_gate_contract(source_packet)

    assert packet["source_redaction_validation_precheck_item_count"] == len(source_packet["redaction_validation_precheck_items"])
    assert len(packet["operator_input_capture_gate_items"]) == len(source_packet["redaction_validation_precheck_items"])

    for index, (source_item, item) in enumerate(zip(source_packet["redaction_validation_precheck_items"], packet["operator_input_capture_gate_items"]), start=1):
        assert item["capture_gate_item_id"] == f"capture_gate_item_{index:02d}_{source_item['source_candidate_id']}"
        assert item["source_precheck_item_id"] == source_item["precheck_item_id"]
        assert item["source_candidate_id"] == source_item["source_candidate_id"]
        assert item["relative_path"] == source_item["relative_path"]
        assert item["evidence_role"] == source_item["evidence_role"]
        assert item["source_family"] == source_item["source_family"]
        assert item["records_count"] == source_item["records_count"]
        assert item["contract_name"] == source_item["contract_name"]
        assert item["intent_scope_label"] == source_item["intent_scope_label"]
        assert item["source_redaction_validation_precheck_status"] == source_item["redaction_validation_precheck_status"]


def test_required_and_missing_input_fields_match_schema(source_packet):
    packet = create_operator_input_capture_gate_contract(source_packet)
    expected_fields = list(REQUIRED_INPUT_FIELDS)

    assert packet["required_input_fields"] == expected_fields
    assert packet["missing_required_input_fields"] == expected_fields

    for item in packet["operator_input_capture_gate_items"]:
        assert item["required_input_fields"] == expected_fields
        assert item["missing_required_input_fields"] == expected_fields


def test_capture_field_contract_properties(source_packet):
    packet = create_operator_input_capture_gate_contract(source_packet)

    policies = [packet["capture_field_contract"]]
    policies.extend(item["capture_field_contract"] for item in packet["operator_input_capture_gate_items"])

    for policy in policies:
        assert set(policy.keys()) == set(REQUIRED_INPUT_FIELDS)
        for field in REQUIRED_INPUT_FIELDS:
            rule = policy[field]
            assert rule["capture_allowed_in_future"] is True
            assert rule["capture_enabled_in_this_task"] is False
            assert rule["current_value"] is None
            assert rule["current_value_present"] is False
            assert rule["placeholder_value"] == "PENDING_OPERATOR_INPUT"
            assert rule["operator_generated_required"] is True
            assert rule["system_generated_forbidden"] is True
            assert rule["evidence_attachment_required"] is True
            assert rule["redaction_precheck_required"] is True
            assert rule["validation_precheck_required"] is True
            assert rule["persistence_enabled_in_this_task"] is False
            assert rule["capture_status"] == "BLOCKED_PENDING_SUPERVISED_ACTIVATION"
            assert rule["blocking_reason"] == "operator_input_capture_gate_not_enabled_in_this_task"


def test_capture_evidence_contract_properties(source_packet):
    packet = create_operator_input_capture_gate_contract(source_packet)

    policies = [packet["capture_evidence_contract"]]
    policies.extend(item["capture_evidence_contract"] for item in packet["operator_input_capture_gate_items"])

    for policy in policies:
        assert policy["operator_identity_or_session_ref_required"] is True
        assert policy["timestamp_required"] is True
        assert policy["source_packet_hash_required"] is True
        assert policy["manual_review_notes_required"] is True
        assert policy["redaction_check_required"] is True
        assert policy["validation_check_required"] is True
        assert policy["no_secret_values_allowed"] is True
        assert policy["no_raw_vendor_redistribution_allowed"] is True
        assert policy["no_unverified_market_values_allowed"] is True
        assert policy["no_financial_signal_language_allowed"] is True
        assert policy["evidence_capture_enabled_in_this_task"] is False


def test_pre_capture_validation_contract_properties(source_packet):
    packet = create_operator_input_capture_gate_contract(source_packet)

    policies = [packet["pre_capture_validation_contract"]]
    policies.extend(item["pre_capture_validation_contract"] for item in packet["operator_input_capture_gate_items"])

    for policy in policies:
        assert policy["field_non_empty_validation_required"] is True
        assert policy["operator_generated_validation_required"] is True
        assert policy["system_generated_rejection_required"] is True
        assert policy["evidence_attachment_validation_required"] is True
        assert policy["redaction_scan_required_before_acceptance"] is True
        assert policy["validation_execution_enabled_in_this_task"] is False
        assert policy["redaction_execution_enabled_in_this_task"] is False
        assert policy["pass_status"] == "BLOCKED_PENDING_OPERATOR_CAPTURE"


def test_redaction_validation_dependency_contract_properties(source_packet):
    packet = create_operator_input_capture_gate_contract(source_packet)

    policies = [packet["redaction_validation_dependency_contract"]]
    policies.extend(item["redaction_validation_dependency_contract"] for item in packet["operator_input_capture_gate_items"])

    for policy in policies:
        assert policy["depends_on_local_redaction_validation_precheck"] is True
        assert policy["source_global_status_required"] == "BLOCKED_LOCAL_REDACTION_VALIDATION_PRECHECK_PENDING_OPERATOR_VALUES"
        assert policy["source_operator_values_required_before_execution"] is True
        assert policy["can_execute_without_operator_values"] is False
        assert policy["dependency_satisfied_in_this_task"] is False


def test_allowed_future_capture_modes_are_enum_only(source_packet):
    packet = create_operator_input_capture_gate_contract(source_packet)

    assert packet["allowed_future_capture_modes"] == list(ALLOWED_FUTURE_CAPTURE_MODES)


def test_capture_execution_policy_deactivates_all_capture_and_generation(source_packet):
    packet = create_operator_input_capture_gate_contract(source_packet)

    policies = [packet["capture_execution_policy"]]
    policies.extend(item["capture_execution_policy"] for item in packet["operator_input_capture_gate_items"])

    for policy in policies:
        assert policy["input_capture_enabled"] is False
        assert policy["editable_ui_enabled"] is False
        assert policy["form_submission_enabled"] is False
        assert policy["operator_value_persistence_enabled"] is False
        assert policy["evidence_capture_enabled"] is False
        assert policy["validation_execution_enabled"] is False
        assert policy["redaction_execution_enabled"] is False
        assert policy["draft_eligibility_recheck_enabled"] is False
        assert policy["draft_generation_enabled"] is False
        assert policy["ai_writer_generation_enabled"] is False
        assert policy["public_postable"] is False
        assert policy["dispatch_ready"] is False


def test_draft_generation_policy_object_deactivates_all_generation_and_storage(source_packet):
    packet = create_operator_input_capture_gate_contract(source_packet)
    policy = packet["draft_generation_policy"]

    assert policy["draft_generation_enabled"] is False
    assert policy["headline_generation_enabled"] is False
    assert policy["hook_generation_enabled"] is False
    assert policy["caption_generation_enabled"] is False
    assert policy["platform_copy_generation_enabled"] is False
    assert policy["ai_writer_generation_enabled"] is False
    assert policy["public_postable"] is False
    assert policy["dispatch_ready"] is False
    assert policy["draft_storage_enabled"] is False
    assert policy["operator_input_capture_enabled"] is False
    assert policy["validation_enabled"] is False
    assert policy["supervised_input_resolution_enabled"] is False


def test_item_status_mappings_and_fail_closed(source_packet):
    # Pending source precheck status mapping
    packet = create_operator_input_capture_gate_contract(source_packet)
    assert packet["operator_input_capture_gate_items"][0]["operator_input_capture_gate_status"] == "BLOCKED_OPERATOR_INPUT_CAPTURE_GATE_PENDING_SUPERVISED_ACTIVATION"

    # Blocked item mapping and unknown mapping
    sample = {
        "task_label": "TASK_CONTENTOPS_0175BW_SUPERVISED_INPUT_RESOLUTION_PLAN_TO_LOCAL_REDACTION_AND_VALIDATION_PRECHECK_V0",
        "global_redaction_validation_precheck_status": "BLOCKED_LOCAL_REDACTION_VALIDATION_PRECHECK_PENDING_OPERATOR_VALUES",
        "redaction_validation_precheck_items": [
            {
                "precheck_item_id": "precheck_1",
                "source_candidate_id": "candidate_1",
                "redaction_validation_precheck_status": "BLOCKED_BY_SUPERVISED_INPUT_RESOLUTION_PLAN",
            },
            {
                "precheck_item_id": "precheck_2",
                "source_candidate_id": "candidate_2",
                "redaction_validation_precheck_status": "SOME_UNKNOWN_STATUS",
            }
        ]
    }
    repaired = create_operator_input_capture_gate_contract(sample)
    assert repaired["operator_input_capture_gate_items"][0]["operator_input_capture_gate_status"] == "BLOCKED_BY_LOCAL_REDACTION_VALIDATION_PRECHECK"
    assert repaired["operator_input_capture_gate_items"][1]["operator_input_capture_gate_status"] == "BLOCKED_BY_LOCAL_REDACTION_VALIDATION_PRECHECK"


def test_forbidden_current_actions_include_capture_persistence_and_recheck(source_packet):
    packet = create_operator_input_capture_gate_contract(source_packet)
    required_actions = {
        "actual_input_capture",
        "editable_input_fields",
        "form_submission",
        "save_capture_approve_generate_controls",
        "operator_value_persistence",
        "evidence_capture",
        "validation_execution",
        "redaction_execution",
        "operator_prose_generation",
        "content_generation",
        "draft_generation",
        "headline_hook_caption_generation",
        "platform_copy_generation",
        "ai_writer_generation",
        "draft_storage",
        "public_posting",
        "live_dispatch",
        "provider_or_platform_api_call",
        "draft_eligibility_recheck",
    }

    assert set(packet["forbidden_current_actions"]) == set(FORBIDDEN_CURRENT_ACTIONS)
    assert required_actions <= set(packet["forbidden_current_actions"])
    for item in packet["operator_input_capture_gate_items"]:
        assert required_actions <= set(item["forbidden_current_actions"])


def test_disallowed_outputs_include_captured_value_and_redacted_value(source_packet):
    packet = create_operator_input_capture_gate_contract(source_packet)
    required_disallowed = {
        "raw_record_contents",
        "source_extracted_facts",
        "market_values",
        "narrative_thesis",
        "headline",
        "hook",
        "caption",
        "draft_paragraph",
        "platform_copy",
        "prediction",
        "recommendation",
        "buy_sell_hold_sizing_signal_language",
        "operator_input_value",
        "operator_review_notes_text",
        "captured_operator_value",
        "redacted_operator_value",
    }

    assert set(packet["disallowed_outputs"]) == set(DISALLOWED_OUTPUTS)
    assert required_disallowed <= set(packet["disallowed_outputs"])
    for item in packet["operator_input_capture_gate_items"]:
        assert required_disallowed <= set(item["disallowed_outputs"])


def test_no_operator_prose_or_public_ready_content_fields_are_emitted(source_packet):
    packet = create_operator_input_capture_gate_contract(source_packet)

    assert FORBIDDEN_OUTPUT_KEYS.isdisjoint(packet.keys())
    for item in packet["operator_input_capture_gate_items"]:
        assert FORBIDDEN_OUTPUT_KEYS.isdisjoint(item.keys())


def test_truth_and_safety_flags_remain_false(source_packet):
    packet = create_operator_input_capture_gate_contract(source_packet)

    assert packet["truth_protection_flags"]
    assert packet["safety_flags"]
    assert all(value is False for value in packet["truth_protection_flags"].values())
    assert all(value is False for value in packet["safety_flags"].values())
    assert packet["truth_protection_flags"]["captured_value_truth_promoted"] is False
    assert packet["safety_flags"]["operator_input_capture_gate_enabled"] is False
    assert packet["safety_flags"]["evidence_capture_enabled"] is False


def test_next_recommended_task_is_set_correctly(source_packet):
    packet = create_operator_input_capture_gate_contract(source_packet)

    assert packet["next_recommended_task"] == NEXT_RECOMMENDED_TASK
    assert packet["allowed_next_step"] == "stage_operator_input_capture_gate_to_supervised_manual_input_dry_run_precheck"


def test_write_artifacts_outputs_json_and_runbook(tmp_path, source_packet):
    source_path = tmp_path / "source_packet.json"
    source_path.write_text(json.dumps(source_packet, sort_keys=True), encoding="utf-8")

    result = write_artifacts(source_path, repo_root=tmp_path)

    packet_path = Path(result["packet_path"])
    runbook_path = Path(result["runbook_path"])
    assert packet_path.exists()
    assert runbook_path.exists()

    loaded = json.loads(packet_path.read_text(encoding="utf-8"))
    assert loaded["global_operator_input_capture_gate_status"] == "BLOCKED_OPERATOR_INPUT_CAPTURE_GATE_PENDING_SUPERVISED_ACTIVATION"
    assert loaded["next_recommended_task"] == NEXT_RECOMMENDED_TASK
    assert "Operator Input Capture Gate Contract" in runbook_path.read_text(encoding="utf-8")


def test_invalid_global_status_fails_closed(source_packet):
    source_packet["global_redaction_validation_precheck_status"] = "PASSED"

    with pytest.raises(ValueError) as exc:
        create_operator_input_capture_gate_contract(source_packet)

    assert "Invalid global precheck status" in str(exc.value)
