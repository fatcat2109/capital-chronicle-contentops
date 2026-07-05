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
    assert evidence["draft_created"] is False
    assert evidence["publish_attempted"] is False
    assert evidence["schedule_attempted"] is False
    assert evidence["email_send_attempted"] is False
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
    assert evidence["draft_created"] is False
    assert evidence["sent"] is False
    assert evidence["publish_attempted"] is False
    assert evidence["schedule_attempted"] is False
    assert evidence["email_send_attempted"] is False


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
    mock_role = MagicMock()
    mock_role.first = mock_role
    mock_role.wait_for.side_effect = Exception("timeout finding role textbox")
    mock_page.locator.return_value = mock_locator
    mock_page.get_by_role.return_value = mock_role

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
    mock_body_locator.nth.return_value = mock_body_locator
    mock_body_locator.wait_for.side_effect = Exception("timeout finding body")
    
    def mock_loc(sel):
        if "Title" in sel or "title" in sel:
            return mock_title_locator
        return mock_body_locator

    mock_role = MagicMock()
    mock_role.nth.return_value = mock_body_locator
    mock_page.locator = mock_loc
    mock_page.get_by_role.return_value = mock_role

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
    assert evidence["draft_created"] is True
    assert evidence["sent"] is True
    assert evidence["publish_attempted"] is False
    assert evidence["schedule_attempted"] is False
    assert evidence["email_send_attempted"] is False
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


def test_cli_secret_leakage_guard():
    from live_contentops.cli_safety import assert_clean_of_secrets
    import pytest
    bad_evidence = {"task_label": "TASK_0013", "leaked_secret": "my_secret_token_123"}
    with pytest.raises(AssertionError, match="Secret leakage detected"):
        assert_clean_of_secrets(bad_evidence, ["my_secret_token_123"])


def test_cli_dry_run_excludes_env_secrets_from_output(tmp_path, capsys):
    fake_secret = "SECRET_SUBSTACK_COOKIE_ABC"
    out = tmp_path / "evidence.json"
    code = cli.main(
        [
            "--title", "Test Title",
            "--body", "Test Body",
            "--output", str(out)
        ],
        secrets=[fake_secret]
    )
    assert code == 0
    evidence = json.loads(out.read_text(encoding="utf-8"))
    printed = capsys.readouterr().out
    assert fake_secret not in printed
    assert fake_secret not in json.dumps(evidence)


def test_cli_dry_run_fails_if_secret_leaked(tmp_path):
    fake_secret = "Test Body" # Exists in the body, which might go into evidence fields if not careful, wait, body is NOT printed raw in the evidence except as message_sha256/message_length. But if we try to inject it as task-id or title, it would leak.
    # Let's test that if we inject a secret that is in the title, it gets caught!
    fake_secret = "SECRET_IN_TITLE_XYZ"
    out = tmp_path / "evidence.json"
    
    # Wait, the CLI doesn't print title in evidence. Let's see if we inject a secret that matches "TASK_0013" (which is in task_label)
    # Yes, task_label contains TASK_0013. If we inject "TASK_0013" as a secret, assert_clean_of_secrets should raise AssertionError!
    import pytest
    with pytest.raises(AssertionError, match="Secret leakage detected"):
        cli.main(
            [
                "--title", "Test Title",
                "--body", "Test Body",
                "--task-id", "0013",
                "--output", str(out)
            ],
            secrets=["TASK_0013"]
        )

