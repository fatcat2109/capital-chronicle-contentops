"""V6 Canonical Substack Article Workflow.

Validates canonical articles, enforces disclosure and citation rules, and ensures
no financial advice or forecasting authority claims exist.
"""
from __future__ import annotations

import uuid
from typing import Any


def create_canonical_article(
    research_packet: dict[str, Any],
    title: str,
    subtitle: str,
    body_markdown: str,
    citations: list[str],
    limitations: str,
    disclosure: str = "This document is for educational purposes only. No financial recommendations are made."
) -> dict[str, Any]:
    """Drafts and validates a Canonical Substack Article.
    
    Enforces review-only status, citation integrity, limitations presence, and financial safety boundaries.
    """
    article_id = f"article_{uuid.uuid4().hex[:12]}"
    
    blockers = []
    
    # Rule 1: Limitations section is required
    if not limitations or len(limitations.strip()) < 10:
        blockers.append("limitations_section_required")
        
    # Rule 2: Citation placeholders cannot be fake IDs
    # Citations must reference actual source refs in the research packet
    valid_source_refs = set(research_packet.get("source_refs", []) + research_packet.get("official_source_refs", []))
    for cit in citations:
        if cit not in valid_source_refs:
            blockers.append(f"invalid_citation_reference:{cit}")
            
    # Rule 3: Preserves source uncertainty (must be mentioned in limitations)
    if "uncertain" not in limitations.lower() and "caveat" not in limitations.lower() and "limit" not in limitations.lower():
        blockers.append("source_uncertainty_must_be_preserved")
        
    # Rule 4: No financial advice or forecast authority claims in body
    financial_advice_keywords = ["buy", "sell", "guaranteed profit", "price target", "investment advisory"]
    for kw in financial_advice_keywords:
        if kw in body_markdown.lower() or kw in title.lower():
            blockers.append("financial_advice_detected")
            
    draft_status = "review_only" if blockers else "draft_completed"
    
    return {
        "article_id": article_id,
        "research_packet_id": research_packet.get("research_packet_id"),
        "title": title,
        "subtitle": subtitle,
        "slug_candidate": title.lower().replace(" ", "-").replace("?", "").replace("!", "")[:50],
        "lede": subtitle,
        "body_markdown": body_markdown,
        "section_map": {
            "introduction": title,
            "analysis": "historical observations only",
            "limitations": limitations
        },
        "citations": citations,
        "limitations": limitations,
        "disclosure": disclosure,
        "media_request": {
            "media_type": "chart_concept",
            "description": f"Historical chart concept related to {title}"
        },
        "seo_packet_id": None,
        "draft_status": draft_status,
        "human_review_required": True,
        "blockers": sorted(list(set(blockers)))
    }
