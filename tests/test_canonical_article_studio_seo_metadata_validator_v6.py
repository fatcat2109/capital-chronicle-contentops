"""Test V6 Canonical Article Studio SEO Metadata Validator."""
from __future__ import annotations

from live_contentops import canonical_article_studio_seo_metadata_packet_v6 as packet_builder
from live_contentops import canonical_article_studio_seo_input_contract_v6 as contract_builder
from live_contentops import canonical_article_studio_seo_metadata_contract_v6 as coordinator
from live_contentops import canonical_article_studio_seo_metadata_validator_v6 as validator


def test_validator_passes_on_clean_simulated_state():
    seo_metadata_packet = packet_builder.make_canonical_article_studio_seo_metadata_packet()
    seo_input_contract = contract_builder.make_canonical_article_studio_seo_input_contract()
    blocked_seo_output = coordinator.make_blocked_seo_output()
    seo_field_status_matrix = coordinator.make_seo_field_status_matrix()
    seo_checklist = coordinator.make_seo_checklist()

    report, blockers = validator.validate_canonical_article_studio_seo_metadata_contract(
        seo_metadata_packet, seo_input_contract, blocked_seo_output,
        seo_field_status_matrix, seo_checklist
    )

    assert report["validation_status"] == "PASSED_WITH_REVIEW_ONLY_BLOCKERS"
    assert len(blockers) == 8
    assert "refined_draft_missing" in blockers
    assert "editorial_refinement_blocked" in blockers
    assert "seo_metadata_generation_blocked" in blockers
    assert "seo_input_contract_incomplete" in blockers
    assert "jim_review_required" in blockers
    assert "publication_blocked" in blockers
    assert "dispatch_blocked" in blockers
    assert "human_review_required" in blockers


def test_validator_fails_on_active_execution():
    seo_metadata_packet = packet_builder.make_canonical_article_studio_seo_metadata_packet()
    seo_metadata_packet["seo_metadata_generation_allowed"] = True
    seo_input_contract = contract_builder.make_canonical_article_studio_seo_input_contract()
    blocked_seo_output = coordinator.make_blocked_seo_output()
    seo_field_status_matrix = coordinator.make_seo_field_status_matrix()
    seo_checklist = coordinator.make_seo_checklist()

    report, blockers = validator.validate_canonical_article_studio_seo_metadata_contract(
        seo_metadata_packet, seo_input_contract, blocked_seo_output,
        seo_field_status_matrix, seo_checklist
    )
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "seo_metadata_generation_blocked" in blockers


def test_validator_fails_on_non_null_seo_field():
    seo_metadata_packet = packet_builder.make_canonical_article_studio_seo_metadata_packet()
    seo_input_contract = contract_builder.make_canonical_article_studio_seo_input_contract()
    blocked_seo_output = coordinator.make_blocked_seo_output()
    seo_field_status_matrix = coordinator.make_seo_field_status_matrix()
    seo_field_status_matrix[0]["generated"] = True
    seo_checklist = coordinator.make_seo_checklist()

    report, blockers = validator.validate_canonical_article_studio_seo_metadata_contract(
        seo_metadata_packet, seo_input_contract, blocked_seo_output,
        seo_field_status_matrix, seo_checklist
    )
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "non_null_seo_field_detected" in blockers


def test_validator_fails_on_source_name_leak():
    seo_metadata_packet = packet_builder.make_canonical_article_studio_seo_metadata_packet()
    seo_input_contract = contract_builder.make_canonical_article_studio_seo_input_contract()
    blocked_seo_output = coordinator.make_blocked_seo_output()
    seo_field_status_matrix = coordinator.make_seo_field_status_matrix()
    seo_field_status_matrix[0]["value"] = "FRED"  # word matched
    seo_checklist = coordinator.make_seo_checklist()

    report, blockers = validator.validate_canonical_article_studio_seo_metadata_contract(
        seo_metadata_packet, seo_input_contract, blocked_seo_output,
        seo_field_status_matrix, seo_checklist
    )
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "source_name_leak_detected" in blockers


def test_no_forbidden_imports_in_validator():
    import live_contentops.canonical_article_studio_seo_metadata_validator_v6 as target_module
    attrs = dir(target_module)
    forbidden = ["urlopen", "requests", "httpx", "getenv", "environ", "openai", "anthropic", "google"]
    for f in forbidden:
        assert f not in attrs


def test_validator_fails_when_required_inputs_missing_or_empty():
    seo_metadata_packet = packet_builder.make_canonical_article_studio_seo_metadata_packet()
    seo_input_contract = contract_builder.make_canonical_article_studio_seo_input_contract()
    blocked_seo_output = coordinator.make_blocked_seo_output()
    seo_field_status_matrix = coordinator.make_seo_field_status_matrix()
    seo_checklist = coordinator.make_seo_checklist()

    seo_input_contract["required_inputs"] = []
    report, blockers = validator.validate_canonical_article_studio_seo_metadata_contract(
        seo_metadata_packet, seo_input_contract, blocked_seo_output,
        seo_field_status_matrix, seo_checklist
    )
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "seo_input_contract_incomplete" in blockers


def test_validator_fails_when_expected_input_missing():
    seo_metadata_packet = packet_builder.make_canonical_article_studio_seo_metadata_packet()
    seo_input_contract = contract_builder.make_canonical_article_studio_seo_input_contract()
    blocked_seo_output = coordinator.make_blocked_seo_output()
    seo_field_status_matrix = coordinator.make_seo_field_status_matrix()
    seo_checklist = coordinator.make_seo_checklist()

    seo_input_contract["required_inputs"].pop(0)  # remove first ref
    report, blockers = validator.validate_canonical_article_studio_seo_metadata_contract(
        seo_metadata_packet, seo_input_contract, blocked_seo_output,
        seo_field_status_matrix, seo_checklist
    )
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "seo_input_contract_incomplete" in blockers


def test_validator_fails_when_unexpected_input_present():
    seo_metadata_packet = packet_builder.make_canonical_article_studio_seo_metadata_packet()
    seo_input_contract = contract_builder.make_canonical_article_studio_seo_input_contract()
    blocked_seo_output = coordinator.make_blocked_seo_output()
    seo_field_status_matrix = coordinator.make_seo_field_status_matrix()
    seo_checklist = coordinator.make_seo_checklist()

    seo_input_contract["required_inputs"].append({
        "input_name": "unexpected_input_ref",
        "required": True,
        "current_status": "missing",
        "value_ref": None,
        "raw_value_persisted": False,
        "blocks_seo_generation": True
    })
    report, blockers = validator.validate_canonical_article_studio_seo_metadata_contract(
        seo_metadata_packet, seo_input_contract, blocked_seo_output,
        seo_field_status_matrix, seo_checklist
    )
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "seo_input_contract_incomplete" in blockers


def test_validator_fails_when_required_is_false():
    seo_metadata_packet = packet_builder.make_canonical_article_studio_seo_metadata_packet()
    seo_input_contract = contract_builder.make_canonical_article_studio_seo_input_contract()
    blocked_seo_output = coordinator.make_blocked_seo_output()
    seo_field_status_matrix = coordinator.make_seo_field_status_matrix()
    seo_checklist = coordinator.make_seo_checklist()

    seo_input_contract["required_inputs"][0]["required"] = False
    report, blockers = validator.validate_canonical_article_studio_seo_metadata_contract(
        seo_metadata_packet, seo_input_contract, blocked_seo_output,
        seo_field_status_matrix, seo_checklist
    )
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "seo_input_contract_incomplete" in blockers


def test_validator_fails_when_current_status_not_missing():
    seo_metadata_packet = packet_builder.make_canonical_article_studio_seo_metadata_packet()
    seo_input_contract = contract_builder.make_canonical_article_studio_seo_input_contract()
    blocked_seo_output = coordinator.make_blocked_seo_output()
    seo_field_status_matrix = coordinator.make_seo_field_status_matrix()
    seo_checklist = coordinator.make_seo_checklist()

    seo_input_contract["required_inputs"][0]["current_status"] = "present"
    report, blockers = validator.validate_canonical_article_studio_seo_metadata_contract(
        seo_metadata_packet, seo_input_contract, blocked_seo_output,
        seo_field_status_matrix, seo_checklist
    )
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "seo_input_contract_incomplete" in blockers


def test_validator_fails_when_value_ref_is_present():
    seo_metadata_packet = packet_builder.make_canonical_article_studio_seo_metadata_packet()
    seo_input_contract = contract_builder.make_canonical_article_studio_seo_input_contract()
    blocked_seo_output = coordinator.make_blocked_seo_output()
    seo_field_status_matrix = coordinator.make_seo_field_status_matrix()
    seo_checklist = coordinator.make_seo_checklist()

    seo_input_contract["required_inputs"][0]["value_ref"] = "some_refined_draft_ref"
    report, blockers = validator.validate_canonical_article_studio_seo_metadata_contract(
        seo_metadata_packet, seo_input_contract, blocked_seo_output,
        seo_field_status_matrix, seo_checklist
    )
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "seo_input_value_ref_present" in blockers


def test_validator_fails_when_raw_value_persisted_is_true():
    seo_metadata_packet = packet_builder.make_canonical_article_studio_seo_metadata_packet()
    seo_input_contract = contract_builder.make_canonical_article_studio_seo_input_contract()
    blocked_seo_output = coordinator.make_blocked_seo_output()
    seo_field_status_matrix = coordinator.make_seo_field_status_matrix()
    seo_checklist = coordinator.make_seo_checklist()

    seo_input_contract["required_inputs"][0]["raw_value_persisted"] = True
    report, blockers = validator.validate_canonical_article_studio_seo_metadata_contract(
        seo_metadata_packet, seo_input_contract, blocked_seo_output,
        seo_field_status_matrix, seo_checklist
    )
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "seo_input_raw_value_persisted" in blockers


def test_validator_fails_when_blocks_seo_generation_is_false():
    seo_metadata_packet = packet_builder.make_canonical_article_studio_seo_metadata_packet()
    seo_input_contract = contract_builder.make_canonical_article_studio_seo_input_contract()
    blocked_seo_output = coordinator.make_blocked_seo_output()
    seo_field_status_matrix = coordinator.make_seo_field_status_matrix()
    seo_checklist = coordinator.make_seo_checklist()

    seo_input_contract["required_inputs"][0]["blocks_seo_generation"] = False
    report, blockers = validator.validate_canonical_article_studio_seo_metadata_contract(
        seo_metadata_packet, seo_input_contract, blocked_seo_output,
        seo_field_status_matrix, seo_checklist
    )
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "seo_input_not_blocking_generation" in blockers
