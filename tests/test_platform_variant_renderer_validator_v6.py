"""Test V6 Platform Variant Renderer Validator."""
from __future__ import annotations

from live_contentops import platform_variant_renderer_packet_v6 as packet_builder
from live_contentops import platform_variant_renderer_input_contract_v6 as contract_builder
from live_contentops import platform_variant_renderer_blocked_output_v6 as coordinator
from live_contentops import platform_variant_renderer_validator_v6 as validator


def test_validator_passes_on_clean_simulated_state():
    packet = packet_builder.make_platform_variant_renderer_packet()
    contract = contract_builder.make_platform_variant_renderer_input_contract()
    output = coordinator.make_blocked_platform_variant_renderer_output()
    matrix = coordinator.make_platform_variant_renderer_matrix()
    checklist = coordinator.make_platform_variant_renderer_checklist()

    report, blockers = validator.validate_platform_variant_renderer_blocked_output(
        packet, contract, output, matrix, checklist
    )

    assert report["validation_status"] == "PASSED_WITH_REVIEW_ONLY_BLOCKERS"
    assert len(blockers) == 9
    assert "approved_canonical_article_missing" in blockers
    assert "seo_metadata_missing" in blockers
    assert "platform_variant_renderer_blocked" in blockers
    assert "destination_binding_missing" in blockers
    assert "exact_payload_approval_missing" in blockers
    assert "jim_review_required" in blockers
    assert "publication_blocked" in blockers
    assert "dispatch_blocked" in blockers
    assert "human_review_required" in blockers


def test_validator_fails_on_active_execution():
    packet = packet_builder.make_platform_variant_renderer_packet()
    packet["approved_canonical_article_available"] = True
    contract = contract_builder.make_platform_variant_renderer_input_contract()
    output = coordinator.make_blocked_platform_variant_renderer_output()
    matrix = coordinator.make_platform_variant_renderer_matrix()
    checklist = coordinator.make_platform_variant_renderer_checklist()

    report, blockers = validator.validate_platform_variant_renderer_blocked_output(
        packet, contract, output, matrix, checklist
    )
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "approved_canonical_article_available_claimed" in blockers


def test_validator_fails_on_non_null_output_fields():
    output_fields = [
        "substack_title", "substack_body", "substack_subtitle",
        "discord_message", "telegram_message", "linkedin_post", "threads_post"
    ]
    for field in output_fields:
        packet = packet_builder.make_platform_variant_renderer_packet()
        contract = contract_builder.make_platform_variant_renderer_input_contract()
        output = coordinator.make_blocked_platform_variant_renderer_output()
        matrix = coordinator.make_platform_variant_renderer_matrix()
        checklist = coordinator.make_platform_variant_renderer_checklist()

        output[field] = "non-null-copy"
        report, blockers = validator.validate_platform_variant_renderer_blocked_output(
            packet, contract, output, matrix, checklist
        )
        assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
        assert "non_null_platform_output_field_detected" in blockers


def test_validator_fails_on_non_empty_lists():
    list_fields = [
        "x_thread", "platform_payloads", "platform_payload_hashes",
        "destination_bindings", "account_bindings", "public_urls",
        "citations", "evidence_refs", "source_names", "platform_metrics"
    ]
    for field in list_fields:
        packet = packet_builder.make_platform_variant_renderer_packet()
        contract = contract_builder.make_platform_variant_renderer_input_contract()
        output = coordinator.make_blocked_platform_variant_renderer_output()
        matrix = coordinator.make_platform_variant_renderer_matrix()
        checklist = coordinator.make_platform_variant_renderer_checklist()

        output[field] = ["item"]
        report, blockers = validator.validate_platform_variant_renderer_blocked_output(
            packet, contract, output, matrix, checklist
        )
        assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
        assert any(b in blockers for b in ["non_empty_forbidden_output_lists_detected", "non_empty_output_lists_detected", "source_name_leak_detected", "citation_or_source_reference_leak_detected"])


def test_validator_fails_on_readiness_matrix_active_lane():
    readiness_keys_to_block = [
        "approved_canonical_article_available",
        "seo_metadata_available",
        "platform_style_rules_available",
        "destination_binding_completed",
        "exact_payload_approval_completed",
        "platform_copy_generated",
        "platform_payload_created",
        "payload_hash_created",
        "outbox_entry_created",
        "dispatch_allowed_now",
        "live_write_allowed_now",
        "public_url_created",
        "valid_for_publication"
    ]
    for rk in readiness_keys_to_block:
        packet = packet_builder.make_platform_variant_renderer_packet()
        contract = contract_builder.make_platform_variant_renderer_input_contract()
        output = coordinator.make_blocked_platform_variant_renderer_output()
        matrix = coordinator.make_platform_variant_renderer_matrix()
        checklist = coordinator.make_platform_variant_renderer_checklist()

        matrix[0][rk] = True
        report, blockers = validator.validate_platform_variant_renderer_blocked_output(
            packet, contract, output, matrix, checklist
        )
        assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
        assert "readiness_matrix_active_lane_detected" in blockers


def test_validator_fails_on_readiness_matrix_unblocked_publication():
    packet = packet_builder.make_platform_variant_renderer_packet()
    contract = contract_builder.make_platform_variant_renderer_input_contract()
    output = coordinator.make_blocked_platform_variant_renderer_output()
    matrix = coordinator.make_platform_variant_renderer_matrix()
    checklist = coordinator.make_platform_variant_renderer_checklist()

    matrix[0]["blocks_publication"] = False
    report, blockers = validator.validate_platform_variant_renderer_blocked_output(
        packet, contract, output, matrix, checklist
    )
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "readiness_matrix_publication_unblocked_detected" in blockers


def test_validator_fails_on_readiness_matrix_invalid_renderer_status():
    packet = packet_builder.make_platform_variant_renderer_packet()
    contract = contract_builder.make_platform_variant_renderer_input_contract()
    output = coordinator.make_blocked_platform_variant_renderer_output()
    matrix = coordinator.make_platform_variant_renderer_matrix()
    checklist = coordinator.make_platform_variant_renderer_checklist()

    matrix[0]["renderer_status"] = "something_else"
    report, blockers = validator.validate_platform_variant_renderer_blocked_output(
        packet, contract, output, matrix, checklist
    )
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "readiness_matrix_active_lane_detected" in blockers


def test_validator_fails_on_readiness_matrix_missing_blockers():
    packet = packet_builder.make_platform_variant_renderer_packet()
    contract = contract_builder.make_platform_variant_renderer_input_contract()
    output = coordinator.make_blocked_platform_variant_renderer_output()
    matrix = coordinator.make_platform_variant_renderer_matrix()
    checklist = coordinator.make_platform_variant_renderer_checklist()

    matrix[0]["blockers"] = ["approved_canonical_article_missing"]
    report, blockers = validator.validate_platform_variant_renderer_blocked_output(
        packet, contract, output, matrix, checklist
    )
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "readiness_matrix_active_lane_detected" in blockers


def test_validator_fails_on_contract_invalidation():
    cases = [
        ("required", False),
        ("current_status", "present"),
        ("value_ref", "some_ref"),
        ("raw_value_persisted", True),
        ("blocks_renderer_execution", False)
    ]
    for key, val in cases:
        packet = packet_builder.make_platform_variant_renderer_packet()
        contract = contract_builder.make_platform_variant_renderer_input_contract()
        output = coordinator.make_blocked_platform_variant_renderer_output()
        matrix = coordinator.make_platform_variant_renderer_matrix()
        checklist = coordinator.make_platform_variant_renderer_checklist()

        contract["required_inputs"][0][key] = val
        report, blockers = validator.validate_platform_variant_renderer_blocked_output(
            packet, contract, output, matrix, checklist
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
        packet = packet_builder.make_platform_variant_renderer_packet()
        contract = contract_builder.make_platform_variant_renderer_input_contract()
        output = coordinator.make_blocked_platform_variant_renderer_output()
        matrix = coordinator.make_platform_variant_renderer_matrix()
        checklist = coordinator.make_platform_variant_renderer_checklist()

        output["substack_title"] = text
        report, blockers = validator.validate_platform_variant_renderer_blocked_output(
            packet, contract, output, matrix, checklist
        )
        assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
        assert expected_blocker in blockers


def test_no_forbidden_behavior_in_validator():
    import live_contentops.platform_variant_renderer_validator_v6 as target_module
    attrs = dir(target_module)
    forbidden = ["urlopen", "requests", "httpx", "getenv", "environ", "openai", "anthropic", "google"]
    for f in forbidden:
        assert f not in attrs
