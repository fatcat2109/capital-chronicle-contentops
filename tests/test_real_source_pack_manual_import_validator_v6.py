"""Test V6 Real Source Pack Manual Import Validator."""
from __future__ import annotations

from live_contentops import real_source_pack_manual_import_validator_v6 as validator


def test_validator_required_blockers():
    fixture = {
        "import_fixture_status": "OPERATOR_MANUAL_SOURCE_PACK_REQUIRED",
        "runtime_truth": False,
        "real_source_pack_imported": False
    }
    hash_packet = {
        "hash_review_status": "WAITING_FOR_OPERATOR_SOURCE_PACK",
        "runtime_truth": False
    }
    policy = {
        "never_persist_raw_source_url": True
    }

    report, blockers = validator.validate_real_source_pack_manual_import(fixture, hash_packet, policy)

    assert report["validation_status"] == "PASSED_WITH_REVIEW_ONLY_BLOCKERS"
    assert "operator_source_pack_missing" in blockers
    assert "source_verification_required" in blockers
    assert "redacted_source_pack_required" in blockers
    assert "evidence_hash_presence_missing" in blockers
    assert "source_requirement_coverage_missing" in blockers
    assert "claim_binding_missing" in blockers
    assert "operator_signature_missing" in blockers
    assert "real_draft_generation_blocked" in blockers
    assert "publication_blocked_until_real_source_verification" in blockers
    assert "dispatch_blocked" in blockers
    assert "human_review_required" in blockers


def test_validator_blocks_generic_leaks():
    fixture = {
        "import_fixture_status": "OPERATOR_MANUAL_SOURCE_PACK_REQUIRED",
        "runtime_truth": True,  # Trigger
        "source_entries": [
            {"source_url": "https://example.org/source"}  # Leak
        ]
    }
    hash_packet = {
        "hash_review_status": "WAITING_FOR_OPERATOR_SOURCE_PACK",
        "runtime_truth": False
    }
    policy = {
        "never_persist_raw_source_url": True
    }

    report, blockers = validator.validate_real_source_pack_manual_import(fixture, hash_packet, policy)

    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "runtime_truth_claimed" in blockers
    assert "url_leak_in_runtime_artifact" in blockers


def test_validator_blocks_on_sensitive_operators_and_metrics():
    fixture = {
        "import_fixture_status": "OPERATOR_MANUAL_SOURCE_PACK_REQUIRED",
        "runtime_truth": False,
        "operator_id": "operator_jim_sig"  # signature leak keyword
    }
    hash_packet = {
        "hash_review_status": "WAITING_FOR_OPERATOR_SOURCE_PACK",
        "runtime_truth": False,
        "notes": "We had 500 clicks on the page"  # metric leak keyword
    }
    policy = {
        "never_persist_raw_source_url": True
    }

    report, blockers = validator.validate_real_source_pack_manual_import(fixture, hash_packet, policy)

    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "operator_signature_leaked" in blockers
    assert "metric_leak_detected" in blockers
