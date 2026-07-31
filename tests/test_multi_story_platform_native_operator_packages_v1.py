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
    "CONTENTOPS_FAST_SHIP_BIND_THREE_V3_PACKETS_TO_CANONICAL_EDITORIAL_AND_OPERATOR_PACKAGES_V1"
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


def test_canonical_editorial_outcomes_bind_articles_claims_roles_and_holds():
    packet = _load("canonical_editorial_outcomes.json")
    assert packet["outcome_count"] == 3
    assert packet["story_ids"] == list(packages.EXPECTED_STORY_IDS)
    for outcome in packet["outcomes"]:
        assert outcome["canonical_article_id"].startswith("cc-canonical-draft-")
        assert outcome["canonical_article_hash"] == packages._logical_hash(
            outcome["canonical_article"]
        )
        assert outcome["article_used_approved_claim_ids"] == list(
            packages.AUTHORIZED_CLAIMS[outcome["story_id"]]
        )
        assert outcome["canonical_article"]["claim_ids_used"] == outcome[
            "article_used_approved_claim_ids"
        ]
        assert len(outcome["role_outcomes"]) == 8
        assert [row["role"] for row in outcome["role_outcomes"]] == [
            "assignment_editor",
            "evidence_planner",
            "reporter_writer",
            "quantitative_editor",
            "visual_editor",
            "copy_editor",
            "platform_editor",
            "adversarial_final_reviewer",
        ]
        assert outcome["editorial_review_hash"] == packages._logical_hash(
            outcome["editorial_review"]
        )
        assert outcome["editorial_state"] == (
            "PASS" if not outcome["unresolved_blockers"] else "HOLD"
        )
        unhashed = dict(outcome)
        observed = unhashed.pop("outcome_hash")
        assert packages._logical_hash(unhashed) == observed


def test_superseding_operator_packages_are_unsigned_pending_and_fully_bound():
    packet = _load("superseding_unsigned_operator_packages.json")
    outcomes = {
        row["story_id"]: row
        for row in _load("canonical_editorial_outcomes.json")["outcomes"]
    }
    assert packet["package_count"] == 3
    assert packet["state"] == "PENDING_OPERATOR_DECISION"
    for package in packet["packages"]:
        outcome = outcomes[package["story_id"]]
        assert package["state"] == "PENDING_OPERATOR_DECISION"
        assert package["signature"] is None
        assert package["operator_identity"] is None
        assert package["selected_decision"] is None
        assert package["operator_approval_captured"] is False
        assert package["publication_authority"] is False
        assert package["dispatch_authority"] is False
        assert package["public_write_authority"] is False
        assert package["authority_binding"]["exact_git_receipt"] == packages._expected_authority_receipt()
        binding = package["editorial_binding"]
        assert binding["v3_packet_id"] == outcome["v3_packet_id"]
        assert binding["v3_packet_logical_hash"] == outcome["v3_packet_logical_hash"]
        assert binding["canonical_article_id"] == outcome["canonical_article_id"]
        assert binding["canonical_article_hash"] == outcome["canonical_article_hash"]
        assert binding["article_used_approved_claim_ids"] == outcome["article_used_approved_claim_ids"]
        assert binding["editorial_review_hash"] == outcome["editorial_review_hash"]
        assert binding["freshness_disposition"] == outcome["freshness_disposition"]
        assert binding["visual_disposition"] == outcome["visual_disposition"]
        assert binding["final_adversarial_review_disposition"] == outcome["final_adversarial_review_disposition"]
        assert binding["unresolved_blockers"] == outcome["unresolved_blockers"]
        assert len(package["variant_payload_hashes"]) == 6
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


def test_authority_claim_mutation_fails_closed(monkeypatch):
    authority = _authority()
    authority["stories"][0]["claims"][0]["claim_id"] = "claim-mutated"
    story = authority["stories"][0]
    story["logical_hash"] = packages.logical_hash({
        key: value for key, value in story.items() if key != "logical_hash"
    })
    authority["logical_hash"] = packages.logical_hash({
        key: value for key, value in authority.items() if key != "logical_hash"
    })
    monkeypatch.setattr(
        packages, "EXPECTED_AUTHORITY_LOGICAL_HASH", authority["logical_hash"]
    )
    with pytest.raises(ValueError, match="claim_allowlist_mismatch:fomc-minutes-2026-04-28-29"):
        packages.build_documents(authority, packages.EXPECTED_UPSTREAM_HEAD)


def test_permission_upgrade_mutation_fails_closed(monkeypatch):
    authority = _authority()
    authority["stories"][1]["consumer_permissions"]["publication_allowed"] = True
    story = authority["stories"][1]
    story["logical_hash"] = packages.logical_hash({
        key: value for key, value in story.items() if key != "logical_hash"
    })
    authority["logical_hash"] = packages.logical_hash({
        key: value for key, value in authority.items() if key != "logical_hash"
    })
    monkeypatch.setattr(
        packages, "EXPECTED_AUTHORITY_LOGICAL_HASH", authority["logical_hash"]
    )
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
    outcome = packages._build_editorial_outcome(story)
    receipt = packages._expected_authority_receipt()
    package = packages._build_package(story, story_rows, outcome, receipt)
    mutated_rows = deepcopy(story_rows)
    mutated_rows[0]["payload_hash"] = "0" * 64
    mutated_package = packages._build_package(story, mutated_rows, outcome, receipt)
    assert mutated_package["package_hash"] != package["package_hash"]
    mutated_outcome = deepcopy(outcome)
    mutated_outcome["canonical_article_hash"] = "0" * 64
    mutated_outcome["outcome_hash"] = packages._logical_hash({
        key: value for key, value in mutated_outcome.items() if key != "outcome_hash"
    })
    article_mutated_package = packages._build_package(
        story, story_rows, mutated_outcome, receipt
    )
    assert article_mutated_package["package_hash"] != package["package_hash"]


def test_wrong_upstream_head_fails_closed():
    with pytest.raises(ValueError, match="upstream_head_mismatch"):
        packages.build_documents(_authority(), "0" * 40)
