"""Test V6 Canonical Article Studio Renderer Validator."""
from __future__ import annotations

from live_contentops import canonical_article_studio_renderer_gate_packet_v6 as packet_builder
from live_contentops import canonical_article_studio_renderer_input_contract_v6 as contract_builder
from live_contentops import canonical_article_studio_source_approved_renderer_v6 as coordinator
from live_contentops import canonical_article_studio_renderer_validator_v6 as validator


def test_validator_passes_on_clean_simulated_state():
    renderer_gate_packet = packet_builder.make_canonical_article_studio_renderer_gate_packet()
    renderer_input_contract = contract_builder.make_canonical_article_studio_renderer_input_contract()
    blocked_renderer_output = coordinator.make_blocked_renderer_output()
    renderer_slot_status_matrix = coordinator.make_renderer_slot_status_matrix()

    report, blockers = validator.validate_canonical_article_studio_source_approved_renderer(
        renderer_gate_packet, renderer_input_contract, blocked_renderer_output, renderer_slot_status_matrix
    )

    assert report["validation_status"] == "PASSED_WITH_REVIEW_ONLY_BLOCKERS"
    assert len(blockers) == 9
    assert "real_source_pack_not_approved" in blockers
    assert "runtime_operator_approval_missing" in blockers
    assert "source_approval_hash_missing" in blockers
    assert "renderer_execution_blocked" in blockers
    assert "article_copy_generation_blocked" in blockers
    assert "jim_review_required" in blockers
    assert "publication_blocked" in blockers
    assert "dispatch_blocked" in blockers
    assert "human_review_required" in blockers


def test_validator_fails_on_active_execution():
    renderer_gate_packet = packet_builder.make_canonical_article_studio_renderer_gate_packet()
    renderer_gate_packet["renderer_execution_allowed"] = True
    renderer_input_contract = contract_builder.make_canonical_article_studio_renderer_input_contract()
    blocked_renderer_output = coordinator.make_blocked_renderer_output()
    renderer_slot_status_matrix = coordinator.make_renderer_slot_status_matrix()

    report, blockers = validator.validate_canonical_article_studio_source_approved_renderer(
        renderer_gate_packet, renderer_input_contract, blocked_renderer_output, renderer_slot_status_matrix
    )
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "renderer_execution_blocked" in blockers


def test_validator_fails_on_non_null_rendered_value():
    renderer_gate_packet = packet_builder.make_canonical_article_studio_renderer_gate_packet()
    renderer_input_contract = contract_builder.make_canonical_article_studio_renderer_input_contract()
    blocked_renderer_output = coordinator.make_blocked_renderer_output()
    renderer_slot_status_matrix = coordinator.make_renderer_slot_status_matrix()
    renderer_slot_status_matrix[0]["rendered_value"] = "Some actual rendered text"

    report, blockers = validator.validate_canonical_article_studio_source_approved_renderer(
        renderer_gate_packet, renderer_input_contract, blocked_renderer_output, renderer_slot_status_matrix
    )
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "non_null_rendered_value_detected" in blockers


def test_validator_fails_on_source_name_leak():
    renderer_gate_packet = packet_builder.make_canonical_article_studio_renderer_gate_packet()
    renderer_input_contract = contract_builder.make_canonical_article_studio_renderer_input_contract()
    blocked_renderer_output = coordinator.make_blocked_renderer_output()
    renderer_slot_status_matrix = coordinator.make_renderer_slot_status_matrix()
    renderer_slot_status_matrix[0]["placeholder_id"] = "FRED"

    report, blockers = validator.validate_canonical_article_studio_source_approved_renderer(
        renderer_gate_packet, renderer_input_contract, blocked_renderer_output, renderer_slot_status_matrix
    )
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "source_name_leak_detected" in blockers


def test_no_forbidden_imports_in_validator():
    import live_contentops.canonical_article_studio_renderer_validator_v6 as target_module
    attrs = dir(target_module)
    forbidden = ["urlopen", "requests", "httpx", "getenv", "environ", "openai", "anthropic", "google"]
    for f in forbidden:
        assert f not in attrs


def test_validator_fails_when_required_inputs_missing_or_empty():
    renderer_gate_packet = packet_builder.make_canonical_article_studio_renderer_gate_packet()
    renderer_input_contract = contract_builder.make_canonical_article_studio_renderer_input_contract()
    blocked_renderer_output = coordinator.make_blocked_renderer_output()
    renderer_slot_status_matrix = coordinator.make_renderer_slot_status_matrix()

    renderer_input_contract["required_inputs"] = []
    report, blockers = validator.validate_canonical_article_studio_source_approved_renderer(
        renderer_gate_packet, renderer_input_contract, blocked_renderer_output, renderer_slot_status_matrix
    )
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "renderer_input_contract_invalid" in blockers


def test_validator_fails_when_expected_input_missing():
    renderer_gate_packet = packet_builder.make_canonical_article_studio_renderer_gate_packet()
    renderer_input_contract = contract_builder.make_canonical_article_studio_renderer_input_contract()
    blocked_renderer_output = coordinator.make_blocked_renderer_output()
    renderer_slot_status_matrix = coordinator.make_renderer_slot_status_matrix()

    renderer_input_contract["required_inputs"].pop(0)  # remove "approved_source_pack_ref"
    report, blockers = validator.validate_canonical_article_studio_source_approved_renderer(
        renderer_gate_packet, renderer_input_contract, blocked_renderer_output, renderer_slot_status_matrix
    )
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "renderer_input_contract_invalid" in blockers


def test_validator_fails_when_unexpected_input_present():
    renderer_gate_packet = packet_builder.make_canonical_article_studio_renderer_gate_packet()
    renderer_input_contract = contract_builder.make_canonical_article_studio_renderer_input_contract()
    blocked_renderer_output = coordinator.make_blocked_renderer_output()
    renderer_slot_status_matrix = coordinator.make_renderer_slot_status_matrix()

    renderer_input_contract["required_inputs"].append({
        "input_name": "unexpected_input_ref",
        "required": True,
        "current_status": "missing",
        "value_ref": None,
        "raw_value_persisted": False,
        "blocks_renderer_execution": True
    })
    report, blockers = validator.validate_canonical_article_studio_source_approved_renderer(
        renderer_gate_packet, renderer_input_contract, blocked_renderer_output, renderer_slot_status_matrix
    )
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "renderer_input_contract_invalid" in blockers


def test_validator_fails_when_required_is_false():
    renderer_gate_packet = packet_builder.make_canonical_article_studio_renderer_gate_packet()
    renderer_input_contract = contract_builder.make_canonical_article_studio_renderer_input_contract()
    blocked_renderer_output = coordinator.make_blocked_renderer_output()
    renderer_slot_status_matrix = coordinator.make_renderer_slot_status_matrix()

    renderer_input_contract["required_inputs"][0]["required"] = False
    report, blockers = validator.validate_canonical_article_studio_source_approved_renderer(
        renderer_gate_packet, renderer_input_contract, blocked_renderer_output, renderer_slot_status_matrix
    )
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "renderer_input_contract_invalid" in blockers


def test_validator_fails_when_current_status_not_missing():
    renderer_gate_packet = packet_builder.make_canonical_article_studio_renderer_gate_packet()
    renderer_input_contract = contract_builder.make_canonical_article_studio_renderer_input_contract()
    blocked_renderer_output = coordinator.make_blocked_renderer_output()
    renderer_slot_status_matrix = coordinator.make_renderer_slot_status_matrix()

    renderer_input_contract["required_inputs"][0]["current_status"] = "present"
    report, blockers = validator.validate_canonical_article_studio_source_approved_renderer(
        renderer_gate_packet, renderer_input_contract, blocked_renderer_output, renderer_slot_status_matrix
    )
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "renderer_input_contract_invalid" in blockers


def test_validator_fails_when_value_ref_is_present():
    renderer_gate_packet = packet_builder.make_canonical_article_studio_renderer_gate_packet()
    renderer_input_contract = contract_builder.make_canonical_article_studio_renderer_input_contract()
    blocked_renderer_output = coordinator.make_blocked_renderer_output()
    renderer_slot_status_matrix = coordinator.make_renderer_slot_status_matrix()

    renderer_input_contract["required_inputs"][0]["value_ref"] = "approved_source_pack_artifact_ref"
    report, blockers = validator.validate_canonical_article_studio_source_approved_renderer(
        renderer_gate_packet, renderer_input_contract, blocked_renderer_output, renderer_slot_status_matrix
    )
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "renderer_input_value_ref_present" in blockers


def test_validator_fails_when_raw_value_persisted_is_true():
    renderer_gate_packet = packet_builder.make_canonical_article_studio_renderer_gate_packet()
    renderer_input_contract = contract_builder.make_canonical_article_studio_renderer_input_contract()
    blocked_renderer_output = coordinator.make_blocked_renderer_output()
    renderer_slot_status_matrix = coordinator.make_renderer_slot_status_matrix()

    renderer_input_contract["required_inputs"][0]["raw_value_persisted"] = True
    report, blockers = validator.validate_canonical_article_studio_source_approved_renderer(
        renderer_gate_packet, renderer_input_contract, blocked_renderer_output, renderer_slot_status_matrix
    )
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "renderer_input_raw_value_persisted" in blockers


def test_validator_fails_when_blocks_renderer_execution_is_false():
    renderer_gate_packet = packet_builder.make_canonical_article_studio_renderer_gate_packet()
    renderer_input_contract = contract_builder.make_canonical_article_studio_renderer_input_contract()
    blocked_renderer_output = coordinator.make_blocked_renderer_output()
    renderer_slot_status_matrix = coordinator.make_renderer_slot_status_matrix()

    renderer_input_contract["required_inputs"][0]["blocks_renderer_execution"] = False
    report, blockers = validator.validate_canonical_article_studio_source_approved_renderer(
        renderer_gate_packet, renderer_input_contract, blocked_renderer_output, renderer_slot_status_matrix
    )
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "renderer_input_not_blocking_execution" in blockers

