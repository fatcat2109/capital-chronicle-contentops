"""Telegram live read-only channel binding permission proof.

This module owns one narrowly-scoped live-read-only proof path for Telegram:
`getMe`, `getChat`, and `getChatMember`, with request budget 3, no retry,
no write/post/send/publish methods, and redacted evidence only.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Callable, Mapping
import json
import os
import re

TASK_LABEL = "TASK_CONTENTOPS_TELEGRAM_READONLY_CHANNEL_BINDING_PERMISSION_PROOF_V0"
PACKET_REL_DIR = Path("docs/automation/TELEGRAM_READONLY_CHANNEL_BINDING_PERMISSION_PROOF")

ALLOWED_HOST = "api.telegram.org"
ALLOWED_SCHEME = "https"
ALLOWED_METHODS = ("getMe", "getChat", "getChatMember")
REQUEST_BUDGET_MAX = 3
TIMEOUT_SECONDS = 10
FLAG_WRITE = "--write-telegram-readonly-channel-binding-permission-proof"
FLAG_OPERATOR_GO = "--operator-go-telegram-readonly-proof"
FLAG_EXECUTE = "--execute-telegram-readonly-proof"

TOKEN_ENV_NAME = "CONTENTOPS_TELEGRAM_BOT_TOKEN"
CHAT_ENV_NAME = "CONTENTOPS_TELEGRAM_CHANNEL_ID_OR_HANDLE"

FORBIDDEN_TELEGRAM_METHOD_FRAGMENTS = (
    "send", "copy", "forward", "edit", "delete", "pin", "unpin", "ban",
    "unban", "restrict", "promote", "set", "create", "answer", "leave",
    "approve", "decline", "revoke", "upload", "stop", "refund",
)

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
    "forbidden_method_fragments", "packet_files_written",
}


@dataclass(frozen=True)
class TelegramReadonlyProbeStep:
    step_name: str
    telegram_method: str
    request_index: int
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
    allowed_host: str
    allowed_scheme: str
    allowed_methods: tuple[str, ...]
    request_budget_max: int
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
class TelegramReadonlyRedactedProof:
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
    request_count: int
    retry_count: int
    live_read_only_request_performed: bool
    live_write_allowed_now: bool
    send_permission_unlocked_now: bool
    no_raw_response_persisted: bool
    redaction_verified: bool


class TelegramReadonlyProofError(RuntimeError):
    """Fail-closed Telegram read-only proof error."""


def build_telegram_readonly_probe_plan() -> TelegramReadonlyProbePlan:
    steps = tuple(
        TelegramReadonlyProbeStep(
            step_name=f"telegram_readonly_{method}",
            telegram_method=method,
            request_index=index,
        )
        for index, method in enumerate(ALLOWED_METHODS, start=1)
    )
    return TelegramReadonlyProbePlan(
        task_label=TASK_LABEL,
        allowed_host=ALLOWED_HOST,
        allowed_scheme=ALLOWED_SCHEME,
        allowed_methods=ALLOWED_METHODS,
        request_budget_max=REQUEST_BUDGET_MAX,
        retry_allowed=False,
        raw_response_persisted=False,
        raw_headers_persisted=False,
        token_persisted=False,
        live_write_allowed_now=False,
        send_permission_unlocked_now=False,
        steps=steps,
    )


def validate_telegram_readonly_allowlist(method: str, host: str = ALLOWED_HOST) -> None:
    if host != ALLOWED_HOST:
        raise TelegramReadonlyProofError("telegram_readonly_host_not_allowed")
    if method not in ALLOWED_METHODS:
        raise TelegramReadonlyProofError("telegram_readonly_method_not_allowed")
    lower_method = method.lower()
    if any(fragment in lower_method for fragment in FORBIDDEN_TELEGRAM_METHOD_FRAGMENTS):
        raise TelegramReadonlyProofError("telegram_readonly_write_method_blocked")


def validate_telegram_readonly_request_budget(request_count: int) -> None:
    if request_count < 0 or request_count > REQUEST_BUDGET_MAX:
        raise TelegramReadonlyProofError("telegram_readonly_request_budget_exceeded")


def redact_telegram_chat_identifier(value: Any) -> str:
    return "telegram_chat_identifier_redacted_present" if value not in (None, "") else "telegram_chat_identifier_missing"


def redact_telegram_user_identifier(value: Any) -> str:
    return "telegram_user_identifier_redacted_present" if value not in (None, "") else "telegram_user_identifier_missing"


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
        raise TelegramReadonlyProofError("telegram_redaction_violation:" + ",".join(violations))


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
    can_post = bool(member_payload.get("can_post_messages")) if is_admin else False
    if status == "creator":
        membership = "bot_channel_creator_confirmed_redacted"
    elif status == "administrator":
        membership = "bot_channel_administrator_confirmed_redacted"
    elif status in {"member", "restricted", "left", "kicked"}:
        membership = f"bot_channel_{status}_not_admin_redacted"
    else:
        membership = "membership_unknown_redacted"
    return membership, is_admin, can_post


def derive_telegram_channel_binding_status(get_chat_ok: bool, chat_type_class: str, member_status_class: str) -> str:
    if get_chat_ok and chat_type_class == "telegram_channel_confirmed_redacted" and "confirmed" in member_status_class:
        return "channel_binding_confirmed_redacted"
    if not get_chat_ok:
        return "channel_binding_unconfirmed_chat_lookup_failed_redacted"
    if chat_type_class != "telegram_channel_confirmed_redacted":
        return "channel_binding_unconfirmed_not_channel_redacted"
    return "channel_binding_unconfirmed_membership_failed_redacted"


def derive_telegram_channel_permission_status(is_admin: bool, can_post: bool) -> str:
    if is_admin and can_post:
        return "can_post_messages_confirmed_redacted"
    if is_admin:
        return "administrator_without_can_post_messages_redacted"
    return "bot_not_channel_administrator_redacted"


def _result_body(envelope: TelegramReadonlyRawResultEnvelope) -> Mapping[str, Any] | None:
    if envelope.ok and isinstance(envelope.body, Mapping):
        result = envelope.body.get("result")
        if isinstance(result, Mapping):
            return result
    return None


def _build_redacted_proof(envelopes: list[TelegramReadonlyRawResultEnvelope]) -> TelegramReadonlyRedactedProof:
    by_method = {envelope.method: envelope for envelope in envelopes}
    get_me = by_method.get("getMe")
    get_chat = by_method.get("getChat")
    get_chat_member = by_method.get("getChatMember")

    get_me_payload = _result_body(get_me) if get_me else None
    chat_payload = _result_body(get_chat) if get_chat else None
    member_payload = _result_body(get_chat_member) if get_chat_member else None

    chat_type_class = classify_telegram_chat_type(chat_payload)
    membership_class, is_admin, can_post = classify_telegram_member_permission(member_payload)
    get_chat_ok = bool(get_chat and get_chat.ok)

    return TelegramReadonlyRedactedProof(
        get_me_ok=bool(get_me and get_me.ok),
        get_chat_ok=get_chat_ok,
        get_chat_member_ok=bool(get_chat_member and get_chat_member.ok),
        bot_identity_seen_redacted=bool(isinstance(get_me_payload, Mapping) and get_me_payload.get("is_bot") is True),
        chat_seen_redacted=bool(chat_payload),
        chat_type_class=chat_type_class,
        membership_status_class=membership_class,
        bot_admin_confirmed_redacted=is_admin,
        can_post_messages_confirmed_redacted=can_post,
        channel_binding_status=derive_telegram_channel_binding_status(get_chat_ok, chat_type_class, membership_class),
        channel_permission_status=derive_telegram_channel_permission_status(is_admin, can_post),
        request_count=len(envelopes),
        retry_count=0,
        live_read_only_request_performed=bool(envelopes),
        live_write_allowed_now=False,
        send_permission_unlocked_now=False,
        no_raw_response_persisted=True,
        redaction_verified=True,
    )


def _packet_base(proof: TelegramReadonlyRedactedProof, operator_go: bool, execution_requested: bool) -> dict[str, Any]:
    plan = build_telegram_readonly_probe_plan()
    return {
        "task_label": TASK_LABEL,
        "platform": "telegram_channel_destination",
        "official_docs_checked": True,
        "official_docs_host": "core.telegram.org",
        "official_docs_methods": list(ALLOWED_METHODS),
        "bot_api_request_format_verified": "telegram_bot_api_token_path_method_name_format_verified_redacted",
        "allowed_host": ALLOWED_HOST,
        "allowed_scheme": ALLOWED_SCHEME,
        "allowed_methods": list(ALLOWED_METHODS),
        "forbidden_method_fragments": list(FORBIDDEN_TELEGRAM_METHOD_FRAGMENTS),
        "request_budget_max": REQUEST_BUDGET_MAX,
        "request_count": proof.request_count,
        "retry_count": proof.retry_count,
        "operator_go_present": bool(operator_go),
        "execution_requested": bool(execution_requested),
        "live_read_only_request_performed": proof.live_read_only_request_performed,
        "no_write_post_send_publish_performed": True,
        "no_raw_request_url_persisted": True,
        "no_raw_response_persisted": True,
        "no_raw_headers_persisted": True,
        "no_token_persisted": True,
        "no_token_logged": True,
        "no_token_hash_or_fingerprint_created": True,
        "no_token_prefix_or_suffix_exposed": True,
        "no_unredacted_chat_or_user_identifier_persisted": True,
        "live_write_allowed_now": False,
        "send_permission_unlocked_now": False,
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
            "steps": [asdict(step) for step in plan.steps],
        },
        "redacted_proof": asdict(proof),
    }


def build_telegram_redacted_candidate_packet(proof: TelegramReadonlyRedactedProof, *, operator_go: bool = False, execution_requested: bool = False) -> dict[str, Any]:
    packet = _packet_base(proof, operator_go, execution_requested)
    packet["packet_type"] = "telegram_readonly_redacted_candidate_packet"
    packet["candidate_status"] = proof.channel_permission_status
    assert_no_telegram_secret_output(packet)
    return packet


def build_telegram_readonly_audit_packet(proof: TelegramReadonlyRedactedProof, *, operator_go: bool = False, execution_requested: bool = False) -> dict[str, Any]:
    packet = _packet_base(proof, operator_go, execution_requested)
    packet["packet_type"] = "telegram_readonly_audit_packet"
    packet["audit_status"] = "pass_redacted" if proof.redaction_verified else "blocked_redaction_failed"
    packet["request_budget_exhausted"] = proof.request_count == REQUEST_BUDGET_MAX
    assert_no_telegram_secret_output(packet)
    return packet


def build_telegram_readonly_evidence_packet(proof: TelegramReadonlyRedactedProof, *, operator_go: bool = False, execution_requested: bool = False) -> dict[str, Any]:
    packet = _packet_base(proof, operator_go, execution_requested)
    packet["packet_type"] = "telegram_readonly_evidence_packet"
    packet["status"] = "pass_redacted_readonly_proof" if proof.redaction_verified else "blocked"
    packet["final_head_self_recording_limitation"] = "Final commit SHA is unknown before commit; verify final HEAD from git after commit/push."
    assert_no_telegram_secret_output(packet)
    return packet


def _default_token_provider() -> str | None:
    # Explicit task-scoped env slot only. Never printed or persisted.
    return os.environ.get(TOKEN_ENV_NAME)


def _default_chat_provider() -> str | None:
    # Explicit task-scoped env slot only. Never printed or persisted.
    return os.environ.get(CHAT_ENV_NAME)


def _telegram_api_call(method: str, token: str, params: Mapping[str, Any] | None = None) -> TelegramReadonlyRawResultEnvelope:
    from urllib import parse as _parse
    from urllib import request as _request
    from urllib import error as _error

    validate_telegram_readonly_allowlist(method)
    params = dict(params or {})
    query = _parse.urlencode(params)
    url = f"https://{ALLOWED_HOST}/bot{token}/{method}"
    if query:
        url += "?" + query
    req = _request.Request(url, method="GET")
    try:
        with _request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
            status = resp.getcode()
            body_text = resp.read().decode("utf-8")
        body = json.loads(body_text)
        return TelegramReadonlyRawResultEnvelope(
            ok=bool(body.get("ok")), method=method, status_code=status, body=body, error_class=None
        )
    except _error.HTTPError as exc:
        return TelegramReadonlyRawResultEnvelope(False, method, exc.code, None, "http_error_redacted")
    except Exception:
        return TelegramReadonlyRawResultEnvelope(False, method, None, None, "request_error_redacted")


def run_telegram_readonly_channel_binding_permission_proof(
    *,
    write: bool = False,
    operator_go: bool = False,
    execution_requested: bool = False,
    repo_root: str | Path | None = None,
    token_provider: Callable[[], str | None] | None = None,
    chat_provider: Callable[[], str | None] | None = None,
    api_caller: Callable[[str, str, Mapping[str, Any] | None], TelegramReadonlyRawResultEnvelope] | None = None,
) -> dict[str, Any]:
    plan = build_telegram_readonly_probe_plan()
    proof = TelegramReadonlyRedactedProof(
        get_me_ok=False,
        get_chat_ok=False,
        get_chat_member_ok=False,
        bot_identity_seen_redacted=False,
        chat_seen_redacted=False,
        chat_type_class="not_executed",
        membership_status_class="not_executed",
        bot_admin_confirmed_redacted=False,
        can_post_messages_confirmed_redacted=False,
        channel_binding_status="blocked_not_executed",
        channel_permission_status="blocked_not_executed",
        request_count=0,
        retry_count=0,
        live_read_only_request_performed=False,
        live_write_allowed_now=False,
        send_permission_unlocked_now=False,
        no_raw_response_persisted=True,
        redaction_verified=True,
    )
    blockers: list[str] = []
    envelopes: list[TelegramReadonlyRawResultEnvelope] = []

    if not operator_go:
        blockers.append("operator_go_required")
    if not execution_requested:
        blockers.append("execution_flag_required")

    if not blockers:
        token_provider = token_provider or _default_token_provider
        chat_provider = chat_provider or _default_chat_provider
        api_caller = api_caller or _telegram_api_call
        token = token_provider()
        chat_id = chat_provider()
        if not token:
            blockers.append("telegram_token_missing_from_task_scoped_source")
        if not chat_id:
            blockers.append("telegram_channel_identifier_missing_from_task_scoped_source")
        if not blockers:
            validate_telegram_readonly_request_budget(0)
            get_me = api_caller("getMe", token, None)
            envelopes.append(get_me)
            validate_telegram_readonly_request_budget(len(envelopes))
            bot_payload = _result_body(get_me)
            bot_id = bot_payload.get("id") if isinstance(bot_payload, Mapping) else None
            get_chat = api_caller("getChat", token, {"chat_id": chat_id})
            envelopes.append(get_chat)
            validate_telegram_readonly_request_budget(len(envelopes))
            get_member = api_caller("getChatMember", token, {"chat_id": chat_id, "user_id": bot_id})
            envelopes.append(get_member)
            validate_telegram_readonly_request_budget(len(envelopes))
            proof = _build_redacted_proof(envelopes)
            token = None
            chat_id = None
            bot_id = None

    if envelopes:
        proof = _build_redacted_proof(envelopes)

    candidate = build_telegram_redacted_candidate_packet(proof, operator_go=operator_go, execution_requested=execution_requested)
    audit = build_telegram_readonly_audit_packet(proof, operator_go=operator_go, execution_requested=execution_requested)
    evidence = build_telegram_readonly_evidence_packet(proof, operator_go=operator_go, execution_requested=execution_requested)
    validation = {
        "task_label": TASK_LABEL,
        "status": "pass" if not scan_packet_for_telegram_secret_risk(evidence) else "blocked",
        "blockers": blockers,
        "request_budget_max": REQUEST_BUDGET_MAX,
        "request_count": proof.request_count,
        "allowed_methods": list(ALLOWED_METHODS),
        "live_write_allowed_now": False,
        "send_permission_unlocked_now": False,
        "redaction_violations": [],
    }
    assert_no_telegram_secret_output(validation)

    output = {
        "task_label": TASK_LABEL,
        "status": "blocked" if blockers else "pass_redacted_readonly_proof",
        "blockers": blockers,
        "request_count": proof.request_count,
        "request_budget_max": REQUEST_BUDGET_MAX,
        "channel_binding_status": proof.channel_binding_status,
        "channel_permission_status": proof.channel_permission_status,
        "live_write_allowed_now": False,
        "send_permission_unlocked_now": False,
        "packets_redacted": True,
    }
    assert_no_telegram_secret_output(output)

    if write:
        root = Path(repo_root) if repo_root is not None else Path(__file__).resolve().parents[1]
        packet_dir = root / PACKET_REL_DIR
        packet_dir.mkdir(parents=True, exist_ok=True)
        files = {
            "redacted_candidate_packet.json": candidate,
            "audit_packet.json": audit,
            "evidence_packet.json": evidence,
            "validation_packet.json": validation,
        }
        for filename, packet in files.items():
            assert_no_telegram_secret_output(packet)
            (packet_dir / filename).write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        (packet_dir / "implementation_report.md").write_text(build_implementation_report(proof, blockers), encoding="utf-8")
        (packet_dir / "official_docs_grounding.md").write_text(build_official_docs_grounding(), encoding="utf-8")
        output["packet_files_written"] = sorted(files.keys()) + ["implementation_report.md", "official_docs_grounding.md"]
    return output


def build_official_docs_grounding() -> str:
    return """# Telegram Read-Only Official Docs Grounding

Official docs source: `https://core.telegram.org/bots/api`.

Verified method families:

- `getMe`: read-only bot identity proof.
- `getChat`: read-only target chat/channel metadata lookup.
- `getChatMember`: read-only bot membership and administrator permission lookup.

Request format:

- Telegram Bot API token-path method-name format, kept symbolic here to avoid raw bot URL persistence.

Safety interpretation:

- Only `api.telegram.org` is allowed.
- Only `getMe`, `getChat`, and `getChatMember` are allowed.
- `ChatMemberAdministrator.can_post_messages` is mapped to a redacted proof class only.
- Live write/post/send/publish remains false.
"""


def build_implementation_report(proof: TelegramReadonlyRedactedProof, blockers: list[str]) -> str:
    return f"""# Telegram Read-Only Channel Binding Permission Proof

Task: `{TASK_LABEL}`

## Result

- Status: `{'blocked' if blockers else 'pass_redacted_readonly_proof'}`
- Request count: `{proof.request_count}` of `{REQUEST_BUDGET_MAX}`
- Channel binding: `{proof.channel_binding_status}`
- Channel permission: `{proof.channel_permission_status}`
- Live write allowed now: `False`
- Send permission unlocked now: `False`

## Blockers

{chr(10).join(f'- `{blocker}`' for blocker in blockers) if blockers else '- None'}

## Safety

- No write/post/send/publish performed.
- No raw request URL persisted.
- No raw response or headers persisted.
- No token, token hash, token prefix, token suffix, chat ID, or bot user ID persisted.
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
    return 0 if result["status"] != "blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())
