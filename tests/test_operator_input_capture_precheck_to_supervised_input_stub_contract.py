"""Tests for Operator Input Capture Precheck to Supervised Input Stub Contract.

Part of TASK_CONTENTOPS_0175BP_OPERATOR_INPUT_CAPTURE_PRECHECK_TO_SUPERVISED_INPUT_STUB_CONTRACT_V0.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from live_contentops.operator_input_capture_precheck_to_supervised_input_stub_contract import (
    ALLOWED_FUTURE_CAPTURE_MODES,
    FORBIDDEN_CURRENT_ACTIONS,
    NEXT_RECOMMENDED_TASK,
    REQUIRED_INPUT_FIELDS,
    create_supervised_input_stub_contract,
    write_artifacts,
)

ROOT = Path(__file__).resolve().parents[1]
SOURCE_PACKET_PATH = ROOT / "docs" / "automation" / "0175BN" / "review_only_intent_to_operator_input_capture_precheck_packet.json"
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
}


@pytest.fixture
def source_packet() -> dict:
    with open(SOURCE_PACKET_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def test_valid_0175bn_packet_produces_deterministic_supervised_stub_contract(source_packet):
    first = create_supervised_input_stub_contract(source_packet)
    second = create_supervised_input_stub_contract(source_packet)

    assert first == second
    assert first["packet_hash"] == second["packet_hash"]
    assert first["task_label"] == "TASK_CONTENTOPS_0175BP_OPERATOR_INPUT_CAPTURE_PRECHECK_TO_SUPERVISED_INPUT_STUB_CONTRACT_V0"
    assert first["source_packet_task_label"] == "TASK_CONTENTOPS_0175BN_REVIEW_ONLY_INTENT_TO_OPERATOR_INPUT_CAPTURE_PRECHECK_V0"
    assert first["global_supervised_input_stub_status"] == "BLOCKED_SUPERVISED_INPUT_CAPTURE_NOT_ENABLED"


def test_every_precheck_item_maps_to_one_supervised_stub_item(source_packet):
    packet = create_supervised_input_stub_contract(source_packet)

    assert packet["source_input_capture_precheck_item_count"] == len(source_packet["input_capture_precheck_items"])
    assert len(packet["supervised_input_stub_items"]) == len(source_packet["input_capture_precheck_items"])

    for source_item, stub_item in zip(source_packet["input_capture_precheck_items"], packet["supervised_input_stub_items"]):
        assert stub_item["source_intent_item_id"] == source_item["intent_item_id"]
        assert stub_item["source_candidate_id"] == source_item["source_candidate_id"]
        assert stub_item["relative_path"] == source_item["relative_path"]
        assert stub_item["evidence_role"] == source_item["evidence_role"]
        assert stub_item["source_family"] == source_item["source_family"]
        assert stub_item["records_count"] == source_item["records_count"]
        assert stub_item["contract_name"] == source_item["contract_name"]
        assert stub_item["intent_scope_label"] == source_item["intent_scope_label"]
        assert stub_item["source_precheck_status"] == source_item["operator_input_capture_precheck_status"]


def test_every_required_field_exists_in_global_and_item_level_policy(source_packet):
    packet = create_supervised_input_stub_contract(source_packet)
    required = set(REQUIRED_INPUT_FIELDS)

    assert set(packet["required_input_fields"]) == required
    assert set(packet["input_stub_field_policy"].keys()) == required

    for item in packet["supervised_input_stub_items"]:
        assert set(item["required_input_fields"]) == required
        assert set(item["input_stub_field_policy"].keys()) == required


def test_stub_field_policy_is_schema_only_pending_and_disabled(source_packet):
    packet = create_supervised_input_stub_contract(source_packet)
    policies = [packet["input_stub_field_policy"]]
    policies.extend(item["input_stub_field_policy"] for item in packet["supervised_input_stub_items"])

    for policy in policies:
        for field in REQUIRED_INPUT_FIELDS:
            rule = policy[field]
            assert rule["required"] is True
            assert rule["slot_status"] == "STUB_SLOT_PENDING_SUPERVISED_INPUT"
            assert rule["value_status"] == "PENDING_OPERATOR_INPUT"
            assert rule["current_value"] is None
            assert rule["placeholder_value"] == "PENDING_OPERATOR_INPUT"
            assert rule["capture_enabled_in_this_task"] is False
            assert rule["editable_in_this_task"] is False
            assert rule["generated_by_system"] is False
            assert rule["operator_must_provide_later"] is True
            assert rule["future_supervised_capture_required"] is True
            assert rule["persistence_enabled"] is False
            assert rule["validation_enabled"] is False


def test_future_capture_modes_are_enum_only_and_not_enabled(source_packet):
    packet = create_supervised_input_stub_contract(source_packet)

    assert packet["allowed_future_capture_modes"] == list(ALLOWED_FUTURE_CAPTURE_MODES)
    assert packet["future_capture_modes_enabled_in_this_task"] is False
    assert set(packet["allowed_future_capture_modes"]) == {
        "manual_supervised_operator_entry",
        "imported_operator_review_packet",
        "deferred_human_review_session",
    }


def test_forbidden_current_actions_include_capture_edit_save_generate_content_live_api(source_packet):
    packet = create_supervised_input_stub_contract(source_packet)
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
        "live_dispatch",
        "provider_or_platform_api_call",
    }

    assert set(packet["forbidden_current_actions"]) == set(FORBIDDEN_CURRENT_ACTIONS)
    assert required_actions <= set(packet["forbidden_current_actions"])
    for item in packet["supervised_input_stub_items"]:
        assert required_actions <= set(item["forbidden_current_actions"])


def test_no_operator_prose_or_public_ready_content_fields_are_emitted(source_packet):
    packet = create_supervised_input_stub_contract(source_packet)

    assert FORBIDDEN_OUTPUT_KEYS.isdisjoint(packet.keys())
    for item in packet["supervised_input_stub_items"]:
        assert FORBIDDEN_OUTPUT_KEYS.isdisjoint(item.keys())


def test_blocked_source_items_remain_blocked():
    sample = {
        "task_label": "TASK_CONTENTOPS_0175BN_REVIEW_ONLY_INTENT_TO_OPERATOR_INPUT_CAPTURE_PRECHECK_V0",
        "global_operator_input_capture_status": "BLOCKED_OPERATOR_INPUT_CAPTURE_NOT_ENABLED",
        "field_policy": {field: {"required": True} for field in REQUIRED_INPUT_FIELDS},
        "input_capture_precheck_items": [
            {
                "intent_item_id": "intent_item_blocked",
                "source_candidate_id": "blocked_candidate",
                "relative_path": "docs/example.json",
                "evidence_role": "contract",
                "source_family": "Example",
                "records_count": 0,
                "contract_name": "EXAMPLE_CONTRACT",
                "intent_scope_label": "example_review",
                "operator_input_capture_precheck_status": "BLOCKED_BY_REVIEW_ONLY_INTENT_PACKET",
                "blocked_reasons": ["example_block"],
                "missing_requirements": ["example_requirement"],
            }
        ],
    }

    packet = create_supervised_input_stub_contract(sample)
    assert packet["supervised_input_stub_items"][0]["supervised_input_stub_status"] == "BLOCKED_BY_OPERATOR_INPUT_CAPTURE_PRECHECK"


def test_pending_source_items_remain_pending_future_capture(source_packet):
    packet = create_supervised_input_stub_contract(source_packet)

    for source_item, stub_item in zip(source_packet["input_capture_precheck_items"], packet["supervised_input_stub_items"]):
        if source_item["operator_input_capture_precheck_status"] == "OPERATOR_INPUT_CAPTURE_PRECHECK_PENDING":
            assert stub_item["supervised_input_stub_status"] == "SUPERVISED_INPUT_STUB_PENDING_FUTURE_CAPTURE"


def test_truth_and_safety_flags_remain_false(source_packet):
    packet = create_supervised_input_stub_contract(source_packet)

    assert packet["truth_protection_flags"]
    assert packet["safety_flags"]
    assert all(value is False for value in packet["truth_protection_flags"].values())
    assert all(value is False for value in packet["safety_flags"].values())


def test_next_recommended_task_is_set_correctly(source_packet):
    packet = create_supervised_input_stub_contract(source_packet)

    assert packet["next_recommended_task"] == NEXT_RECOMMENDED_TASK
    assert packet["allowed_next_step"] == "bind_supervised_input_stub_contract_to_readonly_v5_panel"


def test_write_artifacts_outputs_json_and_runbook(tmp_path, source_packet):
    source_path = tmp_path / "source_packet.json"
    source_path.write_text(json.dumps(source_packet, sort_keys=True), encoding="utf-8")

    result = write_artifacts(source_path, repo_root=tmp_path)

    packet_path = Path(result["packet_path"])
    runbook_path = Path(result["runbook_path"])
    assert packet_path.exists()
    assert runbook_path.exists()

    loaded = json.loads(packet_path.read_text(encoding="utf-8"))
    assert loaded["global_supervised_input_stub_status"] == "BLOCKED_SUPERVISED_INPUT_CAPTURE_NOT_ENABLED"
    assert loaded["next_recommended_task"] == NEXT_RECOMMENDED_TASK
    assert "Supervised Operator Input Stub Contract" in runbook_path.read_text(encoding="utf-8")


def test_invalid_global_status_fails_closed(source_packet):
    source_packet["global_operator_input_capture_status"] = "CAPTURE_ENABLED"

    with pytest.raises(ValueError) as exc:
        create_supervised_input_stub_contract(source_packet)

    assert "Invalid operator input capture global status" in str(exc.value)
