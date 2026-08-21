from __future__ import annotations

from hashlib import sha256
from pathlib import Path

import pytest

from live_contentops.grounded_news_research_v1 import (
    GROUNDING_MODE,
    GroundedNewsResearchInvocationError,
    GroundedNewsResearchV1,
    _locator_event_core_query,
    _locator_query_seed,
    _model_failure,
    build_additive_cc_context_bundle,
    build_deterministic_locator_plan,
)
from live_contentops.nine_router_provider_adapter_v2 import (
    grounding_capability_manifest,
)
from live_contentops.llm_cost_governor_v1 import LLMCostBudgetExceededError
from live_contentops.rolling_x_grounded_article_media_builder_v1 import (
    GroundedArticleBuilderError,
    build_rolling_x_grounded_article_and_media,
)
from live_contentops.rolling_x_targeted_evidence_adapter_v1 import (
    RollingXTargetedEvidenceAdapter,
    _restrict_grounded_packet_to_documents,
)
from live_contentops.source_capability_registry_v2 import (
    load_source_capability_registry,
    resolve_story_capabilities,
)


AS_OF = "2026-08-13T10:00:00Z"


def test_locator_seed_neutralizes_headline_hype_without_adding_facts():
    assert (
        _locator_query_seed("Danube Water Levels Sink To Historic Lows")
        == "Danube Water Levels To low"
    )


def test_frozen_social_headline_gets_bounded_event_core_locator_variant():
    headline = (
        "RT @tongbingxue: Xu Jiayin, founder of China Evergrande Group and former "
        "China's richest man, was sentenced to life in prison by a Sh..."
    )

    assert _locator_event_core_query(headline) == (
        "Xu Jiayin founder China Evergrande sentenced life prison"
    )
    plan = build_deterministic_locator_plan(
        {
            "normalized_headline_proposition": headline,
            "important_entities": [],
            "already_bound_source_urls": [],
            "claims_or_questions_needing_verification": [],
        },
        max_queries=3,
    )
    assert plan["queries"][1] == (
        "Xu Jiayin founder China Evergrande sentenced life prison"
    )
    assert plan["query_text_grants_factual_authority"] is False


def test_post_filter_packet_drops_facts_bound_to_removed_documents():
    kept = _document("kept")
    removed = _document("removed")
    packet = {
        "research_status": "PASS",
        "sources": [
            {
                "source_ref": _source_ref("kept"),
                "evidence_document_id": "kept",
            },
            {
                "source_ref": _source_ref("removed"),
                "evidence_document_id": "removed",
            },
        ],
        "confirmed_facts": [
            {
                "fact_id": "F1",
                "factual_statement": "The United States announced semiconductor export restrictions.",
                "source_refs": [_source_ref("kept"), _source_ref("removed")],
            },
            {
                "fact_id": "F2",
                "factual_statement": "The removed document carried another assertion.",
                "source_refs": [_source_ref("removed")],
            },
        ],
        "attributed_numeric_facts": [],
    }

    filtered = _restrict_grounded_packet_to_documents(packet, [kept])

    assert [row["fact_id"] for row in filtered["confirmed_facts"]] == ["F1"]
    assert filtered["confirmed_facts"][0]["source_refs"] == [_source_ref("kept")]
    assert [row["evidence_document_id"] for row in filtered["sources"]] == ["kept"]
    assert filtered["post_filter_removed_fact_count"] == 1
    assert filtered["research_status"] == "PASS"


def _source_ref(document_id: str) -> str:
    return "SRC_" + sha256(document_id.encode("utf-8")).hexdigest()[:16].upper()


def _document(
    document_id: str = "reuters-chip-rule",
    *,
    publisher: str = "Reuters",
    source_url: str = "https://www.reuters.com/world/us/us-announces-chip-export-rule/",
    authority: str = "reputable_secondary_source",
) -> dict:
    content = (
        "The United States announced new semiconductor export restrictions on Thursday, "
        "the Commerce Department said. The rule takes effect on September 1. Revenue at an "
        "affected supplier rose 18% to $4.2 billion, the company said in its release. "
        + "The restrictions define licensing requirements for advanced chips. " * 35
    )
    return {
        "document_id": document_id,
        "title": "US announces new semiconductor export restrictions",
        "publisher": publisher,
        "source_identity": source_url.split("/")[2],
        "source_authority_class": authority,
        "source_url": source_url,
        "reader_source_url": source_url,
        "published_at_utc": "2026-08-13T08:00:00Z",
        "event_time_utc": "2026-08-13T08:00:00Z",
        "canonical_content_sha256": "a" * 64,
        "canonical_content_text": content,
        "content_type": "text/html",
        "public_claim_allowed": True,
    }


def _request(*, story_type: str = "company_sector_event", mode: str = "STANDARD_NEWS_ANALYSIS") -> dict:
    registry = load_source_capability_registry()
    capability_mode = "analysis" if mode == "STANDARD_NEWS_ANALYSIS" else "straight_news"
    capability = resolve_story_capabilities(
        {
            "story_type": story_type,
            "article_mode": capability_mode,
            "product_article_mode": mode,
        },
        registry,
    )
    return {
        "schema_version": "capital_chronicle.rolling_x_story_evidence_request.v1",
        "cluster_id": "chip-rule-cluster",
        "rank": 1,
        "headline_ids": ["headline-1"],
        "story_type": story_type,
        "article_mode": capability["article_mode"],
        "requested_article_mode": mode,
        "effective_article_mode": mode,
        "resolved_article_mode": mode,
        "needed_evidence": ["Verify the announcement and effective date."],
        "required_evidence_capabilities": list(
            capability["required_evidence_capabilities"]
        ),
        "optional_evidence_capabilities": list(
            capability["optional_evidence_capabilities"]
        ),
        "source_adapter_families": list(capability["source_adapter_families"]),
        "capital_chronicle_numeric_or_analytical_authority_required": False,
        "story_context": {
            "why_now": "US announces new semiconductor export restrictions",
            "leaf_summaries": [
                "US announces new semiconductor export restrictions"
            ],
            "entities_topics": ["United States", "semiconductors"],
            "public_source_urls": [],
            "public_source_url_bindings": [],
            "capital_chronicle_context": {},
        },
        "x_content_is_discovery_and_ranking_only": True,
        "request_logical_hash": "request-hash",
    }


def _model_call(
    document_ids: list[str],
    *,
    numeric_statement: str | None = None,
    suggested_mode: str = "STANDARD_NEWS_ANALYSIS",
):
    refs = [_source_ref(value) for value in document_ids]

    def call(phase: str, _prompt: str) -> dict:
        if phase == "query_plan":
            return {
                "queries": [
                    "US Commerce Department semiconductor export restrictions latest"
                ],
                "verification_questions": ["When does the rule take effect?"],
                "preferred_source_classes": [
                    "official_primary",
                    "reputable_professional_reporting",
                ],
            }
        fact = {
            "fact_id": "fact-core",
            "factual_statement": (
                numeric_statement
                or "The United States announced new semiconductor export restrictions."
            ),
            "source_refs": refs,
            "confidence_class": "CONFIRMED",
            "direct_or_inferred": "DIRECT",
        }
        numeric = []
        if numeric_statement:
            numeric = [
                {
                    "statement": numeric_statement,
                    "value": "$4.2 billion",
                    "source_ref": refs[0],
                    "attribution_required": True,
                }
            ]
        return {
            "core_factual_proposition": fact["factual_statement"],
            "confirmed_facts": [fact],
            "attributed_numeric_facts": numeric,
            "context": [],
            "uncertainties": [],
            "contradictions": [],
            "unsupported_or_unverified": [],
            "suggested_article_mode": suggested_mode,
        }

    return call


def _retriever(documents: list[dict]):
    def retrieve(_request: dict) -> dict:
        return {
            "status": "PASS",
            "evidence_documents": documents,
            "provenance": {"request_count": 2, "retrieved_at_utc": AS_OF},
            "publication_authority": False,
        }

    return retrieve


def test_provider_contract_selects_compatibility_grounding_without_probe():
    capability = grounding_capability_manifest()

    assert capability["native_grounded_citations_supported"] is False
    assert capability["citation_metadata_visible_to_caller"] is False
    assert capability["effective_grounding_path"] == GROUNDING_MODE
    assert capability["network_probe_required"] is False


def test_ordinary_retrieval_uses_deterministic_proposition_and_entity_queries():
    document = _document()
    seen_queries: list[str] = []

    def retrieve(request: dict) -> dict:
        seen_queries.extend(request["story_context"]["grounded_research_queries"])
        return _retriever([document])(request)

    result = GroundedNewsResearchV1(
        evaluation_as_of_utc=AS_OF,
        public_retriever=retrieve,
        structured_model_call=_model_call([document["document_id"]]),
        max_queries=3,
    )(_request())

    assert result["status"] == "PASS"
    assert seen_queries[0] == "US announces new semiconductor export restrictions"
    assert seen_queries[1].endswith("United States semiconductors")
    assert result["query_plan"]["planning_mode"] == "DETERMINISTIC_ORDINARY_LOCATOR"
    assert [row["phase"] for row in result["telemetry"]] == ["source_synthesis"]


def test_empty_first_retrieval_gets_one_bounded_llm_replan():
    document = _document()
    corroborating = _document(
        "ap-chip-rule",
        publisher="Associated Press",
        source_url="https://apnews.com/article/us-chip-export-rule-123",
    )
    retrievals: list[list[str]] = []
    base_model = _model_call([document["document_id"], corroborating["document_id"]])

    def model(phase: str, prompt: str) -> dict:
        if phase == "query_replan":
            return {
                "queries": ["United States Commerce advanced chip licensing rule"],
                "verification_questions": [],
                "preferred_source_classes": ["reputable_professional_reporting"],
            }
        return base_model(phase, prompt)

    def retrieve(request: dict) -> dict:
        retrievals.append(list(request["story_context"]["grounded_research_queries"]))
        documents = [] if len(retrievals) == 1 else [document, corroborating]
        return {
            "status": "PASS" if documents else "BLOCKED",
            "evidence_documents": documents,
            "provenance": {
                "request_count": len(retrievals),
                "retrieved_at_utc": AS_OF,
            },
            "publication_authority": False,
        }

    request = _request(story_type="geopolitical_event", mode="BREAKING_BRIEF")
    result = GroundedNewsResearchV1(
        evaluation_as_of_utc=AS_OF,
        public_retriever=retrieve,
        structured_model_call=model,
        max_queries=3,
    )(request)

    assert result["status"] == "PASS"
    assert result["research_calls"] == 3
    assert len(retrievals) == 2
    assert retrievals[1][0].startswith("United States Commerce")


def test_ordinary_grounded_reporting_passes_without_cc_and_binds_numeric_fact():
    document = _document()
    numeric = "Revenue rose 18% to $4.2 billion, the company said."
    research = GroundedNewsResearchV1(
        evaluation_as_of_utc=AS_OF,
        public_retriever=_retriever([document]),
        structured_model_call=_model_call(
            [document["document_id"]], numeric_statement=numeric
        ),
    )

    result = research(_request())

    assert result["status"] == "PASS"
    packet = result["research_packet"]
    assert packet["grounding_mode"] == GROUNDING_MODE
    assert packet["cc_context"]["state"] == "CC_CONTEXT_UNAVAILABLE"
    assert packet["attributed_numeric_facts"][0]["source_ref"] == _source_ref(
        document["document_id"]
    )
    assert result["minimum_trustworthy_evidence_packet"]["status"] == "PASS"
    assert result["minimum_trustworthy_evidence_packet"][
        "attribution_required"
    ] is True


def test_unsupported_model_number_is_rejected_even_with_real_source_record():
    document = _document()
    research = GroundedNewsResearchV1(
        evaluation_as_of_utc=AS_OF,
        public_retriever=_retriever([document]),
        structured_model_call=_model_call(
            [document["document_id"]],
            numeric_statement="Revenue rose 91% to $99.4 billion, the company said.",
        ),
    )

    result = research(_request())

    assert result["status"] == "BLOCKED"
    assert result["blockers"] == ["research_fact_not_supported_by_bound_source"]
    assert result["retrieval_result"]["accepted_document_count"] == 1


def test_model_assertion_without_an_exact_source_record_cannot_pass():
    document = _document()
    research = GroundedNewsResearchV1(
        evaluation_as_of_utc=AS_OF,
        public_retriever=_retriever([document]),
        structured_model_call=_model_call(["invented-source-id"]),
    )

    result = research(_request())

    assert result["status"] == "BLOCKED"
    assert result["research_calls"] == 1
    assert result["blockers"] == ["research_fact_binding_invalid"]


def test_operator_pause_is_preserved_as_an_exact_pre_network_blocker():
    from live_contentops.llm_operator_control_v1 import LLMOperatorPausedError

    def paused(_phase: str, _prompt: str) -> dict:
        raise LLMOperatorPausedError()

    result = GroundedNewsResearchV1(
        evaluation_as_of_utc=AS_OF,
        public_retriever=_retriever([_document()]),
        structured_model_call=paused,
    )(_request())

    assert result["status"] == "BLOCKED"
    assert result["blockers"] == ["llm_operator_paused"]
    assert result["research_calls"] == 1
    assert result["public_retrieval_requests"] == 2
    assert result["global_infrastructure_exhausted"] is True


def test_additive_cc_context_state_is_available_but_never_grants_authority():
    bundle = build_additive_cc_context_bundle(
        {
            "queried_entities": ["semiconductors"],
            "matches": [
                {
                    "store_id": "macro-store",
                    "table": "market_history",
                    "matched_entity": "semiconductors",
                    "row_reference_hashes": ["row-ref-1"],
                    "schema_fingerprint": "schema-ref",
                }
            ],
            "cc_context_richness": 0.6,
            "catalog_fingerprint": "catalog-ref",
        }
    )

    assert bundle["state"] == "CC_CONTEXT_AVAILABLE"
    assert bundle["cc_context_refs"][0]["row_reference_hashes"] == ["row-ref-1"]
    assert bundle["proprietary_claim_authority_granted"] is False


def test_enhanced_risk_needs_primary_or_independent_corroboration():
    first = _document()
    request = _request(story_type="geopolitical_event", mode="BREAKING_BRIEF")
    one_source = GroundedNewsResearchV1(
        evaluation_as_of_utc=AS_OF,
        public_retriever=_retriever([first]),
        structured_model_call=_model_call(
            [first["document_id"]], suggested_mode="BREAKING_BRIEF"
        ),
    )(request)
    assert one_source["status"] == "BLOCKED"
    assert one_source["blockers"] == [
        "enhanced_risk_grounded_support_insufficient"
    ]

    second = _document(
        "ap-chip-rule",
        publisher="Associated Press",
        source_url="https://apnews.com/article/us-chip-export-rule-123",
    )
    two_source = GroundedNewsResearchV1(
        evaluation_as_of_utc=AS_OF,
        public_retriever=_retriever([first, second]),
        structured_model_call=_model_call(
            [first["document_id"], second["document_id"]],
            suggested_mode="BREAKING_BRIEF",
        ),
    )(request)
    assert two_source["status"] == "PASS"
    assert two_source["claim_evidence_contract"]["status"] == "PASS"


def test_mode_downgrades_and_cached_research_does_not_repeat_calls():
    document = _document()
    calls: list[str] = []
    base = _model_call([document["document_id"]], suggested_mode="BREAKING_BRIEF")

    def recording(phase: str, prompt: str) -> dict:
        calls.append(phase)
        return base(phase, prompt)

    research = GroundedNewsResearchV1(
        evaluation_as_of_utc=AS_OF,
        public_retriever=_retriever([document]),
        structured_model_call=recording,
    )
    request = _request(mode="STANDARD_NEWS_ANALYSIS")
    first = research(request)
    second = research({**request, "effective_article_mode": "BREAKING_BRIEF"})

    assert first["research_packet"]["suggested_article_mode"] == "BREAKING_BRIEF"
    assert second["cache_reused"] is True
    assert calls == ["source_synthesis"]


def test_deterministic_locator_plan_uses_bound_host_without_granting_authority():
    compact = {
        "normalized_headline_proposition": "Company files current quarterly results",
        "important_entities": ["Example Holdings"],
        "already_bound_source_urls": ["https://www.reuters.com/business/example/"],
        "claims_or_questions_needing_verification": ["What did the filing report?"],
    }

    plan = build_deterministic_locator_plan(compact, max_queries=3)

    assert plan["queries"] == [
        "Company files current quarterly results",
        "Company files current quarterly results Example Holdings",
        "reuters Company files current quarterly results",
    ]
    assert plan["already_bound_source_urls_considered"] == 1
    assert plan["query_text_grants_factual_authority"] is False


def test_ordinary_candidate_with_no_source_records_spends_zero_model_calls():
    calls: list[str] = []

    def model(phase: str, _prompt: str) -> dict:
        calls.append(phase)
        raise AssertionError("ordinary empty retrieval must not call a model")

    result = GroundedNewsResearchV1(
        evaluation_as_of_utc=AS_OF,
        public_retriever=_retriever([]),
        structured_model_call=model,
    )(_request())

    assert result["status"] == "BLOCKED"
    assert result["blockers"] == ["grounded_research_source_records_unavailable"]
    assert result["research_calls"] == 0
    assert calls == []


def test_terminal_router_authorization_failure_is_an_exact_global_stop():
    error = GroundedNewsResearchInvocationError(
        "source_synthesis",
        {
            "logical_invocation_id": "synthesis-test",
            "terminal_disposition": "LLM_TERMINAL_NON_RETRYABLE_FAILURE",
            "total_attempts": 1,
            "attempts": [
                {
                    "requested_model": "new/claude-fable-5",
                    "failure_class": "http_403_forbidden",
                }
            ],
        },
    )

    blocker, telemetry, global_stop = _model_failure(
        error,
        phase="source_synthesis",
        logical_invocation_id="synthesis-test",
    )

    assert blocker == (
        "grounded_research_router_configuration_or_authorization_unavailable"
    )
    assert telemetry["terminal_failure_class"] == "http_403_forbidden"
    assert global_stop is True


@pytest.mark.parametrize(
    "failure_class",
    [
        "llm_cycle_logical_call_budget_exhausted",
        "llm_cycle_provider_attempt_budget_exhausted",
        "llm_cycle_token_budget_exhausted",
    ],
)
def test_each_cost_governor_exhaustion_class_is_preserved_as_global_stop(
    failure_class: str,
):
    blocker, telemetry, global_stop = _model_failure(
        LLMCostBudgetExceededError(failure_class),
        phase="source_synthesis",
        logical_invocation_id="synthesis-budget-test",
    )

    assert blocker == failure_class
    assert telemetry["logical_invocation_reserved"] is False
    assert telemetry["provider_attempt_count"] == 0
    assert global_stop is True


def test_grounded_packet_flows_through_adapter_and_existing_writer_builder(tmp_path: Path):
    document = _document()
    request = _request(mode="BREAKING_BRIEF")
    research = GroundedNewsResearchV1(
        evaluation_as_of_utc=AS_OF,
        public_retriever=_retriever([document]),
        structured_model_call=_model_call(
            [document["document_id"]], suggested_mode="BREAKING_BRIEF"
        ),
    )
    adapter = RollingXTargetedEvidenceAdapter(
        evaluation_as_of_utc=AS_OF,
        public_secondary_loader=_retriever([document]),
        grounded_researcher=research,
    )
    receipt = adapter(request)
    assert receipt["status"] == "PASS"
    assert receipt["grounded_research_packet"]["research_status"] == "PASS"

    viability = {
        "status": "SUCCESS",
        "decision": "SELECT_STORY",
        "selected_cluster_id": request["cluster_id"],
        "selected_rank": 1,
        "selected_headline_ids": request["headline_ids"],
        "selected_cluster": {
            "cluster_id": request["cluster_id"],
            "rank": 1,
            "headline_ids": request["headline_ids"],
            "leaf_summaries": request["story_context"]["leaf_summaries"],
            "entities_topics": request["story_context"]["entities_topics"],
            "article_mode": "breaking",
        },
        "selected_evidence": receipt,
        "rank_attempts": [
            {
                "rank": 1,
                "request": request,
                "capability_resolution": {"article_mode": "straight_news"},
            }
        ],
    }

    def writer(_prompt: str) -> dict:
        return {
            "title": "US semiconductor export restrictions",
            "subtitle": "",
            "seo_title": "US semiconductor export restrictions",
            "meta_description": "",
            "market_mechanism": "",
            "policy_context": "",
            "cross_asset_implications": "",
            "social_lede": "",
            "social_mechanism_summary": "",
            "social_policy_summary": "",
            "social_cross_asset_summary": "",
            "substack_body_markdown": (
                "[[SOURCE:SOURCE_1]] reported that the United States announced new "
                "semiconductor export restrictions. The restrictions define licensing "
                "requirements for advanced chips."
            ),
        }

    built = build_rolling_x_grounded_article_and_media(
        viability,
        output_dir=tmp_path,
        article_generator=writer,
        required_asset_count=0,
    )

    assert built["article"]["grounded_source_coverage"]["status"] == "PASS"
    assert built["critical_path_telemetry"]["article_writer_semantic_calls"] == 1
    assert built["critical_path_telemetry"]["mandatory_semantic_review_calls"] == 0
    assert built["media"]["media_asset_count"] == 0


def test_market_move_straight_news_uses_external_sources_but_deep_mode_requires_cc():
    registry = load_source_capability_registry()
    ordinary = resolve_story_capabilities(
        {
            "story_type": "market_move",
            "article_mode": "straight_news",
            "product_article_mode": "BREAKING_BRIEF",
        },
        registry,
    )
    deep = resolve_story_capabilities(
        {
            "story_type": "market_move",
            "article_mode": "deep_analysis",
            "product_article_mode": "CAPITAL_CHRONICLE_DEEP_DIVE",
        },
        registry,
    )

    assert ordinary["capital_chronicle_authority_required"] is False
    assert "public_secondary" in ordinary["source_adapter_families"]
    assert deep["capital_chronicle_authority_required"] is True
    assert "capital_chronicle_market_state" in deep["source_adapter_families"]
