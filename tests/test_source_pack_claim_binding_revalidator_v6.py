"""Test source pack claim binding revalidator."""
from __future__ import annotations

from live_contentops import source_pack_claim_binding_revalidator_v6 as revalidator


def test_revalidate_source_claim_binding():
    # 1. Test missing draft
    draft = {
        "source_pack_complete": False,
        "verified_source_pack_status": "MISSING_REQUIRED_SOURCE_VERIFICATION",
        "source_entries": []
    }
    scaffold = [
        {"claim_id": "claim_1", "source_requirement_refs": "req_1"}
    ]

    report, all_bound = revalidator.revalidate_source_claim_binding(draft, scaffold)
    assert all_bound is False
    assert report["all_claims_bound_to_sources"] is False
    assert len(report["rebound_claims"]) == 1
    assert "claim_binding_missing" in report["rebound_claims"][0]["blockers"]

    # 2. Test successful synthetic match
    valid_pack = {
        "source_pack_complete": True,
        "verified_source_pack_status": "VERIFIED",
        "source_entries": [
            {
                "verification_status": "verified",
                "source_supports_claim_ids": ["claim_1"]
            }
        ]
    }
    report, all_bound = revalidator.revalidate_source_claim_binding(valid_pack, scaffold)
    assert all_bound is True
    assert report["all_claims_bound_to_sources"] is True
    assert report["rebound_claims"][0]["source_support_status"] == "verified"
    assert report["rebound_claims"][0]["allowed_in_article_draft"] is True
