"""Operator evidence summary roll-up over the compiler v2 chain (0174BT).

Local-only, deterministic, fail-closed. This module is a NEW parallel, read-only
evidence layer. It rolls the ALREADY-ACCEPTED chain:

    compiler v2 output -> compile report v2 -> payload hash manifest
        -> approval/dispatch bridge report (0174BP, authoritative rollup)
        -> publish-readiness alignment (0174BR)
        -> redacted-audit alignment (0174BR)

into ONE compact, operator-facing summary object. The summary explains the chain
state WITHOUT making the chain executable. It is the local evidence object that a
future UI can safely render; it is NOT UI implementation.

It does NOT:
  * grant publish/readiness, approval, dispatch, or public-ready status,
  * call any provider/platform API, read credentials/env, or schedule/post/scrape,
  * create a real audit event or edit any audit event allow-list,
  * edit any accepted module (compiler/bridge/evidence/readiness/audit/gate/domain).

Binding (Q: how is the chain bound?): lineage is bound by ids taken from the
AUTHORITATIVE bridge report (bridge_report_id / compiler_output_id /
compile_report_id / payload_hash_manifest_id) plus the canonical bridge_report_hash
derived with the shared canonical_json_sha256 helper over the bridge report object.
Per-platform payload hashes are NOT re-derived here; 0174BP owns the payload hash
manifest. The two 0174BR alignment objects are bound by readiness_alignment_id and
audit_alignment_id, and are cross-checked for lineage/hash consistency at build
time, with the result recorded as boolean flags the validator enforces.

Fail-closed precedence: BLOCKED > UNKNOWN > REVIEW_REQUIRED > PASS.

PASS means only: the summary object is internally consistent and evidence-only, and
every bound component itself validated PASS. PASS NEVER means ready-to-publish,
ready-to-dispatch, operator-approved, live-ready, public-ready, audit-event-created,
credential-access-allowed, scheduler-enabled, or UI-implementation-complete.

Missing vs mismatch (documented fail-closed choice):
  * MISSING required lineage / alignment ids -> UNKNOWN (cannot establish lineage).
  * Present-but-MISMATCHED lineage ids or bridge hash -> BLOCKED (contradiction).
"""
from live_contentops.scd_domain_model import (
    PASS,
    BLOCKED,
    REVIEW_REQUIRED,
    UNKNOWN,
    _schema_ok,
)
from live_contentops.scd_platform_capability_registry_v2 import (
    _value,
    _state,
    _rollup,
    _apply_declared_state,
    _unsafe_runtime_hits,
    _secret_hits,
)
from live_contentops.scd_dispatch_gate import canonical_json_sha256
from live_contentops.scd_compiler_v2_dispatch_bridge import (
    validate_compiler_v2_approval_dispatch_bridge_report,
)
from live_contentops.scd_compiler_v2_bridge_publish_evidence import (
    validate_compiler_v2_bridge_publish_readiness_alignment,
    validate_compiler_v2_bridge_redacted_audit_alignment,
)


# --- Constants -----------------------------------------------------------------------

SUMMARY_SCHEMA_VERSION = "0174bt-v1"
SUMMARY_SCHEMA = "scd_compiler_v2_operator_evidence_summary.schema.json"

# Symbolic, non-executable stance literals. They describe stance only; they never
# enable behavior and contain no runtime/dispatch/scheduler vocabulary.
OPERATOR_SUMMARY_MODE = "local_evidence_summary_only"
ALLOWED_OPERATOR_ACTION = "inspect_evidence_only"

# Descriptive "no_*" labels enumerating actions the summary explicitly does NOT
# enable. These are skipped by the runtime-vocabulary scanner (they are negations).
FORBIDDEN_OPERATOR_ACTIONS = (
    "no_live_posting",
    "no_platform_api_call",
    "no_provider_api_call",
    "no_credential_read",
    "no_scheduler_enable",
    "no_dispatch_execute",
    "no_audit_event_create",
    "no_audit_allowlist_modify",
    "no_autonomous_replies",
    "no_direct_messages",
    "no_scraping",
)

VALID_STATES = (PASS, BLOCKED, REVIEW_REQUIRED, UNKNOWN)

# Flags that must all be false on any valid summary (fail closed -> BLOCKED if true).
SUMMARY_REQUIRED_FALSE_FLAGS = (
    "public_ready",
    "live_ready",
    "dispatch_ready",
    "executable_dispatch",
    "platform_api_allowed_now",
    "credential_read_allowed_now",
    "credentials_requested_now",
    "scheduler_enabled_now",
    "posting_enabled_now",
    "autonomous_replies_enabled_now",
    "dms_enabled_now",
    "scraping_enabled_now",
    "audit_event_created",
    "audit_allowlist_modified",
    "readiness_granted",
)

# Flags that must all be true on any valid summary (fail closed -> BLOCKED if not).
# Note: lineage_complete / alignment_ids_bound are intentionally NOT enforced here;
# missing lineage is handled as UNKNOWN (cannot establish), while present-but-wrong
# bindings (bridge_hash_matches / lineage_ids_consistent false) are BLOCKED.
SUMMARY_REQUIRED_TRUE_FLAGS = (
    "evidence_only",
    "non_executable",
    "manual_review_required",
    "local_only",
    "operator_visible",
    "ui_ready_packet",
    "bridge_report_bound",
    "bridge_hash_matches",
    "lineage_ids_consistent",
)

LINEAGE_ID_FIELDS = (
    "bridge_report_id",
    "compiler_output_id",
    "compile_report_id",
    "payload_hash_manifest_id",
)


# --- Shared helpers ------------------------------------------------------------------

def _schema_state(packet, schema_name):
    ok, message = _schema_ok(packet, schema_name)
    if ok:
        return []
    return [f"schema:{message}"]


def _finalize(packet, core_fn):
    blocked, review, unknown = core_fn(packet)
    result = _state(blocked, review, unknown)
    packet["validation_state"] = result["validation_state"]
    packet["blocked_reasons"] = result["reasons"] if result["validation_state"] == BLOCKED else []
    return packet


def derive_operator_evidence_summary_id(bridge_report_id):
    """Deterministic summary id from the authoritative bridge_report_id."""
    return f"oes_{bridge_report_id}" if bridge_report_id else "oes_unknown"


# --- Core validation -----------------------------------------------------------------

def _summary_core(packet):
    blocked, review, unknown = [], [], []

    for flag in SUMMARY_REQUIRED_FALSE_FLAGS:
        if _value(packet, flag) is True:
            blocked.append(f"{flag}_must_be_false")
    for flag in SUMMARY_REQUIRED_TRUE_FLAGS:
        if _value(packet, flag) is not True:
            blocked.append(f"{flag}_must_be_true")

    if _value(packet, "operator_summary_mode") != OPERATOR_SUMMARY_MODE:
        blocked.append("operator_summary_mode_must_be_local_evidence_summary_only")
    if _value(packet, "allowed_operator_action") != ALLOWED_OPERATOR_ACTION:
        blocked.append("allowed_operator_action_must_be_inspect_evidence_only")

    # Lineage presence: MISSING -> UNKNOWN (cannot establish lineage/hash).
    for id_field in LINEAGE_ID_FIELDS:
        if not _value(packet, id_field):
            unknown.append(f"{id_field}_missing")
    if not _value(packet, "bridge_report_hash"):
        unknown.append("bridge_report_hash_missing")
    if not _value(packet, "readiness_alignment_id"):
        unknown.append("readiness_alignment_id_missing")
    if not _value(packet, "audit_alignment_id"):
        unknown.append("audit_alignment_id_missing")

    # Component states.
    bridge_state = _value(packet, "bridge_report_state")
    readiness_state = _value(packet, "readiness_alignment_state")
    audit_state = _value(packet, "audit_alignment_state")
    component_states = [bridge_state, readiness_state, audit_state]

    for label, state in (
        ("bridge_report_state", bridge_state),
        ("readiness_alignment_state", readiness_state),
        ("audit_alignment_state", audit_state),
    ):
        if state not in VALID_STATES:
            unknown.append(f"{label}_invalid:{state}")

    valid_components = [s for s in component_states if s in VALID_STATES]

    # Count consistency (counts must reflect the recorded component states).
    if _value(packet, "blocker_count") != valid_components.count(BLOCKED):
        blocked.append("blocker_count_inconsistent")
    if _value(packet, "review_required_count") != valid_components.count(REVIEW_REQUIRED):
        blocked.append("review_required_count_inconsistent")
    if _value(packet, "unknown_count") != valid_components.count(UNKNOWN):
        blocked.append("unknown_count_inconsistent")

    # Rollup consistency (only when all three components are valid states).
    if len(valid_components) == 3:
        if _value(packet, "rollup_state") != _rollup(valid_components):
            blocked.append("rollup_state_inconsistent")

    # Fail-closed propagation of bound component states.
    if BLOCKED in component_states:
        blocked.append("component_blocked")
    if UNKNOWN in component_states:
        unknown.append("component_unknown")
    if REVIEW_REQUIRED in component_states:
        review.append("component_review_required")

    # Forbidden runtime vocabulary / secret-like values. The negation list under
    # forbidden_operator_actions is skipped (it enumerates disabled behaviors).
    blocked.extend(_unsafe_runtime_hits(packet, skip_keys=("forbidden_operator_actions",)))
    blocked.extend(_secret_hits(packet))
    return blocked, review, unknown


def validate_operator_evidence_summary(packet):
    """Validate an operator evidence summary packet, fail-closed.

    BLOCKED on schema failure, any required-false flag true, any required-true flag
    not true, a wrong summary mode / allowed-action literal, a recorded bridge-hash
    or lineage-id mismatch (bridge_hash_matches / lineage_ids_consistent false),
    inconsistent counts or rollup, a BLOCKED bound component, runtime/secret hits, or
    a declared PASS contradicting a non-PASS computed state. UNKNOWN propagates from
    missing lineage / alignment ids, an invalid component state, or an UNKNOWN bound
    component. REVIEW_REQUIRED propagates from a REVIEW_REQUIRED bound component.
    PASS still grants nothing.
    """
    blocked = _schema_state(packet, SUMMARY_SCHEMA)
    core_blocked, review, unknown = _summary_core(packet)
    blocked += core_blocked
    return _apply_declared_state(packet, _state(blocked, review, unknown))


# --- Builder -------------------------------------------------------------------------

def build_operator_evidence_summary(bridge_report, readiness_alignment, audit_alignment):
    """Roll the accepted chain into one compact operator-facing summary (no grant).

    Each bound component is validated with its authoritative validator; the three
    states are rolled up with fail-closed precedence. The canonical bridge_report_hash
    is derived over the supplied bridge report (no payload re-derivation). Cross-object
    lineage-id and hash consistency are recorded as boolean flags. Even on PASS, every
    readiness/public/live/dispatch/API/credential/scheduler/posting/audit flag stays
    false. Never mutates any input object.
    """
    bridge_state = validate_compiler_v2_approval_dispatch_bridge_report(bridge_report)["validation_state"]
    readiness_state = validate_compiler_v2_bridge_publish_readiness_alignment(readiness_alignment)["validation_state"]
    audit_state = validate_compiler_v2_bridge_redacted_audit_alignment(audit_alignment)["validation_state"]

    bridge_hash = canonical_json_sha256(bridge_report)

    bridge_report_id = _value(bridge_report, "bridge_report_id", "")
    compiler_output_id = _value(bridge_report, "compiler_output_id", "")
    compile_report_id = _value(bridge_report, "compile_report_id", "")
    payload_hash_manifest_id = _value(bridge_report, "payload_hash_manifest_id", "")
    readiness_alignment_id = _value(readiness_alignment, "readiness_alignment_id", "")
    audit_alignment_id = _value(audit_alignment, "audit_alignment_id", "")

    component_states = [bridge_state, readiness_state, audit_state]
    rollup_state = _rollup(component_states)

    lineage_ids_consistent = (
        _value(readiness_alignment, "bridge_report_id") == bridge_report_id
        and _value(audit_alignment, "bridge_report_id") == bridge_report_id
        and _value(readiness_alignment, "compiler_output_id") == compiler_output_id
        and _value(audit_alignment, "compiler_output_id") == compiler_output_id
        and _value(readiness_alignment, "compile_report_id") == compile_report_id
        and _value(audit_alignment, "compile_report_id") == compile_report_id
        and _value(readiness_alignment, "payload_hash_manifest_id") == payload_hash_manifest_id
        and _value(audit_alignment, "payload_hash_manifest_id") == payload_hash_manifest_id
    )
    bridge_hash_matches = (
        _value(readiness_alignment, "bridge_report_hash") == bridge_hash
        and _value(audit_alignment, "bridge_report_hash") == bridge_hash
    )
    lineage_complete = all([
        bridge_report_id,
        compiler_output_id,
        compile_report_id,
        payload_hash_manifest_id,
        readiness_alignment_id,
        audit_alignment_id,
    ])
    alignment_ids_bound = bool(readiness_alignment_id and audit_alignment_id)

    packet = {
        "schema_version": SUMMARY_SCHEMA_VERSION,
        "operator_evidence_summary_id": derive_operator_evidence_summary_id(bridge_report_id),
        "compiler_output_id": compiler_output_id,
        "compile_report_id": compile_report_id,
        "payload_hash_manifest_id": payload_hash_manifest_id,
        "bridge_report_id": bridge_report_id,
        "bridge_report_hash": bridge_hash,
        "readiness_alignment_id": readiness_alignment_id,
        "audit_alignment_id": audit_alignment_id,
        "bridge_report_state": bridge_state,
        "readiness_alignment_state": readiness_state,
        "audit_alignment_state": audit_state,
        "component_states": list(component_states),
        "rollup_state": rollup_state,
        "blocker_count": component_states.count(BLOCKED),
        "review_required_count": component_states.count(REVIEW_REQUIRED),
        "unknown_count": component_states.count(UNKNOWN),
        "evidence_only": True,
        "non_executable": True,
        "manual_review_required": True,
        "local_only": True,
        "operator_visible": True,
        "ui_ready_packet": True,
        "bridge_report_bound": True,
        "lineage_complete": lineage_complete,
        "bridge_hash_matches": bridge_hash_matches,
        "alignment_ids_bound": alignment_ids_bound,
        "lineage_ids_consistent": lineage_ids_consistent,
        "public_ready": False,
        "live_ready": False,
        "dispatch_ready": False,
        "executable_dispatch": False,
        "platform_api_allowed_now": False,
        "credential_read_allowed_now": False,
        "credentials_requested_now": False,
        "scheduler_enabled_now": False,
        "posting_enabled_now": False,
        "autonomous_replies_enabled_now": False,
        "dms_enabled_now": False,
        "scraping_enabled_now": False,
        "audit_event_created": False,
        "audit_allowlist_modified": False,
        "readiness_granted": False,
        "operator_summary_mode": OPERATOR_SUMMARY_MODE,
        "allowed_operator_action": ALLOWED_OPERATOR_ACTION,
        "forbidden_operator_actions": list(FORBIDDEN_OPERATOR_ACTIONS),
        "validation_state": rollup_state,
        "blocked_reasons": [],
    }
    return _finalize(packet, _summary_core)


# Registry of operator-evidence-summary validators, keyed for data-driven hostile tests.
OPERATOR_EVIDENCE_SUMMARY_VALIDATORS = {
    "operator_evidence_summary": validate_operator_evidence_summary,
}
