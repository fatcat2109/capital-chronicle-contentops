import json
from pathlib import Path

from live_contentops import discord_supervised_dispatch_actions as actions


def write_json(path, data):
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def readiness_target(target_name, payload_id, payload_type, payload_hash, env_key, **overrides):
    data = {
        "allowed_payload_type": payload_type,
        "env_key_name": env_key,
        "last_dispatch_result": "PASS",
        "last_http_status_code": 204,
        "payload_hash": payload_hash,
        "payload_id": payload_id,
        "ready_for_supervised_dispatch": True,
    }
    data.update(overrides)
    return data


def valid_packets():
    hashes = {
        "announcements": "b166aebf1f53956f04ffa5122d6d065fc09e4f7953ec816e1b0b66a01be9d17d",
        "substack_drops": "a084ced7249d9b764132e17888c15c5cfd6177329dbe5ce718311e07e849175d",
        "product_updates": "81075439dcafcdc979482d51dd56ce7cb0a704827a9fbe702a2994b3f329efdd",
    }
    payload_ids = {
        "announcements": "discord_dryrun_announcement_001",
        "substack_drops": "discord_dryrun_substack_drop_001",
        "product_updates": "discord_dryrun_product_update_001",
    }
    payload_types = {
        "announcements": "announcement",
        "substack_drops": "substack_drop",
        "product_updates": "product_update",
    }
    env_keys = {
        "announcements": "DISCORD_ANNOUNCEMENTS_WEBHOOK_URL",
        "substack_drops": "DISCORD_SUBSTACK_DROPS_WEBHOOK_URL",
        "product_updates": "DISCORD_PRODUCT_UPDATES_WEBHOOK_URL",
    }
    dest = {
        "announcements": "discord_announcements_capital_chronicle_01",
        "substack_drops": "discord_substack_drops_capital_chronicle_01",
        "product_updates": "discord_product_updates_capital_chronicle_01",
    }
    cred = {
        "announcements": "discord_announcements_webhook_01",
        "substack_drops": "discord_substack_drops_webhook_01",
        "product_updates": "discord_product_updates_webhook_01",
    }
    readiness = {
        "readiness_status": "PASS",
        "supervised_discord_dispatch_ready": True,
        "verified_targets": {
            target: readiness_target(target, payload_ids[target], payload_types[target], hashes[target], env_keys[target])
            for target in actions.TARGET_ORDER
        },
    }
    payload_packet = {"payloads": [
        {
            "payload_id": payload_ids[target],
            "payload_type": payload_types[target],
            "target_name": target,
            "destination_binding_id": dest[target],
            "credential_handle_id": cred[target],
        }
        for target in actions.TARGET_ORDER
    ]}
    hash_packet = {"approval_packets": [
        {
            "payload_id": payload_ids[target],
            "payload_type": payload_types[target],
            "target_name": target,
            "payload_hash": hashes[target],
            "destination_binding_id": dest[target],
            "credential_handle_id": cred[target],
        }
        for target in actions.TARGET_ORDER
    ]}
    return readiness, payload_packet, hash_packet


def generate(tmp_path, readiness=None, payload_packet=None, hash_packet=None):
    default_r, default_p, default_h = valid_packets()
    r = write_json(tmp_path / "readiness.json", readiness or default_r)
    p = write_json(tmp_path / "payloads.json", payload_packet or default_p)
    h = write_json(tmp_path / "hashes.json", hash_packet or default_h)
    return actions.generate_from_files(readiness_packet=r, payload_packet=p, hash_packet=h, output=tmp_path / "actions.json")


def test_pass_from_valid_readiness_payload_and_hash_packets(tmp_path):
    packet = generate(tmp_path)
    assert packet["action_materialization_status"] == "PASS"
    assert packet["supervised_dispatch_actions_ready"] is True


def test_blocked_if_readiness_packet_missing(tmp_path):
    _, p, h = valid_packets()
    payload = write_json(tmp_path / "payloads.json", p)
    hashes = write_json(tmp_path / "hashes.json", h)
    packet = actions.generate_from_files(readiness_packet=tmp_path / "missing.json", payload_packet=payload, hash_packet=hashes, output=tmp_path / "actions.json")
    assert packet["action_materialization_status"] == "BLOCKED"
    assert "required_input_packet_missing_or_unreadable" in packet["blocker"]


def test_fail_if_supervised_discord_dispatch_ready_false(tmp_path):
    r, p, h = valid_packets()
    r["supervised_discord_dispatch_ready"] = False
    packet = generate(tmp_path, r, p, h)
    assert packet["action_materialization_status"] == "FAIL"
    assert packet["failure_reason"] == "supervised_discord_dispatch_ready_false"


def test_fail_if_target_not_ready(tmp_path):
    r, p, h = valid_packets()
    r["verified_targets"]["product_updates"]["ready_for_supervised_dispatch"] = False
    packet = generate(tmp_path, r, p, h)
    assert packet["action_materialization_status"] == "FAIL"
    assert packet["failure_reason"] == "product_updates_not_ready"


def test_fail_if_payload_hash_missing_from_hash_packet(tmp_path):
    r, p, h = valid_packets()
    h["approval_packets"] = h["approval_packets"][:2]
    packet = generate(tmp_path, r, p, h)
    assert packet["action_materialization_status"] == "FAIL"
    assert packet["failure_reason"] == "product_updates_payload_hash_missing"


def test_fail_if_payload_id_target_mismatch(tmp_path):
    r, p, h = valid_packets()
    p["payloads"][0]["target_name"] = "wrong_target"
    packet = generate(tmp_path, r, p, h)
    assert packet["action_materialization_status"] == "FAIL"
    assert packet["failure_reason"] == "announcements_payload_target_mismatch"


def test_exactly_three_actions_generated(tmp_path):
    packet = generate(tmp_path)
    assert packet["action_count"] == 3
    assert [a["target_name"] for a in packet["actions"]] == list(actions.TARGET_ORDER)


def test_every_action_requires_operator_authorization(tmp_path):
    packet = generate(tmp_path)
    assert all(a["operator_authorization_required"] is True for a in packet["actions"])


def test_every_action_has_request_and_retry_budget(tmp_path):
    packet = generate(tmp_path)
    assert all(a["request_budget_required"] == 1 for a in packet["actions"])
    assert all(a["retry_budget_required"] == 0 for a in packet["actions"])


def test_command_preview_includes_execute_but_is_not_executed(tmp_path):
    packet = generate(tmp_path)
    commands = [a["live_command_preview_redacted"] for a in packet["actions"]]
    assert all(" --execute " in c for c in commands)
    assert all(c.startswith("python -m live_contentops.discord_approved_outbox_live_dispatch") for c in commands)
    assert packet["no_live_request_in_this_task"] is True


def test_command_preview_contains_no_webhook_url(tmp_path):
    packet = generate(tmp_path)
    text = json.dumps(packet, sort_keys=True)
    assert "discord.com/api/webhooks" not in text
    assert "discordapp.com/api/webhooks" not in text
    assert "https://discord" not in text


def test_packet_contains_env_key_names_but_no_env_values(tmp_path):
    packet = generate(tmp_path)
    text = json.dumps(packet, sort_keys=True)
    assert "DISCORD_ANNOUNCEMENTS_WEBHOOK_URL" in text
    assert "DISCORD_SUBSTACK_DROPS_WEBHOOK_URL" in text
    assert "DISCORD_PRODUCT_UPDATES_WEBHOOK_URL" in text
    assert "VtmHv" not in text
    assert "0Sd7p" not in text


def test_packet_marks_no_live_request_and_no_env_read(tmp_path):
    packet = generate(tmp_path)
    assert packet["no_live_request_in_this_task"] is True
    assert packet["no_env_read_in_this_task"] is True
    assert packet["raw_secret_output"] is False


def test_no_network_function_exists_or_is_called():
    module_text = Path(actions.__file__).read_text(encoding="utf-8")
    forbidden = ["urlopen", "Request(", "fetch(", "XMLHttpRequest", "sendBeacon", "__import__(\"os\")", "environ", "getenv"]
    assert all(token not in module_text for token in forbidden)


def test_html_panel_contains_all_three_targets(tmp_path):
    generate(tmp_path)
    panel = (tmp_path / actions.PANEL_FILENAME).read_text(encoding="utf-8")
    assert "announcements" in panel
    assert "substack_drops" in panel
    assert "product_updates" in panel
    assert "3 ready actions" in panel


def test_html_panel_has_disabled_or_absent_live_controls(tmp_path):
    generate(tmp_path)
    panel = (tmp_path / actions.PANEL_FILENAME).read_text(encoding="utf-8")
    assert "button { display:none; }" in panel
    assert "Live controls absent" in panel
    assert "discord.com/api/webhooks" not in panel
