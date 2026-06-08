"""Policy rules definitions."""
from typing import List, Dict, Any
import re

# Allowed Statuses
PASS_REVIEW_REQUIRED = "PASS_REVIEW_REQUIRED"
BLOCKED_SOURCE_REQUIRED = "BLOCKED_SOURCE_REQUIRED"
BLOCKED_FORBIDDEN_FINANCIAL_ADVICE = "BLOCKED_FORBIDDEN_FINANCIAL_ADVICE"
BLOCKED_POSITION_SIZING = "BLOCKED_POSITION_SIZING"
BLOCKED_GUARANTEED_PREDICTION = "BLOCKED_GUARANTEED_PREDICTION"
BLOCKED_BROKER_OR_EXECUTION = "BLOCKED_BROKER_OR_EXECUTION"
BLOCKED_PARTISAN_PERSUASION = "BLOCKED_PARTISAN_PERSUASION"
BLOCKED_ELECTION_GUIDANCE = "BLOCKED_ELECTION_GUIDANCE"
BLOCKED_CONFIDENT_MARKET_FORECAST = "BLOCKED_CONFIDENT_MARKET_FORECAST"
BLOCKED_UNSUPPORTED_CURRENT_EVENT = "BLOCKED_UNSUPPORTED_CURRENT_EVENT"
BLOCKED_SECRET_OR_CREDENTIAL = "BLOCKED_SECRET_OR_CREDENTIAL"
BLOCKED_AUTONOMOUS_REPLY_OR_DM = "BLOCKED_AUTONOMOUS_REPLY_OR_DM"
BLOCKED_AUTO_PUBLISH_REQUEST = "BLOCKED_AUTO_PUBLISH_REQUEST"
BLOCKED_PLATFORM_ACTION_DISABLED = "BLOCKED_PLATFORM_ACTION_DISABLED"
BLOCKED_POLICY_CONFLICT = "BLOCKED_POLICY_CONFLICT"
BLOCKED_UNKNOWN_RISK = "BLOCKED_UNKNOWN_RISK"
BLOCKED_LIVE_FLAGS_TRUE = "BLOCKED_LIVE_FLAGS_TRUE"

# Source-state requirements
REQUIRES_SOURCE_BUNDLE = {"source_required", "current_topic", "timely_sourced", "conditional_reaction", "blocked_until_source"}

# Rule Lists
FINANCIAL_ADVICE_PATTERNS = ["buy", "sell", "hold"]
POSITION_SIZING_PATTERNS = ["position sizing", "allocation amount"]
GUARANTEED_PREDICTION_PATTERNS = ["guaranteed prediction", "will definitely"]
BROKER_EXECUTION_PATTERNS = ["broker", "execution", "order"]
MARKET_FORECAST_PATTERNS = ["confident market forecast"]

PARTISAN_PATTERNS = ["partisan persuasion", "vote for", "vote against"]
ELECTION_GUIDANCE_PATTERNS = ["election guidance", "campaign-like"]

LIVE_ACTION_PATTERNS = ["auto-publish", "publish_now", "schedule_now", "send_now", "autonomous reply", "dm automation"]

SECRET_KEYS = ["api_key", "access_token", "client_secret", "password", "bearer", "refresh_token", "private_key"]
LIVE_FLAGS = ["network_used", "provider_call_used", "platform_api_used", "publishing_enabled", "scheduler_enabled", "auto_approved"]

def check_secret_keys(payload: Dict[str, Any]) -> bool:
    """Recursively check for secret-like keys or values in payload."""
    if isinstance(payload, dict):
        for k, v in payload.items():
            if isinstance(k, str) and any(s in k.lower() for s in SECRET_KEYS):
                return True
            if isinstance(v, str) and any(s in v.lower() for s in SECRET_KEYS):
                return True
            if check_secret_keys(v):
                return True
    elif isinstance(payload, list):
        for item in payload:
            if check_secret_keys(item):
                return True
    return False

def check_live_flags(payload: Dict[str, Any]) -> bool:
    """Check if any live flags are explicitly True."""
    if isinstance(payload, dict):
        for k, v in payload.items():
            if isinstance(k, str) and k in LIVE_FLAGS and v is True:
                return True
    return False

def text_contains_any(text: str, patterns: List[str]) -> bool:
    if not text:
        return False
    text = text.lower()
    return any(p.lower() in text for p in patterns)
