import os
import subprocess
import sys

UI_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "ui",
    "daily_content_studio",
)

INDEX = os.path.join(UI_DIR, "index.html")
STYLES = os.path.join(UI_DIR, "styles.css")
APP = os.path.join(UI_DIR, "app.js")
FIXTURE_JS = os.path.join(UI_DIR, "fixture_data.js")
FIXTURE_JSON = os.path.join(UI_DIR, "daily_content_studio_ui_data_contract_fixture.json")
README = os.path.join(UI_DIR, "README.md")

REQUIRED_BANNERS = [
    "LOCAL ONLY",
    "REVIEW ONLY",
    "NOT PUBLIC-POSTABLE",
    "MANUAL REVIEW REQUIRED",
    "NO LIVE POSTING",
    "NO PLATFORM API",
    "NO PROVIDER/LLM API",
    "NO WEB SEARCH / SCRAPING / NEWS API",
    "NO FINANCIAL ADVICE",
    "NO SIGNAL LANGUAGE",
    "NO CREDENTIALS LOADED",
]

REQUIRED_PANELS = [
    "daily_run_overview",
    "source_context_panel",
    "angle_cards_panel",
    "llm_prompt_handoff_panel",
    "markdown_review_export_panel",
    "external_draft_review_panel",
    "operator_decision_ledger_panel",
    "platform_fit_panel",
    "blockers_and_limitations_panel",
    "manual_actions_panel",
    "audit_status_panel",
    "future_frontend_handoff_panel",
]


def _read(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def test_required_files_exist():
    for p in [INDEX, STYLES, APP, FIXTURE_JS, FIXTURE_JSON, README]:
        assert os.path.isfile(p), f"missing: {p}"


def test_html_has_app_shell_and_safety_header():
    html = _read(INDEX)
    assert 'id="safety-header"' in html
    assert "<main" in html
    assert 'src="app.js"' in html
    assert 'src="fixture_data.js"' in html


def test_css_defines_disabled_blocked_states():
    css = _read(STYLES)
    assert ".action-forbidden" in css
    assert "pointer-events: none" in css
    assert "cursor: not-allowed" in css


def test_js_references_only_local_fixture():
    js = _read(APP)
    assert "window.__DCS_FIXTURE__" in js
    assert "fetch(" not in js
    assert "XMLHttpRequest" not in js


def test_fixture_copy_and_embed_exist():
    assert os.path.isfile(FIXTURE_JSON)
    embed = _read(FIXTURE_JS)
    assert "window.__DCS_FIXTURE__" in embed
    assert '"packet_id"' in embed


def test_banners_present_in_embed():
    embed = _read(FIXTURE_JS)
    for b in REQUIRED_BANNERS:
        assert b in embed, f"missing banner: {b}"


def test_all_required_panels_present():
    html = _read(INDEX)
    for p in REQUIRED_PANELS:
        assert f'data-panel="{p}"' in html, f"missing panel: {p}"


def test_not_public_postable_manual_review_language():
    html = _read(INDEX).lower()
    assert "not public-postable" in html or "not_public_postable" in html
    assert "review-only" in html or "review only" in html


def test_no_live_no_api_no_credential_language():
    embed = _read(FIXTURE_JS)
    for b in [
        "NO LIVE POSTING",
        "NO PLATFORM API",
        "NO PROVIDER/LLM API",
        "NO CREDENTIALS LOADED",
    ]:
        assert b in embed



def test_manual_actions_separated():
    html = _read(INDEX)
    assert "allowed-actions" in html
    assert "forbidden-actions" in html
    js = _read(APP)
    assert "action-allowed" in js
    assert "action-forbidden" in js


def test_forbidden_actions_rendered_disabled():
    js = _read(APP)
    assert 'el("span", "action-forbidden"' in js
    css = _read(STYLES)
    assert ".action-forbidden" in css and "line-through" in css


def test_no_active_live_action_buttons():
    html = _read(INDEX)
    assert "<button" not in html.lower()


def test_no_remote_url_cdn_external_script():
    for path in [INDEX, APP, FIXTURE_JS]:
        content = _read(path)
        assert 'src="http' not in content
        assert 'href="http' not in content
        assert "cdn." not in content
        assert '<script src="//' not in content


def test_no_localstorage_sessionstorage_secret_usage():
    js = _read(APP).replace("localStorage/sessionStorage", "")
    assert "localStorage" not in js
    assert "sessionStorage" not in js


def test_no_enabled_platform_provider_api_actions():
    embed = _read(FIXTURE_JS)
    for flag in [
        '"platform_api_allowed_now": false',
        '"provider_llm_api_allowed_now": false',
        '"repo_web_search_allowed_now": false',
        '"scraping_allowed_now": false',
        '"scheduler_allowed_now": false',
        '"live_posting_enabled_now": false',
        '"credential_read_allowed_now": false',
    ]:
        assert flag in embed, f"expected {flag}"


def test_no_final_public_ready_representation():
    embed = _read(FIXTURE_JS)
    assert '"public_ready_allowed_now": false' in embed
    assert '"final_social_copy_generated": false' in embed
    assert '"publish_ready": false' in embed
    assert '"represents_final_social_copy": false' in embed


def test_no_unsafe_financial_signal_language():
    text = (_read(INDEX) + _read(APP) + _read(FIXTURE_JS)).lower()
    unsafe = [
        "our model predicts",
        "our signal says",
        "target price",
        "buy now",
        "sell now",
        "guaranteed return",
    ]
    for u in unsafe:
        assert u not in text, f"unsafe phrase present: {u}"


def test_existing_cli_summaries_still_run():
    cmds = [
        "pre-alpha-daily-content-studio-ui-data-contract-summary",
        "pre-alpha-daily-content-studio-external-draft-review-summary",
        "pre-alpha-social-platform-foundation-summary",
    ]
    for c in cmds:
        r = subprocess.run(
            [sys.executable, "-m", "live_contentops.cli", c],
            capture_output=True,
            text=True,
        )
        assert r.returncode == 0, f"{c} failed: {r.stderr}"
        assert "packet_status" in r.stdout or "validation_valid" in r.stdout

