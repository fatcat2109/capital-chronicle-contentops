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
