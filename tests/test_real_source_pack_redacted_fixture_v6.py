"""Test V6 Real Source Pack Operator-Filled Redacted Fixture."""
from __future__ import annotations

from live_contentops import real_source_pack_redacted_fixture_v6 as fixture_builder


def test_redacted_fixture_structure():
    fixture = fixture_builder.make_operator_filled_redacted_fixture()
    
    assert fixture["fixture_status"] == "REDACTED_OPERATOR_FILLED_DRY_RUN_REVIEW"
    assert fixture["runtime_truth"] is False
    assert fixture["real_source_pack_imported"] is False
    assert fixture["operator_filled_redacted_fixture"] is True
    assert fixture["raw_values_persisted"] is False
    assert len(fixture["source_entries"]) == 5

    for entry in fixture["source_entries"]:
        assert entry["source_name_redacted"] == "REDACTED_SOURCE_NAME_PRESENT"
        assert entry["source_url_redacted"] == "REDACTED_SOURCE_URL_PRESENT"
        assert entry["source_publisher_redacted"] == "REDACTED_SOURCE_PUBLISHER_PRESENT"
        assert entry["evidence_hash_present"] is True
        assert entry["evidence_hash_redacted"] == "REDACTED_EVIDENCE_HASH_PRESENT"
        assert entry["source_excerpt_ref_redacted"] == "REDACTED_EXCERPT_REF_PRESENT"
        assert entry["source_excerpt_text_redacted"] == "REDACTED_EXCERPT_TEXT_PRESENT"
        assert entry["operator_verified_by_redacted"] == "REDACTED_OPERATOR_SIGNATURE_PRESENT"
        assert entry["verification_status"] == "redacted_presence_only_not_approved"
        assert entry["allowed_for_article_use"] is False
        assert entry["raw_values_persisted"] is False
        assert entry["runtime_truth"] is False
