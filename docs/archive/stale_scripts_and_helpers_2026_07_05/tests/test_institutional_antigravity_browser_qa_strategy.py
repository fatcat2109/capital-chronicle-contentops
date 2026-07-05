from live_contentops import institutional_antigravity_browser_qa_strategy as q

REQUIRED_SCREENS = [
    "command_center", "content_lane_control", "daily_content_studio",
    "draft_inspector", "grounded_news_angle_lab", "publish_readiness_tower",
    "telegram_pilot_gate", "approval_queue", "content_calendar",
    "evidence_vault", "visual_export_studio", "settings_safety_policy",
]


def _packet():
    return q.build_packet()


def test_valid_packet_passes():
    res = q.validate_packet(_packet())
    assert res["valid"], res["errors"]
    assert _packet()["packet_status"] == "pass"


def test_strategy_only_true():
    assert _packet()["strategy_only"] is True


def test_browser_opened_now_false():
    assert _packet()["browser_opened_now"] is False


def test_browser_automation_used_now_false():
    assert _packet()["browser_automation_used_now"] is False


def test_antigravity_used_now_false():
    assert _packet()["antigravity_used_now"] is False


def test_screenshot_capture_enabled_now_false():
    assert _packet()["screenshot_capture_enabled_now"] is False


def test_file_export_enabled_now_false():
    assert _packet()["file_export_enabled_now"] is False


def test_platform_upload_enabled_now_false():
    assert _packet()["platform_upload_enabled_now"] is False


def test_credential_read_allowed_now_false():
    assert _packet()["credential_read_allowed_now"] is False


def test_platform_api_allowed_now_false():
    assert _packet()["platform_api_allowed_now"] is False


def test_live_posting_enabled_now_false():
    assert _packet()["live_posting_enabled_now"] is False


def test_scheduler_allowed_now_false():
    assert _packet()["scheduler_allowed_now"] is False


def test_evidence_mutation_enabled_now_false():
    assert _packet()["evidence_mutation_enabled_now"] is False


def test_browser_qa_purpose_exists():
    assert _packet()["browser_qa_purpose"]


def test_non_goals_no_live_platform():
    assert "no_live_platform_testing" in _packet()["browser_qa_non_goals"]


def test_non_goals_no_credential():
    assert "no_credential_testing" in _packet()["browser_qa_non_goals"]


def test_non_goals_no_screenshot_unless_authorized():
    assert "no_screenshot_capture_unless_separately_authorized" in _packet()["browser_qa_non_goals"]


def test_allowed_browser_target_local_file_only():
    t = _packet()["allowed_browser_target"]
    assert t["local_file_only"] == "ui/institutional_shell/index.html"
    assert t["no_remote_url"] is True


def test_forbidden_includes_external_sites():
    assert "open_external_sites" in _packet()["explicit_forbidden_actions"]


def test_forbidden_includes_network():
    assert "use_network" in _packet()["explicit_forbidden_actions"]


def test_forbidden_includes_secrets_env():
    actions = _packet()["explicit_forbidden_actions"]
    assert "paste_secrets" in actions
    assert "read_env" in actions


def test_forbidden_includes_screenshot_capture():
    assert "capture_screenshots" in _packet()["explicit_forbidden_actions"]


def test_forbidden_includes_platform_posting():
    assert "post_to_platforms" in _packet()["explicit_forbidden_actions"]


def test_forbidden_includes_scheduling():
    assert "schedule_posts" in _packet()["explicit_forbidden_actions"]


def test_forbidden_includes_export_upload():
    actions = _packet()["explicit_forbidden_actions"]
    assert "save_images_or_pdfs" in actions
    assert "upload_screenshots" in actions


def test_manual_checklist_includes_all_12_screens():
    ids = {c["screen_id"] for c in _packet()["manual_screen_checklist"]}
    for s in REQUIRED_SCREENS:
        assert s in ids, s
    assert len(_packet()["manual_screen_checklist"]) == 12


def test_high_priority_checks_present():
    ids = {c["screen_id"] for c in _packet()["high_priority_screen_checks"]}
    for s in ["command_center", "daily_content_studio", "publish_readiness_tower",
              "evidence_vault", "content_calendar", "visual_export_studio"]:
        assert s in ids, s


def test_evidence_template_browser_tool():
    assert "browser_or_tool_used_and_exact_tool" in _packet()["future_browser_qa_evidence_packet_template"]


def test_evidence_template_antigravity_run():
    assert "antigravity_run" in _packet()["future_browser_qa_evidence_packet_template"]


def test_evidence_template_screenshot_status():
    assert "screenshots_captured" in _packet()["future_browser_qa_evidence_packet_template"]


def test_evidence_template_network_status():
    assert "network_used" in _packet()["future_browser_qa_evidence_packet_template"]


def test_evidence_template_env_status():
    assert "env_or_credentials_read" in _packet()["future_browser_qa_evidence_packet_template"]


def test_evidence_template_external_url_status():
    assert "external_url_opened" in _packet()["future_browser_qa_evidence_packet_template"]


def test_evidence_template_screens_inspected():
    assert "screens_inspected" in _packet()["future_browser_qa_evidence_packet_template"]


def test_evidence_template_disabled_control_status():
    assert "disabled_control_status" in _packet()["future_browser_qa_evidence_packet_template"]


def test_evidence_template_redaction_status():
    assert "redaction_secret_status" in _packet()["future_browser_qa_evidence_packet_template"]


def test_evidence_template_git_status():
    assert "git_status" in _packet()["future_browser_qa_evidence_packet_template"]


def test_evidence_template_exact_next_task():
    assert "exact_next_task" in _packet()["future_browser_qa_evidence_packet_template"]


def test_pass_criteria_all_12_reachable():
    assert "all_12_screens_reachable" in _packet()["future_browser_qa_pass_criteria"]


def test_pass_criteria_no_external_url_network():
    assert "no_external_url_or_network_use" in _packet()["future_browser_qa_pass_criteria"]


def test_pass_criteria_no_active_live_controls():
    assert "no_active_live_post_schedule_export_controls" in _packet()["future_browser_qa_pass_criteria"]


def test_blocked_criteria_suspected_secret():
    assert "suspected_secret_visible" in _packet()["future_browser_qa_blocked_criteria"]


def test_blocked_criteria_active_forbidden_control():
    assert "active_forbidden_control_appears" in _packet()["future_browser_qa_blocked_criteria"]


def test_fail_criteria_secret_displayed():
    assert "secret_or_env_value_displayed_or_captured" in _packet()["future_browser_qa_fail_criteria"]


def test_fail_criteria_external_site_opened():
    assert "external_site_opened" in _packet()["future_browser_qa_fail_criteria"]


def test_fail_criteria_network_api_call():
    assert "network_or_api_call_made" in _packet()["future_browser_qa_fail_criteria"]


def test_fail_criteria_screenshot_without_authorization():
    assert "screenshot_captured_without_authorization" in _packet()["future_browser_qa_fail_criteria"]


def test_stop_conditions_secret_env_raw_response():
    assert "secret_env_path_or_raw_response_appears" in _packet()["stop_conditions"]


def test_stop_conditions_external_url():
    assert "any_external_url_opens" in _packet()["stop_conditions"]


def test_stop_conditions_network_publish_export():
    assert "any_control_attempts_network_publish_or_export" in _packet()["stop_conditions"]


def test_stop_conditions_unsafe_browser_profile():
    assert "browser_profile_exposes_credentials" in _packet()["stop_conditions"]


def test_future_guidance_no_self_authorize():
    assert _packet()["future_next_task_guidance"]["self_authorizes_browser_qa"] is False


def test_future_task_named_after_go():
    g = _packet()["future_next_task_guidance"]
    assert g["future_possible_task_named"]
    assert g["future_task_requires_explicit_operator_chatgpt_go"] is True


def test_cli_summary_validation_valid():
    s = q.build_summary()
    assert s["validation_valid"] is True
    assert s["packet_status"] == "pass"


def test_runtime_authority_true_fails():
    p = _packet()
    p["runtime_authority"] = True
    res = q.validate_packet(p)
    assert not res["valid"]
    assert "runtime_authority_must_be_false" in res["errors"]


def test_browser_opened_true_fails():
    p = _packet()
    p["browser_opened_now"] = True
    assert not q.validate_packet(p)["valid"]


def test_antigravity_used_true_fails():
    p = _packet()
    p["antigravity_used_now"] = True
    assert not q.validate_packet(p)["valid"]


def test_missing_screen_fails():
    p = _packet()
    p["manual_screen_checklist"] = p["manual_screen_checklist"][:11]
    assert not q.validate_packet(p)["valid"]


def test_self_authorize_fails():
    p = _packet()
    p["future_next_task_guidance"]["self_authorizes_browser_qa"] = True
    assert not q.validate_packet(p)["valid"]


def test_packet_status_pass_with_errors_fails():
    p = _packet()
    p["runtime_authority"] = True
    p["packet_status"] = "pass"
    res = q.validate_packet(p)
    assert not res["valid"]
    assert "packet_status_pass_but_errors_exist" in res["errors"]

