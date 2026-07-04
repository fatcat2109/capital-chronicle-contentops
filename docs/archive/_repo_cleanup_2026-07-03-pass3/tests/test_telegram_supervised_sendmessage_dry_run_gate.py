import json

from live_contentops import telegram_supervised_sendmessage_dry_run_gate as gate


def _json_text(value):
    return json.dumps(value, sort_keys=True)


def test_supervised_sendmessage_dry_run_prep_is_review_blocked_without_live_write():
    result = gate.run_telegram_supervised_sendmessage_dry_run_gate()
    data = result.as_dict()

    assert data["status"] == "PASS_DRY_RUN_PREP_REVIEW_BLOCKED"
    assert data["sendmessage_called"] is False
    assert data["telegram_write_endpoint_called"] is False
    assert data["live_write_performed"] is False
    assert data["network_request_performed"] is False
    assert data["credential_hydrated"] is False
    assert data["dispatchable_now"] is False
    assert data["valid_for_live_dispatch_now"] is False
    assert data["live_gate_packet"]["live_write_allowed_now"] is False
    assert data["live_gate_packet"]["next_gate_required_before_live_send"] is True
    assert data["outbox_packet"]["outbox_status"] == "blocked_pending_operator_approval"
    assert data["outbox_packet"]["dispatchable_now"] is False
    assert data["outbox_packet"]["status"] != "ready_for_mock_dispatch"


def test_approval_requirement_has_no_self_approval_semantics():
    result = gate.run_telegram_supervised_sendmessage_dry_run_gate()
    approval = result.approval_packet

    assert approval["approval_required"] is True
    assert approval["current_operator_approval_present"] is False
    assert approval["approval_status"] == "blocked_pending_operator_approval"
    assert approval["exact_payload_hash_required"] is True
    assert approval["operator_approved_dry_run_payload_hash"] is False
    assert approval["operator_approved_live_send"] is False
    assert approval["valid_for_dispatch"] is False
    assert approval["valid_for_live_dispatch_now"] is False
    assert approval["no_llm_self_approval"] is True
    assert approval["no_implicit_approval_from_readonly_proof"] is True
    assert approval["approval_event"] is None
    assert "approval_event" not in result.outbox_packet or result.outbox_packet.get("approval_event_id") is None


def test_payload_hash_is_deterministic_and_exact_hash_required():
    first = gate.run_telegram_supervised_sendmessage_dry_run_gate()
    second = gate.run_telegram_supervised_sendmessage_dry_run_gate()
    payload_input = dict(first.payload_packet["payload_hash_input"])
    payload_input["payload_id"] = first.payload_packet["payload_id"]

    assert gate.compute_payload_hash(payload_input) == first.hash_packet["payload_hash"]
    assert first.hash_packet["payload_hash"] == second.hash_packet["payload_hash"]
    assert first.hash_packet["payload_hash_short"] == second.hash_packet["payload_hash_short"]
    assert first.hash_packet["exact_payload_hash_required"] is True
    assert first.approval_packet["payload_hash"] == first.hash_packet["payload_hash"]


def test_packet_builder_returns_required_canonical_packet_set():
    packets = gate.build_all_packets()
    assert set(packets) == {
        "sendmessage_dry_run_payload_packet.json",
        "sendmessage_payload_hash_packet.json",
        "sendmessage_approval_requirement_packet.json",
        "sendmessage_outbox_candidate_packet.json",
        "sendmessage_idempotency_packet.json",
        "sendmessage_kill_switch_packet.json",
        "sendmessage_redacted_audit_packet.json",
        "sendmessage_live_gate_packet.json",
        "evidence_packet.json",
    }
    evidence = packets["evidence_packet.json"]
    assert evidence["result_classification"] == "PASS_DRY_RUN_PREP_REVIEW_BLOCKED"
    assert evidence["canonical_packet_files"] == gate.CANONICAL_PACKET_FILES


def test_outbox_review_blocked_contract_fields():
    result = gate.run_telegram_supervised_sendmessage_dry_run_gate()
    outbox = result.outbox_packet

    assert outbox["outbox_status"] == "blocked_pending_operator_approval"
    assert outbox["dispatchable_now"] is False
    assert outbox["dispatch_performed"] is False
    assert outbox["valid_for_live_dispatch_now"] is False
    assert outbox["request_budget"] == 1
    assert outbox["auto_retry_allowed"] is False
    assert outbox["kill_switch_required"] is True
    assert outbox["redacted_audit_required"] is True
    assert outbox["manual_fallback_required"] is True
    assert outbox["exact_payload_hash_required"] is True
    assert "operator_approval_required" in outbox["blocked_reasons"]
    assert "current_operator_approval_missing" in outbox["blocked_reasons"]


def test_evidence_does_not_imply_live_or_dispatch_readiness():
    evidence = gate.run_telegram_supervised_sendmessage_dry_run_gate().evidence_packet

    assert evidence["live_write_allowed_now"] is False
    assert evidence["valid_for_live_dispatch_now"] is False
    assert evidence["dispatchable_now"] is False
    assert evidence["sendmessage_called"] is False
    assert evidence["telegram_write_endpoint_called"] is False
    assert evidence["network_request_performed"] is False
    assert evidence["credential_hydrated"] is False
    assert evidence["operator_approval_required"] is True
    assert evidence["current_operator_approval_present"] is False
    assert evidence["next_gate_required_before_live_send"] is True
    assert evidence["approval_completed"] is False


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
