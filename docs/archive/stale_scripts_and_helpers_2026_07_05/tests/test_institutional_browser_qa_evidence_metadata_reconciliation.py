from live_contentops import institutional_browser_qa_evidence_metadata_reconciliation as r

REQUIRED_SCREENS = [
    "command_center", "content_lane_control", "daily_content_studio",
    "draft_inspector", "grounded_news_angle_lab", "publish_readiness_tower",
    "telegram_pilot_gate", "approval_queue", "content_calendar",
    "evidence_vault", "visual_export_studio", "settings_safety_policy",
]


def _p():
    return r.build_packet()


def test_valid_packet_passes():
    res = r.validate_packet(_p())
    assert res["valid"], res["errors"]
    assert _p()["packet_status"] == "pass"


def test_0169_classification_is_minor_gap():
    assert _p()["browser_qa_evidence_packet"]["audit_classification"] == "PASS_WITH_MINOR_EVIDENCE_GAP"


def test_browser_opened_true():
    assert _p()["browser_qa_evidence_packet"]["browser_opened"] == "yes"


def test_local_file_url_opened_true():
    assert _p()["browser_qa_evidence_packet"]["local_file_url_opened"] == "yes"


def test_external_url_opened_false():
    assert _p()["browser_qa_evidence_packet"]["external_url_opened"] == "no"


def test_network_used_false():
    assert _p()["browser_qa_evidence_packet"]["network_used_observed"] == "no"


def test_screenshots_captured_false_with_clarification():
    bqa = _p()["browser_qa_evidence_packet"]
    assert bqa["screenshots_captured"] == "no"
    assert "screenshots_captured_clarification" in bqa
    assert bqa["screenshots_captured_clarification"]


def test_files_created_or_changed_false():
    assert _p()["browser_qa_evidence_packet"]["files_created_or_changed_by_browser_qa"] == "no"


def test_all_12_screens_in_evidence():
    ids = {s["screen_id"] for s in _p()["browser_qa_screen_results"]}
    for s in REQUIRED_SCREENS:
        assert s in ids, s
    assert len(_p()["browser_qa_screen_results"]) == 12


def test_all_12_screens_reached():
    for s in _p()["browser_qa_screen_results"]:
        assert s["reached"] == "yes"


def test_secret_visible_count_zero():
    for s in _p()["browser_qa_screen_results"]:
        assert s["secret_raw_data_visible"] == "no"


def test_active_forbidden_controls_zero():
    bqa = _p()["browser_qa_evidence_packet"]
    assert bqa["active_publish_schedule_export_api_evidence_mutation_control_count"] == 0


def test_minor_gap_includes_repo_head_git():
    gaps = " ".join(_p()["minor_evidence_gap_registry"]).lower()
    assert "head" in gaps and "git status" in gaps


def test_minor_gap_includes_antigravity():
    gaps = " ".join(_p()["minor_evidence_gap_registry"]).lower()
    assert "antigravity" in gaps


def test_minor_gap_includes_settings_visual_caveat():
    gaps = " ".join(_p()["minor_evidence_gap_registry"]).lower()
    assert "settings" in gaps


def test_caveat_records_stale_head():
    assert _p()["screenshot_review_caveat"]["stale_accepted_head_example"] == "15b87ff"


def test_caveat_records_stale_gate():
    assert _p()["screenshot_review_caveat"]["stale_current_gate_example"] == "telegram_official_docs_credential_validation_gate"


def test_global_header_not_stale_head():
    rec = _p()["global_header_metadata_reconciliation"]
    assert rec["stale_15b87ff_presented_as_current_global_baseline"] is False


def test_global_header_not_stale_gate():
    rec = _p()["global_header_metadata_reconciliation"]
    assert rec["stale_telegram_docs_gate_presented_as_current_gate"] is False


def test_latest_accepted_baseline_444ef2c():
    rec = _p()["global_header_metadata_reconciliation"]
    assert rec["latest_accepted_code_baseline_before_0170"] == "444ef2c"


def test_latest_browser_qa_recorded():
    rec = _p()["global_header_metadata_reconciliation"]
    assert rec["latest_browser_qa_evidence"] == "0169 PASS_WITH_MINOR_EVIDENCE_GAP"


def test_historical_screen_metadata_policy_present():
    pol = _p()["historical_screen_metadata_policy"]
    assert pol["present"] is True
    assert pol["old_per_screen_heads_classified_historical"] is True


def test_future_browser_go_explicit():
    w = _p()["visual_export_antigravity_wording_policy"]
    assert w["future_browser_antigravity_requires_explicit_go"] is True


def test_visual_export_not_self_authorized():
    w = _p()["visual_export_antigravity_wording_policy"]
    assert w["future_browser_qa_self_authorized"] is False


def test_evidence_vault_includes_0169():
    assert _p()["evidence_vault_update"]["includes_0169_browser_qa_evidence"] is True


def test_project_sources_refresh_not_created():
    assert _p()["project_sources_refresh_created_now"] is False


def test_browser_rerun_false():
    assert _p()["browser_rerun_now"] is False


def test_antigravity_used_false():
    assert _p()["antigravity_used_now"] is False


def test_screenshot_capture_false():
    assert _p()["screenshot_capture_enabled_now"] is False


def test_file_export_false():
    assert _p()["file_export_enabled_now"] is False


def test_platform_upload_false():
    assert _p()["platform_upload_enabled_now"] is False


def test_credential_read_false():
    assert _p()["credential_read_allowed_now"] is False


def test_platform_api_false():
    assert _p()["platform_api_allowed_now"] is False


def test_live_posting_false():
    assert _p()["live_posting_enabled_now"] is False


def test_scheduler_false():
    assert _p()["scheduler_allowed_now"] is False


def test_evidence_mutation_false():
    assert _p()["evidence_mutation_enabled_now"] is False


def test_readme_update_present():
    assert _p()["readme_update"]["present"] is True


def test_long_label_readability_policy_present():
    assert _p()["long_label_readability_policy"]["present"] is True


def test_cli_summary_validation_valid():
    s = r.build_summary()
    assert s["validation_valid"] is True
    assert s["packet_status"] == "pass"


def test_runtime_authority_true_fails():
    p = _p()
    p["runtime_authority"] = True
    res = r.validate_packet(p)
    assert not res["valid"]
    assert "runtime_authority_must_be_false" in res["errors"]


def test_project_sources_refresh_true_fails():
    p = _p()
    p["project_sources_refresh_created_now"] = True
    assert not r.validate_packet(p)["valid"]


def test_stale_head_current_fails():
    p = _p()
    p["global_header_metadata_reconciliation"]["stale_15b87ff_presented_as_current_global_baseline"] = True
    assert not r.validate_packet(p)["valid"]


def test_stale_gate_current_fails():
    p = _p()
    p["global_header_metadata_reconciliation"]["stale_telegram_docs_gate_presented_as_current_gate"] = True
    assert not r.validate_packet(p)["valid"]


def test_wrong_0169_classification_fails():
    p = _p()
    p["browser_qa_evidence_packet"]["audit_classification"] = "PASS"
    res = r.validate_packet(p)
    assert not res["valid"]
    assert "0169_must_be_pass_with_minor_evidence_gap" in res["errors"]


def test_missing_screen_fails():
    p = _p()
    p["browser_qa_screen_results"] = p["browser_qa_screen_results"][:11]
    assert not r.validate_packet(p)["valid"]


def test_packet_status_pass_with_errors_fails():
    p = _p()
    p["runtime_authority"] = True
    p["packet_status"] = "pass"
    res = r.validate_packet(p)
    assert not res["valid"]
    assert "packet_status_pass_but_errors_exist" in res["errors"]

