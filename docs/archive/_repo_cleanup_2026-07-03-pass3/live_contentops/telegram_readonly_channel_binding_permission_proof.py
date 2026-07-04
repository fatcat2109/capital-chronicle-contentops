"""Telegram live read-only channel binding permission proof.

Strict read-only proof gate for Telegram channel binding. It can perform at most
three read-only Telegram Bot API calls: getMe, getChat, getChatMember.
It never persists raw tokens, raw URLs, raw headers, raw responses, channel IDs,
user IDs, token-derived hashes, token prefixes, token suffixes, or token length.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable, Mapping
import json
import os
import re

TASK_LABEL = "TASK_CONTENTOPS_TELEGRAM_READONLY_CHANNEL_BINDING_PERMISSION_PROOF_V0"
REPAIR_TASK_LABEL = "TASK_CONTENTOPS_TELEGRAM_READONLY_CHANNEL_BINDING_PERMISSION_PROOF_R1_REPAIR_PATCH_V0"
PACKET_REL_DIR = Path("docs/automation/TELEGRAM_READONLY_CHANNEL_BINDING_PERMISSION_PROOF")

ALLOWED_HOST = "api.telegram.org"
ALLOWED_SCHEME = "https"
ALLOWED_METHODS = ("getMe", "getChat", "getChatMember")
REQUEST_BUDGET_MAX = 3
TIMEOUT_SECONDS = 10
FLAG_WRITE = "--write-telegram-readonly-channel-binding-permission-proof"
FLAG_OPERATOR_GO = "--operator-go-telegram-readonly-proof"
FLAG_EXECUTE = "--execute-telegram-readonly-proof"

PRIMARY_TOKEN_KEYS = ("TELEGRAM_BOT_TOKEN",)
PRIMARY_CHANNEL_KEYS = ("TELEGRAM_CHANNEL_ID",)
ALIAS_TOKEN_KEYS = ("TELEGRAM_BOT_API_TOKEN", "CONTENTOPS_TELEGRAM_BOT_TOKEN")
ALIAS_CHANNEL_KEYS = (
    "TELEGRAM_TARGET_CHANNEL_ID",
    "TELEGRAM_CHAT_ID",
    "CONTENTOPS_TELEGRAM_CHANNEL_ID_OR_HANDLE",
)
TOKEN_KEYS = PRIMARY_TOKEN_KEYS + ALIAS_TOKEN_KEYS
CHANNEL_KEYS = PRIMARY_CHANNEL_KEYS + ALIAS_CHANNEL_KEYS

PASS_READONLY_PROOF = "PASS_READONLY_PROOF"
BLOCKED_MISSING_CREDENTIAL = "BLOCKED_MISSING_CREDENTIAL"
BLOCKED_MISSING_CHANNEL_ID = "BLOCKED_MISSING_CHANNEL_ID"
BLOCKED_GETME_FAILED = "BLOCKED_GETME_FAILED"
BLOCKED_GETCHAT_FAILED = "BLOCKED_GETCHAT_FAILED"
BLOCKED_NOT_CHANNEL = "BLOCKED_NOT_CHANNEL"
BLOCKED_GETCHATMEMBER_FAILED = "BLOCKED_GETCHATMEMBER_FAILED"
BLOCKED_BOT_NOT_ADMIN = "BLOCKED_BOT_NOT_ADMIN"
BLOCKED_BOT_CANNOT_POST_MESSAGES = "BLOCKED_BOT_CANNOT_POST_MESSAGES"
BLOCKED_ALLOWLIST_VIOLATION = "BLOCKED_ALLOWLIST_VIOLATION"
BLOCKED_SECRET_REDACTION_FAILURE = "BLOCKED_SECRET_REDACTION_FAILURE"
BLOCKED_REQUEST_BUDGET_EXCEEDED = "BLOCKED_REQUEST_BUDGET_EXCEEDED"
BLOCKED_NETWORK_OR_TIMEOUT_ERROR = "BLOCKED_NETWORK_OR_TIMEOUT_ERROR"
BLOCKED_OPERATOR_GO_REQUIRED = "BLOCKED_OPERATOR_GO_REQUIRED"
BLOCKED_EXECUTION_FLAG_REQUIRED = "BLOCKED_EXECUTION_FLAG_REQUIRED"

RESULT_CLASSES = (
    PASS_READONLY_PROOF,
    BLOCKED_MISSING_CREDENTIAL,
    BLOCKED_MISSING_CHANNEL_ID,
    BLOCKED_GETME_FAILED,
    BLOCKED_GETCHAT_FAILED,
    BLOCKED_NOT_CHANNEL,
    BLOCKED_GETCHATMEMBER_FAILED,
    BLOCKED_BOT_NOT_ADMIN,
    BLOCKED_BOT_CANNOT_POST_MESSAGES,
    BLOCKED_ALLOWLIST_VIOLATION,
    BLOCKED_SECRET_REDACTION_FAILURE,
    BLOCKED_REQUEST_BUDGET_EXCEEDED,
    BLOCKED_NETWORK_OR_TIMEOUT_ERROR,
    BLOCKED_OPERATOR_GO_REQUIRED,
    BLOCKED_EXECUTION_FLAG_REQUIRED,
)

FORBIDDEN_TELEGRAM_METHOD_FRAGMENTS = (
    "send", "copy", "forward", "edit", "delete", "pin", "unpin", "ban",
    "unban", "restrict", "promote", "set", "create", "answer", "leave",
    "approve", "decline", "revoke", "upload", "stop", "refund", "webhook",
    "updates", "invite",
)

_FORBIDDEN_PARAM_NAME_FRAGMENTS = ("token", "header", "authorization", "url", "secret", "password")
_SECRET_PATTERNS = (
    re.compile(r"\d{6,}:[A-Za-z0-9_-]{30,}"),
    re.compile(r"api\.telegram\.org/bot", re.IGNORECASE),
    re.compile(r"(?i)bearer\s+[A-Za-z0-9._\-]{10,}"),
    re.compile(r"(?im)^\s*(?:export\s+)?[A-Z0-9_]*(?:TOKEN|SECRET|KEY|PASSWORD|CHAT_ID)[A-Z0-9_]*\s*=\s*\S+"),
    re.compile(r"(?<!\d)-?\d{7,}(?!\d)"),
    re.compile(r"@[A-Za-z0-9_]{3,}"),
)
_FORBIDDEN_PACKET_KEYS = {
    "token", "bot_token", "access_token", "secret", "password", "chat_id",
    "user_id", "id", "username", "invite_link", "raw_url", "raw_request",
    "raw_response", "headers", "authorization", "result", "url",
}
_SCHEMA_LIST_KEYS = {
    "allowed_methods", "redacted_field_classes", "official_docs_methods",
    "forbidden_method_fragments", "packet_files_written", "canonical_packet_files",
    "legacy_packet_aliases", "token_keys_checked", "channel_keys_checked",
    "param_allowlist", "allowed_param_names", "result_classes", "changed_files",
    "files_inspected", "tests_run", "credential_key_names_checked",
    "starting_head", "previous_accepted_baseline", "final_head", "origin_master_sha_after_push",
}


@dataclass(frozen=True)
class TelegramReadonlyProbeStep:
    step_name: str
    telegram_method: str
    request_index: int
    required_params: tuple[str, ...]
    host: str = ALLOWED_HOST
    scheme: str = ALLOWED_SCHEME
    http_method: str = "GET"
    read_only: bool = True
    write_allowed: bool = False
    retry_allowed: bool = False
    raw_response_persisted: bool = False


@dataclass(frozen=True)
class TelegramReadonlyProbePlan:
    task_label: str
    repair_task_label: str
    allowed_host: str
    allowed_scheme: str
    allowed_methods: tuple[str, ...]
    param_allowlist: Mapping[str, tuple[str, ...]]
    request_budget_max: int
    timeout_seconds: int
    retry_allowed: bool
    raw_response_persisted: bool
    raw_headers_persisted: bool
    token_persisted: bool
    live_write_allowed_now: bool
    send_permission_unlocked_now: bool
    steps: tuple[TelegramReadonlyProbeStep, ...]


@dataclass(frozen=True)
class TelegramReadonlyRawResultEnvelope:
    ok: bool
    method: str
    status_code: int | None
    body: Mapping[str, Any] | None
    error_class: str | None = None


@dataclass(frozen=True)
class CredentialSelection:
    selected_key_name: str | None
    key_presence_by_name: Mapping[str, bool]
    key_names_checked: tuple[str, ...]


@dataclass(frozen=True)
class TelegramReadonlyProofState:
    result_classification: str
    blocked_reasons: tuple[str, ...]
    get_me_ok: bool
    get_chat_ok: bool
    get_chat_member_ok: bool
    bot_identity_seen_redacted: bool
    chat_seen_redacted: bool
    chat_type_class: str
    membership_status_class: str
    bot_admin_confirmed_redacted: bool
    can_post_messages_confirmed_redacted: bool
    channel_binding_status: str
    channel_permission_status: str
    request_budget_used: int
    retry_count: int
    live_read_only_request_performed: bool
    live_write_allowed_now: bool
    send_permission_unlocked_now: bool
    no_raw_response_persisted: bool
    redaction_verified: bool
    credential_key_names_checked: tuple[str, ...]
    credential_key_presence: Mapping[str, bool]
    selected_credential_key_name: str | None
    channel_key_names_checked: tuple[str, ...]
    channel_key_presence: Mapping[str, bool]
    selected_channel_key_name: str | None
    channel_id_presence_status: str


class TelegramReadonlyProofError(RuntimeError):
    """Fail-closed Telegram read-only proof error."""


def _param_allowlist() -> dict[str, tuple[str, ...]]:
    return {"getMe": (), "getChat": ("chat_id",), "getChatMember": ("chat_id", "user_id")}


def build_telegram_readonly_probe_plan() -> TelegramReadonlyProbePlan:
    allowed_params = _param_allowlist()
    steps = tuple(
        TelegramReadonlyProbeStep(
            step_name=f"telegram_readonly_{method}",
            telegram_method=method,
            request_index=index,
            required_params=allowed_params[method],
        )
        for index, method in enumerate(ALLOWED_METHODS, start=1)
    )
    return TelegramReadonlyProbePlan(
        task_label=TASK_LABEL,
        repair_task_label=REPAIR_TASK_LABEL,
        allowed_host=ALLOWED_HOST,
        allowed_scheme=ALLOWED_SCHEME,
        allowed_methods=ALLOWED_METHODS,
        param_allowlist=allowed_params,
        request_budget_max=REQUEST_BUDGET_MAX,
        timeout_seconds=TIMEOUT_SECONDS,
        retry_allowed=False,
        raw_response_persisted=False,
        raw_headers_persisted=False,
        token_persisted=False,
        live_write_allowed_now=False,
        send_permission_unlocked_now=False,
        steps=steps,
    )


def validate_telegram_readonly_allowlist(
    method: str,
    host: str = ALLOWED_HOST,
    params: Mapping[str, Any] | None = None,
) -> None:
    if host != ALLOWED_HOST:
        raise TelegramReadonlyProofError(BLOCKED_ALLOWLIST_VIOLATION)
    if method not in ALLOWED_METHODS:
        raise TelegramReadonlyProofError(BLOCKED_ALLOWLIST_VIOLATION)
    lower_method = method.lower()
    if any(fragment in lower_method for fragment in FORBIDDEN_TELEGRAM_METHOD_FRAGMENTS):
        raise TelegramReadonlyProofError(BLOCKED_ALLOWLIST_VIOLATION)
    provided = set((params or {}).keys())
    for key in provided:
        lowered = str(key).lower()
        if any(fragment in lowered for fragment in _FORBIDDEN_PARAM_NAME_FRAGMENTS):
            raise TelegramReadonlyProofError(BLOCKED_ALLOWLIST_VIOLATION)
    expected = set(_param_allowlist()[method])
    if provided != expected:
        raise TelegramReadonlyProofError(BLOCKED_ALLOWLIST_VIOLATION)
    for key in expected:
        if (params or {}).get(key) in (None, ""):
            raise TelegramReadonlyProofError(BLOCKED_ALLOWLIST_VIOLATION)


def validate_telegram_readonly_request_budget(request_count: int) -> None:
    if request_count < 0 or request_count > REQUEST_BUDGET_MAX:
        raise TelegramReadonlyProofError(BLOCKED_REQUEST_BUDGET_EXCEEDED)


def select_secret_key(env: Mapping[str, str], keys: tuple[str, ...]) -> CredentialSelection:
    presence = {key: bool(env.get(key)) for key in keys}
    selected = next((key for key in keys if presence[key]), None)
    return CredentialSelection(selected, presence, keys)


def _read_scoped_repo_env_files(repo_root: str | Path | None = None) -> dict[str, str]:
    root = Path(repo_root) if repo_root is not None else Path(__file__).resolve().parents[1]
    allowed_keys = set(TOKEN_KEYS + CHANNEL_KEYS)
    scoped: dict[str, str] = {}
    for filename in (".env", ".env.local"):
        path = root / filename
        if not path.exists() or not path.is_file():
            continue
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            key, value = stripped.split("=", 1)
            key = key.strip()
            if key.startswith("export "):
                key = key[7:].strip()
            if key not in allowed_keys:
                continue
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in {'\"', "'"}:
                value = value[1:-1]
            if value:
                scoped[key] = value
    return scoped


def _default_env_provider() -> Mapping[str, str]:
    env = dict(getattr(os, "environ"))
    env.update(_read_scoped_repo_env_files())
    return env


def scan_packet_for_telegram_secret_risk(obj: Any) -> list[str]:
    violations: list[str] = []

    def walk(node: Any, key: str | None = None) -> None:
        if isinstance(node, Mapping):
            for k, v in node.items():
                k_text = str(k)
                if k_text.lower() in _FORBIDDEN_PACKET_KEYS:
                    violations.append(f"forbidden_key:{k_text.lower()}")
                walk(v, k_text)
        elif isinstance(node, (list, tuple)):
            for item in node:
                walk(item, key)
        elif isinstance(node, str):
            if key in _SCHEMA_LIST_KEYS:
                return
            for pattern in _SECRET_PATTERNS:
                if pattern.search(node):
                    violations.append(f"secret_like_value:{key or 'value'}")
                    break

    walk(obj)
    return sorted(set(violations))


def assert_no_telegram_secret_output(obj: Any) -> None:
    violations = scan_packet_for_telegram_secret_risk(obj)
    if violations:
        raise TelegramReadonlyProofError(BLOCKED_SECRET_REDACTION_FAILURE + ":" + ",".join(violations))


def classify_telegram_chat_type(chat_payload: Mapping[str, Any] | None) -> str:
    if not isinstance(chat_payload, Mapping):
        return "chat_type_unknown_redacted"
    chat_type = chat_payload.get("type")
    if chat_type == "channel":
        return "telegram_channel_confirmed_redacted"
    if chat_type in {"group", "supergroup", "private"}:
        return f"telegram_{chat_type}_not_channel_redacted"
    return "chat_type_unknown_redacted"


def classify_telegram_member_permission(member_payload: Mapping[str, Any] | None) -> tuple[str, bool, bool]:
    if not isinstance(member_payload, Mapping):
        return "membership_unknown_redacted", False, False
    status = str(member_payload.get("status") or "unknown")
    is_admin = status in {"administrator", "creator"}
    can_post = True if status == "creator" else bool(member_payload.get("can_post_messages")) if is_admin else False
    if status == "creator":
        membership = "bot_channel_creator_confirmed_redacted"
    elif status == "administrator":
        membership = "bot_channel_administrator_confirmed_redacted"
    elif status in {"member", "restricted", "left", "kicked"}:
        membership = f"bot_channel_{status}_not_admin_redacted"
    else:
        membership = "membership_unknown_redacted"
    return membership, is_admin, can_post


def _result_body(envelope: TelegramReadonlyRawResultEnvelope | None) -> Mapping[str, Any] | None:
    if envelope and envelope.ok and isinstance(envelope.body, Mapping):
        result = envelope.body.get("result")
        if isinstance(result, Mapping):
            return result
    return None


def _empty_state(
    result_classification: str,
    blocked_reasons: list[str],
    token_selection: CredentialSelection,
    channel_selection: CredentialSelection,
    request_count: int = 0,
) -> TelegramReadonlyProofState:
    return TelegramReadonlyProofState(
        result_classification=result_classification,
        blocked_reasons=tuple(blocked_reasons),
        get_me_ok=False,
        get_chat_ok=False,
        get_chat_member_ok=False,
        bot_identity_seen_redacted=False,
        chat_seen_redacted=False,
        chat_type_class="not_executed",
        membership_status_class="not_executed",
        bot_admin_confirmed_redacted=False,
        can_post_messages_confirmed_redacted=False,
        channel_binding_status="blocked_not_confirmed_redacted",
        channel_permission_status="blocked_not_confirmed_redacted",
        request_budget_used=request_count,
        retry_count=0,
        live_read_only_request_performed=request_count > 0,
        live_write_allowed_now=False,
        send_permission_unlocked_now=False,
        no_raw_response_persisted=True,
        redaction_verified=True,
        credential_key_names_checked=token_selection.key_names_checked,
        credential_key_presence=token_selection.key_presence_by_name,
        selected_credential_key_name=token_selection.selected_key_name,
        channel_key_names_checked=channel_selection.key_names_checked,
        channel_key_presence=channel_selection.key_presence_by_name,
        selected_channel_key_name=channel_selection.selected_key_name,
        channel_id_presence_status="present" if channel_selection.selected_key_name else "missing",
    )


def _state_from_envelopes(
    result_classification: str,
    blocked_reasons: list[str],
    envelopes: list[TelegramReadonlyRawResultEnvelope],
    token_selection: CredentialSelection,
    channel_selection: CredentialSelection,
) -> TelegramReadonlyProofState:
    by_method = {envelope.method: envelope for envelope in envelopes}
    get_me = by_method.get("getMe")
    get_chat = by_method.get("getChat")
    get_chat_member = by_method.get("getChatMember")
    get_me_payload = _result_body(get_me)
    chat_payload = _result_body(get_chat)
    member_payload = _result_body(get_chat_member)
    chat_type_class = classify_telegram_chat_type(chat_payload)
    membership_class, is_admin, can_post = classify_telegram_member_permission(member_payload)
    channel_binding = (
        "channel_binding_confirmed_redacted"
        if bool(get_chat and get_chat.ok) and chat_type_class == "telegram_channel_confirmed_redacted"
        else "channel_binding_unconfirmed_redacted"
    )
    channel_permission = (
        "can_post_messages_confirmed_redacted"
        if is_admin and can_post else
        "administrator_without_can_post_messages_redacted"
        if is_admin else
        "bot_not_channel_administrator_redacted"
    )
    return TelegramReadonlyProofState(
        result_classification=result_classification,
        blocked_reasons=tuple(blocked_reasons),
        get_me_ok=bool(get_me and get_me.ok),
        get_chat_ok=bool(get_chat and get_chat.ok),
        get_chat_member_ok=bool(get_chat_member and get_chat_member.ok),
        bot_identity_seen_redacted=bool(isinstance(get_me_payload, Mapping) and get_me_payload.get("is_bot") is True),
        chat_seen_redacted=bool(chat_payload),
        chat_type_class=chat_type_class,
        membership_status_class=membership_class,
        bot_admin_confirmed_redacted=is_admin,
        can_post_messages_confirmed_redacted=can_post,
        channel_binding_status=channel_binding,
        channel_permission_status=channel_permission,
        request_budget_used=len(envelopes),
        retry_count=0,
        live_read_only_request_performed=bool(envelopes),
        live_write_allowed_now=False,
        send_permission_unlocked_now=False,
        no_raw_response_persisted=True,
        redaction_verified=True,
        credential_key_names_checked=token_selection.key_names_checked,
        credential_key_presence=token_selection.key_presence_by_name,
        selected_credential_key_name=token_selection.selected_key_name,
        channel_key_names_checked=channel_selection.key_names_checked,
        channel_key_presence=channel_selection.key_presence_by_name,
        selected_channel_key_name=channel_selection.selected_key_name,
        channel_id_presence_status="present" if channel_selection.selected_key_name else "missing",
    )


def _telegram_api_call(method: str, token: str, params: Mapping[str, Any] | None = None) -> TelegramReadonlyRawResultEnvelope:
    from urllib import error as _error
    from urllib import parse as _parse
    from urllib import request as _request

    validate_telegram_readonly_allowlist(method, ALLOWED_HOST, params)
    query = _parse.urlencode(dict(params or {}))
    url = f"https://{ALLOWED_HOST}/bot{token}/{method}"
    if query:
        url += "?" + query
    req = _request.Request(url, method="GET")
    try:
        with _request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
            status = resp.getcode()
            body_text = resp.read().decode("utf-8")
        body = json.loads(body_text)
        return TelegramReadonlyRawResultEnvelope(bool(body.get("ok")), method, status, body, None)
    except _error.HTTPError as exc:
        return TelegramReadonlyRawResultEnvelope(False, method, exc.code, None, "http_error_redacted")
    except Exception:
        return TelegramReadonlyRawResultEnvelope(False, method, None, None, "network_or_timeout_error_redacted")


def _call_readonly(
    api_caller: Callable[[str, str, Mapping[str, Any] | None], TelegramReadonlyRawResultEnvelope],
    method: str,
    token: str,
    params: Mapping[str, Any] | None,
    envelopes: list[TelegramReadonlyRawResultEnvelope],
) -> TelegramReadonlyRawResultEnvelope:
    validate_telegram_readonly_allowlist(method, ALLOWED_HOST, params)
    validate_telegram_readonly_request_budget(len(envelopes) + 1)
    envelope = api_caller(method, token, params)
    envelopes.append(envelope)
    validate_telegram_readonly_request_budget(len(envelopes))
    return envelope


def run_telegram_readonly_channel_binding_permission_proof(
    *,
    write: bool = False,
    operator_go: bool = False,
    execution_requested: bool = False,
    repo_root: str | Path | None = None,
    env_provider: Callable[[], Mapping[str, str]] | None = None,
    token_provider: Callable[[], str | None] | None = None,
    chat_provider: Callable[[], str | None] | None = None,
    api_caller: Callable[[str, str, Mapping[str, Any] | None], TelegramReadonlyRawResultEnvelope] | None = None,
) -> dict[str, Any]:
    env = dict((env_provider or _default_env_provider)())
    if token_provider is not None:
        token_value = token_provider()
        if token_value:
            env = {**env, PRIMARY_TOKEN_KEYS[0]: token_value}
    if chat_provider is not None:
        channel_value = chat_provider()
        if channel_value:
            env = {**env, PRIMARY_CHANNEL_KEYS[0]: channel_value}

    token_selection = select_secret_key(env, TOKEN_KEYS)
    channel_selection = select_secret_key(env, CHANNEL_KEYS)
    blockers: list[str] = []
    envelopes: list[TelegramReadonlyRawResultEnvelope] = []
    api_caller = api_caller or _telegram_api_call

    def finish(result_class: str) -> TelegramReadonlyProofState:
        state = (
            _state_from_envelopes(result_class, blockers, envelopes, token_selection, channel_selection)
            if envelopes else
            _empty_state(result_class, blockers, token_selection, channel_selection)
        )
        return _write_and_output_state(state, write, operator_go, execution_requested, repo_root)

    if not operator_go:
        blockers.append(BLOCKED_OPERATOR_GO_REQUIRED)
        return finish(BLOCKED_OPERATOR_GO_REQUIRED)
    if not execution_requested:
        blockers.append(BLOCKED_EXECUTION_FLAG_REQUIRED)
        return finish(BLOCKED_EXECUTION_FLAG_REQUIRED)
    if not token_selection.selected_key_name:
        blockers.append(BLOCKED_MISSING_CREDENTIAL)
        return finish(BLOCKED_MISSING_CREDENTIAL)
    if not channel_selection.selected_key_name:
        blockers.append(BLOCKED_MISSING_CHANNEL_ID)
        return finish(BLOCKED_MISSING_CHANNEL_ID)

    token = env[token_selection.selected_key_name]
    channel_value = env[channel_selection.selected_key_name]

    try:
        get_me = _call_readonly(api_caller, "getMe", token, None, envelopes)
        if not get_me.ok:
            blockers.append(BLOCKED_GETME_FAILED)
            return finish(BLOCKED_GETME_FAILED)
        bot_payload = _result_body(get_me)
        bot_user_identifier = bot_payload.get("id") if isinstance(bot_payload, Mapping) else None
        if bot_user_identifier in (None, ""):
            blockers.append(BLOCKED_GETME_FAILED)
            return finish(BLOCKED_GETME_FAILED)

        get_chat = _call_readonly(api_caller, "getChat", token, {"chat_id": channel_value}, envelopes)
        if not get_chat.ok:
            blockers.append(BLOCKED_GETCHAT_FAILED)
            return finish(BLOCKED_GETCHAT_FAILED)
        chat_payload = _result_body(get_chat)
        if classify_telegram_chat_type(chat_payload) != "telegram_channel_confirmed_redacted":
            blockers.append(BLOCKED_NOT_CHANNEL)
            return finish(BLOCKED_NOT_CHANNEL)

        get_member = _call_readonly(
            api_caller,
            "getChatMember",
            token,
            {"chat_id": channel_value, "user_id": bot_user_identifier},
            envelopes,
        )
        if not get_member.ok:
            blockers.append(BLOCKED_GETCHATMEMBER_FAILED)
            return finish(BLOCKED_GETCHATMEMBER_FAILED)
        member_payload = _result_body(get_member)
        _membership, is_admin, can_post = classify_telegram_member_permission(member_payload)
        if not is_admin:
            blockers.append(BLOCKED_BOT_NOT_ADMIN)
            return finish(BLOCKED_BOT_NOT_ADMIN)
        if not can_post:
            blockers.append(BLOCKED_BOT_CANNOT_POST_MESSAGES)
            return finish(BLOCKED_BOT_CANNOT_POST_MESSAGES)
        return finish(PASS_READONLY_PROOF)
    except TelegramReadonlyProofError as exc:
        result = str(exc).split(":", 1)[0]
        blockers.append(result if result in RESULT_CLASSES else BLOCKED_ALLOWLIST_VIOLATION)
        return finish(blockers[-1])
    finally:
        token = None
        channel_value = None
        bot_user_identifier = None if "bot_user_identifier" in locals() else None


def _packet_base(state: TelegramReadonlyProofState, operator_go: bool, execution_requested: bool) -> dict[str, Any]:
    plan = build_telegram_readonly_probe_plan()
    packet = {
        "task_label": TASK_LABEL,
        "repair_task_label": REPAIR_TASK_LABEL,
        "result_classification": state.result_classification,
        "blocked_reasons": list(state.blocked_reasons),
        "platform": "telegram_channel_destination",
        "official_docs_checked": True,
        "official_docs_host": "core.telegram.org",
        "official_docs_methods": list(ALLOWED_METHODS),
        "bot_api_request_format_verified": "telegram_bot_api_token_path_method_name_format_verified_redacted",
        "allowed_host": ALLOWED_HOST,
        "allowed_scheme": ALLOWED_SCHEME,
        "allowed_methods": list(ALLOWED_METHODS),
        "param_allowlist": {k: list(v) for k, v in _param_allowlist().items()},
        "allowed_param_names": ["chat_id", "user_id"],
        "forbidden_method_fragments": list(FORBIDDEN_TELEGRAM_METHOD_FRAGMENTS),
        "result_classes": list(RESULT_CLASSES),
        "request_budget_max": REQUEST_BUDGET_MAX,
        "request_budget_used": state.request_budget_used,
        "timeout_seconds": TIMEOUT_SECONDS,
        "retry_count": state.retry_count,
        "operator_go_present": bool(operator_go),
        "execution_requested": bool(execution_requested),
        "credential_key_names_checked": list(state.credential_key_names_checked),
        "credential_key_presence": dict(state.credential_key_presence),
        "selected_credential_key_name": state.selected_credential_key_name,
        "channel_key_names_checked": list(state.channel_key_names_checked),
        "channel_key_presence": dict(state.channel_key_presence),
        "selected_channel_key_name": state.selected_channel_key_name,
        "channel_id_presence_status": state.channel_id_presence_status,
        "live_read_only_request_performed": state.live_read_only_request_performed,
        "no_write_endpoint_called": True,
        "no_write_post_send_publish_performed": True,
        "no_raw_request_url_persisted": True,
        "no_raw_response_persisted": True,
        "no_raw_headers_persisted": True,
        "no_token_persisted": True,
        "no_token_logged": True,
        "no_token_hash_digest_prefix_suffix_length": True,
        "no_unredacted_channel_or_user_identifier_persisted": True,
        "no_auto_retry": True,
        "live_write_allowed_now": False,
        "send_permission_unlocked_now": False,
        "dispatchable_now": False,
        "public_postable_now": False,
        "valid_for_live_dispatch_now": False,
        "redacted_field_classes": [
            "bot_identity_seen_redacted_boolean",
            "chat_seen_redacted_boolean",
            "chat_type_class",
            "membership_status_class",
            "can_post_messages_confirmed_redacted_boolean",
            "binding_status_class",
            "permission_status_class",
        ],
        "probe_plan": {
            **asdict(plan),
            "param_allowlist": {k: list(v) for k, v in plan.param_allowlist.items()},
            "steps": [asdict(step) for step in plan.steps],
        },
        "redacted_proof": asdict(state),
    }
    assert_no_telegram_secret_output(packet)
    return packet


def build_telegram_readonly_probe_plan_packet(state: TelegramReadonlyProofState, operator_go: bool, execution_requested: bool) -> dict[str, Any]:
    packet = _packet_base(state, operator_go, execution_requested)
    packet["packet_type"] = "telegram_readonly_probe_plan_packet"
    return packet


def build_telegram_readonly_probe_result_packet(state: TelegramReadonlyProofState, operator_go: bool, execution_requested: bool) -> dict[str, Any]:
    packet = _packet_base(state, operator_go, execution_requested)
    packet["packet_type"] = "telegram_readonly_probe_result_packet"
    packet["status"] = state.result_classification
    return packet


def build_account_binding_update_candidate_packet(state: TelegramReadonlyProofState) -> dict[str, Any]:
    packet = {
        "task_label": TASK_LABEL,
        "repair_task_label": REPAIR_TASK_LABEL,
        "packet_type": "account_binding_update_candidate_packet",
        "result_classification": state.result_classification,
        "account_binding_status_candidate": "read_only_verified_redacted" if state.result_classification == PASS_READONLY_PROOF else "blocked_redacted",
        "permission_status_candidate": state.channel_permission_status,
        "scope_status_candidate": "telegram_channel_can_post_messages_readonly_proof" if state.result_classification == PASS_READONLY_PROOF else "scope_unconfirmed_redacted",
        "destination_binding_id": "telegram_channel_destination_binding_symbolic_redacted",
        "credential_handle_id": "telegram_bot_credential_handle_symbolic_redacted",
        "live_write_allowed_now": False,
        "dispatchable_now": False,
        "public_postable_now": False,
        "valid_for_live_dispatch_now": False,
        "read_only_probe_performed": state.live_read_only_request_performed,
        "request_budget_used": state.request_budget_used,
        "blocked_reasons": list(state.blocked_reasons),
        "manual_fallback_required": state.result_classification != PASS_READONLY_PROOF,
        "no_secret_output": True,
    }
    assert_no_telegram_secret_output(packet)
    return packet


def build_live_gate_update_candidate_packet(state: TelegramReadonlyProofState) -> dict[str, Any]:
    packet = {
        "task_label": TASK_LABEL,
        "repair_task_label": REPAIR_TASK_LABEL,
        "packet_type": "live_gate_update_candidate_packet",
        "result_classification": state.result_classification,
        "live_gate_candidate_state": "readonly_permission_confirmed_but_live_write_locked" if state.result_classification == PASS_READONLY_PROOF else "blocked_redacted",
        "valid_for_live_dispatch_now": False,
        "gate_passed_now": False,
        "live_write_allowed_now": False,
        "request_budget_max": REQUEST_BUDGET_MAX,
        "request_budget_used": state.request_budget_used,
        "no_auto_retry": True,
        "no_write_endpoint_called": True,
        "credential_hydration_performed": False,
        "raw_response_persisted": False,
        "blocked_reasons": list(state.blocked_reasons),
    }
    assert_no_telegram_secret_output(packet)
    return packet


def build_redacted_audit_packet(state: TelegramReadonlyProofState, operator_go: bool, execution_requested: bool) -> dict[str, Any]:
    packet = _packet_base(state, operator_go, execution_requested)
    packet["packet_type"] = "redacted_audit_packet"
    packet["audit_status"] = "pass_redacted" if state.result_classification == PASS_READONLY_PROOF else "blocked_redacted"
    return packet


def build_evidence_packet(state: TelegramReadonlyProofState, operator_go: bool, execution_requested: bool) -> dict[str, Any]:
    packet = _packet_base(state, operator_go, execution_requested)
    packet.update({
        "packet_type": "evidence_packet",
        "status": state.result_classification,
        "starting_head": "9c78db7c2c26ef237d21e6239d25895731303ce4",
        "previous_accepted_baseline": "b74b2898d0c885850052b08eea6c52c6748cfe6b",
        "repo_path": "A:/Capital Chronicle/tools/cc-live-contentops",
        "branch": "master",
        "cli_change_compatibility_only": True,
        "no_ui_change_proof": True,
        "no_browser_qa_proof": True,
        "no_provider_browser_proof": True,
        "canonical_packet_files": canonical_packet_names(),
        "legacy_packet_aliases": legacy_packet_names(),
        "next_recommended_task": "TASK_CONTENTOPS_TELEGRAM_SUPERVISED_SENDMESSAGE_PREP_AND_DRY_RUN_GATE_V0",
        "final_head_self_recording_limitation": "Final commit SHA is unknown before commit; verify final HEAD from git after commit/push.",
    })
    assert_no_telegram_secret_output(packet)
    return packet


def build_legacy_packet(state: TelegramReadonlyProofState, operator_go: bool, execution_requested: bool, packet_type: str) -> dict[str, Any]:
    packet = _packet_base(state, operator_go, execution_requested)
    packet["packet_type"] = packet_type
    packet["legacy_compat_alias"] = True
    packet["canonical_packets"] = canonical_packet_names()
    packet["status"] = state.result_classification
    assert_no_telegram_secret_output(packet)
    return packet


def canonical_packet_names() -> list[str]:
    return [
        "official_docs_grounding.md",
        "telegram_readonly_probe_plan_packet.json",
        "telegram_readonly_probe_result_packet.json",
        "account_binding_update_candidate_packet.json",
        "live_gate_update_candidate_packet.json",
        "redacted_audit_packet.json",
        "implementation_report.md",
        "evidence_packet.json",
        "next_task_pointer.md",
    ]


def legacy_packet_names() -> list[str]:
    return ["audit_packet.json", "redacted_candidate_packet.json", "validation_packet.json"]


def _write_and_output_state(
    state: TelegramReadonlyProofState,
    write: bool,
    operator_go: bool,
    execution_requested: bool,
    repo_root: str | Path | None,
) -> dict[str, Any]:
    evidence = build_evidence_packet(state, operator_go, execution_requested)
    if write:
        root = Path(repo_root) if repo_root is not None else Path(__file__).resolve().parents[1]
        packet_dir = root / PACKET_REL_DIR
        packet_dir.mkdir(parents=True, exist_ok=True)
        json_packets = {
            "telegram_readonly_probe_plan_packet.json": build_telegram_readonly_probe_plan_packet(state, operator_go, execution_requested),
            "telegram_readonly_probe_result_packet.json": build_telegram_readonly_probe_result_packet(state, operator_go, execution_requested),
            "account_binding_update_candidate_packet.json": build_account_binding_update_candidate_packet(state),
            "live_gate_update_candidate_packet.json": build_live_gate_update_candidate_packet(state),
            "redacted_audit_packet.json": build_redacted_audit_packet(state, operator_go, execution_requested),
            "evidence_packet.json": evidence,
            "audit_packet.json": build_legacy_packet(state, operator_go, execution_requested, "legacy_audit_packet_alias"),
            "redacted_candidate_packet.json": build_legacy_packet(state, operator_go, execution_requested, "legacy_redacted_candidate_packet_alias"),
            "validation_packet.json": build_legacy_packet(state, operator_go, execution_requested, "legacy_validation_packet_alias"),
        }
        for filename, packet in json_packets.items():
            assert_no_telegram_secret_output(packet)
            (packet_dir / filename).write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        (packet_dir / "official_docs_grounding.md").write_text(build_official_docs_grounding(), encoding="utf-8")
        (packet_dir / "implementation_report.md").write_text(build_implementation_report(state), encoding="utf-8")
        (packet_dir / "next_task_pointer.md").write_text(build_next_task_pointer(), encoding="utf-8")
    output = {
        "task_label": TASK_LABEL,
        "repair_task_label": REPAIR_TASK_LABEL,
        "status": state.result_classification,
        "result_classification": state.result_classification,
        "blocked_reasons": list(state.blocked_reasons),
        "request_budget_max": REQUEST_BUDGET_MAX,
        "request_budget_used": state.request_budget_used,
        "credential_key_names_checked": list(state.credential_key_names_checked),
        "credential_key_presence": dict(state.credential_key_presence),
        "selected_credential_key_name": state.selected_credential_key_name,
        "channel_key_names_checked": list(state.channel_key_names_checked),
        "channel_key_presence": dict(state.channel_key_presence),
        "selected_channel_key_name": state.selected_channel_key_name,
        "channel_id_presence_status": state.channel_id_presence_status,
        "live_write_allowed_now": False,
        "send_permission_unlocked_now": False,
        "packets_redacted": True,
    }
    assert_no_telegram_secret_output(output)
    return output


def build_official_docs_grounding() -> str:
    return """# Telegram Read-Only Official Docs Grounding

Official docs source: `https://core.telegram.org/bots/api`.

Verified methods and fields:

- `getMe`: read-only bot identity method; no parameters; returns bot `User`.
- `getChat`: read-only chat lookup; requires `chat_id`; returns chat metadata including type.
- `getChatMember`: read-only membership lookup; requires `chat_id` and `user_id`.
- `ChatMemberAdministrator.can_post_messages`: channel posting permission flag for administrators.

Request format summary:

- Telegram Bot API uses token-path method-name request format on `api.telegram.org`.
- This proof stores only symbolic request-format text, never raw URLs.

Safety interpretation:

- Allowed host: `api.telegram.org`.
- Allowed methods: `getMe`, `getChat`, `getChatMember`.
- Allowed parameter names: `chat_id`, `user_id` only in method-specific exact shapes.
- No write/post/send/publish endpoint is called.
- Live write remains locked after read-only proof.
"""


def build_implementation_report(state: TelegramReadonlyProofState) -> str:
    return f"""# Telegram Read-Only Channel Binding Permission Proof R1 Repair

Task: `{TASK_LABEL}`
Repair task: `{REPAIR_TASK_LABEL}`

## Result

- Result classification: `{state.result_classification}`
- Request budget used: `{state.request_budget_used}` of `{REQUEST_BUDGET_MAX}`
- Live read-only request performed: `{state.live_read_only_request_performed}`
- Live write allowed now: `False`
- Send permission unlocked now: `False`

## Stop Conditions

{chr(10).join(f'- `{reason}`' for reason in state.blocked_reasons) if state.blocked_reasons else '- None'}

## Credential Policy

- Credential key names checked only: `{', '.join(state.credential_key_names_checked)}`
- Channel key names checked only: `{', '.join(state.channel_key_names_checked)}`
- Selected credential key name: `{state.selected_credential_key_name}`
- Selected channel key name: `{state.selected_channel_key_name}`
- No token value, length, prefix, suffix, digest, hash, raw URL, raw header, raw response, raw channel ID, or raw user ID persisted.

## CLI Compatibility

- `live_contentops/cli.py` hook retained as compatibility-only.
- Default CLI-style invocation blocks before network.
- Live read-only calls require explicit operator GO and execute flags.

## Candidate Packets

- Account binding candidate never enables live write, dispatch, public posting, or live dispatch validity.
- Live gate candidate never enables gate pass, live write, or live dispatch validity.
"""


def build_next_task_pointer() -> str:
    return """# Next Task Pointer

Recommended next task:

`TASK_CONTENTOPS_TELEGRAM_SUPERVISED_SENDMESSAGE_PREP_AND_DRY_RUN_GATE_V0`

Rationale:

- Read-only binding and permission proof gate is repaired.
- Live write remains locked.
- Next work should prepare supervised sendMessage dry-run gate without sending live messages.
"""


def main() -> int:
    import sys
    args = sys.argv[1:]
    result = run_telegram_readonly_channel_binding_permission_proof(
        write=FLAG_WRITE in args,
        operator_go=FLAG_OPERATOR_GO in args,
        execution_requested=FLAG_EXECUTE in args,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["result_classification"] == PASS_READONLY_PROOF else 1


if __name__ == "__main__":
    raise SystemExit(main())
