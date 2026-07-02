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


def make_page(*, publish=0, schedule=0, email=0, send_email=0, continue_count=0, dashboard=0, create=0, new_post=0, login=0, editor=0, url_raises=False):
    page = MagicMock()
    if url_raises:
        type(page).url = property(lambda self: (_ for _ in ()).throw(AssertionError("page.url must not be read")))

    def text_locator(text, exact=False):
        counts = {
            "Publish": publish,
            "Schedule": schedule,
            "Email": email,
            "Send email": send_email,
            "Continue": continue_count,
            "Dashboard": dashboard,
            "Create": create,
            "New post": new_post,
            "Sign in": login,
            "Log in": login,
            "Login": login,
            "Untitled": editor,
        }
        return make_locator(counts.get(text, 0))

    def role_locator(role, name=None):
        counts = {
            "Publish": publish,
            "Continue": continue_count,
            "Dashboard": dashboard,
            "Create": create,
            "New post": new_post,
            "Sign in": login,
            "Log in": login,
            "Login": login,
        }
        return make_locator(counts.get(name, 0))

    page.get_by_text.side_effect = text_locator
    page.get_by_role.side_effect = role_locator
    page.locator.return_value = make_locator(editor)
    return page


def wire_browser(mock_sync, *, pages=None, new_page=None):
    mock_p = mock_sync.return_value.__enter__.return_value
    browser = mock_p.chromium.connect_over_cdp.return_value
    context = MagicMock()
    context.pages = pages if pages is not None else []
    if new_page is not None:
        context.new_page.return_value = new_page
    browser.contexts = [context]
    return context


def assert_no_private_capture_fields(evidence):
    forbidden = PRIVATE_FIELD_NAMES & set(evidence)
    assert forbidden == set()
    assert evidence["response_body_recorded"] is False
    assert evidence["response_headers_recorded"] is False
    assert evidence["raw_secret_output"] is False


def assert_signal_fields(evidence):
    assert isinstance(evidence["editor_signal_detected"], bool)
    assert isinstance(evidence["publish_signal_detected"], bool)
    assert isinstance(evidence["continue_signal_detected"], bool)
    assert isinstance(evidence["schedule_signal_detected"], bool)
    assert isinstance(evidence["email_signal_detected"], bool)
    assert evidence["assist_hint"] in {
        "open_draft_editor",
        "editor_detected_publish_control_missing",
        "publish_control_detected_no_click",
        "login_required",
        "unknown_ui_state",
    }


def assert_safe_evidence(evidence):
    assert_no_private_capture_fields(evidence)
    assert_signal_fields(evidence)
    assert evidence["publish_attempted"] is False
    assert evidence["schedule_attempted"] is False
    assert evidence["email_send_attempted"] is False


def test_preflight_dry_run_no_browser(capsys):
    code = cli.main(["--draft-url", "https://substack.example/placeholder", "--task-id", "0018"])
    evidence = json.loads(capsys.readouterr().out)
    assert code == 0
    assert evidence["result_status"] == "DRY_RUN"
    assert evidence["current_page_class"] == "unknown"
    assert evidence["assist_hint"] == "unknown_ui_state"
    assert evidence["publish_preflight_completed"] is False
    assert evidence["browser_cdp_used"] is False
    assert_safe_evidence(evidence)


@patch("playwright.sync_api.sync_playwright")
def test_preflight_missing_cdp_blocks(mock_sync, capsys):
    mock_p = mock_sync.return_value.__enter__.return_value
    mock_p.chromium.connect_over_cdp.side_effect = Exception("refused")
    code = cli.main(["--draft-url", "https://substack.example/placeholder", "--execute"])
    evidence = json.loads(capsys.readouterr().out)
    assert code == 2
    assert evidence["result_status"] == "BLOCKED"
    assert evidence["blocker"] == "missing_cdp"
    assert evidence["current_page_class"] == "unknown"
    assert evidence["assist_hint"] == "unknown_ui_state"
    assert_safe_evidence(evidence)


@patch("playwright.sync_api.sync_playwright")
def test_preflight_login_ui_signal_blocks_without_private_url(mock_sync, capsys):
    page = make_page(login=1, url_raises=True)
    wire_browser(mock_sync, new_page=page)
    code = cli.main(["--draft-url", "https://substack.example/placeholder", "--execute"])
    evidence = json.loads(capsys.readouterr().out)
    assert code == 2
    assert evidence["blocker"] == "login_or_account_mismatch"
    assert evidence["current_page_class"] == "login"
    assert evidence["current_page_reason"] == "login_ui_signal"
    assert evidence["assist_hint"] == "login_required"
    assert evidence["publish_signal_detected"] is False
    assert evidence["publish_controls_detected"] is False
    assert_safe_evidence(evidence)


@patch("playwright.sync_api.sync_playwright")
def test_preflight_detects_controls_and_risks_without_clicking(mock_sync, capsys):
    page = make_page(publish=1, schedule=1, email=1, send_email=1, url_raises=True)
    wire_browser(mock_sync, new_page=page)

    code = cli.main(["--draft-url", "https://substack.example/placeholder", "--execute"])
    evidence = json.loads(capsys.readouterr().out)
    assert code == 0
    assert evidence["result_status"] == "PASS"
    assert evidence["current_page_class"] == "editor_or_draft_candidate"
    assert evidence["assist_hint"] == "publish_control_detected_no_click"
    assert evidence["publish_preflight_completed"] is True
    assert evidence["publish_signal_detected"] is True
    assert evidence["publish_controls_detected"] is True
    assert evidence["schedule_signal_detected"] is True
    assert evidence["email_signal_detected"] is True
    assert evidence["schedule_risk_detected"] is True
    assert evidence["email_send_risk_detected"] is True
    assert not page.get_by_role.return_value.first.click.called
    assert_safe_evidence(evidence)


@patch("playwright.sync_api.sync_playwright")
def test_use_current_draft_no_pages_blocks_current_draft_not_active(mock_sync, capsys):
    wire_browser(mock_sync, pages=[])
    code = cli.main(["--use-current-draft", "--execute"])
    evidence = json.loads(capsys.readouterr().out)
    assert code == 2
    assert evidence["blocker"] == "current_draft_not_active"
    assert evidence["current_page_class"] == "unknown"
    assert evidence["current_page_reason"] == "no_active_pages"
    assert evidence["assist_hint"] == "unknown_ui_state"
    assert_safe_evidence(evidence)


@patch("playwright.sync_api.sync_playwright")
def test_use_current_draft_dashboard_blocks_current_draft_not_active(mock_sync, capsys):
    page = make_page(dashboard=1, create=1, new_post=1, url_raises=True)
    wire_browser(mock_sync, pages=[page])
    code = cli.main(["--use-current-draft", "--execute"])
    evidence = json.loads(capsys.readouterr().out)
    assert code == 2
    assert evidence["blocker"] == "current_draft_not_active"
    assert evidence["current_page_class"] == "dashboard"
    assert evidence["assist_hint"] == "open_draft_editor"
    assert_safe_evidence(evidence)


@patch("playwright.sync_api.sync_playwright")
def test_use_current_draft_editor_candidate_missing_publish_controls_blocks_ui_uncertainty(mock_sync, capsys):
    page = make_page(editor=1, url_raises=True)
    wire_browser(mock_sync, pages=[page])
    code = cli.main(["--use-current-draft", "--execute"])
    evidence = json.loads(capsys.readouterr().out)
    assert code == 2
    assert evidence["blocker"] == "ui_uncertainty"
    assert evidence["current_page_class"] == "editor_or_draft_candidate"
    assert evidence["assist_hint"] == "editor_detected_publish_control_missing"
    assert evidence["editor_signal_detected"] is True
    assert evidence["publish_signal_detected"] is False
    assert evidence["diagnostic_interpretation"] == "publish_controls_not_detected"
    assert_safe_evidence(evidence)


@patch("playwright.sync_api.sync_playwright")
def test_task_0026_state_editor_signal_true_publish_signal_false_blocks_with_assist_hint(mock_sync, capsys):
    page = make_page(editor=1, url_raises=True)
    wire_browser(mock_sync, pages=[page])
    code = cli.main(["--use-current-draft", "--task-id", "0026", "--execute"])
    evidence = json.loads(capsys.readouterr().out)
    assert code == 2
    assert evidence["task_label"] == "TASK_0026"
    assert evidence["result_status"] == "BLOCKED"
    assert evidence["blocker"] == "ui_uncertainty"
    assert evidence["current_page_class"] == "editor_or_draft_candidate"
    assert evidence["editor_signal_detected"] is True
    assert evidence["publish_signal_detected"] is False
    assert evidence["assist_hint"] == "editor_detected_publish_control_missing"
    assert_safe_evidence(evidence)


@patch("playwright.sync_api.sync_playwright")
def test_use_current_draft_editor_candidate_with_publish_controls_passes(mock_sync, capsys):
    page = make_page(publish=1, continue_count=1, url_raises=True)
    wire_browser(mock_sync, pages=[page])
    code = cli.main(["--use-current-draft", "--execute"])
    evidence = json.loads(capsys.readouterr().out)
    assert code == 0
    assert evidence["result_status"] == "PASS"
    assert evidence["current_page_class"] == "editor_or_draft_candidate"
    assert evidence["assist_hint"] == "publish_control_detected_no_click"
    assert evidence["publish_preflight_completed"] is True
    assert evidence["publish_signal_detected"] is True
    assert evidence["publish_controls_detected"] is True
    assert evidence["continue_signal_detected"] is True
    assert evidence["continue_controls_detected"] is True
    assert_safe_evidence(evidence)


@patch("playwright.sync_api.sync_playwright")
def test_page_url_property_raises_if_accessed_but_cli_still_works(mock_sync, capsys):
    page = make_page(publish=1, url_raises=True)
    wire_browser(mock_sync, pages=[page])
    code = cli.main(["--use-current-draft", "--execute"])
    evidence = json.loads(capsys.readouterr().out)
    assert code == 0
    assert evidence["result_status"] == "PASS"
    assert evidence["current_page_class"] == "editor_or_draft_candidate"
    assert evidence["assist_hint"] == "publish_control_detected_no_click"
    assert_safe_evidence(evidence)
