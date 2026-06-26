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


def test_minimal_content_body_contains_content_and_allowed_mentions_only():
    body = pilot.build_minimal_content_body()
    assert body == {
        "content": "Capital Chronicle Discord live pilot test — announcements webhook connectivity check.",
        "allowed_mentions": {"parse": []},
    }


def test_minimal_content_body_has_no_rich_or_thread_fields():
    body = pilot.build_minimal_content_body()
    for key in ["embeds", "attachments", "attachment", "components", "poll", "files", "file", "thread_id", "thread_name"]:
        assert key not in body


def test_exact_http_status_code_is_recorded_for_minimal_content(tmp_path):
    def opener(req, timeout):
        return MockResponse(204)

    packet = pilot.run_live_pilot(
        GATE,
        PAYLOADS,
        tmp_path / "result.json",
        execute=True,
        minimal_content=True,
        environ={pilot.ENV_KEY_NAME: "https://discord.com/api/webhooks/fake/fake"},
        opener=opener,
    )
    assert packet["http_status_code"] == 204
    assert packet["payload_mode"] == "minimal_content_only"


@pytest.mark.parametrize(
    ("status_code", "expected"),
    [
        (200, "success_2xx"),
        (204, "success_2xx"),
        (400, "payload_rejected_or_bad_request"),
        (401, "credential_unauthorized"),
        (403, "credential_unauthorized"),
        (404, "webhook_not_found_or_deleted"),
        (429, "rate_limited"),
        (500, "discord_server_error"),
        (503, "discord_server_error"),
        (302, "unknown_http_status"),
    ],
)
def test_diagnostic_interpretation_maps_status_codes(status_code, expected):
    assert pilot.diagnostic_interpretation(status_code) == expected


def test_diagnostic_interpretation_maps_network_exception_before_response():
    assert pilot.diagnostic_interpretation(None) == "network_exception_before_response"


def test_dry_run_minimal_content_does_not_call_network(tmp_path):
    def forbidden(*args, **kwargs):
        raise AssertionError("network should not be called")

    packet = pilot.run_live_pilot(
        GATE,
        PAYLOADS,
        tmp_path / "result.json",
        execute=False,
        minimal_content=True,
        opener=forbidden,
    )
    assert packet["result_status"] == "BLOCKED"
    assert packet["payload_mode"] == "minimal_content_only"
    assert packet["network_call_attempted"] is False
    assert packet["request_count_attempted"] == 0
