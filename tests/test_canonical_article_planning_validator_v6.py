"""Test canonical article planning validator rules."""
from __future__ import annotations

from live_contentops import canonical_article_planning_validator_v6 as validator


def test_validator_clean():
    packet = {
        "article_packet_id": "art_123",
        "title_candidate": "Safe Title",
        "thesis_candidate": "Safe Thesis"
    }
    reqs = [
        {"research_requirement_id": "req_1", "required_source_type": "type_1", "source_url_placeholder": None, "source_verification_status": "missing"}
    ]
    checklist_data = {"requirements_validated": False}
    claims = [
        {"claim_id": "c1", "source_requirement_refs": ["req_1"]}
    ]
    outline = {
        "title_candidate": "Safe title",
        "section_outline": ["Safe section"]
    }
    risks = []
    placeholders = {
        "substack_canonical_article_draft_pending": {"generated": False}
    }

    report, blockers = validator.validate_article_planning(
        packet, reqs, checklist_data, claims, outline, risks, placeholders
    )

    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "source_verification_required" in blockers
    assert "publication_blocked_until_source_verification" in blockers
    assert "claim_ledger_unverified" in blockers
    assert "article_copy_not_generated" in blockers


def test_validator_detects_unsafe_advice():
    packet = {
        "article_packet_id": "art_123",
        "title_candidate": "Let's check the buy target prices",
        "thesis_candidate": "Safe Thesis"
    }
    reqs = []
    checklist_data = {}
    claims = []
    outline = {}
    risks = []
    placeholders = {}

    _, blockers = validator.validate_article_planning(
        packet, reqs, checklist_data, claims, outline, risks, placeholders
    )

    assert "financial_advice_or_signal_language_detected" in blockers


def test_validator_detects_private_data():
    packet = {
        "article_packet_id": "art_123",
        "title_candidate": "Safe title",
        "thesis_candidate": "Check the private DM from john_smith"
    }
    reqs = []
    checklist_data = {}
    claims = []
    outline = {}
    risks = []
    placeholders = {}

    _, blockers = validator.validate_article_planning(
        packet, reqs, checklist_data, claims, outline, risks, placeholders
    )

    assert "private_or_secret_material_detected" in blockers
    assert "dm_or_private_message_detected" in blockers


def test_validator_detects_empty_claims_or_fake_citations():
    packet = {
        "article_packet_id": "art_123",
        "title_candidate": "Safe title",
        "thesis_candidate": "Safe thesis"
    }
    reqs = [
        {"research_requirement_id": "req_1", "required_source_type": "type_1", "source_url_placeholder": "https://fakeurl.com", "source_verification_status": "verified"}
    ]
    checklist_data = {}
    claims = [
        {"claim_id": "c1", "source_requirement_refs": []}
    ]
    outline = {}
    risks = []
    placeholders = {}

    _, blockers = validator.validate_article_planning(
        packet, reqs, checklist_data, claims, outline, risks, placeholders
    )

    assert "fake_source_or_citation_detected" in blockers
    assert "unsupported_numeric_claim_slot_detected" in blockers
