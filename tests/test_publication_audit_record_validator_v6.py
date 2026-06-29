"""Unit tests for publication audit record validator."""
from __future__ import annotations

from live_contentops import publication_audit_record_packet_v6 as packet_builder
from live_contentops import publication_audit_record_input_contract_v6 as contract_builder
from live_contentops import publication_audit_record_validator_v6 as validator
from live_contentops import publication_audit_record_contract_v6 as coordinator


def test_validator_clean_blocked_passes():
    packet = packet_builder.make_publication_audit_record_packet()
    contract = contract_builder.make_publication_audit_record_input_contract()
    template = coordinator.make_publication_audit_record_blocked_template()
    output = coordinator.make_publication_audit_record_blocked_output()
    matrix = coordinator.make_publication_audit_record_gate_matrix()
    checklist = coordinator.make_publication_audit_record_checklist()

    report, blockers = validator.validate_publication_audit_record_contract(
        packet, contract, template, output, matrix, checklist
    )
    assert report["validation_status"] == "PASSED_WITH_REVIEW_ONLY_BLOCKERS"
    assert report["runtime_truth"] is False
    assert len(blockers) == 11
    assert "supervised_dispatch_result_missing" in blockers


def test_validator_fails_on_packet_flags():
    packet_flags = [
        "supervised_dispatch_success_available",
        "dispatch_response_available",
        "dispatch_attempt_id_available",
        "outbox_entry_available",
        "approved_exact_payload_review_available",
        "payload_hash_available",
        "destination_binding_completed",
        "account_binding_completed",
        "public_url_proof_available",
        "platform_publication_id_available",
        "audit_record_creation_allowed",
        "audit_record_created",
        "audit_record_mutation_allowed",
        "audit_record_mutated",
        "public_url_created",
        "publication_confirmed",
        "metrics_collection_allowed",
        "metrics_collected",
        "feedback_capture_allowed",
        "live_write_attempted",
        "retry_attempted",
        "public_postable"
    ]
    for flag in packet_flags:
        packet = packet_builder.make_publication_audit_record_packet()
        contract = contract_builder.make_publication_audit_record_input_contract()
        template = coordinator.make_publication_audit_record_blocked_template()
        output = coordinator.make_publication_audit_record_blocked_output()
        matrix = coordinator.make_publication_audit_record_gate_matrix()
        checklist = coordinator.make_publication_audit_record_checklist()

        packet[flag] = True
        report, blockers = validator.validate_publication_audit_record_contract(
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
        packet = packet_builder.make_publication_audit_record_packet()
        contract = contract_builder.make_publication_audit_record_input_contract()
        template = coordinator.make_publication_audit_record_blocked_template()
        output = coordinator.make_publication_audit_record_blocked_output()
        matrix = coordinator.make_publication_audit_record_gate_matrix()
        checklist = coordinator.make_publication_audit_record_checklist()

        packet[flag] = True
        report, blockers = validator.validate_publication_audit_record_contract(
            packet, contract, template, output, matrix, checklist
        )
        assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
        assert "forbidden_active_dispatch_flags" in blockers


def test_validator_fails_on_template_fields():
    fields = [
        "audit_record_id", "dispatch_attempt_id", "outbox_entry_id", "approval_id",
        "approval_hash", "payload_hash", "destination_binding_ref", "account_binding_ref",
        "public_url", "public_url_proof_ref", "platform_publication_id", "dispatch_response_ref",
        "request_payload_ref", "response_payload_ref", "audit_redaction_policy_ref",
        "operator_id_redacted", "operator_signature_redacted", "published_at_redacted",
        "audited_at_redacted", "audit_statement"
    ]
    for field in fields:
        packet = packet_builder.make_publication_audit_record_packet()
        contract = contract_builder.make_publication_audit_record_input_contract()
        template = coordinator.make_publication_audit_record_blocked_template()
        output = coordinator.make_publication_audit_record_blocked_output()
        matrix = coordinator.make_publication_audit_record_gate_matrix()
        checklist = coordinator.make_publication_audit_record_checklist()

        template[field] = "active_value"
        report, blockers = validator.validate_publication_audit_record_contract(
            packet, contract, template, output, matrix, checklist
        )
        assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
        assert "non_null_audit_template_fields_detected" in blockers


def test_validator_fails_on_output_lists_and_counts():
    output_lists = [
        "audit_records", "dispatch_responses", "request_payloads",
        "response_payloads", "public_urls", "public_url_proofs",
        "platform_publication_ids", "destination_bindings", "account_bindings",
        "credential_refs", "endpoint_refs", "citations", "evidence_refs", "source_names", "platform_metrics"
    ]
    for lst in output_lists:
        packet = packet_builder.make_publication_audit_record_packet()
        contract = contract_builder.make_publication_audit_record_input_contract()
        template = coordinator.make_publication_audit_record_blocked_template()
        output = coordinator.make_publication_audit_record_blocked_output()
        matrix = coordinator.make_publication_audit_record_gate_matrix()
        checklist = coordinator.make_publication_audit_record_checklist()

        output[lst] = ["active_value"]
        report, blockers = validator.validate_publication_audit_record_contract(
            packet, contract, template, output, matrix, checklist
        )
        assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
        assert "non_empty_output_lists_detected" in blockers

    count_keys = [
        "audit_record_count", "public_url_count", "dispatch_response_count",
        "metric_count", "feedback_capture_count"
    ]
    for key in count_keys:
        packet = packet_builder.make_publication_audit_record_packet()
        contract = contract_builder.make_publication_audit_record_input_contract()
        template = coordinator.make_publication_audit_record_blocked_template()
        output = coordinator.make_publication_audit_record_blocked_output()
        matrix = coordinator.make_publication_audit_record_gate_matrix()
        checklist = coordinator.make_publication_audit_record_checklist()

        output[key] = 1
        report, blockers = validator.validate_publication_audit_record_contract(
            packet, contract, template, output, matrix, checklist
        )
        assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
        assert "non_zero_word_or_variant_count_detected" in blockers


def test_validator_fails_on_matrix_active_lane():
    readiness_keys = [
        "supervised_dispatch_success_available",
        "dispatch_response_available",
        "dispatch_attempt_id_available",
        "outbox_entry_available",
        "approved_exact_payload_review_available",
        "payload_hash_available",
        "destination_binding_completed",
        "account_binding_completed",
        "public_url_proof_available",
        "platform_publication_id_available",
        "audit_record_creation_allowed",
        "audit_record_created",
        "audit_record_mutation_allowed",
        "audit_record_mutated",
        "publication_confirmed",
        "public_url_created",
        "metrics_collection_allowed",
        "metrics_collected",
        "feedback_capture_allowed",
        "live_write_attempted",
        "retry_attempted",
        "dispatch_allowed_now",
        "live_write_allowed_now"
    ]
    for rk in readiness_keys:
        packet = packet_builder.make_publication_audit_record_packet()
        contract = contract_builder.make_publication_audit_record_input_contract()
        template = coordinator.make_publication_audit_record_blocked_template()
        output = coordinator.make_publication_audit_record_blocked_output()
        matrix = coordinator.make_publication_audit_record_gate_matrix()
        checklist = coordinator.make_publication_audit_record_checklist()

        matrix[0][rk] = True
        report, blockers = validator.validate_publication_audit_record_contract(
            packet, contract, template, output, matrix, checklist
        )
        assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
        assert "readiness_matrix_active_lane_detected" in blockers


def test_validator_fails_on_matrix_blocks_publication():
    packet = packet_builder.make_publication_audit_record_packet()
    contract = contract_builder.make_publication_audit_record_input_contract()
    template = coordinator.make_publication_audit_record_blocked_template()
    output = coordinator.make_publication_audit_record_blocked_output()
    matrix = coordinator.make_publication_audit_record_gate_matrix()
    checklist = coordinator.make_publication_audit_record_checklist()

    matrix[0]["blocks_publication"] = False
    report, blockers = validator.validate_publication_audit_record_contract(
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
        packet = packet_builder.make_publication_audit_record_packet()
        contract = contract_builder.make_publication_audit_record_input_contract()
        template = coordinator.make_publication_audit_record_blocked_template()
        output = coordinator.make_publication_audit_record_blocked_output()
        matrix = coordinator.make_publication_audit_record_gate_matrix()
        checklist = coordinator.make_publication_audit_record_checklist()

        contract[key] = val
        report, blockers = validator.validate_publication_audit_record_contract(
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
        ("dispatch_ready", "public_ready_claim_detected"),
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
        packet = packet_builder.make_publication_audit_record_packet()
        contract = contract_builder.make_publication_audit_record_input_contract()
        template = coordinator.make_publication_audit_record_blocked_template()
        output = coordinator.make_publication_audit_record_blocked_output()
        matrix = coordinator.make_publication_audit_record_gate_matrix()
        checklist = coordinator.make_publication_audit_record_checklist()

        packet["publication_audit_record_status"] = text
        report, blockers = validator.validate_publication_audit_record_contract(
            packet, contract, template, output, matrix, checklist
        )
        assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
        assert expected_blocker in blockers


def test_broad_substrings_leak():
    # 1. source_name="Refinitiv"
    packet = packet_builder.make_publication_audit_record_packet()
    contract = contract_builder.make_publication_audit_record_input_contract()
    template = coordinator.make_publication_audit_record_blocked_template()
    output = coordinator.make_publication_audit_record_blocked_output()
    matrix = coordinator.make_publication_audit_record_gate_matrix()
    checklist = coordinator.make_publication_audit_record_checklist()

    packet["publication_audit_record_status"] = "Source Name: Refinitiv"
    report, blockers = validator.validate_publication_audit_record_contract(
        packet, contract, template, output, matrix, checklist
    )
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "source_name_leak_detected" in blockers

    # 2. source_publisher="Reference Data Inc"
    packet = packet_builder.make_publication_audit_record_packet()
    contract = contract_builder.make_publication_audit_record_input_contract()
    template = coordinator.make_publication_audit_record_blocked_template()
    output = coordinator.make_publication_audit_record_blocked_output()
    matrix = coordinator.make_publication_audit_record_gate_matrix()
    checklist = coordinator.make_publication_audit_record_checklist()

    packet["publication_audit_record_status"] = "Publisher: Reference Data Inc"
    report, blockers = validator.validate_publication_audit_record_contract(
        packet, contract, template, output, matrix, checklist
    )
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "source_name_leak_detected" in blockers

    # 3. source_names=["Refinitiv"]
    packet = packet_builder.make_publication_audit_record_packet()
    contract = contract_builder.make_publication_audit_record_input_contract()
    template = coordinator.make_publication_audit_record_blocked_template()
    output = coordinator.make_publication_audit_record_blocked_output()
    matrix = coordinator.make_publication_audit_record_gate_matrix()
    checklist = coordinator.make_publication_audit_record_checklist()

    output["source_names"] = ["Refinitiv"]
    report, blockers = validator.validate_publication_audit_record_contract(
        packet, contract, template, output, matrix, checklist
    )
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "source_name_leak_detected" in blockers

    # 4. operator_signature="contract_operator_signature"
    packet = packet_builder.make_publication_audit_record_packet()
    contract = contract_builder.make_publication_audit_record_input_contract()
    template = coordinator.make_publication_audit_record_blocked_template()
    output = coordinator.make_publication_audit_record_blocked_output()
    matrix = coordinator.make_publication_audit_record_gate_matrix()
    checklist = coordinator.make_publication_audit_record_checklist()

    template["operator_signature"] = "contract_operator_signature"
    report, blockers = validator.validate_publication_audit_record_contract(
        packet, contract, template, output, matrix, checklist
    )
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "operator_signature_leaked" in blockers

    # 5. operator_id="policy_operator_id"
    packet = packet_builder.make_publication_audit_record_packet()
    contract = contract_builder.make_publication_audit_record_input_contract()
    template = coordinator.make_publication_audit_record_blocked_template()
    output = coordinator.make_publication_audit_record_blocked_output()
    matrix = coordinator.make_publication_audit_record_gate_matrix()
    checklist = coordinator.make_publication_audit_record_checklist()

    template["operator_id"] = "policy_operator_id"
    report, blockers = validator.validate_publication_audit_record_contract(
        packet, contract, template, output, matrix, checklist
    )
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "operator_signature_leaked" in blockers

    # 6. approval_id="policy_approval_id"
    packet = packet_builder.make_publication_audit_record_packet()
    contract = contract_builder.make_publication_audit_record_input_contract()
    template = coordinator.make_publication_audit_record_blocked_template()
    output = coordinator.make_publication_audit_record_blocked_output()
    matrix = coordinator.make_publication_audit_record_gate_matrix()
    checklist = coordinator.make_publication_audit_record_checklist()

    template["approval_id"] = "policy_approval_id"
    report, blockers = validator.validate_publication_audit_record_contract(
        packet, contract, template, output, matrix, checklist
    )
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "operator_signature_leaked" in blockers

    # 7. approval_hash="contract_approval_hash"
    packet = packet_builder.make_publication_audit_record_packet()
    contract = contract_builder.make_publication_audit_record_input_contract()
    template = coordinator.make_publication_audit_record_blocked_template()
    output = coordinator.make_publication_audit_record_blocked_output()
    matrix = coordinator.make_publication_audit_record_gate_matrix()
    checklist = coordinator.make_publication_audit_record_checklist()

    template["approval_hash"] = "contract_approval_hash"
    report, blockers = validator.validate_publication_audit_record_contract(
        packet, contract, template, output, matrix, checklist
    )
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "operator_signature_leaked" in blockers

    # 8. payload_hash="policy_payload_hash"
    packet = packet_builder.make_publication_audit_record_packet()
    contract = contract_builder.make_publication_audit_record_input_contract()
    template = coordinator.make_publication_audit_record_blocked_template()
    output = coordinator.make_publication_audit_record_blocked_output()
    matrix = coordinator.make_publication_audit_record_gate_matrix()
    checklist = coordinator.make_publication_audit_record_checklist()

    template["payload_hash"] = "policy_payload_hash"
    report, blockers = validator.validate_publication_audit_record_contract(
        packet, contract, template, output, matrix, checklist
    )
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "operator_signature_leaked" in blockers

    # 9. outbox_entry_id="contract_outbox_entry_id"
    packet = packet_builder.make_publication_audit_record_packet()
    contract = contract_builder.make_publication_audit_record_input_contract()
    template = coordinator.make_publication_audit_record_blocked_template()
    output = coordinator.make_publication_audit_record_blocked_output()
    matrix = coordinator.make_publication_audit_record_gate_matrix()
    checklist = coordinator.make_publication_audit_record_checklist()

    template["outbox_entry_id"] = "contract_outbox_entry_id"
    report, blockers = validator.validate_publication_audit_record_contract(
        packet, contract, template, output, matrix, checklist
    )
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "operator_signature_leaked" in blockers

    # 10. audit_statement="contract audit statement"
    packet = packet_builder.make_publication_audit_record_packet()
    contract = contract_builder.make_publication_audit_record_input_contract()
    template = coordinator.make_publication_audit_record_blocked_template()
    output = coordinator.make_publication_audit_record_blocked_output()
    matrix = coordinator.make_publication_audit_record_gate_matrix()
    checklist = coordinator.make_publication_audit_record_checklist()

    template["audit_statement"] = "contract audit statement"
    report, blockers = validator.validate_publication_audit_record_contract(
        packet, contract, template, output, matrix, checklist
    )
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "operator_signature_leaked" in blockers

    # 11. public_url="https://example.com/ref"
    packet = packet_builder.make_publication_audit_record_packet()
    contract = contract_builder.make_publication_audit_record_input_contract()
    template = coordinator.make_publication_audit_record_blocked_template()
    output = coordinator.make_publication_audit_record_blocked_output()
    matrix = coordinator.make_publication_audit_record_gate_matrix()
    checklist = coordinator.make_publication_audit_record_checklist()

    packet["publication_audit_record_status"] = "https://example.com/ref"
    report, blockers = validator.validate_publication_audit_record_contract(
        packet, contract, template, output, matrix, checklist
    )
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "url_leak_in_runtime_artifact" in blockers
