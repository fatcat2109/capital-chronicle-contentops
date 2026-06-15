"""Tests for the 0174CM Telegram supervised-post dry-run preflight gate.

These tests are NETWORK-FREE and CREDENTIAL-FREE. They assert:
  * Fail-closed by default (no dry_run flag).
  * The happy-path dry-run reaches status=pass with all controls satisfied.
  * Each control failure (shape, language, approval hash, kill switch, binding)
    blocks with a specific reason.
  * Hard-locked policy flags are NEVER true.
  * The deterministic hash contract is stable + order-independent.
  * The leakage guard scrubs a secret-like / @handle leak.
"""

import copy

import pytest

from live_contentops import telegram_supervised_post_dry_run_gate as gate


# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #
def _payload():
    return gate.build_default_payload()


def _approval(payload=None):
    return gate.build_default_approval_record(payload)


def _kill_switch():
    return gate.build_default_kill_switch_state()


def _binding():
    return gate.build_default_target_binding_state()


def _run(**overrides):
    kwargs = dict(
        dry_run=True,
        payload=_payload(),
        approval_record=None,
        kill_switch_state=_kill_switch(),
        target_binding_state=_binding(),
    )
    kwargs.update(overrides)
    # Keep approval matched to the (possibly overridden) payload unless explicitly set.
    if kwargs["approval_record"] is None:
        kwargs["approval_record"] = _approval(kwargs["payload"])
    return gate.run_supervised_post_dry_run_gate(**kwargs)


# --------------------------------------------------------------------------- #
# Fail-closed + happy path
# --------------------------------------------------------------------------- #
def test_fail_closed_when_dry_run_not_requested():
    s = gate.run_supervised_post_dry_run_gate(dry_run=False)
    assert s["status"] == "fail_closed"
    assert "dry_run_not_requested_fail_closed" in s["blocked_reasons"]
    assert s["dry_run_adapter_executed"] is False
    assert s["send_message_attempted"] is False


def test_happy_path_dry_run_passes():
    s = _run()
    assert s["status"] == "pass", s["blocked_reasons"]
    assert s["blocked_reasons"] == []
    assert s["payload_shape_valid"] is True
    assert s["forbidden_language_passed"] is True
    assert s["payload_hash_locked"] is True
    assert s["approval_record_present"] is True
    assert s["approval_hash_matches_payload"] is True
    assert s["target_binding_previously_validated"] is True
    assert s["dry_run_adapter_executed"] is True
    assert s["mock_send_message_shape_valid"] is True
    assert s["redacted_audit_event_created"] is True


def test_hard_locked_flags_never_true():
    for s in (gate.run_supervised_post_dry_run_gate(dry_run=False), _run()):
        assert s["posting_enabled"] is False
        assert s["live_send_enabled"] is False
        assert s["scheduler_enabled"] is False
        assert s["autonomous_replies_enabled"] is False
        assert s["live_publish_gate"] == "blocked"
        assert s["next_gate_required_before_live_post"] is True
        assert s["kill_switch_live_dispatch"] == gate.KS_LIVE_DISPATCH_BLOCK
        assert s["send_message_attempted"] is False
        assert s["live_network_attempted"] is False


# --------------------------------------------------------------------------- #
# Deterministic hash contract
# --------------------------------------------------------------------------- #
def test_hash_is_deterministic_and_order_independent():
    p1 = _payload()
    p2 = {k: p1[k] for k in reversed(list(p1.keys()))}
    p2["extra_unrelated_key"] = "ignored"
    assert gate.compute_payload_hash(p1) == gate.compute_payload_hash(p2)


def test_hash_changes_when_content_changes():
    p1 = _payload()
    p2 = _payload()
    p2["content_text"] = p2["content_text"] + " edited"
    assert gate.compute_payload_hash(p1) != gate.compute_payload_hash(p2)


def test_canonicalize_only_uses_canonical_fields():
    p = _payload()
    p["live_send_enabled"] = True  # not a canonical field
    canon = gate.canonicalize_payload(p)
    assert "live_send_enabled" not in canon


# --------------------------------------------------------------------------- #
# Payload shape failures
# --------------------------------------------------------------------------- #
def test_blocks_on_wrong_platform():
    p = _payload()
    p["platform"] = "x"
    s = _run(payload=p)
    assert s["status"] == "blocked"
    assert "platform_not_telegram" in s["blocked_reasons"]


def test_blocks_on_missing_content_text():
    p = _payload()
    p["content_text"] = "   "
    s = _run(payload=p)
    assert s["status"] == "blocked"
    assert "content_text_missing" in s["blocked_reasons"]


def test_blocks_when_safety_posture_not_set():
    p = _payload()
    p["no_financial_advice"] = False
    s = _run(payload=p)
    assert s["status"] == "blocked"
    assert "no_financial_advice_not_true" in s["blocked_reasons"]


def test_blocks_when_public_postable_true():
    p = _payload()
    p["public_postable"] = True
    s = _run(payload=p)
    assert s["status"] == "blocked"
    assert "public_postable_true_not_allowed_in_dry_run" in s["blocked_reasons"]


def test_blocks_when_live_send_enabled_true_in_payload():
    p = _payload()
    p["live_send_enabled"] = True
    s = _run(payload=p)
    assert s["status"] == "blocked"
    assert "live_send_enabled_true_not_allowed" in s["blocked_reasons"]


# --------------------------------------------------------------------------- #
# Forbidden language
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("term", ["buy", "sell", "short", "price target", "stop loss"])
def test_blocks_on_forbidden_language(term):
    p = _payload()
    p["content_text"] = f"Our view: {term} now for the move."
    # Re-approve to the edited payload so only the language check fails.
    s = _run(payload=p, approval_record=_approval(p))
    assert s["status"] == "blocked"
    assert any(r.startswith("forbidden_language:") for r in s["blocked_reasons"])


def test_forbidden_language_whole_word_not_substring():
    # "broker" is forbidden, but "brokerage" should NOT be matched as it is a
    # different whole word... actually substring guard: ensure 'household' style
    # words don't trip on 'hold'. 'stronghold' contains 'hold' as substring but
    # our regex is whole-word so it must NOT match.
    p = _payload()
    p["content_text"] = ("The institutional stronghold of liquidity remained "
                         "stable while households stayed cautious.")
    s = _run(payload=p, approval_record=_approval(p))
    assert s["forbidden_language_passed"] is True, s["blocked_reasons"]


# --------------------------------------------------------------------------- #
# Approval record
# --------------------------------------------------------------------------- #
def test_blocks_on_approval_hash_mismatch():
    p = _payload()
    bad = _approval(p)
    bad["approved_payload_hash"] = "deadbeef"
    s = _run(payload=p, approval_record=bad)
    assert s["status"] == "blocked"
    assert "approval_hash_mismatch" in s["blocked_reasons"]
    assert s["approval_hash_matches_payload"] is False


def test_blocks_on_revoked_approval():
    p = _payload()
    rec = _approval(p)
    rec["approval_state"] = gate.APPROVAL_STATE_REVOKED
    s = _run(payload=p, approval_record=rec)
    assert s["status"] == "blocked"
    assert "approval_revoked" in s["blocked_reasons"]


def test_live_later_approval_not_valid_for_dry_run_gate():
    p = _payload()
    rec = _approval(p)
    rec["approval_state"] = gate.APPROVAL_STATE_LIVE_LATER
    s = _run(payload=p, approval_record=rec)
    assert s["status"] == "blocked"
    assert "live_post_approval_not_valid_for_dry_run_gate" in s["blocked_reasons"]


def test_blocks_on_missing_ack():
    p = _payload()
    rec = _approval(p)
    rec["dry_run_only_acknowledged"] = False
    s = _run(payload=p, approval_record=rec)
    assert s["status"] == "blocked"
    assert "ack_missing:dry_run_only_acknowledged" in s["blocked_reasons"]


def test_blocks_on_missing_approval_record():
    s = _run(approval_record={})
    assert s["status"] == "blocked"
    assert s["approval_record_present"] is False


# --------------------------------------------------------------------------- #
# Kill switch
# --------------------------------------------------------------------------- #
def test_blocks_when_kill_switch_live_dispatch_not_block():
    ks = _kill_switch()
    ks["kill_switch_live_dispatch"] = "open"
    s = _run(kill_switch_state=ks)
    assert s["status"] == "blocked"
    assert "kill_switch_live_dispatch_not_active_block" in s["blocked_reasons"]
    # Emitted summary still forces active_block.
    assert s["kill_switch_live_dispatch"] == gate.KS_LIVE_DISPATCH_BLOCK


def test_blocks_when_kill_switch_allows_live_send():
    ks = _kill_switch()
    ks["live_send_enabled"] = True
    s = _run(kill_switch_state=ks)
    assert s["status"] == "blocked"
    assert "kill_switch_live_send_enabled_true" in s["blocked_reasons"]


def test_blocks_when_kill_switch_network_allowed():
    ks = _kill_switch()
    ks["network_allowed"] = True
    s = _run(kill_switch_state=ks)
    assert s["status"] == "blocked"
    assert "kill_switch_network_allowed_true" in s["blocked_reasons"]


# --------------------------------------------------------------------------- #
# Target binding
# --------------------------------------------------------------------------- #
def test_blocks_when_binding_not_validated():
    b = _binding()
    b["binding_validated"] = False
    s = _run(target_binding_state=b)
    assert s["status"] == "blocked"
    assert "target_binding_not_previously_validated" in s["blocked_reasons"]


def test_blocks_when_binding_not_channel():
    b = _binding()
    b["target_chat_type_class"] = "private"
    s = _run(target_binding_state=b)
    assert s["status"] == "blocked"
    assert "target_binding_not_channel" in s["blocked_reasons"]


def test_blocks_when_binding_live_recheck_requested():
    b = _binding()
    b["live_recheck_requested"] = True
    s = _run(target_binding_state=b)
    assert s["status"] == "blocked"
    assert "target_binding_live_recheck_requested_not_allowed" in s["blocked_reasons"]


# --------------------------------------------------------------------------- #
# Mock adapter + audit
# --------------------------------------------------------------------------- #
def test_mock_adapter_does_not_mutate_payload():
    p = _payload()
    before = copy.deepcopy(p)
    gate.run_supervised_post_dry_run_gate(
        dry_run=True, payload=p, approval_record=_approval(p),
        kill_switch_state=_kill_switch(), target_binding_state=_binding())
    assert p == before


def test_mock_request_carries_no_token_chat_id_or_url():
    req = gate.build_mock_send_message_request(_payload())
    assert req["token_present_in_request"] is False
    assert req["chat_id_present_in_request"] is False
    assert req["url_constructed"] is False
    assert req["network_accessed"] is False
    assert req["live_execution"] is False


def test_audit_event_has_no_forbidden_keys():
    audit = gate.build_redacted_audit_event("abc123", True)
    ok, reasons = gate.validate_redacted_audit_event(audit)
    assert ok, reasons
    for k in ("token", "chat_id", "channel_id", "channel_username",
              "bot_id", "bot_username", "raw_url", "raw_request", "raw_response"):
        assert k not in audit


def test_injected_adapter_claiming_delivery_blocks():
    def bad_adapter(payload):
        req = gate.build_mock_send_message_request(payload)
        resp = gate.build_mock_send_message_response()
        resp["message_delivered"] = True
        resp["live_execution"] = True
        return req, resp

    s = _run(_adapter=bad_adapter)
    assert s["status"] == "blocked"
    assert "mock_response_claims_delivery_or_live" in s["blocked_reasons"]


# --------------------------------------------------------------------------- #
# Leakage guard
# --------------------------------------------------------------------------- #
def test_redaction_guard_scrubs_secret_like_leak():
    # Smuggle a telegram-token-shaped string through a content field that the
    # default mock adapter echoes via "content_present" only -- so we instead
    # force a leak by injecting it through an adapter that puts it in the req.
    def leaky_adapter(payload):
        req = gate.build_mock_send_message_request(payload)
        req["leaked"] = "123456789:ABCdefGHIjklMNOpqrstUVWxyz0123456789"
        resp = gate.build_mock_send_message_response()
        return req, resp

    # The leak is in the mock req (not the summary), so validate the summary path
    # by directly finalizing a summary that contains a leak.
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


def test_clean_summary_passes_finalize():
    s = _run()
    # A clean pass summary must survive finalize unchanged.
    out = gate._finalize(copy.deepcopy(s))
    assert out["status"] == s["status"]
    assert out["blocked_reasons"] == s["blocked_reasons"]
