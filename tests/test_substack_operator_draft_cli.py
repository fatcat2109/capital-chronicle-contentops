import json
from unittest.mock import MagicMock, patch
import pytest

from live_contentops import substack_operator_draft_cli as cli


def test_cli_dry_run_writes_redacted_evidence(tmp_path, capsys):
    out = tmp_path / "evidence.json"
    code = cli.main([
        "--title", "Capital Chronicle Substack CLI dry run.",
        "--body", "Body content. No market guidance.",
        "--output", str(out)
    ])
    assert code == 0
    evidence = json.loads(out.read_text(encoding="utf-8"))
    printed = capsys.readouterr().out
    assert evidence["task_label"] == "TASK_0000"
    assert evidence["result_status"] == "DRY_RUN"
    assert evidence["sent"] is False
    assert evidence["request_count_attempted"] == 0
    assert evidence["browser_cdp_used"] is False


@patch("playwright.sync_api.sync_playwright")
def test_cli_execute_missing_cdp(mock_sync, capsys):
    mock_p = mock_sync.return_value.__enter__.return_value
    mock_p.chromium.connect_over_cdp.side_effect = Exception("cdp connection refused")

    code = cli.main([
        "--title", "Test Title",
        "--body", "Test Body",
        "--execute"
    ])
    assert code == 2
    evidence = json.loads(capsys.readouterr().out)
    assert evidence["result_status"] == "BLOCKED"
    assert evidence["blocker"] == "missing_cdp"
    assert "cdp_connection_failed" in evidence["diagnostic_interpretation"]
    assert evidence["request_count_attempted"] == 0


@patch("playwright.sync_api.sync_playwright")
def test_cli_execute_login_redirect(mock_sync, capsys):
    mock_p = mock_sync.return_value.__enter__.return_value
    mock_browser = mock_p.chromium.connect_over_cdp.return_value
    mock_context = MagicMock()
    mock_browser.contexts = [mock_context]
    mock_page = MagicMock()
    mock_context.new_page.return_value = mock_page
    
    # Redirected to sign-in page
    mock_page.url = "https://substack.com/sign-in?redirect=publish/post"

    code = cli.main([
        "--title", "Test Title",
        "--body", "Test Body",
        "--execute"
    ])
    assert code == 2
    evidence = json.loads(capsys.readouterr().out)
    assert evidence["result_status"] == "BLOCKED"
    assert evidence["blocker"] == "login_or_account_mismatch"
    assert "redirected_to_login" in evidence["diagnostic_interpretation"]
    assert evidence["request_count_attempted"] == 1


@patch("playwright.sync_api.sync_playwright")
def test_cli_execute_ui_uncertainty_title(mock_sync, capsys):
    mock_p = mock_sync.return_value.__enter__.return_value
    mock_browser = mock_p.chromium.connect_over_cdp.return_value
    mock_context = MagicMock()
    mock_browser.contexts = [mock_context]
    mock_page = MagicMock()
    mock_context.new_page.return_value = mock_page
    mock_page.url = "https://substack.com/publish/post"
    
    mock_locator = MagicMock()
    mock_locator.first = mock_locator
    mock_locator.wait_for.side_effect = Exception("timeout finding title")
    mock_page.locator.return_value = mock_locator

    code = cli.main([
        "--title", "Test Title",
        "--body", "Test Body",
        "--execute"
    ])
    assert code == 2
    evidence = json.loads(capsys.readouterr().out)
    assert evidence["result_status"] == "BLOCKED"
    assert evidence["blocker"] == "ui_uncertainty"
    assert "title_selector_failed" in evidence["diagnostic_interpretation"]
    assert evidence["request_count_attempted"] == 1


@patch("playwright.sync_api.sync_playwright")
def test_cli_execute_ui_uncertainty_body(mock_sync, capsys):
    mock_p = mock_sync.return_value.__enter__.return_value
    mock_browser = mock_p.chromium.connect_over_cdp.return_value
    mock_context = MagicMock()
    mock_browser.contexts = [mock_context]
    mock_page = MagicMock()
    mock_context.new_page.return_value = mock_page
    mock_page.url = "https://substack.com/publish/post"
    
    # Title locator succeeds, but body locator fails
    mock_title_locator = MagicMock()
    mock_title_locator.first = mock_title_locator
    
    mock_body_locator = MagicMock()
    mock_body_locator.first = mock_body_locator
    mock_body_locator.wait_for.side_effect = Exception("timeout finding body")
    
    def mock_loc(sel):
        if "Title" in sel or "title" in sel:
            return mock_title_locator
        return mock_body_locator

    mock_page.locator = mock_loc

    code = cli.main([
        "--title", "Test Title",
        "--body", "Test Body",
        "--execute"
    ])
    assert code == 2
    evidence = json.loads(capsys.readouterr().out)
    assert evidence["result_status"] == "BLOCKED"
    assert evidence["blocker"] == "ui_uncertainty"
    assert "body_selector_failed" in evidence["diagnostic_interpretation"]
    assert evidence["request_count_attempted"] == 1


@patch("playwright.sync_api.sync_playwright")
def test_cli_execute_success(mock_sync, capsys):
    mock_p = mock_sync.return_value.__enter__.return_value
    mock_browser = mock_p.chromium.connect_over_cdp.return_value
    mock_context = MagicMock()
    mock_browser.contexts = [mock_context]
    mock_page = MagicMock()
    mock_context.new_page.return_value = mock_page
    mock_page.url = "https://substack.com/publish/post"
    
    mock_locator = MagicMock()
    mock_locator.first = mock_locator
    mock_page.locator.return_value = mock_locator

    code = cli.main([
        "--title", "Test Title",
        "--body", "Test Body",
        "--execute"
    ])
    assert code == 0
    evidence = json.loads(capsys.readouterr().out)
    assert evidence["result_status"] == "PASS"
    assert evidence["sent"] is True
    assert evidence["blocker"] is None
    assert evidence["diagnostic_interpretation"] == "draft_created_and_autosaved"
    assert evidence["request_count_attempted"] == 1
    assert evidence["browser_cdp_used"] is True


def test_cli_requires_args():
    try:
        cli.main([])
    except SystemExit as exc:
        assert exc.code == 2
    else:
        raise AssertionError("missing args should exit")
