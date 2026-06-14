"""Compiler v2 bridge -> publish-readiness / redacted-audit evidence alignment (0174BR).

Local-only, deterministic, fail-closed. This module is a NEW parallel evidence
layer. It binds the ALREADY-ACCEPTED compiler v2 approval-dispatch bridge report
(0174BP) to two downstream concerns as *evidence only*:

    1. compiler_v2_bridge_publish_readiness_alignment
    2. compiler_v2_bridge_redacted_audit_alignment

It does NOT:
  * grant publish/readiness, approval, dispatch, or public-ready status,
  * call any provider/platform API, read credentials/env, or schedule/post,
  * create a real audit event or edit any audit event allow-list,
  * edit any accepted module (readiness/audit/bridge/registry/compiler/gate/domain).

Binding method (Q3): the bridge report is bound by lineage ids
(bridge_report_id / compiler_output_id / compile_report_id /
payload_hash_manifest_id) plus a canonical bridge_report_hash derived with the
shared canonical_json_sha256 helper over the bridge report object. Per-platform
payload hashes are NOT re-derived here; 0174BP already owns the payload hash
manifest.

Every object returns {"validation_state": <STATE>, "reasons": [...]} from its
validator, where STATE is one of PASS / BLOCKED / REVIEW_REQUIRED / UNKNOWN with
fail-closed precedence BLOCKED > UNKNOWN > REVIEW_REQUIRED > PASS. PASS is only
reachable when the bound bridge report itself validates PASS and zero
contradictions exist; PASS still grants nothing.
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


# --- Constants -----------------------------------------------------------------------

EVIDENCE_SCHEMA_VERSION = "0174br-v1"
HASH_ALGORITHM = "canonical_json_sha256"

READINESS_ALIGNMENT_SCHEMA = "scd_compiler_v2_bridge_publish_readiness_alignment.schema.json"
REDACTED_AUDIT_ALIGNMENT_SCHEMA = "scd_compiler_v2_bridge_redacted_audit_alignment.schema.json"

# Symbolic, non-executable mode literals. These describe stance only; they never
# enable behavior and contain no runtime/dispatch/scheduler vocabulary.
READINESS_ALIGNMENT_MODE = "evidence_only_no_readiness_grant"
AUDIT_ALIGNMENT_MODE = "future_only_redacted_evidence_no_event_creation"
AUDIT_EVENT_TYPE_REQUESTED = "future_bridge_report_alignment_evidence"

VALID_STATES = (PASS, BLOCKED, REVIEW_REQUIRED, UNKNOWN)

# Module-level documentation tables (also asserted by tests). Individual objects
# only carry the subset that applies to them; checking an absent flag is a no-op
# because _value returns None (which is not True).
REQUIRED_FALSE_FLAGS = (
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
    "readiness_granted",
    "audit_event_created",
    "audit_allowlist_modified",
)

REQUIRED_TRUE_FLAGS = (
    "local_only",
    "evidence_only",
    "non_executable",
    "manual_review_required",
    "bridge_report_bound",
    "redacted_safe",
)

# Per-object flag tables (fail closed).
READINESS_REQUIRED_FALSE_FLAGS = (
    "readiness_granted",
    "publish_ready",
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
)
READINESS_REQUIRED_TRUE_FLAGS = (
    "bridge_report_bound",
    "local_only",
    "evidence_only",
    "non_executable",
    "manual_review_required",
    "redacted_safe",
)

AUDIT_REQUIRED_FALSE_FLAGS = (
    "audit_event_created",
    "audit_allowlist_modified",
    "audit_event_type_registered_now",
    "credential_values_present",
    "token_values_present",
    "raw_vendor_payload_present",
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
)
AUDIT_REQUIRED_TRUE_FLAGS = (
    "bridge_report_bound",
    "local_only",
    "evidence_only",
    "non_executable",
    "manual_review_required",
    "redacted_safe",
    "secrets_redacted",
)


# --- Shared helpers ------------------------------------------------------------------

def _schema_state(packet, schema_name):
    ok, message = _schema_ok(packet, schema_name)
    if ok:
        return []
    return [f"schema:{message}"]


def _bridge_state_reasons(state):
    """Translate the bound bridge report's four-state result into reason buckets.

    BLOCKED -> blocked, UNKNOWN -> unknown, REVIEW_REQUIRED -> review,
    PASS -> nothing, anything else -> unknown (cannot establish lineage state).
    """
    blocked, review, unknown = [], [], []
    if state == BLOCKED:
        blocked.append("bound_bridge_report_blocked")
    elif state == UNKNOWN:
        unknown.append("bound_bridge_report_unknown")
    elif state == REVIEW_REQUIRED:
        review.append("bound_bridge_report_review_required")
    elif state != PASS:
        unknown.append(f"bound_bridge_report_state_invalid:{state}")
    return blocked, review, unknown


def derive_bridge_report_hash(bridge_report):
    """Deterministic canonical hash over the bridge report object.

    Pure, local: reuses the shared canonical_json_sha256 helper (sorted keys,
    compact separators). Identical reports hash identically; any change to the
    report changes the hash. No payload re-derivation, no I/O, no network.
    """
    return canonical_json_sha256(bridge_report)


def _lineage_fields(bridge_report, bridge_report_state, bridge_report_hash):
    return {
        "bridge_report_id": _value(bridge_report, "bridge_report_id", ""),
        "bridge_report_hash": bridge_report_hash,
        "compiler_output_id": _value(bridge_report, "compiler_output_id", ""),
        "compile_report_id": _value(bridge_report, "compile_report_id", ""),
        "payload_hash_manifest_id": _value(bridge_report, "payload_hash_manifest_id", ""),
        "bridge_report_state": bridge_report_state,
    }


def _finalize(packet, core_fn):
    blocked, review, unknown = core_fn(packet)
    result = _state(blocked, review, unknown)
    packet["validation_state"] = result["validation_state"]
    packet["blocked_reasons"] = result["reasons"] if result["validation_state"] == BLOCKED else []
    return packet


# --- 1. Bridge -> publish-readiness evidence alignment -------------------------------

def _readiness_core(packet):
    blocked, review, unknown = [], [], []

    for flag in READINESS_REQUIRED_FALSE_FLAGS:
        if _value(packet, flag) is True:
            blocked.append(f"{flag}_must_be_false")
    for flag in READINESS_REQUIRED_TRUE_FLAGS:
        if _value(packet, flag) is not True:
            blocked.append(f"{flag}_must_be_true")

    if _value(packet, "readiness_alignment_mode") != READINESS_ALIGNMENT_MODE:
        blocked.append("readiness_alignment_mode_must_be_evidence_only_no_readiness_grant")

    if not _value(packet, "bridge_report_id"):
        unknown.append("bridge_report_id_missing")
    if not _value(packet, "bridge_report_hash"):
        unknown.append("bridge_report_hash_missing")

    b, r, u = _bridge_state_reasons(_value(packet, "bridge_report_state"))
    blocked += b
    review += r
    unknown += u

    blocked.extend(_unsafe_runtime_hits(packet))
    blocked.extend(_secret_hits(packet))
    return blocked, review, unknown


def build_compiler_v2_bridge_publish_readiness_alignment(bridge_report):
    """Bind the accepted bridge report to publish-readiness evidence (no grant).

    The bound bridge report is validated with its authoritative validator; the
    resulting four-state is propagated (BLOCKED/UNKNOWN/REVIEW_REQUIRED/PASS).
    Even on PASS, readiness_granted/publish_ready/public_ready and every
    live/dispatch/API/credential/scheduler/posting flag stay false. Never
    mutates the input bridge report.
    """
    bridge_state = validate_compiler_v2_approval_dispatch_bridge_report(bridge_report)["validation_state"]
    bridge_hash = derive_bridge_report_hash(bridge_report)
    lineage = _lineage_fields(bridge_report, bridge_state, bridge_hash)

    packet = {
        "schema_version": EVIDENCE_SCHEMA_VERSION,
        "readiness_alignment_id": f"brpra_{lineage['bridge_report_id']}" if lineage["bridge_report_id"] else "brpra_unknown",
        "bridge_report_id": lineage["bridge_report_id"],
        "bridge_report_hash": lineage["bridge_report_hash"],
        "compiler_output_id": lineage["compiler_output_id"],
        "compile_report_id": lineage["compile_report_id"],
        "payload_hash_manifest_id": lineage["payload_hash_manifest_id"],
        "bridge_report_state": lineage["bridge_report_state"],
        "bridge_report_bound": True,
        "local_only": True,
        "evidence_only": True,
        "non_executable": True,
        "manual_review_required": True,
        "redacted_safe": True,
        "readiness_alignment_mode": READINESS_ALIGNMENT_MODE,
        "readiness_granted": False,
        "publish_ready": False,
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
        "validation_state": bridge_state,
        "blocked_reasons": [],
    }
    return _finalize(packet, _readiness_core)


def validate_compiler_v2_bridge_publish_readiness_alignment(packet):
    """Validate a bridge->publish-readiness evidence alignment packet, fail-closed.

    BLOCKED on schema failure, any required-false flag true, any required-true
    flag not true, a wrong alignment mode, runtime/secret hits, a BLOCKED bound
    bridge state, or a declared PASS that contradicts a non-PASS computed state.
    UNKNOWN propagates from an UNKNOWN bound bridge state or missing lineage;
    REVIEW_REQUIRED propagates from a REVIEW_REQUIRED bound bridge state.
    """
    blocked = _schema_state(packet, READINESS_ALIGNMENT_SCHEMA)
    core_blocked, review, unknown = _readiness_core(packet)
    blocked += core_blocked
    return _apply_declared_state(packet, _state(blocked, review, unknown))


# --- 2. Bridge -> redacted-audit evidence alignment ----------------------------------

def _redacted_audit_core(packet):
    blocked, review, unknown = [], [], []

    for flag in AUDIT_REQUIRED_FALSE_FLAGS:
        if _value(packet, flag) is True:
            blocked.append(f"{flag}_must_be_false")
    for flag in AUDIT_REQUIRED_TRUE_FLAGS:
        if _value(packet, flag) is not True:
            blocked.append(f"{flag}_must_be_true")

    if _value(packet, "audit_alignment_mode") != AUDIT_ALIGNMENT_MODE:
        blocked.append("audit_alignment_mode_must_be_future_only_redacted_evidence_no_event_creation")
    if _value(packet, "audit_event_type_requested") != AUDIT_EVENT_TYPE_REQUESTED:
        blocked.append("audit_event_type_requested_must_be_future_bridge_report_alignment_evidence")

    if not _value(packet, "bridge_report_id"):
        unknown.append("bridge_report_id_missing")
    if not _value(packet, "bridge_report_hash"):
        unknown.append("bridge_report_hash_missing")

    b, r, u = _bridge_state_reasons(_value(packet, "bridge_report_state"))
    blocked += b
    review += r
    unknown += u

    blocked.extend(_unsafe_runtime_hits(packet))
    blocked.extend(_secret_hits(packet))
    return blocked, review, unknown


def build_compiler_v2_bridge_redacted_audit_alignment(bridge_report):
    """Bind the accepted bridge report to FUTURE redacted-audit evidence.

    Represents how the bridge could later appear as redaction-safe audit
    evidence WITHOUT creating a real audit event and WITHOUT touching any audit
    event allow-list. audit_event_created / audit_allowlist_modified /
    audit_event_type_registered_now stay false; the requested event type is a
    future-only label, not a registered live event. Never mutates the input.
    """
    bridge_state = validate_compiler_v2_approval_dispatch_bridge_report(bridge_report)["validation_state"]
    bridge_hash = derive_bridge_report_hash(bridge_report)
    lineage = _lineage_fields(bridge_report, bridge_state, bridge_hash)

    packet = {
        "schema_version": EVIDENCE_SCHEMA_VERSION,
        "audit_alignment_id": f"brraa_{lineage['bridge_report_id']}" if lineage["bridge_report_id"] else "brraa_unknown",
        "bridge_report_id": lineage["bridge_report_id"],
        "bridge_report_hash": lineage["bridge_report_hash"],
        "compiler_output_id": lineage["compiler_output_id"],
        "compile_report_id": lineage["compile_report_id"],
        "payload_hash_manifest_id": lineage["payload_hash_manifest_id"],
        "bridge_report_state": lineage["bridge_report_state"],
        "bridge_report_bound": True,
        "local_only": True,
        "evidence_only": True,
        "non_executable": True,
        "manual_review_required": True,
        "redacted_safe": True,
        "audit_alignment_mode": AUDIT_ALIGNMENT_MODE,
        "audit_event_created": False,
        "audit_allowlist_modified": False,
        "audit_event_type_requested": AUDIT_EVENT_TYPE_REQUESTED,
        "audit_event_type_registered_now": False,
        "secrets_redacted": True,
        "credential_values_present": False,
        "token_values_present": False,
        "raw_vendor_payload_present": False,
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
        "validation_state": bridge_state,
        "blocked_reasons": [],
    }
    return _finalize(packet, _redacted_audit_core)


def validate_compiler_v2_bridge_redacted_audit_alignment(packet):
    """Validate a bridge->redacted-audit evidence alignment packet, fail-closed.

    BLOCKED on schema failure, any required-false flag true (including
    audit_event_created / audit_allowlist_modified / audit_event_type_registered_now
    and credential/token/raw-vendor presence), any required-true flag not true,
    wrong alignment mode or requested event-type label, runtime/secret hits, a
    BLOCKED bound bridge state, or a declared PASS contradicting a non-PASS
    computed state. UNKNOWN / REVIEW_REQUIRED propagate from the bound bridge
    state. PASS still creates no audit event.
    """
    blocked = _schema_state(packet, REDACTED_AUDIT_ALIGNMENT_SCHEMA)
    core_blocked, review, unknown = _redacted_audit_core(packet)
    blocked += core_blocked
    return _apply_declared_state(packet, _state(blocked, review, unknown))


# Registry of evidence-alignment validators, keyed for data-driven hostile tests.
COMPILER_V2_BRIDGE_PUBLISH_EVIDENCE_VALIDATORS = {
    "compiler_v2_bridge_publish_readiness_alignment": validate_compiler_v2_bridge_publish_readiness_alignment,
    "compiler_v2_bridge_redacted_audit_alignment": validate_compiler_v2_bridge_redacted_audit_alignment,
}
