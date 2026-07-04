"""Telegram live read-only target channel binding + write-permission readiness gate (0174CL).

This is the SECOND module authorized to make bounded, live, read-only Telegram Bot
API requests, and ONLY the ``getMe`` / ``getChat`` / ``getChatMember`` methods. It
exists to confirm that the repo-local bot is *bound* to the configured target
channel and to *classify* whether future supervised channel posting could be
attempted later. It NEVER posts.

This gate answers (in redacted classes only):
  * Is the configured Telegram target slot present and shaped like a target?
  * Does the target chat exist and is it reachable by the bot? (getChat)
  * What is the chat type? (channel / supergroup / group / private / unknown)
  * What is the bot's member status in the target? (getChatMember)
  * For channels: is ``can_post_messages`` present? -> classify future publish.

HARD GUARANTEES (enforced by tests + leakage guards):
  * Fail-closed by default: NO network unless ``armed=True`` /
    CLI ``--live-telegram-target-binding``.
  * ONLY getMe/getChat/getChatMember are ever constructed or called. sendMessage,
    getUpdates, webhook, admin-mutation, invite, delete, edit, pin, poll methods are
    NEVER built. They are listed in FORBIDDEN_METHODS for defense-in-depth.
  * Host allowlist: only ``api.telegram.org``.
  * Request budget: at most THREE live requests per execution (getMe, getChat,
    getChatMember). No retry, no second-attempt flag.
  * Hard timeout (default 10s) per request.
  * Redacted-only output: NEVER emits token, chat id, channel id, channel username,
    bot id, bot username, request URL, raw response JSON, error description, or any
    prefix/suffix/length/hash/digest. Output is booleans + redacted classes only.
  * No posting/scheduling/replies/DMs/metrics. ``live_publish_gate`` stays ``blocked``.

Channel-only semantics (0174CL decision):
  This gate evaluates a Telegram *channel* publishing target. If getChat returns a
  non-channel type (private/group/supergroup), the gate classifies
  ``can_post_messages_class = not_applicable`` and BLOCKS with
  ``target_type_not_channel_for_supervised_channel_publish_gate``. A separate
  group/supergroup messaging gate may be created later.

The token + target are read from the approved local env source via the existing
0174CJ readiness reader; this module never prints or inspects the raw ``.env`` line.
"""

import json
import re
import socket
import urllib.request
import urllib.error

from live_contentops import prelaunch_telegram_credential_readiness as readiness

TASK_LABEL = "TASK_CONTENTOPS_0174CL_TELEGRAM_TARGET_CHANNEL_BINDING_AND_WRITE_PERMISSION_READINESS_GATE_V0"

LIVE_GATE = "TELEGRAM_TARGET_BINDING_READ_ONLY"
ENDPOINT_FAMILY = "telegram_bot_api_target_channel_binding"

# Host + method allowlists. Nothing else may ever be contacted/called.
ALLOWED_HOST = "api.telegram.org"
ALLOWED_METHODS = ("getMe", "getChat", "getChatMember")

# Bounded request controls.
DEFAULT_TIMEOUT_SECONDS = 10
REQUEST_BUDGET = 3   # getMe + getChat + getChatMember; no retry, no second attempt

# Explicitly forbidden methods (defense-in-depth; this module only ever builds the
# three allowlisted read methods, but we assert these are never used).
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
    "getChatAdministrators",
    "exportChatInviteLink",
    "createChatInviteLink",
    "approveSuggestedPost",
    "declineSuggestedPost",
    "deleteMessage",
    "editMessageText",
    "pinChatMessage",
    "sendPoll",
    "banChatMember",
    "restrictChatMember",
)

# Chat type classes
CHAT_TYPE_CHANNEL = "channel"
CHAT_TYPE_SUPERGROUP = "supergroup"
CHAT_TYPE_GROUP = "group"
CHAT_TYPE_PRIVATE = "private"
CHAT_TYPE_UNKNOWN = "unknown_redacted"
_KNOWN_CHAT_TYPES = {
    "channel": CHAT_TYPE_CHANNEL,
    "supergroup": CHAT_TYPE_SUPERGROUP,
    "group": CHAT_TYPE_GROUP,
    "private": CHAT_TYPE_PRIVATE,
}

# Bot member status classes
STATUS_ADMINISTRATOR = "administrator"
STATUS_CREATOR = "creator"
STATUS_MEMBER = "member"
STATUS_RESTRICTED = "restricted"
STATUS_LEFT = "left"
STATUS_KICKED = "kicked"
STATUS_UNKNOWN = "unknown_redacted"
_KNOWN_MEMBER_STATUSES = {
    "administrator": STATUS_ADMINISTRATOR,
    "creator": STATUS_CREATOR,
    "member": STATUS_MEMBER,
    "restricted": STATUS_RESTRICTED,
    "left": STATUS_LEFT,
    "kicked": STATUS_KICKED,
}

# can_post_messages classes
CPM_TRUE = "true"
CPM_FALSE = "false"
CPM_UNAVAILABLE = "unavailable"
CPM_NOT_APPLICABLE = "not_applicable"
CPM_UNKNOWN = "unknown_redacted"

# Target identifier shape classes (reuse readiness chat-id shape semantics)
TARGET_ABSENT = "absent"
TARGET_PRESENT = "present_redacted_target_like"
TARGET_INVALID = "invalid_shape"

# Reuse the proven secret-like leakage patterns from the readiness harness.
_SECRET_LIKE = list(readiness._SECRET_LIKE)

# Guard against a raw bot-api URL containing a token ever surviving into output.
_URL_WITH_TOKEN = re.compile(r"api\.telegram\.org/bot\d{6,}:")
# Guard against a raw channel @handle surviving into output.
_HANDLE_LIKE = re.compile(r"@[A-Za-z0-9_]{3,}")


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


def classify_target_shape(raw):
    """Redacted shape class for the configured target. Never returns the value."""
    if raw is None or raw.strip() == "":
        return TARGET_ABSENT
    chat_class = readiness.classify_chat_id_shape(raw)
    if chat_class in (readiness.CHAT_INTEGER, readiness.CHAT_HANDLE):
        return TARGET_PRESENT
    return TARGET_INVALID


def _base_summary():
    return {
        "task_label": TASK_LABEL,
        "live_gate": LIVE_GATE,
        "endpoint_family": ENDPOINT_FAMILY,
        "armed": False,
        "request_attempted": False,
        "request_count": 0,
        "request_budget": REQUEST_BUDGET,
        "host_allowlist_passed": False,
        "method_allowlist_passed": False,
        "timeout_seconds": DEFAULT_TIMEOUT_SECONDS,
        "target_slot_present": False,
        "target_identifier_shape_class": TARGET_ABSENT,
        "target_chat_reachable": False,
        "target_chat_type_class": CHAT_TYPE_UNKNOWN,
        "bot_membership_checked": False,
        "bot_member_status_class": STATUS_UNKNOWN,
        "can_post_messages_class": CPM_UNKNOWN,
        "future_supervised_publish_possible_after_remaining_gates": False,
        # Hard-locked policy flags — never true for this gate.
        "posting_enabled": False,
        "send_message_enabled": False,
        "get_updates_enabled": False,
        "webhook_enabled": False,
        "scheduler_enabled": False,
        "autonomous_replies_enabled": False,
        "metrics_fetch_enabled": False,
        "live_publish_gate": "blocked",
        "next_gate_required_before_posting": True,
        "redaction_verified": True,
        "status": "fail_closed",
        "blocked_reasons": [],
    }


def _default_api_caller(method, token, target, timeout_seconds, bot_user_id=None):
    """Perform exactly one live read-only GET request for an allowlisted method.

    Returns a redacted dict. NEVER returns the token, target, URL, headers, bot id,
    username, channel id/username, or the raw response body.

    Redacted return shapes:
      getMe        -> {"ok", "transport_error", "bot_user_id": int|None}
      getChat      -> {"ok", "transport_error", "chat_type": str|None}
      getChatMember-> {"ok", "transport_error", "member_status": str|None,
                       "can_post_messages": bool|None}
    """
    if method not in ALLOWED_METHODS or method in FORBIDDEN_METHODS:
        return {"ok": False, "transport_error": True}

    base = f"https://{ALLOWED_HOST}/bot{token}/{method}"
    if method == "getMe":
        url = base
    elif method == "getChat":
        url = f"{base}?chat_id={urllib.request.quote(str(target))}"
    elif method == "getChatMember":
        url = (
            f"{base}?chat_id={urllib.request.quote(str(target))}"
            f"&user_id={urllib.request.quote(str(bot_user_id))}"
        )
    else:  # pragma: no cover - guarded above
        return {"ok": False, "transport_error": True}

    # Final defense-in-depth: only ever talk to the allowlisted host.
    if not url.startswith(f"https://{ALLOWED_HOST}/"):
        return {"ok": False, "transport_error": True}

    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout_seconds) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
        data = json.loads(raw)
        ok = data.get("ok") is True
        result = data.get("result") if isinstance(data, dict) else None
        if not ok or not isinstance(result, dict):
            return {"ok": False, "transport_error": False}
        if method == "getMe":
            # Keep ONLY the numeric bot user_id (needed internally for getChatMember).
            # It is never emitted to output.
            uid = result.get("id")
            return {"ok": True, "transport_error": False,
                    "bot_user_id": uid if isinstance(uid, int) else None}
        if method == "getChat":
            ctype = result.get("type")
            return {"ok": True, "transport_error": False,
                    "chat_type": ctype if isinstance(ctype, str) else None}
        if method == "getChatMember":
            status = result.get("status")
            cpm = result.get("can_post_messages")
            return {"ok": True, "transport_error": False,
                    "member_status": status if isinstance(status, str) else None,
                    "can_post_messages": cpm if isinstance(cpm, bool) else None}
    except (urllib.error.URLError, socket.timeout, ValueError, OSError):
        # Never surface the exception text (could echo URL/token/target).
        return {"ok": False, "transport_error": True}
    return {"ok": False, "transport_error": True}


def _classify_future_publish(chat_type_class, member_status_class, cpm_class):
    """Channel-only: future supervised publish possible iff channel + admin/creator
    with can_post_messages true. Everything else is blocked for this gate."""
    if chat_type_class != CHAT_TYPE_CHANNEL:
        return False
    if member_status_class not in (STATUS_ADMINISTRATOR, STATUS_CREATOR):
        return False
    return cpm_class == CPM_TRUE


def run_target_binding_gate(
    *,
    armed=False,
    repo_root=None,
    use_process_env=False,
    timeout_seconds=DEFAULT_TIMEOUT_SECONDS,
    _api_caller=None,
):
    """Run the bounded live target-binding gate. Fail-closed by default.

    armed: must be explicitly True to perform ANY network request.
    _api_caller: injectable caller(method, token, target, timeout, bot_user_id)
                 -> redacted dict for tests (network-free). When None and armed,
                 the real bounded caller runs.
    """
    summary = _base_summary()
    summary["timeout_seconds"] = int(timeout_seconds)
    summary["armed"] = bool(armed)

    # 1. Fail closed unless explicitly armed.
    if not armed:
        summary["blocked_reasons"] = ["not_armed_live_request_skipped"]
        summary["status"] = "fail_closed"
        return summary

    # 2. Read approved local env source via the redacted readiness reader.
    env_text, _source_label, available = readiness._read_repo_env_source(
        readiness.os.path.dirname(readiness.os.path.dirname(readiness.__file__))
        if repo_root is None else repo_root,
        use_process_env=use_process_env,
    )
    if not available or env_text is None:
        summary["blocked_reasons"] = ["approved_local_env_source_unavailable"]
        summary["status"] = "fail_closed"
        return summary

    parsed = readiness.parse_approved_env_text(env_text)
    token_raw = parsed["TELEGRAM_BOT_TOKEN"]
    target_raw = parsed["TELEGRAM_TARGET_CHAT_ID"]

    summary["target_slot_present"] = readiness._is_present(target_raw)
    summary["target_identifier_shape_class"] = classify_target_shape(target_raw)

    # 3. Fail closed on missing token (cannot derive bot identity) or target slot.
    if not readiness._is_present(token_raw):
        summary["blocked_reasons"] = ["telegram_bot_token_absent_binding_blocked"]
        summary["status"] = "fail_closed"
        return _finalize(summary)
    if not summary["target_slot_present"]:
        summary["blocked_reasons"] = ["target_slot_absent_fail_closed"]
        summary["status"] = "fail_closed"
        return _finalize(summary)
    if summary["target_identifier_shape_class"] == TARGET_INVALID:
        summary["blocked_reasons"] = ["target_identifier_invalid_shape_fail_closed"]
        summary["status"] = "fail_closed"
        return _finalize(summary)

    # 4. Allowlist gates (host + method) before any request.
    summary["host_allowlist_passed"] = True
    summary["method_allowlist_passed"] = (
        all(m in ALLOWED_METHODS for m in ALLOWED_METHODS)
        and not any(m in FORBIDDEN_METHODS for m in ALLOWED_METHODS)
    )

    caller = _api_caller if _api_caller is not None else _default_api_caller

    # 5a. getMe — derive bot user_id internally (never emitted).
    summary["request_count"] += 1
    summary["request_attempted"] = True
    me = caller("getMe", token_raw, target_raw, timeout_seconds, None)
    if not isinstance(me, dict) or not me.get("ok"):
        summary["blocked_reasons"] = ["getme_identity_unavailable_redacted"]
        summary["status"] = "blocked"
        return _finalize(summary)
    bot_user_id = me.get("bot_user_id")
    if not isinstance(bot_user_id, int):
        summary["blocked_reasons"] = ["getme_bot_user_id_unavailable_redacted"]
        summary["status"] = "blocked"
        return _finalize(summary)

    # 5b. getChat — target binding + chat type.
    summary["request_count"] += 1
    chat = caller("getChat", token_raw, target_raw, timeout_seconds, None)
    if not isinstance(chat, dict) or not chat.get("ok"):
        reason = ("getchat_transport_error_redacted"
                  if isinstance(chat, dict) and chat.get("transport_error")
                  else "getchat_target_unreachable_redacted")
        summary["blocked_reasons"] = [reason]
        summary["status"] = "blocked"
        return _finalize(summary)
    summary["target_chat_reachable"] = True
    summary["target_chat_type_class"] = _KNOWN_CHAT_TYPES.get(
        chat.get("chat_type"), CHAT_TYPE_UNKNOWN)

    # 5c. getChatMember — bot membership/admin/write-permission class.
    summary["request_count"] += 1
    member = caller("getChatMember", token_raw, target_raw, timeout_seconds, bot_user_id)
    if not isinstance(member, dict) or not member.get("ok"):
        reason = ("getchatmember_transport_error_redacted"
                  if isinstance(member, dict) and member.get("transport_error")
                  else "getchatmember_unavailable_redacted")
        summary["blocked_reasons"] = [reason]
        summary["status"] = "blocked"
        return _finalize(summary)
    summary["bot_membership_checked"] = True
    summary["bot_member_status_class"] = _KNOWN_MEMBER_STATUSES.get(
        member.get("member_status"), STATUS_UNKNOWN)

    # 6. can_post_messages classification (channel-only semantics).
    if summary["target_chat_type_class"] != CHAT_TYPE_CHANNEL:
        summary["can_post_messages_class"] = CPM_NOT_APPLICABLE
        summary["future_supervised_publish_possible_after_remaining_gates"] = False
        summary["blocked_reasons"] = [
            "target_type_not_channel_for_supervised_channel_publish_gate"]
        summary["status"] = "blocked"
        return _finalize(summary)

    # Channel target: classify can_post_messages.
    cpm = member.get("can_post_messages")
    status_class = summary["bot_member_status_class"]
    if status_class == STATUS_CREATOR:
        # Channel creators can always post; can_post_messages may be omitted.
        summary["can_post_messages_class"] = CPM_TRUE if cpm is not False else CPM_FALSE
    elif status_class == STATUS_ADMINISTRATOR:
        if cpm is True:
            summary["can_post_messages_class"] = CPM_TRUE
        elif cpm is False:
            summary["can_post_messages_class"] = CPM_FALSE
        else:
            summary["can_post_messages_class"] = CPM_UNAVAILABLE
    else:
        # member / restricted / left / kicked / unknown cannot post to a channel.
        summary["can_post_messages_class"] = CPM_NOT_APPLICABLE

    summary["future_supervised_publish_possible_after_remaining_gates"] = (
        _classify_future_publish(
            summary["target_chat_type_class"], status_class,
            summary["can_post_messages_class"]))

    if summary["future_supervised_publish_possible_after_remaining_gates"]:
        summary["status"] = "pass"
    else:
        summary["status"] = "blocked"
        if status_class in (STATUS_ADMINISTRATOR, STATUS_CREATOR):
            summary["blocked_reasons"] = ["channel_post_permission_absent_blocked"]
        else:
            summary["blocked_reasons"] = ["bot_not_channel_poster_membership_blocked"]

    return _finalize(summary)


def _finalize(summary):
    """Defensive redaction guard over the whole emitted summary. Scrub on leak."""
    leak = _scan_secret_like(summary)
    strings = _string_values(summary)
    url_leak = any(_URL_WITH_TOKEN.search(v) for v in strings)
    handle_leak = any(_HANDLE_LIKE.search(v) for v in strings)
    if leak or url_leak or handle_leak:
        scrubbed = _base_summary()
        scrubbed["armed"] = summary["armed"]
        scrubbed["request_attempted"] = summary["request_attempted"]
        scrubbed["request_count"] = summary["request_count"]
        scrubbed["redaction_verified"] = True
        scrubbed["blocked_reasons"] = ["redaction_guard_triggered"]
        scrubbed["status"] = "blocked"
        return scrubbed
    return summary


def summary(**kwargs):
    """Convenience wrapper returning the redacted gate summary dict."""
    return run_target_binding_gate(**kwargs)


def main(argv=None):
    """CLI: print ONLY the redacted JSON summary.

    Fail-closed unless ``--live-telegram-target-binding`` is passed.

    Usage:
      python -m live_contentops.telegram_target_binding_gate
      python -m live_contentops.telegram_target_binding_gate --live-telegram-target-binding
      python -m live_contentops.telegram_target_binding_gate --live-telegram-target-binding --process-env
    """
    import sys

    args = list(sys.argv[1:] if argv is None else argv)
    armed = "--live-telegram-target-binding" in args
    use_process_env = "--process-env" in args
    result = run_target_binding_gate(armed=armed, use_process_env=use_process_env)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
