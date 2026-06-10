"""Institutional UI/UX front-end rebuild plan packet (0157).

Planning-only. Deterministic, fail-closed validator and redacted summary for the
institutional UI/UX + front-end rebuild master plan. No network, no credentials,
no env reads, no live capability. Mirrors the repo's packet/validator/summary
convention.
"""
import json
import os
import datetime
import jsonschema

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
SCHEMAS_DIR = os.path.join(BASE_DIR, "schemas")
DOCS_DIR = os.path.join(BASE_DIR, "docs")

TASK_LABEL = "TASK_CONTENTOPS_0157_INSTITUTIONAL_UI_UX_FRONTEND_REBUILD_MASTER_PLAN_V0"

MASTER_PLAN_DOC = "docs/INSTITUTIONAL_UI_UX_FRONTEND_REBUILD_MASTER_PLAN_AFTER_0157.md"
BACKLOG_DOC = "docs/INSTITUTIONAL_UI_UX_FRONTEND_REBUILD_BACKLOG_AFTER_0157.md"
QUALITY_MATRIX_DOC = "docs/INSTITUTIONAL_UI_UX_QUALITY_BAR_AND_ACCEPTANCE_MATRIX_AFTER_0157.md"
ANTIGRAVITY_STRATEGY_DOC = "docs/ANTIGRAVITY_BROWSER_QA_STRATEGY_AFTER_0157.md"

PHASE_TASK_LABELS = [
    "TASK_CONTENTOPS_0158_INSTITUTIONAL_DESIGN_SYSTEM_VISUAL_CONTRACT_V0",
    "TASK_CONTENTOPS_0159_UI_VIEW_MODEL_CONTRACT_V2_V0",
    "TASK_CONTENTOPS_0160_INSTITUTIONAL_SHELL_PROTOTYPE_V0",
    "TASK_CONTENTOPS_0161_COMMAND_CENTER_SCREEN_V0",
    "TASK_CONTENTOPS_0162_CONTENT_STUDIO_REBUILD_V0",
    "TASK_CONTENTOPS_0163_PUBLISH_READINESS_TOWER_V0",
    "TASK_CONTENTOPS_0164_EVIDENCE_VAULT_V0",
    "TASK_CONTENTOPS_0165_CALENDAR_WORKFLOW_BOARD_V0",
    "TASK_CONTENTOPS_0166_VISUAL_EXPORT_SCREENSHOT_SAFE_MODE_V0",
    "TASK_CONTENTOPS_0167_ANTIGRAVITY_BROWSER_QA_PASS_V0",
    "TASK_CONTENTOPS_0168_CLINE_INSTITUTIONAL_POLISH_PASS_V0",
]

STATUS_TOKEN_VOCABULARY = [
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
]

FORBIDDEN_TRUE = [
    "runtime_authority",
    "active_frontend_code_changed",
    "backend_server_required",
    "browser_automation_used_now",
    "antigravity_used_now",
    "credential_read_allowed_now",
    "platform_api_allowed_now",
    "live_posting_enabled_now",
    "scheduler_allowed_now",
    "scraping_allowed_now",
    "public_ready_final_copy_generated",
    "signal_language_allowed",
]

REQUIRED_TRUE = [
    "manual_review_required",
    "not_public_postable",
    "safety_banners_required",
]


def _load_schema(name):
    with open(os.path.join(SCHEMAS_DIR, name), "r", encoding="utf-8") as f:
        return json.load(f)


PACKET_SCHEMA = _load_schema("institutional_ui_ux_frontend_rebuild_plan_packet.schema.json")



def build_packet():
    """Build the planning-only packet. All live/credential flags fail-closed false."""
    return {
        "packet_id": "institutional_ui_ux_frontend_rebuild_plan_0157",
        "created_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "runtime_authority": False,
        "task_label": TASK_LABEL,
        "ui_rebuild_mode": "planning_only",
        "active_frontend_code_changed": False,
        "backend_server_required": False,
        "browser_automation_used_now": False,
        "antigravity_used_now": False,
        "credential_read_allowed_now": False,
        "platform_api_allowed_now": False,
        "live_posting_enabled_now": False,
        "scheduler_allowed_now": False,
        "scraping_allowed_now": False,
        "public_ready_final_copy_generated": False,
        "manual_review_required": True,
        "not_public_postable": True,
        "safety_banners_required": True,
        "secret_visible_count": 0,
        "signal_language_allowed": False,
        "master_plan_doc": MASTER_PLAN_DOC,
        "backlog_doc": BACKLOG_DOC,
        "quality_matrix_doc": QUALITY_MATRIX_DOC,
        "antigravity_strategy_doc": ANTIGRAVITY_STRATEGY_DOC,
        "phase_task_labels": list(PHASE_TASK_LABELS),
        "status_token_vocabulary": list(STATUS_TOKEN_VOCABULARY),
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
    if packet.get("ui_rebuild_mode") != "planning_only":
        errors.append("ui_rebuild_mode_must_be_planning_only")
    if packet.get("secret_visible_count") != 0:
        errors.append("secret_visible_count_must_be_zero")

    # Phase coverage must include 0158 through 0168.
    labels = packet.get("phase_task_labels", [])
    for needed in ("0158", "0167", "0168"):
        if not any(needed in lbl for lbl in labels):
            errors.append(f"phase_task_{needed}_missing")

    # Status token vocabulary completeness.
    for tok in STATUS_TOKEN_VOCABULARY:
        if tok not in packet.get("status_token_vocabulary", []):
            errors.append(f"status_token_{tok}_missing")

    # Referenced docs must exist on disk (planning authority committed).
    for key in ("master_plan_doc", "backlog_doc", "quality_matrix_doc", "antigravity_strategy_doc"):
        rel = packet.get(key)
        if not rel or not _doc_exists(rel):
            errors.append(f"{key}_not_found")

    status = packet.get("packet_status")
    if status == "pass" and errors:
        errors.append("packet_status_pass_but_errors_exist")

    return {"valid": len(errors) == 0, "errors": errors}


def summary():
    """Return a JSON-serializable redacted planning summary."""
    packet = build_packet()
    res = validate_packet(packet)
    return {
        "packet_status": packet.get("packet_status") if res["valid"] else "blocked",
        "validation_valid": res["valid"],
        "task_label": packet.get("task_label"),
        "ui_rebuild_mode": packet.get("ui_rebuild_mode"),
        "runtime_authority": packet.get("runtime_authority"),
        "active_frontend_code_changed": packet.get("active_frontend_code_changed"),
        "backend_server_required": packet.get("backend_server_required"),
        "browser_automation_used_now": packet.get("browser_automation_used_now"),
        "antigravity_used_now": packet.get("antigravity_used_now"),
        "credential_read_allowed_now": packet.get("credential_read_allowed_now"),
        "platform_api_allowed_now": packet.get("platform_api_allowed_now"),
        "live_posting_enabled_now": packet.get("live_posting_enabled_now"),
        "scheduler_allowed_now": packet.get("scheduler_allowed_now"),
        "scraping_allowed_now": packet.get("scraping_allowed_now"),
        "public_ready_final_copy_generated": packet.get("public_ready_final_copy_generated"),
        "manual_review_required": packet.get("manual_review_required"),
        "not_public_postable": packet.get("not_public_postable"),
        "safety_banners_required": packet.get("safety_banners_required"),
        "secret_visible_count": packet.get("secret_visible_count"),
        "signal_language_allowed": packet.get("signal_language_allowed"),
        "master_plan_doc": packet.get("master_plan_doc"),
        "backlog_doc": packet.get("backlog_doc"),
        "quality_matrix_doc": packet.get("quality_matrix_doc"),
        "antigravity_strategy_doc": packet.get("antigravity_strategy_doc"),
        "phase_task_count": len(packet.get("phase_task_labels", [])),
        "status_token_count": len(packet.get("status_token_vocabulary", [])),
        "kill_switch_status": packet.get("kill_switch_status"),
        "blocked_reasons": res["errors"],
    }
