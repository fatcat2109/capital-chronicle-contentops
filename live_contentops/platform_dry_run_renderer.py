import json
import os
import jsonschema
import re

CANONICAL_SCHEMA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "schemas", "canonical_social_post.schema.json")
DRY_RUN_SCHEMA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "schemas", "platform_dry_run_payload.schema.json")

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

PLATFORM_REGISTRY = {
    p: {
        "platform_id": p,
        "display_name": p.replace("_", " ").title(),
        "supported_text_modes": ["plain", "links"],
        "supported_media_types": ["image/jpeg"] if p in ["instagram"] else ["image/jpeg", "image/png", "video/mp4", "none"],
        "requires_media": p == "instagram",
        "max_text_length_placeholder": 280 if p == "x" else 2000,
        "constraint_source": "local_placeholder_until_official_docs_verification",
        "official_docs_verified": False,
        "live_api_status": "disabled",
        "credential_required_for_live": True,
        "credential_read_allowed_now": False,
        "scheduling_allowed_now": False,
        "replies_or_dms_allowed_now": False,
        "scraping_allowed_now": False,
        "posting_allowed_now": False
    }
    for p in ["x", "linkedin", "threads", "newsletter", "telegram", "facebook_page", "instagram", "tiktok"]
}

def render_dry_run(canonical_post, platform_id):
    errors = []
    warnings = []
    
    try:
        jsonschema.validate(instance=canonical_post, schema=load_json(CANONICAL_SCHEMA_PATH))
    except jsonschema.ValidationError as e:
        errors.append(f"Canonical schema invalid: {e.message}")

    if platform_id not in PLATFORM_REGISTRY:
        errors.append(f"unsupported_platform:{platform_id}")
    
    if canonical_post.get("public_postable"): errors.append("blocked_flag:public_postable")
    if canonical_post.get("publish_ready"): errors.append("blocked_flag:publish_ready")
    if canonical_post.get("live_posting_enabled"): errors.append("blocked_flag:live_posting_enabled")
    if canonical_post.get("platform_api_payload_generated"): errors.append("blocked_flag:platform_api_payload_generated")

    # Safety checks
    sf = canonical_post.get("safety_flags", {})
    if not sf.get("manual_review_required"): errors.append("safety_flag_missing:manual_review_required")
    if not sf.get("operator_final_check_required"): errors.append("safety_flag_missing:operator_final_check_required")
    if not sf.get("no_financial_advice"): errors.append("safety_flag_missing:no_financial_advice")
    if not sf.get("no_signal_language"): errors.append("safety_flag_missing:no_signal_language")
    if not sf.get("no_execution_language"): errors.append("safety_flag_missing:no_execution_language")

    # Forbidden text
    text_content = (canonical_post.get("title", "") + " " + canonical_post.get("body", "")).lower()
    forbidden_signals = [
        "\\bbuy\\b", "\\bsell\\b", "\\bhold\\b", "\\blong\\b", "\\bshort\\b",
        "\\bentry\\b", "\\bexit\\b", "\\btarget\\b", "position sizing", 
        "\\bbroker\\b", "order routing", "\\bexecution\\b", "\\bsignal\\b", "model says"
    ]
    for sig in forbidden_signals:
        if re.search(sig, text_content):
            errors.append(f"forbidden_signal:{sig.replace(chr(92)+'b', '')}")

    alpha_implications = [
        "capital chronicle alpha says", "artifact_id", "source_artifact_id",
        "dqr_status", "forecast_readiness_status", "our model predicts"
    ]
    for alpha in alpha_implications:
        if alpha in text_content:
            errors.append(f"forbidden_alpha_implication:{alpha}")

    # Media checks
    has_media = len(canonical_post.get("media", [])) > 0
    if platform_id in PLATFORM_REGISTRY:
        reg = PLATFORM_REGISTRY[platform_id]
        if reg["requires_media"] and not has_media:
            errors.append("media_required_for_platform")
        
        text_len = len(text_content)
        if text_len > reg["max_text_length_placeholder"]:
            warnings.append(f"text_exceeds_placeholder_max_length:{text_len}>{reg['max_text_length_placeholder']}")

    render_status = "blocked" if errors else "rendered"

    payload = {
        "dry_run": True,
        "platform_id": platform_id,
        "post_id": canonical_post.get("post_id", ""),
        "payload_preview": {
            "title": canonical_post.get("title"),
            "body": canonical_post.get("body")
        } if render_status == "rendered" else {},
        "warnings": warnings,
        "blocking_errors": errors,
        "render_status": render_status,
        "constraint_source": PLATFORM_REGISTRY.get(platform_id, {}).get("constraint_source", "unknown"),
        "requires_operator_approval": True,
        "not_public_postable": True,
        "live_posting_enabled": False,
        "platform_api_payload_generated": False,
        "credential_accessed": False,
        "network_accessed": False,
        "scheduler_accessed": False,
        "mock_endpoint_name": f"local_mock_{platform_id}_endpoint"
    }

    try:
        jsonschema.validate(instance=payload, schema=load_json(DRY_RUN_SCHEMA_PATH))
    except jsonschema.ValidationError as e:
        payload["blocking_errors"].append(f"Payload schema invalid: {e.message}")
        payload["render_status"] = "blocked"

    return payload

def render_dry_run_from_file(canonical_path, platform_id):
    return render_dry_run(load_json(canonical_path), platform_id)

def summary():
    return {
        "packet_status": "pass",
        "platform_count": len(PLATFORM_REGISTRY),
        "rendered_payload_count": 0,
        "blocked_payload_count": 0,
        "unsupported_platform_count": 0,
        "unsafe_flag_count": 0,
        "official_docs_verified_count": 0
    }
