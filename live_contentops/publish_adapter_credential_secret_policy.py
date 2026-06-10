import json
import os
import re
import jsonschema

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
SCHEMAS_DIR = os.path.join(BASE_DIR, "schemas")
FIXTURES_DIR = os.path.join(BASE_DIR, "fixtures", "publish_adapter_credential_secret_policy")


def _load_schema(name):
    with open(os.path.join(SCHEMAS_DIR, name), "r", encoding="utf-8") as f:
        return json.load(f)


PACKET_SCHEMA = _load_schema("publish_adapter_credential_secret_policy_packet.schema.json")

REGISTRY_PLATFORM_IDS = [
    "telegram",
    "linkedin",
    "x",
    "threads",
    "substack_or_newsletter",
    "manual_external_posting",
]

# Safe placeholder markers permitted in slot/value fields.
SAFE_PLACEHOLDERS = {
    "FUTURE_ONLY_NOT_REQUESTED",
    "REDACTED_NEVER_COMMIT",
    "PLACEHOLDER_SLOT_NAME_ONLY",
}

# Packet-level booleans that must be false (fail closed if true).
PACKET_FORBIDDEN_TRUE = [
    "runtime_authority",
    "credentials_requested_now",
    "platform_api_key_token_needed_from_operator_now",
    "real_secret_values_allowed_in_repo",
    "real_secret_values_present",
    "env_read_allowed_now",
    "os_env_read_allowed_now",
    "credential_validation_enabled_now",
    "credential_storage_enabled_now",
    "credential_logging_allowed",
    "credential_commit_allowed",
    "credential_printing_allowed",
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
    "platform_api_key_token_needed_from_operator_later",
    "secret_redaction_required",
    "never_commit_secrets_required",
    "manual_review_required",
    "not_public_postable",
]

# Patterns that indicate a real / realistic secret value.
SECRET_PATTERNS = [
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bghp_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b"),
    re.compile(r"\b\d{6,}:[A-Za-z0-9_-]{30,}\b"),  # telegram bot token shape
    re.compile(r"\bya29\.[A-Za-z0-9_-]{20,}\b"),  # google oauth access token
    re.compile(r"\bBearer\s+[A-Za-z0-9_\-\.=]{20,}\b"),
    re.compile(r"\beyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\b"),  # jwt
]

# Credential value field names that must hold slot names / placeholders only.
CREDENTIAL_VALUE_FIELDS = [
    "secret_value",
    "secret_values",
    "credential_value",
    "credential_values",
    "token",
    "access_token",
    "api_key",
    "api_secret",
    "client_secret",
    "bot_token",
    "refresh_token",
    "page_token",
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


PHRASE_TOKENS = [
    "our model predicts",
    "our signal says",
    "target price",
    "ai trading bot",
    "bloomberg replacement",
    "guaranteed",
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
    """Detect realistic secret values anywhere in the packet."""
    errors = []

    def _walk(o, key=None):
        if isinstance(o, str):
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


def validate_publish_adapter_credential_secret_policy_packet(packet):
    errors = []

    base_uri = f"file:///{SCHEMAS_DIR.replace(chr(92), '/')}/"
    resolver = jsonschema.RefResolver(base_uri=base_uri, referrer=PACKET_SCHEMA)
    try:
        jsonschema.validate(instance=packet, schema=PACKET_SCHEMA, resolver=resolver)
    except jsonschema.ValidationError as e:
        errors.append(f"schema_invalid:{e.message}")

    if packet.get("policy_mode") != "credential_secret_policy_only":
        errors.append("policy_mode_must_be_credential_secret_policy_only")

    for flag in PACKET_FORBIDDEN_TRUE:
        if packet.get(flag) is True:
            errors.append(f"{flag}_must_be_false")

    for flag in PACKET_REQUIRED_TRUE:
        if packet.get(flag) is not True:
            errors.append(f"{flag}_must_be_true")

    # Required gate models / warning must be present.
    if not packet.get("future_operator_setup_gate"):
        errors.append("future_operator_setup_gate_required")
    if not packet.get("future_credential_validation_gate"):
        errors.append("future_credential_validation_gate_required")
    if not packet.get("operator_warning_no_keys_needed_now"):
        errors.append("operator_warning_no_keys_needed_now_required")

    # Per-platform credential requirement enforcement.
    for entry in packet.get("platform_credential_requirements", []):
        pid = entry.get("platform_id", "unknown")
        if pid not in REGISTRY_PLATFORM_IDS:
            errors.append(f"unsupported_platform_credential_target:{pid}")
        if entry.get("credential_requirement_status") != "future_only_not_requested":
            errors.append(f"credential_requirement_status_must_be_future_only:{pid}")
        if entry.get("real_secret_value_present") is True:
            errors.append(f"real_secret_value_present_must_be_false:{pid}")
        if entry.get("secret_value_placeholder_only") is not True:
            errors.append(f"secret_value_placeholder_only_must_be_true:{pid}")
        if entry.get("redaction_required") is not True:
            errors.append(f"entry_redaction_required_must_be_true:{pid}")
        if entry.get("never_commit_secrets") is not True:
            errors.append(f"entry_never_commit_secrets_must_be_true:{pid}")
        for f in [
            "operator_action_required_now",
            "env_read_allowed_now",
            "credential_validation_enabled_now",
            "live_adapter_enabled_now",
            "platform_api_allowed_now",
        ]:
            if entry.get(f) is True:
                errors.append(f"entry_{f}_must_be_false:{pid}")
        if entry.get("requires_future_official_docs_verification") is not True:
            errors.append(f"entry_requires_future_official_docs_verification_must_be_true:{pid}")

    errors += _scan_secret_values(packet)
    errors += _scan_unsafe(packet)

    if packet.get("packet_status") == "pass" and len(errors) > 0:
        errors.append("packet_status_pass_but_errors_exist")

    return {"valid": len(errors) == 0, "errors": sorted(set(errors))}


def _load_valid_packet():
    with open(os.path.join(FIXTURES_DIR, "publish_adapter_credential_secret_policy_valid.json"), "r", encoding="utf-8") as f:
        return json.load(f)



def summary():
    packet = _load_valid_packet()
    res = validate_publish_adapter_credential_secret_policy_packet(packet)
    reqs = packet.get("platform_credential_requirements", [])
    slot_policy = packet.get("future_env_slot_policy", {})
    slots = slot_policy.get("env_slot_names_future_only", [])

    def _p(flag):
        return 1 if packet.get(flag) is True else 0

    return {
        "packet_status": packet.get("packet_status", ""),
        "platform_credential_requirement_count": len(reqs),
        "future_env_slot_count": len(slots),
        "credentials_requested_now_count": _p("credentials_requested_now"),
        "platform_api_key_token_needed_now_count": _p("platform_api_key_token_needed_from_operator_now"),
        "platform_api_key_token_needed_later_count": _p("platform_api_key_token_needed_from_operator_later"),
        "real_secret_values_present_count": _p("real_secret_values_present"),
        "env_read_allowed_now_count": _p("env_read_allowed_now"),
        "os_env_read_allowed_now_count": _p("os_env_read_allowed_now"),
        "credential_validation_enabled_now_count": _p("credential_validation_enabled_now"),
        "credential_storage_enabled_now_count": _p("credential_storage_enabled_now"),
        "credential_logging_allowed_count": _p("credential_logging_allowed"),
        "credential_commit_allowed_count": _p("credential_commit_allowed"),
        "credential_printing_allowed_count": _p("credential_printing_allowed"),
        "secret_redaction_required_all": packet.get("secret_redaction_required") is True
        and all(e.get("redaction_required") is True for e in reqs),
        "never_commit_secrets_required_all": packet.get("never_commit_secrets_required") is True
        and all(e.get("never_commit_secrets") is True for e in reqs),
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
        "secret_like_value_detected_count": len(_scan_secret_values(packet)),
        "unsupported_platform_credential_target_count": sum(
            1 for e in reqs if e.get("platform_id") not in REGISTRY_PLATFORM_IDS
        ),
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

