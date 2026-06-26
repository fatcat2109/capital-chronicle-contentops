import json
from pathlib import Path

import pytest

from live_contentops import discord_approved_outbox_live_dispatch as pilot
from live_contentops import discord_dispatch_adapter as adapter


class MockResponse:
    def __init__(self, status):
        self.status = status


def load_sample_payload():
    packet = adapter.load_payload_packet(pilot.PAYLOAD_PACKET_PATH)
    return adapter.select_payload(packet, pilot.PAYLOAD_ID)


def env_for_announcement():
    host = "discord.com"
    path = "/api/" + "webhooks" + "/111/" + "test-token"
    return {pilot.ENV_KEY_NAME: "https://" + host + path}


def test_selected_payload_id_is_announcement_payload():
    payload = load_sample_payload()
    assert payload["payload_id"] == pilot.PAYLOAD_ID
    assert payload["payload_type"] == "announcement"
    assert payload["target_name"] == "announcements"


def test_expected_payload_hash_is_verified_from_hash_packet():
    packet = pilot.load_json(pilot.HASH_PACKET_PATH)
    approval = pilot.select_hash_approval(packet, pilot.PAYLOAD_ID, pilot.EXPECTED_PAYLOAD_HASH)
    assert approval["payload_hash"] == pilot.EXPECTED_PAYLOAD_HASH
    assert approval["payload_id"] == pilot.PAYLOAD_ID


def test_wrong_payload_hash_blocks(tmp_path):
    out = tmp_path / "result.json"
    packet = pilot.run_approved_outbox_dispatch(output_path=out, expected_payload_hash="bad_hash")
    assert packet["result_status"] == "BLOCKED"
    assert packet["request_count_attempted"] == 0
    assert packet["blocker"] == "payload_hash_approval_not_found"


@pytest.mark.parametrize(
    ("payload_key", "payload_value", "expected_blocker"),
    [
        ("target_name", "substack_drops", "payload_target_name_mismatch"),
        ("destination_binding_id", "wrong", "payload_destination_binding_id_mismatch"),
        ("credential_handle_id", "wrong", "payload_credential_handle_id_mismatch"),
    ],
)
def test_wrong_target_binding_credential_blocks(tmp_path, payload_key, payload_value, expected_blocker):
    source = adapter.load_payload_packet(pilot.PAYLOAD_PACKET_PATH)
    for item in source["payloads"]:
        if item.get("payload_id") == pilot.PAYLOAD_ID:
            item[payload_key] = payload_value
    payload_path = tmp_path / "payloads.json"
    output_path = tmp_path / "result.json"
    payload_path.write_text(json.dumps(source), encoding="utf-8")
    packet = pilot.run_approved_outbox_dispatch(payload_packet_path=payload_path, output_path=output_path)
    assert packet["result_status"] == "BLOCKED"
    assert packet["blocker"] == expected_blocker
    assert packet["request_count_attempted"] == 0


def test_dispatch_uses_discord_dispatch_adapter(tmp_path):
    calls = []

    class FakeAdapter:
        def __init__(self, environ=None, opener=None):
            calls.append((environ, opener))

        def dispatch(self, payload, **kwargs):
            calls.append((payload, kwargs))
            return {
                "result_status": "DRY_RUN",
                "request_count_attempted": 0,
                "http_status_code": None,
                "status_code_class": "not_attempted",
                "diagnostic_interpretation": "not_attempted",
                "live_write_completed": False,
            }

    packet = pilot.run_approved_outbox_dispatch(output_path=tmp_path / "result.json", adapter_factory=FakeAdapter)
    assert packet["adapter_module"] == "live_contentops.discord_dispatch_adapter"
    assert len(calls) == 2


@pytest.mark.parametrize(
    ("status", "result_status", "diagnostic"),
    [
        (204, "PASS", "success_2xx"),
        (403, "FAIL", "credential_unauthorized"),
    ],
)
def test_mocked_status_maps_to_expected_result(tmp_path, status, result_status, diagnostic):
    def opener(req, timeout):
        return MockResponse(status)

    packet = pilot.run_approved_outbox_dispatch(
        output_path=tmp_path / "result.json",
        execute=True,
        environ=env_for_announcement(),
        opener=opener,
    )
    assert packet["result_status"] == result_status
    assert packet["diagnostic_interpretation"] == diagnostic
    assert packet["request_count_attempted"] == 1


def test_request_budget_blocks_second_post():
    guard = adapter.DispatchBudgetGuard()
    guard.spend_before_post()
    with pytest.raises(adapter.DiscordDispatchBlocked, match="request_budget_exhausted"):
        guard.spend_before_post()


def test_dry_run_path_does_not_call_network(tmp_path):
    def forbidden(*args, **kwargs):
        raise AssertionError("network should not be called")

    packet = pilot.run_approved_outbox_dispatch(output_path=tmp_path / "result.json", opener=forbidden)
    assert packet["result_status"] == "DRY_RUN"
    assert packet["request_count_attempted"] == 0


def test_result_packet_contains_no_webhook_url(tmp_path):
    out = tmp_path / "result.json"
    packet = pilot.run_approved_outbox_dispatch(output_path=out)
    text = out.read_text(encoding="utf-8") + json.dumps(packet, sort_keys=True)
    assert "discord.com/api/webhooks" not in text
    assert "mock_token" not in text
    assert "webhook_url_printed" in text
    assert packet["raw_secret_output"] is False
    assert packet["response_body_recorded"] is False
    assert packet["response_headers_recorded"] is False
