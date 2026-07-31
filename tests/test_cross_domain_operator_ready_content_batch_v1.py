from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

import pytest

from live_contentops import cross_domain_operator_ready_content_batch_v1 as batch


EVIDENCE_DIR = Path(
    "docs/automation/"
    "CONTENTOPS_FAST_SHIP_CROSS_DOMAIN_OPERATOR_READY_CONTENT_BATCH_V1"
)


def _load(name: str):
    return json.loads((EVIDENCE_DIR / name).read_text(encoding="utf-8"))


def test_committed_batch_coverage_and_editorial_outcomes():
    summary = _load("batch_summary.json")
    truth = _load("validation_truth.json")

    assert summary["batch_size"] == 12
    assert summary["authorized_candidate_count"] == 1
    assert summary["context_only_candidate_count"] == 11
    assert summary["candidate_source_family_count"] == 4
    assert summary["governed_fabric_source_family_count"] == 5
    assert summary["domain_count"] == 4
    assert 5 <= summary["editorial_outcome_count"] <= 8
    assert summary["platform_preview_count"] == 5
    assert summary["publication_count"] == 0
    assert summary["public_write_count"] == 0
    assert summary["upstream_write_count"] == 0
    assert truth["status"] == "PASS"
    assert truth["no_source_family_misattribution"] is True
    assert truth["no_live_flags_enabled"] is True


def test_platform_previews_are_substantive_hashed_and_review_only():
    packet = _load("platform_variant_and_preview_summary.json")
    expected_platforms = set(batch.PRIORITY_PLATFORMS)
    variants = packet["variants"]

    assert {row["platform_id"] for row in variants} == expected_platforms
    assert packet["all_valid_for_dispatch_false"] is True
    assert packet["all_public_ready_false"] is True
    for row in variants:
        substantive = row["text"].replace("Not financial advice.", "").strip()
        assert substantive
        assert "U.S. Treasury Curve Steepens" in substantive
        assert row["operator_review_required"] is True
        assert row["approval_required"] is True
        assert row["valid_for_dispatch"] is False
        assert row["dispatch_ready"] is False
        assert row["public_ready"] is False
        assert row["live_eligibility"] is False
        assert len(row["payload_hash"]) == 64
        assert len(row["citation_fingerprints"]) == len(row["citations"])
        assert all(len(value) == 64 for value in row["citation_fingerprints"])

    unsupported = packet["unsupported_surfaces"]
    assert unsupported == [
        {
            "platform_id": "youtube_community",
            "reason": "no canonical v2 local preview contract",
            "status": "UNSUPPORTED_LOCAL_PREVIEW_CONTRACT",
        }
    ]


def test_manifest_artifact_and_logical_hashes_match_committed_bytes():
    manifest = _load("final_manifest.json")
    for artifact in manifest["artifacts"]:
        path = Path(artifact["path"])
        assert path.stat().st_size == artifact["byte_length"]
        assert sha256(path.read_bytes()).hexdigest() == artifact["sha256"]

    unhashed = dict(manifest)
    logical_hash = unhashed.pop("logical_hash")
    assert sha256(batch._canonical(unhashed)).hexdigest() == logical_hash
    assert manifest["publication_authority"] is False
    assert manifest["public_write_performed"] is False
    assert manifest["upstream_write_performed"] is False
    assert manifest["network_intake_performed"] is False
    assert manifest["credential_read_performed"] is False


def test_authorized_disclaimer_only_article_falls_back_to_governed_candidate_copy():
    candidate = {
        "reporting_allowed": True,
        "title": "Governed title",
        "summary": "Governed summary.",
    }
    handoff = {"article": {"rendered_body": "\n\nNot financial advice."}}

    text = batch._safe_source_text(candidate, handoff)

    assert text == "Governed title\n\nGoverned summary.\n\nNot financial advice."


def test_preview_rejects_disclaimer_only_payload():
    candidate = {"candidate_id": "candidate-1"}
    cycle = {
        "output": {
            "platform_payloads": [
                {
                    "platform_id": "telegram",
                    "content_surface": "channel_post",
                    "payload_shape": "dry_run",
                    "mode": "dry_run",
                    "text": "\n\nNot financial advice.",
                    "character_count": 23,
                    "character_limit_max": 4096,
                    "citations": [],
                    "limitations": [],
                }
            ]
        }
    }

    with pytest.raises(
        ValueError,
        match="operator_preview_substantive_text_missing:telegram",
    ):
        batch._preview(candidate, cycle)


def test_preview_keeps_urls_visible_but_hashes_only_citation_fingerprints():
    citation = "https://example.test/governed-source"
    candidate = {"candidate_id": "candidate-1"}
    cycle = {
        "output": {
            "platform_payloads": [
                {
                    "platform_id": "telegram",
                    "content_surface": "channel_post",
                    "payload_shape": "dry_run",
                    "mode": "dry_run",
                    "text": "Governed copy. Not financial advice.",
                    "character_count": 37,
                    "character_limit_max": 4096,
                    "citations": [citation],
                    "limitations": ["local_operator_review_only"],
                }
            ]
        }
    }

    preview = batch._preview(candidate, cycle)["previews"][0]

    assert preview["citations"] == [citation]
    assert preview["citation_fingerprints"] == [
        sha256(citation.encode("utf-8")).hexdigest()
    ]
    assert len(preview["payload_hash"]) == 64
