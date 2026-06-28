"""Test V6 Canonical Article Studio Refinement Validator."""
from __future__ import annotations

from live_contentops import canonical_article_studio_refinement_queue_packet_v6 as packet_builder
from live_contentops import canonical_article_studio_refinement_input_contract_v6 as contract_builder
from live_contentops import canonical_article_studio_editorial_refinement_queue_v6 as coordinator
from live_contentops import canonical_article_studio_refinement_validator_v6 as validator


def test_validator_passes_on_clean_simulated_state():
    refinement_queue_packet = packet_builder.make_canonical_article_studio_refinement_queue_packet()
    refinement_input_contract = contract_builder.make_canonical_article_studio_refinement_input_contract()
    blocked_refinement_output = coordinator.make_blocked_refinement_output()
    refinement_slot_status_matrix = coordinator.make_refinement_slot_status_matrix()
    refinement_checklist = coordinator.make_refinement_checklist()

    report, blockers = validator.validate_canonical_article_studio_editorial_refinement_queue(
        refinement_queue_packet, refinement_input_contract, blocked_refinement_output,
        refinement_slot_status_matrix, refinement_checklist
    )

    assert report["validation_status"] == "PASSED_WITH_REVIEW_ONLY_BLOCKERS"
    assert len(blockers) == 9
    assert "rendered_draft_missing" in blockers
    assert "source_approved_renderer_blocked" in blockers
    assert "refinement_execution_blocked" in blockers
    assert "article_copy_generation_blocked" in blockers
    assert "editorial_review_required" in blockers
    assert "jim_review_required" in blockers
    assert "publication_blocked" in blockers
    assert "dispatch_blocked" in blockers
    assert "human_review_required" in blockers


def test_validator_fails_on_active_execution():
    refinement_queue_packet = packet_builder.make_canonical_article_studio_refinement_queue_packet()
    refinement_queue_packet["refinement_execution_allowed"] = True
    refinement_input_contract = contract_builder.make_canonical_article_studio_refinement_input_contract()
    blocked_refinement_output = coordinator.make_blocked_refinement_output()
    refinement_slot_status_matrix = coordinator.make_refinement_slot_status_matrix()
    refinement_checklist = coordinator.make_refinement_checklist()

    report, blockers = validator.validate_canonical_article_studio_editorial_refinement_queue(
        refinement_queue_packet, refinement_input_contract, blocked_refinement_output,
        refinement_slot_status_matrix, refinement_checklist
    )
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "refinement_execution_blocked" in blockers


def test_validator_fails_on_non_null_refined_value():
    refinement_queue_packet = packet_builder.make_canonical_article_studio_refinement_queue_packet()
    refinement_input_contract = contract_builder.make_canonical_article_studio_refinement_input_contract()
    blocked_refinement_output = coordinator.make_blocked_refinement_output()
    refinement_slot_status_matrix = coordinator.make_refinement_slot_status_matrix()
    refinement_slot_status_matrix[0]["refined_value"] = "Refined copy text"
    refinement_checklist = coordinator.make_refinement_checklist()

    report, blockers = validator.validate_canonical_article_studio_editorial_refinement_queue(
        refinement_queue_packet, refinement_input_contract, blocked_refinement_output,
        refinement_slot_status_matrix, refinement_checklist
    )
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "non_null_refined_value_detected" in blockers


def test_validator_fails_on_source_name_leak():
    refinement_queue_packet = packet_builder.make_canonical_article_studio_refinement_queue_packet()
    refinement_input_contract = contract_builder.make_canonical_article_studio_refinement_input_contract()
    blocked_refinement_output = coordinator.make_blocked_refinement_output()
    refinement_slot_status_matrix = coordinator.make_refinement_slot_status_matrix()
    refinement_slot_status_matrix[0]["rendered_value"] = "FRED"  # word matched
    refinement_checklist = coordinator.make_refinement_checklist()

    report, blockers = validator.validate_canonical_article_studio_editorial_refinement_queue(
        refinement_queue_packet, refinement_input_contract, blocked_refinement_output,
        refinement_slot_status_matrix, refinement_checklist
    )
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "source_name_leak_detected" in blockers


def test_no_forbidden_imports_in_validator():
    import live_contentops.canonical_article_studio_refinement_validator_v6 as target_module
    attrs = dir(target_module)
    forbidden = ["urlopen", "requests", "httpx", "getenv", "environ", "openai", "anthropic", "google"]
    for f in forbidden:
        assert f not in attrs


def test_validator_fails_when_required_inputs_missing_or_empty():
    refinement_queue_packet = packet_builder.make_canonical_article_studio_refinement_queue_packet()
    refinement_input_contract = contract_builder.make_canonical_article_studio_refinement_input_contract()
    blocked_refinement_output = coordinator.make_blocked_refinement_output()
    refinement_slot_status_matrix = coordinator.make_refinement_slot_status_matrix()
    refinement_checklist = coordinator.make_refinement_checklist()

    refinement_input_contract["required_inputs"] = []
    report, blockers = validator.validate_canonical_article_studio_editorial_refinement_queue(
        refinement_queue_packet, refinement_input_contract, blocked_refinement_output,
        refinement_slot_status_matrix, refinement_checklist
    )
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "refinement_input_contract_invalid" in blockers


def test_validator_fails_when_expected_input_missing():
    refinement_queue_packet = packet_builder.make_canonical_article_studio_refinement_queue_packet()
    refinement_input_contract = contract_builder.make_canonical_article_studio_refinement_input_contract()
    blocked_refinement_output = coordinator.make_blocked_refinement_output()
    refinement_slot_status_matrix = coordinator.make_refinement_slot_status_matrix()
    refinement_checklist = coordinator.make_refinement_checklist()

    refinement_input_contract["required_inputs"].pop(0)  # remove first ref
    report, blockers = validator.validate_canonical_article_studio_editorial_refinement_queue(
        refinement_queue_packet, refinement_input_contract, blocked_refinement_output,
        refinement_slot_status_matrix, refinement_checklist
    )
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "refinement_input_contract_invalid" in blockers


def test_validator_fails_when_unexpected_input_present():
    refinement_queue_packet = packet_builder.make_canonical_article_studio_refinement_queue_packet()
    refinement_input_contract = contract_builder.make_canonical_article_studio_refinement_input_contract()
    blocked_refinement_output = coordinator.make_blocked_refinement_output()
    refinement_slot_status_matrix = coordinator.make_refinement_slot_status_matrix()
    refinement_checklist = coordinator.make_refinement_checklist()

    refinement_input_contract["required_inputs"].append({
        "input_name": "unexpected_input_ref",
        "required": True,
        "current_status": "missing",
        "value_ref": None,
        "raw_value_persisted": False,
        "blocks_refinement_execution": True
    })
    report, blockers = validator.validate_canonical_article_studio_editorial_refinement_queue(
        refinement_queue_packet, refinement_input_contract, blocked_refinement_output,
        refinement_slot_status_matrix, refinement_checklist
    )
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "refinement_input_contract_invalid" in blockers


def test_validator_fails_when_required_is_false():
    refinement_queue_packet = packet_builder.make_canonical_article_studio_refinement_queue_packet()
    refinement_input_contract = contract_builder.make_canonical_article_studio_refinement_input_contract()
    blocked_refinement_output = coordinator.make_blocked_refinement_output()
    refinement_slot_status_matrix = coordinator.make_refinement_slot_status_matrix()
    refinement_checklist = coordinator.make_refinement_checklist()

    refinement_input_contract["required_inputs"][0]["required"] = False
    report, blockers = validator.validate_canonical_article_studio_editorial_refinement_queue(
        refinement_queue_packet, refinement_input_contract, blocked_refinement_output,
        refinement_slot_status_matrix, refinement_checklist
    )
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "refinement_input_contract_invalid" in blockers


def test_validator_fails_when_current_status_not_missing():
    refinement_queue_packet = packet_builder.make_canonical_article_studio_refinement_queue_packet()
    refinement_input_contract = contract_builder.make_canonical_article_studio_refinement_input_contract()
    blocked_refinement_output = coordinator.make_blocked_refinement_output()
    refinement_slot_status_matrix = coordinator.make_refinement_slot_status_matrix()
    refinement_checklist = coordinator.make_refinement_checklist()

    refinement_input_contract["required_inputs"][0]["current_status"] = "present"
    report, blockers = validator.validate_canonical_article_studio_editorial_refinement_queue(
        refinement_queue_packet, refinement_input_contract, blocked_refinement_output,
        refinement_slot_status_matrix, refinement_checklist
    )
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "refinement_input_contract_invalid" in blockers


def test_validator_fails_when_value_ref_is_present():
    refinement_queue_packet = packet_builder.make_canonical_article_studio_refinement_queue_packet()
    refinement_input_contract = contract_builder.make_canonical_article_studio_refinement_input_contract()
    blocked_refinement_output = coordinator.make_blocked_refinement_output()
    refinement_slot_status_matrix = coordinator.make_refinement_slot_status_matrix()
    refinement_checklist = coordinator.make_refinement_checklist()

    refinement_input_contract["required_inputs"][0]["value_ref"] = "some_rendered_draft_ref"
    report, blockers = validator.validate_canonical_article_studio_editorial_refinement_queue(
        refinement_queue_packet, refinement_input_contract, blocked_refinement_output,
        refinement_slot_status_matrix, refinement_checklist
    )
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "refinement_input_value_ref_present" in blockers


def test_validator_fails_when_raw_value_persisted_is_true():
    refinement_queue_packet = packet_builder.make_canonical_article_studio_refinement_queue_packet()
    refinement_input_contract = contract_builder.make_canonical_article_studio_refinement_input_contract()
    blocked_refinement_output = coordinator.make_blocked_refinement_output()
    refinement_slot_status_matrix = coordinator.make_refinement_slot_status_matrix()
    refinement_checklist = coordinator.make_refinement_checklist()

    refinement_input_contract["required_inputs"][0]["raw_value_persisted"] = True
    report, blockers = validator.validate_canonical_article_studio_editorial_refinement_queue(
        refinement_queue_packet, refinement_input_contract, blocked_refinement_output,
        refinement_slot_status_matrix, refinement_checklist
    )
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "refinement_input_raw_value_persisted" in blockers


def test_validator_fails_when_blocks_refinement_execution_is_false():
    refinement_queue_packet = packet_builder.make_canonical_article_studio_refinement_queue_packet()
    refinement_input_contract = contract_builder.make_canonical_article_studio_refinement_input_contract()
    blocked_refinement_output = coordinator.make_blocked_refinement_output()
    refinement_slot_status_matrix = coordinator.make_refinement_slot_status_matrix()
    refinement_checklist = coordinator.make_refinement_checklist()

    refinement_input_contract["required_inputs"][0]["blocks_refinement_execution"] = False
    report, blockers = validator.validate_canonical_article_studio_editorial_refinement_queue(
        refinement_queue_packet, refinement_input_contract, blocked_refinement_output,
        refinement_slot_status_matrix, refinement_checklist
    )
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "refinement_input_not_blocking_execution" in blockers
