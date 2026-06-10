import json
import os
import re
import jsonschema

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
SCHEMAS_DIR = os.path.join(BASE_DIR, "schemas")
FIXTURES_DIR = os.path.join(BASE_DIR, "fixtures", "telegram_credential_setup_operator_guide")


def _load_schema(name):
    with open(os.path.join(SCHEMAS_DIR, name), "r", encoding="utf-8") as f:
        return json.load(f)


PACKET_SCHEMA = _load_schema("telegram_credential_setup_operator_guide_packet.schema.json")

PACKET_FORBIDDEN_TRUE = [
    "runtime_authority",
    "platform_api_key_token_needed_from_operator_now",
    "telegram_bot_token_needed_from_operator_now",
    "telegram_chat_id_needed_from_operator_now",
    "real_env_file_read_by_repo_now",
    "real_env_file_read_allowed_now",
    "env_read_allowed_now",
    "os_env_read_allowed_now",
    "credential_validation_enabled_now",
    "credential_storage_enabled_now",
    "credential_logging_allowed",
    "credential_commit_allowed",
    "credential_printing_allowed",
    "token_value_present",
    "chat_id_value_present",
    "real_secret_values_present",
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
    "guide_only",
    "real_env_file_may_exist_locally",
    "placeholder_only",
    "secret_redaction_required",
    "never_commit_secrets_required",
    "never_paste_secrets_warning_required",
    "rotation_warning_required_if_exposed",
    "future_presence_check_required",
    "future_live_adapter_gate_required",
    "manual_review_required",
    "not_public_postable",
    "official_docs_verification_required_later",
]

SAFE_PLACEHOLDERS = {
    "FUTURE_ONLY_NOT_REQUESTED",
    "REDACTED_NEVER_COMMIT",
    "PLACEHOLDER_SLOT_NAME_ONLY",
    "REDACTED",
    "[REDACTED]",
    "OPERATOR_LOCAL_ENV_FILE_PROVIDED_OUT_OF_BAND",
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

# Realistic Telegram chat id: -100 followed by 10+ digits (supergroup/channel).
CHAT_ID_PATTERN = re.compile(r"-100\d{8,}")

DETECTOR_SOURCE_KEYS = {
    "detector_patterns_redacted",
    "false_positive_notes",
    "scan_command_label",
    "detector_pattern_examples",
}


def _looks_like_secret(s):
    if not isinstance(s, str) or s in SAFE_PLACEHOLDERS:
        return False
    for pat in SECRET_PATTERNS:
        if pat.search(s):
            return True
    if CHAT_ID_PATTERN.search(s):
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



def validate_telegram_credential_setup_operator_guide_packet(packet):
    errors = []

    try:
        jsonschema.validate(instance=packet, schema=PACKET_SCHEMA)
    except jsonschema.ValidationError as e:
        errors.append(f"schema_invalid:{e.message}")

    if packet.get("guide_mode") != "telegram_credential_setup_operator_guide_only":
        errors.append("guide_mode_must_be_telegram_credential_setup_operator_guide_only")

    for flag in PACKET_FORBIDDEN_TRUE:
        if packet.get(flag) is True:
            errors.append(f"{flag}_must_be_false")

    for flag in PACKET_REQUIRED_TRUE:
        if packet.get(flag) is not True:
            errors.append(f"{flag}_must_be_true")

    # Required warnings (string content) must be present.
    if not packet.get("never_paste_secrets_warning"):
        errors.append("never_paste_secrets_warning_required")
    if not packet.get("rotation_warning"):
        errors.append("rotation_warning_required")

    # Future boundaries must be present.
    if not packet.get("future_presence_check_boundary"):
        errors.append("future_presence_check_boundary_required")
    if not packet.get("future_live_adapter_boundary"):
        errors.append("future_live_adapter_boundary_required")

    # Credential slots must be placeholder-only with no real values / no action now.
    for slot in packet.get("credential_slot_policy", []):
        sid = slot.get("slot_name", "unknown")
        if slot.get("value_status") != "placeholder_only":
            errors.append(f"slot_value_status_not_placeholder_only:{sid}")
        if slot.get("real_value_present") is True:
            errors.append(f"slot_real_value_present:{sid}")
        if slot.get("operator_action_required_now") is True:
            errors.append(f"slot_operator_action_required_now:{sid}")
        if slot.get("read_allowed_now") is True:
            errors.append(f"slot_read_allowed_now:{sid}")
        if slot.get("validation_allowed_now") is True:
            errors.append(f"slot_validation_allowed_now:{sid}")

    # Operator checklist items must not require action now.
    for item in packet.get("operator_setup_checklist", []):
        iid = item.get("item_id", "unknown")
        if item.get("operator_action_required_now") is True:
            errors.append(f"checklist_operator_action_required_now:{iid}")

    errors += _scan_secret_values(packet)
    errors += _scan_unsafe(packet)

    if packet.get("packet_status") == "pass" and len(errors) > 0:
        errors.append("packet_status_pass_but_errors_exist")

    return {"valid": len(errors) == 0, "errors": sorted(set(errors))}


def _load_valid_packet():
    with open(os.path.join(FIXTURES_DIR, "telegram_credential_setup_operator_guide_valid.json"), "r", encoding="utf-8") as f:
        return json.load(f)



def summary():
    packet = _load_valid_packet()
    res = validate_telegram_credential_setup_operator_guide_packet(packet)
    slots = packet.get("credential_slot_policy", [])
    checklist = packet.get("operator_setup_checklist", [])

    def _p(flag):
        return 1 if packet.get(flag) is True else 0

    return {
        "packet_status": packet.get("packet_status", ""),
        "guide_mode": packet.get("guide_mode", ""),
        "credential_slot_count": len(slots),
        "operator_checklist_count": len(checklist),
        "platform_api_key_token_needed_now_count": _p("platform_api_key_token_needed_from_operator_now"),
        "telegram_bot_token_needed_now_count": _p("telegram_bot_token_needed_from_operator_now"),
        "telegram_chat_id_needed_now_count": _p("telegram_chat_id_needed_from_operator_now"),
        "real_env_file_read_by_repo_now_count": _p("real_env_file_read_by_repo_now"),
        "real_env_file_read_allowed_now_count": _p("real_env_file_read_allowed_now"),
        "env_read_allowed_now_count": _p("env_read_allowed_now"),
        "os_env_read_allowed_now_count": _p("os_env_read_allowed_now"),
        "credential_validation_enabled_now_count": _p("credential_validation_enabled_now"),
        "credential_storage_enabled_now_count": _p("credential_storage_enabled_now"),
        "credential_logging_allowed_count": _p("credential_logging_allowed"),
        "credential_commit_allowed_count": _p("credential_commit_allowed"),
        "credential_printing_allowed_count": _p("credential_printing_allowed"),
        "token_value_present_count": _p("token_value_present"),
        "chat_id_value_present_count": _p("chat_id_value_present"),
        "real_secret_values_present_count": _p("real_secret_values_present"),
        "placeholder_only_all": packet.get("placeholder_only") is True,
        "secret_redaction_required_all": packet.get("secret_redaction_required") is True,
        "never_commit_secrets_required_all": packet.get("never_commit_secrets_required") is True,
        "never_paste_secrets_warning_required_all": packet.get("never_paste_secrets_warning_required") is True,
        "rotation_warning_required_if_exposed_all": packet.get("rotation_warning_required_if_exposed") is True,
        "future_presence_check_required_all": packet.get("future_presence_check_required") is True,
        "future_live_adapter_gate_required_all": packet.get("future_live_adapter_gate_required") is True,
        "secret_like_value_detected_count": len(_scan_secret_values(packet)),
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
        "official_docs_verification_completed_now_count": _p("official_docs_verification_completed_now"),
        "validation_valid": res["valid"],
        "provider_call_used_by_repo": False,
        "search_call_used_by_repo": False,
        "network_call_used_by_repo": False,
        "telegram_api_used_by_repo": False,
        "platform_action_used_by_repo": False,
        "credential_or_env_read_used": False,
        "scheduler_accessed": False,
        "scraping_allowed_now": False,
        "newsletter_send_enabled": False,
        "cms_integration_enabled": False,
        "autonomous_reply_dm_enabled": False,
    }

