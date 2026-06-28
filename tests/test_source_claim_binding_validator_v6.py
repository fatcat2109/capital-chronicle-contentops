"""Test source-claim binding validator module."""
from __future__ import annotations

from live_contentops import source_claim_binding_validator_v6 as validator


def test_binding_missing_by_default():
    claims = [
        {"claim_id": "c1", "claim_text_draft": "Draft claim text", "source_requirement_refs": ["req_1"]}
    ]
    pack = {
        "source_entries": [
            {"source_requirement_id": "req_1", "verification_status": "missing"}
        ]
    }

    report = validator.generate_source_claim_binding_report(claims, pack)
    assert report["all_claims_bound_to_sources"] is False

    binding = report["bindings"][0]
    assert binding["source_support_status"] == "missing"
    assert binding["allowed_in_article_draft"] is False
    assert "source_verification_required" in binding["blockers"]


def test_binding_success_when_verified():
    claims = [
        {"claim_id": "c1", "claim_text_draft": "Draft claim text", "source_requirement_refs": ["req_1"]}
    ]
    pack = {
        "source_entries": [
            {"source_requirement_id": "req_1", "verification_status": "verified"}
        ]
    }

    report = validator.generate_source_claim_binding_report(claims, pack)
    assert report["all_claims_bound_to_sources"] is True

    binding = report["bindings"][0]
    assert binding["source_support_status"] == "verified"
    assert binding["allowed_in_article_draft"] is True
    assert len(binding["blockers"]) == 0
