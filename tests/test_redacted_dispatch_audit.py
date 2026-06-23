import pytest

from live_contentops import redacted_dispatch_audit as audit


def _entry(**overrides):
    data = {
        "outbox_entry_id": "outbox_1",
        "approval_ledger_entry_id": "app_1",
        "approval_event_id": "app_1",
        "platform_id": "x_profile",
        "payload_class_id": "x_short_post",
        "destination_binding_id": "x_profile_default",
        "credential_handle_id": "x_symbolic_handle",
        "payload_hash": "a" * 64,
        "idempotency_key": "b" * 64,
        "blocked_reasons": [],
        "manual_fallback_status": "manual_fallback_not_required",
    }
    data.update(overrides)
    return data


def _idem():
    return {"status": "new_key_allowed_for_local_outbox_only", "idempotency_key": "b" * 64, "blocked_reasons": [], "auto_retry_allowed": False}


def _kill():
    return {"status": "kill_switch_clear", "manual_fallback_state": "manual_fallback_not_required", "blocked_reasons": []}


def _sink():
    return audit.AuditSinkReadiness("sink", True, True).as_dict()


def test_blocked_audit_uses_request_budget_zero_and_false_flags():
    event = audit.build_blocked_dispatch_audit_event(_entry(), ["blocked"])
    assert event["request_budget_used"] == 0
    assert event["retry_count"] == 0
    assert event["raw_request_persisted"] is False
    assert event["raw_response_persisted"] is False
    assert event["token_logged"] is False
    assert event["headers_logged"] is False
    assert event["credential_value_logged"] is False
    assert event["no_secret_output"] is True
    audit.assert_redacted_audit_safe(event)


def test_mock_audit_is_clearly_non_live():
    event = audit.build_mock_dispatch_audit_event(_entry(), _idem(), _kill(), _sink())
    assert event["mock_dispatch"] is True
    assert event["dispatch_classification"] == "mock_non_live"
    assert event["live_request_performed"] is False
    assert event["platform_api_called"] is False
    assert event["success_classification"] == "mock_success_only_non_live"


def test_no_secret_shaped_strings_allowed():
    event = audit.build_blocked_dispatch_audit_event(_entry(), ["blocked"])
    event["note"] = "Bearer abcdefghijklmnopqrstuvwxyz1234567890"
    with pytest.raises(AssertionError):
        audit.assert_redacted_audit_safe(event)


def test_audit_checksum_detects_tampering():
    event = audit.build_mock_dispatch_audit_event(_entry(), _idem(), _kill(), _sink())
    assert audit.validate_redacted_dispatch_audit_event(event)["valid"] is True
    event["platform_id"] = "tampered"
    result = audit.validate_redacted_dispatch_audit_event(event)
    assert result["valid"] is False
    assert "audit_checksum_mismatch" in result["blocked_reasons"]


def test_packet_declares_required_audit_contract():
    packet = audit.redacted_dispatch_audit_packet()
    assert packet["raw_request_persisted"] is False
    assert packet["raw_response_persisted"] is False
    assert packet["retry_count"] == 0
    assert "build_blocked_dispatch_audit_event" in packet["helper_api_completed"]
