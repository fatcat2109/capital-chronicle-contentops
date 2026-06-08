"""Deterministic local LinkedIn adapter dry-run and staging."""
import datetime
import uuid
import re
from typing import Dict, Any, List
from .. import policy_rules
from .. import contract_validation

def check_bearer_oauth_client_secret(payload: Dict[str, Any]) -> bool:
    """Detect bearer, oauth, or secret keys."""
    if policy_rules.check_secret_keys(payload):
        return True

    token_pattern = re.compile(r"oauth|bearer|token|api_key|access_token|client_secret|client_id", re.IGNORECASE)
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

def check_real_linkedin_url_or_id(val: str) -> bool:
    """Reject if looks like real linkedin URL or ID unless specifically placeholder."""
    val_lower = val.lower()
    if "placeholder" in val_lower or "future_only" in val_lower:
        return False

    if "linkedin.com/" in val_lower:
        return True
    if re.match(r"urn:li:[a-zA-Z0-9_]+:[0-9]+", val):
        return True
    if re.match(r"^[0-9]{7,25}$", val):
        return True
    return False

def validate_dry_run_request(req: Dict[str, Any]):
    if req.get("linkedin_api_used") is True:
        raise ValueError("linkedin_api_used cannot be true.")
    if req.get("platform_api_used") is True:
        raise ValueError("platform_api_used cannot be true.")
    if req.get("safe_for_publish") is True:
        raise ValueError("safe_for_publish cannot be true.")
    if req.get("dry_run_only") is not True:
        raise ValueError("dry_run_only must be true.")
    if req.get("staging_only") is not True:
        raise ValueError("staging_only must be true.")
    if req.get("scope_verification_required") is not True:
        raise ValueError("scope_verification_required must be true.")
    if check_bearer_oauth_client_secret(req):
        raise ValueError("Bearer/OAuth/ClientSecret-like field detected.")
    if check_real_linkedin_url_or_id(req.get("target_account_label", "")):
        raise ValueError("Real-looking LinkedIn URL or ID detected.")

def build_linkedin_dry_run_request(provider_result: Dict[str, Any], queue_item: Dict[str, Any], post_mode: str = "post") -> Dict[str, Any]:
    req_id = "ln_req_" + str(uuid.uuid4()).replace("-", "")

    req = {
        "request_id": req_id,
        "source_provider_result_id": provider_result.get("result_id", ""),
        "policy_decision_id": queue_item.get("source_policy_decision_id", ""),
        "approval_queue_item_id": queue_item.get("queue_item_id", ""),
        "target_account_label": "PLACEHOLDER_STAGING_LINKEDIN_ACCOUNT",
        "target_surface": "company_page_placeholder",
        "post_mode": post_mode,
        "message_text": provider_result.get("simulated_output_text", ""),
        "source_state": queue_item.get("source_state", ""),
        "policy_status": queue_item.get("policy_status", ""),
        "queue_status": queue_item.get("queue_status", ""),
        "dry_run_only": True,
        "staging_only": True,
        "scope_verification_required": True,
        "human_approval_required": True,
        "network_used": False,
        "provider_call_used": False,
        "platform_api_used": False,
        "linkedin_api_used": False,
        "publishing_enabled": False,
        "scheduler_enabled": False,
        "auto_approved": False,
        "live_platform_enabled": False,
        "safe_for_publish": False,
        "created_at": datetime.datetime.now().isoformat()
    }
    validate_dry_run_request(req)
    return req

def run_linkedin_dry_run(request: Dict[str, Any]) -> Dict[str, Any]:
    validate_dry_run_request(request)

    policy_status = request.get("policy_status", "")
    queue_status = request.get("queue_status", "")

    msg = request.get("message_text", "")
    is_article = request.get("post_mode") == "article"

    if policy_status not in [policy_rules.PASS_REVIEW_REQUIRED, ""]:
        is_blocked = True
        preview_text = f"[LOCAL LINKEDIN DRY RUN ONLY] [SIMULATED LINKEDIN PREVIEW] [BLOCKED] Post blocked due to policy: {policy_status}"
    elif queue_status not in ["REVIEW_REQUIRED", "APPROVED_FOR_FUTURE_DRY_RUN_ONLY", ""]:
        is_blocked = True
        preview_text = f"[LOCAL LINKEDIN DRY RUN ONLY] [SIMULATED LINKEDIN PREVIEW] [BLOCKED] Post blocked due to queue status: {queue_status}"
    else:
        is_blocked = False
        preview_text = "[LOCAL LINKEDIN DRY RUN ONLY] [SIMULATED LINKEDIN PREVIEW] [NOT POSTED] [NOT SCHEDULED] [NOT FINAL PUBLIC COPY] [NO LINKEDIN API USED] [NO LIVE LLM USED] [SCOPE VERIFICATION REQUIRED BEFORE ANY FUTURE LIVE WORK]\n\n" + msg

    result_id = "ln_res_" + str(uuid.uuid4()).replace("-", "")
    char_count = len(preview_text)

    res = {
        "result_id": result_id,
        "request_id": request.get("request_id", ""),
        "platform": "linkedin",
        "adapter_mode": "dry_run",
        "dry_run_only": True,
        "staging_only": True,
        "scope_verification_required": True,
        "simulated_post_preview": preview_text,
        "character_count": char_count,
        "formatting_warnings": [] if char_count < 3000 else ["Message exceeds standard LinkedIn length"],
        "blocked_or_warning_reasons": ["Policy blocked"] if is_blocked else [],
        "staging_contract_id": "none",
        "scope_checklist_id": "none",
        "network_used": False,
        "provider_call_used": False,
        "platform_api_used": False,
        "linkedin_api_used": False,
        "publishing_enabled": False,
        "scheduler_enabled": False,
        "auto_approved": False,
        "safe_for_publish": False,
        "human_approval_required": True,
        "created_at": datetime.datetime.now().isoformat()
    }

    if is_article and not is_blocked:
        res["simulated_article_preview"] = {
            "title": "Simulated Article Title",
            "body": preview_text
        }

    validate_linkedin_dry_run_result(res)
    return res

def validate_linkedin_dry_run_result(result: Dict[str, Any]):
    if result.get("linkedin_api_used") is True:
        raise ValueError("linkedin_api_used cannot be true.")
    if result.get("platform_api_used") is True:
        raise ValueError("platform_api_used cannot be true.")
    if result.get("safe_for_publish") is True:
        raise ValueError("safe_for_publish cannot be true.")
    if result.get("scope_verification_required") is not True:
        raise ValueError("scope_verification_required must be true.")
    if check_bearer_oauth_client_secret(result):
        raise ValueError("Bearer/OAuth/ClientSecret-like field detected.")

def build_linkedin_staging_contract() -> Dict[str, Any]:
    return {
        "contract_id": "stg_ln_" + str(uuid.uuid4()).replace("-", ""),
        "platform": "linkedin",
        "prerequisites_required": [
            "Explicit operator GO for LinkedIn credentials",
            "Secret manager plan",
            "OAuth/client secret storage outside repo",
            "Staging account or organization identifier captured locally by operator, not invented",
            "No autonomous comments/replies/DMs/connection requests/reactions",
            "No scraping",
            "Dry-run pass",
            "Policy pass",
            "Approval queue pass",
            "Audit log pass",
            "Kill switch pass",
            "Rate-limit policy enforced",
            "Platform-policy review",
            "Rollback/quarantine/correction plan",
            "Limited pilot scope",
            "Manual review checkpoint"
        ],
        "is_ready_for_credentials": False,
        "created_at": datetime.datetime.now().isoformat()
    }

def build_linkedin_scope_verification_checklist() -> Dict[str, Any]:
    return {
        "checklist_id": "scope_ln_" + str(uuid.uuid4()).replace("-", ""),
        "platform": "linkedin",
        "verification_items": [
            "Explicit operator GO for LinkedIn credential work",
            "Official LinkedIn developer/app capability verification by operator or explicitly scoped online-docs task",
            "Exact scope names must be verified later, not invented now",
            "Account type / company page / member posting target must be verified later"
        ],
        "scope_names_verified_real": False,
        "created_at": datetime.datetime.now().isoformat()
    }
