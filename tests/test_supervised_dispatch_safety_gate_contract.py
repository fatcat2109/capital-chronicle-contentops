"""Tests for the 0174TM/TN/TO kill switch + rate policy + dispatch gate contract.

Deterministic, stdlib-only, offline. These tests assert the final LOCAL safety
layer on top of the accepted chain:

  * 0174TM kill switch -- fail-closed by default; only an explicit
    ``kill_switch_clear`` state with a fresh policy snapshot is clear.
  * 0174TN rate/spend/retry policy -- forbids retries, budgets, queues,
    schedulers, and more-than-one request; clear only for a one-request gate.
  * 0174TO one-request supervised dispatch gate -- re-proves the full deep
    cross-binding and produces a LOCAL DispatchAuthorizationCandidate that is
    NEVER live-executable and NEVER a dispatch. A registry suppresses duplicate
    request ids and idempotency fingerprints.

All upstream objects are built through the GENUINE authority chain
(0174ED -> 0174EE -> 0174TG/TH/TI -> 0174TJ/TK/TL), never via hand-rolled
dicts, so the bindings are real.
"""

import copy

from live_contentops import approval_ledger_payload_hash_contract as approval
from live_contentops import dispatch_outbox_idempotency_contract as outbox
from live_contentops import remote_operator_inbox_intent_review_contract as review
from live_contentops import editorial_preview_supervised_dry_run_contract as ep
from live_contentops import supervised_dispatch_safety_gate_contract as sg


# --------------------------------------------------------------------------- #
# Fixtures / helpers -- the genuine 0174ED -> ... -> 0174TL chain
# --------------------------------------------------------------------------- #
def _payload():
    return approval.canonical_payload_dict(
        platform="telegram",
        payload_text="One CPI print is not a regime shift.",
        destination_binding_id="a" * 64,
        credential_handle_id="b" * 64,
        media_manifest_hash="c" * 64,
        visibility_class="public_default",
        content_lane="grounded_news_context",
        policy_snapshot_id="policy_v1",
        platform_adapter_version="telegram_adapter_v1",
        platform_formatting="default",
        thread_split=None,
        disclosure_class="none",
    )


def _real_outbox_entry():
    payload = _payload()
    ledger = approval.ApprovalLedger()
    ch = approval.create_approval_challenge(
        payload, challenge_id="chal-ee-1", operator_id="operator_jim",
        created_at_epoch=1000, expires_at_epoch=2000)
    entry = approval.record_approval(
        ch, payload, ledger_entry_id="led-ee-1", approved_at_epoch=1500,
        operator_id="operator_jim")
    ledger.append_approval(entry)
    vres = approval.validate_approval_for_current_payload(
        ledger, entry, payload, now_epoch=1600)
    pre = outbox.run_dispatch_preflight(
        payload, entry, vres,
        dispatch_intent_class=outbox.INTENT_SUPERVISED_SINGLE,
        gate_snapshot_class=outbox.GATE_ALLOWS_LOCAL_OUTBOX,
        gate_snapshot_id="gate_v1", operator_id="operator_jim")
    assert pre["status"] == outbox.OutboxStatus.PASS
    return outbox.build_outbox_entry(pre, "outbox_entry_0001",
                                     created_at_epoch=1700)


def _real_review_approved(entry):
    challenge = review.create_review_challenge(
        entry, challenge_id="review-chal-1", operator_id="operator_jim",
        created_at_epoch=1700, expires_at_epoch=9999)
    inbound = {
        "source_surface_class": review.SOURCE_SURFACE_CLASS,
        "inbound_message_id": "inbound_msg_approve",
        "received_at_epoch": 1_700_000_100,
        "operator_id": "operator_jim",
        "operator_identity_class": review.IDENTITY_VERIFIED,
        "chat_binding_id": "chat_binding_alpha",
        "message_text_redacted": review.DEFAULT_APPROVAL_PHRASE,
        "reply_to_challenge_id": "review-chal-1",
    }
    norm = review.normalize_inbound_envelope(inbound)
    assert norm["status"] == review.InboxStatus.PASS
    intent = review.parse_operator_intent(
        norm["record"], required_approval_phrase=review.DEFAULT_APPROVAL_PHRASE)
    vres = review.validate_review_challenge_response(
        challenge, intent, entry, now_epoch=1800,
        responding_operator_id="operator_jim")
    assert vres["review_outcome_class"] == review.REVIEW_APPROVED_NOT_DISPATCHED
    return vres


def _surface_bodies():
    return {
        ep.SURFACE_TELEGRAM_CHANNEL: "Neutral context summary for telegram.",
        ep.SURFACE_X_POST: "Grounded recap of the CPI print for X.",
        ep.SURFACE_LINKEDIN_POST: "Measured macro context note for LinkedIn.",
        ep.SURFACE_MANUAL_PUBLISH_PACKET: "Manual publish packet neutral summary.",
    }


def _full_dry_run():
    """Return (entry, review_result, editorial_record, preview_set, dry_run)."""
    entry = _real_outbox_entry()
    rr = _real_review_approved(entry)
    er = ep.run_editorial_agent(
        rr, entry, editorial_id="editorial_0001",
        editor_operator_id="operator_jim", decided_at_epoch=1900,
        editorial_summary_redacted="Grounded recap of the CPI print.",
        content_lane="grounded_news_context")
    ps = ep.build_platform_preview_set(
        er, entry, preview_set_id="preview_set_0001", built_at_epoch=2000,
        surface_bodies_redacted=_surface_bodies())
    dr = ep.run_supervised_dry_run(
        rr, entry, er, ps, dry_run_id="dry_run_0001",
        operator_id="operator_jim", run_at_epoch=2100)
    assert dr["status"] == ep.Status.PASS
    return entry, rr, er, ps, dr


def _clear_kill_switch(dr):
    return sg.evaluate_kill_switch(
        dr, operator_id="operator_jim", policy_snapshot_id="ks_policy_v1",
        kill_switch_state=sg.KILL_SWITCH_CLEAR,
        current_policy_snapshot_id="ks_policy_v1")


def _clear_rate_policy():
    snap = sg.build_rate_spend_retry_policy_snapshot(
        policy_snapshot_id="rate_policy_v1")
    return sg.evaluate_rate_spend_retry_policy(snap, operator_id="operator_jim")


def _bundle(dr, ks, rp, entry, *, request_id="supervised_request_0001"):
    return sg.build_one_request_dispatch_gate_input_bundle(
        dr, ks, rp,
        operator_id="operator_jim",
        supervised_request_id=request_id,
        outbox_entry_id=entry["outbox_entry_id"],
        payload_hash_short=entry["payload_hash_short"],
        payload_hash=entry["payload_hash"],
        idempotency_key_short=entry["idempotency_key_short"],
        idempotency_key=entry["idempotency_key"],
        approval_ledger_entry_id=entry["approval_ledger_entry_id"],
        review_challenge_id="review-chal-1",
        editorial_id="editorial_0001",
        preview_set_id="preview_set_0001")


# --------------------------------------------------------------------------- #
# 1. Valid full chain
# --------------------------------------------------------------------------- #
def test_valid_full_chain_creates_candidate_not_dispatched():
    entry, rr, er, ps, dr = _full_dry_run()
    ks = _clear_kill_switch(dr)
    rp = _clear_rate_policy()
    assert ks["status"] == sg.Status.PASS
    assert ks["kill_switch_clear"] is True
    assert rp["status"] == sg.Status.PASS
    assert rp["rate_spend_retry_policy_clear"] is True
    gate = sg.run_one_request_dispatch_gate(_bundle(dr, ks, rp, entry))
    assert gate["status"] == sg.Status.PASS
    assert gate["dispatch_gate_outcome_class"] == sg.GATE_CANDIDATE_CREATED
    assert gate["candidate_created_not_dispatched"] is True
    cand = gate["dispatch_authorization_candidate"]
    assert cand is not None
    assert cand["max_requests_authorized"] == 1
    assert cand["valid_for_live_execution"] is False
    assert cand["requires_operator_live_gate"] is True
    assert gate["dispatch_gate_checksum"]


# --------------------------------------------------------------------------- #
# 2-10. Kill switch behaviors
# --------------------------------------------------------------------------- #
def test_kill_switch_defaults_fail_closed_if_state_missing():
    _, _, _, _, dr = _full_dry_run()
    ks = sg.evaluate_kill_switch(
        dr, operator_id="operator_jim", policy_snapshot_id="ks_policy_v1",
        kill_switch_state=None)
    assert ks["status"] == sg.Status.BLOCKED
    assert ks["kill_switch_clear"] is False
    assert sg.BLOCK_KILL_SWITCH_STATE_MISSING in ks["blocked_reasons"]


def test_kill_switch_global_dispatch_disabled_blocks():
    _, _, _, _, dr = _full_dry_run()
    ks = sg.evaluate_kill_switch(
        dr, operator_id="operator_jim", policy_snapshot_id="ks_policy_v1",
        kill_switch_state=sg.KILL_SWITCH_GLOBAL_DISABLED)
    assert ks["status"] == sg.Status.BLOCKED
    assert (sg.BLOCK_KILL_SWITCH_DISABLED + ":" + sg.KILL_SWITCH_GLOBAL_DISABLED
            ) in ks["blocked_reasons"]


def test_kill_switch_platform_dispatch_disabled_blocks():
    _, _, _, _, dr = _full_dry_run()
    ks = sg.evaluate_kill_switch(
        dr, operator_id="operator_jim", policy_snapshot_id="ks_policy_v1",
        kill_switch_state=sg.KILL_SWITCH_PLATFORM_DISABLED)
    assert ks["status"] == sg.Status.BLOCKED
    assert (sg.BLOCK_KILL_SWITCH_DISABLED + ":"
            + sg.KILL_SWITCH_PLATFORM_DISABLED) in ks["blocked_reasons"]


def test_kill_switch_credential_handle_disabled_blocks():
    _, _, _, _, dr = _full_dry_run()
    ks = sg.evaluate_kill_switch(
        dr, operator_id="operator_jim", policy_snapshot_id="ks_policy_v1",
        kill_switch_state=sg.KILL_SWITCH_CREDENTIAL_DISABLED)
    assert ks["status"] == sg.Status.BLOCKED
    assert (sg.BLOCK_KILL_SWITCH_DISABLED + ":"
            + sg.KILL_SWITCH_CREDENTIAL_DISABLED) in ks["blocked_reasons"]


def test_kill_switch_destination_binding_disabled_blocks():
    _, _, _, _, dr = _full_dry_run()
    ks = sg.evaluate_kill_switch(
        dr, operator_id="operator_jim", policy_snapshot_id="ks_policy_v1",
        kill_switch_state=sg.KILL_SWITCH_DESTINATION_DISABLED)
    assert ks["status"] == sg.Status.BLOCKED
    assert (sg.BLOCK_KILL_SWITCH_DISABLED + ":"
            + sg.KILL_SWITCH_DESTINATION_DISABLED) in ks["blocked_reasons"]


def test_kill_switch_operator_dispatch_disabled_blocks():
    _, _, _, _, dr = _full_dry_run()
    ks = sg.evaluate_kill_switch(
        dr, operator_id="operator_jim", policy_snapshot_id="ks_policy_v1",
        kill_switch_state=sg.KILL_SWITCH_OPERATOR_DISABLED)
    assert ks["status"] == sg.Status.BLOCKED
    assert (sg.BLOCK_KILL_SWITCH_DISABLED + ":"
            + sg.KILL_SWITCH_OPERATOR_DISABLED) in ks["blocked_reasons"]


def test_kill_switch_dispatch_window_closed_blocks():
    _, _, _, _, dr = _full_dry_run()
    ks = sg.evaluate_kill_switch(
        dr, operator_id="operator_jim", policy_snapshot_id="ks_policy_v1",
        kill_switch_state=sg.KILL_SWITCH_WINDOW_CLOSED)
    assert ks["status"] == sg.Status.BLOCKED
    assert (sg.BLOCK_KILL_SWITCH_DISABLED + ":" + sg.KILL_SWITCH_WINDOW_CLOSED
            ) in ks["blocked_reasons"]


def test_kill_switch_unknown_state_blocks():
    _, _, _, _, dr = _full_dry_run()
    ks = sg.evaluate_kill_switch(
        dr, operator_id="operator_jim", policy_snapshot_id="ks_policy_v1",
        kill_switch_state="some_unknown_state")
    assert ks["status"] == sg.Status.BLOCKED
    assert sg.BLOCK_KILL_SWITCH_STATE_UNKNOWN in ks["blocked_reasons"]


def test_kill_switch_stale_policy_snapshot_blocks():
    _, _, _, _, dr = _full_dry_run()
    ks = sg.evaluate_kill_switch(
        dr, operator_id="operator_jim", policy_snapshot_id="ks_policy_OLD",
        kill_switch_state=sg.KILL_SWITCH_CLEAR,
        current_policy_snapshot_id="ks_policy_v1")
    assert ks["status"] == sg.Status.BLOCKED
    assert sg.BLOCK_KILL_SWITCH_POLICY_SNAPSHOT_STALE in ks["blocked_reasons"]


def test_kill_switch_missing_policy_snapshot_blocks():
    _, _, _, _, dr = _full_dry_run()
    ks = sg.evaluate_kill_switch(
        dr, operator_id="operator_jim", policy_snapshot_id=None,
        kill_switch_state=sg.KILL_SWITCH_CLEAR)
    assert ks["status"] == sg.Status.BLOCKED
    assert sg.BLOCK_KILL_SWITCH_POLICY_SNAPSHOT_MISSING in ks["blocked_reasons"]


# --------------------------------------------------------------------------- #
# 11-15. Rate / spend / retry policy behaviors
# --------------------------------------------------------------------------- #
def test_rate_policy_missing_blocks():
    rp = sg.evaluate_rate_spend_retry_policy(None, operator_id="operator_jim")
    assert rp["status"] == sg.Status.BLOCKED
    assert sg.BLOCK_RATE_POLICY_MISSING in rp["blocked_reasons"]


def test_rate_policy_auto_retry_allowed_blocks():
    snap = sg.build_rate_spend_retry_policy_snapshot(
        policy_snapshot_id="rate_policy_v1")
    snap["auto_retry_allowed"] = True
    rp = sg.evaluate_rate_spend_retry_policy(snap, operator_id="operator_jim")
    assert rp["status"] == sg.Status.BLOCKED
    assert sg.BLOCK_RATE_AUTO_RETRY_ALLOWED in rp["blocked_reasons"]


def test_rate_policy_max_requests_gt_one_blocks():
    snap = sg.build_rate_spend_retry_policy_snapshot(
        policy_snapshot_id="rate_policy_v1")
    snap["max_requests_per_gate"] = 5
    rp = sg.evaluate_rate_spend_retry_policy(snap, operator_id="operator_jim")
    assert rp["status"] == sg.Status.BLOCKED
    assert sg.BLOCK_RATE_MAX_REQUESTS_GT_ONE in rp["blocked_reasons"]


def test_rate_policy_scheduler_queue_backoff_enabled_blocks():
    for field, reason in (
            ("scheduler_enabled", sg.BLOCK_RATE_SCHEDULER_ENABLED),
            ("queue_worker_enabled", sg.BLOCK_RATE_QUEUE_WORKER_ENABLED),
            ("backoff_loop_enabled", sg.BLOCK_RATE_BACKOFF_LOOP_ENABLED),
            ("scheduled_retry_enabled", sg.BLOCK_RATE_SCHEDULED_RETRY_ENABLED)):
        snap = sg.build_rate_spend_retry_policy_snapshot(
            policy_snapshot_id="rate_policy_v1")
        snap[field] = True
        rp = sg.evaluate_rate_spend_retry_policy(
            snap, operator_id="operator_jim")
        assert rp["status"] == sg.Status.BLOCKED, field
        assert reason in rp["blocked_reasons"], field


def test_rate_policy_provider_budget_hydrated_blocks():
    snap = sg.build_rate_spend_retry_policy_snapshot(
        policy_snapshot_id="rate_policy_v1")
    snap["provider_budget_hydrated"] = True
    rp = sg.evaluate_rate_spend_retry_policy(snap, operator_id="operator_jim")
    assert rp["status"] == sg.Status.BLOCKED
    assert sg.BLOCK_RATE_PROVIDER_BUDGET_HYDRATED in rp["blocked_reasons"]


def test_rate_policy_non_symbolic_spend_limit_blocks():
    snap = sg.build_rate_spend_retry_policy_snapshot(
        policy_snapshot_id="rate_policy_v1")
    snap["spend_limit_class"] = "usd_500_hydrated"
    rp = sg.evaluate_rate_spend_retry_policy(snap, operator_id="operator_jim")
    assert rp["status"] == sg.Status.BLOCKED
    assert sg.BLOCK_RATE_SPEND_NOT_SYMBOLIC in rp["blocked_reasons"]


def test_rate_policy_reapproval_not_required_blocks():
    snap = sg.build_rate_spend_retry_policy_snapshot(
        policy_snapshot_id="rate_policy_v1")
    snap["operator_reapproval_required_after_failure"] = False
    rp = sg.evaluate_rate_spend_retry_policy(snap, operator_id="operator_jim")
    assert rp["status"] == sg.Status.BLOCKED
    assert sg.BLOCK_RATE_REAPPROVAL_NOT_REQUIRED in rp["blocked_reasons"]


# --------------------------------------------------------------------------- #
# 16-25. Gate cross-binding behaviors
# --------------------------------------------------------------------------- #
def test_gate_dry_run_not_complete_blocks():
    entry, rr, er, ps, dr = _full_dry_run()
    not_complete = copy.deepcopy(dr)
    not_complete["dry_run_outcome_class"] = ep.DRY_RUN_NOT_COMPLETE
    not_complete["dry_run_complete_not_dispatched"] = False
    not_complete["status"] = ep.Status.BLOCKED
    ks = _clear_kill_switch(dr)
    rp = _clear_rate_policy()
    gate = sg.run_one_request_dispatch_gate(
        _bundle(not_complete, ks, rp, entry))
    assert gate["status"] == sg.Status.BLOCKED
    assert sg.BLOCK_GATE_DRY_RUN_NOT_COMPLETE in gate["blocked_reasons"]


def test_gate_dry_run_live_flag_blocks():
    entry, rr, er, ps, dr = _full_dry_run()
    live = copy.deepcopy(dr)
    live["platform_api_called"] = True
    ks = _clear_kill_switch(dr)
    rp = _clear_rate_policy()
    gate = sg.run_one_request_dispatch_gate(_bundle(live, ks, rp, entry))
    assert gate["status"] == sg.Status.BLOCKED
    assert sg.BLOCK_GATE_DRY_RUN_LIVE_FLAG_SET in gate["blocked_reasons"]


def test_gate_wrong_operator_id_blocks():
    entry, rr, er, ps, dr = _full_dry_run()
    ks = _clear_kill_switch(dr)
    rp = _clear_rate_policy()
    bundle = _bundle(dr, ks, rp, entry)
    bundle["operator_id"] = "operator_eve"
    gate = sg.run_one_request_dispatch_gate(bundle)
    assert gate["status"] == sg.Status.BLOCKED
    assert sg.BLOCK_GATE_OPERATOR_ID_MISMATCH in gate["blocked_reasons"]


def test_gate_wrong_outbox_entry_id_blocks():
    entry, rr, er, ps, dr = _full_dry_run()
    ks = _clear_kill_switch(dr)
    rp = _clear_rate_policy()
    bundle = _bundle(dr, ks, rp, entry)
    bundle["outbox_entry_id"] = "outbox_entry_9999"
    gate = sg.run_one_request_dispatch_gate(bundle)
    assert gate["status"] == sg.Status.BLOCKED
    assert sg.BLOCK_GATE_OUTBOX_ENTRY_MISMATCH in gate["blocked_reasons"]


def test_gate_wrong_payload_hash_short_blocks():
    entry, rr, er, ps, dr = _full_dry_run()
    ks = _clear_kill_switch(dr)
    rp = _clear_rate_policy()
    bundle = _bundle(dr, ks, rp, entry)
    bundle["payload_hash_short"] = "deadbeefdeadbeef"
    bundle["payload_hash"] = None
    gate = sg.run_one_request_dispatch_gate(bundle)
    assert gate["status"] == sg.Status.BLOCKED
    assert sg.BLOCK_GATE_PAYLOAD_HASH_MISMATCH in gate["blocked_reasons"]


def test_gate_wrong_approval_ledger_entry_id_blocks():
    entry, rr, er, ps, dr = _full_dry_run()
    ks = _clear_kill_switch(dr)
    rp = _clear_rate_policy()
    bundle = _bundle(dr, ks, rp, entry)
    bundle["approval_ledger_entry_id"] = "led_9999"
    gate = sg.run_one_request_dispatch_gate(bundle)
    assert gate["status"] == sg.Status.BLOCKED
    assert sg.BLOCK_GATE_LEDGER_ENTRY_MISMATCH in gate["blocked_reasons"]


def test_gate_wrong_review_challenge_id_blocks():
    entry, rr, er, ps, dr = _full_dry_run()
    ks = _clear_kill_switch(dr)
    rp = _clear_rate_policy()
    bundle = _bundle(dr, ks, rp, entry)
    bundle["review_challenge_id"] = "rc_9999"
    gate = sg.run_one_request_dispatch_gate(bundle)
    assert gate["status"] == sg.Status.BLOCKED
    assert sg.BLOCK_GATE_CHALLENGE_ID_MISMATCH in gate["blocked_reasons"]


def test_gate_wrong_editorial_id_blocks():
    entry, rr, er, ps, dr = _full_dry_run()
    ks = _clear_kill_switch(dr)
    rp = _clear_rate_policy()
    bundle = _bundle(dr, ks, rp, entry)
    bundle["editorial_id"] = "editorial_9999"
    gate = sg.run_one_request_dispatch_gate(bundle)
    assert gate["status"] == sg.Status.BLOCKED
    assert sg.BLOCK_GATE_EDITORIAL_ID_MISMATCH in gate["blocked_reasons"]


def test_gate_wrong_preview_set_id_blocks():
    entry, rr, er, ps, dr = _full_dry_run()
    ks = _clear_kill_switch(dr)
    rp = _clear_rate_policy()
    bundle = _bundle(dr, ks, rp, entry)
    bundle["preview_set_id"] = "preview_set_9999"
    gate = sg.run_one_request_dispatch_gate(bundle)
    assert gate["status"] == sg.Status.BLOCKED
    assert sg.BLOCK_GATE_PREVIEW_SET_ID_MISMATCH in gate["blocked_reasons"]


def test_gate_missing_supervised_request_id_blocks():
    entry, rr, er, ps, dr = _full_dry_run()
    ks = _clear_kill_switch(dr)
    rp = _clear_rate_policy()
    bundle = _bundle(dr, ks, rp, entry, request_id=None)
    gate = sg.run_one_request_dispatch_gate(bundle)
    assert gate["status"] == sg.Status.BLOCKED
    assert sg.BLOCK_GATE_REQUEST_ID_MISSING in gate["blocked_reasons"]


def test_gate_kill_switch_not_clear_blocks():
    entry, rr, er, ps, dr = _full_dry_run()
    ks = sg.evaluate_kill_switch(
        dr, operator_id="operator_jim", policy_snapshot_id="ks_policy_v1",
        kill_switch_state=sg.KILL_SWITCH_GLOBAL_DISABLED)
    rp = _clear_rate_policy()
    gate = sg.run_one_request_dispatch_gate(_bundle(dr, ks, rp, entry))
    assert gate["status"] == sg.Status.BLOCKED
    assert sg.BLOCK_GATE_KILL_SWITCH_NOT_CLEAR in gate["blocked_reasons"]


def test_gate_rate_policy_not_clear_blocks():
    entry, rr, er, ps, dr = _full_dry_run()
    ks = _clear_kill_switch(dr)
    snap = sg.build_rate_spend_retry_policy_snapshot(
        policy_snapshot_id="rate_policy_v1")
    snap["auto_retry_allowed"] = True
    rp = sg.evaluate_rate_spend_retry_policy(snap, operator_id="operator_jim")
    gate = sg.run_one_request_dispatch_gate(_bundle(dr, ks, rp, entry))
    assert gate["status"] == sg.Status.BLOCKED
    assert sg.BLOCK_GATE_RATE_POLICY_NOT_CLEAR in gate["blocked_reasons"]


# --------------------------------------------------------------------------- #
# 26-27. Registry suppression
# --------------------------------------------------------------------------- #
def test_registry_suppresses_duplicate_request_id():
    entry, rr, er, ps, dr = _full_dry_run()
    ks = _clear_kill_switch(dr)
    rp = _clear_rate_policy()
    gate = sg.run_one_request_dispatch_gate(_bundle(dr, ks, rp, entry))
    registry = sg.DispatchGateRegistry()
    first = registry.submit(gate, ks, rp)
    assert first["appended"] is True
    assert first["registry_outcome_class"] == sg.GATE_REGISTRY_APPENDED
    # Same request id, identical binding -> duplicate request id suppression.
    second = registry.submit(gate, ks, rp)
    assert second["appended"] is False
    assert second["duplicate_suppressed"] is True
    assert second["registry_outcome_class"] == (
        sg.GATE_REGISTRY_DUPLICATE_REQUEST_ID)
    assert registry.candidate_count() == 1


def test_registry_suppresses_duplicate_idempotency_fingerprint():
    entry, rr, er, ps, dr = _full_dry_run()
    ks = _clear_kill_switch(dr)
    rp = _clear_rate_policy()
    gate_a = sg.run_one_request_dispatch_gate(
        _bundle(dr, ks, rp, entry, request_id="supervised_request_A"))
    # Different request id, SAME authority binding -> same fingerprint.
    gate_b = sg.run_one_request_dispatch_gate(
        _bundle(dr, ks, rp, entry, request_id="supervised_request_B"))
    registry = sg.DispatchGateRegistry()
    first = registry.submit(gate_a, ks, rp)
    assert first["appended"] is True
    second = registry.submit(gate_b, ks, rp)
    assert second["appended"] is False
    assert second["registry_outcome_class"] == (
        sg.GATE_REGISTRY_DUPLICATE_FINGERPRINT)
    assert registry.candidate_count() == 1


# --------------------------------------------------------------------------- #
# 28-30. Candidate hard invariants
# --------------------------------------------------------------------------- #
def test_candidate_sets_all_unsafe_flags_false():
    entry, rr, er, ps, dr = _full_dry_run()
    ks = _clear_kill_switch(dr)
    rp = _clear_rate_policy()
    gate = sg.run_one_request_dispatch_gate(_bundle(dr, ks, rp, entry))
    cand = gate["dispatch_authorization_candidate"]
    for flag in ("dispatch_performed", "live_request_performed",
                 "platform_api_called", "telegram_api_called",
                 "credential_hydrated", "llm_behavior", "scheduler_enabled",
                 "auto_retry_allowed"):
        assert cand[flag] is False, flag


def test_candidate_max_requests_authorized_is_one():
    entry, rr, er, ps, dr = _full_dry_run()
    ks = _clear_kill_switch(dr)
    rp = _clear_rate_policy()
    gate = sg.run_one_request_dispatch_gate(_bundle(dr, ks, rp, entry))
    assert gate["dispatch_authorization_candidate"][
        "max_requests_authorized"] == 1


def test_candidate_not_valid_for_live_execution():
    entry, rr, er, ps, dr = _full_dry_run()
    ks = _clear_kill_switch(dr)
    rp = _clear_rate_policy()
    gate = sg.run_one_request_dispatch_gate(_bundle(dr, ks, rp, entry))
    cand = gate["dispatch_authorization_candidate"]
    assert cand["valid_for_live_execution"] is False
    assert cand["requires_operator_live_gate"] is True
    assert cand["candidate_is_provider_authorization"] is False


# --------------------------------------------------------------------------- #
# 31. Audit deterministic + leak-free
# --------------------------------------------------------------------------- #
def test_redacted_immutable_audit_deterministic_and_leak_free():
    entry, rr, er, ps, dr = _full_dry_run()
    ks = _clear_kill_switch(dr)
    rp = _clear_rate_policy()
    gate = sg.run_one_request_dispatch_gate(_bundle(dr, ks, rp, entry))
    a1 = sg.build_redacted_immutable_dispatch_audit(gate, ks, rp)
    a2 = sg.build_redacted_immutable_dispatch_audit(gate, ks, rp)
    assert a1["audit_checksum"] == a2["audit_checksum"]
    assert sg.scan_for_leaks(a1) == []
    assert a1["valid_for_live_execution"] is False
    assert a1["no_raw_credential_stored"] is True


# --------------------------------------------------------------------------- #
# 32-33. Fail-closed on forbidden / financial-advice content
# --------------------------------------------------------------------------- #
def test_gate_fail_closed_on_forbidden_value():
    entry, rr, er, ps, dr = _full_dry_run()
    ks = _clear_kill_switch(dr)
    rp = _clear_rate_policy()
    tampered = copy.deepcopy(dr)
    tampered["leak"] = "ghp_abcdefghijklmnopqrstuvwxyz0123456789"
    gate = sg.run_one_request_dispatch_gate(_bundle(tampered, ks, rp, entry))
    assert gate["status"] == sg.Status.FAIL_CLOSED
    assert gate["forbidden_fields_detected"] is True
    assert sg.BLOCK_GATE_FORBIDDEN_VALUE in gate["blocked_reasons"]


def test_gate_fail_closed_on_financial_advice():
    entry, rr, er, ps, dr = _full_dry_run()
    ks = _clear_kill_switch(dr)
    rp = _clear_rate_policy()
    tampered = copy.deepcopy(dr)
    tampered["editorial_note"] = "You should buy now for guaranteed profit."
    gate = sg.run_one_request_dispatch_gate(_bundle(tampered, ks, rp, entry))
    assert gate["status"] == sg.Status.FAIL_CLOSED
    assert gate["financial_advice_detected"] is True
    assert sg.BLOCK_GATE_FINANCIAL_ADVICE in gate["blocked_reasons"]


def test_kill_switch_fail_closed_on_forbidden_value():
    _, _, _, _, dr = _full_dry_run()
    tampered = copy.deepcopy(dr)
    tampered["leak"] = "ghp_abcdefghijklmnopqrstuvwxyz0123456789"
    ks = sg.evaluate_kill_switch(
        tampered, operator_id="operator_jim",
        policy_snapshot_id="ks_policy_v1",
        kill_switch_state=sg.KILL_SWITCH_CLEAR)
    assert ks["status"] == sg.Status.FAIL_CLOSED
    assert ks["forbidden_fields_detected"] is True


# --------------------------------------------------------------------------- #
# 34-36. Module hygiene
# --------------------------------------------------------------------------- #
def test_no_forbidden_imports_or_env_access():
    from pathlib import Path
    src = Path(sg.__file__).read_text(encoding="utf-8")
    for banned in ("import requests", "import httpx", "import aiohttp",
                   "import urllib", "import socket", "import ssl",
                   "import webbrowser", "import subprocess", "import dotenv",
                   "import keyring", "import sqlite3", "import openai",
                   "import anthropic", "import telegram", "import tweepy",
                   "import selenium", "import playwright",
                   "os.environ", "os.getenv"):
        assert banned not in src, banned


def _code_only(path):
    """Return module source with string literals + comments removed.

    Network/credential operation strings are forbidden in EXECUTABLE code, but
    the module legitimately documents what it does NOT do in its docstrings and
    comments (e.g. "NO env / .env read", "no sendMessage"). Scanning raw source
    would false-positive on that safety prose, so we tokenize and drop STRING
    and COMMENT tokens first -- mirroring test_security_scans.py, which matches
    real operations rather than documentation text.
    """
    import io
    import tokenize
    from pathlib import Path
    src = Path(path).read_text(encoding="utf-8")
    out = []
    try:
        for tok in tokenize.generate_tokens(io.StringIO(src).readline):
            if tok.type in (tokenize.STRING, tokenize.COMMENT):
                continue
            out.append(tok.string)
    except tokenize.TokenError:
        # Fall back to raw source if tokenization is interrupted; the other
        # guards still apply.
        return src
    return " ".join(out)


def test_no_network_or_credential_access_strings():
    from pathlib import Path
    code = _code_only(sg.__file__)
    for banned in (".env", "getUpdates", "sendMessage", "bot_token",
                   "oauth", "access_token", "refresh_token"):
        assert banned not in code, banned


def test_module_import_has_no_side_effects(tmp_path):
    import importlib
    # Re-importing must not write any files into the cwd/artifact dirs.
    before = set(tmp_path.iterdir())
    importlib.reload(sg)
    after = set(tmp_path.iterdir())
    assert before == after


# --------------------------------------------------------------------------- #
# 37. Packet + doc deterministic and leak-free
# --------------------------------------------------------------------------- #
def test_packet_is_clean_and_deterministic():
    p1 = sg.build_packet()
    p2 = sg.build_packet()
    assert p1["checksum_sha256"] == p2["checksum_sha256"]
    assert sg.scan_for_leaks(p1) == []
    assert p1["task_label"] == sg.TASK_LABEL
    assert p1["status"] == sg.Status.PASS
    assert p1["known_kill_switch_states"] == sorted(
        sg.KNOWN_KILL_SWITCH_STATES)


def test_doc_is_clean_and_deterministic():
    d1 = sg.build_doc()
    d2 = sg.build_doc()
    assert d1 == d2
    assert sg.scan_for_leaks(d1) == []
    assert "0174TM/TN/TO" in d1
    assert sg.EXACT_NEXT_TASK_RECOMMENDATION in d1


def test_write_artifacts_writes_two_files(tmp_path):
    paths = sg.write_artifacts(str(tmp_path))
    assert len(paths) == 2
    for p in paths:
        with open(p, encoding="utf-8") as fh:
            content = fh.read()
        assert content
        assert sg.scan_for_leaks(content) == []


def test_safety_flags_present_on_all_objects():
    entry, rr, er, ps, dr = _full_dry_run()
    ks = _clear_kill_switch(dr)
    rp = _clear_rate_policy()
    gate = sg.run_one_request_dispatch_gate(_bundle(dr, ks, rp, entry))
    audit = sg.build_redacted_immutable_dispatch_audit(gate, ks, rp)
    for rec in (ks, rp, gate, audit):
        assert rec["credential_hydrated"] is False
        assert rec["network_performed"] is False
        assert rec["llm_behavior"] is False
        assert rec["dispatch_performed"] is False
        assert rec["scheduler_enabled"] is False
        assert rec["auto_retry_allowed"] is False


# --------------------------------------------------------------------------- #
# R1. Upstream safety-flag revalidation hardening
# --------------------------------------------------------------------------- #
def test_r1_valid_full_chain_still_creates_candidate_not_dispatched():
    entry, rr, er, ps, dr = _full_dry_run()
    ks = _clear_kill_switch(dr)
    rp = _clear_rate_policy()
    gate = sg.run_one_request_dispatch_gate(_bundle(dr, ks, rp, entry))
    assert gate["status"] == sg.Status.PASS
    assert gate["dispatch_gate_outcome_class"] == sg.GATE_CANDIDATE_CREATED
    assert gate["candidate_created_not_dispatched"] is True


def test_r1_detect_unsafe_behavior_claims_clean_artifact_returns_empty():
    _, _, _, _, dr = _full_dry_run()
    assert sg.detect_unsafe_behavior_claims(dr, sg.ARTIFACT_DRY_RUN) == []
    assert sg.detect_unsafe_behavior_claims({}, sg.ARTIFACT_KILL_SWITCH) == []


def test_r1_detect_unsafe_behavior_claims_reports_base_and_flag_suffix():
    reasons = sg.detect_unsafe_behavior_claims(
        {"network_performed": True}, sg.ARTIFACT_KILL_SWITCH)
    assert sg.BLOCK_GATE_KILL_SWITCH_UNSAFE_BEHAVIOR in reasons
    assert (sg.BLOCK_GATE_KILL_SWITCH_UNSAFE_BEHAVIOR
            + ":network_performed") in reasons


def _tamper_dry_run(flag, value=True):
    entry, rr, er, ps, dr = _full_dry_run()
    tampered = copy.deepcopy(dr)
    tampered[flag] = value
    ks = _clear_kill_switch(dr)
    rp = _clear_rate_policy()
    gate = sg.run_one_request_dispatch_gate(_bundle(tampered, ks, rp, entry))
    return gate


def test_r1_dry_run_network_performed_blocks():
    gate = _tamper_dry_run("network_performed")
    assert gate["status"] == sg.Status.BLOCKED
    assert sg.BLOCK_GATE_DRY_RUN_UNSAFE_BEHAVIOR in gate["blocked_reasons"]
    assert (sg.BLOCK_GATE_DRY_RUN_UNSAFE_BEHAVIOR
            + ":network_performed") in gate["blocked_reasons"]


def test_r1_dry_run_telegram_api_called_blocks():
    gate = _tamper_dry_run("telegram_api_called")
    assert gate["status"] == sg.Status.BLOCKED
    assert sg.BLOCK_GATE_DRY_RUN_UNSAFE_BEHAVIOR in gate["blocked_reasons"]


def test_r1_dry_run_llm_behavior_blocks():
    gate = _tamper_dry_run("llm_behavior")
    assert gate["status"] == sg.Status.BLOCKED
    assert sg.BLOCK_GATE_DRY_RUN_UNSAFE_BEHAVIOR in gate["blocked_reasons"]


def test_r1_dry_run_scheduler_enabled_blocks():
    gate = _tamper_dry_run("scheduler_enabled")
    assert gate["status"] == sg.Status.BLOCKED
    assert sg.BLOCK_GATE_DRY_RUN_UNSAFE_BEHAVIOR in gate["blocked_reasons"]


def test_r1_dry_run_auto_retry_allowed_blocks():
    gate = _tamper_dry_run("auto_retry_allowed")
    assert gate["status"] == sg.Status.BLOCKED
    assert sg.BLOCK_GATE_DRY_RUN_UNSAFE_BEHAVIOR in gate["blocked_reasons"]


def _tamper_kill_switch(flag, value=True):
    entry, rr, er, ps, dr = _full_dry_run()
    ks = _clear_kill_switch(dr)
    # Keep the clear status/pass metadata intact; only flip an unsafe flag.
    assert ks["status"] == sg.Status.PASS
    assert ks["kill_switch_clear"] is True
    ks[flag] = value
    rp = _clear_rate_policy()
    gate = sg.run_one_request_dispatch_gate(_bundle(dr, ks, rp, entry))
    return gate


def test_r1_kill_switch_network_performed_blocks_despite_clear():
    gate = _tamper_kill_switch("network_performed")
    assert gate["status"] == sg.Status.BLOCKED
    assert sg.BLOCK_GATE_KILL_SWITCH_UNSAFE_BEHAVIOR in gate["blocked_reasons"]


def test_r1_kill_switch_platform_api_called_blocks():
    gate = _tamper_kill_switch("platform_api_called")
    assert gate["status"] == sg.Status.BLOCKED
    assert sg.BLOCK_GATE_KILL_SWITCH_UNSAFE_BEHAVIOR in gate["blocked_reasons"]


def test_r1_kill_switch_credential_hydrated_blocks():
    gate = _tamper_kill_switch("credential_hydrated")
    assert gate["status"] == sg.Status.BLOCKED
    assert sg.BLOCK_GATE_KILL_SWITCH_UNSAFE_BEHAVIOR in gate["blocked_reasons"]


def test_r1_kill_switch_live_ready_blocks():
    gate = _tamper_kill_switch("live_ready")
    assert gate["status"] == sg.Status.BLOCKED
    assert sg.BLOCK_GATE_KILL_SWITCH_UNSAFE_BEHAVIOR in gate["blocked_reasons"]


def test_r1_kill_switch_evaluation_is_dispatch_blocks():
    gate = _tamper_kill_switch("kill_switch_evaluation_is_dispatch")
    assert gate["status"] == sg.Status.BLOCKED
    assert (sg.BLOCK_GATE_KILL_SWITCH_UNSAFE_BEHAVIOR
            + ":kill_switch_evaluation_is_dispatch") in gate["blocked_reasons"]


def _tamper_rate_policy(flag, value=True):
    entry, rr, er, ps, dr = _full_dry_run()
    ks = _clear_kill_switch(dr)
    rp = _clear_rate_policy()
    assert rp["status"] == sg.Status.PASS
    assert rp["rate_spend_retry_policy_clear"] is True
    rp[flag] = value
    gate = sg.run_one_request_dispatch_gate(_bundle(dr, ks, rp, entry))
    return gate


def test_r1_rate_policy_network_performed_blocks_despite_clear():
    gate = _tamper_rate_policy("network_performed")
    assert gate["status"] == sg.Status.BLOCKED
    assert sg.BLOCK_GATE_RATE_POLICY_UNSAFE_BEHAVIOR in gate["blocked_reasons"]


def test_r1_rate_policy_scheduler_enabled_blocks():
    gate = _tamper_rate_policy("scheduler_enabled")
    assert gate["status"] == sg.Status.BLOCKED
    assert sg.BLOCK_GATE_RATE_POLICY_UNSAFE_BEHAVIOR in gate["blocked_reasons"]


def test_r1_rate_policy_auto_retry_allowed_blocks():
    gate = _tamper_rate_policy("auto_retry_allowed")
    assert gate["status"] == sg.Status.BLOCKED
    assert sg.BLOCK_GATE_RATE_POLICY_UNSAFE_BEHAVIOR in gate["blocked_reasons"]


def test_r1_rate_policy_credential_hydrated_blocks():
    gate = _tamper_rate_policy("credential_hydrated")
    assert gate["status"] == sg.Status.BLOCKED
    assert sg.BLOCK_GATE_RATE_POLICY_UNSAFE_BEHAVIOR in gate["blocked_reasons"]


def test_r1_rate_policy_evaluation_is_dispatch_blocks():
    gate = _tamper_rate_policy("rate_spend_retry_evaluation_is_dispatch")
    assert gate["status"] == sg.Status.BLOCKED
    assert (sg.BLOCK_GATE_RATE_POLICY_UNSAFE_BEHAVIOR
            + ":rate_spend_retry_evaluation_is_dispatch"
            ) in gate["blocked_reasons"]


def test_r1_blocked_reasons_identify_artifact_class_and_flag():
    gate = _tamper_kill_switch("platform_api_called")
    matching = [r for r in gate["blocked_reasons"]
                if r == (sg.BLOCK_GATE_KILL_SWITCH_UNSAFE_BEHAVIOR
                         + ":platform_api_called")]
    assert matching == [
        sg.BLOCK_GATE_KILL_SWITCH_UNSAFE_BEHAVIOR + ":platform_api_called"]


def test_r1_candidate_still_sets_unsafe_flags_false_on_valid_chain():
    entry, rr, er, ps, dr = _full_dry_run()
    ks = _clear_kill_switch(dr)
    rp = _clear_rate_policy()
    gate = sg.run_one_request_dispatch_gate(_bundle(dr, ks, rp, entry))
    cand = gate["dispatch_authorization_candidate"]
    for flag in ("dispatch_performed", "live_request_performed",
                 "platform_api_called", "telegram_api_called",
                 "credential_hydrated", "llm_behavior", "scheduler_enabled",
                 "auto_retry_allowed"):
        assert cand[flag] is False, flag
    assert cand["valid_for_live_execution"] is False


def test_r1_registry_still_suppresses_duplicates():
    entry, rr, er, ps, dr = _full_dry_run()
    ks = _clear_kill_switch(dr)
    rp = _clear_rate_policy()
    gate_a = sg.run_one_request_dispatch_gate(
        _bundle(dr, ks, rp, entry, request_id="supervised_request_R1A"))
    gate_b = sg.run_one_request_dispatch_gate(
        _bundle(dr, ks, rp, entry, request_id="supervised_request_R1B"))
    registry = sg.DispatchGateRegistry()
    assert registry.submit(gate_a, ks, rp)["appended"] is True
    # Same request id -> request-id suppression.
    assert registry.submit(gate_a, ks, rp)["registry_outcome_class"] == (
        sg.GATE_REGISTRY_DUPLICATE_REQUEST_ID)
    # Different request id, same binding -> fingerprint suppression.
    assert registry.submit(gate_b, ks, rp)["registry_outcome_class"] == (
        sg.GATE_REGISTRY_DUPLICATE_FINGERPRINT)
    assert registry.candidate_count() == 1


def test_r1_packet_includes_invariants_and_blocked_reasons():
    p = sg.build_packet()
    for inv in (
            "dispatch_gate_revalidates_upstream_safety_flags",
            "kill_switch_clear_metadata_cannot_hide_unsafe_behavior",
            "rate_policy_clear_metadata_cannot_hide_retry_or_scheduler_behavior",
            "dry_run_complete_metadata_cannot_hide_network_or_live_behavior",
            "unsafe_upstream_behavior_claim_blocks_candidate"):
        assert inv in p["hard_invariants"], inv
    for reason in (
            sg.BLOCK_GATE_DRY_RUN_UNSAFE_BEHAVIOR,
            sg.BLOCK_GATE_KILL_SWITCH_UNSAFE_BEHAVIOR,
            sg.BLOCK_GATE_RATE_POLICY_UNSAFE_BEHAVIOR):
        assert reason in p["r1_upstream_revalidation_blocked_reasons"], reason


def test_r1_packet_and_doc_deterministic_and_leak_free():
    p1 = sg.build_packet()
    p2 = sg.build_packet()
    assert p1["checksum_sha256"] == p2["checksum_sha256"]
    assert sg.scan_for_leaks(p1) == []
    d1 = sg.build_doc()
    d2 = sg.build_doc()
    assert d1 == d2
    assert sg.scan_for_leaks(d1) == []
    assert sg.BLOCK_GATE_KILL_SWITCH_UNSAFE_BEHAVIOR in d1
