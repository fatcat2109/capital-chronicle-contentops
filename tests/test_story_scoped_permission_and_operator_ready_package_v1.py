from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path

from live_contentops import multi_story_platform_native_operator_packages_v1 as packages
from live_contentops.window_incremental_editorial_shadow_v1 import (
    build_candidate_bound_evidence_packet,
)


UPSTREAM_AUTHORITY = Path(
    "A:/Capital Chronicle/Headline Raw data local json/"
    "capital-chronicle-ingestion-multi-story-authority-v1/"
    "docs/research/publication_evidence/current/"
    "CapitalChronicleMultiStoryScopedReportingAuthorityBatchV1.json"
)
EVIDENCE_DIR = Path(
    "docs/automation/"
    "CONTENTOPS_FAST_SHIP_STORY_SCOPED_PERMISSION_AND_FIRST_TEXT_ONLY_OPERATOR_READY_PACKAGE_V1"
)


def _authority():
    return json.loads(UPSTREAM_AUTHORITY.read_text(encoding="utf-8"))


def _load(name: str):
    return json.loads((EVIDENCE_DIR / name).read_text(encoding="utf-8"))


def test_exact_upstream_claim_permissions_are_derived_without_scope_widening():
    decisions = [
        packages.derive_story_scoped_claim_permission(story, claim)
        for story in _authority()["stories"]
        for claim in story["claims"]
    ]
    assert len(decisions) == 5
    assert all(row["reporting_allowed"] is True for row in decisions)
    assert all(row["permission_state"] == "PUBLIC_CLAIM_ALLOWED" for row in decisions)
    assert all(row["blockers"] == [] for row in decisions)
    assert all(row["source_family_wide_authority"] is False for row in decisions)
    assert all(row["numeric_reporting_allowed"] is False for row in decisions)
    assert all(row["interpretation_allowed"] is False for row in decisions)
    assert all(row["publication_authority"] is False for row in decisions)
    assert all(row["dispatch_authority"] is False for row in decisions)


def test_each_missing_or_widened_authority_field_fails_closed_per_claim():
    story = _authority()["stories"][0]
    claim = story["claims"][0]

    missing_reporting = deepcopy(claim)
    missing_reporting.pop("reporting_allowed")
    decision = packages.derive_story_scoped_claim_permission(story, missing_reporting)
    assert decision["permission_state"] == "PUBLIC_CLAIM_BLOCKED"
    assert decision["blockers"] == [
        "upstream_authority_field_missing_or_false:upstream_claim.reporting_allowed"
    ]

    widened_family = deepcopy(story)
    widened_family["consumer_permissions"]["source_family_wide_authority"] = True
    decision = packages.derive_story_scoped_claim_permission(widened_family, claim)
    assert decision["permission_state"] == "PUBLIC_CLAIM_BLOCKED"
    assert decision["blockers"] == [
        "upstream_authority_field_missing_or_true:consumer_permissions.source_family_wide_authority"
    ]

    missing_allowlist = deepcopy(story)
    missing_allowlist["consumer_permissions"]["authorized_claim_ids"] = []
    decision = packages.derive_story_scoped_claim_permission(missing_allowlist, claim)
    assert decision["permission_state"] == "PUBLIC_CLAIM_BLOCKED"
    assert decision["blockers"] == [
        "upstream_authority_field_missing_claim_id:consumer_permissions.authorized_claim_ids"
    ]


def test_nonnumeric_public_claim_bridge_allows_narrative_without_numeric_authority():
    story = _authority()["stories"][2]
    candidate = packages._build_canonical_candidate(story)
    packet = build_candidate_bound_evidence_packet(
        candidate,
        generated_at_utc=story["timestamps"]["published_at"],
    )
    assert packet["numeric_claims"] == []
    assert packet["public_claim_permissions"] == {
        "numeric_claims_allowed": False,
        "narrative_synthesis_allowed": True,
        "llm_numeric_authority": False,
        "decision": "ALLOW",
    }
    assert packet["blockers"] == []


def test_rebuilt_v3_and_editorial_outputs_preserve_per_story_capabilities():
    documents = packages.build_documents(_authority(), packages.EXPECTED_UPSTREAM_HEAD)
    packets = documents["canonical_content_evidence_packets_v3.json"]["packets"]
    assert len(packets) == 3
    assert all(row["generic_claim_permissions"]["decision"] == "ALLOW" for row in packets)
    outcomes = {
        row["story_id"]: row
        for row in documents["canonical_editorial_outcomes.json"]["outcomes"]
    }
    fomc = outcomes["fomc-minutes-2026-04-28-29"]
    apple = outcomes["apple-sec-10q-2026-000013"]
    usgs = outcomes["usgs-reviewed-ridgecrest-ci38457511"]
    for row in (fomc, apple):
        assert row["freshness_disposition"]["market_sensitive"] is True
        assert row["freshness_disposition"]["market_snapshot_required"] is True
        assert len(row["freshness_disposition"]["blockers"]) == 2
    assert usgs["freshness_disposition"]["market_sensitive"] is False
    assert usgs["freshness_disposition"]["market_snapshot_required"] is False
    assert usgs["freshness_disposition"]["blockers"] == []
    assert usgs["editorial_state"] == "HOLD"
    assert set(usgs["unresolved_blockers"]) == {
        "fewer_than_three_useful_visuals",
        "insufficient_visual_evidence_diversity",
        "lead_visual_missing",
        "structured_role_review_failed_or_claimed_authority:visual_editor",
        "structured_adversarial_review_failed_or_claimed_authority",
    }


def test_committed_readiness_records_bind_hashes_and_keep_live_authority_false():
    records = _load("per_platform_readiness_records.json")
    ready = [row for row in records["records"] if row["operator_ready_for_decision"]]
    assert records["record_count"] == 18
    assert records["operator_ready_record_count"] == 5
    assert len(ready) == 5
    for row in records["records"]:
        assert row["publication_authority"] is False
        assert row["dispatch_authority"] is False
        assert all(len(value) == 64 for value in row["hashes"].values())
    assert all(row["source_family"] == "usgs_comcat" for row in ready)
    assert all(row["effective_platform_visual_mode"] == "text_only" for row in ready)
    assert all(row["operator_decision_state"] == "PENDING_OPERATOR_DECISION" for row in ready)

    operator_packages = _load("text_only_operator_ready_packages.json")
    assert operator_packages["package_count"] == 5
    for package in operator_packages["packages"]:
        assert package["editorial_state"] == "EDITORIALLY_READY_FOR_OPERATOR_DECISION"
        assert package["operator_decision_state"] == "PENDING_OPERATOR_DECISION"
        assert package["publication_authority"] is False
        assert package["dispatch_authority"] is False
        assert package["public_write_authority"] is False
        assert package["effective_platform_visual_mode"] == "text_only"

    manifest = _load("final_manifest.json")
    for artifact in manifest["artifacts"]:
        path = Path(artifact["path"])
        assert sha256(path.read_bytes()).hexdigest() == artifact["byte_sha256"]
    unhashed = dict(manifest)
    observed = unhashed.pop("logical_hash")
    canonical = json.dumps(
        unhashed, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")
    assert sha256(canonical).hexdigest() == observed
