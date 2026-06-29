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


def test_validator_fails_on_non_empty_citations():
    seo_metadata_packet = packet_builder.make_canonical_article_studio_seo_metadata_packet()
    seo_input_contract = contract_builder.make_canonical_article_studio_seo_input_contract()
    blocked_seo_output = coordinator.make_blocked_seo_output()
    seo_field_status_matrix = coordinator.make_seo_field_status_matrix()
    seo_checklist = coordinator.make_seo_checklist()

    blocked_seo_output["citations"] = ["https://example.com/source"]
    report, blockers = validator.validate_canonical_article_studio_seo_metadata_contract(
        seo_metadata_packet, seo_input_contract, blocked_seo_output,
        seo_field_status_matrix, seo_checklist
    )
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "citation_or_source_reference_leak_detected" in blockers
    assert "non_empty_forbidden_output_lists_detected" in blockers


def test_validator_fails_on_non_empty_evidence_refs():
    seo_metadata_packet = packet_builder.make_canonical_article_studio_seo_metadata_packet()
    seo_input_contract = contract_builder.make_canonical_article_studio_seo_input_contract()
    blocked_seo_output = coordinator.make_blocked_seo_output()
    seo_field_status_matrix = coordinator.make_seo_field_status_matrix()
    seo_checklist = coordinator.make_seo_checklist()

    blocked_seo_output["evidence_refs"] = ["ref_123"]
    report, blockers = validator.validate_canonical_article_studio_seo_metadata_contract(
        seo_metadata_packet, seo_input_contract, blocked_seo_output,
        seo_field_status_matrix, seo_checklist
    )
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "citation_or_source_reference_leak_detected" in blockers
    assert "non_empty_forbidden_output_lists_detected" in blockers


def test_validator_fails_on_non_empty_source_names():
    seo_metadata_packet = packet_builder.make_canonical_article_studio_seo_metadata_packet()
    seo_input_contract = contract_builder.make_canonical_article_studio_seo_input_contract()
    blocked_seo_output = coordinator.make_blocked_seo_output()
    seo_field_status_matrix = coordinator.make_seo_field_status_matrix()
    seo_checklist = coordinator.make_seo_checklist()

    blocked_seo_output["source_names"] = ["Acme Research"]
    report, blockers = validator.validate_canonical_article_studio_seo_metadata_contract(
        seo_metadata_packet, seo_input_contract, blocked_seo_output,
        seo_field_status_matrix, seo_checklist
    )
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "source_name_leak_detected" in blockers
    assert "non_empty_forbidden_output_lists_detected" in blockers


def test_validator_fails_on_non_empty_source_publishers_or_urls():
    seo_metadata_packet = packet_builder.make_canonical_article_studio_seo_metadata_packet()
    seo_input_contract = contract_builder.make_canonical_article_studio_seo_input_contract()
    blocked_seo_output = coordinator.make_blocked_seo_output()
    seo_field_status_matrix = coordinator.make_seo_field_status_matrix()
    seo_checklist = coordinator.make_seo_checklist()

    # 1. source_publishers
    blocked_seo_output["source_publishers"] = ["Acme Publish"]
    report, blockers = validator.validate_canonical_article_studio_seo_metadata_contract(
        seo_metadata_packet, seo_input_contract, blocked_seo_output,
        seo_field_status_matrix, seo_checklist
    )
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "source_name_leak_detected" in blockers
    assert "non_empty_forbidden_output_lists_detected" in blockers

    # 2. source_urls
    blocked_seo_output_2 = coordinator.make_blocked_seo_output()
    blocked_seo_output_2["source_urls"] = ["https://acme.org"]
    report2, blockers2 = validator.validate_canonical_article_studio_seo_metadata_contract(
        seo_metadata_packet, seo_input_contract, blocked_seo_output_2,
        seo_field_status_matrix, seo_checklist
    )
    assert report2["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "citation_or_source_reference_leak_detected" in blockers2
    assert "non_empty_forbidden_output_lists_detected" in blockers2


def test_validator_fails_on_unrecognized_plural_source_identity():
    seo_metadata_packet = packet_builder.make_canonical_article_studio_seo_metadata_packet()
    seo_input_contract = contract_builder.make_canonical_article_studio_seo_input_contract()
    blocked_seo_output = coordinator.make_blocked_seo_output()
    seo_field_status_matrix = coordinator.make_seo_field_status_matrix()
    seo_checklist = coordinator.make_seo_checklist()

    blocked_seo_output["publishers"] = ["Acme Research"]
    report, blockers = validator.validate_canonical_article_studio_seo_metadata_contract(
        seo_metadata_packet, seo_input_contract, blocked_seo_output,
        seo_field_status_matrix, seo_checklist
    )
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "source_name_leak_detected" in blockers
    assert "non_empty_forbidden_output_lists_detected" in blockers


def test_validator_fails_on_non_empty_tags_etc():
    # non-empty tags, keyword_targets, seo_notes, editorial_notes
    list_fields = ["tags", "keyword_targets", "seo_notes", "editorial_notes"]
    for field in list_fields:
        seo_metadata_packet = packet_builder.make_canonical_article_studio_seo_metadata_packet()
        seo_input_contract = contract_builder.make_canonical_article_studio_seo_input_contract()
        blocked_seo_output = coordinator.make_blocked_seo_output()
        seo_field_status_matrix = coordinator.make_seo_field_status_matrix()
        seo_checklist = coordinator.make_seo_checklist()

        blocked_seo_output[field] = ["test_item"]
        report, blockers = validator.validate_canonical_article_studio_seo_metadata_contract(
            seo_metadata_packet, seo_input_contract, blocked_seo_output,
            seo_field_status_matrix, seo_checklist
        )
        assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
        assert "non_empty_output_lists_detected" in blockers


def test_validator_fails_on_non_null_fields_and_scores():
    output_fields = [
        "seo_title", "seo_meta_description", "slug", "canonical_url",
        "social_preview_title", "social_preview_description"
    ]
    for field in output_fields:
        seo_metadata_packet = packet_builder.make_canonical_article_studio_seo_metadata_packet()
        seo_input_contract = contract_builder.make_canonical_article_studio_seo_input_contract()
        blocked_seo_output = coordinator.make_blocked_seo_output()
        seo_field_status_matrix = coordinator.make_seo_field_status_matrix()
        seo_checklist = coordinator.make_seo_checklist()

        blocked_seo_output[field] = "non-null-val"
        report, blockers = validator.validate_canonical_article_studio_seo_metadata_contract(
            seo_metadata_packet, seo_input_contract, blocked_seo_output,
            seo_field_status_matrix, seo_checklist
        )
        assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
        assert "non_null_seo_field_detected" in blockers

    # scores check
    score_fields = ["seo_score", "readability_score"]
    for field in score_fields:
        seo_metadata_packet = packet_builder.make_canonical_article_studio_seo_metadata_packet()
        seo_input_contract = contract_builder.make_canonical_article_studio_seo_input_contract()
        blocked_seo_output = coordinator.make_blocked_seo_output()
        seo_field_status_matrix = coordinator.make_seo_field_status_matrix()
        seo_checklist = coordinator.make_seo_checklist()

        blocked_seo_output[field] = 90
        report, blockers = validator.validate_canonical_article_studio_seo_metadata_contract(
            seo_metadata_packet, seo_input_contract, blocked_seo_output,
            seo_field_status_matrix, seo_checklist
        )
        assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
        assert "scores_present_detected" in blockers

    # non-zero counts
    count_keys = ["body_word_count", "source_citation_count", "evidence_excerpt_count"]
    for key in count_keys:
        seo_metadata_packet = packet_builder.make_canonical_article_studio_seo_metadata_packet()
        seo_input_contract = contract_builder.make_canonical_article_studio_seo_input_contract()
        blocked_seo_output = coordinator.make_blocked_seo_output()
        seo_field_status_matrix = coordinator.make_seo_field_status_matrix()
        seo_checklist = coordinator.make_seo_checklist()

        blocked_seo_output[key] = 10
        report, blockers = validator.validate_canonical_article_studio_seo_metadata_contract(
            seo_metadata_packet, seo_input_contract, blocked_seo_output,
            seo_field_status_matrix, seo_checklist
        )
        assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
        assert "non_zero_word_or_citation_count_detected" in blockers


def test_validator_fails_on_various_contract_invalidations():
    # required=false, current_status=present, non-null value_ref, raw_value_persisted=true, and blocks_seo_generation=false
    cases = [
        ("required", False),
        ("current_status", "present"),
        ("value_ref", "some_ref"),
        ("raw_value_persisted", True),
        ("blocks_seo_generation", False)
    ]
    for key, val in cases:
        seo_metadata_packet = packet_builder.make_canonical_article_studio_seo_metadata_packet()
        seo_input_contract = contract_builder.make_canonical_article_studio_seo_input_contract()
        blocked_seo_output = coordinator.make_blocked_seo_output()
        seo_field_status_matrix = coordinator.make_seo_field_status_matrix()
        seo_checklist = coordinator.make_seo_checklist()

        seo_input_contract["required_inputs"][0][key] = val
        report, blockers = validator.validate_canonical_article_studio_seo_metadata_contract(
            seo_metadata_packet, seo_input_contract, blocked_seo_output,
            seo_field_status_matrix, seo_checklist
        )
        assert report["validation_status"] == "FAILED_WITH_BLOCKERS"


def test_validator_fails_on_leakage_scans():
    leaks = [
        ("https://google.com", "url_leak_in_runtime_artifact"),
        ("a" * 64, "hash_leak_in_runtime_artifact"),
        ("sha256:abcd", "hash_leak_in_runtime_artifact"),
        ("excerpt: some actual text", "source_excerpt_leak_in_runtime_artifact"),
        ("[1]", "citation_or_source_reference_leak_detected"),
        ("Source: some", "citation_or_source_reference_leak_detected"),
        ("citation: some", "citation_or_source_reference_leak_detected"),
        ("reference_url: some", "citation_or_source_reference_leak_detected"),
        ("source_url: some", "citation_or_source_reference_leak_detected"),
        ("impressions", "metric_leak_detected"),
        ("public_ready", "public_ready_claim_detected"),
        ("operator_jim_sig", "operator_signature_leaked"),
        ("approval_123", "approval_id_present"),
        ("2026-06-29", "fake_approval_timestamp_detected"),
        ("email@example.com", "private_or_secret_material_detected"),
        ("sessionid", "private_or_secret_material_detected"),
        ("direct message", "dm_or_private_message_detected"),
        ("guaranteed return", "financial_advice_or_signal_language_detected"),
        ("Federal Reserve", "source_name_leak_detected"),
        ("Bloomberg", "source_name_leak_detected")
    ]
    for text, expected_blocker in leaks:
        seo_metadata_packet = packet_builder.make_canonical_article_studio_seo_metadata_packet()
        seo_input_contract = contract_builder.make_canonical_article_studio_seo_input_contract()
        blocked_seo_output = coordinator.make_blocked_seo_output()
        seo_field_status_matrix = coordinator.make_seo_field_status_matrix()
        seo_checklist = coordinator.make_seo_checklist()

        blocked_seo_output["seo_title"] = text
        report, blockers = validator.validate_canonical_article_studio_seo_metadata_contract(
            seo_metadata_packet, seo_input_contract, blocked_seo_output,
            seo_field_status_matrix, seo_checklist
        )
        assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
        assert expected_blocker in blockers

