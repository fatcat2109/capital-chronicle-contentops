"""Deterministic local provider gateway simulator."""
import datetime
import uuid
from typing import Dict, Any, List
from . import policy_rules
from . import contract_validation

# Provider Registry Constants
OPENAI_FUTURE_ONLY = "OPENAI_FUTURE_ONLY"
ANTHROPIC_FUTURE_ONLY = "ANTHROPIC_FUTURE_ONLY"
AZURE_OPENAI_FUTURE_ONLY = "AZURE_OPENAI_FUTURE_ONLY"
LOCAL_MODEL_FUTURE_ONLY = "LOCAL_MODEL_FUTURE_ONLY"
DRY_RUN_SIMULATOR = "DRY_RUN_SIMULATOR"

PROVIDER_STATUS = {
    OPENAI_FUTURE_ONLY: {"status": "FUTURE_ONLY", "disabled": True, "no_key": True, "no_network": True},
    ANTHROPIC_FUTURE_ONLY: {"status": "FUTURE_ONLY", "disabled": True, "no_key": True, "no_network": True},
    AZURE_OPENAI_FUTURE_ONLY: {"status": "FUTURE_ONLY", "disabled": True, "no_key": True, "no_network": True},
    LOCAL_MODEL_FUTURE_ONLY: {"status": "FUTURE_ONLY", "disabled": True, "no_key": True, "no_network": True},
    DRY_RUN_SIMULATOR: {"status": "SIMULATOR_ONLY", "disabled": False, "no_key": True, "no_network": True}
}

def validate_dry_run_request(req: Dict[str, Any]):
    if req.get("requested_provider") != DRY_RUN_SIMULATOR:
        raise ValueError("Only DRY_RUN_SIMULATOR is currently permitted.")
    if req.get("network_used") is True:
        raise ValueError("network_used cannot be true.")
    if req.get("provider_call_used") is True:
        raise ValueError("provider_call_used cannot be true.")
    if req.get("platform_api_used") is True:
        raise ValueError("platform_api_used cannot be true.")
    if req.get("publishing_enabled") is True:
        raise ValueError("publishing_enabled cannot be true.")
    if req.get("safe_for_publish") is True:
        raise ValueError("safe_for_publish cannot be true.")
    if req.get("dry_run_only") is not True:
        raise ValueError("dry_run_only must be true.")
    if policy_rules.check_secret_keys(req):
        raise ValueError("Secret-like field detected.")

def build_provider_dry_run_request(payload: Dict[str, Any], queue_item: Dict[str, Any] = None) -> Dict[str, Any]:
    req_id = "req_" + str(uuid.uuid4()).replace("-", "")

    req = {
        "request_id": req_id,
        "prompt_contract_id": payload.get("prompt_contract_id", ""),
        "source_payload_id": payload.get("id", ""),
        "policy_decision_id": queue_item.get("source_policy_decision_id", "") if queue_item else "",
        "approval_queue_item_id": queue_item.get("queue_item_id", "") if queue_item else "",
        "requested_provider": DRY_RUN_SIMULATOR,
        "requested_model": "local-sim",
        "dry_run_mode": True,
        "prompt_text": payload.get("prompt_text", ""),
        "source_state": queue_item.get("source_state", "none") if queue_item else "none",
        "risk_flags": queue_item.get("risk_flags", []) if queue_item else [],
        "human_approval_required": True,
        "policy_status": queue_item.get("policy_status", "") if queue_item else "",
        "queue_status": queue_item.get("queue_status", "") if queue_item else "",
        "network_used": False,
        "provider_call_used": False,
        "platform_api_used": False,
        "publishing_enabled": False,
        "scheduler_enabled": False,
        "auto_approved": False,
        "live_provider_enabled": False,
        "dry_run_only": True,
        "created_at": datetime.datetime.now().isoformat()
    }
    validate_dry_run_request(req)
    return req

def run_provider_dry_run(request: Dict[str, Any]) -> Dict[str, Any]:
    validate_dry_run_request(request)

    # Preconditions check
    policy_status = request.get("policy_status", "")
    queue_status = request.get("queue_status", "")

    if policy_status not in [policy_rules.PASS_REVIEW_REQUIRED, ""]:
        # Blocked or Source Required
        is_blocked = True
        blocked_reasons = [f"Policy status is {policy_status}"]
        simulated_text = "[LOCAL PROVIDER DRY RUN ONLY] [SIMULATED OUTPUT] [BLOCKED] Output generation blocked due to policy/source state."
    elif queue_status not in ["REVIEW_REQUIRED", "APPROVED_FOR_FUTURE_DRY_RUN_ONLY", ""]:
        is_blocked = True
        blocked_reasons = [f"Queue status is {queue_status}"]
        simulated_text = "[LOCAL PROVIDER DRY RUN ONLY] [SIMULATED OUTPUT] [BLOCKED] Output generation blocked due to queue state."
    else:
        is_blocked = False
        blocked_reasons = []
        simulated_text = "[LOCAL PROVIDER DRY RUN ONLY] [SIMULATED OUTPUT] [NOT FINAL COPY] [NOT APPROVED] [NOT POSTED] [NO LIVE LLM USED] This is a safe candidate outline."

    result_id = "res_" + str(uuid.uuid4()).replace("-", "")

    res = {
        "result_id": result_id,
        "request_id": request.get("request_id", ""),
        "provider_name": request.get("requested_provider", DRY_RUN_SIMULATOR),
        "model_name": request.get("requested_model", "local-sim"),
        "dry_run_only": True,
        "simulated_output_text": simulated_text,
        "candidate_outputs": [{"text": simulated_text}] if not is_blocked else [],
        "safety_echo": "Acknowledged and enforced local safe bounds.",
        "blocked_or_warning_reasons": blocked_reasons,
        "token_estimate": 150,
        "cost_estimate_usd": 0.0,
        "latency_ms_estimate": 5,
        "network_used": False,
        "provider_call_used": False,
        "platform_api_used": False,
        "publishing_enabled": False,
        "scheduler_enabled": False,
        "auto_approved": False,
        "safe_for_publish": False,
        "human_approval_required": True,
        "created_at": datetime.datetime.now().isoformat()
    }
    validate_provider_dry_run_result(res)
    return res

def validate_provider_dry_run_result(result: Dict[str, Any]):
    if result.get("safe_for_publish") is True:
        raise ValueError("safe_for_publish cannot be true.")
    if result.get("provider_call_used") is True:
        raise ValueError("provider_call_used cannot be true.")
    if result.get("network_used") is True:
        raise ValueError("network_used cannot be true.")
    if policy_rules.check_secret_keys(result):
        raise ValueError("Secret-like field detected.")
