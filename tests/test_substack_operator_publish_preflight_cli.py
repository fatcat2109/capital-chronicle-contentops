import json
from unittest.mock import MagicMock, patch

from live_contentops import substack_operator_publish_preflight_cli as cli


def test_preflight_dry_run_no_browser(capsys):
    code = cli.main(["--draft-url", "https://substack.com/p/test", "--task-id", "0018"])
    evidence = json.loads(capsys.readouterr().out)
    assert code == 0
    assert evidence["result_status"] == "DRY_RUN"
    assert evidence["publish_preflight_completed"] is False
    assert evidence["publish_attempted"] is False
    assert evidence["schedule_attempted"] is False
    assert evidence["email_send_attempted"] is False
    assert evidence["browser_cdp_used"] is False


@patch("playwright.sync_api.sync_playwright")
def test_preflight_missing_cdp_blocks(mock_sync, capsys):
    mock_p = mock_sync.return_value.__enter__.return_value
    mock_p.chromium.connect_over_cdp.side_effect = Exception("refused")
    code = cli.main(["--draft-url", "https://substack.com/p/test", "--execute"])
    evidence = json.loads(capsys.readouterr().out)
    assert code == 2
    assert evidence["result_status"] == "BLOCKED"
    assert evidence["blocker"] == "missing_cdp"
    assert evidence["publish_attempted"] is False


@patch("playwright.sync_api.sync_playwright")
def test_preflight_login_redirect_blocks(mock_sync, capsys):
    mock_p = mock_sync.return_value.__enter__.return_value
    browser = mock_p.chromium.connect_over_cdp.return_value
    context = MagicMock()
    browser.contexts = [context]
    page = MagicMock()
    context.new_page.return_value = page
    page.url = "https://substack.com/sign-in"
    code = cli.main(["--draft-url", "https://substack.com/p/test", "--execute"])
    evidence = json.loads(capsys.readouterr().out)
    assert code == 2
    assert evidence["blocker"] == "login_or_account_mismatch"
    assert evidence["publish_controls_detected"] is False


@patch("playwright.sync_api.sync_playwright")
def test_preflight_detects_controls_and_risks_without_clicking(mock_sync, capsys):
    mock_p = mock_sync.return_value.__enter__.return_value
    browser = mock_p.chromium.connect_over_cdp.return_value
    context = MagicMock()
    browser.contexts = [context]
    page = MagicMock()
    context.new_page.return_value = page
    page.url = "https://substack.com/p/test"

    def text_locator(text, exact=False):
        loc = MagicMock()
        loc.count.return_value = 1 if text in {"Publish", "Schedule", "Email", "Send email"} else 0
        return loc

    def role_locator(role, name=None):
        loc = MagicMock()
        loc.count.return_value = 1 if name == "Publish" else 0
        return loc

    page.get_by_text.side_effect = text_locator
    page.get_by_role.side_effect = role_locator
    code = cli.main(["--draft-url", "https://substack.com/p/test", "--execute"])
    evidence = json.loads(capsys.readouterr().out)
    assert code == 0
    assert evidence["result_status"] == "PASS"
    assert evidence["publish_preflight_completed"] is True
    assert evidence["publish_controls_detected"] is True
    assert evidence["schedule_risk_detected"] is True
    assert evidence["email_send_risk_detected"] is True
    assert evidence["publish_attempted"] is False
    assert not page.get_by_role.return_value.first.click.called
