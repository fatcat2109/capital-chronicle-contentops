"""Deterministic live policy engine."""
from typing import Dict, Any, List
import datetime
from . import policy_rules
from .contracts import PolicyDecision, PlaneOwner, NetworkReach

def evaluate_policy(payload: Dict[str, Any], target_id: str = "unknown") -> Dict[str, Any]:
    """Evaluates a payload and returns a deterministic PolicyDecision dict."""

    status = policy_rules.PASS_REVIEW_REQUIRED
    block_reasons = []
    review_reasons = ["Content requires human review"]

    # Check secrets
    if policy_rules.check_secret_keys(payload):
        status = policy_rules.BLOCKED_SECRET_OR_CREDENTIAL
        block_reasons.append("Secret-like key or value detected")

    # Check live flags
    if policy_rules.check_live_flags(payload):
        status = policy_rules.BLOCKED_LIVE_FLAGS_TRUE
        block_reasons.append("Live capability flag is set to true")

    # Source requirements
    source_state = payload.get("source_state")
    if source_state in policy_rules.REQUIRES_SOURCE_BUNDLE:
        source_ids = payload.get("source_bundle_ids")
        if not source_ids:
            status = policy_rules.BLOCKED_SOURCE_REQUIRED
            block_reasons.append(f"source_state '{source_state}' requires non-empty source_bundle_ids")

    # Text analysis
    text = str(payload.get("text", "")).lower() + " " + str(payload.get("system_instruction", "")).lower() + " " + str(payload.get("user_context", "")).lower()

    if policy_rules.text_contains_any(text, policy_rules.FINANCIAL_ADVICE_PATTERNS):
        status = policy_rules.BLOCKED_FORBIDDEN_FINANCIAL_ADVICE
        block_reasons.append("Contains forbidden financial advice instructions")
    elif policy_rules.text_contains_any(text, policy_rules.POSITION_SIZING_PATTERNS):
        status = policy_rules.BLOCKED_POSITION_SIZING
        block_reasons.append("Contains position sizing or allocation guidance")
    elif policy_rules.text_contains_any(text, policy_rules.GUARANTEED_PREDICTION_PATTERNS):
        status = policy_rules.BLOCKED_GUARANTEED_PREDICTION
        block_reasons.append("Contains guaranteed predictions")
    elif policy_rules.text_contains_any(text, policy_rules.BROKER_EXECUTION_PATTERNS):
        status = policy_rules.BLOCKED_BROKER_OR_EXECUTION
        block_reasons.append("Contains broker or execution language")
    elif policy_rules.text_contains_any(text, policy_rules.MARKET_FORECAST_PATTERNS):
        status = policy_rules.BLOCKED_CONFIDENT_MARKET_FORECAST
        block_reasons.append("Contains confident market forecast")

    if policy_rules.text_contains_any(text, policy_rules.PARTISAN_PATTERNS):
        status = policy_rules.BLOCKED_PARTISAN_PERSUASION
        block_reasons.append("Contains partisan persuasion")
    elif policy_rules.text_contains_any(text, policy_rules.ELECTION_GUIDANCE_PATTERNS):
        status = policy_rules.BLOCKED_ELECTION_GUIDANCE
        block_reasons.append("Contains election guidance")

    if policy_rules.text_contains_any(text, policy_rules.LIVE_ACTION_PATTERNS):
        status = policy_rules.BLOCKED_AUTO_PUBLISH_REQUEST
        block_reasons.append("Contains live action or auto-publish request")

    is_blocked = status != policy_rules.PASS_REVIEW_REQUIRED

    decision = PolicyDecision(
        decision_id="dec_" + str(datetime.datetime.now().timestamp()).replace(".", ""),
        target_id=target_id,
        policy_version="1.0.0",
        status=status,
    )

    # We will expand PolicyDecision dict with additional output fields as requested
    decision_dict = decision.to_dict()
    decision_dict.update({
        "severity": "high" if is_blocked else "info",
        "risk_flags": ["blocked"] if is_blocked else [],
        "block_reasons": block_reasons,
        "review_reasons": [] if is_blocked else review_reasons,
        "source_requirements": source_state,
        "required_human_actions": ["Review"] if not is_blocked else [],
        "safe_to_continue_to_human_review": not is_blocked,
        "safe_for_provider_generation": False,
        "safe_for_adapter_dry_run": False,
        "safe_for_publish": False,
        "plane_owner": PlaneOwner.CONTROL_PLANE.value,
        "network_reach": NetworkReach.NO_NETWORK.value,
        "created_at": datetime.datetime.now().isoformat()
    })

    return decision_dict
