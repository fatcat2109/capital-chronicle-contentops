import json

from live_contentops import telegram_supervised_sendmessage_dry_run_gate as gate


def _json_text(value):
    return json.dumps(value, sort_keys=True)


def test_supervised_sendmessage_dry_run_gate_passes_without_live_write():
    result = gate.run_telegram_supervised_sendmessage_dry_run_gate()
    data = result.as_dict()

    assert data["status"] == "PASS_DRY_RUN_GATE"
    assert data["blocked_reasons"] == []
    assert data["sendmessage_called"] is False
    assert data["live_write_performed"] is False
    assert data["network_request_performed"] is False
    assert data["credential_hydrated"] is False
    assert data["valid_for_live_dispatch_now"] is False
    assert data["live_gate_packet"]["live_write_allowed_now"] is False
    assert data["live_gate_packet"]["next_gate_required_before_live_send"] is True
    assert data["outbox_packet"]["status"] == "ready_for_mock_dispatch"
    assert data["idempotency_packet"]["status"] == "new_key_allowed_for_local_outbox_only"


def test_payload_hash_and_approval_are_deterministic_and_bound():
    result = gate.run_telegram_supervised_sendmessage_dry_run_gate()
    payload_packet = result.payload_packet
    hash_packet = result.hash_packet
    approval_event = result.approval_packet["approval_event"]

    payload_input = dict(payload_packet["payload_hash_input"])
    payload_input["payload_id"] = payload_packet["payload_id"]
    assert gate.compute_payload_hash(payload_input) == hash_packet["payload_hash"]
    assert approval_event["payload_hash"] == hash_packet["payload_hash"]
    assert approval_event["valid_for_dispatch"] is True
    assert approval_event["valid_for_live_dispatch_now"] is False
    assert result.evidence_packet["operator_approved_live_send"] is False


def test_packet_builder_returns_required_packet_set():
    packets = gate.build_all_packets()
    assert set(packets) == {
        "payload_packet.json",
        "payload_hash_packet.json",
        "approval_packet.json",
        "outbox_candidate_packet.json",
        "idempotency_packet.json",
        "kill_switch_packet.json",
        "redacted_audit_packet.json",
        "live_gate_packet.json",
        "evidence_packet.json",
    }
    assert packets["evidence_packet.json"]["result_classification"] == "PASS_DRY_RUN_GATE"


def test_packets_do_not_contain_telegram_secret_shapes_or_raw_request_fields():
    result = gate.run_telegram_supervised_sendmessage_dry_run_gate()
    data = result.as_dict()
    text = _json_text(data)

    forbidden_fragments = [
        "https://api.telegram.org/",
        "sendMessage?",
        "Authorization",
        "Bearer ",
    ]
    for fragment in forbidden_fragments:
        assert fragment not in text

    assert gate.scan_packet_for_telegram_secret_risk(data) == []
    assert "DRY_RUN_NOT_FOR_LIVE_SEND" in text


def test_forbidden_advice_language_blocks_payload_validation():
    payload_packet = gate.build_telegram_sendmessage_dry_run_payload()
    payload_packet["payload_hash_input"]["payload_text"] += " Buy now for guaranteed profit."

    validation = gate.validate_telegram_sendmessage_payload(payload_packet)

    assert validation["valid"] is False
    assert "forbidden_text:buy" in validation["blocked_reasons"]
    assert "forbidden_text:guaranteed" in validation["blocked_reasons"]
    assert "forbidden_text:profit" in validation["blocked_reasons"]


