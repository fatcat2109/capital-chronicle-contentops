"""Tests for Supervised Input Stub to Draft Eligibility Gate Precheck.

Part of TASK_CONTENTOPS_0175BS_SUPERVISED_INPUT_STUB_TO_DRAFT_ELIGIBILITY_GATE_PRECHECK_V0.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from live_contentops.supervised_input_stub_to_draft_eligibility_gate_precheck import (
    FORBIDDEN_CURRENT_ACTIONS,
    DISALLOWED_OUTPUTS,
    NEXT_RECOMMENDED_TASK,
    create_draft_eligibility_gate_precheck,
    write_artifacts,
)

ROOT = Path(__file__).resolve().parents[1]
SOURCE_PACKET_PATH = ROOT / "docs" / "automation" / "0175BP" / "operator_input_capture_precheck_to_supervised_input_stub_contract_packet.json"
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


def test_valid_0175bp_packet_produces_deterministic_draft_eligibility_precheck(source_packet):
    first = create_draft_eligibility_gate_precheck(source_packet)
    second = create_draft_eligibility_gate_precheck(source_packet)

    assert first == second
    assert first["packet_hash"] == second["packet_hash"]
    assert first["task_label"] == "TASK_CONTENTOPS_0175BS_SUPERVISED_INPUT_STUB_TO_DRAFT_ELIGIBILITY_GATE_PRECHECK_V0"
    assert first["source_packet_task_label"] == "TASK_CONTENTOPS_0175BP_OPERATOR_INPUT_CAPTURE_PRECHECK_TO_SUPERVISED_INPUT_STUB_CONTRACT_V0"
    assert first["global_draft_eligibility_status"] == "BLOCKED_DRAFT_ELIGIBILITY_PENDING_OPERATOR_INPUT"
    assert first["global_draft_generation_enabled"] is False
    assert first["global_public_postable"] is False


def test_every_stub_item_maps_to_one_draft_eligibility_item(source_packet):
    packet = create_draft_eligibility_gate_precheck(source_packet)

    assert packet["source_supervised_input_stub_item_count"] == len(source_packet["supervised_input_stub_items"])
    assert len(packet["draft_eligibility_items"]) == len(source_packet["supervised_input_stub_items"])

    for source_item, item in zip(source_packet["supervised_input_stub_items"], packet["draft_eligibility_items"]):
        assert item["source_stub_item_id"] == source_item["stub_item_id"]
        assert item["source_intent_item_id"] == source_item["source_intent_item_id"]
        assert item["source_candidate_id"] == source_item["source_candidate_id"]
        assert item["relative_path"] == source_item["relative_path"]
        assert item["evidence_role"] == source_item["evidence_role"]
        assert item["source_family"] == source_item["source_family"]
        assert item["records_count"] == source_item["records_count"]
        assert item["contract_name"] == source_item["contract_name"]
        assert item["intent_scope_label"] == source_item["intent_scope_label"]
        assert item["source_supervised_input_stub_status"] == source_item["supervised_input_stub_status"]
        assert item["draft_eligibility_status"] == "BLOCKED_BY_SUPERVISED_INPUT_STUB_CONTRACT"
        assert item["draft_generation_enabled"] is False
        assert item["public_postable"] is False


def test_forbidden_current_actions_include_draft_generation_and_all_locks(source_packet):
    packet = create_draft_eligibility_gate_precheck(source_packet)
    required_actions = {
        "draft_generation",
        "actual_input_capture",
        "editable_input_fields",
        "form_submission",
        "save_capture_approve_generate_controls",
        "operator_prose_generation",
        "content_generation",
        "headline_hook_caption_generation",
        "platform_copy_generation",
        "live_dispatch",
        "provider_or_platform_api_call",
        "actual_draft_generation",
    }

    assert set(packet["forbidden_current_actions"]) == set(FORBIDDEN_CURRENT_ACTIONS)
    assert required_actions <= set(packet["forbidden_current_actions"])
    for item in packet["draft_eligibility_items"]:
        assert required_actions <= set(item["forbidden_current_actions"])


def test_no_operator_prose_or_public_ready_content_fields_are_emitted(source_packet):
    packet = create_draft_eligibility_gate_precheck(source_packet)

    assert FORBIDDEN_OUTPUT_KEYS.isdisjoint(packet.keys())
    for item in packet["draft_eligibility_items"]:
        assert FORBIDDEN_OUTPUT_KEYS.isdisjoint(item.keys())


def test_truth_and_safety_flags_remain_false(source_packet):
    packet = create_draft_eligibility_gate_precheck(source_packet)

    assert packet["truth_protection_flags"]
    assert packet["safety_flags"]
    assert all(value is False for value in packet["truth_protection_flags"].values())
    assert all(value is False for value in packet["safety_flags"].values())


def test_next_recommended_task_is_set_correctly(source_packet):
    packet = create_draft_eligibility_gate_precheck(source_packet)

    assert packet["next_recommended_task"] == NEXT_RECOMMENDED_TASK
    assert packet["allowed_next_step"] == "resolve_supervised_input_stub_contract_requirements"


def test_write_artifacts_outputs_json_and_runbook(tmp_path, source_packet):
    source_path = tmp_path / "source_packet.json"
    source_path.write_text(json.dumps(source_packet, sort_keys=True), encoding="utf-8")

    result = write_artifacts(source_path, repo_root=tmp_path)

    packet_path = Path(result["packet_path"])
    runbook_path = Path(result["runbook_path"])
    assert packet_path.exists()
    assert runbook_path.exists()

    loaded = json.loads(packet_path.read_text(encoding="utf-8"))
    assert loaded["global_draft_eligibility_status"] == "BLOCKED_DRAFT_ELIGIBILITY_PENDING_OPERATOR_INPUT"
    assert loaded["next_recommended_task"] == NEXT_RECOMMENDED_TASK
    assert "Draft Eligibility Gate Precheck" in runbook_path.read_text(encoding="utf-8")


def test_invalid_global_status_fails_closed(source_packet):
    source_packet["global_supervised_input_stub_status"] = "CAPTURE_ENABLED"

    with pytest.raises(ValueError) as exc:
        create_draft_eligibility_gate_precheck(source_packet)

    assert "Invalid global supervised input stub status" in str(exc.value)
