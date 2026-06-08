"""Deterministic local Instagram asset export planner and Meta capability review."""
import datetime
import uuid
import re
from typing import Dict, Any, List
from .. import policy_rules

def check_bearer_oauth_client_secret(payload: Dict[str, Any]) -> bool:
    """Detect bearer, oauth, app secret, or keys."""
    if policy_rules.check_secret_keys(payload):
        return True

    token_pattern = re.compile(r"oauth|bearer|token|api_key|access_token|client_secret|app_secret|app_id", re.IGNORECASE)
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

def check_real_instagram_url_or_id(val: str) -> bool:
    """Reject if looks like real Instagram/Meta URL or ID unless specifically placeholder."""
    val_lower = val.lower()
    if "placeholder" in val_lower or "future_only" in val_lower:
        return False

    if "instagram.com/" in val_lower or "facebook.com/" in val_lower or "meta.com/" in val_lower:
        return True
    if re.match(r"^[0-9]{15,25}$", val):  # Typical Meta Graph ID lengths
        return True
    if val.startswith("@") and not "placeholder" in val_lower:
        return True
    return False

def validate_dry_run_request(req: Dict[str, Any]):
    if req.get("instagram_api_used") is True:
        raise ValueError("instagram_api_used cannot be true.")
    if req.get("meta_api_used") is True:
        raise ValueError("meta_api_used cannot be true.")
    if req.get("graph_api_used") is True:
        raise ValueError("graph_api_used cannot be true.")
    if req.get("platform_api_used") is True:
        raise ValueError("platform_api_used cannot be true.")
    if req.get("upload_enabled") is True:
        raise ValueError("upload_enabled cannot be true.")
    if req.get("safe_for_publish") is True:
        raise ValueError("safe_for_publish cannot be true.")
    if req.get("dry_run_only") is not True:
        raise ValueError("dry_run_only must be true.")
    if req.get("staging_only") is not True:
        raise ValueError("staging_only must be true.")
    if req.get("asset_export_only") is not True:
        raise ValueError("asset_export_only must be true.")
    if req.get("meta_capability_review_required") is not True:
        raise ValueError("meta_capability_review_required must be true.")
    if check_bearer_oauth_client_secret(req):
        raise ValueError("Bearer/OAuth/ClientSecret/AppSecret-like field detected.")
    if check_real_instagram_url_or_id(req.get("target_account_label", "")):
        raise ValueError("Real-looking Instagram/Meta URL, handle, or ID detected.")

def build_instagram_asset_package_request(provider_result: Dict[str, Any], queue_item: Dict[str, Any], asset_mode: str = "post") -> Dict[str, Any]:
    req_id = "ig_req_" + str(uuid.uuid4()).replace("-", "")

    req = {
        "request_id": req_id,
        "source_provider_result_id": provider_result.get("result_id", ""),
        "policy_decision_id": queue_item.get("source_policy_decision_id", ""),
        "approval_queue_item_id": queue_item.get("queue_item_id", ""),
        "target_account_label": "PLACEHOLDER_STAGING_INSTAGRAM_ACCOUNT",
        "asset_mode": asset_mode,
        "caption_text": provider_result.get("simulated_output_text", ""),
        "visual_brief_text": "Visual brief from provider logic if any",
        "source_state": queue_item.get("source_state", ""),
        "policy_status": queue_item.get("policy_status", ""),
        "queue_status": queue_item.get("queue_status", ""),
        "dry_run_only": True,
        "staging_only": True,
        "asset_export_only": True,
        "meta_capability_review_required": True,
        "human_approval_required": True,
        "network_used": False,
        "provider_call_used": False,
        "platform_api_used": False,
        "instagram_api_used": False,
        "meta_api_used": False,
        "graph_api_used": False,
        "publishing_enabled": False,
        "scheduler_enabled": False,
        "upload_enabled": False,
        "auto_approved": False,
        "live_platform_enabled": False,
        "safe_for_publish": False,
        "created_at": datetime.datetime.now().isoformat()
    }
    validate_dry_run_request(req)
    return req

def run_instagram_asset_export_dry_run(request: Dict[str, Any]) -> Dict[str, Any]:
    validate_dry_run_request(request)

    policy_status = request.get("policy_status", "")
    queue_status = request.get("queue_status", "")

    msg = request.get("caption_text", "")
    asset_mode = request.get("asset_mode")

    if policy_status not in [policy_rules.PASS_REVIEW_REQUIRED, ""]:
        is_blocked = True
        preview_text = f"[LOCAL INSTAGRAM ASSET EXPORT ONLY] [SIMULATED ASSET PACKAGE] [BLOCKED] Post blocked due to policy: {policy_status}"
    elif queue_status not in ["REVIEW_REQUIRED", "APPROVED_FOR_FUTURE_DRY_RUN_ONLY", ""]:
        is_blocked = True
        preview_text = f"[LOCAL INSTAGRAM ASSET EXPORT ONLY] [SIMULATED ASSET PACKAGE] [BLOCKED] Post blocked due to queue status: {queue_status}"
    else:
        is_blocked = False
        preview_text = "[LOCAL INSTAGRAM ASSET EXPORT ONLY] [SIMULATED ASSET PACKAGE] [NOT POSTED] [NOT UPLOADED] [NOT SCHEDULED] [NOT FINAL PUBLIC COPY] [NO INSTAGRAM API USED] [NO META API USED] [NO LIVE LLM USED] [META CAPABILITY REVIEW REQUIRED BEFORE ANY FUTURE LIVE WORK]\n\n" + msg

    result_id = "ig_res_" + str(uuid.uuid4()).replace("-", "")

    res = {
        "result_id": result_id,
        "request_id": request.get("request_id", ""),
        "platform": "instagram",
        "adapter_mode": "asset_export_dry_run",
        "dry_run_only": True,
        "staging_only": True,
        "asset_export_only": True,
        "meta_capability_review_required": True,
        "caption_preview": preview_text,
        "visual_asset_manifest": {"status": "planned", "details": "Visual export only, no actual images generated."},
        "formatting_warnings": [] if len(preview_text) < 2200 else ["Message exceeds standard Instagram caption length"],
        "blocked_or_warning_reasons": ["Policy blocked"] if is_blocked else [],
        "staging_contract_id": "none",
        "capability_checklist_id": "none",
        "network_used": False,
        "provider_call_used": False,
        "platform_api_used": False,
        "instagram_api_used": False,
        "meta_api_used": False,
        "graph_api_used": False,
        "publishing_enabled": False,
        "scheduler_enabled": False,
        "upload_enabled": False,
        "auto_approved": False,
        "safe_for_publish": False,
        "human_approval_required": True,
        "created_at": datetime.datetime.now().isoformat()
    }

    if not is_blocked:
        if asset_mode == "carousel":
            res["carousel_plan"] = {"slides": 3, "description": "Simulated carousel stub"}
        elif asset_mode == "story":
            res["story_plan"] = {"frames": 1, "description": "Simulated story stub"}
        elif asset_mode == "reel":
            res["reel_plan"] = {"duration": "15s", "description": "Simulated reel storyboard stub"}

    validate_instagram_asset_package_result(res)
    return res

def validate_instagram_asset_package_result(result: Dict[str, Any]):
    if result.get("instagram_api_used") is True:
        raise ValueError("instagram_api_used cannot be true.")
    if result.get("meta_api_used") is True:
        raise ValueError("meta_api_used cannot be true.")
    if result.get("graph_api_used") is True:
        raise ValueError("graph_api_used cannot be true.")
    if result.get("platform_api_used") is True:
        raise ValueError("platform_api_used cannot be true.")
    if result.get("upload_enabled") is True:
        raise ValueError("upload_enabled cannot be true.")
    if result.get("safe_for_publish") is True:
        raise ValueError("safe_for_publish cannot be true.")
    if result.get("meta_capability_review_required") is not True:
        raise ValueError("meta_capability_review_required must be true.")
    if check_bearer_oauth_client_secret(result):
        raise ValueError("Bearer/OAuth/ClientSecret/AppSecret-like field detected.")

def build_instagram_staging_contract() -> Dict[str, Any]:
    return {
        "contract_id": "stg_ig_" + str(uuid.uuid4()).replace("-", ""),
        "platform": "instagram",
        "prerequisites_required": [
            "Explicit operator GO for Meta/Instagram credentials",
            "Secret manager plan",
            "OAuth/client secret/app secret storage outside repo",
            "Staging account identifier captured locally by operator, not invented",
            "No autonomous comments/replies/DMs/reactions/follows",
            "No scraping",
            "No upload/live publishing",
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

def build_meta_capability_review_checklist() -> Dict[str, Any]:
    return {
        "checklist_id": "cap_meta_" + str(uuid.uuid4()).replace("-", ""),
        "platform": "instagram",
        "verification_items": [
            "Explicit operator GO for Meta/Instagram credential work",
            "Official Meta developer/app capability verification by operator or future explicitly scoped online-docs task",
            "Exact API permission names must be verified later, not invented now",
            "Account type requirements must be verified later",
            "Instagram account / Facebook page / business manager linkage must be verified later",
            "App review requirement must be verified later"
        ],
        "permission_names_verified_real": False,
        "created_at": datetime.datetime.now().isoformat()
    }
