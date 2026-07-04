import json
from dataclasses import asdict
from pathlib import Path

from live_contentops.discord_supervised_live_pilot_from_approved_outbox_v6 import *

SAMPLE = Path("docs/automation/V6_DISCORD_DRY_RUN_OUTBOX_OPERATOR_APPROVAL_SPINE/sample_discord_dry_run_outbox_packet.json")
FAKE_WEBHOOK = "https://discord.example.invalid/api/webhooks/fake/value-never-serialize"


def _outbox():
    return load_json(SAMPLE)


def _approval(hash_value=None, status="approved", budget=1):
    pkt = _outbox()
    return {
        "operator_approval_status": status,
        "approved_by": "jim",
        "approved_at": "2026-07-01T02:45:00+07:00",
        "exact_payload_hash": hash_value or pkt["approved_payload_hash"],
        "request_budget": budget,
    }


def test_blocked_when_approval_missing():
    result = make_supervised_live_pilot_result(_outbox(), None, env={DISCORD_REQUIRED_KEY_NAME: FAKE_WEBHOOK})
    assert result.result_class == "blocked"
    assert result.request_count == 0
    assert result.live_send_attempted is False
    assert "operator_approval_declaration_missing" in result.blockers


def test_blocked_when_approval_pending():
    result = make_supervised_live_pilot_result(_outbox(), _approval(status="pending"), env={DISCORD_REQUIRED_KEY_NAME: FAKE_WEBHOOK})
    assert result.result_class == "blocked"
    assert result.request_count == 0
    assert "operator_approval_status_not_approved" in result.blockers


def test_blocked_when_hash_mismatch():
    result = make_supervised_live_pilot_result(_outbox(), _approval(hash_value="0" * 64), env={DISCORD_REQUIRED_KEY_NAME: FAKE_WEBHOOK})
    assert result.result_class == "blocked"
    assert result.request_count == 0
    assert "operator_approval_exact_payload_hash_mismatch" in result.blockers


def test_blocked_when_env_key_missing():
    result = make_supervised_live_pilot_result(_outbox(), _approval(), env={})
    assert result.result_class == "blocked"
    assert result.env_key_present is False
    assert any(b.startswith("env_key_missing") for b in result.blockers)


def test_blocked_when_kill_switch_active():
    result = make_supervised_live_pilot_result(_outbox(), _approval(), env={DISCORD_REQUIRED_KEY_NAME: FAKE_WEBHOOK}, kill_switch_active=True)
    assert result.result_class == "blocked"
    assert result.kill_switch_active is True
    assert "kill_switch_active" in result.blockers


def test_blocked_when_request_budget_not_one():
    result = make_supervised_live_pilot_result(_outbox(), _approval(), env={DISCORD_REQUIRED_KEY_NAME: FAKE_WEBHOOK}, request_budget=2)
    assert result.result_class == "blocked"
    assert result.request_budget == 2
    assert "request_budget_not_one" in result.blockers


def test_live_path_fake_sender_sends_exactly_one_request_with_exact_preview():
    calls = []
    def fake_sender(url, content, timeout_seconds):
        calls.append({"url": url, "content": content, "timeout": timeout_seconds})
        return {"status_code": 204, "body": "must-not-serialize"}
    outbox = _outbox()
    result = make_supervised_live_pilot_result(outbox, _approval(), env={DISCORD_REQUIRED_KEY_NAME: FAKE_WEBHOOK}, sender=fake_sender)
    assert result.result_class == "success"
    assert result.request_count == 1
    assert result.live_send_attempted is True
    assert result.live_send_succeeded is True
    assert result.redacted_status_class == "2xx"
    assert len(calls) == 1
    assert calls[0]["content"] == outbox["discord_preview_text"]


def test_no_retry_path_when_sender_returns_failure():
    calls = []
    def fake_sender(url, content, timeout_seconds):
        calls.append(1)
        return {"status_code": 500, "body": "sensitive failure body"}
    result = make_supervised_live_pilot_result(_outbox(), _approval(), env={DISCORD_REQUIRED_KEY_NAME: FAKE_WEBHOOK}, sender=fake_sender)
    assert result.result_class == "failed_redacted"
    assert result.request_count == 1
    assert result.redacted_status_class == "5xx"
    assert len(calls) == 1


def test_no_raw_webhook_env_or_secret_values_serialized():
    result = make_supervised_live_pilot_result(_outbox(), _approval(), env={DISCORD_REQUIRED_KEY_NAME: FAKE_WEBHOOK}, sender=lambda *_: {"status_code": 204})
    data = json.dumps(asdict(result)).lower()
    assert "value-never-serialize" not in data
    assert "discord.example.invalid" not in data
    assert "discord_live_announcements_webhook=" not in data
    assert result.raw_secret_values_serialized is False
    assert result.webhook_url_serialized is False
    assert result.env_lines_serialized is False


def test_no_response_body_serialized():
    result = make_supervised_live_pilot_result(_outbox(), _approval(), env={DISCORD_REQUIRED_KEY_NAME: FAKE_WEBHOOK}, sender=lambda *_: {"status_code": 400, "body": "secret response body"})
    data = json.dumps(asdict(result)).lower()
    assert "secret response body" not in data
    assert result.response_body_serialized is False
    assert result.result_class == "failed_redacted"


def test_result_records_request_count_correctly():
    blocked = make_supervised_live_pilot_result(_outbox(), None, env={DISCORD_REQUIRED_KEY_NAME: FAKE_WEBHOOK})
    sent = make_supervised_live_pilot_result(_outbox(), _approval(), env={DISCORD_REQUIRED_KEY_NAME: FAKE_WEBHOOK}, sender=lambda *_: {"status_code": 204})
    assert blocked.request_count == 0
    assert sent.request_count == 1


def test_committed_sample_result_is_blocked_no_live_send():
    path = Path("docs/automation/V6_DISCORD_SUPERVISED_LIVE_PILOT_FROM_APPROVED_OUTBOX/sample_discord_supervised_live_pilot_result_blocked.json")
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    assert data["result_class"] == "blocked"
    assert data["live_send_attempted"] is False
    assert data["request_count"] == 0
    assert data["network_call_made"] is False


def test_static_prevents_direct_discord_calls_outside_sender_abstraction():
    src = Path("live_contentops/discord_supervised_live_pilot_from_approved_outbox_v6.py").read_text(encoding="utf-8-sig")
    assert "requests" not in src
    assert "httpx" not in src
    assert src.count("urlopen") == 1
    assert "discord.com/api" not in src
    assert "api/webhooks" not in src
    assert "webhook_value)" not in src
