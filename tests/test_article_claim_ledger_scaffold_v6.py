"""Test article claim ledger scaffold module."""
from __future__ import annotations

from live_contentops import article_claim_ledger_scaffold_v6 as claims


def test_generate_claim_ledger_scaffold():
    reqs = [
        {"research_requirement_id": "req_1", "required_source_type": "treasury_yield_series"},
        {"research_requirement_id": "req_2", "required_source_type": "yield_curve_calculation"},
        {"research_requirement_id": "req_3", "required_source_type": "historical_volatility"}
    ]

    scaffold = claims.generate_claim_ledger_scaffold(reqs)
    assert len(scaffold) == 3

    for c in scaffold:
        assert c["verification_status"] == "unverified"
        assert c["allowed_in_public_draft"] is False
        assert c["needs_human_review"] is True
        assert c["no_numeric_truth_invented"] is True
        assert c["no_forward_signal"] is True
        assert len(c["source_requirement_refs"]) > 0
        assert c["source_requirement_refs"][0] in ["req_1", "req_2", "req_3"]
