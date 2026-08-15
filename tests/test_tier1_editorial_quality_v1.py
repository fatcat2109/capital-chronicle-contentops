from __future__ import annotations

from live_contentops.tier1_editorial_quality_v1 import (
    audit_tier1_article,
    build_comparison_packet,
    build_grounded_oil_release_candidate,
    combine_editorial_gates,
    rendered_body,
    review_tier1_article_with_llm,
    review_minimum_evidence_news_brief,
    validate_llm_editorial_review,
    evaluate_headline_desk,
    LLM_REVIEW_CHECKS,
)


def test_material_quote_requires_exact_evidence_and_source_binding() -> None:
    article = {
        "title": "Retail Sales Decline in July",
        "editorial_mode": "straight_news",
        "effective_article_mode": "BREAKING_BRIEF",
        "substack_body_markdown": (
            'MarketWatch called the pullback an “Amazon Prime hangover” after retail '
            "sales declined in July. The report did not state the magnitude of the decline. "
            "That limits conclusions about its scale."
        ),
    }

    unbound = audit_tier1_article(article, media_assets=[])
    assert unbound["editorial_checks"]["no_fabricated_quotes"] is False

    article["quote_source_records"] = [{
        "quote_text": "Amazon Prime hangover",
        "evidence_document_ids": ["doc-1"],
        "source_binding_ids": ["source-1"],
    }]
    grounded = audit_tier1_article(article, media_assets=[])
    assert grounded["editorial_checks"]["no_fabricated_quotes"] is True


def test_minimum_evidence_review_accepts_fresh_isolated_codex_method() -> None:
    article = {
        "article_generation_method": "FRESH_ISOLATED_CODEX_EDITORIAL_BRAIN",
        "substack_body_markdown": (
            "Retail sales slumped as cheaper gas and an Amazon Prime hangover were cited."
        ),
        "minimum_trustworthy_evidence_packet": {
            "status": "PASS",
            "risk_tier": "ORDINARY",
            "core_factual_proposition": (
                "Retail sales slump. Cheaper gas and an Amazon Prime hangover are the chief culprits."
            ),
            "source_url": "https://example.test/source",
            "evidence_document_id": "doc-1",
        },
        "source_bindings": [{
            "source_id": "source-1",
            "evidence_document_id": "doc-1",
        }],
        "source_binding_ids_referenced": ["source-1"],
        "evidence_document_ids": ["doc-1"],
        "x_content_grants_factual_authority": False,
    }

    review = review_minimum_evidence_news_brief(article)
    assert review["decision"] == "PASS"
    assert review["material_failed_checks"] == []


def _media() -> list[dict]:
    return [
        {"asset_id": "primary", "caption": "Primary", "alt_text": "Primary chart", "sha256": "a" * 64},
        {"asset_id": "policy_corridor", "caption": "Policy", "alt_text": "Policy chart", "sha256": "b" * 64},
        {"asset_id": "sofr_context", "caption": "Curve", "alt_text": "Curve chart", "sha256": "c" * 64},
    ]


def _passing_llm_review(_prompt: str, _provider: str) -> dict:
    return {
        "decision": "PASS",
        "mode": "analysis",
        "checks": {
            "clear_news_peg": True,
            "why_now": True,
            "material_market_consequence": True,
            "concise_nut_graf": True,
            "mode_consistent": True,
            "material_claims_supported": True,
            "no_factual_contradiction": True,
            "no_fabricated_numbers": True,
            "material_evidence_matches": True,
            "no_misleading_framing": True,
            "severe_coherence_ok": True,
            "source_backed_mechanism": True,
            "relevant_context": True,
            "specific_confirmation_condition": True,
            "specific_falsification_condition": True,
            "reader_facing_prose": True,
            "no_unsupported_certainty": True,
            "no_fabricated_quotes": True,
            "no_financial_advice": True,
            "high_information_density": True,
        },
        "issues": [],
        "summary": "The article has a current peg, a sourced mechanism, concrete tests, and reader-facing prose.",
    }


def test_process_language_and_missing_why_now_fail_tier1_gate() -> None:
    body = "## Note\n\nThe editorial task is to fill the draft. The chart manifest records a visual."
    article = {"title": "Fed Funds", "seo_title": "Fed Funds", "slug": "fed-funds", "meta_description": "short", "substack_body_markdown": body}
    audit = audit_tier1_article(article, media_assets=_media())
    assert audit["classification"] == "NEEDS_REVISION"
    assert audit["process_language_hits"]
    assert audit["editorial_checks"]["lede_why_now"] is False


def test_rendered_body_removes_visual_markers() -> None:
    assert "[[VISUAL:" not in rendered_body("Opening\n\n[[VISUAL:primary]]\n\nClose")


def test_optional_seo_remains_advisory_but_reader_value_is_hard() -> None:
    article = {
        "title": "Agency Confirms A New Public Notice",
        "editorial_mode": "straight_news",
        "substack_body_markdown": (
            "The agency confirmed a new public notice today. What matters is that the "
            "published notice is now the governing public record."
        ),
    }

    audit = audit_tier1_article(article, media_assets=[])

    assert audit["classification"] == "NEEDS_REVISION"
    assert audit["seo_score"] < 85
    assert audit["seo_blockers"]
    assert audit["seo_findings_are_advisory"] is True
    assert audit["hard_editorial_blockers"] == ["reader_value_floor"]
    assert audit["reader_value_gate"]["classification"] == "INSUFFICIENT_READER_VALUE"


def test_semantic_review_advisory_only_revision_is_normalized_to_pass() -> None:
    checks = {name: True for name in LLM_REVIEW_CHECKS}
    checks["specific_confirmation_condition"] = False
    normalized = validate_llm_editorial_review(
        {
            "decision": "NEEDS_REVISION",
            "mode": "straight_news",
            "checks": checks,
            "issues": [
                {
                    "code": "optional_confirmation_detail",
                    "evidence": "Useful brief has no sophisticated confirmation framing.",
                }
            ],
            "summary": "Only an advisory context improvement remains.",
        }
    )

    assert normalized["decision"] == "PASS"
    assert normalized["material_failed_checks"] == []
    assert normalized["advisory_failed_checks"] == [
        "specific_confirmation_condition"
    ]
    assert normalized["advisory_only_revision_normalized_to_pass"] is True


def test_revised_fixture_passes_editorial_and_seo_gates() -> None:
    original = {
        "title": "Effective Fed Funds Rate Holds at 3.62% as Policy Calibration Continues",
        "subtitle": "FRED latest update",
        "seo_title": "Effective Fed Funds Rate at 3.62% and the Policy Corridor",
        "slug": "effective-fed-funds-rate-3-62-policy-calibration",
        "meta_description": "FRED's latest effective federal funds reading was 3.62% on 2026-07-08 inside the 3.50% to 3.75% target range, keeping policy transmission in focus.",
        "substack_body_markdown": "## Opening\n\nThe editorial task is to explain the latest 3.62% reading on 2026-07-08. The chart manifest records the process.",
    }
    packet = build_comparison_packet(
        {"article": original, "media": {"assets": _media()}},
        canonical_url="https://capitalchronicle.substack.com/p/example",
        llm_provider="test",
        llm_reviewer=_passing_llm_review,
    )
    assert packet["classification"] == "PASS_LOCAL_REVISED_CANDIDATE"
    assert packet["revised_audit"]["editorial_score"] >= 85
    assert packet["revised_audit"]["seo_score"] >= 85
    assert packet["revised_audit"]["word_count"] < 1400
    assert packet["source_continuity"]["all_three_visuals_retained"] is True
    assert packet["public_write_performed"] is False
    assert packet["llm_semantic_review"]["decision"] == "PASS"
    assert packet["combined_editorial_gate"]["classification"] == "PASS"


def test_llm_review_is_bounded_and_cannot_override_deterministic_failure() -> None:
    article = {
        "title": "Fed Funds",
        "editorial_mode": "analysis",
        "substack_body_markdown": "The editorial task is to explain the pipeline.",
    }
    deterministic = audit_tier1_article(article, media_assets=_media())
    llm_review = review_tier1_article_with_llm(
        article,
        llm_provider="test",
        llm_reviewer=_passing_llm_review,
    )
    combined = combine_editorial_gates(deterministic, llm_review)
    assert llm_review["publication_authority"] is False
    assert llm_review["decision"] == "PASS"
    assert combined["classification"] == "NEEDS_REVISION"
    assert combined["llm_cannot_override_deterministic_blockers"] is True


def test_llm_review_fails_closed_on_incomplete_schema() -> None:
    review = review_tier1_article_with_llm(
        {"title": "Fed Funds", "substack_body_markdown": "Current rates analysis."},
        llm_provider="test",
        llm_reviewer=lambda _prompt, _provider: {"decision": "PASS", "mode": "analysis", "checks": {}, "issues": [], "summary": "Pass."},
    )
    assert review["status"] == "INVALID_LLM_REVIEW"
    assert review["decision"] == "NEEDS_REVISION"


def test_grounded_oil_release_candidate_passes_topic_aware_gate() -> None:
    media = [
        {"asset_id": "primary", "caption": "WTI and volatility.", "alt_text": "WTI chart", "source_page_url": "https://fred.stlouisfed.org/series/DCOILWTICO", "latest_observation_value": 68.25, "latest_observation_date": "2026-07-07"},
        {"asset_id": "recent_price", "caption": "Recent WTI path.", "alt_text": "Recent WTI chart", "source_page_url": "https://fred.stlouisfed.org/series/DCOILWTICO"},
        {"asset_id": "multi_year_range", "caption": "Multi-year WTI range.", "alt_text": "Multi-year WTI chart", "source_page_url": "https://fred.stlouisfed.org/series/DCOILWTICO"},
    ]
    source_packet = {
        "status": "PASS_OFFICIAL_EIA_RELEASE_GROUNDED",
        "source_url": "https://www.eia.gov/pressroom/releases/press590.php",
        "supporting_source_urls": [
            "https://www.eia.gov/outlooks/steo/",
            "https://fred.stlouisfed.org/series/DCOILWTICO",
            "https://www.federalreserve.gov/newsevents/pressreleases/monetary20260617a.htm",
        ],
        "source_text_sha256": "d" * 64,
        "facts": {
            "release_date": "2026-07-07",
            "brent_june_average_usd_per_barrel": 85,
            "brent_q3_2026_forecast_usd_per_barrel": 74,
            "brent_2027_forecast_usd_per_barrel": 65,
            "gasoline_q3_2026_forecast_usd_per_gallon": 3.80,
            "gasoline_q4_2026_forecast_usd_per_gallon": 3.40,
            "next_weekly_petroleum_status_report_date": "2026-07-15",
            "next_steo_release_date": "2026-08-11",
        },
    }
    article = build_grounded_oil_release_candidate(
        {"why_ranked": "Fresh official EIA forecast with cross-asset implications."},
        source_packet=source_packet,
        media_assets=media,
    )
    audit = audit_tier1_article(article, media_assets=media)
    assert audit["classification"] == "PASS"
    assert audit["editorial_score"] >= 85
    assert audit["seo_score"] >= 85
    assert audit["visual_asset_ids"] == ["primary", "recent_price", "multi_year_range"]
    assert not audit["process_language_hits"]
    assert "July 15 Weekly Petroleum Status Report" in article["substack_body_markdown"]
    assert "August 11 Short-Term Energy Outlook" in article["substack_body_markdown"]


def test_deep_analysis_requires_original_value_and_detects_semantic_redundancy() -> None:
    article = {
        "editorial_mode": "deep_analysis",
        "substack_body_markdown": "## A\n\nThis sentence repeats the same market mechanism and conditions in detail for readers.\n\n## B\n\nThis sentence repeats the same market mechanism and conditions in detail for readers.",
    }
    audit = audit_tier1_article(article, media_assets=_media())
    assert audit["editorial_checks"]["mode_rubric"] is False
    assert audit["editorial_checks"]["original_value_claim_support"] is False
    assert audit["paragraph_redundancy_findings"]
    assert audit["seo_hygiene_is_observed_search_performance"] is False


def test_headline_desk_preserves_clickbait_rejection_without_authority() -> None:
    desk = evaluate_headline_desk({"title": "Official data update", "seo_title": "Official data update", "seo_primary_keyword": "official", "social_headline": "Shocking secret proves markets always rise"})
    social = next(row for row in desk["variants"] if row["channel"] == "social")
    assert "no_clickbait" in social["rejection_reasons"]
    assert "no_mismatch" in social["rejection_reasons"]
    assert desk["publication_authority"] is False
