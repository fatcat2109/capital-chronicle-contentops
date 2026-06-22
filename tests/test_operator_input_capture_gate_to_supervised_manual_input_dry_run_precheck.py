"""Tests for Operator Input Capture Gate to Supervised Manual Input Dry Run Precheck.

Part of TASK_CONTENTOPS_0175BY_OPERATOR_INPUT_CAPTURE_GATE_TO_SUPERVISED_MANUAL_INPUT_DRY_RUN_PRECHECK_V0.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from live_contentops.operator_input_capture_gate_to_supervised_manual_input_dry_run_precheck import (
    BLOCKED_UNTIL_VALUES_EXIST,
    DISALLOWED_OUTPUTS,
    DRY_RUN_CHECKS_WITHOUT_VALUES,
    FORBIDDEN_CURRENT_ACTIONS,
    FUTURE_EVIDENCE_REQUIREMENTS,
    FUTURE_OPERATOR_MANUAL_STEPS,
    NEXT_RECOMMENDED_TASK,
    REQUIRED_INPUT_FIELDS,
    create_supervised_manual_input_dry_run_precheck,
    write_artifacts,
)

ROOT = Path(__file__).resolve().parents[1]
SOURCE_PACKET_PATH = ROOT / "docs" / "automation" / "0175BX" / "local_redaction_validation_precheck_to_operator_input_capture_gate_contract_packet.json"
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


def test_valid_0175bx_packet_produces_deterministic_dry_run_precheck(source_packet):
    first = create_supervised_manual_input_dry_run_precheck(source_packet)
    second = create_supervised_manual_input_dry_run_precheck(source_packet)

    assert first == second
    assert first["packet_hash"] == second["packet_hash"]
    assert first["task_label"] == "TASK_CONTENTOPS_0175BY_OPERATOR_INPUT_CAPTURE_GATE_TO_SUPERVISED_MANUAL_INPUT_DRY_RUN_PRECHECK_V0"
    assert first["source_packet_task_label"] == "TASK_CONTENTOPS_0175BX_LOCAL_REDACTION_VALIDATION_PRECHECK_TO_OPERATOR_INPUT_CAPTURE_GATE_CONTRACT_V0"
    assert first["global_supervised_manual_input_dry_run_precheck_status"] == "BLOCKED_SUPERVISED_MANUAL_INPUT_DRY_RUN_PENDING_REAL_VALUES"


def test_every_capture_gate_item_maps_to_one_dry_run_precheck_item(source_packet):
    packet = create_supervised_manual_input_dry_run_precheck(source_packet)

    assert packet["source_capture_gate_item_count"] == len(source_packet["operator_input_capture_gate_items"])
    assert len(packet["supervised_manual_input_dry_run_precheck_items"]) == len(source_packet["operator_input_capture_gate_items"])

    for index, (source_item, item) in enumerate(zip(source_packet["operator_input_capture_gate_items"], packet["supervised_manual_input_dry_run_precheck_items"]), start=1):
        assert item["dry_run_precheck_item_id"] == f"manual_input_dry_run_item_{index:02d}_{source_item['source_candidate_id']}"
        assert item["source_capture_gate_item_id"] == source_item["capture_gate_item_id"]
        assert item["source_precheck_item_id"] == source_item["source_precheck_item_id"]
        assert item["source_candidate_id"] == source_item["source_candidate_id"]
        assert item["relative_path"] == source_item["relative_path"]
        assert item["evidence_role"] == source_item["evidence_role"]
        assert item["source_family"] == source_item["source_family"]
        assert item["records_count"] == source_item["records_count"]
        assert item["contract_name"] == source_item["contract_name"]
        assert item["intent_scope_label"] == source_item["intent_scope_label"]
        assert item["source_operator_input_capture_gate_status"] == source_item["operator_input_capture_gate_status"]


def test_required_and_missing_input_fields_remain_unresolved(source_packet):
    packet = create_supervised_manual_input_dry_run_precheck(source_packet)

    assert packet["required_input_fields"] == list(REQUIRED_INPUT_FIELDS)
    assert packet["missing_required_input_fields"] == list(REQUIRED_INPUT_FIELDS)
    for item in packet["supervised_manual_input_dry_run_precheck_items"]:
        assert item["required_input_fields"] == list(REQUIRED_INPUT_FIELDS)
        assert item["missing_required_input_fields"] == list(REQUIRED_INPUT_FIELDS)


def test_future_operator_steps_are_schema_only(source_packet):
    packet = create_supervised_manual_input_dry_run_precheck(source_packet)

    assert packet["future_operator_manual_steps"] == list(FUTURE_OPERATOR_MANUAL_STEPS)
    assert "enter_operator_owned_values_in_future_task_only" in packet["future_operator_manual_steps"]
    assert "run_local_redaction_scan_after_values_exist" in packet["future_operator_manual_steps"]
    for item in packet["supervised_manual_input_dry_run_precheck_items"]:
        assert item["future_operator_manual_steps"] == list(FUTURE_OPERATOR_MANUAL_STEPS)


def test_dry_run_checks_possible_without_values_are_limited_to_schema_checks(source_packet):
    packet = create_supervised_manual_input_dry_run_precheck(source_packet)

    assert packet["dry_run_checks_without_values"] == list(DRY_RUN_CHECKS_WITHOUT_VALUES)
    matrix = packet["dry_run_check_matrix"]
    assert set(matrix) == set(DRY_RUN_CHECKS_WITHOUT_VALUES)
    for row in matrix.values():
        assert row["dry_run_check_possible_without_values"] is True
        assert row["executes_real_capture"] is False
        assert row["executes_validation_or_redaction"] is False
        assert row["writes_persistence"] is False
        assert row["promotes_truth"] is False
        assert row["check_status"] == "DRY_RUN_SCHEMA_CHECK_ONLY"


def test_blocked_until_values_exist_matrix_disables_all_runtime_actions(source_packet):
    packet = create_supervised_manual_input_dry_run_precheck(source_packet)

    assert packet["blocked_until_values_exist"] == list(BLOCKED_UNTIL_VALUES_EXIST)
    matrix = packet["blocked_execution_matrix"]
    assert set(matrix) == set(BLOCKED_UNTIL_VALUES_EXIST)
    for row in matrix.values():
        assert row["blocked_now"] is True
        assert row["requires_real_operator_values"] is True
        assert row["enabled_in_this_task"] is False
        assert row["blocking_reason"] == "real_operator_values_absent_and_capture_disabled"


def test_future_evidence_requirements_are_not_captured(source_packet):
    packet = create_supervised_manual_input_dry_run_precheck(source_packet)

    assert packet["future_evidence_requirements"] == list(FUTURE_EVIDENCE_REQUIREMENTS)
    matrix = packet["future_evidence_requirement_matrix"]
    assert set(matrix) == set(FUTURE_EVIDENCE_REQUIREMENTS)
    for row in matrix.values():
        assert row["required_in_future"] is True
        assert row["captured_in_this_task"] is False
        assert row["current_value_present"] is False
        assert row["current_value"] is None
        assert row["blocking_reason"] == "evidence_capture_not_enabled_in_this_task"


def test_manual_input_dry_run_policy_blocks_capture_and_execution(source_packet):
    packet = create_supervised_manual_input_dry_run_precheck(source_packet)
    policies = [packet["manual_input_dry_run_policy"]]
    policies.extend(item["manual_input_dry_run_policy"] for item in packet["supervised_manual_input_dry_run_precheck_items"])

    for policy in policies:
        assert policy["dry_run_precheck_only"] is True
        assert policy["manual_input_session_started"] is False
        assert policy["operator_input_capture_enabled_in_this_task"] is False
        assert policy["real_operator_value_acceptance_enabled_in_this_task"] is False
        assert policy["editable_ui_enabled_in_this_task"] is False
        assert policy["form_submission_enabled_in_this_task"] is False
        assert policy["evidence_capture_enabled_in_this_task"] is False
        assert policy["persistence_enabled_in_this_task"] is False
        assert policy["validation_execution_enabled_in_this_task"] is False
        assert policy["redaction_execution_enabled_in_this_task"] is False
        assert policy["draft_eligibility_recheck_enabled_in_this_task"] is False
        assert policy["pass_status"] == "BLOCKED_PENDING_REAL_OPERATOR_VALUES"


def test_capture_execution_policy_disables_ui_storage_and_generation(source_packet):
    packet = create_supervised_manual_input_dry_run_precheck(source_packet)
    policies = [packet["capture_execution_policy"]]
    policies.extend(item["capture_execution_policy"] for item in packet["supervised_manual_input_dry_run_precheck_items"])

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
        assert policy["local_storage_enabled"] is False
        assert policy["session_storage_enabled"] is False


def test_draft_eligibility_remains_blocked(source_packet):
    packet = create_supervised_manual_input_dry_run_precheck(source_packet)
    blockers = [packet["draft_eligibility_block_reason"]]
    blockers.extend(item["draft_eligibility_block_reason"] for item in packet["supervised_manual_input_dry_run_precheck_items"])

    for block in blockers:
        assert block["draft_eligibility_status"] == "BLOCKED_DRAFT_ELIGIBILITY_SUPERVISED_INPUT_REQUIRED"
        assert block["draft_generation_enabled"] is False
        assert block["draft_eligibility_recheck_enabled"] is False
        assert block["required_operator_values_present"] is False
        assert block["redaction_validation_passed"] is False
        assert block["evidence_requirements_satisfied"] is False
        assert "missing_required_operator_inputs" in block["blocking_reasons"]
        assert "redaction_validation_not_executed" in block["blocking_reasons"]


def test_forbidden_current_actions_cover_ui_capture_storage_execution_and_live(source_packet):
    packet = create_supervised_manual_input_dry_run_precheck(source_packet)
    required_actions = {
        "actual_input_capture",
        "real_operator_value_acceptance",
        "editable_input_fields",
        "form_submission",
        "save_capture_approve_generate_controls",
        "operator_value_persistence",
        "evidence_capture",
        "validation_execution",
        "redaction_execution",
        "draft_generation",
        "ai_writer_generation",
        "public_posting",
        "live_dispatch",
        "provider_or_platform_api_call",
        "local_storage_write",
        "session_storage_write",
        "draft_eligibility_recheck",
    }

    assert set(packet["forbidden_current_actions"]) == set(FORBIDDEN_CURRENT_ACTIONS)
    assert required_actions <= set(packet["forbidden_current_actions"])
    for item in packet["supervised_manual_input_dry_run_precheck_items"]:
        assert required_actions <= set(item["forbidden_current_actions"])


def test_no_operator_values_or_public_ready_content_fields_are_emitted(source_packet):
    packet = create_supervised_manual_input_dry_run_precheck(source_packet)

    assert set(packet["disallowed_outputs"]) == set(DISALLOWED_OUTPUTS)
    assert FORBIDDEN_OUTPUT_KEYS.isdisjoint(packet.keys())
    for item in packet["supervised_manual_input_dry_run_precheck_items"]:
        assert FORBIDDEN_OUTPUT_KEYS.isdisjoint(item.keys())
        assert set(item["disallowed_outputs"]) == set(DISALLOWED_OUTPUTS)


def test_truth_and_safety_flags_remain_false(source_packet):
    packet = create_supervised_manual_input_dry_run_precheck(source_packet)

    assert packet["truth_protection_flags"]
    assert packet["safety_flags"]
    assert all(value is False for value in packet["truth_protection_flags"].values())
    assert all(value is False for value in packet["safety_flags"].values())
    assert packet["truth_protection_flags"]["captured_value_truth_promoted"] is False
    assert packet["safety_flags"]["actual_operator_input_capture_enabled"] is False
    assert packet["safety_flags"]["manual_input_dry_run_enabled"] is False
    assert packet["safety_flags"]["local_storage_write_enabled"] is False
    assert packet["safety_flags"]["session_storage_write_enabled"] is False


def test_item_status_mappings_and_fail_closed(source_packet):
    packet = create_supervised_manual_input_dry_run_precheck(source_packet)
    assert packet["supervised_manual_input_dry_run_precheck_items"][0]["supervised_manual_input_dry_run_precheck_status"] == "BLOCKED_SUPERVISED_MANUAL_INPUT_DRY_RUN_PENDING_REAL_VALUES"

    sample = {
        "task_label": "TASK_CONTENTOPS_0175BX_LOCAL_REDACTION_VALIDATION_PRECHECK_TO_OPERATOR_INPUT_CAPTURE_GATE_CONTRACT_V0",
        "global_operator_input_capture_gate_status": "BLOCKED_OPERATOR_INPUT_CAPTURE_GATE_PENDING_SUPERVISED_ACTIVATION",
        "operator_input_capture_gate_items": [
            {
                "capture_gate_item_id": "capture_gate_1",
                "source_candidate_id": "candidate_1",
                "operator_input_capture_gate_status": "BLOCKED_BY_LOCAL_REDACTION_VALIDATION_PRECHECK",
            },
            {
                "capture_gate_item_id": "capture_gate_2",
                "source_candidate_id": "candidate_2",
                "operator_input_capture_gate_status": "UNKNOWN",
            },
        ],
    }
    repaired = create_supervised_manual_input_dry_run_precheck(sample)
    assert repaired["supervised_manual_input_dry_run_precheck_items"][0]["supervised_manual_input_dry_run_precheck_status"] == "BLOCKED_BY_OPERATOR_INPUT_CAPTURE_GATE"
    assert repaired["supervised_manual_input_dry_run_precheck_items"][1]["supervised_manual_input_dry_run_precheck_status"] == "BLOCKED_BY_OPERATOR_INPUT_CAPTURE_GATE"


def test_next_recommended_task_is_set_correctly(source_packet):
    packet = create_supervised_manual_input_dry_run_precheck(source_packet)

    assert packet["next_recommended_task"] == NEXT_RECOMMENDED_TASK
    assert packet["allowed_next_step"] == "stage_supervised_manual_input_dry_run_precheck_to_operator_value_intake_policy"


def test_write_artifacts_outputs_json_and_runbook(tmp_path, source_packet):
    source_path = tmp_path / "source_packet.json"
    source_path.write_text(json.dumps(source_packet, sort_keys=True), encoding="utf-8")

    result = write_artifacts(source_path, repo_root=tmp_path)

    packet_path = Path(result["packet_path"])
    runbook_path = Path(result["runbook_path"])
    assert packet_path.exists()
    assert runbook_path.exists()

    loaded = json.loads(packet_path.read_text(encoding="utf-8"))
    assert loaded["global_supervised_manual_input_dry_run_precheck_status"] == "BLOCKED_SUPERVISED_MANUAL_INPUT_DRY_RUN_PENDING_REAL_VALUES"
    assert loaded["next_recommended_task"] == NEXT_RECOMMENDED_TASK
    assert "Supervised Manual Input Dry Run Precheck" in runbook_path.read_text(encoding="utf-8")


def test_invalid_global_status_fails_closed(source_packet):
    source_packet["global_operator_input_capture_gate_status"] = "PASSED"

    with pytest.raises(ValueError) as exc:
        create_supervised_manual_input_dry_run_precheck(source_packet)

    assert "Invalid global capture gate status" in str(exc.value)
