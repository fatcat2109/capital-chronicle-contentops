import json
import os
import datetime
import jsonschema

from live_contentops.telegram_redacted_credential_presence_check import (
    classify_token_shape,
    classify_chat_id_shape,
    _is_present,
    parse_approved_env_text,
    _scan_secret_like,
    _scan_unsafe,
)

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
SCHEMAS_DIR = os.path.join(BASE_DIR, "schemas")

TASK_LABEL = "TASK_CONTENTOPS_0156_TELEGRAM_OFFICIAL_DOCS_AND_CREDENTIAL_VALIDATION_GATE_NO_POST_V0"
PRESENCE_TASK_LABEL = "TASK_CONTENTOPS_0155_TELEGRAM_REDACTED_CREDENTIAL_PRESENCE_CHECK_LOCAL_ONLY_V0"

OFFICIAL_DOCS_DOMAIN = "core.telegram.org"
TELEGRAM_API_DOMAIN = "api.telegram.org"
OFFICIAL_DOCS_FETCH_BUDGET = 3
TELEGRAM_API_REQUEST_BUDGET = 1
ALLOWED_TELEGRAM_METHOD = "getMe"


def _load_schema(name):
    with open(os.path.join(SCHEMAS_DIR, name), "r", encoding="utf-8") as f:
        return json.load(f)


PACKET_SCHEMA = _load_schema("telegram_official_docs_credential_validation_gate_packet.schema.json")

FORBIDDEN_TRUE = [
    "runtime_authority",
    "bot_id_reported",
    "bot_username_reported",
    "token_value_printed",
    "chat_id_value_printed",
    "token_snippet_reported",
    "chat_id_snippet_reported",
    "exact_length_reported",
    "hash_or_digest_reported",
    "request_url_printed",
    "raw_response_printed",
    "sendmessage_called",
    "getupdates_called",
    "live_adapter_enabled_now",
    "live_posting_enabled_now",
    "scheduler_allowed_now",
    "provider_llm_api_allowed_now",
    "repo_web_search_allowed_now_except_official_docs",
    "scraping_allowed_now",
    "backend_server_required",
    "publish_all_button_enabled_now",
    "one_button_publish_all_enabled_now",
    "final_social_copy_generated",
    "channel_write_permission_validated",
    "channel_posting_validated",
]

REQUIRED_TRUE = [
    "manual_review_required",
    "not_public_postable",
    "next_gate_required_before_posting",
]

# Default official-docs facts verified for getMe from core.telegram.org:
# getMe requires no parameters and returns a User object (id, is_bot, first_name,
# optional username). Base request URL form: https://api.telegram.org/bot<token>/METHOD_NAME.
# getMe validates token identity only; it does NOT prove channel write permission.
DEFAULT_OFFICIAL_DOCS_NOTES = [
    "getMe_requires_no_parameters",
    "getMe_returns_user_object_with_is_bot_true_for_bots",
    "base_url_form_is_api_telegram_org_bot_token_method",
    "getMe_validates_token_identity_only_not_channel_write_permission",
    "channel_write_permission_requires_future_separate_gate_no_post_in_0156",
]



def _base_packet():
    return {
        "packet_id": "tg_official_docs_cred_validation_gate_0156",
        "created_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "runtime_authority": False,
        "task_label": TASK_LABEL,
        "gate_mode": "official_docs_and_getme_credential_validation_no_post",
        "candidate_platform_id": "telegram",
        "linked_presence_check_task": PRESENCE_TASK_LABEL,
        "approved_env_source_label": "unavailable",
        "env_source_read_attempted": False,
        "env_source_read_succeeded": False,
        "telegram_bot_token_present": None,
        "telegram_target_chat_id_present": None,
        "telegram_bot_token_shape_class": "not_checked_blocked",
        "telegram_target_chat_id_shape_class": "not_checked_blocked",
        "official_docs_verification_attempted": False,
        "official_docs_source_domain": "none",
        "official_docs_verified": False,
        "official_docs_fetch_count": 0,
        "official_docs_fetch_budget": OFFICIAL_DOCS_FETCH_BUDGET,
        "official_docs_notes": [],
        "credential_validation_attempted": False,
        "credential_validation_method": "none",
        "telegram_api_request_count": 0,
        "telegram_api_request_budget": TELEGRAM_API_REQUEST_BUDGET,
        "telegram_api_allowed_now_for_getme_only": False,
        "telegram_api_called": False,
        "getme_called": False,
        "getme_validation_succeeded": False,
        "getme_response_redacted": True,
        "getme_bot_identity_confirmed": False,
        "bot_id_reported": False,
        "bot_username_reported": False,
        "token_value_printed": False,
        "chat_id_value_printed": False,
        "token_snippet_reported": False,
        "chat_id_snippet_reported": False,
        "exact_length_reported": False,
        "hash_or_digest_reported": False,
        "request_url_printed": False,
        "raw_response_printed": False,
        "api_error_redacted": True,
        "sendmessage_called": False,
        "getupdates_called": False,
        "live_adapter_enabled_now": False,
        "live_posting_enabled_now": False,
        "scheduler_allowed_now": False,
        "provider_llm_api_allowed_now": False,
        "repo_web_search_allowed_now_except_official_docs": False,
        "scraping_allowed_now": False,
        "backend_server_required": False,
        "publish_all_button_enabled_now": False,
        "one_button_publish_all_enabled_now": False,
        "final_social_copy_generated": False,
        "manual_review_required": True,
        "not_public_postable": True,
        "next_gate_required_before_posting": True,
        "channel_write_permission_validated": False,
        "channel_posting_validated": False,
        "kill_switch_status": "active",
        "blocked_action_policy": {
            "sendMessage": "blocked",
            "getUpdates": "blocked",
            "setWebhook": "blocked",
            "deleteWebhook": "blocked",
            "any_method_except_getme": "blocked",
            "live_posting": "blocked",
            "scheduler": "blocked",
            "live_adapter": "blocked",
            "value_or_snippet_output": "blocked",
            "request_url_output": "blocked",
            "raw_response_output": "blocked",
        },
        "safety_policy": {
            "redacted_only": True,
            "getme_only": True,
            "request_budget_enforced": True,
            "no_values": True,
            "no_snippets": True,
            "no_lengths_or_hashes": True,
            "no_request_url": True,
            "no_channel_write_validation": True,
        },
        "blocked_reasons": [],
        "packet_status": "blocked",
    }


def verify_official_docs(fetched_docs=None, _live_fetcher=None):
    """Return (verified, source_domain, fetch_count, notes) for getMe official docs.

    fetched_docs: optional dict of already-fetched official-docs facts (test path).
    _live_fetcher: optional callable for a real bounded fetch (max 3) from
                   core.telegram.org. Never used to fetch any non-official domain.
    """
    if fetched_docs is not None:
        domain = fetched_docs.get("source_domain", "none")
        if domain != OFFICIAL_DOCS_DOMAIN:
            return (False, "none", 0, ["official_docs_domain_not_allowlisted"])
        notes = list(fetched_docs.get("notes", DEFAULT_OFFICIAL_DOCS_NOTES))
        count = int(fetched_docs.get("fetch_count", 1))
        if count > OFFICIAL_DOCS_FETCH_BUDGET:
            return (False, OFFICIAL_DOCS_DOMAIN, count, ["official_docs_fetch_budget_exceeded"])
        return (bool(fetched_docs.get("verified", True)), OFFICIAL_DOCS_DOMAIN, count, notes)
    if _live_fetcher is None:
        return (False, "none", 0, ["official_docs_not_verified"])
    count, ok = _live_fetcher(OFFICIAL_DOCS_DOMAIN, OFFICIAL_DOCS_FETCH_BUDGET)
    if count > OFFICIAL_DOCS_FETCH_BUDGET:
        return (False, OFFICIAL_DOCS_DOMAIN, count, ["official_docs_fetch_budget_exceeded"])
    return (bool(ok), OFFICIAL_DOCS_DOMAIN, count, list(DEFAULT_OFFICIAL_DOCS_NOTES))


def _redact_getme_result(raw_result):
    """Turn a getMe 'result' object into redacted booleans only.

    Never returns bot id, username, names, or any value.
    """
    if not isinstance(raw_result, dict):
        return {"identity_confirmed": False}
    is_bot = raw_result.get("is_bot") is True
    has_id = "id" in raw_result
    return {"identity_confirmed": bool(is_bot and has_id)}



def run_getme_validation(env_text, api_caller, source_label=None):
    """Run at most one getMe request to validate token identity. Redacted only.

    env_text: approved local env source text (caller-supplied). Never logged/stored.
    api_caller: callable(method_name, token) -> dict with keys:
                {"ok": bool, "result": {...}|None, "error_code": int|None,
                 "description": str|None}
                The caller MUST construct the URL internally and MUST NOT return
                the token, the request URL, or raw headers. Only getMe is allowed.
    Returns a fully-built, redacted packet (call validate_* to fail-close).
    """
    packet = _base_packet()

    if source_label in (
        "OPERATOR_LOCAL_ENV_FILE_PROVIDED_OUT_OF_BAND",
        "APPROVED_LOCAL_ENV_SOURCE_REDACTED",
    ):
        packet["approved_env_source_label"] = source_label
    elif env_text is not None:
        packet["approved_env_source_label"] = "APPROVED_LOCAL_ENV_SOURCE_REDACTED"

    if env_text is None:
        packet["blocked_reasons"] = ["approved_local_env_source_unavailable"]
        packet["packet_status"] = "blocked"
        return packet

    parsed = parse_approved_env_text(env_text)
    token_raw = parsed["TELEGRAM_BOT_TOKEN"]
    chat_raw = parsed["TELEGRAM_TARGET_CHAT_ID"]

    packet["env_source_read_attempted"] = True
    packet["env_source_read_succeeded"] = True
    packet["telegram_bot_token_present"] = _is_present(token_raw)
    packet["telegram_target_chat_id_present"] = _is_present(chat_raw)
    packet["telegram_bot_token_shape_class"] = classify_token_shape(token_raw)
    packet["telegram_target_chat_id_shape_class"] = classify_chat_id_shape(chat_raw)

    if not _is_present(token_raw):
        packet["blocked_reasons"] = ["telegram_bot_token_absent_getme_blocked"]
        packet["packet_status"] = "blocked"
        return packet

    if api_caller is None:
        packet["blocked_reasons"] = ["no_api_caller_supplied_getme_not_run"]
        packet["packet_status"] = "blocked"
        return packet

    packet["telegram_api_allowed_now_for_getme_only"] = True
    packet["credential_validation_attempted"] = True
    packet["credential_validation_method"] = "getMe"


    resp = api_caller(ALLOWED_TELEGRAM_METHOD, token_raw)
    packet["telegram_api_called"] = True
    packet["getme_called"] = True
    packet["telegram_api_request_count"] = 1

    if not isinstance(resp, dict):
        packet["api_error_redacted"] = True
        packet["blocked_reasons"] = ["getme_response_malformed_redacted"]
        packet["packet_status"] = "blocked"
        return packet

    if resp.get("ok") is True:
        redacted = _redact_getme_result(resp.get("result"))
        packet["getme_validation_succeeded"] = True
        packet["getme_bot_identity_confirmed"] = redacted["identity_confirmed"]
        if _is_present(chat_raw) and redacted["identity_confirmed"]:
            packet["packet_status"] = "pass"
        elif redacted["identity_confirmed"]:
            packet["blocked_reasons"] = [
                "target_chat_id_absent_future_live_readiness_incomplete"
            ]
            packet["packet_status"] = "blocked"
        else:
            packet["blocked_reasons"] = ["getme_bot_identity_not_confirmed"]
            packet["packet_status"] = "blocked"
    else:
        packet["getme_validation_succeeded"] = False
        packet["api_error_redacted"] = True
        packet["blocked_reasons"] = ["getme_validation_failed_error_redacted"]
        packet["packet_status"] = "blocked"

    leak = _scan_secret_like(packet)
    if leak:
        packet["telegram_bot_token_shape_class"] = "not_checked_blocked"
        packet["telegram_target_chat_id_shape_class"] = "not_checked_blocked"
        packet["blocked_reasons"] = ["redaction_guard_triggered"]
        packet["getme_bot_identity_confirmed"] = False
        packet["packet_status"] = "blocked"

    return packet



def validate_telegram_official_docs_credential_validation_gate_packet(packet):
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
    if packet.get("gate_mode") != "official_docs_and_getme_credential_validation_no_post":
        errors.append("gate_mode_mismatch")
    if packet.get("candidate_platform_id") != "telegram":
        errors.append("candidate_platform_id_must_be_telegram")

    # Request budget enforcement.
    if packet.get("telegram_api_request_count", 0) > packet.get("telegram_api_request_budget", 1):
        errors.append("telegram_api_request_budget_exceeded")
    if packet.get("official_docs_fetch_count", 0) > packet.get("official_docs_fetch_budget", 3):
        errors.append("official_docs_fetch_budget_exceeded")

    # Only getMe is allowed as a credential-validation method.
    method = packet.get("credential_validation_method")
    if method not in ("getMe", "none"):
        errors.append("credential_validation_method_must_be_getme_or_none")

    # Official-docs domain allowlist.
    domain = packet.get("official_docs_source_domain")
    if domain not in (OFFICIAL_DOCS_DOMAIN, "none"):
        errors.append("official_docs_source_domain_not_allowlisted")

    label = packet.get("approved_env_source_label")
    if label not in (
        "OPERATOR_LOCAL_ENV_FILE_PROVIDED_OUT_OF_BAND",
        "APPROVED_LOCAL_ENV_SOURCE_REDACTED",
        "unavailable",
    ):
        errors.append("approved_env_source_label_invalid")

    errors += _scan_secret_like(packet)
    errors += _scan_unsafe(packet)

    status = packet.get("packet_status")
    if status == "pass" and errors:
        errors.append("packet_status_pass_but_errors_exist")

    return {"valid": len(errors) == 0, "errors": errors}



def summary(env_text=None, api_caller=None, source_label=None, fetched_docs=None):
    """Return a JSON-serializable redacted summary. No values, snippets, or paths.

    When env_text/api_caller are None, returns a fail-closed BLOCKED summary.
    fetched_docs: optional pre-fetched official-docs facts (core.telegram.org only).
    """
    verified, domain, fetch_count, notes = verify_official_docs(fetched_docs=fetched_docs)

    packet = run_getme_validation(env_text=env_text, api_caller=api_caller, source_label=source_label)
    packet["official_docs_verification_attempted"] = fetched_docs is not None
    packet["official_docs_source_domain"] = domain
    packet["official_docs_verified"] = verified
    packet["official_docs_fetch_count"] = fetch_count
    packet["official_docs_notes"] = notes

    res = validate_telegram_official_docs_credential_validation_gate_packet(packet)
    return {
        "packet_status": packet.get("packet_status"),
        "validation_valid": res["valid"],
        "task_label": packet.get("task_label"),
        "gate_mode": packet.get("gate_mode"),
        "candidate_platform_id": packet.get("candidate_platform_id"),
        "linked_presence_check_task": packet.get("linked_presence_check_task"),
        "approved_env_source_label": packet.get("approved_env_source_label"),
        "env_source_read_attempted": packet.get("env_source_read_attempted"),
        "env_source_read_succeeded": packet.get("env_source_read_succeeded"),
        "telegram_bot_token_present": packet.get("telegram_bot_token_present"),
        "telegram_target_chat_id_present": packet.get("telegram_target_chat_id_present"),
        "telegram_bot_token_shape_class": packet.get("telegram_bot_token_shape_class"),
        "telegram_target_chat_id_shape_class": packet.get("telegram_target_chat_id_shape_class"),
        "official_docs_verification_attempted": packet.get("official_docs_verification_attempted"),
        "official_docs_source_domain": packet.get("official_docs_source_domain"),
        "official_docs_verified": packet.get("official_docs_verified"),
        "official_docs_fetch_count": packet.get("official_docs_fetch_count"),
        "official_docs_fetch_budget": packet.get("official_docs_fetch_budget"),
        "official_docs_notes": packet.get("official_docs_notes"),
        "credential_validation_attempted": packet.get("credential_validation_attempted"),
        "credential_validation_method": packet.get("credential_validation_method"),
        "telegram_api_request_count": packet.get("telegram_api_request_count"),
        "telegram_api_request_budget": packet.get("telegram_api_request_budget"),
        "telegram_api_allowed_now_for_getme_only": packet.get("telegram_api_allowed_now_for_getme_only"),
        "telegram_api_called": packet.get("telegram_api_called"),
        "getme_called": packet.get("getme_called"),
        "getme_validation_succeeded": packet.get("getme_validation_succeeded"),
        "getme_response_redacted": packet.get("getme_response_redacted"),
        "getme_bot_identity_confirmed": packet.get("getme_bot_identity_confirmed"),
        "bot_id_reported": packet.get("bot_id_reported"),
        "bot_username_reported": packet.get("bot_username_reported"),
        "token_value_printed": packet.get("token_value_printed"),
        "chat_id_value_printed": packet.get("chat_id_value_printed"),
        "token_snippet_reported": packet.get("token_snippet_reported"),
        "chat_id_snippet_reported": packet.get("chat_id_snippet_reported"),
        "exact_length_reported": packet.get("exact_length_reported"),
        "hash_or_digest_reported": packet.get("hash_or_digest_reported"),
        "request_url_printed": packet.get("request_url_printed"),
        "raw_response_printed": packet.get("raw_response_printed"),
        "api_error_redacted": packet.get("api_error_redacted"),
        "sendmessage_called": packet.get("sendmessage_called"),
        "getupdates_called": packet.get("getupdates_called"),
        "live_adapter_enabled_now": packet.get("live_adapter_enabled_now"),
        "live_posting_enabled_now": packet.get("live_posting_enabled_now"),
        "scheduler_allowed_now": packet.get("scheduler_allowed_now"),
        "provider_llm_api_allowed_now": packet.get("provider_llm_api_allowed_now"),
        "repo_web_search_allowed_now_except_official_docs": packet.get("repo_web_search_allowed_now_except_official_docs"),
        "scraping_allowed_now": packet.get("scraping_allowed_now"),
        "backend_server_required": packet.get("backend_server_required"),
        "publish_all_button_enabled_now": packet.get("publish_all_button_enabled_now"),
        "one_button_publish_all_enabled_now": packet.get("one_button_publish_all_enabled_now"),
        "final_social_copy_generated": packet.get("final_social_copy_generated"),
        "manual_review_required": packet.get("manual_review_required"),
        "not_public_postable": packet.get("not_public_postable"),
        "next_gate_required_before_posting": packet.get("next_gate_required_before_posting"),
        "channel_write_permission_validated": packet.get("channel_write_permission_validated"),
        "channel_posting_validated": packet.get("channel_posting_validated"),
        "kill_switch_status": packet.get("kill_switch_status"),
        "secret_like_value_detected_count": len(_scan_secret_like(packet)),
        "unsafe_language_count": len(_scan_unsafe(packet)),
        "blocked_reasons": packet.get("blocked_reasons", []),
    }
