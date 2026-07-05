import json
import uuid
import datetime
from pathlib import Path

SCHEMA_PATH = Path(__file__).parent.parent / "schemas" / "institutional_antigravity_browser_qa_strategy_packet.schema.json"

REQUIRED_SCREENS = [
    "command_center", "content_lane_control", "daily_content_studio",
    "draft_inspector", "grounded_news_angle_lab", "publish_readiness_tower",
    "telegram_pilot_gate", "approval_queue", "content_calendar",
    "evidence_vault", "visual_export_studio", "settings_safety_policy",
]

HIGH_PRIORITY_SCREENS = [
    "command_center", "daily_content_studio", "publish_readiness_tower",
    "evidence_vault", "content_calendar", "visual_export_studio",
]

EXPLICIT_FORBIDDEN_ACTIONS = [
    "open_external_sites", "use_network", "submit_forms",
    "click_live_publish_connect_export_api_controls", "run_console_scripts",
    "paste_secrets", "read_env", "capture_screenshots", "upload_screenshots",
    "save_images_or_pdfs", "post_to_platforms", "schedule_posts",
    "call_telegram", "use_platform_credentials", "scrape_metrics",
    "mutate_evidence", "refresh_project_sources",
]

EVIDENCE_PACKET_FIELDS = [
    "task_label", "result_pass_blocked_fail", "worker_tool", "repo_path",
    "branch", "starting_head", "final_head", "browser_or_tool_used_and_exact_tool",
    "antigravity_run", "screenshots_captured", "network_used",
    "env_or_credentials_read", "external_url_opened", "screens_inspected",
    "issues_found", "disabled_control_status", "redaction_secret_status",
    "visual_quality_status", "safety_status", "validation_commands_results",
    "git_status", "active_blockers", "exact_next_task",
    "confirmation_no_live_api_posting_scheduling_export_evidence_mutation",
]

PASS_CRITERIA = [
    "all_12_screens_reachable", "no_rendering_crash", "no_broken_nav",
    "labels_visible", "disabled_controls_visually_clear",
    "no_secret_or_raw_env_or_raw_response_visible",
    "no_active_live_post_schedule_export_controls",
    "no_external_url_or_network_use", "no_antigravity_side_effects",
    "no_screenshots_unless_explicitly_authorized",
    "no_repo_mutation_except_scoped_evidence_docs",
]

BLOCKED_CRITERIA = [
    "browser_cannot_open_local_file", "screen_cannot_render", "nav_broken",
    "suspected_secret_visible", "active_forbidden_control_appears",
    "network_or_external_url_required",
    "screenshot_or_export_required_without_authorization",
    "credential_browser_profile_safety_ambiguity",
]

FAIL_CRITERIA = [
    "secret_or_env_value_displayed_or_captured", "external_site_opened",
    "network_or_api_call_made", "platform_login_used",
    "live_posting_scheduling_export_attempted",
    "screenshot_captured_without_authorization",
    "antigravity_run_outside_explicit_scope", "evidence_mutated_outside_scope",
    "repo_files_changed_outside_allowed_scope", "forbidden_controls_active",
]

STOP_CONDITIONS = [
    "secret_env_path_or_raw_response_appears", "any_external_url_opens",
    "any_control_attempts_network_publish_or_export",
    "browser_profile_exposes_credentials",
    "local_shell_requires_server_or_network",
    "antigravity_requests_broader_permissions_than_scoped",
]


def build_packet() -> dict:
    return {
        "packet_id": f"ag-qa-strategy-{uuid.uuid4().hex[:8]}",
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "task_label": "TASK_CONTENTOPS_0168_ANTIGRAVITY_BROWSER_QA_STRATEGY_AND_MANUAL_RUNBOOK_V0",
        "runbook_mode": "ANTIGRAVITY_BROWSER_QA_STRATEGY_RUNBOOK",
        "runtime_authority": False,
        "strategy_only": True,
        "browser_opened_now": False,
        "browser_automation_used_now": False,
        "antigravity_used_now": False,
        "screenshot_capture_enabled_now": False,
        "file_export_enabled_now": False,
        "platform_upload_enabled_now": False,
        "static_local_only": True,
        "credential_read_allowed_now": False,
        "platform_api_allowed_now": False,
        "provider_llm_api_allowed_now": False,
        "repo_web_search_allowed_now": False,
        "live_posting_enabled_now": False,
        "scheduler_allowed_now": False,
        "scraping_allowed_now": False,
        "evidence_mutation_enabled_now": False,
        "browser_qa_purpose": [
            "verify_local_static_rendering_only",
            "verify_nav_coverage_visually",
            "verify_visible_labels_watermarks_redaction_surfaces",
            "verify_disabled_controls_visually",
            "verify_layout_readability",
            "verify_no_accidental_live_post_export_affordance",
            "verify_screenshot_safe_surfaces",
            "verify_evidence_limitation_freshness_surfaces",
        ],
        "browser_qa_non_goals": [
            "no_backend_functionality_testing",
            "no_live_platform_testing",
            "no_telegram_testing",
            "no_provider_llm_testing",
            "no_credential_testing",
            "no_network_testing",
            "no_publishing_scheduling_export_testing",
            "no_market_data_validation",
            "no_screenshot_capture_unless_separately_authorized",
        ],
        "allowed_browser_target": {
            "local_file_only": "ui/institutional_shell/index.html",
            "file_protocol_manual_open_only": True,
            "local_static_server_only_if_future_task_explicitly_allows": True,
            "no_remote_url": True,
            "no_platform_login": True,
            "avoid_browser_profile_with_credentials": True,
            "no_devtools_network_calls": True,
        },
        "explicit_forbidden_actions": EXPLICIT_FORBIDDEN_ACTIONS,
        "manual_screen_checklist": [
            {
                "screen_id": s,
                "expected_checks": [
                    "screen_title_present",
                    "safety_status_labels_present",
                    "limitations_evidence_visible_where_applicable",
                    "disabled_controls_visibly_disabled",
                    "no_secret_raw_env_raw_response",
                    "no_active_publish_schedule_export_api_behavior",
                    "visual_layout_readable",
                    "no_red_green_market_direction_semantics",
                ],
            }
            for s in REQUIRED_SCREENS
        ],
        "high_priority_screen_checks": [
            {"screen_id": "command_center", "checks": ["kill_switch_active", "status_cards", "next_allowed_action"]},
            {"screen_id": "daily_content_studio", "checks": ["lanes", "grounded_news_rule", "source_evidence_requirements", "review_only_state"]},
            {"screen_id": "publish_readiness_tower", "checks": ["8_platforms_dry_run_only", "telegram_gate_disabled_redacted", "zero_live_enabled"]},
            {"screen_id": "evidence_vault", "checks": ["minor_evidence_gap_0163_visible", "evidence_mutation_disabled", "audit_timeline_visible"]},
            {"screen_id": "content_calendar", "checks": ["manual_workflow_only", "forbidden_states_not_active", "metrics_manual_only"]},
            {"screen_id": "visual_export_studio", "checks": ["screenshot_not_captured", "export_disabled", "redaction_watermarks_visible", "antigravity_future_only"]},
        ],
        "future_browser_qa_evidence_packet_template": EVIDENCE_PACKET_FIELDS,
        "future_browser_qa_pass_criteria": PASS_CRITERIA,
        "future_browser_qa_blocked_criteria": BLOCKED_CRITERIA,
        "future_browser_qa_fail_criteria": FAIL_CRITERIA,
        "stop_conditions": STOP_CONDITIONS,
        "future_next_task_guidance": {
            "self_authorizes_browser_qa": False,
            "next_allowed_action": "AWAIT OPERATOR/CHATGPT_AUDIT_OF_0168_RUNBOOK_EVIDENCE_BEFORE_ANY_BROWSER_OR_ANTIGRAVITY_TASK",
            "future_possible_task_named": "TASK_CONTENTOPS_0169_OPERATOR_APPROVED_ANTIGRAVITY_BROWSER_QA_LOCAL_STATIC_SHELL_V0",
            "future_task_requires_explicit_operator_chatgpt_go": True,
        },
        "blocked_reasons": [],
        "packet_status": "pass",
        "kill_switch_status": "active",
    }



_BOOL_FALSE_FIELDS = [
    "runtime_authority", "browser_opened_now", "browser_automation_used_now",
    "antigravity_used_now", "screenshot_capture_enabled_now",
    "file_export_enabled_now", "platform_upload_enabled_now",
    "credential_read_allowed_now", "platform_api_allowed_now",
    "provider_llm_api_allowed_now", "repo_web_search_allowed_now",
    "live_posting_enabled_now", "scheduler_allowed_now", "scraping_allowed_now",
    "evidence_mutation_enabled_now",
]


def validate_packet(packet: dict) -> dict:
    errors = []
    if packet.get("runtime_authority") is True:
        errors.append("runtime_authority_must_be_false")
    if packet.get("strategy_only") is not True:
        errors.append("strategy_only_must_be_true")
    if packet.get("static_local_only") is not True:
        errors.append("static_local_only_must_be_true")
    for f in _BOOL_FALSE_FIELDS:
        if packet.get(f) is True:
            errors.append(f"{f}_must_be_false")

    checklist_ids = {c.get("screen_id") for c in packet.get("manual_screen_checklist", [])}
    for s in REQUIRED_SCREENS:
        if s not in checklist_ids:
            errors.append(f"manual_checklist_missing_screen:{s}")

    forbidden = set(packet.get("explicit_forbidden_actions", []))
    for required in ["use_network", "open_external_sites", "paste_secrets",
                     "read_env", "capture_screenshots", "post_to_platforms",
                     "schedule_posts", "save_images_or_pdfs", "upload_screenshots"]:
        if required not in forbidden:
            errors.append(f"forbidden_actions_missing:{required}")

    tmpl = set(packet.get("future_browser_qa_evidence_packet_template", []))
    for required in ["browser_or_tool_used_and_exact_tool", "antigravity_run",
                     "screenshots_captured", "network_used", "env_or_credentials_read",
                     "external_url_opened", "screens_inspected", "disabled_control_status",
                     "redaction_secret_status", "git_status", "exact_next_task"]:
        if required not in tmpl:
            errors.append(f"evidence_template_missing:{required}")

    pass_c = set(packet.get("future_browser_qa_pass_criteria", []))
    for required in ["all_12_screens_reachable", "no_external_url_or_network_use",
                     "no_active_live_post_schedule_export_controls"]:
        if required not in pass_c:
            errors.append(f"pass_criteria_missing:{required}")

    blocked_c = set(packet.get("future_browser_qa_blocked_criteria", []))
    for required in ["suspected_secret_visible", "active_forbidden_control_appears"]:
        if required not in blocked_c:
            errors.append(f"blocked_criteria_missing:{required}")

    fail_c = set(packet.get("future_browser_qa_fail_criteria", []))
    for required in ["secret_or_env_value_displayed_or_captured", "external_site_opened",
                     "network_or_api_call_made", "screenshot_captured_without_authorization"]:
        if required not in fail_c:
            errors.append(f"fail_criteria_missing:{required}")

    stop_c = set(packet.get("stop_conditions", []))
    for required in ["secret_env_path_or_raw_response_appears", "any_external_url_opens",
                     "any_control_attempts_network_publish_or_export",
                     "browser_profile_exposes_credentials"]:
        if required not in stop_c:
            errors.append(f"stop_conditions_missing:{required}")

    guidance = packet.get("future_next_task_guidance", {})
    if guidance.get("self_authorizes_browser_qa") is True:
        errors.append("future_next_task_must_not_self_authorize_browser_qa")

    if packet.get("packet_status") == "pass" and errors:
        errors.append("packet_status_pass_but_errors_exist")

    return {"valid": not errors, "errors": errors}



def build_summary() -> dict:
    packet = build_packet()
    res = validate_packet(packet)
    guidance = packet["future_next_task_guidance"]
    return {
        "packet_status": packet["packet_status"] if res["valid"] else "blocked",
        "validation_valid": res["valid"],
        "runbook_mode": packet["runbook_mode"],
        "strategy_only": packet["strategy_only"],
        "browser_opened_now": packet["browser_opened_now"],
        "browser_automation_used_now": packet["browser_automation_used_now"],
        "antigravity_used_now": packet["antigravity_used_now"],
        "screenshot_capture_enabled_now": packet["screenshot_capture_enabled_now"],
        "file_export_enabled_now": packet["file_export_enabled_now"],
        "platform_upload_enabled_now": packet["platform_upload_enabled_now"],
        "static_local_only": packet["static_local_only"],
        "credential_read_allowed_now": packet["credential_read_allowed_now"],
        "platform_api_allowed_now": packet["platform_api_allowed_now"],
        "provider_llm_api_allowed_now": packet["provider_llm_api_allowed_now"],
        "repo_web_search_allowed_now": packet["repo_web_search_allowed_now"],
        "live_posting_enabled_now": packet["live_posting_enabled_now"],
        "scheduler_allowed_now": packet["scheduler_allowed_now"],
        "scraping_allowed_now": packet["scraping_allowed_now"],
        "evidence_mutation_enabled_now": packet["evidence_mutation_enabled_now"],
        "manual_screen_check_count": len(packet["manual_screen_checklist"]),
        "high_priority_screen_check_count": len(packet["high_priority_screen_checks"]),
        "explicit_forbidden_action_count": len(packet["explicit_forbidden_actions"]),
        "evidence_packet_field_count": len(packet["future_browser_qa_evidence_packet_template"]),
        "pass_criteria_count": len(packet["future_browser_qa_pass_criteria"]),
        "blocked_criteria_count": len(packet["future_browser_qa_blocked_criteria"]),
        "fail_criteria_count": len(packet["future_browser_qa_fail_criteria"]),
        "stop_condition_count": len(packet["stop_conditions"]),
        "future_browser_task_named": bool(guidance.get("future_possible_task_named")),
        "future_browser_task_self_authorized": guidance.get("self_authorizes_browser_qa"),
        "next_allowed_action_present": bool(guidance.get("next_allowed_action")),
        "kill_switch_status": packet["kill_switch_status"],
        "blocked_reasons": res["errors"],
    }

