"""Test source pack draft validator rules."""
from __future__ import annotations

from live_contentops import source_pack_draft_validator_v6 as validator


def test_validator_detects_fakes_or_missing_fields():
    # 1. Draft is incomplete by default
    pack = {
        "source_pack_complete": False,
        "verified_source_pack_status": "MISSING_REQUIRED_SOURCE_VERIFICATION",
        "source_claim_binding_pending": True,
        "source_entries": [
            {
                "source_requirement_id": "req_1",
                "verification_status": "missing",
                "source_url": None,
                "evidence_hash": None
            }
        ]
    }

    report, blockers = validator.validate_source_pack_draft(pack)
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "operator_source_entries_missing" in blockers
    assert "source_verification_required" in blockers
    assert "claim_binding_missing" in blockers
    assert "source_url_missing" in blockers
    assert "evidence_hash_missing" in blockers
    assert "retrieved_at_missing" in blockers
    assert "operator_signature_missing" in blockers
    assert "source_excerpt_ref_missing" in blockers
    assert report["safety_checks"]["verified_fields_complete"] is False
    assert report["missing_required_field_counts"] == 5

    # 2. Re-test with a faked URL entry
    pack = {
        "source_pack_complete": True,
        "verified_source_pack_status": "COMPLETE",
        "source_claim_binding_pending": False,
        "source_entries": [
            {
                "source_requirement_id": "req_1",
                "verification_status": "verified",
                "source_url": "https://example.com/fake-treasury-yields",
                "evidence_hash": "stub_hash_123",
                "retrieved_at": "2026-06-28T12:00:00Z",
                "operator_verified_by": "operator_jim_sig",
                "source_excerpt_ref": "yield data excerpt"
            }
        ]
    }
    report, blockers = validator.validate_source_pack_draft(pack)
    assert "fake_source_or_evidence_detected" in blockers
    assert "source_url_missing" in blockers
    assert "evidence_hash_missing" in blockers


def test_validator_detects_missing_mandatory_attributes_on_verified():
    pack = {
        "source_pack_complete": True,
        "verified_source_pack_status": "COMPLETE",
        "source_claim_binding_pending": False,
        "source_entries": [
            {
                "source_requirement_id": "req_1",
                "verification_status": "verified",
                "source_url": "https://official-treasury.gov",
                "evidence_hash": "sha256_ab091c3",
                "retrieved_at": None,  # missing
                "operator_verified_by": None,  # missing
                "source_excerpt_ref": None  # missing
            }
        ]
    }
    report, blockers = validator.validate_source_pack_draft(pack)
    assert "retrieved_at_missing" in blockers
    assert "operator_signature_missing" in blockers
    assert "source_excerpt_ref_missing" in blockers
