import copy

from live_contentops.editorial_quality_audit_v6 import (
    EDITORIAL_APPROVED,
    EDITORIAL_BLOCKED,
    EDITORIAL_NEEDS_REVIEW,
    audit_editorial_quality_packet,
)


def _clean_article_packet():
    intro = (
        "The latest WTI oil evidence gives the recession-risk debate a current starting point. "
        "WTI crude was reported at $71.87 per barrel on 2026-06-29, and the recent 90-day "
        "move was 7.8%. The question now is how that energy channel interacts with household "
        "income, inflation expectations, and policy timing."
    )
    sections = [
        {
            "title": "Why Now: Current Oil Evidence",
            "body": (
                "The current setup matters because the data endpoint is recent and source-backed. "
                "FRED series DCOILWTICO carries the WTI observation through 2026-06-29, while the "
                "EIA is the underlying petroleum source. That makes the evidence current enough for "
                "a 2026 macro article."
            ),
        },
        {
            "title": "Transmission Channels",
            "body": (
                "Oil volatility can affect transport costs, real income, and inflation expectations. "
                "Those channels do not prove a recession by themselves, but they widen the range of "
                "macro outcomes that policy makers and companies need to monitor."
            ),
        },
        {
            "title": "Rates and Recession Context",
            "body": (
                "Yield curves and energy prices are separate lenses. Treasury and Federal Reserve "
                "sources should be used for rate context, while FRED and EIA support the oil-price "
                "claims. This separation keeps the evidence from doing more work than it can support."
            ),
        },
        {
            "title": "Limits and Counterargument",
            "body": (
                "The counterargument is straightforward: a higher oil-volatility reading is not "
                "sufficient evidence of a recession. The interpretation would weaken if the oil move "
                "reversed quickly or if income and credit data stayed resilient."
            ),
        },
        {
            "title": "What to Watch Next",
            "body": (
                "Readers should watch the next inflation releases, policy communication, energy "
                "inventory data, and Treasury yield updates. The article should monitor whether the "
                "oil channel persists for more than 6 months before treating it as a durable cycle input."
            ),
        },
    ]
    draft = {
        "title": "Oil Volatility Is Rising; Recession Risk Needs a Cleaner Evidence Map",
        "subtitle": "A source-led macro briefing on WTI, policy limits, and recession-risk evidence.",
        "slug_candidate": "oil-volatility-recession-risk-evidence-map",
        "dek": "Current WTI data help explain why oil volatility belongs in recession-risk analysis without turning one chart into a cycle call.",
        "meta_description": "Capital Chronicle maps current WTI oil volatility, recession-risk channels, source limits, and what to watch next.",
        "thesis": "Current oil volatility belongs in a recession-risk dashboard, but the thesis needs source-backed limits.",
        "intro": intro,
        "sections": sections,
        "conclusion": (
            "The evidence supports monitoring oil volatility, not treating it as a standalone recession call. "
            "What to watch next is whether energy pressure persists alongside inflation, yield, and credit data."
        ),
        "citations": [
            "https://fred.stlouisfed.org/series/DCOILWTICO",
            "https://www.eia.gov/dnav/pet/pet_pri_spt_s1_d.htm",
            "https://www.federalreserve.gov/monetarypolicy.htm",
            "https://home.treasury.gov/policy-issues/financing-the-government/interest-rate-statistics",
        ],
        "source_notes_for_operator": "FRED, EIA, Federal Reserve, and Treasury source rows support the article claims.",
        "source_trail": [
            {
                "label": "FRED DCOILWTICO",
                "publisher_or_origin": "FRED / EIA",
                "url": "https://fred.stlouisfed.org/series/DCOILWTICO",
                "claim_supported": "WTI latest observation and 90-day price comparison.",
            },
            {
                "label": "EIA petroleum prices",
                "publisher_or_origin": "U.S. Energy Information Administration",
                "url": "https://www.eia.gov/dnav/pet/pet_pri_spt_s1_d.htm",
                "claim_supported": "Underlying petroleum source for WTI spot price observations.",
            },
            {
                "label": "Federal Reserve policy context",
                "publisher_or_origin": "Federal Reserve",
                "url": "https://www.federalreserve.gov/monetarypolicy.htm",
                "claim_supported": "Policy transmission context for inflation and rates discussion.",
            },
            {
                "label": "Treasury rates context",
                "publisher_or_origin": "U.S. Treasury",
                "url": "https://home.treasury.gov/policy-issues/financing-the-government/interest-rate-statistics",
                "claim_supported": "Yield and rates context for recession-risk discussion.",
            },
        ],
    }
    return {
        "source_context_packet": {
            "operator_idea": "US recession risks rise as oil volatility spikes",
            "editorial_angle": "Focus on data transparency, geopolitics, and yield curves.",
        },
        "canonical_article_draft": draft,
        "seo_packet": {
            "target_keyword": "oil volatility recession risk",
            "meta_description": draft["meta_description"],
        },
    }


def test_blocks_irrelevant_citation_and_source_note_urls():
    packet = _clean_article_packet()
    yahoo_url = "https://finance.yahoo.com/m/c68d12c5-efbe-3987-854b-a8e2c68b8ea1/mitch-mcconnell%2C-still.html"
    packet["canonical_article_draft"]["citations"].append(yahoo_url)
    packet["canonical_article_draft"]["source_notes_for_operator"] += f" {yahoo_url}"
    packet["research_grounding_packet"] = {"cited_source_notes": yahoo_url}

    audit = audit_editorial_quality_packet(packet, topic="US recession risks rise as oil volatility spikes")

    assert audit["classification"] == EDITORIAL_BLOCKED
    assert audit["tier1_editorial_approved"] is False
    assert any(item.startswith("irrelevant_citation_urls:") for item in audit["blockers"])
    assert any(item.startswith("irrelevant_source_note_urls:") for item in audit["blockers"])


def test_clean_source_backed_article_can_be_editorial_approved():
    audit = audit_editorial_quality_packet(
        _clean_article_packet(),
        topic="US recession risks rise as oil volatility spikes",
    )

    assert audit["classification"] == EDITORIAL_APPROVED
    assert audit["tier1_editorial_approved"] is True
    assert audit["blockers"] == []
    assert audit["review_items"] == []


def test_source_diversity_and_pipeline_language_trigger_review_not_dispatch_failure():
    packet = _clean_article_packet()
    draft = packet["canonical_article_draft"]
    draft["citations"] = [
        "https://fred.stlouisfed.org/series/DCOILWTICO",
        "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DCOILWTICO",
        "https://www.eia.gov/dnav/pet/pet_pri_spt_s1_d.htm",
    ]
    draft["source_trail"] = draft["source_trail"][:2] + [
        {
            "label": "FRED DCOILWTICO downloadable observations",
            "publisher_or_origin": "FRED CSV",
            "url": "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DCOILWTICO",
            "claim_supported": "Derived 90-day and realized-volatility calculations from the WTI series.",
        }
    ]
    draft["conclusion"] += (
        " The ContentOps pipeline, operator workflow, and deterministic media audit should not appear "
        "this often in public copy."
    )
    packet["seo_packet"]["target_keyword"] = "spikes"

    audit = audit_editorial_quality_packet(packet, topic="US recession risks rise as oil volatility spikes")

    assert audit["classification"] == EDITORIAL_NEEDS_REVIEW
    assert audit["tier1_editorial_approved"] is False
    assert "seo_target_keyword_not_topic_aligned" in audit["review_items"]
    assert "source_diversity_too_narrow:2<3" in audit["review_items"]
    assert any(item.startswith("public_body_pipeline_internal_language:") for item in audit["review_items"])


def test_audit_does_not_mutate_packet():
    packet = _clean_article_packet()
    original = copy.deepcopy(packet)

    audit_editorial_quality_packet(packet, topic="US recession risks rise as oil volatility spikes")

    assert packet == original
