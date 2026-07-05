import json
import os
import subprocess
import sys

from live_contentops import institutional_ui_view_model_contract_v2 as vm

BASE_DIR = os.path.dirname(os.path.dirname(__file__))


def test_valid_full_packet_passes():
    packet = vm.build_packet()
    res = vm.validate_packet(packet)
    assert res["valid"], res["errors"]
    assert packet["packet_status"] == "pass"


def test_fixture_contains_all_12_screens():
    packet = vm.build_packet()
    screen_ids = [s["screen_id"] for s in packet["screens"]]
    for sid in vm.REQUIRED_SCREENS:
        assert sid in screen_ids, sid
    assert len(packet["screens"]) == 12


def test_missing_command_center_fails():
    packet = vm.build_packet()
    packet["screens"] = [s for s in packet["screens"] if s["screen_id"] != "command_center"]
    res = vm.validate_packet(packet)
    assert not res["valid"]
    assert "screen_command_center_missing" in res["errors"]


def test_missing_any_required_screen_fails():
    packet = vm.build_packet()
    packet["screens"] = [s for s in packet["screens"] if s["screen_id"] != "evidence_vault"]
    res = vm.validate_packet(packet)
    assert not res["valid"]
    assert "screen_evidence_vault_missing" in res["errors"]


def test_missing_required_component_fails():
    packet = vm.build_packet()
    packet["component_registry"] = [c for c in packet["component_registry"] if c["component_id"] != "gate_card"]
    res = vm.validate_packet(packet)
    assert not res["valid"]
    assert "component_gate_card_missing" in res["errors"]


def test_missing_required_status_token_fails():
    packet = vm.build_packet()
    packet["status_token_registry"] = [r for r in packet["status_token_registry"] if r["status_token_id"] != "SECRET_REDACTED"]
    res = vm.validate_packet(packet)
    assert not res["valid"]
    assert "status_token_SECRET_REDACTED_missing" in res["errors"]


def test_missing_required_safety_banner_fails():
    packet = vm.build_packet()
    packet["safety_banners"] = [b for b in packet["safety_banners"] if b != "NOT_PUBLIC_POSTABLE"]
    res = vm.validate_packet(packet)
    assert not res["valid"]
    assert "safety_banner_NOT_PUBLIC_POSTABLE_missing" in res["errors"]


def test_runtime_authority_true_fails():
    packet = vm.build_packet()
    packet["runtime_authority"] = True
    res = vm.validate_packet(packet)
    assert not res["valid"]
    assert "runtime_authority_must_be_false" in res["errors"]


def test_local_only_false_fails():
    packet = vm.build_packet()
    packet["local_only"] = False
    res = vm.validate_packet(packet)
    assert not res["valid"]
    assert "local_only_must_be_true" in res["errors"]


def test_fixture_or_mock_data_only_false_fails():
    packet = vm.build_packet()
    packet["fixture_or_mock_data_only"] = False
    res = vm.validate_packet(packet)
    assert not res["valid"]
    assert "fixture_or_mock_data_only_must_be_true" in res["errors"]


def test_active_frontend_code_changed_true_fails():
    packet = vm.build_packet()
    packet["active_frontend_code_changed"] = True
    res = vm.validate_packet(packet)
    assert not res["valid"]
    assert "active_frontend_code_changed_must_be_false" in res["errors"]


def test_backend_server_required_true_fails():
    packet = vm.build_packet()
    packet["backend_server_required"] = True
    res = vm.validate_packet(packet)
    assert not res["valid"]
    assert "backend_server_required_must_be_false" in res["errors"]


def test_browser_automation_used_true_fails():
    packet = vm.build_packet()
    packet["browser_automation_used_now"] = True
    res = vm.validate_packet(packet)
    assert not res["valid"]
    assert "browser_automation_used_now_must_be_false" in res["errors"]


def test_antigravity_used_true_fails():
    packet = vm.build_packet()
    packet["antigravity_used_now"] = True
    res = vm.validate_packet(packet)
    assert not res["valid"]
    assert "antigravity_used_now_must_be_false" in res["errors"]


def test_credential_read_allowed_true_fails():
    packet = vm.build_packet()
    packet["credential_read_allowed_now"] = True
    res = vm.validate_packet(packet)
    assert not res["valid"]
    assert "credential_read_allowed_now_must_be_false" in res["errors"]


def test_platform_api_allowed_true_fails():
    packet = vm.build_packet()
    packet["platform_api_allowed_now"] = True
    res = vm.validate_packet(packet)
    assert not res["valid"]


def test_live_posting_enabled_true_fails():
    packet = vm.build_packet()
    packet["live_posting_enabled_now"] = True
    res = vm.validate_packet(packet)
    assert not res["valid"]
    assert "live_posting_enabled_now_must_be_false" in res["errors"]


def test_scheduler_allowed_true_fails():
    packet = vm.build_packet()
    packet["scheduler_allowed_now"] = True
    res = vm.validate_packet(packet)
    assert not res["valid"]
    assert "scheduler_allowed_now_must_be_false" in res["errors"]


def test_scraping_allowed_true_fails():
    packet = vm.build_packet()
    packet["scraping_allowed_now"] = True
    res = vm.validate_packet(packet)
    assert not res["valid"]
    assert "scraping_allowed_now_must_be_false" in res["errors"]


def test_public_ready_final_copy_generated_true_fails():
    packet = vm.build_packet()
    packet["public_ready_final_copy_generated"] = True
    res = vm.validate_packet(packet)
    assert not res["valid"]
    assert "public_ready_final_copy_generated_must_be_false" in res["errors"]


def test_telegram_pilot_gate_missing_channel_permission_unvalidated_fails():
    packet = vm.build_packet()
    for s in packet["screens"]:
        if s["screen_id"] == "telegram_pilot_gate":
            s["required_status_tokens"] = [t for t in s["required_status_tokens"] if t != "CHANNEL_PERMISSION_UNVALIDATED"]
    res = vm.validate_packet(packet)
    assert not res["valid"]
    assert "telegram_pilot_gate_missing_channel_permission_unvalidated" in res["errors"]


def test_publish_readiness_tower_enabling_publish_all_fails():
    packet = vm.build_packet()
    for s in packet["screens"]:
        if s["screen_id"] == "publish_readiness_tower":
            s["forbidden_controls"] = [c for c in s["forbidden_controls"] if c != "one_button_publish_all"]
    res = vm.validate_packet(packet)
    assert not res["valid"]
    assert "publish_readiness_tower_must_forbid_publish_all" in res["errors"]


def test_content_calendar_scheduled_live_state_fails():
    packet = vm.build_packet()
    for s in packet["screens"]:
        if s["screen_id"] == "content_calendar":
            s["forbidden_controls"] = [c for c in s["forbidden_controls"] if c != "scheduled_post"]
    res = vm.validate_packet(packet)
    assert not res["valid"]
    assert "content_calendar_must_forbid_scheduled_post" in res["errors"]


def test_visual_export_studio_without_redaction_fails():
    packet = vm.build_packet()
    for s in packet["screens"]:
        if s["screen_id"] == "visual_export_studio":
            s["forbidden_controls"] = [c for c in s["forbidden_controls"] if c != "unredacted_capture"]
    res = vm.validate_packet(packet)
    assert not res["valid"]
    assert "visual_export_studio_must_forbid_unredacted_capture" in res["errors"]


def test_settings_safety_policy_displaying_credentials_fails():
    packet = vm.build_packet()
    for s in packet["screens"]:
        if s["screen_id"] == "settings_safety_policy":
            s["forbidden_controls"] = [c for c in s["forbidden_controls"] if c != "credential_display"]
    res = vm.validate_packet(packet)
    assert not res["valid"]
    assert "settings_safety_policy_must_forbid_credential_display" in res["errors"]


def test_redaction_policy_missing_fails():
    packet = vm.build_packet()
    packet["redaction_policy"] = {}
    res = vm.validate_packet(packet)
    assert not res["valid"]
    assert "redaction_policy_missing" in res["errors"]



def test_each_screen_has_banner_and_blocked_action_policy():
    packet = vm.build_packet()
    for s in packet["screens"]:
        assert s.get("required_banners"), s["screen_id"]
        assert s.get("blocked_action_policy"), s["screen_id"]
        assert s.get("redaction_requirements"), s["screen_id"]


def test_evidence_facing_screens_have_evidence_refs():
    packet = vm.build_packet()
    by_id = {s["screen_id"]: s for s in packet["screens"]}
    for sid in ("evidence_vault", "draft_inspector", "grounded_news_angle_lab"):
        assert by_id[sid].get("evidence_refs"), sid


def test_packet_status_pass_with_errors_fails():
    packet = vm.build_packet()
    packet["runtime_authority"] = True
    packet["packet_status"] = "pass"
    res = vm.validate_packet(packet)
    assert not res["valid"]
    assert "packet_status_pass_but_errors_exist" in res["errors"]


def test_secret_visible_count_nonzero_fails():
    packet = vm.build_packet()
    packet["secret_visible_count"] = 1
    res = vm.validate_packet(packet)
    assert not res["valid"]


def test_red_green_market_direction_semantics_true_fails():
    packet = vm.build_packet()
    packet["red_green_market_direction_semantics"] = True
    res = vm.validate_packet(packet)
    assert not res["valid"]
    assert "red_green_market_direction_semantics_must_be_false" in res["errors"]


def test_unsafe_signal_language_enabled_true_fails():
    packet = vm.build_packet()
    packet["unsafe_signal_language_enabled"] = True
    res = vm.validate_packet(packet)
    assert not res["valid"]
    assert "unsafe_signal_language_enabled_must_be_false" in res["errors"]


def test_valid_fixture_file_validates():
    path = os.path.join(BASE_DIR, "fixtures", "institutional_ui_view_model_contract_v2_valid.json")
    with open(path, "r", encoding="utf-8") as f:
        packet = json.load(f)
    res = vm.validate_packet(packet)
    assert res["valid"], res["errors"]


def test_invalid_fixture_file_fails_closed():
    path = os.path.join(BASE_DIR, "fixtures", "institutional_ui_view_model_contract_v2_invalid_live_enabled.json")
    with open(path, "r", encoding="utf-8") as f:
        packet = json.load(f)
    res = vm.validate_packet(packet)
    assert not res["valid"]
    assert any("must_be_false" in e for e in res["errors"])


def test_contract_docs_exist():
    packet = vm.build_packet()
    assert len(packet["contract_docs"]) >= 4
    for rel in packet["contract_docs"]:
        assert os.path.isfile(os.path.join(BASE_DIR, rel)), rel


def test_summary_validation_valid_true():
    s = vm.summary()
    assert s["validation_valid"] is True
    assert s["packet_status"] == "pass"
    assert s["screen_count"] == 12
    assert s["component_count"] == 26
    assert s["status_token_count"] == 19
    assert s["safety_banner_count"] == 16
    assert s["evidence_ref_policy_present"] is True
    assert s["redaction_policy_present"] is True
    assert s["blocked_action_policy_present"] is True
    assert s["screenshot_safe_rules_present"] is True
    assert s["handoff_to_0160_present"] is True
    assert s["secret_visible_count"] == 0
    assert s["kill_switch_status"] == "active"


def test_cli_summary_runs():
    r = subprocess.run(
        [sys.executable, "-m", "live_contentops.cli",
         "pre-alpha-institutional-ui-view-model-contract-v2-summary"],
        capture_output=True,
        text=True,
        cwd=BASE_DIR,
    )
    assert r.returncode == 0, r.stderr
    out = json.loads(r.stdout)
    assert out["packet_status"] == "pass"
    assert out["validation_valid"] is True
    assert out["secret_visible_count"] == 0
