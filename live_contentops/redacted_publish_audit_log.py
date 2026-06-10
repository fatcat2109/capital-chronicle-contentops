import json
import os
import re
import jsonschema

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
SCHEMAS_DIR = os.path.join(BASE_DIR, "schemas")
FIXTURES_DIR = os.path.join(BASE_DIR, "fixtures", "redacted_publish_audit_log")


def _load_schema(name):
    with open(os.path.join(SCHEMAS_DIR, name), "r", encoding="utf-8") as f:
        return json.load(f)


PACKET_SCHEMA = _load_schema("redacted_publish_audit_log_packet.schema.json")

ALLOWED_AUDIT_EVENT_TYPES = {
    "dry_run_publish_manifest_created",
    "dry_run_payload_preview_validated",
    "manual_review_gate_checked",
    "kill_switch_status_checked",
    "credential_policy_checked_no_values",
    "no_secret_scan_completed",
    "redaction_policy_checked",
    "blocked_live_action_detected",
    "future_platform_response_redaction_planned",
    "evidence_packet_export_checked",
}

FORBIDDEN_AUDIT_EVENT_TYPES = {
    "live_post_succeeded",
    "live_post_failed",
    "platform_api_called",
    "credential_value_read",
    "credential_value_validated",
    "oauth_flow_completed",
    "token_refreshed",
    "publish_all_executed",
    "scheduled_post_created",
}

# Packet-level booleans that must be false (fail closed if true).
PACKET_FORBIDDEN_TRUE = [
    "runtime_authority",
    "platform_api_key_token_needed_from_operator_now",
    "credentials_requested_now",
    "env_read_allowed_now",
    "os_env_read_allowed_now",
    "credential_validation_enabled_now",
    "credential_storage_enabled_now",
    "credential_logging_allowed",
    "credential_commit_allowed",
    "credential_printing_allowed",
    "unredacted_secret_allowed_in_audit",
    "unredacted_secret_allowed_in_evidence",
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
]

# Packet-level booleans that must be true (fail closed if not true).
PACKET_REQUIRED_TRUE = [
    "audit_log_model_only",
    "evidence_guard_model_only",
    "platform_api_key_token_needed_from_operator_later",
    "platform_response_logging_future_only",
    "platform_response_redaction_required_later",
    "secret_redaction_required",
    "never_commit_secrets_required",
    "no_secret_scan_required",
    "kill_switch_audit_required",
    "manual_review_required",
    "not_public_postable",
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


def _looks_like_secret(s):
    if not isinstance(s, str):
        return False
    if s in SAFE_PLACEHOLDERS:
        return False
    for pat in SECRET_PATTERNS:
        if pat.search(s):
            return True
    return False


# Keys whose string values are detector-source regex literals (allowed false positives).
DETECTOR_SOURCE_KEYS = {
    "detector_patterns_redacted",
    "false_positive_notes",
    "scan_command_label",
    "detector_pattern_examples",
}

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


def validate_redacted_publish_audit_log_packet(packet):
    errors = []

    base_uri = f"file:///{SCHEMAS_DIR.replace(chr(92), '/')}/"
    resolver = jsonschema.RefResolver(base_uri=base_uri, referrer=PACKET_SCHEMA)
    try:
        jsonschema.validate(instance=packet, schema=PACKET_SCHEMA, resolver=resolver)
    except jsonschema.ValidationError as e:
        errors.append(f"schema_invalid:{e.message}")

    if packet.get("audit_mode") != "redacted_audit_and_secret_evidence_guard_only":
        errors.append("audit_mode_must_be_redacted_audit_and_secret_evidence_guard_only")

    for flag in PACKET_FORBIDDEN_TRUE:
        if packet.get(flag) is True:
            errors.append(f"{flag}_must_be_false")

    for flag in PACKET_REQUIRED_TRUE:
        if packet.get(flag) is not True:
            errors.append(f"{flag}_must_be_true")

    # Required models must be present.
    if not packet.get("secret_redaction_policy"):
        errors.append("secret_redaction_policy_required")
    if not packet.get("no_secret_scan_result_model"):
        errors.append("no_secret_scan_result_model_required")
    if not packet.get("kill_switch_audit_model"):
        errors.append("kill_switch_audit_model_required")
    if not packet.get("evidence_packet_policy"):
        errors.append("evidence_packet_policy_required")

    # Evidence packet policy must forbid all unsafe content.
    epp = packet.get("evidence_packet_policy", {})
    for forbidden in [
        "allow_env_contents",
        "allow_os_env_values",
        "allow_token_snippets",
        "allow_screenshots_with_secrets",
        "allow_logs_with_secrets",
        "allow_oauth_callback_values",
        "allow_platform_response_bodies_with_credentials",
    ]:
        if epp.get(forbidden) is True:
            errors.append(f"evidence_policy_{forbidden}_must_be_false")

    # Audit event enforcement.
    for ev in packet.get("audit_events", []):
        eid = ev.get("event_id", "unknown")
        et = ev.get("event_type")
        if et in FORBIDDEN_AUDIT_EVENT_TYPES:
            errors.append(f"forbidden_audit_event_type:{et}:{eid}")
        elif et not in ALLOWED_AUDIT_EVENT_TYPES:
            errors.append(f"unknown_audit_event_type:{et}:{eid}")
        if ev.get("secret_values_present") is True:
            errors.append(f"event_secret_values_present:{eid}")
        if ev.get("credential_values_present") is True:
            errors.append(f"event_credential_values_present:{eid}")
        if ev.get("platform_response_values_present") is True:
            if ev.get("redaction_status") != "redacted_future_only":
                errors.append(f"event_unredacted_platform_response:{eid}")
        if ev.get("live_action_performed") is True:
            errors.append(f"event_live_action_performed:{eid}")
        if ev.get("platform_api_called") is True:
            errors.append(f"event_platform_api_called:{eid}")
        if ev.get("evidence_safe") is not True:
            errors.append(f"event_evidence_not_safe:{eid}")

    errors += _scan_secret_values(packet)
    errors += _scan_unsafe(packet)

    if packet.get("packet_status") == "pass" and len(errors) > 0:
        errors.append("packet_status_pass_but_errors_exist")

    return {"valid": len(errors) == 0, "errors": sorted(set(errors))}


def _load_valid_packet():
    with open(os.path.join(FIXTURES_DIR, "redacted_publish_audit_log_valid.json"), "r", encoding="utf-8") as f:
        return json.load(f)



def summary():
    packet = _load_valid_packet()
    res = validate_redacted_publish_audit_log_packet(packet)
    events = packet.get("audit_events", [])
    scans = packet.get("no_secret_scan_result_model", {})

    def _p(flag):
        return 1 if packet.get(flag) is True else 0

    def _evcount(flag):
        return sum(1 for e in events if e.get(flag) is True)

    allowed_ev = sum(1 for e in events if e.get("event_type") in ALLOWED_AUDIT_EVENT_TYPES)
    forbidden_ev = sum(1 for e in events if e.get("event_type") in FORBIDDEN_AUDIT_EVENT_TYPES)

    return {
        "packet_status": packet.get("packet_status", ""),
        "audit_event_count": len(events),
        "allowed_audit_event_count": allowed_ev,
        "forbidden_audit_event_count": forbidden_ev,
        "no_secret_scan_result_count": 1 if scans else 0,
        "platform_api_key_token_needed_now_count": _p("platform_api_key_token_needed_from_operator_now"),
        "platform_api_key_token_needed_later_count": _p("platform_api_key_token_needed_from_operator_later"),
        "credentials_requested_now_count": _p("credentials_requested_now"),
        "env_read_allowed_now_count": _p("env_read_allowed_now"),
        "os_env_read_allowed_now_count": _p("os_env_read_allowed_now"),
        "credential_validation_enabled_now_count": _p("credential_validation_enabled_now"),
        "credential_storage_enabled_now_count": _p("credential_storage_enabled_now"),
        "credential_logging_allowed_count": _p("credential_logging_allowed"),
        "credential_commit_allowed_count": _p("credential_commit_allowed"),
        "credential_printing_allowed_count": _p("credential_printing_allowed"),
        "unredacted_secret_in_audit_count": _p("unredacted_secret_allowed_in_audit"),
        "unredacted_secret_in_evidence_count": _p("unredacted_secret_allowed_in_evidence"),
        "secret_values_present_count": _evcount("secret_values_present"),
        "credential_values_present_count": _evcount("credential_values_present"),
        "platform_response_values_present_count": _evcount("platform_response_values_present"),
        "secret_like_value_detected_count": len(_scan_secret_values(packet)),
        "secret_redaction_required_all": packet.get("secret_redaction_required") is True,
        "never_commit_secrets_required_all": packet.get("never_commit_secrets_required") is True,
        "no_secret_scan_required_all": packet.get("no_secret_scan_required") is True,
        "kill_switch_audit_required_all": packet.get("kill_switch_audit_required") is True,
        "evidence_safe_all": all(e.get("evidence_safe") is True for e in events),
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

