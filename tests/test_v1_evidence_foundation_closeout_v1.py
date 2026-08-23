from __future__ import annotations

import inspect
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from live_contentops import _eight_platform_substack_first_pipeline_impl_v1 as implementation
from live_contentops.eight_platform_substack_first_pipeline_v1 import (
    run_rolling_x_newsroom_cycle,
)
from live_contentops.official_codex_provider_v1 import (
    OFFICIAL_SDK_VERSION,
    OfficialCodexProviderError,
)
from live_contentops.official_codex_source_discovery_v1 import (
    OfficialCodexUrlDiscoveryProvider,
)
from live_contentops.quota_efficient_source_discovery_v1 import (
    QuotaEfficientSourceDiscoverySession,
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
from scripts.prove_v1_quota_efficient_batch_tail_discovery_v1 import (
    build_acceptance_receipt,
)
from scripts import prove_v1_quota_efficient_batch_tail_discovery_v1 as quota_proof


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


def _fake_batch_discovery_sdk(*, mutate_contract=None, runtime_error: str | None = None):
    class Thread:
        def run(self, prompt, **_kwargs):
            if runtime_error is not None:
                raise RuntimeError(runtime_error)
            prompt_input = json.loads(prompt.rsplit("\n\n", 1)[1])
            story_results = []
            for index, request in enumerate(
                prompt_input["story_requests"], start=1
            ):
                story_results.append(
                    {
                        "schema_version": (
                            "contentops.codex_source_discovery_urls.v1"
                        ),
                        "story_identity": request["story_identity"],
                        "headline_ids": list(request["headline_ids"]),
                        "trigger_reason": "BOUNDED_ACCESS_FAILURE",
                        "prior_blockers": list(request["prior_blockers"]),
                        "candidate_urls": [
                            f"https://apnews.com/article/batch-sdk-{index}"
                        ],
                        "search_call_id": f"batch-sdk-search-{index}",
                        "searched_at_utc": "2026-08-23T02:00:01Z",
                        "search_snippets_included": False,
                        "model_summaries_included": False,
                        "candidate_urls_are_evidence": False,
                        "factual_or_numeric_authority_granted": False,
                        "publication_authority_granted": False,
                    }
                )
            contract = {
                "schema_version": (
                    "contentops.codex_source_discovery_batch_urls.v1"
                ),
                "batch_id": prompt_input["batch_id"],
                "pass_kind": prompt_input["pass_kind"],
                "story_results": story_results,
                "search_snippets_included": False,
                "model_summaries_included": False,
                "candidate_urls_are_evidence": False,
                "factual_or_numeric_authority_granted": False,
                "publication_authority_granted": False,
            }
            if callable(mutate_contract):
                contract = mutate_contract(contract)
            return SimpleNamespace(
                status="completed",
                error=None,
                final_response=json.dumps(contract),
                items=[
                    SimpleNamespace(type="userMessage"),
                    SimpleNamespace(type="webSearch"),
                    SimpleNamespace(type="agentMessage"),
                ],
                usage=SimpleNamespace(
                    total=SimpleNamespace(
                        input_tokens=20,
                        cached_input_tokens=0,
                        cache_write_input_tokens=0,
                        output_tokens=4,
                        reasoning_output_tokens=2,
                        total_tokens=24,
                    )
                ),
                duration_ms=20,
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
            "claim_contract_sha256": f"claim-contract-{rank}",
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


def _source_discovery_required_receipt(request: dict) -> dict:
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


def _contract_for_request(request: dict, *, suffix: str) -> dict:
    return {
        "schema_version": "contentops.codex_source_discovery_urls.v1",
        "story_identity": request["cluster_id"],
        "headline_ids": list(request["headline_ids"]),
        "trigger_reason": "BOUNDED_ACCESS_FAILURE",
        "prior_blockers": list(request["prior_blockers"]),
        "candidate_urls": [f"https://apnews.com/article/{suffix}"],
        "search_call_id": f"batch-search-{suffix}",
        "searched_at_utc": "2026-08-23T02:00:01Z",
        "search_snippets_included": False,
        "model_summaries_included": False,
        "candidate_urls_are_evidence": False,
        "factual_or_numeric_authority_granted": False,
        "publication_authority_granted": False,
    }


class _BatchDiscoveryFixture:
    def __init__(
        self,
        *,
        unresolved_in_batch: set[str] | None = None,
        tokens_by_pass: dict[str, int] | None = None,
        cross_bind: bool = False,
    ) -> None:
        self.unresolved_in_batch = set(unresolved_in_batch or set())
        self.tokens_by_pass = dict(tokens_by_pass or {"BATCH": 100, "TAIL": 50})
        self.cross_bind = cross_bind
        self.calls: list[dict] = []

    def discover_batch(self, requests, *, pass_kind):
        request_rows = [dict(request) for request in requests]
        self.calls.append(
            {
                "pass_kind": pass_kind,
                "story_membership": [row["cluster_id"] for row in request_rows],
            }
        )
        contracts = [
            _contract_for_request(
                request,
                suffix=f"{pass_kind.casefold()}-{index}",
            )
            for index, request in enumerate(request_rows, start=1)
            if not (
                pass_kind == "BATCH"
                and request["cluster_id"] in self.unresolved_in_batch
            )
        ]
        if self.cross_bind and contracts:
            contracts[0] = {
                **contracts[0],
                "headline_ids": ["headline-from-another-story"],
            }
        return {
            "contracts": contracts,
            "provider_receipt": {
                "schema_version": (
                    "contentops.official_codex_url_discovery_batch_receipt.v1"
                ),
                "pass_kind": pass_kind,
                "turn_result_usage": {
                    "total_tokens": self.tokens_by_pass.get(pass_kind, 0)
                },
                "search_snippets_persisted": False,
                "model_summaries_persisted": False,
                "candidate_urls_are_evidence": False,
                "public_write_attempted": False,
            },
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


def test_official_url_discovery_batch_returns_exact_isolated_contracts_in_one_turn(
    tmp_path: Path,
):
    provider = OfficialCodexUrlDiscoveryProvider(
        output_dir=tmp_path,
        sdk_factory=lambda: _fake_batch_discovery_sdk(),
        environment={},
    )
    requests = [
        {
            **_discovery_request(),
            "cluster_id": f"batch-story-{index}",
            "headline_ids": [f"batch-headline-{index}"],
        }
        for index in range(1, 4)
    ]

    result = provider.discover_batch(requests, pass_kind="BATCH")

    assert provider.call_count == 1
    assert [row["story_identity"] for row in result["contracts"]] == [
        "batch-story-1",
        "batch-story-2",
        "batch-story-3",
    ]
    receipt = result["provider_receipt"]
    assert receipt["story_count"] == 3
    assert receipt["resolved_story_count"] == 3
    assert receipt["turn_result_usage"]["total_tokens"] == 24
    assert receipt["search_snippets_persisted"] is False
    assert receipt["model_summaries_persisted"] is False
    assert receipt["candidate_urls_are_evidence"] is False
    assert receipt["public_write_attempted"] is False


def test_official_url_discovery_batch_rejects_cross_bound_headline_identity(
    tmp_path: Path,
):
    def cross_bind(contract):
        contract["story_results"][0]["headline_ids"] = ["wrong-headline"]
        return contract

    provider = OfficialCodexUrlDiscoveryProvider(
        output_dir=tmp_path,
        sdk_factory=lambda: _fake_batch_discovery_sdk(
            mutate_contract=cross_bind
        ),
        environment={},
    )
    requests = [
        {
            **_discovery_request(),
            "cluster_id": f"batch-story-{index}",
            "headline_ids": [f"batch-headline-{index}"],
        }
        for index in range(1, 3)
    ]

    with pytest.raises(OfficialCodexProviderError) as error:
        provider.discover_batch(requests, pass_kind="BATCH")

    assert error.value.code == "CODEX_SOURCE_DISCOVERY_BATCH_CONTRACT_INVALID"
    assert error.value.receipt["candidate_urls_persisted"] is False
    assert error.value.receipt["candidate_urls_are_evidence"] is False
    assert error.value.receipt["public_write_attempted"] is False


def test_official_url_discovery_batch_rejects_model_summary_authority(
    tmp_path: Path,
):
    def add_summary_authority(contract):
        contract["model_summaries_included"] = True
        return contract

    provider = OfficialCodexUrlDiscoveryProvider(
        output_dir=tmp_path,
        sdk_factory=lambda: _fake_batch_discovery_sdk(
            mutate_contract=add_summary_authority
        ),
        environment={},
    )

    with pytest.raises(OfficialCodexProviderError) as error:
        provider.discover_batch([_discovery_request()], pass_kind="BATCH")

    assert error.value.code == "CODEX_SOURCE_DISCOVERY_BATCH_CONTRACT_INVALID"
    assert error.value.receipt["model_summaries_persisted"] is False
    assert error.value.receipt["factual_or_numeric_authority_granted"] is False


def test_official_url_discovery_batch_classifies_chatgpt_usage_limit_without_turn(
    tmp_path: Path,
):
    provider = OfficialCodexUrlDiscoveryProvider(
        output_dir=tmp_path,
        sdk_factory=lambda: _fake_batch_discovery_sdk(
            runtime_error="You've hit your usage limit. Purchase more credits."
        ),
        environment={},
    )

    with pytest.raises(OfficialCodexProviderError) as error:
        provider.discover_batch([_discovery_request()], pass_kind="BATCH")

    assert error.value.code == "CHATGPT_USAGE_LIMIT_REACHED"
    assert error.value.phase == "TURN_EXECUTION"
    assert error.value.model_turn_completed is False
    assert error.value.receipt == {}


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
    assert int(result.get("xhigh_worker_invocations") or 0) == 0
    assert int(result.get("article_generation_attempts") or 0) == 0
    assert result["public_write_performed"] is False
    assert result["source_route_health_input_sha256"]


def test_quota_efficient_cycle_shares_one_batch_turn_across_four_exact_story_identities(
    monkeypatch, tmp_path: Path
):
    acquisition_calls: list[dict] = []
    discoverer = _BatchDiscoveryFixture(tokens_by_pass={"BATCH": 120})

    def acquire(request):
        acquisition_calls.append(dict(request))
        if "codex_source_discovery" not in request:
            return _source_discovery_required_receipt(request)
        assert request["codex_source_discovery"]["candidate_urls_are_evidence"] is False
        return _pass_receipt(request)

    result = _run_cycle(
        monkeypatch,
        tmp_path,
        count=4,
        evidence_acquirer=acquire,
        source_discoverer=discoverer,
        evidence_only_target_count=4,
        article_builder=lambda _viability: (_ for _ in ()).throw(
            AssertionError("batch evidence proof must not invoke article builder")
        ),
    )

    accounting = result["quota_efficient_source_discovery"]
    assert result["classification"] == (
        "PASS_V1_QUOTA_EFFICIENT_BATCH_TAIL_DISCOVERY_ECONOMICAL_READY_POOL"
    )
    assert [row["cluster_id"] for row in result["evidence_ready_pool"]["candidates"]] == [
        "evidence-ready-1",
        "evidence-ready-2",
        "evidence-ready-3",
        "evidence-ready-4",
    ]
    assert discoverer.calls == [
        {
            "pass_kind": "BATCH",
            "story_membership": [
                "evidence-ready-1",
                "evidence-ready-2",
                "evidence-ready-3",
                "evidence-ready-4",
            ],
        }
    ]
    assert accounting["batch_discovery_turns"] == 1
    assert accounting["tail_discovery_turns"] == 0
    assert accounting["total_discovery_turns"] == 1
    assert accounting["accounted_discovery_tokens"] == 120
    assert accounting["candidates_covered_per_turn"] == [4]
    assert len(acquisition_calls) == 8
    assert result["xhigh_worker_invocations"] == 0
    assert result["article_generation_attempts"] == 0
    assert result["publishing_adapter_called"] is False
    assert result["public_write_performed"] is False
    assert result["unknown_write_detected"] is False


def test_deterministically_viable_frontier_causes_zero_discovery_turns(
    monkeypatch, tmp_path: Path
):
    discoverer = _BatchDiscoveryFixture()

    result = _run_cycle(
        monkeypatch,
        tmp_path,
        count=4,
        evidence_acquirer=_pass_receipt,
        source_discoverer=discoverer,
        evidence_only_target_count=4,
    )

    accounting = result["quota_efficient_source_discovery"]
    assert discoverer.calls == []
    assert accounting["total_discovery_turns"] == 0
    assert accounting["accounted_discovery_tokens"] == 0
    assert accounting["ready_candidate_yield"] == 4


def test_autonomous_batch_tail_path_propagates_unchanged_coordinator_request_ceiling(
    monkeypatch, tmp_path: Path
):
    observed: dict[str, int] = {}

    def default_acquirer_factory(**kwargs):
        observed["coordinated_request_ceiling"] = int(
            kwargs["coordinated_request_ceiling"]
        )
        return _pass_receipt

    monkeypatch.setattr(
        implementation,
        "_default_rolling_x_evidence_acquirer",
        default_acquirer_factory,
    )

    result = _run_cycle(
        monkeypatch,
        tmp_path,
        count=4,
        autonomous_source_discovery_enabled=True,
        source_discoverer=_BatchDiscoveryFixture(),
        evidence_only_target_count=4,
    )

    assert observed == {"coordinated_request_ceiling": 96}
    assert result["quota_efficient_source_discovery"]["budget"][
        "max_deterministic_network_requests"
    ] == 96
    assert result["evidence_ready_pool"]["ready_candidate_count"] == 4


def test_tail_skips_batch_unresolved_stories_without_a_prior_eligible_url(
    monkeypatch, tmp_path: Path
):
    unresolved = {"evidence-ready-2", "evidence-ready-3", "evidence-ready-4"}
    discoverer = _BatchDiscoveryFixture(unresolved_in_batch=unresolved)

    def acquire(request):
        if "codex_source_discovery" not in request:
            return _source_discovery_required_receipt(request)
        return _pass_receipt(request)

    result = _run_cycle(
        monkeypatch,
        tmp_path,
        count=4,
        evidence_acquirer=acquire,
        source_discoverer=discoverer,
        evidence_only_target_count=4,
    )

    accounting = result["quota_efficient_source_discovery"]
    assert [row["pass_kind"] for row in discoverer.calls] == ["BATCH"]
    assert discoverer.calls[0]["story_membership"] == [
        "evidence-ready-1",
        "evidence-ready-2",
        "evidence-ready-3",
        "evidence-ready-4",
    ]
    assert accounting["batch_discovery_turns"] == 1
    assert accounting["tail_discovery_turns"] == 0
    assert accounting["tail_is_subset_only"] is True
    assert accounting["each_story_reaches_tail_at_most_once"] is True
    skipped = {
        row["story_identity"]: row["decision"]
        for row in accounting["tail_retry_decisions"]
    }
    assert skipped == {
        "evidence-ready-2": "SKIP_NO_PRIOR_ELIGIBLE_URL",
        "evidence-ready-3": "SKIP_NO_PRIOR_ELIGIBLE_URL",
        "evidence-ready-4": "SKIP_NO_PRIOR_ELIGIBLE_URL",
    }


def test_tail_uses_one_distinct_route_only_after_concrete_access_failure(
    monkeypatch, tmp_path: Path
):
    class TailCaptureDiscovery(_BatchDiscoveryFixture):
        def __init__(self):
            super().__init__()
            self.tail_prior_urls: dict[str, list[str]] = {}

        def discover_batch(self, requests, *, pass_kind):
            rows = [dict(request) for request in requests]
            if pass_kind == "TAIL":
                self.tail_prior_urls = {
                    row["cluster_id"]: list(row.get("prior_discovered_urls") or [])
                    for row in rows
                }
            return super().discover_batch(rows, pass_kind=pass_kind)

    discoverer = TailCaptureDiscovery()

    def acquire(request):
        contract = dict(request.get("codex_source_discovery") or {})
        if not contract:
            return _source_discovery_required_receipt(request)
        urls = [str(value) for value in contract.get("candidate_urls") or []]
        if any("batch-" in value for value in urls):
            blocked = _source_discovery_required_receipt(request)
            blocked["blockers"] = [
                *blocked["blockers"],
                "HTTP Error 403: Forbidden",
                "public_source_redirect_authority_invalid",
            ]
            return blocked
        return _pass_receipt(request)

    result = _run_cycle(
        monkeypatch,
        tmp_path,
        count=1,
        evidence_acquirer=acquire,
        source_discoverer=discoverer,
        evidence_only_target_count=1,
    )

    accounting = result["quota_efficient_source_discovery"]
    assert [row["pass_kind"] for row in discoverer.calls] == ["BATCH", "TAIL"]
    assert discoverer.tail_prior_urls == {
        "evidence-ready-1": ["https://apnews.com/article/batch-1"]
    }
    assert accounting["tail_retry_decisions"] == [
        {
            "story_identity": "evidence-ready-1",
            "headline_ids": ["headline-1"],
            "decision": "ELIGIBLE_DISTINCT_ROUTE_AFTER_ACCESS_FAILURE",
            "prior_discovered_url_count": 1,
            "concrete_access_failures": [
                "HTTP Error 403: Forbidden",
                "public_source_redirect_authority_invalid",
            ],
            "distinct_route_required": True,
        }
    ]
    assert accounting["turns"][0]["ready_candidate_gain"] == 0
    assert accounting["turns"][1]["ready_candidate_gain"] == 1
    assert result["evidence_ready_pool"]["ready_candidate_count"] == 1


def test_productive_batch_defers_eligible_tail_while_fresh_unseen_work_remains(
    monkeypatch, tmp_path: Path
):
    discoverer = _BatchDiscoveryFixture()

    def acquire(request):
        contract = dict(request.get("codex_source_discovery") or {})
        if not contract:
            return _source_discovery_required_receipt(request)
        if request["cluster_id"] == "evidence-ready-1":
            return _pass_receipt(request)
        blocked = _source_discovery_required_receipt(request)
        blocked["blockers"] = [
            *blocked["blockers"],
            "HTTP Error 403: Forbidden",
        ]
        return blocked

    result = _run_cycle(
        monkeypatch,
        tmp_path,
        count=2,
        evidence_acquirer=acquire,
        source_discoverer=discoverer,
        evidence_only_target_count=2,
        quota_discovery_fresh_unseen_available=True,
    )

    accounting = result["quota_efficient_source_discovery"]
    assert [row["pass_kind"] for row in discoverer.calls] == ["BATCH"]
    assert accounting["allocation_decisions"] == [
        {
            "decision": "DEFER_TAIL_FOR_FRESH_UNSEEN_BATCH",
            "after_turn_number": 1,
            "batch_resolved_story_count": 2,
            "batch_candidate_story_count": 2,
            "reason": "FRESH_BATCH_MARGINAL_URL_YIELD_REMAINS_USEFUL",
        }
    ]
    assert accounting["turns"][0]["ready_candidate_gain"] == 1
    assert accounting["turns"][0]["marginal_url_yield"] == 1.0
    assert accounting["turns"][0]["marginal_ready_yield"] == 0.5


def test_batch_cross_story_binding_fails_closed_before_deterministic_resume(
    monkeypatch, tmp_path: Path
):
    discoverer = _BatchDiscoveryFixture(cross_bind=True)
    resumed_calls: list[dict] = []

    def acquire(request):
        if "codex_source_discovery" in request:
            resumed_calls.append(dict(request))
        return _source_discovery_required_receipt(request)

    result = _run_cycle(
        monkeypatch,
        tmp_path,
        count=2,
        evidence_acquirer=acquire,
        source_discoverer=discoverer,
        evidence_only_target_count=1,
    )

    accounting = result["quota_efficient_source_discovery"]
    assert resumed_calls == []
    assert accounting["status"] == "PASS"
    assert {
        row["failure_code"] for row in accounting["failures"]
    } == {"quota_discovery_provider_cross_story_binding"}
    assert result["classification"] == "NO_PUBLICATION"


def test_discovery_token_ceiling_rejects_contracts_and_stops_before_tail(
    monkeypatch, tmp_path: Path
):
    discoverer = _BatchDiscoveryFixture(
        tokens_by_pass={"BATCH": 2_000_001, "TAIL": 1}
    )
    resumed_calls: list[dict] = []

    def acquire(request):
        if "codex_source_discovery" in request:
            resumed_calls.append(dict(request))
        return _source_discovery_required_receipt(request)

    result = _run_cycle(
        monkeypatch,
        tmp_path,
        count=2,
        evidence_acquirer=acquire,
        source_discoverer=discoverer,
        evidence_only_target_count=1,
    )

    accounting = result["quota_efficient_source_discovery"]
    assert resumed_calls == []
    assert [row["pass_kind"] for row in discoverer.calls] == ["BATCH"]
    assert accounting["status"] == "BLOCKED"
    assert accounting["terminal_budget_blocker"] == (
        "URL_DISCOVERY_TOKEN_CEILING_EXCEEDED"
    )
    assert result["exact_next_blocker"] == "URL_DISCOVERY_TOKEN_CEILING_EXCEEDED"


def test_discovery_turn_ceiling_fails_closed_without_per_candidate_fallback():
    discoverer = _BatchDiscoveryFixture(unresolved_in_batch={"story-1", "story-2"})

    def acquire(request):
        return _source_discovery_required_receipt(request)

    requests = [
        {
            "cluster_id": f"story-{index}",
            "headline_ids": [f"headline-{index}"],
            "rank": index,
            "request_logical_hash": f"request-{index}",
        }
        for index in range(1, 3)
    ]
    session = QuotaEfficientSourceDiscoverySession(
        evidence_acquirer=acquire,
        source_discoverer=discoverer,
        max_batch_turns=1,
        max_tail_turns=1,
        max_total_turns=1,
    )
    attempts = []
    for request in requests:
        receipt = session.acquire(request)
        attempts.append(
            {
                "rank": request["rank"],
                "request": request,
                "evidence_receipt": receipt,
                "blockers": list(receipt["blockers"]),
            }
        )
    viability = {"rank_attempts": attempts}

    batch = session.discover_unresolved(viability, pass_kind="BATCH")
    next_request = {
        "cluster_id": "story-3",
        "headline_ids": ["headline-3"],
        "rank": 3,
        "request_logical_hash": "request-3",
    }
    next_receipt = session.acquire(next_request)
    second_batch = session.discover_unresolved(
        {
            "rank_attempts": [
                {
                    "rank": 3,
                    "request": next_request,
                    "evidence_receipt": next_receipt,
                    "blockers": list(next_receipt["blockers"]),
                }
            ]
        },
        pass_kind="BATCH",
    )

    assert batch == {"called": True, "new_contract_count": 0}
    assert second_batch["called"] is False
    assert second_batch["blocker"] == "URL_DISCOVERY_TURN_CEILING_EXCEEDED"
    assert len(discoverer.calls) == 1
    assert session.snapshot()["status"] == "BLOCKED"


def test_production_day_quota_carries_turns_tokens_requests_and_exact_residual():
    production_day_id = "newsroom-production-day-2026-08-23-bangkok"
    prior = {
        "schema_version": "contentops.quota_efficient_source_discovery.v1",
        "newsroom_production_day_id": production_day_id,
        "accounting_complete": True,
        "turns": [
            {
                "turn_number": 1,
                "pass_kind": "BATCH",
                "candidate_story_count": 1,
                "accounted_discovery_tokens": 100,
            }
        ],
        "deterministic_acquisition_calls": 1,
        "deterministic_network_requests": 70,
        "cache_and_reuse": {},
        "batch_covered_story_membership": [
            {"story_identity": "prior-story", "headline_ids": ["prior-headline"]}
        ],
        "tail_covered_story_membership": [],
        "deterministic_frontier": [],
        "failures": [],
    }
    discoverer = _BatchDiscoveryFixture(tokens_by_pass={"BATCH": 50})

    def acquire(request):
        receipt = _source_discovery_required_receipt(request)
        receipt["evidence_acquisition_provenance"] = {
            "grounded_research": {"public_retrieval_requests": 20}
        }
        return receipt

    session = QuotaEfficientSourceDiscoverySession(
        evidence_acquirer=acquire,
        source_discoverer=discoverer,
        newsroom_production_day_id=production_day_id,
        prior_accounting=prior,
    )
    request = {
        "cluster_id": "new-story",
        "headline_ids": ["new-headline"],
        "rank": 1,
        "request_logical_hash": "new-request",
    }
    initial = session.acquire(request)
    viability = {
        "rank_attempts": [
            {
                "rank": 1,
                "request": request,
                "evidence_receipt": initial,
                "blockers": list(initial["blockers"]),
            }
        ]
    }
    assert session.discover_unresolved(viability, pass_kind="BATCH")[
        "new_contract_count"
    ] == 1
    snapshot = session.snapshot()

    assert snapshot["batch_discovery_turns"] == 2
    assert snapshot["total_discovery_turns"] == 2
    assert snapshot["accounted_discovery_tokens"] == 150
    assert snapshot["deterministic_network_requests"] == 90
    assert snapshot["turns"][-1]["deterministic_network_requests"] == 20
    assert snapshot["remaining_budget"] == {
        "batch_turns": 0,
        "tail_turns": 2,
        "total_turns": 2,
        "accounted_discovery_tokens": 1_999_850,
        "deterministic_network_requests": 6,
    }
    assert snapshot["prior_accounting_sha256"]


def test_production_day_quota_rejects_cross_day_reset():
    prior = {
        "schema_version": "contentops.quota_efficient_source_discovery.v1",
        "newsroom_production_day_id": "newsroom-production-day-2026-08-22-bangkok",
    }
    with pytest.raises(ValueError, match="production_day_identity_mismatch"):
        QuotaEfficientSourceDiscoverySession(
            evidence_acquirer=_pass_receipt,
            source_discoverer=_BatchDiscoveryFixture(),
            newsroom_production_day_id=(
                "newsroom-production-day-2026-08-23-bangkok"
            ),
            prior_accounting=prior,
        )


def test_production_day_quota_fails_closed_at_shared_turn_token_and_request_ceiling():
    production_day_id = "newsroom-production-day-2026-08-23-bangkok"
    evidence_calls: list[dict] = []
    provider = _BatchDiscoveryFixture()

    def acquire(request):
        evidence_calls.append(dict(request))
        return _source_discovery_required_receipt(request)

    request_ceiling_prior = {
        "schema_version": "contentops.quota_efficient_source_discovery.v1",
        "newsroom_production_day_id": production_day_id,
        "accounting_complete": True,
        "turns": [],
        "deterministic_network_requests": 96,
        "cache_and_reuse": {},
        "batch_covered_story_membership": [],
        "tail_covered_story_membership": [],
        "deterministic_frontier": [],
        "failures": [],
    }
    request_session = QuotaEfficientSourceDiscoverySession(
        evidence_acquirer=acquire,
        source_discoverer=provider,
        newsroom_production_day_id=production_day_id,
        prior_accounting=request_ceiling_prior,
    )
    blocked = request_session.acquire(
        {"cluster_id": "story-request", "headline_ids": ["headline-request"]}
    )
    assert evidence_calls == []
    assert blocked["blockers"] == [
        "URL_DISCOVERY_DETERMINISTIC_REQUEST_CEILING_EXCEEDED"
    ]

    token_ceiling_prior = {
        **request_ceiling_prior,
        "deterministic_network_requests": 0,
        "turns": [
            {
                "turn_number": 1,
                "pass_kind": "BATCH",
                "candidate_story_count": 1,
                "accounted_discovery_tokens": 2_000_000,
            }
        ],
    }
    token_session = QuotaEfficientSourceDiscoverySession(
        evidence_acquirer=acquire,
        source_discoverer=provider,
        newsroom_production_day_id=production_day_id,
        prior_accounting=token_ceiling_prior,
    )
    request = {
        "cluster_id": "story-token",
        "headline_ids": ["headline-token"],
        "rank": 1,
    }
    initial = token_session.acquire(request)
    result = token_session.discover_unresolved(
        {
            "rank_attempts": [
                {
                    "rank": 1,
                    "request": request,
                    "evidence_receipt": initial,
                    "blockers": list(initial["blockers"]),
                }
            ]
        },
        pass_kind="BATCH",
    )
    assert result == {
        "called": False,
        "new_contract_count": 0,
        "blocker": "URL_DISCOVERY_TOKEN_CEILING_EXCEEDED",
    }
    assert provider.calls == []


def test_later_cycle_receives_only_residual_coordinated_request_allowance(
    monkeypatch, tmp_path: Path
):
    observed: dict[str, int] = {}
    production_day_id = "newsroom-production-day-2026-08-23-bangkok"
    prior = {
        "schema_version": "contentops.quota_efficient_source_discovery.v1",
        "newsroom_production_day_id": production_day_id,
        "accounting_complete": True,
        "turns": [],
        "deterministic_network_requests": 70,
        "cache_and_reuse": {},
        "batch_covered_story_membership": [],
        "tail_covered_story_membership": [],
        "deterministic_frontier": [],
        "failures": [],
    }

    def default_acquirer_factory(**kwargs):
        observed["coordinated_request_ceiling"] = int(
            kwargs["coordinated_request_ceiling"]
        )
        return _pass_receipt

    monkeypatch.setattr(
        implementation,
        "_default_rolling_x_evidence_acquirer",
        default_acquirer_factory,
    )
    result = _run_cycle(
        monkeypatch,
        tmp_path,
        count=1,
        autonomous_source_discovery_enabled=True,
        source_discoverer=_BatchDiscoveryFixture(),
        evidence_only_target_count=1,
        newsroom_production_day_id=production_day_id,
        quota_discovery_prior_accounting=prior,
    )

    assert observed == {"coordinated_request_ceiling": 26}
    accounting = result["quota_efficient_source_discovery"]
    assert accounting["deterministic_network_requests"] == 70
    assert accounting["remaining_budget"]["deterministic_network_requests"] == 26


def test_same_candidate_request_reuses_governed_resumed_receipt_without_rediscovery():
    discoverer = _BatchDiscoveryFixture()
    acquisition_calls: list[dict] = []

    def acquire(request):
        acquisition_calls.append(dict(request))
        if "codex_source_discovery" not in request:
            return _source_discovery_required_receipt(request)
        return _pass_receipt(request)

    request = {
        "cluster_id": "evidence-ready-1",
        "headline_ids": ["headline-1"],
        "rank": 1,
        "required_evidence_capabilities": [
            "credible_event_confirmation",
            "basic_attributed_facts",
        ],
        "request_logical_hash": "same-request-hash",
    }
    session = QuotaEfficientSourceDiscoverySession(
        evidence_acquirer=acquire,
        source_discoverer=discoverer,
    )
    initial = session.acquire(request)
    viability = {
        "rank_attempts": [
            {
                "rank": 1,
                "request": request,
                "evidence_receipt": initial,
                "blockers": list(initial["blockers"]),
            }
        ]
    }

    assert session.discover_unresolved(viability, pass_kind="BATCH")[
        "new_contract_count"
    ] == 1
    first = session.acquire(request)
    second = session.acquire(request)

    assert first["status"] == "PASS"
    assert second == first
    assert len(discoverer.calls) == 1
    assert len(acquisition_calls) == 2
    assert session.snapshot()["cache_and_reuse"]["resumed_receipt_cache_hits"] == 1


def test_acceptance_receipt_reports_current_host_runtime_proof_required_for_usage_limit(
    tmp_path: Path,
):
    cycle = {
        "quota_efficient_source_discovery": {
            "status": "PASS",
            "accounting_complete": True,
            "batch_discovery_turns": 0,
            "tail_discovery_turns": 0,
            "total_discovery_turns": 0,
            "accounted_discovery_tokens": 0,
            "deterministic_network_requests": 2,
            "failures": [
                {
                    "failure_code": "CHATGPT_USAGE_LIMIT_REACHED",
                    "model_turn_completed": False,
                }
            ],
            "candidate_urls_are_evidence": False,
            "tail_is_subset_only": True,
        },
        "evidence_ready_pool": {"candidates": []},
        "ranked_viability": {"rank_attempts": []},
        "critical_path_telemetry": {"article_writer_semantic_calls": 0},
        "article_generation_attempts": 0,
        "public_write_performed": False,
        "publishing_adapter_called": False,
        "unknown_write_detected": False,
        "exact_next_blocker": "ALL_RANKED_CLUSTERS_EVIDENCE_BLOCKED",
    }

    receipt = build_acceptance_receipt(
        cycle,
        cutoff_utc="2026-08-23T02:00:00Z",
        prepared_state={
            "full_rolling_headline_count": 10,
            "prepared_candidate_count": 4,
        },
        runtime_output_dir=tmp_path,
    )

    assert receipt["classification"] == "CURRENT_HOST_RUNTIME_PROOF_REQUIRED"
    assert receipt["exact_remaining_blocker"] == "CHATGPT_USAGE_LIMIT_REACHED"


def test_ordinary_minimum_packet_pass_does_not_invent_supported_claim_requirement(
    tmp_path: Path,
):
    candidates = []
    attempts = []
    for index in range(1, 5):
        cluster_id = f"ordinary-{index}"
        headline_id = f"ordinary-headline-{index}"
        document_id = f"ordinary-document-{index}"
        candidates.append(
            {
                "cluster_id": cluster_id,
                "headline_ids": [headline_id],
                "evidence_status": "PASS",
                "freshness_pass": True,
                "supported_claim_count": 0,
                "unresolved_blockers": [],
                "writer_invoked": False,
                "article_generated": False,
            }
        )
        attempts.append(
            {
                "rank": index,
                "cluster_id": cluster_id,
                "headline_ids": [headline_id],
                "status": "VIABLE",
                "evidence_receipt": {
                    "status": "PASS",
                    "evidence_review_tier": "ORDINARY_MINIMUM",
                    "minimum_trustworthy_evidence_packet": {
                        "status": "PASS",
                        "risk_tier": "ORDINARY",
                        "core_factual_proposition": (
                            f"Directly bound ordinary proposition {index}"
                        ),
                        "source_url": f"https://apnews.com/article/ordinary-{index}",
                        "evidence_document_id": document_id,
                        "evidence_packet_sha256": f"ordinary-packet-{index}",
                    },
                    "evidence_documents": [
                        {
                            "document_id": document_id,
                            "publisher": "Associated Press",
                            "source_url": (
                                f"https://apnews.com/article/ordinary-{index}"
                            ),
                            "canonical_content_sha256": str(index) * 64,
                            "freshness_state": "FRESH_CURRENT_OPERATOR_READINESS",
                            "public_claim_allowed": True,
                        }
                    ],
                    "blockers": [],
                },
            }
        )
    cycle = {
        "quota_efficient_source_discovery": {
            "schema_version": "contentops.quota_efficient_source_discovery.v1",
            "status": "PASS",
            "accounting_complete": True,
            "batch_discovery_turns": 1,
            "tail_discovery_turns": 0,
            "total_discovery_turns": 1,
            "accounted_discovery_tokens": 100,
            "deterministic_network_requests": 4,
            "failures": [],
            "candidate_urls_are_evidence": False,
            "tail_is_subset_only": True,
        },
        "evidence_ready_pool": {"candidates": candidates},
        "ranked_viability": {"rank_attempts": attempts},
        "critical_path_telemetry": {"article_writer_semantic_calls": 0},
        "article_generation_attempts": 0,
        "public_write_performed": False,
        "publishing_adapter_called": False,
        "unknown_write_detected": False,
    }

    receipt = build_acceptance_receipt(
        cycle,
        cutoff_utc="2026-08-23T15:00:00Z",
        prepared_state={
            "full_rolling_headline_count": 12,
            "prepared_candidate_count": 4,
        },
        runtime_output_dir=tmp_path,
    )

    assert receipt["classification"] == (
        "PASS_V1_QUOTA_EFFICIENT_BATCH_TAIL_DISCOVERY_ECONOMICAL_READY_POOL"
    )
    assert all(
        row["ready_contract_kind"]
        == "ORDINARY_MINIMUM_TRUSTWORTHY_EVIDENCE_PACKET"
        and row["ready_contract_status"] == "PASS"
        and row["supported_claim_count"] == 0
        for row in receipt["ready_candidates"]
    )


def test_enhanced_ready_contract_still_requires_supported_claim():
    document = {
        "document_id": "enhanced-document",
        "publisher": "Associated Press",
        "source_url": "https://apnews.com/article/enhanced",
        "canonical_content_sha256": "a" * 64,
        "freshness_state": "FRESH_CURRENT_OPERATOR_READINESS",
        "public_claim_allowed": True,
    }
    base = {
        "evidence_review_tier": "ENHANCED",
        "evidence_documents": [document],
        "blockers": [],
    }
    blocked = quota_proof._ready_contract(
        {
            **base,
            "claim_evidence_contract": {
                "status": "PASS",
                "supported_claims": [],
                "supported_claim_count": 0,
                "fabricated_claim_count": 0,
                "claim_contract_sha256": "enhanced-empty",
            },
        }
    )
    passed = quota_proof._ready_contract(
        {
            **base,
            "claim_evidence_contract": {
                "status": "PASS",
                "supported_claims": [
                    {
                        "claim_id": "claim-1",
                        "evidence_document_ids": ["enhanced-document"],
                    }
                ],
                "supported_claim_count": 1,
                "fabricated_claim_count": 0,
                "claim_contract_sha256": "enhanced-supported",
            },
        }
    )

    assert blocked["status"] == "BLOCKED"
    assert passed["status"] == "PASS"
    assert passed["contract_sha256"] == "enhanced-supported"


def test_multi_frontier_runner_freezes_universe_carries_budget_health_and_identities(
    monkeypatch, tmp_path: Path
):
    headline_ids = [f"headline-{index}" for index in range(1, 5)]
    rolling_input = {
        "schema_version": "capital_chronicle.rolling_x_headline_input.v1",
        "unique_headline_ids": headline_ids,
        "headlines": [{"headline_id": value} for value in headline_ids],
        "counts": {"accepted": 4},
    }
    prepare_calls: list[dict] = []
    cycle_calls: list[dict] = []
    monkeypatch.setattr(
        quota_proof,
        "load_rolling_x_headline_sidecars",
        lambda **_kwargs: rolling_input,
    )

    def prepare(**kwargs):
        prepare_calls.append(dict(kwargs))
        evaluated = set(kwargs.get("evaluated_headline_ids") or [])
        selected = next((value for value in headline_ids if value not in evaluated), None)
        rows = [selected] if selected else []
        return {
            "full_rolling_headline_count": 4,
            "prepared_candidate_count": len(rows),
            "prepared_frontier": {"selected_headline_ids": rows},
            "autonomous_source_discovery_available": True,
            "source_route_health_input_sha256": f"health-{len(prepare_calls)}",
        }

    monkeypatch.setattr(quota_proof, "build_prepared_rolling_x_candidate_state", prepare)

    def cycle(**kwargs):
        cycle_calls.append(dict(kwargs))
        index = len(cycle_calls)
        headline_id = f"headline-{index}"
        turns = [
            {
                "turn_number": 1,
                "pass_kind": "BATCH",
                "candidate_story_count": 1,
                "accounted_discovery_tokens": 10,
            }
        ]
        if index >= 2:
            turns.append(
                {
                    "turn_number": 2,
                    "pass_kind": "BATCH",
                    "candidate_story_count": 1,
                    "accounted_discovery_tokens": 10,
                }
            )
        accounting = {
            "schema_version": "contentops.quota_efficient_source_discovery.v1",
            "newsroom_production_day_id": kwargs["newsroom_production_day_id"],
            "status": "PASS",
            "accounting_complete": True,
            "turns": turns,
            "batch_discovery_turns": len(turns),
            "tail_discovery_turns": 0,
            "total_discovery_turns": len(turns),
            "accounted_discovery_tokens": 10 * len(turns),
            "deterministic_network_requests": index,
            "remaining_budget": {
                "batch_turns": 2 - len(turns),
                "tail_turns": 2,
                "total_turns": 4 - len(turns),
                "accounted_discovery_tokens": 2_000_000 - 10 * len(turns),
                "deterministic_network_requests": 96 - index,
            },
            "failures": [],
            "candidate_urls_are_evidence": False,
            "tail_is_subset_only": True,
        }
        health = {
            "schema_version": "contentops.source_route_health.v1",
            "routing_only": True,
            "hosts": [
                {
                    "normalized_host": "apnews.com",
                    "success_count": index,
                    "failure_count": 0,
                }
            ],
            "routes": [],
            "sourceability_or_health_grants_factual_authority": False,
            "sourceability_or_health_grants_publication_authority": False,
        }
        return {
            "quota_efficient_source_discovery": accounting,
            "evidence_ready_pool": {"candidates": []},
            "ranked_viability": {
                "rank_attempts": [
                    {
                        "rank": 1,
                        "cluster_id": f"story-{index}",
                        "headline_ids": [headline_id],
                        "status": "BLOCKED",
                        "blockers": ["evidence_documents_missing"],
                        "evidence_receipt": {
                            "blockers": ["evidence_documents_missing"]
                        },
                    }
                ]
            },
            "critical_path_telemetry": {"article_writer_semantic_calls": 0},
            "article_generation_attempts": 0,
            "public_write_performed": False,
            "publishing_adapter_called": False,
            "unknown_write_detected": False,
            "exact_next_blocker": "ALL_RANKED_CLUSTERS_EVIDENCE_BLOCKED",
            "source_route_health": health,
            "preselection_intelligence": {
                "sourceability_observations_consumed": index > 1,
            },
        }

    monkeypatch.setattr(quota_proof, "run_rolling_x_newsroom_cycle", cycle)

    receipt = quota_proof.run(
        runtime_output_dir=tmp_path / "runtime",
        evidence_output=tmp_path / "receipt.json",
        cutoff_utc="2026-08-23T15:00:00Z",
        source_route_health_path=tmp_path / "missing-health.json",
    )

    assert receipt["frontier_count"] == 4
    assert receipt["evaluated_headline_ids"] == headline_ids
    assert receipt["repeated_headline_ids"] == []
    assert receipt["repeated_story_ids"] == []
    assert receipt["production_day_budget"]["consumed"] == {
        "batch_turns": 2,
        "tail_turns": 0,
        "total_turns": 2,
        "accounted_discovery_tokens": 20,
        "deterministic_network_requests": 4,
    }
    assert "quota_discovery_prior_accounting" not in cycle_calls[0]
    assert cycle_calls[0]["quota_discovery_budget"] == {
        "max_batch_turns": 24,
        "max_tail_turns": 24,
        "max_total_turns": 24,
        "max_accounted_tokens": 18_000_000,
        "max_deterministic_network_requests": 384,
    }
    assert [
        row["quota_discovery_fresh_unseen_available"] for row in cycle_calls
    ] == [True, True, True, False]
    assert cycle_calls[1]["quota_discovery_prior_accounting"][
        "deterministic_network_requests"
    ] == 1
    assert cycle_calls[2]["quota_discovery_prior_accounting"][
        "deterministic_network_requests"
    ] == 2
    assert prepare_calls[1]["source_route_health"]["hosts"][0][
        "success_count"
    ] == 1
    assert "prior_prepared_state" not in prepare_calls[1]
    assert receipt["source_route_health"][
        "sourceability_or_health_grants_factual_authority"
    ] is False


def test_multi_frontier_runner_classifies_pre_turn_usage_limit_as_host_blocker(
    monkeypatch, tmp_path: Path
):
    rolling_input = {
        "schema_version": "capital_chronicle.rolling_x_headline_input.v1",
        "unique_headline_ids": ["headline-1"],
        "headlines": [{"headline_id": "headline-1"}],
        "counts": {"accepted": 1},
    }
    monkeypatch.setattr(
        quota_proof,
        "load_rolling_x_headline_sidecars",
        lambda **_kwargs: rolling_input,
    )
    monkeypatch.setattr(
        quota_proof,
        "build_prepared_rolling_x_candidate_state",
        lambda **_kwargs: {
            "full_rolling_headline_count": 1,
            "prepared_candidate_count": 1,
            "prepared_frontier": {"selected_headline_ids": ["headline-1"]},
            "autonomous_source_discovery_available": True,
        },
    )
    monkeypatch.setattr(
        quota_proof,
        "run_rolling_x_newsroom_cycle",
        lambda **kwargs: {
            "quota_efficient_source_discovery": {
                "schema_version": "contentops.quota_efficient_source_discovery.v1",
                "newsroom_production_day_id": kwargs["newsroom_production_day_id"],
                "status": "BLOCKED",
                "accounting_complete": True,
                "batch_discovery_turns": 0,
                "tail_discovery_turns": 0,
                "total_discovery_turns": 0,
                "accounted_discovery_tokens": 0,
                "deterministic_network_requests": 1,
                "terminal_provider_blocker": "CHATGPT_USAGE_LIMIT_REACHED",
                "remaining_budget": {
                    "batch_turns": 24,
                    "tail_turns": 24,
                    "total_turns": 24,
                    "accounted_discovery_tokens": 18_000_000,
                    "deterministic_network_requests": 383,
                },
                "failures": [
                    {
                        "failure_code": "CHATGPT_USAGE_LIMIT_REACHED",
                        "model_turn_completed": False,
                    }
                ],
                "candidate_urls_are_evidence": False,
                "tail_is_subset_only": True,
                "turns": [],
            },
            "ranked_viability": {
                "rank_attempts": [
                    {
                        "rank": 1,
                        "cluster_id": "story-1",
                        "headline_ids": ["headline-1"],
                        "status": "BLOCKED",
                        "blockers": ["SOURCE_DISCOVERY_REQUIRED"],
                        "evidence_receipt": {
                            "blockers": ["SOURCE_DISCOVERY_REQUIRED"]
                        },
                    }
                ]
            },
            "evidence_ready_pool": {"candidates": []},
            "critical_path_telemetry": {"article_writer_semantic_calls": 0},
            "article_generation_attempts": 0,
            "public_write_performed": False,
            "publishing_adapter_called": False,
            "unknown_write_detected": False,
            "exact_next_blocker": "CHATGPT_USAGE_LIMIT_REACHED",
        },
    )

    receipt = quota_proof.run(
        runtime_output_dir=tmp_path / "runtime",
        evidence_output=tmp_path / "receipt.json",
        cutoff_utc="2026-08-23T22:41:06Z",
        source_route_health_path=tmp_path / "missing-health.json",
    )

    assert receipt["classification"] == "CURRENT_HOST_RUNTIME_PROOF_REQUIRED"
    assert receipt["exact_remaining_blocker"] == "CHATGPT_USAGE_LIMIT_REACHED"
    assert receipt["checks"][
        "genuine_host_or_provider_dependency_unavailable"
    ] is True
    assert receipt["frontier_count"] == 1


def test_quota_proof_reuses_daily_app_sourceability_and_route_health_inputs(
    monkeypatch, tmp_path: Path
):
    source_health = {
        "schema_version": "contentops.source_route_health.v1",
        "routing_only": True,
        "hosts": [
            {
                "normalized_host": "apnews.com",
                "success_count": 2,
                "failure_count": 0,
            },
            {
                "normalized_host": "bloomberg.com",
                "success_count": 0,
                "failure_count": 2,
            },
        ],
        "routes": [],
        "sourceability_or_health_grants_factual_authority": False,
        "sourceability_or_health_grants_numeric_authority": False,
        "sourceability_or_health_grants_permission_authority": False,
        "sourceability_or_health_grants_publication_authority": False,
    }
    source_health_path = tmp_path / "source_route_health_v1.json"
    source_health_path.write_text(json.dumps(source_health), encoding="utf-8")
    rolling_input = {
        "schema_version": "capital_chronicle.rolling_x_headline_input.v1",
        "headlines": [{"headline_id": "headline-1"}],
        "unique_headline_ids": ["headline-1"],
        "counts": {"accepted": 1},
    }
    observed: dict[str, dict] = {}

    monkeypatch.setattr(
        quota_proof,
        "load_rolling_x_headline_sidecars",
        lambda **_kwargs: rolling_input,
    )

    def prepare(**kwargs):
        observed["prepared"] = dict(kwargs)
        selected = [] if kwargs.get("evaluated_headline_ids") else ["headline-1"]
        return {
            "full_rolling_headline_count": 1,
            "prepared_candidate_count": len(selected),
            "prepared_frontier": {"selected_headline_ids": selected},
            "autonomous_source_discovery_available": True,
            "source_route_health_input_sha256": "route-health-input-hash",
        }

    monkeypatch.setattr(quota_proof, "build_prepared_rolling_x_candidate_state", prepare)

    def cycle(**kwargs):
        observed["cycle"] = dict(kwargs)
        return {
            "quota_efficient_source_discovery": {
                "status": "PASS",
                "accounting_complete": True,
                "batch_discovery_turns": 0,
                "tail_discovery_turns": 0,
                "total_discovery_turns": 0,
                "accounted_discovery_tokens": 0,
                "deterministic_network_requests": 0,
                "newsroom_production_day_id": kwargs["newsroom_production_day_id"],
                "schema_version": "contentops.quota_efficient_source_discovery.v1",
                "remaining_budget": {
                    "batch_turns": 2,
                    "tail_turns": 2,
                    "total_turns": 4,
                    "accounted_discovery_tokens": 2000000,
                    "deterministic_network_requests": 96,
                },
                "failures": [],
                "candidate_urls_are_evidence": False,
                "tail_is_subset_only": True,
            },
            "evidence_ready_pool": {"candidates": []},
            "ranked_viability": {
                "rank_attempts": [
                    {
                        "rank": 1,
                        "cluster_id": "story-1",
                        "headline_ids": ["headline-1"],
                        "status": "BLOCKED",
                        "blockers": ["evidence_documents_missing"],
                        "evidence_receipt": {
                            "blockers": ["evidence_documents_missing"]
                        },
                    }
                ]
            },
            "critical_path_telemetry": {"article_writer_semantic_calls": 0},
            "article_generation_attempts": 0,
            "public_write_performed": False,
            "publishing_adapter_called": False,
            "unknown_write_detected": False,
            "exact_next_blocker": "ALL_RANKED_CLUSTERS_EVIDENCE_BLOCKED",
            "source_route_health_input_sha256": "route-health-input-hash",
            "source_route_health": source_health,
            "preselection_intelligence": {
                "sourceability_observations_consumed": True,
            },
        }

    monkeypatch.setattr(quota_proof, "run_rolling_x_newsroom_cycle", cycle)

    receipt = quota_proof.run(
        runtime_output_dir=tmp_path / "runtime",
        evidence_output=tmp_path / "receipt.json",
        cutoff_utc="2026-08-23T14:30:00Z",
        source_route_health_path=source_health_path,
    )

    assert observed["prepared"]["autonomous_source_discovery_available"] is True
    assert observed["prepared"]["source_route_health"] == source_health
    assert observed["cycle"]["source_route_health"] == source_health
    assert receipt["frontiers"][0]["sourceability_parity"] == {
        "prepared_frontier_autonomous_source_discovery_available": True,
        "prepared_frontier_source_route_health_input_sha256": (
            "route-health-input-hash"
        ),
        "cycle_source_route_health_input_sha256": "route-health-input-hash",
        "preselection_sourceability_observations_consumed": True,
        "routing_only": True,
        "factual_numeric_or_publication_authority_granted": False,
    }


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


def test_default_canonical_cycle_never_instantiates_expensive_source_discovery(
    monkeypatch, tmp_path: Path
):
    provider_constructions: list[Path] = []

    def acquire(request):
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
            "blockers": ["evidence_documents_missing", "SOURCE_DISCOVERY_REQUIRED"],
            "publication_authority": False,
        }

    class ForbiddenDefaultProvider:
        def __init__(self, *, output_dir: Path):
            provider_constructions.append(output_dir)

        def __call__(self, _request):
            raise AssertionError("default canonical cycle must not call expensive discovery")

    monkeypatch.setattr(
        implementation,
        "_default_rolling_x_evidence_acquirer",
        lambda **_kwargs: acquire,
    )
    monkeypatch.setattr(
        "live_contentops.official_codex_source_discovery_v1.OfficialCodexUrlDiscoveryProvider",
        ForbiddenDefaultProvider,
    )

    result = _run_cycle(
        monkeypatch,
        tmp_path,
        count=1,
        evidence_only_target_count=1,
    )

    attempt = result["ranked_viability"]["rank_attempts"][0]
    assert (
        inspect.signature(run_rolling_x_newsroom_cycle)
        .parameters["autonomous_source_discovery_enabled"]
        .default
        is False
    )
    assert provider_constructions == []
    assert attempt["evidence_receipt"]["autonomous_source_discovery"]["status"] == (
        "SUPPORTED_DISCOVERY_PROVIDER_UNAVAILABLE"
    )
    assert attempt["evidence_receipt"]["claim_evidence_contract"]["status"] == "BLOCKED"
    assert int(result.get("xhigh_worker_invocations") or 0) == 0
    assert int(result.get("article_generation_attempts") or 0) == 0
    assert result["public_write_performed"] is False


def test_explicit_opt_in_constructs_provider_and_preserves_same_candidate_handshake(
    monkeypatch, tmp_path: Path
):
    discovery_calls: list[dict] = []
    provider_constructions: list[Path] = []

    def acquire(request):
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
                "blockers": ["evidence_documents_missing", "SOURCE_DISCOVERY_REQUIRED"],
                "publication_authority": False,
            }
        return _pass_receipt(request)

    class OptInProvider:
        def __init__(self, *, output_dir: Path):
            provider_constructions.append(output_dir)

        def __call__(self, request):
            discovery_calls.append(dict(request))
            return {
                "contract": {
                    "schema_version": "contentops.codex_source_discovery_urls.v1",
                    "story_identity": request["cluster_id"],
                    "headline_ids": list(request["headline_ids"]),
                    "trigger_reason": "NO_VIABLE_DETERMINISTIC_PATH",
                    "prior_blockers": list(request["prior_blockers"]),
                    "candidate_urls": ["https://apnews.com/article/explicit-opt-in"],
                    "search_call_id": "explicit-opt-in-fixture",
                    "searched_at_utc": "2026-08-23T02:00:01Z",
                    "search_snippets_included": False,
                    "model_summaries_included": False,
                    "candidate_urls_are_evidence": False,
                    "factual_or_numeric_authority_granted": False,
                    "publication_authority_granted": False,
                },
                "provider_receipt": {
                    "role": "V1_URL_ONLY_SOURCE_DISCOVERY",
                    "candidate_urls_are_evidence": False,
                },
            }

    monkeypatch.setattr(
        implementation,
        "_default_rolling_x_evidence_acquirer",
        lambda **_kwargs: acquire,
    )
    monkeypatch.setattr(
        "live_contentops.official_codex_source_discovery_v1.OfficialCodexUrlDiscoveryProvider",
        OptInProvider,
    )

    result = _run_cycle(
        monkeypatch,
        tmp_path,
        count=1,
        autonomous_source_discovery_enabled=True,
        evidence_only_target_count=1,
    )

    candidate = result["evidence_ready_pool"]["candidates"][0]
    assert len(provider_constructions) == 1
    assert len(discovery_calls) == 1
    assert candidate["claim_contract_status"] == "PASS"
    assert candidate["freshness_pass"] is True
    assert candidate["publication_authority_granted"] is False
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
