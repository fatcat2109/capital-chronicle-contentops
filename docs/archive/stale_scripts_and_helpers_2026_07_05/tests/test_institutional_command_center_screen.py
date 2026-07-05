import json
import os
import subprocess
import sys

from live_contentops import institutional_command_center_screen as cc

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
SHELL_DIR = os.path.join(BASE_DIR, "ui", "institutional_shell")


def _read(name):
    with open(os.path.join(SHELL_DIR, name), "r", encoding="utf-8") as f:
        return f.read()


def test_valid_packet_passes():
    packet = cc.build_packet()
    res = cc.validate_packet(packet)
    assert res["valid"], res["errors"]
    assert packet["packet_status"] == "pass"


def test_shell_files_exist():
    for name in ("index.html", "styles.css", "app.js", "fixture_data.js"):
        assert os.path.isfile(os.path.join(SHELL_DIR, name)), name


def test_command_center_screen_exists():
    txt = _read("fixture_data.js")
    assert "command_center" in txt
    assert "command_center_detail" in txt


def test_hero_status_band_exists():
    txt = _read("fixture_data.js")
    assert "hero_status_band" in txt
    assert "Capital Chronicle ContentOps Command Center" in txt


def test_safety_ribbon_includes_all_required():
    txt = _read("fixture_data.js")
    for item in cc.REQUIRED_SAFETY_RIBBON:
        assert item in txt, item


def test_executive_status_cards_present():
    txt = _read("fixture_data.js")
    for card in ("System Safety", "Build Baseline", "Publish Automation",
                 "Telegram Pilot Gate", "Evidence / Audit", "UI Rebuild Track",
                 "Content Studio Track", "Residual Drift"):
        assert card in txt, card


def test_gate_timeline_includes_accepted():
    txt = _read("fixture_data.js")
    for g in ("0157", "0158", "0159", "0160", "0161"):
        assert g in txt, g


def test_gate_timeline_includes_future():
    txt = _read("fixture_data.js")
    for g in ("0162", "0163", "0164", "0165", "0166", "0167", "0168"):
        assert g in txt, g


def test_blocked_action_matrix_live_posting():
    txt = _read("fixture_data.js")
    assert "live_posting" in txt


def test_blocked_action_matrix_scheduler():
    txt = _read("fixture_data.js")
    assert "scheduler" in txt


def test_blocked_action_matrix_platform_api():
    txt = _read("fixture_data.js")
    assert "platform_api" in txt


def test_blocked_action_matrix_provider_api():
    txt = _read("fixture_data.js")
    assert "provider_llm_api" in txt


def test_blocked_action_matrix_scraping():
    txt = _read("fixture_data.js")
    assert "scraping" in txt


def test_blocked_action_matrix_replies_dms():
    txt = _read("fixture_data.js")
    assert "autonomous_replies_dms" in txt


def test_blocked_action_matrix_publish_all():
    txt = _read("fixture_data.js")
    assert "one_button_publish_all" in txt


def test_blocked_action_matrix_credential_display():
    txt = _read("fixture_data.js")
    assert "credential_display" in txt


def test_evidence_summary_keys_present():
    txt = _read("fixture_data.js")
    for key in ("full_suite_result", "focused_tests_result", "cli_summaries",
                "secret_scan_status", "forbidden_scope_status", "git_status_summary"):
        assert key in txt, key


def test_telegram_gate_redacted_credential_presence():
    txt = _read("fixture_data.js")
    assert "redacted_presence_only" in txt


def test_telegram_gate_getme_not_run():
    txt = _read("fixture_data.js")
    assert "not_run_unless_explicitly_executed_later" in txt


def test_telegram_gate_channel_permission_unvalidated():
    txt = _read("fixture_data.js")
    assert "channel_write_permission" in txt
    assert "unvalidated" in txt


def test_telegram_gate_send_message_disabled():
    packet = cc.build_packet()
    assert packet["telegram_gate_state"]["send_message"] == "disabled"


def test_publish_automation_dry_run_live_disabled():
    packet = cc.build_packet()
    assert packet["publish_automation_state"]["mode"] == "dry_run_only"
    assert packet["publish_automation_state"]["live"] == "disabled"


def test_content_studio_review_only_not_public_postable():
    packet = cc.build_packet()
    assert packet["content_studio_state"]["review_only"] is True
    assert packet["content_studio_state"]["not_public_postable"] is True
    assert packet["content_studio_state"]["final_social_copy_generated_by_repo"] is False


def test_ui_rebuild_antigravity_future_only():
    packet = cc.build_packet()
    assert packet["ui_rebuild_state"]["antigravity"] == "future_only"
    assert packet["ui_rebuild_state"]["browser_qa"] == "none_yet"


def test_residual_drift_env_untouched():
    txt = _read("fixture_data.js")
    assert "untouched/untracked" in txt


def test_next_allowed_action_requires_audit():
    txt = _read("fixture_data.js")
    assert "AUDIT_OF_0161_EVIDENCE_BEFORE_ANY_NEXT_TASK" in txt


def test_no_active_live_controls():
    app = _read("app.js")
    assert "disabled-control" in app
    assert "aria-disabled" in app


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


def test_no_token_like_secret_visible():
    assert cc._count_secret_hits() == 0


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
    packet = cc.build_packet()
    assert packet["red_green_market_direction_semantics"] is False


def test_active_frontend_scope_within_shell():
    packet = cc.build_packet()
    assert "ui/institutional_shell" in packet["active_frontend_code_changed_scope"]



def test_runtime_authority_true_fails():
    packet = cc.build_packet()
    packet["runtime_authority"] = True
    res = cc.validate_packet(packet)
    assert not res["valid"]
    assert "runtime_authority_must_be_false" in res["errors"]


def test_live_posting_enabled_true_fails():
    packet = cc.build_packet()
    packet["live_posting_enabled_now"] = True
    res = cc.validate_packet(packet)
    assert not res["valid"]
    assert "live_posting_enabled_now_must_be_false" in res["errors"]


def test_missing_gate_fails():
    packet = cc.build_packet()
    packet["gate_timeline"] = [g for g in packet["gate_timeline"] if g["gate"] != "0157"]
    res = cc.validate_packet(packet)
    assert not res["valid"]
    assert "gate_timeline_missing_0157" in res["errors"]


def test_missing_blocked_action_fails():
    packet = cc.build_packet()
    packet["blocked_action_matrix"] = [a for a in packet["blocked_action_matrix"] if a["action"] != "live_posting"]
    res = cc.validate_packet(packet)
    assert not res["valid"]
    assert "blocked_action_missing_live_posting" in res["errors"]


def test_telegram_send_message_enabled_fails():
    packet = cc.build_packet()
    packet["telegram_gate_state"]["send_message"] = "enabled"
    res = cc.validate_packet(packet)
    assert not res["valid"]
    assert "telegram_send_message_must_be_disabled" in res["errors"]


def test_packet_status_pass_with_errors_fails():
    packet = cc.build_packet()
    packet["runtime_authority"] = True
    packet["packet_status"] = "pass"
    res = cc.validate_packet(packet)
    assert not res["valid"]
    assert "packet_status_pass_but_errors_exist" in res["errors"]


def test_summary_validation_valid_true():
    s = cc.summary()
    assert s["validation_valid"] is True
    assert s["packet_status"] == "pass"
    assert s["safety_ribbon_count"] == 10
    assert s["executive_status_card_count"] == 8
    assert s["gate_timeline_item_count"] == 12
    assert s["blocked_action_count"] == 13
    assert s["hero_status_band_present"] is True
    assert s["evidence_summary_present"] is True
    assert s["telegram_gate_state_present"] is True
    assert s["fetch_call_count"] == 0
    assert s["secret_visible_count"] == 0
    assert s["kill_switch_status"] == "active"


def test_cli_summary_runs():
    r = subprocess.run(
        [sys.executable, "-m", "live_contentops.cli",
         "pre-alpha-institutional-command-center-screen-summary"],
        capture_output=True,
        text=True,
        cwd=BASE_DIR,
    )
    assert r.returncode == 0, r.stderr
    out = json.loads(r.stdout)
    assert out["packet_status"] == "pass"
    assert out["validation_valid"] is True
    assert out["secret_visible_count"] == 0
