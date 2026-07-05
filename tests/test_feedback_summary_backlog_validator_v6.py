"""Unit tests for feedback summary backlog validator."""
from __future__ import annotations

import sys
from live_contentops import feedback_summary_backlog_packet_v6 as packet_builder
from live_contentops import feedback_summary_backlog_input_contract_v6 as contract_builder
from live_contentops import feedback_summary_backlog_validator_v6 as validator
from live_contentops import feedback_summary_backlog_contract_v6 as coordinator


def test_validator_clean_blocked_passes():
    packet = packet_builder.make_feedback_summary_backlog_packet()
    contract = contract_builder.make_feedback_summary_backlog_input_contract()
    template = coordinator.make_feedback_summary_backlog_blocked_template()
    output = coordinator.make_feedback_summary_backlog_blocked_output()
    matrix = coordinator.make_feedback_summary_backlog_gate_matrix()
    checklist = coordinator.make_feedback_summary_backlog_checklist()

    report, blockers = validator.validate_feedback_summary_backlog_contract(
        packet, contract, template, output, matrix, checklist
    )
    assert report["validation_status"] == "PASSED_WITH_REVIEW_ONLY_BLOCKERS"
    assert report["runtime_truth"] is False
    assert len(blockers) == 11
    assert "community_feedback_capture_missing" in blockers


def test_validator_fails_on_packet_flags():
    packet_flags = [
        "community_feedback_capture_available",
        "redacted_feedback_records_available",
        "comments_available",
        "reactions_available",
        "metrics_available",
        "public_url_proof_available",
        "platform_publication_id_available",
        "feedback_summarization_policy_available",
        "backlog_routing_policy_available",
        "jim_feedback_review_completed",
        "operator_summary_authorization_present",
        "summary_generation_allowed",
        "summary_generation_performed",
        "backlog_item_creation_allowed",
        "backlog_item_created",
        "next_article_signal_created",
        "scraping_performed",
        "live_write_attempted",
        "retry_attempted",
        "public_url_created",
        "public_postable"
    ]
    for flag in packet_flags:
        packet = packet_builder.make_feedback_summary_backlog_packet()
        contract = contract_builder.make_feedback_summary_backlog_input_contract()
        template = coordinator.make_feedback_summary_backlog_blocked_template()
        output = coordinator.make_feedback_summary_backlog_blocked_output()
        matrix = coordinator.make_feedback_summary_backlog_gate_matrix()
        checklist = coordinator.make_feedback_summary_backlog_checklist()

        packet[flag] = True
        report, blockers = validator.validate_feedback_summary_backlog_contract(
            packet, contract, template, output, matrix, checklist
        )
        assert report["validation_status"] == "FAILED_WITH_BLOCKERS"


def test_validator_fails_on_input_contract_mutations():
    # 1. Missing input
    packet = packet_builder.make_feedback_summary_backlog_packet()
    contract = contract_builder.make_feedback_summary_backlog_input_contract()
    template = coordinator.make_feedback_summary_backlog_blocked_template()
    output = coordinator.make_feedback_summary_backlog_blocked_output()
    matrix = coordinator.make_feedback_summary_backlog_gate_matrix()
    checklist = coordinator.make_feedback_summary_backlog_checklist()

    contract["required_inputs"].pop(0)
    report, blockers = validator.validate_feedback_summary_backlog_contract(
        packet, contract, template, output, matrix, checklist
    )
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "platform_input_contract_incomplete" in blockers

    # 2. Unexpected input
    contract = contract_builder.make_feedback_summary_backlog_input_contract()
    contract["required_inputs"].append({
        "input_name": "unexpected_input",
        "required": True,
        "current_status": "missing",
        "value_ref": None,
        "raw_value_persisted": False,
        "blocks_feedback_summary_backlog_creation": True
    })
    report, blockers = validator.validate_feedback_summary_backlog_contract(
        packet, contract, template, output, matrix, checklist
    )
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "platform_input_contract_incomplete" in blockers

    # 3. required=False
    contract = contract_builder.make_feedback_summary_backlog_input_contract()
    contract["required_inputs"][0]["required"] = False
    report, blockers = validator.validate_feedback_summary_backlog_contract(
        packet, contract, template, output, matrix, checklist
    )
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "platform_input_contract_incomplete" in blockers

    # 4. current_status=present
    contract = contract_builder.make_feedback_summary_backlog_input_contract()
    contract["required_inputs"][0]["current_status"] = "present"
    report, blockers = validator.validate_feedback_summary_backlog_contract(
        packet, contract, template, output, matrix, checklist
    )
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "platform_input_contract_incomplete" in blockers

    # 5. Non-null value_ref
    contract = contract_builder.make_feedback_summary_backlog_input_contract()
    contract["required_inputs"][0]["value_ref"] = "some_ref"
    report, blockers = validator.validate_feedback_summary_backlog_contract(
        packet, contract, template, output, matrix, checklist
    )
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "platform_input_value_ref_present" in blockers

    # 6. raw_value_persisted=True
    contract = contract_builder.make_feedback_summary_backlog_input_contract()
    contract["required_inputs"][0]["raw_value_persisted"] = True
    report, blockers = validator.validate_feedback_summary_backlog_contract(
        packet, contract, template, output, matrix, checklist
    )
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "platform_input_raw_value_persisted" in blockers

    # 7. blocks_feedback_summary_backlog_creation=False
    contract = contract_builder.make_feedback_summary_backlog_input_contract()
    contract["required_inputs"][0]["blocks_feedback_summary_backlog_creation"] = False
    report, blockers = validator.validate_feedback_summary_backlog_contract(
        packet, contract, template, output, matrix, checklist
    )
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "platform_input_not_blocking_generation" in blockers


def test_validator_fails_on_template_fields():
    fields = [
        "feedback_summary_id", "backlog_item_id", "next_article_signal_id",
        "community_feedback_capture_ref", "redacted_feedback_records_ref",
        "feedback_capture_policy_ref", "feedback_summarization_policy_ref",
        "backlog_routing_policy_ref", "public_url_proof_ref", "platform_publication_id_ref",
        "audit_redaction_policy_ref", "request_payload_ref", "response_payload_ref",
        "operator_id_redacted", "operator_signature_redacted", "created_at_redacted",
        "feedback_summary_statement", "backlog_item_statement"
    ]
    for field in fields:
        packet = packet_builder.make_feedback_summary_backlog_packet()
        contract = contract_builder.make_feedback_summary_backlog_input_contract()
        template = coordinator.make_feedback_summary_backlog_blocked_template()
        output = coordinator.make_feedback_summary_backlog_blocked_output()
        matrix = coordinator.make_feedback_summary_backlog_gate_matrix()
        checklist = coordinator.make_feedback_summary_backlog_checklist()

        template[field] = "active_value"
        report, blockers = validator.validate_feedback_summary_backlog_contract(
            packet, contract, template, output, matrix, checklist
        )
        assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
        assert "non_null_feedback_template_fields_detected" in blockers


def test_validator_fails_on_output_lists_and_counts():
    output_lists = [
        "feedback_summaries", "backlog_items", "next_article_signals",
        "redacted_feedback_records", "comments", "reactions", "platform_metrics",
        "public_urls", "public_url_proofs", "platform_publication_ids",
        "citations", "evidence_refs", "source_names", "user_handles", "private_messages",
        "request_payloads", "response_payloads"
    ]
    for lst in output_lists:
        packet = packet_builder.make_feedback_summary_backlog_packet()
        contract = contract_builder.make_feedback_summary_backlog_input_contract()
        template = coordinator.make_feedback_summary_backlog_blocked_template()
        output = coordinator.make_feedback_summary_backlog_blocked_output()
        matrix = coordinator.make_feedback_summary_backlog_gate_matrix()
        checklist = coordinator.make_feedback_summary_backlog_checklist()

        output[lst] = ["active_value"]
        report, blockers = validator.validate_feedback_summary_backlog_contract(
            packet, contract, template, output, matrix, checklist
        )
        assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
        assert "non_empty_output_lists_detected" in blockers

    count_keys = [
        "feedback_summary_count", "backlog_item_count", "next_article_signal_count",
        "redacted_record_count", "comment_count", "reaction_count", "metric_count"
    ]
    for key in count_keys:
        packet = packet_builder.make_feedback_summary_backlog_packet()
        contract = contract_builder.make_feedback_summary_backlog_input_contract()
        template = coordinator.make_feedback_summary_backlog_blocked_template()
        output = coordinator.make_feedback_summary_backlog_blocked_output()
        matrix = coordinator.make_feedback_summary_backlog_gate_matrix()
        checklist = coordinator.make_feedback_summary_backlog_checklist()

        output[key] = 1
        report, blockers = validator.validate_feedback_summary_backlog_contract(
            packet, contract, template, output, matrix, checklist
        )
        assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
        assert "non_zero_word_or_variant_count_detected" in blockers


def test_validator_fails_on_matrix_active_lane():
    readiness_keys = [
        "community_feedback_capture_available",
        "redacted_feedback_records_available",
        "comments_available",
        "reactions_available",
        "metrics_available",
        "public_url_proof_available",
        "platform_publication_id_available",
        "feedback_summarization_policy_available",
        "backlog_routing_policy_available",
        "operator_summary_authorization_present",
        "jim_feedback_review_completed",
        "summary_generation_allowed",
        "summary_generation_performed",
        "backlog_item_creation_allowed",
        "backlog_item_created",
        "next_article_signal_created",
        "model_provider_call_performed",
        "provider_call_performed",
        "browser_session_started",
        "env_read_performed",
        "credentials_hydrated",
        "platform_api_request_performed",
        "webhook_request_performed",
        "scraping_performed",
        "audit_record_mutated",
        "live_write_attempted",
        "retry_attempted",
        "public_url_created"
    ]
    for rk in readiness_keys:
        packet = packet_builder.make_feedback_summary_backlog_packet()
        contract = contract_builder.make_feedback_summary_backlog_input_contract()
        template = coordinator.make_feedback_summary_backlog_blocked_template()
        output = coordinator.make_feedback_summary_backlog_blocked_output()
        matrix = coordinator.make_feedback_summary_backlog_gate_matrix()
        checklist = coordinator.make_feedback_summary_backlog_checklist()

        matrix[0][rk] = True
        report, blockers = validator.validate_feedback_summary_backlog_contract(
            packet, contract, template, output, matrix, checklist
        )
        assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
        assert "readiness_matrix_active_lane_detected" in blockers


def test_validator_fails_on_matrix_blocks_publication():
    packet = packet_builder.make_feedback_summary_backlog_packet()
    contract = contract_builder.make_feedback_summary_backlog_input_contract()
    template = coordinator.make_feedback_summary_backlog_blocked_template()
    output = coordinator.make_feedback_summary_backlog_blocked_output()
    matrix = coordinator.make_feedback_summary_backlog_gate_matrix()
    checklist = coordinator.make_feedback_summary_backlog_checklist()

    matrix[0]["blocks_publication"] = False
    report, blockers = validator.validate_feedback_summary_backlog_contract(
        packet, contract, template, output, matrix, checklist
    )
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "readiness_matrix_publication_unblocked_detected" in blockers


def test_validator_fails_on_matrix_status():
    packet = packet_builder.make_feedback_summary_backlog_packet()
    contract = contract_builder.make_feedback_summary_backlog_input_contract()
    template = coordinator.make_feedback_summary_backlog_blocked_template()
    output = coordinator.make_feedback_summary_backlog_blocked_output()
    matrix = coordinator.make_feedback_summary_backlog_gate_matrix()
    checklist = coordinator.make_feedback_summary_backlog_checklist()

    matrix[0]["summary_backlog_gate_status"] = "unblocked"
    report, blockers = validator.validate_feedback_summary_backlog_contract(
        packet, contract, template, output, matrix, checklist
    )
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "readiness_matrix_active_lane_detected" in blockers


def test_validator_fails_on_missing_row_blockers():
    packet = packet_builder.make_feedback_summary_backlog_packet()
    contract = contract_builder.make_feedback_summary_backlog_input_contract()
    template = coordinator.make_feedback_summary_backlog_blocked_template()
    output = coordinator.make_feedback_summary_backlog_blocked_output()
    matrix = coordinator.make_feedback_summary_backlog_gate_matrix()
    checklist = coordinator.make_feedback_summary_backlog_checklist()

    matrix[0]["blockers"] = []
    report, blockers = validator.validate_feedback_summary_backlog_contract(
        packet, contract, template, output, matrix, checklist
    )
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "readiness_matrix_active_lane_detected" in blockers


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
        ("Bloomberg", "source_name_leak_detected"),
        ("@user_handle", "user_handle_leak_detected"),
        ("summary: some summary text", "summary_text_leak_detected"),
        ("backlog: some backlog text", "backlog_text_leak_detected")
    ]
    for text, expected_blocker in leaks:
        packet = packet_builder.make_feedback_summary_backlog_packet()
        contract = contract_builder.make_feedback_summary_backlog_input_contract()
        template = coordinator.make_feedback_summary_backlog_blocked_template()
        output = coordinator.make_feedback_summary_backlog_blocked_output()
        matrix = coordinator.make_feedback_summary_backlog_gate_matrix()
        checklist = coordinator.make_feedback_summary_backlog_checklist()

        packet["feedback_summary_backlog_status"] = text
        report, blockers = validator.validate_feedback_summary_backlog_contract(
            packet, contract, template, output, matrix, checklist
        )
        assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
        assert expected_blocker in blockers


def test_no_forbidden_behavior_modules():
    import subprocess
    forbidden_modules = [
        "requests", "httpx", "urllib", "openai", "anthropic", "google.genai",
        "vertex", "discord", "telegram", "tweepy", "selenium", "playwright",
        "bs4", "scrapy"
    ]
    code = f"""
import sys
import importlib
try:
    importlib.import_module("live_contentops.feedback_summary_backlog_validator_v6")
except Exception as e:
    print(f"ImportError: {{e}}")
    sys.exit(1)
forbidden = {forbidden_modules}
found = [m for m in forbidden if m in sys.modules and sys.modules[m] is not None and m != "urllib"]
if found:
    print("FOUND_FORBIDDEN:" + ",".join(found))
    sys.exit(2)
sys.exit(0)
"""
    res = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert res.returncode == 0, f"Forbidden imports found or import failed. Output: {res.stdout.strip()}. Stderr: {res.stderr.strip()}"
