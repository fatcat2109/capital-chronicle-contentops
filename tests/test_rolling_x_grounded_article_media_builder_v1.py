from __future__ import annotations

import json
from pathlib import Path

import pytest

from live_contentops import _eight_platform_substack_first_pipeline_impl_v1 as implementation
from live_contentops import rolling_x_grounded_article_media_builder_v1 as builder
from live_contentops.rolling_x_grounded_article_media_builder_v1 import (
    CODEX_EDITORIAL_BRAIN_TRIGGER,
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


def _handle_generator(asset_ids=()):
    def generator(prompt):
        governed = json.loads(prompt.split("GOVERNED_INPUT:\n", 1)[1])
        handle = governed["evidence_documents"][0]["source_handle"]
        body = _passing_body(FR_URL, list(asset_ids))
        for label in ("Federal Register", "rule", "register", "timeline"):
            body = body.replace(f"[{label}]({FR_URL})", label)
        body += f"\n\nSource: [[SOURCE:{handle}]]"
        result = _make_generator(FR_URL, list(asset_ids))(prompt)
        result["substack_body_markdown"] = body
        return result

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


def test_generation_prompt_matches_reader_facing_semantic_gate():
    context = extract_governed_story_context(
        _viability(story_type="data_release", article_mode="straight_news")
    )
    prompt = builder.build_article_generation_prompt(
        context,
        ["official_source_document_card", "decision_fact_card", "document_excerpt_card"],
    )

    assert "use the publisher name rather than a raw URL as link text" in prompt
    assert "state the core news once" in prompt
    assert "Do not add a generic financial-advice" in prompt
    assert "End the body with the exact line" not in prompt
    assert "No word count, heading count" in prompt
    assert "Select only the subset that materially improves understanding" in prompt
    assert "canonical_content_text fields are governed factual evidence" in prompt
    assert "supported_claims_highlight_core_expected_claims_but_are_not_exhaustive" in prompt
    assert "never calculate or infer a new number" in prompt


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
        required_asset_count=3,
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


def test_writer_receives_stable_source_handle_and_serialization_resolves_bound_url(tmp_path):
    prompts = []

    def generator(prompt):
        prompts.append(prompt)
        return _handle_generator()(prompt)

    result = build_rolling_x_grounded_article_and_media(
        _viability(), output_dir=tmp_path, article_generator=generator
    )

    assert len(prompts) == 1
    governed = json.loads(prompts[0].split("GOVERNED_INPUT:\n", 1)[1])
    assert governed["evidence_documents"][0]["source_handle"] == "SOURCE_1"
    assert "source_url" not in governed["evidence_documents"][0]
    assert FR_URL not in prompts[0]
    article = result["article"]
    assert "[[SOURCE:" not in article["substack_body_markdown"]
    assert f"[www.federalregister.gov]({FR_URL})" in article["substack_body_markdown"]
    assert article["source_binding_ids_referenced"] == [
        article["source_bindings"][0]["source_id"]
    ]


def test_unknown_writer_url_fails_closed_in_normal_bound_path(tmp_path):
    generator = _handle_generator()

    def unbound_generator(prompt):
        result = generator(prompt)
        result["substack_body_markdown"] += "\n\nUnknown: https://invented.example/story"
        return result

    with pytest.raises(GroundedArticleBuilderError, match="unbound_source_url"):
        build_rolling_x_grounded_article_and_media(
            _viability(), output_dir=tmp_path, article_generator=unbound_generator
        )


def test_unresolved_discovery_url_serializes_truthful_attribution_without_link(tmp_path):
    discovery_url = "https://news.google.com/rss/articles/opaque-discovery-path"
    document = _official_document(source_url=discovery_url)
    document.update(
        {
            "publisher": "Reuters",
            "source_identity": "reuters.com",
            "source_authority_class": "reputable_secondary_source",
            "secondary_listing_only": True,
            "reader_source_url": None,
        }
    )
    result = build_rolling_x_grounded_article_and_media(
        _viability(evidence=_evidence([document])),
        output_dir=tmp_path,
        article_generator=_handle_generator(),
    )
    article = result["article"]
    assert "Source: Reuters" in article["substack_body_markdown"]
    assert "Treasury Stress Testing Rule" not in article["substack_body_markdown"].split(
        "Source: Reuters", 1
    )[1]
    assert discovery_url not in article["substack_body_markdown"]
    assert article["source_trail"] == []
    assert article["source_attributions"][0]["reader_attribution_mode"] == "ATTRIBUTION_ONLY"
    assert article["source_attributions"][0]["title"] == "Treasury Stress Testing Rule"


def test_source_resolution_prevents_adjacent_duplicate_publisher_attribution():
    document = _official_document()
    document.update(
        {
            "publisher": "Reuters",
            "source_identity": "reuters.com",
            "source_authority_class": "reputable_secondary_source",
            "secondary_listing_only": True,
            "reader_source_url": None,
        }
    )
    context = extract_governed_story_context(_viability(evidence=_evidence([document])))
    resolved, source_ids, blockers = builder._resolve_generated_source_references(
        "According to Reuters [[SOURCE:SOURCE_1]], the rule changed. Reuters "
        "[[SOURCE:SOURCE_1]] reported the timetable.",
        context=context,
    )

    assert blockers == []
    assert source_ids
    assert "Reuters Reuters" not in resolved
    assert "According to Reuters, the rule changed" in resolved
    assert "Reuters reported the timetable" in resolved


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


def test_generated_article_cannot_reintroduce_exact_omitted_nonnumeric_claim():
    context = extract_governed_story_context(_viability())
    omitted_text = "The agency secretly expanded the rule beyond the published scope."
    context["claim_evidence_contract"] = {
        "status": "PASS",
        "supported_claims": [
            {
                "claim_id": "supported-1",
                "claim_text": "Treasury published a final stress testing rule.",
                "evidence_document_ids": ["official-primary-abc123"],
            }
        ],
        "omitted_unsupported_claims": [
            {"claim_id": "omitted-1", "claim_text": omitted_text, "reason": "unsupported"}
        ],
    }
    blockers = validate_generated_article(
        {
            "title": "Treasury Publishes Final Stress Testing Rule",
            "substack_body_markdown": (
                _passing_body(FR_URL, _regulatory_asset_ids()) + "\n\n" + omitted_text
            ),
            "evidence_document_ids": ["official-primary-abc123"],
            "cluster_id": "c1",
            "headline_ids": ["h1"],
            "x_content_grants_factual_authority": False,
        },
        context=context,
        visual_asset_ids=_regulatory_asset_ids(),
    )

    assert "article_reintroduced_omitted_claim" in blockers


def test_ordinary_story_uses_one_quality_writer_and_skips_semantic_review(
    tmp_path, monkeypatch
):
    document = _official_document()
    evidence = _evidence([document])
    evidence.update({
        "evidence_review_tier": "ORDINARY_MINIMUM",
        "evidence_substance": {
            "schema_version": "contentops.evidence_substance_summary.v1",
            "article_mode": "BREAKING_BRIEF",
            "target_usable_content_words": 90,
            "usable_content_words": 240,
            "enough_for_useful_article": True,
            "enrichment_recommended": False,
            "additional_source_is_eligibility_requirement": False,
            "publication_authority": False,
        },
        "minimum_trustworthy_evidence_packet": {
            "schema_version": "contentops.minimum_trustworthy_evidence_packet.v1",
            "status": "PASS",
            "risk_tier": "ORDINARY",
            "core_factual_proposition": "Treasury Stress Testing Rule",
            "source_title": "Treasury Stress Testing Rule",
            "publisher": "Federal Register",
            "source_url": FR_URL,
            "published_at_utc": "2026-08-08T09:00:00Z",
            "evidence_document_id": document["document_id"],
            "source_authority_class": "official_public_primary_source",
            "attribution_required": False,
            "publication_authority": False,
        },
    })

    writer_calls = []
    quality_writer = _make_generator(FR_URL, [])

    def counted_quality_writer(prompt):
        writer_calls.append(prompt)
        return quality_writer(prompt)

    built = build_rolling_x_grounded_article_and_media(
        _viability(evidence=evidence),
        output_dir=tmp_path,
        article_generator=counted_quality_writer,
    )
    assert len(writer_calls) == 1
    governed = json.loads(writer_calls[0].split("GOVERNED_INPUT:\n", 1)[1])
    assert governed["supported_claims"] == [
        {
            "additional_source_is_eligibility_requirement": False,
            "attribution_required": False,
            "claim_id": "ordinary-core-proposition",
            "claim_text": "Treasury Stress Testing Rule",
            "evidence_document_ids": [document["document_id"]],
            "support_status": "SUPPORTED_MINIMUM_TRUSTWORTHY_EVIDENCE",
        }
    ]
    assert governed["evidence_substance"]["enough_for_useful_article"] is True
    assert "never truncate useful evidence-rich reporting" in writer_calls[0]
    assert "three distinct kinds of value" in writer_calls[0]
    assert "Do not chain source-title restatements" in writer_calls[0]
    assert built["article"]["article_generation_method"] == "ROUTED_LLM_GROUNDED_ARTICLE"
    assert built["article"]["supported_claim_count"] == 1
    assert built["article"]["supported_claims"] == governed["supported_claims"]
    assert built["critical_path_telemetry"]["article_writer_semantic_calls"] == 1
    assert built["media"]["media_asset_count"] == 0
    payloads = implementation.build_native_derivative_payloads(
        article=built["article"],
        selection={"dek": "", "market_mechanism": "", "policy_context": "", "cross_asset_implications": ""},
        canonical_url="https://capitalchronicle.substack.com/p/ordinary-brief",
        media_asset_ids=[],
    )
    assert set(payloads) >= {
        "telegram", "discord", "x", "linkedin", "facebook_page",
        "instagram_business", "threads", "youtube",
    }
    assert payloads["x"]["reply_texts"] == []

    editorial = implementation._run_bounded_rolling_x_editorial_cycle(
        article=built["article"],
        media_assets=built["media"]["assets"],
        editorial_reviewer=lambda _article: (_ for _ in ()).throw(
            AssertionError("ordinary brief must not call semantic review")
        ),
        article_reviser=lambda *_args: (_ for _ in ()).throw(
            AssertionError("ordinary brief must not call semantic revision")
        ),
    )
    assert editorial["status"] == "PASS"
    assert editorial["semantic_review_required"] is False

    def visual_failure(*_args, **_kwargs):
        raise OSError("controlled optional visual failure")

    monkeypatch.setattr(builder, "build_source_backed_media_assets", visual_failure)
    text_only = build_rolling_x_grounded_article_and_media(
        _viability(evidence=evidence),
        output_dir=tmp_path / "text-only",
        article_generator=_make_generator(FR_URL, []),
    )
    assert text_only["media"]["media_asset_count"] == 0
    assert text_only["media"]["visual_optional_failure"] == "OSError"
    assert "[[VISUAL:" not in text_only["article"]["substack_body_markdown"]


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
    # Production default reaches the exact XHIGH editorial seam before any legacy writer.
    legacy_writer_calls = []
    monkeypatch.setattr(
        builder,
        "_default_article_generator",
        lambda _prompt: legacy_writer_calls.append(_prompt),
    )
    xhigh_calls = []

    def fake_xhigh(**kwargs):
        xhigh_calls.append(kwargs)
        generated = _codex_output_from_useful()
        generated.update({
            "article_generation_method": "FRESH_ISOLATED_CODEX_XHIGH_DEFAULT_EDITORIAL_BRAIN",
            "editorial_brain_status": "CODEX_XHIGH_DEFAULT",
            "_writer_router_telemetry": {
                "logical_invocations": 1,
                "nine_router_writer_called_before_xhigh": False,
                "degraded_editorial_brain": False,
            },
        })
        return generated

    monkeypatch.setattr(builder, "_run_codex_editorial_fallback", fake_xhigh)
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

    # Default builder produced a grounded article without forcing generic source cards.
    assert result["article"] is not None
    assert len(xhigh_calls) == 1
    assert legacy_writer_calls == []
    assert result["article"]["editorial_brain_status"] == "CODEX_XHIGH_DEFAULT"
    assert result["article"]["cluster_id"] == "c1"
    assert len(result["media"]["assets"]) == 0
    # Editorial review ran and passed (semantic reviewer invoked).
    assert result["editorial_cycle"]["status"] == "PASS"
    # Cached readiness is passive; the coordinator owns exact JIT verification at publication.
    # The newsroom therefore returns a plan while still performing no public write here.
    assert "release_candidate_preparation" in result
    assert result["classification"] == "PASS_PUBLICATION_PLAN_READY"
    assert result["publication_lifecycle_plan"]["destinations"][0][
        "jit_verification_required"
    ] is True
    assert result["publishing_adapter_called"] is False
    assert result["public_write_performed"] is False
    assert result["unknown_write_detected"] is False


def test_concise_mode_uses_quality_writer_before_deterministic_outage_fallback(tmp_path):
    viability = _viability(story_type="regulatory_fiscal_event", article_mode="straight_news")
    viability["rank_attempts"][0]["request"].update(
        {
            "requested_article_mode": "BREAKING_BRIEF",
            "resolved_article_mode": "BREAKING_BRIEF",
            "effective_article_mode": "BREAKING_BRIEF",
        }
    )
    calls = []
    fixture_generator = _make_generator(FR_URL, [])

    def quality_writer(prompt):
        calls.append(prompt)
        return fixture_generator(prompt)

    result = build_rolling_x_grounded_article_and_media(
        viability,
        output_dir=tmp_path,
        article_generator=quality_writer,
    )

    assert len(calls) == 1
    assert result["article"]["article_generation_method"] == "ROUTED_LLM_GROUNDED_ARTICLE"
    assert result["article"]["article_generation_router_failure"] is None


def test_decision5_provider_outage_copy_cannot_become_canonical_product(
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
    from live_contentops.nine_router_llm_seam_v2 import RoutedInvocationError

    def unavailable_quality_writer(_prompt):
        raise RoutedInvocationError(
            {
                "terminal_disposition": "PROVIDER_EXHAUSTED",
                "failure_class": "requested_model_temporarily_unavailable",
            }
        )

    monkeypatch.setattr(builder, "_default_article_generator", unavailable_quality_writer)
    codex_calls = []

    def unavailable_codex(**kwargs):
        codex_calls.append(kwargs)
        raise GroundedArticleBuilderError("CODEX_EDITORIAL_EXECUTION_FAILED")

    monkeypatch.setattr(builder, "_run_codex_editorial_fallback", unavailable_codex)

    result = implementation._run_rolling_x_newsroom_cycle(
        run_id="decision-5-offline-replay",
        output_dir=tmp_path,
        cutoff_utc="2026-08-11T12:57:00Z",
        story_type_by_cluster={"c1": "geopolitical_event"},
        editorial_reviewer=implementation._default_rolling_x_editorial_reviewer,
        article_reviser=lambda article, *_args: {
            **article,
            "substack_body_markdown": (
                str(article.get("substack_body_markdown") or "")
                + "\n\nThe provider-outage copy remains below the reader-value publication floor."
            ),
        },
        publication_enabled=False,
    )

    assert result["classification"] == "NO_PUBLICATION"
    assert result["exact_next_blocker"] == "ALL_BOUNDED_CANDIDATES_EXHAUSTED"
    assert result["candidate_walk"]["candidate_attempts"][0]["terminal_reason"] == (
        "GROUNDED_ARTICLE_BUILDER_FAIL_CLOSED"
    )
    assert len(codex_calls) == 1
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
    assert result["exact_next_blocker"] == "ALL_BOUNDED_CANDIDATES_EXHAUSTED"
    assert result["candidate_walk"]["candidate_attempts"][0]["terminal_reason"] == (
        "GROUNDED_ARTICLE_BUILDER_FAIL_CLOSED"
    )
    assert result["grounded_article_builder_blockers"] == [
        "article_untraceable_numeric_claim"
    ]
    assert result["public_write_performed"] is False


def test_deterministic_outage_brief_uses_ordinary_minimum_evidence_claim():
    document = _official_document(document_id="ordinary-source-1")
    evidence = _evidence([document])
    evidence["minimum_trustworthy_evidence_packet"] = {
        "schema_version": "contentops.minimum_trustworthy_evidence_packet.v1",
        "status": "PASS",
        "risk_tier": "ORDINARY",
        "core_factual_proposition": "Treasury published a final stress testing rule.",
        "evidence_document_id": "ordinary-source-1",
        "publisher": "Federal Register",
        "published_at_utc": "2026-08-08T09:00:00Z",
        "attribution_required": True,
        "publication_authority": False,
    }
    context = extract_governed_story_context(_viability(evidence=evidence))

    generated = builder._deterministic_supported_claim_brief(context, [])

    assert generated["article_generation_method"] == "DETERMINISTIC_SUPPORTED_CLAIM_BRIEF"
    assert "treasury published a final stress testing rule" in generated[
        "substack_body_markdown"
    ].casefold()
    assert "[[SOURCE:" in generated["substack_body_markdown"]


def test_writer_validator_rejects_used_fact_without_its_bound_source():
    governed_input = {
        "evidence_documents": [
            {"document_id": "d1", "source_handle": "SOURCE_1"},
            {"document_id": "d2", "source_handle": "SOURCE_2"},
        ],
        "supported_claims": [
            {
                "claim_id": "F3",
                "claim_text": "Low Danube water forced the second reactor shutdown.",
                "evidence_document_ids": ["d2"],
            }
        ],
    }
    article = {
        "substack_body_markdown": (
            "Low Danube water forced the second reactor shutdown. [[SOURCE:SOURCE_1]]"
        )
    }

    assert builder._writer_response_source_coverage_blockers(
        article, governed_input
    ) == ["grounded_fact_used_without_bound_source_reference:F3"]

    article["substack_body_markdown"] += " [[SOURCE:SOURCE_2]]"
    assert builder._writer_response_source_coverage_blockers(article, governed_input) == []


def test_writer_validator_rejects_uncovered_connective_paragraph():
    governed_input = {
        "evidence_documents": [
            {
                "document_id": "d1",
                "source_handle": "SOURCE_1",
                "canonical_content_text": "Danube water levels remain low.",
            }
        ],
        "supported_claims": [
            {
                "claim_id": "F1",
                "claim_text": "Danube water levels remain low.",
                "evidence_document_ids": ["d1"],
            }
        ],
    }
    article = {
        "substack_body_markdown": (
            "Danube water levels remain low. [[SOURCE:SOURCE_1]]\n\n"
            "This sweeping transformation definitively reshapes every strategic calculation."
        )
    }

    assert builder._writer_response_source_coverage_blockers(
        article, governed_input
    ) == ["grounded_paragraph_source_coverage_incomplete:1"]


def _useful_writer_output(handle="SOURCE_1"):
    return {
        "title": "Treasury Publishes Final Stress Testing Rule",
        "subtitle": "The official document establishes a compliance sequence.",
        "seo_title": "Treasury Stress Testing Rule Published",
        "meta_description": "Treasury published the final rule and documented its compliance timetable.",
        "market_mechanism": "",
        "policy_context": "The official rule documents implementation.",
        "cross_asset_implications": "",
        "social_lede": "Treasury published the final stress testing rule.",
        "social_mechanism_summary": "The document establishes the compliance sequence.",
        "social_policy_summary": "Affected entities are covered by the final rule.",
        "social_cross_asset_summary": "",
        "substack_body_markdown": (
            f"Treasury published a final stress testing rule, according to [[SOURCE:{handle}]]. "
            "The official document says the rule takes effect after a compliance date and "
            "applies to affected entities.\n\n"
            "Capital Chronicle inference: the documented administrative sequence may give "
            "affected entities a clearer order for planning implementation while they prepare "
            "for the stated compliance date.\n\n"
            "The official document says Treasury published the final stress testing rule, that "
            "the rule takes effect after a compliance date, and that it applies to affected "
            "entities. Reading those items together supplies the strongest supported detail.\n\n"
            "Capital Chronicle inference: that sequence may help affected entities plan "
            "implementation, while a superseding official notice would leave the timing and "
            "compliance schedule unresolved. Until then, the published final rule is the "
            "documented reference point for implementation."
        ),
    }


def test_writer_utility_preflight_rejects_thin_copy_and_accepts_useful_copy():
    context = extract_governed_story_context(_viability())
    prompt = builder.build_article_generation_prompt(context, [])
    governed = json.loads(prompt.split("GOVERNED_INPUT:\n", 1)[1])
    governed["evidence_substance"] = {"enough_for_useful_article": True}
    thin = {
        "title": "Treasury Publishes Final Rule",
        "substack_body_markdown": (
            "Treasury published a final stress testing rule [[SOURCE:SOURCE_1]]."
        ),
    }

    thin_codes = builder._writer_utility_preflight(thin, governed)
    assert "WRITER_UTILITY_INSUFFICIENT_READER_SUBSTANCE" in thin_codes
    assert "WRITER_UTILITY_NO_DISTINCT_READER_PAYOFF" in thin_codes
    assert builder._writer_utility_preflight(_useful_writer_output(), governed) == []


def test_default_writer_uses_one_repair_then_one_separate_cx_utility_rescue(
    monkeypatch,
):
    from live_contentops import nine_router_llm_seam_v2 as seam
    from live_contentops.nine_router_ordered_model_router_v2 import (
        ACCEPTED,
        CX_FINAL_FALLBACK_MODEL,
        ORDERED_MODEL_POOL,
    )

    context = extract_governed_story_context(_viability())
    prompt = builder.build_article_generation_prompt(context, [])
    thin = {
        "title": "Treasury Publishes Final Rule",
        "substack_body_markdown": (
            "Treasury published a final stress testing rule [[SOURCE:SOURCE_1]]."
        ),
    }
    calls = []

    def fake_routed(**kwargs):
        calls.append(kwargs["role_task_id"])
        if kwargs["role_task_id"] == seam.ROLE_ARTICLE_WRITING:
            first = kwargs["validator"](json.dumps(thin))
            assert first[0] is False
            repaired_prompt = kwargs["repair_prompt_builder"](
                kwargs["prompt"], json.dumps(thin), first[3]
            )
            assert json.dumps(thin) not in repaired_prompt
            second = kwargs["validator"](json.dumps(thin))
            assert second[0] is True
            return {
                "terminal_disposition": ACCEPTED,
                "logical_invocation_id": kwargs["logical_invocation_id"],
                "selected_model": ORDERED_MODEL_POOL[0],
                "models_attempted_in_order": [ORDERED_MODEL_POOL[0]],
                "total_attempts": 2,
                "total_fallback_transitions": 0,
                "total_structured_repair_attempts": 1,
                "attempts": [],
                "output": second[2],
            }
        accepted = kwargs["validator"](json.dumps(_useful_writer_output()))
        assert accepted[0] is True
        return {
            "terminal_disposition": ACCEPTED,
            "logical_invocation_id": kwargs["logical_invocation_id"],
            "selected_model": CX_FINAL_FALLBACK_MODEL,
            "models_attempted_in_order": [CX_FINAL_FALLBACK_MODEL],
            "total_attempts": 1,
            "total_fallback_transitions": 0,
            "total_structured_repair_attempts": 0,
            "attempts": [],
            "output": accepted[2],
        }

    monkeypatch.setattr(seam, "routed_llm_invocation", fake_routed)
    generated = builder._default_article_generator(prompt)

    assert calls == [
        seam.ROLE_ARTICLE_WRITING,
        seam.ROLE_ARTICLE_WRITING_CX_RESCUE,
    ]
    telemetry = generated["_writer_router_telemetry"]
    assert telemetry["normal_repair_attempted"] is True
    assert telemetry["cx_utility_rescue_attempted"] is True
    assert telemetry["logical_invocations"] == 2
    assert generated["_writer_utility_preflight"]["classification"] == "PASS"


def test_cx_utility_rescue_cannot_add_unsupported_claims(monkeypatch):
    from live_contentops import nine_router_llm_seam_v2 as seam
    from live_contentops.nine_router_ordered_model_router_v2 import ACCEPTED, ORDERED_MODEL_POOL

    context = extract_governed_story_context(_viability())
    prompt = builder.build_article_generation_prompt(context, [])
    thin = {
        "title": "Treasury Publishes Final Rule",
        "substack_body_markdown": (
            "Treasury published a final stress testing rule [[SOURCE:SOURCE_1]]."
        ),
    }

    def fake_routed(**kwargs):
        if kwargs["role_task_id"] == seam.ROLE_ARTICLE_WRITING:
            first = kwargs["validator"](json.dumps(thin))
            kwargs["repair_prompt_builder"](kwargs["prompt"], json.dumps(thin), first[3])
            second = kwargs["validator"](json.dumps(thin))
            return {
                "terminal_disposition": ACCEPTED,
                "selected_model": ORDERED_MODEL_POOL[0],
                "models_attempted_in_order": [ORDERED_MODEL_POOL[0]],
                "total_attempts": 2,
                "total_structured_repair_attempts": 1,
                "attempts": [],
                "output": second[2],
            }
        unsupported = _useful_writer_output()
        unsupported["substack_body_markdown"] += (
            "\n\nA newly discovered lunar bank guaranteed profits across every global market."
        )
        rejected = kwargs["validator"](json.dumps(unsupported))
        assert rejected[0] is False
        assert rejected[1] == "factual_validation_failure"
        return {
            "terminal_disposition": "LLM_TERMINAL_NON_RETRYABLE_FAILURE",
            "models_attempted_in_order": ["cx/gpt-5.6-sol(xhigh)"],
            "total_attempts": 1,
            "total_structured_repair_attempts": 0,
            "attempts": [],
            "output": None,
        }

    monkeypatch.setattr(seam, "routed_llm_invocation", fake_routed)
    with pytest.raises(
        GroundedArticleBuilderError,
        match="TRIGGER_V1_CODEX_EDITORIAL_BRAIN_VERTICAL_SLICE",
    ) as raised:
        builder._default_article_generator(prompt)
    assert raised.value.writer_router_telemetry["logical_invocations"] == 2
    assert raised.value.writer_router_telemetry["cx_utility_rescue_attempted"] is True
    assert raised.value.writer_router_telemetry["cx_rescue"]["terminal_disposition"] == (
        "LLM_TERMINAL_NON_RETRYABLE_FAILURE"
    )


def _codex_eligible_viability(*, cc_required=False, authority_verified=False):
    document = _official_document()
    evidence = _evidence([document], authority_verified=authority_verified)
    evidence["minimum_trustworthy_evidence_packet"] = {
        "status": "PASS",
        "risk_tier": "ORDINARY",
        "core_factual_proposition": (
            "Treasury published a final stress testing rule that takes effect after a compliance "
            "date and applies to affected entities."
        ),
        "evidence_document_id": document["document_id"],
        "attribution_required": True,
        "publication_authority": False,
    }
    evidence["evidence_substance"] = {
        "enough_for_useful_article": True,
        "usable_document_count": 1,
    }
    evidence["claim_evidence_contract"] = {
        "supported_claims": [],
        "omitted_unsupported_claims": [],
        "omitted_claim_count": 0,
    }
    return _viability(
        evidence=evidence,
        cc_required=cc_required,
        capability_authority_required=cc_required,
    )


def _codex_output_from_useful(*, body_suffix=""):
    output = _useful_writer_output()
    output["substack_body_markdown"] += body_suffix
    output.update(
        {
            "source_handles_used": ["SOURCE_1"],
            "evidence_document_ids": ["official-primary-abc123"],
            "explicit_inferences": [],
            "self_review_summary": (
                "Uses the bound source, states the news once, and adds no unsupported number."
            ),
            "abstain_reason": None,
        }
    )
    return output


def _codex_execution(output, *, execution_id="codex-exec-1"):
    return {
        "exit_classification": "SUCCESS",
        "exit_code": 0,
        "wall_time_seconds": 1.5,
        "timeout_seconds": 30.0,
        "fresh_execution_id": execution_id,
        "effective_model": None,
        "usage": {},
        "tool_event_counts": {
            "command_executions": 0,
            "web_searches": 0,
            "mcp_tool_calls": 0,
            "file_changes": 0,
            "browser_calls": 0,
        },
        "output": output,
    }


def test_accepted_codex_trigger_routes_to_one_isolated_job_and_existing_gates(tmp_path):
    calls = []

    def codex_adapter(request):
        calls.append(request)
        return _codex_execution(_codex_output_from_useful())

    built = build_rolling_x_grounded_article_and_media(
        _codex_eligible_viability(),
        output_dir=tmp_path / "opportunity",
        accepted_codex_trigger_receipt={
            "classification": CODEX_EDITORIAL_BRAIN_TRIGGER,
            "writer_router": {"logical_invocations": 2},
        },
        codex_execution_adapter=codex_adapter,
        codex_runtime_root=tmp_path / "runtime",
        codex_timeout_seconds=30,
    )

    assert len(calls) == 1
    assert calls[0].job_dir.parent.parent == tmp_path / "runtime"
    assert built["article"]["article_generation_method"] == (
        "FRESH_ISOLATED_CODEX_XHIGH_DEFAULT_EDITORIAL_BRAIN"
    )
    assert calls[0].requested_model == "gpt-5.6-sol"
    assert calls[0].requested_reasoning_effort == "xhigh"
    assert built["article"]["editorial_brain_status"] == "CODEX_XHIGH_DEFAULT"
    assert built["article"]["codex_editorial_brain_receipt"]["status"] == "COMPLETED"
    assert built["article"]["writer_reader_value_preflight"]["classification"] == "PASS"
    assert "[[SOURCE:" not in built["article"]["substack_body_markdown"]
    assert FR_URL in built["article"]["substack_body_markdown"]
    assert built["critical_path_telemetry"]["article_writer_semantic_calls"] == 3
    assert built["publication_authority"] is False


def test_codex_is_not_invoked_for_authority_ineligible_story(tmp_path):
    calls = []

    def codex_adapter(request):
        calls.append(request)
        return _codex_execution(_codex_output_from_useful())

    with pytest.raises(
        GroundedArticleBuilderError,
        match="analytical_mode_requires_capital_chronicle_authority",
    ):
        build_rolling_x_grounded_article_and_media(
            _codex_eligible_viability(cc_required=True, authority_verified=False),
            output_dir=tmp_path / "opportunity",
            accepted_codex_trigger_receipt={
                "classification": CODEX_EDITORIAL_BRAIN_TRIGGER
            },
            codex_execution_adapter=codex_adapter,
            codex_runtime_root=tmp_path / "runtime",
        )
    assert calls == []


def test_default_xhigh_runs_before_legacy_writer_and_factual_rejection_does_not_fallback(
    tmp_path, monkeypatch
):
    codex_calls = []
    legacy_calls = []

    def prohibited_legacy(_prompt):
        legacy_calls.append(_prompt)
        raise AssertionError("legacy writer must not run after XHIGH factual rejection")

    def rejected_xhigh(**kwargs):
        codex_calls.append(kwargs)
        raise GroundedArticleBuilderError(
            "CODEX_EDITORIAL_OUTPUT_REJECTED",
            writer_router_telemetry={
                "logical_invocations": 1,
                "codex_editorial_brain": {
                    "validation_result": {
                        "classification": "FAIL_FORBIDDEN",
                        "forbidden_failure_codes": ["article_untraceable_numeric_claim"],
                    }
                },
            },
        )

    monkeypatch.setattr(builder, "_default_article_generator", prohibited_legacy)
    monkeypatch.setattr(builder, "_run_codex_editorial_fallback", rejected_xhigh)

    with pytest.raises(
        GroundedArticleBuilderError,
        match="CODEX_EDITORIAL_OUTPUT_REJECTED",
    ):
        build_rolling_x_grounded_article_and_media(
            _codex_eligible_viability(),
            output_dir=tmp_path / "opportunity",
            codex_runtime_root=tmp_path / "runtime",
        )

    assert len(codex_calls) == 1
    assert legacy_calls == []


def test_codex_unsupported_numeric_output_is_rejected_without_revision(tmp_path):
    calls = []

    def codex_adapter(request):
        calls.append(request)
        return _codex_execution(
            _codex_output_from_useful(
                body_suffix="\n\nThe rule creates a new $999 billion obligation."
            )
        )

    with pytest.raises(GroundedArticleBuilderError, match="CODEX_EDITORIAL_OUTPUT_REJECTED") as raised:
        build_rolling_x_grounded_article_and_media(
            _codex_eligible_viability(),
            output_dir=tmp_path / "opportunity",
            accepted_codex_trigger_receipt={
                "classification": CODEX_EDITORIAL_BRAIN_TRIGGER
            },
            codex_execution_adapter=codex_adapter,
            codex_runtime_root=tmp_path / "runtime",
        )

    assert len(calls) == 1
    receipt = raised.value.writer_router_telemetry["codex_editorial_brain"]
    assert receipt["revision_count"] == 0
    assert "article_untraceable_numeric_claim" in receipt["validation_result"][
        "forbidden_failure_codes"
    ]


def test_codex_untraceable_quotation_is_rejected_without_revision(tmp_path):
    calls = []

    def codex_adapter(request):
        calls.append(request)
        return _codex_execution(
            _codex_output_from_useful(
                body_suffix=(
                    '\n\nAn unnamed observer called the rule “a guaranteed windfall for every bank.”'
                )
            )
        )

    with pytest.raises(GroundedArticleBuilderError, match="CODEX_EDITORIAL_OUTPUT_REJECTED") as raised:
        build_rolling_x_grounded_article_and_media(
            _codex_eligible_viability(),
            output_dir=tmp_path / "opportunity",
            accepted_codex_trigger_receipt={
                "classification": CODEX_EDITORIAL_BRAIN_TRIGGER
            },
            codex_execution_adapter=codex_adapter,
            codex_runtime_root=tmp_path / "runtime",
        )

    assert len(calls) == 1
    receipt = raised.value.writer_router_telemetry["codex_editorial_brain"]
    assert receipt["revision_count"] == 0
    assert "article_untraceable_quotation" in receipt["validation_result"][
        "forbidden_failure_codes"
    ]


def test_existing_writer_path_remains_primary_when_it_succeeds(tmp_path):
    calls = []

    def codex_adapter(request):
        calls.append(request)
        return _codex_execution(_codex_output_from_useful())

    built = build_rolling_x_grounded_article_and_media(
        _codex_eligible_viability(),
        output_dir=tmp_path / "opportunity",
        article_generator=lambda _prompt: _useful_writer_output(),
        codex_execution_adapter=codex_adapter,
        codex_runtime_root=tmp_path / "runtime",
    )

    assert calls == []
    assert built["article"]["article_generation_method"] == "ROUTED_LLM_GROUNDED_ARTICLE"


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
