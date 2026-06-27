import json
from pathlib import Path

from live_contentops import discord_one_action_live_dispatch_closeout as closeout


def write(path: Path, data: dict):
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def gate_packet(**overrides):
    data = {
        "approval_gate_status": "PASS",
        "action_status_from_source": "READY",
        "selected_action_id": closeout.SELECTED_ACTION_ID,
        "selected_target_name": closeout.TARGET_NAME,
        "selected_payload_id": closeout.PAYLOAD_ID,
        "selected_payload_type": closeout.PAYLOAD_TYPE,
        "selected_payload_hash": closeout.PAYLOAD_HASH,
        "destination_binding_id": closeout.DESTINATION_BINDING_ID,
        "credential_handle_id": closeout.CREDENTIAL_HANDLE_ID,
        "env_key_name": closeout.ENV_KEY_NAME,
        "future_live_dispatch_allowed": False,
    }
    data.update(overrides)
    return data


def authorization_packet(**overrides):
    data = {
        "selected_action_id": closeout.SELECTED_ACTION_ID,
        "selected_target_name": closeout.TARGET_NAME,
        "selected_payload_id": closeout.PAYLOAD_ID,
        "selected_payload_type": closeout.PAYLOAD_TYPE,
        "selected_payload_hash": closeout.PAYLOAD_HASH,
        "destination_binding_id": closeout.DESTINATION_BINDING_ID,
        "credential_handle_id": closeout.CREDENTIAL_HANDLE_ID,
        "env_key_name": closeout.ENV_KEY_NAME,
        "current_task_operator_authorization": True,
        "current_task_live_dispatch_allowed": True,
    }
    data.update(overrides)
    return data


def result_packet(**overrides):
    data = {
        "result_status": "PASS",
        "selected_action_id": closeout.SELECTED_ACTION_ID,
        "target_name": closeout.TARGET_NAME,
        "payload_id": closeout.PAYLOAD_ID,
        "payload_type": closeout.PAYLOAD_TYPE,
        "payload_hash": closeout.PAYLOAD_HASH,
        "destination_binding_id": closeout.DESTINATION_BINDING_ID,
        "credential_handle_id": closeout.CREDENTIAL_HANDLE_ID,
        "env_key_name": closeout.ENV_KEY_NAME,
        "http_status_code": 204,
        "status_code_class": "2xx",
        "diagnostic_interpretation": "success_2xx",
        "request_count_attempted": 1,
        "retry_count_attempted": 0,
        "live_write_completed": True,
        "response_body_recorded": False,
        "response_headers_recorded": False,
        "raw_secret_output": False,
        "webhook_url_printed": False,
        "public_url": None,
        "webhook_message_id": None,
    }
    data.update(overrides)
    return data


def make_paths(tmp_path, gate=None, auth=None, result=None):
    g = write(tmp_path / "gate.json", gate or gate_packet())
    a = write(tmp_path / "auth.json", auth or authorization_packet())
    r = write(tmp_path / "result.json", result or result_packet())
    return g, a, r


def packet_for(tmp_path, gate=None, auth=None, result=None):
    g, a, r = make_paths(tmp_path, gate, auth, result)
    return closeout.closeout_packet(operator_gate_packet=g, authorization_packet=a, result_packet=r)


def test_pass_from_valid_gate_authorization_result_packets(tmp_path):
    packet = packet_for(tmp_path)
    assert packet["closeout_status"] == "PASS"
    assert packet["full_supervised_dispatch_chain_verified"] is True


def test_blocked_if_any_required_packet_is_missing(tmp_path):
    packet = closeout.closeout_packet(operator_gate_packet=tmp_path / "missing.json", authorization_packet=tmp_path / "auth.json", result_packet=tmp_path / "result.json")
    assert packet["closeout_status"] == "BLOCKED"


def test_fail_if_selected_action_mismatches(tmp_path):
    assert packet_for(tmp_path, gate=gate_packet(selected_action_id="wrong"))["closeout_status"] == "FAIL"


def test_fail_if_payload_hash_mismatches(tmp_path):
    assert packet_for(tmp_path, result=result_packet(payload_hash="bad"))["closeout_status"] == "FAIL"


def test_fail_if_current_task_operator_authorization_not_true(tmp_path):
    assert packet_for(tmp_path, auth=authorization_packet(current_task_operator_authorization=False))["closeout_status"] == "FAIL"


def test_fail_if_current_task_live_dispatch_allowed_not_true(tmp_path):
    assert packet_for(tmp_path, auth=authorization_packet(current_task_live_dispatch_allowed=False))["closeout_status"] == "FAIL"


def test_fail_if_result_status_not_pass(tmp_path):
    assert packet_for(tmp_path, result=result_packet(result_status="FAIL"))["closeout_status"] == "FAIL"


def test_fail_if_http_status_not_2xx(tmp_path):
    assert packet_for(tmp_path, result=result_packet(http_status_code=403, status_code_class="4xx"))["closeout_status"] == "FAIL"


def test_fail_if_request_count_not_one(tmp_path):
    assert packet_for(tmp_path, result=result_packet(request_count_attempted=0))["closeout_status"] == "FAIL"


def test_fail_if_retry_count_not_zero(tmp_path):
    assert packet_for(tmp_path, result=result_packet(retry_count_attempted=1))["closeout_status"] == "FAIL"


def test_fail_if_live_write_completed_not_true(tmp_path):
    assert packet_for(tmp_path, result=result_packet(live_write_completed=False))["closeout_status"] == "FAIL"


def test_fail_if_response_body_header_recorded(tmp_path):
    assert packet_for(tmp_path, result=result_packet(response_body_recorded=True))["closeout_status"] == "FAIL"
    assert packet_for(tmp_path, result=result_packet(response_headers_recorded=True))["closeout_status"] == "FAIL"


def test_fail_if_webhook_url_printed_true(tmp_path):
    assert packet_for(tmp_path, result=result_packet(webhook_url_printed=True))["closeout_status"] == "FAIL"


def test_packet_marks_no_live_request_in_this_task(tmp_path):
    assert packet_for(tmp_path)["safety"]["no_live_request_in_this_task"] is True


def test_packet_marks_no_env_read_in_this_task(tmp_path):
    assert packet_for(tmp_path)["safety"]["no_env_read_in_this_task"] is True


def test_packet_marks_supervised_live_loop_verified(tmp_path):
    assert packet_for(tmp_path)["readiness_update"]["supervised_live_loop_verified"] is True


def test_packet_marks_next_real_content_requires_real_approved_payload(tmp_path):
    assert packet_for(tmp_path)["readiness_update"]["next_real_content_dispatch_requires_real_approved_payload"] is True


def test_no_network_env_function_exists_or_is_called():
    names = set(dir(closeout))
    assert "urlopen" not in names
    assert "requests" not in names
    assert "environ" not in names
    assert "getenv" not in names
