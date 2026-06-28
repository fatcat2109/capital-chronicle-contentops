"""Test V6 Canonical Draft Positive Path Validator."""
from __future__ import annotations

from live_contentops import canonical_draft_positive_path_validator_v6 as validator


def test_validator_clean_run():
    packet = {
        "positive_path_status": "READY_FOR_TEST_ONLY_DRY_RUN",
        "runtime_truth": False
    }
    fixture = {
        "test_only": True,
        "runtime_truth": False
    }
    bindings = [
        {"claim_id": "claim_001", "source_requirement_refs": ["req_001"]}
    ]
    draft_packet = {
        "canonical_draft_status": "REVIEW_ONLY_SYNTHETIC_POSITIVE_PATH",
        "runtime_truth": False
    }
    md = "# TEST-ONLY / NOT RUNTIME TRUTH\nMacroeconomic provenance tracked."

    report, blockers = validator.validate_positive_path_draft_generation(
        packet, fixture, bindings, draft_packet, md
    )

    assert report["validation_status"] == "PASSED_WITH_REVIEW_ONLY_BLOCKERS"
    assert "runtime_source_pack_not_verified" in blockers
    assert "publication_blocked_until_real_source_verification" in blockers


def test_validator_fails_on_forbidden_patterns():
    packet = {
        "runtime_truth": True
    }
    fixture = {
        "test_only": True,
        "runtime_truth": False
    }
    bindings = [
        {"claim_id": "claim_001", "source_requirement_refs": ["req_001"]}
    ]
    draft_packet = {
        "runtime_truth": False
    }
    # Has a forbidden word (buy) and a URL
    md = "We suggest to buy now. Source: https://treasury.gov"

    report, blockers = validator.validate_positive_path_draft_generation(
        packet, fixture, bindings, draft_packet, md
    )

    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "runtime_truth_claimed" in blockers
    assert "url_leak_in_runtime_artifact" in blockers
    assert "financial_advice_or_signal_language_detected" in blockers
