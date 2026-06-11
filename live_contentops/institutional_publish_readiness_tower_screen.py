"""Institutional publish readiness tower screen packet (0163).

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

TASK_LABEL = "TASK_CONTENTOPS_0163_INSTITUTIONAL_PUBLISH_READINESS_TOWER_SCREEN_V0"

RUNTIME_SHELL_FILES = [
    "ui/institutional_shell/index.html",
    "ui/institutional_shell/styles.css",
    "ui/institutional_shell/app.js",
    "ui/institutional_shell/fixture_data.js",
]

REQUIRED_SAFETY_BANNERS = [
    "LOCAL_ONLY", "DRY_RUN_ONLY", "REVIEW_ONLY", "MANUAL_REVIEW_REQUIRED",
    "NOT_PUBLIC_POSTABLE", "LIVE_DISABLED", "API_VALIDATED_NO_POST",
    "CHANNEL_PERMISSION_UNVALIDATED", "KILL_SWITCH_ACTIVE", "SECRET_REDACTED",
    "NO_FINANCIAL_ADVICE", "NO_SIGNAL_LANGUAGE",
]

REQUIRED_PLATFORMS = [
    "telegram", "x", "linkedin", "threads", "substack",
    "facebook_page", "instagram", "tiktok",
]

REQUIRED_DISABLED_CONTROLS = [
    "publish", "schedule", "connect_api", "oauth", "send_message",
    "getme_live_call", "upload_media", "publish_all", "auto_post",
    "scrape_metrics", "reply_dm",
]

REQUIRED_TELEGRAM_GATES = [
    "credential_presence", "official_docs_verification", "getme_token_validation",
    "channel_write_permission", "dry_run_payload_preview", "manual_approval",
    "kill_switch", "send_message", "live_adapter", "posting", "scheduler",
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


PACKET_SCHEMA = _load_schema("institutional_publish_readiness_tower_screen_packet.schema.json")


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


def _platform_registry():
    rows = []
    meta = {
        "telegram": ("Telegram", "future pilot channel", "redacted_presence_only", "implemented", "channel write permission unvalidated; separate GO required"),
        "x": ("X", "short education/process hooks", "not_configured_redacted", "pending", "docs verification + credentials pending"),
        "linkedin": ("LinkedIn", "professional process insight", "not_configured_redacted", "pending", "docs verification + credentials pending"),
        "threads": ("Threads", "conversational mirror", "not_configured_redacted", "pending", "docs verification + credentials pending"),
        "substack": ("Substack", "long-form home", "not_configured_redacted", "pending", "docs verification + credentials pending"),
        "facebook_page": ("Facebook Page", "process distribution", "not_configured_redacted", "pending", "docs verification + credentials pending"),
        "instagram": ("Instagram", "visual process recap", "not_configured_redacted", "pending", "docs verification + credentials pending"),
        "tiktok": ("TikTok", "short explainer", "not_configured_redacted", "pending", "docs verification + credentials pending"),
    }
    for pid in REQUIRED_PLATFORMS:
        name, use, cred, docs, blocker = meta[pid]
        rows.append({
            "platform_id": pid, "display_name": name, "intended_use": use,
            "dry_run_render": "modeled", "credential_state": cred,
            "docs_verification": docs, "manual_review_required": True,
            "not_public_postable": True, "live_api": "disabled",
            "scheduling": "disabled", "next_blocker": blocker,
        })
    return rows


def build_packet():
    """Build the publish readiness tower screen packet. Fail-closed flags."""
    packet = {
        "packet_id": "institutional_publish_readiness_tower_screen_0163",
        "created_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "task_label": TASK_LABEL,
        "publish_readiness_tower_mode": "static_local_only",
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
        "platform_capability_registry_panel": _platform_registry(),
        "dry_run_batch_manifest_panel": {
            "dry_run_only": True,
            "fixture_mock_payload_only": True,
            "real_platform_payload_dispatch": False,
            "source_lineage_required": True,
            "limitation_visibility_required": True,
            "idempotency_policy_modeled": True,
            "partial_failure_policy_modeled": True,
            "redacted_audit_required": True,
            "manual_approval_gate_required": True,
        },
        "manual_approval_gate_panel": {
            "approval_required_before_live_publish": True,
            "current_state": "review_only_dry_run",
            "public_ready_approval_enabled_now": False,
            "operator_decision_required": True,
            "revocation_supported": True,
            "auto_approval": False,
        },
        "kill_switch_gate_panel": {
            "kill_switch_active": True,
            "blocks_publishing": True,
            "no_publish_while_active": True,
            "must_be_audited_in_future_live_tasks": True,
        },
    }
    return _build_packet_tail(packet)



def _build_packet_tail(packet):
    """Attach remaining panels and counters to the packet."""
    packet["credential_secret_state_panel"] = {
        "credentials_local_only_out_of_band": True,
        "credential_values_displayed": False,
        "token_chat_id_redacted": True,
        "env_path_shown": False,
        "secret_redaction_required": True,
        "credential_read_in_this_task": False,
        "validation_implies_posting_permission": False,
    }
    packet["redacted_audit_gate_panel"] = {
        "audit_events_modeled": True,
        "unredacted_secrets_in_audit": False,
        "raw_request_urls_in_audit": False,
        "raw_platform_responses_in_audit": False,
        "raw_env_path_in_audit": False,
        "future_platform_responses_must_be_redacted": True,
        "evidence_packet_must_be_secret_safe": True,
    }
    packet["official_docs_gate_panel"] = {
        "per_platform_docs_verification_required": True,
        "telegram_official_docs_gate": "implemented",
        "other_platforms_require_future_verification": True,
        "docs_verification_is_runtime_authority": False,
        "docs_verification_enables_live_posting": False,
    }
    packet["telegram_pilot_tower_panel"] = {
        "sub_gates": [
            {"gate": "credential_presence", "state": "redacted_presence_only"},
            {"gate": "official_docs_verification", "state": "implemented"},
            {"gate": "getme_token_validation", "state": "gate_implemented_live_run_status_separate_later"},
            {"gate": "channel_write_permission", "state": "unvalidated"},
            {"gate": "dry_run_payload_preview", "state": "modeled_only"},
            {"gate": "manual_approval", "state": "required"},
            {"gate": "kill_switch", "state": "active"},
            {"gate": "send_message", "state": "disabled"},
            {"gate": "live_adapter", "state": "disabled"},
            {"gate": "posting", "state": "disabled"},
            {"gate": "scheduler", "state": "disabled"},
        ],
        "next_step": "next Telegram live step requires a separate explicit operator/ChatGPT GO",
    }
    packet["publish_disabled_control_surface"] = [
        {"control": c, "state": "disabled"} for c in REQUIRED_DISABLED_CONTROLS
    ]
    packet["idempotency_partial_failure_panel"] = {
        "idempotency_required_before_live": True,
        "duplicate_prevention_required": True,
        "partial_failure_policy_required": True,
        "rollback_manual_fallback_required": True,
        "current_live_retry_loop": False,
    }
    packet["future_live_handoff_panel"] = {
        "live_adapter_absent_disabled": True,
        "one_platform_live_requires_explicit_go": True,
        "autonomous_posting": False,
        "autonomous_replies_dms": False,
        "platform_by_platform_rollout_only": True,
    }
    packet["evidence_summary"] = {
        "publish_automation_readiness": "linked",
        "platform_capability_registry": "linked",
        "dry_run_manifest": "linked",
        "credential_policy": "linked",
        "redacted_audit_log": "linked",
        "telegram_gate": "linked",
        "validation_test_scan_evidence_required": True,
    }
    packet["next_allowed_action_panel"] = {
        "directive": "AWAIT OPERATOR/CHATGPT AUDIT_OF_0163_EVIDENCE_BEFORE_ANY_NEXT_TASK",
        "future_task": "0164 Evidence Vault only after audit",
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
    if packet.get("publish_readiness_tower_mode") != "static_local_only":
        errors.append("publish_readiness_tower_mode_must_be_static_local_only")
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

    # Platform registry completeness + per-platform constraints.
    plats = {p.get("platform_id"): p for p in packet.get("platform_capability_registry_panel", [])}
    for pid in REQUIRED_PLATFORMS:
        if pid not in plats:
            errors.append(f"platform_missing_{pid}")
    for pid, p in plats.items():
        if p.get("live_api") != "disabled":
            errors.append(f"platform_live_api_must_be_disabled_{pid}")
        if p.get("scheduling") != "disabled":
            errors.append(f"platform_scheduling_must_be_disabled_{pid}")
        if p.get("not_public_postable") is not True:
            errors.append(f"platform_must_be_not_public_postable_{pid}")
        if p.get("dry_run_render") != "modeled":
            errors.append(f"platform_must_be_dry_run_{pid}")

    # Dry-run manifest must not imply real dispatch.
    dm = packet.get("dry_run_batch_manifest_panel", {})
    if dm.get("dry_run_only") is not True:
        errors.append("manifest_must_be_dry_run_only")
    if dm.get("real_platform_payload_dispatch") is not False:
        errors.append("manifest_must_not_dispatch")

    # Manual approval gate must not auto-approve.
    ma = packet.get("manual_approval_gate_panel", {})
    if ma.get("approval_required_before_live_publish") is not True:
        errors.append("manual_approval_required")
    if ma.get("auto_approval") is not False:
        errors.append("manual_approval_must_not_auto_approve")

    # Kill switch gate must be active/blocking.
    ks = packet.get("kill_switch_gate_panel", {})
    if ks.get("kill_switch_active") is not True:
        errors.append("kill_switch_must_be_active")
    if ks.get("blocks_publishing") is not True:
        errors.append("kill_switch_must_block_publishing")

    # Credential panel must not display or imply values.
    cp = packet.get("credential_secret_state_panel", {})
    if cp.get("credential_values_displayed") is not False:
        errors.append("credential_values_must_not_be_displayed")
    if cp.get("env_path_shown") is not False:
        errors.append("env_path_must_not_be_shown")
    if cp.get("validation_implies_posting_permission") is not False:
        errors.append("validation_must_not_imply_posting")

    return _validate_packet_tail(packet, errors)



def _validate_packet_tail(packet, errors):
    """Second half of validation: audit, docs, telegram, controls, scans."""
    # Redacted audit gate must block raw secrets/urls/responses/env.
    ra = packet.get("redacted_audit_gate_panel", {})
    for key in ("unredacted_secrets_in_audit", "raw_request_urls_in_audit",
                "raw_platform_responses_in_audit", "raw_env_path_in_audit"):
        if ra.get(key) is not False:
            errors.append(f"redacted_audit_must_block_{key}")

    # Official docs gate must not enable live posting.
    od = packet.get("official_docs_gate_panel", {})
    if od.get("docs_verification_enables_live_posting") is not False:
        errors.append("docs_verification_must_not_enable_live_posting")

    # Telegram pilot gates completeness + guardrails.
    tg = packet.get("telegram_pilot_tower_panel", {})
    gates = {g.get("gate"): g.get("state") for g in tg.get("sub_gates", [])}
    for g in REQUIRED_TELEGRAM_GATES:
        if g not in gates:
            errors.append(f"telegram_gate_missing_{g}")
    if gates.get("channel_write_permission") != "unvalidated":
        errors.append("telegram_channel_permission_must_be_unvalidated")
    if gates.get("send_message") != "disabled":
        errors.append("telegram_send_message_must_be_disabled")
    if gates.get("posting") != "disabled":
        errors.append("telegram_posting_must_be_disabled")
    if gates.get("live_adapter") != "disabled":
        errors.append("telegram_live_adapter_must_be_disabled")
    if gates.get("scheduler") != "disabled":
        errors.append("telegram_scheduler_must_be_disabled")
    if gates.get("credential_presence") != "redacted_presence_only":
        errors.append("telegram_credential_presence_must_be_redacted")

    # Publish-disabled control surface completeness + no active controls.
    controls = {c.get("control"): c.get("state") for c in packet.get("publish_disabled_control_surface", [])}
    for c in REQUIRED_DISABLED_CONTROLS:
        if c not in controls:
            errors.append(f"disabled_control_missing_{c}")
    for c, state in controls.items():
        if state != "disabled":
            errors.append(f"control_must_be_disabled_{c}")

    # Idempotency / partial failure: no live retry loop.
    ip = packet.get("idempotency_partial_failure_panel", {})
    if ip.get("idempotency_required_before_live") is not True:
        errors.append("idempotency_required")
    if ip.get("partial_failure_policy_required") is not True:
        errors.append("partial_failure_policy_required")
    if ip.get("current_live_retry_loop") is not False:
        errors.append("no_live_retry_loop_allowed")

    # Future live handoff requires explicit GO.
    fh = packet.get("future_live_handoff_panel", {})
    if fh.get("one_platform_live_requires_explicit_go") is not True:
        errors.append("future_live_requires_explicit_go")
    if fh.get("autonomous_posting") is not False:
        errors.append("no_autonomous_posting")

    # Next allowed action must require audit before 0164.
    nap = packet.get("next_allowed_action_panel", {})
    if "AUDIT_OF_0163" not in str(nap.get("directive", "")):
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

    if _count_secret_hits() != 0:
        errors.append("secret_like_value_present")

    if packet.get("packet_status") == "pass" and errors:
        errors.append("packet_status_pass_but_errors_exist")

    return {"valid": len(errors) == 0, "errors": errors}



def summary():
    """Return a JSON-serializable redacted publish readiness tower summary."""
    packet = build_packet()
    res = validate_packet(packet)
    plats = packet.get("platform_capability_registry_panel", [])
    dry = [p for p in plats if p.get("dry_run_render") == "modeled"]
    live = [p for p in plats if p.get("live_api") != "disabled"]
    sched = [p for p in plats if p.get("scheduling") != "disabled"]
    public = [p for p in plats if p.get("not_public_postable") is not True]
    controls = packet.get("publish_disabled_control_surface", [])
    active = [c for c in controls if c.get("state") != "disabled"]
    tg = packet.get("telegram_pilot_tower_panel", {})
    return {
        "packet_status": packet.get("packet_status") if res["valid"] else "blocked",
        "validation_valid": res["valid"],
        "publish_readiness_tower_mode": packet.get("publish_readiness_tower_mode"),
        "static_local_only": packet.get("static_local_only"),
        "platform_count": len(plats),
        "dry_run_platform_count": len(dry),
        "live_enabled_platform_count": len(live),
        "scheduler_enabled_platform_count": len(sched),
        "public_postable_platform_count": len(public),
        "manual_approval_gate_present": bool(packet.get("manual_approval_gate_panel")),
        "kill_switch_gate_present": bool(packet.get("kill_switch_gate_panel")),
        "credential_secret_state_present": bool(packet.get("credential_secret_state_panel")),
        "redacted_audit_gate_present": bool(packet.get("redacted_audit_gate_panel")),
        "official_docs_gate_present": bool(packet.get("official_docs_gate_panel")),
        "telegram_pilot_gate_count": len(tg.get("sub_gates", [])),
        "disabled_control_count": len(controls),
        "active_publish_control_count": len(active),
        "idempotency_policy_present": bool(packet.get("idempotency_partial_failure_panel", {}).get("idempotency_required_before_live")),
        "partial_failure_policy_present": bool(packet.get("idempotency_partial_failure_panel", {}).get("partial_failure_policy_required")),
        "future_live_handoff_present": bool(packet.get("future_live_handoff_panel")),
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
        "secret_visible_count": packet.get("secret_visible_count"),
        "unsafe_signal_language_enabled": packet.get("unsafe_signal_language_enabled"),
        "red_green_market_direction_semantics": packet.get("red_green_market_direction_semantics"),
        "kill_switch_status": "active",
        "blocked_reasons": res["errors"],
    }

    return hits
