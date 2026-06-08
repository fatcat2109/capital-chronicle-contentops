"""Deterministic policy engine placeholder."""
from typing import Dict, Any

FORBIDDEN_STRINGS = [
    "buy", "sell", "hold", "position sizing", "guaranteed prediction",
    "vote for", "partisan", "auto-publish"
]

def evaluate_policy(payload: Dict[str, Any]) -> str:
    """Return 'blocked' or 'review_required'."""
    source_state = payload.get("source_state")
    if source_state == "source_required" and not payload.get("source_bundle_ids"):
        return "blocked"
    
    text = str(payload.get("text", "")).lower()
    for f in FORBIDDEN_STRINGS:
        if f in text:
            return "blocked"
            
    return "review_required"
