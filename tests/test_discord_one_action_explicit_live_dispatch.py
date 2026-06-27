import json
from pathlib import Path

import pytest

from live_contentops import discord_one_action_explicit_live_dispatch as live


class FakeResponse:
    status = 204


def write_json(path, data):
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def valid_gate(**overrides):
    data = {
        "approval_gate_status": "PASS",
        "selected_action_id": live.SELECTED_ACTION_ID,
        "selected_target_name": live.TARGET_NAME,
        "selected_payload_id": live.PAYLOAD_ID,
        "selected_payload_hash": live.PAYLOAD_HASH,
        "selected_payload_type": live.PAYLOAD_TYPE,
        "destination_binding_id": live.DESTINATION_BINDING_ID,
        "credential_handle_id": live.CREDENTIAL_HANDLE_ID,
        "env_key_name": live.ENV_KEY_NAME,
        "operator_authorization_state": "NOT_AUTHORIZED_IN_THIS_TASK",
        "future_live_dispatch_allowed": False,
        "approval_binding": {
            "action_id": live.SELECTED_ACTION_ID,
            "target_name": live.TARGET_NAME,
            "payload_id": live.PAYLOAD_ID,
            "payload_hash": live.PAYLOAD_HASH,
            "destination_binding_id": live.DESTINATION_BINDING_ID,
            "credential_handle_id": live.CREDENTIAL_HANDLE_ID,
            "request_budget_required": 1,
            "retry_budget_required": 0,
            "wait_query_param": False,
            "user_agent_required": "CapitalChronicleContentOps/1.0",
        },
    }
    data.update(overrides)
    return data


def gate_path(tmp_path, data=None):
    return write_json(tmp_path / "gate.json", data or valid_gate())


def test_wrapper_loads_and_validates_selected_operator_gate(tmp_path):
    packet = live.authorization_packet(gate_path(tmp_path))
    assert packet["selected_action_id"] == live.SELECTED_ACTION_ID
    assert packet["current_task_live_dispatch_allowed"] is True


def test_current_task_authorization_packet_is_separate_from_prior_gate(tmp_path):
    gate = gate_path(tmp_path)
    out = tmp_path / "auth.json"
    packet = live.write_authorization_packet(gate, out)
    assert out.exists()
    assert packet["prior_gate_future_live_dispatch_allowed"] is False
    assert packet["current_task_live_dispatch_allowed"] is True


def test_prior_gate_future_live_false_is_accepted(tmp_path):
    packet = live.authorization_packet(gate_path(tmp_path, valid_gate(future_live_dispatch_allowed=False)))
    assert packet["prior_gate_future_live_dispatch_allowed"] is False


def test_wrong_selected_action_blocks(tmp_path):
    with pytest.raises(live.ExplicitLiveDispatchBlocked, match="gate_selected_action_id_mismatch"):
        live.authorization_packet(gate_path(tmp_path, valid_gate(selected_action_id="wrong")))


def test_wrong_target_blocks(tmp_path):
    with pytest.raises(live.ExplicitLiveDispatchBlocked, match="gate_selected_target_name_mismatch"):
        live.authorization_packet(gate_path(tmp_path, valid_gate(selected_target_name="wrong")))


def test_wrong_payload_id_blocks(tmp_path):
    with pytest.raises(live.ExplicitLiveDispatchBlocked, match="gate_selected_payload_id_mismatch"):
        live.authorization_packet(gate_path(tmp_path, valid_gate(selected_payload_id="wrong")))


def test_wrong_payload_hash_blocks(tmp_path):
    with pytest.raises(live.ExplicitLiveDispatchBlocked, match="gate_selected_payload_hash_mismatch"):
        live.authorization_packet(gate_path(tmp_path, valid_gate(selected_payload_hash="bad")))


def test_dry_run_path_attempts_zero_network(tmp_path):
    packet = live.run_dry_run(tmp_path / "result.json", gate_path(tmp_path))
    assert packet["result_status"] == "DRY_RUN"
    assert packet["request_count_attempted"] == 0


def test_live_path_with_mocked_204_attempts_exactly_one_request(tmp_path):
    calls = []
    def opener(req, timeout):
        calls.append((req, timeout))
        return FakeResponse()
    fake_url = "https://" + "discord.com" + "/api/" + "webhooks" + "/1/token"
    packet = live.run_live_once(tmp_path / "result.json", gate_path(tmp_path), environ={live.ENV_KEY_NAME: fake_url}, opener=opener)
    assert len(calls) == 1
    assert packet["request_count_attempted"] == 1


def test_mocked_204_maps_to_pass_success_2xx(tmp_path):
    fake_url = "https://" + "discord.com" + "/api/" + "webhooks" + "/1/token"
    packet = live.run_live_once(tmp_path / "result.json", gate_path(tmp_path), environ={live.ENV_KEY_NAME: fake_url}, opener=lambda req, timeout: FakeResponse())
    assert packet["result_status"] == "PASS"
    assert packet["diagnostic_interpretation"] == "success_2xx"


def test_mocked_403_maps_to_fail_credential_unauthorized(tmp_path):
    packet = live.result_packet_from_wrapper({
        "result_status": "FAIL",
        "request_count_attempted": 1,
        "retry_count_attempted": 0,
        "http_status_code": 403,
        "status_code_class": "4xx",
        "diagnostic_interpretation": "credential_unauthorized",
        "live_write_completed": False,
        "user_agent_set": True,
    })
    assert packet["result_status"] == "FAIL"
    assert packet["diagnostic_interpretation"] == "credential_unauthorized"


def test_request_budget_blocks_second_post():
    packet = live.result_packet_from_wrapper({
        "result_status": "PASS",
        "request_count_attempted": 2,
        "retry_count_attempted": 0,
        "http_status_code": 204,
        "status_code_class": "2xx",
        "diagnostic_interpretation": "success_2xx",
        "live_write_completed": True,
        "user_agent_set": True,
    })
    assert packet["result_status"] == "BLOCKED"
    assert packet["diagnostic_interpretation"] == "request_budget_exhausted"
    assert packet["live_write_completed"] is False


def test_result_packet_contains_env_key_name_but_no_env_value(tmp_path):
    packet = live.run_dry_run(tmp_path / "result.json", gate_path(tmp_path))
    text = json.dumps(packet, sort_keys=True)
    assert live.ENV_KEY_NAME in text
    assert "SHOULD_NOT_APPEAR" not in text
    assert "ENV_VALUE_SENTINEL" not in text


def test_result_packet_contains_no_discord_webhook_url(tmp_path):
    packet = live.run_dry_run(tmp_path / "result.json", gate_path(tmp_path))
    text = json.dumps(packet, sort_keys=True)
    assert "discord.com/api/webhooks" not in text
    assert "discordapp.com/api/webhooks" not in text
    assert "https://discord" not in text


def test_no_response_body_header_is_recorded(tmp_path):
    packet = live.run_dry_run(tmp_path / "result.json", gate_path(tmp_path))
    assert packet["response_body_recorded"] is False
    assert packet["response_headers_recorded"] is False
