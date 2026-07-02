import json
from unittest.mock import patch

from live_contentops import substack_operator_publish_cli as cli


def test_publish_dry_run_does_not_publish(capsys):
    code = cli.main(["--task-id", "0018"])
    evidence = json.loads(capsys.readouterr().out)
    assert code == 0
    assert evidence["result_status"] == "DRY_RUN"
    assert evidence["publish_attempted"] is False
    assert evidence["publish_completed"] is False
    assert evidence["email_send_attempted"] is False
    assert evidence["schedule_attempted"] is False
    assert evidence["publish_boundary_required_confirmation"] == "PUBLISH_BOUNDARY_NOT_YET_APPROVED"


@patch("live_contentops.substack_operator_publish_cli.run_cdp_publish")
def test_execute_allow_publication_without_phrase_blocks_before_cdp(mock_publish, capsys):
    code = cli.main([
        "--execute",
        "--allow-publication",
        "--i-understand-this-can-publish",
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


@patch("live_contentops.substack_operator_publish_cli.run_cdp_publish")
def test_execute_allow_publication_wrong_phrase_blocks_before_cdp(mock_publish, capsys):
    code = cli.main([
        "--execute",
        "--allow-publication",
        "--i-understand-this-can-publish",
        "--operator-confirmation",
        "WRONG_PHRASE",
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


@patch("live_contentops.substack_operator_publish_cli.run_cdp_publish")
def test_execute_current_exact_phrase_still_blocks_before_cdp(mock_publish, capsys):
    code = cli.main([
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
    assert evidence["diagnostic_interpretation"] == "current_confirmation_phrase_is_a_lock_not_an_approval"
    assert evidence["publish_attempted"] is False
    assert evidence["request_count_attempted"] == 0
    mock_publish.assert_not_called()
