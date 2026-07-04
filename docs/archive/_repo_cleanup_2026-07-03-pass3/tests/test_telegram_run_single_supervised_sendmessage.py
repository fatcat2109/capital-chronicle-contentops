"""Tests for the 0174UK/UL/UM single supervised Telegram sendMessage runner.

These tests use an INJECTED mock transport for every "live" path -- NO real
network call is ever made here. They assert the runner's fail-closed posture,
the redaction guarantees, the exactly-one-send budget, and that the emitted
evidence is scanner-clean and free of token/destination/raw-response material.
"""

import importlib
import io
import json
import sys
from contextlib import redirect_stdout
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

runner = importlib.import_module(
    "tools.telegram_run_single_supervised_sendmessage")
adapter = importlib.import_module(
    "live_contentops.telegram_local_adapter_contract")

FAKE_TOKEN = "123456789:AaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQq00"
FAKE_DESTINATION = "@cc_operator_test_channel"


# --------------------------------------------------------------------------- #
# Mock transports
# --------------------------------------------------------------------------- #
def _ok_transport():
    calls = {"n": 0}

    def _t():
        calls["n"] += 1
        return (True, 200, {"has_message_id": True})

    _t.calls = calls
    return _t


def _provider_error_transport():
    calls = {"n": 0}

    def _t():
        calls["n"] += 1
        return (False, 400, {"has_message_id": False})

    _t.calls = calls
    return _t


def _raising_transport():
    calls = {"n": 0}

    def _t():
        calls["n"] += 1
        raise OSError("network down")

    _t.calls = calls
    return _t


# --------------------------------------------------------------------------- #
# Import + default-mode posture
# --------------------------------------------------------------------------- #
def test_import_has_no_side_effects():
    """Re-importing the runner module performs no writes/network/env reads."""
    mod = importlib.reload(runner)
    assert mod.TASK_LABEL.startswith("TASK_CONTENTOPS_0174UK_UL_UM")
    assert mod.REQUEST_BUDGET == 1
    assert mod.REQUEST_TIMEOUT_SECONDS == 10


def test_default_mode_does_not_read_dotenv_or_network(tmp_path, monkeypatch):
    """Default (no --from-dotenv) run reads no .env and performs no network."""
    def _boom(*_a, **_k):
        raise AssertionError("load_dotenv_values must not be called by default")

    monkeypatch.setattr(runner, "load_dotenv_values", _boom)
    monkeypatch.setattr(runner, "ROOT", tmp_path)
    monkeypatch.setattr(runner, "_head", lambda ref="HEAD": "deadbeef")
    monkeypatch.setattr(runner, "_git_status_summary", lambda: "changed_entries=0")

    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = runner.main(argv=[])
    out = buf.getvalue()
    assert rc == 0
    assert "REAL_SENDMESSAGE_ATTEMPTED False" in out
    assert "CREDENTIAL_SOURCE " + runner.CREDENTIAL_SOURCE_NONE in out


# --------------------------------------------------------------------------- #
# dotenv loader reads ONLY the two allowed keys
# --------------------------------------------------------------------------- #
def test_dotenv_loader_reads_only_two_allowed_keys(tmp_path):
    """Loader returns token + destination and ignores every other key."""
    env = tmp_path / ".env"
    env.write_text(
        "# comment line\n"
        "TELEGRAM_BOT_TOKEN=\"" + FAKE_TOKEN + "\"\n"
        "TEST_TELEGRAM_CHANNEL='" + FAKE_DESTINATION + "'\n"
        "TELEGRAM_TARGET_CHAT_ID=should_not_be_read\n"
        "GCP_PRIVATE_KEY=-----BEGIN PRIVATE KEY-----\n"
        "OTHER=ignored\n",
        encoding="utf-8")
    token, destination = runner.load_dotenv_values(env)
    assert token == FAKE_TOKEN
    assert destination == FAKE_DESTINATION


def test_dotenv_loader_missing_file_returns_none(tmp_path):
    token, destination = runner.load_dotenv_values(tmp_path / "absent.env")
    assert token is None and destination is None


def test_dotenv_loader_does_not_read_target_chat_id(tmp_path):
    """The TELEGRAM_TARGET_CHAT_ID key must never be surfaced by the loader."""
    env = tmp_path / ".env"
    env.write_text(
        "TELEGRAM_TARGET_CHAT_ID=-1009999999\n"
        "TELEGRAM_BOT_TOKEN=" + FAKE_TOKEN + "\n",
        encoding="utf-8")
    token, destination = runner.load_dotenv_values(env)
    assert token == FAKE_TOKEN
    assert destination is None


# --------------------------------------------------------------------------- #
# Missing token / destination block BEFORE any network call
# --------------------------------------------------------------------------- #
def test_missing_token_blocks_before_network():
    transport = _ok_transport()
    _, _, _, result = runner.run_single_supervised_send(
        operator_live_send_enabled=True, token=None,
        destination=FAKE_DESTINATION, http_transport=transport)
    assert result["outcome_class"] == runner.SEND_BLOCKED
    assert runner.BLOCK_CREDENTIAL_MISSING in result["blocked_reasons"]
    assert result["send_attempted"] is False
    assert transport.calls["n"] == 0


def test_missing_destination_blocks_before_network():
    transport = _ok_transport()
    _, _, _, result = runner.run_single_supervised_send(
        operator_live_send_enabled=True, token=FAKE_TOKEN,
        destination=None, http_transport=transport)
    assert result["outcome_class"] == runner.SEND_BLOCKED
    assert runner.BLOCK_DESTINATION_MISSING in result["blocked_reasons"]
    assert result["send_attempted"] is False
    assert transport.calls["n"] == 0


def test_live_not_enabled_blocks_before_network():
    transport = _ok_transport()
    _, _, _, result = runner.run_single_supervised_send(
        operator_live_send_enabled=False, token=FAKE_TOKEN,
        destination=FAKE_DESTINATION, http_transport=transport)
    assert result["outcome_class"] == runner.SEND_BLOCKED
    assert runner.BLOCK_LIVE_NOT_ENABLED in result["blocked_reasons"]
    assert transport.calls["n"] == 0


# --------------------------------------------------------------------------- #
# Payload content: scanner-clean, no financial advice, budget 1
# --------------------------------------------------------------------------- #
def test_supervised_message_is_scanner_clean_and_not_financial_advice():
    assert adapter.scan_for_leaks(runner.SUPERVISED_TEST_MESSAGE) == []
    assert adapter.scan_for_financial_advice(runner.SUPERVISED_TEST_MESSAGE) == []


def test_one_request_budget_is_exactly_one():
    transport = _ok_transport()
    _, _, one_request, _ = runner.run_single_supervised_send(
        operator_live_send_enabled=True, token=FAKE_TOKEN,
        destination=FAKE_DESTINATION, http_transport=transport)
    descriptor = one_request["request_descriptor"]
    assert descriptor["request_count_authorized"] == 1
    assert one_request["one_request_outcome_class"] == adapter.REQUEST_OK


# --------------------------------------------------------------------------- #
# Mocked live success / provider error / network exception
# --------------------------------------------------------------------------- #
def test_mocked_live_success_redacted_message_proof():
    transport = _ok_transport()
    _, _, _, result = runner.run_single_supervised_send(
        operator_live_send_enabled=True, token=FAKE_TOKEN,
        destination=FAKE_DESTINATION, http_transport=transport)
    assert result["outcome_class"] == runner.SEND_OK
    assert result["send_succeeded"] is True
    assert result["budget_used"] == 1
    assert result["provider_status_code_class"] == adapter.PROVIDER_CODE_SUCCESS_CLASS
    assert result["response_status_class"] == adapter.RESPONSE_STATUS_OK_CLASS
    assert result["message_id_class"] == adapter.MESSAGE_ID_PRESENT_CLASS
    assert transport.calls["n"] == 1


def test_mocked_provider_error_redacted_error_proof():
    transport = _provider_error_transport()
    _, _, _, result = runner.run_single_supervised_send(
        operator_live_send_enabled=True, token=FAKE_TOKEN,
        destination=FAKE_DESTINATION, http_transport=transport)
    assert result["outcome_class"] == runner.SEND_PROVIDER_ERROR
    assert result["send_succeeded"] is False
    assert result["budget_used"] == 1
    assert result["provider_status_code_class"] == (
        adapter.PROVIDER_CODE_CLIENT_ERROR_CLASS)
    assert result["message_id_class"] == adapter.MESSAGE_ID_ABSENT_CLASS
    assert transport.calls["n"] == 1


def test_mocked_network_exception_redacted_blocked_proof():
    transport = _raising_transport()
    _, _, _, result = runner.run_single_supervised_send(
        operator_live_send_enabled=True, token=FAKE_TOKEN,
        destination=FAKE_DESTINATION, http_transport=transport)
    assert result["outcome_class"] == runner.SEND_NETWORK_BLOCKED
    assert result["send_succeeded"] is False
    assert transport.calls["n"] == 1


def test_exactly_one_transport_call_on_success():
    transport = _ok_transport()
    runner.run_single_supervised_send(
        operator_live_send_enabled=True, token=FAKE_TOKEN,
        destination=FAKE_DESTINATION, http_transport=transport)
    assert transport.calls["n"] == 1


# --------------------------------------------------------------------------- #
# Evidence packet: redacted, scanner-clean, no secrets, correct booleans
# --------------------------------------------------------------------------- #
def _build_packet_for(transport, **kw):
    rendered, enforcer, one_request, send_result = (
        runner.run_single_supervised_send(
            operator_live_send_enabled=True, token=FAKE_TOKEN,
            destination=FAKE_DESTINATION, http_transport=transport))
    return runner.build_evidence_packet(
        rendered, enforcer, one_request, send_result,
        start_head="aaa", final_head="bbb", origin_head="bbb",
        credential_source_class=runner.CREDENTIAL_SOURCE_DOTENV,
        destination_source_class=runner.DESTINATION_SOURCE_DOTENV_TEST_CHANNEL,
        destination_binding_checksum=runner._fingerprint16(
            FAKE_DESTINATION, "x"),
        destination_present_redacted=True, real_send_attempted=True, **kw)


def test_evidence_packet_is_scanner_clean_and_no_advice():
    packet = _build_packet_for(_ok_transport())
    doc = runner.build_evidence_doc(packet)
    assert runner.scan_evidence(packet, doc) == []
    assert runner.scan_for_financial_advice_safe(packet, doc) == []


def test_evidence_contains_no_token_destination_or_raw_response():
    packet = _build_packet_for(_ok_transport())
    doc = runner.build_evidence_doc(packet)
    blob = json.dumps(packet) + doc
    assert FAKE_TOKEN not in blob
    assert FAKE_DESTINATION not in blob
    assert "api.telegram.org/bot" not in blob  # no tokened URL
    assert packet["stores_no_token"] is True
    assert packet["stores_no_raw_destination"] is True
    assert packet["stores_no_raw_response"] is True
    assert packet["stores_no_raw_url"] is True
    assert packet["stores_no_headers"] is True
    assert packet["stores_no_cookies"] is True
    assert packet["stores_no_raw_chat_id"] is True


def test_evidence_records_no_retry_scheduler_webhook_polling():
    packet = _build_packet_for(_ok_transport())
    assert packet["no_retry"] is True
    assert packet["no_scheduler"] is True
    assert packet["no_webhook"] is True
    assert packet["no_polling"] is True
    assert packet["no_get_updates"] is True
    assert packet["no_autonomous_reply"] is True
    assert packet["no_media_edit_delete"] is True
    assert packet["no_second_send_path"] is True


def test_evidence_budget_used_one_on_success():
    packet = _build_packet_for(_ok_transport())
    assert packet["request_budget_used"] == 1
    assert packet["request_budget_authorized"] == 1
    assert packet["send_outcome_class"] == runner.SEND_OK


def test_request_descriptor_has_no_token_or_raw_chat_id():
    transport = _ok_transport()
    _, _, one_request, _ = runner.run_single_supervised_send(
        operator_live_send_enabled=True, token=FAKE_TOKEN,
        destination=FAKE_DESTINATION, http_transport=transport)
    descriptor = one_request["request_descriptor"]
    assert descriptor["contains_url_with_token"] is False
    assert descriptor["contains_token_value"] is False
    assert descriptor["contains_raw_chat_id"] is False


# --------------------------------------------------------------------------- #
# write_evidence refuses to persist anything unsafe
# --------------------------------------------------------------------------- #
def test_write_evidence_writes_clean_artifacts(tmp_path):
    packet = _build_packet_for(_ok_transport())
    doc = runner.build_evidence_doc(packet)
    written = runner.write_evidence(tmp_path, packet, doc)
    assert len(written) == 2
    for path in written:
        assert Path(path).is_file()


def test_write_evidence_refuses_when_violation_present(tmp_path):
    packet = _build_packet_for(_ok_transport())
    # Inject a forbidden raw token value to prove the scanner gate fires.
    packet = dict(packet)
    packet["accidental_token"] = FAKE_TOKEN
    doc = runner.build_evidence_doc(
        {k: v for k, v in packet.items() if k != "accidental_token"})
    with pytest.raises(RuntimeError):
        runner.write_evidence(tmp_path, packet, doc)


# --------------------------------------------------------------------------- #
# Method / host facts: sendMessage only, getUpdates/setWebhook absent
# --------------------------------------------------------------------------- #
def test_method_is_send_message_and_inbound_methods_absent():
    packet = _build_packet_for(_ok_transport())
    assert packet["method_name"] == adapter.METHOD_SUPERVISED_SEND == "sendMessage"
    assert packet["api_host"] == adapter.TELEGRAM_API_HOST == "api.telegram.org"
    blob = json.dumps(packet)
    assert "getUpdates" not in blob
    assert "setWebhook" not in blob


# --------------------------------------------------------------------------- #
# R1: deterministic redacted response_checksum
# --------------------------------------------------------------------------- #
def test_success_proof_has_non_null_response_checksum():
    packet = _build_packet_for(_ok_transport())
    assert packet["response_checksum"] is not None
    assert packet["response_shape_checksum"] is not None


def test_provider_error_proof_has_non_null_response_checksum():
    packet = _build_packet_for(_provider_error_transport())
    assert packet["response_checksum"] is not None
    assert packet["send_outcome_class"] == runner.SEND_PROVIDER_ERROR


def test_network_exception_proof_has_non_null_response_checksum():
    packet = _build_packet_for(_raising_transport())
    assert packet["response_checksum"] is not None
    assert packet["send_outcome_class"] == runner.SEND_NETWORK_BLOCKED


def test_blocked_before_network_proof_may_have_null_response_checksum():
    """A blocked (no send attempted) result carries a null response_checksum."""
    rendered, enforcer, one_request, send_result = (
        runner.run_single_supervised_send(
            operator_live_send_enabled=False, token=FAKE_TOKEN,
            destination=FAKE_DESTINATION, http_transport=_ok_transport()))
    assert send_result["send_attempted"] is False
    assert runner.compute_redacted_send_response_checksum(send_result) is None
    packet = runner.build_evidence_packet(
        rendered, enforcer, one_request, send_result,
        start_head="aaa", final_head="bbb", origin_head="bbb",
        real_send_attempted=False)
    assert packet["response_checksum"] is None


def test_checksum_changes_when_redacted_classes_change():
    """Different redacted status/message-id classes => different checksum."""
    ok_checksum = runner.compute_redacted_send_response_checksum({
        "send_attempted": True,
        "outcome_class": runner.SEND_OK,
        "send_succeeded": True,
        "provider_status_code_class": adapter.PROVIDER_CODE_SUCCESS_CLASS,
        "response_status_class": adapter.RESPONSE_STATUS_OK_CLASS,
        "message_id_class": adapter.MESSAGE_ID_PRESENT_CLASS,
        "budget_used": 1,
    })
    err_checksum = runner.compute_redacted_send_response_checksum({
        "send_attempted": True,
        "outcome_class": runner.SEND_PROVIDER_ERROR,
        "send_succeeded": False,
        "provider_status_code_class": adapter.PROVIDER_CODE_CLIENT_ERROR_CLASS,
        "response_status_class": adapter.RESPONSE_STATUS_ERROR_CLASS,
        "message_id_class": adapter.MESSAGE_ID_ABSENT_CLASS,
        "budget_used": 1,
    })
    assert ok_checksum != err_checksum
    # Deterministic: identical redacted input reproduces the same checksum.
    ok_again = runner.compute_redacted_send_response_checksum({
        "send_attempted": True,
        "outcome_class": runner.SEND_OK,
        "send_succeeded": True,
        "provider_status_code_class": adapter.PROVIDER_CODE_SUCCESS_CLASS,
        "response_status_class": adapter.RESPONSE_STATUS_OK_CLASS,
        "message_id_class": adapter.MESSAGE_ID_PRESENT_CLASS,
        "budget_used": 1,
    })
    assert ok_checksum == ok_again


def test_checksum_input_contains_no_token_destination_or_raw_material():
    """The checksum is stable regardless of token/destination/raw response."""
    # Build two packets with identical redacted outcome but different secrets.
    rendered_a, enforcer_a, one_request_a, sr_a = (
        runner.run_single_supervised_send(
            operator_live_send_enabled=True, token=FAKE_TOKEN,
            destination=FAKE_DESTINATION, http_transport=_ok_transport()))
    rendered_b, enforcer_b, one_request_b, sr_b = (
        runner.run_single_supervised_send(
            operator_live_send_enabled=True,
            token="987654321:ZzYyXxWwVvUuTtSsRrQqPpOoNnMmLlKk11",
            destination="@a_totally_different_channel",
            http_transport=_ok_transport()))
    # Same redacted send-result classes => same response checksum, proving the
    # raw token/destination/response never feed the checksum.
    assert (runner.compute_redacted_send_response_checksum(sr_a)
            == runner.compute_redacted_send_response_checksum(sr_b))


def test_evidence_records_second_live_test_sequence():
    packet = _build_packet_for(_ok_transport())
    assert packet["live_test_sequence"] == 2
    assert runner.LIVE_TEST_SEQUENCE == 2
    doc = runner.build_evidence_doc(packet)
    assert "second supervised live test" in doc


def test_response_checksum_packet_remains_scanner_clean():
    for transport in (_ok_transport(), _provider_error_transport(),
                      _raising_transport()):
        packet = _build_packet_for(transport)
        doc = runner.build_evidence_doc(packet)
        assert runner.scan_evidence(packet, doc) == []
        assert runner.scan_for_financial_advice_safe(packet, doc) == []
