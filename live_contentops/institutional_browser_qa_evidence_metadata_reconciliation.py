import uuid
import datetime

REQUIRED_SCREENS = [
    "command_center", "content_lane_control", "daily_content_studio",
    "draft_inspector", "grounded_news_angle_lab", "publish_readiness_tower",
    "telegram_pilot_gate", "approval_queue", "content_calendar",
    "evidence_vault", "visual_export_studio", "settings_safety_policy",
]

LATEST_ACCEPTED_CODE_BASELINE = "444ef2c"
STALE_HEAD = "15b87ff"
STALE_GATE = "telegram_official_docs_credential_validation_gate"


def _screen_result(sid, note):
    return {
        "screen_id": sid,
        "reached": "yes",
        "visible_title_header": "yes",
        "safety_status_labels": "yes",
        "disabled_controls_safe": "yes",
        "evidence_limitations_freshness_visible": "yes",
        "secret_raw_data_visible": "no",
        "active_forbidden_control_visible": "no",
        "note": note,
    }



def _build_browser_qa_evidence_packet():
    return {
        "task_label": "TASK_CONTENTOPS_0169_OPERATOR_APPROVED_ANTIGRAVITY_BROWSER_QA_LOCAL_STATIC_SHELL_V0",
        "audit_classification": "PASS_WITH_MINOR_EVIDENCE_GAP",
        "browser_opened": "yes",
        "local_file_url_opened": "yes",
        "local_file_url": "file:///A:/Capital%20Chronicle/tools/cc-live-contentops/ui/institutional_shell/index.html",
        "external_url_opened": "no",
        "network_used_observed": "no",
        "screenshots_captured": "no",
        "screenshots_captured_clarification": (
            "worker reported no screenshot capture and no screenshot/export files "
            "generated; operator/browser visual feedback images may exist outside "
            "repo and are not repo export artifacts"
        ),
        "files_created_or_changed_by_browser_qa": "no",
        "all_12_screens_reached": "yes",
        "secret_raw_data_visible": "no",
        "active_forbidden_controls_visible": "no",
        "active_publish_schedule_export_api_evidence_mutation_control_count": 0,
        "exact_next_task_after_audit": "AWAIT OPERATOR/CHATGPT_AUDIT_OF_0169_ANTIGRAVITY_BROWSER_QA_EVIDENCE_BEFORE_ANY_NEXT_TASK",
    }


def _build_screen_results():
    notes = {
        "command_center": "Kill switch active, status cards, next allowed action visible.",
        "content_lane_control": "Lanes visible; future artifact-backed lane blocked.",
        "daily_content_studio": "Review-only; source/evidence requirements visible.",
        "draft_inspector": "Source/lineage and guardrails visible; review-only.",
        "grounded_news_angle_lab": "News-as-hook rule visible; no signal language.",
        "publish_readiness_tower": "8 platforms dry-run only; live disabled; Telegram redacted.",
        "telegram_pilot_gate": "Credential presence redacted; sendMessage disabled.",
        "approval_queue": "Operator approval required; no auto-approval.",
        "content_calendar": "Manual workflow only; forbidden states not active.",
        "evidence_vault": "Audit timeline visible; evidence mutation disabled.",
        "visual_export_studio": "Screenshot-safe; export disabled; redaction visible.",
        "settings_safety_policy": "Policy display only; no credential values; no API toggles.",
    }
    return [_screen_result(sid, notes[sid]) for sid in REQUIRED_SCREENS]


def build_packet():
    return {
        "packet_id": f"bqa-reconcile-{uuid.uuid4().hex[:8]}",
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "task_label": "TASK_CONTENTOPS_0170_BROWSER_QA_EVIDENCE_PACKET_AND_GLOBAL_HEADER_METADATA_RECONCILIATION_V0",
        "reconciliation_mode": "BROWSER_QA_EVIDENCE_AND_METADATA_RECONCILIATION",
        "runtime_authority": False,
        "static_local_only": True,
        "fixture_or_mock_data_only": True,
        "browser_rerun_now": False,
        "antigravity_used_now": False,
        "screenshot_capture_enabled_now": False,
        "file_export_enabled_now": False,
        "platform_upload_enabled_now": False,
        "active_frontend_code_changed_scope": "ui/institutional_shell",
        "backend_server_required": False,
        "frontend_dependencies_added": False,
        "credential_read_allowed_now": False,
        "platform_api_allowed_now": False,
        "provider_llm_api_allowed_now": False,
        "repo_web_search_allowed_now": False,
        "live_posting_enabled_now": False,
        "scheduler_allowed_now": False,
        "scraping_allowed_now": False,
        "evidence_mutation_enabled_now": False,
        "project_sources_refresh_created_now": False,
        "browser_qa_evidence_packet": _build_browser_qa_evidence_packet(),
        "browser_qa_screen_results": _build_screen_results(),
        "minor_evidence_gap_registry": [
            "browser QA packet omitted repo path/branch/HEAD/git status/terminal validation fields",
            "packet did not explicitly state Antigravity used yes/no",
            "attached visual evidence did not clearly show Settings / Safety Policy selected though packet reported it inspected",
            "worker reported screenshots captured=no while operator/browser feedback images were later available in chat; no screenshot/export files were generated by repo/worker",
        ],
        "screenshot_review_caveat": {
            "visual_review_found_stale_global_header_metadata": True,
            "stale_accepted_head_example": STALE_HEAD,
            "stale_current_gate_example": STALE_GATE,
            "accepted_code_baseline_after_0168": LATEST_ACCEPTED_CODE_BASELINE,
            "is_live_or_safety_failure": False,
            "is_operator_confusing_consistency_issue": True,
            "reconciled_by_this_task": True,
        },
        "global_header_metadata_reconciliation": {
            "latest_accepted_code_baseline_before_0170": LATEST_ACCEPTED_CODE_BASELINE,
            "latest_browser_qa_evidence": "0169 PASS_WITH_MINOR_EVIDENCE_GAP",
            "stale_15b87ff_presented_as_current_global_baseline": False,
            "stale_telegram_docs_gate_presented_as_current_gate": False,
            "current_gate_label": "0170 browser qa evidence + metadata reconciliation",
            "live_posting_enabled": False,
            "platform_api_enabled": False,
            "scheduler_enabled": False,
            "kill_switch_status": "active",
        },
        "historical_screen_metadata_policy": {
            "present": True,
            "policy": (
                "Older per-screen HEADs (e.g. command_center 1c03ca0, 0159 timeline "
                "entry 15b87ff) are historical per-screen implementation provenance, "
                "not the current global repo baseline."
            ),
            "old_per_screen_heads_classified_historical": True,
        },
        "visual_export_antigravity_wording_policy": {
            "present": True,
            "browser_qa_evidence_pass_occurred": True,
            "future_browser_qa_self_authorized": False,
            "future_browser_antigravity_requires_explicit_go": True,
            "live_api_post_export_behavior_disabled": True,
        },
        "long_label_readability_policy": {
            "present": True,
            "issue": "Long next-action labels could wrap awkwardly (e.g. BEFOR E_ANY_NEXT_TASK).",
            "fix": "Human-readable display label with spaces plus a machine-readable *_code field preserving the full ID.",
        },
        "evidence_vault_update": {
            "includes_0169_browser_qa_evidence": True,
            "classification_0169": "PASS_WITH_MINOR_EVIDENCE_GAP",
            "metadata_reconciliation_0170_current_gate": True,
            "evidence_mutation": False,
            "project_sources_refresh_yet": False,
        },
        "readme_update": {
            "present": True,
            "documents_0169_browser_qa_pass_with_minor_gap": True,
            "documents_global_header_metadata_semantics": True,
            "project_sources_refresh_only_after_0170_audit": True,
        },
        "blocked_reasons": [],
        "packet_status": "pass",
        "kill_switch_status": "active",
    }



_BOOL_FALSE = [
    "runtime_authority", "browser_rerun_now", "antigravity_used_now",
    "screenshot_capture_enabled_now", "file_export_enabled_now",
    "platform_upload_enabled_now", "backend_server_required",
    "frontend_dependencies_added", "credential_read_allowed_now",
    "platform_api_allowed_now", "provider_llm_api_allowed_now",
    "repo_web_search_allowed_now", "live_posting_enabled_now",
    "scheduler_allowed_now", "scraping_allowed_now",
    "evidence_mutation_enabled_now", "project_sources_refresh_created_now",
]

_REQUIRED_BQA_FIELDS = [
    "task_label", "audit_classification", "browser_opened", "local_file_url_opened",
    "local_file_url", "external_url_opened", "network_used_observed",
    "screenshots_captured", "screenshots_captured_clarification",
    "files_created_or_changed_by_browser_qa", "all_12_screens_reached",
    "secret_raw_data_visible", "active_forbidden_controls_visible",
    "active_publish_schedule_export_api_evidence_mutation_control_count",
    "exact_next_task_after_audit",
]


def validate_packet(packet):
    errors = []
    if packet.get("runtime_authority") is True:
        errors.append("runtime_authority_must_be_false")
    if packet.get("static_local_only") is not True:
        errors.append("static_local_only_must_be_true")
    if packet.get("fixture_or_mock_data_only") is not True:
        errors.append("fixture_or_mock_data_only_must_be_true")
    for f in _BOOL_FALSE:
        if packet.get(f) is True:
            errors.append(f"{f}_must_be_false")

    bqa = packet.get("browser_qa_evidence_packet", {})
    if bqa.get("audit_classification") != "PASS_WITH_MINOR_EVIDENCE_GAP":
        errors.append("0169_must_be_pass_with_minor_evidence_gap")
    for f in _REQUIRED_BQA_FIELDS:
        if f not in bqa:
            errors.append(f"browser_qa_packet_missing:{f}")

    results = packet.get("browser_qa_screen_results", [])
    ids = {r.get("screen_id") for r in results}
    for s in REQUIRED_SCREENS:
        if s not in ids:
            errors.append(f"screen_results_missing:{s}")

    gaps = " ".join(packet.get("minor_evidence_gap_registry", [])).lower()
    if "head" not in gaps or "git status" not in gaps:
        errors.append("minor_gap_missing_repo_head_git_field")
    if "antigravity" not in gaps:
        errors.append("minor_gap_missing_antigravity_field")

    cav = packet.get("screenshot_review_caveat", {})
    if cav.get("stale_accepted_head_example") != STALE_HEAD:
        errors.append("caveat_missing_stale_head_example")
    if cav.get("stale_current_gate_example") != STALE_GATE:
        errors.append("caveat_missing_stale_gate_example")

    rec = packet.get("global_header_metadata_reconciliation", {})
    if rec.get("stale_15b87ff_presented_as_current_global_baseline") is not False:
        errors.append("stale_head_still_current_global_baseline")
    if rec.get("stale_telegram_docs_gate_presented_as_current_gate") is not False:
        errors.append("stale_telegram_gate_still_current")
    if rec.get("latest_accepted_code_baseline_before_0170") != LATEST_ACCEPTED_CODE_BASELINE:
        errors.append("latest_accepted_code_baseline_not_444ef2c")

    if not packet.get("historical_screen_metadata_policy", {}).get("present"):
        errors.append("historical_screen_metadata_policy_missing")

    wording = packet.get("visual_export_antigravity_wording_policy", {})
    if wording.get("future_browser_qa_self_authorized") is True:
        errors.append("visual_export_wording_self_authorizes_browser_qa")

    if not packet.get("evidence_vault_update", {}).get("includes_0169_browser_qa_evidence"):
        errors.append("evidence_vault_update_missing_0169")

    if not packet.get("long_label_readability_policy", {}).get("present"):
        errors.append("long_label_readability_policy_missing")

    if not packet.get("readme_update", {}).get("present"):
        errors.append("readme_update_missing")

    if packet.get("packet_status") == "pass" and errors:
        errors.append("packet_status_pass_but_errors_exist")

    return {"valid": not errors, "errors": errors}



def build_summary():
    packet = build_packet()
    res = validate_packet(packet)
    bqa = packet["browser_qa_evidence_packet"]
    rec = packet["global_header_metadata_reconciliation"]
    reached = sum(1 for r in packet["browser_qa_screen_results"] if r.get("reached") == "yes")
    return {
        "packet_status": packet["packet_status"] if res["valid"] else "blocked",
        "validation_valid": res["valid"],
        "reconciliation_mode": packet["reconciliation_mode"],
        "static_local_only": packet["static_local_only"],
        "browser_rerun_now": packet["browser_rerun_now"],
        "antigravity_used_now": packet["antigravity_used_now"],
        "screenshot_capture_enabled_now": packet["screenshot_capture_enabled_now"],
        "file_export_enabled_now": packet["file_export_enabled_now"],
        "platform_upload_enabled_now": packet["platform_upload_enabled_now"],
        "browser_qa_classification": bqa["audit_classification"],
        "browser_qa_screen_count": len(packet["browser_qa_screen_results"]),
        "browser_qa_reached_screen_count": reached,
        "browser_qa_secret_visible_count": 0,
        "browser_qa_active_forbidden_control_count": 0,
        "minor_evidence_gap_count": len(packet["minor_evidence_gap_registry"]),
        "screenshot_review_caveat_present": True,
        "stale_global_header_issue_recorded": packet["screenshot_review_caveat"]["visual_review_found_stale_global_header_metadata"],
        "global_header_current_baseline_reconciled": rec["latest_accepted_code_baseline_before_0170"] == LATEST_ACCEPTED_CODE_BASELINE,
        "historical_screen_metadata_policy_present": packet["historical_screen_metadata_policy"]["present"],
        "visual_export_antigravity_wording_policy_present": packet["visual_export_antigravity_wording_policy"]["present"],
        "long_label_readability_policy_present": packet["long_label_readability_policy"]["present"],
        "evidence_vault_0169_entry_present": packet["evidence_vault_update"]["includes_0169_browser_qa_evidence"],
        "readme_update_present": packet["readme_update"]["present"],
        "project_sources_refresh_created_now": packet["project_sources_refresh_created_now"],
        "backend_server_required": packet["backend_server_required"],
        "frontend_dependencies_added": packet["frontend_dependencies_added"],
        "credential_read_allowed_now": packet["credential_read_allowed_now"],
        "platform_api_allowed_now": packet["platform_api_allowed_now"],
        "live_posting_enabled_now": packet["live_posting_enabled_now"],
        "scheduler_allowed_now": packet["scheduler_allowed_now"],
        "scraping_allowed_now": packet["scraping_allowed_now"],
        "evidence_mutation_enabled_now": packet["evidence_mutation_enabled_now"],
        "active_frontend_code_changed_scope": packet["active_frontend_code_changed_scope"],
        "kill_switch_status": packet["kill_switch_status"],
        "blocked_reasons": res["errors"],
    }

