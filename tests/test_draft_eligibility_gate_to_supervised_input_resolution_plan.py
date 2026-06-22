"""Tests for Draft Eligibility Gate to Supervised Input Resolution Plan.

Part of TASK_CONTENTOPS_0175BV_DRAFT_ELIGIBILITY_GATE_TO_SUPERVISED_INPUT_RESOLUTION_PLAN_V0.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from live_contentops.draft_eligibility_gate_to_supervised_input_resolution_plan import (
    REQUIRED_INPUT_FIELDS,
    ALLOWED_FUTURE_RESOLUTION_METHODS,
    VALIDATION_REQUIREMENTS,
    EVIDENCE_REQUIREMENTS,
    FORBIDDEN_CURRENT_ACTIONS,
    DISALLOWED_OUTPUTS,
    NEXT_RECOMMENDED_TASK,
    create_supervised_input_resolution_plan,
    write_artifacts,
)

ROOT = Path(__file__).resolve().parents[1]
SOURCE_PACKET_PATH = ROOT / "docs" / "automation" / "0175BS" / "supervised_input_stub_to_draft_eligibility_gate_precheck_packet.json"
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
}


@pytest.fixture
def source_packet() -> dict:
    with open(SOURCE_PACKET_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def test_valid_0175bs_packet_produces_deterministic_resolution_plan(source_packet):
    first = create_supervised_input_resolution_plan(source_packet)
    second = create_supervised_input_resolution_plan(source_packet)

    assert first == second
    assert first["packet_hash"] == second["packet_hash"]
    assert first["task_label"] == "TASK_CONTENTOPS_0175BV_DRAFT_ELIGIBILITY_GATE_TO_SUPERVISED_INPUT_RESOLUTION_PLAN_V0"
    assert first["source_packet_task_label"] == "TASK_CONTENTOPS_0175BS_SUPERVISED_INPUT_STUB_TO_DRAFT_ELIGIBILITY_GATE_PRECHECK_V0"
    assert first["global_resolution_plan_status"] == "BLOCKED_SUPERVISED_INPUT_RESOLUTION_REQUIRED"


def test_every_draft_eligibility_item_maps_to_one_supervised_input_resolution_item(source_packet):
    packet = create_supervised_input_resolution_plan(source_packet)

    assert packet["source_draft_eligibility_item_count"] == len(source_packet["draft_eligibility_items"])
    assert len(packet["supervised_input_resolution_items"]) == len(source_packet["draft_eligibility_items"])

    for index, (source_item, item) in enumerate(zip(source_packet["draft_eligibility_items"], packet["supervised_input_resolution_items"]), start=1):
        assert item["resolution_item_id"] == f"resolution_item_{index:02d}_{source_item['source_candidate_id']}"
        assert item["source_draft_eligibility_item_id"] == source_item["draft_eligibility_item_id"]
        assert item["source_candidate_id"] == source_item["source_candidate_id"]
        assert item["relative_path"] == source_item["relative_path"]
        assert item["evidence_role"] == source_item["evidence_role"]
        assert item["source_family"] == source_item["source_family"]
        assert item["records_count"] == source_item["records_count"]
        assert item["contract_name"] == source_item["contract_name"]
        assert item["intent_scope_label"] == source_item["intent_scope_label"]
        assert item["source_draft_eligibility_status"] == source_item["draft_eligibility_status"]


def test_required_and_missing_input_fields_match_schema(source_packet):
    packet = create_supervised_input_resolution_plan(source_packet)
    expected_fields = list(REQUIRED_INPUT_FIELDS)

    assert packet["required_input_fields"] == expected_fields
    assert packet["missing_required_input_fields"] == expected_fields

    for item in packet["supervised_input_resolution_items"]:
        assert item["required_input_fields"] == expected_fields
        assert item["missing_required_input_fields"] == expected_fields


def test_field_resolution_plan_properties(source_packet):
    packet = create_supervised_input_resolution_plan(source_packet)

    policies = [packet["field_resolution_plan"]]
    policies.extend(item["field_resolution_plan"] for item in packet["supervised_input_resolution_items"])

    for policy in policies:
        assert set(policy.keys()) == set(REQUIRED_INPUT_FIELDS)
        for field in REQUIRED_INPUT_FIELDS:
            rule = policy[field]
            assert rule["required"] is True
            assert rule["current_value"] is None
            assert rule["placeholder_value"] == "PENDING_OPERATOR_INPUT"
            assert rule["resolution_status"] == "PENDING_SUPERVISED_OPERATOR_RESOLUTION"
            assert rule["resolution_enabled_in_this_task"] is False
            assert rule["editable_in_this_task"] is False
            assert rule["generated_by_system"] is False
            assert rule["persistence_enabled"] is False
            assert rule["validation_enabled"] is False
            assert rule["future_resolution_required"] is True
            assert rule["allowed_future_resolution_methods"] == list(ALLOWED_FUTURE_RESOLUTION_METHODS)
            assert rule["evidence_required"] is True
            assert rule["evidence_requirement_label"] == "OPERATOR_PROVIDED_REVIEW_EVIDENCE_REQUIRED"
            assert rule["blocking_reason"] == "supervised_input_resolution_required_before_draft_eligibility"


def test_draft_generation_policy_object_deactivates_all_generation_and_storage(source_packet):
    packet = create_supervised_input_resolution_plan(source_packet)
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
    # Pending draft eligibility status mapping
    packet = create_supervised_input_resolution_plan(source_packet)
    assert packet["supervised_input_resolution_items"][0]["resolution_status"] == "BLOCKED_SUPERVISED_INPUT_RESOLUTION_REQUIRED"

    # Blocked item mapping and unknown mapping
    sample = {
        "task_label": "TASK_CONTENTOPS_0175BS_SUPERVISED_INPUT_STUB_TO_DRAFT_ELIGIBILITY_GATE_PRECHECK_V0",
        "global_draft_eligibility_status": "BLOCKED_DRAFT_ELIGIBILITY_SUPERVISED_INPUT_REQUIRED",
        "draft_eligibility_items": [
            {
                "draft_eligibility_item_id": "item_1",
                "source_candidate_id": "candidate_1",
                "draft_eligibility_status": "BLOCKED_BY_SUPERVISED_INPUT_STUB_CONTRACT",
            },
            {
                "draft_eligibility_item_id": "item_2",
                "source_candidate_id": "candidate_2",
                "draft_eligibility_status": "SOME_UNKNOWN_STATUS",
            }
        ]
    }
    repaired = create_supervised_input_resolution_plan(sample)
    assert repaired["supervised_input_resolution_items"][0]["resolution_status"] == "BLOCKED_BY_DRAFT_ELIGIBILITY_GATE_PRECHECK"
    assert repaired["supervised_input_resolution_items"][1]["resolution_status"] == "BLOCKED_BY_DRAFT_ELIGIBILITY_GATE_PRECHECK"


def test_validation_requirements_present_and_enabled_false(source_packet):
    packet = create_supervised_input_resolution_plan(source_packet)
    expected_reqs = list(VALIDATION_REQUIREMENTS)

    assert packet["validation_requirements"] == expected_reqs
    assert packet["draft_generation_policy"]["validation_enabled"] is False
    assert packet["safety_flags"]["validation_enabled"] is False

    for item in packet["supervised_input_resolution_items"]:
        assert item["validation_requirements"] == expected_reqs
        assert item["field_resolution_plan"]["intended_audience_lane"]["validation_enabled"] is False


def test_evidence_requirements_satisfied(source_packet):
    packet = create_supervised_input_resolution_plan(source_packet)
    expected_evidence = dict(EVIDENCE_REQUIREMENTS)

    assert packet["evidence_requirements"] == expected_evidence
    assert packet["evidence_requirements"]["no_secret_values_allowed"] is True
    assert packet["evidence_requirements"]["no_raw_vendor_redistribution_allowed"] is True

    for item in packet["supervised_input_resolution_items"]:
        assert item["evidence_requirements"] == expected_evidence


def test_forbidden_current_actions_include_validation_and_persistence(source_packet):
    packet = create_supervised_input_resolution_plan(source_packet)
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
        "persistence_write",
    }

    assert set(packet["forbidden_current_actions"]) == set(FORBIDDEN_CURRENT_ACTIONS)
    assert required_actions <= set(packet["forbidden_current_actions"])
    for item in packet["supervised_input_resolution_items"]:
        assert required_actions <= set(item["forbidden_current_actions"])


def test_disallowed_outputs_include_operator_values(source_packet):
    packet = create_supervised_input_resolution_plan(source_packet)
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
    }

    assert set(packet["disallowed_outputs"]) == set(DISALLOWED_OUTPUTS)
    assert required_disallowed <= set(packet["disallowed_outputs"])
    for item in packet["supervised_input_resolution_items"]:
        assert required_disallowed <= set(item["disallowed_outputs"])


def test_no_operator_prose_or_public_ready_content_fields_are_emitted(source_packet):
    packet = create_supervised_input_resolution_plan(source_packet)

    assert FORBIDDEN_OUTPUT_KEYS.isdisjoint(packet.keys())
    for item in packet["supervised_input_resolution_items"]:
        assert FORBIDDEN_OUTPUT_KEYS.isdisjoint(item.keys())


def test_truth_and_safety_flags_remain_false(source_packet):
    packet = create_supervised_input_resolution_plan(source_packet)

    assert packet["truth_protection_flags"]
    assert packet["safety_flags"]
    assert all(value is False for value in packet["truth_protection_flags"].values())
    assert all(value is False for value in packet["safety_flags"].values())
    assert packet["truth_protection_flags"]["operator_input_truth_promoted"] is False
    assert packet["safety_flags"]["supervised_input_resolution_enabled"] is False


def test_next_recommended_task_is_set_correctly(source_packet):
    packet = create_supervised_input_resolution_plan(source_packet)

    assert packet["next_recommended_task"] == NEXT_RECOMMENDED_TASK
    assert packet["allowed_next_step"] == "stage_supervised_input_resolution_redaction_and_validation"


def test_write_artifacts_outputs_json_and_runbook(tmp_path, source_packet):
    source_path = tmp_path / "source_packet.json"
    source_path.write_text(json.dumps(source_packet, sort_keys=True), encoding="utf-8")

    result = write_artifacts(source_path, repo_root=tmp_path)

    packet_path = Path(result["packet_path"])
    runbook_path = Path(result["runbook_path"])
    assert packet_path.exists()
    assert runbook_path.exists()

    loaded = json.loads(packet_path.read_text(encoding="utf-8"))
    assert loaded["global_resolution_plan_status"] == "BLOCKED_SUPERVISED_INPUT_RESOLUTION_REQUIRED"
    assert loaded["next_recommended_task"] == NEXT_RECOMMENDED_TASK
    assert "Draft Eligibility Gate to Supervised Input Resolution Plan" in runbook_path.read_text(encoding="utf-8")


def test_invalid_global_status_fails_closed(source_packet):
    source_packet["global_draft_eligibility_status"] = "PASSED"

    with pytest.raises(ValueError) as exc:
        create_supervised_input_resolution_plan(source_packet)

    assert "Invalid global draft eligibility status" in str(exc.value)
