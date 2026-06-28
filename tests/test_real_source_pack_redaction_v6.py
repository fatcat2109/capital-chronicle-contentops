"""Test V6 Real Source Pack Redaction Policy."""
from __future__ import annotations

from live_contentops import real_source_pack_redaction_v6 as redaction_builder


def test_make_redaction_policy():
    policy = redaction_builder.make_redaction_policy()
    
    assert policy["never_persist_raw_source_url"] is True
    assert policy["never_persist_raw_evidence_hash"] is True
    assert policy["never_persist_raw_source_excerpt"] is True
    assert policy["never_persist_raw_operator_signature"] is True
    
    # Assert forbidden fields list is set
    assert "source_url" in policy["forbidden_raw_fields"]
    assert "evidence_hash" in policy["forbidden_raw_fields"]
    assert "operator_signature" in policy["forbidden_raw_fields"]
    
    # Assert blockers list is present
    assert "raw_source_url_persisted" in policy["violation_blockers"]
    assert "raw_evidence_hash_persisted" in policy["violation_blockers"]
