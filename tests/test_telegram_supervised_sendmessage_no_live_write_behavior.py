import socket

from live_contentops import telegram_supervised_sendmessage_dry_run_gate as gate


def test_dry_run_gate_does_not_open_socket(monkeypatch):
    def fail_socket(*args, **kwargs):
        raise AssertionError("socket creation forbidden in dry-run gate")

    monkeypatch.setattr(socket, "socket", fail_socket)

    result = gate.run_telegram_supervised_sendmessage_dry_run_gate()

    assert result.status == "PASS_DRY_RUN_GATE"
    assert result.evidence_packet["no_provider_api_call_proof"] is True
    assert result.evidence_packet["telegram_write_endpoint_called"] is False


def test_dry_run_gate_does_not_read_environment(monkeypatch):
    def fail_getenv(*args, **kwargs):
        raise AssertionError("env read forbidden in dry-run gate")

    monkeypatch.setattr("os.getenv", fail_getenv)

    result = gate.run_telegram_supervised_sendmessage_dry_run_gate()

    assert result.status == "PASS_DRY_RUN_GATE"
    assert result.evidence_packet["credential_hydrated"] is False


def test_live_write_markers_are_false_across_all_packets():
    result = gate.run_telegram_supervised_sendmessage_dry_run_gate()

    for packet in gate.build_all_packets().values():
        assert packet.get("sendmessage_called", False) is False
        assert packet.get("telegram_write_endpoint_called", False) is False
        assert packet.get("live_write_performed", False) is False
        assert packet.get("network_request_performed", False) is False
        assert packet.get("credential_hydrated", False) is False
        assert packet.get("valid_for_live_dispatch_now", False) is False

    assert result.live_gate_packet["live_write_allowed_now"] is False


def test_duplicate_idempotency_blocks_without_live_behavior():
    first = gate.run_telegram_supervised_sendmessage_dry_run_gate()
    duplicate_key = first.idempotency_packet["idempotency_key"]

    second = gate.run_telegram_supervised_sendmessage_dry_run_gate(existing_idempotency_keys={duplicate_key})

    assert second.status == "BLOCKED_DRY_RUN_GATE"
    assert second.idempotency_packet["duplicate"] is True
    assert second.live_gate_packet["live_write_allowed_now"] is False
    assert second.evidence_packet["sendmessage_called"] is False
    assert second.evidence_packet["live_write_performed"] is False
    assert second.evidence_packet["network_request_performed"] is False
