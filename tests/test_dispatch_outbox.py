from dataclasses import asdict

import pytest

from live_contentops import approval_ledger as ledger
from live_contentops import approval_payload_hash as payload_hash
from live_contentops import dispatch_outbox


def _payload():
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
    return p


def _approval_event(payload):
    h = payload_hash.compute_payload_hash(payload)
    return asdict(ledger.build_operator_approved_event(
        operator_id="jim_op",
        approval_channel="local_ui",
        challenge_id="challenge_1",
        payload_id="payload_1",
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
        "allow_local_outbox": True,
        "kill_switch_engaged": False,
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

    assert result["status"] == dispatch_outbox.OUTBOX_STATUS_CREATED
    assert result["outbox_entry"]["outbox_entry_id"] == "outbox_1"
    assert result["outbox_entry"]["dispatch_performed"] is False
    assert result["outbox_entry"]["live_request_performed"] is False
    assert result["outbox_entry"]["platform_api_called"] is False
    assert result["outbox_entry"]["credential_hydrated"] is False
    assert result["outbox_entry"]["auto_retry_allowed"] is False
    assert result["audit_event"]["raw_credential_stored"] is False


def test_duplicate_idempotency_key_blocks_second_outbox_entry():
    payload = _payload()
    event = _approval_event(payload)
    first = dispatch_outbox.prepare_dispatch_outbox_entry(
        payload,
        [event],
        _kill_switch_clear(),
    ).as_dict()
    key = first["idempotency_decision"]["idempotency_key"]

    duplicate = dispatch_outbox.prepare_dispatch_outbox_entry(
        payload,
        [event],
        _kill_switch_clear(),
        existing_idempotency_keys={key},
    ).as_dict()

    assert duplicate["status"] == dispatch_outbox.OUTBOX_STATUS_DUPLICATE
    assert duplicate["outbox_entry"] is None
    assert duplicate["idempotency_decision"]["duplicate"] is True
    assert "duplicate_idempotency_key" in duplicate["blocked_reasons"]


def test_kill_switch_missing_fails_closed_before_idempotency():
    payload = _payload()
    event = _approval_event(payload)

    result = dispatch_outbox.prepare_dispatch_outbox_entry(
        payload,
        [event],
        None,
    ).as_dict()

    assert result["status"] == dispatch_outbox.OUTBOX_STATUS_BLOCKED
    assert result["outbox_entry"] is None
    assert "kill_switch_state_missing" in result["blocked_reasons"]
    assert result["kill_switch_decision"]["local_outbox_allowed"] is False


def test_payload_edit_after_approval_blocks_outbox():
    payload = _payload()
    event = _approval_event(payload)
    edited = dict(payload)
    edited["payload_text"] = "Edited after approval"

    result = dispatch_outbox.prepare_dispatch_outbox_entry(
        edited,
        [event],
        _kill_switch_clear(),
    ).as_dict()

    assert result["status"] == dispatch_outbox.OUTBOX_STATUS_BLOCKED
    assert result["outbox_entry"] is None
    assert any("approval_state_not_current" in r for r in result["blocked_reasons"])
    assert "payload_hash_mismatch" in result["blocked_reasons"]


def test_secret_shaped_value_blocks_fail_closed():
    payload = _payload()
    payload["payload_text"] = "Bearer abcdefghijklmnopqrstuvwxyz1234567890"
    event = _approval_event(_payload())

    result = dispatch_outbox.prepare_dispatch_outbox_entry(
        payload,
        [event],
        _kill_switch_clear(),
    ).as_dict()

    assert result["status"] == dispatch_outbox.OUTBOX_STATUS_BLOCKED
    assert result["outbox_entry"] is None
    assert any(reason.startswith("secret_risk_detected") for reason in result["blocked_reasons"])


def test_packet_declares_removed_approval_apis_not_used():
    packet = dispatch_outbox.dispatch_outbox_packet()
    assert packet["removed_approval_ledger_apis_not_used"] == [
        "validate_approval_record",
        "validate_kill_switch_state",
        "validate_audit_event",
        "check_action_allowed",
    ]
