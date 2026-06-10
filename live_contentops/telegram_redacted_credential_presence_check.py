import json
import os
import re
import datetime
import jsonschema

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
SCHEMAS_DIR = os.path.join(BASE_DIR, "schemas")

TASK_LABEL = "TASK_CONTENTOPS_0155_TELEGRAM_REDACTED_CREDENTIAL_PRESENCE_CHECK_LOCAL_ONLY_V0"

APPROVED_SLOT_KEYS = ("TELEGRAM_BOT_TOKEN", "TELEGRAM_TARGET_CHAT_ID")


def _load_schema(name):
    with open(os.path.join(SCHEMAS_DIR, name), "r", encoding="utf-8") as f:
        return json.load(f)


PACKET_SCHEMA = _load_schema("telegram_redacted_credential_presence_check_packet.schema.json")

FORBIDDEN_TRUE = [
    "runtime_authority",
    "real_env_path_printed",
    "real_env_path_committed",
    "credential_values_printed",
    "credential_values_committed",
    "token_snippet_reported",
    "chat_id_snippet_reported",
    "exact_length_reported",
    "hash_or_digest_reported",
    "telegram_api_allowed_now",
    "telegram_api_called",
    "credential_validation_enabled_now",
    "live_adapter_enabled_now",
    "live_posting_enabled_now",
    "scheduler_allowed_now",
    "platform_api_allowed_now",
    "provider_llm_api_allowed_now",
    "repo_web_search_allowed_now",
    "scraping_allowed_now",
    "backend_server_required",
    "publish_all_button_enabled_now",
    "one_button_publish_all_enabled_now",
    "final_social_copy_generated",
]

REQUIRED_TRUE = [
    "manual_review_required",
    "not_public_postable",
    "kill_switch_required_for_future_live",
    "redacted_audit_required_for_future_live",
    "official_docs_verification_required_later",
    "live_adapter_gate_required_later",
]



# --- redacted shape classification (no values, no lengths, no snippets) ---

_BOT_TOKEN_LIKE = re.compile(r"^\d{6,}:[A-Za-z0-9_-]{30,}$")
_INTEGER_LIKE = re.compile(r"^-?\d+$")
_CHANNEL_HANDLE_LIKE = re.compile(r"^@[A-Za-z0-9_]{3,}$")


def classify_token_shape(raw):
    """Return a redacted shape class for a token value. Never returns the value."""
    if raw is None:
        return "absent"
    if raw.strip() == "":
        return "present_redacted_empty_or_whitespace"
    if _BOT_TOKEN_LIKE.match(raw.strip()):
        return "present_redacted_telegram_bot_token_like"
    return "present_redacted_nonempty_nonclassifiable"


def classify_chat_id_shape(raw):
    """Return a redacted shape class for a chat id value. Never returns the value."""
    if raw is None:
        return "absent"
    s = raw.strip()
    if s == "":
        return "present_redacted_empty_or_whitespace"
    if _INTEGER_LIKE.match(s):
        return "present_redacted_integer_like"
    if _CHANNEL_HANDLE_LIKE.match(s):
        return "present_redacted_channel_handle_like"
    return "present_redacted_nonempty_nonclassifiable"


def _is_present(raw):
    """A slot counts as present only if non-empty after strip."""
    return raw is not None and raw.strip() != ""


def parse_approved_env_text(text):
    """Parse env text, returning only approved slot raw values + a generic warning count.

    Never returns other keys, names, or line contents.
    """
    values = {k: None for k in APPROVED_SLOT_KEYS}
    invalid_line_count = 0
    for line in text.splitlines():
        stripped = line.strip()
        if stripped == "" or stripped.startswith("#"):
            continue
        if "=" not in stripped:
            invalid_line_count += 1
            continue
        key, _, val = stripped.partition("=")
        key = key.strip()
        if key in APPROVED_SLOT_KEYS:
            v = val.strip()
            if len(v) >= 2 and v[0] == v[-1] and v[0] in ("'", '"'):
                v = v[1:-1]
            values[key] = v
        # all other keys silently ignored (names/values never recorded)
    return {**values, "invalid_line_count": invalid_line_count}


def _base_packet():
    return {
        "packet_id": "tg_redacted_presence_check_0155",
        "created_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "runtime_authority": False,
        "task_label": TASK_LABEL,
        "check_mode": "local_redacted_presence_check_only",
        "candidate_platform_id": "telegram",
        "approved_env_source_label": "unavailable",
        "real_env_path_printed": False,
        "real_env_path_committed": False,
        "env_source_read_attempted": False,
        "env_source_read_succeeded": False,
        "env_source_missing_or_unavailable": True,
        "credential_values_printed": False,
        "credential_values_committed": False,
        "token_snippet_reported": False,
        "chat_id_snippet_reported": False,
        "exact_length_reported": False,
        "hash_or_digest_reported": False,
        "telegram_bot_token_present": None,
        "telegram_target_chat_id_present": None,
        "telegram_bot_token_shape_class": "not_checked_blocked",
        "telegram_target_chat_id_shape_class": "not_checked_blocked",
        "telegram_api_allowed_now": False,
        "telegram_api_called": False,
        "credential_validation_enabled_now": False,
        "live_adapter_enabled_now": False,
        "live_posting_enabled_now": False,
        "scheduler_allowed_now": False,
        "platform_api_allowed_now": False,
        "provider_llm_api_allowed_now": False,
        "repo_web_search_allowed_now": False,
        "scraping_allowed_now": False,
        "backend_server_required": False,
        "publish_all_button_enabled_now": False,
        "one_button_publish_all_enabled_now": False,
        "final_social_copy_generated": False,
        "manual_review_required": True,
        "not_public_postable": True,
        "kill_switch_required_for_future_live": True,
        "redacted_audit_required_for_future_live": True,
        "official_docs_verification_required_later": True,
        "live_adapter_gate_required_later": True,
        "blocked_action_policy": {
            "telegram_api": "blocked",
            "live_posting": "blocked",
            "scheduler": "blocked",
            "credential_validation": "blocked",
            "value_or_snippet_output": "blocked",
            "path_output": "blocked",
        },
        "safety_policy": {
            "redacted_only": True,
            "no_values": True,
            "no_snippets": True,
            "no_lengths_or_hashes": True,
            "no_paths": True,
        },
        "blocked_reasons": [],
        "packet_status": "blocked",
    }



def validate_telegram_redacted_credential_presence_check_packet(packet):
    """Deterministic fail-closed validation. Reports only redacted booleans/classes."""
    errors = []

    try:
        jsonschema.validate(packet, PACKET_SCHEMA)
    except jsonschema.ValidationError as e:
        errors.append(f"schema_error:{e.message}")

    for k in FORBIDDEN_TRUE:
        if packet.get(k) is True:
            errors.append(f"{k}_must_be_false")
    for k in REQUIRED_TRUE:
        if packet.get(k) is not True:
            errors.append(f"{k}_must_be_true")

    if packet.get("task_label") != TASK_LABEL:
        errors.append("task_label_mismatch")
    if packet.get("check_mode") != "local_redacted_presence_check_only":
        errors.append("check_mode_mismatch")
    if packet.get("candidate_platform_id") != "telegram":
        errors.append("candidate_platform_id_must_be_telegram")

    # Never leak a real path; only redacted source labels allowed.
    label = packet.get("approved_env_source_label")
    if label not in (
        "OPERATOR_LOCAL_ENV_FILE_PROVIDED_OUT_OF_BAND",
        "APPROVED_LOCAL_ENV_SOURCE_REDACTED",
        "unavailable",
    ):
        errors.append("approved_env_source_label_invalid")

    # Secret-like leakage guard over the whole packet (no detector-source exception).
    errors += _scan_secret_like(packet)
    errors += _scan_unsafe(packet)

    status = packet.get("packet_status")
    if status == "pass" and errors:
        errors.append("packet_status_pass_but_errors_exist")

    return {"valid": len(errors) == 0, "errors": errors}



# --- leakage guards ---

_SECRET_LIKE = [
    re.compile(r"\d{6,}:[A-Za-z0-9_-]{30,}"),       # telegram bot token body
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),
    re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"),
    re.compile(r"ya29\.[A-Za-z0-9_-]{20,}"),
    re.compile(r"-100\d{8,}"),                        # realistic supergroup chat id
]


def _scan_secret_like(obj):
    """Reject any secret-like value appearing anywhere in emitted output."""
    errors = []

    def _walk(o, key=None):
        if isinstance(o, str):
            for pat in _SECRET_LIKE:
                if pat.search(o):
                    errors.append(f"secret_like_value_detected:{key or 'value'}")
                    break
        elif isinstance(o, dict):
            for k, v in o.items():
                _walk(v, k)
        elif isinstance(o, list):
            for v in o:
                _walk(v, key)

    _walk(obj)
    return errors


_PHRASE_TOKENS = [
    "our model predicts",
    "our signal says",
    "target price",
    "ai trading bot",
    "bloomberg replacement",
    "capital chronicle alpha says",
]
_WORD_TOKENS = ["buy", "sell", "hold", "broker"]


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
    for st in _PHRASE_TOKENS:
        if st in lower:
            errors.append(f"unsafe_signal_detected:{st}")
    words = lower.replace("\n", " ").replace(".", " ").replace(",", " ").split()
    for st in _WORD_TOKENS:
        if st in words:
            errors.append(f"unsafe_signal_detected:{st}")
    return errors



def build_presence_check(env_text=None, source_label=None):
    """Build a redacted presence-check packet.

    env_text: the raw text of the approved local env source, supplied by the caller
              from an approved local source. Never logged, never stored, never
              returned. If None, the source is treated as unavailable (BLOCKED).
    source_label: redacted label only; a real path must never be passed/printed here.
    """
    packet = _base_packet()

    if source_label in (
        "OPERATOR_LOCAL_ENV_FILE_PROVIDED_OUT_OF_BAND",
        "APPROVED_LOCAL_ENV_SOURCE_REDACTED",
    ):
        packet["approved_env_source_label"] = source_label
    else:
        packet["approved_env_source_label"] = (
            "APPROVED_LOCAL_ENV_SOURCE_REDACTED" if env_text is not None else "unavailable"
        )

    if env_text is None:
        packet["env_source_read_attempted"] = False
        packet["env_source_read_succeeded"] = False
        packet["env_source_missing_or_unavailable"] = True
        packet["telegram_bot_token_present"] = None
        packet["telegram_target_chat_id_present"] = None
        packet["telegram_bot_token_shape_class"] = "not_checked_blocked"
        packet["telegram_target_chat_id_shape_class"] = "not_checked_blocked"
        packet["blocked_reasons"] = ["approved_local_env_source_unavailable"]
        packet["packet_status"] = "blocked"
        return packet

    parsed = parse_approved_env_text(env_text)
    token_raw = parsed["TELEGRAM_BOT_TOKEN"]
    chat_raw = parsed["TELEGRAM_TARGET_CHAT_ID"]

    packet["env_source_read_attempted"] = True
    packet["env_source_read_succeeded"] = True
    packet["env_source_missing_or_unavailable"] = False
    packet["telegram_bot_token_present"] = _is_present(token_raw)
    packet["telegram_target_chat_id_present"] = _is_present(chat_raw)
    packet["telegram_bot_token_shape_class"] = classify_token_shape(token_raw)
    packet["telegram_target_chat_id_shape_class"] = classify_chat_id_shape(chat_raw)
    # invalid_line_count intentionally not embedded to avoid any line-content risk;
    # only a generic boolean flag is recorded.
    packet["env_parse_warnings_present"] = parsed["invalid_line_count"] > 0
    packet["packet_status"] = "pass"

    # Defensive: never let a raw value survive into the packet.
    leak = _scan_secret_like(packet)
    if leak:
        packet["telegram_bot_token_shape_class"] = "not_checked_blocked"
        packet["telegram_target_chat_id_shape_class"] = "not_checked_blocked"
        packet["blocked_reasons"] = ["redaction_guard_triggered"]
        packet["packet_status"] = "blocked"

    return packet



def summary(env_text=None, source_label=None):
    """Return a JSON-serializable redacted summary. No values, snippets, or paths."""
    packet = build_presence_check(env_text=env_text, source_label=source_label)
    res = validate_telegram_redacted_credential_presence_check_packet(packet)
    return {
        "packet_status": packet.get("packet_status"),
        "validation_valid": res["valid"],
        "task_label": packet.get("task_label"),
        "check_mode": packet.get("check_mode"),
        "candidate_platform_id": packet.get("candidate_platform_id"),
        "approved_env_source_label": packet.get("approved_env_source_label"),
        "env_source_read_attempted": packet.get("env_source_read_attempted"),
        "env_source_read_succeeded": packet.get("env_source_read_succeeded"),
        "env_source_missing_or_unavailable": packet.get("env_source_missing_or_unavailable"),
        "telegram_bot_token_present": packet.get("telegram_bot_token_present"),
        "telegram_target_chat_id_present": packet.get("telegram_target_chat_id_present"),
        "telegram_bot_token_shape_class": packet.get("telegram_bot_token_shape_class"),
        "telegram_target_chat_id_shape_class": packet.get("telegram_target_chat_id_shape_class"),
        "real_env_path_printed": packet.get("real_env_path_printed"),
        "real_env_path_committed": packet.get("real_env_path_committed"),
        "credential_values_printed": packet.get("credential_values_printed"),
        "credential_values_committed": packet.get("credential_values_committed"),
        "token_snippet_reported": packet.get("token_snippet_reported"),
        "chat_id_snippet_reported": packet.get("chat_id_snippet_reported"),
        "exact_length_reported": packet.get("exact_length_reported"),
        "hash_or_digest_reported": packet.get("hash_or_digest_reported"),
        "telegram_api_allowed_now": packet.get("telegram_api_allowed_now"),
        "telegram_api_called": packet.get("telegram_api_called"),
        "credential_validation_enabled_now": packet.get("credential_validation_enabled_now"),
        "live_adapter_enabled_now": packet.get("live_adapter_enabled_now"),
        "live_posting_enabled_now": packet.get("live_posting_enabled_now"),
        "scheduler_allowed_now": packet.get("scheduler_allowed_now"),
        "platform_api_allowed_now": packet.get("platform_api_allowed_now"),
        "provider_llm_api_allowed_now": packet.get("provider_llm_api_allowed_now"),
        "repo_web_search_allowed_now": packet.get("repo_web_search_allowed_now"),
        "scraping_allowed_now": packet.get("scraping_allowed_now"),
        "backend_server_required": packet.get("backend_server_required"),
        "publish_all_button_enabled_now": packet.get("publish_all_button_enabled_now"),
        "one_button_publish_all_enabled_now": packet.get("one_button_publish_all_enabled_now"),
        "final_social_copy_generated": packet.get("final_social_copy_generated"),
        "manual_review_required": packet.get("manual_review_required"),
        "not_public_postable": packet.get("not_public_postable"),
        "kill_switch_required_for_future_live": packet.get("kill_switch_required_for_future_live"),
        "redacted_audit_required_for_future_live": packet.get("redacted_audit_required_for_future_live"),
        "secret_like_value_detected_count": len(_scan_secret_like(packet)),
        "unsafe_language_count": len(_scan_unsafe(packet)),
        "blocked_reasons": packet.get("blocked_reasons", []),
    }

