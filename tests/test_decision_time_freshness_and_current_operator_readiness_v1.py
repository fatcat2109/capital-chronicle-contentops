from __future__ import annotations

from copy import deepcopy
from hashlib import sha1, sha256
import json
from pathlib import Path

from live_contentops.decision_time_operator_readiness_v1 import (
    build_decision_time_freshness_records,
)
from live_contentops.freshness_market_state_v2 import evaluate_freshness


PRIOR = Path(
    "docs/automation/"
    "CONTENTOPS_FAST_SHIP_STORY_SCOPED_PERMISSION_AND_FIRST_TEXT_ONLY_OPERATOR_READY_PACKAGE_V1"
)
CURRENT = Path(
    "docs/automation/"
    "CONTENTOPS_FAST_SHIP_DECISION_TIME_FRESHNESS_AND_CURRENT_OPERATOR_READINESS_TRUTH_V1"
)
FIXTURE = Path("tests/fixtures/multi_story_scoped_reporting_authority_batch_v1.json")
CUTOFF = "2026-08-01T00:00:00Z"


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _simple_packet(published: str = "2026-01-01T00:00:00Z"):
    return {
        "as_of_utc": published,
        "events": [],
        "headlines": [],
        "official_source_documents": [{"published_at_utc": published}],
        "numeric_claims": [],
        "market_snapshots": [],
        "blockers": [],
    }


def _request(**overrides):
    return {
        "article_mode": "analysis",
        "market_sensitive": False,
        "market_snapshot_required": False,
        "fresh_material_delta": False,
        **overrides,
    }


def _documents():
    return (
        _load(PRIOR / "canonical_content_evidence_packets_v3.json")["packets"],
        _load(PRIOR / "canonical_editorial_outcomes.json")["outcomes"],
        _load(PRIOR / "superseding_unsigned_operator_packages.json")["packages"],
    )


def test_historical_replay_and_current_operator_cutoff_produce_distinct_age_truth():
    packet = _simple_packet()
    historical = evaluate_freshness(
        packet,
        _request(readiness_evaluation_basis="HISTORICAL_SOURCE_TIME_FRESHNESS_REPLAY"),
    )
    current = evaluate_freshness(
        packet,
        _request(
            readiness_evaluation_basis="CURRENT_OPERATOR_READINESS",
            operator_evaluation_as_of_utc="2026-01-03T00:00:00Z",
        ),
    )
    assert historical["primary_source_age_hours"] == 0.0
    assert historical["decision"] == "PASS"
    assert current["primary_source_age_hours"] == 48.0
    assert current["decision"] == "BLOCK"
    assert current["blockers"] == [
        "analysis_requires_fresh_material_delta_or_current_reaction"
    ]
    assert historical["readiness_evaluation_basis"] == "HISTORICAL_SOURCE_TIME_FRESHNESS_REPLAY"
    assert current["readiness_evaluation_basis"] == "CURRENT_OPERATOR_READINESS"


def test_current_operator_readiness_requires_explicit_cutoff_without_clock_fallback():
    decision = evaluate_freshness(
        _simple_packet(),
        _request(readiness_evaluation_basis="CURRENT_OPERATOR_READINESS"),
    )
    assert decision["evaluation_as_of_utc"] is None
    assert decision["primary_source_age_hours"] is None
    assert decision["decision"] == "BLOCK"
    assert "operator_evaluation_as_of_utc_required" in decision["blockers"]


def test_current_cutoff_preserves_snapshot_requirement_independence():
    packet = _simple_packet()
    common = {
        "readiness_evaluation_basis": "CURRENT_OPERATOR_READINESS",
        "operator_evaluation_as_of_utc": "2026-01-03T00:00:00Z",
        "fresh_material_delta": True,
    }
    no_snapshot = evaluate_freshness(
        packet,
        _request(market_sensitive=True, market_snapshot_required=False, **common),
    )
    explicit_snapshot = evaluate_freshness(
        packet,
        _request(market_sensitive=False, market_snapshot_required=True, **common),
    )
    assert no_snapshot["blockers"] == []
    assert explicit_snapshot["blockers"] == [
        "market_sensitive_story_snapshot_stale_or_missing",
        "market_sensitive_story_ingest_stale_or_missing",
    ]


def test_stale_usgs_physical_event_blocks_without_market_snapshot_blockers():
    records = _load(CURRENT / "decision_time_freshness_records.json")["records"]
    usgs = next(row for row in records if row["source_family"] == "usgs_comcat")
    historical = usgs["historical_point_in_time_replay"]
    current = usgs["current_operator_readiness"]
    assert historical["decision"] == "PASS"
    assert historical["primary_source_age_hours"] == 0.0
    assert current["decision"] == "BLOCK"
    assert current["primary_source_age_hours"] > 60000
    assert current["blockers"] == [
        "analysis_requires_fresh_material_delta_or_current_reaction"
    ]
    assert current["market_snapshot_required"] is False


def test_retrospective_and_historical_explainer_framing_fail_closed_without_authority():
    common = {
        "readiness_evaluation_basis": "CURRENT_OPERATOR_READINESS",
        "operator_evaluation_as_of_utc": CUTOFF,
        "market_sensitive": False,
        "market_snapshot_required": False,
    }
    retrospective = evaluate_freshness(
        _simple_packet(), {**common, "article_mode": "retrospective"}
    )
    explainer = evaluate_freshness(
        _simple_packet(),
        {
            **common,
            "article_mode": "explainer",
            "historical_framing_requested": True,
        },
    )
    assert "retrospective_framing_requires_explicit_claim_authority" in retrospective["blockers"]
    assert "historical_explainer_framing_requires_explicit_claim_authority" in explainer["blockers"]
    authorized = evaluate_freshness(
        _simple_packet(),
        {
            **common,
            "article_mode": "retrospective",
            "historical_framing_authorized": True,
        },
    )
    assert authorized["decision"] == "PASS"


def test_fixed_cutoff_replay_is_deterministic_and_cutoff_mutates_freshness_hashes():
    packets, outcomes, packages = _documents()
    first = build_decision_time_freshness_records(
        packets=packets,
        outcomes=outcomes,
        packages=packages,
        operator_evaluation_as_of_utc=CUTOFF,
    )
    replay = build_decision_time_freshness_records(
        packets=deepcopy(packets),
        outcomes=deepcopy(outcomes),
        packages=deepcopy(packages),
        operator_evaluation_as_of_utc=CUTOFF,
    )
    later = build_decision_time_freshness_records(
        packets=packets,
        outcomes=outcomes,
        packages=packages,
        operator_evaluation_as_of_utc="2026-08-02T00:00:00Z",
    )
    assert first == replay
    assert first["logical_hash"] != later["logical_hash"]
    assert [row["hashes"]["current_freshness_hash"] for row in first["records"]] != [
        row["hashes"]["current_freshness_hash"] for row in later["records"]
    ]
    for earlier, changed in zip(first["records"], later["records"], strict=True):
        assert earlier["hashes"]["package_hash"] == changed["hashes"]["package_hash"]
        assert earlier["hashes"]["article_hash"] == changed["hashes"]["article_hash"]
        assert earlier["hashes"]["v3_packet_hash"] == changed["hashes"]["v3_packet_hash"]


def test_repo_relative_authority_fixture_preserves_exact_pinned_git_artifact_bytes():
    data = FIXTURE.read_bytes()
    assert len(data) == 16646
    assert sha1(f"blob {len(data)}\0".encode() + data).hexdigest() == "fbb25216d08b5a4c5ca30386cf8f47ed468c1eac"
    assert sha256(data).hexdigest() == "5bc4ca67c4c149c0f68eeacdcb3899fbd29e3647945723c9ceb955a69ddb5d05"


def test_all_current_platform_receipts_are_truthful_hash_bound_and_no_write():
    document = _load(CURRENT / "current_operator_readiness_records.json")
    assert document["record_count"] == 18
    assert document["current_operator_ready_count"] == 0
    assert document["superseded_prior_text_only_receipt_count"] == 5
    assert document["operator_decision_state"] == "PENDING_OPERATOR_DECISION"
    superseded = [
        row
        for row in document["records"]
        if row["supersedes_prior_text_only_operator_ready_receipt"]
    ]
    assert len(superseded) == 5
    assert all(row["source_family"] == "usgs_comcat" for row in superseded)
    assert all(row["superseded_prior_receipt_hash"] for row in superseded)
    for row in document["records"]:
        assert row["canonical_editorial_state"] == "HOLD"
        assert row["current_operator_readiness"]["CURRENT_OPERATOR_READY"] is False
        assert row["current_operator_readiness"]["freshness_decision"]["decision"] == "BLOCK"
        assert row["current_operator_readiness"]["operator_evaluation_as_of_utc"] == CUTOFF
        assert row["publication_authority"] is False
        assert row["dispatch_authority"] is False
        assert row["public_write_authority"] is False
        assert all(len(value) == 64 for value in row["hashes"].values())
        assert row["source_timestamps"]["published_at_utc"]
    usgs = [row for row in document["records"] if row["source_family"] == "usgs_comcat"]
    assert all(
        "market_sensitive_story_snapshot_stale_or_missing"
        not in row["current_operator_readiness"]["unresolved_blockers"]
        for row in usgs
    )


def test_committed_decision_time_evidence_logical_and_byte_hashes_validate():
    decision = _load(CURRENT / "decision_time_freshness_records.json")
    current = _load(CURRENT / "current_operator_readiness_records.json")
    for document in (decision, current):
        observed = document["logical_hash"]
        core = {key: value for key, value in document.items() if key != "logical_hash"}
        assert observed == sha256(
            json.dumps(core, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()
        ).hexdigest()
    manifest = _load(CURRENT / "final_manifest.json")
    manifest_hash = manifest["logical_hash"]
    manifest_core = {key: value for key, value in manifest.items() if key != "logical_hash"}
    assert manifest_hash == sha256(
        json.dumps(manifest_core, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()
    ).hexdigest()
    for artifact in manifest["artifacts"]:
        assert artifact["byte_sha256"] == sha256(Path(artifact["path"]).read_bytes()).hexdigest()
