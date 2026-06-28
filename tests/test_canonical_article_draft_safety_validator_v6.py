"""Test canonical article draft safety validator rules."""
from __future__ import annotations

from live_contentops import canonical_article_draft_safety_validator_v6 as validator


def test_validator_detects_secrets_or_dms():
    draft = {"article_copy_generated": False}
    pack = {"verified_source_pack_status": "MISSING_REQUIRED_SOURCE_VERIFICATION"}
    gate = {"gate_status": "BLOCKED_MISSING_VERIFIED_SOURCE_PACK"}
    binding = {"all_claims_bound_to_sources": False}

    # Secrets trigger
    report, blockers = validator.validate_article_draft(
        draft, pack, gate, binding, "This has secret cookie and session details."
    )
    assert "private_or_secret_material_detected" in blockers

    # DM trigger
    report, blockers = validator.validate_article_draft(
        draft, pack, gate, binding, "Please read the private DM message."
    )
    assert "dm_or_private_message_detected" in blockers


def test_validator_detects_financial_advice_or_fake_urls():
    draft = {"article_copy_generated": False}
    pack = {
        "verified_source_pack_status": "COMPLETE",
        "source_entries": [
            {"source_requirement_id": "req_1", "source_url": "https://fakeurl.com", "verification_status": "verified"}
        ]
    }
    gate = {"gate_status": "PASSED"}
    binding = {"all_claims_bound_to_sources": True}

    report, blockers = validator.validate_article_draft(
        draft, pack, gate, binding, "This draft says we should buy yield positions."
    )
    assert "fake_source_or_citation_detected" in blockers
    assert "financial_advice_or_signal_language_detected" in blockers
    assert report["safety_checks"]["no_financial_advice_language"] is False
    assert "buy" in report["financial_advice_matches"]


def test_validator_false_positive_shielding():
    draft = {"article_copy_generated": False}
    pack = {"verified_source_pack_status": "MISSING_REQUIRED_SOURCE_VERIFICATION"}
    gate = {"gate_status": "BLOCKED_MISSING_VERIFIED_SOURCE_PACK"}
    binding = {"all_claims_bound_to_sources": False}

    # Verify safe substrings inside other words do NOT trigger advice flag
    report, blockers = validator.validate_article_draft(
        draft, pack, gate, binding, "This Placeholder is for a shareholder on the threshold. Do not uphold a holding pattern."
    )
    assert "financial_advice_or_signal_language_detected" not in blockers
    assert report["safety_checks"]["no_financial_advice_language"] is True
    assert report["financial_advice_matches"] == []
