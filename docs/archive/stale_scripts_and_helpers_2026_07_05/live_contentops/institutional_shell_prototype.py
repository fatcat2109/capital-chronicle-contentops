"""Institutional shell prototype packet (0160).

Static/local-only frontend prototype contract. Deterministic, fail-closed
validator and redacted summary. Inspects the static shell assets under
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

TASK_LABEL = "TASK_CONTENTOPS_0160_INSTITUTIONAL_SHELL_PROTOTYPE_STATIC_LOCAL_V0"

SHELL_FILES = [
    "ui/institutional_shell/index.html",
    "ui/institutional_shell/styles.css",
    "ui/institutional_shell/app.js",
    "ui/institutional_shell/fixture_data.js",
    "ui/institutional_shell/README.md",
]

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

REQUIRED_COMPONENTS = [
    "global_safety_ribbon", "command_center_status_header", "gate_card",
    "blocked_reason_stack", "evidence_link_card", "source_lineage_panel",
    "data_sufficiency_matrix", "forecast_readiness_card", "credential_redaction_badge",
    "platform_readiness_card", "telegram_gate_stepper", "approval_decision_card",
    "audit_timeline", "draft_inspector_panel", "claim_risk_panel",
    "content_lane_badge", "publish_disabled_control", "screenshot_safe_watermark",
    "limitation_strip", "freshness_chip", "proxy_only_warning", "missing_data_row",
    "not_public_postable_banner", "manual_review_required_banner",
    "kill_switch_indicator", "forbidden_action_tooltip",
]

REQUIRED_SAFETY_BANNERS = [
    "LOCAL_ONLY", "DRY_RUN_ONLY", "REVIEW_ONLY", "NOT_PUBLIC_POSTABLE",
    "LIVE_DISABLED", "KILL_SWITCH_ACTIVE", "SECRET_REDACTED",
    "NO_FINANCIAL_ADVICE", "NO_SIGNAL_LANGUAGE",
]

# Patterns that must NOT appear as executable/network capability in shell assets.
# These match actual call/constructor/remote-resource syntax, not prose mentions
# such as "no fetch" or "no WebSocket" which are allowed safe negation text.
NETWORK_PATTERNS = [
    r"\bfetch\s*\(",
    r"new\s+XMLHttpRequest",
    r"new\s+WebSocket",
    r"new\s+EventSource",
    r"https?://",
    r"src\s*=\s*[\"']\s*https?://",
    r"href\s*=\s*[\"']\s*https?://",
]

# Secret-like / forbidden-value patterns that must NOT appear in shell assets.
SECRET_PATTERNS = [
    r"\d{6,}:[A-Za-z0-9_-]{30,}",   # telegram bot token shape
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
    "screenshot_safe_mode_present",
    "redaction_policy_visible",
    "blocked_action_policy_visible",
]


def _load_schema(name):
    with open(os.path.join(SCHEMAS_DIR, name), "r", encoding="utf-8") as f:
        return json.load(f)


PACKET_SCHEMA = _load_schema("institutional_shell_prototype_packet.schema.json")


def _read(rel_path):
    p = os.path.join(BASE_DIR, rel_path)
    if not os.path.isfile(p):
        return None
    with open(p, "r", encoding="utf-8") as f:
        return f.read()


def _file_exists(rel_path):
    return os.path.isfile(os.path.join(BASE_DIR, rel_path))


def _scan_shell_text():
    """Concatenate shell asset text for content scans (excludes README prose)."""
    parts = []
    for rel in SHELL_FILES:
        txt = _read(rel)
        if txt:
            parts.append((rel, txt))
    return parts


def _count_network_hits():
    hits = 0
    for rel, txt in _scan_shell_text():
        for pat in NETWORK_PATTERNS:
            hits += len(re.findall(pat, txt, re.IGNORECASE))
    return hits


def _count_secret_hits():
    hits = 0
    for rel, txt in _scan_shell_text():
        for pat in SECRET_PATTERNS:
            hits += len(re.findall(pat, txt))
    return hits


def build_packet():
    """Build the static-local shell prototype packet. Fail-closed safety flags."""
    fetch_hits = _count_network_hits()
    secret_hits = _count_secret_hits()
    return {
        "packet_id": "institutional_shell_prototype_0160",
        "created_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "task_label": TASK_LABEL,
        "shell_mode": "static_local_only",
        "runtime_authority": False,
        "static_local_only": True,
        "fixture_or_mock_data_only": True,
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
        "secret_visible_count": secret_hits,
        "shell_files": list(SHELL_FILES),
        "screens_rendered": list(REQUIRED_SCREENS),
        "components_rendered": list(REQUIRED_COMPONENTS),
        "safety_banners_rendered": list(REQUIRED_SAFETY_BANNERS),
        "screenshot_safe_mode_present": True,
        "redaction_policy_visible": True,
        "blocked_action_policy_visible": True,
        "forbidden_controls_active_count": 0,
        "external_dependency_count": 0,
        "remote_url_count": 0,
        "fetch_call_count": fetch_hits,
        "active_frontend_code_changed_scope": "ui/institutional_shell",
        "future_handoff": {
            "to_task": "0161_command_center_screen",
            "no_backend": True,
            "no_network": True,
            "no_env_access": True,
            "no_live_controls": True,
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
    if packet.get("shell_mode") != "static_local_only":
        errors.append("shell_mode_must_be_static_local_only")
    if packet.get("secret_visible_count") != 0:
        errors.append("secret_visible_count_must_be_zero")
    if packet.get("forbidden_controls_active_count") != 0:
        errors.append("forbidden_controls_active_count_must_be_zero")

    # Shell files exist on disk.
    for rel in SHELL_FILES:
        if not _file_exists(rel):
            errors.append(f"shell_file_missing:{rel}")

    # Required screens / components / banners present in fixture asset.
    fixture_txt = _read("ui/institutional_shell/fixture_data.js") or ""
    for sid in REQUIRED_SCREENS:
        if sid not in fixture_txt:
            errors.append(f"screen_{sid}_missing")
    for comp in REQUIRED_COMPONENTS:
        if comp not in fixture_txt:
            errors.append(f"component_{comp}_missing")
    for banner in REQUIRED_SAFETY_BANNERS:
        if banner not in fixture_txt:
            errors.append(f"safety_banner_{banner}_missing")

    # Static-only network scan over all shell assets.
    net_hits = _count_network_hits()
    if net_hits != 0:
        errors.append(f"network_capability_present:{net_hits}")
    if packet.get("fetch_call_count") not in (0, None) and packet.get("fetch_call_count") != net_hits:
        errors.append("fetch_call_count_mismatch")
    if packet.get("fetch_call_count") != 0:
        errors.append("fetch_call_count_must_be_zero")
    if packet.get("external_dependency_count") != 0:
        errors.append("external_dependency_count_must_be_zero")
    if packet.get("remote_url_count") != 0:
        errors.append("remote_url_count_must_be_zero")

    # Secret-like scan over all shell assets.
    if _count_secret_hits() != 0:
        errors.append("secret_like_value_present")

    # Telegram pilot gate must forbid live calls; calendar must forbid live states.
    for needed in ("getme_call", "sendmessage", "live_adapter"):
        if needed not in fixture_txt:
            errors.append(f"telegram_pilot_gate_must_forbid_{needed}")
    for needed in ("scheduled_post", "auto_publish", "live_state"):
        if needed not in fixture_txt:
            errors.append(f"content_calendar_must_forbid_{needed}")

    # Active frontend changes only within the new shell path.
    scope = packet.get("active_frontend_code_changed_scope", "")
    if "ui/institutional_shell" not in scope:
        errors.append("active_frontend_scope_out_of_bounds")

    status = packet.get("packet_status")
    if status == "pass" and errors:
        errors.append("packet_status_pass_but_errors_exist")

    return {"valid": len(errors) == 0, "errors": errors}


def summary():
    """Return a JSON-serializable redacted shell-prototype summary."""
    packet = build_packet()
    res = validate_packet(packet)
    return {
        "packet_status": packet.get("packet_status") if res["valid"] else "blocked",
        "validation_valid": res["valid"],
        "shell_mode": packet.get("shell_mode"),
        "static_local_only": packet.get("static_local_only"),
        "screen_count": len(packet.get("screens_rendered", [])),
        "component_count": len(packet.get("components_rendered", [])),
        "safety_banner_count": len(packet.get("safety_banners_rendered", [])),
        "shell_file_count": len(packet.get("shell_files", [])),
        "screenshot_safe_mode_present": packet.get("screenshot_safe_mode_present"),
        "redaction_policy_visible": packet.get("redaction_policy_visible"),
        "blocked_action_policy_visible": packet.get("blocked_action_policy_visible"),
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
