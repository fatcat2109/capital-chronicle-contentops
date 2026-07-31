from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path

import pytest

from live_contentops import multi_story_platform_native_operator_packages_v1 as packages
from live_contentops.payload_preview_hash_v6 import compute_payload_hash


EVIDENCE_DIR = Path(
    "docs/automation/"
    "CONTENTOPS_FAST_SHIP_MULTI_STORY_PLATFORM_NATIVE_OPERATOR_PACKAGES_V1"
)
UPSTREAM_AUTHORITY = Path(
    "A:/Capital Chronicle/Headline Raw data local json/"
    "capital-chronicle-ingestion-multi-story-authority-v1/"
    "docs/research/publication_evidence/current/"
    "CapitalChronicleMultiStoryScopedReportingAuthorityBatchV1.json"
)


def _load(name: str):
    return json.loads((EVIDENCE_DIR / name).read_text(encoding="utf-8"))


def _authority():
    return json.loads(UPSTREAM_AUTHORITY.read_text(encoding="utf-8"))


def test_committed_candidate_batch_has_required_scale_and_exact_five_families():
    packet = _load("candidate_batch.json")
    assert 15 <= packet["candidate_count"] <= 25
    assert packet["candidate_count"] == len(packet["candidates"])
    assert packet["source_family_count"] == 5
    assert packet["source_family_ids"] == sorted({
        "federal_reserve_fomc",
        "sec_edgar",
        "usgs_comcat",
        "story_scoped_publication_evidence_v1",
        "nonnumeric_story_scoped_publication_evidence_v1",
    })
    assert sum(row["candidate_role"] == "PRIMARY_OPERATOR_PACKAGE" for row in packet["candidates"]) == 3
    assert all(row["publication_authority"] is False for row in packet["candidates"])


def test_committed_variants_are_six_per_story_platform_native_and_review_only():
    packet = _load("platform_native_variants.json")
    assert packet["variant_count"] == 18
    assert packet["platform_ids"] == list(packages.PLATFORM_IDS)
    for story_id in packages.EXPECTED_STORY_IDS:
        rows = [row for row in packet["variants"] if row["story_id"] == story_id]
        assert [row["platform_id"] for row in rows] == list(packages.PLATFORM_IDS)
        assert len({row["text"] for row in rows}) == 6
        for row in rows:
            assert row["character_count"] == len(row["text"])
            assert row["character_count"] <= row["character_limit_max"]
            assert row["operator_review_required"] is True
            assert row["approval_required"] is True
            assert row["valid_for_dispatch"] is False
            assert row["dispatch_ready"] is False
            assert row["public_ready"] is False
            assert row["live_eligibility"] is False
            hash_input = {
                key: row[key]
                for key in (
                    "story_id", "candidate_id", "authority_story_logical_hash",
                    "authorized_claim_ids", "platform_id", "content_surface",
                    "payload_shape", "mode", "text", "citation_fingerprints",
                    "limitation_fingerprints", "policy",
                )
            }
            assert row["payload_hash"] == compute_payload_hash(hash_input)


def test_youtube_community_is_text_only_default_article_surface_not_video():
    packet = _load("platform_native_variants.json")
    youtube_rows = [row for row in packet["variants"] if row["platform_id"] == "youtube_community"]
    assert len(youtube_rows) == 3
    for row in youtube_rows:
        assert row["content_surface"] == "community_text_post"
        assert row["youtube_contract"] == {
            "default_article_surface_confirmed": True,
            "media_required": False,
            "post_type": "text_only_community_post",
            "surface": "youtube_community",
            "video_upload_request": False,
        }
        assert "text-only Community post package" in row["text"]


def test_operator_packages_are_unsigned_pending_and_exactly_hash_bound():
    packet = _load("unsigned_operator_approval_packages.json")
    variants = _load("platform_native_variants.json")["variants"]
    assert packet["package_count"] == 3
    assert packet["state"] == "PENDING_OPERATOR_DECISION"
    for package in packet["packages"]:
        assert package["state"] == "PENDING_OPERATOR_DECISION"
        assert package["signature"] is None
        assert package["operator_identity"] is None
        assert package["selected_decision"] is None
        assert package["operator_approval_captured"] is False
        assert package["publication_authority"] is False
        assert package["dispatch_authority"] is False
        assert package["public_write_authority"] is False
        rows = [row for row in variants if row["story_id"] == package["story_id"]]
        assert package["variant_payload_hashes"] == {row["platform_id"]: row["payload_hash"] for row in rows}
        unhashed = dict(package)
        observed = unhashed.pop("package_hash")
        assert packages._logical_hash(unhashed) == observed


def test_manifest_hashes_match_committed_bytes_and_replay_is_deterministic():
    manifest = _load("final_manifest.json")
    for artifact in manifest["artifacts"]:
        path = Path(artifact["path"])
        assert path.stat().st_size == artifact["byte_length"]
        assert sha256(path.read_bytes()).hexdigest() == artifact["sha256"]
    unhashed = dict(manifest)
    logical_hash = unhashed.pop("logical_hash")
    assert packages._logical_hash(unhashed) == logical_hash
    first = packages.build_documents(_authority(), packages.EXPECTED_UPSTREAM_HEAD)
    second = packages.build_documents(_authority(), packages.EXPECTED_UPSTREAM_HEAD)
    assert packages._canonical(first) == packages._canonical(second)


def test_authority_claim_mutation_fails_closed():
    authority = _authority()
    authority["stories"][0]["claims"][0]["claim_id"] = "claim-mutated"
    with pytest.raises(ValueError, match="claim_allowlist_mismatch:fomc-minutes-2026-04-28-29"):
        packages.build_documents(authority, packages.EXPECTED_UPSTREAM_HEAD)


def test_permission_upgrade_mutation_fails_closed():
    authority = _authority()
    authority["stories"][1]["consumer_permissions"]["publication_allowed"] = True
    with pytest.raises(ValueError, match="permission_boundary_mismatch:apple-sec-10q-2026-000013"):
        packages.build_documents(authority, packages.EXPECTED_UPSTREAM_HEAD)


def test_unsupported_prose_and_usgs_numeric_mutations_fail_closed():
    story = _authority()["stories"][2]
    with pytest.raises(ValueError, match="usgs_magnitude_not_authorized"):
        packages._assert_prose_allowed(story, "USGS reports M 7.1. Not financial advice.")
    with pytest.raises(ValueError, match="unsupported_prose"):
        packages._assert_prose_allowed(story, "This is a market reaction forecast. Not financial advice.")


def test_variant_and_package_hashes_change_on_exact_copy_mutation():
    authority = _authority()
    story = authority["stories"][0]
    row = packages._build_variant(story, packages._candidate_id(story), "linkedin")
    mutated = deepcopy(row)
    mutated["text"] += " "
    hash_input = {
        key: mutated[key]
        for key in (
            "story_id", "candidate_id", "authority_story_logical_hash",
            "authorized_claim_ids", "platform_id", "content_surface",
            "payload_shape", "mode", "text", "citation_fingerprints",
            "limitation_fingerprints", "policy",
        )
    }
    assert compute_payload_hash(hash_input) != row["payload_hash"]
    story_rows = [packages._build_variant(story, packages._candidate_id(story), platform) for platform in packages.PLATFORM_IDS]
    package = packages._build_package(story, story_rows)
    mutated_rows = deepcopy(story_rows)
    mutated_rows[0]["payload_hash"] = "0" * 64
    mutated_package = packages._build_package(story, mutated_rows)
    assert mutated_package["package_hash"] != package["package_hash"]


def test_wrong_upstream_head_fails_closed():
    with pytest.raises(ValueError, match="upstream_head_mismatch"):
        packages.build_documents(_authority(), "0" * 40)
