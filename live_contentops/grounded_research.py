import uuid
from typing import List, Dict

SOURCE_TYPES = [
    "official", "media", "platform_observation", "manual_note",
    "vendor_tool_snapshot", "internal_artifact", "synthetic_fixture"
]

def generate_research_context(req: dict) -> dict:
    """Generate a deterministic grounded research context."""
    source_items = req.get("source_items", [])
    
    # Process sources to enforce contract
    processed_sources = []
    for s in source_items:
        is_synthetic = s.get("synthetic_fixture", True)
        processed_sources.append({
            "source_id": s.get("source_id", f"src_{uuid.uuid4().hex[:8]}"),
            "title": s.get("title", "Untitled Source"),
            "publisher_or_origin": s.get("publisher_or_origin", "Unknown"),
            "url_or_local_reference": s.get("url_or_local_reference", ""),
            "source_type": s.get("source_type", "synthetic_fixture"),
            "retrieved_at": s.get("retrieved_at", "DETERMINISTIC_TIMESTAMP"),
            "freshness_label": s.get("freshness_label", "unknown"),
            "claim_summary": s.get("claim_summary", ""),
            "allowed_usage": s.get("allowed_usage", "advisory_only"),
            "limitations": s.get("limitations", ["Synthetic source - not for live use"] if is_synthetic else []),
            "citation_required": s.get("citation_required", True),
            "synthetic_fixture": is_synthetic
        })

    has_synthetic = any(s["synthetic_fixture"] for s in processed_sources)
    
    is_current_events = req.get("is_current_events", False)
    warnings = []
    blockers = []
    
    if is_current_events and not processed_sources:
        warnings.append("Current event topic lacks grounded research context.")
        blockers.append("Cannot post current events without source citations.")
        
    search_performed = req.get("search_performed", False) or any(not s["synthetic_fixture"] for s in processed_sources)
    advisory_only = has_synthetic or req.get("advisory_only", True)

    return {
        "research_context_id": f"res_{uuid.uuid4().hex[:8]}",
        "topic": req.get("topic", "Unknown"),
        "content_type": req.get("content_type", "post"),
        "intended_platforms": req.get("intended_platforms", []),
        "query_set": req.get("query_set", []),
        "generated_at": "DETERMINISTIC_TIMESTAMP",
        "freshness_window": req.get("freshness_window", "24h"),
        "source_items": processed_sources,
        "current_news_summary": req.get("current_news_summary", ""),
        "platform_meta_observations": req.get("platform_meta_observations", []),
        "audience_language_observations": req.get("audience_language_observations", []),
        "claims_allowed": req.get("claims_allowed", []),
        "claims_blocked": req.get("claims_blocked", []),
        "caveats": req.get("caveats", []),
        "cost_budget_notes": "Search once per content packet, cache current-news for short windows, cache evergreen longer.",
        "provider_or_tool_provenance": "local_deterministic_fixture" if not search_performed else "live_search_engine",
        "search_performed": search_performed,
        "advisory_only": advisory_only,
        "not_public_postable_reason": "Contains synthetic research fixture data" if has_synthetic else None,
        "warnings": warnings,
        "blockers": blockers
    }
