import json
from pathlib import Path

from live_contentops import discord_operator_approval_gate as gate


def write_json(path, data):
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def valid_action(**overrides):
    data = {
        "action_id": "discord_supervised_dispatch_action_announcements",
        "action_status": "READY",
        "target_name": "announcements",
        "payload_id": "discord_dryrun_announcement_001",
        "payload_type": "announcement",
        "payload_hash": "b166aebf1f53956f04ffa5122d6d065fc09e4f7953ec816e1b0b66a01be9d17d",
        "env_key_name": "DISCORD_ANNOUNCEMENTS_WEBHOOK_URL",
        "destination_binding_id": "discord_announcements_capital_chronicle_01",
        "credential_handle_id": "discord_announcements_webhook_01",
        "readiness_verified": True,
        "payload_hash_verified": True,
        "operator_authorization_required": True,
        "live_command_preview_redacted": "python -m live_contentops.discord_approved_outbox_live_dispatch --target announcements --payload-id discord_dryrun_announcement_001 --execute --output docs/automation/DISCORD_SUPERVISED_DISPATCH_ACTIONS/live_results/announcements_result_packet.json",
        "request_budget_required": 1,
        "retry_budget_required": 0,
        "wait_query_param": False,
        "user_agent_required": "CapitalChronicleContentOps/1.0",
    }
    data.update(overrides)
    return data


def valid_actions_packet(action=None):
    return {
        "action_materialization_status": "PASS",
        "supervised_dispatch_actions_ready": True,
        "actions": [action or valid_action()],
    }


def generate(tmp_path, packet=None, action_id="discord_supervised_dispatch_action_announcements"):
    source = write_json(tmp_path / "actions.json", packet or valid_actions_packet())
    return gate.generate_from_files(actions_packet=source, action_id=action_id, output=tmp_path / "gate.json")


def test_pass_from_valid_selected_action(tmp_path):
    packet = generate(tmp_path)
    assert packet["approval_gate_status"] == "PASS"
    assert packet["selected_action_id"] == "discord_supervised_dispatch_action_announcements"


def test_blocked_if_actions_packet_missing(tmp_path):
    packet = gate.generate_from_files(actions_packet=tmp_path / "missing.json", action_id="discord_supervised_dispatch_action_announcements", output=tmp_path / "gate.json")
    assert packet["approval_gate_status"] == "BLOCKED"
    assert "actions_packet_missing_or_unreadable" in packet["blocker"]


def test_fail_if_selected_action_missing(tmp_path):
    packet = generate(tmp_path, valid_actions_packet(), action_id="missing_action")
    assert packet["approval_gate_status"] == "FAIL"
    assert packet["failure_reason"] == "selected_action_missing"


def test_fail_if_action_status_not_ready(tmp_path):
    packet = generate(tmp_path, valid_actions_packet(valid_action(action_status="BLOCKED")))
    assert packet["failure_reason"] == "action_status_not_ready"


def test_fail_if_readiness_verified_false(tmp_path):
    packet = generate(tmp_path, valid_actions_packet(valid_action(readiness_verified=False)))
    assert packet["failure_reason"] == "readiness_verified_false"


def test_fail_if_payload_hash_verified_false(tmp_path):
    packet = generate(tmp_path, valid_actions_packet(valid_action(payload_hash_verified=False)))
    assert packet["failure_reason"] == "payload_hash_verified_false"


def test_fail_if_operator_authorization_required_false(tmp_path):
    packet = generate(tmp_path, valid_actions_packet(valid_action(operator_authorization_required=False)))
    assert packet["failure_reason"] == "operator_authorization_required_false"


def test_fail_if_request_budget_not_1(tmp_path):
    packet = generate(tmp_path, valid_actions_packet(valid_action(request_budget_required=2)))
    assert packet["failure_reason"] == "request_budget_required_not_1"


def test_fail_if_retry_budget_not_0(tmp_path):
    packet = generate(tmp_path, valid_actions_packet(valid_action(retry_budget_required=1)))
    assert packet["failure_reason"] == "retry_budget_required_not_0"


def test_packet_has_future_live_dispatch_allowed_false(tmp_path):
    packet = generate(tmp_path)
    assert packet["future_live_dispatch_allowed"] is False


def test_packet_has_not_authorized_state(tmp_path):
    packet = generate(tmp_path)
    assert packet["operator_authorization_state"] == "NOT_AUTHORIZED_IN_THIS_TASK"


def test_command_preview_preserved_but_not_executed(tmp_path):
    packet = generate(tmp_path)
    assert "--execute" in packet["command_preview_redacted"]
    assert packet["no_live_request_in_this_task"] is True
    assert packet["future_live_dispatch_allowed"] is False


def test_packet_contains_env_key_name_but_no_env_value(tmp_path):
    packet = generate(tmp_path)
    text = json.dumps(packet, sort_keys=True)
    assert "DISCORD_ANNOUNCEMENTS_WEBHOOK_URL" in text
    assert "VtmHv" not in text
    assert "0Sd7p" not in text


def test_packet_contains_no_webhook_url(tmp_path):
    packet = generate(tmp_path)
    text = json.dumps(packet, sort_keys=True)
    assert "discord.com/api/webhooks" not in text
    assert "discordapp.com/api/webhooks" not in text
    assert "https://discord" not in text


def test_panel_contains_selected_action_and_no_active_live_button(tmp_path):
    generate(tmp_path)
    panel = (tmp_path / gate.PANEL_FILENAME).read_text(encoding="utf-8")
    assert "discord_supervised_dispatch_action_announcements" in panel
    assert "NOT_AUTHORIZED_IN_THIS_TASK" in panel
    assert "Live controls absent" in panel
    assert "button { display:none; }" in panel


def test_no_network_env_function_exists_or_is_called():
    module_text = Path(gate.__file__).read_text(encoding="utf-8")
    forbidden = ["urlopen", "Request(", "fetch(", "XMLHttpRequest", "sendBeacon", "__import__(\"os\")", "environ", "getenv"]
    assert all(token not in module_text for token in forbidden)
