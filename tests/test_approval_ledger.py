from dataclasses import asdict

import pytest

from live_contentops import approval_ledger as ledger


def test_requested_event_not_dispatch_valid():
    event = ledger.build_approval_requested_event(
        operator_id="jim_op",
        payload_id="p1",
        payload_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        platform_id="x_profile",
        payload_class_id="x_short_post",
        destination_binding_id="x_profile_default",
        credential_handle_id="x_bearer",
        policy_snapshot_id="v1",
    )
    assert event.valid_for_dispatch is False
    assert "awaiting_operator_approval" in event.blocked_reasons


def test_rejected_event_not_valid():
    event = ledger.build_operator_rejected_event(
        operator_id="jim_op",
        payload_id="p1",
        payload_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        platform_id="x_profile",
        payload_class_id="x_short_post",
        destination_binding_id="x_profile_default",
        credential_handle_id="x_bearer",
        policy_snapshot_id="v1",
    )
    assert event.valid_for_dispatch is False
    assert "operator_rejected_payload" in event.blocked_reasons


def test_revoked_event_not_valid():
    event = ledger.build_operator_revoked_event(
        operator_id="jim_op",
        payload_id="p1",
        payload_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        supersedes_event_id="app_123",
    )
    assert event.valid_for_dispatch is False
    assert "operator_revoked_approval" in event.blocked_reasons


def test_invalidated_events_not_valid():
    for reason in ("edit", "destination_change", "credential_change", "policy_change"):
        event = ledger.build_approval_invalidated_event(
            operator_id="jim_op",
            payload_id="p1",
            payload_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            invalidation_reason=reason,
            supersedes_event_id="app_123",
        )
        assert event.valid_for_dispatch is False
        assert f"invalidated_by_{reason}" in event.blocked_reasons


def test_expired_event_not_valid():
    event = ledger.build_approval_expired_event(
        operator_id="jim_op",
        payload_id="p1",
        payload_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        supersedes_event_id="app_123",
    )
    assert event.valid_for_dispatch is False
    assert "approval_expired" in event.blocked_reasons


def test_append_only_immutable_checks():
    event1 = ledger.build_approval_requested_event(
        operator_id="jim_op",
        payload_id="p1",
        payload_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        platform_id="x_profile",
        payload_class_id="x_short_post",
        destination_binding_id="x_profile_default",
        credential_handle_id="x_bearer",
        policy_snapshot_id="v1",
    )
    ledger_list = [asdict(event1)]
    ledger.assert_ledger_append_only_shape(ledger_list)

    # Mutate event field and verify it fails assertion
    ledger_list[0]["operator_id"] = "hacker_op"
    with pytest.raises(AssertionError):
        ledger.assert_ledger_append_only_shape(ledger_list)


def test_approval_text_redacted_safe():
    event = ledger.build_approval_requested_event(
        operator_id="jim_op",
        payload_id="p1",
        payload_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        platform_id="x_profile",
        payload_class_id="x_short_post",
        destination_binding_id="x_profile_default",
        credential_handle_id="x_bearer",
        policy_snapshot_id="v1",
        approval_text="My bot token is 123456:AABBCCDDEEFFGGHHIIJJKKLLMMNNOOPPQQRR and password=hunter2",
    )
    assert "123456:AABBCCDDEEFFGGHHIIJJKKLLMMNNOOPPQQRR" not in event.approval_text_redacted
    assert "hunter2" not in event.approval_text_redacted
    assert "[REDACTED_BOT_TOKEN]" in event.approval_text_redacted
    assert "password=[REDACTED]" in event.approval_text_redacted
