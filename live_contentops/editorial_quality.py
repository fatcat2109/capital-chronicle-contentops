"""Deterministic local prompt quality and style QA harness."""

import re

AUDIENCE_MODES = [
    "macro_professional",
    "quant_systematic_trader",
    "builder_ai_tooling",
    "general_finance_reader",
    "product_evaluator"
]

PLATFORMS = ["linkedin", "x", "threads", "substack"]

FORBIDDEN_CLAIMS = [
    "buy", "sell", "hold", "position sizing", "guaranteed prediction",
    "100% sure", "can't miss", "trade recommendation", "alpha strategy",
    "execution engine", "signal service", "bloomberg replacement", "ai trading bot"
]

LIMITATION_KEYWORDS = [
    "limitations", "risk", "however", "caveat", "assumption", "model bias",
    "incomplete", "unknown", "uncertainty"
]

def evaluate_quality(payload: dict) -> dict:
    """Evaluates editorial quality deterministically.
    
    Expects payload:
    {
        "text": "...",
        "platform": "linkedin",
        "audience": "macro_professional",
        "is_synthetic_demo": False
    }
    """
    text = payload.get("text", "")
    platform = payload.get("platform", "linkedin").lower()
    audience = payload.get("audience", "general_finance_reader").lower()
    is_synthetic = payload.get("is_synthetic_demo", False)

    lower_text = text.lower()
    
    # Safety Risk (highest priority)
    safety_risk = 0
    blocked_claims = []
    for claim in FORBIDDEN_CLAIMS:
        if claim in lower_text:
            safety_risk += 10
            blocked_claims.append(claim)

    # Source Discipline
    source_discipline = 10
    if "fakeurl.com" in lower_text or "invented metric" in lower_text or "source: trust me" in lower_text:
        source_discipline = 0
    
    # Limitation Visibility
    limitation_visibility = 0
    if any(k in lower_text for k in LIMITATION_KEYWORDS):
        limitation_visibility = 10
    elif len(text) > 100:
        limitation_visibility = 2 # Weak if not explicitly stated in long texts

    # Platform Fit
    platform_fit = 5
    if platform == "x":
        if len(text) <= 280 and "\n\n" not in text:
            platform_fit = 10
        elif len(text) > 280:
            platform_fit = 2 # Too long
    elif platform == "linkedin":
        if "\n\n" in text and len(text) > 50:
            platform_fit = 10 # Professional spacing
        else:
            platform_fit = 4
    elif platform == "threads":
        if len(text) < 500 and not text.isupper():
            platform_fit = 8
    elif platform == "substack":
        if len(text) > 300 and "##" in text:
            platform_fit = 10 # Structured depth
            
    # Hook Strength
    hook_strength = 5
    lines = text.strip().split('\n')
    if lines and len(lines[0]) < 80 and ("?" in lines[0] or any(str(i) in lines[0] for i in range(10))):
        hook_strength = 10
        
    # Specificity
    specificity = 5
    if any(str(i) in lower_text for i in range(10)) or "$" in lower_text or "%" in lower_text:
        specificity = 10
        
    # Repetition Risk
    repetition_risk = 0
    words = lower_text.split()
    if words:
        unique_ratio = len(set(words)) / len(words)
        if unique_ratio < 0.4 and len(words) > 20:
            repetition_risk = 10

    not_public_postable_reason = None
    if safety_risk >= 10:
        not_public_postable_reason = "Contains forbidden claims (buy/sell/guaranteed/etc)."
    elif is_synthetic:
        not_public_postable_reason = "Synthetic demo input cannot be published."
    elif source_discipline < 5:
        not_public_postable_reason = "Source discipline violation (fake URLs/metrics)."

    return {
        "score_summary": {
            "safety_risk": safety_risk,
            "hook_strength": hook_strength,
            "platform_fit": platform_fit,
            "limitation_visibility": limitation_visibility,
            "source_discipline": source_discipline,
            "specificity": specificity,
            "repetition_risk": repetition_risk
        },
        "blocked_claims_detected": blocked_claims,
        "not_public_postable_reason": not_public_postable_reason,
        "is_advisory_only": True
    }
