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


def test_rank_walk_can_resume_after_downstream_candidate_local_failure():
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
        start_after_rank=1,
    )

    assert result["selected_rank"] == 2
    assert [row["rank"] for row in calls] == [2]
    assert [row["rank"] for row in result["rank_attempts"]] == [2]
    assert result["start_after_rank"] == 1


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


def test_registry_ordinary_market_reporting_does_not_require_capital_chronicle_authority():
    seen = []

    result = select_first_viable_rolling_x_cluster(
        assignment=_assignment(_cluster("market", 1, market_sensitive=False)),
        acquire_evidence=lambda request: seen.append(request) or _receipt(
            request, authority=True
        ),
        story_type_by_cluster={"market": "market_move"},
    )

    assert result["status"] == "SUCCESS"
    assert seen[0]["capital_chronicle_numeric_or_analytical_authority_required"] is False
    assert seen[0]["effective_article_mode"] == "BREAKING_BRIEF"


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
    assert result["publishability_pool_exhausted"] is True
    assert result["evidence_request_budget_exhausted"] is False


def test_acquisition_budget_exhaustion_is_not_mislabeled_as_pool_exhaustion():
    calls = []

    def acquire(request):
        calls.append(request["rank"])
        receipt = _receipt(request, status="BLOCKED")
        receipt["evidence_acquisition_provenance"] = {
            "public_secondary": {
                "status": "BLOCKED",
                "blockers": ["public_source_request_budget_exhausted"],
                "provenance": {
                    "request_count": 24,
                    "request_limit": 24,
                    "diagnostics": ["public_source_request_budget_exhausted"],
                },
            }
        }
        return receipt

    result = select_first_viable_rolling_x_cluster(
        assignment=_assignment(
            _cluster("one", 1), _cluster("two", 2), _cluster("three", 3)
        ),
        acquire_evidence=acquire,
        story_type_by_cluster={
            "one": "physical_event",
            "two": "physical_event",
            "three": "physical_event",
        },
    )

    assert result["status"] == "NO_PUBLICATION"
    assert result["reason_code"] == (
        "EVIDENCE_REQUEST_BUDGET_EXHAUSTED_BEFORE_PUBLISHABILITY_POOL_CLOSURE"
    )
    assert result["evidence_request_budget_exhausted"] is True
    assert result["evidence_request_budget_blockers"] == [
        "public_source_request_budget_exhausted"
    ]
    assert result["publishability_pool_exhausted"] is False
    assert result["attempted_candidate_count"] == 3
    assert result["unattempted_candidate_count"] == 0
    assert calls == [1, 2, 3]


def test_global_llm_budget_exhaustion_stops_candidate_walk_as_infrastructure():
    calls = []

    def acquire(request):
        calls.append(request["rank"])
        receipt = _receipt(request, status="BLOCKED")
        receipt["blockers"] = ["llm_cycle_provider_attempt_budget_exhausted"]
        receipt["evidence_acquisition_provenance"] = {
            "grounded_research": {
                "status": "BLOCKED",
                "blockers": ["llm_cycle_provider_attempt_budget_exhausted"],
                "infrastructure_failure_class": (
                    "llm_cycle_provider_attempt_budget_exhausted"
                ),
                "global_infrastructure_exhausted": True,
            }
        }
        return receipt

    result = select_first_viable_rolling_x_cluster(
        assignment=_assignment(
            _cluster("one", 1), _cluster("two", 2), _cluster("three", 3)
        ),
        acquire_evidence=acquire,
        story_type_by_cluster={
            "one": "physical_event",
            "two": "physical_event",
            "three": "physical_event",
        },
    )

    assert result["status"] == "BLOCKED"
    assert result["decision"] is None
    assert result["reason_code"] == "INFRASTRUCTURE_BUDGET_OR_PROVIDER_EXHAUSTED"
    assert result["attempted_candidate_count"] == 1
    assert result["unattempted_candidate_count"] == 2
    assert result["global_infrastructure_blockers"] == [
        "llm_cycle_provider_attempt_budget_exhausted"
    ]
    assert calls == [1]


def test_one_exhausted_evidence_lane_does_not_block_later_other_lane_candidate():
    calls = []

    def acquire(request):
        calls.append(request["rank"])
        if request["rank"] == 1:
            receipt = _receipt(request, status="BLOCKED")
            receipt["evidence_acquisition_provenance"] = {
                "public_secondary": {
                    "status": "BLOCKED",
                    "blockers": ["public_source_request_budget_exhausted"],
                }
            }
            return receipt
        return _receipt(request)

    result = select_first_viable_rolling_x_cluster(
        assignment=_assignment(_cluster("secondary", 1), _cluster("official", 2)),
        acquire_evidence=acquire,
        story_type_by_cluster={
            "secondary": "physical_event",
            "official": "data_release",
        },
    )

    assert result["status"] == "SUCCESS"
    assert result["selected_cluster_id"] == "official"
    assert result["selected_rank"] == 2
    assert calls == [1, 2]
    assert result["evidence_request_budget_exhausted"] is True


def test_pass_receipt_is_not_vetoed_by_exhausted_optional_lane_diagnostic():
    def acquire(request):
        receipt = _receipt(request)
        receipt["evidence_acquisition_provenance"] = {
            "public_secondary": {
                "status": "BLOCKED",
                "blockers": ["public_source_request_budget_exhausted"],
            }
        }
        return receipt

    result = select_first_viable_rolling_x_cluster(
        assignment=_assignment(_cluster("official", 1)),
        acquire_evidence=acquire,
        story_type_by_cluster={"official": "data_release"},
    )

    assert result["status"] == "SUCCESS"
    assert result["selected_cluster_id"] == "official"
    assert result["evidence_request_budget_exhausted"] is False


def test_budget_blocked_deep_mode_can_downgrade_same_cluster_to_viable_brief():
    calls = []

    def acquire(request):
        calls.append(dict(request))
        if len(calls) == 1:
            receipt = _receipt(request, status="BLOCKED")
            receipt["evidence_acquisition_provenance"] = {
                "public_secondary": {
                    "status": "BLOCKED",
                    "blockers": ["public_source_request_budget_exhausted"],
                }
            }
            return receipt
        return _receipt(request)

    result = select_first_viable_rolling_x_cluster(
        assignment=_assignment(_cluster("downgrade", 1, article_mode="deep_dive")),
        acquire_evidence=acquire,
        story_type_by_cluster={"downgrade": "physical_event"},
    )

    assert result["status"] == "SUCCESS"
    assert result["selected_cluster_id"] == "downgrade"
    assert len(calls) == 2
    assert calls[0]["effective_article_mode"] == "STANDARD_NEWS_ANALYSIS"
    assert calls[1]["effective_article_mode"] == "BREAKING_BRIEF"
    assert any(
        row["evidence_request_budget_blockers"]
        == ["public_source_request_budget_exhausted"]
        for row in result["rank_attempts"][0]["mode_attempts"]
    )
