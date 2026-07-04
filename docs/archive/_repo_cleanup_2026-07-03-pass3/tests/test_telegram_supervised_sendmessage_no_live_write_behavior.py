import socket

from live_contentops import telegram_supervised_sendmessage_dry_run_gate as gate


def test_dry_run_gate_does_not_open_socket(monkeypatch):
    def fail_socket(*args, **kwargs):
        raise AssertionError("socket creation forbidden in dry-run gate")

    monkeypatch.setattr(socket, "socket", fail_socket)

    result = gate.run_telegram_supervised_sendmessage_dry_run_gate()

    assert result.status == "PASS_DRY_RUN_PREP_REVIEW_BLOCKED"
    assert result.evidence_packet["no_provider_api_call_proof"] is True
    assert result.evidence_packet["telegram_write_endpoint_called"] is False
    assert result.evidence_packet["network_request_performed"] is False


def test_dry_run_gate_does_not_read_environment(monkeypatch):
    def fail_getenv(*args, **kwargs):
        raise AssertionError("env read forbidden in dry-run gate")

    monkeypatch.setattr("os.getenv", fail_getenv)

    result = gate.run_telegram_supervised_sendmessage_dry_run_gate()

    assert result.status == "PASS_DRY_RUN_PREP_REVIEW_BLOCKED"
    assert result.evidence_packet["credential_hydrated"] is False
    assert result.evidence_packet["no_env_read_proof"] is True


def test_live_write_markers_are_false_across_all_packets():
    result = gate.run_telegram_supervised_sendmessage_dry_run_gate()

    for packet in gate.build_all_packets().values():
        assert packet.get("sendmessage_called", False) is False
        assert packet.get("telegram_write_endpoint_called", False) is False
        assert packet.get("live_write_performed", False) is False
        assert packet.get("network_request_performed", False) is False
        assert packet.get("credential_hydrated", False) is False
        assert packet.get("dispatchable_now", False) is False
        assert packet.get("valid_for_live_dispatch_now", False) is False

    assert result.live_gate_packet["live_write_allowed_now"] is False
    assert result.live_gate_packet["current_operator_approval_present"] is False


def test_duplicate_idempotency_blocks_without_live_behavior():
    first = gate.run_telegram_supervised_sendmessage_dry_run_gate()
    duplicate_key = first.idempotency_packet["idempotency_key"]

    second = gate.run_telegram_supervised_sendmessage_dry_run_gate(existing_idempotency_keys={duplicate_key})

    assert second.status == "PASS_DRY_RUN_PREP_REVIEW_BLOCKED"
    assert second.idempotency_packet["duplicate"] is True
    assert "duplicate_idempotency_key" in second.idempotency_packet["blocked_reasons"]
    assert "duplicate_idempotency_key" in second.outbox_packet["blocked_reasons"]
    assert second.outbox_packet["outbox_status"] == "blocked_pending_operator_approval"
    assert second.live_gate_packet["live_write_allowed_now"] is False
    assert second.evidence_packet["sendmessage_called"] is False
    assert second.evidence_packet["live_write_performed"] is False
    assert second.evidence_packet["network_request_performed"] is False


def test_no_ready_for_mock_dispatch_without_operator_approval():
    result = gate.run_telegram_supervised_sendmessage_dry_run_gate()
    text = str(result.as_dict())

    assert result.outbox_packet["status"] == "blocked_pending_operator_approval"
    assert "ready_for_mock_dispatch" not in text
    assert result.approval_packet["operator_approved_dry_run_payload_hash"] is False
    assert result.approval_packet["operator_approved_live_send"] is False
