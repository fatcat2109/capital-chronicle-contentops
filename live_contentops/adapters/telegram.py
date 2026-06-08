"""Deterministic local Telegram adapter dry-run and staging."""
import datetime
import uuid
from typing import Dict, Any, List
import re
from .. import policy_rules
from .. import contract_validation

def check_bot_token(payload: Dict[str, Any]) -> bool:
    """Detect bot tokens or secret keys."""
    if policy_rules.check_secret_keys(payload):
        return True

    bot_token_pattern = re.compile(r"bot_token|[0-9]{8,10}:[a-zA-Z0-9_-]{35,}")
    def _search(obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if bot_token_pattern.search(str(k)): return True
                if _search(v): return True
        elif isinstance(obj, list):
            for i in obj:
                if _search(i): return True
        elif isinstance(obj, str):
            if bot_token_pattern.search(obj): return True
        return False
    return _search(payload)

def check_real_chat_id(val: str) -> bool:
    """Reject if looks like real chat ID unless specifically placeholder."""
    val_lower = val.lower()
    if "placeholder" in val_lower or "future_only" in val_lower:
        return False

    if val.startswith("-100") and len(val) >= 10:
        return True
    if re.match(r"^@?[a-zA-Z0-9_]{5,32}$", val):
        return True
    return False

def validate_dry_run_request(req: Dict[str, Any]):
    if req.get("telegram_api_used") is True:
        raise ValueError("telegram_api_used cannot be true.")
    if req.get("platform_api_used") is True:
        raise ValueError("platform_api_used cannot be true.")
    if req.get("safe_for_publish") is True:
        raise ValueError("safe_for_publish cannot be true.")
    if req.get("dry_run_only") is not True:
        raise ValueError("dry_run_only must be true.")
    if req.get("staging_only") is not True:
        raise ValueError("staging_only must be true.")
    if check_bot_token(req):
        raise ValueError("Bot-token-like field detected.")
    if check_real_chat_id(req.get("target_channel_label", "")):
        raise ValueError("Real-looking chat_id detected.")

def build_telegram_dry_run_request(provider_result: Dict[str, Any], queue_item: Dict[str, Any]) -> Dict[str, Any]:
    req_id = "t_req_" + str(uuid.uuid4()).replace("-", "")

    req = {
        "request_id": req_id,
        "source_provider_result_id": provider_result.get("result_id", ""),
        "policy_decision_id": queue_item.get("source_policy_decision_id", ""),
        "approval_queue_item_id": queue_item.get("queue_item_id", ""),
        "target_channel_label": "PLACEHOLDER_STAGING_CHANNEL",
        "message_mode": "dry_run",
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
        "telegram_api_used": False,
        "publishing_enabled": False,
        "scheduler_enabled": False,
        "auto_approved": False,
        "live_platform_enabled": False,
        "safe_for_publish": False,
        "created_at": datetime.datetime.now().isoformat()
    }
    validate_dry_run_request(req)
    return req

def run_telegram_dry_run(request: Dict[str, Any]) -> Dict[str, Any]:
    validate_dry_run_request(request)

    policy_status = request.get("policy_status", "")
    queue_status = request.get("queue_status", "")

    if policy_status not in [policy_rules.PASS_REVIEW_REQUIRED, ""]:
        is_blocked = True
        preview_text = f"[LOCAL TELEGRAM DRY RUN ONLY] [SIMULATED MESSAGE PREVIEW] [BLOCKED] Message blocked due to policy: {policy_status}"
    elif queue_status not in ["REVIEW_REQUIRED", "APPROVED_FOR_FUTURE_DRY_RUN_ONLY", ""]:
        is_blocked = True
        preview_text = f"[LOCAL TELEGRAM DRY RUN ONLY] [SIMULATED MESSAGE PREVIEW] [BLOCKED] Message blocked due to queue status: {queue_status}"
    else:
        is_blocked = False
        preview_text = "[LOCAL TELEGRAM DRY RUN ONLY] [SIMULATED MESSAGE PREVIEW] [NOT SENT] [NOT SCHEDULED] [NOT FINAL PUBLIC COPY] [NO TELEGRAM API USED] [NO LIVE LLM USED]\\n\\n" + request.get("message_text", "")

    result_id = "t_res_" + str(uuid.uuid4()).replace("-", "")

    res = {
        "result_id": result_id,
        "request_id": request.get("request_id", ""),
        "platform": "telegram",
        "adapter_mode": "dry_run",
        "dry_run_only": True,
        "staging_only": True,
        "simulated_message_preview": preview_text,
        "message_character_count": len(preview_text),
        "formatting_warnings": [] if len(preview_text) < 4096 else ["Message exceeds standard Telegram length"],
        "blocked_or_warning_reasons": ["Policy blocked"] if is_blocked else [],
        "staging_contract_id": "none",
        "network_used": False,
        "provider_call_used": False,
        "platform_api_used": False,
        "telegram_api_used": False,
        "publishing_enabled": False,
        "scheduler_enabled": False,
        "auto_approved": False,
        "safe_for_publish": False,
        "human_approval_required": True,
        "created_at": datetime.datetime.now().isoformat()
    }
    validate_telegram_dry_run_result(res)
    return res

def validate_telegram_dry_run_result(result: Dict[str, Any]):
    if result.get("telegram_api_used") is True:
        raise ValueError("telegram_api_used cannot be true.")
    if result.get("platform_api_used") is True:
        raise ValueError("platform_api_used cannot be true.")
    if result.get("safe_for_publish") is True:
        raise ValueError("safe_for_publish cannot be true.")
    if check_bot_token(result):
        raise ValueError("Bot-token-like field detected.")

def build_telegram_staging_contract() -> Dict[str, Any]:
    return {
        "contract_id": "stg_" + str(uuid.uuid4()).replace("-", ""),
        "platform": "telegram",
        "prerequisites_required": [
            "Explicit operator GO for Telegram credentials",
            "Secret manager plan (Bot token storage outside repo)",
            "Staging channel ID captured locally by operator, not invented",
            "No autonomous replies/DMs permitted",
            "Dry-run pass",
            "Policy pass",
            "Approval queue pass",
            "Audit log pass",
            "Kill switch pass",
            "Rate-limit policy enforced",
            "Rollback/quarantine plan established",
            "Message deletion / correction plan established",
            "Platform policy review complete",
            "Limited pilot scope defined"
        ],
        "is_ready_for_credentials": False,
        "created_at": datetime.datetime.now().isoformat()
    }
