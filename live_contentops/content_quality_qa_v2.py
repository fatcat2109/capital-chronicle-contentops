"""V6 Content Quality QA.

Provides scoring metrics for article drafts, SEO packets, and platform variants.
"""
from __future__ import annotations

from typing import Any


def score_draft_quality(
    article_packet: dict[str, Any],
    seo_packet: dict[str, Any],
    platform_variants: dict[str, Any]
) -> dict[str, Any]:
    """Generates quality scorecard metrics without certifying publication readiness."""
    # Check if caveats are preserved
    has_disclosure = bool(article_packet.get("disclosure"))
    has_limitations = bool(article_packet.get("limitations"))
    caveat_score = 100.0 if (has_disclosure and has_limitations) else 50.0
    
    # SEO fit from seo packet or defaults
    readability = float(seo_packet.get("readability_score", 85.0))
    editorial = float(seo_packet.get("editorial_score", 90.0))
    audience = float(seo_packet.get("audience_fit_score", 95.0))
    
    # Source integrity: unverified dry-run sources yield a low integrity score to signal caution
    requires_verification = article_packet.get("draft_status") == "review_only_draft_requires_source_verification"
    source_score = 40.0 if requires_verification else 95.0
    
    # Platform compliance
    has_blockers = False
    for fam, var in platform_variants.items():
        if var.get("blocked_reasons"):
            has_blockers = True
            break
            
    platform_score = 60.0 if has_blockers else 98.0
    thread_score = 50.0 if ("segment_truncation_detected" in str(platform_variants) or "segment_length_limit_exceeded" in str(platform_variants)) else 95.0
    seo_score = 90.0 if seo_packet.get("rejected_clickbait") == [] else 70.0
    
    return {
        "readability_score": readability,
        "editorial_clarity_score": editorial,
        "audience_fit_score": audience,
        "caveat_preservation_score": caveat_score,
        "source_integrity_score": source_score,
        "platform_fit_score": platform_score,
        "thread_continuity_score": thread_score,
        "SEO_quality_score": seo_score,
        "qa_signal_status": "REVIEW_ONLY_QA_COMPLETE"
    }
