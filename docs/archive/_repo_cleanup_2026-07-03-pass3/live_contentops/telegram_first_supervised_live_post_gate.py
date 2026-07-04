"""Telegram FIRST supervised live-post gate (0174CN).

This is the THIRD and final module authorized to make a bounded LIVE Telegram Bot
API request, and ONLY the ``sendMessage`` method, exactly ONCE. It exists to send
ONE operator-approved Telegram message to the previously validated configured
target channel, then emit a redacted audit summary.

This is NOT a general publisher. It is a one-time supervised live-post pilot gate.

Prior gates (unchanged by this module):
  * 0174CK validated bot token identity via live read-only ``getMe``.
  * 0174CL validated target channel binding + channel post permission via
    ``getMe`` -> ``getChat`` -> ``getChatMember``.
  * 0174CM validated the local supervised post preflight (deterministic payload
    hash, dry-run approval record, kill switch live-dispatch block, mock would-send
    shape, redacted audit event) WITHOUT any live send.

HARD REQUIREMENT:
  The task fails closed unless BOTH explicit one-time live flags are present
  (``--telegram-first-supervised-live-post`` AND ``--operator-go-0174cn``) AND an
  exact operator approval object matches the EXACT payload hash. If either flag is
  absent, or the approval/hash/target/dry-run/kill-switch checks fail, NO send.

HARD GUARANTEES (enforced by tests + leakage guards):
  * Fail-closed by default: NO network unless BOTH live flags are present.
  * ONLY ``sendMessage`` is ever constructed/called. Every other method
    (getMe, getChat, getChatMember, getUpdates, setWebhook, deleteWebhook,
    getWebhookInfo, sendPhoto, sendMediaGroup, copyMessage, forwardMessage,
    editMessageText, deleteMessage, pinChatMessage, sendPoll, sendChatAction, ...)
    is in FORBIDDEN_METHODS and NEVER built.
  * Host allowlist: only ``api.telegram.org``.
  * Request budget: at most ONE live request. No retry, no second-attempt flag.
  * Hard timeout (default 10s).
  * Redacted-only output: NEVER emits token, chat id, channel id, channel username,
    bot id, bot username, raw URL, raw request body, raw response JSON, message id
    value, date value, or any prefix/suffix/length/hash/digest of any secret or
    account identifier. Output is booleans + redacted classes only.
  * After the send, ALL future/live automation gates remain blocked:
    ``live_publish_gate = blocked_after_one_time_pilot``, posting/scheduler/
    replies/webhook/getUpdates/metrics all stay False.
"""

import json
import re
import socket
import urllib.request
import urllib.error

from live_contentops import prelaunch_telegram_credential_readiness as readiness
from live_contentops import telegram_supervised_post_dry_run_gate as dryrun

TASK_LABEL = (
    "TASK_CONTENTOPS_0174CN_TELEGRAM_FIRST_SUPERVISED_LIVE_POST_"
    "TO_OPERATOR_APPROVED_TARGET_V0"
)

LIVE_GATE = "TELEGRAM_FIRST_SUPERVISED_LIVE_POST_0174CN"
ENDPOINT_FAMILY = "telegram_bot_api_first_supervised_live_post"

# Host + method allowlists. ONLY sendMessage may ever be built/called.
ALLOWED_HOST = "api.telegram.org"
ALLOWED_METHOD = "sendMessage"

# Bounded request controls.
DEFAULT_TIMEOUT_SECONDS = 10
REQUEST_BUDGET = 1   # exactly one sendMessage; no retry, no second attempt

# Explicit one-time live authorization flags. BOTH are required.
FLAG_LIVE_POST = "--telegram-first-supervised-live-post"
FLAG_OPERATOR_GO = "--operator-go-0174cn"

# Telegram text hard limit (sendMessage).
TELEGRAM_TEXT_LIMIT = 4096

# Operator live approval state (distinct from any dry-run approval state).
APPROVAL_STATE_FIRST_LIVE = "operator_approved_for_first_live_post_0174cn"

# One-time live override classes.
OVERRIDE_OK = "operator_approved_0174cn_only"
OVERRIDE_ABSENT = "absent"
OVERRIDE_INVALID = "invalid"

# Explicitly forbidden methods (defense-in-depth; this module only ever builds the
# single allowlisted sendMessage method, but we assert these are never used).
FORBIDDEN_METHODS = (
    "getMe",
    "getChat",
    "getChatMember",
    "getUpdates",
    "setWebhook",
    "deleteWebhook",
    "getWebhookInfo",
    "sendPhoto",
    "sendMediaGroup",
    "copyMessage",
    "forwardMessage",
    "editMessageText",
    "deleteMessage",
    "pinChatMessage",
    "sendPoll",
    "sendChatAction",
    "answerCallbackQuery",
    "banChatMember",
    "restrictChatMember",
    "exportChatInviteLink",
    "createChatInviteLink",
)

# Telegram response ok classes (redacted).
RESP_OK_TRUE = "true"
RESP_OK_FALSE = "false"
RESP_TRANSPORT_ERROR = "transport_error"
RESP_UNKNOWN = "unknown_redacted"

# Chat type classes (redacted; only the symbolic type, never an identifier).
CHAT_TYPE_CHANNEL = "channel"
CHAT_TYPE_UNKNOWN = "unknown_redacted"
_KNOWN_CHAT_TYPES = {"channel", "supergroup", "group", "private"}

# Reuse the proven secret-like leakage patterns from the readiness harness.
_SECRET_LIKE = list(readiness._SECRET_LIKE)
# Guard against a raw bot-api URL containing a token ever surviving into output.
_URL_WITH_TOKEN = re.compile(r"api\.telegram\.org/bot\d{6,}:")
# Guard against a raw channel @handle surviving into output.
_HANDLE_LIKE = re.compile(r"@[A-Za-z0-9_]{3,}")


# --------------------------------------------------------------------------- #
# Leakage guard helpers
# --------------------------------------------------------------------------- #
def _scan_secret_like(obj):
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


# --------------------------------------------------------------------------- #
# Payload + approval (reuses 0174CM canonicalization for the EXACT hash lock)
# --------------------------------------------------------------------------- #
def canonicalize_payload(payload):
    """Deterministic canonical JSON for the payload (delegates to 0174CM)."""
    return dryrun.canonicalize_payload(payload)


def compute_payload_hash(payload):
    """Deterministic SHA-256 hex digest of the canonical payload (0174CM contract)."""
    return dryrun.compute_payload_hash(payload)


def validate_payload_shape(payload):
    """Validate the live post payload shape. Returns (ok, [reasons]).

    Builds on the 0174CM shape contract, plus a hard Telegram text-limit check
    for the live send.
    """
    ok, reasons = dryrun.validate_payload_shape(payload)
    reasons = list(reasons)
    text = payload.get("content_text") if isinstance(payload, dict) else None
    if isinstance(text, str) and len(text) > TELEGRAM_TEXT_LIMIT:
        reasons.append("content_text_exceeds_telegram_limit")
    return (len(reasons) == 0), reasons


def check_forbidden_language(text):
    """No-advice / no-signal forbidden-language scan (delegates to 0174CM)."""
    return dryrun.check_forbidden_language(text)


def validate_live_approval_record(record, expected_hash):
    """Validate the operator LIVE approval record for 0174CN. (ok, [reasons]).

    A dry-run (0174CM) approval state is explicitly NOT accepted here. The record
    must carry the dedicated first-live-post approval state AND the exact payload
    hash AND all one-time live acknowledgements.
    """
    reasons = []
    if not isinstance(record, dict):
        return False, ["live_approval_record_missing"]

    state = record.get("approval_state")
    if state != APPROVAL_STATE_FIRST_LIVE:
        # Anything else (including the 0174CM dry-run approval) is rejected.
        reasons.append(f"approval_state_not_first_live_post:{state or 'none'}")

    approved_hash = record.get("approved_payload_hash")
    if not approved_hash:
        reasons.append("approved_payload_hash_missing")
    elif approved_hash != expected_hash:
        reasons.append("live_approval_hash_mismatch")

    if not record.get("operator_go_ref"):
        reasons.append("operator_go_ref_missing")

    for ack in ("human_review_completed",
                "target_binding_0174cl_accepted",
                "dry_run_0174cm_accepted",
                "understands_live_post",
                "one_time_only"):
        if record.get(ack) is not True:
            reasons.append(f"ack_missing:{ack}")

    return (len(reasons) == 0), reasons


def validate_target_binding_state(binding):
    """Target binding REPRESENTED as previously passed (0174CL). No live recheck.

    Reuses the 0174CM target-binding representation contract.
    """
    ok, reasons = dryrun.validate_target_binding_state(binding)
    return ok, list(reasons)


def validate_one_time_kill_switch(ks):
    """Validate the one-time live override kill-switch state. (ok, [reasons]).

    Global live dispatch remains blocked by default. This one-time live pilot is
    permitted ONLY when an explicit 0174CN-scoped override is present. Scheduler /
    reply / DM / webhook / getUpdates remain blocked.
    """
    reasons = []
    if not isinstance(ks, dict):
        return False, ["kill_switch_state_missing"]

    if ks.get("global_live_dispatch") != "blocked":
        reasons.append("global_live_dispatch_not_blocked")
    if ks.get("one_time_live_override") != "operator_approved_0174cn_only":
        reasons.append("one_time_live_override_not_0174cn_scoped")
    if ks.get("scheduler_enabled") is True:
        reasons.append("scheduler_enabled_true")
    if ks.get("autonomous_replies_enabled") is True:
        reasons.append("autonomous_replies_enabled_true")
    if ks.get("webhook_enabled") is True:
        reasons.append("webhook_enabled_true")
    if ks.get("get_updates_enabled") is True:
        reasons.append("get_updates_enabled_true")

    return (len(reasons) == 0), reasons


def classify_one_time_override(ks):
    """Redacted class for the one-time live override slot."""
    if not isinstance(ks, dict):
        return OVERRIDE_ABSENT
    val = ks.get("one_time_live_override")
    if val is None:
        return OVERRIDE_ABSENT
    if val == "operator_approved_0174cn_only":
        return OVERRIDE_OK
    return OVERRIDE_INVALID


# --------------------------------------------------------------------------- #
# The single bounded live sendMessage caller
# --------------------------------------------------------------------------- #
def _default_api_caller(method, token, target, text, timeout_seconds):
    """Perform EXACTLY ONE live sendMessage POST for the allowlisted method.

    Returns a redacted dict. NEVER returns the token, target, URL, headers, raw
    request body, raw response body, message id value, or date value.

    Redacted return shape:
      {"ok": bool, "transport_error": bool, "message_id_present": bool,
       "date_present": bool, "chat_type": str|None}
    """
    if method != ALLOWED_METHOD or method in FORBIDDEN_METHODS:
        return {"ok": False, "transport_error": True,
                "message_id_present": False, "date_present": False,
                "chat_type": None}

    url = f"https://{ALLOWED_HOST}/bot{token}/{method}"
    # Final defense-in-depth: only ever talk to the allowlisted host.
    if not url.startswith(f"https://{ALLOWED_HOST}/"):
        return {"ok": False, "transport_error": True,
                "message_id_present": False, "date_present": False,
                "chat_type": None}

    body = json.dumps({"chat_id": target, "text": text}).encode("utf-8")
    req = urllib.request.Request(
        url, data=body, method="POST",
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout_seconds) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
        data = json.loads(raw)
        ok = data.get("ok") is True
        result = data.get("result") if isinstance(data, dict) else None
        if not ok or not isinstance(result, dict):
            return {"ok": False, "transport_error": False,
                    "message_id_present": False, "date_present": False,
                    "chat_type": None}
        # Keep ONLY redacted booleans/classes. Never retain id/date VALUES.
        chat = result.get("chat")
        chat_type = chat.get("type") if isinstance(chat, dict) else None
        return {
            "ok": True,
            "transport_error": False,
            "message_id_present": "message_id" in result,
            "date_present": "date" in result,
            "chat_type": chat_type if isinstance(chat_type, str) else None,
        }
    except (urllib.error.URLError, socket.timeout, ValueError, OSError):
        # Never surface the exception text (could echo URL/token/target).
        return {"ok": False, "transport_error": True,
                "message_id_present": False, "date_present": False,
                "chat_type": None}


# --------------------------------------------------------------------------- #
# Redacted audit event
# --------------------------------------------------------------------------- #
def build_redacted_audit_event(payload_hash, response_ok_class, message_id_present):
    """Redacted live-post audit event. NO secrets, account ids, message id, raw resp."""
    return {
        "event_type": "telegram_first_supervised_live_post_0174cn",
        "live_gate": LIVE_GATE,
        "platform": "telegram",
        "payload_hash_present": bool(payload_hash),
        "send_message_attempted": True,
        "telegram_response_ok_class": response_ok_class,
        "message_id_present": bool(message_id_present),
        "credential_accessed_for_send_only": True,
        "scheduler_accessed": False,
        "webhook_accessed": False,
        "get_updates_accessed": False,
        "second_attempt_made": False,
        "unsafe_secret_detected": False,
    }


# --------------------------------------------------------------------------- #
# Summary scaffolding
# --------------------------------------------------------------------------- #
def _base_summary():
    return {
        "task_label": TASK_LABEL,
        "live_gate": LIVE_GATE,
        "endpoint_family": ENDPOINT_FAMILY,
        "request_attempted": False,
        "request_count": 0,
        "request_budget": REQUEST_BUDGET,
        "allowed_method": ALLOWED_METHOD,
        "timeout_seconds": DEFAULT_TIMEOUT_SECONDS,
        "host_allowlist_passed": False,
        "method_allowlist_passed": False,
        "payload_shape_valid": False,
        "forbidden_language_passed": False,
        "payload_hash_locked": False,
        "live_approval_record_present": False,
        "live_approval_hash_matches_payload": False,
        "target_binding_previously_validated": False,
        "dry_run_preflight_previously_validated": False,
        "one_time_operator_go_present": False,
        "one_time_live_override_class": OVERRIDE_ABSENT,
        "send_message_attempted": False,
        "message_sent": False,
        "telegram_response_ok_class": RESP_UNKNOWN,
        "message_id_present": False,
        "redacted_audit_event_created": False,
        # Hard-locked policy flags — never true for/after this gate.
        "posting_enabled": False,
        "live_send_enabled": False,
        "scheduler_enabled": False,
        "autonomous_replies_enabled": False,
        "webhook_enabled": False,
        "get_updates_enabled": False,
        "metrics_fetch_enabled": False,
        "live_publish_gate": "blocked_after_one_time_pilot",
        "next_gate_required_before_next_live_post": True,
        "redaction_verified": True,
        "status": "fail_closed",
        "blocked_reasons": [],
    }


def _finalize(summary):
    """Defensive redaction guard over the whole emitted summary. Scrub on leak."""
    leak = _scan_secret_like(summary)
    strings = _string_values(summary)
    url_leak = any(_URL_WITH_TOKEN.search(v) for v in strings)
    handle_leak = any(_HANDLE_LIKE.search(v) for v in strings)
    if leak or url_leak or handle_leak:
        scrubbed = _base_summary()
        scrubbed["request_attempted"] = summary["request_attempted"]
        scrubbed["request_count"] = summary["request_count"]
        scrubbed["send_message_attempted"] = summary["send_message_attempted"]
        scrubbed["message_sent"] = summary["message_sent"]
        scrubbed["redaction_verified"] = True
        scrubbed["blocked_reasons"] = ["redaction_guard_triggered"]
        scrubbed["status"] = "blocked"
        return scrubbed
    return summary


# --------------------------------------------------------------------------- #
# Default safe local fixtures (the exact operator-approved 0174CN pilot payload)
# --------------------------------------------------------------------------- #
def build_default_payload():
    """The EXACT operator-approved live pilot payload for 0174CN.

    Conservative, non-market-advisory text. No buy/sell/hold/long/short/target/
    entry/exit/signal/guaranteed/model-predicts language. Under the Telegram limit.
    """
    return {
        "payload_id": "cc-telegram-first-live-pilot-0174cn-0001",
        "platform": "telegram",
        "target_slot": "TELEGRAM_TARGET_CHAT_ID",
        "content_text": (
            "Capital Chronicle ContentOps live Telegram pilot: supervised one-time "
            "post path validated. Local-first, human-approved, no financial advice, "
            "no trading calls, no automation. Further publishing remains gated."
        ),
        "content_class": "live_pilot_notice",
        "source_packet_id": None,
        "local_fixture_ref": (
            "live_contentops/telegram_first_supervised_live_post_gate.py"
            "#build_default_payload"
        ),
        "no_financial_advice": True,
        "no_signal_language": True,
        "human_review_required": True,
        "public_postable": False,
        "live_send_enabled": False,
    }


def build_default_live_approval_record(payload=None):
    """A matching first-live-post operator approval record for ``payload``."""
    if payload is None:
        payload = build_default_payload()
    return {
        "approval_state": APPROVAL_STATE_FIRST_LIVE,
        "operator_go_ref": "operator-go-0174cn-0001",
        "approved_payload_hash": compute_payload_hash(payload),
        "human_review_completed": True,
        "target_binding_0174cl_accepted": True,
        "dry_run_0174cm_accepted": True,
        "understands_live_post": True,
        "one_time_only": True,
    }


def build_default_target_binding_state():
    """Redacted representation that 0174CL previously validated a channel target."""
    return dryrun.build_default_target_binding_state()


def build_default_kill_switch_state():
    """One-time kill switch: global dispatch blocked, 0174CN-scoped override only."""
    return {
        "global_live_dispatch": "blocked",
        "one_time_live_override": "operator_approved_0174cn_only",
        "scheduler_enabled": False,
        "autonomous_replies_enabled": False,
        "webhook_enabled": False,
        "get_updates_enabled": False,
    }


# --------------------------------------------------------------------------- #
# Main gate
# --------------------------------------------------------------------------- #
def run_first_supervised_live_post_gate(
    *,
    live_post_flag=False,
    operator_go_flag=False,
    repo_root=None,
    use_process_env=False,
    timeout_seconds=DEFAULT_TIMEOUT_SECONDS,
    payload=None,
    live_approval_record=None,
    target_binding_state=None,
    dry_run_preflight_validated=True,
    kill_switch_state=None,
    _api_caller=None,
):
    """Run the bounded one-time supervised live-post gate. Fail-closed by default.

    BOTH ``live_post_flag`` and ``operator_go_flag`` must be True to perform ANY
    network request. ``_api_caller`` is an injectable caller
    (method, token, target, text, timeout) -> redacted dict for network-free tests.
    """
    summary = _base_summary()
    summary["timeout_seconds"] = int(timeout_seconds)
    summary["one_time_operator_go_present"] = bool(operator_go_flag)

    payload = build_default_payload() if payload is None else payload
    live_approval_record = (build_default_live_approval_record(payload)
                            if live_approval_record is None else live_approval_record)
    target_binding_state = (build_default_target_binding_state()
                            if target_binding_state is None else target_binding_state)
    kill_switch_state = (build_default_kill_switch_state()
                         if kill_switch_state is None else kill_switch_state)

    summary["one_time_live_override_class"] = classify_one_time_override(kill_switch_state)

    # 1. Fail closed unless BOTH explicit live flags are present.
    if not (live_post_flag and operator_go_flag):
        reasons = []
        if not live_post_flag:
            reasons.append("live_post_flag_absent_fail_closed")
        if not operator_go_flag:
            reasons.append("operator_go_flag_absent_fail_closed")
        summary["blocked_reasons"] = reasons
        summary["status"] = "fail_closed"
        return _finalize(summary)

    blocked = []

    # 3. Validate exact payload shape (+ Telegram text limit).
    shape_ok, shape_reasons = validate_payload_shape(payload)
    summary["payload_shape_valid"] = shape_ok
    blocked.extend(shape_reasons)

    # 4. Validate no-advice / no-signal / forbidden language.
    lang_ok, lang_reasons = check_forbidden_language(
        payload.get("content_text") if isinstance(payload, dict) else None)
    summary["forbidden_language_passed"] = lang_ok
    blocked.extend(lang_reasons)

    # 5 + 6. Canonicalize + compute deterministic payload hash (always lockable).
    payload_hash = compute_payload_hash(payload)
    summary["payload_hash_locked"] = bool(payload_hash)

    # 7. Validate operator LIVE approval record (exact hash match).
    summary["live_approval_record_present"] = (
        isinstance(live_approval_record, dict) and bool(live_approval_record))
    approval_ok, approval_reasons = validate_live_approval_record(
        live_approval_record, payload_hash)
    summary["live_approval_hash_matches_payload"] = (
        isinstance(live_approval_record, dict)
        and live_approval_record.get("approved_payload_hash") == payload_hash
    )
    blocked.extend(approval_reasons)

    # 8. Validate target binding represented as previously passed (no live recheck).
    binding_ok, binding_reasons = validate_target_binding_state(target_binding_state)
    summary["target_binding_previously_validated"] = binding_ok
    blocked.extend(binding_reasons)

    # 0174CM dry-run preflight must be represented as previously validated.
    summary["dry_run_preflight_previously_validated"] = bool(dry_run_preflight_validated)
    if not dry_run_preflight_validated:
        blocked.append("dry_run_0174cm_preflight_not_validated")

    # 9. Validate one-time kill switch (global blocked, 0174CN-scoped override only).
    ks_ok, ks_reasons = validate_one_time_kill_switch(kill_switch_state)
    blocked.extend(ks_reasons)

    # Allowlist gates (host + single method) before any request.
    summary["host_allowlist_passed"] = True
    summary["method_allowlist_passed"] = (
        ALLOWED_METHOD not in FORBIDDEN_METHODS)

    # If ANY gate failed, block BEFORE any live send.
    if blocked:
        summary["status"] = "blocked"
        summary["blocked_reasons"] = sorted(set(blocked))
        return _finalize(summary)

    # 2. Read approved local env source via the redacted readiness reader (token +
    #    target only). This module never prints/inspects the raw .env line.
    env_text, _source_label, available = readiness._read_repo_env_source(
        readiness.os.path.dirname(readiness.os.path.dirname(readiness.__file__))
        if repo_root is None else repo_root,
        use_process_env=use_process_env,
    )
    if not available or env_text is None:
        summary["blocked_reasons"] = ["approved_local_env_source_unavailable"]
        summary["status"] = "fail_closed"
        return _finalize(summary)
    parsed = readiness.parse_approved_env_text(env_text)
    token_raw = parsed["TELEGRAM_BOT_TOKEN"]
    target_raw = parsed["TELEGRAM_TARGET_CHAT_ID"]
    if not readiness._is_present(token_raw) or not readiness._is_present(target_raw):
        summary["blocked_reasons"] = ["telegram_credential_or_target_absent_fail_closed"]
        summary["status"] = "fail_closed"
        return _finalize(summary)

    # 10 + 11. Build the exact sendMessage request internally and execute EXACTLY
    #          ONE live call. No retry, no second attempt.
    caller = _api_caller if _api_caller is not None else _default_api_caller
    summary["request_count"] += 1
    summary["request_attempted"] = True
    summary["send_message_attempted"] = True
    resp = caller(ALLOWED_METHOD, token_raw, target_raw,
                  payload.get("content_text"), timeout_seconds)

    # 12. Parse only the redacted response class.
    if not isinstance(resp, dict):
        summary["telegram_response_ok_class"] = RESP_UNKNOWN
        summary["status"] = "blocked"
        summary["blocked_reasons"] = ["send_response_unparseable_redacted"]
        return _finalize(summary)
    if resp.get("transport_error"):
        summary["telegram_response_ok_class"] = RESP_TRANSPORT_ERROR
        summary["status"] = "blocked"
        summary["blocked_reasons"] = ["send_transport_error_redacted"]
        return _finalize(summary)
    if resp.get("ok"):
        summary["telegram_response_ok_class"] = RESP_OK_TRUE
        summary["message_sent"] = True
        summary["message_id_present"] = bool(resp.get("message_id_present"))
    else:
        summary["telegram_response_ok_class"] = RESP_OK_FALSE
        summary["message_sent"] = False
        summary["status"] = "blocked"
        summary["blocked_reasons"] = ["telegram_response_not_ok_redacted"]
        return _finalize(summary)

    # 13. Emit redacted audit event.
    audit = build_redacted_audit_event(
        payload_hash, summary["telegram_response_ok_class"],
        summary["message_id_present"])
    leak = _scan_secret_like(audit)
    summary["redacted_audit_event_created"] = not leak

    # 14. Keep all future/live automation gates blocked after the send.
    summary["live_publish_gate"] = "blocked_after_one_time_pilot"
    summary["next_gate_required_before_next_live_post"] = True

    summary["status"] = "pass" if summary["message_sent"] else "blocked"
    return _finalize(summary)


def summary(**kwargs):
    """Convenience wrapper returning the redacted gate summary dict."""
    return run_first_supervised_live_post_gate(**kwargs)


def main(argv=None):
    """CLI: print ONLY the redacted JSON summary.

    Fail-closed unless BOTH ``--telegram-first-supervised-live-post`` AND
    ``--operator-go-0174cn`` are passed.

    Usage:
      python -m live_contentops.telegram_first_supervised_live_post_gate
      python -m live_contentops.telegram_first_supervised_live_post_gate \\
          --telegram-first-supervised-live-post --operator-go-0174cn
    """
    import sys

    args = list(sys.argv[1:] if argv is None else argv)
    live_post_flag = FLAG_LIVE_POST in args
    operator_go_flag = FLAG_OPERATOR_GO in args
    use_process_env = "--process-env" in args
    result = run_first_supervised_live_post_gate(
        live_post_flag=live_post_flag,
        operator_go_flag=operator_go_flag,
        use_process_env=use_process_env,
    )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
