from dataclasses import asdict

import pytest

from live_contentops import approval_ledger as ledger
from live_contentops import approval_payload_hash as payload_hash
from live_contentops import dispatch_outbox


def _payload(**overrides):
    p = payload_hash.canonical_payload_hash_input(
        platform_id="x_profile",
        destination_binding_id="x_profile_default",
        credential_handle_id="x_symbolic_handle",
        payload_schema_version="v1",
        adapter_version="1.0.0",
        payload_class_id="x_short_post",
        payload_text="Grounded dispatch prep only",
        platform_formatting="plain",
        media_manifest_hash="media_none",
        policy_snapshot_id="policy_v1",
    )
    p["payload_id"] = "payload_1"
    p.update(overrides)
    return p


def _approval_event(payload):
    h = payload_hash.compute_payload_hash(payload)
    return asdict(ledger.build_operator_approved_event(
        operator_id="jim_op",
        approval_channel="local_ui",
        challenge_id="challenge_1",
        payload_id=payload.get("payload_id", "payload_1"),
        payload_hash=h,
        platform_id=payload["platform_id"],
        payload_class_id=payload["payload_class_id"],
        destination_binding_id=payload["destination_binding_id"],
        credential_handle_id=payload["credential_handle_id"],
        media_manifest_hash=payload["media_manifest_hash"],
        policy_snapshot_id=payload["policy_snapshot_id"],
        approval_text="Approved exact payload hash.",
    ))


def _kill_switch_clear():
    return {
        "snapshot_id": "ks_1",
        "scope": "inactive",
        "allow_local_outbox": True,
        "kill_switch_engaged": False,
        "kill_switch_active": False,
        "live_dispatch_enabled": False,
    }


def test_prepare_dispatch_outbox_entry_creates_local_record_not_dispatch():
    payload = _payload()
    event = _approval_event(payload)

    result = dispatch_outbox.prepare_dispatch_outbox_entry(
        payload,
        [event],
        _kill_switch_clear(),
        outbox_entry_id="outbox_1",
    ).as_dict()

    entry = result["outbox_entry"]
    assert result["status"] == dispatch_outbox.OUTBOX_STATUS_READY_FOR_MOCK_DISPATCH
    assert entry["outbox_entry_id"] == "outbox_1"
    assert entry["request_budget"] == 1
    assert entry["auto_retry_allowed"] is False
    assert entry["valid_for_live_dispatch_now"] is False
    assert entry["audit_sink_required"] is True
    assert entry["manual_fallback_required"] is True
    assert entry["kill_switch_required"] is True
    assert entry["dispatch_mode"] == "dry_run"
    assert entry["dispatch_performed"] is False
    assert entry["live_request_performed"] is False
    assert entry["platform_api_called"] is False
    assert entry["credential_hydrated"] is False
    assert result["audit_event"]["raw_credential_stored"] is False


def test_ready_for_supervised_live_future_still_not_live_now():
    payload = _payload()
    event = _approval_event(payload)
    result = dispatch_outbox.prepare_dispatch_outbox_entry(
        payload,
        [event],
        _kill_switch_clear(),
        dispatch_mode="supervised_live_future",
    ).as_dict()
    assert result["status"] == dispatch_outbox.OUTBOX_STATUS_READY_FOR_SUPERVISED_LIVE_FUTURE
    assert result["outbox_entry"]["valid_for_live_dispatch_now"] is False


def test_duplicate_idempotency_key_blocks_second_outbox_entry():
    payload = _payload()
    event = _approval_event(payload)
    first = dispatch_outbox.prepare_dispatch_outbox_entry(payload, [event], _kill_switch_clear()).as_dict()
    key = first["idempotency_decision"]["idempotency_key"]

    duplicate = dispatch_outbox.prepare_dispatch_outbox_entry(
        payload,
        [event],
        _kill_switch_clear(),
        existing_idempotency_keys={key},
    ).as_dict()

    assert duplicate["status"] == dispatch_outbox.OUTBOX_STATUS_BLOCKED_BY_DUPLICATE
    assert duplicate["outbox_entry"] is None
    assert duplicate["idempotency_decision"]["duplicate"] is True
    assert "duplicate_idempotency_key" in duplicate["blocked_reasons"]
    assert duplicate["idempotency_decision"]["auto_retry_allowed"] is False


def test_kill_switch_missing_fails_closed_before_idempotency():
    payload = _payload()
    event = _approval_event(payload)
    result = dispatch_outbox.prepare_dispatch_outbox_entry(payload, [event], None).as_dict()
    assert result["status"] == dispatch_outbox.OUTBOX_STATUS_BLOCKED_BY_KILL_SWITCH
    assert result["outbox_entry"] is None
    assert "kill_switch_state_missing" in result["blocked_reasons"]
    assert result["kill_switch_decision"]["local_outbox_allowed"] is False


def test_no_outbox_without_approved_current_approval():
    payload = _payload()
    result = dispatch_outbox.prepare_dispatch_outbox_entry(payload, [], _kill_switch_clear()).as_dict()
    assert result["status"] == dispatch_outbox.OUTBOX_STATUS_BLOCKED_BY_APPROVAL
    assert result["outbox_entry"] is None
    assert any("approval_state_not_current:not_requested" in r for r in result["blocked_reasons"])


def test_requested_approval_cannot_create_ready_outbox():
    payload = _payload()
    h = payload_hash.compute_payload_hash(payload)
    requested = asdict(ledger.build_approval_requested_event(
        operator_id="jim_op",
        payload_id="payload_1",
        payload_hash=h,
        platform_id=payload["platform_id"],
        payload_class_id=payload["payload_class_id"],
        destination_binding_id=payload["destination_binding_id"],
        credential_handle_id=payload["credential_handle_id"],
        media_manifest_hash=payload["media_manifest_hash"],
        policy_snapshot_id=payload["policy_snapshot_id"],
    ))
    result = dispatch_outbox.prepare_dispatch_outbox_entry(payload, [requested], _kill_switch_clear()).as_dict()
    assert result["outbox_entry"] is None
    assert result["status"] == dispatch_outbox.OUTBOX_STATUS_BLOCKED_BY_APPROVAL


def test_revoked_expired_invalidated_approval_blocks_outbox():
    payload = _payload()
    approved = _approval_event(payload)
    h = payload_hash.compute_payload_hash(payload)
    followups = [
        ledger.build_operator_revoked_event("jim_op", "payload_1", h, approved["ledger_event_id"]),
        ledger.build_approval_expired_event("jim_op", "payload_1", h, approved["ledger_event_id"]),
        ledger.build_approval_invalidated_event("jim_op", "payload_1", h, "edit", approved["ledger_event_id"]),
    ]
    for followup in followups:
        result = dispatch_outbox.prepare_dispatch_outbox_entry(
            payload,
            [approved, asdict(followup)],
            _kill_switch_clear(),
        ).as_dict()
        assert result["outbox_entry"] is None
        assert result["status"] == dispatch_outbox.OUTBOX_STATUS_BLOCKED_BY_APPROVAL


def test_payload_edit_after_approval_blocks_outbox():
    payload = _payload()
    event = _approval_event(payload)
    edited = dict(payload)
    edited["payload_text"] = "Edited after approval"
    result = dispatch_outbox.prepare_dispatch_outbox_entry(edited, [event], _kill_switch_clear()).as_dict()
    assert result["status"] == dispatch_outbox.OUTBOX_STATUS_BLOCKED_BY_APPROVAL
    assert result["outbox_entry"] is None
    assert any("approval_state_not_current" in r for r in result["blocked_reasons"])
    assert "payload_hash_mismatch" in result["blocked_reasons"]


def test_secret_shaped_value_blocks_fail_closed():
    payload = _payload(payload_text="Bearer abcdefghijklmnopqrstuvwxyz1234567890")
    event = _approval_event(_payload())
    result = dispatch_outbox.prepare_dispatch_outbox_entry(payload, [event], _kill_switch_clear()).as_dict()
    assert result["status"] == dispatch_outbox.OUTBOX_STATUS_MANUAL_FALLBACK_REQUIRED
    assert result["outbox_entry"] is None
    assert any(reason.startswith("secret_risk_detected") for reason in result["blocked_reasons"])


def test_assert_no_live_dispatch_ready_now_fails_if_entry_claims_live_ready():
    with pytest.raises(AssertionError):
        dispatch_outbox.assert_no_live_dispatch_ready_now([{
            "valid_for_live_dispatch_now": True,
            "dispatch_performed": False,
            "live_request_performed": False,
            "platform_api_called": False,
            "credential_hydrated": False,
            "auto_retry_allowed": False,
        }])


def test_packet_declares_removed_approval_apis_not_used():
    packet = dispatch_outbox.dispatch_outbox_packet()
    assert packet["helper_api_completed"] == ["derive_outbox_status", "assert_no_live_dispatch_ready_now"]
    assert packet["removed_approval_ledger_apis_not_used"] == [
        "validate_approval_record",
        "validate_kill_switch_state",
        "validate_audit_event",
        "check_action_allowed",
    ]
