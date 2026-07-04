import json
import os
import re
import jsonschema

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
SCHEMAS_DIR = os.path.join(BASE_DIR, "schemas")
FIXTURES_DIR = os.path.join(BASE_DIR, "fixtures", "telegram_live_pilot_gate")


def _load_schema(name):
    with open(os.path.join(SCHEMAS_DIR, name), "r", encoding="utf-8") as f:
        return json.load(f)


PACKET_SCHEMA = _load_schema("telegram_live_pilot_gate_packet.schema.json")

ALLOWED_GATE_DECISIONS = {
    "ready_to_prepare_future_credential_setup_task",
    "blocked_missing_safety_dependency",
    "blocked_missing_operator_warning",
    "blocked_scope_violation",
    "not_ready",
}

DEPENDENCY_GATE_KEYS = [
    "publish_automation_readiness_0148",
    "dry_run_publish_batch_manifest_0149",
    "credential_secret_policy_0150",
    "redacted_publish_audit_log_0151",
]

PACKET_FORBIDDEN_TRUE = [
    "runtime_authority",
    "platform_api_key_token_needed_from_operator_now",
    "telegram_bot_token_needed_from_operator_now",
    "telegram_chat_id_needed_from_operator_now",
    "credentials_requested_now",
    "env_read_allowed_now",
    "os_env_read_allowed_now",
    "credential_validation_enabled_now",
    "credential_storage_enabled_now",
    "credential_logging_allowed",
    "credential_commit_allowed",
    "credential_printing_allowed",
    "telegram_api_allowed_now",
    "platform_api_allowed_now",
    "live_adapter_enabled_now",
    "oauth_flow_enabled_now",
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
    "official_docs_verification_completed_now",
]

PACKET_REQUIRED_TRUE = [
    "readiness_gate_only",
    "candidate_platform_is_telegram",
    "platform_api_key_token_needed_from_operator_later",
    "telegram_bot_token_needed_from_operator_later",
    "telegram_chat_id_needed_from_operator_later",
    "secret_redaction_required",
    "never_commit_secrets_required",
    "no_secret_scan_required",
    "manual_review_required",
    "not_public_postable",
    "official_docs_verification_required_later",
    "operator_setup_gate_required_later",
    "live_adapter_gate_required_later",
    "kill_switch_required",
    "redacted_audit_log_required",
]

SAFE_PLACEHOLDERS = {
    "FUTURE_ONLY_NOT_REQUESTED",
    "REDACTED_NEVER_COMMIT",
    "PLACEHOLDER_SLOT_NAME_ONLY",
    "REDACTED",
    "[REDACTED]",
}

SECRET_PATTERNS = [
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bghp_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b"),
    re.compile(r"\b\d{6,}:[A-Za-z0-9_-]{30,}\b"),
    re.compile(r"\bya29\.[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\bBearer\s+[A-Za-z0-9_\-\.=]{20,}\b"),
    re.compile(r"\beyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\b"),
]

DETECTOR_SOURCE_KEYS = {
    "detector_patterns_redacted",
    "false_positive_notes",
    "scan_command_label",
    "detector_pattern_examples",
}


def _looks_like_secret(s):
    if not isinstance(s, str):
        return False
    if s in SAFE_PLACEHOLDERS:
        return False
    for pat in SECRET_PATTERNS:
        if pat.search(s):
            return True
    return False


PHRASE_TOKENS = [
    "our model predicts",
    "our signal says",
    "target price",
    "ai trading bot",
    "bloomberg replacement",
    "guaranteed",
    "capital chronicle alpha says",
]
WORD_BOUND_TOKENS = ["buy", "sell", "hold", "broker"]


def _scan_unsafe(obj):
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
    return errors


def _scan_secret_values(obj):
    """Detect realistic secret values; skip detector-source keys (false positives)."""
    errors = []

    def _walk(o, key=None):
        if isinstance(o, str):
            if key in DETECTOR_SOURCE_KEYS:
                return
            if _looks_like_secret(o):
                errors.append(f"secret_like_value_detected:{key or 'value'}")
        elif isinstance(o, dict):
            for k, v in o.items():
                _walk(v, k)
        elif isinstance(o, list):
            for v in o:
                _walk(v, key)

    _walk(obj)
    return errors


def validate_telegram_live_pilot_gate_packet(packet):
    errors = []

    base_uri = f"file:///{SCHEMAS_DIR.replace(chr(92), '/')}/"
    resolver = jsonschema.RefResolver(base_uri=base_uri, referrer=PACKET_SCHEMA)
    try:
        jsonschema.validate(instance=packet, schema=PACKET_SCHEMA, resolver=resolver)
    except jsonschema.ValidationError as e:
        errors.append(f"schema_invalid:{e.message}")

    if packet.get("gate_mode") != "one_platform_live_pilot_readiness_gate_only":
        errors.append("gate_mode_must_be_one_platform_live_pilot_readiness_gate_only")

    if packet.get("candidate_platform_id") != "telegram":
        errors.append("candidate_platform_id_must_be_telegram")

    decision = packet.get("gate_decision")
    if decision not in ALLOWED_GATE_DECISIONS:
        errors.append(f"unknown_gate_decision:{decision}")

    for flag in PACKET_FORBIDDEN_TRUE:
        if packet.get(flag) is True:
            errors.append(f"{flag}_must_be_false")

    for flag in PACKET_REQUIRED_TRUE:
        if packet.get(flag) is not True:
            errors.append(f"{flag}_must_be_true")

    # Operator warning required.
    if not packet.get("operator_warning_no_token_needed_now"):
        errors.append("operator_warning_no_token_needed_now_required")

    # Dependency gates must be present and satisfied.
    dgs = packet.get("dependency_gate_status", {})
    for k in DEPENDENCY_GATE_KEYS:
        if k not in dgs:
            errors.append(f"dependency_gate_missing:{k}")
        elif dgs.get(k) != "satisfied":
            errors.append(f"dependency_gate_unsatisfied:{k}")

    # Future credential slot requirements must not request action now.
    for req in packet.get("future_telegram_credential_requirements", []):
        sid = req.get("slot_name", "unknown")
        if req.get("operator_action_required_now") is True:
            errors.append(f"future_credential_slot_action_required_now:{sid}")
        if req.get("real_secret_value_present") is True:
            errors.append(f"future_credential_slot_real_secret_present:{sid}")

    # Future operator prerequisites must not request action now.
    for item in packet.get("future_operator_prerequisite_checklist", []):
        iid = item.get("item_id", "unknown")
        if item.get("operator_action_required_now") is True:
            errors.append(f"future_operator_prerequisite_action_required_now:{iid}")

    errors += _scan_secret_values(packet)
    errors += _scan_unsafe(packet)

    if packet.get("packet_status") == "pass" and len(errors) > 0:
        errors.append("packet_status_pass_but_errors_exist")

    return {"valid": len(errors) == 0, "errors": sorted(set(errors))}


def _load_valid_packet():
    with open(os.path.join(FIXTURES_DIR, "telegram_live_pilot_gate_valid.json"), "r", encoding="utf-8") as f:
        return json.load(f)



def summary():
    packet = _load_valid_packet()
    res = validate_telegram_live_pilot_gate_packet(packet)
    slots = packet.get("future_telegram_credential_requirements", [])
    prereqs = packet.get("future_operator_prerequisite_checklist", [])
    dgs = packet.get("dependency_gate_status", {})

    def _p(flag):
        return 1 if packet.get(flag) is True else 0

    later_actions = sum(
        1 for x in (slots + prereqs) if x.get("operator_action_required_later") is True
    )

    return {
        "packet_status": packet.get("packet_status", ""),
        "candidate_platform_id": packet.get("candidate_platform_id", ""),
        "gate_decision": packet.get("gate_decision", ""),
        "dependency_gate_count": len(DEPENDENCY_GATE_KEYS),
        "dependency_gate_satisfied_count": sum(1 for k in DEPENDENCY_GATE_KEYS if dgs.get(k) == "satisfied"),
        "future_credential_slot_count": len(slots),
        "future_operator_prerequisite_count": len(prereqs),
        "platform_api_key_token_needed_now_count": _p("platform_api_key_token_needed_from_operator_now"),
        "telegram_bot_token_needed_now_count": _p("telegram_bot_token_needed_from_operator_now"),
        "telegram_chat_id_needed_now_count": _p("telegram_chat_id_needed_from_operator_now"),
        "platform_api_key_token_needed_later_count": _p("platform_api_key_token_needed_from_operator_later"),
        "telegram_bot_token_needed_later_count": _p("telegram_bot_token_needed_from_operator_later"),
        "telegram_chat_id_needed_later_count": _p("telegram_chat_id_needed_from_operator_later"),
        "credentials_requested_now_count": _p("credentials_requested_now"),
        "env_read_allowed_now_count": _p("env_read_allowed_now"),
        "os_env_read_allowed_now_count": _p("os_env_read_allowed_now"),
        "credential_validation_enabled_now_count": _p("credential_validation_enabled_now"),
        "credential_storage_enabled_now_count": _p("credential_storage_enabled_now"),
        "credential_logging_allowed_count": _p("credential_logging_allowed"),
        "credential_commit_allowed_count": _p("credential_commit_allowed"),
        "credential_printing_allowed_count": _p("credential_printing_allowed"),
        "secret_like_value_detected_count": len(_scan_secret_values(packet)),
        "real_secret_values_present_count": sum(1 for s in slots if s.get("real_secret_value_present") is True),
        "telegram_api_enabled_count": _p("telegram_api_allowed_now"),
        "platform_api_enabled_count": _p("platform_api_allowed_now"),
        "live_adapter_enabled_count": _p("live_adapter_enabled_now"),
        "oauth_flow_enabled_count": _p("oauth_flow_enabled_now"),
        "live_posting_enabled_count": _p("live_posting_enabled_now"),
        "scheduler_enabled_count": _p("scheduler_allowed_now"),
        "provider_llm_api_enabled_count": _p("provider_llm_api_allowed_now"),
        "repo_web_search_enabled_count": _p("repo_web_search_allowed_now"),
        "scraping_enabled_count": _p("scraping_allowed_now"),
        "newsletter_or_cms_api_enabled_count": _p("newsletter_or_cms_api_allowed_now"),
        "backend_server_required_count": _p("backend_server_required"),
        "publish_all_button_enabled_count": _p("publish_all_button_enabled_now"),
        "one_button_publish_all_enabled_count": _p("one_button_publish_all_enabled_now"),
        "publish_approval_system_created_count": _p("publish_approval_system_created"),
        "public_ready_approval_allowed_count": _p("public_ready_approval_allowed_now"),
        "final_social_copy_generated_count": _p("final_social_copy_generated"),
        "manual_review_required_all": packet.get("manual_review_required") is True,
        "not_public_postable_all": packet.get("not_public_postable") is True,
        "official_docs_verification_required_later_all": packet.get("official_docs_verification_required_later") is True,
        "official_docs_verification_completed_now_count": _p("official_docs_verification_completed_now"),
        "operator_action_required_now_count": 0,
        "operator_action_required_later_count": later_actions,
        "kill_switch_required_all": packet.get("kill_switch_required") is True,
        "redacted_audit_log_required_all": packet.get("redacted_audit_log_required") is True,
        "no_secret_scan_required_all": packet.get("no_secret_scan_required") is True,
        "validation_valid": res["valid"],
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

