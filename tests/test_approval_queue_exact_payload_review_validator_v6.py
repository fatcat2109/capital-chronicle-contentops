"""Unit tests for approval queue exact payload review validator module."""
from __future__ import annotations

import json
from live_contentops import approval_queue_exact_payload_review_packet_v6 as packet_builder
from live_contentops import approval_queue_exact_payload_review_input_contract_v6 as contract_builder
from live_contentops import approval_queue_exact_payload_review_validator_v6 as validator
from live_contentops import approval_queue_exact_payload_review_contract_v6 as coordinator


def test_validator_clean_blocked_passes():
    packet = packet_builder.make_approval_queue_exact_payload_review_packet()
    contract = contract_builder.make_approval_queue_exact_payload_review_input_contract()
    template = coordinator.make_approval_queue_blocked_review_template()
    output = coordinator.make_approval_queue_blocked_review_output()
    matrix = coordinator.make_approval_queue_review_gate_matrix()
    checklist = coordinator.make_approval_queue_review_checklist()

    report, blockers = validator.validate_approval_queue_exact_payload_review_contract(
        packet, contract, template, output, matrix, checklist
    )
    assert report["validation_status"] == "PASSED_WITH_REVIEW_ONLY_BLOCKERS"
    assert report["runtime_truth"] is False
    assert len(blockers) == 10
    assert "platform_variant_approval_packet_missing" in blockers


def test_validator_fails_on_packet_flags():
    packet_flags = [
        "platform_variant_approval_packet_available",
        "rendered_platform_payloads_available",
        "exact_payload_preview_available",
        "platform_payload_manifest_available",
        "destination_binding_completed",
        "account_binding_completed",
        "payload_hash_policy_available",
        "approval_policy_available",
        "approval_packet_available",
        "jim_review_completed",
        "operator_review_present",
        "exact_payload_review_allowed",
        "exact_payload_review_performed",
        "exact_payload_approval_completed",
        "approval_queue_entry_created",
        "approval_id_created",
        "approval_hash_created",
        "payload_hash_created",
        "operator_signature_present",
        "approval_valid_for_dispatch",
        "outbox_entry_created"
    ]
    for flag in packet_flags:
        packet = packet_builder.make_approval_queue_exact_payload_review_packet()
        contract = contract_builder.make_approval_queue_exact_payload_review_input_contract()
        template = coordinator.make_approval_queue_blocked_review_template()
        output = coordinator.make_approval_queue_blocked_review_output()
        matrix = coordinator.make_approval_queue_review_gate_matrix()
        checklist = coordinator.make_approval_queue_review_checklist()

        packet[flag] = True
        report, blockers = validator.validate_approval_queue_exact_payload_review_contract(
            packet, contract, template, output, matrix, checklist
        )
        assert report["validation_status"] == "FAILED_WITH_BLOCKERS"


def test_validator_fails_on_active_dispatch_flags():
    forbidden_flags = [
        "allowed_for_publication",
        "public_postable",
        "dispatch_allowed_now",
        "live_write_allowed_now"
    ]
    for flag in forbidden_flags:
        packet = packet_builder.make_approval_queue_exact_payload_review_packet()
        contract = contract_builder.make_approval_queue_exact_payload_review_input_contract()
        template = coordinator.make_approval_queue_blocked_review_template()
        output = coordinator.make_approval_queue_blocked_review_output()
        matrix = coordinator.make_approval_queue_review_gate_matrix()
        checklist = coordinator.make_approval_queue_review_checklist()

        packet[flag] = True
        report, blockers = validator.validate_approval_queue_exact_payload_review_contract(
            packet, contract, template, output, matrix, checklist
        )
        assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
        assert "forbidden_active_dispatch_flags" in blockers


def test_validator_fails_on_template_fields():
    fields = [
        "approval_queue_entry_id", "approval_id", "approval_hash", "payload_hash",
        "exact_payload_preview_ref", "platform_payload_manifest_ref", "destination_binding_ref",
        "account_binding_ref", "operator_id_redacted", "operator_signature_redacted",
        "reviewed_at_redacted", "review_statement"
    ]
    for field in fields:
        packet = packet_builder.make_approval_queue_exact_payload_review_packet()
        contract = contract_builder.make_approval_queue_exact_payload_review_input_contract()
        template = coordinator.make_approval_queue_blocked_review_template()
        output = coordinator.make_approval_queue_blocked_review_output()
        matrix = coordinator.make_approval_queue_review_gate_matrix()
        checklist = coordinator.make_approval_queue_review_checklist()

        template[field] = "active_value"
        report, blockers = validator.validate_approval_queue_exact_payload_review_contract(
            packet, contract, template, output, matrix, checklist
        )
        assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
        assert "non_null_review_template_fields_detected" in blockers


def test_validator_fails_on_output_lists_and_counts():
    output_lists = [
        "platform_payloads", "platform_payload_hashes", "exact_payload_previews",
        "review_records", "approval_records", "approval_ledger_entries",
        "destination_bindings", "account_bindings", "public_urls", "outbox_entries",
        "citations", "evidence_refs", "source_names", "platform_metrics"
    ]
    for lst in output_lists:
        packet = packet_builder.make_approval_queue_exact_payload_review_packet()
        contract = contract_builder.make_approval_queue_exact_payload_review_input_contract()
        template = coordinator.make_approval_queue_blocked_review_template()
        output = coordinator.make_approval_queue_blocked_review_output()
        matrix = coordinator.make_approval_queue_review_gate_matrix()
        checklist = coordinator.make_approval_queue_review_checklist()

        output[lst] = ["active_value"]
        report, blockers = validator.validate_approval_queue_exact_payload_review_contract(
            packet, contract, template, output, matrix, checklist
        )
        assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
        assert "non_empty_output_lists_detected" in blockers

    count_keys = [
        "review_record_count", "approval_record_count", "payload_hash_count",
        "outbox_entry_count", "destination_binding_count", "public_url_count"
    ]
    for key in count_keys:
        packet = packet_builder.make_approval_queue_exact_payload_review_packet()
        contract = contract_builder.make_approval_queue_exact_payload_review_input_contract()
        template = coordinator.make_approval_queue_blocked_review_template()
        output = coordinator.make_approval_queue_blocked_review_output()
        matrix = coordinator.make_approval_queue_review_gate_matrix()
        checklist = coordinator.make_approval_queue_review_checklist()

        output[key] = 1
        report, blockers = validator.validate_approval_queue_exact_payload_review_contract(
            packet, contract, template, output, matrix, checklist
        )
        assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
        assert "non_zero_word_or_variant_count_detected" in blockers


def test_validator_fails_on_matrix_active_lane():
    readiness_keys = [
        "platform_variant_approval_packet_available",
        "rendered_platform_payload_available",
        "exact_payload_preview_available",
        "destination_binding_completed",
        "account_binding_completed",
        "payload_hash_created",
        "approval_queue_entry_created",
        "approval_id_created",
        "approval_hash_created",
        "operator_signature_present",
        "exact_payload_review_performed",
        "exact_payload_approval_completed",
        "approval_valid_for_dispatch",
        "outbox_entry_created",
        "dispatch_allowed_now",
        "live_write_allowed_now",
        "public_url_created",
        "valid_for_publication"
    ]
    for rk in readiness_keys:
        packet = packet_builder.make_approval_queue_exact_payload_review_packet()
        contract = contract_builder.make_approval_queue_exact_payload_review_input_contract()
        template = coordinator.make_approval_queue_blocked_review_template()
        output = coordinator.make_approval_queue_blocked_review_output()
        matrix = coordinator.make_approval_queue_review_gate_matrix()
        checklist = coordinator.make_approval_queue_review_checklist()

        matrix[0][rk] = True
        report, blockers = validator.validate_approval_queue_exact_payload_review_contract(
            packet, contract, template, output, matrix, checklist
        )
        assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
        assert "readiness_matrix_active_lane_detected" in blockers


def test_validator_fails_on_matrix_blocks_publication():
    packet = packet_builder.make_approval_queue_exact_payload_review_packet()
    contract = contract_builder.make_approval_queue_exact_payload_review_input_contract()
    template = coordinator.make_approval_queue_blocked_review_template()
    output = coordinator.make_approval_queue_blocked_review_output()
    matrix = coordinator.make_approval_queue_review_gate_matrix()
    checklist = coordinator.make_approval_queue_review_checklist()

    matrix[0]["blocks_publication"] = False
    report, blockers = validator.validate_approval_queue_exact_payload_review_contract(
        packet, contract, template, output, matrix, checklist
    )
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "readiness_matrix_publication_unblocked_detected" in blockers


def test_validator_fails_on_input_contract_mutations():
    invalid_cases = [
        ("contract_status", "ACTIVE_STATUS"),
        ("required_inputs", []),
    ]
    for key, val in invalid_cases:
        packet = packet_builder.make_approval_queue_exact_payload_review_packet()
        contract = contract_builder.make_approval_queue_exact_payload_review_input_contract()
        template = coordinator.make_approval_queue_blocked_review_template()
        output = coordinator.make_approval_queue_blocked_review_output()
        matrix = coordinator.make_approval_queue_review_gate_matrix()
        checklist = coordinator.make_approval_queue_review_checklist()

        contract[key] = val
        report, blockers = validator.validate_approval_queue_exact_payload_review_contract(
            packet, contract, template, output, matrix, checklist
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
        packet = packet_builder.make_approval_queue_exact_payload_review_packet()
        contract = contract_builder.make_approval_queue_exact_payload_review_input_contract()
        template = coordinator.make_approval_queue_blocked_review_template()
        output = coordinator.make_approval_queue_blocked_review_output()
        matrix = coordinator.make_approval_queue_review_gate_matrix()
        checklist = coordinator.make_approval_queue_review_checklist()

        packet["approval_queue_review_status"] = text
        report, blockers = validator.validate_approval_queue_exact_payload_review_contract(
            packet, contract, template, output, matrix, checklist
        )
        assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
        assert expected_blocker in blockers


def test_no_forbidden_behavior_in_validator():
    import live_contentops.approval_queue_exact_payload_review_validator_v6 as target_module
    attrs = dir(target_module)
    forbidden = ["urlopen", "requests", "httpx", "getenv", "environ", "openai", "anthropic", "google"]
    for f in forbidden:
        assert f not in attrs
