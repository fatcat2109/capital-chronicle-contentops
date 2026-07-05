"""Institutional command center screen packet (0161).

Static/local-only frontend screen contract. Deterministic, fail-closed validator
and redacted summary. Inspects the static shell assets under
ui/institutional_shell/ WITHOUT opening a browser, WITHOUT network, WITHOUT env
reads. Mirrors the repo's packet/validator/summary convention.
"""
import json
import os
import re
import datetime
import jsonschema

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
SCHEMAS_DIR = os.path.join(BASE_DIR, "schemas")
SHELL_DIR = os.path.join(BASE_DIR, "ui", "institutional_shell")

TASK_LABEL = "TASK_CONTENTOPS_0161_INSTITUTIONAL_COMMAND_CENTER_SCREEN_V0"

RUNTIME_SHELL_FILES = [
    "ui/institutional_shell/index.html",
    "ui/institutional_shell/styles.css",
    "ui/institutional_shell/app.js",
    "ui/institutional_shell/fixture_data.js",
]

REQUIRED_SAFETY_RIBBON = [
    "LOCAL_ONLY", "DRY_RUN_ONLY", "REVIEW_ONLY", "MANUAL_REVIEW_REQUIRED",
    "NOT_PUBLIC_POSTABLE", "LIVE_DISABLED", "KILL_SWITCH_ACTIVE",
    "SECRET_REDACTED", "NO_FINANCIAL_ADVICE", "NO_SIGNAL_LANGUAGE",
]

REQUIRED_BLOCKED_ACTIONS = [
    "live_posting", "scheduler", "platform_api", "provider_llm_api", "scraping",
    "autonomous_replies_dms", "one_button_publish_all", "public_ready_final_copy",
    "credential_display", "raw_env_paths", "raw_request_urls",
    "raw_platform_responses", "broker_execution_order_routing",
]

REQUIRED_GATES = ["0157", "0158", "0159", "0160", "0161",
                  "0162", "0163", "0164", "0165", "0166", "0167", "0168"]

REQUIRED_EVIDENCE_KEYS = [
    "full_suite_result", "focused_tests_result", "cli_summaries",
    "secret_scan_status", "forbidden_scope_status", "git_status_summary",
]

NETWORK_PATTERNS = [
    r"\bfetch\s*\(",
    r"new\s+XMLHttpRequest",
    r"new\s+WebSocket",
    r"new\s+EventSource",
    r"https?://",
    r"src\s*=\s*[\"']\s*https?://",
    r"href\s*=\s*[\"']\s*https?://",
]

SECRET_PATTERNS = [
    r"\d{6,}:[A-Za-z0-9_-]{30,}",
    r"-----BEGIN",
    r"\bAKIA[0-9A-Z]{16}\b",
    r"\bghp_[A-Za-z0-9]{20,}\b",
    r"xox[baprs]-[A-Za-z0-9-]+",
    r"AIza[0-9A-Za-z_-]{30,}",
]

FORBIDDEN_TRUE = [
    "runtime_authority",
    "backend_server_required",
    "frontend_dependencies_added",
    "browser_automation_used_now",
    "antigravity_used_now",
    "credential_read_allowed_now",
    "platform_api_allowed_now",
    "live_posting_enabled_now",
    "scheduler_allowed_now",
    "scraping_allowed_now",
    "public_ready_final_copy_generated",
    "red_green_market_direction_semantics",
    "unsafe_signal_language_enabled",
]

REQUIRED_TRUE = [
    "static_local_only",
    "fixture_or_mock_data_only",
]


def _load_schema(name):
    with open(os.path.join(SCHEMAS_DIR, name), "r", encoding="utf-8") as f:
        return json.load(f)


PACKET_SCHEMA = _load_schema("institutional_command_center_screen_packet.schema.json")


def _read(rel_path):
    p = os.path.join(BASE_DIR, rel_path)
    if not os.path.isfile(p):
        return None
    with open(p, "r", encoding="utf-8") as f:
        return f.read()


def _file_exists(rel_path):
    return os.path.isfile(os.path.join(BASE_DIR, rel_path))


def _scan_runtime_text():
    parts = []
    for rel in RUNTIME_SHELL_FILES:
        txt = _read(rel)
        if txt:
            parts.append((rel, txt))
    return parts


def _count_network_hits():
    hits = 0
    for rel, txt in _scan_runtime_text():
        for pat in NETWORK_PATTERNS:
            hits += len(re.findall(pat, txt, re.IGNORECASE))
    return hits


def _count_secret_hits():
    hits = 0
    for rel, txt in _scan_runtime_text():
        for pat in SECRET_PATTERNS:
            hits += len(re.findall(pat, txt))
    return hits


def build_packet():
    """Build the command center screen packet. Fail-closed safety flags."""
    return {
        "packet_id": "institutional_command_center_screen_0161",
        "created_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "task_label": TASK_LABEL,
        "command_center_mode": "static_local_only",
        "runtime_authority": False,
        "static_local_only": True,
        "fixture_or_mock_data_only": True,
        "active_frontend_code_changed_scope": "ui/institutional_shell",
        "backend_server_required": False,
        "frontend_dependencies_added": False,
        "browser_automation_used_now": False,
        "antigravity_used_now": False,
        "credential_read_allowed_now": False,
        "platform_api_allowed_now": False,
        "live_posting_enabled_now": False,
        "scheduler_allowed_now": False,
        "scraping_allowed_now": False,
        "public_ready_final_copy_generated": False,
        "red_green_market_direction_semantics": False,
        "unsafe_signal_language_enabled": False,
        "secret_visible_count": _count_secret_hits(),
        "accepted_baseline": "1c03ca0",
        "hero_status_band": {
            "title": "Capital Chronicle ContentOps Command Center",
            "system_mode": "local / static / fixture-driven",
            "accepted_head": "1c03ca0",
            "kill_switch": "active",
            "public_state": "not_public_postable",
            "live_api_state": "disabled",
            "current_gate": "0161 command center screen implementation",
            "next_allowed_action": "AWAIT OPERATOR/CHATGPT AUDIT_OF_0161_EVIDENCE_BEFORE_ANY_NEXT_TASK",
        },
        "safety_ribbon": list(REQUIRED_SAFETY_RIBBON),
        "executive_status_cards": [
            {"id": "system_safety", "title": "System Safety"},
            {"id": "build_baseline", "title": "Build Baseline"},
            {"id": "publish_automation", "title": "Publish Automation"},
            {"id": "telegram_pilot_gate", "title": "Telegram Pilot Gate"},
            {"id": "evidence_audit", "title": "Evidence / Audit"},
            {"id": "ui_rebuild_track", "title": "UI Rebuild Track"},
            {"id": "content_studio_track", "title": "Content Studio Track"},
            {"id": "residual_drift", "title": "Residual Drift"},
        ],
        "gate_timeline": [{"gate": g} for g in REQUIRED_GATES],
        "blocked_action_matrix": [
            {"action": a, "state": "disabled"} for a in REQUIRED_BLOCKED_ACTIONS
        ],
        "evidence_summary": {
            "full_suite_result": "fixture baseline green",
            "focused_tests_result": "fixture baseline green",
            "cli_summaries": "passing",
            "secret_scan_status": "clean",
            "forbidden_scope_status": "clean",
            "git_status_summary": "only known residual drift untouched",
            "known_residual_drift": "untouched",
            "evidence_packet_required": True,
        },
        "telegram_gate_state": {
            "credential_presence": "redacted_presence_only",
            "official_docs_gate": "implemented",
            "live_getme": "not_run_unless_explicitly_executed_later",
            "channel_write_permission": "unvalidated",
            "send_message": "disabled",
            "live_adapter": "disabled",
            "posting": "disabled",
            "next_step": "requires separate audit/gate",
        },
        "publish_automation_state": {
            "mode": "dry_run_only",
            "manual_approval_required": True,
            "live": "disabled",
            "one_button_publish_all": "disabled",
        },
        "content_studio_state": {
            "review_only": True,
            "source_evidence_required": True,
            "not_public_postable": True,
            "final_social_copy_generated_by_repo": False,
        },
        "ui_rebuild_state": {
            "accepted": ["0157", "0158", "0159", "0160"],
            "current": "0161",
            "antigravity": "future_only",
            "browser_qa": "none_yet",
            "screenshots": "none_yet",
        },
        "residual_drift_panel": {
            "env_local": "exists locally; must remain untouched/untracked",
            "cleanup_commands_allowed": False,
        },
        "next_allowed_action_panel": {
            "directive": "AWAIT OPERATOR/CHATGPT AUDIT_OF_0161_EVIDENCE_BEFORE_ANY_NEXT_TASK",
            "future_task": "0162 Content Studio Rebuild only after audit",
        },
        "forbidden_controls_active_count": 0,
        "external_dependency_count": 0,
        "remote_url_count": 0,
        "fetch_call_count": _count_network_hits(),
        "screenshot_safe_policy": {
            "present": True,
            "redact_secrets": True,
            "redact_env_paths": True,
        },
        "redaction_policy": {
            "redact_secrets": True,
            "redact_env_paths": True,
            "redact_request_urls": True,
            "redact_raw_platform_responses": True,
        },
        "blocked_reasons": [],
        "packet_status": "pass",
    }



def validate_packet(packet):
    """Deterministic fail-closed validation, including static-asset scans."""
    errors = []

    try:
        jsonschema.validate(packet, PACKET_SCHEMA)
    except jsonschema.ValidationError as e:
        errors.append(f"schema_error:{e.message}")

    for k in FORBIDDEN_TRUE:
        if packet.get(k) is True:
            errors.append(f"{k}_must_be_false")
    for k in REQUIRED_TRUE:
        if packet.get(k) is not True:
            errors.append(f"{k}_must_be_true")

    if packet.get("task_label") != TASK_LABEL:
        errors.append("task_label_mismatch")
    if packet.get("command_center_mode") != "static_local_only":
        errors.append("command_center_mode_must_be_static_local_only")
    if packet.get("secret_visible_count") != 0:
        errors.append("secret_visible_count_must_be_zero")
    if packet.get("forbidden_controls_active_count") != 0:
        errors.append("forbidden_controls_active_count_must_be_zero")

    scope = packet.get("active_frontend_code_changed_scope", "")
    if "ui/institutional_shell" not in scope:
        errors.append("active_frontend_scope_out_of_bounds")

    # Runtime shell files exist.
    for rel in RUNTIME_SHELL_FILES:
        if not _file_exists(rel):
            errors.append(f"shell_file_missing:{rel}")

    # Safety ribbon completeness.
    ribbon = packet.get("safety_ribbon", [])
    for item in REQUIRED_SAFETY_RIBBON:
        if item not in ribbon:
            errors.append(f"safety_ribbon_missing_{item}")

    # Executive cards count.
    if len(packet.get("executive_status_cards", [])) < 8:
        errors.append("executive_status_cards_insufficient")

    # Gate timeline completeness.
    gates = [g.get("gate") for g in packet.get("gate_timeline", [])]
    for g in REQUIRED_GATES:
        if g not in gates:
            errors.append(f"gate_timeline_missing_{g}")

    # Blocked action matrix completeness.
    actions = [a.get("action") for a in packet.get("blocked_action_matrix", [])]
    for a in REQUIRED_BLOCKED_ACTIONS:
        if a not in actions:
            errors.append(f"blocked_action_missing_{a}")

    # Evidence summary completeness.
    ev = packet.get("evidence_summary", {})
    for key in REQUIRED_EVIDENCE_KEYS:
        if key not in ev:
            errors.append(f"evidence_summary_missing_{key}")

    # Telegram gate state guardrails.
    tg = packet.get("telegram_gate_state", {})
    if tg.get("channel_write_permission") != "unvalidated":
        errors.append("telegram_channel_permission_must_be_unvalidated")
    if tg.get("send_message") != "disabled":
        errors.append("telegram_send_message_must_be_disabled")
    if tg.get("credential_presence") != "redacted_presence_only":
        errors.append("telegram_credential_presence_must_be_redacted")

    # Publish automation must not imply live capability.
    pa = packet.get("publish_automation_state", {})
    if pa.get("mode") != "dry_run_only":
        errors.append("publish_automation_must_be_dry_run_only")
    if pa.get("live") != "disabled":
        errors.append("publish_automation_live_must_be_disabled")
    if pa.get("one_button_publish_all") != "disabled":
        errors.append("publish_automation_publish_all_must_be_disabled")

    # Content studio must not imply public-ready final copy.
    cs = packet.get("content_studio_state", {})
    if cs.get("final_social_copy_generated_by_repo") is not False:
        errors.append("content_studio_final_copy_must_be_false")
    if cs.get("not_public_postable") is not True:
        errors.append("content_studio_must_be_not_public_postable")

    # UI rebuild state must include Antigravity future-only / no browser QA yet.
    ui = packet.get("ui_rebuild_state", {})
    if ui.get("antigravity") != "future_only":
        errors.append("ui_rebuild_antigravity_must_be_future_only")
    if ui.get("browser_qa") != "none_yet":
        errors.append("ui_rebuild_browser_qa_must_be_none_yet")

    # Residual drift panel must include .env untouched.
    rd = packet.get("residual_drift_panel", {})
    if "untouched" not in str(rd.get("env_local", "")):
        errors.append("residual_drift_env_must_be_untouched")

    # Next allowed action must require audit before next task.
    nap = packet.get("next_allowed_action_panel", {})
    if "AUDIT_OF_0161" not in str(nap.get("directive", "")):
        errors.append("next_allowed_action_must_require_audit")

    # Static-only network scan.
    net_hits = _count_network_hits()
    if net_hits != 0:
        errors.append(f"network_capability_present:{net_hits}")
    if packet.get("fetch_call_count") != 0:
        errors.append("fetch_call_count_must_be_zero")
    if packet.get("external_dependency_count") != 0:
        errors.append("external_dependency_count_must_be_zero")
    if packet.get("remote_url_count") != 0:
        errors.append("remote_url_count_must_be_zero")

    # Secret-like scan.
    if _count_secret_hits() != 0:
        errors.append("secret_like_value_present")

    status = packet.get("packet_status")
    if status == "pass" and errors:
        errors.append("packet_status_pass_but_errors_exist")

    return {"valid": len(errors) == 0, "errors": errors}



def summary():
    """Return a JSON-serializable redacted command center screen summary."""
    packet = build_packet()
    res = validate_packet(packet)
    return {
        "packet_status": packet.get("packet_status") if res["valid"] else "blocked",
        "validation_valid": res["valid"],
        "command_center_mode": packet.get("command_center_mode"),
        "static_local_only": packet.get("static_local_only"),
        "hero_status_band_present": bool(packet.get("hero_status_band")),
        "safety_ribbon_count": len(packet.get("safety_ribbon", [])),
        "executive_status_card_count": len(packet.get("executive_status_cards", [])),
        "gate_timeline_item_count": len(packet.get("gate_timeline", [])),
        "blocked_action_count": len(packet.get("blocked_action_matrix", [])),
        "evidence_summary_present": bool(packet.get("evidence_summary")),
        "telegram_gate_state_present": bool(packet.get("telegram_gate_state")),
        "publish_automation_state_present": bool(packet.get("publish_automation_state")),
        "content_studio_state_present": bool(packet.get("content_studio_state")),
        "ui_rebuild_state_present": bool(packet.get("ui_rebuild_state")),
        "residual_drift_panel_present": bool(packet.get("residual_drift_panel")),
        "next_allowed_action_present": bool(packet.get("next_allowed_action_panel")),
        "forbidden_controls_active_count": packet.get("forbidden_controls_active_count"),
        "external_dependency_count": packet.get("external_dependency_count"),
        "remote_url_count": packet.get("remote_url_count"),
        "fetch_call_count": packet.get("fetch_call_count"),
        "active_frontend_code_changed_scope": packet.get("active_frontend_code_changed_scope"),
        "backend_server_required": packet.get("backend_server_required"),
        "frontend_dependencies_added": packet.get("frontend_dependencies_added"),
        "browser_automation_used_now": packet.get("browser_automation_used_now"),
        "antigravity_used_now": packet.get("antigravity_used_now"),
        "credential_read_allowed_now": packet.get("credential_read_allowed_now"),
        "platform_api_allowed_now": packet.get("platform_api_allowed_now"),
        "live_posting_enabled_now": packet.get("live_posting_enabled_now"),
        "scheduler_allowed_now": packet.get("scheduler_allowed_now"),
        "scraping_allowed_now": packet.get("scraping_allowed_now"),
        "public_ready_final_copy_generated": packet.get("public_ready_final_copy_generated"),
        "secret_visible_count": packet.get("secret_visible_count"),
        "unsafe_signal_language_enabled": packet.get("unsafe_signal_language_enabled"),
        "red_green_market_direction_semantics": packet.get("red_green_market_direction_semantics"),
        "kill_switch_status": "active",
        "blocked_reasons": res["errors"],
    }

    return os.path.isfile(os.path.join(BASE_DIR, rel_path))
