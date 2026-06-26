import json
from pathlib import Path

import pytest

from live_contentops import discord_one_request_live_pilot as pilot

GATE = Path("docs/automation/DISCORD_LIVE_PILOT_AUTHORIZATION_GATE/live_pilot_authorization_gate_packet.json")
PAYLOADS = Path("docs/automation/DISCORD_WEBHOOK_PAYLOAD_CONTRACT/sample_payloads.json")


class MockResponse:
    def __init__(self, status):
        self.status = status


def load_gate():
    return json.loads(GATE.read_text(encoding="utf-8"))


def load_payloads():
    return json.loads(PAYLOADS.read_text(encoding="utf-8"))


def test_exact_announcement_payload_is_selected():
    payload = pilot.select_payload(load_payloads())
    assert payload["payload_id"] == pilot.PAYLOAD_ID
    assert payload["payload_type"] == "announcement"
    assert payload["target_name"] == "announcements"


def test_wrong_payload_hash_blocks():
    gate = load_gate()
    gate["selected_payload_hash"] = "wrong"
    with pytest.raises(pilot.LivePilotBlocked, match="payload_hash_mismatch"):
        pilot.validate_gate_packet(gate)


def test_wrong_candidate_id_blocks():
    gate = load_gate()
    gate["selected_dispatch_candidate_id"] = "wrong"
    with pytest.raises(pilot.LivePilotBlocked, match="candidate_id_mismatch"):
        pilot.validate_gate_packet(gate)


def test_wrong_destination_binding_blocks():
    gate = load_gate()
    gate["selected_destination_binding_id"] = "wrong"
    with pytest.raises(pilot.LivePilotBlocked, match="destination_binding_mismatch"):
        pilot.validate_gate_packet(gate)


def test_request_body_includes_allowed_mentions_parse_empty():
    body = pilot.build_request_body(pilot.select_payload(load_payloads()))
    assert body["allowed_mentions"] == {"parse": []}


def test_request_body_has_no_attachments_components_polls_or_thread_params():
    body = pilot.build_request_body(pilot.select_payload(load_payloads()))
    for key in ["attachments", "attachment", "files", "file", "components", "poll", "thread_id", "thread_name"]:
        assert key not in body


def test_request_budget_allows_only_one_attempt():
    guard = pilot.RequestBudgetGuard()
    guard.spend_before_post()
    assert guard.attempted_requests == 1
    assert guard.remaining_requests == 0


def test_second_attempt_refused_by_budget_guard():
    guard = pilot.RequestBudgetGuard()
    guard.spend_before_post()
    with pytest.raises(pilot.LivePilotBlocked, match="request_budget_exhausted"):
        guard.spend_before_post()


def test_cli_without_execute_does_not_call_network(tmp_path):
    def forbidden(*args, **kwargs):
        raise AssertionError("network should not be called")

    packet = pilot.run_live_pilot(GATE, PAYLOADS, tmp_path / "result.json", execute=False, opener=forbidden)
    assert packet["result_status"] == "BLOCKED"
    assert packet["network_call_attempted"] is False
    assert packet["request_count_attempted"] == 0


def test_result_packet_schema_contains_no_webhook_url(tmp_path):
    packet = pilot.run_live_pilot(GATE, PAYLOADS, tmp_path / "result.json", execute=False)
    text = json.dumps(packet, sort_keys=True).lower()
    assert "discord.com/api/webhooks" not in text
    assert "discordapp.com/api/webhooks" not in text
    assert packet["webhook_url_printed"] is False


def test_result_packet_schema_contains_no_token_or_value_metadata_terms(tmp_path):
    packet = pilot.run_live_pilot(GATE, PAYLOADS, tmp_path / "result.json", execute=False)
    text = json.dumps(packet, sort_keys=True).lower()
    for term in ["token_value", "token_length", "token_prefix", "token_suffix", "token_digest", "env_value"]:
        assert term not in text


def test_non_2xx_produces_fail_without_body_or_headers(tmp_path):
    def opener(req, timeout):
        return MockResponse(404)

    packet = pilot.run_live_pilot(
        GATE,
        PAYLOADS,
        tmp_path / "result.json",
        execute=True,
        environ={pilot.ENV_KEY_NAME: "https://discord.com/api/webhooks/fake/fake"},
        opener=opener,
    )
    assert packet["result_status"] == "FAIL"
    assert packet["status_code_class"] == "4xx"
    assert packet["request_count_attempted"] == 1
    assert packet["retry_count_attempted"] == 0
    assert packet["response_body_recorded"] is False
    assert packet["response_headers_recorded"] is False


def test_2xx_produces_pass_without_body_or_headers(tmp_path):
    def opener(req, timeout):
        return MockResponse(204)

    packet = pilot.run_live_pilot(
        GATE,
        PAYLOADS,
        tmp_path / "result.json",
        execute=True,
        environ={pilot.ENV_KEY_NAME: "https://discord.com/api/webhooks/fake/fake"},
        opener=opener,
    )
    assert packet["result_status"] == "PASS"
    assert packet["status_code_class"] == "2xx"
    assert packet["live_write_completed"] is True
    assert packet["response_body_recorded"] is False
    assert packet["response_headers_recorded"] is False
