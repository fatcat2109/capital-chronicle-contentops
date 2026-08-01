from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path

from live_contentops.freshness_market_state_v2 import evaluate_freshness
from live_contentops.temporal_authority_v1 import (
    build_current_readiness_parity,
    build_historical_replay_integrity_matrix,
    build_temporal_authority_records,
    evaluate_temporal_authority_item,
    logical_hash,
)


PRIOR = Path(
    "docs/automation/"
    "CONTENTOPS_FAST_SHIP_STORY_SCOPED_PERMISSION_AND_FIRST_TEXT_ONLY_OPERATOR_READY_PACKAGE_V1"
)
DECISION = Path(
    "docs/automation/"
    "CONTENTOPS_FAST_SHIP_DECISION_TIME_FRESHNESS_AND_CURRENT_OPERATOR_READINESS_TRUTH_V1"
)
CURRENT = Path(
    "docs/automation/"
    "CONTENTOPS_FAST_SHIP_TEMPORAL_AUTHORITY_AND_POINT_IN_TIME_REPLAY_INTEGRITY_V1"
)
CUTOFF = "2026-01-02T00:00:00Z"
OPERATOR_CUTOFF = "2026-08-01T00:00:00Z"


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _item(**overrides):
    values = {
        "evidence_kind": "USED_CLAIM",
        "evidence_id": "claim-generic",
        "event_time_utc": "2026-01-01T00:00:00Z",
        "published_or_release_time_utc": "2026-01-01T00:00:00Z",
        "known_at_or_retrieved_at_utc": "2026-01-01T12:00:00Z",
        "revision_at_utc": "2026-01-01T18:00:00Z",
        "historical_replay_cutoff_utc": CUTOFF,
        "operator_evaluation_cutoff_utc": OPERATOR_CUTOFF,
    }
    values.update(overrides)
    return evaluate_temporal_authority_item(**values)


def _build():
    packets = _load(PRIOR / "canonical_content_evidence_packets_v3.json")["packets"]
    outcomes = _load(PRIOR / "canonical_editorial_outcomes.json")["outcomes"]
    packages = _load(PRIOR / "superseding_unsigned_operator_packages.json")["packages"]
    decisions = _load(DECISION / "decision_time_freshness_records.json")["records"]
    return build_temporal_authority_records(
        packets=packets,
        outcomes=outcomes,
        packages=packages,
        decision_time_records=decisions,
        operator_evaluation_as_of_utc=OPERATOR_CUTOFF,
    )


def test_known_at_before_equal_and_after_cutoff_truth_table():
    assert _item(known_at_or_retrieved_at_utc="2026-01-01T23:59:59Z")["point_in_time_authority_status"] == "PASS"
    assert _item(known_at_or_retrieved_at_utc=CUTOFF)["point_in_time_authority_status"] == "PASS"
    after = _item(known_at_or_retrieved_at_utc="2026-01-02T00:00:01Z")
    assert after["point_in_time_authority_status"] == "BLOCK"
    assert "known_at_or_retrieved_at_after_historical_replay_cutoff" in after["blockers"]


def test_unknown_known_at_is_unproven_and_fail_closed_without_coercion():
    result = _item(known_at_or_retrieved_at_utc="legacy_retrieval_timestamp_not_evidenced")
    assert result["point_in_time_authority_status"] == "UNPROVEN"
    assert result["point_in_time_authority_decision"] == "BLOCK"
    assert result["temporal_inputs"]["known_at_or_retrieved_at"]["normalized_utc"] is None
    assert "known_at_or_retrieved_at_unavailable_or_unevidenced" in result["unproven_reasons"]
    assert result["timestamp_invention_or_coercion_performed"] is False


def test_revision_before_equal_after_cutoff_and_predecessor_binding_truth_table():
    assert _item(revision_at_utc="2026-01-01T23:59:59Z")["point_in_time_authority_status"] == "PASS"
    assert _item(revision_at_utc=CUTOFF)["point_in_time_authority_status"] == "PASS"
    leaked = _item(revision_at_utc="2026-01-02T00:00:01Z")
    assert leaked["point_in_time_authority_status"] == "BLOCK"
    assert leaked["blockers"] == ["FUTURE_REVISION_LEAKAGE_BLOCK"]
    bound = _item(
        revision_at_utc="2026-01-02T00:00:01Z",
        bound_historical_predecessor={"artifact_hash": "a" * 64},
    )
    assert bound["point_in_time_authority_status"] == "BLOCK"
    assert "FUTURE_REVISION_LEAKAGE_BLOCK" in bound["blockers"]
    assert any(
        reason.startswith("historical_predecessor_binding_missing_fields:")
        for reason in bound["unproven_reasons"]
    )


def test_future_source_timestamp_is_rejected_by_temporal_authority_and_freshness():
    authority = _item(published_or_release_time_utc="2026-01-02T00:00:01Z")
    assert authority["point_in_time_authority_status"] == "BLOCK"
    assert "published_or_release_time_after_historical_replay_cutoff" in authority["blockers"]
    freshness = evaluate_freshness(
        {
            "as_of_utc": CUTOFF,
            "official_source_documents": [
                {"published_at_utc": "2026-01-02T00:00:01Z"}
            ],
        },
        {
            "article_mode": "analysis",
            "fresh_material_delta": True,
            "market_sensitive": False,
            "market_snapshot_required": False,
            "readiness_evaluation_basis": "HISTORICAL_SOURCE_TIME_FRESHNESS_REPLAY",
        },
    )
    assert freshness["primary_source_age_hours"] is None
    assert freshness["decision"] == "BLOCK"
    assert "primary_source_timestamp_after_evaluation_cutoff" in freshness["blockers"]


def test_source_time_freshness_pass_never_implies_point_in_time_authority():
    temporal = _build()
    usgs = next(row for row in temporal["records"] if row["story_id"].startswith("usgs-"))
    assert usgs["historical_source_time_freshness_replay"]["decision"] == "PASS"
    assert usgs["historical_source_time_freshness_replay"]["source_age_hours"] == 0
    assert usgs["historical_source_time_freshness_replay"]["does_not_imply_point_in_time_authority"] is True
    assert usgs["point_in_time_authority"]["status"] == "BLOCK"
    assert "FUTURE_REVISION_LEAKAGE_BLOCK" in usgs["point_in_time_authority"]["blockers"]
    assert "known_at_or_retrieved_at_unavailable_or_unevidenced" in usgs["point_in_time_authority"]["unproven_reasons"]


def test_current_story_temporal_authority_matches_expected_fail_closed_truth():
    records = {row["story_id"]: row for row in _build()["records"]}
    fomc = records["fomc-minutes-2026-04-28-29"]["point_in_time_authority"]
    apple = records["apple-sec-10q-2026-000013"]["point_in_time_authority"]
    usgs = records["usgs-reviewed-ridgecrest-ci38457511"]["point_in_time_authority"]
    assert fomc["status"] == "BLOCK"
    assert "known_at_or_retrieved_at_after_historical_replay_cutoff" in fomc["blockers"]
    assert apple["status"] == "UNPROVEN"
    assert "known_at_or_retrieved_at_unavailable_or_unevidenced" in apple["unproven_reasons"]
    assert usgs["status"] == "BLOCK"
    assert "FUTURE_REVISION_LEAKAGE_BLOCK" in usgs["blockers"]
    assert sum(row["point_in_time_authority"]["status"] == "PASS" for row in records.values()) == 0


def test_temporal_inputs_and_cutoffs_mutate_hashes_deterministically():
    baseline = _item()
    assert baseline == _item()
    mutations = [
        _item(event_time_utc="2025-12-31T23:00:00Z"),
        _item(published_or_release_time_utc="2025-12-31T23:00:00Z"),
        _item(known_at_or_retrieved_at_utc="2026-01-01T13:00:00Z"),
        _item(revision_at_utc="2026-01-01T19:00:00Z"),
        _item(historical_replay_cutoff_utc="2026-01-03T00:00:00Z"),
        _item(operator_evaluation_cutoff_utc="2026-08-02T00:00:00Z"),
    ]
    assert all(row["temporal_authority_hash"] != baseline["temporal_authority_hash"] for row in mutations)


def test_all_18_current_holds_and_exact_five_supersessions_remain_hash_identical():
    temporal = _build()
    source = _load(DECISION / "current_operator_readiness_records.json")
    parity = build_current_readiness_parity(source, temporal)
    assert parity["record_count"] == 18
    assert parity["current_operator_ready_count"] == 0
    assert parity["superseded_prior_text_only_receipt_count"] == 5
    assert all(row["CURRENT_OPERATOR_READY"] is False for row in parity["records"])
    assert all(row["canonical_package_state"] == "PENDING_OPERATOR_DECISION" for row in parity["records"])
    assert all(row["canonical_editorial_state"] == "HOLD" for row in parity["records"])
    superseded = [row for row in parity["records"] if row["supersedes_prior_text_only_operator_ready_receipt"]]
    assert len(superseded) == 5
    assert all(row["story_id"] == "usgs-reviewed-ridgecrest-ci38457511" for row in superseded)
    for parity_row, source_row in zip(parity["records"], source["records"], strict=True):
        for key in ("package_hash", "article_hash", "v3_packet_hash", "variant_hash"):
            assert parity_row[key] == source_row["hashes"][key]
        assert parity_row["prior_receipt_hash"] == source_row["receipt_hash"]
        assert parity_row["publication_authority"] is False
        assert parity_row["dispatch_authority"] is False
        assert parity_row["approval_authority"] is False
        assert parity_row["public_write_authority"] is False


def test_matrix_and_committed_temporal_artifacts_are_logically_hash_valid():
    temporal = _build()
    matrix = build_historical_replay_integrity_matrix(temporal)
    assert matrix["historical_authority_pass_count"] == 0
    assert matrix["source_time_pass_does_not_grant_authority"] is True
    for filename in (
        "temporal_authority_records.json",
        "historical_replay_integrity_matrix.json",
        "current_readiness_parity.json",
        "validation_truth.json",
        "final_manifest.json",
    ):
        document = _load(CURRENT / filename)
        observed = document["logical_hash"]
        core = {key: value for key, value in document.items() if key != "logical_hash"}
        assert observed == logical_hash(core)
    committed = _load(CURRENT / "temporal_authority_records.json")
    assert committed == temporal
    assert committed["starting_remote_head"] == "1548196ebffd2bc7ce82a4ae290211b9c53a45df"
    assert committed["publication_authority"] is False
    assert committed["dispatch_authority"] is False
    assert committed["approval_authority"] is False
    assert committed["public_write_authority"] is False
    manifest = _load(CURRENT / "final_manifest.json")
    for artifact in manifest["artifacts"]:
        assert artifact["byte_sha256"] == sha256(
            Path(artifact["path"]).read_bytes()
        ).hexdigest()


def test_canonical_json_hash_helper_matches_sha256_reference():
    value = {"z": 1, "a": [False, None, "x"]}
    expected = sha256(
        json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()
    ).hexdigest()
    assert logical_hash(deepcopy(value)) == expected
