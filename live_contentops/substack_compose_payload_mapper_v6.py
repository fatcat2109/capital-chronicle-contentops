"""V6 Substack Compose Payload Mapper.

Maps canonical Substack fields into compose payload previews and checks policies.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "6.0.0"


def map_canonical_to_preview(
    contract_packet: dict[str, Any]
) -> dict[str, Any]:
    """Extracts canonical article parameters and maps them into compose preview schema."""
    canonical_article = contract_packet.get("canonical_article", {})
    seo_packet = contract_packet.get("seo_packet", {})
    hash_manifest = contract_packet.get("hash_manifest", {})
    
    title = canonical_article.get("title", "Stub Title")
    subtitle = canonical_article.get("subtitle", "Stub Subtitle")
    body_markdown = canonical_article.get("body_markdown", "Stub Body")
    limitations = canonical_article.get("limitations", "No limits.")
    disclosure = canonical_article.get("disclosure", "No disclosure.")
    citations = canonical_article.get("citations", ["UNVERIFIED_SAMPLE_SOURCE_REF"])
    seo_desc = seo_packet.get("seo_meta_description", "SEO Description Stub")
    
    # Create simple slug from title
    slug = "-".join(title.lower().split()[:5])
    
    return {
        "schema_version": SCHEMA_VERSION,
        "title": title,
        "subtitle": subtitle,
        "slug_candidate": slug,
        "body_markdown": body_markdown,
        "limitations": limitations,
        "disclosure": disclosure,
        "citations": citations,
        "seo_meta_description": seo_desc,
        "payload_hash": hash_manifest.get("canonical_article_hash", "unhashed"),
        "source_verification_required": True,
        "human_review_required": True,
        "review_only": True,
        "allowed_for_publication": False,
        "public_postable": False,
        "dispatch_allowed_now": False
    }


def validate_compose_payload(
    preview_data: dict[str, Any]
) -> dict[str, Any]:
    """Performs validation checks against Substack compose payload values."""
    blockers = []
    
    # Check for empty body/title
    if not preview_data.get("title") or preview_data["title"] == "Stub Title":
        blockers.append("empty_or_stub_title")
    if not preview_data.get("body_markdown") or preview_data["body_markdown"] == "Stub Body":
        blockers.append("empty_or_stub_body")
        
    # Check for placeholder citations
    if "UNVERIFIED_SAMPLE_SOURCE_REF" in preview_data.get("citations", []):
        blockers.append("source_verification_required")
        blockers.append("publication_blocked_until_source_verification")
        
    # Protect against financial keywords (e.g. signal-service framing)
    advice_triggers = ["buy stock", "sell stock", "guaranteed returns", "trade setup"]
    body_lower = preview_data.get("body_markdown", "").lower()
    for trigger in advice_triggers:
        if trigger in body_lower:
            blockers.append("unsafe_financial_advice_phrase_detected")
            
    validation_passed = len(blockers) == 0
    
    return {
        "schema_version": SCHEMA_VERSION,
        "validation_passed": validation_passed,
        "blocker_count": len(blockers),
        "blockers": sorted(list(set(blockers)))
    }
