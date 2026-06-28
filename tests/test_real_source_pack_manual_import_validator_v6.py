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
        "runtime_truth": False
    }
    hash_packet = {
        "hash_review_status": "WAITING_FOR_OPERATOR_SOURCE_PACK",
        "runtime_truth": False
    }
    policy = {
        "never_persist_raw_source_url": True
    }

    # 1. URL leak
    fixture_url = {**fixture, "some_url": "https://example.org/source"}
    report, blockers = validator.validate_real_source_pack_manual_import(fixture_url, hash_packet, policy)
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "url_leak_in_runtime_artifact" in blockers

    # 2. 64-char hash
    fixture_hash = {**fixture, "some_hash": "a" * 64}
    report, blockers = validator.validate_real_source_pack_manual_import(fixture_hash, hash_packet, policy)
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "hash_leak_in_runtime_artifact" in blockers

    # sha256 prefix format
    fixture_sha = {**fixture, "some_sha": "sha256:12345abcdef"}
    report, blockers = validator.validate_real_source_pack_manual_import(fixture_sha, hash_packet, policy)
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "hash_leak_in_runtime_artifact" in blockers

    # 3. Citation markers
    fixture_cit = {**fixture, "text": "This claims [1] citation."}
    report, blockers = validator.validate_real_source_pack_manual_import(fixture_cit, hash_packet, policy)
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "citation_or_source_reference_leak_detected" in blockers

    # 4. Non-placeholder excerpt
    fixture_exc = {**fixture, "source_excerpt_text": "Real raw excerpt content here."}
    report, blockers = validator.validate_real_source_pack_manual_import(fixture_exc, hash_packet, policy)
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "source_excerpt_leak_in_runtime_artifact" in blockers

    # 5. Non-null operator signature
    fixture_op = {**fixture, "operator_id": "jim"}
    report, blockers = validator.validate_real_source_pack_manual_import(fixture_op, hash_packet, policy)
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "operator_signature_leaked" in blockers

    # 6. Non-null timestamp / ISO text
    fixture_ts = {**fixture, "approved_at": "2026-06-28T12:00:00Z"}
    report, blockers = validator.validate_real_source_pack_manual_import(fixture_ts, hash_packet, policy)
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "fake_approval_timestamp_detected" in blockers

    # 7. Metrics
    fixture_metric = {**fixture, "notes": "We had 500 impressions."}
    report, blockers = validator.validate_real_source_pack_manual_import(fixture_metric, hash_packet, policy)
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "metric_leak_detected" in blockers

    # 8. Public-ready
    fixture_ready = {**fixture, "status": "ready_to_publish"}
    report, blockers = validator.validate_real_source_pack_manual_import(fixture_ready, hash_packet, policy)
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "public_ready_claim_detected" in blockers


def test_validator_blocks_imported_misuse():
    fixture = {
        "import_fixture_status": "OPERATOR_MANUAL_SOURCE_PACK_REQUIRED",
        "runtime_truth": False,
        "real_source_pack_imported": True,
        "raw_values_persisted": True  # Failure condition
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
    assert "real_source_pack_import_requires_redacted_review" in blockers


def test_validator_blocks_source_pack_complete_misuse():
    fixture = {
        "import_fixture_status": "OPERATOR_MANUAL_SOURCE_PACK_REQUIRED",
        "runtime_truth": False,
        "source_pack_complete": True,
        "all_required_sources_verified": False  # Failure condition
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
    assert "source_pack_complete_without_coverage" in blockers


def test_validator_blocks_article_use_approval_separation():
    fixture = {
        "import_fixture_status": "OPERATOR_MANUAL_SOURCE_PACK_REQUIRED",
        "runtime_truth": False,
        "allowed_for_article_use": True  # Failure condition
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
    assert "source_approval_missing" in blockers


def test_validator_harmless_redacted_labels():
    fixture = {
        "import_fixture_status": "OPERATOR_MANUAL_SOURCE_PACK_REQUIRED",
        "runtime_truth": False,
        "source_url_redacted": "Redacted: URL Presence Verified",
        "evidence_hash_redacted": "Redacted: Evidence Hash Verified",
        "source_excerpt_ref_redacted": "Redacted: Excerpt Verified",
        "source_excerpt_text_redacted": "Redacted: Excerpt Content Verified",
        "operator_verified_by_redacted": "Redacted: Operator Verified",
        "retrieved_at_redacted": "Redacted: Timestamp Verified",
        "evidence_hash_present": True
    }
    hash_packet = {
        "hash_review_status": "WAITING_FOR_OPERATOR_SOURCE_PACK",
        "runtime_truth": False,
        "redacted_hash_presence_only": True
    }
    policy = {
        "never_persist_raw_source_url": True
    }

    report, blockers = validator.validate_real_source_pack_manual_import(fixture, hash_packet, policy)

    assert report["validation_status"] == "PASSED_WITH_REVIEW_ONLY_BLOCKERS"
    assert "url_leak_in_runtime_artifact" not in blockers
    assert "hash_leak_in_runtime_artifact" not in blockers
    assert "operator_signature_leaked" not in blockers
    assert "fake_approval_timestamp_detected" not in blockers


def test_no_forbidden_imports_in_validator():
    import live_contentops.real_source_pack_manual_import_validator_v6 as target_module
    attrs = dir(target_module)
    forbidden = ["urlopen", "requests", "httpx", "getenv", "environ", "openai", "anthropic", "google"]
    for f in forbidden:
        assert f not in attrs
