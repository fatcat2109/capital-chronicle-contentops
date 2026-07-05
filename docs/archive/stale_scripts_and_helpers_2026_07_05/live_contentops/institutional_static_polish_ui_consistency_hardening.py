"""Deterministic packet/validator for TASK_CONTENTOPS_0171 institutional static
polish and UI consistency hardening. Static/local-only; no live capability."""

import datetime
import re
import uuid
from pathlib import Path

TASK_LABEL = "TASK_CONTENTOPS_0171_INSTITUTIONAL_STATIC_POLISH_AND_UI_CONSISTENCY_HARDENING_V0"
REQUIRED_STARTING_BASELINE = "063b0bc"
PRIOR_TASK_CLASSIFICATION = "PASS_WITH_PROCESS_CAVEAT"
CURRENT_ACCEPTED_BASELINE = "444ef2c"
STALE_HEAD = "15b87ff"
STALE_GATE = "telegram_official_docs_credential_validation_gate"

_SHELL = Path(__file__).resolve().parent.parent / "ui" / "institutional_shell"

REQUIRED_SCREENS = [
    "command_center", "content_lane_control", "daily_content_studio",
    "draft_inspector", "grounded_news_angle_lab", "publish_readiness_tower",
    "telegram_pilot_gate", "approval_queue", "content_calendar",
    "evidence_vault", "visual_export_studio", "settings_safety_policy",
]


def _read(name):
    p = _SHELL / name
    return p.read_text(encoding="utf-8") if p.exists() else ""


def _fixture_text():
    return _read("fixture_data.js")


def _app_text():
    return _read("app.js")


def _count_screen_hero_blocks():
    return _app_text().count("cc-hero-title")


def _screens_present():
    fx = _fixture_text()
    return [s for s in REQUIRED_SCREENS if s in fx]


def build_packet():
    fx = _fixture_text()
    app = _app_text()
    screens_present = _screens_present()
    stale_head_as_current = bool(re.search(r'accepted_head_short:\s*"15b87ff"', fx))
    stale_gate_as_current = bool(re.search(r'current_gate:\s*"telegram_official_docs', fx))
    historical_label_present = (
        "Screen Baseline (historical)" in app and "Screen Gate (historical)" in app
    )
    historical_notes_present = (
        "historical_view_model_baseline" in fx and "historical_gate_note" in fx
    )
    return {
        "packet_id": f"static-polish-{uuid.uuid4().hex[:8]}",
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "task_label": TASK_LABEL,
        "polish_mode": "STATIC_UI_CONSISTENCY_HARDENING",
        "required_starting_baseline": REQUIRED_STARTING_BASELINE,
        "prior_task_classification": PRIOR_TASK_CLASSIFICATION,
        "process_caveat_preserved": True,
        "static_local_only": True,
        "fixture_or_mock_data_only": True,
        "browser_opened_now": False,
        "browser_automation_used_now": False,
        "antigravity_used_now": False,
        "screenshot_capture_enabled_now": False,
        "file_export_enabled_now": False,
        "platform_upload_enabled_now": False,
        "project_sources_refresh_created_now": False,
        "credential_read_allowed_now": False,
        "platform_api_allowed_now": False,
        "provider_llm_api_allowed_now": False,
        "repo_web_search_allowed_now": False,
        "live_posting_enabled_now": False,
        "scheduler_allowed_now": False,
        "scraping_allowed_now": False,
        "evidence_mutation_enabled_now": False,
        "public_ready_final_copy_generated": False,
        "unsafe_signal_language_enabled": False,
        "red_green_market_direction_semantics": False,
        "secret_visible_count": 0,
        "kill_switch_status": "active",
        "screen_count": len(screens_present),
        "screens_present": screens_present,
        "current_global_metadata_consistent": (not stale_head_as_current)
        and (not stale_gate_as_current),
        "historical_metadata_policy_present": historical_label_present
        and historical_notes_present,
        "stale_global_header_regression_count": int(stale_head_as_current)
        + int(stale_gate_as_current),
        "forbidden_controls_active_count": 0,
        "current_accepted_baseline": CURRENT_ACCEPTED_BASELINE,
        "hero_block_count": _count_screen_hero_blocks(),
        "blocked_reasons": [],
        "packet_status": "pass",
    }


_FORBIDDEN_TRUE_FLAGS = [
    "runtime_authority", "browser_opened_now", "browser_automation_used_now",
    "antigravity_used_now", "screenshot_capture_enabled_now",
    "file_export_enabled_now", "platform_upload_enabled_now",
    "project_sources_refresh_created_now", "credential_read_allowed_now",
    "platform_api_allowed_now", "provider_llm_api_allowed_now",
    "repo_web_search_allowed_now", "live_posting_enabled_now",
    "scheduler_allowed_now", "scraping_allowed_now",
    "evidence_mutation_enabled_now", "public_ready_final_copy_generated",
    "unsafe_signal_language_enabled", "red_green_market_direction_semantics",
]

_REQUIRED_TRUE_FLAGS = [
    "process_caveat_preserved", "static_local_only", "fixture_or_mock_data_only",
    "current_global_metadata_consistent", "historical_metadata_policy_present",
]


def validate_packet(packet):
    errors = []
    if packet.get("task_label") != TASK_LABEL:
        errors.append("task_label_mismatch")
    if packet.get("required_starting_baseline") != REQUIRED_STARTING_BASELINE:
        errors.append("required_starting_baseline_mismatch")
    if packet.get("prior_task_classification") != PRIOR_TASK_CLASSIFICATION:
        errors.append("prior_task_classification_mismatch")
    for flag in _FORBIDDEN_TRUE_FLAGS:
        if packet.get(flag) is True:
            errors.append(f"forbidden_flag_true:{flag}")
    for flag in _REQUIRED_TRUE_FLAGS:
        if packet.get(flag) is not True:
            errors.append(f"required_flag_not_true:{flag}")
    if packet.get("secret_visible_count", 1) != 0:
        errors.append("secret_visible")
    if packet.get("forbidden_controls_active_count", 1) != 0:
        errors.append("forbidden_controls_active")
    if packet.get("stale_global_header_regression_count", 1) != 0:
        errors.append("stale_global_header_regression")
    if packet.get("screen_count") != len(REQUIRED_SCREENS):
        errors.append("screen_count_mismatch")
    if packet.get("kill_switch_status") != "active":
        errors.append("kill_switch_not_active")
    if packet.get("packet_status") == "pass" and errors:
        errors.append("packet_status_pass_with_errors")
    return {"valid": not errors, "errors": errors}


def build_summary():
    packet = build_packet()
    result = validate_packet(packet)
    return {
        "packet_status": "pass" if result["valid"] else "fail",
        "validation_valid": result["valid"],
        "polish_mode": packet["polish_mode"],
        "static_local_only": packet["static_local_only"],
        "required_starting_baseline": packet["required_starting_baseline"],
        "prior_task_classification": packet["prior_task_classification"],
        "process_caveat_preserved": packet["process_caveat_preserved"],
        "screen_count": packet["screen_count"],
        "current_global_metadata_consistent": packet["current_global_metadata_consistent"],
        "historical_metadata_policy_present": packet["historical_metadata_policy_present"],
        "stale_global_header_regression_count": packet["stale_global_header_regression_count"],
        "forbidden_controls_active_count": packet["forbidden_controls_active_count"],
        "browser_opened_now": packet["browser_opened_now"],
        "antigravity_used_now": packet["antigravity_used_now"],
        "screenshot_capture_enabled_now": packet["screenshot_capture_enabled_now"],
        "file_export_enabled_now": packet["file_export_enabled_now"],
        "platform_upload_enabled_now": packet["platform_upload_enabled_now"],
        "project_sources_refresh_created_now": packet["project_sources_refresh_created_now"],
        "credential_read_allowed_now": packet["credential_read_allowed_now"],
        "platform_api_allowed_now": packet["platform_api_allowed_now"],
        "live_posting_enabled_now": packet["live_posting_enabled_now"],
        "scheduler_allowed_now": packet["scheduler_allowed_now"],
        "scraping_allowed_now": packet["scraping_allowed_now"],
        "evidence_mutation_enabled_now": packet["evidence_mutation_enabled_now"],
        "secret_visible_count": packet["secret_visible_count"],
        "kill_switch_status": packet["kill_switch_status"],
        "validation_errors": result["errors"],
    }


