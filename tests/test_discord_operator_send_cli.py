import json

from live_contentops import discord_operator_send_cli as cli
from live_contentops.discord_dispatch_adapter import DiscordDispatchAdapter


class MockResponse:
    status = 204


def test_cli_dry_run_writes_redacted_evidence_without_network(tmp_path, capsys):
    def forbidden(*args, **kwargs):
        raise AssertionError("network should not be called")

    out = tmp_path / "evidence.json"
    code = cli.main(
        ["--message", "Capital Chronicle CLI dry run. No financial advice.", "--output", str(out)],
        adapter_factory=lambda: DiscordDispatchAdapter(opener=forbidden),
    )
    evidence = json.loads(out.read_text(encoding="utf-8"))
    printed = capsys.readouterr().out
    assert code == 0
    assert evidence["task_label"] == "TASK_0000"
    assert evidence["result_status"] == "DRY_RUN"
    assert evidence["sent"] is False
    assert evidence["request_count_attempted"] == 0
    assert evidence["retry_count_attempted"] == 0
    assert evidence["webhook_url_printed"] is False
    assert evidence["raw_secret_output"] is False
    assert "discord.com/api/webhooks" not in printed
    assert "mock_token" not in printed


def test_cli_execute_missing_env_blocks_without_network(capsys):
    def forbidden(*args, **kwargs):
        raise AssertionError("network should not be called")

    code = cli.main(
        ["--message", "Capital Chronicle missing env test. No financial advice.", "--execute"],
        adapter_factory=lambda: DiscordDispatchAdapter(environ={}, opener=forbidden),
    )
    evidence = json.loads(capsys.readouterr().out)
    assert code == 2
    assert evidence["result_status"] == "BLOCKED"
    assert evidence["blocker"] == "env_key_missing_DISCORD_ANNOUNCEMENTS_WEBHOOK_URL"
    assert evidence["request_count_attempted"] == 0
    assert evidence["sent"] is False


def test_cli_execute_success_uses_mocked_transport_once(capsys):
    calls = []

    def opener(req, timeout):
        calls.append(req)
        return MockResponse()

    env = {"DISCORD_ANNOUNCEMENTS_WEBHOOK_URL": "https://discord.com/api/webhooks/111/mock_token"}
    code = cli.main(
        [
            "--message",
            "Capital Chronicle mocked send. No financial advice.",
            "--task-id",
            "0007",
            "--execute",
        ],
        adapter_factory=lambda: DiscordDispatchAdapter(environ=env, opener=opener),
    )
    evidence = json.loads(capsys.readouterr().out)
    assert code == 0
    assert len(calls) == 1
    assert evidence["task_label"] == "TASK_0007"
    assert evidence["result_status"] == "PASS"
    assert evidence["sent"] is True
    assert evidence["request_count_attempted"] == 1
    assert evidence["retry_count_attempted"] == 0
    assert evidence["status_code_class"] == "2xx"
    assert evidence["response_body_recorded"] is False
    assert evidence["response_headers_recorded"] is False
    assert evidence["http_status_code_recorded"] is False


def test_cli_requires_message():
    try:
        cli.main([])
    except SystemExit as exc:
        assert exc.code == 2
    else:
        raise AssertionError("missing --message should exit")


def test_cli_secret_leakage_guard():
    from live_contentops.cli_safety import assert_clean_of_secrets
    import pytest
    bad_evidence = {"task_label": "TASK_0011", "leaked_secret": "my_secret_token_123"}
    with pytest.raises(AssertionError, match="Secret leakage detected"):
        assert_clean_of_secrets(bad_evidence, ["my_secret_token_123"])


def test_cli_dry_run_excludes_env_secrets_from_output(tmp_path, capsys):
    fake_webhook = "https://discord.com/api/webhooks/999/SECRET_DISCORD_TOKEN_XYZ"
    env = {"DISCORD_ANNOUNCEMENTS_WEBHOOK_URL": fake_webhook}

    def forbidden(*args, **kwargs):
        raise AssertionError("network should not be called")

    out = tmp_path / "evidence.json"
    code = cli.main(
        ["--message", "Capital Chronicle CLI dry run. No financial advice.", "--output", str(out)],
        adapter_factory=lambda: DiscordDispatchAdapter(environ=env, opener=forbidden),
    )
    evidence = json.loads(out.read_text(encoding="utf-8"))
    printed = capsys.readouterr().out

    assert code == 0
    assert "SECRET_DISCORD_TOKEN_XYZ" not in printed
    assert "SECRET_DISCORD_TOKEN_XYZ" not in json.dumps(evidence)

