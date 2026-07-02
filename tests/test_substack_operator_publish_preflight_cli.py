import json
from unittest.mock import MagicMock, patch

from live_contentops import substack_operator_publish_preflight_cli as cli

PRIVATE_FIELD_NAMES = {
    "current_url",
    "page_url",
    "url",
    "draft_url",
    "private_url",
    "page_title",
    "title",
    "body",
    "body_text",
    "dom",
    "dom_dump",
    "screenshot",
    "screenshot_path",
}


def make_locator(count):
    loc = MagicMock()
    loc.count.return_value = count
    return loc


def wire_browser(mock_sync, *, pages=None, new_page=None):
    mock_p = mock_sync.return_value.__enter__.return_value
    browser = mock_p.chromium.connect_over_cdp.return_value
    context = MagicMock()
    context.pages = pages if pages is not None else []
    if new_page is not None:
        context.new_page.return_value = new_page
    browser.contexts = [context]
    return context


def wire_control_counts(page, *, publish=0, schedule=0, email=0, send_email=0, continue_count=0):
    def text_locator(text, exact=False):
        counts = {
            "Publish": publish,
            "Schedule": schedule,
            "Email": email,
            "Send email": send_email,
            "Continue": continue_count,
        }
        return make_locator(counts.get(text, 0))

    def role_locator(role, name=None):
        counts = {"Publish": publish, "Continue": continue_count}
        return make_locator(counts.get(name, 0))

    page.get_by_text.side_effect = text_locator
    page.get_by_role.side_effect = role_locator


def assert_no_private_capture_fields(evidence):
    forbidden = PRIVATE_FIELD_NAMES & set(evidence)
    assert forbidden == set()
    assert evidence["response_body_recorded"] is False
    assert evidence["response_headers_recorded"] is False
    assert evidence["raw_secret_output"] is False


def test_preflight_dry_run_no_browser(capsys):
    code = cli.main(["--draft-url", "https://substack.com/p/test", "--task-id", "0018"])
    evidence = json.loads(capsys.readouterr().out)
    assert code == 0
    assert evidence["result_status"] == "DRY_RUN"
    assert evidence["current_page_class"] == "unknown"
    assert evidence["publish_preflight_completed"] is False
    assert evidence["publish_attempted"] is False
    assert evidence["schedule_attempted"] is False
    assert evidence["email_send_attempted"] is False
    assert evidence["browser_cdp_used"] is False
    assert_no_private_capture_fields(evidence)


@patch("playwright.sync_api.sync_playwright")
def test_preflight_missing_cdp_blocks(mock_sync, capsys):
    mock_p = mock_sync.return_value.__enter__.return_value
    mock_p.chromium.connect_over_cdp.side_effect = Exception("refused")
    code = cli.main(["--draft-url", "https://substack.com/p/test", "--execute"])
    evidence = json.loads(capsys.readouterr().out)
    assert code == 2
    assert evidence["result_status"] == "BLOCKED"
    assert evidence["blocker"] == "missing_cdp"
    assert evidence["current_page_class"] == "unknown"
    assert evidence["publish_attempted"] is False
    assert_no_private_capture_fields(evidence)


@patch("playwright.sync_api.sync_playwright")
def test_preflight_login_redirect_blocks_without_private_url(mock_sync, capsys):
    page = MagicMock()
    page.url = "https://substack.com/sign-in"
    wire_browser(mock_sync, new_page=page)
    code = cli.main(["--draft-url", "https://substack.com/p/test", "--execute"])
    evidence = json.loads(capsys.readouterr().out)
    assert code == 2
    assert evidence["blocker"] == "login_or_account_mismatch"
    assert evidence["current_page_class"] == "login"
    assert evidence["diagnostic_interpretation"] == "redirected_to_login"
    assert evidence["publish_controls_detected"] is False
    assert_no_private_capture_fields(evidence)


@patch("playwright.sync_api.sync_playwright")
def test_preflight_detects_controls_and_risks_without_clicking(mock_sync, capsys):
    page = MagicMock()
    page.url = "https://substack.com/p/test"
    wire_browser(mock_sync, new_page=page)
    wire_control_counts(page, publish=1, schedule=1, email=1, send_email=1)

    code = cli.main(["--draft-url", "https://substack.com/p/test", "--execute"])
    evidence = json.loads(capsys.readouterr().out)
    assert code == 0
    assert evidence["result_status"] == "PASS"
    assert evidence["current_page_class"] == "editor_or_draft_candidate"
    assert evidence["publish_preflight_completed"] is True
    assert evidence["publish_controls_detected"] is True
    assert evidence["schedule_risk_detected"] is True
    assert evidence["email_send_risk_detected"] is True
    assert evidence["publish_attempted"] is False
    assert not page.get_by_role.return_value.first.click.called
    assert_no_private_capture_fields(evidence)


@patch("playwright.sync_api.sync_playwright")
def test_use_current_draft_no_pages_blocks_current_draft_not_active(mock_sync, capsys):
    wire_browser(mock_sync, pages=[])
    code = cli.main(["--use-current-draft", "--execute"])
    evidence = json.loads(capsys.readouterr().out)
    assert code == 2
    assert evidence["blocker"] == "current_draft_not_active"
    assert evidence["current_page_class"] == "unknown"
    assert evidence["current_page_reason"] == "no_active_pages"
    assert evidence["publish_attempted"] is False
    assert_no_private_capture_fields(evidence)


@patch("playwright.sync_api.sync_playwright")
def test_use_current_draft_dashboard_blocks_current_draft_not_active(mock_sync, capsys):
    page = MagicMock()
    page.url = "https://substack.com/dashboard"
    wire_browser(mock_sync, pages=[page])
    code = cli.main(["--use-current-draft", "--execute"])
    evidence = json.loads(capsys.readouterr().out)
    assert code == 2
    assert evidence["blocker"] == "current_draft_not_active"
    assert evidence["current_page_class"] == "dashboard"
    assert evidence["current_page_reason"] == "dashboard_path_hint"
    assert evidence["publish_attempted"] is False
    assert_no_private_capture_fields(evidence)


@patch("playwright.sync_api.sync_playwright")
def test_use_current_draft_editor_candidate_missing_publish_controls_blocks_ui_uncertainty(mock_sync, capsys):
    page = MagicMock()
    page.url = "https://substack.com/p/test"
    wire_browser(mock_sync, pages=[page])
    wire_control_counts(page, publish=0)
    code = cli.main(["--use-current-draft", "--execute"])
    evidence = json.loads(capsys.readouterr().out)
    assert code == 2
    assert evidence["blocker"] == "ui_uncertainty"
    assert evidence["current_page_class"] == "editor_or_draft_candidate"
    assert evidence["diagnostic_interpretation"] == "publish_controls_not_detected"
    assert evidence["publish_attempted"] is False
    assert_no_private_capture_fields(evidence)


@patch("playwright.sync_api.sync_playwright")
def test_use_current_draft_editor_candidate_with_publish_controls_passes(mock_sync, capsys):
    page = MagicMock()
    page.url = "https://substack.com/p/test"
    wire_browser(mock_sync, pages=[page])
    wire_control_counts(page, publish=1, continue_count=1)
    code = cli.main(["--use-current-draft", "--execute"])
    evidence = json.loads(capsys.readouterr().out)
    assert code == 0
    assert evidence["result_status"] == "PASS"
    assert evidence["current_page_class"] == "editor_or_draft_candidate"
    assert evidence["publish_preflight_completed"] is True
    assert evidence["publish_controls_detected"] is True
    assert evidence["continue_controls_detected"] is True
    assert evidence["publish_attempted"] is False
    assert_no_private_capture_fields(evidence)
