"""Telegram supervised post dry-run + approval-ledger + kill-switch preflight gate (0174CM).

This is the FINAL preflight gate BEFORE any future supervised live Telegram post.
It proves that a future ``sendMessage`` could only ever happen when EVERY required
control is satisfied, and it NEVER sends a live Telegram message.

It is a STRICTLY LOCAL module:
  * No network of any kind (no urllib / requests / httpx / socket imports).
  * No Telegram live methods are constructed as URLs.
  * No env / credential read (prefers none; reads nothing from .env).
  * Imports ONLY hashlib, json, re.

This gate answers (in redacted/symbolic form only):
  * Is the assembled payload shape valid?
  * Does the payload pass the no-financial-advice / no-signal-language guard?
  * Is the payload canonicalized and SHA-256 hash-locked deterministically?
  * Is there an operator approval record that matches the EXACT payload hash?
  * Is the target channel binding represented as previously validated (0174CL)?
    (We DO NOT re-run any live 0174CL call here.)
  * Does the kill switch allow ONLY the local dry-run path while keeping live
    dispatch in ``active_block``?
  * Can a mock (would-send) sendMessage request/response be produced WITHOUT any
    token / chat id / raw URL, and a redacted audit event emitted?

HARD SEMANTICS:
  * "dry-run passed" != "sent".
  * "operator approved for dry-run" != "operator approved for live post".
  * "target channel binding passed" != "live posting enabled".
  * Future live send requires a separate explicit 0174CN task + operator GO.

HARD GUARANTEES (enforced by tests + leakage guards):
  * Fail-closed by default: the gate runs the local dry-run path ONLY when
    ``dry_run=True`` / CLI ``--telegram-supervised-post-dry-run``. Otherwise it
    returns ``status = fail_closed`` and executes no adapter.
  * ``kill_switch_live_dispatch`` is ALWAYS ``active_block``.
  * ``live_send_enabled`` / ``posting_enabled`` / ``scheduler_enabled`` /
    ``autonomous_replies_enabled`` are ALWAYS ``False``.
  * ``live_publish_gate`` stays ``blocked``; ``next_gate_required_before_live_post``
    stays ``True``.
  * Redacted-only output: booleans + symbolic classes only. A defensive leakage
    guard scrubs the summary if any secret-like value or @handle survives.
"""

import copy
import hashlib
import json
import re

TASK_LABEL = (
    "TASK_CONTENTOPS_0174CM_TELEGRAM_SUPERVISED_POST_DRY_RUN_"
    "APPROVAL_LEDGER_AND_KILL_SWITCH_GATE_V0"
)

LIVE_GATE = "TELEGRAM_SUPERVISED_POST_DRY_RUN"
PLATFORM = "telegram"
TARGET_SLOT = "TELEGRAM_TARGET_CHAT_ID"

# Approval states. Dry-run approval is explicitly NOT a live-post approval.
APPROVAL_STATE_DRY_RUN = "operator_approved_for_dry_run"
APPROVAL_STATE_LIVE_LATER = "operator_approved_for_live_post_later"
APPROVAL_STATE_REVOKED = "revoked"
APPROVAL_STATE_NONE = "none"

# Kill switch symbolic states.
KS_LIVE_DISPATCH_BLOCK = "active_block"
KS_DRY_RUN_PASS = "pass"
KS_DRY_RUN_LOCAL_ONLY = "explicit_local_only_allowed"
KS_DRY_RUN_BLOCKED = "blocked"

# The exact, ordered set of fields that DEFINE the message payload the operator
# approves. The payload hash is computed over the canonical form of these fields
# ONLY, so the approval is bound to the exact content + target + safety posture.
CANONICAL_FIELDS = (
    "payload_id",
    "platform",
    "target_slot",
    "content_text",
    "content_class",
    "source_packet_id",
    "local_fixture_ref",
    "no_financial_advice",
    "no_signal_language",
    "human_review_required",
    "public_postable",
)

# Forbidden financial-advice / trading-signal language (whole-word matched).
FORBIDDEN_TERMS = (
    "buy", "sell", "hold", "long", "short", "target", "entry", "exit",
    "signal", "broker", "order", "execution", "guaranteed", "model says",
    "price target", "stop loss", "take profit",
)

# Secret-like leakage patterns (defense-in-depth). The summary only ever holds
# booleans + symbolic strings, but we scrub if anything matches.
_SECRET_LIKE = [
    re.compile(r"\d{6,}:[A-Za-z0-9_-]{30,}"),          # telegram bot token body
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),  # PEM private key
    re.compile(r"AKIA[0-9A-Z]{16}"),                    # AWS access key id
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),                # GitHub PAT
]
# Guard against a raw bot-api URL containing a token ever surviving into output.
_URL_WITH_TOKEN = re.compile(r"api\.telegram\.org/bot\d{6,}:")
# Guard against a raw channel @handle surviving into output.
_HANDLE_LIKE = re.compile(r"@[A-Za-z0-9_]{3,}")


# --------------------------------------------------------------------------- #
# Canonicalization + deterministic hashing
# --------------------------------------------------------------------------- #
def canonicalize_payload(payload):
    """Return the deterministic canonical JSON string for the payload.

    Only ``CANONICAL_FIELDS`` participate. Keys are emitted in a fixed,
    sorted order with compact separators so the output is stable regardless of
    input dict ordering or unrelated extra keys.
    """
    if not isinstance(payload, dict):
        payload = {}
    canonical = {k: payload.get(k, None) for k in CANONICAL_FIELDS}
    return json.dumps(canonical, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False)


def compute_payload_hash(payload):
    """Deterministic SHA-256 hex digest of the canonical payload."""
    canonical = canonicalize_payload(payload)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# --------------------------------------------------------------------------- #
# Validation helpers
# --------------------------------------------------------------------------- #
def validate_payload_shape(payload):
    """Validate the supervised post payload shape. Returns (ok, [reasons])."""
    reasons = []
    if not isinstance(payload, dict):
        return False, ["payload_not_object"]

    if not payload.get("payload_id"):
        reasons.append("payload_id_missing")
    if payload.get("platform") != PLATFORM:
        reasons.append("platform_not_telegram")
    if payload.get("target_slot") != TARGET_SLOT:
        reasons.append("target_slot_not_expected")
    if not isinstance(payload.get("content_text"), str) or not payload.get("content_text").strip():
        reasons.append("content_text_missing")
    if not payload.get("content_class"):
        reasons.append("content_class_missing")
    if not (payload.get("source_packet_id") or payload.get("local_fixture_ref")):
        reasons.append("source_ref_missing")

    # Required safety posture (must be explicitly set).
    if payload.get("no_financial_advice") is not True:
        reasons.append("no_financial_advice_not_true")
    if payload.get("no_signal_language") is not True:
        reasons.append("no_signal_language_not_true")
    if payload.get("human_review_required") is not True:
        reasons.append("human_review_required_not_true")
    # public_postable must be false unless approved; this gate never marks it true.
    if payload.get("public_postable") is True:
        reasons.append("public_postable_true_not_allowed_in_dry_run")
    # live send is never enabled here.
    if payload.get("live_send_enabled") is True:
        reasons.append("live_send_enabled_true_not_allowed")

    return (len(reasons) == 0), reasons


def check_forbidden_language(text):
    """Whole-word/phrase forbidden-language scan. Returns (passed, [reasons])."""
    reasons = []
    if not isinstance(text, str):
        return False, ["content_text_not_string"]
    haystack = " " + text.lower() + " "
    for term in FORBIDDEN_TERMS:
        t = term.lower()
        if " " in t:
            # multi-word phrase: substring match is sufficient
            if t in haystack:
                reasons.append(f"forbidden_language:{t.replace(' ', '_')}")
        else:
            if re.search(r"(?<![a-z])" + re.escape(t) + r"(?![a-z])", haystack):
                reasons.append(f"forbidden_language:{t}")
    return (len(reasons) == 0), reasons


def validate_approval_record(record, expected_hash):
    """Check approval record matches the EXACT payload hash. (ok, [reasons])."""
    reasons = []
    if not isinstance(record, dict):
        return False, ["approval_record_missing"]

    state = record.get("approval_state")
    if state == APPROVAL_STATE_REVOKED:
        reasons.append("approval_revoked")
    elif state == APPROVAL_STATE_LIVE_LATER:
        # A future-live approval is NOT valid authorization for this gate, and
        # must never be honored as a live-post authorization here.
        reasons.append("live_post_approval_not_valid_for_dry_run_gate")
    elif state != APPROVAL_STATE_DRY_RUN:
        reasons.append(f"approval_state_not_dry_run:{state or APPROVAL_STATE_NONE}")

    if not record.get("operator_approval_ref"):
        reasons.append("operator_approval_ref_missing")

    approved_hash = record.get("approved_payload_hash")
    if not approved_hash:
        reasons.append("approved_payload_hash_missing")
    elif approved_hash != expected_hash:
        reasons.append("approval_hash_mismatch")

    # Required dry-run acknowledgements.
    for ack in ("not_financial_advice_acknowledged",
                "no_signal_language_acknowledged",
                "human_review_completed",
                "dry_run_only_acknowledged"):
        if record.get(ack) is not True:
            reasons.append(f"ack_missing:{ack}")

    return (len(reasons) == 0), reasons


def validate_kill_switch_state(ks):
    """Validate kill switch. live dispatch MUST stay active_block. (ok, [reasons])."""
    reasons = []
    if not isinstance(ks, dict):
        return False, ["kill_switch_state_missing"]

    if ks.get("kill_switch_live_dispatch") != KS_LIVE_DISPATCH_BLOCK:
        reasons.append("kill_switch_live_dispatch_not_active_block")
    if ks.get("live_send_enabled") is True:
        reasons.append("kill_switch_live_send_enabled_true")
    if ks.get("network_allowed") is True:
        reasons.append("kill_switch_network_allowed_true")
    if ks.get("kill_switch_dry_run") not in (KS_DRY_RUN_PASS, KS_DRY_RUN_LOCAL_ONLY):
        reasons.append("kill_switch_dry_run_not_allowed")

    return (len(reasons) == 0), reasons


def validate_target_binding_state(binding):
    """Check target binding is REPRESENTED as previously validated (0174CL).

    We never re-run a live 0174CL call. We only inspect a local, redacted
    representation that the binding gate previously passed for a channel target.
    """
    reasons = []
    if not isinstance(binding, dict):
        return False, ["target_binding_state_missing"]

    if binding.get("binding_validated") is not True:
        reasons.append("target_binding_not_previously_validated")
    if binding.get("target_chat_type_class") != "channel":
        reasons.append("target_binding_not_channel")
    if binding.get("can_post_messages_class") != "true":
        reasons.append("target_binding_post_permission_not_true")
    if binding.get("future_supervised_publish_possible_after_remaining_gates") is not True:
        reasons.append("target_binding_future_publish_not_possible")
    # Defense-in-depth: the binding representation must not carry live re-run intent.
    if binding.get("live_recheck_requested") is True:
        reasons.append("target_binding_live_recheck_requested_not_allowed")

    return (len(reasons) == 0), reasons


# --------------------------------------------------------------------------- #
# Mock (would-send) adapter + redacted audit event
# --------------------------------------------------------------------------- #
def build_mock_send_message_request(payload):
    """Build a redacted mock sendMessage REQUEST CLASS.

    Contains NO token, NO chat id, NO raw URL, NO @handle. Only class-level,
    symbolic descriptors. This is a 'would-send' shape, never a live request.
    """
    content_text = payload.get("content_text", "") if isinstance(payload, dict) else ""
    return {
        "method_class": "sendMessage_mock",
        "platform": PLATFORM,
        "target_slot_class": "configured_target_redacted",
        "parse_mode_class": "plain_text",
        "content_present": bool(isinstance(content_text, str) and content_text.strip()),
        "dry_run": True,
        "mock_only": True,
        "live_execution": False,
        "network_accessed": False,
        "url_constructed": False,
        "token_present_in_request": False,
        "chat_id_present_in_request": False,
    }


def build_mock_send_message_response():
    """Build a redacted mock sendMessage RESPONSE CLASS (would-send only)."""
    return {
        "response_class": "sendMessage_mock_response",
        "mock_only": True,
        "dry_run": True,
        "would_send": True,
        "message_delivered": False,
        "live_execution": False,
        "network_accessed": False,
        "credential_accessed": False,
        "scheduler_accessed": False,
    }


def validate_mock_send_message(mock_req, mock_resp):
    """Validate the mock request/response shape is safe + non-mutating. (ok,[reasons])."""
    reasons = []
    if not isinstance(mock_req, dict) or not isinstance(mock_resp, dict):
        return False, ["mock_objects_missing"]

    if mock_req.get("method_class") != "sendMessage_mock":
        reasons.append("mock_request_method_class_invalid")
    if not mock_req.get("dry_run") or not mock_req.get("mock_only"):
        reasons.append("mock_request_not_dry_run")
    if mock_req.get("live_execution") or mock_req.get("network_accessed"):
        reasons.append("mock_request_live_or_network_true")
    if mock_req.get("url_constructed") or mock_req.get("token_present_in_request") \
            or mock_req.get("chat_id_present_in_request"):
        reasons.append("mock_request_leaks_url_token_or_chat_id")

    if not mock_resp.get("mock_only") or not mock_resp.get("dry_run"):
        reasons.append("mock_response_not_dry_run")
    if mock_resp.get("message_delivered") or mock_resp.get("live_execution") \
            or mock_resp.get("network_accessed"):
        reasons.append("mock_response_claims_delivery_or_live")

    return (len(reasons) == 0), reasons


def build_redacted_audit_event(payload_hash, approval_ref_present):
    """Build a redacted would-send audit event. NO secrets, NO account ids, NO raw request."""
    return {
        "event_type": "telegram_supervised_post_dry_run_would_send",
        "live_gate": LIVE_GATE,
        "platform": PLATFORM,
        "payload_hash_present": bool(payload_hash),
        "approval_ref_present": bool(approval_ref_present),
        "send_message_attempted": False,
        "live_execution": False,
        "network_accessed": False,
        "credential_accessed": False,
        "scheduler_accessed": False,
        "unsafe_secret_detected": False,
    }


def validate_redacted_audit_event(audit):
    """Validate the audit event carries no secrets/account ids/raw request. (ok,[reasons])."""
    reasons = []
    if not isinstance(audit, dict):
        return False, ["audit_event_missing"]
    if audit.get("send_message_attempted") or audit.get("live_execution"):
        reasons.append("audit_claims_send_or_live")
    if audit.get("network_accessed") or audit.get("credential_accessed") \
            or audit.get("scheduler_accessed"):
        reasons.append("audit_claims_network_credential_or_scheduler")
    if audit.get("unsafe_secret_detected"):
        reasons.append("audit_unsafe_secret_detected")
    # Forbidden keys that would indicate a raw request/account id leak.
    for forbidden_key in ("token", "chat_id", "channel_id", "channel_username",
                           "bot_id", "bot_username", "raw_url", "raw_request",
                           "raw_response"):
        if forbidden_key in audit:
            reasons.append(f"audit_forbidden_key:{forbidden_key}")
    leak = _scan_secret_like(audit)
    if leak:
        reasons.extend(leak)
    return (len(reasons) == 0), reasons


def _default_mock_adapter(payload):
    """Default pure mock adapter. Returns NEW objects; never mutates ``payload``.

    Produces (mock_request, mock_response). Performs NO network and NO live call.
    """
    safe_payload = copy.deepcopy(payload) if isinstance(payload, dict) else {}
    req = build_mock_send_message_request(safe_payload)
    resp = build_mock_send_message_response()
    return req, resp


# --------------------------------------------------------------------------- #
# Leakage guard
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
# Summary scaffolding
# --------------------------------------------------------------------------- #
def _base_summary():
    return {
        "task_label": TASK_LABEL,
        "live_gate": LIVE_GATE,
        "platform": PLATFORM,
        "request_attempted": False,
        "live_network_attempted": False,
        "send_message_attempted": False,
        "payload_shape_valid": False,
        "forbidden_language_passed": False,
        "payload_hash_locked": False,
        "approval_record_present": False,
        "approval_hash_matches_payload": False,
        "target_binding_previously_validated": False,
        "kill_switch_live_dispatch": KS_LIVE_DISPATCH_BLOCK,
        "kill_switch_dry_run": KS_DRY_RUN_BLOCKED,
        "dry_run_adapter_executed": False,
        "mock_send_message_shape_valid": False,
        "redacted_audit_event_created": False,
        # Hard-locked policy flags — never true for this gate.
        "posting_enabled": False,
        "live_send_enabled": False,
        "scheduler_enabled": False,
        "autonomous_replies_enabled": False,
        "live_publish_gate": "blocked",
        "next_gate_required_before_live_post": True,
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
        scrubbed["redaction_verified"] = True
        scrubbed["blocked_reasons"] = ["redaction_guard_triggered"]
        scrubbed["status"] = "blocked"
        return scrubbed
    return summary


# --------------------------------------------------------------------------- #
# Default safe local fixtures (used by the CLI / convenience callers)
# --------------------------------------------------------------------------- #
def build_default_payload():
    """A minimal, SAFE local dry-run payload (no forbidden language)."""
    return {
        "payload_id": "cc-telegram-dryrun-fixture-0001",
        "platform": PLATFORM,
        "target_slot": TARGET_SLOT,
        "content_text": (
            "Capital Chronicle daily macro context summary for editorial review. "
            "This is a supervised dry-run preflight sample. No recommendations are "
            "provided and nothing here is investment advice."
        ),
        "content_class": "macro_context_note",
        "source_packet_id": None,
        "local_fixture_ref": "tests/fixtures/telegram/supervised_dry_run_payload.json",
        "no_financial_advice": True,
        "no_signal_language": True,
        "human_review_required": True,
        "public_postable": False,
        "live_send_enabled": False,
    }


def build_default_approval_record(payload=None):
    """A matching dry-run approval record for ``payload`` (default fixture)."""
    if payload is None:
        payload = build_default_payload()
    return {
        "approval_state": APPROVAL_STATE_DRY_RUN,
        "operator_approval_ref": "operator-dryrun-approval-0001",
        "approved_payload_hash": compute_payload_hash(payload),
        "not_financial_advice_acknowledged": True,
        "no_signal_language_acknowledged": True,
        "human_review_completed": True,
        "dry_run_only_acknowledged": True,
    }


def build_default_kill_switch_state():
    """Kill switch: live dispatch blocked, dry-run local-only allowed."""
    return {
        "kill_switch_live_dispatch": KS_LIVE_DISPATCH_BLOCK,
        "kill_switch_dry_run": KS_DRY_RUN_LOCAL_ONLY,
        "live_send_enabled": False,
        "network_allowed": False,
    }


def build_default_target_binding_state():
    """A redacted representation that 0174CL previously validated a channel target."""
    return {
        "binding_validated": True,
        "target_chat_type_class": "channel",
        "can_post_messages_class": "true",
        "future_supervised_publish_possible_after_remaining_gates": True,
        "live_recheck_requested": False,
    }


# --------------------------------------------------------------------------- #
# Main gate
# --------------------------------------------------------------------------- #
def run_supervised_post_dry_run_gate(
    *,
    dry_run=False,
    payload=None,
    approval_record=None,
    kill_switch_state=None,
    target_binding_state=None,
    _adapter=None,
):
    """Run the local supervised-post DRY-RUN preflight gate. Fail-closed by default.

    dry_run: must be explicitly True to run the local dry-run path. Otherwise the
             gate returns ``status = fail_closed`` and executes no adapter.
    _adapter: injectable pure mock adapter(payload) -> (mock_req, mock_resp) for
              tests. When None, the default pure mock adapter is used. NEVER
              performs network or a live Telegram call.
    """
    summary = _base_summary()

    # 0. Fail closed unless the explicit local dry-run is requested.
    if not dry_run:
        summary["status"] = "fail_closed"
        summary["blocked_reasons"] = ["dry_run_not_requested_fail_closed"]
        return _finalize(summary)

    # Use safe default local fixtures when not supplied.
    payload = build_default_payload() if payload is None else payload
    approval_record = (build_default_approval_record(payload)
                       if approval_record is None else approval_record)
    kill_switch_state = (build_default_kill_switch_state()
                         if kill_switch_state is None else kill_switch_state)
    target_binding_state = (build_default_target_binding_state()
                            if target_binding_state is None else target_binding_state)

    blocked = []

    # 1. Validate payload shape.
    shape_ok, shape_reasons = validate_payload_shape(payload)
    summary["payload_shape_valid"] = shape_ok
    blocked.extend(shape_reasons)

    # 2. Validate forbidden language / no-advice / no-signal.
    lang_ok, lang_reasons = check_forbidden_language(
        payload.get("content_text") if isinstance(payload, dict) else None)
    summary["forbidden_language_passed"] = lang_ok
    blocked.extend(lang_reasons)

    # 3 + 4. Canonicalize + compute deterministic payload hash (always lockable).
    payload_hash = compute_payload_hash(payload)
    summary["payload_hash_locked"] = bool(payload_hash)

    # 5. Approval record present + matches EXACT payload hash.
    summary["approval_record_present"] = isinstance(approval_record, dict) and bool(approval_record)
    approval_ok, approval_reasons = validate_approval_record(approval_record, payload_hash)
    summary["approval_hash_matches_payload"] = (
        isinstance(approval_record, dict)
        and approval_record.get("approved_payload_hash") == payload_hash
    )
    blocked.extend(approval_reasons)

    # 6. Target binding represented as previously validated (no live re-run).
    binding_ok, binding_reasons = validate_target_binding_state(target_binding_state)
    summary["target_binding_previously_validated"] = binding_ok
    blocked.extend(binding_reasons)

    # 7. Kill switch: live dispatch must stay active_block; dry-run path allowed.
    ks_ok, ks_reasons = validate_kill_switch_state(kill_switch_state)
    if isinstance(kill_switch_state, dict):
        summary["kill_switch_dry_run"] = kill_switch_state.get(
            "kill_switch_dry_run", KS_DRY_RUN_BLOCKED)
    blocked.extend(ks_reasons)
    # kill_switch_live_dispatch is ALWAYS active_block in the emitted summary.
    summary["kill_switch_live_dispatch"] = KS_LIVE_DISPATCH_BLOCK

    # If any pre-check failed, block BEFORE running the mock adapter.
    if blocked:
        summary["status"] = "blocked"
        summary["blocked_reasons"] = sorted(set(blocked))
        return _finalize(summary)

    # 8 + 9. Run the pure mock would-send adapter (no network, no mutation).
    adapter = _adapter if _adapter is not None else _default_mock_adapter
    mock_req, mock_resp = adapter(payload)
    summary["dry_run_adapter_executed"] = True
    mock_ok, mock_reasons = validate_mock_send_message(mock_req, mock_resp)
    summary["mock_send_message_shape_valid"] = mock_ok
    blocked.extend(mock_reasons)

    # 10. Emit redacted would-send audit event.
    audit = build_redacted_audit_event(payload_hash,
                                        approval_record.get("operator_approval_ref"))
    audit_ok, audit_reasons = validate_redacted_audit_event(audit)
    summary["redacted_audit_event_created"] = audit_ok
    blocked.extend(audit_reasons)

    if blocked:
        summary["status"] = "blocked"
        summary["blocked_reasons"] = sorted(set(blocked))
        return _finalize(summary)

    summary["status"] = "pass"
    summary["blocked_reasons"] = []
    return _finalize(summary)


def summary(**kwargs):
    """Convenience wrapper returning the redacted gate summary dict."""
    return run_supervised_post_dry_run_gate(**kwargs)


def main(argv=None):
    """CLI: print ONLY the redacted JSON summary.

    Fail-closed unless ``--telegram-supervised-post-dry-run`` is passed.
    There is NO live-network flag in this task.

    Usage:
      python -m live_contentops.telegram_supervised_post_dry_run_gate
      python -m live_contentops.telegram_supervised_post_dry_run_gate --telegram-supervised-post-dry-run
    """
    import sys

    args = list(sys.argv[1:] if argv is None else argv)
    dry_run = "--telegram-supervised-post-dry-run" in args
    result = run_supervised_post_dry_run_gate(dry_run=dry_run)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
