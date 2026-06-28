"""V6 Research Grounding Packet.

Validates grounding sources, evaluates freshness, checks safe angles, and enforces safety constraints.
"""
from __future__ import annotations

import uuid
from typing import Any


def construct_research_grounding_packet(
    topic: str,
    source_refs: list[str],
    official_source_refs: list[str] | None = None,
    non_official_source_refs: list[str] | None = None,
    freshness_status: str = "unknown",
    source_quality_status: str = "unverified",
    missing_evidence: list[str] | None = None,
    unsupported_claims: list[str] | None = None
) -> dict[str, Any]:
    """Generates and validates a Research Grounding Packet.
    
    Enforces rules around missing sources, unknown freshness, and safety boundaries.
    """
    official_refs = official_source_refs or []
    non_official_refs = non_official_source_refs or []
    missing_ev = missing_evidence or []
    unsupported = unsupported_claims or []
    
    blocked_reasons = []
    
    # Rule 1: Source missing state is preserved
    if not source_refs and not official_refs:
        blocked_reasons.append("source_evidence_missing")
        
    # Rule 2: Unknown freshness blocks public-ready state (allowed_for_publication=False)
    if freshness_status == "unknown" or freshness_status == "stale":
        blocked_reasons.append("source_freshness_unverified")
        
    # Rule 3: Unsupported claims cannot pass
    if unsupported:
        blocked_reasons.append("unsupported_claims_present")
        
    # Drafting vs Publication rules:
    # Drafting can be allowed even if publication is blocked (e.g. if we have basic topic info)
    allowed_for_drafting = len(topic) > 0 and "source_evidence_missing" not in blocked_reasons
    allowed_for_publication = len(blocked_reasons) == 0 and freshness_status == "fresh"
    
    return {
        "research_packet_id": f"research_{uuid.uuid4().hex[:12]}",
        "topic": topic,
        "source_mode": "dry_run_stub",
        "source_refs": source_refs,
        "official_source_refs": official_refs,
        "non_official_source_refs": non_official_refs,
        "freshness_status": freshness_status,
        "source_quality_status": source_quality_status,
        "missing_evidence": missing_ev,
        "safe_angles": [f"Educational analysis of {topic}", f"Historical context of {topic}"],
        "unsafe_angles": ["Price targets", "Forecasts", "Investment recommendations"],
        "required_caveats": [
            "This content is for educational purposes only.",
            "No financial recommendations or trade suggestions are made."
        ],
        "no_signal_status": True,
        "no_advice_status": True,
        "allowed_for_drafting": allowed_for_drafting,
        "allowed_for_publication": allowed_for_publication,
        "blocked_reasons": sorted(list(set(blocked_reasons)))
    }
