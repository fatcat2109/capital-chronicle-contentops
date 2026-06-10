import json
import os
import jsonschema

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
SCHEMAS_DIR = os.path.join(BASE_DIR, "schemas")
FIXTURES_DIR = os.path.join(BASE_DIR, "fixtures", "publish_automation_readiness")


def _load_schema(name):
    with open(os.path.join(SCHEMAS_DIR, name), "r", encoding="utf-8") as f:
        return json.load(f)


REGISTRY_SCHEMA = _load_schema("platform_capability_registry_packet.schema.json")
READINESS_SCHEMA = _load_schema("publish_automation_readiness_packet.schema.json")

# Platform-entry booleans that must be false (fail closed if true).
PLATFORM_FORBIDDEN_TRUE = [
    "credentials_requested_now",
    "credential_read_allowed_now",
    "credentials_available",
    "live_api_enabled_now",
    "live_posting_enabled_now",
    "scheduling_enabled_now",
    "publish_ready",
]

# Readiness packet-level booleans that must be false (fail closed if true).
READINESS_FORBIDDEN_TRUE = [
    "runtime_authority",
    "credentials_requested_now",
    "credential_read_allowed_now",
    "platform_api_allowed_now",
    "live_posting_enabled_now",
    "scheduler_allowed_now",
    "provider_llm_api_allowed_now",
    "repo_web_search_allowed_now",
    "scraping_allowed_now",
    "newsletter_or_cms_api_allowed_now",
    "backend_server_required",
    "publish_all_button_enabled_now",
    "one_button_publish_all_enabled_now",
    "publish_approval_system_created",
    "public_ready_approval_allowed_now",
    "final_social_copy_generated",
    "operator_action_required_now_for_credentials",
]

# Readiness packet-level booleans that must be true (fail closed if not true).
READINESS_REQUIRED_TRUE = [
    "dry_run_only",
    "manual_review_required",
    "not_public_postable",
    "kill_switch_required",
    "redacted_audit_log_required",
]

PHRASE_TOKENS = [
    "our model predicts",
    "our signal says",
    "target price",
    "position sizing",
    "ai trading bot",
    "bloomberg replacement",
    "signal service",
    "guaranteed",
    "will move",
    "watch this level",
    "ready to post",
]
WORD_BOUND_TOKENS = ["buy", "sell", "hold", "entry", "exit", "broker", "long", "short"]


def _scan_unsafe(obj, real_artifacts=False):
    parts = []

    def _collect(o):
        if isinstance(o, str):
            parts.append(o)
        elif isinstance(o, dict):
            for v in o.values():
                _collect(v)
        elif isinstance(o, list):
            for v in o:
                _collect(v)

    _collect(obj)
    lower = "\n".join(parts).lower()
    errors = []
    for st in PHRASE_TOKENS:
        if st in lower:
            errors.append(f"unsafe_signal_detected:{st}")
    words = lower.replace("\n", " ").replace(".", " ").replace(",", " ").split()
    for st in WORD_BOUND_TOKENS:
        if st in words:
            errors.append(f"unsafe_signal_detected:{st}")
    if "unsupported numeric" in lower or "fake alpha" in lower:
        errors.append("unsupported_numeric_market_claim")
    if "capital chronicle alpha says" in lower and not real_artifacts:
        errors.append("alpha_claim_without_real_artifact")
    return errors


def _schema_errors(packet, schema):
    errors = []
    base_uri = f"file:///{SCHEMAS_DIR.replace(chr(92), '/')}/"
    resolver = jsonschema.RefResolver(base_uri=base_uri, referrer=schema)
    try:
        jsonschema.validate(instance=packet, schema=schema, resolver=resolver)
    except jsonschema.ValidationError as e:
        errors.append(f"schema_invalid:{e.message}")
    return errors


def validate_platform_capability_registry_packet(packet):
    errors = []
    errors += _schema_errors(packet, REGISTRY_SCHEMA)

    if packet.get("registry_mode") != "platform_capability_registry_dry_run_only":
        errors.append("registry_mode_must_be_platform_capability_registry_dry_run_only")
    if packet.get("runtime_authority") is True:
        errors.append("runtime_authority_must_be_false")

    for p in packet.get("platforms", []):
        pid = p.get("platform_id", "unknown")
        for flag in PLATFORM_FORBIDDEN_TRUE:
            if p.get(flag) is True:
                errors.append(f"platform_{flag}_must_be_false:{pid}")
        if p.get("adapter_status") in ("implemented", "live", "enabled"):
            errors.append(f"platform_adapter_status_must_not_be_live:{pid}")
        if p.get("requires_future_official_docs_verification") is not True:
            errors.append(f"platform_requires_future_official_docs_verification_must_be_true:{pid}")
        if p.get("manual_review_required") is not True:
            errors.append(f"platform_manual_review_required_must_be_true:{pid}")
        if p.get("not_public_postable") is not True:
            errors.append(f"platform_not_public_postable_must_be_true:{pid}")

    errors += _scan_unsafe(packet)

    if packet.get("packet_status") == "pass" and len(errors) > 0:
        errors.append("packet_status_pass_but_errors_exist")

    return {"valid": len(errors) == 0, "errors": sorted(set(errors))}


def _load_registry():
    with open(os.path.join(FIXTURES_DIR, "platform_capability_registry_valid.json"), "r", encoding="utf-8") as f:
        return json.load(f)


def validate_publish_automation_readiness_packet(packet):
    errors = []
    errors += _schema_errors(packet, READINESS_SCHEMA)

    if packet.get("readiness_mode") != "dry_run_readiness_only":
        errors.append("readiness_mode_must_be_dry_run_readiness_only")

    for flag in READINESS_FORBIDDEN_TRUE:
        if packet.get(flag) is True:
            errors.append(f"{flag}_must_be_false")

    for flag in READINESS_REQUIRED_TRUE:
        if packet.get(flag) is not True:
            errors.append(f"{flag}_must_be_true")

    if not packet.get("kill_switch_model"):
        errors.append("kill_switch_model_required")
    if not packet.get("audit_log_policy"):
        errors.append("audit_log_policy_required")
    if not packet.get("manual_approval_gate_model"):
        errors.append("manual_approval_gate_model_required")

    batch = packet.get("publish_batch_model", {})
    if batch.get("live_execution_status") not in (None, "disabled"):
        errors.append("publish_batch_live_execution_must_be_disabled")

    real_artifacts = packet.get("safety_policy", {}).get("real_approved_artifacts_present") is True
    errors += _scan_unsafe(packet, real_artifacts=real_artifacts)

    if packet.get("packet_status") == "pass" and len(errors) > 0:
        errors.append("packet_status_pass_but_errors_exist")

    return {"valid": len(errors) == 0, "errors": sorted(set(errors))}


def _load_readiness():
    with open(os.path.join(FIXTURES_DIR, "publish_automation_readiness_valid.json"), "r", encoding="utf-8") as f:
        return json.load(f)



def summary():
    packet = _load_readiness()
    registry = _load_registry()
    res = validate_publish_automation_readiness_packet(packet)
    reg_res = validate_platform_capability_registry_packet(registry)
    platforms = registry.get("platforms", [])

    def _pcount(flag):
        return sum(1 for p in platforms if p.get(flag) is True)

    return {
        "packet_status": packet.get("packet_status", ""),
        "registry_packet_status": registry.get("packet_status", ""),
        "platform_count": len(platforms),
        "not_implemented_adapter_count": sum(
            1 for p in platforms if p.get("adapter_status") == "not_implemented"
        ),
        "future_docs_verification_required_count": sum(
            1 for p in platforms if p.get("requires_future_official_docs_verification") is True
        ),
        "credentials_requested_now_count": _pcount("credentials_requested_now"),
        "credential_read_enabled_count": _pcount("credential_read_allowed_now"),
        "platform_api_enabled_count": _pcount("live_api_enabled_now"),
        "live_posting_enabled_count": _pcount("live_posting_enabled_now"),
        "scheduler_enabled_count": _pcount("scheduling_enabled_now"),
        "provider_llm_api_enabled_count": 0,
        "repo_web_search_enabled_count": 0,
        "scraping_enabled_count": 0,
        "newsletter_or_cms_api_enabled_count": 0,
        "backend_server_required_count": 1 if packet.get("backend_server_required") is True else 0,
        "publish_all_button_enabled_count": 1 if packet.get("publish_all_button_enabled_now") is True else 0,
        "one_button_publish_all_enabled_count": 1 if packet.get("one_button_publish_all_enabled_now") is True else 0,
        "public_ready_approval_allowed_count": 1 if packet.get("public_ready_approval_allowed_now") is True else 0,
        "publish_approval_system_created_count": 1 if packet.get("publish_approval_system_created") is True else 0,
        "final_social_copy_generated_count": 1 if packet.get("final_social_copy_generated") is True else 0,
        "manual_review_required_all": packet.get("manual_review_required") is True
        and all(p.get("manual_review_required") is True for p in platforms),
        "not_public_postable_all": packet.get("not_public_postable") is True
        and all(p.get("not_public_postable") is True for p in platforms),
        "kill_switch_required_all": packet.get("kill_switch_required") is True,
        "redacted_audit_log_required_all": packet.get("redacted_audit_log_required") is True,
        "credential_operator_action_required_now_count": 1
        if packet.get("operator_action_required_now_for_credentials") is True
        else 0,
        "credential_operator_action_required_later_count": 1
        if packet.get("operator_action_required_later_for_credentials") is True
        else 0,
        "unsafe_language_count": 0,
        "validation_valid": res["valid"],
        "registry_validation_valid": reg_res["valid"],
        "provider_call_used_by_repo": False,
        "search_call_used_by_repo": False,
        "network_call_used_by_repo": False,
        "news_api_used_by_repo": False,
        "market_data_api_used_by_repo": False,
        "platform_action_used_by_repo": False,
        "credential_or_env_read_used": False,
        "scheduler_accessed": False,
        "scraping_allowed_now": False,
        "newsletter_send_enabled": False,
        "cms_integration_enabled": False,
        "autonomous_reply_dm_enabled": False,
    }

