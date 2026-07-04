import json

from live_contentops import discord_live_dispatch_closeout as closeout


def approved(**overrides):
    packet = {
        "result_status": "PASS",
        "target_name": "announcements",
        "payload_id": closeout.ANNOUNCEMENTS_PAYLOAD_ID,
        "payload_hash": closeout.ANNOUNCEMENTS_PAYLOAD_HASH,
        "http_status_code": 204,
        "request_count_attempted": 1,
        "retry_count_attempted": 0,
    }
    packet.update(overrides)
    return packet


def smoke(substack_status=204, product_status=204, include_substack=True, include_product=True):
    targets = []
    if include_substack:
        targets.append({"target_name": "substack_drops", "http_status_code": substack_status})
    if include_product:
        targets.append({"target_name": "product_updates", "http_status_code": product_status})
    return {"targets": targets}


def test_closeout_pass_when_announcements_approved_dispatch_is_pass_204():
    packet = closeout.build_closeout_packet(approved(), smoke())
    assert packet["closeout_status"] == "PASS"
    assert packet["verified_paths"]["announcements"]["adapter_dispatch_verified"] is True
    assert packet["verified_paths"]["announcements"]["last_http_status_code"] == 204


def test_closeout_pass_when_substack_and_product_smoke_are_204():
    packet = closeout.build_closeout_packet(approved(), smoke())
    assert packet["verified_paths"]["substack_drops"]["smoke_verified"] is True
    assert packet["verified_paths"]["product_updates"]["smoke_verified"] is True


def test_closeout_blocked_if_approved_dispatch_packet_missing(tmp_path):
    output = tmp_path / "out.json"
    packet = closeout.closeout_from_files(
        approved_dispatch_packet=tmp_path / "missing.json",
        multi_smoke_packet=tmp_path / "smoke.json",
        output=output,
    )
    assert packet["closeout_status"] == "BLOCKED"
    assert packet["no_live_request_in_this_task"] is True


def test_closeout_fail_if_announcements_dispatch_status_not_pass():
    packet = closeout.build_closeout_packet(approved(result_status="FAIL"), smoke())
    assert packet["closeout_status"] == "FAIL"
    assert packet["failure_reason"] == "announcements_adapter_dispatch_not_pass"


def test_closeout_fail_if_announcements_status_not_2xx():
    packet = closeout.build_closeout_packet(approved(http_status_code=403), smoke())
    assert packet["closeout_status"] == "FAIL"
    assert packet["failure_reason"] == "announcements_adapter_dispatch_not_2xx"


def test_closeout_fail_if_substack_smoke_missing_or_not_2xx():
    missing = closeout.build_closeout_packet(approved(), smoke(include_substack=False))
    not_2xx = closeout.build_closeout_packet(approved(), smoke(substack_status=403))
    assert missing["closeout_status"] == "FAIL"
    assert missing["failure_reason"] == "substack_drops_smoke_missing"
    assert not_2xx["closeout_status"] == "FAIL"
    assert not_2xx["failure_reason"] == "substack_drops_smoke_not_2xx"


def test_closeout_fail_if_product_updates_smoke_missing_or_not_2xx():
    missing = closeout.build_closeout_packet(approved(), smoke(include_product=False))
    not_2xx = closeout.build_closeout_packet(approved(), smoke(product_status=500))
    assert missing["closeout_status"] == "FAIL"
    assert missing["failure_reason"] == "product_updates_smoke_missing"
    assert not_2xx["closeout_status"] == "FAIL"
    assert not_2xx["failure_reason"] == "product_updates_smoke_not_2xx"


def test_no_network_function_exists_or_is_called():
    assert not hasattr(closeout, "urlopen")
    assert not hasattr(closeout, "Request")
    assert not hasattr(closeout, "dispatch")


def test_generated_packet_marks_no_live_request_true(tmp_path):
    approved_path = tmp_path / "approved.json"
    smoke_path = tmp_path / "smoke.json"
    output = tmp_path / "out.json"
    approved_path.write_text(json.dumps(approved()), encoding="utf-8")
    smoke_path.write_text(json.dumps(smoke()), encoding="utf-8")
    packet = closeout.closeout_from_files(
        approved_dispatch_packet=approved_path,
        multi_smoke_packet=smoke_path,
        output=output,
    )
    assert packet["no_live_request_in_this_task"] is True
    assert json.loads(output.read_text(encoding="utf-8"))["no_live_request_in_this_task"] is True


def test_generated_packet_has_announcements_ready_for_supervised_dispatch():
    packet = closeout.build_closeout_packet(approved(), smoke())
    assert packet["supervised_use_status"]["announcements"] == "ready_for_supervised_dispatch"


def test_generated_packet_has_substack_product_ready_for_adapter_dispatch_pilot():
    packet = closeout.build_closeout_packet(approved(), smoke())
    assert packet["supervised_use_status"]["substack_drops"] == "ready_for_adapter_dispatch_pilot"
    assert packet["supervised_use_status"]["product_updates"] == "ready_for_adapter_dispatch_pilot"


def test_generated_packet_contains_no_webhook_url():
    packet = closeout.build_closeout_packet(approved(), smoke())
    text = json.dumps(packet, sort_keys=True)
    assert "discord.com/api/webhooks" not in text
    assert "discordapp.com/api/webhooks" not in text
    assert "webhook_token" not in text
