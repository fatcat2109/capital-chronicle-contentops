"""Test V6 Real Source Pack Redacted Fixture Validator."""
from __future__ import annotations

from live_contentops import real_source_pack_redacted_fixture_v6 as fixture_builder
from live_contentops import real_source_pack_redacted_fixture_review_v6 as review_mod
from live_contentops import real_source_pack_redacted_fixture_validator_v6 as validator
from live_contentops import real_source_pack_redaction_v6 as redaction_builder


def test_validator_passes_on_clean_redacted_fixture():
    fixture = fixture_builder.make_operator_filled_redacted_fixture()
    hash_presence = review_mod.make_redacted_hash_presence_review(len(fixture["source_entries"]))
    policy = redaction_builder.make_redaction_policy()

    report, blockers = validator.validate_real_source_pack_redacted_fixture(
        fixture, hash_presence, policy
    )

    assert report["validation_status"] == "PASSED_WITH_REVIEW_ONLY_BLOCKERS"
    assert "operator_source_approval_missing" in blockers
    assert "runtime_truth_false" in blockers
    assert "canonical_draft_generation_blocked" in blockers
    assert "publication_blocked_until_real_source_verification" in blockers
    assert "dispatch_blocked" in blockers
    assert "human_review_required" in blockers
    assert "source_verification_required" in blockers
    # Confirm no leak blockers
    assert "url_leak_in_runtime_artifact" not in blockers
    assert "hash_leak_in_runtime_artifact" not in blockers


def test_validator_fails_on_raw_data_leak():
    fixture = fixture_builder.make_operator_filled_redacted_fixture()
    # inject URL leak
    fixture["source_entries"][0]["source_url_redacted"] = "https://federalreserve.gov/yields"
    hash_presence = review_mod.make_redacted_hash_presence_review(len(fixture["source_entries"]))
    policy = redaction_builder.make_redaction_policy()

    report, blockers = validator.validate_real_source_pack_redacted_fixture(
        fixture, hash_presence, policy
    )

    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "url_leak_in_runtime_artifact" in blockers


def test_no_forbidden_imports_in_validator():
    import live_contentops.real_source_pack_redacted_fixture_validator_v6 as target_module
    attrs = dir(target_module)
    forbidden = ["urlopen", "requests", "httpx", "getenv", "environ", "openai", "anthropic", "google"]
    for f in forbidden:
        assert f not in attrs
