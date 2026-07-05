import json
import os
import subprocess
import sys

from live_contentops import institutional_shell_prototype as shell

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
SHELL_DIR = os.path.join(BASE_DIR, "ui", "institutional_shell")


def _read(name):
    with open(os.path.join(SHELL_DIR, name), "r", encoding="utf-8") as f:
        return f.read()


def test_valid_packet_passes():
    packet = shell.build_packet()
    res = shell.validate_packet(packet)
    assert res["valid"], res["errors"]
    assert packet["packet_status"] == "pass"


def test_index_html_exists():
    assert os.path.isfile(os.path.join(SHELL_DIR, "index.html"))


def test_styles_css_exists():
    assert os.path.isfile(os.path.join(SHELL_DIR, "styles.css"))


def test_app_js_exists():
    assert os.path.isfile(os.path.join(SHELL_DIR, "app.js"))


def test_fixture_data_js_exists():
    assert os.path.isfile(os.path.join(SHELL_DIR, "fixture_data.js"))


def test_readme_exists():
    assert os.path.isfile(os.path.join(SHELL_DIR, "README.md"))


def test_all_12_screens_present():
    txt = _read("fixture_data.js")
    for sid in shell.REQUIRED_SCREENS:
        assert sid in txt, sid


def test_all_nav_labels_present():
    txt = _read("fixture_data.js")
    for title in ["Command Center", "Content Lane Control", "Daily Content Studio",
                  "Draft Inspector", "Grounded News Angle Lab", "Publish Readiness Tower",
                  "Telegram Pilot Gate", "Approval Queue", "Content Calendar",
                  "Evidence Vault", "Visual Export Studio", "Settings / Safety Policy"]:
        assert title in txt, title


def test_required_safety_banners_present():
    txt = _read("fixture_data.js")
    for banner in shell.REQUIRED_SAFETY_BANNERS:
        assert banner in txt, banner


def test_required_components_present():
    txt = _read("fixture_data.js")
    for comp in shell.REQUIRED_COMPONENTS:
        assert comp in txt, comp


def test_screenshot_safe_mode_present():
    txt = _read("fixture_data.js")
    assert "screenshot_safe_mode" in txt
    assert "SCREENSHOT-SAFE" in txt


def test_redaction_policy_visible():
    txt = _read("fixture_data.js")
    assert "redaction_policy" in txt
    assert "redact_secrets" in txt


def test_telegram_pilot_gate_disables_live():
    txt = _read("fixture_data.js")
    for needed in ("getme_call", "sendmessage", "live_adapter"):
        assert needed in txt, needed


def test_publish_readiness_tower_disables_live():
    txt = _read("fixture_data.js")
    assert "one_button_publish_all" in txt
    assert "Platform API disabled" in txt
    assert "Scheduler disabled" in txt


def test_content_calendar_excludes_live_states():
    txt = _read("fixture_data.js")
    for needed in ("scheduled_post", "auto_publish", "live_state"):
        assert needed in txt, needed


def test_settings_does_not_display_credentials():
    txt = _read("fixture_data.js")
    assert "credential_display" in txt  # listed as forbidden control
    assert "no_credentials_displayed" in txt


def test_no_external_cdn_or_remote_url():
    for name in ("index.html", "styles.css", "app.js", "fixture_data.js"):
        txt = _read(name)
        assert "http://" not in txt, name
        assert "https://" not in txt, name


def test_no_network_calls():
    for name in ("app.js", "fixture_data.js", "index.html"):
        txt = _read(name)
        assert "fetch(" not in txt, name
        assert "new XMLHttpRequest" not in txt, name
        assert "new WebSocket" not in txt, name
        assert "new EventSource" not in txt, name


def test_no_backend_required():
    packet = shell.build_packet()
    assert packet["backend_server_required"] is False


def test_no_dependency_files_added():
    for dep in ("package.json", "package-lock.json", "yarn.lock", "vite.config.js"):
        assert not os.path.isfile(os.path.join(SHELL_DIR, dep)), dep


def test_no_token_like_secret_visible():
    assert shell._count_secret_hits() == 0


def test_no_raw_env_path_visible():
    for name in ("index.html", "styles.css", "app.js", "fixture_data.js"):
        txt = _read(name)
        assert ".env" not in txt, name


def test_no_actionable_signal_text():
    banned = ["buy now", "sell now", "go long", "go short", "bullish", "bearish",
              "buy/sell", "alpha signal"]
    for name in ("app.js", "fixture_data.js", "styles.css", "index.html"):
        txt = _read(name).lower()
        for term in banned:
            assert term not in txt, (name, term)


def test_no_red_green_market_direction_semantics():
    packet = shell.build_packet()
    assert packet["red_green_market_direction_semantics"] is False


def test_forbidden_controls_only_disabled():
    # app.js renders forbidden controls only as disabled spans, never wired actions.
    app = _read("app.js")
    assert "disabled-control" in app
    assert "aria-disabled" in app


def test_active_frontend_scope_within_shell():
    packet = shell.build_packet()
    assert "ui/institutional_shell" in packet["active_frontend_code_changed_scope"]


def test_runtime_authority_true_fails():
    packet = shell.build_packet()
    packet["runtime_authority"] = True
    res = shell.validate_packet(packet)
    assert not res["valid"]
    assert "runtime_authority_must_be_false" in res["errors"]


def test_backend_server_required_true_fails():
    packet = shell.build_packet()
    packet["backend_server_required"] = True
    res = shell.validate_packet(packet)
    assert not res["valid"]
    assert "backend_server_required_must_be_false" in res["errors"]


def test_frontend_dependencies_added_true_fails():
    packet = shell.build_packet()
    packet["frontend_dependencies_added"] = True
    res = shell.validate_packet(packet)
    assert not res["valid"]
    assert "frontend_dependencies_added_must_be_false" in res["errors"]


def test_live_posting_enabled_true_fails():
    packet = shell.build_packet()
    packet["live_posting_enabled_now"] = True
    res = shell.validate_packet(packet)
    assert not res["valid"]
    assert "live_posting_enabled_now_must_be_false" in res["errors"]


def test_packet_status_pass_with_errors_fails():
    packet = shell.build_packet()
    packet["runtime_authority"] = True
    packet["packet_status"] = "pass"
    res = shell.validate_packet(packet)
    assert not res["valid"]
    assert "packet_status_pass_but_errors_exist" in res["errors"]


def test_summary_validation_valid_true():
    s = shell.summary()
    assert s["validation_valid"] is True
    assert s["packet_status"] == "pass"
    assert s["screen_count"] == 12
    assert s["component_count"] == 26
    assert s["safety_banner_count"] == 9
    assert s["shell_file_count"] == 5
    assert s["fetch_call_count"] == 0
    assert s["external_dependency_count"] == 0
    assert s["remote_url_count"] == 0
    assert s["secret_visible_count"] == 0
    assert s["screenshot_safe_mode_present"] is True
    assert s["redaction_policy_visible"] is True


def test_cli_summary_runs():
    r = subprocess.run(
        [sys.executable, "-m", "live_contentops.cli",
         "pre-alpha-institutional-shell-prototype-summary"],
        capture_output=True,
        text=True,
        cwd=BASE_DIR,
    )
    assert r.returncode == 0, r.stderr
    out = json.loads(r.stdout)
    assert out["packet_status"] == "pass"
    assert out["validation_valid"] is True
    assert out["secret_visible_count"] == 0
