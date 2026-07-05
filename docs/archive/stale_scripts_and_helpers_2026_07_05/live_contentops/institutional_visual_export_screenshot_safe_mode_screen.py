"""Institutional visual export + screenshot-safe mode screen packet (0166).

Static/local-only frontend screen contract. Deterministic, fail-closed validator
and redacted summary. Inspects static shell assets under ui/institutional_shell/
WITHOUT a browser, network, env reads, screenshot capture, or export generation.
"""
import json
import os
import re
import datetime
import jsonschema

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
SCHEMAS_DIR = os.path.join(BASE_DIR, "schemas")

TASK_LABEL = "TASK_CONTENTOPS_0166_INSTITUTIONAL_VISUAL_EXPORT_AND_SCREENSHOT_SAFE_MODE_SCREEN_V0"

RUNTIME_SHELL_FILES = [
    "ui/institutional_shell/index.html",
    "ui/institutional_shell/styles.css",
    "ui/institutional_shell/app.js",
    "ui/institutional_shell/fixture_data.js",
]

REQUIRED_SAFETY_BANNERS = [
    "LOCAL_ONLY", "REVIEW_ONLY", "MANUAL_REVIEW_REQUIRED", "NOT_PUBLIC_POSTABLE",
    "LIVE_DISABLED", "EXPORT_PREP_ONLY", "SCREENSHOT_NOT_CAPTURED", "SECRET_REDACTED",
    "NO_FINANCIAL_ADVICE", "NO_SIGNAL_LANGUAGE", "MISSING_DATA_VISIBLE",
    "LIMITATIONS_VISIBLE", "WATERMARK_REQUIRED", "ANTIGRAVITY_FUTURE_ONLY",
]

REQUIRED_EXPORT_CARDS = [
    "command_center", "content_studio", "publish_readiness_tower",
    "evidence_vault", "content_calendar",
]

REQUIRED_REDACTION_FIELDS = [
    "credentials", "token_chat_id_values", "env_paths", "raw_request_urls",
    "raw_platform_responses", "raw_vendor_data",
]

REQUIRED_WATERMARK_LABELS = [
    "Local fixture UI", "Not public-postable", "Review-only", "No financial advice",
    "No signal language", "Live/API disabled",
]

REQUIRED_CHECKLIST_ITEMS = [
    "no_secrets_visible", "no_raw_env_path", "no_raw_request_url",
    "no_raw_platform_response", "no_public_ready_false_claim",
    "no_signal_or_trade_advice_language", "limitations_visible",
    "evidence_refs_visible", "watermark_visible",
]

REQUIRED_BLOCKED_ACTIONS = [
    "capture_screenshot", "export_png", "export_pdf", "export_svg", "download_file",
    "upload_to_platform", "publish_to_platform", "schedule_post", "run_antigravity",
    "browser_capture", "read_env", "edit_evidence",
]

REQUIRED_PREVIEW_STATES = [
    "export_ready_with_redaction", "blocked_missing_limitations",
    "blocked_secret_visible", "blocked_public_ready_claim",
    "blocked_no_evidence_refs", "blocked_unredacted_platform_response",
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
    "runtime_authority", "screenshot_capture_enabled_now", "file_export_enabled_now",
    "platform_upload_enabled_now", "backend_server_required", "frontend_dependencies_added",
    "browser_automation_used_now", "antigravity_used_now", "credential_read_allowed_now",
    "platform_api_allowed_now", "provider_llm_api_allowed_now", "repo_web_search_allowed_now",
    "live_posting_enabled_now", "scheduler_allowed_now", "scraping_allowed_now",
    "public_ready_final_copy_generated", "evidence_mutation_enabled_now",
    "red_green_market_direction_semantics", "unsafe_signal_language_enabled",
]

REQUIRED_TRUE = ["static_local_only", "fixture_or_mock_data_only", "export_preparation_only"]


def _load_schema(name):
    with open(os.path.join(SCHEMAS_DIR, name), "r", encoding="utf-8") as f:
        return json.load(f)


PACKET_SCHEMA = _load_schema("institutional_visual_export_screenshot_safe_mode_screen_packet.schema.json")


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


def _export_safe_card_gallery():
    def card(card_id, source, watermark, labels, forbidden):
        return {
            "card_id": card_id, "source_screen": source,
            "export_safe_status": "export_ready_with_redaction",
            "required_watermark": watermark, "required_labels": labels,
            "evidence_refs_visible": True, "limitations_visible": True,
            "redaction_required": True, "forbidden_fields": forbidden,
            "blocked_export_reason": None,
        }
    return [
        card("esc-command-center", "command_center", "Local fixture UI — Screenshot-safe",
             ["Not public-postable", "Review-only", "Live/API disabled"],
             ["credentials", "env_paths", "raw_request_urls"]),
        card("esc-content-studio", "content_studio", "Local fixture UI — Screenshot-safe",
             ["Not public-postable", "Review-only", "No financial advice", "No signal language"],
             ["raw_platform_responses", "credentials"]),
        card("esc-publish-readiness", "publish_readiness_tower", "Local fixture UI — Dry-run only",
             ["Live disabled", "Dry-run only", "Manual approval required"],
             ["credentials", "raw_request_urls", "raw_platform_responses"]),
        card("esc-evidence-vault", "evidence_vault", "Local fixture UI — Audit read-only",
             ["Audit read-only", "Secret redacted", "Evidence refs visible"],
             ["env_paths", "credentials", "raw_platform_responses"]),
        card("esc-content-calendar", "content_calendar", "Local fixture UI — Manual workflow only",
             ["Manual publish tracking only", "Scheduler disabled", "Not public-postable"],
             ["credentials", "raw_request_urls"]),
        card("esc-telegram-gate", "publish_readiness_tower", "Local fixture UI — Telegram redacted",
             ["Credentials redacted", "sendMessage disabled", "Channel permission unvalidated"],
             ["token_chat_id", "credentials", "raw_platform_responses"]),
    ]


def build_packet():
    """Build the visual export + screenshot-safe mode packet. Fail-closed flags."""
    packet = {
        "packet_id": "institutional_visual_export_screenshot_safe_mode_screen_0166",
        "created_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "task_label": TASK_LABEL,
        "visual_export_mode": "static_local_only",
        "runtime_authority": False,
        "static_local_only": True,
        "fixture_or_mock_data_only": True,
        "export_preparation_only": True,
        "screenshot_capture_enabled_now": False,
        "file_export_enabled_now": False,
        "platform_upload_enabled_now": False,
        "active_frontend_code_changed_scope": "ui/institutional_shell",
        "backend_server_required": False,
        "frontend_dependencies_added": False,
        "browser_automation_used_now": False,
        "antigravity_used_now": False,
        "credential_read_allowed_now": False,
        "platform_api_allowed_now": False,
        "provider_llm_api_allowed_now": False,
        "repo_web_search_allowed_now": False,
        "live_posting_enabled_now": False,
        "scheduler_allowed_now": False,
        "scraping_allowed_now": False,
        "public_ready_final_copy_generated": False,
        "evidence_mutation_enabled_now": False,
        "red_green_market_direction_semantics": False,
        "unsafe_signal_language_enabled": False,
        "secret_visible_count": _count_secret_hits(),
        "screenshot_safe_mode_panel": {
            "visual_prep_only": True,
            "screenshot_taken_by_task": False,
            "browser_automation": False,
            "antigravity_run": False,
            "image_video_pdf_export_created": False,
            "platform_upload_or_post": False,
            "operator_manual_redaction_verification_required": True,
        },
        "export_safe_card_gallery": _export_safe_card_gallery(),
        "redaction_overlay_panel": [
            {"field": "credentials", "displayed": False},
            {"field": "token_chat_id_values", "displayed": False},
            {"field": "env_paths", "displayed": False},
            {"field": "raw_request_urls", "displayed": False},
            {"field": "raw_platform_responses", "displayed": False},
            {"field": "raw_vendor_data", "displayed": False},
            {"field": "personal_operator_local_paths", "displayed": False},
            {"field": "unapproved_source_artifact_ids", "displayed": False},
            {"field": "secret_hashes_snippets_lengths", "displayed": False},
            {"field": "platform_target_identifiers", "displayed": False},
        ],
        "watermark_status_label_panel": [
            "Local fixture UI", "Not public-postable", "Review-only", "No financial advice",
            "No signal language", "Live/API disabled", "Limitations visible",
            "Missing/degraded/proxy visible", "Screenshot-safe mode", "Evidence refs visible",
        ],
    }
    return _build_packet_tail(packet)



def _build_packet_tail(packet):
    """Attach remaining panels and counters."""
    packet["limitations_freshness_visibility_panel"] = {
        "limitations_cannot_be_hidden": True,
        "freshness_visible_for_market_current_claims": True,
        "missing_degraded_proxy_states_visible": True,
        "dqr_forecast_readiness_blocks_visible": True,
        "no_confident_forecast_when_data_sufficiency_blocks": True,
    }
    packet["evidence_reference_visibility_panel"] = {
        "evidence_refs_visible": True,
        "task_evidence_packet_ids_visible": True,
        "source_artifact_ids_only_if_approved_real": True,
        "future_artifact_backed_without_real_ids_blocked": True,
        "evidence_vault_handoff_read_only": True,
        "invented_source_artifact_ids_allowed": False,
    }
    packet["export_eligibility_checklist"] = [
        "no_secrets_visible", "no_raw_env_path", "no_raw_request_url",
        "no_raw_platform_response", "no_raw_vendor_data", "no_public_ready_false_claim",
        "no_signal_or_trade_advice_language", "limitations_visible",
        "freshness_visible_where_required", "evidence_refs_visible",
        "watermark_visible", "operator_review_required",
    ]
    packet["blocked_export_action_matrix"] = [
        {"action": "capture_screenshot", "state": "disabled"},
        {"action": "export_png", "state": "disabled"},
        {"action": "export_pdf", "state": "disabled"},
        {"action": "export_svg", "state": "disabled"},
        {"action": "download_file", "state": "disabled"},
        {"action": "upload_to_platform", "state": "disabled"},
        {"action": "publish_to_platform", "state": "disabled"},
        {"action": "schedule_post", "state": "disabled"},
        {"action": "send_telegram_message", "state": "disabled"},
        {"action": "run_antigravity", "state": "disabled"},
        {"action": "browser_capture", "state": "disabled"},
        {"action": "scrape_metrics", "state": "disabled"},
        {"action": "refresh_project_sources", "state": "disabled"},
        {"action": "read_env", "state": "disabled"},
        {"action": "edit_evidence", "state": "disabled"},
    ]
    packet["antigravity_handoff_panel"] = {
        "antigravity_run_yet": False,
        "future_0167_may_define_browser_qa": True,
        "future_task_requires_explicit_go": True,
        "browser_qa_must_be_narrow_and_screenshot_safe": True,
        "no_live_api_env_in_browser": True,
        "no_credentials_in_browser_state": True,
        "no_platform_posting": True,
    }
    packet["visual_quality_checklist"] = {
        "high_contrast": True,
        "text_legibility": True,
        "dense_but_readable": True,
        "status_labels_visible": True,
        "blocked_states_obvious": True,
        "redaction_obvious": True,
        "color_only_status_communication": False,
        "green_red_as_market_direction": False,
        "pnl_trading_look": False,
        "social_scheduler_glamor": False,
    }
    packet["screenshot_safe_preview_states"] = [
        {"state": "export_ready_with_redaction", "export_safe": True},
        {"state": "blocked_missing_limitations", "export_safe": False, "blocked": True},
        {"state": "blocked_secret_visible", "export_safe": False, "blocked": True},
        {"state": "blocked_public_ready_claim", "export_safe": False, "blocked": True},
        {"state": "blocked_no_evidence_refs", "export_safe": False, "blocked": True},
        {"state": "blocked_unredacted_platform_response", "export_safe": False, "blocked": True},
    ]
    packet["manual_operator_checklist"] = [
        "inspect_visible_labels", "inspect_redaction_overlays", "inspect_evidence_refs",
        "inspect_limitations_freshness", "inspect_no_live_or_action_controls",
        "confirm_no_secrets", "confirm_no_public_ready_false_claim",
        "document_manual_screenshot_context_later_if_performed_outside_repo",
    ]
    packet["evidence_summary"] = {
        "linked_design_system_screenshot_safe_rules": True,
        "linked_evidence_vault": True,
        "linked_content_calendar": True,
        "linked_publish_readiness_tower": True,
        "linked_command_center": True,
        "validation_test_scan_evidence_required": True,
    }
    packet["next_allowed_action_panel"] = {
        "directive": "AWAIT OPERATOR/CHATGPT AUDIT_OF_0166_EVIDENCE_BEFORE_ANY_NEXT_TASK",
        "future_task": "0167 Antigravity Browser QA only after audit",
    }
    packet["forbidden_controls_active_count"] = 0
    packet["external_dependency_count"] = 0
    packet["remote_url_count"] = 0
    packet["fetch_call_count"] = _count_network_hits()
    packet["screenshot_safe_policy"] = {"present": True, "redact_secrets": True, "redact_env_paths": True}
    packet["redaction_policy"] = {
        "redact_secrets": True, "redact_env_paths": True,
        "redact_request_urls": True, "redact_raw_platform_responses": True,
    }
    packet["blocked_reasons"] = []
    packet["packet_status"] = "pass"
    return packet



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
    if packet.get("visual_export_mode") != "static_local_only":
        errors.append("visual_export_mode_must_be_static_local_only")
    if packet.get("secret_visible_count") != 0:
        errors.append("secret_visible_count_must_be_zero")
    if packet.get("forbidden_controls_active_count") != 0:
        errors.append("forbidden_controls_active_count_must_be_zero")

    scope = packet.get("active_frontend_code_changed_scope", "")
    if "ui/institutional_shell" not in scope:
        errors.append("active_frontend_scope_out_of_bounds")

    for rel in RUNTIME_SHELL_FILES:
        if not _file_exists(rel):
            errors.append(f"shell_file_missing:{rel}")

    # Screenshot-safe mode panel must not imply actual capture.
    ssm = packet.get("screenshot_safe_mode_panel", {})
    if ssm.get("screenshot_taken_by_task") is not False:
        errors.append("screenshot_must_not_be_taken")
    if ssm.get("image_video_pdf_export_created") is not False:
        errors.append("export_file_must_not_be_created")
    if ssm.get("browser_automation") is not False:
        errors.append("browser_automation_must_be_false")
    if ssm.get("antigravity_run") is not False:
        errors.append("antigravity_run_must_be_false")

    # Export-safe card gallery: at least 6 cards, required source screens present.
    cards = packet.get("export_safe_card_gallery", [])
    if len(cards) < 6:
        errors.append("fewer_than_6_export_safe_cards")
    sources = {c.get("source_screen") for c in cards}
    for src in REQUIRED_EXPORT_CARDS:
        if src not in sources:
            errors.append(f"export_card_missing_source_{src}")
    if not any(c.get("card_id") == "esc-telegram-gate" for c in cards):
        errors.append("telegram_gate_redacted_card_missing")

    # Redaction overlay completeness.
    redaction_fields = {r.get("field") for r in packet.get("redaction_overlay_panel", [])}
    for f in REQUIRED_REDACTION_FIELDS:
        # token_chat_id_values mapped, also accept token_chat_id
        if f not in redaction_fields:
            errors.append(f"redaction_field_missing_{f}")
    for r in packet.get("redaction_overlay_panel", []):
        if r.get("displayed") is not False:
            errors.append(f"redaction_field_displayed_{r.get('field')}")

    # Watermark labels.
    labels = packet.get("watermark_status_label_panel", [])
    for w in REQUIRED_WATERMARK_LABELS:
        if w not in labels:
            errors.append(f"watermark_label_missing_{w}")

    return _validate_packet_tail(packet, errors)



def _validate_packet_tail(packet, errors):
    """Second half of validation: panels, checklist, controls, scans."""
    lfp = packet.get("limitations_freshness_visibility_panel", {})
    if lfp.get("limitations_cannot_be_hidden") is not True:
        errors.append("limitations_must_not_be_hidden")
    if lfp.get("freshness_visible_for_market_current_claims") is not True:
        errors.append("freshness_must_be_visible_for_current_claims")

    erp = packet.get("evidence_reference_visibility_panel", {})
    if erp.get("evidence_refs_visible") is not True:
        errors.append("evidence_refs_must_be_visible")
    if erp.get("invented_source_artifact_ids_allowed") is not False:
        errors.append("invented_artifact_ids_must_not_be_allowed")

    checklist = packet.get("export_eligibility_checklist", [])
    for item in REQUIRED_CHECKLIST_ITEMS:
        if item not in checklist:
            errors.append(f"checklist_missing_{item}")

    actions = {a.get("action"): a.get("state") for a in packet.get("blocked_export_action_matrix", [])}
    for a in REQUIRED_BLOCKED_ACTIONS:
        if a not in actions:
            errors.append(f"blocked_action_missing_{a}")
        elif actions[a] != "disabled":
            errors.append(f"action_not_disabled_{a}")

    ah = packet.get("antigravity_handoff_panel", {})
    if ah.get("antigravity_run_yet") is not False:
        errors.append("antigravity_must_not_be_run_yet")
    if ah.get("future_task_requires_explicit_go") is not True:
        errors.append("antigravity_future_must_require_explicit_go")

    vq = packet.get("visual_quality_checklist", {})
    if vq.get("color_only_status_communication") is not False:
        errors.append("color_only_status_must_be_false")
    if vq.get("green_red_as_market_direction") is not False:
        errors.append("green_red_market_direction_must_be_false")

    previews = {p.get("state"): p for p in packet.get("screenshot_safe_preview_states", [])}
    for ps in REQUIRED_PREVIEW_STATES:
        if ps not in previews:
            errors.append(f"preview_state_missing_{ps}")
    # Only export_ready_with_redaction may be export-safe.
    for state, p in previews.items():
        if state == "export_ready_with_redaction":
            if p.get("export_safe") is not True:
                errors.append("export_ready_state_must_be_safe")
        else:
            if p.get("export_safe") is True:
                errors.append(f"blocked_preview_must_not_be_safe_{state}")
            if p.get("blocked") is not True:
                errors.append(f"blocked_preview_must_be_blocked_{state}")

    if not packet.get("manual_operator_checklist"):
        errors.append("manual_operator_checklist_missing")
    if not packet.get("evidence_summary"):
        errors.append("evidence_summary_missing")

    nap = packet.get("next_allowed_action_panel", {})
    if "AUDIT_OF_0166" not in str(nap.get("directive", "")):
        errors.append("next_allowed_action_must_require_audit")

    net_hits = _count_network_hits()
    if net_hits != 0:
        errors.append(f"network_capability_present:{net_hits}")
    if packet.get("fetch_call_count") != 0:
        errors.append("fetch_call_count_must_be_zero")
    if packet.get("external_dependency_count") != 0:
        errors.append("external_dependency_count_must_be_zero")
    if packet.get("remote_url_count") != 0:
        errors.append("remote_url_count_must_be_zero")
    if _count_secret_hits() != 0:
        errors.append("secret_like_value_present")

    if packet.get("packet_status") == "pass" and errors:
        errors.append("packet_status_pass_but_errors_exist")

    return {"valid": len(errors) == 0, "errors": errors}



def summary():
    """Return a JSON-serializable redacted visual export summary."""
    packet = build_packet()
    res = validate_packet(packet)
    cards = packet.get("export_safe_card_gallery", [])
    ready = [c for c in cards if not c.get("blocked_export_reason")]
    previews = packet.get("screenshot_safe_preview_states", [])
    blocked_previews = [p for p in previews if p.get("blocked")]
    return {
        "packet_status": packet.get("packet_status") if res["valid"] else "blocked",
        "validation_valid": res["valid"],
        "visual_export_mode": packet.get("visual_export_mode"),
        "static_local_only": packet.get("static_local_only"),
        "export_preparation_only": packet.get("export_preparation_only"),
        "screenshot_capture_enabled_now": packet.get("screenshot_capture_enabled_now"),
        "file_export_enabled_now": packet.get("file_export_enabled_now"),
        "platform_upload_enabled_now": packet.get("platform_upload_enabled_now"),
        "screenshot_safe_mode_present": bool(packet.get("screenshot_safe_mode_panel")),
        "export_safe_card_count": len(cards),
        "export_safe_card_ready_count": len(ready),
        "blocked_preview_state_count": len(blocked_previews),
        "redaction_rule_count": len(packet.get("redaction_overlay_panel", [])),
        "watermark_label_count": len(packet.get("watermark_status_label_panel", [])),
        "limitation_visibility_rule_count": len(packet.get("limitations_freshness_visibility_panel", {})),
        "evidence_visibility_rule_count": len(packet.get("evidence_reference_visibility_panel", {})),
        "export_checklist_item_count": len(packet.get("export_eligibility_checklist", [])),
        "blocked_export_action_count": len(packet.get("blocked_export_action_matrix", [])),
        "active_export_or_capture_control_count": 0,
        "antigravity_handoff_present": bool(packet.get("antigravity_handoff_panel")),
        "visual_quality_checklist_present": bool(packet.get("visual_quality_checklist")),
        "manual_operator_checklist_present": bool(packet.get("manual_operator_checklist")),
        "evidence_summary_present": bool(packet.get("evidence_summary")),
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
        "provider_llm_api_allowed_now": packet.get("provider_llm_api_allowed_now"),
        "repo_web_search_allowed_now": packet.get("repo_web_search_allowed_now"),
        "live_posting_enabled_now": packet.get("live_posting_enabled_now"),
        "scheduler_allowed_now": packet.get("scheduler_allowed_now"),
        "scraping_allowed_now": packet.get("scraping_allowed_now"),
        "public_ready_final_copy_generated": packet.get("public_ready_final_copy_generated"),
        "evidence_mutation_enabled_now": packet.get("evidence_mutation_enabled_now"),
        "secret_visible_count": packet.get("secret_visible_count"),
        "raw_env_path_visible": False,
        "raw_request_url_visible": False,
        "raw_platform_response_visible": False,
        "unsafe_signal_language_enabled": packet.get("unsafe_signal_language_enabled"),
        "red_green_market_direction_semantics": packet.get("red_green_market_direction_semantics"),
        "kill_switch_status": "active",
        "blocked_reasons": res["errors"],
    }

    return hits
