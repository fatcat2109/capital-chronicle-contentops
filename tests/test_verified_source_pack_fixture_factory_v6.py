"""Test verified source pack fixture factory module."""
from __future__ import annotations

from live_contentops import verified_source_pack_fixture_factory_v6 as factory


def test_make_test_only_positive_verified_source_pack():
    pack = factory.make_test_only_positive_verified_source_pack()
    assert pack["source_pack_draft_status"] == "VERIFIED_OPERATOR_INPUT_COMPLETE"
    assert pack["source_pack_complete"] is True
    assert pack["all_required_sources_verified"] is True
    assert pack["all_claims_bound_to_sources"] is True
    assert pack["verified_source_pack_status"] == "VERIFIED"
    assert len(pack["source_entries"]) == 1

    entry = pack["source_entries"][0]
    assert entry["verification_status"] == "verified"
    assert "https://www.federalreserve.gov" in entry["source_url"]
    assert entry["operator_verified_by"] == "operator_jim_sig"
