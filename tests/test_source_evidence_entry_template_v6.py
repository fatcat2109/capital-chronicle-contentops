"""Test source evidence entry template module."""
from __future__ import annotations

from live_contentops import source_evidence_entry_template_v6 as temp


def test_generate_source_evidence_entry_template():
    entry = temp.generate_source_evidence_entry_template("req_1", "type_1")

    assert entry["source_requirement_id"] == "req_1"
    assert entry["required_source_type"] == "type_1"
    assert entry["source_name"] is None
    assert entry["source_url"] is None
    assert entry["evidence_hash"] is None
    assert entry["retrieval_method"] == "manual_operator_research_pending"
    assert entry["retrieved_at"] is None
    assert entry["source_excerpt_ref"] is None
    assert entry["verification_status"] == "missing"
    assert entry["allowed_for_article_use"] is False
