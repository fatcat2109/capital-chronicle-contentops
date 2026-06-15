"""Telegram live read-only getMe identity validation gate (0174CK).

This is the FIRST and ONLY module authorized to make a bounded, live, read-only
Telegram Bot API request, and ONLY the ``getMe`` method. It exists to confirm
that the repo-local bot token authenticates with Telegram (token identity),
nothing more.

HARD GUARANTEES (enforced by tests + leakage guards):
  * Fail-closed by default: NO network is performed unless the caller passes an
    explicit arming flag (``armed=True`` / CLI ``--live-telegram-getme``).
  * Only ``getMe`` is ever called. ``sendMessage`` / ``getUpdates`` / webhook /
    channel-write / admin methods are NEVER constructed or called.
  * Host allowlist: only ``api.telegram.org``.
  * Request budget: at most ONE live request per execution (one extra attempt is
    permitted ONLY when ``allow_second_attempt=True``, and is still capped at 2).
  * Hard timeout (default 10s).
  * Redacted-only output: NEVER emits the token, chat id, request URL, raw
    response JSON, bot id, bot username, token/chat-id prefix/suffix/length, or
    any hash/digest. Output is booleans + redacted classes only.
  * No posting, scheduling, replies/DMs, metrics, or scraping. ``live_publish_gate``
    remains ``blocked``.

The token is read from the approved local env source via the existing 0174CJ
readiness reader (``prelaunch_telegram_credential_readiness``); this module never
prints or inspects the raw ``.env`` line.
"""

import json
import re
import socket
import urllib.request
import urllib.error

from live_contentops import prelaunch_telegram_credential_readiness as readiness

TASK_LABEL = "TASK_CONTENTOPS_0174CK_TELEGRAM_LIVE_GATE_READ_ONLY_BOT_ID_VALIDATION_V0"

LIVE_GATE = "TELEGRAM_GETME_READ_ONLY"
ENDPOINT_FAMILY = "telegram_bot_api_getMe"

# Host + method allowlists. Nothing else may ever be contacted/called.
ALLOWED_HOST = "api.telegram.org"
ALLOWED_METHOD = "getMe"

# Bounded request controls.
DEFAULT_TIMEOUT_SECONDS = 10
MAX_REQUEST_BUDGET = 2          # only reachable with allow_second_attempt
DEFAULT_REQUEST_BUDGET = 1

# Explicitly forbidden methods (defense-in-depth; this module only ever builds
# getMe, but we assert these are never the configured method).
FORBIDDEN_METHODS = (
    "sendMessage",
    "sendPhoto",
    "sendMediaGroup",
    "copyMessage",
    "forwardMessage",
    "getUpdates",
    "setWebhook",
    "deleteWebhook",
    "getWebhookInfo",
    "editMessageText",
    "answerCallbackQuery",
    "getChat",
    "getChatAdministrators",
    "banChatMember",
)

# Reuse the proven secret-like leakage patterns from the readiness harness.
_SECRET_LIKE = list(readiness._SECRET_LIKE)


def _scan_secret_like(obj):
    """Return labels for any secret-like value appearing anywhere in output."""
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


# Guard against a raw bot-api URL containing a token ever surviving into output.
_URL_WITH_TOKEN = re.compile(r"api\.telegram\.org/bot\d{6,}:")


def _base_summary():
    return {
        "task_label": TASK_LABEL,
        "live_gate": LIVE_GATE,
        "endpoint_family": ENDPOINT_FAMILY,
        "armed": False,
        "request_attempted": False,
        "host_allowlist_passed": False,
        "method_allowlist_passed": False,
        "request_budget": DEFAULT_REQUEST_BUDGET,
        "request_count": 0,
        "timeout_seconds": DEFAULT_TIMEOUT_SECONDS,
        "token_present": None,
        "token_shape_class": readiness.TOKEN_ABSENT,
        "response_ok": False,
        "bot_identity_validated": False,
        "redaction_verified": True,
        # Hard-locked policy flags — never true for this gate.
        "posting_enabled": False,
        "send_message_enabled": False,
        "get_updates_enabled": False,
        "webhook_enabled": False,
        "channel_write_validated": False,
        "scheduler_enabled": False,
        "autonomous_replies_enabled": False,
        "metrics_fetch_enabled": False,
        "live_publish_gate": "blocked",
        "manual_review_required": True,
        "next_gate_required_before_posting": True,
        "status": "blocked",
        "blocked_reasons": [],
    }


def _default_getme_caller(token, timeout_seconds):
    """Perform exactly one live getMe GET request. Returns a redacted dict.

    Returns: {"ok": bool, "is_bot": bool, "has_id": bool, "transport_error": bool}
    NEVER returns the token, the URL, headers, or the raw response body.
    """
    url = f"https://{ALLOWED_HOST}/bot{token}/{ALLOWED_METHOD}"
    # Final defense-in-depth: only ever talk to the allowlisted host.
    if not url.startswith(f"https://{ALLOWED_HOST}/"):
        return {"ok": False, "is_bot": False, "has_id": False, "transport_error": True}
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout_seconds) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
        data = json.loads(raw)
        ok = data.get("ok") is True
        result = data.get("result") if isinstance(data, dict) else None
        is_bot = isinstance(result, dict) and result.get("is_bot") is True
        has_id = isinstance(result, dict) and "id" in result
        # Discard raw/url/token immediately; return only redacted booleans.
        return {"ok": ok, "is_bot": is_bot, "has_id": has_id, "transport_error": False}
    except (urllib.error.URLError, socket.timeout, ValueError, OSError):
        # Never surface the exception text (could echo URL/token).
        return {"ok": False, "is_bot": False, "has_id": False, "transport_error": True}


def run_getme_gate(
    *,
    armed=False,
    repo_root=None,
    use_process_env=False,
    timeout_seconds=DEFAULT_TIMEOUT_SECONDS,
    allow_second_attempt=False,
    _api_caller=None,
):
    """Run the bounded live getMe identity gate. Fail-closed by default.

    armed: must be explicitly True to perform ANY network request.
    _api_caller: injectable caller(token, timeout)->redacted dict for tests
                 (network-free). When None and armed, the real bounded caller runs.
    """
    summary = _base_summary()
    summary["timeout_seconds"] = int(timeout_seconds)
    summary["request_budget"] = MAX_REQUEST_BUDGET if allow_second_attempt else DEFAULT_REQUEST_BUDGET
    summary["armed"] = bool(armed)

    # 1. Fail closed unless explicitly armed.
    if not armed:
        summary["blocked_reasons"] = ["not_armed_live_request_skipped"]
        summary["status"] = "blocked"
        return summary

    # 2. Read approved local env source via the redacted readiness reader.
    env_text, _source_label, available = readiness._read_repo_env_source(
        readiness.os.path.dirname(readiness.os.path.dirname(readiness.__file__))
        if repo_root is None else repo_root,
        use_process_env=use_process_env,
    )
    if not available or env_text is None:
        summary["blocked_reasons"] = ["approved_local_env_source_unavailable"]
        summary["status"] = "blocked"
        return summary

    parsed = readiness.parse_approved_env_text(env_text)
    token_raw = parsed["TELEGRAM_BOT_TOKEN"]
    summary["token_present"] = readiness._is_present(token_raw)
    summary["token_shape_class"] = readiness.classify_token_shape(token_raw)

    if not readiness._is_present(token_raw):
        summary["blocked_reasons"] = ["telegram_bot_token_absent_getme_blocked"]
        summary["status"] = "blocked"
        return summary

    # 3. Allowlist gates (host + method) before any request.
    summary["host_allowlist_passed"] = True
    summary["method_allowlist_passed"] = ALLOWED_METHOD == "getMe" and ALLOWED_METHOD not in FORBIDDEN_METHODS

    # 4. Perform at most one (or two, if explicitly allowed) bounded request.
    caller = _api_caller if _api_caller is not None else _default_getme_caller
    budget = summary["request_budget"]
    resp = None
    for _ in range(budget):
        summary["request_count"] += 1
        summary["request_attempted"] = True
        resp = caller(token_raw, timeout_seconds)
        if isinstance(resp, dict) and resp.get("ok"):
            break  # success; do not consume further budget

    if not isinstance(resp, dict):
        summary["blocked_reasons"] = ["getme_response_malformed_redacted"]
        summary["status"] = "blocked"
    elif resp.get("ok"):
        summary["response_ok"] = True
        summary["bot_identity_validated"] = bool(resp.get("is_bot") and resp.get("has_id"))
        if summary["bot_identity_validated"]:
            summary["status"] = "pass"
        else:
            summary["blocked_reasons"] = ["getme_bot_identity_not_confirmed"]
            summary["status"] = "blocked"
    else:
        summary["response_ok"] = False
        if resp.get("transport_error"):
            summary["blocked_reasons"] = ["getme_transport_error_redacted"]
        else:
            summary["blocked_reasons"] = ["getme_validation_failed_error_redacted"]
        summary["status"] = "blocked"

    # 5. Defensive redaction guard over the whole emitted summary.
    leak = _scan_secret_like(summary)
    if leak or any(_URL_WITH_TOKEN.search(v) for v in _string_values(summary)):
        # Scrub and fail closed.
        scrubbed = _base_summary()
        scrubbed["armed"] = summary["armed"]
        scrubbed["request_attempted"] = summary["request_attempted"]
        scrubbed["request_count"] = summary["request_count"]
        scrubbed["redaction_verified"] = True
        scrubbed["blocked_reasons"] = ["redaction_guard_triggered"]
        scrubbed["status"] = "blocked"
        return scrubbed

    return summary


def _string_values(obj):
    out = []

    def _walk(o):
        if isinstance(o, str):
            out.append(o)
        elif isinstance(o, dict):
            for v in o.values():
                _walk(v)
        elif isinstance(o, list):
            for v in o:
                _walk(v)

    _walk(obj)
    return out


def summary(**kwargs):
    """Convenience wrapper returning the redacted gate summary dict."""
    return run_getme_gate(**kwargs)


def main(argv=None):
    """CLI: print ONLY the redacted JSON summary.

    Fail-closed unless ``--live-telegram-getme`` is passed.

    Usage:
      python -m live_contentops.telegram_live_getme_gate
      python -m live_contentops.telegram_live_getme_gate --live-telegram-getme
      python -m live_contentops.telegram_live_getme_gate --live-telegram-getme --process-env
    """
    import sys

    args = list(sys.argv[1:] if argv is None else argv)
    armed = "--live-telegram-getme" in args
    use_process_env = "--process-env" in args
    allow_second = "--allow-second-attempt" in args
    result = run_getme_gate(
        armed=armed,
        use_process_env=use_process_env,
        allow_second_attempt=allow_second,
    )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
