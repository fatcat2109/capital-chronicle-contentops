from __future__ import annotations

import json
from pathlib import Path

from live_contentops.article_rich_text_v1 import (
    markdown_to_rich_text,
    rich_text_to_html,
    rich_text_to_plain_text,
    sanitize_source_text,
)
from live_contentops.edge_cdp_publishing_adapter_v1 import _substack_native_segment_html
from live_contentops.tier1_editorial_quality_v1 import evaluate_reader_value
from live_contentops.visual_asset_discovery_v1 import (
    AssetDiscoveryProvider,
    build_visual_intent_plan,
    discover_and_rank_assets,
    validate_asset_candidate,
)


ROOT = Path(__file__).resolve().parents[1]
GOLDEN = ROOT / "docs" / "automation" / (
    "DATABASE_PUBLICATION_AUTHORITY_AND_CONTENTOPS_FULL_LIVE_CLOSURE_V1"
) / "contentops_database_publication_live_20260714_1"


def _concise_article() -> dict:
    return {
        "title": "Agency Publishes a New Energy Supply Update",
        "editorial_mode": "straight_news",
        "effective_article_mode": "BREAKING_BRIEF",
        "article_generation_method": "ROUTED_LLM_GROUNDED_ARTICLE",
        "substack_body_markdown": (
            "[The agency](https://example.gov/release) published a new energy supply update "
            "today, confirming the change in its public record. The release establishes what "
            "happened and gives readers a primary source for the current fact pattern.\n\n"
            "The update matters because the confirmed supply change can now be separated from "
            "earlier expectations. Capital Chronicle does not infer prices, causes, or market "
            "effects that the source does not establish.\n\n"
            "Important uncertainty remains around implementation and timing. Subsequent official "
            "releases or independent reporting would be needed before adding numerical effects, "
            "forecasts, or a broader analytical conclusion for readers today."
        ),
    }


def test_one_sentence_plus_three_evidence_cards_is_not_publishable() -> None:
    article = {
        "title": "Agency Publishes an Energy Update",
        "editorial_mode": "straight_news",
        "effective_article_mode": "BREAKING_BRIEF",
        "article_generation_method": "ROUTED_LLM_GROUNDED_ARTICLE",
        "substack_body_markdown": (
            "[The agency](https://example.gov) published an update.\n\n"
            "[[VISUAL:source]]\n\n[[VISUAL:evidence]]\n\n[[VISUAL:metadata]]"
        ),
    }
    media = [
        {"asset_id": value, "caption": f"Evidence card {value}", "alt_text": value}
        for value in ("source", "evidence", "metadata")
    ]
    gate = evaluate_reader_value(article, media_assets=media)
    assert gate["classification"] == "INSUFFICIENT_READER_VALUE"
    assert gate["reader_prose_word_count"] < gate["floor"]["minimum_words"]
    assert gate["visual_count"] == 3


def test_clean_concise_ordinary_brief_can_pass_without_images() -> None:
    gate = evaluate_reader_value(_concise_article(), media_assets=[])
    assert gate["classification"] == "PASS"
    assert gate["floor_class"] == "CONCISE_UPDATE"
    assert gate["meaningful_paragraph_count"] == 3
    assert gate["visual_count"] == 0
    assert gate["checks"]["reader_value_independent_of_media"] is True


def test_useful_concise_copy_is_not_blocked_by_paragraph_or_word_target_ceremony() -> None:
    article = _concise_article()
    article["substack_body_markdown"] = " ".join(
        article["substack_body_markdown"].split()
    )

    gate = evaluate_reader_value(article)

    assert gate["classification"] == "PASS"
    assert gate["meaningful_paragraph_count"] == 1
    assert gate["formatting_targets"]["paragraph_target_met"] is False
    assert gate["formatting_targets_are_advisory"] is True


def test_normal_and_analysis_copy_do_not_require_heading_ceremony() -> None:
    normal = _concise_article()
    normal["effective_article_mode"] = "QUICK_ANALYSIS"
    normal["substack_body_markdown"] += (
        " The public record also establishes a clear sequence for implementation. Readers can "
        "therefore distinguish the confirmed change from any later market interpretation."
    )
    analysis = dict(normal)
    analysis["editorial_mode"] = "analysis"
    analysis["substack_body_markdown"] = normal["substack_body_markdown"] + (
        " The timing matters because the official update replaces an older public baseline. "
        "Implementation details will determine how quickly the confirmed change reaches users. "
        "A later agency notice would confirm whether the schedule remains intact. A withdrawal "
        "or amended record would challenge the current reading without changing what is known now. "
        "That distinction keeps the analysis anchored to the public evidence readers can inspect. "
        "It also leaves room for later reporting to add genuinely new information."
    )

    normal_gate = evaluate_reader_value(normal)
    analysis_gate = evaluate_reader_value(analysis)

    assert normal_gate["classification"] == "PASS"
    assert normal_gate["heading_count"] == 0
    assert normal_gate["formatting_targets"]["heading_target_met"] is False
    assert analysis_gate["classification"] == "PASS"
    assert analysis_gate["heading_count"] == 0
    assert analysis_gate["formatting_targets"]["heading_target_met"] is False


def test_title_only_repetitive_and_pipeline_copy_remain_hard_reader_value_failures() -> None:
    title_only = {
        **_concise_article(),
        "substack_body_markdown": "Agency Publishes a New Energy Supply Update",
    }
    repeated_sentence = (
        "The agency confirmed the public update and explained the implementation sequence."
    )
    filler = {
        **_concise_article(),
        "substack_body_markdown": " ".join([repeated_sentence] * 8),
    }
    pipeline = {
        **_concise_article(),
        "substack_body_markdown": (
            _concise_article()["substack_body_markdown"]
            + " The ContentOps pipeline and prompt completed the editorial task."
        ),
    }

    assert evaluate_reader_value(title_only)["classification"] == "INSUFFICIENT_READER_VALUE"
    assert evaluate_reader_value(filler)["checks"]["no_repetitive_filler"] is False
    assert evaluate_reader_value(pipeline)["checks"]["no_process_or_pipeline_language"] is False


def test_immutable_treasury_article_is_executable_golden_capability_fixture() -> None:
    article = json.loads((GOLDEN / "article_manifest_v1.json").read_text(encoding="utf-8"))
    media = json.loads((GOLDEN / "media_manifest_v1.json").read_text(encoding="utf-8"))["assets"]
    article["article_generation_method"] = "ROUTED_LLM_GROUNDED_ARTICLE"
    gate = evaluate_reader_value(article, media_assets=media)
    assert gate["classification"] == "PASS"
    assert gate["reader_prose_word_count"] >= 900
    assert gate["meaningful_paragraph_count"] >= 12
    assert gate["heading_count"] >= 4
    assert len(media) == 3
    assert {row["role"] for row in media} == {
        "lead_contextual", "document_excerpt", "primary_quantitative_chart"
    }


def test_raw_source_html_is_cleaned_and_script_navigation_are_omitted() -> None:
    raw = (
        "<!DOCTYPE html><html><head><style>.x{display:none}</style></head>"
        "<body><nav>Navigation boilerplate</nav><main><h1>Energy update</h1>"
        "<p>The useful official excerpt confirms the release.</p></main>"
        "<script>alert('no')</script></body></html>"
    )
    cleaned = sanitize_source_text(raw)
    assert "Energy update" in cleaned
    assert "useful official excerpt" in cleaned
    assert "DOCTYPE" not in cleaned
    assert "Navigation boilerplate" not in cleaned
    assert "alert" not in cleaned
    assert "<" not in cleaned


def test_raw_html_in_article_is_a_hard_reader_value_blocker() -> None:
    article = _concise_article()
    article["substack_body_markdown"] += "\n\n<!DOCTYPE html><script>bad()</script>"
    gate = evaluate_reader_value(article)
    assert gate["classification"] == "INSUFFICIENT_READER_VALUE"
    assert {"raw_doctype", "raw_html", "script_or_style_markup"}.issubset(
        set(gate["markup_findings"])
    )


def test_markdown_heading_link_and_emphasis_serialize_to_native_semantics() -> None:
    markdown = (
        "## What changed\n\nThe [official release](https://example.gov/release) "
        "contains **confirmed facts** and *important context*."
    )
    document = markdown_to_rich_text(markdown)
    html = rich_text_to_html(document)
    plain = rich_text_to_plain_text(document)
    adapter_html = _substack_native_segment_html(markdown)
    assert "<h2>What changed</h2>" in html
    assert '<a href="https://example.gov/release">official release</a>' in html
    assert "<strong>confirmed facts</strong>" in html
    assert "<em>important context</em>" in html
    assert adapter_html == html
    assert "##" not in plain
    assert "[official release](" not in plain


def test_link_nested_inside_emphasis_remains_native_link_and_emphasis() -> None:
    document = markdown_to_rich_text(
        "*Read the [official record](https://official.example/record) for context.*"
    )
    rendered = rich_text_to_html(document)

    assert '<em><a href="https://official.example/record">official record</a></em>' in rendered
    assert "](https://" not in rich_text_to_plain_text(document)


def _treasury_documentary_candidate(**overrides) -> dict:
    return {
        "visual_intent": "PERSON_OR_INSTITUTION_CONTEXT",
        "query": "Treasury yield curve official building photograph",
        "source_page_url": "https://commons.wikimedia.org/wiki/File:Treasury_Building_(32648233951).jpg",
        "original_asset_url": "https://upload.wikimedia.org/wikipedia/commons/e/e6/Treasury_Building_%2832648233951%29.jpg",
        "creator_publisher": "U.S. Department of the Treasury",
        "reuse_basis": "U.S. federal government work; public domain in the United States",
        "license_url": "https://commons.wikimedia.org/wiki/Template:PD-USGov-Treasury",
        "attribution": "U.S. Department of the Treasury",
        "width": 1908,
        "height": 1266,
        "content_hash": "sha256:" + "a" * 64,
        "perceptual_hash": "0123456789abcdef",
        "documentary_generated_classification": "DOCUMENTARY",
        "rights_status": "PUBLIC_DOMAIN",
        "story_relevance_score": 0.92,
        "subject_correctness_score": 0.98,
        "editorial_usefulness_score": 0.81,
        "composition_score": 0.88,
        "visual_diversity_score": 0.9,
        **overrides,
    }


def test_visual_asset_broker_supports_real_documentary_media_and_rejects_unknown_rights() -> None:
    article = {
        "title": "Treasury Yield Curve Edges Wider as Long Rates Rise",
        "substack_body_markdown": "The Treasury yield curve changed after the official release.",
    }
    plan = build_visual_intent_plan(article, evidence={"governed_data_series": [1]})
    intents = {row["visual_intent"] for row in plan["intents"]}
    assert {"HERO_DOCUMENTARY", "PERSON_OR_INSTITUTION_CONTEXT", "QUANTITATIVE_CHART", "COMPARISON"}.issubset(intents)
    assert all(len(row["queries"]) >= 1 for row in plan["intents"])

    unknown = _treasury_documentary_candidate(rights_status="UNKNOWN", reuse_basis="unknown")
    assert validate_asset_candidate(unknown)["status"] == "REJECTED"
    generated_fake = _treasury_documentary_candidate(
        documentary_generated_classification="CONCEPTUAL_GENERATED"
    )
    assert validate_asset_candidate(generated_fake)["status"] == "REJECTED"

    provider = AssetDiscoveryProvider(
        provider_id="wikimedia_commons",
        discover=lambda intent: (
            [_treasury_documentary_candidate(visual_intent=intent["visual_intent"], query=intent["queries"][0])]
            if intent["visual_intent"] == "PERSON_OR_INSTITUTION_CONTEXT"
            else []
        ),
    )
    result = discover_and_rank_assets(plan, providers=[provider], maximum_selected=3)
    assert result["status"] == "PASS"
    assert result["selected_count"] == 1
    assert result["selected_assets"][0]["documentary_generated_classification"] == "DOCUMENTARY"
    assert result["selected_assets"][0]["rights_status"] == "PUBLIC_DOMAIN"
    assert result["fixed_visual_quota"] is False
