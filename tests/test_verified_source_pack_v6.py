"""Test verified source pack schemas and default missing generators."""
from __future__ import annotations

from live_contentops import verified_source_pack_v6 as sp


def test_verified_source_pack_schema():
    schema = sp.get_verified_source_pack_schema()
    assert "properties" in schema
    assert "verified_source_pack_status" in schema["properties"]
    assert "source_entries" in schema["properties"]


def test_generate_default_missing_source_pack():
    reqs = [
        {"research_requirement_id": "req_1", "required_source_type": "type_1", "source_name_placeholder": "Name 1"}
    ]

    pack = sp.generate_default_missing_source_pack(reqs)
    assert pack["verified_source_pack_status"] == "MISSING_REQUIRED_SOURCE_VERIFICATION"
    assert pack["source_pack_complete"] is False
    assert pack["human_research_required"] is True
    assert pack["source_verification_required"] is True
    assert len(pack["source_entries"]) == 1

    entry = pack["source_entries"][0]
    assert entry["source_requirement_id"] == "req_1"
    assert entry["required_source_type"] == "type_1"
    assert entry["source_name"] == "Name 1"
    assert entry["source_url"] is None
    assert entry["verification_status"] == "missing"
    assert entry["allowed_for_article_use"] is False
