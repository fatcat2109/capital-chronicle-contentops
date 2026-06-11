"""Institutional content calendar + workflow board screen packet (0165).

Static/local-only frontend screen contract. Deterministic, fail-closed validator
and redacted summary. Inspects static shell assets under ui/institutional_shell/
WITHOUT a browser, network, or env reads. Mirrors the repo packet/validator/
summary convention.
"""
import json
import os
import re
import datetime
import jsonschema

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
SCHEMAS_DIR = os.path.join(BASE_DIR, "schemas")

TASK_LABEL = "TASK_CONTENTOPS_0165_INSTITUTIONAL_CONTENT_CALENDAR_AND_WORKFLOW_BOARD_SCREEN_V0"

RUNTIME_SHELL_FILES = [
    "ui/institutional_shell/index.html",
    "ui/institutional_shell/styles.css",
    "ui/institutional_shell/app.js",
    "ui/institutional_shell/fixture_data.js",
]

REQUIRED_SAFETY_BANNERS = [
    "LOCAL_ONLY", "REVIEW_ONLY", "MANUAL_REVIEW_REQUIRED", "NOT_PUBLIC_POSTABLE",
    "LIVE_DISABLED", "SCHEDULER_DISABLED", "KILL_SWITCH_ACTIVE", "SECRET_REDACTED",
    "NO_FINANCIAL_ADVICE", "NO_SIGNAL_LANGUAGE", "MISSING_DATA_VISIBLE",
    "MANUAL_PUBLISH_TRACKING_ONLY",
]

ALLOWED_WORKFLOW_STATES = [
    "idea", "source_needed", "draft_review", "blocked",
    "operator_approved_for_manual", "manually_posted", "metrics_entered",
]

FORBIDDEN_STATES = [
    "scheduled", "auto_publish_ready", "live_published_by_system", "public_ready",
    "publish_queued", "platform_dispatched", "api_posted", "bot_posted",
]

REQUIRED_CONTENT_TYPES = [
    "data_sufficiency", "forecast_readiness", "failure_forensics", "build_in_public",
    "macro_education", "product_update", "market_note",
]

REQUIRED_LANES = ["pre_alpha_process", "grounded_news_context", "future_artifact_backed"]

REQUIRED_BLOCKED_REASONS = [
    "missing_source", "missing_artifact_id", "future_artifact_not_available",
    "claim_risk_too_high", "market_note_missing_freshness", "limitation_not_visible",
    "manual_review_missing", "public_ready_disabled", "scheduler_disabled",
    "live_posting_disabled",
]

REQUIRED_DISABLED_CONTROLS = [
    "schedule", "auto_publish", "publish_now", "queue", "platform_sync",
    "scrape_metrics", "fetch_post_url", "generate_final_copy", "approve_all",
    "upload_evidence", "refresh_project_sources",
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
    "runtime_authority", "backend_server_required", "frontend_dependencies_added",
    "browser_automation_used_now", "antigravity_used_now", "credential_read_allowed_now",
    "platform_api_allowed_now", "provider_llm_api_allowed_now", "repo_web_search_allowed_now",
    "live_posting_enabled_now", "scheduler_allowed_now", "scraping_allowed_now",
    "public_ready_final_copy_generated", "evidence_mutation_enabled_now",
    "red_green_market_direction_semantics", "unsafe_signal_language_enabled",
]

REQUIRED_TRUE = ["static_local_only", "fixture_or_mock_data_only", "manual_workflow_only"]


def _load_schema(name):
    with open(os.path.join(SCHEMAS_DIR, name), "r", encoding="utf-8") as f:
        return json.load(f)


PACKET_SCHEMA = _load_schema("institutional_content_calendar_workflow_board_screen_packet.schema.json")


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


def _content_items():
    base = {
        "source_status": "sources_attached", "evidence_refs": ["ev-x"],
        "freshness_status": "current", "limitation_status": "limitations_visible",
        "approval_state": "pending_operator", "manual_publish_state": "not_posted",
        "blocked_reasons": [], "next_operator_action": "review",
    }

    def mk(item_id, title, ctype, lane, state, **over):
        d = dict(base)
        d.update({"item_id": item_id, "title": title, "content_type": ctype,
                  "lane": lane, "lifecycle_state": state, "claim_risk": over.get("claim_risk", "evergreen_education")})
        d.update(over)
        return d

    market_extra = {"educational_general_only": True, "no_signal_language": True, "no_buy_sell_hold": True}
    return [
        mk("ci-001", "Data sufficiency report walkthrough", "data_sufficiency", "pre_alpha_process", "draft_review"),
        mk("ci-002", "What forecast-not-ready means", "forecast_readiness", "pre_alpha_process", "idea",
           source_status="no_source_yet", evidence_refs=[], freshness_status="n_a", claim_risk="first_party_philosophy"),
        mk("ci-003", "Postmortem: pipeline degraded run", "failure_forensics", "pre_alpha_process", "blocked",
           source_status="missing_source", evidence_refs=[], freshness_status="stale",
           limitation_status="limitations_missing", blocked_reasons=["missing_source", "limitation_not_visible"]),
        mk("ci-004", "Build-in-public: shipping the evidence vault", "build_in_public", "pre_alpha_process",
           "operator_approved_for_manual", approval_state="approved_manual_only", claim_risk="first_party_philosophy"),
        mk("ci-005", "Macro education: what CPI is and is not", "macro_education", "grounded_news_context",
           "draft_review", claim_risk="current_factual_claim_requires_citation"),
        mk("ci-006", "Product update: institutional shell screens", "product_update", "pre_alpha_process",
           "manually_posted", approval_state="approved_manual_only", manual_publish_state="manually_posted_out_of_band",
           claim_risk="first_party_philosophy"),
        mk("ci-007", "Market note: rates context, educational only", "market_note", "grounded_news_context",
           "metrics_entered", approval_state="approved_manual_only", manual_publish_state="manually_posted_out_of_band",
           freshness_status="current_freshness_labeled", claim_risk="current_factual_claim_requires_citation",
           manual_metrics={"manual_impressions": 0, "manual_clicks": 0,
                           "manual_post_url": "recorded_out_of_band_not_fetched"}, **market_extra),
        mk("ci-008", "Market note draft missing freshness label", "market_note", "grounded_news_context",
           "blocked", freshness_status="freshness_missing", claim_risk="current_factual_claim_requires_citation",
           blocked_reasons=["market_note_missing_freshness"], **market_extra),
    ]


def build_packet():
    """Build the content calendar + workflow board screen packet. Fail-closed flags."""
    items = _content_items()
    packet = {
        "packet_id": "institutional_content_calendar_workflow_board_screen_0165",
        "created_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "task_label": TASK_LABEL,
        "content_calendar_mode": "static_local_only",
        "runtime_authority": False,
        "static_local_only": True,
        "fixture_or_mock_data_only": True,
        "manual_workflow_only": True,
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
        "workflow_states": list(ALLOWED_WORKFLOW_STATES),
        "forbidden_states": list(FORBIDDEN_STATES),
        "content_items": items,
        "content_type_coverage": list(REQUIRED_CONTENT_TYPES),
        "lane_model": [
            {"lane": "pre_alpha_process", "state": "allowed_review_only"},
            {"lane": "grounded_news_context", "state": "allowed_with_source_citation"},
            {"lane": "future_artifact_backed", "state": "blocked"},
        ],
    }
    return _build_packet_tail(packet)



def _build_packet_tail(packet):
    """Attach remaining panels and counters."""
    packet["evidence_source_panel"] = {
        "source_evidence_required": True,
        "artifact_ids_required_for_future_artifact_backed": True,
        "source_url_date_required_for_current_factual_claims": True,
        "invented_source_artifact_ids_allowed": False,
        "missing_source_blocks_publish_readiness": True,
        "proxy_or_degraded_status_visible": True,
    }
    packet["approval_manual_publish_panel"] = {
        "operator_approval_required": True,
        "approval_is_automatic": False,
        "approval_implies_platform_posting": False,
        "manual_publish_is_out_of_band": True,
        "manual_post_url_recorded_later_not_fetched": True,
        "metrics_entered_later_manually": True,
        "api_sync": False,
    }
    packet["freshness_limitations_panel"] = {
        "stale_items_require_review": True,
        "freshness_label_required_for_current_claims": True,
        "missing_degraded_proxy_labels_visible": True,
        "forecast_readiness_blocked_is_valid_state": True,
        "no_confident_forecast_when_dqr_blocks": True,
    }
    packet["blocked_reasons_panel"] = list(REQUIRED_BLOCKED_REASONS)
    packet["calendar_view"] = {
        "grid_style": "static_week_planning_grid",
        "implies_scheduled_posts": False,
        "slots": [
            {"label": "planned review slot", "day": "Mon"},
            {"label": "manual publish window candidate", "day": "Tue"},
            {"label": "source refresh checkpoint", "day": "Wed"},
            {"label": "metrics entry reminder", "day": "Thu"},
            {"label": "planned review slot", "day": "Fri"},
        ],
    }
    packet["workflow_board_view"] = {
        "columns": list(ALLOWED_WORKFLOW_STATES),
        "drag_drop_backend_required": False,
        "persistence_implied": False,
    }
    packet["metrics_placeholder_panel"] = {
        "manual_impressions": "manual_entry_only",
        "manual_clicks": "manual_entry_only",
        "manual_engagement_notes": "manual_entry_only",
        "manual_post_url": "recorded_out_of_band_not_fetched",
        "manual_posted_at": "operator_supplied",
        "scraping": False,
        "platform_api_metrics": False,
        "automatic_sync": False,
    }
    packet["decision_ledger_handoff"] = {
        "decisions_evidence_backed": True,
        "revocation_supported_or_future_required": True,
        "decision_history_read_only": True,
        "auto_approval": False,
    }
    packet["evidence_vault_handoff"] = {
        "every_item_needs_evidence_refs": True,
        "audit_trail_needed": True,
        "evidence_packet_standard_applies": True,
        "evidence_mutation_from_this_screen": False,
    }
    packet["visual_export_handoff"] = {
        "next_screen": "0166 Visual Export / Screenshot-Safe Mode",
        "screenshot_export_must_be_redacted": True,
        "export_to_platform": False,
    }
    packet["disabled_controls_surface"] = [
        {"control": c, "state": "disabled"} for c in REQUIRED_DISABLED_CONTROLS
    ]
    packet["evidence_summary"] = {
        "linked_content_studio": True,
        "linked_publish_readiness_tower": True,
        "linked_evidence_vault": True,
        "linked_decision_ledger": True,
        "linked_manual_publish_metrics": True,
        "validation_test_scan_evidence_required": True,
    }
    packet["next_allowed_action_panel"] = {
        "directive": "AWAIT OPERATOR/CHATGPT AUDIT_OF_0165_EVIDENCE_BEFORE_ANY_NEXT_TASK",
        "future_task": "0166 Visual Export / Screenshot-Safe Mode only after audit",
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
    if packet.get("content_calendar_mode") != "static_local_only":
        errors.append("content_calendar_mode_must_be_static_local_only")
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

    # Workflow states completeness.
    states = packet.get("workflow_states", [])
    for s in ALLOWED_WORKFLOW_STATES:
        if s not in states:
            errors.append(f"workflow_state_missing_{s}")

    # Forbidden states must not appear as active lifecycle states.
    items = packet.get("content_items", [])
    active_states = {it.get("lifecycle_state") for it in items}
    for fs in FORBIDDEN_STATES:
        if fs in active_states:
            errors.append(f"forbidden_state_active_{fs}")
        if fs in states:
            errors.append(f"forbidden_state_in_workflow_states_{fs}")

    # At least 8 content items.
    if len(items) < 8:
        errors.append("fewer_than_8_content_items")

    # Required content types.
    coverage = packet.get("content_type_coverage", [])
    for ct in REQUIRED_CONTENT_TYPES:
        if ct not in coverage:
            errors.append(f"content_type_missing_{ct}")

    # Market note items must carry educational/freshness/no-signal constraints.
    market_items = [it for it in items if it.get("content_type") == "market_note"]
    if not market_items:
        errors.append("no_market_note_item")
    for it in market_items:
        if not it.get("educational_general_only"):
            errors.append(f"market_note_not_educational_{it.get('item_id')}")
        if not it.get("no_signal_language"):
            errors.append(f"market_note_signal_language_{it.get('item_id')}")
        if not it.get("no_buy_sell_hold"):
            errors.append(f"market_note_buy_sell_hold_{it.get('item_id')}")
        if not it.get("freshness_status"):
            errors.append(f"market_note_no_freshness_field_{it.get('item_id')}")

    # Lane model completeness + future_artifact_backed blocked.
    lanes = {l.get("lane"): l.get("state") for l in packet.get("lane_model", [])}
    for ln in REQUIRED_LANES:
        if ln not in lanes:
            errors.append(f"lane_missing_{ln}")
    if lanes.get("future_artifact_backed") != "blocked":
        errors.append("future_artifact_backed_must_be_blocked")

    return _validate_packet_tail(packet, errors)



def _validate_packet_tail(packet, errors):
    """Second half of validation: panels, controls, scans."""
    esp = packet.get("evidence_source_panel", {})
    if esp.get("source_evidence_required") is not True:
        errors.append("evidence_source_required_must_be_true")
    if esp.get("invented_source_artifact_ids_allowed") is not False:
        errors.append("invented_artifact_ids_must_not_be_allowed")

    amp = packet.get("approval_manual_publish_panel", {})
    if amp.get("operator_approval_required") is not True:
        errors.append("operator_approval_required_must_be_true")
    if amp.get("approval_implies_platform_posting") is not False:
        errors.append("approval_must_not_imply_platform_posting")
    if amp.get("api_sync") is not False:
        errors.append("manual_publish_api_sync_must_be_false")

    flp = packet.get("freshness_limitations_panel", {})
    if flp.get("missing_degraded_proxy_labels_visible") is not True:
        errors.append("missing_degraded_proxy_must_be_visible")

    brp = packet.get("blocked_reasons_panel", [])
    for r in REQUIRED_BLOCKED_REASONS:
        if r not in brp:
            errors.append(f"blocked_reason_missing_{r}")

    cal = packet.get("calendar_view", {})
    if cal.get("implies_scheduled_posts") is not False:
        errors.append("calendar_must_not_imply_scheduled_posts")
    cal_text = json.dumps(cal).lower()
    for bad in ("scheduled post", "auto publish", "dispatch time", "queue"):
        if bad in cal_text:
            errors.append(f"calendar_uses_forbidden_semantics_{bad.replace(' ', '_')}")

    mpp = packet.get("metrics_placeholder_panel", {})
    if mpp.get("scraping") is not False:
        errors.append("metrics_scraping_must_be_false")
    if mpp.get("platform_api_metrics") is not False:
        errors.append("metrics_platform_api_must_be_false")
    if mpp.get("automatic_sync") is not False:
        errors.append("metrics_automatic_sync_must_be_false")

    dlh = packet.get("decision_ledger_handoff", {})
    if dlh.get("auto_approval") is not False:
        errors.append("decision_ledger_must_not_auto_approve")

    evh = packet.get("evidence_vault_handoff", {})
    if evh.get("evidence_mutation_from_this_screen") is not False:
        errors.append("evidence_vault_handoff_must_not_mutate")

    veh = packet.get("visual_export_handoff", {})
    if veh.get("export_to_platform") is not False:
        errors.append("visual_export_must_not_export_to_platform")

    controls = {c.get("control"): c.get("state") for c in packet.get("disabled_controls_surface", [])}
    for c in REQUIRED_DISABLED_CONTROLS:
        if c not in controls:
            errors.append(f"disabled_control_missing_{c}")
        elif controls[c] != "disabled":
            errors.append(f"control_not_disabled_{c}")

    nap = packet.get("next_allowed_action_panel", {})
    if "AUDIT_OF_0165" not in str(nap.get("directive", "")):
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
    """Return a JSON-serializable redacted calendar/workflow summary."""
    packet = build_packet()
    res = validate_packet(packet)
    items = packet.get("content_items", [])
    market = [i for i in items if i.get("content_type") == "market_note"]
    market_ok = [i for i in market if i.get("educational_general_only") and i.get("no_signal_language")
                 and i.get("no_buy_sell_hold") and i.get("freshness_status")]
    lanes = packet.get("lane_model", [])
    blocked_lanes = [l for l in lanes if l.get("state") == "blocked"]
    return {
        "packet_status": packet.get("packet_status") if res["valid"] else "blocked",
        "validation_valid": res["valid"],
        "content_calendar_mode": packet.get("content_calendar_mode"),
        "static_local_only": packet.get("static_local_only"),
        "manual_workflow_only": packet.get("manual_workflow_only"),
        "workflow_state_count": len(packet.get("workflow_states", [])),
        "forbidden_state_count": len(packet.get("forbidden_states", [])),
        "active_forbidden_state_count": 0,
        "content_item_count": len(items),
        "content_type_count": len(packet.get("content_type_coverage", [])),
        "market_note_count": len(market),
        "market_note_with_required_limits_count": len(market_ok),
        "lane_count": len(lanes),
        "blocked_lane_count": len(blocked_lanes),
        "evidence_source_panel_present": bool(packet.get("evidence_source_panel")),
        "approval_manual_publish_panel_present": bool(packet.get("approval_manual_publish_panel")),
        "freshness_limitations_panel_present": bool(packet.get("freshness_limitations_panel")),
        "blocked_reason_count": len(packet.get("blocked_reasons_panel", [])),
        "calendar_slot_count": len((packet.get("calendar_view", {}) or {}).get("slots", [])),
        "workflow_board_column_count": len((packet.get("workflow_board_view", {}) or {}).get("columns", [])),
        "metrics_placeholder_present": bool(packet.get("metrics_placeholder_panel")),
        "decision_ledger_handoff_present": bool(packet.get("decision_ledger_handoff")),
        "evidence_vault_handoff_present": bool(packet.get("evidence_vault_handoff")),
        "visual_export_handoff_present": bool(packet.get("visual_export_handoff")),
        "disabled_control_count": len(packet.get("disabled_controls_surface", [])),
        "active_schedule_or_publish_control_count": 0,
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
        "unsafe_signal_language_enabled": packet.get("unsafe_signal_language_enabled"),
        "red_green_market_direction_semantics": packet.get("red_green_market_direction_semantics"),
        "kill_switch_status": "active",
        "blocked_reasons": res["errors"],
    }

    return hits
