from __future__ import annotations

from pathlib import Path

import pytest

from live_contentops.cross_domain_continuous_shadow_v1 import (
    CHECKPOINTS,
    build_continuous_shadow_operation,
)
from live_contentops.governed_upstream_bridge_v1 import is_ancestor
from live_contentops.universal_governed_registry_v1 import (
    load_governed_registry_authority,
    validate_governed_pool,
)


ROOT = Path(__file__).parents[1]
UPSTREAM_ROOT = (
    ROOT.parent.parent
    / "Headline Raw data local json"
    / "capital-chronicle-ingestion"
)


@pytest.fixture(scope="module")
def operation():
    if not (UPSTREAM_ROOT / ".git").exists():
        pytest.skip("governed upstream worktree unavailable")
    return build_continuous_shadow_operation(
        repo_root=ROOT,
        upstream_root=UPSTREAM_ROOT,
    )


def test_operation_is_multi_cutoff_five_window_and_no_write(operation):
    assert operation["summary"] == {
        "checkpoint_count": 9,
        "window_decision_count": 45,
        "real_candidate_version_count": 8,
        "real_family_count": 6,
        "governed_update_chain_count": 1,
        "internal_assignment_count": 1,
        "publication_count": 0,
        "public_write_count": 0,
        "same_cutoff_duplicate_assignment_count": 0,
    }
    assert operation["operation_mode"] == "DETERMINISTIC_LOCAL_CONTINUOUS_SHADOW"
    assert operation["network_intake_performed"] is False
    assert operation["continuous_live_intake_claimed"] is False
    assert operation["publication_authority"] is False
    assert operation["public_write_performed"] is False
    assert operation["upstream_write_performed"] is False


def test_new_records_enter_only_after_known_at_time(operation):
    for checkpoint, pool in zip(
        operation["checkpoint_ledger"],
        operation["multi_cutoff_candidate_pools"],
    ):
        assert checkpoint["cutoff_utc"] == pool["cutoff_time_utc"]
        assert all(
            candidate["known_at_utc"] <= checkpoint["cutoff_utc"]
            for candidate in pool["candidates"]
        )
        assert checkpoint["available_candidate_count"] == len(pool["candidates"])


def test_same_cutoff_rerun_is_idempotent(operation):
    replay = build_continuous_shadow_operation(
        repo_root=ROOT,
        upstream_root=UPSTREAM_ROOT,
    )
    assert replay == operation
    assert [row["idempotency_key"] for row in operation["checkpoint_ledger"]] == [
        row["idempotency_key"] for row in replay["checkpoint_ledger"]
    ]


def test_real_correction_chain_preserves_versions_and_relationships(operation):
    ledger = operation["clustering_update_chain_ledger"]
    correction = next(
        row
        for row in ledger["clusters"]
        if [item["relationship"] for item in row["relationships"]]
        == ["initial_event", "correction"]
    )
    assert len(correction["candidate_ids"]) == 2
    assert ledger["exercised_relationships"] == ["initial_event", "correction"]
    assert ledger["governed_correction_relationships"]


def test_unchanged_identity_is_assigned_only_once(operation):
    assigned = [
        decision["selected_candidate_id"]
        for checkpoint in operation["five_window_shadow_decisions"]
        for decision in checkpoint["decisions"]
        if decision["selected_candidate_id"] is not None
    ]
    assert len(assigned) == 1
    assert len(set(assigned)) == 1
    later_blockers = [
        blocker
        for checkpoint in operation["five_window_shadow_decisions"]
        for decision in checkpoint["decisions"]
        for held in decision["held_candidates"]
        if held["candidate_id"] == assigned[0]
        for blocker in held["blockers"]
    ]
    assert "prior_identity_without_governed_delta" in later_blockers


def test_context_only_candidates_remain_held(operation):
    final = operation["multi_cutoff_candidate_pools"][-1]
    context = [row for row in final["candidates"] if not row["reporting_allowed"]]
    assert len(context) == 7
    assert all("context_only_evidence" in row["blockers"] for row in context)
    assert all(row["publication_authority"] is False for row in context)


def test_explicit_zero_unavailable_and_stale_are_distinct(operation):
    eligible_pool = operation["multi_cutoff_candidate_pools"][
        CHECKPOINTS.index("2026-07-14T00:00:00Z")
    ]
    numeric = next(
        row
        for row in eligible_pool["candidates"]
        if row["evidence_requirement_profile_id"] == "numeric_economic_release"
    )
    assert numeric["ranking_inputs"]["surprise"]["availability"] == "EXPLICIT_ZERO"
    assert numeric["ranking_inputs"]["surprise"]["score"] == 0
    assert numeric["ranking_inputs"]["audience_relevance"]["availability"] == (
        "UNAVAILABLE"
    )
    assert numeric["ranking_inputs"]["audience_relevance"]["score"] is None
    stale = next(
        row
        for row in operation["multi_cutoff_candidate_pools"][-1]["candidates"]
        if row["candidate_id"] == numeric["candidate_id"]
    )
    assert stale["freshness"]["stale"] is True
    assert "stale_at_checkpoint" in stale["blockers"]


def test_every_checkpoint_pool_passes_governed_validation(operation):
    trusted = operation["trusted_evidence_index"]
    authority = load_governed_registry_authority(repo_root=ROOT)
    for pool in operation["multi_cutoff_candidate_pools"]:
        assert validate_governed_pool(
            pool,
            authority=authority,
            trusted_evidence_index=trusted,
        ) == ()


def test_six_required_real_families_are_present(operation):
    final = operation["multi_cutoff_candidate_pools"][-1]
    assert {
        row["evidence_requirement_profile_id"] for row in final["candidates"]
    } == {
        "numeric_economic_release",
        "official_action",
        "corporate_filing",
        "geopolitical_or_sanctions",
        "physical_disruption",
    }
    assert len({family for row in final["candidates"] for family in row["source_family_ids"]}) == 6


def test_ofac_snapshot_never_becomes_action_or_market_reaction(operation):
    final = operation["multi_cutoff_candidate_pools"][-1]
    candidate = next(
        row
        for row in final["candidates"]
        if row["evidence_requirement_profile_id"] == "geopolitical_or_sanctions"
    )
    assert [row["claim_type"] for row in candidate["claims"]] == [
        "entity_relationship"
    ]
    assert candidate["claims"][0]["structured_payload"]["relationship_type"] == (
        "snapshot_contains"
    )
    assert candidate["market_evidence_records"] == []


def test_local_upstream_receipts_are_exact_and_branch_advanced(operation):
    receipt = operation["local_dbh2_receipt"]
    assert receipt["local_artifact_status"] == "PASS_ALL_EXACT_SHA256"
    assert len(receipt["local_artifacts"]) == 10
    assert receipt["artifact_producer_commit_reachable_from_observed_head"] is True
    assert receipt["observed_head_reachable_from_later_branch_head"] is True
    assert is_ancestor(
        UPSTREAM_ROOT,
        receipt["observed_head"],
        receipt["later_observed_branch_head"],
    )
