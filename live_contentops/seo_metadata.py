import uuid

def generate_seo_metadata_pack(req: dict, context: dict = None) -> dict:
    """Generate SEO and hashtag metadata for a given content packet."""
    
    keywords = req.get("suggested_keywords", [])
    hashtags = req.get("suggested_hashtags", [])
    
    warnings = []
    blockers = []
    
    # Financial advice / trading signal checks on keywords and hashtags
    blocked_terms = ["buy", "sell", "execution", "guaranteed", "alpha", "signal", "order routing", "bloomberg replacement"]
    for term in keywords + hashtags:
        term_lower = term.lower()
        if any(b in term_lower for b in blocked_terms):
            blockers.append(f"Blocked term found in SEO metadata: {term}")

    is_synthetic = req.get("is_synthetic", True)

    return {
        "metadata_pack_id": f"seo_{uuid.uuid4().hex[:8]}",
        "topic": req.get("topic", "Unknown"),
        "platform": req.get("platform", "Unknown"),
        "content_type": req.get("content_type", "post"),
        "suggested_keywords": keywords,
        "suggested_hashtags": hashtags,
        "search_intent": req.get("search_intent", ""),
        "audience_terms": req.get("audience_terms", []),
        "title_angles": req.get("title_angles", []),
        "hook_angles": req.get("hook_angles", []),
        "banned_or_risky_terms": blocked_terms,
        "source_requirements": req.get("source_requirements", "Citation required for any claims"),
        "freshness_requirements": req.get("freshness_requirements", "Latest 24h data"),
        "not_public_postable_reason": "Synthetic metadata fixture" if is_synthetic else None,
        "advisory_only": True,
        "warnings": warnings,
        "blockers": blockers
    }
