from __future__ import annotations

from live_contentops.newsroom_assignment_scheduler_v1 import (
    ROLLING_X_ASSIGNMENT_SCHEMA_VERSION,
    _validate_rolling_x_story_type_output,
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
        "claim_evidence_contract": {
            "status": "PASS",
            "supported_claim_count": 1,
            "fabricated_claim_count": 0,
            "supported_claims": [{
                "claim_id": "fixture-claim",
                "claim_text": "The official record confirms the controlled event.",
                "support_status": "SUPPORTED_PRIMARY",
            }],
            "omitted_unsupported_claims": [],
        },
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


def test_first_viable_rank_stops_all_lower_rank_acquisition():
    calls = []
    result = select_first_viable_rolling_x_cluster(
        assignment=_assignment(
            _cluster("one", 1), _cluster("two", 2), _cluster("three", 3)
        ),
        acquire_evidence=lambda request: calls.append(request) or _receipt(request),
        story_type_by_cluster={
            "one": "physical_event",
            "two": "physical_event",
            "three": "physical_event",
        },
    )

    assert result["selected_rank"] == 1
    assert [row["rank"] for row in calls] == [1]
    assert [row["rank"] for row in result["rank_attempts"]] == [1]


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
        "credible_event_confirmation", "basic_attributed_facts"
    ]


def test_explicit_story_type_beats_legacy_market_sensitive_default():
    seen = []

    result = select_first_viable_rolling_x_cluster(
        assignment=_assignment(_cluster("policy", 1, market_sensitive=True)),
        acquire_evidence=lambda request: seen.append(request) or _receipt(request),
        story_type_by_cluster={"policy": "regulatory_fiscal_event"},
    )

    assert result["status"] == "SUCCESS"
    assert seen[0]["story_type"] == "regulatory_fiscal_event"
    assert seen[0]["market_sensitive"] is True
    assert seen[0]["capital_chronicle_numeric_or_analytical_authority_required"] is False


def test_registry_market_context_requires_capital_chronicle_authority():
    seen = []

    result = select_first_viable_rolling_x_cluster(
        assignment=_assignment(_cluster("market", 1, market_sensitive=False)),
        acquire_evidence=lambda request: seen.append(request) or _receipt(
            request, authority=True
        ),
        story_type_by_cluster={"market": "market_move"},
    )

    assert result["status"] == "SUCCESS"
    assert seen[0]["capital_chronicle_numeric_or_analytical_authority_required"] is True


def test_unknown_explicit_story_type_fails_closed():
    try:
        select_first_viable_rolling_x_cluster(
            assignment=_assignment(_cluster("one", 1)),
            acquire_evidence=lambda request: _receipt(request),
            story_type_by_cluster={"one": "invented_story_type"},
        )
    except ValueError as exc:
        assert str(exc) == "rolling_x_story_type_unknown"
    else:
        raise AssertionError("unknown story type must fail closed")


def test_story_type_classifier_requires_exact_cluster_coverage():
    import json

    allowed = {"market_move", "physical_event"}
    valid, failure, output = _validate_rolling_x_story_type_output(
        json.dumps({"stories": [
            {"cluster_id": "one", "story_type": "market_move", "reason": "Market event."},
            {"cluster_id": "two", "story_type": "physical_event", "reason": "Physical event."},
        ]}),
        cluster_ids=["one", "two"],
        allowed_story_types=allowed,
    )
    assert valid is True
    assert failure is None
    assert [row["cluster_id"] for row in output["stories"]] == ["one", "two"]

    for rows in (
        [
            {"cluster_id": "one", "story_type": "market_move", "reason": "One."},
            {"cluster_id": "one", "story_type": "physical_event", "reason": "Duplicate."},
        ],
        [
            {"cluster_id": "one", "story_type": "market_move", "reason": "One."},
            {"cluster_id": "unknown", "story_type": "physical_event", "reason": "Unknown."},
        ],
    ):
        valid, failure, output = _validate_rolling_x_story_type_output(
            json.dumps({"stories": rows}),
            cluster_ids=["one", "two"],
            allowed_story_types=allowed,
        )
        assert valid is False
        assert failure == "structured_output_schema_invalid"
        assert output is None


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
