import json
from pathlib import Path

import pytest

from live_contentops import discord_multi_target_live_smoke as smoke


class MockResponse:
    def __init__(self, status):
        self.status = status


def valid_env():
    return {
        "DISCORD_SUBSTACK_DROPS_WEBHOOK_URL": "https://discord.com/api/webhooks/111/token_a",
        "DISCORD_PRODUCT_UPDATES_WEBHOOK_URL": "https://discord.com/api/webhooks/222/token_b",
    }


def test_dry_run_does_not_call_network(tmp_path):
    def forbidden(*args, **kwargs):
        raise AssertionError("network should not be called")

    packet = smoke.run_smoke(tmp_path / "result.json", execute=False, opener=forbidden)
    assert packet["result_status"] == "BLOCKED"
    assert packet["request_count_attempted"] == 0
    assert packet["summary"]["targets_planned"] == 2
    assert packet["summary"]["targets_attempted"] == 0


def test_live_mode_attempts_exactly_two_targets(tmp_path):
    calls = []

    def opener(req, timeout):
        calls.append(req)
        return MockResponse(204)

    packet = smoke.run_smoke(tmp_path / "result.json", execute=True, environ=valid_env(), opener=opener)
    assert len(calls) == 2
    assert packet["request_count_attempted"] == 2
    assert [target["request_count_attempted"] for target in packet["targets"]] == [1, 1]


def test_no_retry_when_one_target_fails(tmp_path):
    statuses = [204, 403]
    calls = []

    def opener(req, timeout):
        calls.append(req)
        return MockResponse(statuses[len(calls) - 1])

    packet = smoke.run_smoke(tmp_path / "result.json", execute=True, environ=valid_env(), opener=opener)
    assert len(calls) == 2
    assert packet["retry_count_attempted"] == 0
    assert packet["request_count_attempted"] == 2


def test_per_target_request_budget_hard_cap():
    guard = smoke.RequestBudgetGuard()
    guard.spend_before_post("substack_drops")
    with pytest.raises(smoke.DiscordSmokeBlocked, match="per_target_budget_exhausted_substack_drops"):
        guard.spend_before_post("substack_drops")


def test_total_request_budget_hard_cap():
    guard = smoke.RequestBudgetGuard()
    guard.spend_before_post("substack_drops")
    guard.spend_before_post("product_updates")
    with pytest.raises(smoke.DiscordSmokeBlocked, match="request_budget_exhausted"):
        guard.spend_before_post("another_target")


def test_payload_contains_only_content_and_allowed_mentions():
    for target in smoke.TARGETS:
        body = smoke.build_minimal_content_body(target)
        assert set(body) == {"content", "allowed_mentions"}
        assert body["allowed_mentions"] == {"parse": []}
        assert "financial advice" not in json.dumps(body).lower()


def test_user_agent_header_is_set(tmp_path):
    seen = []

    def opener(req, timeout):
        seen.append(req)
        return MockResponse(204)

    smoke.run_smoke(tmp_path / "result.json", execute=True, environ=valid_env(), opener=opener)
    assert all(req.headers["User-agent"] == smoke.USER_AGENT for req in seen)


@pytest.mark.parametrize(
    ("status_code", "expected"),
    [
        (204, "success_2xx"),
        (403, "credential_unauthorized"),
        (404, "webhook_not_found_or_deleted"),
    ],
)
def test_diagnostic_interpretation_maps_required_statuses(status_code, expected):
    assert smoke.diagnostic_interpretation(status_code) == expected


def test_mixed_2xx_4xx_maps_to_partial(tmp_path):
    statuses = [204, 403]
    calls = []

    def opener(req, timeout):
        calls.append(req)
        return MockResponse(statuses[len(calls) - 1])

    packet = smoke.run_smoke(tmp_path / "result.json", execute=True, environ=valid_env(), opener=opener)
    assert packet["result_status"] == "PARTIAL"
    assert packet["summary"]["targets_passed"] == 1
    assert packet["summary"]["targets_failed"] == 1


def test_both_2xx_maps_to_pass(tmp_path):
    def opener(req, timeout):
        return MockResponse(204)

    packet = smoke.run_smoke(tmp_path / "result.json", execute=True, environ=valid_env(), opener=opener)
    assert packet["result_status"] == "PASS"
    assert packet["summary"]["targets_passed"] == 2
    assert packet["summary"]["targets_failed"] == 0


def test_both_4xx_maps_to_fail(tmp_path):
    def opener(req, timeout):
        return MockResponse(404)

    packet = smoke.run_smoke(tmp_path / "result.json", execute=True, environ=valid_env(), opener=opener)
    assert packet["result_status"] == "FAIL"
    assert packet["summary"]["targets_passed"] == 0
    assert packet["summary"]["targets_failed"] == 2


def test_result_packet_contains_no_webhook_url_or_raw_env_value(tmp_path):
    env = valid_env()

    def opener(req, timeout):
        return MockResponse(204)

    packet = smoke.run_smoke(tmp_path / "result.json", execute=True, environ=env, opener=opener)
    text = json.dumps(packet, sort_keys=True)
    assert "discord.com/api/webhooks" not in text
    assert "token_a" not in text
    assert "token_b" not in text
    assert packet["webhook_url_printed"] is False
    assert packet["raw_secret_output"] is False


def test_missing_env_key_blocks_before_network(tmp_path):
    def forbidden(*args, **kwargs):
        raise AssertionError("network should not be called")

    with pytest.raises(smoke.DiscordSmokeBlocked, match="env_key_missing_DISCORD_PRODUCT_UPDATES_WEBHOOK_URL"):
        smoke.run_smoke(
            tmp_path / "result.json",
            execute=True,
            environ={"DISCORD_SUBSTACK_DROPS_WEBHOOK_URL": "https://discord.com/api/webhooks/111/token_a"},
            opener=forbidden,
        )
