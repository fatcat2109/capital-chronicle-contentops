import json
import os
import subprocess
import sys

from live_contentops import institutional_design_system as ds

BASE_DIR = os.path.dirname(os.path.dirname(__file__))


def test_valid_packet_passes():
    packet = ds.build_packet()
    res = ds.validate_packet(packet)
    assert res["valid"], res["errors"]
    assert packet["packet_status"] == "pass"


def test_planning_only_mode():
    packet = ds.build_packet()
    assert packet["design_system_mode"] == "planning_only"
    assert packet["planning_only"] is True
    assert packet["runtime_authority"] is False


def test_missing_required_status_token_fails():
    packet = ds.build_packet()
    packet["status_tokens"] = [t for t in packet["status_tokens"] if t != "SECRET_REDACTED"]
    res = ds.validate_packet(packet)
    assert not res["valid"]
    assert "status_token_SECRET_REDACTED_missing" in res["errors"]


def test_missing_required_safety_banner_fails():
    packet = ds.build_packet()
    packet["safety_banners"] = [b for b in packet["safety_banners"] if b != "NOT_PUBLIC_POSTABLE"]
    res = ds.validate_packet(packet)
    assert not res["valid"]
    assert "safety_banner_NOT_PUBLIC_POSTABLE_missing" in res["errors"]


def test_runtime_authority_true_fails():
    packet = ds.build_packet()
    packet["runtime_authority"] = True
    res = ds.validate_packet(packet)
    assert not res["valid"]
    assert "runtime_authority_must_be_false" in res["errors"]


def test_active_frontend_code_changed_true_fails():
    packet = ds.build_packet()
    packet["active_frontend_code_changed"] = True
    res = ds.validate_packet(packet)
    assert not res["valid"]
    assert "active_frontend_code_changed_must_be_false" in res["errors"]


def test_frontend_dependency_added_true_fails():
    packet = ds.build_packet()
    packet["frontend_dependencies_added"] = True
    res = ds.validate_packet(packet)
    assert not res["valid"]
    assert "frontend_dependencies_added_must_be_false" in res["errors"]


def test_backend_server_required_true_fails():
    packet = ds.build_packet()
    packet["backend_server_required"] = True
    res = ds.validate_packet(packet)
    assert not res["valid"]
    assert "backend_server_required_must_be_false" in res["errors"]


def test_browser_automation_used_true_fails():
    packet = ds.build_packet()
    packet["browser_automation_used_now"] = True
    res = ds.validate_packet(packet)
    assert not res["valid"]
    assert "browser_automation_used_now_must_be_false" in res["errors"]


def test_antigravity_used_true_fails():
    packet = ds.build_packet()
    packet["antigravity_used_now"] = True
    res = ds.validate_packet(packet)
    assert not res["valid"]
    assert "antigravity_used_now_must_be_false" in res["errors"]


def test_credential_read_allowed_true_fails():
    packet = ds.build_packet()
    packet["credential_read_allowed_now"] = True
    res = ds.validate_packet(packet)
    assert not res["valid"]
    assert "credential_read_allowed_now_must_be_false" in res["errors"]


def test_platform_api_allowed_true_fails():
    packet = ds.build_packet()
    packet["platform_api_allowed_now"] = True
    res = ds.validate_packet(packet)
    assert not res["valid"]


def test_live_posting_enabled_true_fails():
    packet = ds.build_packet()
    packet["live_posting_enabled_now"] = True
    res = ds.validate_packet(packet)
    assert not res["valid"]
    assert "live_posting_enabled_now_must_be_false" in res["errors"]


def test_scheduler_allowed_true_fails():
    packet = ds.build_packet()
    packet["scheduler_allowed_now"] = True
    res = ds.validate_packet(packet)
    assert not res["valid"]
    assert "scheduler_allowed_now_must_be_false" in res["errors"]


def test_scraping_allowed_true_fails():
    packet = ds.build_packet()
    packet["scraping_allowed_now"] = True
    res = ds.validate_packet(packet)
    assert not res["valid"]
    assert "scraping_allowed_now_must_be_false" in res["errors"]


def test_public_ready_final_copy_generated_true_fails():
    packet = ds.build_packet()
    packet["public_ready_final_copy_generated"] = True
    res = ds.validate_packet(packet)
    assert not res["valid"]
    assert "public_ready_final_copy_generated_must_be_false" in res["errors"]


def test_forbidden_visual_metaphors_missing_fails():
    packet = ds.build_packet()
    packet["forbidden_visual_metaphors"] = [
        m for m in packet["forbidden_visual_metaphors"]
        if m not in ("trade_buttons", "pnl_widgets", "buy_sell_chips", "alpha_signal_badges")
    ]
    res = ds.validate_packet(packet)
    assert not res["valid"]
    assert any("forbidden_visual_metaphor_" in e for e in res["errors"])


def test_red_green_market_direction_semantics_true_fails():
    packet = ds.build_packet()
    packet["red_green_market_direction_semantics"] = True
    res = ds.validate_packet(packet)
    assert not res["valid"]
    assert "red_green_market_direction_semantics_must_be_false" in res["errors"]


def test_secret_visible_count_nonzero_fails():
    packet = ds.build_packet()
    packet["secret_visible_count"] = 1
    res = ds.validate_packet(packet)
    assert not res["valid"]


def test_unsafe_signal_language_enabled_true_fails():
    packet = ds.build_packet()
    packet["unsafe_signal_language_enabled"] = True
    res = ds.validate_packet(packet)
    assert not res["valid"]
    assert "unsafe_signal_language_enabled_must_be_false" in res["errors"]


def test_packet_status_pass_with_errors_fails():
    packet = ds.build_packet()
    packet["runtime_authority"] = True
    packet["packet_status"] = "pass"
    res = ds.validate_packet(packet)
    assert not res["valid"]
    assert "packet_status_pass_but_errors_exist" in res["errors"]


def test_component_taxonomy_required_components_present():
    packet = ds.build_packet()
    for comp in ("global_safety_ribbon", "gate_card", "evidence_link_card",
                 "credential_redaction_badge", "telegram_gate_stepper",
                 "not_public_postable_banner", "kill_switch_indicator"):
        assert comp in packet["component_taxonomy"], comp


def test_screenshot_safe_rules_require_no_secrets():
    packet = ds.build_packet()
    for rule in ("no_secrets", "no_raw_env_path", "no_public_ready_false_claims"):
        assert rule in packet["screenshot_safe_rules"], rule


def test_design_system_docs_exist():
    packet = ds.build_packet()
    assert len(packet["design_system_docs"]) >= 5
    for rel in packet["design_system_docs"]:
        assert os.path.isfile(os.path.join(BASE_DIR, rel)), rel


def test_summary_validation_valid_true():
    s = ds.summary()
    assert s["validation_valid"] is True
    assert s["packet_status"] == "pass"
    assert s["status_token_count"] == 19
    assert s["safety_banner_count"] == 16
    assert s["forbidden_visual_metaphor_count"] == 9
    assert s["screenshot_safe_rules_present"] is True
    assert s["handoff_to_view_model_present"] is True
    assert s["secret_visible_count"] == 0
    assert s["red_green_market_direction_semantics"] is False
    assert s["kill_switch_status"] == "active"


def test_cli_summary_runs():
    r = subprocess.run(
        [sys.executable, "-m", "live_contentops.cli",
         "pre-alpha-institutional-design-system-summary"],
        capture_output=True,
        text=True,
        cwd=BASE_DIR,
    )
    assert r.returncode == 0, r.stderr
    out = json.loads(r.stdout)
    assert out["packet_status"] == "pass"
    assert out["validation_valid"] is True
    assert out["secret_visible_count"] == 0
