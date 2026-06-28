"""Test verified source pack fixture factory module."""
from __future__ import annotations

from live_contentops import verified_source_pack_fixture_factory_v6 as factory


def test_make_test_only_positive_verified_source_pack():
    pack = factory.make_test_only_positive_verified_source_pack()
    assert pack["test_only"] is True
    assert pack["runtime_truth"] is False
    assert pack["operator_verified_by"] == "TEST_ONLY_OPERATOR_NOT_REAL_VERIFICATION"
    assert pack["verified_source_pack_status"] == "TEST_ONLY_VERIFIED_FIXTURE"
    assert pack["source_pack_draft_status"] == "TEST_ONLY_VERIFIED_FIXTURE"
    assert pack["allowed_for_article_use"] is False
    assert pack["draft_generation_allowed"] is False
    assert pack["source_pack_complete"] is False
    assert len(pack["source_entries"]) == 0


def test_full_positive_path_validation_in_unit_tests():
    # Construct a fully populated positive fixture locally in the test only
    pos_pack = {
        "source_pack_draft_status": "VERIFIED_OPERATOR_INPUT_COMPLETE",
        "source_pack_complete": True,
        "all_required_sources_verified": True,
        "all_claims_bound_to_sources": True,
        "verified_source_pack_status": "VERIFIED",
        "source_claim_binding_pending": False,
        "allowed_for_article_use": True,
        "draft_generation_allowed": True,
        "human_review_required": True,
        "source_entries": [
            {
                "source_requirement_id": "req_67a5db6704f5",
                "required_source_type": "official_interest_rates",
                "source_name": "Test Treasury Release Service",
                "source_url": "https://test.treasury.gov/h15",
                "source_publisher": "Test Gov",
                "retrieval_method": "manual_operator_research_complete",
                "retrieved_at": "2026-06-28T12:00:00Z",
                "evidence_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                "source_excerpt_ref": "H.15 selected data",
                "source_excerpt_text_redacted": "Nominal yield curve details.",
                "source_supports_claim_ids": ["claim_d474a9fdbcd6", "claim_63d1cf20e9bf", "claim_492c29ad9746"],
                "limitations": "None",
                "caveats": "None",
                "operator_verified_by": "operator_test_sig",
                "verification_status": "verified",
                "allowed_for_article_use": True,
                "human_review_required": True,
                "source_verification_required": True
            }
        ]
    }

    from live_contentops import verified_source_pack_import_v6 as import_handler
    from live_contentops import source_pack_claim_binding_revalidator_v6 as binding_revalidator
    from live_contentops import verified_source_pack_revalidation_v6 as revalidation
    report, blockers = import_handler.validate_imported_source_pack(pos_pack)
    assert "fake_source_or_evidence_detected" not in blockers
    assert blockers == ["publication_blocked_until_source_verification"]

    claim_scaffold = [{"claim_id": "claim_d474a9fdbcd6", "source_requirement_refs": "req_67a5db6704f5"}]
    binding_report, all_bound = binding_revalidator.revalidate_source_claim_binding(pos_pack, claim_scaffold)
    assert all_bound is True

    gate_report = revalidation.run_gate_revalidation(pos_pack, all_bound, blockers)
    assert gate_report["gate_status"] == "PASSED_VERIFIED_SOURCE_PACK_VALID"
    assert gate_report["draft_copy_generation_allowed"] is True
