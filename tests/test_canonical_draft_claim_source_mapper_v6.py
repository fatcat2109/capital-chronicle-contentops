"""Test V6 Canonical Draft Claim-Source Mapper."""
from __future__ import annotations

from live_contentops import canonical_draft_claim_source_mapper_v6 as mapper


def test_map_claims_to_test_only_sources():
    claims = [
        {"claim_id": "claim_d474a9fdbcd6", "source_requirement_refs": ["req_67a5db6704f5"]},
        {"claim_id": "claim_63d1cf20e9bf", "source_requirement_refs": ["req_bfcb46cc38cc"]}
    ]
    requirements = [
        {"research_requirement_id": "req_67a5db6704f5"},
        {"research_requirement_id": "req_bfcb46cc38cc"}
    ]

    bindings = mapper.map_claims_to_test_only_sources(claims, requirements)

    assert len(bindings) == 2
    assert bindings[0]["claim_id"] == "claim_d474a9fdbcd6"
    assert bindings[0]["source_requirement_refs"] == ["req_67a5db6704f5"]
    assert bindings[0]["source_support_status"] == "test_only_bound"
    assert bindings[0]["allowed_in_review_draft"] is True
    assert bindings[0]["allowed_in_publication"] is False
    assert bindings[0]["runtime_truth"] is False
