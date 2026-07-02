import hashlib
import json
from unittest.mock import MagicMock, patch

from live_contentops import substack_operator_publish_cli as cli


def test_publish_dry_run_does_not_publish(capsys):
    code = cli.main(["--task-id", "0019"])
    evidence = json.loads(capsys.readouterr().out)
    assert code == 0
    assert evidence["result_status"] == "DRY_RUN"
    assert evidence["publish_attempted"] is False
    assert evidence["publish_completed"] is False
    assert evidence["email_send_attempted"] is False
    assert evidence["schedule_attempted"] is False


def test_publish_execute_requires_explicit_approval(capsys):
    code = cli.main(["--execute", "--draft-url", "https://substack.com/p/test", "--expected-title-sha256", "abc", "--email-mode", "no-email"])
    evidence = json.loads(capsys.readouterr().out)
    assert code == 2
    assert evidence["blocker"] == "missing_operator_publish_approval"
    assert evidence["publish_attempted"] is False


@patch("playwright.sync_api.sync_playwright")
def test_publish_title_hash_mismatch_blocks_before_click(mock_sync, capsys):
    mock_p = mock_sync.return_value.__enter__.return_value
    browser = mock_p.chromium.connect_over_cdp.return_value
    context = MagicMock()
    browser.contexts = [context]
    page = MagicMock()
    context.new_page.return_value = page
    page.url = "https://substack.com/p/test"
    page.title.return_value = "Wrong title"
    code = cli.main([
        "--execute", "--allow-publication", "--draft-url", "https://substack.com/p/test",
        "--expected-title-sha256", hashlib.sha256(b"Right title").hexdigest(), "--email-mode", "no-email"
    ])
    evidence = json.loads(capsys.readouterr().out)
    assert code == 2
    assert evidence["blocker"] == "title_hash_mismatch"
    assert evidence["publish_attempted"] is False


@patch("playwright.sync_api.sync_playwright")
def test_publish_success_mock_clicks_publish_once_or_more(mock_sync, capsys):
    mock_p = mock_sync.return_value.__enter__.return_value
    browser = mock_p.chromium.connect_over_cdp.return_value
    context = MagicMock()
    browser.contexts = [context]
    page = MagicMock()
    context.new_page.return_value = page
    page.url = "https://substack.com/p/test"
    page.title.return_value = "Expected title"
    clicked = []

    def text_locator(text, exact=False):
        loc = MagicMock()
        loc.count.return_value = 0
        loc.first.click.side_effect = lambda timeout=0: clicked.append(text)
        return loc

    def role_locator(role, name=None):
        loc = MagicMock()
        loc.count.return_value = 1 if name == "Publish" else 0
        loc.first.click.side_effect = lambda timeout=0: clicked.append(name)
        return loc

    page.get_by_text.side_effect = text_locator
    page.get_by_role.side_effect = role_locator
    code = cli.main([
        "--execute", "--allow-publication", "--draft-url", "https://substack.com/p/test",
        "--expected-title-sha256", hashlib.sha256(b"Expected title").hexdigest(), "--email-mode", "no-email"
    ])
    evidence = json.loads(capsys.readouterr().out)
    assert code == 0
    assert evidence["result_status"] == "PASS"
    assert evidence["publish_attempted"] is True
    assert evidence["publish_completed"] is True
    assert evidence["email_send_attempted"] is False
    assert "Publish" in clicked
