"""Tests for Supervised Input Resolution Plan to Local Redaction and Validation Precheck.

Part of TASK_CONTENTOPS_0175BW_SUPERVISED_INPUT_RESOLUTION_PLAN_TO_LOCAL_REDACTION_AND_VALIDATION_PRECHECK_V0.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from live_contentops.supervised_input_resolution_plan_to_local_redaction_and_validation_precheck import (
    REQUIRED_INPUT_FIELDS,
    ALLOWED_FUTURE_VALIDATION_MODES,
    FORBIDDEN_CURRENT_ACTIONS,
    DISALLOWED_OUTPUTS,
    NEXT_RECOMMENDED_TASK,
    create_local_redaction_and_validation_precheck,
    write_artifacts,
)

ROOT = Path(__file__).resolve().parents[1]
SOURCE_PACKET_PATH = ROOT / "docs" / "automation" / "0175BV" / "draft_eligibility_gate_to_supervised_input_resolution_plan_packet.json"
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
    "redacted_operator_value",
}


@pytest.fixture
def source_packet() -> dict:
    with open(SOURCE_PACKET_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def test_valid_0175bv_packet_produces_deterministic_precheck(source_packet):
    first = create_local_redaction_and_validation_precheck(source_packet)
    second = create_local_redaction_and_validation_precheck(source_packet)

    assert first == second
    assert first["packet_hash"] == second["packet_hash"]
    assert first["task_label"] == "TASK_CONTENTOPS_0175BW_SUPERVISED_INPUT_RESOLUTION_PLAN_TO_LOCAL_REDACTION_AND_VALIDATION_PRECHECK_V0"
    assert first["source_packet_task_label"] == "TASK_CONTENTOPS_0175BV_DRAFT_ELIGIBILITY_GATE_TO_SUPERVISED_INPUT_RESOLUTION_PLAN_V0"
    assert first["global_redaction_validation_precheck_status"] == "BLOCKED_LOCAL_REDACTION_VALIDATION_PRECHECK_PENDING_OPERATOR_VALUES"


def test_every_supervised_input_resolution_item_maps_to_one_redaction_validation_precheck_item(source_packet):
    packet = create_local_redaction_and_validation_precheck(source_packet)

    assert packet["source_resolution_item_count"] == len(source_packet["supervised_input_resolution_items"])
    assert len(packet["redaction_validation_precheck_items"]) == len(source_packet["supervised_input_resolution_items"])

    for index, (source_item, item) in enumerate(zip(source_packet["supervised_input_resolution_items"], packet["redaction_validation_precheck_items"]), start=1):
        assert item["precheck_item_id"] == f"precheck_item_{index:02d}_{source_item['source_candidate_id']}"
        assert item["source_resolution_item_id"] == source_item["resolution_item_id"]
        assert item["source_candidate_id"] == source_item["source_candidate_id"]
        assert item["relative_path"] == source_item["relative_path"]
        assert item["evidence_role"] == source_item["evidence_role"]
        assert item["source_family"] == source_item["source_family"]
        assert item["records_count"] == source_item["records_count"]
        assert item["contract_name"] == source_item["contract_name"]
        assert item["intent_scope_label"] == source_item["intent_scope_label"]
        assert item["source_resolution_status"] == source_item["resolution_status"]


def test_required_and_missing_input_fields_match_schema(source_packet):
    packet = create_local_redaction_and_validation_precheck(source_packet)
    expected_fields = list(REQUIRED_INPUT_FIELDS)

    assert packet["required_input_fields"] == expected_fields
    assert packet["missing_required_input_fields"] == expected_fields

    for item in packet["redaction_validation_precheck_items"]:
        assert item["required_input_fields"] == expected_fields
        assert item["missing_required_input_fields"] == expected_fields


def test_field_redaction_policy_properties(source_packet):
    packet = create_local_redaction_and_validation_precheck(source_packet)

    policies = [packet["field_redaction_policy"]]
    policies.extend(item["field_redaction_policy"] for item in packet["redaction_validation_precheck_items"])

    for policy in policies:
        assert set(policy.keys()) == set(REQUIRED_INPUT_FIELDS)
        for field in REQUIRED_INPUT_FIELDS:
            rule = policy[field]
            assert rule["redaction_required"] is True
            assert rule["current_value_present"] is False
            assert rule["current_value"] is None
            assert rule["redaction_status"] == "PENDING_OPERATOR_VALUE"
            assert rule["pii_secret_scan_required"] is True
            assert rule["credential_secret_scan_required"] is True
            assert rule["raw_vendor_redistribution_scan_required"] is True
            assert rule["market_value_scan_required"] is True
            assert rule["prohibited_signal_language_scan_required"] is True
            assert rule["redaction_execution_enabled_in_this_task"] is False
            assert rule["pass_status"] == "BLOCKED_PENDING_OPERATOR_VALUE"


def test_field_validation_policy_properties(source_packet):
    packet = create_local_redaction_and_validation_precheck(source_packet)

    policies = [packet["field_validation_policy"]]
    policies.extend(item["field_validation_policy"] for item in packet["redaction_validation_precheck_items"])

    for policy in policies:
        assert set(policy.keys()) == set(REQUIRED_INPUT_FIELDS)
        for field in REQUIRED_INPUT_FIELDS:
            rule = policy[field]
            assert rule["validation_required"] is True
            assert rule["current_value_present"] is False
            assert rule["current_value"] is None
            assert rule["validation_status"] == "PENDING_OPERATOR_VALUE"
            assert rule["value_non_empty_required"] is True
            assert rule["operator_generated_required"] is True
            assert rule["system_generated_forbidden"] is True
            assert rule["evidence_attachment_required"] is True
            assert rule["source_packet_hash_required"] is True
            assert rule["timestamp_required"] is True
            assert rule["validation_execution_enabled_in_this_task"] is False
            assert rule["pass_status"] == "BLOCKED_PENDING_OPERATOR_VALUE"


def test_evidence_validation_policy_properties(source_packet):
    packet = create_local_redaction_and_validation_precheck(source_packet)

    policies = [packet["evidence_validation_policy"]]
    policies.extend(item["evidence_validation_policy"] for item in packet["redaction_validation_precheck_items"])

    for policy in policies:
        assert policy["operator_identity_or_session_ref_required"] is True
        assert policy["timestamp_required"] is True
        assert policy["source_packet_hash_required"] is True
        assert policy["manual_review_notes_required"] is True
        assert policy["redaction_check_required"] is True
        assert policy["no_secret_values_allowed"] is True
        assert policy["no_raw_vendor_redistribution_allowed"] is True
        assert policy["no_unverified_market_values_allowed"] is True
        assert policy["no_financial_signal_language_allowed"] is True
        assert policy["evidence_validation_enabled_in_this_task"] is False


def test_allowed_future_validation_modes_are_enum_only(source_packet):
    packet = create_local_redaction_and_validation_precheck(source_packet)

    assert packet["allowed_future_validation_modes"] == list(ALLOWED_FUTURE_VALIDATION_MODES)


def test_validation_execution_policy_deactivates_all_execution_and_generation(source_packet):
    packet = create_local_redaction_and_validation_precheck(source_packet)

    policies = [packet["validation_execution_policy"]]
    policies.extend(item["validation_execution_policy"] for item in packet["redaction_validation_precheck_items"])

    for policy in policies:
        assert policy["redaction_execution_enabled"] is False
        assert policy["field_validation_enabled"] is False
        assert policy["evidence_validation_enabled"] is False
        assert policy["operator_value_persistence_enabled"] is False
        assert policy["draft_eligibility_recheck_enabled"] is False
        assert policy["draft_generation_enabled"] is False
        assert policy["ai_writer_generation_enabled"] is False
        assert policy["public_postable"] is False
        assert policy["dispatch_ready"] is False


def test_draft_generation_policy_object_deactivates_all_generation_and_storage(source_packet):
    packet = create_local_redaction_and_validation_precheck(source_packet)
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
    # Pending resolution status mapping
    packet = create_local_redaction_and_validation_precheck(source_packet)
    assert packet["redaction_validation_precheck_items"][0]["redaction_validation_precheck_status"] == "BLOCKED_LOCAL_REDACTION_VALIDATION_PRECHECK_PENDING_OPERATOR_VALUES"

    # Blocked item mapping and unknown mapping
    sample = {
        "task_label": "TASK_CONTENTOPS_0175BV_DRAFT_ELIGIBILITY_GATE_TO_SUPERVISED_INPUT_RESOLUTION_PLAN_V0",
        "global_resolution_plan_status": "BLOCKED_SUPERVISED_INPUT_RESOLUTION_REQUIRED",
        "supervised_input_resolution_items": [
            {
                "resolution_item_id": "res_1",
                "source_candidate_id": "candidate_1",
                "resolution_status": "BLOCKED_BY_DRAFT_ELIGIBILITY_GATE_PRECHECK",
            },
            {
                "resolution_item_id": "res_2",
                "source_candidate_id": "candidate_2",
                "resolution_status": "SOME_UNKNOWN_STATUS",
            }
        ]
    }
    repaired = create_local_redaction_and_validation_precheck(sample)
    assert repaired["redaction_validation_precheck_items"][0]["redaction_validation_precheck_status"] == "BLOCKED_BY_SUPERVISED_INPUT_RESOLUTION_PLAN"
    assert repaired["redaction_validation_precheck_items"][1]["redaction_validation_precheck_status"] == "BLOCKED_BY_SUPERVISED_INPUT_RESOLUTION_PLAN"


def test_forbidden_current_actions_include_redaction_and_recheck(source_packet):
    packet = create_local_redaction_and_validation_precheck(source_packet)
    required_actions = {
        "actual_input_capture",
        "editable_input_fields",
        "form_submission",
        "save_capture_approve_generate_controls",
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
        "validation_execution",
        "redaction_execution",
        "persistence_write",
        "draft_eligibility_recheck",
    }

    assert set(packet["forbidden_current_actions"]) == set(FORBIDDEN_CURRENT_ACTIONS)
    assert required_actions <= set(packet["forbidden_current_actions"])
    for item in packet["redaction_validation_precheck_items"]:
        assert required_actions <= set(item["forbidden_current_actions"])


def test_disallowed_outputs_include_redacted_value(source_packet):
    packet = create_local_redaction_and_validation_precheck(source_packet)
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
        "redacted_operator_value",
    }

    assert set(packet["disallowed_outputs"]) == set(DISALLOWED_OUTPUTS)
    assert required_disallowed <= set(packet["disallowed_outputs"])
    for item in packet["redaction_validation_precheck_items"]:
        assert required_disallowed <= set(item["disallowed_outputs"])


def test_no_operator_prose_or_public_ready_content_fields_are_emitted(source_packet):
    packet = create_local_redaction_and_validation_precheck(source_packet)

    assert FORBIDDEN_OUTPUT_KEYS.isdisjoint(packet.keys())
    for item in packet["redaction_validation_precheck_items"]:
        assert FORBIDDEN_OUTPUT_KEYS.isdisjoint(item.keys())


def test_truth_and_safety_flags_remain_false(source_packet):
    packet = create_local_redaction_and_validation_precheck(source_packet)

    assert packet["truth_protection_flags"]
    assert packet["safety_flags"]
    assert all(value is False for value in packet["truth_protection_flags"].values())
    assert all(value is False for value in packet["safety_flags"].values())
    assert packet["truth_protection_flags"]["redacted_value_truth_promoted"] is False
    assert packet["safety_flags"]["redaction_execution_enabled"] is False
    assert packet["safety_flags"]["draft_eligibility_recheck_enabled"] is False


def test_next_recommended_task_is_set_correctly(source_packet):
    packet = create_local_redaction_and_validation_precheck(source_packet)

    assert packet["next_recommended_task"] == NEXT_RECOMMENDED_TASK
    assert packet["allowed_next_step"] == "stage_local_redaction_validation_precheck_to_operator_input_capture_gate"


def test_write_artifacts_outputs_json_and_runbook(tmp_path, source_packet):
    source_path = tmp_path / "source_packet.json"
    source_path.write_text(json.dumps(source_packet, sort_keys=True), encoding="utf-8")

    result = write_artifacts(source_path, repo_root=tmp_path)

    packet_path = Path(result["packet_path"])
    runbook_path = Path(result["runbook_path"])
    assert packet_path.exists()
    assert runbook_path.exists()

    loaded = json.loads(packet_path.read_text(encoding="utf-8"))
    assert loaded["global_redaction_validation_precheck_status"] == "BLOCKED_LOCAL_REDACTION_VALIDATION_PRECHECK_PENDING_OPERATOR_VALUES"
    assert loaded["next_recommended_task"] == NEXT_RECOMMENDED_TASK
    assert "Local Redaction and Validation Precheck" in runbook_path.read_text(encoding="utf-8")


def test_invalid_global_status_fails_closed(source_packet):
    source_packet["global_resolution_plan_status"] = "RESOLVED"

    with pytest.raises(ValueError) as exc:
        create_local_redaction_and_validation_precheck(source_packet)

    assert "Invalid global resolution plan status" in str(exc.value)
