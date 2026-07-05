"""Institutional UI view-model contract V2 packet (0159).

Contract/spec only. Deterministic, fail-closed validator and redacted summary for
the institutional UI view-model contract V2. No network, no credentials, no env
reads, no live capability. Mirrors the repo's packet/validator/summary convention.
"""
import json
import os
import datetime
import jsonschema

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
SCHEMAS_DIR = os.path.join(BASE_DIR, "schemas")

TASK_LABEL = "TASK_CONTENTOPS_0159_INSTITUTIONAL_UI_VIEW_MODEL_CONTRACT_V2_V0"

CONTRACT_DOCS = [
    "docs/INSTITUTIONAL_UI_VIEW_MODEL_CONTRACT_V2_AFTER_0159.md",
    "docs/INSTITUTIONAL_UI_SCREEN_VIEW_MODELS_AFTER_0159.md",
    "docs/INSTITUTIONAL_UI_VIEW_MODEL_FIXTURE_AND_BINDING_STRATEGY_AFTER_0159.md",
    "docs/INSTITUTIONAL_UI_VIEW_MODEL_HANDOFF_TO_SHELL_PROTOTYPE_AFTER_0159.md",
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

REQUIRED_STATUS_TOKENS = [
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

REQUIRED_COMPONENTS = [
    "global_safety_ribbon",
    "command_center_status_header",
    "gate_card",
    "blocked_reason_stack",
    "evidence_link_card",
    "source_lineage_panel",
    "data_sufficiency_matrix",
    "forecast_readiness_card",
    "credential_redaction_badge",
    "platform_readiness_card",
    "telegram_gate_stepper",
    "approval_decision_card",
    "audit_timeline",
    "draft_inspector_panel",
    "claim_risk_panel",
    "content_lane_badge",
    "publish_disabled_control",
    "screenshot_safe_watermark",
    "limitation_strip",
    "freshness_chip",
    "proxy_only_warning",
    "missing_data_row",
    "not_public_postable_banner",
    "manual_review_required_banner",
    "kill_switch_indicator",
    "forbidden_action_tooltip",
]

REQUIRED_SAFETY_BANNERS = [
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
    "local_only",
    "fixture_or_mock_data_only",
]


def _load_schema(name):
    with open(os.path.join(SCHEMAS_DIR, name), "r", encoding="utf-8") as f:
        return json.load(f)




def _screen(screen_id, title, components, banners, tokens, evidence_refs,
            blocked_action_policy, redaction_requirements, forbidden_controls):
    return {
        "screen_id": screen_id,
        "title": title,
        "primary_components": components,
        "required_banners": banners,
        "required_status_tokens": tokens,
        "evidence_refs": evidence_refs,
        "blocked_reason_refs": [],
        "blocked_action_policy": blocked_action_policy,
        "redaction_requirements": redaction_requirements,
        "forbidden_controls": forbidden_controls,
        "empty_state": "unknown_with_reason",
        "screenshot_safe_behavior": "redacted_no_secrets_no_false_readiness",
        "fixture_id": f"vm_{screen_id}",
    }



def _build_screens():
    no_live = ["publish", "schedule", "connect", "oauth", "one_button_publish_all"]
    return [
        _screen("command_center", "Command Center",
                ["global_safety_ribbon", "command_center_status_header", "blocked_reason_stack", "kill_switch_indicator"],
                ["LOCAL_ONLY", "KILL_SWITCH_ACTIVE", "LIVE_DISABLED"],
                ["PASS", "DEGRADED", "BLOCKED", "KILL_SWITCH_ACTIVE"],
                ["evidence_vault_link"], "no_live_action", "no_secrets", no_live),
        _screen("content_lane_control", "Content Lane Control",
                ["content_lane_badge", "not_public_postable_banner", "blocked_reason_stack"],
                ["NOT_PUBLIC_POSTABLE", "REVIEW_ONLY"],
                ["NOT_PUBLIC_POSTABLE", "MANUAL_ONLY", "BLOCKED"],
                ["lane_policy_ref"], "no_lane_mixing", "no_secrets", no_live + ["lane_mix_enable"]),
        _screen("daily_content_studio", "Daily Content Studio",
                ["draft_inspector_panel", "limitation_strip", "not_public_postable_banner", "manual_review_required_banner"],
                ["NOT_PUBLIC_POSTABLE", "REVIEW_ONLY", "MANUAL_REVIEW_REQUIRED"],
                ["REVIEW_REQUIRED", "NOT_PUBLIC_POSTABLE", "DEGRADED"],
                ["source_lineage_ref"], "no_final_copy_generation", "no_secrets_no_final_copy", no_live + ["final_copy_generation"]),
        _screen("draft_inspector", "Draft Inspector",
                ["source_lineage_panel", "draft_inspector_panel", "claim_risk_panel", "limitation_strip"],
                ["NOT_PUBLIC_POSTABLE", "MANUAL_REVIEW_REQUIRED"],
                ["REVIEW_REQUIRED", "DEGRADED", "BLOCKED"],
                ["per_claim_source_ref"], "no_public_ready_state", "no_secrets", no_live + ["approve_public_ready"]),
        _screen("grounded_news_angle_lab", "Grounded News Angle Lab",
                ["evidence_link_card", "proxy_only_warning", "limitation_strip", "not_public_postable_banner"],
                ["PROXY_ONLY", "NOT_PUBLIC_POSTABLE", "NO_SIGNAL_LANGUAGE"],
                ["PROXY_ONLY", "REVIEW_REQUIRED", "DEGRADED"],
                ["angle_citation_ref"], "no_repo_web_search_call", "no_secrets", no_live + ["repo_web_search_call"]),
        _screen("publish_readiness_tower", "Publish Readiness Tower",
                ["platform_readiness_card", "gate_card", "credential_redaction_badge", "publish_disabled_control"],
                ["LIVE_DISABLED", "DRY_RUN_ONLY", "NOT_PUBLIC_POSTABLE", "SECRET_REDACTED"],
                ["LIVE_DISABLED", "DRY_RUN_ONLY", "BLOCKED", "SECRET_REDACTED"],
                ["readiness_evidence_ref"], "no_publish_all", "credentials_redacted_no_values", no_live),
        _screen("telegram_pilot_gate", "Telegram Pilot Gate",
                ["telegram_gate_stepper", "credential_redaction_badge", "gate_card", "publish_disabled_control"],
                ["SECRET_REDACTED", "LIVE_DISABLED", "API_VALIDATED_NO_POST", "CHANNEL_PERMISSION_UNVALIDATED"],
                ["CREDENTIAL_PRESENT_REDACTED", "API_VALIDATED_NO_POST", "CHANNEL_PERMISSION_UNVALIDATED", "LIVE_DISABLED"],
                ["gate_evidence_ref"], "no_getme_no_sendmessage_no_post", "token_chatid_never_shown",
                no_live + ["getme_call", "sendmessage", "live_adapter"]),
        _screen("approval_queue", "Approval Queue",
                ["approval_decision_card", "audit_timeline", "manual_review_required_banner"],
                ["MANUAL_REVIEW_REQUIRED", "REVIEW_ONLY"],
                ["REVIEW_REQUIRED", "MANUAL_ONLY", "PASS", "BLOCKED"],
                ["per_item_evidence_ref"], "no_auto_approval", "history_redacted_safe", no_live + ["auto_approval"]),
        _screen("content_calendar", "Content Calendar",
                ["content_lane_badge", "not_public_postable_banner", "manual_review_required_banner"],
                ["NOT_PUBLIC_POSTABLE", "REVIEW_ONLY", "MANUAL_REVIEW_REQUIRED"],
                ["NOT_PUBLIC_POSTABLE", "REVIEW_REQUIRED", "MANUAL_ONLY"],
                ["item_source_needed_ref"], "no_scheduled_or_live_state", "no_secrets",
                no_live + ["scheduled_post", "auto_publish", "live_state"]),
        _screen("evidence_vault", "Evidence Vault",
                ["evidence_link_card", "source_lineage_panel", "data_sufficiency_matrix", "freshness_chip", "missing_data_row", "audit_timeline"],
                ["PROXY_ONLY", "MISSING_DATA_VISIBLE", "DQR_BLOCKING"],
                ["PASS", "DEGRADED", "PROXY_ONLY", "STALE", "UNKNOWN", "DQR_BLOCKING"],
                ["artifact_evidence_ref"], "no_live_data_fetch", "no_raw_vendor_data_references_only", no_live + ["live_data_fetch"]),
        _screen("visual_export_studio", "Visual Export Studio",
                ["screenshot_safe_watermark", "screenshot_safe_toggle", "visual_export_preview"],
                ["SECRET_REDACTED", "NOT_PUBLIC_POSTABLE", "LIVE_DISABLED"],
                ["SECRET_REDACTED", "NOT_PUBLIC_POSTABLE", "LIVE_DISABLED"],
                ["report_card_evidence_ref"], "no_unredacted_capture", "redact_secrets_env_responses_urls",
                no_live + ["file_write", "network_export", "unredacted_capture"]),
        _screen("settings_safety_policy", "Settings / Safety Policy",
                ["safety_policy_panel", "posture_summary_row", "kill_switch_indicator"],
                ["LIVE_DISABLED", "KILL_SWITCH_ACTIVE", "DRY_RUN_ONLY"],
                ["LIVE_DISABLED", "KILL_SWITCH_ACTIVE", "DRY_RUN_ONLY"],
                [], "no_credential_display", "no_credentials_displayed",
                no_live + ["api_controls", "live_publishing_toggle", "credential_display"]),
    ]



def _build_status_token_registry():
    bands = {
        "PASS": "info", "DEGRADED": "caution", "BLOCKED": "blocking",
        "REVIEW_REQUIRED": "caution", "NOT_PUBLIC_POSTABLE": "locked",
        "LIVE_DISABLED": "locked", "UNKNOWN": "caution", "PROXY_ONLY": "caution",
        "STALE": "caution", "SECRET_REDACTED": "locked",
        "CREDENTIAL_PRESENT_REDACTED": "locked", "CREDENTIAL_VALIDATED_NO_POST": "locked",
        "API_VALIDATED_NO_POST": "locked", "CHANNEL_PERMISSION_UNVALIDATED": "caution",
        "DQR_BLOCKING": "blocking", "FORECAST_NOT_READY": "caution",
        "MANUAL_ONLY": "info", "DRY_RUN_ONLY": "locked", "KILL_SWITCH_ACTIVE": "blocking",
    }
    return [
        {
            "status_token_id": tok,
            "severity_band": bands[tok],
            "visual_role": "operational_status_only",
            "icon_role": "labeled_glyph",
            "forbidden_interpretation": "never_market_direction",
        }
        for tok in REQUIRED_STATUS_TOKENS
    ]


def _build_component_registry():
    return [
        {
            "component_id": comp,
            "design_system_component_ref": comp,
            "required_status_tokens": [],
            "redaction_fields": [],
            "empty_state": "unknown_with_reason",
            "screenshot_safe_state": "redacted",
            "test_contract": "renders_state_no_secrets_no_live",
        }
        for comp in REQUIRED_COMPONENTS
    ]



def build_packet():
    """Build the contract-only view-model packet. Fail-closed safety flags."""
    return {
        "packet_id": "institutional_ui_view_model_contract_v2_0159",
        "created_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "task_label": TASK_LABEL,
        "view_model_contract_version": "v2",
        "ui_contract_mode": "contract_only",
        "runtime_authority": False,
        "local_only": True,
        "fixture_or_mock_data_only": True,
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
        "linked_design_system_packet_id": "institutional_design_system_0158",
        "linked_ui_rebuild_plan_packet_id": "institutional_ui_ux_frontend_rebuild_plan_0157",
        "screens": _build_screens(),
        "global_state": {
            "repo_path_label": "cc-live-contentops",
            "branch_label": "master",
            "accepted_head_short": "1ae6e62",
            "system_mode": "local_pre_alpha",
            "kill_switch_status": "active",
            "live_posting_enabled_now": False,
            "platform_api_allowed_now": False,
            "credential_state_summary": "credentials_present_redacted_no_values",
            "current_gate": "telegram_official_docs_credential_validation_gate",
            "next_allowed_action": "await_operator_audit",
            "active_blockers": [],
            "known_residual_drift_count": 0,
            "not_public_postable_count": 12,
            "manual_review_required_count": 12,
        },
        "status_token_registry": _build_status_token_registry(),
        "component_registry": _build_component_registry(),
        "safety_banners": list(REQUIRED_SAFETY_BANNERS),
        "redaction_policy": {
            "redact_secrets": True,
            "redact_env_paths": True,
            "redact_raw_platform_responses": True,
            "redact_request_urls": True,
            "no_raw_vendor_data": True,
        },
        "evidence_ref_policy": {
            "references_only": True,
            "no_raw_vendor_payload": True,
        },
        "blocked_action_policy": {
            "fail_closed": True,
            "every_blocked_has_reason": True,
            "no_live_action": True,
        },
        "safety_policy": {
            "review_only_default": True,
            "not_public_postable_default": True,
            "live_disabled": True,
            "kill_switch_active": True,
        },
        "fixture_strategy": {
            "deterministic": True,
            "local_embeddable": True,
            "valid_fixture": "fixtures/institutional_ui_view_model_contract_v2_valid.json",
            "invalid_fixture": "fixtures/institutional_ui_view_model_contract_v2_invalid_live_enabled.json",
        },
        "future_handoff": {
            "to_task": "0160_institutional_shell_prototype",
            "no_backend": True,
            "no_network": True,
            "no_env_access": True,
            "no_live_controls": True,
        },
        "contract_docs": list(CONTRACT_DOCS),
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
    if packet.get("ui_contract_mode") != "contract_only":
        errors.append("ui_contract_mode_must_be_contract_only")
    if packet.get("view_model_contract_version") != "v2":
        errors.append("view_model_contract_version_must_be_v2")
    if packet.get("secret_visible_count") != 0:
        errors.append("secret_visible_count_must_be_zero")

    screens = packet.get("screens", [])
    screen_ids = [s.get("screen_id") for s in screens]
    for sid in REQUIRED_SCREENS:
        if sid not in screen_ids:
            errors.append(f"screen_{sid}_missing")

    tokens_present = {r.get("status_token_id") for r in packet.get("status_token_registry", [])}
    for tok in REQUIRED_STATUS_TOKENS:
        if tok not in tokens_present:
            errors.append(f"status_token_{tok}_missing")

    components_present = {c.get("component_id") for c in packet.get("component_registry", [])}
    for comp in REQUIRED_COMPONENTS:
        if comp not in components_present:
            errors.append(f"component_{comp}_missing")

    for banner in REQUIRED_SAFETY_BANNERS:
        if banner not in packet.get("safety_banners", []):
            errors.append(f"safety_banner_{banner}_missing")

    # Per-screen integrity: each screen needs >=1 banner and a blocked_action_policy.
    for s in screens:
        sid = s.get("screen_id")
        if not s.get("required_banners"):
            errors.append(f"screen_{sid}_missing_safety_banner")
        if not s.get("blocked_action_policy"):
            errors.append(f"screen_{sid}_missing_blocked_action_policy")
        if not s.get("redaction_requirements"):
            errors.append(f"screen_{sid}_missing_redaction_requirements")

    # Screen-specific guardrails.
    by_id = {s.get("screen_id"): s for s in screens}
    tg = by_id.get("telegram_pilot_gate")
    if tg and "CHANNEL_PERMISSION_UNVALIDATED" not in tg.get("required_status_tokens", []):
        errors.append("telegram_pilot_gate_missing_channel_permission_unvalidated")
    if tg:
        fc = tg.get("forbidden_controls", [])
        for needed in ("getme_call", "sendmessage", "live_adapter"):
            if needed not in fc:
                errors.append(f"telegram_pilot_gate_must_forbid_{needed}")

    prt = by_id.get("publish_readiness_tower")
    if prt and "one_button_publish_all" not in prt.get("forbidden_controls", []):
        errors.append("publish_readiness_tower_must_forbid_publish_all")

    cal = by_id.get("content_calendar")
    if cal:
        for needed in ("scheduled_post", "auto_publish", "live_state"):
            if needed not in cal.get("forbidden_controls", []):
                errors.append(f"content_calendar_must_forbid_{needed}")

    ves = by_id.get("visual_export_studio")
    if ves and "unredacted_capture" not in ves.get("forbidden_controls", []):
        errors.append("visual_export_studio_must_forbid_unredacted_capture")

    ssp = by_id.get("settings_safety_policy")
    if ssp and "credential_display" not in ssp.get("forbidden_controls", []):
        errors.append("settings_safety_policy_must_forbid_credential_display")

    # Global policies present.
    for policy_key in ("redaction_policy", "evidence_ref_policy", "blocked_action_policy", "safety_policy"):
        if not packet.get(policy_key):
            errors.append(f"{policy_key}_missing")

    rp = packet.get("redaction_policy", {})
    for needed in ("redact_secrets", "redact_env_paths", "redact_request_urls"):
        if rp.get(needed) is not True:
            errors.append(f"redaction_policy_{needed}_must_be_true")

    for rel in packet.get("contract_docs", []):
        if not _doc_exists(rel):
            errors.append(f"contract_doc_not_found:{rel}")
    if len(packet.get("contract_docs", [])) < 4:
        errors.append("contract_docs_incomplete")

    status = packet.get("packet_status")
    if status == "pass" and errors:
        errors.append("packet_status_pass_but_errors_exist")

    return {"valid": len(errors) == 0, "errors": errors}



def summary():
    """Return a JSON-serializable redacted view-model contract summary."""
    packet = build_packet()
    res = validate_packet(packet)
    screens = packet.get("screens", [])
    screen_ids = [s.get("screen_id") for s in screens]
    tokens_present = {r.get("status_token_id") for r in packet.get("status_token_registry", [])}
    components_present = {c.get("component_id") for c in packet.get("component_registry", [])}
    banners = packet.get("safety_banners", [])
    return {
        "packet_status": packet.get("packet_status") if res["valid"] else "blocked",
        "validation_valid": res["valid"],
        "ui_contract_mode": packet.get("ui_contract_mode"),
        "view_model_contract_version": packet.get("view_model_contract_version"),
        "screen_count": len(screens),
        "component_count": len(packet.get("component_registry", [])),
        "status_token_count": len(packet.get("status_token_registry", [])),
        "safety_banner_count": len(banners),
        "fixture_count": 2,
        "missing_required_screen_count": len([s for s in REQUIRED_SCREENS if s not in screen_ids]),
        "missing_required_component_count": len([c for c in REQUIRED_COMPONENTS if c not in components_present]),
        "missing_required_status_token_count": len([t for t in REQUIRED_STATUS_TOKENS if t not in tokens_present]),
        "missing_required_banner_count": len([b for b in REQUIRED_SAFETY_BANNERS if b not in banners]),
        "screenshot_safe_rules_present": bool(packet.get("redaction_policy")),
        "evidence_ref_policy_present": bool(packet.get("evidence_ref_policy")),
        "redaction_policy_present": bool(packet.get("redaction_policy")),
        "blocked_action_policy_present": bool(packet.get("blocked_action_policy")),
        "handoff_to_0160_present": bool(packet.get("future_handoff")),
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
        "secret_visible_count": packet.get("secret_visible_count"),
        "unsafe_signal_language_enabled": packet.get("unsafe_signal_language_enabled"),
        "red_green_market_direction_semantics": packet.get("red_green_market_direction_semantics"),
        "kill_switch_status": packet.get("kill_switch_status"),
        "blocked_reasons": res["errors"],
    }

PACKET_SCHEMA = _load_schema("institutional_ui_view_model_contract_v2_packet.schema.json")
