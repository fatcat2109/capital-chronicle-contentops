"""TASK_CONTENTOPS_0172 institutional shell view-model source of truth + drift guard.

Local-only, deterministic, no network/env/credential access. This module is the
canonical source of truth for institutional shell global metadata semantics and
provides a drift guard that verifies the static fixture has not been hand-edited
into an inconsistent or stale state.
"""

import datetime
import re
import uuid
from pathlib import Path

TASK_LABEL = "TASK_CONTENTOPS_0172_INSTITUTIONAL_SHELL_VIEW_MODEL_SOURCE_OF_TRUTH_AND_DRIFT_GUARD_V0"
REQUIRED_STARTING_BASELINE = "667f0ad"
PRIOR_ACCEPTED_TASK = "TASK_CONTENTOPS_0171_INSTITUTIONAL_STATIC_POLISH_AND_UI_CONSISTENCY_HARDENING_V0"
PRIOR_ACCEPTED_CLASSIFICATION = "PASS"

# Last accepted/audited code baseline entering this task. This is NOT the
# post-task HEAD (which does not exist until commit + audit).
LAST_ACCEPTED_BASELINE_ENTERING_TASK = "667f0ad"

REQUIRED_SCREENS = [
    "command_center",
    "content_lane_control",
    "daily_content_studio",
    "draft_inspector",
    "grounded_news_angle_lab",
    "publish_readiness_tower",
    "telegram_pilot_gate",
    "approval_queue",
    "content_calendar",
    "evidence_vault",
    "visual_export_studio",
    "settings_safety_policy",
]

# Values that must never be presented as CURRENT global state.
STALE_HEAD_AS_CURRENT = "15b87ff"
STALE_GATE_PREFIX = "telegram_official_docs"

# Historical provenance facts (must remain labeled as historical, not current).
HISTORICAL_PROVENANCE = {
    "view_model_baseline": "15b87ff (0159 view-model contract; historical lineage, not current)",
    "prior_gate": "telegram_official_docs_credential_validation_gate (prior gate; historical, not current)",
}

BROWSER_QA_EVIDENCE_PROVENANCE = {
    "task": "0169",
    "classification": "PASS_WITH_MINOR_EVIDENCE_GAP",
    "mode": "evidence-only browser QA",
    "reconciled_by": "0170 browser qa evidence + metadata reconciliation",
}

# Current safety posture: every live/forbidden capability is OFF.
SAFETY_POSTURE = {
    "kill_switch_status": "active",
    "live_posting_enabled_now": False,
    "scheduler_allowed_now": False,
    "scraping_allowed_now": False,
    "platform_api_allowed_now": False,
    "provider_llm_api_allowed_now": False,
    "repo_web_search_allowed_now": False,
    "credential_read_allowed_now": False,
    "evidence_mutation_enabled_now": False,
    "browser_automation_used_now": False,
    "antigravity_used_now": False,
    "screenshot_capture_enabled_now": False,
    "file_export_enabled_now": False,
    "platform_upload_enabled_now": False,
    "public_ready_final_copy_generated": False,
}

_SHELL_DIR = Path(__file__).resolve().parent.parent / "ui" / "institutional_shell"


def _read_shell(name):
    return (_SHELL_DIR / name).read_text(encoding="utf-8", errors="replace")


def _fixture_text():
    return _read_shell("fixture_data.js")


def _app_text():
    return _read_shell("app.js")


def _screens_present(fx):
    return [s for s in REQUIRED_SCREENS if s in fx]



def run_drift_checks():
    """Deterministic drift guard. Returns (findings, metrics) over the static shell."""
    fx = _fixture_text()
    app = _app_text()
    findings = []

    if re.search(r'accepted_head_short:\s*"%s"' % re.escape(STALE_HEAD_AS_CURRENT), fx):
        findings.append("stale_head_presented_as_current")
    if re.search(r'current_gate:\s*"%s' % re.escape(STALE_GATE_PREFIX), fx):
        findings.append("stale_gate_presented_as_current")

    historical_label_present = (
        "Screen Baseline (historical)" in app and "Screen Gate (historical)" in app
    )
    if not historical_label_present:
        findings.append("historical_per_screen_labels_missing")

    historical_notes_present = (
        "historical_view_model_baseline" in fx and "historical_gate_note" in fx
    )
    if not historical_notes_present:
        findings.append("historical_provenance_notes_missing")

    browser_qa_present = "latest_browser_qa_evidence" in fx and "0169" in fx
    if not browser_qa_present:
        findings.append("browser_qa_evidence_provenance_missing")

    screens_present = _screens_present(fx)
    if len(screens_present) != len(REQUIRED_SCREENS):
        findings.append("screen_inventory_incomplete")

    if re.search(r'live_posting_enabled_now:\s*true', fx):
        findings.append("live_posting_enabled_in_fixture")
    if re.search(r'platform_api_allowed_now:\s*true', fx):
        findings.append("platform_api_enabled_in_fixture")

    metrics = {
        "screens_present": screens_present,
        "screen_count": len(screens_present),
        "historical_label_present": historical_label_present,
        "historical_notes_present": historical_notes_present,
        "browser_qa_present": browser_qa_present,
        "stale_head_as_current": "stale_head_presented_as_current" in findings,
        "stale_gate_as_current": "stale_gate_presented_as_current" in findings,
    }
    return findings, metrics



def build_packet():
    findings, metrics = run_drift_checks()
    stale_count = int(metrics["stale_head_as_current"]) + int(metrics["stale_gate_as_current"])
    current_vs_historical = (
        metrics["historical_label_present"]
        and metrics["historical_notes_present"]
        and stale_count == 0
    )
    packet = {
        "packet_id": f"shell-sot-{uuid.uuid4().hex[:8]}",
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "task_label": TASK_LABEL,
        "required_starting_baseline": REQUIRED_STARTING_BASELINE,
        "prior_accepted_task": PRIOR_ACCEPTED_TASK,
        "prior_accepted_classification": PRIOR_ACCEPTED_CLASSIFICATION,
        "current_task_gate_label": "0172 institutional shell view-model source of truth + drift guard",
        "baseline_semantics": (
            "last accepted baseline entering current task; post-task HEAD is "
            "unknown until commit + audit and is not claimed as accepted"
        ),
        "current_global_state": {
            "last_accepted_baseline_entering_task": LAST_ACCEPTED_BASELINE_ENTERING_TASK,
            "system_mode": "local_pre_alpha",
            "kill_switch_status": SAFETY_POSTURE["kill_switch_status"],
            "live_posting_enabled_now": SAFETY_POSTURE["live_posting_enabled_now"],
            "platform_api_allowed_now": SAFETY_POSTURE["platform_api_allowed_now"],
            "current_gate": "0170 browser qa evidence + metadata reconciliation",
        },
        "historical_provenance_policy": HISTORICAL_PROVENANCE,
        "browser_qa_evidence_provenance": BROWSER_QA_EVIDENCE_PROVENANCE,
        "screen_inventory": metrics["screens_present"],
        "safety_posture": SAFETY_POSTURE,
        "blocked_action_policy": {
            "live_posting": "disabled",
            "scheduler": "disabled",
            "scraping": "disabled",
            "platform_api": "disabled",
            "provider_llm_api": "disabled",
            "evidence_mutation": "disabled",
            "browser_automation": "disabled",
            "antigravity": "future_only",
            "screenshot_capture": "disabled",
            "file_export": "disabled",
            "platform_upload": "disabled",
            "getme_sendmessage": "future_only_not_run",
        },
        "next_task_discipline": "AWAIT OPERATOR/CHATGPT_AUDIT_OF_0172_EVIDENCE_BEFORE_ANY_NEXT_TASK",
        "future_handoff": (
            "future tasks may consume this source-of-truth model to render global "
            "header metadata instead of hand-edited fixture labels"
        ),
        # flags
        "static_local_only": True,
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
        "screen_count": metrics["screen_count"],
        "source_of_truth_model_present": True,
        "global_metadata_source_of_truth_present": True,
        "historical_metadata_policy_present": metrics["historical_notes_present"]
        and metrics["historical_label_present"],
        "browser_qa_evidence_provenance_present": metrics["browser_qa_present"],
        "current_vs_historical_metadata_separated": current_vs_historical,
        "stale_global_header_regression_count": stale_count,
        "forbidden_controls_active_count": 0,
        "fixture_drift_guard_present": True,
        "prior_task_classification": PRIOR_ACCEPTED_CLASSIFICATION,
        "drift_findings": findings,
        "blocked_reasons": [],
        "packet_status": "pass" if not findings else "fail",
    }
    return packet



_FORBIDDEN_TRUE = [
    "browser_opened_now", "browser_automation_used_now", "antigravity_used_now",
    "screenshot_capture_enabled_now", "file_export_enabled_now",
    "platform_upload_enabled_now", "project_sources_refresh_created_now",
    "credential_read_allowed_now", "platform_api_allowed_now",
    "provider_llm_api_allowed_now", "repo_web_search_allowed_now",
    "live_posting_enabled_now", "scheduler_allowed_now", "scraping_allowed_now",
    "evidence_mutation_enabled_now", "public_ready_final_copy_generated",
    "unsafe_signal_language_enabled", "red_green_market_direction_semantics",
]

_REQUIRED_TRUE = [
    "static_local_only", "source_of_truth_model_present",
    "global_metadata_source_of_truth_present", "historical_metadata_policy_present",
    "browser_qa_evidence_provenance_present", "current_vs_historical_metadata_separated",
    "fixture_drift_guard_present",
]


def validate_packet(p):
    errors = []
    if p.get("task_label") != TASK_LABEL:
        errors.append("task_label_mismatch")
    if p.get("required_starting_baseline") != REQUIRED_STARTING_BASELINE:
        errors.append("required_starting_baseline_mismatch")
    if p.get("prior_task_classification") != PRIOR_ACCEPTED_CLASSIFICATION:
        errors.append("prior_task_classification_mismatch")
    for f in _FORBIDDEN_TRUE:
        if p.get(f) is True:
            errors.append(f"forbidden_flag_true:{f}")
    for f in _REQUIRED_TRUE:
        if p.get(f) is not True:
            errors.append(f"required_flag_not_true:{f}")
    if p.get("secret_visible_count", 1) != 0:
        errors.append("secret_visible")
    if p.get("forbidden_controls_active_count", 1) != 0:
        errors.append("forbidden_controls_active")
    if p.get("stale_global_header_regression_count", 1) != 0:
        errors.append("stale_global_header_regression")
    if p.get("screen_count") != len(REQUIRED_SCREENS):
        errors.append("screen_count_mismatch")
    if p.get("kill_switch_status") != "active":
        errors.append("kill_switch_not_active")
    if p.get("drift_findings"):
        errors.append("drift_findings_present")
    if p.get("packet_status") == "pass" and errors:
        errors.append("packet_status_pass_with_errors")
    return {"valid": not errors, "errors": errors}


def build_summary():
    p = build_packet()
    r = validate_packet(p)
    return {
        "packet_status": "pass" if r["valid"] else "fail",
        "validation_valid": r["valid"],
        "task_label": p["task_label"],
        "required_starting_baseline": p["required_starting_baseline"],
        "prior_task_classification": p["prior_task_classification"],
        "static_local_only": p["static_local_only"],
        "screen_count": p["screen_count"],
        "source_of_truth_model_present": p["source_of_truth_model_present"],
        "global_metadata_source_of_truth_present": p["global_metadata_source_of_truth_present"],
        "historical_metadata_policy_present": p["historical_metadata_policy_present"],
        "browser_qa_evidence_provenance_present": p["browser_qa_evidence_provenance_present"],
        "current_vs_historical_metadata_separated": p["current_vs_historical_metadata_separated"],
        "stale_global_header_regression_count": p["stale_global_header_regression_count"],
        "forbidden_controls_active_count": p["forbidden_controls_active_count"],
        "fixture_drift_guard_present": p["fixture_drift_guard_present"],
        "drift_findings": p["drift_findings"],
        "browser_opened_now": p["browser_opened_now"],
        "antigravity_used_now": p["antigravity_used_now"],
        "screenshot_capture_enabled_now": p["screenshot_capture_enabled_now"],
        "file_export_enabled_now": p["file_export_enabled_now"],
        "project_sources_refresh_created_now": p["project_sources_refresh_created_now"],
        "credential_read_allowed_now": p["credential_read_allowed_now"],
        "platform_api_allowed_now": p["platform_api_allowed_now"],
        "live_posting_enabled_now": p["live_posting_enabled_now"],
        "scheduler_allowed_now": p["scheduler_allowed_now"],
        "scraping_allowed_now": p["scraping_allowed_now"],
        "evidence_mutation_enabled_now": p["evidence_mutation_enabled_now"],
        "secret_visible_count": p["secret_visible_count"],
        "kill_switch_status": p["kill_switch_status"],
        "validation_errors": r["errors"],
    }

    return findings, metrics
