"""Institutional design system packet (0158).

Planning-only. Deterministic, fail-closed validator and redacted summary for the
institutional design system / futuristic fintech visual contract. No network, no
credentials, no env reads, no live capability. Mirrors the repo's packet/
validator/summary convention.
"""
import json
import os
import datetime
import jsonschema

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
SCHEMAS_DIR = os.path.join(BASE_DIR, "schemas")

TASK_LABEL = "TASK_CONTENTOPS_0158_INSTITUTIONAL_DESIGN_SYSTEM_AND_FUTURISTIC_FINTECH_VISUAL_CONTRACT_V0"

DESIGN_SYSTEM_DOCS = [
    "docs/INSTITUTIONAL_DESIGN_SYSTEM_AND_FUTURISTIC_FINTECH_VISUAL_CONTRACT_AFTER_0158.md",
    "docs/INSTITUTIONAL_UI_COMPONENT_TAXONOMY_AFTER_0158.md",
    "docs/INSTITUTIONAL_STATUS_SEMANTICS_AND_SAFETY_BANNERS_AFTER_0158.md",
    "docs/INSTITUTIONAL_SCREENSHOT_SAFE_AND_REDACTED_VISUAL_EXPORT_RULES_AFTER_0158.md",
    "docs/INSTITUTIONAL_DESIGN_SYSTEM_HANDOFF_TO_VIEW_MODEL_AFTER_0158.md",
]

STATUS_TOKENS = [
    "PASS",
    "DEGRADED",
    "BLOCKED",
    "REVIEW_REQUIRED",
    "NOT_PUBLIC_POSTABLE",
    "LIVE_DISABLED",
    "UNKNOWN",
    "PROXY_ONLY",
    "STALE",
    "SECRET_REDACTED",
    "CREDENTIAL_PRESENT_REDACTED",
    "CREDENTIAL_VALIDATED_NO_POST",
    "API_VALIDATED_NO_POST",
    "CHANNEL_PERMISSION_UNVALIDATED",
    "DQR_BLOCKING",
    "FORECAST_NOT_READY",
    "MANUAL_ONLY",
    "DRY_RUN_ONLY",
    "KILL_SWITCH_ACTIVE",
]

COMPONENT_TAXONOMY = [
    "global_safety_ribbon",
    "command_center_status_header",
    "content_lane_badge",
    "forbidden_action_tooltip",
    "gate_card",
    "blocked_reason_stack",
    "publish_disabled_control",
    "not_public_postable_banner",
    "manual_review_required_banner",
    "kill_switch_indicator",
    "screenshot_safe_watermark",
    "evidence_link_card",
    "source_lineage_panel",
    "audit_timeline",
    "limitation_strip",
    "claim_risk_panel",
    "draft_inspector_panel",
    "approval_decision_card",
    "markdown_review_export_view",
    "platform_readiness_card",
    "content_lane_readiness_row",
    "telegram_gate_stepper",
    "credential_redaction_badge",
    "data_sufficiency_matrix",
    "forecast_readiness_card",
    "freshness_chip",
    "proxy_only_warning",
    "missing_data_row",
    "content_calendar_grid",
    "workflow_board_column",
    "visual_export_preview",
    "screenshot_safe_toggle",
    "safety_policy_panel",
    "posture_summary_row",
]

SAFETY_BANNERS = [
    "LOCAL_ONLY",
    "DRY_RUN_ONLY",
    "REVIEW_ONLY",
    "MANUAL_REVIEW_REQUIRED",
    "NOT_PUBLIC_POSTABLE",
    "LIVE_DISABLED",
    "API_VALIDATED_NO_POST",
    "CHANNEL_PERMISSION_UNVALIDATED",
    "KILL_SWITCH_ACTIVE",
    "SECRET_REDACTED",
    "NO_FINANCIAL_ADVICE",
    "NO_SIGNAL_LANGUAGE",
    "DQR_BLOCKING",
    "FORECAST_NOT_READY",
    "PROXY_ONLY",
    "MISSING_DATA_VISIBLE",
]

FORBIDDEN_VISUAL_METAPHORS = [
    "trade_buttons",
    "pnl_widgets",
    "buy_sell_chips",
    "bullish_bearish_arrows",
    "alpha_signal_badges",
    "rocket_moon_visuals",
    "casino_crypto_aesthetics",
    "execution_console",
    "broker_order_routing_icons",
]

SCREENSHOT_SAFE_RULES = [
    "no_secrets",
    "no_raw_env_path",
    "no_raw_vendor_data",
    "no_raw_platform_response",
    "no_raw_request_url",
    "no_public_ready_false_claims",
    "no_forecast_readiness_false_claims",
    "no_advice_or_signal_language",
    "watermark_required_when_safe_mode_active",
    "limitations_remain_visible",
]

REQUIRED_STATUS_TOKENS = list(STATUS_TOKENS)
REQUIRED_SAFETY_BANNERS = list(SAFETY_BANNERS)

FORBIDDEN_TRUE = [
    "runtime_authority",
    "active_frontend_code_changed",
    "frontend_dependencies_added",
    "backend_server_required",
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
    "planning_only",
    "handoff_to_view_model",
]


def _load_schema(name):
    with open(os.path.join(SCHEMAS_DIR, name), "r", encoding="utf-8") as f:
        return json.load(f)




def build_packet():
    """Build the planning-only design system packet. Fail-closed safety flags."""
    return {
        "packet_id": "institutional_design_system_0158",
        "created_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "task_label": TASK_LABEL,
        "design_system_mode": "planning_only",
        "runtime_authority": False,
        "planning_only": True,
        "active_frontend_code_changed": False,
        "frontend_dependencies_added": False,
        "backend_server_required": False,
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
        "secret_visible_count": 0,
        "status_tokens": list(STATUS_TOKENS),
        "component_taxonomy": list(COMPONENT_TAXONOMY),
        "safety_banners": list(SAFETY_BANNERS),
        "screenshot_safe_rules": list(SCREENSHOT_SAFE_RULES),
        "forbidden_visual_metaphors": list(FORBIDDEN_VISUAL_METAPHORS),
        "handoff_to_view_model": True,
        "design_system_docs": list(DESIGN_SYSTEM_DOCS),
        "kill_switch_status": "active",
        "blocked_reasons": [],
        "packet_status": "pass",
    }


def _doc_exists(rel_path):
    return os.path.isfile(os.path.join(BASE_DIR, rel_path))



def validate_packet(packet):
    """Deterministic fail-closed validation."""
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
    if packet.get("design_system_mode") != "planning_only":
        errors.append("design_system_mode_must_be_planning_only")
    if packet.get("secret_visible_count") != 0:
        errors.append("secret_visible_count_must_be_zero")

    for tok in REQUIRED_STATUS_TOKENS:
        if tok not in packet.get("status_tokens", []):
            errors.append(f"status_token_{tok}_missing")

    for banner in REQUIRED_SAFETY_BANNERS:
        if banner not in packet.get("safety_banners", []):
            errors.append(f"safety_banner_{banner}_missing")

    for metaphor in FORBIDDEN_VISUAL_METAPHORS:
        if metaphor not in packet.get("forbidden_visual_metaphors", []):
            errors.append(f"forbidden_visual_metaphor_{metaphor}_missing")

    required_components = [
        "global_safety_ribbon",
        "gate_card",
        "evidence_link_card",
        "credential_redaction_badge",
        "telegram_gate_stepper",
        "not_public_postable_banner",
        "kill_switch_indicator",
    ]
    for comp in required_components:
        if comp not in packet.get("component_taxonomy", []):
            errors.append(f"component_{comp}_missing")

    if not packet.get("screenshot_safe_rules"):
        errors.append("screenshot_safe_rules_missing")
    else:
        for rule in ("no_secrets", "no_raw_env_path", "no_public_ready_false_claims"):
            if rule not in packet.get("screenshot_safe_rules", []):
                errors.append(f"screenshot_safe_rule_{rule}_missing")

    for rel in packet.get("design_system_docs", []):
        if not _doc_exists(rel):
            errors.append(f"design_system_doc_not_found:{rel}")
    if len(packet.get("design_system_docs", [])) < 5:
        errors.append("design_system_docs_incomplete")

    status = packet.get("packet_status")
    if status == "pass" and errors:
        errors.append("packet_status_pass_but_errors_exist")

    return {"valid": len(errors) == 0, "errors": errors}


def summary():
    """Return a JSON-serializable redacted design-system summary."""
    packet = build_packet()
    res = validate_packet(packet)
    return {
        "packet_status": packet.get("packet_status") if res["valid"] else "blocked",
        "validation_valid": res["valid"],
        "design_system_mode": packet.get("design_system_mode"),
        "status_token_count": len(packet.get("status_tokens", [])),
        "component_count": len(packet.get("component_taxonomy", [])),
        "safety_banner_count": len(packet.get("safety_banners", [])),
        "forbidden_visual_metaphor_count": len(packet.get("forbidden_visual_metaphors", [])),
        "screenshot_safe_rules_present": bool(packet.get("screenshot_safe_rules")),
        "handoff_to_view_model_present": packet.get("handoff_to_view_model"),
        "active_frontend_code_changed": packet.get("active_frontend_code_changed"),
        "frontend_dependencies_added": packet.get("frontend_dependencies_added"),
        "backend_server_required": packet.get("backend_server_required"),
        "browser_automation_used_now": packet.get("browser_automation_used_now"),
        "antigravity_used_now": packet.get("antigravity_used_now"),
        "credential_read_allowed_now": packet.get("credential_read_allowed_now"),
        "platform_api_allowed_now": packet.get("platform_api_allowed_now"),
        "live_posting_enabled_now": packet.get("live_posting_enabled_now"),
        "scheduler_allowed_now": packet.get("scheduler_allowed_now"),
        "scraping_allowed_now": packet.get("scraping_allowed_now"),
        "public_ready_final_copy_generated": packet.get("public_ready_final_copy_generated"),
        "red_green_market_direction_semantics": packet.get("red_green_market_direction_semantics"),
        "secret_visible_count": packet.get("secret_visible_count"),
        "unsafe_signal_language_enabled": packet.get("unsafe_signal_language_enabled"),
        "design_system_doc_count": len(packet.get("design_system_docs", [])),
        "kill_switch_status": packet.get("kill_switch_status"),
        "blocked_reasons": res["errors"],
    }

PACKET_SCHEMA = _load_schema("institutional_design_system_packet.schema.json")
