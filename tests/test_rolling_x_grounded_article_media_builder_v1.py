from __future__ import annotations

import json
from pathlib import Path

import pytest

from live_contentops import _eight_platform_substack_first_pipeline_impl_v1 as implementation
from live_contentops import rolling_x_grounded_article_media_builder_v1 as builder
from live_contentops.rolling_x_grounded_article_media_builder_v1 import (
    GroundedArticleBuilderError,
    build_rolling_x_grounded_article_and_media,
    build_source_backed_media_assets,
    extract_governed_story_context,
    validate_generated_article,
    _untraceable_numeric_claims,
    _authority_blockers,
    _evidence_bound_entities,
    _underlying_source_rights,
    _document_host,
    UNDERLYING_RIGHTS_PUBLIC_DOMAIN,
    UNDERLYING_RIGHTS_UNRESOLVED,
    OWN_RENDER_RIGHTS_STATE,
)


FR_URL = "https://www.federalregister.gov/documents/2026/08/08/2026-16100/treasury-stress-rule"


def _official_document(
    *,
    document_id="official-primary-abc123",
    source_url=FR_URL,
    published="2026-08-08T09:00:00Z",
    family="official_regulatory_fiscal",
    content=None,
):
    return {
        "document_id": document_id,
        "title": "Treasury Stress Testing Rule",
        "publisher": "www.federalregister.gov",
        "source_identity": "www.federalregister.gov",
        "source_authority_class": "official_public_primary_source",
        "source_adapter_family": family,
        "source_url": source_url,
        "requested_source_url": source_url,
        "published_at_utc": published,
        "event_time_utc": published,
        "known_at_utc": "2026-08-08T12:00:00Z",
        "content_sha256": "d" * 64,
        "raw_sha256": "d" * 64,
        "canonical_content_text": content
        or (
            "The Treasury published a final stress testing rule on 2026-08-08. "
            "The rule takes effect after a compliance date and applies to affected entities."
        ),
        "public_claim_allowed": True,
        "cluster_id": "c1",
        "headline_ids": ["h1"],
        "request_logical_hash": "a" * 64,
        "permission_state": "PUBLIC_CLAIM_ALLOWED",
        "freshness_state": "FRESH_CURRENT_OPERATOR_READINESS",
    }


def _evidence(documents, *, status="PASS", authority_verified=False):
    return {
        "status": status,
        "cluster_id": "c1",
        "headline_ids": ["h1"],
        "provided_evidence_capabilities": [
            "official_document",
            "implementation_timeline",
            "affected_entities",
        ],
        "evidence_documents": list(documents),
        "capital_chronicle_authority_verified": authority_verified,
        "numeric_evidence_required": False,
        "blockers": [],
        "publication_authority": False,
        "evidence_acquisition_provenance": {},
    }


def _request(story_type="regulatory_fiscal_event", article_mode="straight_news", cc_required=False):
    return {
        "schema_version": "capital_chronicle.rolling_x_story_evidence_request.v1",
        "cluster_id": "c1",
        "rank": 1,
        "headline_ids": ["h1"],
        "story_type": story_type,
        "article_mode": article_mode,
        "required_evidence_capabilities": [
            "official_document",
            "implementation_timeline",
            "affected_entities",
        ],
        "source_adapter_families": ["official_regulatory_fiscal"],
        "market_sensitive": False,
        "market_snapshot_required": False,
        "capital_chronicle_numeric_or_analytical_authority_required": cc_required,
        "request_logical_hash": "a" * 64,
    }


def _viability(
    *,
    story_type="regulatory_fiscal_event",
    article_mode="straight_news",
    evidence=None,
    cc_required=False,
    capability_authority_required=False,
):
    evidence = evidence or _evidence([_official_document()])
    cluster = {
        "cluster_id": "c1",
        "rank": 1,
        "headline_ids": ["h1"],
        "story_mode": "reporting",
        "article_mode": article_mode,
        "market_sensitive": False,
        "why_now": "A final official rule was just published.",
        "selection_case": "Timely official rule with a clear compliance timeline.",
        "seo_intent": "Treasury stress rule compliance",
        "leaf_summaries": ["Treasury published a final stress testing rule."],
        "entities_topics": ["Treasury", "Stress Testing"],
    }
    return {
        "schema_version": "capital_chronicle.rolling_x_ranked_evidence_viability.v1",
        "status": "SUCCESS",
        "decision": "SELECT_STORY",
        "reason_code": "FIRST_VIABLE_RANKED_CLUSTER_SELECTED",
        "selected_cluster_id": "c1",
        "selected_rank": 1,
        "selected_headline_ids": ["h1"],
        "selected_cluster": cluster,
        "selected_evidence": evidence,
        "rank_attempts": [
            {
                "rank": 1,
                "cluster_id": "c1",
                "headline_ids": ["h1"],
                "request": _request(
                    story_type=story_type, article_mode=article_mode, cc_required=cc_required
                ),
                "capability_resolution": {
                    "status": "PASS",
                    "story_type": story_type,
                    "article_mode": article_mode,
                    "capital_chronicle_authority_required": capability_authority_required,
                    "required_evidence_capabilities": [
                        "official_document",
                        "implementation_timeline",
                        "affected_entities",
                    ],
                    "source_adapter_families": ["official_regulatory_fiscal"],
                },
                "evidence_receipt": evidence,
                "status": "VIABLE",
                "blockers": [],
            }
        ],
        "evidence_acquired_after_ranking": True,
        "x_content_grants_evidence_authority": False,
        "publication_authority_granted": False,
    }


def _passing_body(source_url, asset_ids):
    markers = "\n\n".join(f"[[VISUAL:{asset_id}]]" for asset_id in asset_ids)
    return (
        "The Treasury published a final stress testing rule on 2026-08-08, establishing a new "
        "compliance timeline for affected entities. What matters is that the official rule sets an "
        "explicit effective date and names the entities subject to it, as recorded by the Federal "
        "Register in the policy transmission to banks.\n\n"
        f"{markers}\n\n"
        "## What The Official Rule Establishes\n\n"
        f"The rule text, as published by the [Federal Register]({source_url}), defines the scope and "
        "the compliance sequence. The governing document is the authoritative record.\n\n"
        "## The Compliance Mechanism\n\n"
        "Implementation proceeds through an official compliance date documented in the rule. The "
        "mechanism is administrative and does not depend on market conditions. The timeline is "
        "recorded in the official register and tied to affected entities.\n\n"
        "## What Comes Next\n\n"
        "The affected entities must meet the documented requirements by the stated effective date.\n\n"
        "## What Would Confirm Or Challenge This\n\n"
        "Confirmation would require the official effective date to hold as documented, which would "
        "confirm the compliance schedule. The account would be challenged by a superseding Federal "
        "Register notice that delays the effective date. The Federal Register notice and the "
        "effective date are the next named catalysts. Sources: "
        f"[rule]({source_url}), [register]({source_url}), [timeline]({source_url}).\n\n"
        "This article is for informational purposes only and is not financial advice."
    )


def _make_generator(source_url, asset_ids):
    body = _passing_body(source_url, asset_ids)

    def generator(prompt):
        return {
            "title": "Treasury Publishes Final Stress Testing Rule With Compliance Timeline",
            "subtitle": "The official rule sets an explicit effective date and names affected entities.",
            "seo_title": "Treasury Stress Testing Rule Compliance Timeline Explained",
            "meta_description": (
                "The Treasury published a final stress testing rule with an official compliance "
                "timeline and affected entities, as recorded by the Federal Register."
            ),
            "market_mechanism": "The rule sets an administrative compliance sequence recorded in the register.",
            "policy_context": "The governing document defines scope and the effective date.",
            "cross_asset_implications": "No market reaction is asserted without separate evidence.",
            "social_lede": "Treasury published a final stress testing rule.",
            "social_mechanism_summary": "The rule sets an administrative compliance sequence.",
            "social_policy_summary": "The document defines scope and the effective date.",
            "social_cross_asset_summary": "No market reaction is asserted here.",
            "substack_body_markdown": body,
        }

    return generator


def _regulatory_asset_ids():
    return [
        "official_source_document_card",
        "decision_fact_card",
        "decision_timeline_card",
    ]


# --- extraction & authority -------------------------------------------------------


def test_extract_rejects_non_selected_viability():
    viability = _viability()
    viability["status"] = "NO_PUBLICATION"
    viability["decision"] = "NO_PUBLICATION"
    with pytest.raises(GroundedArticleBuilderError):
        extract_governed_story_context(viability)


def test_authority_blockers_when_exact_contract_requires_capital_chronicle():
    context = {
        "article_mode": "analysis",
        "capital_chronicle_authority_required": True,
        "capital_chronicle_authority_verified": False,
    }
    assert _authority_blockers(context) == [
        "analytical_mode_requires_capital_chronicle_authority"
    ]


def test_authority_ok_straight_news_without_capital_chronicle():
    context = {"article_mode": "straight_news", "capital_chronicle_authority_verified": False}
    assert _authority_blockers(context) == []


def test_authority_ok_analytical_with_capital_chronicle_verified():
    context = {
        "article_mode": "deep_analysis",
        "capital_chronicle_authority_required": True,
        "capital_chronicle_authority_verified": True,
    }
    assert _authority_blockers(context) == []


# --- numeric traceability ---------------------------------------------------------


def test_untraceable_quantitative_claim_detected():
    body = "The index rose 12.5% and revenue hit $3.2 billion on the announcement."
    evidence = "No numbers here at all."
    assert _untraceable_numeric_claims(body, evidence)


def test_traceable_quantitative_claim_passes():
    body = "The index rose 12.5% as recorded."
    evidence = "The index rose 12.5 percent in the official release."
    assert _untraceable_numeric_claims(body, evidence) == []


# --- media primitives -------------------------------------------------------------


def test_media_assets_three_distinct_for_regulatory(tmp_path):
    context = extract_governed_story_context(
        _viability(story_type="regulatory_fiscal_event", article_mode="straight_news")
    )
    assets = build_source_backed_media_assets(context, output_dir=tmp_path)
    assert len(assets) == 3
    ids = [row["asset_id"] for row in assets]
    assert ids == _regulatory_asset_ids()
    dimensions = {row["evidence_dimension"] for row in assets}
    assert len(dimensions) >= 2
    for asset in assets:
        assert Path(asset["path"]).is_file()
        assert asset["sha256"]
        assert asset["provenance_status"] == "SOURCE_BACKED"
        assert asset["source_page_url"] == FR_URL
        assert asset["caption"] and asset["alt_text"]
    assert any(row.get("supports_headline") for row in assets)


def test_media_assets_use_excerpt_third_for_non_timeline_story(tmp_path):
    context = extract_governed_story_context(
        _viability(story_type="data_release", article_mode="straight_news")
    )
    assets = build_source_backed_media_assets(context, output_dir=tmp_path)
    ids = [row["asset_id"] for row in assets]
    assert ids[2] in {"document_excerpt_card", "decision_timeline_card"}
    assert len(set(ids)) == 3


# --- full controlled build (Phases 11 A/B/C + quality) ----------------------------


@pytest.mark.parametrize("story_type", [
    "regulatory_fiscal_event",
    "data_release",
    "company_sector_event",
])
def test_controlled_build_produces_grounded_article_and_media(tmp_path, story_type):
    viability = _viability(story_type=story_type, article_mode="straight_news")
    asset_ids = (
        _regulatory_asset_ids()
        if story_type == "regulatory_fiscal_event"
        else ["official_source_document_card", "decision_fact_card", "document_excerpt_card"]
    )
    result = build_rolling_x_grounded_article_and_media(
        viability,
        output_dir=tmp_path,
        article_generator=_make_generator(FR_URL, asset_ids),
    )
    article = result["article"]
    assets = result["media"]["assets"]

    assert article["title"]
    assert article["substack_body_markdown"]
    assert article["seo_title"]
    assert article["meta_description"]
    assert article["article_mode"] == "straight_news"
    assert article["cluster_id"] == "c1"
    assert article["headline_ids"] == ["h1"]
    assert article["x_content_grants_factual_authority"] is False
    assert article["evidence_document_ids"] == ["official-primary-abc123"]
    assert article["visual_asset_ids_expected"] == asset_ids
    assert sorted(article["source_trail"]) == [FR_URL]

    # every visual marker resolves to an actual asset
    assert article["substack_body_markdown"].count("[[VISUAL:") == 3
    for asset_id in asset_ids:
        assert f"[[VISUAL:{asset_id}]]" in article["substack_body_markdown"]

    assert len(assets) == 3
    for asset in assets:
        assert Path(asset["path"]).is_file()


def test_analytical_mode_blocks_without_capital_chronicle_authority(tmp_path):
    viability = _viability(
        story_type="data_release", article_mode="analysis", cc_required=True
    )
    with pytest.raises(GroundedArticleBuilderError, match="capital_chronicle"):
        build_rolling_x_grounded_article_and_media(
            viability,
            output_dir=tmp_path,
            article_generator=_make_generator(FR_URL, []),
        )


def test_evidence_substitution_attacks_fail_closed(tmp_path):
    # (a) X content cannot become evidence: body references an unbound X url.
    context = extract_governed_story_context(_viability())
    bad_body = "See the report at https://x.com/status/123 for the facts."
    blockers = validate_generated_article(
        {
            "title": "t",
            "subtitle": "s",
            "seo_title": "seo",
            "meta_description": "m",
            "market_mechanism": "mech",
            "policy_context": "pol",
            "cross_asset_implications": "cross",
            "substack_body_markdown": bad_body,
            "evidence_document_ids": ["official-primary-abc123"],
            "cluster_id": "c1",
            "headline_ids": ["h1"],
            "x_content_grants_factual_authority": False,
        },
        context=context,
        visual_asset_ids=[],
    )
    assert "article_references_unbound_source_url" in blockers

    # (b) invented numeric output fails validation.
    invented_body = "Revenue surged 47.2% and the market cap reached $9.9 billion. " + " ".join(
        f"[[VISUAL:{a}]]" for a in _regulatory_asset_ids()
    )
    blockers = validate_generated_article(
        {
            "title": "t",
            "subtitle": "s",
            "seo_title": "seo",
            "meta_description": "m",
            "market_mechanism": "mech",
            "policy_context": "pol",
            "cross_asset_implications": "cross",
            "substack_body_markdown": invented_body,
            "evidence_document_ids": ["official-primary-abc123"],
            "cluster_id": "c1",
            "headline_ids": ["h1"],
            "x_content_grants_factual_authority": False,
        },
        context=context,
        visual_asset_ids=_regulatory_asset_ids(),
    )
    assert "article_untraceable_numeric_claim" in blockers

    # (c) unknown evidence ids fail.
    blockers = validate_generated_article(
        {
            "title": "t",
            "subtitle": "s",
            "seo_title": "seo",
            "meta_description": "m",
            "market_mechanism": "mech",
            "policy_context": "pol",
            "cross_asset_implications": "cross",
            "substack_body_markdown": _passing_body(FR_URL, _regulatory_asset_ids()),
            "evidence_document_ids": ["not-a-real-evidence-id"],
            "cluster_id": "c1",
            "headline_ids": ["h1"],
            "x_content_grants_factual_authority": False,
        },
        context=context,
        visual_asset_ids=_regulatory_asset_ids(),
    )
    assert "article_evidence_document_binding_mismatch" in blockers

    # (d) unbound cluster/headline identity fails.
    blockers = validate_generated_article(
        {
            "title": "t",
            "subtitle": "s",
            "seo_title": "seo",
            "meta_description": "m",
            "market_mechanism": "mech",
            "policy_context": "pol",
            "cross_asset_implications": "cross",
            "substack_body_markdown": _passing_body(FR_URL, _regulatory_asset_ids()),
            "evidence_document_ids": ["official-primary-abc123"],
            "cluster_id": "someone-elses-cluster",
            "headline_ids": ["h1"],
            "x_content_grants_factual_authority": False,
        },
        context=context,
        visual_asset_ids=_regulatory_asset_ids(),
    )
    assert "article_cluster_binding_mismatch" in blockers

    # (e) x factual authority must be denied.
    blockers = validate_generated_article(
        {
            "title": "t",
            "subtitle": "s",
            "seo_title": "seo",
            "meta_description": "m",
            "market_mechanism": "mech",
            "policy_context": "pol",
            "cross_asset_implications": "cross",
            "substack_body_markdown": _passing_body(FR_URL, _regulatory_asset_ids()),
            "evidence_document_ids": ["official-primary-abc123"],
            "cluster_id": "c1",
            "headline_ids": ["h1"],
            "x_content_grants_factual_authority": True,
        },
        context=context,
        visual_asset_ids=_regulatory_asset_ids(),
    )
    assert "article_must_deny_x_factual_authority" in blockers


# --- controlled end-to-end smoke through the canonical cycle (default builder) ----


def _semantic(decision):
    return {
        "status": "SUCCESS",
        "decision": decision,
        "mode": "straight_news",
        "issues": [],
        "publication_authority": False,
    }


def test_default_builder_invoked_and_path_reaches_release_gate_with_zero_public_writes(
    monkeypatch, tmp_path
):
    viability = _viability(story_type="regulatory_fiscal_event", article_mode="straight_news")
    intake = {
        "schema_version": "capital_chronicle.rolling_x_headline_input.v1",
        "counts": {"accepted": 1},
    }
    assignment = {
        "schema_version": "capital_chronicle.rolling_x_newsroom_assignment.v1",
        "status": "SUCCESS",
        "decision": "SELECT_STORY",
        "assignment_logical_hash": "assignment-hash",
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
        lambda **kwargs: viability,
    )
    # Default article generator (deterministic fixture) used by the default builder.
    monkeypatch.setattr(
        builder,
        "_default_article_generator",
        _make_generator(FR_URL, _regulatory_asset_ids()),
    )
    # Deterministic audit passes so the editorial cycle proves semantic review.
    monkeypatch.setattr(
        "live_contentops.tier1_editorial_quality_v1.audit_tier1_article",
        lambda article, media_assets=(): {"classification": "PASS"},
    )
    monkeypatch.setattr(
        implementation,
        "_rolling_x_destination_readiness",
        lambda **kwargs: {
            "all_required_destinations_ready": False,
            "destinations": {"substack": {"write_eligible": False, "status": "BLOCKED"}},
        },
    )
    # Publisher must NOT be reached because readiness blocks the release candidate.
    monkeypatch.setattr(
        implementation,
        "_run_eight_platform_substack_first_pipeline",
        lambda **kwargs: (_ for _ in ()).throw(
            AssertionError("publisher must not be invoked when no destination is ready")
        ),
    )

    result = implementation._run_rolling_x_newsroom_cycle(
        run_id="controlled-smoke",
        output_dir=tmp_path,
        cutoff_utc="2026-08-08T00:00:00Z",
        article_builder=None,  # default canonical builder
        editorial_reviewer=lambda value: _semantic("PASS"),
        article_reviser=lambda value, review, round_number: value,
        publication_enabled=True,
    )

    # Default builder produced a grounded article + three source-backed media assets.
    assert result["article"] is not None
    assert result["article"]["cluster_id"] == "c1"
    assert len(result["media"]["assets"]) == 3
    # Editorial review ran and passed (semantic reviewer invoked).
    assert result["editorial_cycle"]["status"] == "PASS"
    # Release preparation ran and evaluated destination readiness -> blocked, no public write.
    assert "release_candidate_preparation" in result
    assert result["classification"] == "NO_PUBLICATION"
    assert result["publishing_adapter_called"] is False
    assert result["public_write_performed"] is False
    assert result["unknown_write_detected"] is False


def test_decision5_desk_label_replay_reaches_article_review_and_shadow_package(
    monkeypatch, tmp_path
):
    """Sanitized exact Decision 5 contract: desk label must not poison brief SEO metadata."""
    source_url = "https://news.google.com/rss/articles/decision-5-public-source"
    document = _official_document(
        document_id="public-secondary-decision-5",
        source_url=source_url,
        family="reputable_public_secondary",
        content=(
            "Public reporting says the U.S. fired on a ship that was breaking its blockade "
            "of Iran. No unsupported number or quotation is included."
        ),
    )
    document.update(
        {
            "title": "Exclusive | U.S. Fires on Ship Breaking Its Blockade of Iran",
            "publisher": "Public Source A",
            "source_identity": "public-source-a.example",
            "source_authority_class": "reputable_independent_public_secondary",
            "underlying_reuse_classification": "metadata_only_no_excerpt",
        }
    )
    evidence = _evidence([document])
    evidence["provided_evidence_capabilities"] = ["public_secondary_corroboration"]
    evidence["claim_evidence_contract"] = {
        "status": "PASS",
        "claim_contract_sha256": "c" * 64,
        "supported_claim_count": 1,
        "omitted_claim_count": 0,
        "supported_claims": [
            {
                "claim_id": "claim-decision-5",
                "claim_text": "U.S. Fires on Ship Breaking Its Blockade of Iran - WSJ",
                "evidence_document_ids": ["public-secondary-decision-5"],
            }
        ],
        "omitted_unsupported_claims": [],
    }
    viability = _viability(
        story_type="geopolitical_event", article_mode="straight_news", evidence=evidence
    )
    viability["selected_cluster"].update(
        {
            "article_mode": "breaking",
            "resolved_article_mode": "BREAKING_BRIEF",
            "requested_article_mode": "BREAKING_BRIEF",
            "effective_article_mode": "BREAKING_BRIEF",
        }
    )
    request = viability["rank_attempts"][0]["request"]
    request.update(
        {
            "article_mode": "straight_news",
            "requested_article_mode": "BREAKING_BRIEF",
            "resolved_article_mode": "BREAKING_BRIEF",
            "effective_article_mode": "BREAKING_BRIEF",
            "required_evidence_capabilities": ["public_secondary_corroboration"],
        }
    )
    viability["rank_attempts"][0]["capability_resolution"].update(
        {
            "article_mode": "straight_news",
            "required_evidence_capabilities": ["public_secondary_corroboration"],
        }
    )
    intake = {
        "schema_version": "capital_chronicle.rolling_x_headline_input.v1",
        "counts": {"accepted": 1},
    }
    assignment = {
        "schema_version": "capital_chronicle.rolling_x_newsroom_assignment.v1",
        "status": "SUCCESS",
        "decision": "SELECT_STORY",
        "assignment_logical_hash": "decision-5-assignment",
        "ranked_clusters": [viability["selected_cluster"]],
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
        lambda **kwargs: viability,
    )

    result = implementation._run_rolling_x_newsroom_cycle(
        run_id="decision-5-offline-replay",
        output_dir=tmp_path,
        cutoff_utc="2026-08-11T12:57:00Z",
        story_type_by_cluster={"c1": "geopolitical_event"},
        editorial_reviewer=implementation._default_rolling_x_editorial_reviewer,
        article_reviser=lambda *_args: (_ for _ in ()).throw(
            AssertionError("Decision 5 deterministic brief must pass without an LLM revision")
        ),
        publication_enabled=False,
    )

    assert result["article"]["article_generation_method"] == (
        "DETERMINISTIC_SUPPORTED_CLAIM_BRIEF"
    )
    assert result["article"]["seo_primary_keyword"] == "fires"
    assert result["editorial_cycle"]["status"] == "PASS"
    assert result["editorial_cycle"]["revision_rounds_completed"] == 0
    assert result["platform_package_generated"] is True
    assert result["shadow_package_ready"] is True
    assert result["public_write_performed"] is False
    assert result["unknown_write_detected"] is False


def test_builder_fail_closed_surfaces_as_no_publication_not_crash(monkeypatch, tmp_path):
    viability = _viability(story_type="regulatory_fiscal_event", article_mode="straight_news")
    intake = {
        "schema_version": "capital_chronicle.rolling_x_headline_input.v1",
        "counts": {"accepted": 1},
    }
    assignment = {
        "schema_version": "capital_chronicle.rolling_x_newsroom_assignment.v1",
        "status": "SUCCESS",
        "decision": "SELECT_STORY",
        "assignment_logical_hash": "assignment-hash",
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
        lambda **kwargs: viability,
    )

    def raising_builder(viability_arg):
        raise GroundedArticleBuilderError("article_untraceable_numeric_claim")

    result = implementation._run_rolling_x_newsroom_cycle(
        run_id="builder-fail-closed",
        output_dir=tmp_path,
        cutoff_utc="2026-08-08T00:00:00Z",
        article_builder=raising_builder,
        editorial_reviewer=lambda value: _semantic("PASS"),
        article_reviser=lambda value, review, round_number: value,
        publication_enabled=True,
    )
    assert result["classification"] == "NO_PUBLICATION"
    assert result["exact_next_blocker"] == "GROUNDED_ARTICLE_BUILDER_FAIL_CLOSED"
    assert result["grounded_article_builder_blockers"] == [
        "article_untraceable_numeric_claim"
    ]
    assert result["public_write_performed"] is False


# --- Phase 2: media factual provenance (framing/X cannot become evidence facts) ---


def test_framing_only_entities_cannot_become_evidence_bound_entities():
    # The evidence document carries NO entity fields. Editorial framing/X-derived
    # entities_topics must not be relabeled as accepted-evidence entities.
    doc = _official_document()
    assert "bound_entities" not in doc and "affected_entities" not in doc and "entities" not in doc
    assert _evidence_bound_entities(doc) == []


def test_evidence_bound_entities_are_used_when_the_evidence_itself_carries_them():
    doc = _official_document()
    doc["bound_entities"] = ["Treasury", "Office of Financial Research"]
    assert _evidence_bound_entities(doc) == ["Treasury", "Office of Financial Research"]


def test_fact_card_builds_without_framing_entities(tmp_path):
    viability = _viability(story_type="regulatory_fiscal_event", article_mode="straight_news")
    # Inject X/framing-derived entities_topics; the fact card must not consume them as facts.
    viability["selected_cluster"]["entities_topics"] = ["XOnlyEntity", "DiscoveryTopic"]
    context = extract_governed_story_context(viability)
    assets = build_source_backed_media_assets(context, output_dir=tmp_path)
    fact_card = next(row for row in assets if row["asset_id"] == "decision_fact_card")
    # The fact card remains a fact card and is source-backed; framing entities are not evidence.
    assert fact_card["modality"] == "fact_card"
    assert fact_card["provenance_status"] == "SOURCE_BACKED"
    assert _evidence_bound_entities(context["evidence_documents"][0]) == []


# --- Phase 3: media rights provenance (render ownership vs underlying rights) ---


def test_render_ownership_is_separate_from_underlying_source_rights(tmp_path):
    viability = _viability(story_type="regulatory_fiscal_event", article_mode="straight_news")
    context = extract_governed_story_context(viability)
    assets = build_source_backed_media_assets(context, output_dir=tmp_path)
    for asset in assets:
        # Capital Chronicle owns the rendered bytes only...
        assert asset["render_rights_status"] == OWN_RENDER_RIGHTS_STATE
        # ...and the underlying official source content is recorded separately as public
        # domain, never claimed as capital_chronicle_owned.
        assert asset["underlying_source_rights_status"] == UNDERLYING_RIGHTS_PUBLIC_DOMAIN
        assert asset["underlying_source_rights_status"] != OWN_RENDER_RIGHTS_STATE
        # The basis is now an explicit government-authorship classification, never a blanket
        # claim derived solely from the official_public_primary_source authority class.
        assert asset["source_reuse_basis"].startswith("us_government_authorship_public_domain")
        assert asset["source_reuse_basis"] != "official_public_primary_source_public_domain"


def test_underlying_source_rights_helper_does_not_overclaim():
    official = _official_document()
    rights, basis = _underlying_source_rights(official)
    assert rights == UNDERLYING_RIGHTS_PUBLIC_DOMAIN

    nonofficial = _official_document()
    nonofficial["source_authority_class"] = "untrusted_web_source"
    rights, basis = _underlying_source_rights(nonofficial)
    assert rights == UNDERLYING_RIGHTS_UNRESOLVED
    assert basis == "no_established_reuse_basis"


def test_unresolved_underlying_rights_render_metadata_only_not_excerpt(tmp_path):
    viability = _viability(story_type="company_sector_event", article_mode="straight_news")
    # Downgrade the source authority so excerpt reuse has no established basis.
    viability["selected_evidence"]["evidence_documents"][0]["source_authority_class"] = (
        "untrusted_web_source"
    )
    context = extract_governed_story_context(viability)
    assets = build_source_backed_media_assets(context, output_dir=tmp_path)
    modalities = {row["modality"] for row in assets}
    # No excerpt is rendered when underlying reuse rights are unresolved.
    assert "document_excerpt" not in modalities
    assert "source_metadata" in modalities
    metadata_card = next(row for row in assets if row["modality"] == "source_metadata")
    assert metadata_card["underlying_source_rights_status"] == UNDERLYING_RIGHTS_UNRESOLVED
    # Still three distinct assets (metadata-only diversity, no overclaimed excerpt).
    assert len(assets) == 3
    assert len({row["asset_id"] for row in assets}) == 3


def test_official_excerpt_is_not_overclaimed_as_cc_owned(tmp_path):
    viability = _viability(story_type="data_release", article_mode="straight_news")
    context = extract_governed_story_context(viability)
    assets = build_source_backed_media_assets(context, output_dir=tmp_path)
    excerpt = next(
        (row for row in assets if row["modality"] == "document_excerpt"), None
    )
    assert excerpt is not None
    assert excerpt["underlying_source_rights_status"] == UNDERLYING_RIGHTS_PUBLIC_DOMAIN
    assert excerpt["underlying_source_rights_status"] != OWN_RENDER_RIGHTS_STATE


# --- Rights provenance: evidence authority != reuse/public-domain rights --------


def _evidence_document(
    *,
    family,
    authority="official_public_primary_source",
    publisher="www.federalregister.gov",
    source_url="https://www.federalregister.gov/documents/x",
):
    doc = _official_document()
    doc["source_adapter_family"] = family
    doc["source_authority_class"] = authority
    doc["publisher"] = publisher
    doc["source_identity"] = publisher
    doc["source_url"] = source_url
    doc["requested_source_url"] = source_url
    return doc


def test_government_authored_source_has_supported_public_domain_basis():
    doc = _evidence_document(family="official_regulatory_fiscal")
    rights, basis = _underlying_source_rights(doc)
    assert rights == UNDERLYING_RIGHTS_PUBLIC_DOMAIN
    # Basis is government authorship at a governed publisher, NOT the authority class alone.
    assert basis.startswith("us_government_authorship_public_domain")
    assert "official_public_primary_source_public_domain" != basis


def test_sec_company_filing_evidence_authority_does_not_imply_public_domain():
    doc = _evidence_document(
        family="company_primary",
        authority="official_public_primary_source",
        publisher="www.sec.gov",
        source_url="https://www.sec.gov/Archives/edgar/data/0000000000/filings/10k.htm",
    )
    # The document remains authoritative primary evidence...
    assert doc["source_authority_class"] == "official_public_primary_source"
    rights, basis = _underlying_source_rights(doc)
    # ...but the company-authored underlying content must NOT become public domain.
    assert rights == UNDERLYING_RIGHTS_UNRESOLVED
    assert basis == "official_evidence_company_authored_no_public_domain"


def test_sec_regulatory_family_does_not_imply_public_domain():
    doc = _evidence_document(
        family="sec_regulatory",
        publisher="data.sec.gov",
        source_url="https://data.sec.gov/api/xbrl/companyfacts/CIK0000.json",
    )
    rights, basis = _underlying_source_rights(doc)
    assert rights == UNDERLYING_RIGHTS_UNRESOLVED
    assert basis == "official_evidence_company_authored_no_public_domain"


def test_company_investor_relations_release_not_public_domain():
    doc = _evidence_document(
        family="company_primary",
        publisher="ir.example-corp.com",
        source_url="https://ir.example-corp.com/newsroom/press-release.html",
    )
    rights, basis = _underlying_source_rights(doc)
    assert rights == UNDERLYING_RIGHTS_UNRESOLVED


def test_unknown_third_party_official_hosted_document_unresolved():
    doc = _evidence_document(
        family="official_macro",
        publisher="data.example-intl.org",
        source_url="https://data.example-intl.org/release.json",
    )
    rights, basis = _underlying_source_rights(doc)
    assert rights == UNDERLYING_RIGHTS_UNRESOLVED
    assert basis == "government_family_publisher_not_governed_public_domain"


def test_explicit_governed_public_domain_override_is_respected():
    doc = _evidence_document(family="official_macro", publisher="unlisted.example.gov")
    doc["underlying_reuse_classification"] = "governed_government_public_domain"
    rights, basis = _underlying_source_rights(doc)
    assert rights == UNDERLYING_RIGHTS_PUBLIC_DOMAIN
    assert basis == "explicit_governed_government_public_domain"


def _sec_viability():
    doc = _evidence_document(
        family="company_primary",
        publisher="www.sec.gov",
        source_url="https://www.sec.gov/Archives/edgar/data/0000000000/filings/10k.htm",
    )
    return _viability(story_type="company_sector_event", evidence=_evidence([doc]))


def test_sec_company_unresolved_rights_render_metadata_only_not_excerpt(tmp_path):
    context = extract_governed_story_context(_sec_viability())
    assets = build_source_backed_media_assets(context, output_dir=tmp_path)
    modalities = {row["modality"] for row in assets}
    # No underlying excerpt is reproduced when reuse rights are unresolved.
    assert "document_excerpt" not in modalities
    # Metadata-only source-backed reference remains allowed.
    assert "source_metadata" in modalities
    for row in assets:
        assert row["underlying_source_rights_status"] == UNDERLYING_RIGHTS_UNRESOLVED
        assert OWN_RENDER_RIGHTS_STATE not in {row["underlying_source_rights_status"]}
        assert row["render_rights_status"] == OWN_RENDER_RIGHTS_STATE


def test_render_rights_distinct_from_underlying_rights_for_sec(tmp_path):
    context = extract_governed_story_context(_sec_viability())
    assets = build_source_backed_media_assets(context, output_dir=tmp_path)
    assert len(assets) == 3 and len({row["asset_id"] for row in assets}) == 3
    for row in assets:
        assert row["render_rights_status"] != row["underlying_source_rights_status"]


def test_document_host_normalized():
    assert _document_host({"publisher": "www.SEC.gov"}) == "sec.gov"
    assert _document_host({"source_identity": "federalregister.gov"}) == "federalregister.gov"
    assert _document_host({"source_url": "https://www.treasury.gov/resource-center"}) == "treasury.gov"
