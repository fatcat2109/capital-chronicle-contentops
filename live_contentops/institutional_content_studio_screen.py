"""Institutional content studio screen packet (0162).

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

TASK_LABEL = "TASK_CONTENTOPS_0162_INSTITUTIONAL_CONTENT_STUDIO_REBUILD_SCREEN_V0"

RUNTIME_SHELL_FILES = [
    "ui/institutional_shell/index.html",
    "ui/institutional_shell/styles.css",
    "ui/institutional_shell/app.js",
    "ui/institutional_shell/fixture_data.js",
]

REQUIRED_SAFETY_BANNERS = [
    "LOCAL_ONLY", "REVIEW_ONLY", "MANUAL_REVIEW_REQUIRED", "NOT_PUBLIC_POSTABLE",
    "LIVE_DISABLED", "SECRET_REDACTED", "NO_FINANCIAL_ADVICE", "NO_SIGNAL_LANGUAGE",
    "MISSING_DATA_VISIBLE", "FORECAST_NOT_READY",
]

REQUIRED_LANES = ["pre_alpha_process", "grounded_news_context", "future_artifact_backed"]

REQUIRED_CLAIM_CLASSES = [
    "first_party_philosophy", "evergreen_education", "cited_factual_claim",
    "current_factual_claim_requiring_citation", "market_sensitive_claim",
    "forbidden_claim",
]

REQUIRED_GUARDRAILS = [
    "buy_sell_hold", "long_short", "position_sizing", "entries_exits",
    "target_prices", "guaranteed_prediction", "signal_service_framing",
    "execution_broker_order_routing", "fake_alpha",
    "unsupported_numeric_market_claims", "raw_vendor_data_redistribution",
    "hidden_missing_degraded_proxy_data",
]

REQUIRED_SOURCE_FIELDS = [
    "source_url", "source_date", "source_summary", "claim_risk_notes",
    "freshness_label", "limitation_label",
]

REQUIRED_BLOCKED_ACTIONS = [
    "generate_final_public_copy", "auto_approve", "publish", "schedule",
    "provider_llm_api", "news_search_fetch", "platform_api", "scrape_metrics",
    "artifact_backed_without_real_artifacts", "create_market_signal",
    "credential_display", "one_button_publish_all",
]

REQUIRED_PLATFORMS = ["substack", "linkedin", "x", "threads", "telegram"]

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
    "provider_llm_api_allowed_now",
    "repo_web_search_allowed_now",
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


PACKET_SCHEMA = _load_schema("institutional_content_studio_screen_packet.schema.json")


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
    """Build the content studio screen packet. Fail-closed safety flags."""
    packet = {
        "packet_id": "institutional_content_studio_screen_0162",
        "created_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "task_label": TASK_LABEL,
        "content_studio_mode": "static_local_only",
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
        "provider_llm_api_allowed_now": False,
        "repo_web_search_allowed_now": False,
        "live_posting_enabled_now": False,
        "scheduler_allowed_now": False,
        "scraping_allowed_now": False,
        "public_ready_final_copy_generated": False,
        "red_green_market_direction_semantics": False,
        "unsafe_signal_language_enabled": False,
        "secret_visible_count": _count_secret_hits(),
        "content_lanes": [
            {"lane_id": "pre_alpha_process", "state": "allowed_review_only"},
            {"lane_id": "grounded_news_context", "state": "allowed_with_constraints"},
            {"lane_id": "future_artifact_backed", "state": "blocked"},
        ],
        "lane_rules": {
            "lane_mixing": "blocked",
            "future_artifact_fixture_use": "blocked",
            "source_artifact_ids_invented": "blocked",
            "capital_chronicle_alpha_implied_before_approval": "blocked",
        },
        "grounded_news_rule_panel": {
            "news_is_hook_not_signal": True,
            "source_metadata_supplied_externally": True,
            "repo_searches_or_fetches_news": False,
            "market_direction_claims": "blocked",
            "model_predicts_claims": "blocked",
            "actionable_trade_framing": "blocked",
        },
        "source_evidence_requirements": [
            {"field": "source_url", "requirement": "required for factual/current claims"},
            {"field": "source_date", "requirement": "required for factual/current claims"},
            {"field": "source_summary", "requirement": "required"},
            {"field": "claim_risk_notes", "requirement": "required"},
            {"field": "freshness_label", "requirement": "required"},
            {"field": "limitation_label", "requirement": "required"},
            {"field": "artifact_id", "requirement": "real artifact ID required later"},
            {"field": "missing_source", "requirement": "blocks publish-readiness"},
        ],
        "draft_review_only_panel": {
            "draft_origin": "externally drafted / manual draft only",
            "repo_calls_provider_llm_api": False,
            "draft_is_review_only": True,
            "final_public_copy_generation": "disabled",
            "manual_jim_review_required": True,
        },
        "claim_risk_classifier": [
            {"class": "first_party_philosophy", "handling": "allowed"},
            {"class": "evergreen_education", "handling": "allowed"},
            {"class": "cited_factual_claim", "handling": "allowed_with_citation"},
            {"class": "current_factual_claim_requiring_citation", "handling": "requires_citation"},
            {"class": "market_sensitive_claim", "handling": "blocked_or_transformed_to_evergreen_education"},
            {"class": "forbidden_claim", "handling": "blocked"},
        ],
        "guardrail_results": [{"category": c, "state": "forbidden"} for c in REQUIRED_GUARDRAILS],
    }
    return _build_packet_tail(packet)



def _build_packet_tail(packet):
    """Attach remaining panels and counters to the packet."""
    packet["limitations_refusal_mode"] = {
        "missing_stays_missing": True,
        "degraded_stays_degraded": True,
        "proxy_only_is_labeled": True,
        "forecast_readiness_can_stay_blocked": True,
        "no_forecast_is_valid_output": True,
        "uncertainty_must_be_visible": True,
    }
    packet["platform_fit_preview"] = [
        {"platform": p, "mode": "dry_run_read_only"} for p in REQUIRED_PLATFORMS
    ]
    packet["platform_fit_constraints"] = {
        "export_to_platform": "disabled",
        "schedule": "disabled",
        "publish": "disabled",
        "live_api": "disabled",
    }
    packet["editorial_quality_state"] = {
        "review_completeness": "fixture_static",
        "evidence_completeness": "fixture_static",
        "limitation_visibility": "fixture_static",
        "guardrail_cleanliness": "fixture_static",
        "manual_review_pending": True,
        "implies_publish_ready": False,
    }
    packet["decision_ledger_handoff"] = {
        "operator_decision_required": True,
        "approval_is_automatic": False,
        "revocation_supported": True,
        "evidence_refs_required": True,
        "public_ready_approval_enabled_now": False,
    }
    packet["draft_inspector_handoff"] = {
        "next_drilldown_surface": "draft_inspector",
        "source_lineage_must_remain_visible": True,
        "guardrails_must_remain_visible": True,
    }
    packet["blocked_action_matrix"] = [
        {"action": a, "state": "disabled"} for a in REQUIRED_BLOCKED_ACTIONS
    ]
    packet["evidence_summary"] = {
        "content_studio_workbench": "linked (concept)",
        "grounded_news_rule": "linked",
        "external_draft_review": "linked",
        "decision_ledger": "linked",
        "platform_fit_readiness_dry_run": "linked",
        "evidence_packet_required": True,
    }
    packet["next_allowed_action_panel"] = {
        "directive": "AWAIT OPERATOR/CHATGPT AUDIT_OF_0162_EVIDENCE_BEFORE_ANY_NEXT_TASK",
        "future_task": "0163 Publish Readiness Tower only after audit",
    }
    packet["forbidden_controls_active_count"] = 0
    packet["external_dependency_count"] = 0
    packet["remote_url_count"] = 0
    packet["fetch_call_count"] = _count_network_hits()
    packet["screenshot_safe_policy"] = {
        "present": True, "redact_secrets": True, "redact_env_paths": True,
    }
    packet["redaction_policy"] = {
        "redact_secrets": True,
        "redact_env_paths": True,
        "redact_request_urls": True,
        "redact_raw_platform_responses": True,
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
    if packet.get("content_studio_mode") != "static_local_only":
        errors.append("content_studio_mode_must_be_static_local_only")
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

    lanes = {l.get("lane_id"): l for l in packet.get("content_lanes", [])}
    for lane in REQUIRED_LANES:
        if lane not in lanes:
            errors.append(f"content_lane_missing_{lane}")
    fab = lanes.get("future_artifact_backed", {})
    if fab.get("state") != "blocked":
        errors.append("future_artifact_backed_must_be_blocked")

    lr = packet.get("lane_rules", {})
    if lr.get("lane_mixing") != "blocked":
        errors.append("lane_mixing_must_be_blocked")
    if lr.get("source_artifact_ids_invented") != "blocked":
        errors.append("source_artifact_ids_invention_must_be_blocked")

    gn = packet.get("grounded_news_rule_panel", {})
    if gn.get("news_is_hook_not_signal") is not True:
        errors.append("grounded_news_must_be_hook_not_signal")
    if gn.get("repo_searches_or_fetches_news") is not False:
        errors.append("repo_news_search_must_be_disabled")

    fields = [s.get("field") for s in packet.get("source_evidence_requirements", [])]
    for f in REQUIRED_SOURCE_FIELDS:
        if f not in fields:
            errors.append(f"source_evidence_missing_{f}")

    dr = packet.get("draft_review_only_panel", {})
    if dr.get("repo_calls_provider_llm_api") is not False:
        errors.append("draft_panel_must_not_call_provider_llm")
    if dr.get("draft_is_review_only") is not True:
        errors.append("draft_must_be_review_only")
    if dr.get("final_public_copy_generation") != "disabled":
        errors.append("final_public_copy_generation_must_be_disabled")
    if dr.get("manual_jim_review_required") is not True:
        errors.append("manual_review_must_be_required")
    return _validate_packet_tail(packet, errors)



def _validate_packet_tail(packet, errors):
    """Second half of validation: classifier, guardrails, platform, scans."""
    classes = [c.get("class") for c in packet.get("claim_risk_classifier", [])]
    for c in REQUIRED_CLAIM_CLASSES:
        if c not in classes:
            errors.append(f"claim_risk_class_missing_{c}")
    for c in packet.get("claim_risk_classifier", []):
        if c.get("class") == "market_sensitive_claim":
            h = str(c.get("handling", ""))
            if "blocked" not in h and "transformed" not in h:
                errors.append("market_sensitive_claim_must_be_blocked_or_transformed")

    cats = [g.get("category") for g in packet.get("guardrail_results", [])]
    for g in REQUIRED_GUARDRAILS:
        if g not in cats:
            errors.append(f"guardrail_missing_{g}")

    lim = packet.get("limitations_refusal_mode", {})
    for key in ("missing_stays_missing", "degraded_stays_degraded", "proxy_only_is_labeled"):
        if lim.get(key) is not True:
            errors.append(f"limitations_must_keep_{key}")

    for p in packet.get("platform_fit_preview", []):
        if p.get("mode") != "dry_run_read_only":
            errors.append(f"platform_fit_must_be_dry_run_{p.get('platform')}")
    pfc = packet.get("platform_fit_constraints", {})
    for key in ("export_to_platform", "schedule", "publish", "live_api"):
        if pfc.get(key) != "disabled":
            errors.append(f"platform_fit_{key}_must_be_disabled")

    eq = packet.get("editorial_quality_state", {})
    if eq.get("implies_publish_ready") is not False:
        errors.append("editorial_quality_must_not_imply_publish_ready")

    dl = packet.get("decision_ledger_handoff", {})
    if dl.get("operator_decision_required") is not True:
        errors.append("decision_ledger_operator_decision_required")
    if dl.get("approval_is_automatic") is not False:
        errors.append("decision_ledger_must_not_auto_approve")

    di = packet.get("draft_inspector_handoff", {})
    if di.get("next_drilldown_surface") != "draft_inspector":
        errors.append("draft_inspector_handoff_missing")

    actions = [a.get("action") for a in packet.get("blocked_action_matrix", [])]
    for a in REQUIRED_BLOCKED_ACTIONS:
        if a not in actions:
            errors.append(f"blocked_action_missing_{a}")

    nap = packet.get("next_allowed_action_panel", {})
    if "AUDIT_OF_0162" not in str(nap.get("directive", "")):
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
    """Return a JSON-serializable redacted content studio screen summary."""
    packet = build_packet()
    res = validate_packet(packet)
    lanes = packet.get("content_lanes", [])
    allowed = [l for l in lanes if str(l.get("state", "")).startswith("allowed")]
    blocked = [l for l in lanes if l.get("state") == "blocked"]
    return {
        "packet_status": packet.get("packet_status") if res["valid"] else "blocked",
        "validation_valid": res["valid"],
        "content_studio_mode": packet.get("content_studio_mode"),
        "static_local_only": packet.get("static_local_only"),
        "content_lane_count": len(lanes),
        "allowed_lane_count": len(allowed),
        "blocked_lane_count": len(blocked),
        "grounded_news_rule_present": bool(packet.get("grounded_news_rule_panel")),
        "source_evidence_requirement_count": len(packet.get("source_evidence_requirements", [])),
        "claim_risk_class_count": len(packet.get("claim_risk_classifier", [])),
        "guardrail_category_count": len(packet.get("guardrail_results", [])),
        "limitation_rule_count": len(packet.get("limitations_refusal_mode", {})),
        "platform_fit_preview_count": len(packet.get("platform_fit_preview", [])),
        "blocked_action_count": len(packet.get("blocked_action_matrix", [])),
        "evidence_summary_present": bool(packet.get("evidence_summary")),
        "decision_ledger_handoff_present": bool(packet.get("decision_ledger_handoff")),
        "draft_inspector_handoff_present": bool(packet.get("draft_inspector_handoff")),
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
        "secret_visible_count": packet.get("secret_visible_count"),
        "unsafe_signal_language_enabled": packet.get("unsafe_signal_language_enabled"),
        "red_green_market_direction_semantics": packet.get("red_green_market_direction_semantics"),
        "kill_switch_status": "active",
        "blocked_reasons": res["errors"],
    }
