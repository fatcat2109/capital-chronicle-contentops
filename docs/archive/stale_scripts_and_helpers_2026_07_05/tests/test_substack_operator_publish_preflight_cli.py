import json
from unittest.mock import MagicMock, patch

from live_contentops import substack_operator_publish_preflight_cli as cli

CONFIRM = "CONTINUE_PREFLIGHT_ONLY_NO_PUBLISH"
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


class SignalPage:
    def __init__(self, before, after=None, *, url_raises=False, title_raises=False):
        self.before = before
        self.after = after or before
        self.after_click = False
        self.continue_clicks = 0
        if url_raises:
            type(self).url = property(lambda self: (_ for _ in ()).throw(AssertionError("page.url must not be read")))
        if title_raises:
            type(self).title = lambda self: (_ for _ in ()).throw(AssertionError("page.title must not be read"))

    @property
    def state(self):
        return self.after if self.after_click else self.before

    def get_by_text(self, text, *args, **kwargs):
        counts = {
            "Publish": self.state.get("publish", 0),
            "Schedule": self.state.get("schedule", 0),
            "Email": self.state.get("email", 0),
            "Send email": self.state.get("send_email", 0),
            "Continue": self.state.get("continue_count", 0),
            "Dashboard": self.state.get("dashboard", 0),
            "Create": self.state.get("create", 0),
            "New post": self.state.get("new_post", 0),
            "Sign in": self.state.get("login", 0),
            "Log in": self.state.get("login", 0),
            "Login": self.state.get("login", 0),
            "Untitled": self.state.get("editor", 0),
        }
        return make_locator(counts.get(text, 0))

    def get_by_role(self, role, name=None, *args, **kwargs):
        counts = {
            "Publish": self.state.get("publish", 0),
            "Continue": self.state.get("continue_count", 0),
            "Dashboard": self.state.get("dashboard", 0),
            "Create": self.state.get("create", 0),
            "New post": self.state.get("new_post", 0),
            "Sign in": self.state.get("login", 0),
            "Log in": self.state.get("login", 0),
            "Login": self.state.get("login", 0),
        }
        loc = make_locator(counts.get(name, 0))
        if name == "Continue":
            first = MagicMock()
            first.click.side_effect = self._click_continue
            loc.first = first
        return loc

    def locator(self, selector, *args, **kwargs):
        return make_locator(self.state.get("editor", 0))

    def _click_continue(self, **kwargs):
        self.continue_clicks += 1
        self.after_click = True

    def wait_for_load_state(self, *args, **kwargs):
        return None

    def wait_for_timeout(self, *args, **kwargs):
        return None

    def close(self):
        return None

    def goto(self, *args, **kwargs):
        return None


def make_page(*, publish=0, schedule=0, email=0, send_email=0, continue_count=0, dashboard=0, create=0, new_post=0, login=0, editor=0, url_raises=False, title_raises=False):
    return SignalPage(
        {
            "publish": publish,
            "schedule": schedule,
            "email": email,
            "send_email": send_email,
            "continue_count": continue_count,
            "dashboard": dashboard,
            "create": create,
            "new_post": new_post,
            "login": login,
            "editor": editor,
        },
        url_raises=url_raises,
        title_raises=title_raises,
    )


def make_continue_page(*, before=None, after=None, url_raises=True, title_raises=True):
    return SignalPage(before or {"continue_count": 1}, after or {"publish": 1}, url_raises=url_raises, title_raises=title_raises)


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
    for key in [
        "editor_signal_detected",
        "publish_signal_detected",
        "continue_signal_detected",
        "schedule_signal_detected",
        "email_signal_detected",
        "before_continue_signal_detected",
        "after_publish_signal_detected",
        "after_continue_signal_detected",
        "after_schedule_signal_detected",
        "after_email_signal_detected",
        "continue_preflight_clicked",
    ]:
        assert isinstance(evidence[key], bool)
    assert isinstance(evidence["continue_preflight_click_count"], int)
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
    assert evidence["assist_hint"] == "login_required"
    assert_safe_evidence(evidence)


@patch("playwright.sync_api.sync_playwright")
def test_preflight_detects_controls_and_risks_without_clicking(mock_sync, capsys):
    page = make_page(publish=1, schedule=1, email=1, send_email=1, url_raises=True)
    wire_browser(mock_sync, new_page=page)
    code = cli.main(["--draft-url", "https://substack.example/placeholder", "--execute"])
    evidence = json.loads(capsys.readouterr().out)
    assert code == 0
    assert evidence["result_status"] == "PASS"
    assert evidence["assist_hint"] == "publish_control_detected_no_click"
    assert evidence["publish_signal_detected"] is True
    assert evidence["schedule_signal_detected"] is True
    assert evidence["email_signal_detected"] is True
    assert page.continue_clicks == 0
    assert_safe_evidence(evidence)


@patch("playwright.sync_api.sync_playwright")
def test_use_current_draft_no_pages_blocks_current_draft_not_active(mock_sync, capsys):
    wire_browser(mock_sync, pages=[])
    code = cli.main(["--use-current-draft", "--execute"])
    evidence = json.loads(capsys.readouterr().out)
    assert code == 2
    assert evidence["blocker"] == "current_draft_not_active"
    assert evidence["current_page_class"] == "unknown"
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
    assert page.continue_clicks == 0
    assert_safe_evidence(evidence)


@patch("playwright.sync_api.sync_playwright")
def test_use_current_draft_editor_candidate_missing_publish_controls_blocks_ui_uncertainty(mock_sync, capsys):
    page = make_page(editor=1, url_raises=True)
    wire_browser(mock_sync, pages=[page])
    code = cli.main(["--use-current-draft", "--execute"])
    evidence = json.loads(capsys.readouterr().out)
    assert code == 2
    assert evidence["blocker"] == "ui_uncertainty"
    assert evidence["assist_hint"] == "editor_detected_publish_control_missing"
    assert evidence["editor_signal_detected"] is True
    assert evidence["publish_signal_detected"] is False
    assert page.continue_clicks == 0
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
    assert evidence["assist_hint"] == "publish_control_detected_no_click"
    assert evidence["publish_signal_detected"] is True
    assert evidence["continue_signal_detected"] is True
    assert page.continue_clicks == 0
    assert_safe_evidence(evidence)


@patch("playwright.sync_api.sync_playwright")
def test_page_url_property_raises_if_accessed_but_cli_still_works(mock_sync, capsys):
    page = make_page(publish=1, url_raises=True, title_raises=True)
    wire_browser(mock_sync, pages=[page])
    code = cli.main(["--use-current-draft", "--execute"])
    evidence = json.loads(capsys.readouterr().out)
    assert code == 0
    assert evidence["result_status"] == "PASS"
    assert evidence["assist_hint"] == "publish_control_detected_no_click"
    assert_safe_evidence(evidence)


@patch("playwright.sync_api.sync_playwright")
def test_continue_preflight_missing_confirmation_blocks_before_click(mock_sync, capsys):
    page = make_continue_page()
    wire_browser(mock_sync, pages=[page])
    code = cli.main(["--use-current-draft", "--execute", "--allow-continue-preflight-click"])
    evidence = json.loads(capsys.readouterr().out)
    assert code == 2
    assert evidence["blocker"] == "continue_preflight_confirmation_required"
    assert evidence["continue_preflight_clicked"] is False
    assert evidence["continue_preflight_click_count"] == 0
    assert page.continue_clicks == 0
    assert_safe_evidence(evidence)


@patch("playwright.sync_api.sync_playwright")
def test_continue_preflight_wrong_confirmation_blocks_before_click(mock_sync, capsys):
    page = make_continue_page()
    wire_browser(mock_sync, pages=[page])
    code = cli.main(["--use-current-draft", "--execute", "--allow-continue-preflight-click", "--operator-confirmation", "WRONG"])
    evidence = json.loads(capsys.readouterr().out)
    assert code == 2
    assert evidence["blocker"] == "continue_preflight_confirmation_required"
    assert evidence["continue_preflight_clicked"] is False
    assert page.continue_clicks == 0
    assert_safe_evidence(evidence)


@patch("playwright.sync_api.sync_playwright")
def test_continue_preflight_current_tab_not_editor_blocks_before_click(mock_sync, capsys):
    page = make_page(dashboard=1, create=1, url_raises=True)
    wire_browser(mock_sync, pages=[page])
    code = cli.main(["--use-current-draft", "--execute", "--allow-continue-preflight-click", "--operator-confirmation", CONFIRM])
    evidence = json.loads(capsys.readouterr().out)
    assert code == 2
    assert evidence["blocker"] == "current_draft_not_active"
    assert evidence["continue_preflight_clicked"] is False
    assert page.continue_clicks == 0
    assert_safe_evidence(evidence)


@patch("playwright.sync_api.sync_playwright")
def test_continue_preflight_schedule_or_email_before_click_blocks_before_click(mock_sync, capsys):
    page = make_continue_page(before={"continue_count": 1, "schedule": 1, "email": 1})
    wire_browser(mock_sync, pages=[page])
    code = cli.main(["--use-current-draft", "--execute", "--allow-continue-preflight-click", "--operator-confirmation", CONFIRM])
    evidence = json.loads(capsys.readouterr().out)
    assert code == 2
    assert evidence["blocker"] == "pre_continue_schedule_or_email_risk_detected"
    assert evidence["continue_preflight_clicked"] is False
    assert page.continue_clicks == 0
    assert_safe_evidence(evidence)


@patch("playwright.sync_api.sync_playwright")
def test_continue_preflight_safe_click_once_then_publish_detected_passes(mock_sync, capsys):
    page = make_continue_page(before={"continue_count": 1}, after={"publish": 1, "continue_count": 1})
    wire_browser(mock_sync, pages=[page])
    code = cli.main(["--use-current-draft", "--execute", "--allow-continue-preflight-click", "--operator-confirmation", CONFIRM])
    evidence = json.loads(capsys.readouterr().out)
    assert code == 0
    assert evidence["result_status"] == "PASS"
    assert evidence["blocker"] is None
    assert evidence["continue_preflight_clicked"] is True
    assert evidence["continue_preflight_click_count"] == 1
    assert page.continue_clicks == 1
    assert evidence["before_continue_signal_detected"] is True
    assert evidence["after_publish_signal_detected"] is True
    assert evidence["after_schedule_signal_detected"] is False
    assert evidence["after_email_signal_detected"] is False
    assert evidence["assist_hint"] == "publish_control_detected_no_click"
    assert evidence["publish_attempted"] is False
    assert_safe_evidence(evidence)


@patch("playwright.sync_api.sync_playwright")
def test_continue_preflight_safe_click_once_then_schedule_email_detected_blocks(mock_sync, capsys):
    page = make_continue_page(before={"continue_count": 1}, after={"schedule": 1, "email": 1})
    wire_browser(mock_sync, pages=[page])
    code = cli.main(["--use-current-draft", "--execute", "--allow-continue-preflight-click", "--operator-confirmation", CONFIRM])
    evidence = json.loads(capsys.readouterr().out)
    assert code == 2
    assert evidence["blocker"] == "post_continue_schedule_or_email_risk_detected"
    assert evidence["continue_preflight_clicked"] is True
    assert evidence["continue_preflight_click_count"] == 1
    assert page.continue_clicks == 1
    assert evidence["after_schedule_signal_detected"] is True
    assert evidence["after_email_signal_detected"] is True
    assert_safe_evidence(evidence)
