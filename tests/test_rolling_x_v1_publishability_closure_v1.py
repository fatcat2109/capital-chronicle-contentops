from __future__ import annotations

from copy import deepcopy

import pytest

from live_contentops import _eight_platform_substack_first_pipeline_impl_v1 as pipeline
from live_contentops.source_capability_registry_v2 import (
    load_source_capability_registry,
    resolve_story_capabilities,
)
from live_contentops.official_primary_evidence_loader_v1 import (
    OFFICIAL_HOSTS_BY_FAMILY,
    BoundedOfficialPrimaryEvidenceLoader,
)
from live_contentops.official_primary_source_locator_v1 import (
    BoundedOfficialPrimarySourceLocator,
    LOCATOR_FAMILIES,
)
from live_contentops.newsroom_assignment_scheduler_v1 import (
    _leaf_evidence_reachability,
    _rolling_x_publishability_path_profile,
    build_bounded_rolling_x_publishability_pool,
    build_deterministic_rolling_x_assignment_fallback,
)
from live_contentops.preselection_intelligence_v1 import (
    apply_preselection_intelligence,
    _evidence_reachability as _preselection_evidence_reachability,
)
from live_contentops.rolling_x_grounded_article_media_builder_v1 import (
    GroundedArticleBuilderError,
)


# --- policy_decision article-mode profiles (Phase 13) -----------------------------


def test_policy_straight_news_does_not_require_capital_chronicle_authority():
    registry = load_source_capability_registry()
    capability = resolve_story_capabilities(
        {"story_type": "policy_decision", "article_mode": "straight_news"}, registry
    )
    # Base policy_decision row is market_sensitive, but straight_news must not need CC authority.
    assert capability["capital_chronicle_authority_required"] is False
    assert capability["market_snapshot_required"] is False
    assert capability["market_context_required"] is False
    assert capability["required_evidence_capabilities"] == [
        "credible_event_confirmation",
        "basic_attributed_facts",
    ]
    assert set(capability["optional_evidence_capabilities"]) == {
        "official_statement",
        "decision_timeline",
        "issuing_authority",
    }
    assert capability["source_adapter_families"] == ["official_policy", "public_secondary"]


def test_policy_analysis_request_does_not_create_independent_analytical_authority():
    registry = load_source_capability_registry()
    capability = resolve_story_capabilities(
        {"story_type": "policy_decision", "article_mode": "analysis"}, registry
    )
    # The calibrated acquisition profile can still produce a truthful brief when governed
    # analytical context is absent; a later mode gate must downgrade rather than fabricate it.
    assert capability["capital_chronicle_authority_required"] is False
    assert capability["market_snapshot_required"] is False
    assert "governed_analytical_context" in capability["optional_evidence_capabilities"]
    assert capability["required_evidence_capabilities"] == [
        "credible_event_confirmation",
        "basic_attributed_facts",
    ]


def test_market_sensitive_metadata_alone_never_adds_capital_chronicle_authority():
    registry = load_source_capability_registry()
    # regulatory_fiscal_event straight_news remains CC-free even if market metadata present.
    capability = resolve_story_capabilities(
        {"story_type": "regulatory_fiscal_event", "article_mode": "straight_news"}, registry
    )
    assert capability["capital_chronicle_authority_required"] is False
    assert capability["market_snapshot_required"] is False


# --- official_policy loader (Phase 14) --------------------------------------------


FR_STATEMENT_URL = "https://www.federalreserve.gov/newsevents/pressreleases/monetary20260809a.htm"


def _fr_statement_html(date="2026-08-08"):
    return (
        f'<html><head><meta name="date" content="{date}"></head><body>'
        "Federal Open Market Committee statement on monetary policy. "
        "The Committee reaffirmed the target range for the federal funds rate.</body></html>"
    ).encode()


def _response(url, body, status=200, content_type="text/html"):
    return {
        "status": status,
        "final_url": url,
        "headers": {"content-type": content_type},
        "body": body,
    }


def _policy_request(url=FR_STATEMENT_URL):
    return {
        "cluster_id": "c1",
        "headline_ids": ["h1"],
        "request_logical_hash": "a" * 64,
        "source_adapter_families": ["official_policy"],
        "required_evidence_capabilities": [
            "official_statement",
            "decision_timeline",
            "issuing_authority",
        ],
        "story_context": {
            "official_source_url_bindings": [{"url": url, "headline_id": "h1"}],
        },
    }


def test_official_policy_family_is_allowlisted():
    assert "www.federalreserve.gov" in OFFICIAL_HOSTS_BY_FAMILY["official_policy"]


def test_official_policy_loader_validates_statement_capabilities_and_binding():
    loader = BoundedOfficialPrimaryEvidenceLoader(
        evaluation_as_of_utc="2026-08-09T00:00:00Z",
        http_get=lambda url, timeout, maximum: _response(url, _fr_statement_html()),
    )
    packet = loader(_policy_request())
    assert packet["status"] == "PASS", packet["blockers"]
    provided = set(packet["provided_evidence_capabilities"])
    assert {"official_statement", "decision_timeline", "issuing_authority"} <= provided
    document = packet["official_source_documents"][0]
    assert document["source_authority_class"] == "official_public_primary_source"
    assert document["source_url"] == FR_STATEMENT_URL
    assert document["source_headline_id"] == "h1"
    assert document["published_at_utc"] == "2026-08-08T00:00:00Z"
    assert packet["provenance"]["retrieved_at_utc"] is not None
    assert packet["provenance"]["evaluation_as_of_utc"] == "2026-08-09T00:00:00Z"


def test_official_policy_loader_fails_closed_for_post_cutoff_publication():
    loader = BoundedOfficialPrimaryEvidenceLoader(
        evaluation_as_of_utc="2026-08-09T00:00:00Z",
        http_get=lambda url, timeout, maximum: _response(
            url, _fr_statement_html(date="2026-08-10")
        ),
    )
    packet = loader(_policy_request())
    assert packet["status"] == "BLOCKED"
    assert "official_source_published_after_evaluation_cutoff" in packet["blockers"]


# --- official_policy locator (Phase 14) -------------------------------------------


def test_official_policy_locator_finds_federal_reserve_statement_discovery_only():
    index_html = (
        '<html><a href="/newsevents/pressreleases/monetary20260809a.htm">'
        "FOMC issues implementation note</a></html>"
    ).encode()
    locator = BoundedOfficialPrimarySourceLocator(
        http_get=lambda url, timeout, maximum: _response(url, index_html)
    )
    result = locator(
        {
            "cluster_id": "c1",
            "headline_ids": ["h1"],
            "source_adapter_families": ["official_policy"],
            "evaluation_as_of_utc": "2026-08-09T00:00:00Z",
            "story_context": {"why_now": "FOMC decision", "entities_topics": ["Federal Reserve"]},
        }
    )
    assert result["status"] == "PASS", result.get("blockers")
    assert result["candidate_official_url"] == FR_STATEMENT_URL
    assert result["discovery_only"] is True
    assert result["factual_authority"] is False
    assert result["publication_authority"] is False
    assert result["evidence_capabilities"] == []


def test_official_policy_locator_fails_closed_when_no_statement_found():
    locator = BoundedOfficialPrimarySourceLocator(
        http_get=lambda url, timeout, maximum: _response(url, b"<html>nothing here</html>")
    )
    result = locator(
        {
            "cluster_id": "c1",
            "headline_ids": ["h1"],
            "source_adapter_families": ["official_policy"],
        }
    )
    assert result["status"] == "BLOCKED"


# --- evidence reachability (Phase 15) ---------------------------------------------


def _records(headline_ids_to_urls):
    return {
        headline_id: {
            "headline_id": headline_id,
            "source_timestamp_utc": "2026-08-08T00:00:00Z",
            "external_content": {"official_source_urls": urls},
        }
        for headline_id, urls in headline_ids_to_urls.items()
    }


def test_reachability_supported_now_when_bound_official_url_matches_family():
    cluster = {"member_headline_ids": ["h1"]}
    records = _records({"h1": [FR_STATEMENT_URL]})
    reach = _leaf_evidence_reachability(cluster, records)
    assert reach["direct_primary_binding"] is True
    assert "official_policy" in reach["supported_source_families"]
    assert reach["bounded_locator_available"] is True
    assert reach["current_v1_path"] == "SUPPORTED_NOW"
    assert reach["grants_factual_or_evidence_or_publication_authority"] is False


def test_reachability_no_current_path_when_no_bound_official_url():
    cluster = {"member_headline_ids": ["h1"]}
    records = _records({"h1": []})
    reach = _leaf_evidence_reachability(cluster, records)
    assert reach["direct_primary_binding"] is False
    assert reach["supported_source_families"] == []
    assert reach["current_v1_path"] == "NO_CURRENT_PATH"


def test_reachability_projects_existing_exact_state_fms_locator_from_context():
    cluster = {"member_headline_ids": ["h1"]}
    records = {
        "h1": {
            "headline_id": "h1",
            "source_timestamp_utc": "2026-08-21T16:28:47Z",
            "external_content": {
                "headline_text": (
                    "U.S. STATE DEPARTMENT APPROVES POSSIBLE SALE OF UH-60M BLACK HAWK "
                    "HELICOPTERS TO NORWAY WORTH ABOUT $2.3 BILLION."
                ),
                "official_source_urls": [],
            },
        }
    }
    reach = _leaf_evidence_reachability(cluster, records)
    assert reach["direct_primary_binding"] is False
    assert reach["bounded_locator_available"] is True
    assert reach["context_routed_locator_applicable"] is True
    assert reach["context_routed_locator_surface_ids"] == [
        "state_current_fms_press_releases_v1"
    ]
    assert reach["context_routed_locator_families"] == ["official_regulatory_fiscal"]
    assert reach["current_v1_path"] == "LOCATOR_SUPPORTED"
    assert reach["grants_factual_or_evidence_or_publication_authority"] is False


def test_publishability_path_keeps_direct_first_then_exact_context_locator():
    records = {
        "direct": {
            "external_content": {
                "headline_text": "Federal Reserve decision",
                "official_source_urls": [FR_STATEMENT_URL],
            }
        },
        "located": {
            "external_content": {
                "headline_text": (
                    "U.S. STATE DEPARTMENT OKAYS POSSIBLE SALE OF AIM-9X SIDEWINDER "
                    "BLOCK II MISSILES TO SOUTH KOREA."
                ),
                "official_source_urls": [],
            }
        },
        "secondary": {
            "external_content": {
                "headline_text": "Public report",
                "official_source_urls": ["https://www.reuters.com/world/example"],
            }
        },
    }
    direct = _rolling_x_publishability_path_profile(
        ["direct"], records_by_id=records
    )
    located = _rolling_x_publishability_path_profile(
        ["located"], records_by_id=records
    )
    secondary = _rolling_x_publishability_path_profile(
        ["secondary"], records_by_id=records
    )
    assert direct["tier"] == "EXACT_OFFICIAL_DIRECT"
    assert located["tier"] == "EXACT_CONTEXT_ROUTED_OFFICIAL_LOCATOR"
    assert located["context_routed_locator_surface_ids"] == [
        "state_current_fms_press_releases_v1"
    ]
    assert secondary["tier"] == "REPUTABLE_PUBLIC_SECONDARY"
    assert direct["priority"] > located["priority"] > secondary["priority"]
    assert located["grants_factual_or_evidence_or_publication_authority"] is False


def test_reachability_conditional_when_urls_bound_but_outside_supported_family():
    cluster = {"member_headline_ids": ["h1"]}
    records = _records({"h1": ["https://www.reuters.com/world/some-story"]})
    reach = _leaf_evidence_reachability(cluster, records)
    assert reach["direct_primary_binding"] is False
    assert reach["current_v1_path"] == "CONDITIONAL"
    assert reach["supported_source_families"] == []


def test_locator_families_cover_supported_official_paths():
    assert {"official_regulatory_fiscal", "official_macro", "company_primary",
            "sec_regulatory", "official_policy"} <= set(LOCATOR_FAMILIES)


def test_same_cycle_walk_reaches_exact_official_candidate_beyond_old_rank_twelve(
    monkeypatch, tmp_path
):
    headlines = []
    for index in range(14):
        urls = [f"https://www.bloomberg.com/news/articles/2026-08-11/story-{index}"]
        source_timestamp = f"2026-08-11T{index:02d}:00:00Z"
        if index == 12:
            urls = ["https://example.com/newer-generic-story"]
            source_timestamp = "2026-08-11T23:30:00Z"
        elif index == 13:
            urls = ["https://www.newyorkfed.org/newsevents/news/research/2026/report"]
            source_timestamp = "2026-08-11T01:00:00Z"
        headlines.append(
            {
                "headline_id": f"h{index}",
                "source_timestamp_utc": source_timestamp,
                "source_locator": {"path": "fixture.jsonl", "line": index + 1},
                "external_content": {
                    "headline_text": f"Controlled current event candidate {index}",
                    "official_source_urls": urls,
                    "follow_up_data_need_candidates": [],
                },
            }
        )
    intake = {
        "schema_version": "capital_chronicle.rolling_x_headline_input.v1",
        "cutoff_time_utc": "2026-08-12T00:00:00Z",
        "window_start_utc": "2026-08-11T00:00:00Z",
        "window_hours": 24.0,
        "headlines": headlines,
        "unique_headline_ids": [row["headline_id"] for row in headlines],
        "counts": {"accepted": len(headlines)},
        "canonical_input_hash": "frozen-fixture-input",
    }
    assignment = {
        "schema_version": "capital_chronicle.rolling_x_newsroom_assignment.v1",
        "status": "SUCCESS",
        "decision": "SELECT_STORY",
        "input_binding": {"canonical_input_hash": "frozen-fixture-input"},
        "ranked_clusters": [
            {
                "cluster_id": f"editorial-{index}",
                "rank": index + 1,
                "headline_ids": [f"h{index}"],
                "leaf_cluster_ids": [f"leaf-{index}"],
                "story_mode": "reporting",
                "article_mode": "breaking",
                "market_sensitive": False,
                "why_now": f"Controlled candidate {index} is current.",
                "selection_case": "Controlled editorial shortlist fixture.",
                "seo_intent": "controlled current event",
                "visual_strategy": "Deterministic title card.",
                "needed_evidence": ["Directly supporting public evidence."],
            }
            for index in range(12)
        ],
        "leaf_clusters": [
            {
                "leaf_cluster_id": f"leaf-{index}",
                "partition_id": "fixture",
                "member_headline_ids": [f"h{index}"],
                "event_topic_summary": f"Controlled current event candidate {index}",
                "canonical_representative_headline_id": f"h{index}",
                "entities": [f"entity-{index}"],
                "topics": ["controlled-event"],
                "duplicate_update_chain": {
                    "relationship": "distinct",
                    "ordered_headline_ids": [f"h{index}"],
                },
            }
            for index in range(14)
        ],
    }
    def assign_fixture(**kwargs):
        assignment["input_binding"]["canonical_input_hash"] = kwargs[
            "rolling_input"
        ]["canonical_input_hash"]
        return assignment

    monkeypatch.setattr(
        "live_contentops.newsroom_assignment_scheduler_v1.assign_rolling_x_headlines_with_nine_router",
        assign_fixture,
    )

    evidence_calls = []
    shared_request_counter = {"count": 0, "limit": 24}

    def acquire(request):
        evidence_calls.append(dict(request))
        exact_official = request["headline_ids"] == ["h13"]
        # Mirror the real bounded loaders' shared worst-case accounting: an exact bound
        # official fetch costs one request, while a secondary candidate may consume three
        # bound URLs plus one RSS discovery request.
        shared_request_counter["count"] += 1 if exact_official else 4
        if shared_request_counter["count"] > shared_request_counter["limit"]:
            raise RuntimeError("public_source_request_budget_exhausted")
        if not exact_official:
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
                "blockers": ["fixture_evidence_dead_candidate"],
                "capital_chronicle_authority_verified": False,
                "numeric_evidence_required": False,
                "publication_authority": False,
            }
        return {
            "status": "PASS",
            "cluster_id": request["cluster_id"],
            "headline_ids": list(request["headline_ids"]),
            "provided_evidence_capabilities": list(
                request["required_evidence_capabilities"]
            ),
            "evidence_documents": [
                {
                    "document_id": "official-fixture-document",
                    "source_url": (
                        "https://www.newyorkfed.org/newsevents/news/research/2026/report"
                    ),
                }
            ],
            "claim_evidence_contract": {
                "status": "PASS",
                "supported_claim_count": 1,
                "fabricated_claim_count": 0,
                "supported_claims": [
                    {
                        "claim_id": "fixture-claim",
                        "claim_text": "The controlled official record confirms the event.",
                        "support_status": "SUPPORTED_PRIMARY",
                    }
                ],
                "omitted_unsupported_claims": [],
            },
            "capital_chronicle_authority_verified": False,
            "numeric_evidence_required": False,
            "blockers": [],
            "publication_authority": False,
        }

    def classify(*, clusters, **_kwargs):
        mapping = {
            str(row["cluster_id"]): "regulatory_fiscal_event" for row in clusters
        }
        return {
            "stories": [
                {
                    "cluster_id": cluster_id,
                    "story_type": story_type,
                    "reason": "Controlled classification fixture.",
                }
                for cluster_id, story_type in mapping.items()
            ],
            "story_type_by_cluster": mapping,
            "semantic_routing_grants_authority": False,
        }

    article_calls = []

    def stop_after_selection(viability):
        article_calls.append(dict(viability))
        raise GroundedArticleBuilderError("fixture_stop_after_publishability_selection")

    result = pipeline._run_rolling_x_newsroom_cycle(
        run_id="rank-thirteen-publishability-walk",
        output_dir=tmp_path,
        cutoff_utc="2026-08-12T00:00:00Z",
        rolling_input=intake,
        evidence_acquirer=acquire,
        story_type_classifier=classify,
        article_builder=stop_after_selection,
        editorial_reviewer=lambda _article: {},
        article_reviser=lambda value, _review, _round: value,
        publication_enabled=False,
    )

    pool = result["publishability_candidate_pool"]
    assert pool["source_ranked_candidate_count"] == 12
    assert pool["combined_candidate_count"] == 14
    assert pool["reserve_candidate_count"] == 2
    assert pool["compact_universe_exhausted_by_pool"] is True
    assert pool["combined_candidate_binding_hash"]
    # The exact-official unused semantic leaf is promoted before secondary paths, so the
    # shared request budget is not consumed by twelve four-request secondary probes first.
    assert len(evidence_calls) == 1
    assert shared_request_counter == {"count": 1, "limit": 24}
    assert evidence_calls[0]["headline_ids"] == ["h13"]
    assert result["ranked_viability"]["selected_rank"] == 1
    assert result["ranked_viability"]["selected_headline_ids"] == ["h13"]
    assert len(article_calls) == 1
    assert article_calls[0]["selected_headline_ids"] == ["h13"]
    assert article_calls[0]["selected_cluster"]["preselection_original_rank"] == 1
    assert (
        article_calls[0]["selected_cluster"]["publishability_pool_origin"]
        == "UNUSED_SEMANTIC_LEAF_RESERVE"
    )
    assert article_calls[0]["selected_cluster"]["entities_topics"] == [
        "entity-13", "controlled-event"
    ]
    assert article_calls[0]["selected_cluster"]["update_chain"] == {
        "relationship": "distinct",
        "ordered_headline_ids": ["h13"],
    }


def test_preselection_recognizes_exact_official_org_host_without_suffix_guessing():
    reach = _preselection_evidence_reachability(
        {
            "public_source_urls": [
                "https://www.newyorkfed.org/newsevents/news/research/2026/report"
            ]
        },
        {},
    )

    assert reach["known_official_path"] is True
    assert reach["unregistered_official_suffix_candidate"] is False
    assert reach["factual_authority_granted"] is False


def test_preselection_caps_editorial_rank_decay_for_large_publishability_pool(
    monkeypatch,
):
    monkeypatch.setattr(
        "live_contentops.preselection_intelligence_v1.query_story_scoped_cc_context",
        lambda _catalog, _entities: {
            "cc_context_richness": 0.0,
            "matched_store_ids": [],
            "matched_store_count": 0,
            "matches": [],
            "grants_factual_or_numeric_authority": False,
        },
    )
    result = apply_preselection_intelligence(
        [
            {"cluster_id": "first", "rank": 1, "headline_ids": ["h1"]},
            {"cluster_id": "reserve", "rank": 64, "headline_ids": ["h64"]},
        ],
        published_corpus=[],
        cc_catalog={"stores": []},
    )
    scores = {
        row["cluster_id"]: row["preselection_score"]
        for row in result["ranked_clusters"]
    }

    assert scores["first"] - scores["reserve"] == 16.0


def test_publishability_pool_preserves_semantic_no_publication_decision():
    assignment = {
        "schema_version": "capital_chronicle.rolling_x_newsroom_assignment.v1",
        "status": "NO_PUBLICATION",
        "decision": "NO_PUBLICATION",
        "reason_code": "EDITORIAL_NO_PUBLICATION",
        "ranked_clusters": [],
    }
    result = build_bounded_rolling_x_publishability_pool(
        assignment=assignment,
        rolling_input={
            "schema_version": "capital_chronicle.rolling_x_headline_input.v1",
            "headlines": [
                {
                    "headline_id": "held-by-editor",
                    "source_timestamp_utc": "2026-08-11T23:00:00Z",
                    "external_content": {
                        "headline_text": "The semantic editor intentionally held this item."
                    },
                }
            ],
        },
    )

    assert result["decision"] == "NO_PUBLICATION"
    assert result["reason_code"] == "EDITORIAL_NO_PUBLICATION"
    assert result["ranked_clusters"] == []
    telemetry = result["publishability_candidate_pool"]
    assert telemetry["reserve_candidate_count"] == 0
    assert telemetry["combined_candidate_count"] == 0
    assert telemetry["included_compact_headline_count"] == 0
    assert telemetry["held_after_bounded_pool_count"] == 1
    assert telemetry["candidate_order"] == []
    assert telemetry["combined_candidate_binding_hash"]
    assert telemetry["pool_logical_hash"]


def _valid_pool_fixture():
    headlines = [
        {
            "headline_id": f"h{index}",
            "source_timestamp_utc": "2026-08-11T23:00:00Z",
            "external_content": {
                "headline_text": f"Bound event {index}",
                "official_source_urls": [],
            },
        }
        for index in range(2)
    ]
    rolling_input = {
        "schema_version": "capital_chronicle.rolling_x_headline_input.v1",
        "canonical_input_hash": "bound-input",
        "headlines": headlines,
    }
    leaves = [
        {
            "leaf_cluster_id": f"leaf-{index}",
            "member_headline_ids": [f"h{index}"],
            "canonical_representative_headline_id": f"h{index}",
            "event_topic_summary": f"Bound event {index}",
            "entities": [f"Entity {index}"],
            "topics": ["bound-event"],
            "duplicate_update_chain": {
                "relationship": "distinct",
                "ordered_headline_ids": [f"h{index}"],
            },
        }
        for index in range(2)
    ]
    assignment = {
        "schema_version": "capital_chronicle.rolling_x_newsroom_assignment.v1",
        "status": "SUCCESS",
        "decision": "SELECT_STORY",
        "input_binding": {"canonical_input_hash": "bound-input"},
        "ranked_clusters": [{
            "cluster_id": "ranked-0",
            "rank": 1,
            "headline_ids": ["h0"],
            "leaf_cluster_ids": ["leaf-0"],
            "article_mode": "breaking",
            "needed_evidence": ["Official record."],
        }],
        "leaf_clusters": leaves,
        "assignment_method": "NINE_ROUTER_SEMANTIC_ASSIGNMENT",
    }
    return assignment, rolling_input


def test_publishability_pool_preserves_unused_semantic_leaf_bindings():
    assignment, rolling_input = _valid_pool_fixture()

    result = build_bounded_rolling_x_publishability_pool(
        assignment=assignment, rolling_input=rolling_input
    )

    reserve = next(
        row for row in result["ranked_clusters"]
        if row["publishability_pool_origin"] == "UNUSED_SEMANTIC_LEAF_RESERVE"
    )
    assert reserve["headline_ids"] == ["h1"]
    assert reserve["leaf_cluster_ids"] == ["leaf-1"]
    assert reserve["entities_topics"] == ["Entity 1", "bound-event"]
    assert reserve["update_chain"]["ordered_headline_ids"] == ["h1"]
    assert result["publishability_candidate_pool"]["combined_candidate_binding_hash"]


def test_publishability_pool_expands_bounded_deterministic_fallback():
    _, rolling_input = _valid_pool_fixture()
    rolling_input = deepcopy(rolling_input)
    rolling_input["headlines"] = [
        {
            "headline_id": f"h{index}",
            "source_timestamp_utc": "2026-08-11T23:00:00Z",
            "external_content": {
                "headline_text": f"Bound event {index}",
                "official_source_urls": [],
            },
        }
        for index in range(20)
    ]
    assignment = build_deterministic_rolling_x_assignment_fallback(
        rolling_input=rolling_input,
        max_ranked_clusters=12,
    )

    result = build_bounded_rolling_x_publishability_pool(
        assignment=assignment,
        rolling_input=rolling_input,
    )

    assert len(result["ranked_clusters"]) == 20
    assert len(result["leaf_clusters"]) == 20
    assert result["publishability_candidate_pool"]["reserve_candidate_count"] == 8
    assert result["publishability_candidate_pool"]["held_after_bounded_pool_count"] == 0


def test_canonical_cycle_falls_back_once_when_semantic_leaf_union_is_invalid(
    monkeypatch, tmp_path
):
    assignment, rolling_input = _valid_pool_fixture()
    invalid = deepcopy(assignment)
    invalid["leaf_clusters"] = invalid["leaf_clusters"][:1]

    def invalid_assignment(**kwargs):
        invalid["input_binding"]["canonical_input_hash"] = kwargs[
            "rolling_input"
        ]["canonical_input_hash"]
        return invalid

    monkeypatch.setattr(
        "live_contentops.newsroom_assignment_scheduler_v1.assign_rolling_x_headlines_with_nine_router",
        invalid_assignment,
    )

    def blocked_evidence(request):
        return {
            "status": "BLOCKED",
            "cluster_id": request["cluster_id"],
            "headline_ids": list(request["headline_ids"]),
            "provided_evidence_capabilities": [],
            "evidence_documents": [],
            "claim_evidence_contract": {"status": "BLOCKED"},
            "blockers": ["controlled_no_evidence"],
            "capital_chronicle_authority_verified": False,
            "numeric_evidence_required": False,
            "publication_authority": False,
        }

    result = pipeline._run_rolling_x_newsroom_cycle(
        run_id="invalid-semantic-leaf-union",
        output_dir=tmp_path,
        cutoff_utc="2026-08-12T00:00:00Z",
        rolling_input={
            **rolling_input,
            "cutoff_time_utc": "2026-08-12T00:00:00Z",
            "window_start_utc": "2026-08-11T00:00:00Z",
            "window_hours": 24.0,
            "unique_headline_ids": ["h0", "h1"],
            "counts": {"accepted": 2},
        },
        evidence_acquirer=blocked_evidence,
        story_type_classifier=lambda *, clusters, **_kwargs: {
            "stories": [
                {"cluster_id": row["cluster_id"], "story_type": "breaking_news"}
                for row in clusters
            ],
            "story_type_by_cluster": {
                row["cluster_id"]: "breaking_news" for row in clusters
            },
            "semantic_routing_grants_authority": False,
        },
        publication_enabled=False,
    )

    fallback = result["assignment"]["semantic_assignment_failure"]
    assert fallback["reason_code"] == "ROLLING_X_SEMANTIC_ASSIGNMENT_BINDING_INVALID"
    assert fallback["validation_error"] == (
        "rolling_x_publishability_pool_leaf_headline_union_mismatch"
    )
    assert result["classification"] in {"NO_PUBLICATION", "BLOCKED"}
    assert result["public_write_performed"] is False


@pytest.mark.parametrize(
    ("mutate", "reason"),
    [
        (
            lambda assignment, _input: assignment["ranked_clusters"][0].update(
                {"rank": True}
            ),
            "rolling_x_publishability_pool_source_binding_invalid",
        ),
        (
            lambda assignment, _input: assignment["ranked_clusters"][0].update(
                {"leaf_cluster_ids": ["leaf-1"]}
            ),
            "rolling_x_publishability_pool_source_leaf_union_mismatch",
        ),
        (
            lambda assignment, _input: assignment["leaf_clusters"][1].update(
                {"member_headline_ids": ["h0"]}
            ),
            "rolling_x_publishability_pool_leaf_binding_invalid",
        ),
        (
            lambda assignment, rolling_input: rolling_input.update(
                {"canonical_input_hash": "different-input"}
            ),
            "rolling_x_publishability_pool_input_hash_mismatch",
        ),
    ],
)
def test_publishability_pool_rejects_invalid_assignment_bindings(mutate, reason):
    assignment, rolling_input = _valid_pool_fixture()
    assignment = deepcopy(assignment)
    rolling_input = deepcopy(rolling_input)
    mutate(assignment, rolling_input)

    with pytest.raises(ValueError, match=f"^{reason}$"):
        build_bounded_rolling_x_publishability_pool(
            assignment=assignment, rolling_input=rolling_input
        )
