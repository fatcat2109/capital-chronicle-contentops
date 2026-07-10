from __future__ import annotations

from live_contentops.tier1_editorial_quality_v1 import (
    audit_tier1_article,
    build_comparison_packet,
    combine_editorial_gates,
    rendered_body,
    review_tier1_article_with_llm,
)


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
