from __future__ import annotations

import json
from pathlib import Path

import pytest

from live_contentops.governed_upstream_bridge_v1 import (
    BLOCKED_LOCAL_ARTIFACT,
    GovernedArtifactBlocked,
    is_ancestor,
    resolve_observed_head,
    verify_local_artifact,
)
from live_contentops.universal_news_cross_domain_canary_v1 import (
    build_real_cross_domain_canary,
)


ROOT = Path(__file__).parents[1]
UPSTREAM_ROOT = ROOT.parent.parent / "Headline Raw data local json" / "capital-chronicle-ingestion"
TASK_START_UPSTREAM_HEAD = "c0a57145986ce9f25fc083369970e3b121a5ba73"


def test_missing_local_governed_artifact_fails_with_exact_blocker(tmp_path):
    with pytest.raises(GovernedArtifactBlocked, match=BLOCKED_LOCAL_ARTIFACT):
        verify_local_artifact(
            root=tmp_path,
            relative_path="missing.duckdb",
            expected_sha256="0" * 64,
            artifact_kind="duckdb",
        )


def test_local_governed_artifact_hash_mismatch_fails_with_exact_blocker(tmp_path):
    artifact = tmp_path / "artifact.parquet"
    artifact.write_bytes(b"exact bytes")
    with pytest.raises(GovernedArtifactBlocked, match=BLOCKED_LOCAL_ARTIFACT):
        verify_local_artifact(
            root=tmp_path,
            relative_path=artifact.name,
            expected_sha256="0" * 64,
            artifact_kind="parquet",
        )


def test_local_governed_artifact_exact_hash_passes(tmp_path):
    from hashlib import sha256

    artifact = tmp_path / "artifact.parquet"
    artifact.write_bytes(b"exact bytes")
    receipt = verify_local_artifact(
        root=tmp_path,
        relative_path=artifact.name,
        expected_sha256=sha256(b"exact bytes").hexdigest(),
        artifact_kind="parquet",
    )
    assert receipt.status == "PASS_EXACT_SHA256"


@pytest.fixture(scope="module")
def real_canary():
    if not (UPSTREAM_ROOT / ".git").exists():
        pytest.skip("governed upstream worktree is not available")
    current = resolve_observed_head(UPSTREAM_ROOT)
    if not is_ancestor(UPSTREAM_ROOT, TASK_START_UPSTREAM_HEAD, current):
        pytest.skip("initial upstream authority is not reachable")
    return build_real_cross_domain_canary(
        upstream_root=UPSTREAM_ROOT,
        observed_head=TASK_START_UPSTREAM_HEAD,
    )


def test_real_canary_has_six_distinct_official_categories(real_canary):
    assert real_canary["classification"] == "PASS_REAL_CROSS_DOMAIN_CANARY_NO_PUBLICATION"
    assert len(real_canary["selected_real_categories"]) == 6
    assert real_canary["candidate_counts"] == {
        "total": 6,
        "reporting_eligible": 1,
        "held_context_only": 5,
        "rejected_contract_invalid": 0,
    }


def test_real_canary_claim_graph_is_numeric_and_nonnumeric(real_canary):
    assert real_canary["claim_counts_by_type"] == {
        "corporate_filing_fact": 1,
        "entity_relationship": 1,
        "event_occurrence": 1,
        "factual_text": 1,
        "legal_or_regulatory_action": 1,
        "numeric_observation": 4,
    }


def test_every_real_candidate_has_exact_lineage_and_no_publication(real_canary):
    cluster_by_candidate = {
        candidate_id: cluster
        for cluster in real_canary["pool"]["clusters"]
        for candidate_id in cluster["candidate_ids"]
    }
    for candidate in real_canary["pool"]["candidates"]:
        assert candidate["evidence_refs"]
        assert candidate["source_documents"]
        assert candidate["publication_authority"] is False
        assert candidate["public_write_allowed"] is False
        assert candidate["global_dqr_override"] is False
        assert {
            ref for claim in candidate["claims"] for ref in claim["evidence_refs"]
        } == set(candidate["evidence_refs"])
        cluster = cluster_by_candidate[candidate["candidate_id"]]
        assert candidate["cluster_id"] == cluster["cluster_id"]
        assert candidate["story_id"] == cluster["story_id"]
        assert candidate["update_chain_id"] == cluster["update_chain_id"]


def test_ofac_snapshot_is_context_not_new_sanctions_action(real_canary):
    candidate = next(
        row for row in real_canary["pool"]["candidates"]
        if row["evidence_requirement_profile_id"] == "geopolitical_or_sanctions"
    )
    assert [row["claim_type"] for row in candidate["claims"]] == ["entity_relationship"]
    assert "current_entity_snapshot_is_context_not_a_new_sanctions_action" in candidate["limitations"]
    assert candidate["reporting_allowed"] is False
    relationships = candidate["producer_binding"]["revision_relationships"]
    assert len(relationships) == 1
    assert relationships[0]["relation_type"] == "snapshot_contains"


def test_filing_metadata_does_not_claim_earnings_or_market_reaction(real_canary):
    candidate = next(
        row for row in real_canary["pool"]["candidates"]
        if row["evidence_requirement_profile_id"] == "corporate_filing"
    )
    assert [row["claim_type"] for row in candidate["claims"]] == ["corporate_filing_fact"]
    text = json.dumps(candidate, sort_keys=True).lower()
    assert "no_earnings_revenue_valuation_or_market_reaction_claim" in text
    assert '"claim_type": "market_reaction"' not in text


def test_dbh2_receipts_cover_duckdb_and_nine_parquet_partitions(real_canary):
    receipt = real_canary["pool"]["upstream_binding"]["dbh2_bridge_receipt"]
    assert receipt["local_artifact_status"] == "PASS_ALL_EXACT_SHA256"
    assert receipt["artifact_producer_commit"] != receipt["observed_head"]
    assert receipt["artifact_producer_commit_reachable_from_observed_head"] is True
    assert len(receipt["local_artifacts"]) == 10
    assert all(row["status"] == "PASS_EXACT_SHA256" for row in receipt["local_artifacts"])


def test_v1_pool_receipt_separates_producer_commit_from_observed_head(real_canary):
    receipt = real_canary["pool"]["upstream_binding"]["v1_pool_receipt"]
    assert receipt["producer_commit"] == "8c63faca0603f81bebfbb68380a0dc4ad51ab87d"
    assert receipt["producer_commit"] != receipt["observed_head"]


def test_task_start_observed_head_remains_reachable_after_branch_advancement(real_canary):
    receipt = real_canary["pool"]["upstream_binding"]["dbh2_bridge_receipt"]
    assert receipt["observed_head_reachable_from_later_branch_head"] is True
    assert is_ancestor(
        UPSTREAM_ROOT,
        receipt["observed_head"],
        receipt["later_observed_branch_head"],
    )


def test_real_assignment_preserves_zero_unavailable_and_no_publication(real_canary):
    numeric = next(
        row for row in real_canary["pool"]["candidates"]
        if row["evidence_requirement_profile_id"] == "numeric_economic_release"
    )
    assert numeric["ranking_inputs"]["surprise"]["availability"] == "EXPLICIT_ZERO"
    assert numeric["ranking_inputs"]["surprise"]["score"] == 0
    assert numeric["ranking_inputs"]["audience_relevance"]["availability"] == "UNAVAILABLE"
    assert numeric["ranking_inputs"]["audience_relevance"]["score"] is None
    assert real_canary["assignment"]["summary"]["publication_count"] == 0
    assert real_canary["assignment"]["summary"]["public_write_count"] == 0


def test_real_canary_is_deterministic(real_canary):
    replay = build_real_cross_domain_canary(
        upstream_root=UPSTREAM_ROOT,
        observed_head=real_canary["upstream_observed_head"],
    )
    assert replay == real_canary
