from __future__ import annotations

import json
from pathlib import Path

import pytest

from live_contentops import _eight_platform_substack_first_pipeline_impl_v1 as implementation
from live_contentops.destination_transport_registry_v1 import V1_REQUIRED_PUBLICATION_DESTINATIONS
from live_contentops.nine_router_ordered_model_router_v2 import ProviderResult


def _all_ready():
    return {
        "all_required_destinations_ready": True,
        "destinations": {
            destination: {
                "readiness_state": "READY_NON_BROWSER_BINDING",
                "write_eligible": True,
                "identity_match": True,
            }
            for destination in V1_REQUIRED_PUBLICATION_DESTINATIONS
        },
    }


def _xhigh_receipt(article, governed_input="a" * 64):
    if isinstance(governed_input, dict):
        worker_request = governed_input
        governed_input_hash = worker_request["governed_input_hash"]
        packet = worker_request["bounded_governed_context"][
            "institutional_edge_editorial_packet"
        ]
        title = str(article.get("title") or "Official Event Update")
        dek = str(article.get("dek") or article.get("subtitle") or title)
        body = str(
            article.get("substack_body_markdown")
            or f"{title}. The official record establishes the current position.\n\n"
            "The next official update remains the relevant checkpoint for readers."
        )
        meta = str(article.get("meta_description") or dek)
        slug = str(article.get("slug") or "official-event-update")
        article.update({
            "title": title,
            "canonical_editorial_headline": title,
            "subtitle": dek,
            "dek": dek,
            "seo_title": str(article.get("seo_title") or title),
            "search_title": str(article.get("seo_title") or title),
            "social_lede": str(article.get("social_lede") or title),
            "social_hook": str(article.get("social_lede") or title),
            "meta_description": meta,
            "author_identity": "Capital Chronicle",
            "publisher_identity": "Capital Chronicle",
            "slug": slug,
            "canonical_slug_candidate": slug,
            "substack_body_markdown": body,
            "primary_reader_question": "What does the official record establish?",
            "secondary_reader_questions": [],
            "entities": ["Official Agency"],
            "topics": ["official event"],
            "search_freshness_class": "CURRENT",
            "internal_link_candidates": [],
            "structured_data_packet": {
                "@type": "NewsArticle",
                "headline": title,
                "description": meta,
                "datePublished": "2026-08-17T09:00:00Z",
                "dateModified": "2026-08-17T09:00:00Z",
                "author": "Capital Chronicle",
                "publisher": "Capital Chronicle",
            },
            "epistemic_claims": [],
            "quote_source_records": [],
            "humor_lines": [],
            "institutional_edge_editorial_packet_sha256": packet[
                "editorial_packet_sha256"
            ],
        })
    else:
        governed_input_hash = governed_input
    return {
        "model": "gpt-5.6-sol", "reasoning_effort": "XHIGH",
        "fresh": True, "isolated": True,
        "governed_input_hash": governed_input_hash,
        "bounded_revision_count": 0,
        "public_write_attempted": False,
        "article": article,
    }


def _article(body="Current official event analysis with reader-facing context."):
    return {
        "title": "Official Event Update",
        "subtitle": "Verified official records establish the event timeline and explain what readers should watch next.",
        "seo_title": "Official Event Update",
        "slug": "official-event-update",
        "meta_description": "An official event update with verified context, limitations, and implications for readers.",
        "editorial_mode": "analysis",
        "substack_body_markdown": body,
        "market_mechanism": "The official timeline clarifies how the event affects the named entities and what remains unresolved.",
        "policy_context": "The governing record defines the current scope and implementation sequence without adding market claims.",
        "cross_asset_implications": "No market or cross-asset reaction is asserted without separate Capital Chronicle evidence.",
    }


def _semantic(decision, failed_checks=None):
    return {
        "status": "SUCCESS",
        "decision": decision,
        "mode": "analysis",
        "issues": [] if decision == "PASS" else ["clarify why now"],
        "failed_checks": (
            []
            if decision == "PASS"
            else list(failed_checks or ["material_claims_supported"])
        ),
        "publication_authority": False,
    }


def _story_routing(clusters, story_type="regulatory_fiscal_event", **_kwargs):
    return {
        "stories": [
            {
                "cluster_id": row["cluster_id"],
                "story_type": story_type,
                "reason": "Exact focused test routing.",
            }
            for row in clusters
        ],
        "story_type_by_cluster": {
            row["cluster_id"]: story_type for row in clusters
        },
        "router_summary": {"terminal_disposition": "accepted"},
        "semantic_routing_grants_authority": False,
    }


def _walk_viability(rank: int, *, status: str = "SUCCESS", blockers=None) -> dict:
    cluster = {
        "cluster_id": f"candidate-{rank}",
        "rank": rank,
        "headline_ids": [f"headline-{rank}"],
        "resolved_article_mode": "BREAKING_BRIEF",
    }
    blocked = status != "SUCCESS"
    attempt = {
        "rank": rank,
        "cluster_id": cluster["cluster_id"],
        "headline_ids": cluster["headline_ids"],
        "status": "BLOCKED" if blocked else "VIABLE",
        "effective_article_mode": "BREAKING_BRIEF",
        "blockers": list(blockers or []),
    }
    return {
        "status": status,
        "decision": "NO_PUBLICATION" if blocked else "SELECT_STORY",
        "reason_code": "ALL_RANKED_CLUSTERS_EVIDENCE_BLOCKED" if blocked else "FIRST_VIABLE_RANKED_CLUSTER_SELECTED",
        "ranked_candidate_count": 3,
        "selected_rank": None if blocked else rank,
        "selected_cluster_id": None if blocked else cluster["cluster_id"],
        "selected_headline_ids": [] if blocked else cluster["headline_ids"],
        "selected_cluster": None if blocked else cluster,
        "selected_evidence": None if blocked else {"status": "PASS"},
        "rank_attempts": [attempt],
        "publication_authority_granted": False,
    }


def _configure_candidate_walk_cycle(monkeypatch, selector, editorial):
    monkeypatch.setattr(
        "live_contentops.newsroom_assignment_scheduler_v1.load_rolling_x_headline_sidecars",
        lambda **kwargs: {
            "schema_version": "capital_chronicle.rolling_x_headline_input.v1",
            "counts": {"accepted": 3},
        },
    )
    monkeypatch.setattr(
        "live_contentops.newsroom_assignment_scheduler_v1.assign_rolling_x_headlines_with_nine_router",
        lambda **kwargs: {
            "status": "SUCCESS",
            "decision": "SELECT_STORY",
            "assignment_logical_hash": "candidate-walk-assignment",
        },
    )
    monkeypatch.setattr(
        "live_contentops.newsroom_assignment_scheduler_v1.select_first_viable_rolling_x_cluster",
        selector,
    )
    monkeypatch.setattr(implementation, "_run_bounded_rolling_x_editorial_cycle", editorial)
    monkeypatch.setattr(
        implementation,
        "_prepare_rolling_x_release_candidate",
        lambda **kwargs: {
            "classification": "PASS_TEXT_IMAGE_RELEASE_CANDIDATE_REHEARSAL",
            "release_candidate_lock_verification": {"status": "PASS_RELEASE_CANDIDATE_LOCK"},
            "payloads": {"substack": {"title": kwargs["article"].get("title")}},
        },
    )
    monkeypatch.setattr(
        implementation,
        "_build_rolling_x_publication_plan",
        lambda **kwargs: {"schema_version": "test.plan.v1", "destinations": ["substack"]},
    )


@pytest.mark.parametrize(
    (
        "resolved_owner",
        "resolved_mode",
        "expected_routing_mode",
        "expected_institutional_mode",
    ),
    [
        ("attempt_effective", "WEEK_AHEAD_OR_WATCH", "WEEK_AHEAD_OR_WATCH", "WEEK_AHEAD_WATCH"),
        ("cluster_resolved", "DATA_OR_DOCUMENT_LENS", "DATA_OR_DOCUMENT_LENS", "DOCUMENT_LENS"),
        ("attempt_resolved", "WHAT_THE_MARKET_IS_MISSING", "WHAT_THE_MARKET_IS_MISSING", "HOUSE_VIEW"),
        ("cluster_resolved", "BREAKING_BRIEF", "BREAKING_BRIEF", "BREAKING_BRIEF"),
        (None, None, "breaking", "BREAKING_BRIEF"),
    ],
)
def test_canonical_cycle_routes_resolved_product_mode_before_legacy_fallback(
    monkeypatch,
    tmp_path: Path,
    resolved_owner,
    resolved_mode,
    expected_routing_mode,
    expected_institutional_mode,
):
    viability = _walk_viability(1)
    selected_attempt = viability["rank_attempts"][0]
    selected_attempt.pop("effective_article_mode")
    selected_attempt["request"] = {"article_mode": "breaking"}
    viability["selected_cluster"].pop("resolved_article_mode")
    if resolved_owner == "attempt_effective":
        selected_attempt["effective_article_mode"] = resolved_mode
    elif resolved_owner == "attempt_resolved":
        selected_attempt["resolved_article_mode"] = resolved_mode
    elif resolved_owner == "cluster_resolved":
        viability["selected_cluster"]["resolved_article_mode"] = resolved_mode

    _configure_candidate_walk_cycle(
        monkeypatch,
        lambda **kwargs: viability,
        lambda **kwargs: {
            "status": "PASS",
            "article": kwargs["article"],
            "mandatory_semantic_review_calls": 0,
            "review_history": [],
        },
    )

    from live_contentops import codex_desktop_newsroom_operator_v1 as desktop_operator

    real_build_route = desktop_operator.build_editorial_worker_routing_packet
    routed_modes = []

    def capture_route(**kwargs):
        routed_modes.append(kwargs["article_mode"])
        return real_build_route(**kwargs)

    monkeypatch.setattr(
        desktop_operator,
        "build_editorial_worker_routing_packet",
        capture_route,
    )
    worker_requests = []

    def build_article(value):
        worker_request = value["editorial_worker_request"]
        worker_requests.append(worker_request)
        article = {
            "title": "Canonical mode propagation",
            "cluster_id": value["selected_cluster_id"],
            "headline_ids": value["selected_headline_ids"],
            "effective_article_mode": resolved_mode or "BREAKING_BRIEF",
        }
        return {
            "article": article,
            "media": {"assets": []},
            "critical_path_telemetry": {"article_writer_semantic_calls": 1},
            "editorial_worker_receipt": _xhigh_receipt(article, worker_request),
        }

    result = implementation._run_rolling_x_newsroom_cycle(
        run_id=f"mode-propagation-{expected_institutional_mode.lower()}",
        output_dir=tmp_path,
        cutoff_utc="2026-08-20T12:00:13Z",
        article_builder=build_article,
        destination_readiness_override=_all_ready(),
        publication_enabled=True,
    )

    assert result["classification"] == "PASS_PUBLICATION_PLAN_READY"
    assert routed_modes == [expected_routing_mode]
    assert len(worker_requests) == 1
    institutional_packet = worker_requests[0]["bounded_governed_context"][
        "institutional_edge_editorial_packet"
    ]
    assert institutional_packet["article_mode"] == expected_institutional_mode
    assert institutional_packet["grants_factual_authority"] is False
    assert institutional_packet["grants_numeric_authority"] is False
    assert institutional_packet["grants_permission_authority"] is False
    assert institutional_packet["grants_public_write_authority"] is False
    assert result["public_write_performed"] is False


def test_same_opportunity_reader_value_failure_advances_and_first_publishable_stops(
    monkeypatch, tmp_path: Path
):
    selector_calls = []
    builder_calls = []

    def selector(**kwargs):
        start = int(kwargs.get("start_after_rank") or 0)
        selector_calls.append(start)
        return _walk_viability(1 if start == 0 else 2)

    def editorial(**kwargs):
        article = dict(kwargs["article"])
        if article["cluster_id"] == "candidate-1":
            return {
                "status": "NO_PUBLICATION",
                "reason_code": "INSUFFICIENT_READER_VALUE",
                "article": article,
                "mandatory_semantic_review_calls": 0,
                "review_history": [{
                    "deterministic_review": {
                        "reader_value_gate": {"blockers": ["mode_appropriate_substance"]}
                    }
                }],
            }
        return {
            "status": "PASS",
            "article": article,
            "mandatory_semantic_review_calls": 0,
            "review_history": [],
        }

    _configure_candidate_walk_cycle(monkeypatch, selector, editorial)

    def builder(value):
        rank = int(value["selected_rank"])
        builder_calls.append(rank)
        article = {
                "title": f"Candidate {rank}",
                "cluster_id": value["selected_cluster_id"],
                "headline_ids": value["selected_headline_ids"],
                "effective_article_mode": "BREAKING_BRIEF",
            }
        return {
            "article": article,
            "media": {"assets": []},
            "critical_path_telemetry": {"article_writer_semantic_calls": 1},
            "editorial_worker_receipt": _xhigh_receipt(
                article, value["editorial_worker_request"]
            ),
        }

    result = implementation._run_rolling_x_newsroom_cycle(
        run_id="candidate-walk-reader-value",
        output_dir=tmp_path,
        cutoff_utc="2026-08-15T07:00:00Z",
        article_builder=builder,
        destination_readiness_override=_all_ready(),
        publication_enabled=True,
    )

    assert result["classification"] == "PASS_PUBLICATION_PLAN_READY"
    assert builder_calls == [1, 2]
    assert selector_calls == [0, 1]
    assert result["candidate_walk"]["selected_publication_candidate_rank"] == 2
    assert [row["terminal_reason"] for row in result["candidate_walk"]["candidate_attempts"]] == [
        "INSUFFICIENT_READER_VALUE",
        "PUBLICATION_QUALIFIED",
    ]
    assert result["critical_path_telemetry"]["mandatory_semantic_review_calls"] == 0


def test_post_xhigh_validation_failure_terminalizes_candidate_and_advances_distinct_rank(
    monkeypatch, tmp_path: Path
):
    selector_calls = []
    builder_calls = []

    def selector(**kwargs):
        start = int(kwargs.get("start_after_rank") or 0)
        selector_calls.append(start)
        return _walk_viability(1 if start == 0 else 2)

    _configure_candidate_walk_cycle(
        monkeypatch,
        selector,
        lambda **kwargs: {
            "status": "PASS",
            "article": kwargs["article"],
            "mandatory_semantic_review_calls": 0,
            "review_history": [],
        },
    )

    def builder(value):
        rank = int(value["selected_rank"])
        builder_calls.append(rank)
        article = {
            "title": f"Candidate {rank}",
            "cluster_id": value["selected_cluster_id"],
            "headline_ids": value["selected_headline_ids"],
            "effective_article_mode": "BREAKING_BRIEF",
        }
        receipt = _xhigh_receipt(article, value["editorial_worker_request"])
        if rank == 1:
            receipt["bounded_revision_count"] = 1
            receipt["article"]["substack_body_markdown"] += (
                "\n\nThe publication title is “Federal Reserve H.4.1.”"
            )
            receipt["article"]["quote_source_records"] = []
        return {
            "article": receipt["article"],
            "media": {"assets": []},
            "critical_path_telemetry": {"article_writer_semantic_calls": 1},
            "editorial_worker_receipt": receipt,
        }

    result = implementation._run_rolling_x_newsroom_cycle(
        run_id="candidate-walk-post-xhigh-validation",
        output_dir=tmp_path,
        cutoff_utc="2026-08-20T12:00:13Z",
        article_builder=builder,
        destination_readiness_override=_all_ready(),
        publication_enabled=True,
    )

    assert result["classification"] == "PASS_PUBLICATION_PLAN_READY"
    assert builder_calls == [1, 2]
    assert selector_calls == [0, 1]
    attempts = result["candidate_walk"]["candidate_attempts"]
    assert [row["rank"] for row in attempts] == [1, 2]
    assert attempts[0]["terminal_reason"].startswith(
        "EDITORIAL_WORKER_DETERMINISTIC_VALIDATION_FAILED:"
    )
    assert attempts[0]["deterministic_validation_blockers"] == [
        "fake_or_unbound_quote_presentation"
    ]
    assert attempts[1]["terminal_reason"] == "PUBLICATION_QUALIFIED"
    assert len({row["cluster_id"] for row in attempts}) == 2
    assert result["candidate_walk"]["selected_publication_candidate_rank"] == 2


def test_exhausted_native_xhigh_candidate_advances_to_distinct_fresh_worker(
    monkeypatch, tmp_path: Path
):
    selector_calls = []
    builder_calls = []

    def selector(**kwargs):
        start = int(kwargs.get("start_after_rank") or 0)
        selector_calls.append(start)
        return _walk_viability(1 if start == 0 else 2)

    real_editorial_cycle = implementation._run_bounded_rolling_x_editorial_cycle
    _configure_candidate_walk_cycle(
        monkeypatch,
        selector,
        lambda **kwargs: (_ for _ in ()).throw(
            AssertionError("real native XHIGH editorial path must be used")
        ),
    )
    monkeypatch.setattr(
        implementation, "_run_bounded_rolling_x_editorial_cycle", real_editorial_cycle
    )
    monkeypatch.setattr(
        "live_contentops.tier1_editorial_quality_v1.audit_tier1_article",
        lambda article, media_assets=(): {"classification": "PASS"},
    )
    router_reviser_calls = []

    def builder(value):
        rank = int(value["selected_rank"])
        builder_calls.append(rank)
        article = {
            "title": f"Candidate {rank}",
            "cluster_id": value["selected_cluster_id"],
            "headline_ids": value["selected_headline_ids"],
            "effective_article_mode": "BREAKING_BRIEF",
        }
        receipt = _xhigh_receipt(article, value["editorial_worker_request"])
        receipt["bounded_revision_count"] = 1 if rank == 1 else 0
        return {
            "article": receipt["article"],
            "media": {"assets": []},
            "critical_path_telemetry": {"article_writer_semantic_calls": 1},
            "editorial_worker_receipt": receipt,
        }

    result = implementation._run_rolling_x_newsroom_cycle(
        run_id="candidate-walk-native-xhigh-budget",
        output_dir=tmp_path,
        cutoff_utc="2026-08-20T12:00:13Z",
        article_builder=builder,
        editorial_reviewer=lambda article: _semantic(
            "NEEDS_REVISION" if article["cluster_id"] == "candidate-1" else "PASS"
        ),
        article_reviser=lambda *args: router_reviser_calls.append(args),
        destination_readiness_override=_all_ready(),
        publication_enabled=True,
    )

    assert result["classification"] == "PASS_PUBLICATION_PLAN_READY"
    assert builder_calls == [1, 2]
    assert selector_calls == [0, 1]
    assert router_reviser_calls == []
    attempts = result["candidate_walk"]["candidate_attempts"]
    assert attempts[0]["terminal_reason"] == "EDITORIAL_WORKER_REVISION_BUDGET_EXHAUSTED"
    assert attempts[1]["terminal_reason"] == "PUBLICATION_QUALIFIED"
    assert result["candidate_walk"]["selected_publication_candidate_rank"] == 2


def test_same_opportunity_evidence_failure_advances_before_writer(monkeypatch, tmp_path: Path):
    builder_calls = []
    viability = _walk_viability(2)
    viability["rank_attempts"].insert(
        0,
        {
            "rank": 1,
            "cluster_id": "candidate-1",
            "headline_ids": ["headline-1"],
            "status": "BLOCKED",
            "effective_article_mode": "BREAKING_BRIEF",
            "blockers": ["minimum_trustworthy_evidence_missing"],
        },
    )
    _configure_candidate_walk_cycle(
        monkeypatch,
        lambda **kwargs: viability,
        lambda **kwargs: {
            "status": "PASS",
            "article": kwargs["article"],
            "mandatory_semantic_review_calls": 0,
            "review_history": [],
        },
    )

    result = implementation._run_rolling_x_newsroom_cycle(
        run_id="candidate-walk-evidence",
        output_dir=tmp_path,
        cutoff_utc="2026-08-15T07:00:00Z",
        article_builder=lambda value: builder_calls.append(value["selected_rank"]) or (lambda article: {
            "article": article,
            "media": {"assets": []},
            "critical_path_telemetry": {"article_writer_semantic_calls": 1},
            "editorial_worker_receipt": _xhigh_receipt(
                article, value["editorial_worker_request"]
            ),
        })({
                "title": "Candidate 2",
                "cluster_id": value["selected_cluster_id"],
                "headline_ids": value["selected_headline_ids"],
                "effective_article_mode": "BREAKING_BRIEF",
            }),
        destination_readiness_override=_all_ready(),
        publication_enabled=True,
    )

    assert result["classification"] == "PASS_PUBLICATION_PLAN_READY"
    assert builder_calls == [2]
    assert result["candidate_walk"]["candidate_attempts"][0]["terminal_reason"].startswith(
        "EVIDENCE_BLOCKED:"
    )


def test_publication_article_without_valid_native_xhigh_receipt_fails_closed(
    monkeypatch, tmp_path: Path
):
    viability = _walk_viability(1)
    _configure_candidate_walk_cycle(
        monkeypatch,
        lambda **kwargs: viability,
        lambda **kwargs: (_ for _ in ()).throw(
            AssertionError("invalid worker return must stop before editorial review")
        ),
    )
    result = implementation._run_rolling_x_newsroom_cycle(
        run_id="invalid-native-xhigh-receipt",
        output_dir=tmp_path,
        cutoff_utc="2026-08-15T07:00:00Z",
        article_builder=lambda value: {
            "article": {
                "title": "Unbound article",
                "cluster_id": value["selected_cluster_id"],
                "headline_ids": value["selected_headline_ids"],
            },
            "media": {"assets": []},
        },
        destination_readiness_override=_all_ready(),
        publication_enabled=True,
    )
    assert result["classification"] == "NO_PUBLICATION"
    assert result["exact_next_blocker"] == "ALL_BOUNDED_CANDIDATES_EXHAUSTED"
    assert result["candidate_walk"]["candidate_attempts"][0]["terminal_reason"] == (
        "EDITORIAL_WORKER_UNAVAILABLE_OR_INVALID"
    )
    assert result["legacy_writer_fallback_used"] is False


def test_publication_probe_exposes_initial_native_xhigh_request_without_building_copy(
    monkeypatch, tmp_path: Path
):
    viability = _walk_viability(1)
    _configure_candidate_walk_cycle(
        monkeypatch,
        lambda **kwargs: viability,
        lambda **kwargs: (_ for _ in ()).throw(
            AssertionError("probe must stop before editorial review")
        ),
    )

    result = implementation._run_rolling_x_newsroom_cycle(
        run_id="native-xhigh-probe-request",
        output_dir=tmp_path,
        cutoff_utc="2026-08-20T12:00:13Z",
        destination_readiness_override=_all_ready(),
        publication_enabled=True,
    )

    assert result["classification"] == "NO_PUBLICATION"
    assert result["exact_next_blocker"] == "EDITORIAL_WORKER_UNAVAILABLE_OR_INVALID"
    assert result["editorial_worker_routing"]["decision"] == (
        "SPAWN_ONE_FRESH_ISOLATED_XHIGH_EDITORIAL_WORKER"
    )
    assert result["legacy_writer_fallback_used"] is False
    assert result["public_write_performed"] is False
    assert result["public_write_performed"] is False


def test_all_candidate_exhaustion_returns_truthful_no_publication(monkeypatch, tmp_path: Path):
    def selector(**kwargs):
        start = int(kwargs.get("start_after_rank") or 0)
        if start < 2:
            return _walk_viability(start + 1)
        return _walk_viability(
            3,
            status="NO_PUBLICATION",
            blockers=["minimum_trustworthy_evidence_missing"],
        )

    _configure_candidate_walk_cycle(
        monkeypatch,
        selector,
        lambda **kwargs: {
            "status": "NO_PUBLICATION",
            "reason_code": "INSUFFICIENT_READER_VALUE",
            "article": kwargs["article"],
            "mandatory_semantic_review_calls": 0,
            "review_history": [],
        },
    )
    def builder(value):
        article = {
            "title": f"Candidate {value['selected_rank']}",
            "cluster_id": value["selected_cluster_id"],
            "headline_ids": value["selected_headline_ids"],
            "effective_article_mode": "BREAKING_BRIEF",
        }
        return {
            "article": article,
            "media": {"assets": []},
            "critical_path_telemetry": {"article_writer_semantic_calls": 1},
            "editorial_worker_receipt": _xhigh_receipt(
                article, value["editorial_worker_request"]
            ),
        }

    result = implementation._run_rolling_x_newsroom_cycle(
        run_id="candidate-walk-exhaustion",
        output_dir=tmp_path,
        cutoff_utc="2026-08-15T07:00:00Z",
        article_builder=builder,
        destination_readiness_override=_all_ready(),
        publication_enabled=True,
    )

    assert result["classification"] == "NO_PUBLICATION"
    assert result["exact_next_blocker"] == "ALL_BOUNDED_CANDIDATES_EXHAUSTED"
    assert result["candidate_walk"]["attempted_candidate_count"] == 3
    assert result["candidate_walk"]["unattempted_candidate_count"] == 0
    assert [row["rank"] for row in result["candidate_walk"]["candidate_attempts"]] == [1, 2, 3]


def test_bounded_editorial_cycle_immediate_pass(monkeypatch):
    monkeypatch.setattr(
        "live_contentops.tier1_editorial_quality_v1.audit_tier1_article",
        lambda article, media_assets=(): {"classification": "PASS"},
    )
    revisions = []
    result = implementation._run_bounded_rolling_x_editorial_cycle(
        article=_article(),
        media_assets=[],
        editorial_reviewer=lambda article: _semantic("PASS"),
        article_reviser=lambda article, review, round_number: revisions.append(round_number),
    )
    assert result["status"] == "PASS"
    assert result["revision_rounds_completed"] == 0
    assert revisions == []


def test_bounded_editorial_cycle_revises_once_then_passes(monkeypatch):
    monkeypatch.setattr(
        "live_contentops.tier1_editorial_quality_v1.audit_tier1_article",
        lambda article, media_assets=(): {"classification": "PASS"},
    )
    decisions = iter(("NEEDS_REVISION", "PASS"))
    result = implementation._run_bounded_rolling_x_editorial_cycle(
        article=_article(),
        media_assets=[],
        editorial_reviewer=lambda article: _semantic(next(decisions)),
        article_reviser=lambda article, review, round_number: {
            **article,
            "substack_body_markdown": article["substack_body_markdown"] + " Clarified why now.",
        },
    )
    assert result["status"] == "PASS"
    assert result["revision_rounds_completed"] == 1
    assert len(result["review_history"]) == 2


def test_bounded_editorial_cycle_exhausts_after_one_revision(monkeypatch):
    monkeypatch.setattr(
        "live_contentops.tier1_editorial_quality_v1.audit_tier1_article",
        lambda article, media_assets=(): {"classification": "PASS"},
    )
    result = implementation._run_bounded_rolling_x_editorial_cycle(
        article=_article(),
        media_assets=[],
        editorial_reviewer=lambda article: _semantic("NEEDS_REVISION"),
        article_reviser=lambda article, review, round_number: {
            **article,
            "substack_body_markdown": article["substack_body_markdown"] + f" Revision {round_number}.",
        },
    )
    assert result["status"] == "NO_PUBLICATION"
    assert result["reason_code"] == "EDITORIAL_REVISION_ROUNDS_EXHAUSTED"
    assert result["revision_rounds_completed"] == 1
    assert len(result["review_history"]) == 2


def test_bounded_editorial_cycle_skips_second_review_after_style_only_revision(monkeypatch):
    monkeypatch.setattr(
        "live_contentops.tier1_editorial_quality_v1.audit_tier1_article",
        lambda article, media_assets=(): {"classification": "PASS"},
    )
    reviews = []

    def review(_article):
        reviews.append(True)
        return _semantic("NEEDS_REVISION", ["reader_facing_prose"])

    result = implementation._run_bounded_rolling_x_editorial_cycle(
        article=_article(),
        media_assets=[],
        editorial_reviewer=review,
        article_reviser=lambda article, review, round_number: {
            **article,
            "substack_body_markdown": article["substack_body_markdown"]
            + " Clarified reader-facing language.",
        },
    )

    assert result["status"] == "PASS"
    assert result["revision_rounds_completed"] == 1
    assert len(reviews) == 1
    assert result["review_history"][0]["revision"][
        "second_semantic_review_required"
    ] is False


def test_bounded_editorial_cycle_fails_closed_when_review_router_fails(monkeypatch):
    from live_contentops.nine_router_llm_seam_v2 import RoutedInvocationError

    monkeypatch.setattr(
        "live_contentops.tier1_editorial_quality_v1.audit_tier1_article",
        lambda article, media_assets=(): {"classification": "PASS"},
    )

    def fail_review(_article):
        raise RoutedInvocationError(
            {
                "terminal_disposition": "PROVIDER_EXHAUSTED",
                "models_attempted_in_order": ["model-a"],
                "raw_output": "must-not-persist",
            }
        )

    result = implementation._run_bounded_rolling_x_editorial_cycle(
        article=_article(),
        media_assets=[],
        editorial_reviewer=fail_review,
        article_reviser=lambda article, review, round_number: article,
    )

    assert result["status"] == "NO_PUBLICATION"
    assert result["reason_code"] == "EDITORIAL_REVIEW_ROUTER_FAILURE"
    assert result["publication_authority_granted"] is False
    failure = result["review_history"][0]["llm_semantic_review"]["router_failure"]
    assert failure["terminal_disposition"] == "PROVIDER_EXHAUSTED"
    assert "raw_output" not in failure


def test_bounded_editorial_cycle_fails_closed_when_revision_router_fails(monkeypatch):
    from live_contentops.nine_router_llm_seam_v2 import RoutedInvocationError

    monkeypatch.setattr(
        "live_contentops.tier1_editorial_quality_v1.audit_tier1_article",
        lambda article, media_assets=(): {"classification": "PASS"},
    )

    def fail_revision(_article, _review, _round_number):
        raise RoutedInvocationError(
            {
                "terminal_disposition": "BUDGET_EXHAUSTED",
                "budget_exhausted_reason": "llm_cycle_provider_attempt_budget_exhausted",
                "models_attempted_in_order": ["model-a", "model-b"],
                "provider_error": "must-not-persist",
            }
        )

    result = implementation._run_bounded_rolling_x_editorial_cycle(
        article=_article(),
        media_assets=[],
        editorial_reviewer=lambda article: _semantic("NEEDS_REVISION"),
        article_reviser=fail_revision,
    )

    assert result["status"] == "NO_PUBLICATION"
    assert result["reason_code"] == "EDITORIAL_REVISION_ROUTER_FAILURE"
    assert result["revision_rounds_completed"] == 0
    assert result["publication_authority_granted"] is False
    failure = result["review_history"][0]["revision"]["router_failure"]
    assert failure["budget_exhausted_reason"] == (
        "llm_cycle_provider_attempt_budget_exhausted"
    )
    assert "provider_error" not in failure


def _native_xhigh_binding_for_editorial_test(article, revision_count=0):
    from live_contentops.codex_desktop_newsroom_operator_v1 import (
        build_editorial_worker_routing_packet,
        validate_editorial_worker_return,
    )

    route = build_editorial_worker_routing_packet(
        opportunity_state="ARTICLE_QUALIFIED",
        governed_context={
            "accepted_evidence_packet": {
                "status": "PASS",
                "evidence_documents": [{"document_id": "official-1"}],
            },
            "exact_source_handles": ["official-1"],
        },
        readiness_checked_before_editorial=True,
        readiness_state="READY",
    )
    receipt = _xhigh_receipt(dict(article), route["worker_request"])
    receipt["bounded_revision_count"] = revision_count
    return route, receipt, validate_editorial_worker_return(
        worker_return=receipt,
        expected_governed_input_hash=route["governed_input_hash"],
    )


def test_native_xhigh_needs_revision_requires_same_worker_without_router_rewriter(monkeypatch):
    monkeypatch.setattr(
        "live_contentops.tier1_editorial_quality_v1.audit_tier1_article",
        lambda article, media_assets=(): {"classification": "PASS"},
    )
    route, receipt, validation = _native_xhigh_binding_for_editorial_test(_article())
    reviser_calls = []

    result = implementation._run_bounded_rolling_x_editorial_cycle(
        article=_article(),
        media_assets=[],
        editorial_reviewer=lambda article: _semantic("NEEDS_REVISION"),
        article_reviser=lambda *args: reviser_calls.append(args),
        native_xhigh_worker_return=receipt,
        native_xhigh_worker_validation=validation,
        native_xhigh_worker_request=route["worker_request"],
    )

    assert result["reason_code"] == "SAME_XHIGH_WORKER_REVISION_REQUIRED"
    assert result["same_xhigh_worker_revision_contract"]["same_worker_required"] is True
    assert result["same_xhigh_worker_revision_contract"]["router_final_writer_forbidden"] is True
    assert reviser_calls == []


def test_native_xhigh_exhausted_revision_budget_never_calls_router_rewriter(monkeypatch):
    monkeypatch.setattr(
        "live_contentops.tier1_editorial_quality_v1.audit_tier1_article",
        lambda article, media_assets=(): {"classification": "PASS"},
    )
    route, receipt, validation = _native_xhigh_binding_for_editorial_test(
        _article(), revision_count=1
    )
    reviser_calls = []

    result = implementation._run_bounded_rolling_x_editorial_cycle(
        article=_article(),
        media_assets=[],
        editorial_reviewer=lambda article: _semantic("NEEDS_REVISION"),
        article_reviser=lambda *args: reviser_calls.append(args),
        native_xhigh_worker_return=receipt,
        native_xhigh_worker_validation=validation,
        native_xhigh_worker_request=route["worker_request"],
    )

    assert result["reason_code"] == "EDITORIAL_WORKER_REVISION_BUDGET_EXHAUSTED"
    assert result["review_history"][0]["revision"]["native_xhigh_article_reviser_forbidden"] is True
    assert reviser_calls == []


def test_revision_binding_failure_uses_structured_repair_class(monkeypatch):
    from live_contentops import nine_router_llm_seam_v2 as seam

    article = {
        **_article(),
        "cluster_id": "cluster-1",
        "headline_ids": ["headline-1"],
        "evidence_document_ids": ["evidence-1"],
        "x_content_grants_factual_authority": False,
    }
    observed = {}

    def routed(**kwargs):
        observed["prompt"] = kwargs["prompt"]
        invalid = {**article, "cluster_id": "changed-cluster"}
        validation = kwargs["validator"](json.dumps(invalid))
        observed["validation"] = validation
        return {
            "terminal_disposition": "ACCEPTED",
            "output": article,
        }

    monkeypatch.setattr(seam, "routed_llm_invocation", routed)

    revised = implementation._default_rolling_x_article_reviser(
        article,
        {"issues": [{"code": "reader_facing_prose"}]},
        1,
    )

    assert revised == article
    assert observed["validation"] == (
        False,
        "structured_output_malformed",
        None,
        "revision_cluster_id_changed",
    )
    assert "use publisher names rather than raw URLs as link text" in observed["prompt"]
    assert "remove generic financial-advice/informational-purpose boilerplate" in observed["prompt"]
    assert "do not repeat the same claim in adjacent paragraphs" in observed["prompt"]


def test_canonical_cycle_stops_before_generation_when_ranked_evidence_blocks(monkeypatch, tmp_path: Path):
    intake = {
        "schema_version": "capital_chronicle.rolling_x_headline_input.v1",
        "counts": {"accepted": 1},
    }
    assignment = {
        "schema_version": "capital_chronicle.rolling_x_newsroom_assignment.v1",
        "status": "SUCCESS",
        "decision": "SELECT_STORY",
        "ranked_clusters": [{"cluster_id": "c1", "rank": 1, "headline_ids": ["h1"]}],
    }
    monkeypatch.setattr(
        "live_contentops.newsroom_assignment_scheduler_v1.load_rolling_x_headline_sidecars",
        lambda **kwargs: intake,
    )
    monkeypatch.setattr(
        "live_contentops.newsroom_assignment_scheduler_v1.assign_rolling_x_headlines_with_nine_router",
        lambda **kwargs: assignment,
    )
    monkeypatch.setattr(
        "live_contentops.newsroom_assignment_scheduler_v1.select_first_viable_rolling_x_cluster",
        lambda **kwargs: {"status": "NO_PUBLICATION", "reason_code": "ALL_RANKED_CLUSTERS_EVIDENCE_BLOCKED"},
    )
    result = implementation._run_rolling_x_newsroom_cycle(
        run_id="proof",
        output_dir=tmp_path,
        cutoff_utc="2026-08-08T00:00:00Z",
        story_type_classifier=_story_routing,
        publication_enabled=False,
    )
    assert result["classification"] == "NO_PUBLICATION"
    assert result["publishing_adapter_called"] is False
    assert result["public_write_performed"] is False
    assert result["exact_next_blocker"] == "ALL_RANKED_CLUSTERS_EVIDENCE_BLOCKED"


def test_assignment_infrastructure_failure_is_blocked_not_editorial_no_publication(
    monkeypatch, tmp_path: Path
):
    monkeypatch.setattr(
        "live_contentops.newsroom_assignment_scheduler_v1.load_rolling_x_headline_sidecars",
        lambda **kwargs: {
            "schema_version": "capital_chronicle.rolling_x_headline_input.v1",
            "counts": {"accepted": 1},
        },
    )
    monkeypatch.setattr(
        "live_contentops.newsroom_assignment_scheduler_v1.assign_rolling_x_headlines_with_nine_router",
        lambda **kwargs: {
            "status": "BLOCKED",
            "decision": None,
            "reason_code": "ROLLING_X_LEAF_ASSIGNMENT_BLOCKED",
        },
    )

    result = implementation._run_rolling_x_newsroom_cycle(
        run_id="assignment-blocked",
        output_dir=tmp_path,
        cutoff_utc="2026-08-08T00:00:00Z",
        publication_enabled=False,
    )

    assert result["classification"] == "BLOCKED"
    assert result["ranked_viability"]["decision"] is None
    assert result["exact_next_blocker"] == "ROLLING_X_LEAF_ASSIGNMENT_BLOCKED"
    assert result["publishing_adapter_called"] is False
    assert result["public_write_performed"] is False


def test_resume_existing_logical_cycle_preserves_frozen_cutoff_and_input_binding(
    monkeypatch, tmp_path: Path
):
    evidence_path = tmp_path / "rolling_x_newsroom_cycle_evidence_v1.json"
    evidence_path.write_text(
        json.dumps({
            "classification": "NO_PUBLICATION",
            "run_id": "same-logical-cycle",
            "intake": {
                "cutoff_time_utc": "2026-08-08T00:00:00Z",
                "canonical_input_hash": "frozen-input-hash",
            },
            "public_write_performed": False,
        }),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "live_contentops.newsroom_assignment_scheduler_v1.load_rolling_x_headline_sidecars",
        lambda **kwargs: (_ for _ in ()).throw(
            AssertionError("resume must not reload or rebind sidecars")
        ),
    )

    result = implementation._run_rolling_x_newsroom_cycle(
        run_id="same-logical-cycle",
        output_dir=tmp_path,
        cutoff_utc="2026-08-09T00:00:00Z",
        publication_enabled=False,
    )

    assert result["intake"]["cutoff_time_utc"] == "2026-08-08T00:00:00Z"
    assert result["intake"]["canonical_input_hash"] == "frozen-input-hash"
    assert result["reentry_guard"] == "existing_cycle_evidence_detected_no_automatic_retry"


def test_invalid_semantic_decision_fails_closed_and_exhausts(monkeypatch):
    monkeypatch.setattr(
        "live_contentops.tier1_editorial_quality_v1.audit_tier1_article",
        lambda article, media_assets=(): {"classification": "PASS"},
    )
    result = implementation._run_bounded_rolling_x_editorial_cycle(
        article=_article(),
        media_assets=[],
        editorial_reviewer=lambda article: {"status": "SUCCESS", "decision": "PUBLISH"},
        article_reviser=lambda article, review, round_number: {
            **article,
            "substack_body_markdown": article["substack_body_markdown"] + f" Revision {round_number}.",
        },
    )
    assert result["status"] == "NO_PUBLICATION"
    assert result["revision_rounds_completed"] == 1
    assert all(
        row["llm_semantic_review"]["decision"] == "NEEDS_REVISION"
        for row in result["review_history"]
    )
    assert all(
        row["llm_semantic_review"]["publication_authority"] is False
        for row in result["review_history"]
    )


def test_dynamic_destination_readiness_uses_only_verified_statuses():
    result = implementation._rolling_x_destination_readiness(
        cdp_port=9223,
        doctor={"status": "READY_TO_ATTACH", "recommended_cdp_port": 9223},
        account_preflight={
            "substack": {"authenticated": True, "destination_identity": "Capital Chronicle"},
            "x": {"authenticated": True, "destination_identity": "@Capitalnicle"},
            "linkedin": {"authenticated": True, "destination_identity": "linkedin:jimcc"},
            "youtube": {"authenticated": True, "destination_identity": "@CapitalChronicleYouTube"},
        },
        capability_presence={
            "telegram": True,
            "discord": True,
            "facebook_page": True,
            "instagram_business": True,
            "threads": True,
        },
    )
    assert result["all_required_destinations_ready"] is False
    assert result["destinations"]["telegram"]["write_eligible"] is False
    assert result["destinations"]["discord"]["write_eligible"] is False

    blocked = implementation._rolling_x_destination_readiness(
        cdp_port=9223,
        doctor={"status": "READY_TO_ATTACH", "recommended_cdp_port": 9223},
        account_preflight={
            "substack": {"authenticated": True},
            "x": {"authenticated": True, "destination_identity": "@wrong"},
            "linkedin": {"authenticated": True, "destination_identity": "linkedin:jimcc"},
            "youtube": {"authenticated": True},
        },
        capability_presence={
            "telegram": True,
            "discord": True,
            "facebook_page": True,
            "instagram_business": True,
            "threads": True,
        },
    )
    assert blocked["all_required_destinations_ready"] is False
    assert blocked["destinations"]["x"]["status"] == "IDENTITY_MISMATCH"


def _release_inputs(tmp_path: Path):
    assets = []
    for index, asset_id in enumerate(("event_record", "timeline", "geography"), start=1):
        path = tmp_path / f"{asset_id}.png"
        path.write_bytes(f"image-{index}".encode())
        assets.append(
            {
                "asset_id": asset_id,
                "path": str(path),
                "sha256": implementation._sha256_file(path),
                "caption": f"Verified {asset_id} source visual.",
                "alt_text": f"Verified {asset_id} visual",
                "source_label": "Official Agency",
                "source_page_url": f"https://official.example/{asset_id}",
                "provenance_status": "VERIFIED",
            }
        )
    evidence_documents = [
        {"evidence_id": "ev-1", "source_url": "https://official.example/record"}
    ]
    viability = {
        "status": "SUCCESS",
        "selected_cluster_id": "c1",
        "selected_rank": 1,
        "selected_headline_ids": ["h1"],
        "selected_cluster": {"cluster_id": "c1", "rank": 1, "headline_ids": ["h1"]},
        "selected_evidence": {"evidence_documents": evidence_documents},
    }
    body = "\n\n".join(
        [
            (
                "Official event records released today establish the latest change, identify the "
                "responsible agency, and explain why the implementation sequence matters now. The "
                "record is the controlling source for this update, while later notices may refine "
                "the schedule or scope."
            ),
            "[[VISUAL:event_record]]",
            (
                "## What changed\nThe agency's published record identifies the affected entities, "
                "the action now in force, and the boundary of the announcement. It distinguishes "
                "confirmed implementation details from questions that remain open, giving readers "
                "a clear account without extending beyond the official evidence."
            ),
            "[[VISUAL:timeline]]",
            (
                "## Why it matters\nThe implementation sequence determines when the announced change "
                "can affect the named institutions and when compliance obligations begin. The "
                "timeline also separates the current decision from possible later steps that have "
                "not yet been confirmed by the agency."
            ),
            "[[VISUAL:geography]]",
            (
                "## Evidence and limits\nThis account relies on the agency record and its stated "
                "effective sequence. It does not infer market effects, unannounced policy choices, "
                "or the behavior of entities outside the document's scope. A corrected notice or "
                "conflicting official update would require the article to be revised."
            ),
            (
                "## What comes next\nReaders should watch the named agency's implementation notice, "
                "any formal clarification of scope, and the first dated compliance milestone. "
                "Those records would confirm whether the current sequence remains intact or whether "
                "the agency has changed the timing."
            ),
        ]
    )
    article = {
        **_article(body),
        "editorial_mode": "straight_news",
        "cluster_id": "c1",
        "headline_ids": ["h1"],
        "evidence_document_ids": ["ev-1"],
        "x_content_grants_factual_authority": False,
        "canonical_url": "https://capitalchronicle.substack.com/p/pending-publication",
        "social_lede": "The official event record establishes the latest verified update.",
        "social_mechanism_summary": "The implementation timeline explains why the event matters now.",
        "social_policy_summary": "The governing record defines the current scope and sequence.",
        "social_cross_asset_summary": "No unsupported market reaction is asserted.",
    }
    assignment = {"assignment_logical_hash": "assignment-hash"}
    media = {"assets": assets}
    editorial = {"status": "PASS", "article": article, "review_history": []}
    readiness = {
        "all_required_destinations_ready": True,
        "destinations": {
            platform: {"write_eligible": True, "status": "READY_AUTHENTICATED"}
            for platform in ("substack", "x", "linkedin", "youtube")
        } | {
            platform: {"write_eligible": True, "status": "READY_NON_BROWSER_BINDING"}
            for platform in ("telegram", "discord", "facebook_page", "instagram_business", "threads")
        },
    }
    return assignment, viability, article, media, editorial, readiness


def test_rolling_x_release_candidate_builds_and_verifies_canonical_lock(tmp_path: Path):
    assignment, viability, article, media, editorial, readiness = _release_inputs(tmp_path)
    result = implementation._prepare_rolling_x_release_candidate(
        run_id="rolling-release",
        output_dir=tmp_path,
        intake={"schema_version": "capital_chronicle.rolling_x_headline_input.v1"},
        assignment=assignment,
        viability=viability,
        article=article,
        media=media,
        editorial_cycle=editorial,
        destination_readiness=readiness,
    )
    assert result["classification"] == "PASS_TEXT_IMAGE_RELEASE_CANDIDATE_REHEARSAL"
    assert result["release_candidate_lock_verification"]["status"] == "PASS_RELEASE_CANDIDATE_LOCK"
    assert set(implementation._RELEASE_PREPARATION_ARTIFACTS).issubset(
        {path.name for path in tmp_path.iterdir()}
    )
    context = json.loads((tmp_path / "run_context_v1.json").read_text(encoding="utf-8"))
    assert context["rolling_x_live_path_used"] is True
    assert context["generic_live_path_used"] is False
    payloads = json.loads((tmp_path / "native_payloads_rehearsal_v1.json").read_text(encoding="utf-8"))
    assert payloads["x"]["quality_metrics"]["complete_article_visual_count"] == 3
    assert payloads["threads"]["quality_metrics"]["reply_count"] == 2


def test_enhanced_breaking_brief_uses_text_only_native_packages_without_article_media():
    article = {
        "title": "Kushner's Gaza Talks With Netanyahu End Without a Breakthrough",
        "subtitle": (
            "Newer pre-cutoff reporting closes the earlier scheduled-meeting state and "
            "reports that the Netanyahu talks produced no breakthrough."
        ),
        "social_hook": (
            "Jared Kushner's Gaza talks with Benjamin Netanyahu have occurred, with "
            "newer reporting describing no breakthrough."
        ),
        "effective_article_mode": "BREAKING_BRIEF",
        "minimum_trustworthy_evidence_packet": {
            "status": "PASS",
            "risk_tier": "ENHANCED",
        },
    }
    payloads = implementation.build_native_derivative_payloads(
        article=article,
        selection={},
        canonical_url="https://capitalchronicle.substack.com/p/pending-publication",
        media_asset_ids=(),
    )

    assert set(payloads) == {
        "telegram", "x", "linkedin", "discord", "facebook_page",
        "instagram_business", "threads", "youtube",
    }
    for platform in ("x", "threads"):
        package = payloads[platform]
        assert package["hard_truncation_used"] is False
        assert all(not row["media_asset_ids"] for row in package["posts"])
        assert max(package["quality_metrics"]["post_character_counts"]) <= package["platform_limit"]
    all_payload_text = str(payloads).casefold()
    assert "ahead of netanyahu talks" not in all_payload_text
    assert "scheduled to meet netanyahu" not in all_payload_text
    assert "planned netanyahu talks" not in all_payload_text


def test_release_candidate_defers_unready_derivative_to_exact_jit_verification(tmp_path: Path):
    assignment, viability, article, media, editorial, readiness = _release_inputs(tmp_path)
    readiness["all_required_destinations_ready"] = False
    readiness["destinations"]["x"] = {"write_eligible": False, "status": "BLOCKED"}
    result = implementation._prepare_rolling_x_release_candidate(
        run_id="rolling-blocked",
        output_dir=tmp_path,
        intake={"schema_version": "capital_chronicle.rolling_x_headline_input.v1"},
        assignment=assignment,
        viability=viability,
        article=article,
        media=media,
        editorial_cycle=editorial,
        destination_readiness=readiness,
    )
    assert result["classification"] == "PASS_TEXT_IMAGE_RELEASE_CANDIDATE_REHEARSAL"
    assert "destination_not_ready:x" not in result["blockers"]
    assert result["release_candidate_lock_verification"]["status"] == "PASS_RELEASE_CANDIDATE_LOCK"
    plan = implementation._build_rolling_x_publication_plan(
        run_id="rolling-blocked",
        output_dir=tmp_path,
        viability=viability,
        preparation=result,
        readiness=readiness,
    )
    assert plan["quality_probation_policy_id"] == "QUALITY_PROBATION_FOUR_WINDOW_V1"
    assert plan["full_v1_distribution_required"] is True
    assert len(plan["required_publication_destinations"]) == 9
    assert len(plan["required_derivative_destinations"]) == 8
    planned_x = next(row for row in plan["destinations"] if row["destination"] == "x")
    assert planned_x["readiness_state"] == "BLOCKED"
    assert planned_x["jit_verification_required"] is True
    assert not any(
        row["destination"] == "x" for row in plan["skipped_derivative_destinations"]
    )


def test_passive_substack_state_reaches_coordinator_jit_boundary(tmp_path: Path):
    assignment, viability, article, media, editorial, readiness = _release_inputs(tmp_path)
    readiness["destinations"]["substack"] = {
        "write_eligible": False,
        "status": "TRANSPORT_UNAVAILABLE",
    }
    result = implementation._prepare_rolling_x_release_candidate(
        run_id="rolling-substack-jit",
        output_dir=tmp_path,
        intake={"schema_version": "capital_chronicle.rolling_x_headline_input.v1"},
        assignment=assignment,
        viability=viability,
        article=article,
        media=media,
        editorial_cycle=editorial,
        destination_readiness=readiness,
    )
    assert result["classification"] == "PASS_TEXT_IMAGE_RELEASE_CANDIDATE_REHEARSAL"
    assert "destination_not_ready:substack" not in result["blockers"]
    assert "substack_jit_readiness_required" in result["distribution_warnings"]
    plan = implementation._build_rolling_x_publication_plan(
        run_id="rolling-substack-jit",
        output_dir=tmp_path,
        viability=viability,
        preparation=result,
        readiness=readiness,
    )
    planned = next(row for row in plan["destinations"] if row["destination"] == "substack")
    assert planned["jit_verification_required"] is True


def test_optional_seo_and_visual_absence_do_not_rescue_one_sentence_copy(tmp_path: Path):
    assignment, viability, article, _media, editorial, readiness = _release_inputs(tmp_path)
    for field in (
        "subtitle",
        "seo_title",
        "meta_description",
        "market_mechanism",
        "policy_context",
        "cross_asset_implications",
    ):
        article[field] = ""
    article["substack_body_markdown"] = (
        "The official agency confirmed the public event in its published record."
    )
    result = implementation._prepare_rolling_x_release_candidate(
        run_id="rolling-minimum-useful-article",
        output_dir=tmp_path,
        intake={"schema_version": "capital_chronicle.rolling_x_headline_input.v1"},
        assignment=assignment,
        viability=viability,
        article=article,
        media={"assets": []},
        editorial_cycle=editorial,
        destination_readiness=readiness,
    )

    assert result["classification"] == "BLOCKED_TEXT_IMAGE_RELEASE_CANDIDATE_REHEARSAL"
    assert "INSUFFICIENT_READER_VALUE" in result["blockers"]
    assert result["context"]["media"]["media_asset_count"] == 0
    assert all(
        not blocker.startswith("article_field_missing:") for blocker in result["blockers"]
    )


def test_passed_cycle_returns_plan_without_direct_backend_write(monkeypatch, tmp_path: Path):
    assignment, viability, article, media, editorial, readiness = _release_inputs(tmp_path)
    calls = []
    monkeypatch.setattr(
        "live_contentops.newsroom_assignment_scheduler_v1.load_rolling_x_headline_sidecars",
        lambda **kwargs: {"schema_version": "capital_chronicle.rolling_x_headline_input.v1"},
    )
    monkeypatch.setattr(
        "live_contentops.newsroom_assignment_scheduler_v1.assign_rolling_x_headlines_with_nine_router",
        lambda **kwargs: {"status": "SUCCESS", "assignment_logical_hash": "assignment-hash"},
    )
    monkeypatch.setattr(
        "live_contentops.newsroom_assignment_scheduler_v1.select_first_viable_rolling_x_cluster",
        lambda **kwargs: viability,
    )
    monkeypatch.setattr(implementation, "_rolling_x_destination_readiness", lambda **kwargs: readiness)
    monkeypatch.setattr(
        implementation,
        "_run_bounded_rolling_x_editorial_cycle",
        lambda **kwargs: editorial,
    )
    monkeypatch.setattr(
        implementation,
        "_run_eight_platform_substack_first_pipeline",
        lambda **kwargs: calls.append(kwargs) or {
            "classification": "PASS_SUBSTACK_FIRST_TEXT_IMAGE_DISTRIBUTION_V1",
            "results": {
                "substack": {
                    "status": "SUCCESS",
                    "public_url": "https://capitalchronicle.substack.com/p/official-event-update",
                    "provider_readback_verified": True,
                    "readback": {"status": "SUCCESS"},
                }
            },
        },
    )
    result = implementation._run_rolling_x_newsroom_cycle(
        run_id="rolling-dispatch",
        output_dir=tmp_path,
        cutoff_utc="2026-08-08T00:00:00Z",
        article_builder=lambda value: {
            "article": article, "media": media,
            "editorial_worker_receipt": _xhigh_receipt(
                article, value["editorial_worker_request"]
            ),
        },
        editorial_reviewer=lambda value: _semantic("PASS"),
        article_reviser=lambda value, review, round_number: value,
        destination_readiness_override=_all_ready(),
        publication_enabled=True,
    )
    assert len(calls) == 0
    assert result["classification"] == "PASS_PUBLICATION_PLAN_READY"
    assert result["public_write_performed"] is False
    assert result["daily_app_newsroom_direct_write"] is False
    route = result["editorial_worker_routing"]
    worker_request = route["worker_request"]
    editorial_packet = worker_request["bounded_governed_context"][
        "institutional_edge_editorial_packet"
    ]
    assert route["xhigh_worker_count_requested"] == 1
    assert worker_request["model"] == "gpt-5.6-sol"
    assert worker_request["reasoning_effort"] == "XHIGH"
    assert worker_request["governed_input_hash"] == route["governed_input_hash"]
    assert editorial_packet["editorial_packet_sha256"] == article[
        "institutional_edge_editorial_packet_sha256"
    ]
    assert result["article"]["institutional_edge_editorial_validation"][
        "classification"
    ] == "PASS"
    from live_contentops.tier1_editorial_quality_v1 import evaluate_reader_value

    assert evaluate_reader_value(
        result["article"], media_assets=media["assets"]
    )["classification"] == "PASS"
    assert result["critical_path_telemetry"]["mandatory_semantic_review_calls"] == 0
    plan = result["publication_lifecycle_plan"]
    assert len(plan["destinations"]) == 9
    seo_package_hash = plan["editorial_seo_package"][
        "editorial_seo_package_sha256"
    ]
    assert seo_package_hash
    assert all(
        row["editorial_seo_package_sha256"] == seo_package_hash
        for row in plan["destinations"]
    )
    assert (tmp_path / "editorial_seo_package_v1.json").is_file()
    assert result["unknown_write_detected"] is False


def test_router_outage_fallback_has_no_live_publication_authority(monkeypatch, tmp_path: Path):
    _assignment, viability, article, media, _editorial, readiness = _release_inputs(tmp_path)
    article.update(
        {
            "article_generation_method": "DETERMINISTIC_SUPPORTED_CLAIM_BRIEF",
            "article_generation_router_failure": {
                "terminal_disposition": "PROVIDER_EXHAUSTED"
            },
        }
    )
    monkeypatch.setattr(
        "live_contentops.newsroom_assignment_scheduler_v1.load_rolling_x_headline_sidecars",
        lambda **kwargs: {"schema_version": "capital_chronicle.rolling_x_headline_input.v1"},
    )
    monkeypatch.setattr(
        "live_contentops.newsroom_assignment_scheduler_v1.assign_rolling_x_headlines_with_nine_router",
        lambda **kwargs: {"status": "SUCCESS", "assignment_logical_hash": "assignment-hash"},
    )
    monkeypatch.setattr(
        "live_contentops.newsroom_assignment_scheduler_v1.select_first_viable_rolling_x_cluster",
        lambda **kwargs: viability,
    )
    monkeypatch.setattr(implementation, "_rolling_x_destination_readiness", lambda **kwargs: readiness)
    monkeypatch.setattr(
        implementation,
        "_run_bounded_rolling_x_editorial_cycle",
        lambda **kwargs: (_ for _ in ()).throw(
            AssertionError("outage fallback must stop before editorial/release planning")
        ),
    )

    result = implementation._run_rolling_x_newsroom_cycle(
        run_id="router-outage-no-publication",
        output_dir=tmp_path,
        cutoff_utc="2026-08-08T00:00:00Z",
        article_builder=lambda value: {
            "article": article, "media": media,
            "editorial_worker_receipt": _xhigh_receipt(
                article, value["editorial_worker_request"]
            ),
        },
        destination_readiness_override=_all_ready(),
        publication_enabled=True,
    )

    assert result["classification"] == "NO_PUBLICATION"
    assert result["exact_next_blocker"] == (
        "ARTICLE_GENERATION_ROUTER_FAILURE_NO_PUBLICATION_AUTHORITY"
    )
    assert result["article_generation_publication_eligible"] is False
    assert result["publishing_adapter_called"] is False
    assert result["public_write_performed"] is False


def test_assignment_router_exception_writes_fail_closed_cycle_evidence(
    monkeypatch, tmp_path: Path
):
    from live_contentops.nine_router_llm_seam_v2 import RoutedInvocationError

    monkeypatch.setattr(
        "live_contentops.newsroom_assignment_scheduler_v1.load_rolling_x_headline_sidecars",
        lambda **kwargs: {
            "schema_version": "capital_chronicle.rolling_x_headline_input.v1",
            "counts": {"accepted": 1},
        },
    )

    def fail_assignment(**_kwargs):
        raise RoutedInvocationError(
            {
                "role_task_id": "rolling_x_newsroom_assignment",
                "terminal_disposition": "LLM_TERMINAL_NON_RETRYABLE_FAILURE",
                "models_attempted_in_order": ["model-a"],
                "raw_output": "must-not-persist",
            }
        )

    monkeypatch.setattr(
        "live_contentops.newsroom_assignment_scheduler_v1.assign_rolling_x_headlines_with_nine_router",
        fail_assignment,
    )

    result = implementation._run_rolling_x_newsroom_cycle(
        run_id="assignment-router-failure",
        output_dir=tmp_path,
        cutoff_utc="2026-08-08T00:00:00Z",
        publication_enabled=False,
    )

    assert result["classification"] == "BLOCKED"
    assert result["exact_next_blocker"] == "ROLLING_X_GLOBAL_EDITOR_BLOCKED"
    assert result["publishing_adapter_called"] is False
    assert result["public_write_performed"] is False
    persisted = json.loads(
        (tmp_path / "rolling_x_newsroom_cycle_evidence_v1.json").read_text(
            encoding="utf-8"
        )
    )
    telemetry = persisted["assignment"]["telemetry"]
    assert telemetry["terminal_disposition"] == "LLM_TERMINAL_NON_RETRYABLE_FAILURE"
    assert telemetry["models_attempted_in_order"] == ["model-a"]
    assert "raw_output" not in telemetry
    assert "publication_lifecycle_plan" not in result


def test_native_xhigh_revision_need_writes_same_worker_contract_without_router_fallback(monkeypatch, tmp_path: Path):
    _assignment, viability, article, media, _editorial, readiness = _release_inputs(tmp_path)
    monkeypatch.setattr(
        "live_contentops.newsroom_assignment_scheduler_v1.load_rolling_x_headline_sidecars",
        lambda **kwargs: {"schema_version": "capital_chronicle.rolling_x_headline_input.v1"},
    )
    monkeypatch.setattr(
        "live_contentops.newsroom_assignment_scheduler_v1.assign_rolling_x_headlines_with_nine_router",
        lambda **kwargs: {"status": "SUCCESS", "assignment_logical_hash": "assignment-hash"},
    )
    monkeypatch.setattr(
        "live_contentops.newsroom_assignment_scheduler_v1.select_first_viable_rolling_x_cluster",
        lambda **kwargs: viability,
    )
    monkeypatch.setattr(implementation, "_rolling_x_destination_readiness", lambda **kwargs: readiness)

    revision_router_calls = []

    result = implementation._run_rolling_x_newsroom_cycle(
        run_id="native-xhigh-same-worker-revision",
        output_dir=tmp_path,
        cutoff_utc="2026-08-08T00:00:00Z",
        article_builder=lambda value: {
            "article": article, "media": media,
            "editorial_worker_receipt": _xhigh_receipt(
                article, value["editorial_worker_request"]
            ),
        },
        editorial_reviewer=lambda value: _semantic("NEEDS_REVISION"),
        article_reviser=lambda *args: revision_router_calls.append(args),
        destination_readiness_override=_all_ready(),
        publication_enabled=True,
    )

    assert result["classification"] == "NO_PUBLICATION"
    assert result["exact_next_blocker"] == "SAME_XHIGH_WORKER_REVISION_REQUIRED"
    assert result["editorial_cycle"]["publication_authority_granted"] is False
    assert revision_router_calls == []
    assert "publication_lifecycle_plan" not in result
    persisted = json.loads(
        (tmp_path / "rolling_x_newsroom_cycle_evidence_v1.json").read_text(encoding="utf-8")
    )
    assert persisted["exact_next_blocker"] == "SAME_XHIGH_WORKER_REVISION_REQUIRED"
    assert persisted["editorial_cycle"]["review_history"][0]["revision"]["status"] == (
        "SAME_XHIGH_WORKER_REVISION_REQUIRED"
    )


def test_old_backend_unknown_write_fixture_cannot_bypass_plan_coordinator(
    monkeypatch, tmp_path: Path
):
    assignment, viability, article, media, editorial, readiness = _release_inputs(tmp_path)
    monkeypatch.setattr(
        "live_contentops.newsroom_assignment_scheduler_v1.load_rolling_x_headline_sidecars",
        lambda **kwargs: {"schema_version": "capital_chronicle.rolling_x_headline_input.v1"},
    )
    monkeypatch.setattr(
        "live_contentops.newsroom_assignment_scheduler_v1.assign_rolling_x_headlines_with_nine_router",
        lambda **kwargs: {"status": "SUCCESS", "assignment_logical_hash": "assignment-hash"},
    )
    monkeypatch.setattr(
        "live_contentops.newsroom_assignment_scheduler_v1.select_first_viable_rolling_x_cluster",
        lambda **kwargs: viability,
    )
    monkeypatch.setattr(implementation, "_rolling_x_destination_readiness", lambda **kwargs: readiness)
    monkeypatch.setattr(
        implementation,
        "_run_bounded_rolling_x_editorial_cycle",
        lambda **kwargs: editorial,
    )
    monkeypatch.setattr(
        implementation,
        "_run_eight_platform_substack_first_pipeline",
        lambda **kwargs: {
            "classification": "FAILED_EIGHT_PLATFORM_FULL_CONTENTOPS_LIVE_RUN_V1",
            "results": {
                "substack": {"status": "SUCCESS", "provider_readback_verified": True},
                "x": {
                    "status": "FAILED_X_PERMALINK_READBACK",
                    "write_outcome_certainty": "unknown",
                    "automatic_retry_blocked": True,
                },
            },
        },
    )
    result = implementation._run_rolling_x_newsroom_cycle(
        run_id="rolling-unknown",
        output_dir=tmp_path,
        cutoff_utc="2026-08-08T00:00:00Z",
        article_builder=lambda value: {
            "article": article, "media": media,
            "editorial_worker_receipt": _xhigh_receipt(
                article, value["editorial_worker_request"]
            ),
        },
        editorial_reviewer=lambda value: _semantic("PASS"),
        article_reviser=lambda value, review, round_number: value,
        destination_readiness_override=_all_ready(),
        publication_enabled=True,
    )
    assert result["unknown_write_detected"] is False
    assert result["public_write_performed"] is False
    assert result["daily_app_newsroom_direct_write"] is False
    assert result["classification"] == "PASS_PUBLICATION_PLAN_READY"


def test_default_cycle_uses_real_targeted_evidence_adapter(monkeypatch, tmp_path: Path):
    intake = {
        "schema_version": "capital_chronicle.rolling_x_headline_input.v1",
        "counts": {"accepted": 1},
    }
    assignment = {
        "schema_version": "capital_chronicle.rolling_x_newsroom_assignment.v1",
        "status": "SUCCESS",
        "decision": "SELECT_STORY",
        "ranked_clusters": [
            {
                "cluster_id": "c1",
                "rank": 1,
                "headline_ids": ["h1"],
                "market_sensitive": True,
                "article_mode": "breaking",
            }
        ],
    }
    seen = []

    class FakeAdapter:
        def __init__(self, **kwargs):
            seen.append(("init", kwargs))

        def __call__(self, request):
            seen.append(("call", request))
            return {
                "status": "BLOCKED",
                "cluster_id": request["cluster_id"],
                "headline_ids": request["headline_ids"],
                "provided_evidence_capabilities": [],
                "evidence_documents": [],
                "capital_chronicle_authority_verified": False,
                "numeric_evidence_required": True,
                "blockers": ["exact_governed_story_evidence_missing"],
                "publication_authority": False,
            }

    monkeypatch.setattr(
        "live_contentops.newsroom_assignment_scheduler_v1.load_rolling_x_headline_sidecars",
        lambda **kwargs: intake,
    )
    monkeypatch.setattr(
        "live_contentops.newsroom_assignment_scheduler_v1.assign_rolling_x_headlines_with_nine_router",
        lambda **kwargs: assignment,
    )
    monkeypatch.setattr(
        "live_contentops.rolling_x_targeted_evidence_adapter_v1.RollingXTargetedEvidenceAdapter",
        FakeAdapter,
    )

    result = implementation._run_rolling_x_newsroom_cycle(
        run_id="default-adapter",
        output_dir=tmp_path,
        cutoff_utc="2026-08-08T00:00:00Z",
        capital_chronicle_root=Path("read-only-cc-root"),
        story_type_classifier=_story_routing,
        publication_enabled=False,
    )

    assert [kind for kind, _ in seen] == ["init", "call"]
    assert seen[0][1]["capital_chronicle_root"] == Path("read-only-cc-root")
    assert result["classification"] == "NO_PUBLICATION"
    assert result["ranked_viability"]["rank_attempts"][0]["blockers"]


def test_canonical_cycle_classifies_accepted_shortlist_once_without_external_mapping(
    monkeypatch, tmp_path: Path
):
    intake = {
        "schema_version": "capital_chronicle.rolling_x_headline_input.v1",
        "counts": {"accepted": 2},
        "headlines": [],
    }
    clusters = [
        {"cluster_id": "c1", "rank": 1, "headline_ids": ["h1"], "article_mode": "breaking"},
        {"cluster_id": "c2", "rank": 2, "headline_ids": ["h2"], "article_mode": "breaking"},
    ]
    assignment = {
        "schema_version": "capital_chronicle.rolling_x_newsroom_assignment.v1",
        "status": "SUCCESS",
        "decision": "SELECT_STORY",
        "ranked_clusters": clusters,
    }
    classifier_calls = []
    viability_calls = []
    monkeypatch.setattr(
        "live_contentops.newsroom_assignment_scheduler_v1.assign_rolling_x_headlines_with_nine_router",
        lambda **kwargs: assignment,
    )
    monkeypatch.setattr(
        "live_contentops.newsroom_assignment_scheduler_v1.select_first_viable_rolling_x_cluster",
        lambda **kwargs: viability_calls.append(kwargs) or {
            "status": "NO_PUBLICATION",
            "reason_code": "ALL_RANKED_CLUSTERS_EVIDENCE_BLOCKED",
        },
    )

    result = implementation._run_rolling_x_newsroom_cycle(
        run_id="automatic-story-routing",
        output_dir=tmp_path,
        cutoff_utc="2026-08-08T00:00:00Z",
        rolling_input=intake,
        story_type_classifier=lambda **kwargs: classifier_calls.append(kwargs)
        or _story_routing(kwargs["clusters"]),
        evidence_acquirer=lambda request: (_ for _ in ()).throw(
            AssertionError("patched viability owns this focused seam")
        ),
        publication_enabled=False,
    )

    assert result["classification"] == "NO_PUBLICATION"
    assert len(classifier_calls) == 1
    assert [row["cluster_id"] for row in classifier_calls[0]["clusters"]] == ["c1", "c2"]
    assert viability_calls[0]["story_type_by_cluster"] == {
        "c1": "regulatory_fiscal_event",
        "c2": "regulatory_fiscal_event",
    }
    assert result["story_routing"]["semantic_routing_grants_authority"] is False
    assert (tmp_path / "rolling_x_story_routing_v1.json").is_file()


def test_canonical_cycle_fails_closed_on_unknown_or_duplicate_classifier_ids(
    monkeypatch, tmp_path: Path
):
    assignment = {
        "schema_version": "capital_chronicle.rolling_x_newsroom_assignment.v1",
        "status": "SUCCESS",
        "decision": "SELECT_STORY",
        "ranked_clusters": [
            {"cluster_id": "c1", "rank": 1, "headline_ids": ["h1"], "article_mode": "breaking"},
            {"cluster_id": "c2", "rank": 2, "headline_ids": ["h2"], "article_mode": "breaking"},
        ],
    }
    monkeypatch.setattr(
        "live_contentops.newsroom_assignment_scheduler_v1.assign_rolling_x_headlines_with_nine_router",
        lambda **kwargs: assignment,
    )
    for label, stories, mapping in (
        (
            "unknown",
            [
                {"cluster_id": "c1", "story_type": "regulatory_fiscal_event"},
                {"cluster_id": "unknown", "story_type": "regulatory_fiscal_event"},
            ],
            {"c1": "regulatory_fiscal_event", "unknown": "regulatory_fiscal_event"},
        ),
        (
            "duplicate",
            [
                {"cluster_id": "c1", "story_type": "regulatory_fiscal_event"},
                {"cluster_id": "c1", "story_type": "regulatory_fiscal_event"},
            ],
            {"c1": "regulatory_fiscal_event", "c2": "regulatory_fiscal_event"},
        ),
    ):
        output = tmp_path / label
        result = implementation._run_rolling_x_newsroom_cycle(
            run_id=f"classifier-{label}",
            output_dir=output,
            cutoff_utc="2026-08-08T00:00:00Z",
            rolling_input={"schema_version": "capital_chronicle.rolling_x_headline_input.v1", "headlines": []},
            story_type_classifier=lambda **_kwargs: {
                "stories": stories,
                "story_type_by_cluster": mapping,
                "semantic_routing_grants_authority": False,
            },
            evidence_acquirer=lambda request: (_ for _ in ()).throw(
                AssertionError("invalid classifier output must stop before evidence")
            ),
            publication_enabled=False,
        )
        assert result["classification"] == "BLOCKED"
        assert result["exact_next_blocker"] == "STORY_TYPE_CLASSIFICATION_BLOCKED"
        assert result["ranked_viability"]["rank_attempts"] == []


def test_canonical_cycle_forwards_frozen_input_and_exact_checkpoints(
    monkeypatch, tmp_path: Path
):
    intake = {
        "schema_version": "capital_chronicle.rolling_x_headline_input.v1",
        "canonical_input_hash": "frozen-input-hash",
        "cutoff_time_utc": "2026-08-08T09:18:54Z",
        "counts": {"accepted": 1},
    }
    leaf_checkpoints = {"leaf-1": {"checkpoint": "exact"}}
    global_checkpoint = {"checkpoint": "exact-global"}
    calls = []
    monkeypatch.setattr(
        "live_contentops.newsroom_assignment_scheduler_v1.load_rolling_x_headline_sidecars",
        lambda **kwargs: (_ for _ in ()).throw(
            AssertionError("frozen resume must not reload X sidecars")
        ),
    )

    def assign(**kwargs):
        calls.append(kwargs)
        return {
            "schema_version": "capital_chronicle.rolling_x_newsroom_assignment.v1",
            "status": "SUCCESS",
            "decision": "NO_PUBLICATION",
            "ranked_clusters": [],
        }

    monkeypatch.setattr(
        "live_contentops.newsroom_assignment_scheduler_v1.assign_rolling_x_headlines_with_nine_router",
        assign,
    )

    result = implementation._run_rolling_x_newsroom_cycle(
        run_id="frozen-resume",
        output_dir=tmp_path,
        cutoff_utc="2026-08-08T09:18:54Z",
        rolling_input=intake,
        leaf_checkpoints=leaf_checkpoints,
        global_checkpoint=global_checkpoint,
        assignment_provider_call=lambda *_args: (_ for _ in ()).throw(
            AssertionError("assignment provider call forbidden")
        ),
        publication_enabled=False,
    )

    assert len(calls) == 1
    assert calls[0]["rolling_input"] == intake
    assert calls[0]["leaf_checkpoints"] is leaf_checkpoints
    assert calls[0]["global_checkpoint"] is global_checkpoint
    assert result["intake"]["canonical_input_hash"] == "frozen-input-hash"
    assert result["classification"] == "NO_PUBLICATION"


def test_publication_window_clusters_only_prepared_frontier_before_evidence_walk(
    monkeypatch, tmp_path: Path
):
    from live_contentops.newsroom_assignment_scheduler_v1 import (
        _logical_hash,
        _rolling_x_canonical_hash_material,
        build_prepared_rolling_x_candidate_state,
    )

    recorded = json.loads(
        Path(
            "docs/automation/ROLLING_X_NEWSROOM_LIVE_V1/real_cycle/rolling_x_intake_v1.json"
        ).read_text(encoding="utf-8")
    )
    rolling_input = {
        **{key: value for key, value in recorded.items() if key != "headlines"},
        "headlines": [dict(row) for row in recorded["headlines"][:8]],
    }
    rolling_input["unique_headline_ids"] = [
        row["headline_id"] for row in rolling_input["headlines"]
    ]
    rolling_input["counts"] = {**rolling_input["counts"], "accepted": 8}
    for row in rolling_input["headlines"]:
        row["source_timestamp_utc"] = "2026-08-08T08:00:00Z"
    rolling_input["canonical_input_hash"] = _logical_hash(
        _rolling_x_canonical_hash_material(rolling_input)
    )
    prepared = build_prepared_rolling_x_candidate_state(
        rolling_input=rolling_input,
        prepared_at_utc="2026-08-08T09:18:54Z",
    )
    provider_calls = []

    def prepared_frontier_provider(prompt, model, timeout):
        provider_calls.append({"prompt": prompt, "model": model, "timeout": timeout})
        if "leaf_input:\n" in prompt:
            payload = json.loads(prompt.split("leaf_input:\n", 1)[1])
            ids = [row["headline_id"] for row in payload["headlines"]]
            groups = [
                (ids[:3], "duplicate"),
                (ids[3:5], "material_update"),
                *[([headline_id], "distinct") for headline_id in ids[5:]],
            ]
            clusters = []
            for index, (member_ids, relationship) in enumerate(groups, start=1):
                clusters.append({
                    "member_headline_ids": member_ids,
                    "event_topic_summary": f"Prepared distinct story {index}",
                    "canonical_representative_headline_id": member_ids[-1],
                    "entities": [f"Entity {index}"],
                    "topics": ["prepared frontier"],
                    "duplicate_update_chain": {
                        "relationship": relationship,
                        "ordered_headline_ids": member_ids,
                    },
                    "candidate_relevance_signals": {
                        "audience_relevance": 70,
                        "evidence_prospects": 70,
                        "seo_potential": 60,
                        "qualified_engagement_potential": 65,
                        "saturation_risk": 20,
                    },
                })
            output = {"clusters": clusters}
        else:
            payload = json.loads(prompt.split("global_editor_input:\n", 1)[1])
            rows = []
            for rank, summary in enumerate(payload["leaf_cluster_summaries"], start=1):
                rows.append({
                    "rank": rank,
                    "leaf_cluster_ids": [summary["id"]],
                    "cross_partition_relationship": summary["relationship"],
                    "canonical_leaf_cluster_id": summary["id"],
                    "story_mode": "reporting",
                    "article_mode": "STANDARD_NEWS_ANALYSIS",
                    "market_sensitive": False,
                    "why_now": f"Prepared story {rank} is current and distinct.",
                    "selection_case": "The bounded evidence path warrants evaluation.",
                    "seo_intent": "Explain the current distinct story.",
                    "visual_strategy": "Use a source-backed title card.",
                    "needed_evidence": ["Verify the core proposition."],
                })
            output = {
                "decision": "SELECT_STORY",
                "selection_rationale": "The prepared frontier contains distinct candidates.",
                "selected_shortlist_rank": 1,
                "ranked_shortlist": rows,
            }
        return ProviderResult(
            text=json.dumps(output),
            resolved_model=model.split("/", 1)[-1].split("(", 1)[0],
            usage={"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
            cost={"total_cost": 0.001},
        )

    result = implementation._run_rolling_x_newsroom_cycle(
        run_id="prepared-window",
        output_dir=tmp_path,
        cutoff_utc="2026-08-08T09:48:54Z",
        prepared_candidate_state=prepared,
        assignment_provider_call=prepared_frontier_provider,
        evidence_acquirer=lambda _request: {
            "status": "BLOCKED",
            "blockers": ["CONTROLLED_NO_EVIDENCE"],
            "provided_evidence_capabilities": [],
        },
        publication_enabled=False,
        published_corpus=[],
        cc_catalog={"stores": [], "root_exists": False},
    )

    telemetry = result["critical_path_telemetry"]
    assert telemetry["prepared_candidate_state_reused"] is True
    assert telemetry["full_universe_semantic_assignment_on_critical_path"] is False
    assert telemetry["bounded_prepared_frontier_semantic_assignment"] is True
    assert telemetry["assignment_semantic_calls"] == 2
    assert telemetry["story_type_semantic_calls"] == 0
    assert result["assignment"]["prepared_candidate_state_reused"] is True
    assert len(provider_calls) == 2
    assert result["candidate_walk"]["attempted_candidate_count"] == 5
    frontier = result["prepared_story_frontier"]
    assert frontier["prepared_headline_identity_count"] == 8
    assert frontier["distinct_story_opportunity_count"] == 5
    assert frontier["candidate_slots_saved_by_semantic_clustering"] == 3
    assert frontier["relationship_counts"] == {
        "duplicate": 1, "material_update": 1, "distinct": 3,
    }
    assert frontier["exact_headline_identity_coverage"] is True
    assert set(frontier["leaf_covered_headline_ids"]) == set(
        rolling_input["unique_headline_ids"]
    )
    assert any(
        row["relationship"] == "material_update"
        and row["headline_identity_count"] == 2
        for row in frontier["duplicate_update_chain_collapse_matrix"]
    )


def test_prepared_frontier_semantic_failure_holds_before_evidence_fallback(
    monkeypatch, tmp_path: Path
):
    from live_contentops.newsroom_assignment_scheduler_v1 import (
        _logical_hash,
        _rolling_x_canonical_hash_material,
        build_prepared_rolling_x_candidate_state,
    )

    recorded = json.loads(Path(
        "docs/automation/ROLLING_X_NEWSROOM_LIVE_V1/real_cycle/rolling_x_intake_v1.json"
    ).read_text(encoding="utf-8"))
    rolling_input = {
        **{key: value for key, value in recorded.items() if key != "headlines"},
        "headlines": [dict(row) for row in recorded["headlines"][:4]],
    }
    rolling_input["unique_headline_ids"] = [
        row["headline_id"] for row in rolling_input["headlines"]
    ]
    rolling_input["counts"] = {**rolling_input["counts"], "accepted": 4}
    for row in rolling_input["headlines"]:
        row["source_timestamp_utc"] = "2026-08-08T08:00:00Z"
    rolling_input["canonical_input_hash"] = _logical_hash(
        _rolling_x_canonical_hash_material(rolling_input)
    )
    prepared = build_prepared_rolling_x_candidate_state(
        rolling_input=rolling_input,
        prepared_at_utc="2026-08-08T09:18:54Z",
    )
    evidence_calls = []
    blocked_assignment = {
        "schema_version": "capital_chronicle.rolling_x_newsroom_assignment.v1",
        "status": "BLOCKED",
        "decision": None,
        "reason_code": "ROLLING_X_LEAF_ASSIGNMENT_BLOCKED",
        "leaf_clusters": [], "ranked_clusters": [], "router_calls": [],
        "telemetry": {"logical_router_calls": 1},
        "router_output_grants_publication_authority": False,
    }
    monkeypatch.setattr(
        "live_contentops.newsroom_assignment_scheduler_v1.assign_rolling_x_headlines_with_nine_router",
        lambda **_kwargs: dict(blocked_assignment),
    )

    result = implementation._run_rolling_x_newsroom_cycle(
        run_id="prepared-window-semantic-blocked",
        output_dir=tmp_path,
        cutoff_utc="2026-08-08T09:48:54Z",
        prepared_candidate_state=prepared,
        evidence_acquirer=lambda request: evidence_calls.append(request),
        publication_enabled=False,
        published_corpus=[],
        cc_catalog={"stores": [], "root_exists": False},
    )

    assert result["assignment"]["status"] == "BLOCKED"
    assert result["assignment"].get("assignment_method") != (
        "DETERMINISTIC_EVIDENCE_REACHABLE_FALLBACK"
    )
    assert result["prepared_story_frontier"]["status"] == "BLOCKED"
    assert result["candidate_walk"]["attempted_candidate_count"] == 0
    assert evidence_calls == []
    assert result["public_write_performed"] is False
    assert result["unknown_write_detected"] is False
