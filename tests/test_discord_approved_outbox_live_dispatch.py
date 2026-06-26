import json

import pytest

from live_contentops import discord_approved_outbox_live_dispatch as pilot
from live_contentops import discord_dispatch_adapter as adapter


class MockResponse:
    def __init__(self, status):
        self.status = status


def load_sample_payload(target_name="announcements"):
    target = pilot.APPROVED_TARGETS[target_name]
    packet = adapter.load_payload_packet(pilot.PAYLOAD_PACKET_PATH)
    return adapter.select_payload(packet, target.payload_id)


def env_for_target(target_name="announcements"):
    target = pilot.APPROVED_TARGETS[target_name]
    host = "discord.com"
    token = "test" + "-" + "token"
    path = "/api/" + "webhooks" + "/111/" + token
    return {target.env_key_name: "https://" + host + path}


def test_selected_payload_id_is_announcement_payload():
    payload = load_sample_payload("announcements")
    assert payload["payload_id"] == pilot.PAYLOAD_ID
    assert payload["payload_type"] == "announcement"
    assert payload["target_name"] == "announcements"


def test_selected_payload_id_is_substack_drop_payload():
    payload = load_sample_payload("substack_drops")
    assert payload["payload_id"] == pilot.SUBSTACK_PAYLOAD_ID
    assert payload["payload_type"] == "substack_drop"
    assert payload["target_name"] == "substack_drops"


def test_selected_payload_id_is_product_update_payload():
    payload = load_sample_payload("product_updates")
    assert payload["payload_id"] == pilot.PRODUCT_UPDATES_PAYLOAD_ID
    assert payload["payload_type"] == "product_update"
    assert payload["target_name"] == "product_updates"


@pytest.mark.parametrize("target_name", ["announcements", "substack_drops", "product_updates"])
def test_expected_payload_hash_is_verified_from_hash_packet(target_name):
    target = pilot.APPROVED_TARGETS[target_name]
    packet = pilot.load_json(pilot.HASH_PACKET_PATH)
    approval = pilot.select_hash_approval(packet, target.payload_id, target.expected_payload_hash)
    assert approval["payload_hash"] == target.expected_payload_hash
    assert approval["payload_id"] == target.payload_id


@pytest.mark.parametrize("target_name", ["announcements", "substack_drops", "product_updates"])
def test_wrong_payload_hash_blocks(tmp_path, target_name):
    out = tmp_path / "result.json"
    packet = pilot.run_approved_outbox_dispatch(
        output_path=out,
        target_name=target_name,
        expected_payload_hash="bad_hash",
    )
    assert packet["result_status"] == "BLOCKED"
    assert packet["request_count_attempted"] == 0
    assert packet["blocker"] == "payload_hash_approval_not_found"


@pytest.mark.parametrize("target_name", ["announcements", "substack_drops", "product_updates"])
@pytest.mark.parametrize(
    ("payload_key", "payload_value", "expected_blocker"),
    [
        ("target_name", "wrong_target", "payload_target_name_mismatch"),
        ("destination_binding_id", "wrong", "payload_destination_binding_id_mismatch"),
        ("credential_handle_id", "wrong", "payload_credential_handle_id_mismatch"),
    ],
)
def test_wrong_target_binding_credential_blocks(tmp_path, target_name, payload_key, payload_value, expected_blocker):
    target = pilot.APPROVED_TARGETS[target_name]
    source = adapter.load_payload_packet(pilot.PAYLOAD_PACKET_PATH)
    for item in source["payloads"]:
        if item.get("payload_id") == target.payload_id:
            item[payload_key] = payload_value
    payload_path = tmp_path / "payloads.json"
    output_path = tmp_path / "result.json"
    payload_path.write_text(json.dumps(source), encoding="utf-8")
    packet = pilot.run_approved_outbox_dispatch(
        payload_packet_path=payload_path,
        output_path=output_path,
        target_name=target_name,
    )
    assert packet["result_status"] == "BLOCKED"
    assert packet["blocker"] == expected_blocker
    assert packet["request_count_attempted"] == 0


@pytest.mark.parametrize("target_name", ["announcements", "substack_drops", "product_updates"])
def test_dispatch_uses_discord_dispatch_adapter(tmp_path, target_name):
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

    packet = pilot.run_approved_outbox_dispatch(
        output_path=tmp_path / "result.json",
        target_name=target_name,
        adapter_factory=FakeAdapter,
    )
    assert packet["adapter_module"] == "live_contentops.discord_dispatch_adapter"
    assert len(calls) == 2
    assert calls[1][1]["target_name"] == target_name


@pytest.mark.parametrize("target_name", ["announcements", "substack_drops", "product_updates"])
@pytest.mark.parametrize(
    ("status", "result_status", "diagnostic"),
    [
        (204, "PASS", "success_2xx"),
        (403, "FAIL", "credential_unauthorized"),
    ],
)
def test_mocked_status_maps_to_expected_result(tmp_path, target_name, status, result_status, diagnostic):
    def opener(req, timeout):
        return MockResponse(status)

    packet = pilot.run_approved_outbox_dispatch(
        output_path=tmp_path / "result.json",
        execute=True,
        target_name=target_name,
        environ=env_for_target(target_name),
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


@pytest.mark.parametrize("target_name", ["announcements", "substack_drops", "product_updates"])
def test_dry_run_path_does_not_call_network(tmp_path, target_name):
    def forbidden(*args, **kwargs):
        raise AssertionError("network should not be called")

    packet = pilot.run_approved_outbox_dispatch(
        output_path=tmp_path / "result.json",
        target_name=target_name,
        opener=forbidden,
    )
    assert packet["result_status"] == "DRY_RUN"
    assert packet["request_count_attempted"] == 0


@pytest.mark.parametrize("target_name", ["announcements", "substack_drops", "product_updates"])
def test_result_packet_contains_no_webhook_url(tmp_path, target_name):
    out = tmp_path / "result.json"
    packet = pilot.run_approved_outbox_dispatch(output_path=out, target_name=target_name)
    text = out.read_text(encoding="utf-8") + json.dumps(packet, sort_keys=True)
    assert "discord.com/api/webhooks" not in text
    assert "discordapp.com/api/webhooks" not in text
    assert "mock_token" not in text
    assert "test-token" not in text
    assert "webhook_url_printed" in text
    assert packet["raw_secret_output"] is False
    assert packet["response_body_recorded"] is False
    assert packet["response_headers_recorded"] is False
