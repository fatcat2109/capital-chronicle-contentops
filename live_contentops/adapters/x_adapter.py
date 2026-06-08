"""Deterministic local X (Twitter) adapter dry-run and staging."""
import datetime
import uuid
import re
from typing import Dict, Any, List
from .. import policy_rules
from .. import contract_validation

def check_bearer_oauth_token(payload: Dict[str, Any]) -> bool:
    """Detect bearer, oauth, or secret keys."""
    if policy_rules.check_secret_keys(payload):
        return True

    token_pattern = re.compile(r"oauth|bearer|token|api_key|access_token|client_secret", re.IGNORECASE)
    def _search(obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if token_pattern.search(str(k)): return True
                if _search(v): return True
        elif isinstance(obj, list):
            for i in obj:
                if _search(i): return True
        elif isinstance(obj, str):
            if token_pattern.search(obj) and len(obj) > 10: return True
        return False
    return _search(payload)

def check_real_handle_or_id(val: str) -> bool:
    """Reject if looks like real handle or tweet ID unless specifically placeholder."""
    val_lower = val.lower()
    if "placeholder" in val_lower or "future_only" in val_lower:
        return False

    if re.match(r"^@[a-zA-Z0-9_]{4,15}$", val):
        return True
    if re.match(r"^[0-9]{18,20}$", val):
        return True
    return False

def validate_dry_run_request(req: Dict[str, Any]):
    if req.get("x_api_used") is True:
        raise ValueError("x_api_used cannot be true.")
    if req.get("platform_api_used") is True:
        raise ValueError("platform_api_used cannot be true.")
    if req.get("safe_for_publish") is True:
        raise ValueError("safe_for_publish cannot be true.")
    if req.get("dry_run_only") is not True:
        raise ValueError("dry_run_only must be true.")
    if req.get("staging_only") is not True:
        raise ValueError("staging_only must be true.")
    if check_bearer_oauth_token(req):
        raise ValueError("Bearer/OAuth-token-like field detected.")
    if check_real_handle_or_id(req.get("target_account_label", "")):
        raise ValueError("Real-looking handle or ID detected.")

def build_x_dry_run_request(provider_result: Dict[str, Any], queue_item: Dict[str, Any], post_mode: str = "post") -> Dict[str, Any]:
    req_id = "x_req_" + str(uuid.uuid4()).replace("-", "")

    req = {
        "request_id": req_id,
        "source_provider_result_id": provider_result.get("result_id", ""),
        "policy_decision_id": queue_item.get("source_policy_decision_id", ""),
        "approval_queue_item_id": queue_item.get("queue_item_id", ""),
        "target_account_label": "PLACEHOLDER_STAGING_ACCOUNT",
        "post_mode": post_mode,
        "message_text": provider_result.get("simulated_output_text", ""),
        "source_state": queue_item.get("source_state", ""),
        "policy_status": queue_item.get("policy_status", ""),
        "queue_status": queue_item.get("queue_status", ""),
        "dry_run_only": True,
        "staging_only": True,
        "human_approval_required": True,
        "network_used": False,
        "provider_call_used": False,
        "platform_api_used": False,
        "x_api_used": False,
        "publishing_enabled": False,
        "scheduler_enabled": False,
        "auto_approved": False,
        "live_platform_enabled": False,
        "safe_for_publish": False,
        "created_at": datetime.datetime.now().isoformat()
    }
    validate_dry_run_request(req)
    return req

def run_x_dry_run(request: Dict[str, Any]) -> Dict[str, Any]:
    validate_dry_run_request(request)

    policy_status = request.get("policy_status", "")
    queue_status = request.get("queue_status", "")

    msg = request.get("message_text", "")
    is_thread = request.get("post_mode") == "thread"

    if policy_status not in [policy_rules.PASS_REVIEW_REQUIRED, ""]:
        is_blocked = True
        preview_text = f"[LOCAL X DRY RUN ONLY] [SIMULATED POST PREVIEW] [BLOCKED] Post blocked due to policy: {policy_status}"
    elif queue_status not in ["REVIEW_REQUIRED", "APPROVED_FOR_FUTURE_DRY_RUN_ONLY", ""]:
        is_blocked = True
        preview_text = f"[LOCAL X DRY RUN ONLY] [SIMULATED POST PREVIEW] [BLOCKED] Post blocked due to queue status: {queue_status}"
    else:
        is_blocked = False
        preview_text = "[LOCAL X DRY RUN ONLY] [SIMULATED POST PREVIEW] [NOT POSTED] [NOT SCHEDULED] [NOT FINAL PUBLIC COPY] [NO X API USED] [NO LIVE LLM USED]\n\n" + msg

    result_id = "x_res_" + str(uuid.uuid4()).replace("-", "")
    char_count = len(preview_text)

    res = {
        "result_id": result_id,
        "request_id": request.get("request_id", ""),
        "platform": "x",
        "adapter_mode": "dry_run",
        "dry_run_only": True,
        "staging_only": True,
        "simulated_post_preview": preview_text,
        "character_count": char_count,
        "thread_part_count": 3 if is_thread else 1,
        "formatting_warnings": [] if char_count < 280 or is_thread else ["Message exceeds standard X length for single post"],
        "blocked_or_warning_reasons": ["Policy blocked"] if is_blocked else [],
        "staging_contract_id": "none",
        "network_used": False,
        "provider_call_used": False,
        "platform_api_used": False,
        "x_api_used": False,
        "publishing_enabled": False,
        "scheduler_enabled": False,
        "auto_approved": False,
        "safe_for_publish": False,
        "human_approval_required": True,
        "created_at": datetime.datetime.now().isoformat()
    }

    if is_thread and not is_blocked:
        res["simulated_thread_preview"] = [
            preview_text[:100] + " 1/3",
            "Part 2 mock 2/3",
            "Part 3 mock 3/3"
        ]

    validate_x_dry_run_result(res)
    return res

def validate_x_dry_run_result(result: Dict[str, Any]):
    if result.get("x_api_used") is True:
        raise ValueError("x_api_used cannot be true.")
    if result.get("platform_api_used") is True:
        raise ValueError("platform_api_used cannot be true.")
    if result.get("safe_for_publish") is True:
        raise ValueError("safe_for_publish cannot be true.")
    if check_bearer_oauth_token(result):
        raise ValueError("Bearer/OAuth-token-like field detected.")

def build_x_staging_contract() -> Dict[str, Any]:
    return {
        "contract_id": "stg_x_" + str(uuid.uuid4()).replace("-", ""),
        "platform": "x",
        "prerequisites_required": [
            "Explicit operator GO for X credentials",
            "Secret manager plan",
            "OAuth/bearer token storage outside repo",
            "Staging account identifier captured locally by operator, not invented",
            "No autonomous replies/DMs",
            "No engagement automation",
            "No scraping",
            "Dry-run pass",
            "Policy pass",
            "Approval queue pass",
            "Audit log pass",
            "Kill switch pass",
            "Rate-limit policy enforced",
            "Platform-policy review",
            "Rollback/quarantine plan",
            "Correction/delete-post handling plan",
            "Limited pilot scope",
            "Daily post cap",
            "Manual review checkpoint"
        ],
        "is_ready_for_credentials": False,
        "created_at": datetime.datetime.now().isoformat()
    }
