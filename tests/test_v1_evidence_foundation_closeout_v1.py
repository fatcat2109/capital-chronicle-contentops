from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from live_contentops import _eight_platform_substack_first_pipeline_impl_v1 as implementation
from live_contentops.official_codex_provider_v1 import (
    OFFICIAL_SDK_VERSION,
    OfficialCodexProviderError,
)
from live_contentops.official_codex_source_discovery_v1 import (
    OfficialCodexUrlDiscoveryProvider,
)
from live_contentops.rolling_x_grounded_article_media_builder_v1 import (
    GroundedArticleBuilderError,
    build_rolling_x_grounded_article_and_media,
    normalize_article_transport_representation,
    resolve_article_transport_envelope,
)
from scripts.prove_v1_evidence_foundation_closeout_v1 import (
    build_closeout_receipt,
)


FROZEN_ROOT = Path(
    "docs/automation/"
    "TASK_V1_THROUGHPUT_SOURCEABILITY_GROUNDED_DISCOVERY_AND_SEMANTIC_GATE_CLOSEOUT_V1/"
    "fresh_current_4_32_zero_write_rehearsal/frontier_1"
)


def _discovery_contract() -> dict:
    return {
        "schema_version": "contentops.codex_source_discovery_urls.v1",
        "story_identity": "discovery-story",
        "headline_ids": ["headline-1"],
        "trigger_reason": "NO_VIABLE_DETERMINISTIC_PATH",
        "prior_blockers": ["evidence_documents_missing"],
        "candidate_urls": ["https://apnews.com/article/current-story"],
        "search_call_id": "web-search-1",
        "searched_at_utc": "2026-08-23T02:00:01Z",
        "search_snippets_included": False,
        "model_summaries_included": False,
        "candidate_urls_are_evidence": False,
        "factual_or_numeric_authority_granted": False,
        "publication_authority_granted": False,
    }


def _fake_discovery_sdk(item_types: list[str]):
    class Thread:
        def run(self, *_args, **_kwargs):
            return SimpleNamespace(
                status="completed",
                error=None,
                final_response=json.dumps(_discovery_contract()),
                items=[SimpleNamespace(type=value) for value in item_types],
                usage=SimpleNamespace(
                    total=SimpleNamespace(
                        input_tokens=10,
                        cached_input_tokens=0,
                        cache_write_input_tokens=0,
                        output_tokens=2,
                        reasoning_output_tokens=1,
                        total_tokens=12,
                    )
                ),
                duration_ms=10,
            )

    class SDK:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def account(self, **_kwargs):
            return SimpleNamespace(account=SimpleNamespace(type="chatgpt"))

        def models(self, **_kwargs):
            return SimpleNamespace(
                data=[
                    SimpleNamespace(
                        id="gpt-5.6-sol",
                        supported_reasoning_efforts=[
                            SimpleNamespace(reasoning_effort="high")
                        ],
                    )
                ]
            )

        def thread_start(self, **_kwargs):
            return Thread()

    enum = SimpleNamespace(deny_all="deny_all", read_only="read_only", high="high")
    return SDK(), enum, enum, enum, OFFICIAL_SDK_VERSION


def _discovery_request() -> dict:
    return {
        "cluster_id": "discovery-story",
        "headline_ids": ["headline-1"],
        "prior_blockers": ["evidence_documents_missing"],
        "source_adapter_families": ["public_secondary"],
        "story_context": {"why_now": "Current story"},
    }


def _aggregate_cycle_fixture(index: int) -> dict:
    candidate = {
        "cluster_id": f"aggregate-{index}",
        "evidence_status": "PASS",
        "claim_contract_status": "PASS",
        "freshness_pass": True,
        "supported_claim_count": 1,
        "evidence_document_hashes": [str(index) * 64],
        "unresolved_blockers": [],
        "writer_invoked": False,
        "article_generated": False,
    }
    discovery = (
        {
            "status": "SAME_CANDIDATE_RESUMED",
            "story_identity": f"aggregate-{index}",
            "resumed_story_identity": f"aggregate-{index}",
            "same_candidate_resumed": True,
            "search_snippet_or_model_summary_authority": False,
            "provider_receipt": {"turn_result_usage": {"total_tokens": 12}},
        }
        if index == 1
        else {}
    )
    return {
        "evidence_ready_pool": {"candidates": [candidate]},
        "ranked_viability": {
            "rank_attempts": [
                {
                    "cluster_id": f"aggregate-{index}",
                    "status": "VIABLE",
                    "blockers": (
                        ["public_source_route_suppressed_by_recent_health"]
                        if index == 2
                        else []
                    ),
                    "evidence_receipt": {
                        "autonomous_source_discovery": discovery,
                        "evidence_documents": [
                            {
                                "document_id": f"doc-{index}",
                                "source_url": f"https://apnews.com/article/{index}",
                                "canonical_content_sha256": str(index) * 64,
                                "freshness_state": "FRESH_CURRENT_OPERATOR_READINESS",
                            }
                        ],
                        "evidence_acquisition_provenance": {
                            "grounded_research": {
                                "research_calls": 1,
                                "telemetry": [
                                    {
                                        "token_usage": {
                                            "prompt_tokens": 10,
                                            "completion_tokens": 2,
                                            "total_tokens": 12,
                                        }
                                    }
                                ],
                            }
                        },
                        "provenance": {"request_count_total": 2},
                    },
                }
            ]
        },
        "prepared_candidate_state": {
            "source_route_health_input_sha256": "health-hash" if index > 1 else None
        },
        "critical_path_telemetry": {"full_rolling_headline_count": 377},
        "article_generation_attempts": 0,
        "editorial_worker_count_invoked": 0,
        "xhigh_worker_invocations": 0,
        "public_write_performed": False,
        "unknown_write_detected": False,
        "publishing_adapter_called": False,
    }


def _assignment(count: int) -> dict:
    return {
        "schema_version": "capital_chronicle.rolling_x_newsroom_assignment.v1",
        "status": "SUCCESS",
        "decision": "SELECT_STORY",
        "ranked_clusters": [
            {
                "cluster_id": f"evidence-ready-{rank}",
                "rank": rank,
                "headline_ids": [f"headline-{rank}"],
                "article_mode": "breaking",
                "resolved_article_mode": "BREAKING_BRIEF",
                "why_now": f"Distinct current governed development {rank}",
                "selection_case": f"Distinct current governed development {rank}",
                "leaf_summaries": [f"Distinct current governed development {rank}"],
                "entities_topics": [f"Entity {rank}"],
            }
            for rank in range(1, count + 1)
        ],
        "telemetry": {"logical_router_calls": 0},
    }


def _pass_receipt(request: dict) -> dict:
    rank = int(request["rank"])
    document_id = f"document-{rank}"
    proposition = f"Distinct current governed development {rank} is confirmed"
    return {
        "status": "PASS",
        "cluster_id": request["cluster_id"],
        "headline_ids": list(request["headline_ids"]),
        "provided_evidence_capabilities": list(
            request["required_evidence_capabilities"]
        ),
        "evidence_review_tier": "ENHANCED",
        "claim_evidence_contract": {
            "status": "PASS",
            "supported_claim_count": 1,
            "fabricated_claim_count": 0,
            "supported_claims": [
                {
                    "claim_id": f"claim-{rank}",
                    "claim_text": proposition,
                    "evidence_document_ids": [document_id],
                }
            ],
        },
        "evidence_documents": [
            {
                "document_id": document_id,
                "title": proposition,
                "publisher": "Associated Press",
                "source_identity": "apnews.com",
                "source_authority_class": "reputable_secondary_source",
                "source_url": f"https://apnews.com/article/current-{rank}",
                "published_at_utc": "2026-08-23T01:00:00Z",
                "event_time_utc": "2026-08-23T01:00:00Z",
                "known_at_utc": "2026-08-23T01:05:00Z",
                "canonical_content_text": proposition,
                "canonical_content_sha256": str(rank) * 64,
                "public_claim_allowed": True,
                "permission_state": "PUBLIC_CLAIM_ALLOWED",
                "freshness_state": "FRESH_CURRENT_OPERATOR_READINESS",
                "cluster_id": request["cluster_id"],
                "headline_ids": list(request["headline_ids"]),
            }
        ],
        "capital_chronicle_authority_verified": False,
        "numeric_evidence_required": False,
        "blockers": [],
        "publication_authority": False,
    }


def _run_cycle(monkeypatch, tmp_path: Path, *, count: int, **kwargs):
    assignment = _assignment(count)
    monkeypatch.setattr(
        "live_contentops.newsroom_assignment_scheduler_v1.assign_rolling_x_headlines_with_nine_router",
        lambda **_kwargs: assignment,
    )
    monkeypatch.setattr(
        "live_contentops.preselection_intelligence_v1.apply_preselection_intelligence",
        lambda clusters, **_kwargs: {
            "ranked_clusters": list(clusters),
            "preselection_logical_hash": "evidence-foundation-focused-proof",
        },
    )
    return implementation._run_rolling_x_newsroom_cycle(
        run_id="evidence-foundation-focused-proof",
        output_dir=tmp_path,
        cutoff_utc="2026-08-23T02:00:00Z",
        rolling_input={
            "schema_version": "capital_chronicle.rolling_x_headline_input.v1",
            "headlines": [],
            "counts": {"accepted": count},
        },
        story_type_by_cluster={
            f"evidence-ready-{rank}": "general_public_event"
            for rank in range(1, count + 1)
        },
        publication_enabled=False,
        published_corpus=[],
        cc_catalog={"stores": [], "root_exists": False},
        **kwargs,
    )


def test_official_url_discovery_requires_observed_web_search_and_persists_no_search_text(
    tmp_path: Path,
):
    provider = OfficialCodexUrlDiscoveryProvider(
        output_dir=tmp_path,
        sdk_factory=lambda: _fake_discovery_sdk(["userMessage", "webSearch", "agentMessage"]),
        environment={},
    )

    result = provider(_discovery_request())

    assert result["contract"]["candidate_urls"] == [
        "https://apnews.com/article/current-story"
    ]
    receipt = result["provider_receipt"]
    assert receipt["search_snippets_persisted"] is False
    assert receipt["model_summaries_persisted"] is False
    assert receipt["candidate_urls_are_evidence"] is False
    assert receipt["factual_or_numeric_authority_granted"] is False
    assert receipt["publication_authority_granted"] is False


@pytest.mark.parametrize("unexpected_item", ["commandExecution", "mcpToolCall", "fileChange"])
def test_official_url_discovery_rejects_non_search_actions_even_with_valid_url_contract(
    tmp_path: Path, unexpected_item: str
):
    provider = OfficialCodexUrlDiscoveryProvider(
        output_dir=tmp_path,
        sdk_factory=lambda: _fake_discovery_sdk(
            ["userMessage", "webSearch", unexpected_item, "agentMessage"]
        ),
        environment={},
    )

    with pytest.raises(OfficialCodexProviderError) as error:
        provider(_discovery_request())

    assert error.value.code == "CODEX_SOURCE_DISCOVERY_UNEXPECTED_ACTION_ITEM"
    assert error.value.receipt["candidate_urls_are_evidence"] is False
    assert error.value.receipt["public_write_attempted"] is False


def test_production_day_aggregator_requires_four_distinct_ready_candidates_and_zero_writer():
    receipt = build_closeout_receipt(
        [_aggregate_cycle_fixture(index) for index in range(1, 5)]
    )

    assert receipt["classification"] == (
        "PASS_V1_EVIDENCE_FOUNDATION_4_ARTICLE_READY_ZERO_WRITER"
    )
    assert receipt["ready_candidate_count"] == 4
    assert receipt["bounded_economics"]["network_requests"] == 8
    assert receipt["bounded_economics"]["grounded_research_calls"] == 4
    assert receipt["source_route_health"]["reused_across_opportunities"] is True
    assert receipt["safety"]["writer_or_article_invocations"] == 0


def test_production_day_aggregator_excludes_adjudicated_semantic_duplicate_from_yield():
    receipt = build_closeout_receipt(
        [_aggregate_cycle_fixture(index) for index in range(1, 6)],
        excluded_candidate_clusters=["aggregate-2"],
    )

    assert receipt["classification"] == (
        "PASS_V1_EVIDENCE_FOUNDATION_4_ARTICLE_READY_ZERO_WRITER"
    )
    assert receipt["ready_candidate_count"] == 4
    assert receipt["excluded_semantic_duplicate_clusters"] == ["aggregate-2"]
    assert "aggregate-2" not in {
        row["cluster_id"] for row in receipt["ready_candidates"]
    }


def test_production_day_aggregator_proves_health_carry_forward_from_monotonic_routes():
    cycles = [_aggregate_cycle_fixture(index) for index in range(1, 5)]
    for index, cycle in enumerate(cycles, start=1):
        cycle["prepared_candidate_state"] = {}
        cycle["source_route_health"] = {
            "routes": [
                {
                    "route_identity_sha256": "route-health-identity",
                    "success_count": 0,
                    "failure_count": index,
                }
            ]
        }

    receipt = build_closeout_receipt(cycles)

    carry = receipt["source_route_health"]["carry_forward_proof"]
    assert receipt["classification"] == (
        "PASS_V1_EVIDENCE_FOUNDATION_4_ARTICLE_READY_ZERO_WRITER"
    )
    assert carry["explicit_input_hash_observed"] is False
    assert carry["maximum_shared_exact_routes_between_opportunities"] == 1
    assert carry["maximum_advanced_exact_routes_between_opportunities"] == 1


def test_evidence_only_cycle_collects_four_distinct_ready_candidates_and_never_calls_writer(
    monkeypatch, tmp_path: Path
):
    result = _run_cycle(
        monkeypatch,
        tmp_path,
        count=4,
        evidence_acquirer=_pass_receipt,
        source_route_health={
            "schema_version": "contentops.source_route_health.v1",
            "routes": [],
            "hosts": [],
            "routing_only": True,
        },
        article_builder=lambda _viability: (_ for _ in ()).throw(
            AssertionError("evidence-only boundary must never invoke article builder")
        ),
        evidence_only_target_count=4,
    )

    pool = result["evidence_ready_pool"]
    assert result["classification"] == (
        "PASS_V1_EVIDENCE_FOUNDATION_4_ARTICLE_READY_ZERO_WRITER"
    )
    assert pool["target_met"] is True
    assert [row["cluster_id"] for row in pool["candidates"]] == [
        "evidence-ready-1",
        "evidence-ready-2",
        "evidence-ready-3",
        "evidence-ready-4",
    ]
    assert all(row["supported_claim_count"] >= 1 for row in pool["candidates"])
    assert all(row["freshness_pass"] is True for row in pool["candidates"])
    assert result["xhigh_worker_invocations"] == 0
    assert result["article_generation_attempts"] == 0
    assert result["public_write_performed"] is False
    assert result["source_route_health_input_sha256"]


def test_runtime_discovery_handshake_resumes_exact_same_candidate_without_hardcoded_url(
    monkeypatch, tmp_path: Path
):
    acquisition_calls: list[dict] = []
    discovery_calls: list[dict] = []

    def acquire(request):
        acquisition_calls.append(dict(request))
        if "codex_source_discovery" not in request:
            return {
                "status": "BLOCKED",
                "cluster_id": request["cluster_id"],
                "headline_ids": list(request["headline_ids"]),
                "provided_evidence_capabilities": [],
                "evidence_documents": [],
                "claim_evidence_contract": {
                    "status": "BLOCKED",
                    "supported_claim_count": 0,
                    "fabricated_claim_count": 0,
                },
                "blockers": [
                    "public_source_http_403",
                    "evidence_documents_missing",
                    "SOURCE_DISCOVERY_REQUIRED",
                ],
                "publication_authority": False,
            }
        return _pass_receipt(request)

    def discover(request):
        discovery_calls.append(dict(request))
        return {
            "contract": {
                "schema_version": "contentops.codex_source_discovery_urls.v1",
                "story_identity": request["cluster_id"],
                "headline_ids": list(request["headline_ids"]),
                "trigger_reason": "BOUNDED_ACCESS_FAILURE",
                "prior_blockers": list(request["prior_blockers"]),
                "candidate_urls": [
                    "https://apnews.com/article/runtime-discovered-not-hardcoded-by-cycle"
                ],
                "search_call_id": "focused-supported-provider-call",
                "searched_at_utc": "2026-08-23T02:00:01Z",
                "search_snippets_included": False,
                "model_summaries_included": False,
                "candidate_urls_are_evidence": False,
                "factual_or_numeric_authority_granted": False,
                "publication_authority_granted": False,
            },
            "provider_receipt": {
                "role": "V1_URL_ONLY_SOURCE_DISCOVERY",
                "reasoning_effort": "HIGH",
                "candidate_urls_are_evidence": False,
            },
        }

    result = _run_cycle(
        monkeypatch,
        tmp_path,
        count=1,
        evidence_acquirer=acquire,
        source_discoverer=discover,
        evidence_only_target_count=1,
    )

    candidate = result["evidence_ready_pool"]["candidates"][0]
    assert len(discovery_calls) == 1
    assert len(acquisition_calls) == 2
    assert acquisition_calls[0]["cluster_id"] == acquisition_calls[1]["cluster_id"]
    assert acquisition_calls[0]["headline_ids"] == acquisition_calls[1]["headline_ids"]
    assert acquisition_calls[1]["codex_source_discovery"]["candidate_urls"]
    assert candidate["cluster_id"] == "evidence-ready-1"
    assert result["xhigh_worker_invocations"] == 0


def test_frozen_editorial_output_is_losslessly_unwrapped_then_hard_article_validation_remains_fail_closed(
    tmp_path: Path,
):
    worker_return = json.loads(
        (FROZEN_ROOT / "editorial_worker_revision_return_v1.json").read_text(
            encoding="utf-8"
        )
    )
    worker_request = json.loads(
        (FROZEN_ROOT / "editorial_worker_request_v1.json").read_text(
            encoding="utf-8"
        )
    )
    resolved = resolve_article_transport_envelope(worker_return)
    assert resolved["title"] == worker_return["editorial_output"][
        "canonical_editorial_headline"
    ]
    assert resolved["substack_body_markdown"] == worker_return["editorial_output"][
        "article_body"
    ]
    assert "epistemic_claims" not in resolved

    evidence = dict(
        worker_request["bounded_governed_context"]["accepted_evidence_packet"]
    )
    cluster_id = str(evidence["cluster_id"])
    headline_ids = list(evidence["headline_ids"])
    viability = {
        "status": "SUCCESS",
        "decision": "SELECT_STORY",
        "selected_rank": 1,
        "selected_cluster_id": cluster_id,
        "selected_headline_ids": headline_ids,
        "selected_cluster": {
            "cluster_id": cluster_id,
            "headline_ids": headline_ids,
            "why_now": "Frozen transport proof",
        },
        "selected_evidence": evidence,
        "editorial_worker_request": worker_request,
        "rank_attempts": [
            {
                "rank": 1,
                "request": {
                    "story_type": "general_public_event",
                    "article_mode": "straight_news",
                    "effective_article_mode": "BREAKING_BRIEF",
                    "resolved_article_mode": "BREAKING_BRIEF",
                    "story_context": {},
                    "capital_chronicle_numeric_or_analytical_authority_required": False,
                },
                "capability_resolution": {},
            }
        ],
    }
    normalized = normalize_article_transport_representation(
        resolved,
        context={
            "institutional_edge_editorial_packet": worker_request[
                "bounded_governed_context"
            ]["institutional_edge_editorial_packet"]
        },
    )
    with pytest.raises(GroundedArticleBuilderError):
        build_rolling_x_grounded_article_and_media(
            viability,
            output_dir=tmp_path,
            article_generator=lambda _prompt: normalized,
            required_asset_count=0,
        )
