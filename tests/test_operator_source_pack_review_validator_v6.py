"""Test V6 Operator Source Pack Review Validator."""
from __future__ import annotations

from live_contentops import operator_source_pack_review_validator_v6 as validator


def test_validator_required_blockers():
    packet = {
        "review_status": "OPERATOR_SOURCE_PACK_REVIEW_REQUIRED",
        "runtime_truth": False,
        "real_source_pack_imported": False
    }
    checklist = []
    template = {
        "valid_for_draft_generation": False,
        "valid_for_publication": False,
        "valid_for_dispatch": False
    }
    html = "<html></html>"

    report, blockers = validator.validate_operator_source_pack_review(packet, checklist, template, html)

    assert report["validation_status"] == "PASSED_WITH_REVIEW_ONLY_BLOCKERS"
    assert "operator_source_pack_missing" in blockers
    assert "operator_signature_missing" in blockers
    assert "source_verification_required" in blockers
    assert "source_url_missing" in blockers
    assert "evidence_hash_missing" in blockers
    assert "retrieved_at_missing" in blockers
    assert "source_excerpt_ref_missing" in blockers
    assert "claim_binding_missing" in blockers
    assert "real_draft_generation_blocked" in blockers
    assert "publication_blocked_until_real_source_verification" in blockers
    assert "dispatch_blocked" in blockers
    assert "human_review_required" in blockers


def test_validator_blocks_on_sensitive_leaks():
    packet = {
        "review_status": "OPERATOR_SOURCE_PACK_REVIEW_REQUIRED",
        "runtime_truth": True  # Forbidden
    }
    checklist = [
        {"checklist_item_id": "item_1", "notes": "We suggest to buy some options."}  # Financial advice keyword
    ]
    template = {
        "valid_for_draft_generation": False,
        "valid_for_publication": False,
        "valid_for_dispatch": False
    }
    # Has a forbidden URL and signature keyword
    html = "<html>Link to federalreserve.gov by operator_jim_sig</html>"

    report, blockers = validator.validate_operator_source_pack_review(packet, checklist, template, html)

    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "runtime_truth_claimed" in blockers
    assert "financial_advice_or_signal_language_detected" in blockers
    assert "operator_signature_leaked" in blockers
    assert "url_leak_in_runtime_artifact" in blockers
