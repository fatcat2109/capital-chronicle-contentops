import json
from live_contentops import platform_content_generators_v6 as generators

def test_generate_platform_variants_review_only():
    article = {
        "article_id": "art_123",
        "title": "Study of Volatility",
        "subtitle": "Unverified deep dive",
        "body_markdown": "Yield movements analysis based on unverified dry-run sample data.",
        "citations": ["UNVERIFIED_SAMPLE_SOURCE_REF"],
        "limitations": "Treasury yield volatility is uncertain and parameters are limited.",
        "disclosure": "This is educational only, no recommendations are made.",
        "draft_status": "review_only_draft_requires_source_verification",
        "required_caveats": ["Source verification required"]
    }
    seo = {
        "blockers": ["source_verification_required"]
    }
    
    variants = generators.generate_variant_pack(article, seo)
    
    for fam, var in variants.items():
        assert var["source_article_id"] == "art_123"
        assert var["platform_family"] == fam
        assert var["public_postable"] is False
        assert var["dispatch_allowed_now"] is False
        assert var["approval_required"] is True
        assert var["source_verification_required"] is True
        assert "publication_blocked_until_source_verification" in var["blocked_reasons"]
        assert "source_verification_required" in var["blocked_reasons"]

def test_financial_advice_phrasing_is_blocked_in_variants():
    article = {
        "article_id": "art_123",
        "title": "Yield Buy Signal study",
        "subtitle": "Buy recommendations study",
        "body_markdown": "This study has yield buy signal text that is unsafe.",
        "citations": ["UNVERIFIED_SAMPLE_SOURCE_REF"],
        "limitations": "Treasury yield volatility is uncertain and parameters are limited.",
        "disclosure": "This is educational only, no recommendations are made.",
        "draft_status": "review_only_draft_requires_source_verification"
    }
    seo = {}
    var = generators.generate_platform_variant(article, seo, "x_manual_thread")
    assert "financial_advice_detected" in var["blocked_reasons"]

def test_stripping_limitations_or_disclosure_is_blocked():
    article = {
        "article_id": "art_123",
        "title": "Volatility Study",
        "subtitle": "Vol study",
        "body_markdown": "Yield movements analysis.",
        "citations": ["UNVERIFIED_SAMPLE_SOURCE_REF"],
        "limitations": "", # empty limitations
        "disclosure": "", # empty disclosure
        "draft_status": "review_only_draft_requires_source_verification"
    }
    seo = {}
    var = generators.generate_platform_variant(article, seo, "x_manual_thread")
    assert "limitations_must_be_preserved" in var["blocked_reasons"]
    assert "disclosure_must_be_preserved" in var["blocked_reasons"]

def test_hashes_are_sha256_and_no_stub_hashes():
    article = {
        "article_id": "art_123",
        "title": "Study of Volatility",
        "subtitle": "Unverified deep dive",
        "body_markdown": "Yield movements analysis based on unverified dry-run sample data.",
        "citations": ["UNVERIFIED_SAMPLE_SOURCE_REF"],
        "limitations": "Treasury yield volatility is uncertain and parameters are limited.",
        "disclosure": "This is educational only, no recommendations are made.",
        "draft_status": "review_only_draft_requires_source_verification"
    }
    seo = {}
    variants = generators.generate_variant_pack(article, seo)
    
    import re
    for fam, var in variants.items():
        for s in var["segments"]:
            assert s["segment_hash"] != "stub_hash_value"
            assert isinstance(s["segment_hash"], str)
            assert re.match(r"^[0-9a-f]{64}$", s["segment_hash"])
            
def test_repeated_generation_is_stable():
    article = {
        "article_id": "art_123",
        "title": "Study of Volatility",
        "subtitle": "Unverified deep dive",
        "body_markdown": "Yield movements analysis based on unverified dry-run sample data.",
        "citations": ["UNVERIFIED_SAMPLE_SOURCE_REF"],
        "limitations": "Treasury yield volatility is uncertain and parameters are limited.",
        "disclosure": "This is educational only, no recommendations are made.",
        "draft_status": "review_only_draft_requires_source_verification"
    }
    seo = {}
    v1 = generators.generate_platform_variant(article, seo, "x_manual_thread")
    v2 = generators.generate_platform_variant(article, seo, "x_manual_thread")
    
    assert v1["segments"][0]["segment_hash"] == v2["segments"][0]["segment_hash"]

def test_non_threaded_platform_limits_are_blocked():
    # Set text that exceeds Threads max limit but Threads doesn't support threading or does support it?
    # X/manual thread supports threading. Let's use Instagram manual caption (limit 2200).
    article = {
        "article_id": "art_123",
        "title": "Volatility study",
        "subtitle": "Vol study",
        "body_markdown": "A" * 3000, # exceeds limit
        "citations": ["UNVERIFIED_SAMPLE_SOURCE_REF"],
        "limitations": "Treasury yield volatility is uncertain and parameters are limited.",
        "disclosure": "This is educational only, no recommendations are made.",
        "draft_status": "review_only_draft_requires_source_verification"
    }
    seo = {}
    # Discord drop doesn't support threading or continuation comment
    var = generators.generate_platform_variant(article, seo, "discord_drop")
    assert "platform_does_not_support_continuation_segmentation" in var["blocked_reasons"]

