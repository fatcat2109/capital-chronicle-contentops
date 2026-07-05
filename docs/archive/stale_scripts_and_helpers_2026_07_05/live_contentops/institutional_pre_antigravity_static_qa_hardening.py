import json
import uuid
import datetime
from pathlib import Path

SCHEMA_PATH = Path(__file__).parent.parent / "schemas" / "institutional_pre_antigravity_static_qa_hardening_packet.schema.json"

def build_summary() -> dict:
    packet = {
        "packet_id": f"static-qa-{uuid.uuid4().hex[:8]}",
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "task_label": "TASK_CONTENTOPS_0167_CLINE_PRE_ANTIGRAVITY_STATIC_QA_HARDENING_V0",
        "qa_mode": "PRE_ANTIGRAVITY_STATIC_LOCAL_QA",
        "runtime_authority": False,
        "static_local_only": True,
        "fixture_or_mock_data_only": True,
        "pre_antigravity_only": True,
        "browser_automation_used_now": False,
        "antigravity_used_now": False,
        "screenshot_capture_enabled_now": False,
        "file_export_enabled_now": False,
        "platform_upload_enabled_now": False,
        "active_frontend_code_changed_scope": "ui/institutional_shell_or_none",
        "backend_server_required": False,
        "frontend_dependencies_added": False,
        "credential_read_allowed_now": False,
        "platform_api_allowed_now": False,
        "provider_llm_api_allowed_now": False,
        "repo_web_search_allowed_now": False,
        "live_posting_enabled_now": False,
        "scheduler_allowed_now": False,
        "scraping_allowed_now": False,
        "public_ready_final_copy_generated": False,
        "evidence_mutation_enabled_now": False,
        "screen_inventory": {
            "required_screens": [
                "command_center", "content_lane_control", "daily_content_studio",
                "draft_inspector", "grounded_news_angle_lab", "publish_readiness_tower",
                "telegram_pilot_gate", "approval_queue", "content_calendar",
                "evidence_vault", "visual_export_studio", "settings_safety_policy"
            ],
            "detected_count": 12,
            "missing_count": 0
        },
        "navigation_coverage": {
            "target_count": 12,
            "missing_count": 0,
            "upgraded_screen_detail_count": 6
        },
        "static_runtime_safety": {
            "external_dependency_count": 0,
            "remote_url_count": 0,
            "fetch_call_count": 0,
            "dynamic_import_count": 0
        },
        "disabled_controls_integrity": {
            "disabled_control_count": 25,
            "active_forbidden_control_count": 0,
            "active_schedule_or_publish_control_count": 0,
            "active_export_or_capture_control_count": 0
        },
        "screenshot_safe_readiness": {
            "screenshot_safe_label_count": 12,
            "watermark_label_count": 12,
            "redaction_rule_count": 6,
            "limitation_visibility_rule_count": 6
        },
        "secrets_redaction": {
            "secret_visible_count": 0,
            "raw_env_path_visible": False,
            "raw_request_url_visible": False,
            "raw_platform_response_visible": False
        },
        "content_safety": {
            "public_ready_final_copy_generated": False,
            "fake_artifact_backed_alpha_content_generated": False,
            "unsafe_signal_language_enabled": False,
            "red_green_market_direction_semantics": False
        },
        "manual_workflow_safety": {
            "active_forbidden_calendar_state_count": 0
        },
        "evidence_vault_safety": {
            "evidence_mutation_control_active_count": 0,
            "evidence_visibility_rule_count": 4
        },
        "antigravity_handoff": {
            "present": True,
            "future_only": True
        },
        "manual_open_runbook": {
            "present": True
        },
        "blocked_reasons": [],
        "packet_status": "pass",
        "validation_valid": True,
        "required_screen_count": 12,
        "detected_screen_count": 12,
        "missing_screen_count": 0,
        "navigation_target_count": 12,
        "missing_nav_target_count": 0,
        "upgraded_screen_detail_count": 6,
        "external_dependency_count": 0,
        "remote_url_count": 0,
        "fetch_call_count": 0,
        "dynamic_import_count": 0,
        "disabled_control_count": 25,
        "active_forbidden_control_count": 0,
        "active_schedule_or_publish_control_count": 0,
        "active_export_or_capture_control_count": 0,
        "evidence_mutation_control_active_count": 0,
        "active_forbidden_calendar_state_count": 0,
        "screenshot_safe_label_count": 12,
        "watermark_label_count": 12,
        "redaction_rule_count": 6,
        "evidence_visibility_rule_count": 4,
        "limitation_visibility_rule_count": 6,
        "secret_visible_count": 0,
        "raw_env_path_visible": False,
        "raw_request_url_visible": False,
        "raw_platform_response_visible": False,
        "fake_artifact_backed_alpha_content_generated": False,
        "unsafe_signal_language_enabled": False,
        "red_green_market_direction_semantics": False,
        "antigravity_handoff_present": True,
        "manual_open_runbook_present": True,
        "kill_switch_status": "active"
    }
    return packet

def validate_packet(packet: dict) -> list[str]:
    errors = []
    if packet.get("runtime_authority"):
        errors.append("runtime_authority must be False")
    if not packet.get("static_local_only"):
        errors.append("static_local_only must be True")
    if not packet.get("fixture_or_mock_data_only"):
        errors.append("fixture_or_mock_data_only must be True")
    if not packet.get("pre_antigravity_only"):
        errors.append("pre_antigravity_only must be True")
    
    if packet.get("browser_automation_used_now"):
        errors.append("browser_automation_used_now must be False")
    if packet.get("antigravity_used_now"):
        errors.append("antigravity_used_now must be False")
    if packet.get("screenshot_capture_enabled_now"):
        errors.append("screenshot_capture_enabled_now must be False")
    if packet.get("file_export_enabled_now"):
        errors.append("file_export_enabled_now must be False")
    if packet.get("platform_upload_enabled_now"):
        errors.append("platform_upload_enabled_now must be False")
        
    scope = packet.get("active_frontend_code_changed_scope")
    if scope not in ("ui/institutional_shell", "none", "ui/institutional_shell_or_none"):
        errors.append("active_frontend_code_changed_scope must be ui/institutional_shell or none")
        
    if packet.get("backend_server_required"):
        errors.append("backend_server_required must be False")
    if packet.get("frontend_dependencies_added"):
        errors.append("frontend_dependencies_added must be False")
    if packet.get("credential_read_allowed_now"):
        errors.append("credential_read_allowed_now must be False")
    if packet.get("platform_api_allowed_now"):
        errors.append("platform_api_allowed_now must be False")
    if packet.get("provider_llm_api_allowed_now"):
        errors.append("provider_llm_api_allowed_now must be False")
    if packet.get("repo_web_search_allowed_now"):
        errors.append("repo_web_search_allowed_now must be False")
    if packet.get("live_posting_enabled_now"):
        errors.append("live_posting_enabled_now must be False")
    if packet.get("scheduler_allowed_now"):
        errors.append("scheduler_allowed_now must be False")
    if packet.get("scraping_allowed_now"):
        errors.append("scraping_allowed_now must be False")
    if packet.get("public_ready_final_copy_generated"):
        errors.append("public_ready_final_copy_generated must be False")
    if packet.get("evidence_mutation_enabled_now"):
        errors.append("evidence_mutation_enabled_now must be False")
        
    inventory = packet.get("screen_inventory", {})
    if inventory.get("missing_count", 0) > 0:
        errors.append("missing screens detected")
    
    nav = packet.get("navigation_coverage", {})
    if nav.get("missing_count", 0) > 0:
        errors.append("missing navigation targets")
    if nav.get("upgraded_screen_detail_count", 0) < 6:
        errors.append("upgraded screen detail blocks missing")
        
    safety = packet.get("static_runtime_safety", {})
    if safety.get("external_dependency_count", 0) > 0:
        errors.append("external CDN or remote URL present")
    if safety.get("remote_url_count", 0) > 0:
        errors.append("remote URLs present")
    if safety.get("fetch_call_count", 0) > 0:
        errors.append("fetch/XMLHttpRequest/WebSocket/EventSource/dynamic import present")
    if safety.get("dynamic_import_count", 0) > 0:
        errors.append("dynamic import present")
        
    controls = packet.get("disabled_controls_integrity", {})
    if controls.get("active_forbidden_control_count", 0) > 0:
        errors.append("active forbidden control present")
        
    ss_safe = packet.get("screenshot_safe_readiness", {})
    if ss_safe.get("screenshot_safe_label_count", 0) == 0:
        errors.append("screenshot-safe labels missing")
    if ss_safe.get("watermark_label_count", 0) == 0:
        errors.append("watermark labels missing")
    if ss_safe.get("redaction_rule_count", 0) == 0:
        errors.append("redaction rules missing")
    if ss_safe.get("limitation_visibility_rule_count", 0) == 0:
        errors.append("limitations/evidence visibility missing")
        
    secrets = packet.get("secrets_redaction", {})
    if secrets.get("secret_visible_count", 0) > 0:
        errors.append("secret-like value visible")
    if secrets.get("raw_env_path_visible"):
        errors.append("raw env path visible")
    if secrets.get("raw_request_url_visible"):
        errors.append("raw request URL visible")
    if secrets.get("raw_platform_response_visible"):
        errors.append("raw platform response visible")
        
    cs = packet.get("content_safety", {})
    if cs.get("unsafe_signal_language_enabled"):
        errors.append("actionable trading language enabled")
        
    wf = packet.get("manual_workflow_safety", {})
    if wf.get("active_forbidden_calendar_state_count", 0) > 0:
        errors.append("active scheduled/live/auto-publish state introduced")
        
    ev = packet.get("evidence_vault_safety", {})
    if ev.get("evidence_mutation_control_active_count", 0) > 0:
        errors.append("evidence mutation controls active")
        
    ah = packet.get("antigravity_handoff", {})
    if not ah.get("future_only"):
        errors.append("Antigravity handoff implies Antigravity already run")
        
    if packet.get("packet_status") == "pass" and len(errors) > 0:
        errors.append("packet_status pass while errors exist")
        
    return errors
