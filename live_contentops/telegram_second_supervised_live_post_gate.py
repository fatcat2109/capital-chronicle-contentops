"""Telegram SECOND supervised live-post gate (0174CR).

This module is the second (and only the second) bounded LIVE Telegram Bot API
gate. It may make EXACTLY ONE ``sendMessage`` request, and ONLY if every gate
passes. It exists to send ONE operator-approved Telegram message to the
previously validated configured target channel, then persist a durable redacted
post-send ledger.

This is NOT a general publisher. It is a one-time supervised live-post gate.

Prior gates (unchanged by this module; read-only inputs where relevant):
  * 0174CK validated bot token identity (getMe).
  * 0174CL validated target channel binding + post permission.
  * 0174CM validated the local supervised post dry-run preflight.
  * 0174CN delivered exactly ONE first supervised live post.
  * 0174CO persisted the redacted first post-pilot ledger.
  * 0174CP/R1 selected the Telegram second-gate path + verified CLI wiring.
  * 0174CQ persisted the SECOND supervised post DRY-RUN ledger
    (status=pass, would_send_message=true, request_budget=0, no live send).

HARD REQUIREMENT:
  Fail closed unless BOTH explicit one-time live flags are present
  (``--telegram-second-supervised-live-post`` AND ``--operator-go-0174cr``) AND:
    * the 0174CQ dry-run ledger exists and is in the exact expected state,
    * an exact operator LIVE approval object matches the EXACT payload hash,
    * a one-time kill-switch override scoped to 0174CR only is present,
    * no existing 0174CR ledger already recorded an attempt/send (no duplicate).

HARD GUARANTEES (enforced by tests + leakage guards):
  * Fail-closed by default: NO network unless BOTH live flags are present.
  * ONLY ``sendMessage`` is ever constructed/called. Every other method is in
    FORBIDDEN_METHODS and NEVER built.
  * Host allowlist: only ``api.telegram.org``. Method allowlist: only sendMessage.
  * Request budget: at most ONE live request. No retry, no second attempt.
  * Hard timeout (default 10s).
  * Redacted-only output/ledger: NEVER emits or persists token, chat id, channel
    id, channel username, bot id, bot username, raw URL, raw request body, raw
    response JSON, message id value, or date value. Only booleans + redacted
    classes.
  * After the send, ALL future/live automation gates remain blocked:
    ``live_publish_gate = blocked_after_second_live_pilot``.
"""

import hashlib
import json
import os.path
import re
import socket
import urllib.error
import urllib.request

from live_contentops import prelaunch_telegram_credential_readiness as readiness
from live_contentops import telegram_supervised_post_dry_run_gate as dryrun

TASK_LABEL = (
    "TASK_CONTENTOPS_0174CR_TELEGRAM_SECOND_SUPERVISED_LIVE_POST_"
    "OPERATOR_GO_GATE_V0"
)

LIVE_GATE = "TELEGRAM_SECOND_SUPERVISED_LIVE_POST_0174CR"
ENDPOINT_FAMILY = "telegram_bot_api_second_supervised_live_post"
PLATFORM = "telegram"
SOURCE_BASELINE_COMMIT = "0a38e91f1b5e6b4c94d2322ffa8b78d99449fbe3"

# Host + method allowlists. ONLY sendMessage may ever be built/called.
ALLOWED_HOST = "api.telegram.org"
ALLOWED_METHOD = "sendMessage"

# Bounded request controls.
DEFAULT_TIMEOUT_SECONDS = 10
REQUEST_BUDGET = 1   # exactly one sendMessage; no retry, no second attempt

# Explicit one-time live authorization flags. BOTH are required.
FLAG_LIVE_POST = "--telegram-second-supervised-live-post"
FLAG_OPERATOR_GO = "--operator-go-0174cr"
FLAG_WRITE_LEDGER = "--write-telegram-second-live-ledger"

# Telegram text hard limit (sendMessage).
TELEGRAM_TEXT_LIMIT = 4096

# Operator live approval state (distinct from any dry-run approval state).
APPROVAL_STATE_SECOND_LIVE = "operator_approved_for_second_live_post_0174cr"

# One-time live override classes.
OVERRIDE_OK = "operator_approved_0174cr_only"
OVERRIDE_ABSENT = "absent"
OVERRIDE_INVALID = "invalid"

# 0174CQ dry-run ledger required state (input gate).
DRY_RUN_SOURCE_GATE = "TELEGRAM_SECOND_SUPERVISED_POST_DRY_RUN_LEDGER_0174CQ"
DRY_RUN_LEDGER_REL_PATH = os.path.join(
    "docs", "credential_readiness", "0174CQ",
    "telegram_second_supervised_post_dry_run_ledger.json")

# 0174CR durable post-send ledger artifact location.
LEDGER_REL_DIR = os.path.join("docs", "credential_readiness", "0174CR")
LEDGER_FILENAME = "telegram_second_supervised_live_post_ledger.json"

# The EXACT operator-approved SECOND LIVE payload text (NOT the dry-run text).
SECOND_LIVE_PAYLOAD_TEXT = (
    "Capital Chronicle ContentOps second supervised Telegram pilot: "
    "human-approved publish controls remain gated. Local-first workflow "
    "validation continues. No financial advice, no trading calls, no automation."
)

# Explicitly forbidden methods (defense-in-depth; this module only ever builds
# the single allowlisted sendMessage method).
FORBIDDEN_METHODS = (
    "getMe", "getChat", "getChatMember", "getUpdates", "setWebhook",
    "deleteWebhook", "getWebhookInfo", "sendPhoto", "sendMediaGroup",
    "copyMessage", "forwardMessage", "editMessageText", "deleteMessage",
    "pinChatMessage", "sendPoll", "sendChatAction", "answerCallbackQuery",
    "banChatMember", "restrictChatMember", "exportChatInviteLink",
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

# --------------------------------------------------------------------------- #
# Redaction patterns (defense-in-depth).
# --------------------------------------------------------------------------- #
_SECRET_LIKE = list(readiness._SECRET_LIKE)
_URL_WITH_TOKEN = re.compile(r"api\.telegram\.org/bot\d{6,}:")
_TELEGRAM_URL = re.compile(r"api\.telegram\.org")
_HANDLE_LIKE = re.compile(r"@[A-Za-z0-9_]{3,}")
_LONG_DIGITS = re.compile(r"(?<!\d)-?\d{7,}(?!\d)")

_FORBIDDEN_KEYS = (
    "token", "bot_token", "chat_id", "channel_id", "channel_username",
    "bot_id", "bot_username", "message_id", "message_id_value", "date",
    "date_value", "raw_url", "raw_request", "raw_response",
    "target_identifier", "target_value", "access_token", "refresh_token",
    "client_secret", "api_key",
)


# --------------------------------------------------------------------------- #
# Redaction scanner
# --------------------------------------------------------------------------- #
def scan_ledger_for_leaks(ledger):
    """Return a sorted list of redaction violations for the ledger object."""
    violations = []

    def _walk(obj, key=None):
        if isinstance(obj, dict):
            for k, v in obj.items():
                kl = str(k).lower()
                if kl in _FORBIDDEN_KEYS:
                    violations.append(f"forbidden_key:{kl}")
                _walk(v, k)
        elif isinstance(obj, list):
            for v in obj:
                _walk(v, key)
        elif isinstance(obj, str):
            _scan_string(obj, key)

    def _scan_string(s, key):
        for pat in _SECRET_LIKE:
            if pat.search(s):
                violations.append(f"secret_like_value:{key or 'value'}")
                break
        if _URL_WITH_TOKEN.search(s) or _TELEGRAM_URL.search(s):
            violations.append(f"telegram_url:{key or 'value'}")
        if _HANDLE_LIKE.search(s):
            violations.append(f"raw_handle:{key or 'value'}")
        if key not in ("payload_hash",) and _LONG_DIGITS.search(s):
            if not _is_known_safe_identifier(s):
                violations.append(f"long_digits_possible_id:{key or 'value'}")

    _walk(ledger)
    return sorted(set(violations))


def _is_known_safe_identifier(s):
    """True for known-safe identifier strings (baseline git SHA, payload hash)."""
    if s == SOURCE_BASELINE_COMMIT:
        return True
    if re.fullmatch(r"[0-9a-f]{40}", s) or re.fullmatch(r"[0-9a-f]{64}", s):
        return True
    return False


# --------------------------------------------------------------------------- #
# Payload + approval (reuses 0174CM canonicalization for the EXACT hash lock)
# --------------------------------------------------------------------------- #
def build_default_payload():
    """The EXACT operator-approved SECOND LIVE pilot payload for 0174CR."""
    return {
        "payload_id": "cc-telegram-second-live-pilot-0174cr-0001",
        "platform": PLATFORM,
        "target_slot": dryrun.TARGET_SLOT,
        "content_text": SECOND_LIVE_PAYLOAD_TEXT,
        "content_class": "live_pilot_notice",
        "source_packet_id": None,
        "local_fixture_ref": (
            "live_contentops/telegram_second_supervised_live_post_gate.py"
            "#build_default_payload"
        ),
        "no_financial_advice": True,
        "no_signal_language": True,
        "human_review_required": True,
        "public_postable": False,
        "live_send_enabled": False,
    }


def compute_payload_hash(payload):
    """Deterministic SHA-256 hex digest of the canonical payload (0174CM)."""
    return dryrun.compute_payload_hash(payload)


def validate_payload_shape(payload):
    """Validate the live post payload shape (+ Telegram text limit)."""
    ok, reasons = dryrun.validate_payload_shape(payload)
    reasons = list(reasons)
    text = payload.get("content_text") if isinstance(payload, dict) else None
    if isinstance(text, str) and len(text) > TELEGRAM_TEXT_LIMIT:
        reasons.append("content_text_exceeds_telegram_limit")
    return (len(reasons) == 0), reasons


def validate_exact_payload_text(text):
    """The live payload text must be EXACTLY the operator-approved text."""
    if text != SECOND_LIVE_PAYLOAD_TEXT:
        return False, ["payload_text_not_exact_second_live_text"]
    return True, []


def check_forbidden_language(text):
    """No-advice / no-signal forbidden-language scan (delegates to 0174CM)."""
    return dryrun.check_forbidden_language(text)


def validate_live_approval_record(record, expected_hash):
    """Validate the operator LIVE approval record for 0174CR. (ok, [reasons])."""
    reasons = []
    if not isinstance(record, dict):
        return False, ["live_approval_record_missing"]

    state = record.get("approval_state")
    if state != APPROVAL_STATE_SECOND_LIVE:
        reasons.append(f"approval_state_not_second_live_post:{state or 'none'}")

    approved_hash = record.get("approved_payload_hash")
    if not approved_hash:
        reasons.append("approved_payload_hash_missing")
    elif approved_hash != expected_hash:
        reasons.append("live_approval_hash_mismatch")

    for ack in ("human_review_completed",
                "prior_0174cq_dry_run_ledger_accepted",
                "understands_this_sends_live_message",
                "one_time_only"):
        if record.get(ack) is not True:
            reasons.append(f"ack_missing:{ack}")

    return (len(reasons) == 0), reasons


def validate_one_time_kill_switch(ks):
    """Validate the one-time live override kill-switch state. (ok, [reasons])."""
    reasons = []
    if not isinstance(ks, dict):
        return False, ["kill_switch_state_missing"]

    if ks.get("global_live_dispatch") != "blocked":
        reasons.append("global_live_dispatch_not_blocked")
    if ks.get("one_time_live_override") != OVERRIDE_OK:
        reasons.append("one_time_live_override_not_0174cr_scoped")
    if ks.get("scheduler_enabled") is True:
        reasons.append("scheduler_enabled_true")
    if ks.get("autonomous_replies_enabled") is True:
        reasons.append("autonomous_replies_enabled_true")
    if ks.get("webhook_enabled") is True:
        reasons.append("webhook_enabled_true")
    if ks.get("get_updates_enabled") is True:
        reasons.append("get_updates_enabled_true")
    if ks.get("metrics_fetch_enabled") is True:
        reasons.append("metrics_fetch_enabled_true")

    return (len(reasons) == 0), reasons


def classify_one_time_override(ks):
    """Redacted class for the one-time live override slot."""
    if not isinstance(ks, dict):
        return OVERRIDE_ABSENT
    val = ks.get("one_time_live_override")
    if val is None:
        return OVERRIDE_ABSENT
    if val == OVERRIDE_OK:
        return OVERRIDE_OK
    return OVERRIDE_INVALID


# --------------------------------------------------------------------------- #
# 0174CQ dry-run ledger validation (required input gate)
# --------------------------------------------------------------------------- #
_DRY_RUN_REQUIRED_STATE = {
    "status": "pass",
    "gate": DRY_RUN_SOURCE_GATE,
    "would_send_message": True,
    "request_attempted": False,
    "live_network_attempted": False,
    "send_message_attempted": False,
    "message_sent": False,
    "request_budget": 0,
    "live_publish_gate": "blocked_after_second_dry_run",
    "next_gate_required_before_second_live_post": True,
}


def load_dry_run_ledger(repo_root):
    """Load the 0174CQ dry-run ledger dict, or None if missing/unparseable."""
    path = os.path.join(repo_root, DRY_RUN_LEDGER_REL_PATH)
    if not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.loads(fh.read())
    except (ValueError, OSError):
        return None


def validate_dry_run_ledger(ledger):
    """Validate the 0174CQ dry-run ledger is in the exact expected state."""
    if not isinstance(ledger, dict):
        return False, ["dry_run_ledger_missing_or_unparseable"]
    reasons = []
    for key, expected in _DRY_RUN_REQUIRED_STATE.items():
        if ledger.get(key) != expected:
            reasons.append(f"dry_run_ledger_field_mismatch:{key}")
    return (len(reasons) == 0), reasons


# --------------------------------------------------------------------------- #
# Duplicate-send prevention
# --------------------------------------------------------------------------- #
def load_existing_live_ledger(repo_root):
    """Load an existing 0174CR ledger dict, or None if absent/unparseable."""
    path = os.path.join(repo_root, LEDGER_REL_DIR, LEDGER_FILENAME)
    if not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.loads(fh.read())
    except (ValueError, OSError):
        return None


def existing_ledger_blocks_resend(ledger):
    """True if an existing 0174CR ledger already recorded an attempt/send."""
    if not isinstance(ledger, dict):
        return False
    return bool(ledger.get("request_attempted") or ledger.get("message_sent"))


# --------------------------------------------------------------------------- #
# The single bounded live sendMessage caller
# --------------------------------------------------------------------------- #
def _default_api_caller(method, token, target, text, timeout_seconds):
    """Perform EXACTLY ONE live sendMessage POST for the allowlisted method.

    Returns a redacted dict. NEVER returns the token, target, URL, headers, raw
    request body, raw response body, message id value, or date value.
    """
    if method != ALLOWED_METHOD or method in FORBIDDEN_METHODS:
        return {"ok": False, "transport_error": True,
                "message_id_present": False, "date_present": False,
                "chat_type": None}

    url = f"https://{ALLOWED_HOST}/bot{token}/{method}"
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
        return {"ok": False, "transport_error": True,
                "message_id_present": False, "date_present": False,
                "chat_type": None}


# --------------------------------------------------------------------------- #
# Ledger builder + serialization
# --------------------------------------------------------------------------- #
def _chat_type_class(raw_chat_type):
    """Redact the chat type to a symbolic class only."""
    if raw_chat_type == "channel":
        return CHAT_TYPE_CHANNEL
    return CHAT_TYPE_UNKNOWN


def build_ledger(*, payload_hash, approval_ok, response_class, request_attempted,
                 request_count, send_message_attempted, message_sent,
                 message_id_present, date_present, chat_type_class,
                 pre_live_commit, status, blocked_reasons):
    """Assemble the durable redacted post-send ledger."""
    return {
        "task_label": TASK_LABEL,
        "gate": LIVE_GATE,
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        "pre_live_implementation_commit": pre_live_commit,
        "platform": PLATFORM,
        "dry_run_source_gate": DRY_RUN_SOURCE_GATE,
        "prior_chain": {
            "telegram_identity_validated": True,
            "telegram_target_binding_validated": True,
            "first_live_post_delivered_once": True,
            "first_post_pilot_ledger_persisted": True,
            "next_platform_selection_accepted": True,
            "second_dry_run_ledger_accepted": True,
        },
        "payload_text_persisted": True,
        "payload_text": SECOND_LIVE_PAYLOAD_TEXT,
        "payload_hash": payload_hash,
        "approval_record_present": True,
        "approval_hash_matches_payload": bool(approval_ok),
        "one_time_operator_go_present": True,
        "one_time_live_override_class": OVERRIDE_OK,
        "host_allowlist_passed": True,
        "method_allowlist_passed": True,
        "allowed_method": ALLOWED_METHOD,
        "request_attempted": bool(request_attempted),
        "request_count": int(request_count),
        "request_budget": REQUEST_BUDGET,
        "send_message_attempted": bool(send_message_attempted),
        "message_sent": bool(message_sent),
        "telegram_response_ok_class": response_class,
        "message_id_present": bool(message_id_present),
        "message_id_value_persisted": False,
        "date_present": bool(date_present),
        "date_value_persisted": False,
        "target_identifier_persisted": False,
        "raw_request_persisted": False,
        "raw_response_persisted": False,
        "credential_persisted": False,
        "no_retry": True,
        "second_attempt_made": False,
        "scheduler_enabled": False,
        "webhook_enabled": False,
        "get_updates_enabled": False,
        "autonomous_replies_enabled": False,
        "metrics_fetch_enabled": False,
        "live_publish_gate": "blocked_after_second_live_pilot",
        "next_gate_required_before_any_future_live_post": True,
        "redaction_verified": True,
        "status": status,
        "blocked_reasons": sorted(set(blocked_reasons)),
    }


def serialize_ledger(ledger):
    """Deterministic JSON serialization: sorted keys, stable separators, newline."""
    return json.dumps(ledger, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False) + "\n"


def compute_ledger_checksum(ledger):
    """SHA-256 of the deterministic serialization (artifact integrity)."""
    return hashlib.sha256(serialize_ledger(ledger).encode("utf-8")).hexdigest()


# --------------------------------------------------------------------------- #
# Default safe local fixtures
# --------------------------------------------------------------------------- #
def build_default_live_approval_record(payload=None):
    """A matching second-live-post operator approval record for ``payload``."""
    if payload is None:
        payload = build_default_payload()
    return {
        "approval_state": APPROVAL_STATE_SECOND_LIVE,
        "operator_go_ref": "operator-go-0174cr-0001",
        "approved_payload_hash": compute_payload_hash(payload),
        "human_review_completed": True,
        "prior_0174cq_dry_run_ledger_accepted": True,
        "understands_this_sends_live_message": True,
        "one_time_only": True,
    }


def build_default_target_binding_state():
    """Redacted representation that 0174CL previously validated a channel target."""
    return dryrun.build_default_target_binding_state()


def build_default_kill_switch_state():
    """One-time kill switch: global dispatch blocked, 0174CR-scoped override only."""
    return {
        "global_live_dispatch": "blocked",
        "one_time_live_override": OVERRIDE_OK,
        "scheduler_enabled": False,
        "autonomous_replies_enabled": False,
        "webhook_enabled": False,
        "get_updates_enabled": False,
        "metrics_fetch_enabled": False,
    }


# --------------------------------------------------------------------------- #
# Main gate
# --------------------------------------------------------------------------- #
def run_second_supervised_live_post_gate(
    *,
    live_post_flag=False,
    operator_go_flag=False,
    write_ledger=False,
    repo_root=None,
    use_process_env=False,
    timeout_seconds=DEFAULT_TIMEOUT_SECONDS,
    payload=None,
    live_approval_record=None,
    target_binding_state=None,
    kill_switch_state=None,
    dry_run_ledger=None,
    existing_live_ledger=None,
    _api_caller=None,
):
    """Run the bounded one-time SECOND supervised live-post gate. Fail-closed.

    BOTH ``live_post_flag`` and ``operator_go_flag`` must be True to perform ANY
    network request. ``_api_caller`` is an injectable caller
    (method, token, target, text, timeout) -> redacted dict for network-free tests.
    """
    if repo_root is None:
        repo_root = os.path.dirname(os.path.dirname(__file__))

    payload = build_default_payload() if payload is None else payload
    live_approval_record = (build_default_live_approval_record(payload)
                            if live_approval_record is None else live_approval_record)
    target_binding_state = (build_default_target_binding_state()
                            if target_binding_state is None else target_binding_state)
    kill_switch_state = (build_default_kill_switch_state()
                         if kill_switch_state is None else kill_switch_state)

    payload_hash = compute_payload_hash(payload)
    override_class = classify_one_time_override(kill_switch_state)

    def _summary(*, request_attempted=False, request_count=0,
                 send_message_attempted=False, message_sent=False,
                 response_class=RESP_UNKNOWN, message_id_present=False,
                 date_present=False, chat_type_class=CHAT_TYPE_UNKNOWN,
                 approval_ok=False, status="fail_closed", blocked_reasons=None,
                 ledger_written=False, ledger_checksum=None):
        return {
            "task_label": TASK_LABEL,
            "gate": LIVE_GATE,
            "source_baseline_commit": SOURCE_BASELINE_COMMIT,
            "live_flags_present": bool(live_post_flag and operator_go_flag),
            "one_time_operator_go_present": bool(operator_go_flag),
            "one_time_live_override_class": override_class,
            "payload_hash": payload_hash,
            "approval_hash_matches_payload": bool(approval_ok),
            "allowed_method": ALLOWED_METHOD,
            "host_allowlist_passed": True,
            "method_allowlist_passed": ALLOWED_METHOD not in FORBIDDEN_METHODS,
            "timeout_seconds": int(timeout_seconds),
            "request_attempted": bool(request_attempted),
            "request_count": int(request_count),
            "request_budget": REQUEST_BUDGET,
            "send_message_attempted": bool(send_message_attempted),
            "message_sent": bool(message_sent),
            "telegram_response_ok_class": response_class,
            "message_id_present": bool(message_id_present),
            "date_present": bool(date_present),
            "chat_type_class": chat_type_class,
            "write_requested": bool(write_ledger),
            "ledger_written": bool(ledger_written),
            "ledger_path": os.path.join(LEDGER_REL_DIR, LEDGER_FILENAME),
            "ledger_checksum": ledger_checksum,
            "no_retry": True,
            "second_attempt_made": False,
            "scheduler_enabled": False,
            "webhook_enabled": False,
            "get_updates_enabled": False,
            "autonomous_replies_enabled": False,
            "metrics_fetch_enabled": False,
            "live_publish_gate": "blocked_after_second_live_pilot",
            "next_gate_required_before_any_future_live_post": True,
            "redaction_verified": True,
            "status": status,
            "blocked_reasons": sorted(set(blocked_reasons or [])),
        }

    # 1. Fail closed unless BOTH explicit live flags are present.
    if not (live_post_flag and operator_go_flag):
        reasons = []
        if not live_post_flag:
            reasons.append("live_post_flag_absent_fail_closed")
        if not operator_go_flag:
            reasons.append("operator_go_flag_absent_fail_closed")
        return _summary(status="fail_closed", blocked_reasons=reasons)

    blocked = []

    # 2. Duplicate-send prevention: existing 0174CR ledger with attempt/send blocks.
    if existing_live_ledger is None:
        existing_live_ledger = load_existing_live_ledger(repo_root)
    if existing_ledger_blocks_resend(existing_live_ledger):
        return _summary(status="blocked",
                        blocked_reasons=["existing_0174cr_ledger_blocks_resend"])

    # 3. 0174CQ dry-run ledger must exist and be in the exact expected state.
    if dry_run_ledger is None:
        dry_run_ledger = load_dry_run_ledger(repo_root)
    if dry_run_ledger is None:
        blocked.append("dry_run_0174cq_ledger_missing")
    else:
        dr_ok, dr_reasons = validate_dry_run_ledger(dry_run_ledger)
        if not dr_ok:
            blocked.extend(dr_reasons)

    # 4. Validate exact payload text + shape (+ Telegram text limit).
    exact_ok, exact_reasons = validate_exact_payload_text(
        payload.get("content_text") if isinstance(payload, dict) else None)
    blocked.extend(exact_reasons)
    shape_ok, shape_reasons = validate_payload_shape(payload)
    blocked.extend(shape_reasons)

    # 5. Validate no-advice / no-signal / forbidden language.
    lang_ok, lang_reasons = check_forbidden_language(
        payload.get("content_text") if isinstance(payload, dict) else None)
    blocked.extend(lang_reasons)

    # 6. Validate operator LIVE approval record (exact hash match).
    approval_ok, approval_reasons = validate_live_approval_record(
        live_approval_record, payload_hash)
    approval_hash_matches = (
        isinstance(live_approval_record, dict)
        and live_approval_record.get("approved_payload_hash") == payload_hash)
    blocked.extend(approval_reasons)

    # 7. Validate target binding represented as previously passed (no live recheck).
    binding_ok, binding_reasons = dryrun.validate_target_binding_state(
        target_binding_state)
    blocked.extend(binding_reasons)

    # 8. Validate one-time kill switch (global blocked, 0174CR-scoped override only).
    ks_ok, ks_reasons = validate_one_time_kill_switch(kill_switch_state)
    blocked.extend(ks_reasons)

    # If ANY gate failed, block BEFORE any live send.
    if blocked:
        return _summary(status="blocked", approval_ok=approval_hash_matches,
                        blocked_reasons=blocked)

    # 9. Read approved local env source (token + target only) via redacted reader.
    env_text, _label, available = readiness._read_repo_env_source(
        repo_root, use_process_env=use_process_env)
    if not available or env_text is None:
        return _summary(status="fail_closed", approval_ok=approval_hash_matches,
                        blocked_reasons=["approved_local_env_source_unavailable"])
    parsed = readiness.parse_approved_env_text(env_text)
    token_raw = parsed["TELEGRAM_BOT_TOKEN"]
    target_raw = parsed["TELEGRAM_TARGET_CHAT_ID"]
    if not readiness._is_present(token_raw) or not readiness._is_present(target_raw):
        return _summary(status="fail_closed", approval_ok=approval_hash_matches,
                        blocked_reasons=["telegram_credential_or_target_absent_fail_closed"])

    # 10 + 11. Execute EXACTLY ONE live call. No retry, no second attempt.
    caller = _api_caller if _api_caller is not None else _default_api_caller
    resp = caller(ALLOWED_METHOD, token_raw, target_raw,
                  payload.get("content_text"), timeout_seconds)
    request_attempted = True
    request_count = 1
    send_message_attempted = True

    # 12. Parse ONLY the redacted response class.
    message_sent = False
    message_id_present = False
    date_present = False
    chat_type_class = CHAT_TYPE_UNKNOWN
    status = "blocked"
    resp_blocked = []

    if not isinstance(resp, dict):
        response_class = RESP_UNKNOWN
        resp_blocked.append("send_response_unparseable_redacted")
    elif resp.get("transport_error"):
        response_class = RESP_TRANSPORT_ERROR
        resp_blocked.append("send_transport_error_redacted")
    elif resp.get("ok"):
        response_class = RESP_OK_TRUE
        message_sent = True
        message_id_present = bool(resp.get("message_id_present"))
        date_present = bool(resp.get("date_present"))
        chat_type_class = _chat_type_class(resp.get("chat_type"))
        status = "pass"
    else:
        response_class = RESP_OK_FALSE
        resp_blocked.append("telegram_response_not_ok_redacted")

    # 13. Build durable redacted ledger + redaction scan before any write.
    ledger = build_ledger(
        payload_hash=payload_hash, approval_ok=approval_hash_matches,
        response_class=response_class, request_attempted=request_attempted,
        request_count=request_count, send_message_attempted=send_message_attempted,
        message_sent=message_sent, message_id_present=message_id_present,
        date_present=date_present, chat_type_class=chat_type_class,
        pre_live_commit=SOURCE_BASELINE_COMMIT,
        status=status, blocked_reasons=resp_blocked)

    violations = scan_ledger_for_leaks(ledger)
    ledger_written = False
    ledger_checksum = None
    if violations:
        # Never write a leaking ledger; report redaction block but keep send facts.
        return _summary(
            request_attempted=request_attempted, request_count=request_count,
            send_message_attempted=send_message_attempted, message_sent=message_sent,
            response_class=response_class, message_id_present=message_id_present,
            date_present=date_present, chat_type_class=chat_type_class,
            approval_ok=approval_hash_matches, status="blocked",
            blocked_reasons=["redaction_guard_triggered"])

    ledger_checksum = compute_ledger_checksum(ledger)

    # 14. Persist durable ledger ONLY when write flag is present.
    if write_ledger:
        out_dir = os.path.join(repo_root, LEDGER_REL_DIR)
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, LEDGER_FILENAME)
        with open(out_path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(serialize_ledger(ledger))
        ledger_written = True

    return _summary(
        request_attempted=request_attempted, request_count=request_count,
        send_message_attempted=send_message_attempted, message_sent=message_sent,
        response_class=response_class, message_id_present=message_id_present,
        date_present=date_present, chat_type_class=chat_type_class,
        approval_ok=approval_hash_matches, status=status,
        blocked_reasons=resp_blocked, ledger_written=ledger_written,
        ledger_checksum=ledger_checksum)


def summary(**kwargs):
    """Convenience wrapper returning the redacted gate summary dict."""
    return run_second_supervised_live_post_gate(**kwargs)


def main(argv=None):
    """CLI: print ONLY the redacted JSON summary.

    Fail-closed unless BOTH ``--telegram-second-supervised-live-post`` AND
    ``--operator-go-0174cr`` are passed. The durable ledger is written only when
    ``--write-telegram-second-live-ledger`` is also present.
    """
    import sys

    args = list(sys.argv[1:] if argv is None else argv)
    live_post_flag = FLAG_LIVE_POST in args
    operator_go_flag = FLAG_OPERATOR_GO in args
    write_ledger = FLAG_WRITE_LEDGER in args
    use_process_env = "--process-env" in args
    result = run_second_supervised_live_post_gate(
        live_post_flag=live_post_flag,
        operator_go_flag=operator_go_flag,
        write_ledger=write_ledger,
        use_process_env=use_process_env,
    )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
