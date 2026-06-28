"""V6 Operator Intent Contract.

Defines operator intent classes, safety validation rules, and financial advice prevention wrappers.
"""
from __future__ import annotations

import re
from typing import Any

INTENT_CLASSES = [
    "create_canonical_article",
    "summarize_source",
    "create_discord_drop",
    "create_platform_variants",
    "create_product_update",
    "create_research_question_backlog",
    "inspect_draft",
    "approve_payload",
    "reject_payload",
    "request_manual_fallback",
    "request_webhook_dispatch",
    "request_audit_summary"
]


def validate_operator_intent(req: dict[str, Any]) -> dict[str, Any]:
    """Validates operator intent text and request parameters.
    
    Ensures no approval without hash, blocks ambiguous live write keywords,
    and rewrites or blocks unsafe financial advice/predictions.
    """
    intent_class = req.get("intent_class")
    intent_text = req.get("intent_text", "")
    payload_hash = req.get("payload_hash")
    
    blockers = []
    rewritten_text = intent_text
    
    if intent_class not in INTENT_CLASSES:
        blockers.append("invalid_intent_class")
        
    # Rule 1: Approval intent requires exact payload hash
    if intent_class == "approve_payload":
        if not payload_hash or len(payload_hash) < 32:
            blockers.append("operator_signature_missing")
            
    # Rule 2: Ambiguous live-write language is blocked
    live_write_keywords = ["dispatch", "publish", "post to live", "write to database", "hydrate credentials"]
    for kw in live_write_keywords:
        if kw in intent_text.lower():
            blockers.append("ambiguous_live_write_language")
            
    # Rule 3: Unsafe finance signal requests are blocked or rewritten into educational framing
    unsafe_finance_keywords = ["buy signal", "sell signal", "target price", "guaranteed return", "when to exit", "position sizing"]
    for kw in unsafe_finance_keywords:
        if kw in intent_text.lower():
            # If request allows rewriting, rewrite into educational framing
            if req.get("allow_rewrite", True):
                # Rewrite keyword to safe phrasing
                rewritten_text = re.sub(
                    rf"\b{kw}\b",
                    "historical educational context of the asset",
                    rewritten_text,
                    flags=re.IGNORECASE
                )
            else:
                blockers.append("unsafe_financial_signal_requested")
                
    # Rule 4: Community questions can become content ideas only after research grounding
    if "community asked" in intent_text.lower() or "user question" in intent_text.lower():
        if not req.get("research_grounding_complete", False):
            blockers.append("research_grounding_required_for_community_intake")
            
    return {
        "intent_class": intent_class,
        "original_intent_text": intent_text,
        "validated_intent_text": rewritten_text,
        "is_valid": len(blockers) == 0,
        "blockers": sorted(list(set(blockers)))
    }
