from live_contentops import content_quality_qa_v2 as quality_qa

def test_score_draft_quality():
    article = {
        "article_id": "art_123",
        "title": "Study of Volatility",
        "subtitle": "Unverified deep dive",
        "body_markdown": "Treasury yields observations.",
        "citations": ["UNVERIFIED_SAMPLE_SOURCE_REF"],
        "limitations": "Limit notes.",
        "disclosure": "Disclosure notes.",
        "draft_status": "review_only_draft_requires_source_verification"
    }
    seo = {
        "readability_score": 85.0,
        "editorial_score": 90.0,
        "audience_fit_score": 95.0,
        "rejected_clickbait": []
    }
    variants = {
        "substack_canonical": {
            "variant_id": "var_1",
            "blocked_reasons": ["publication_blocked_until_source_verification"]
        }
    }
    
    scorecard = quality_qa.score_draft_quality(article, seo, variants)
    assert scorecard["readability_score"] == 85.0
    assert scorecard["caveat_preservation_score"] == 100.0
    assert scorecard["source_integrity_score"] == 40.0 # unverified
    assert scorecard["platform_fit_score"] == 60.0 # has blockers
