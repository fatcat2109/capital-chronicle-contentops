"""Test V6 Operator Source Pack Review Validator."""
from __future__ import annotations

import json
from pathlib import Path
from live_contentops import operator_source_pack_review_validator_v6 as validator
from live_contentops import project_sources_upload_bundle_v6 as upload_lane


def test_validator_required_blockers():
    packet = {
        "review_status": "OPERATOR_SOURCE_PACK_REVIEW_REQUIRED",
        "runtime_truth": False,
        "real_source_pack_imported": False
    }
    checklist = []
    template = {
        "valid_for_draft_generation": False,
        "valid_for_publication": False,
        "valid_for_dispatch": False
    }
    html = "<html></html>"

    report, blockers = validator.validate_operator_source_pack_review(packet, checklist, template, html)

    assert report["validation_status"] == "PASSED_WITH_REVIEW_ONLY_BLOCKERS"
    assert "operator_source_pack_missing" in blockers
    assert "operator_signature_missing" in blockers
    assert "source_verification_required" in blockers
    assert "source_url_missing" in blockers
    assert "evidence_hash_missing" in blockers
    assert "retrieved_at_missing" in blockers
    assert "source_excerpt_ref_missing" in blockers
    assert "claim_binding_missing" in blockers
    assert "real_draft_generation_blocked" in blockers
    assert "publication_blocked_until_real_source_verification" in blockers
    assert "dispatch_blocked" in blockers
    assert "human_review_required" in blockers


def test_validator_generic_leaks():
    packet = {
        "review_status": "OPERATOR_SOURCE_PACK_REVIEW_REQUIRED",
        "runtime_truth": False
    }
    template = {
        "valid_for_draft_generation": False,
        "valid_for_publication": False,
        "valid_for_dispatch": False
    }

    # 1. URL leak
    checklist_url = [{"checklist_item_id": "item_1", "source_url": "https://example.org/source"}]
    report, blockers = validator.validate_operator_source_pack_review(packet, checklist_url, template, "<html></html>")
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "url_leak_in_runtime_artifact" in blockers

    # 2. Hash leak
    hash_64 = "a" * 64
    checklist_hash = [{"checklist_item_id": "item_1", "evidence_hash": hash_64}]
    report, blockers = validator.validate_operator_source_pack_review(packet, checklist_hash, template, "<html></html>")
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "hash_leak_in_runtime_artifact" in blockers

    # sha256 prefix format
    checklist_sha256 = [{"checklist_item_id": "item_1", "evidence_hash": "sha256:12345abcdef"}]
    report, blockers = validator.validate_operator_source_pack_review(packet, checklist_sha256, template, "<html></html>")
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "hash_leak_in_runtime_artifact" in blockers

    # 3. Excerpt leak
    checklist_excerpt = [{"checklist_item_id": "item_1", "source_excerpt_ref": "Actual extracted excerpt content text."}]
    report, blockers = validator.validate_operator_source_pack_review(packet, checklist_excerpt, template, "<html></html>")
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "source_excerpt_leak_in_runtime_artifact" in blockers

    # 4. Citation leak
    html_citation = "<html>This claims some truth [1] paired with text.</html>"
    report, blockers = validator.validate_operator_source_pack_review(packet, [], template, html_citation)
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "citation_or_source_reference_leak_detected" in blockers

    # 5. Non-null operator signature / identity
    template_operator = {
        "valid_for_draft_generation": False,
        "valid_for_publication": False,
        "valid_for_dispatch": False,
        "operator_id": "jim"
    }
    report, blockers = validator.validate_operator_source_pack_review(packet, [], template_operator, "<html></html>")
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "operator_signature_leaked" in blockers

    # 6. Timestamp leak
    template_timestamp = {
        "valid_for_draft_generation": False,
        "valid_for_publication": False,
        "valid_for_dispatch": False,
        "approved_at": "2026-06-28T12:00:00Z"
    }
    report, blockers = validator.validate_operator_source_pack_review(packet, [], template_timestamp, "<html></html>")
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "fake_approval_timestamp_detected" in blockers

    # 7. Metric leak
    html_metric = "<html>We achieved 1000 impressions on our last post.</html>"
    report, blockers = validator.validate_operator_source_pack_review(packet, [], template, html_metric)
    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "metric_leak_detected" in blockers


def test_validator_harmless_labels_allowed():
    packet = {
        "review_status": "OPERATOR_SOURCE_PACK_REVIEW_REQUIRED",
        "runtime_truth": False
    }
    checklist = [
        {
            "source_url_required": True,
            "evidence_hash_required": True,
            "source_excerpt_ref_required": True,
            "current_status": "missing"
        }
    ]
    template = {
        "valid_for_draft_generation": False,
        "valid_for_publication": False,
        "valid_for_dispatch": False,
        "operator_id": None
    }
    html = "<html>Required: source_url and evidence_hash</html>"

    report, blockers = validator.validate_operator_source_pack_review(packet, checklist, template, html)
    assert report["validation_status"] == "PASSED_WITH_REVIEW_ONLY_BLOCKERS"
    assert "url_leak_in_runtime_artifact" not in blockers
    assert "hash_leak_in_runtime_artifact" not in blockers
    assert "operator_signature_leaked" not in blockers


def test_no_forbidden_behavior_in_validator():
    import live_contentops.operator_source_pack_review_validator_v6 as target_module
    attrs = dir(target_module)
    forbidden = ["urlopen", "requests", "httpx", "getenv", "environ", "openai", "anthropic", "google"]
    for f in forbidden:
        assert f not in attrs
