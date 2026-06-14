"""Operator evidence surface contract bridge (0174BU PREP02).

Local-only, deterministic, fail-closed. NEW parallel, read-only projection that
maps an ALREADY-ACCEPTED 0174BT operator evidence summary into a compact, UI-safe
surface contract the later 0174BU UI work can consume. It edits no accepted
module, schema, fixture, or test, and it grants nothing.

It NEVER grants publish/readiness/approval/dispatch/public-ready/live-ready
status, calls any provider/platform API, reads credentials/env, schedules, posts,
scrapes, replies, DMs, creates an audit event, or edits an audit allow-list. PASS
means only: the surface object is internally consistent, evidence-only, UI-safe.

Fail-closed precedence: BLOCKED > UNKNOWN > REVIEW_REQUIRED > PASS. Missing
required lineage/hash ids -> UNKNOWN (cannot establish lineage).
"""
from live_contentops.scd_domain_model import (
    PASS, BLOCKED, REVIEW_REQUIRED, UNKNOWN, _schema_ok,
)
from live_contentops.scd_platform_capability_registry_v2 import (
    _value, _state, _rollup, _apply_declared_state, _unsafe_runtime_hits, _secret_hits,
)

SURFACE_SCHEMA_VERSION = "0174bu-prep02-v1"
SURFACE_SCHEMA = "scd_operator_evidence_surface_contract.schema.json"
SOURCE_TASK_LABEL = "TASK_CONTENTOPS_0174BT_OPERATOR_EVIDENCE_SUMMARY_V0"
SOURCE_EVIDENCE_BASELINE_HEAD = "add55ea1c7447770cb9382f86af1794b951ae8f1"
SOURCE_EVIDENCE_BASELINE_SUBJECT = "feat: add operator evidence summary for compiler v2 chain"
NO_GRANT_LABEL = "EVIDENCE ONLY / NO GRANT"
ALLOWED_LOCAL_ACTION = "inspect evidence only"

VALID_STATES = (PASS, BLOCKED, REVIEW_REQUIRED, UNKNOWN)

SURFACE_REQUIRED_FALSE_FLAGS = (
    "public_ready", "live_ready", "dispatch_ready", "executable_dispatch",
    "platform_api_allowed_now", "credential_read_allowed_now", "scheduler_enabled_now",
    "posting_enabled_now", "audit_event_created", "audit_allowlist_modified", "readiness_granted",
)
SURFACE_REQUIRED_TRUE_FLAGS = (
    "evidence_only", "non_executable", "manual_review_required", "local_only", "ui_surface_ready",
)
LINEAGE_ID_FIELDS = (
    "operator_evidence_summary_id", "compiler_output_id", "compile_report_id",
    "payload_hash_manifest_id", "bridge_report_id", "bridge_report_hash",
    "readiness_alignment_id", "audit_alignment_id",
)
# Descriptive negation / narrative fields skipped by the runtime-vocabulary scanner;
# they intentionally enumerate disabled behaviors (negations), not enabled ones.
SCAN_SKIP_KEYS = ("blocked_actions", "required_false_flag_matrix", "truth_model_notes")
BLOCKED_ACTIONS = (
    "no_live_posting", "no_platform_api_call", "no_provider_api_call", "no_credential_read",
    "no_scheduler_enable", "no_dispatch_execute", "no_audit_event_create",
    "no_audit_allowlist_modify", "no_autonomous_replies", "no_direct_messages", "no_scraping",
)
EVIDENCE_PATH_NODES = (
    "compiler_v2_output", "compile_report_v2", "payload_hash_manifest",
    "approval_bridge_report_0174bp", "publish_readiness_alignment_0174br",
    "redacted_audit_alignment_0174br", "operator_evidence_summary_0174bt",
)
TRUTH_MODEL_NOTES = (
    "surface is evidence-only and grants nothing",
    "pass means internally consistent and ui-safe only, never publish or live or ready",
    "projection of accepted 0174bt summary; no accepted module edited",
    "all readiness, api, credential, and posting flags are forced false",
)


def derive_operator_evidence_surface_id(operator_evidence_summary_id):
    """Deterministic surface id from the bound 0174BT summary id."""
    if operator_evidence_summary_id:
        return f"oes_surface_{operator_evidence_summary_id}"
    return "oes_surface_unknown"


def _surface_core(packet):
    blocked, review, unknown = [], [], []
    for flag in SURFACE_REQUIRED_FALSE_FLAGS:
        if _value(packet, flag) is True:
            blocked.append(f"{flag}_must_be_false")
    for flag in SURFACE_REQUIRED_TRUE_FLAGS:
        if _value(packet, flag) is not True:
            blocked.append(f"{flag}_must_be_true")
    if _value(packet, "no_grant_label") != NO_GRANT_LABEL:
        blocked.append("no_grant_label_invalid")
    if _value(packet, "allowed_local_action") != ALLOWED_LOCAL_ACTION:
        blocked.append("allowed_local_action_invalid")
    for id_field in LINEAGE_ID_FIELDS:
        if not _value(packet, id_field):
            unknown.append(f"{id_field}_missing")
    states = _value(packet, "component_states", [])
    if not isinstance(states, list):
        unknown.append("component_states_invalid")
        states = []
    valid = [s for s in states if s in VALID_STATES]
    for s in states:
        if s not in VALID_STATES:
            unknown.append(f"component_state_invalid:{s}")
    if _value(packet, "blocker_count") != valid.count(BLOCKED):
        blocked.append("blocker_count_inconsistent")
    if _value(packet, "review_required_count") != valid.count(REVIEW_REQUIRED):
        blocked.append("review_required_count_inconsistent")
    if _value(packet, "unknown_count") != valid.count(UNKNOWN):
        blocked.append("unknown_count_inconsistent")
    if states and len(valid) == len(states) and _value(packet, "rollup_state") != _rollup(valid):
        blocked.append("rollup_state_inconsistent")
    if BLOCKED in valid:
        blocked.append("component_blocked")
    if UNKNOWN in valid:
        unknown.append("component_unknown")
    if REVIEW_REQUIRED in valid:
        review.append("component_review_required")
    blocked.extend(_unsafe_runtime_hits(packet, skip_keys=SCAN_SKIP_KEYS))
    blocked.extend(_secret_hits(packet))
    return blocked, review, unknown


def validate_operator_evidence_surface_contract(packet):
    """Fail-closed validation of a surface contract packet (grants nothing)."""
    ok, message = _schema_ok(packet, SURFACE_SCHEMA)
    blocked = [] if ok else [f"schema:{message}"]
    core_blocked, review, unknown = _surface_core(packet)
    return _apply_declared_state(packet, _state(blocked + core_blocked, review, unknown))


def build_operator_evidence_surface_contract(operator_evidence_summary):
    """Project an accepted 0174BT summary into a UI-safe surface contract.

    Never mutates the input. Carries lineage/hash ids and component states/counts,
    forces every readiness/api/credential/scheduler/posting/audit flag false, and
    attaches descriptive (non-executable) surface metadata.
    """
    s = operator_evidence_summary
    summary_id = _value(s, "operator_evidence_summary_id", "")
    states = _value(s, "component_states", [])
    states = list(states) if isinstance(states, list) else []
    rollup_state = _value(s, "rollup_state", UNKNOWN)
    matrix = [
        {"component": "bridge_report", "state": _value(s, "bridge_report_state", UNKNOWN),
         "evidence_id": _value(s, "bridge_report_id", "")},
        {"component": "readiness_alignment", "state": _value(s, "readiness_alignment_state", UNKNOWN),
         "evidence_id": _value(s, "readiness_alignment_id", "")},
        {"component": "audit_alignment", "state": _value(s, "audit_alignment_state", UNKNOWN),
         "evidence_id": _value(s, "audit_alignment_id", "")},
    ]
    packet = {
        "surface_schema_version": SURFACE_SCHEMA_VERSION,
        "surface_id": derive_operator_evidence_surface_id(summary_id),
        "source_task_label": SOURCE_TASK_LABEL,
        "source_evidence_baseline_head": SOURCE_EVIDENCE_BASELINE_HEAD,
        "source_evidence_baseline_subject": SOURCE_EVIDENCE_BASELINE_SUBJECT,
        "operator_evidence_summary_id": summary_id,
        "compiler_output_id": _value(s, "compiler_output_id", ""),
        "compile_report_id": _value(s, "compile_report_id", ""),
        "payload_hash_manifest_id": _value(s, "payload_hash_manifest_id", ""),
        "bridge_report_id": _value(s, "bridge_report_id", ""),
        "bridge_report_hash": _value(s, "bridge_report_hash", ""),
        "readiness_alignment_id": _value(s, "readiness_alignment_id", ""),
        "audit_alignment_id": _value(s, "audit_alignment_id", ""),
        "bridge_report_state": _value(s, "bridge_report_state", UNKNOWN),
        "readiness_alignment_state": _value(s, "readiness_alignment_state", UNKNOWN),
        "audit_alignment_state": _value(s, "audit_alignment_state", UNKNOWN),
        "component_states": states,
        "rollup_state": rollup_state,
        "blocker_count": _value(s, "blocker_count", 0),
        "review_required_count": _value(s, "review_required_count", 0),
        "unknown_count": _value(s, "unknown_count", 0),
        "no_grant_label": NO_GRANT_LABEL,
        "allowed_local_action": ALLOWED_LOCAL_ACTION,
        "blocked_actions": list(BLOCKED_ACTIONS),
        "evidence_path_nodes": list(EVIDENCE_PATH_NODES),
        "component_state_matrix": matrix,
        "required_false_flag_matrix": [{"flag": f, "value": False} for f in SURFACE_REQUIRED_FALSE_FLAGS],
        "hostile_matrix_summary": {"total_cases": 0, "never_pass": True},
        "truth_model_notes": list(TRUTH_MODEL_NOTES),
        "validation_state": rollup_state,
        "blocked_reasons": [],
    }
    packet.update({f: True for f in SURFACE_REQUIRED_TRUE_FLAGS})
    packet.update({f: False for f in SURFACE_REQUIRED_FALSE_FLAGS})
    result = validate_operator_evidence_surface_contract(packet)
    packet["validation_state"] = result["validation_state"]
    packet["blocked_reasons"] = result["reasons"] if result["validation_state"] == BLOCKED else []
    return packet


def build_static_js_bridge(packet):
    """Return a deterministic static JS literal (STEP 02B placeholder).

    Defines window.CC_OPERATOR_EVIDENCE_SURFACE with a minimal evidence-only,
    no-grant projection. Full deterministic serialization lands in the 02D
    generator. No json import, no network, no filesystem access.
    """
    version = str(_value(packet, "surface_schema_version", SURFACE_SCHEMA_VERSION))
    surface_id = str(_value(packet, "surface_id", ""))
    state = str(_value(packet, "validation_state", UNKNOWN))
    return (
        "window.CC_OPERATOR_EVIDENCE_SURFACE = {"
        '"surface_schema_version":"' + version + '",'
        '"surface_id":"' + surface_id + '",'
        '"validation_state":"' + state + '",'
        '"no_grant_label":"' + NO_GRANT_LABEL + '"};'
    )
