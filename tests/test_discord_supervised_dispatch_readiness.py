import json
from pathlib import Path

from live_contentops import discord_supervised_dispatch_readiness as readiness


def target_packet(target_name, **overrides):
    spec = readiness.TARGET_SPECS[target_name]
    data = {
        "adapter_dispatch_verified": True,
        "diagnostic_interpretation": "success_2xx",
        "http_status_code": 204,
        "payload_hash": spec.payload_hash,
        "payload_id": spec.payload_id,
        "ready_for_supervised_dispatch": True,
        "request_count_attempted": 1,
        "result_status": "PASS",
        "retry_count_attempted": 0,
        "status_code_class": "2xx",
    }
    data.update(overrides)
    return data


def valid_closeout(**summary_overrides):
    summary = {
        "all_targets_adapter_dispatch_verified": True,
        "remaining_discord_dispatch_pilots": 0,
        "supervised_discord_dispatch_ready": True,
        "verified_target_count": 3,
    }
    summary.update(summary_overrides)
    return {
        "closeout_status": "PASS",
        "readiness_summary": summary,
        "verified_targets": {
            "announcements": target_packet("announcements"),
            "substack_drops": target_packet("substack_drops"),
            "product_updates": target_packet("product_updates"),
        },
    }


def write_json(path, data):
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_pass_from_valid_tri_target_closeout_packet(tmp_path):
    source = write_json(tmp_path / "closeout.json", valid_closeout())
    packet = readiness.generate_from_files(tri_target_closeout=source, output=tmp_path / "packet.json")
    assert packet["readiness_status"] == "PASS"
    assert packet["supervised_discord_dispatch_ready"] is True


def test_blocked_if_tri_target_closeout_missing(tmp_path):
    packet = readiness.generate_from_files(tri_target_closeout=tmp_path / "missing.json", output=tmp_path / "packet.json")
    assert packet["readiness_status"] == "BLOCKED"
    assert "tri_target_closeout_missing_or_unreadable" in packet["blocker"]


def test_fail_if_supervised_discord_dispatch_ready_false(tmp_path):
    source = write_json(tmp_path / "closeout.json", valid_closeout(supervised_discord_dispatch_ready=False))
    packet = readiness.generate_from_files(tri_target_closeout=source, output=tmp_path / "packet.json")
    assert packet["readiness_status"] == "FAIL"
    assert packet["failure_reason"] == "supervised_discord_dispatch_ready_false"


def test_fail_if_verified_target_count_not_3(tmp_path):
    source = write_json(tmp_path / "closeout.json", valid_closeout(verified_target_count=2))
    packet = readiness.generate_from_files(tri_target_closeout=source, output=tmp_path / "packet.json")
    assert packet["readiness_status"] == "FAIL"
    assert packet["failure_reason"] == "verified_target_count_not_3"


def test_fail_if_any_target_not_ready_for_supervised_dispatch(tmp_path):
    data = valid_closeout()
    data["verified_targets"]["product_updates"]["ready_for_supervised_dispatch"] = False
    source = write_json(tmp_path / "closeout.json", data)
    packet = readiness.generate_from_files(tri_target_closeout=source, output=tmp_path / "packet.json")
    assert packet["readiness_status"] == "FAIL"
    assert packet["failure_reason"] == "product_updates_not_ready_for_supervised_dispatch"


def test_packet_includes_all_three_env_key_names_but_no_env_values(tmp_path):
    source = write_json(tmp_path / "closeout.json", valid_closeout())
    packet = readiness.generate_from_files(tri_target_closeout=source, output=tmp_path / "packet.json")
    env_keys = {target["env_key_name"] for target in packet["verified_targets"].values()}
    assert env_keys == {
        "DISCORD_ANNOUNCEMENTS_WEBHOOK_URL",
        "DISCORD_SUBSTACK_DROPS_WEBHOOK_URL",
        "DISCORD_PRODUCT_UPDATES_WEBHOOK_URL",
    }
    text = json.dumps(packet, sort_keys=True)
    assert "discord.com/api/webhooks" not in text
    assert "discordapp.com/api/webhooks" not in text


def test_packet_marks_no_live_request_and_no_env_read(tmp_path):
    source = write_json(tmp_path / "closeout.json", valid_closeout())
    packet = readiness.generate_from_files(tri_target_closeout=source, output=tmp_path / "packet.json")
    assert packet["no_live_request_in_this_task"] is True
    assert packet["no_env_read_in_this_task"] is True
    assert packet["raw_secret_output"] is False


def test_no_network_function_exists_or_is_called():
    module_text = Path(readiness.__file__).read_text(encoding="utf-8")
    forbidden = ["urlopen", "Request(", "fetch(", "XMLHttpRequest", "sendBeacon", "__import__(\"os\")", "environ", "getenv"]
    assert all(token not in module_text for token in forbidden)


def test_runbook_file_is_generated_and_mentions_all_three_targets(tmp_path):
    source = write_json(tmp_path / "closeout.json", valid_closeout())
    readiness.generate_from_files(tri_target_closeout=source, output=tmp_path / "packet.json")
    runbook = (tmp_path / readiness.RUNBOOK_FILENAME).read_text(encoding="utf-8")
    assert "announcements" in runbook
    assert "substack_drops" in runbook
    assert "product_updates" in runbook
    assert "No autonomous posting" in runbook


def test_static_panel_is_generated_as_non_live_operator_view(tmp_path):
    source = write_json(tmp_path / "closeout.json", valid_closeout())
    readiness.generate_from_files(tri_target_closeout=source, output=tmp_path / "packet.json")
    panel = (tmp_path / readiness.PANEL_FILENAME).read_text(encoding="utf-8")
    assert "Discord supervised dispatch readiness" in panel
    assert "no live request in this view" in panel
    assert "announcements" in panel
    assert "substack_drops" in panel
    assert "product_updates" in panel


def test_generated_packet_contains_no_webhook_url(tmp_path):
    source = write_json(tmp_path / "closeout.json", valid_closeout())
    out = tmp_path / "packet.json"
    packet = readiness.generate_from_files(tri_target_closeout=source, output=out)
    text = out.read_text(encoding="utf-8") + json.dumps(packet, sort_keys=True)
    assert "discord.com/api/webhooks" not in text
    assert "discordapp.com/api/webhooks" not in text
    assert "VtmHv" not in text
    assert "0Sd7p" not in text
