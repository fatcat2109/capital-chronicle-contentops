"""Test V6 Canonical Draft Eligibility Validator."""
from __future__ import annotations

from live_contentops import canonical_draft_eligibility_packet_v6 as packet_builder
from live_contentops import approved_redacted_source_pack_test_fixture_v6 as summary_builder
from live_contentops import canonical_draft_from_approved_redacted_source_pack_v6 as coordinator
from live_contentops import canonical_draft_eligibility_validator_v6 as validator


def test_validator_passes_on_clean_simulated_state():
    packet = packet_builder.make_canonical_draft_eligibility_packet()
    summary = summary_builder.make_approved_redacted_source_pack_summary()
    matrix = coordinator.make_claim_eligibility_matrix()
    preview = coordinator.make_generation_blocked_preview()

    report, blockers = validator.validate_canonical_draft_eligibility(
        packet, summary, matrix, preview
    )

    assert report["validation_status"] == "PASSED_WITH_REVIEW_ONLY_BLOCKERS"
    assert "runtime_operator_approval_missing" in blockers
    assert "real_source_pack_not_approved" in blockers
    assert "runtime_draft_generation_blocked" in blockers
    assert "article_copy_generation_blocked" in blockers
    assert "publication_blocked" in blockers
    assert "dispatch_blocked" in blockers
    assert "human_review_required" in blockers


def test_validator_fails_on_active_runtime_approval():
    packet = packet_builder.make_canonical_draft_eligibility_packet()
    packet["real_source_pack_approved"] = True  # Leak/active approval
    summary = summary_builder.make_approved_redacted_source_pack_summary()
    matrix = coordinator.make_claim_eligibility_matrix()
    preview = coordinator.make_generation_blocked_preview()

    report, blockers = validator.validate_canonical_draft_eligibility(
        packet, summary, matrix, preview
    )

    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "real_source_pack_approved_claimed" in blockers


def test_validator_fails_on_raw_secret_leak():
    packet = packet_builder.make_canonical_draft_eligibility_packet()
    summary = summary_builder.make_approved_redacted_source_pack_summary()
    summary["notes"] = "Here is operator_jim_sig leaked"  # Leak keyword
    matrix = coordinator.make_claim_eligibility_matrix()
    preview = coordinator.make_generation_blocked_preview()

    report, blockers = validator.validate_canonical_draft_eligibility(
        packet, summary, matrix, preview
    )

    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "operator_signature_leaked" in blockers


def test_validator_fails_on_financial_advice_leaked():
    packet = packet_builder.make_canonical_draft_eligibility_packet()
    summary = summary_builder.make_approved_redacted_source_pack_summary()
    matrix = coordinator.make_claim_eligibility_matrix()
    preview = coordinator.make_generation_blocked_preview() + "\nThis is a buy signal!" # advice

    report, blockers = validator.validate_canonical_draft_eligibility(
        packet, summary, matrix, preview
    )

    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "financial_advice_or_signal_language_detected" in blockers


def test_no_forbidden_imports_in_validator():
    import live_contentops.canonical_draft_eligibility_validator_v6 as target_module
    attrs = dir(target_module)
    forbidden = ["urlopen", "requests", "httpx", "getenv", "environ", "openai", "anthropic", "google"]
    for f in forbidden:
        assert f not in attrs


def test_validator_fails_on_source_name_leak():
    packet = packet_builder.make_canonical_draft_eligibility_packet()
    summary = summary_builder.make_approved_redacted_source_pack_summary()
    matrix = coordinator.make_claim_eligibility_matrix()
    preview = coordinator.make_generation_blocked_preview()
    # leak in packet
    packet["source_name"] = "Federal Reserve"

    report, blockers = validator.validate_canonical_draft_eligibility(
        packet, summary, matrix, preview
    )
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "source_name_leak_detected" in blockers


def test_validator_fails_on_source_publisher_leak():
    packet = packet_builder.make_canonical_draft_eligibility_packet()
    summary = summary_builder.make_approved_redacted_source_pack_summary()
    matrix = coordinator.make_claim_eligibility_matrix()
    preview = coordinator.make_generation_blocked_preview()
    # leak in summary
    summary["source_publisher"] = "US Treasury"

    report, blockers = validator.validate_canonical_draft_eligibility(
        packet, summary, matrix, preview
    )
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "source_name_leak_detected" in blockers


def test_validator_fails_on_preview_source_name_leak():
    packet = packet_builder.make_canonical_draft_eligibility_packet()
    summary = summary_builder.make_approved_redacted_source_pack_summary()
    matrix = coordinator.make_claim_eligibility_matrix()
    preview = coordinator.make_generation_blocked_preview() + "\nSource name: Federal Reserve"

    report, blockers = validator.validate_canonical_draft_eligibility(
        packet, summary, matrix, preview
    )
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "source_name_leak_detected" in blockers


def test_validator_does_not_fail_on_safe_references():
    packet = packet_builder.make_canonical_draft_eligibility_packet()
    summary = summary_builder.make_approved_redacted_source_pack_summary()
    matrix = coordinator.make_claim_eligibility_matrix()
    # Safe fields in matrix
    matrix[0]["source_requirement_refs"] = ["req_e6edaf8e7750"]
    matrix[0]["blockers"] = ["raw_source_values_not_available_for_model"]
    preview = coordinator.make_generation_blocked_preview()

    report, blockers = validator.validate_canonical_draft_eligibility(
        packet, summary, matrix, preview
    )
    assert report["validation_status"] == "PASSED_WITH_REVIEW_ONLY_BLOCKERS"
    assert "source_name_leak_detected" not in blockers


def test_validator_fails_on_arbitrary_url():
    packet = packet_builder.make_canonical_draft_eligibility_packet()
    summary = summary_builder.make_approved_redacted_source_pack_summary()
    matrix = coordinator.make_claim_eligibility_matrix()
    preview = coordinator.make_generation_blocked_preview() + "\nSee https://example.com/data"

    report, blockers = validator.validate_canonical_draft_eligibility(
        packet, summary, matrix, preview
    )
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "url_leak_in_runtime_artifact" in blockers


def test_validator_fails_on_64_char_hash():
    packet = packet_builder.make_canonical_draft_eligibility_packet()
    summary = summary_builder.make_approved_redacted_source_pack_summary()
    matrix = coordinator.make_claim_eligibility_matrix()
    preview = coordinator.make_generation_blocked_preview() + "\nHash: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

    report, blockers = validator.validate_canonical_draft_eligibility(
        packet, summary, matrix, preview
    )
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "hash_leak_in_runtime_artifact" in blockers


def test_validator_fails_on_sha256_prefix():
    packet = packet_builder.make_canonical_draft_eligibility_packet()
    summary = summary_builder.make_approved_redacted_source_pack_summary()
    matrix = coordinator.make_claim_eligibility_matrix()
    preview = coordinator.make_generation_blocked_preview() + "\nsha256:abcd"

    report, blockers = validator.validate_canonical_draft_eligibility(
        packet, summary, matrix, preview
    )
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "hash_leak_in_runtime_artifact" in blockers


def test_validator_fails_on_citation_marker():
    packet = packet_builder.make_canonical_draft_eligibility_packet()
    summary = summary_builder.make_approved_redacted_source_pack_summary()
    matrix = coordinator.make_claim_eligibility_matrix()
    preview = coordinator.make_generation_blocked_preview() + "\nAs seen in [1]"

    report, blockers = validator.validate_canonical_draft_eligibility(
        packet, summary, matrix, preview
    )
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "citation_or_source_reference_leak_detected" in blockers


def test_validator_fails_on_source_excerpt():
    packet = packet_builder.make_canonical_draft_eligibility_packet()
    summary = summary_builder.make_approved_redacted_source_pack_summary()
    matrix = coordinator.make_claim_eligibility_matrix()
    preview = coordinator.make_generation_blocked_preview() + "\nExcerpt: the yield curve inverted"

    report, blockers = validator.validate_canonical_draft_eligibility(
        packet, summary, matrix, preview
    )
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "source_excerpt_leak_in_runtime_artifact" in blockers


def test_validator_fails_on_metric_term():
    packet = packet_builder.make_canonical_draft_eligibility_packet()
    summary = summary_builder.make_approved_redacted_source_pack_summary()
    matrix = coordinator.make_claim_eligibility_matrix()
    preview = coordinator.make_generation_blocked_preview() + "\nCTR was 5%"

    report, blockers = validator.validate_canonical_draft_eligibility(
        packet, summary, matrix, preview
    )
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "metric_leak_detected" in blockers


def test_validator_fails_on_public_ready_phrase():
    packet = packet_builder.make_canonical_draft_eligibility_packet()
    summary = summary_builder.make_approved_redacted_source_pack_summary()
    matrix = coordinator.make_claim_eligibility_matrix()
    preview = coordinator.make_generation_blocked_preview() + "\nThis is ready_to_publish"

    report, blockers = validator.validate_canonical_draft_eligibility(
        packet, summary, matrix, preview
    )
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "public_ready_claim_detected" in blockers


def test_validator_fails_on_active_dispatch_flags():
    packet = packet_builder.make_canonical_draft_eligibility_packet()
    packet["public_postable"] = True
    summary = summary_builder.make_approved_redacted_source_pack_summary()
    matrix = coordinator.make_claim_eligibility_matrix()
    preview = coordinator.make_generation_blocked_preview()

    report, blockers = validator.validate_canonical_draft_eligibility(
        packet, summary, matrix, preview
    )
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "forbidden_active_dispatch_flags" in blockers

