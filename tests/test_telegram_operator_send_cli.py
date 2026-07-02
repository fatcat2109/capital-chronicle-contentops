import json

from live_contentops import telegram_operator_send_cli as cli


def test_cli_dry_run_writes_redacted_evidence_without_network(tmp_path, capsys):
    def forbidden():
        raise AssertionError("network should not be called")

    out = tmp_path / "evidence.json"
    code = cli.main(
        ["--message", "Capital Chronicle Telegram CLI dry run. No market guidance.", "--output", str(out)],
        env_provider=lambda: {},
        http_transport=forbidden,
    )
    evidence = json.loads(out.read_text(encoding="utf-8"))
    printed = capsys.readouterr().out
    assert code == 0
    assert evidence["task_label"] == "TASK_0000"
    assert evidence["result_status"] == "DRY_RUN"
    assert evidence["sent"] is False
    assert evidence["request_count_attempted"] == 0
    assert evidence["retry_count_attempted"] == 0
    assert evidence["raw_secret_output"] is False
    assert evidence["secret_derived_metadata_recorded"] is False
    assert "123456:FAKE" not in printed
    assert "@fake_channel" not in printed


def test_cli_execute_missing_env_blocks_without_network(capsys):
    def forbidden():
        raise AssertionError("network should not be called")

    code = cli.main(
        ["--message", "Capital Chronicle Telegram missing env test. No market guidance.", "--execute"],
        env_provider=lambda: {},
        http_transport=forbidden,
    )
    evidence = json.loads(capsys.readouterr().out)
    assert code == 2
    assert evidence["result_status"] == "BLOCKED"
    assert evidence["blocker"] == "telegram_env_missing"
    assert evidence["request_count_attempted"] == 0
    assert evidence["sent"] is False


def test_cli_execute_success_uses_mocked_transport_once(capsys):
    calls = []

    def transport():
        calls.append(True)
        return True, 200, {"has_message_id": True}

    env = {"TELEGRAM_BOT_TOKEN": "123456:FAKE", "TEST_TELEGRAM_CHANNEL": "@fake_channel"}
    code = cli.main(
        [
            "--message",
            "Capital Chronicle Telegram mocked send. No market guidance.",
            "--task-id",
            "0009",
            "--execute",
        ],
        env_provider=lambda: env,
        http_transport=transport,
    )
    evidence = json.loads(capsys.readouterr().out)
    assert code == 0
    assert len(calls) == 1
    assert evidence["task_label"] == "TASK_0009"
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
