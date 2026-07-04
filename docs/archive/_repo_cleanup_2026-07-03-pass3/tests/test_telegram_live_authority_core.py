import pytest

from live_contentops import telegram_live_authority_core as core


def test_payload_hash_stable_for_same_payload():
    assert core.compute_payload_hash() == core.compute_payload_hash()


def test_payload_hash_changes_when_text_changes():
    assert core.compute_payload_hash("changed") != core.compute_payload_hash()


def test_payload_hash_changes_when_destination_binding_changes():
    assert core.compute_payload_hash(destination_binding_id="other_binding") != core.compute_payload_hash()


def test_payload_hash_changes_when_credential_handle_changes():
    assert core.compute_payload_hash(credential_handle_id="other_credential") != core.compute_payload_hash()


def test_token_shaped_payload_blocks():
    with pytest.raises(ValueError):
        core.compute_payload_hash("123456:abcdefghijklmnopqrstuvwxyzABCDEF")


def test_only_sendmessage_allowed_write_method():
    packet = core.build_payload_packet()
    assert packet["method"] == "sendMessage"
    with pytest.raises(ValueError):
        core.build_payload_packet(method="sendPhoto")
    with pytest.raises(ValueError):
        core.build_payload_packet(method="sendDocument")
    with pytest.raises(ValueError):
        core.build_payload_packet(method="sendRichMessage")


def test_approval_outbox_audit_are_redacted():
    packet = core.build_payload_packet()
    approval = core.build_approval_event(packet)
    outbox = core.build_outbox_candidate(packet, approval)
    kill = core.classify_kill_switch(None)
    idem = {"idempotency_state": "no_prior_success_or_unknown"}
    probes = {"getMe": {"request_count": 1}, "getChat": {"request_count": 1}}
    send = {"request_count": 1, "result_classification": "live_send_success"}
    audit = core.build_redacted_audit_event(packet, approval, outbox, kill, idem, probes, send, {"raw_values_persisted": False})
    assert audit["raw_request_persisted"] is False
    assert audit["raw_response_persisted"] is False
    assert audit["no_retry_performed"] is True
    assert audit["no_second_send_performed"] is True
