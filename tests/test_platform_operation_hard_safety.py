import json
from unittest.mock import patch

from live_contentops import discord_operator_send_cli
from live_contentops import substack_operator_draft_cli
from live_contentops import substack_operator_publish_cli
from live_contentops import substack_operator_publish_preflight_cli
from live_contentops import telegram_operator_send_cli
from live_contentops.discord_dispatch_adapter import DiscordDispatchAdapter


def assert_no_autonomy(evidence):
    assert evidence["publish_attempted"] is False
    assert evidence["schedule_attempted"] is False
    assert evidence["email_send_attempted"] is False
    assert evidence["autonomous_dispatch_created"] is False
    assert evidence["queue_created"] is False
    assert evidence["scheduler_created"] is False


def test_discord_cli_hard_safety_fields(capsys):
    evidence_code = discord_operator_send_cli.main(
        ["--message", "Capital Chronicle hard safety dry run. No market guidance."],
        adapter_factory=lambda: DiscordDispatchAdapter(environ={}, opener=lambda *a, **k: None),
    )
    evidence = json.loads(capsys.readouterr().out)
    assert evidence_code == 0
    assert_no_autonomy(evidence)


def test_telegram_cli_hard_safety_fields(capsys):
    evidence_code = telegram_operator_send_cli.main(
        ["--message", "Capital Chronicle hard safety dry run. No market guidance."],
        env_provider=lambda: {},
        http_transport=lambda: (_ for _ in ()).throw(AssertionError("network should not run")),
    )
    evidence = json.loads(capsys.readouterr().out)
    assert evidence_code == 0
    assert_no_autonomy(evidence)


def test_substack_draft_dry_run_hard_safety_fields(capsys):
    code = substack_operator_draft_cli.main([
        "--title",
        "Capital Chronicle hard safety draft test",
        "--body",
        "Capital Chronicle hard safety draft body. No market guidance.",
    ])
    evidence = json.loads(capsys.readouterr().out)
    assert code == 0
    assert evidence["result_status"] == "DRY_RUN"
    assert evidence["draft_created"] is False
    assert evidence["publish_attempted"] is False
    assert evidence["schedule_attempted"] is False
    assert evidence["email_send_attempted"] is False


def test_substack_publish_preflight_dry_run_hard_safety_fields(capsys):
    code = substack_operator_publish_preflight_cli.main(["--draft-url", "https://substack.com/p/test"])
    evidence = json.loads(capsys.readouterr().out)
    assert code == 0
    assert evidence["result_status"] == "DRY_RUN"
    assert evidence["publish_preflight_completed"] is False
    assert evidence["publish_attempted"] is False
    assert evidence["schedule_attempted"] is False
    assert evidence["email_send_attempted"] is False


@patch("live_contentops.substack_operator_publish_cli.run_cdp_publish")
def test_substack_publish_cli_current_phrase_blocks_before_cdp(mock_publish, capsys):
    code = substack_operator_publish_cli.main([
        "--execute",
        "--allow-publication",
        "--i-understand-this-can-publish",
        "--operator-confirmation",
        "PUBLISH_BOUNDARY_NOT_YET_APPROVED",
        "--draft-url",
        "https://substack.com/p/test",
        "--expected-title-sha256",
        "abc",
        "--email-mode",
        "no-email",
    ])
    evidence = json.loads(capsys.readouterr().out)
    assert code == 2
    assert evidence["blocker"] == "publish_boundary_not_approved"
    assert evidence["publish_attempted"] is False
    assert evidence["request_count_attempted"] == 0
    mock_publish.assert_not_called()
