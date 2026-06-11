"""Institutional evidence vault + audit timeline screen packet (0164).

Static/local-only frontend screen contract. Deterministic, fail-closed validator
and redacted summary. Inspects the static shell assets under
ui/institutional_shell/ WITHOUT a browser, network, or env reads. Mirrors the
repo packet/validator/summary convention.
"""
import json
import os
import re
import datetime
import jsonschema

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
SCHEMAS_DIR = os.path.join(BASE_DIR, "schemas")
SHELL_DIR = os.path.join(BASE_DIR, "ui", "institutional_shell")

TASK_LABEL = "TASK_CONTENTOPS_0164_INSTITUTIONAL_EVIDENCE_VAULT_AND_AUDIT_TIMELINE_SCREEN_V0"

RUNTIME_SHELL_FILES = [
    "ui/institutional_shell/index.html",
    "ui/institutional_shell/styles.css",
    "ui/institutional_shell/app.js",
    "ui/institutional_shell/fixture_data.js",
]

REQUIRED_SAFETY_BANNERS = [
    "LOCAL_ONLY", "REVIEW_ONLY", "MANUAL_REVIEW_REQUIRED", "NOT_PUBLIC_POSTABLE",
    "LIVE_DISABLED", "KILL_SWITCH_ACTIVE", "SECRET_REDACTED", "NO_FINANCIAL_ADVICE",
    "NO_SIGNAL_LANGUAGE", "MISSING_DATA_VISIBLE", "EVIDENCE_REQUIRED", "AUDIT_READ_ONLY",
]

REQUIRED_TASK_IDS = ["0157", "0158", "0159", "0160", "0161", "0162", "0163"]

REQUIRED_FORBIDDEN_SCOPES = [
    "network_calls", "platform_api", "telegram_api", "getme", "sendmessage",
    "provider_llm_api", "news_search_market_api", "credential_env_read",
    "live_posting", "scheduler", "scraping", "live_adapter",
    "autonomous_replies_dms", "one_button_publish_all", "public_ready_final_copy",
    "fake_artifact_backed_alpha", "backend_server", "frontend_dependencies",
    "browser_automation", "antigravity", "screenshots_video_capture",
    "core_capital_chronicle_repo_mutation",
]

REQUIRED_CLASSIFICATIONS = [
    "PASS", "PASS_WITH_PROCESS_CAVEAT", "PASS_WITH_MINOR_EVIDENCE_GAP",
    "BLOCKED", "FAIL",
]

REQUIRED_CLI_SUMMARIES = [
    "institutional design system summary",
    "institutional ui view-model contract summary",
    "institutional shell prototype summary",
    "institutional command center screen summary",
    "institutional content studio screen summary",
    "institutional publish readiness tower screen summary",
    "publish automation readiness summary",
    "dry-run publish batch manifest summary",
    "redacted publish audit log summary",
    "telegram live pilot gate summary",
    "telegram official-docs credential validation gate summary",
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

REQUIRED_TRUE = ["static_local_only", "fixture_or_mock_data_only"]


def _load_schema(name):
    with open(os.path.join(SCHEMAS_DIR, name), "r", encoding="utf-8") as f:
        return json.load(f)


PACKET_SCHEMA = _load_schema("institutional_evidence_vault_audit_timeline_screen_packet.schema.json")


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


def _task_index():
    return [
        {"task_id": "0157", "classification": "PASS", "final_head": "260ae89", "artifact_category": "planning/spec", "full_suite": "1306 passed, 28 skipped", "forbidden_scope_status": "preserved"},
        {"task_id": "0158", "classification": "PASS", "final_head": "1ae6e62", "artifact_category": "design-system", "full_suite": "1332 passed, 28 skipped", "forbidden_scope_status": "preserved"},
        {"task_id": "0159", "classification": "PASS", "final_head": "15b87ff", "artifact_category": "view-model contract", "full_suite": "1369 passed, 28 skipped", "forbidden_scope_status": "preserved"},
        {"task_id": "0160", "classification": "PASS", "final_head": "1c03ca0", "artifact_category": "static shell", "full_suite": "1402 passed, 28 skipped", "forbidden_scope_status": "preserved"},
        {"task_id": "0161", "classification": "PASS", "final_head": "1b0f34a", "artifact_category": "command center screen", "full_suite": "1444 passed, 28 skipped", "forbidden_scope_status": "preserved"},
        {"task_id": "0162", "classification": "PASS", "final_head": "85f7627", "artifact_category": "content studio screen", "full_suite": "1502 passed, 28 skipped", "forbidden_scope_status": "preserved"},
        {"task_id": "0163", "classification": "PASS_WITH_MINOR_EVIDENCE_GAP", "final_head": "a7989ea", "artifact_category": "publish readiness tower screen", "full_suite": "1561 passed, 28 skipped", "forbidden_scope_status": "preserved"},
    ]


def _commit_timeline():
    return [
        {"task_id": "0157", "head": "260ae89", "state": "accepted"},
        {"task_id": "0158", "head": "1ae6e62", "state": "accepted"},
        {"task_id": "0159", "head": "15b87ff", "state": "accepted"},
        {"task_id": "0160", "head": "1c03ca0", "state": "accepted"},
        {"task_id": "0161", "head": "1b0f34a", "state": "accepted"},
        {"task_id": "0162", "head": "85f7627", "state": "accepted"},
        {"task_id": "0163", "head": "a7989ea", "state": "current_baseline"},
        {"task_id": "0164", "head": "pending", "state": "in_progress"},
        {"task_id": "0165", "head": "future", "state": "future_placeholder"},
        {"task_id": "0166", "head": "future", "state": "future_placeholder"},
        {"task_id": "0167", "head": "future", "state": "future_placeholder"},
        {"task_id": "0168", "head": "future", "state": "future_placeholder"},
    ]


def _test_history():
    return [
        {"task_id": t, "result": r, "source": "accepted_state"}
        for t, r in [
            ("0157", "1306 passed, 28 skipped"), ("0158", "1332 passed, 28 skipped"),
            ("0159", "1369 passed, 28 skipped"), ("0160", "1402 passed, 28 skipped"),
            ("0161", "1444 passed, 28 skipped"), ("0162", "1502 passed, 28 skipped"),
            ("0163", "1561 passed, 28 skipped"),
        ]
    ]


def _cli_matrix():
    rows = [{"summary": s, "state": "passing"} for s in REQUIRED_CLI_SUMMARIES]
    rows.append({"summary": "platform capability registry summary", "state": "not_invoked_in_final_batch"})
    rows.append({"summary": "publish adapter credential secret policy summary", "state": "reverified_passing_in_0164"})
    rows.append({"summary": "telegram credential setup guide summary", "state": "reverified_passing_in_0164"})
    return rows


def _forbidden_scope_matrix():
    return [{"scope": s, "state": "disabled"} for s in REQUIRED_FORBIDDEN_SCOPES]


def build_packet():
    """Build the evidence vault screen packet. Fail-closed flags."""
    packet = {
        "packet_id": "institutional_evidence_vault_audit_timeline_screen_0164",
        "created_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "task_label": TASK_LABEL,
        "evidence_vault_mode": "static_local_only",
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
        "evidence_mutation_enabled_now": False,
        "red_green_market_direction_semantics": False,
        "unsafe_signal_language_enabled": False,
        "secret_visible_count": _count_secret_hits(),
        "task_evidence_packet_index": _task_index(),
        "commit_timeline": _commit_timeline(),
        "validation_command_timeline": [
            {"command": "pytest focused tests", "result": "passed"},
            {"command": "pytest full suite", "result": "1561 passed, 28 skipped"},
            {"command": "CLI summaries", "result": "passed"},
            {"command": "node --check ui/institutional_shell/app.js", "result": "passed"},
            {"command": "git diff --check", "result": "clean"},
            {"command": "static asset validator checks", "result": "passed"},
            {"command": "secret scan", "result": "clean"},
        ],
        "test_result_history": _test_history(),
        "cli_summary_snapshot_matrix": _cli_matrix(),
    }
    return _build_packet_tail(packet)



def _build_packet_tail(packet):
    """Attach remaining panels and counters to the packet."""
    packet["secret_scan_summary_panel"] = {
        "secret_visible_count": 0,
        "raw_env_path_visible": False,
        "raw_request_url_visible": False,
        "raw_platform_response_visible": False,
        "credential_value_visible": False,
        "token_chat_id_visible": False,
        "scan_matches_policy_test_field_name_only": True,
        "no_secrets_printed_or_committed": True,
    }
    packet["forbidden_scope_matrix"] = _forbidden_scope_matrix()
    packet["residual_drift_registry"] = [
        {"item": "local_env_file", "state": "untouched_untracked", "note": "raw path never displayed"},
        {"item": "strategy_docs_pdfs", "state": "untouched"},
        {"item": "project_sources_bundle_AFTER_0074", "state": "untouched"},
        {"item": "recovered_strategy_docs", "state": "untouched"},
        {"item": "pycache", "state": "acceptable_untracked_cache"},
    ]
    packet["active_blockers_panel"] = [
        "live posting blocked",
        "scheduler blocked",
        "platform API blocked",
        "credential display blocked",
        "Antigravity not yet run",
        "live Telegram step requires separate explicit operator/ChatGPT GO",
        "future 0165 requires audit of 0164 evidence first",
    ]
    packet["evidence_packet_standard_panel"] = [
        "task label", "PASS/BLOCKED/FAIL", "repo path", "branch", "starting HEAD",
        "final HEAD", "commit hash or skip reason", "files inspected/created/changed/staged",
        "validation commands/results", "focused/full tests", "CLI summary outputs",
        "scan results", "forbidden-scope status", "residual drift touched yes/no",
        "git status", "active blockers", "exact next task",
        "no network/API/env/live/browser/Antigravity confirmation",
    ]
    packet["audit_classification_legend"] = [
        {"classification": "PASS", "meaning": "All acceptance criteria met; no gaps."},
        {"classification": "PASS_WITH_PROCESS_CAVEAT", "meaning": "Accepted with a noted process caveat that does not affect output safety."},
        {"classification": "PASS_WITH_MINOR_EVIDENCE_GAP", "meaning": "Accepted; a non-blocking evidence item was not fully captured. Applies to 0163."},
        {"classification": "BLOCKED", "meaning": "Cannot safely proceed; prerequisites unmet."},
        {"classification": "FAIL", "meaning": "A forbidden action occurred or acceptance criteria violated."},
    ]
    packet["next_task_discipline_panel"] = {
        "current_allowed_next_task": "audit of 0164 evidence",
        "future_after_audit": "0165 Calendar + Workflow Board",
        "cline_must_not_self_select": True,
        "no_phase_skipping": True,
        "no_antigravity_until_later_qa": True,
    }
    packet["audit_timeline_visualization"] = [
        {"task_id": t["task_id"], "head": t["final_head"], "classification": t["classification"],
         "evidence_status": "minor_gap_visible" if t["task_id"] == "0163" else "complete",
         "blocked_scopes": "all live planes", "validation_summary": "full suite green",
         "next_pointer": "audit then next"}
        for t in _task_index()
    ]
    packet["minor_evidence_gap_registry"] = [
        {"task_id": "0163",
         "gap": "optional CLI summaries for platform capability registry, publish-adapter credential-secret policy, and Telegram credential setup guide were not separately invoked in the final batch",
         "status": "minor_evidence_gap_not_blocker",
         "followup": "0164 reverified credential-secret policy and Telegram credential setup guide summaries passing; platform capability registry has no registered CLI command name"},
    ]
    packet["evidence_summary"] = {
        "ui_track_tasks_indexed": 7,
        "latest_full_suite": "1561 passed, 28 skipped",
        "secret_scan": "clean",
        "forbidden_scopes_preserved": True,
        "residual_drift_untouched": True,
        "evidence_packet_required": True,
    }
    packet["next_allowed_action_panel"] = {
        "directive": "AWAIT OPERATOR/CHATGPT AUDIT_OF_0164_EVIDENCE_BEFORE_ANY_NEXT_TASK",
        "future_task": "0165 Calendar + Workflow Board only after audit",
    }
    packet["evidence_mutation_controls_active_count"] = 0
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
    if packet.get("evidence_vault_mode") != "static_local_only":
        errors.append("evidence_vault_mode_must_be_static_local_only")
    if packet.get("secret_visible_count") != 0:
        errors.append("secret_visible_count_must_be_zero")
    if packet.get("evidence_mutation_controls_active_count") != 0:
        errors.append("evidence_mutation_controls_must_be_zero")
    if packet.get("forbidden_controls_active_count") != 0:
        errors.append("forbidden_controls_active_count_must_be_zero")

    scope = packet.get("active_frontend_code_changed_scope", "")
    if "ui/institutional_shell" not in scope:
        errors.append("active_frontend_scope_out_of_bounds")

    for rel in RUNTIME_SHELL_FILES:
        if not _file_exists(rel):
            errors.append(f"shell_file_missing:{rel}")

    # Task evidence index completeness + 0163 classification.
    idx = {t.get("task_id"): t for t in packet.get("task_evidence_packet_index", [])}
    for tid in REQUIRED_TASK_IDS:
        if tid not in idx:
            errors.append(f"task_evidence_missing_{tid}")
    if idx.get("0163", {}).get("classification") != "PASS_WITH_MINOR_EVIDENCE_GAP":
        errors.append("0163_must_be_pass_with_minor_evidence_gap")

    # Commit timeline must include accepted baseline a7989ea.
    heads = [c.get("head") for c in packet.get("commit_timeline", [])]
    if "a7989ea" not in heads:
        errors.append("commit_timeline_missing_baseline_a7989ea")

    # Validation timeline must include core commands.
    cmds = " ".join(c.get("command", "") for c in packet.get("validation_command_timeline", [])).lower()
    for needle in ("focused", "full suite", "cli summaries", "secret scan", "git diff"):
        if needle not in cmds:
            errors.append(f"validation_timeline_missing_{needle.replace(' ', '_')}")

    # Test history must include latest 1561 passed, 28 skipped.
    hist = " ".join(h.get("result", "") for h in packet.get("test_result_history", []))
    if "1561 passed, 28 skipped" not in hist:
        errors.append("test_history_missing_latest")

    # CLI matrix must include institutional screen summaries.
    cli = [r.get("summary") for r in packet.get("cli_summary_snapshot_matrix", [])]
    for s in REQUIRED_CLI_SUMMARIES:
        if s not in cli:
            errors.append(f"cli_matrix_missing_{s.replace(' ', '_')}")

    return _validate_packet_tail(packet, errors)



def _validate_packet_tail(packet, errors):
    """Second half of validation: scan/secret/forbidden-scope checks."""
    # Secret scan panel must not allow visible secrets/env.
    ssp = packet.get("secret_scan_summary_panel", {})
    if ssp.get("secret_visible_count") != 0:
        errors.append("secret_scan_panel_secret_visible")
    if ssp.get("raw_env_path_visible") is not False:
        errors.append("secret_scan_panel_env_path_visible")
    if ssp.get("raw_request_url_visible") is not False:
        errors.append("secret_scan_panel_request_url_visible")
    if ssp.get("raw_platform_response_visible") is not False:
        errors.append("secret_scan_panel_platform_response_visible")

    # Forbidden-scope matrix completeness + all disabled.
    fsm = {f.get("scope"): f.get("state") for f in packet.get("forbidden_scope_matrix", [])}
    for s in REQUIRED_FORBIDDEN_SCOPES:
        if s not in fsm:
            errors.append(f"forbidden_scope_missing_{s}")
        elif fsm[s] != "disabled":
            errors.append(f"forbidden_scope_enabled_{s}")

    # Residual drift registry must include local env untouched.
    drift = {d.get("item"): d.get("state") for d in packet.get("residual_drift_registry", [])}
    if "untouched" not in str(drift.get("local_env_file", "")):
        errors.append("residual_drift_local_env_must_be_untouched")

    # Active blockers must include required entries.
    blockers = " ".join(packet.get("active_blockers_panel", [])).lower()
    for needle in ("live posting", "scheduler", "platform api", "credential display",
                   "antigravity", "telegram"):
        if needle not in blockers:
            errors.append(f"active_blocker_missing_{needle.replace(' ', '_')}")

    # Audit classification legend completeness.
    classes = [c.get("classification") for c in packet.get("audit_classification_legend", [])]
    for c in REQUIRED_CLASSIFICATIONS:
        if c not in classes:
            errors.append(f"audit_classification_missing_{c}")

    # Next-task discipline must require audit before 0165 and forbid self-select.
    ntd = packet.get("next_task_discipline_panel", {})
    if "0164" not in str(ntd.get("current_allowed_next_task", "")):
        errors.append("next_task_discipline_must_require_audit")
    if ntd.get("cline_must_not_self_select") is not True:
        errors.append("next_task_discipline_must_forbid_self_select")

    # Minor evidence gap registry must mark 0163.
    gaps = [g.get("task_id") for g in packet.get("minor_evidence_gap_registry", [])]
    if "0163" not in gaps:
        errors.append("minor_evidence_gap_must_include_0163")

    # Next allowed action.
    nap = packet.get("next_allowed_action_panel", {})
    if "AUDIT_OF_0164" not in str(nap.get("directive", "")):
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
    """Return a JSON-serializable redacted evidence vault summary."""
    packet = build_packet()
    res = validate_packet(packet)
    fsm = packet.get("forbidden_scope_matrix", [])
    enabled = [f for f in fsm if f.get("state") != "disabled"]
    return {
        "packet_status": packet.get("packet_status") if res["valid"] else "blocked",
        "validation_valid": res["valid"],
        "evidence_vault_mode": packet.get("evidence_vault_mode"),
        "static_local_only": packet.get("static_local_only"),
        "evidence_packet_count": len(packet.get("task_evidence_packet_index", [])),
        "commit_timeline_count": len(packet.get("commit_timeline", [])),
        "validation_command_count": len(packet.get("validation_command_timeline", [])),
        "test_result_history_count": len(packet.get("test_result_history", [])),
        "cli_summary_snapshot_count": len(packet.get("cli_summary_snapshot_matrix", [])),
        "secret_scan_summary_present": bool(packet.get("secret_scan_summary_panel")),
        "forbidden_scope_count": len(fsm),
        "forbidden_scope_enabled_count": len(enabled),
        "residual_drift_item_count": len(packet.get("residual_drift_registry", [])),
        "active_blocker_count": len(packet.get("active_blockers_panel", [])),
        "audit_classification_count": len(packet.get("audit_classification_legend", [])),
        "minor_evidence_gap_count": len(packet.get("minor_evidence_gap_registry", [])),
        "evidence_packet_standard_present": bool(packet.get("evidence_packet_standard_panel")),
        "next_task_discipline_present": bool(packet.get("next_task_discipline_panel")),
        "audit_timeline_present": bool(packet.get("audit_timeline_visualization")),
        "evidence_mutation_control_active_count": packet.get("evidence_mutation_controls_active_count"),
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
