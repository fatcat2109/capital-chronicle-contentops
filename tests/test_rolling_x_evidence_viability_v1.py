from __future__ import annotations

from live_contentops.newsroom_assignment_scheduler_v1 import (
    ROLLING_X_ASSIGNMENT_SCHEMA_VERSION,
    select_first_viable_rolling_x_cluster,
)


def _assignment(*clusters, decision="SELECT_STORY"):
    return {
        "schema_version": ROLLING_X_ASSIGNMENT_SCHEMA_VERSION,
        "decision": decision,
        "ranked_clusters": list(clusters),
    }


def _cluster(cluster_id, rank, *, market_sensitive=False, article_mode="breaking"):
    return {
        "cluster_id": cluster_id,
        "rank": rank,
        "headline_ids": [f"headline-{rank}"],
        "article_mode": article_mode,
        "market_sensitive": market_sensitive,
        "needed_evidence": ["official record"],
    }


def _receipt(request, *, status="PASS", capabilities=None, authority=False):
    return {
        "status": status,
        "cluster_id": request["cluster_id"],
        "headline_ids": list(request["headline_ids"]),
        "provided_evidence_capabilities": capabilities or request["required_evidence_capabilities"],
        "evidence_documents": [{"source_url": "https://official.example/record"}],
        "capital_chronicle_authority_verified": authority,
        "numeric_evidence_required": False,
    }


def test_rank_one_blocker_falls_back_to_rank_two_and_acquires_after_ranking():
    calls = []

    def acquire(request):
        calls.append(request)
        if request["rank"] == 1:
            return _receipt(request, status="BLOCKED", capabilities=[])
        return _receipt(request)

    result = select_first_viable_rolling_x_cluster(
        assignment=_assignment(_cluster("one", 1), _cluster("two", 2)),
        acquire_evidence=acquire,
        story_type_by_cluster={"one": "physical_event", "two": "physical_event"},
    )

    assert result["status"] == "SUCCESS"
    assert result["selected_cluster_id"] == "two"
    assert [row["rank"] for row in result["rank_attempts"]] == [1, 2]
    assert [row["rank"] for row in calls] == [1, 2]
    assert all(row["x_content_grants_evidence_authority"] is False for row in [result])
    assert result["evidence_acquired_after_ranking"] is True


def test_non_market_factual_story_does_not_require_market_or_numeric_evidence():
    seen = []

    def acquire(request):
        seen.append(request)
        return _receipt(request)

    result = select_first_viable_rolling_x_cluster(
        assignment=_assignment(_cluster("factual", 1, market_sensitive=False)),
        acquire_evidence=acquire,
    )

    assert result["status"] == "SUCCESS"
    assert seen[0]["market_snapshot_required"] is False
    assert seen[0]["capital_chronicle_numeric_or_analytical_authority_required"] is False
    assert seen[0]["required_evidence_capabilities"] == [
        "official_document", "implementation_timeline", "affected_entities"
    ]


def test_all_ranked_clusters_blocked_returns_governed_no_publication():
    def acquire(request):
        return _receipt(request, status="BLOCKED", capabilities=[])

    result = select_first_viable_rolling_x_cluster(
        assignment=_assignment(_cluster("one", 1), _cluster("two", 2)),
        acquire_evidence=acquire,
        story_type_by_cluster={"one": "physical_event", "two": "physical_event"},
    )

    assert result["status"] == "NO_PUBLICATION"
    assert result["decision"] == "NO_PUBLICATION"
    assert result["selected_cluster_id"] is None
    assert len(result["rank_attempts"]) == 2
    assert all(row["status"] == "BLOCKED" for row in result["rank_attempts"])
