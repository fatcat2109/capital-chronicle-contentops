"""Tests for the 0174CN Telegram FIRST supervised live-post gate.

These tests are NETWORK-FREE and CREDENTIAL-FREE. The single live sendMessage is
NEVER exercised here: every test injects a fake ``_api_caller`` so no real network
call is made, OR asserts the fail-closed/blocked paths that never reach a caller.

They assert:
  * Fail-closed by default (missing either live flag => no caller invoked).
  * Both-flags + valid approval/binding/kill-switch => status=pass via injected
    caller that reports a redacted ok response.
  * Each control failure (flag, approval state/hash/ack, binding, kill switch,
    payload shape, forbidden language) blocks BEFORE any caller is invoked.
  * The default pilot payload is itself safe (shape + language) and hash-locked.
  * At most ONE live request is ever attempted (request budget == 1).
  * Hard-locked policy flags are NEVER true.
  * The redacted caller contract returns only booleans/classes (no id/date values).
  * The leakage guard scrubs a secret-like / @handle leak.
"""

import copy

import pytest

from live_contentops import telegram_first_supervised_live_post_gate as gate


# --------------------------------------------------------------------------- #
# Helpers / fakes
# --------------------------------------------------------------------------- #
def _payload():
    return gate.build_default_payload()


def _approval(payload=None):
    return gate.build_default_live_approval_record(payload)


def _binding():
    return gate.build_default_target_binding_state()


def _kill_switch():
    return gate.build_default_kill_switch_state()


class _CallTracker:
    """Records calls and returns a configurable redacted response."""

    def __init__(self, response=None):
        self.calls = []
        self.response = response if response is not None else {
            "ok": True, "transport_error": False,
            "message_id_present": True, "date_present": True,
            "chat_type": "channel",
        }

    def __call__(self, method, token, target, text, timeout_seconds):
        self.calls.append({
            "method": method, "token": token, "target": target,
            "text": text, "timeout_seconds": timeout_seconds,
        })
        return self.response


def _run(**overrides):
    """Run armed (both flags) with safe defaults + an injected caller by default."""
    tracker = overrides.pop("_tracker", None)
    if "_api_caller" not in overrides:
        tracker = tracker or _CallTracker()
        overrides["_api_caller"] = tracker
    kwargs = dict(
        live_post_flag=True,
        operator_go_flag=True,
        payload=_payload(),
        live_approval_record=None,
        target_binding_state=_binding(),
        dry_run_preflight_validated=True,
        kill_switch_state=_kill_switch(),
    )
    kwargs.update(overrides)
    if kwargs["live_approval_record"] is None:
        kwargs["live_approval_record"] = _approval(kwargs["payload"])
    result = gate.run_first_supervised_live_post_gate(**kwargs)
    return result, tracker


# --------------------------------------------------------------------------- #
# Fail-closed
# --------------------------------------------------------------------------- #
def test_fail_closed_when_no_flags():
    tracker = _CallTracker()
    s = gate.run_first_supervised_live_post_gate(_api_caller=tracker)
    assert s["status"] == "fail_closed"
    assert "live_post_flag_absent_fail_closed" in s["blocked_reasons"]
    assert "operator_go_flag_absent_fail_closed" in s["blocked_reasons"]
    assert s["send_message_attempted"] is False
    assert tracker.calls == []


def test_fail_closed_when_only_live_post_flag():
    tracker = _CallTracker()
    s = gate.run_first_supervised_live_post_gate(
        live_post_flag=True, operator_go_flag=False, _api_caller=tracker)
    assert s["status"] == "fail_closed"
    assert "operator_go_flag_absent_fail_closed" in s["blocked_reasons"]
    assert tracker.calls == []


def test_fail_closed_when_only_operator_go_flag():
    tracker = _CallTracker()
    s = gate.run_first_supervised_live_post_gate(
        live_post_flag=False, operator_go_flag=True, _api_caller=tracker)
    assert s["status"] == "fail_closed"
    assert "live_post_flag_absent_fail_closed" in s["blocked_reasons"]
    assert tracker.calls == []


# --------------------------------------------------------------------------- #
# Happy path (injected caller; no real network)
# --------------------------------------------------------------------------- #
def test_happy_path_sends_once_and_passes():
    s, tracker = _run()
    assert s["status"] == "pass", s["blocked_reasons"]
    assert s["blocked_reasons"] == []
    assert s["payload_shape_valid"] is True
    assert s["forbidden_language_passed"] is True
    assert s["payload_hash_locked"] is True
    assert s["live_approval_record_present"] is True
    assert s["live_approval_hash_matches_payload"] is True
    assert s["target_binding_previously_validated"] is True
    assert s["dry_run_preflight_previously_validated"] is True
    assert s["send_message_attempted"] is True
    assert s["message_sent"] is True
    assert s["telegram_response_ok_class"] == gate.RESP_OK_TRUE
    assert s["message_id_present"] is True
    assert s["redacted_audit_event_created"] is True
    # Exactly one live request.
    assert s["request_count"] == 1
    assert len(tracker.calls) == 1
    assert tracker.calls[0]["method"] == gate.ALLOWED_METHOD


def test_request_budget_is_one():
    assert gate.REQUEST_BUDGET == 1


def test_default_pilot_payload_is_safe():
    p = _payload()
    shape_ok, shape_reasons = gate.validate_payload_shape(p)
    assert shape_ok, shape_reasons
    lang_ok, lang_reasons = gate.check_forbidden_language(p["content_text"])
    assert lang_ok, lang_reasons


def test_hard_locked_flags_never_true():
    s, _ = _run()
    s_closed = gate.run_first_supervised_live_post_gate()
    for summ in (s, s_closed):
        assert summ["posting_enabled"] is False
        assert summ["live_send_enabled"] is False
        assert summ["scheduler_enabled"] is False
        assert summ["autonomous_replies_enabled"] is False
        assert summ["webhook_enabled"] is False
        assert summ["get_updates_enabled"] is False
        assert summ["metrics_fetch_enabled"] is False
        assert summ["live_publish_gate"] == "blocked_after_one_time_pilot"
        assert summ["next_gate_required_before_next_live_post"] is True


# --------------------------------------------------------------------------- #
# Caller is never invoked when a pre-check fails
# --------------------------------------------------------------------------- #
def test_blocks_on_wrong_platform_without_calling():
    p = _payload()
    p["platform"] = "x"
    s, tracker = _run(payload=p)
    assert s["status"] == "blocked"
    assert "platform_not_telegram" in s["blocked_reasons"]
    assert tracker.calls == []
    assert s["send_message_attempted"] is False


def test_blocks_on_forbidden_language_without_calling():
    p = _payload()
    p["content_text"] = "Our view: buy now for the move."
    s, tracker = _run(payload=p, live_approval_record=_approval(p))
    assert s["status"] == "blocked"
    assert any(r.startswith("forbidden_language:") for r in s["blocked_reasons"])
    assert tracker.calls == []


def test_blocks_on_text_over_telegram_limit():
    p = _payload()
    p["content_text"] = "a" * (gate.TELEGRAM_TEXT_LIMIT + 1)
    s, tracker = _run(payload=p, live_approval_record=_approval(p))
    assert s["status"] == "blocked"
    assert "content_text_exceeds_telegram_limit" in s["blocked_reasons"]
    assert tracker.calls == []


# --------------------------------------------------------------------------- #
# Approval record
# --------------------------------------------------------------------------- #
def test_blocks_on_approval_hash_mismatch():
    p = _payload()
    bad = _approval(p)
    bad["approved_payload_hash"] = "deadbeef"
    s, tracker = _run(payload=p, live_approval_record=bad)
    assert s["status"] == "blocked"
    assert "live_approval_hash_mismatch" in s["blocked_reasons"]
    assert s["live_approval_hash_matches_payload"] is False
    assert tracker.calls == []


def test_dry_run_approval_state_not_accepted():
    p = _payload()
    rec = _approval(p)
    # Reuse the 0174CM dry-run approval state; it must NOT authorize a live post.
    rec["approval_state"] = "operator_approved_for_dry_run"
    s, tracker = _run(payload=p, live_approval_record=rec)
    assert s["status"] == "blocked"
    assert any(r.startswith("approval_state_not_first_live_post")
               for r in s["blocked_reasons"])
    assert tracker.calls == []


def test_blocks_on_missing_ack():
    p = _payload()
    rec = _approval(p)
    rec["one_time_only"] = False
    s, tracker = _run(payload=p, live_approval_record=rec)
    assert s["status"] == "blocked"
    assert "ack_missing:one_time_only" in s["blocked_reasons"]
    assert tracker.calls == []


def test_blocks_on_missing_operator_go_ref():
    p = _payload()
    rec = _approval(p)
    rec["operator_go_ref"] = ""
    s, tracker = _run(payload=p, live_approval_record=rec)
    assert s["status"] == "blocked"
    assert "operator_go_ref_missing" in s["blocked_reasons"]
    assert tracker.calls == []


# --------------------------------------------------------------------------- #
# Target binding + dry-run preflight representation
# --------------------------------------------------------------------------- #
def test_blocks_when_binding_not_channel():
    b = _binding()
    b["target_chat_type_class"] = "private"
    s, tracker = _run(target_binding_state=b)
    assert s["status"] == "blocked"
    assert "target_binding_not_channel" in s["blocked_reasons"]
    assert tracker.calls == []


def test_blocks_when_dry_run_preflight_not_validated():
    s, tracker = _run(dry_run_preflight_validated=False)
    assert s["status"] == "blocked"
    assert "dry_run_0174cm_preflight_not_validated" in s["blocked_reasons"]
    assert tracker.calls == []


# --------------------------------------------------------------------------- #
# Kill switch
# --------------------------------------------------------------------------- #
def test_blocks_when_global_dispatch_not_blocked():
    ks = _kill_switch()
    ks["global_live_dispatch"] = "open"
    s, tracker = _run(kill_switch_state=ks)
    assert s["status"] == "blocked"
    assert "global_live_dispatch_not_blocked" in s["blocked_reasons"]
    assert tracker.calls == []


def test_blocks_when_override_not_0174cn_scoped():
    ks = _kill_switch()
    ks["one_time_live_override"] = "something_else"
    s, tracker = _run(kill_switch_state=ks)
    assert s["status"] == "blocked"
    assert "one_time_live_override_not_0174cn_scoped" in s["blocked_reasons"]
    assert s["one_time_live_override_class"] == gate.OVERRIDE_INVALID
    assert tracker.calls == []


def test_blocks_when_scheduler_enabled_in_kill_switch():
    ks = _kill_switch()
    ks["scheduler_enabled"] = True
    s, tracker = _run(kill_switch_state=ks)
    assert s["status"] == "blocked"
    assert "scheduler_enabled_true" in s["blocked_reasons"]
    assert tracker.calls == []


# --------------------------------------------------------------------------- #
# Response handling (injected caller)
# --------------------------------------------------------------------------- #
def test_transport_error_blocks():
    resp = {"ok": False, "transport_error": True,
            "message_id_present": False, "date_present": False, "chat_type": None}
    s, tracker = _run(_api_caller=_CallTracker(resp))
    assert s["status"] == "blocked"
    assert s["telegram_response_ok_class"] == gate.RESP_TRANSPORT_ERROR
    assert "send_transport_error_redacted" in s["blocked_reasons"]
    assert s["message_sent"] is False
    # The single attempt was still made.
    assert s["send_message_attempted"] is True


def test_response_not_ok_blocks():
    resp = {"ok": False, "transport_error": False,
            "message_id_present": False, "date_present": False, "chat_type": None}
    s, tracker = _run(_api_caller=_CallTracker(resp))
    assert s["status"] == "blocked"
    assert s["telegram_response_ok_class"] == gate.RESP_OK_FALSE
    assert "telegram_response_not_ok_redacted" in s["blocked_reasons"]
    assert s["message_sent"] is False


# --------------------------------------------------------------------------- #
# Redacted audit event + leakage guard
# --------------------------------------------------------------------------- #
def test_audit_event_has_no_forbidden_keys():
    audit = gate.build_redacted_audit_event("abc123", gate.RESP_OK_TRUE, True)
    for k in ("token", "chat_id", "channel_id", "channel_username",
              "bot_id", "bot_username", "raw_url", "raw_request", "raw_response",
              "message_id", "date"):
        assert k not in audit
    assert audit["send_message_attempted"] is True
    assert audit["message_id_present"] is True


def test_redaction_guard_scrubs_secret_like_leak():
    s = gate._base_summary()
    s["blocked_reasons"] = ["123456789:ABCdefGHIjklMNOpqrstUVWxyz0123456789"]
    out = gate._finalize(s)
    assert out["status"] == "blocked"
    assert out["blocked_reasons"] == ["redaction_guard_triggered"]


def test_redaction_guard_scrubs_handle_leak():
    s = gate._base_summary()
    s["blocked_reasons"] = ["leaked_@capitalchronicle_channel"]
    out = gate._finalize(s)
    assert out["status"] == "blocked"
    assert out["blocked_reasons"] == ["redaction_guard_triggered"]


def test_clean_pass_summary_survives_finalize():
    s, _ = _run()
    out = gate._finalize(copy.deepcopy(s))
    assert out["status"] == s["status"]
    assert out["blocked_reasons"] == s["blocked_reasons"]


# --------------------------------------------------------------------------- #
# Default caller defense-in-depth (no network: forbidden method short-circuits)
# --------------------------------------------------------------------------- #
def test_default_caller_refuses_forbidden_method_without_network():
    # Passing a forbidden method must return a transport_error dict and never
    # construct/contact a URL. getMe is forbidden in this gate.
    out = gate._default_api_caller("getMe", "tok", "target", "text", 1)
    assert out["ok"] is False
    assert out["transport_error"] is True
    assert out["message_id_present"] is False


def test_hash_matches_dry_run_contract():
    # The 0174CN hash MUST equal the 0174CM canonical hash for the same payload.
    from live_contentops import telegram_supervised_post_dry_run_gate as dryrun
    p = _payload()
    assert gate.compute_payload_hash(p) == dryrun.compute_payload_hash(p)
