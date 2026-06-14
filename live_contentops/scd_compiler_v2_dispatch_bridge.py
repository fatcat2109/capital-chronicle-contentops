"""Compiler v2 -> approval/dispatch boundary bridge validators (SCD, 0174BP).

Local-only, deterministic, fail-closed. This is a NEW, parallel reconciliation
module. It does NOT replace or edit the existing 0174AS dispatch gate
(scd_dispatch_gate.py) or the 0174AR/0174BN compilers; it only reconciles a
verified platform payload compiler v2 compile report against two candidate
control objects:

    1. an approval ledger candidate entry (SCDApprovalLedgerEntry), and
    2. a dispatch-gate candidate (SCDOneButtonDispatchGateRequest +
       SCDDispatchFreezeManifest).

The bridge re-derives per-platform payload hashes locally from the compiler v2
output using deterministic canonical JSON (canonical_json_sha256, reused from
the dispatch gate module), and compares those derived hashes against the hash
refs the candidate control objects assert. Any mismatch fails closed (BLOCKED).
It also closes the historical trust gap where a dispatch gate could self-assert
`precondition_summary.platform_compile_pass = true` without any actual compiler
v2 report agreeing: the bridge BLOCKS a claimed compile pass that contradicts
the report's `final_recommendation`.

It NEVER connects to a platform, never calls a provider/LLM/network/API, never
reads credentials or environment, never schedules, and never enables live,
mock, or public dispatch. Forbidden-runtime and secret detectors are
single-sourced from the registry v2 module so detector literals are never
re-typed here, and the hash helper is single-sourced from the dispatch gate.

Domain object validated here:

    SCDCompilerV2DispatchBridgeResult

Validators return {"validation_state": <STATE>, "reasons": [...]}.
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
from live_contentops.scd_platform_payload_compiler_v2 import (
    validate_platform_payload_compile_report_v2,
)
# Single-source the canonical hash helper; importing is not editing.
from live_contentops.scd_dispatch_gate import canonical_json_sha256

BRIDGE_SCHEMA = "scd_compiler_v2_dispatch_bridge_result.schema.json"

# The only allowed bridge mode. No live/mock/dispatch execution mode exists.
ALLOWED_BRIDGE_MODE = "local_reconciliation_dry_run_only"

# Flags that must never be true on any bridge object (fail closed if true).
REQUIRED_FALSE_FLAGS_BRIDGE = (
    "public_ready",
    "live_eligibility",
    "live_ready",
    "dispatch_ready",
    "mock_dispatch_ready",
    "executable_dispatch",
    "live_api_enabled_now",
    "platform_api_allowed_now",
    "credential_read_allowed_now",
    "credentials_requested_now",
    "posting_enabled_now",
    "scheduler_enabled_now",
    "autonomous_replies_enabled_now",
    "dms_enabled_now",
    "scraping_enabled_now",
)

# The candidate decision state that is eligible for (mock-only) approval lineage.
APPROVED_MOCK_DECISION_STATE = "approved_mock_only"

# Reason/label-bearing keys whose string values legitimately carry control
# vocabulary (e.g. "dispatch", "mock"). They are skipped by the runtime-word
# scan to avoid false positives, but are NEVER skipped by the secret scan.
_RUNTIME_SCAN_SKIP_KEYS = (
    "reasons",
    "blocked_reasons",
    "review_reasons",
    "unknown_reasons",
    "requested_action",
    "one_button_label",
    "bridge_mode",
)


# --- Deterministic local hash derivation ---------------------------------------------

def derive_platform_payload_hashes_v2(compiler_output):
    """Re-derive per-platform payload hashes from a compiler v2 output packet.

    Pure, local, deterministic: canonical_json_sha256 over each payload object
    (sorted keys), in payload order. No network, no I/O, no credential or
    environment access, no external data. Returns a list of hash strings whose
    order matches compiler_output["platform_payloads"].
    """
    payloads = _value(compiler_output, "platform_payloads", []) or []
    return [canonical_json_sha256(payload) for payload in payloads]


def _hashes_match(derived, refs):
    """Order-independent multiset comparison of derived vs. asserted hashes."""
    return sorted(derived) == sorted(refs)


def _report_state_reasons(compile_report):
    """Map a compile report's validated state into bridge precedence buckets."""
    blocked, review, unknown = [], [], []
    state = validate_platform_payload_compile_report_v2(compile_report)["validation_state"]
    if state == BLOCKED:
        blocked.append("compile_report_blocked")
    elif state == UNKNOWN:
        unknown.append("compile_report_unknown")
    elif state == REVIEW_REQUIRED:
        review.append("compile_report_review_required")
    return state, blocked, review, unknown


# --- Approval-ledger reconciliation --------------------------------------------------

def reconcile_report_with_approval_ledger_v2(compile_report, approval_ledger_entry, compiler_output):
    """Reconcile a compiler v2 compile report against an approval ledger candidate.

    Fail-closed checks:
      * the compile report must itself validate (BLOCKED/UNKNOWN/REVIEW degrade);
      * the ledger's compiler_output_id/compile_report_id lineage must match the
        report (mismatch -> BLOCKED);
      * re-derived payload hashes must match the ledger's
        platform_payload_hash_refs (mismatch -> BLOCKED; missing -> UNKNOWN);
      * decision_state must be approved_mock_only (blocked -> BLOCKED, anything
        else -> REVIEW_REQUIRED);
      * no live/public/executable flag may be true; no secret may appear.

    Returns a sub-result dict (never mutates inputs).
    """
    report_state, blocked, review, unknown = _report_state_reasons(compile_report)

    report_output_id = _value(compile_report, "compiler_output_id")
    report_id = _value(compile_report, "compile_report_id")
    ledger_output_id = _value(approval_ledger_entry, "compiler_output_id")
    ledger_report_id = _value(approval_ledger_entry, "compile_report_id")

    if not ledger_output_id:
        unknown.append("approval_ledger_compiler_output_id_missing")
    elif ledger_output_id != report_output_id:
        blocked.append("approval_ledger_compiler_output_id_mismatch")
    if ledger_report_id and report_id and ledger_report_id != report_id:
        blocked.append("approval_ledger_compile_report_id_mismatch")

    decision_state = _value(approval_ledger_entry, "decision_state")
    if decision_state == "blocked":
        blocked.append("approval_ledger_decision_blocked")
    elif decision_state != APPROVED_MOCK_DECISION_STATE:
        review.append(f"approval_ledger_not_approved_mock_only:{decision_state}")

    derived = derive_platform_payload_hashes_v2(compiler_output)
    refs = _value(approval_ledger_entry, "platform_payload_hash_refs", []) or []
    hash_match = _hashes_match(derived, refs)
    if not refs:
        unknown.append("approval_ledger_no_payload_hash_refs")
    elif not hash_match:
        blocked.append("approval_ledger_payload_hash_mismatch")

    for flag in ("public_ready", "live_ready", "executable_dispatch"):
        if _value(approval_ledger_entry, flag) is True:
            blocked.append(f"approval_ledger_{flag}_must_be_false")

    blocked.extend(_unsafe_runtime_hits(approval_ledger_entry, skip_keys=_RUNTIME_SCAN_SKIP_KEYS))
    blocked.extend(_secret_hits(approval_ledger_entry))

    result = _state(blocked, review, unknown)
    return {
        "ledger_entry_id": _value(approval_ledger_entry, "ledger_entry_id", ""),
        "hash_match": bool(hash_match and refs),
        "derived_hash_count": len(derived),
        "ref_hash_count": len(refs),
        "lineage_matches_report": ledger_output_id == report_output_id,
        "result": result["validation_state"],
        "reasons": result["reasons"],
    }


# --- Dispatch-gate / freeze reconciliation -------------------------------------------

def reconcile_report_with_dispatch_gate_v2(compile_report, gate_request, freeze_manifest, compiler_output):
    """Reconcile a compiler v2 compile report against a dispatch-gate candidate.

    Fail-closed checks:
      * the compile report must itself validate (BLOCKED/UNKNOWN/REVIEW degrade);
      * a gate that self-asserts precondition_summary.platform_compile_pass=true
        while the report's final_recommendation is not PASS is BLOCKED (this is
        the core trust-gap closure);
      * re-derived payload hashes must match the freeze manifest's
        platform_payload_hashes (mismatch -> BLOCKED; missing -> UNKNOWN);
      * any mutation_after_freeze, non-manual freeze, or live/public/executable
        flag fails closed; no secret may appear.

    Returns a sub-result dict (never mutates inputs).
    """
    report_state, blocked, review, unknown = _report_state_reasons(compile_report)
    recommendation = _value(compile_report, "final_recommendation")

    pre = _value(gate_request, "precondition_summary", {}) or {}
    claimed_compile_pass = _value(pre, "platform_compile_pass")
    claim_consistent = True
    if claimed_compile_pass is True and recommendation != PASS:
        blocked.append(f"gate_claims_compile_pass_but_report_is:{recommendation}")
        claim_consistent = False
    if _value(pre, "no_blocked_states") is False:
        blocked.append("gate_precondition_no_blocked_states_is_false")

    derived = derive_platform_payload_hashes_v2(compiler_output)
    freeze_hashes = _value(freeze_manifest, "platform_payload_hashes", []) or []
    hash_match = _hashes_match(derived, freeze_hashes)
    if not freeze_hashes:
        unknown.append("freeze_manifest_no_payload_hashes")
    elif not hash_match:
        blocked.append("freeze_manifest_payload_hash_mismatch")

    if _value(freeze_manifest, "mutation_after_freeze_detected") is True:
        blocked.append("mutation_after_freeze_detected")
    if _value(freeze_manifest, "manual_publish_only") is not True:
        blocked.append("freeze_manual_publish_only_must_be_true")
    if _value(gate_request, "manual_publish_only") is not True:
        blocked.append("gate_request_manual_publish_only_must_be_true")

    for flag in ("public_ready", "live_ready", "executable_dispatch"):
        if _value(gate_request, flag) is True:
            blocked.append(f"gate_request_{flag}_must_be_false")
        if _value(freeze_manifest, flag) is True:
            blocked.append(f"freeze_{flag}_must_be_false")

    # The bridge never authorizes the button; an enabled button here is advisory
    # only and still cannot grant readiness.
    if _value(gate_request, "one_button_enabled") is True and recommendation != PASS:
        blocked.append("one_button_enabled_while_report_not_pass")

    blocked.extend(_unsafe_runtime_hits(gate_request, skip_keys=_RUNTIME_SCAN_SKIP_KEYS))
    blocked.extend(_unsafe_runtime_hits(freeze_manifest, skip_keys=_RUNTIME_SCAN_SKIP_KEYS))
    blocked.extend(_secret_hits(gate_request))
    blocked.extend(_secret_hits(freeze_manifest))

    result = _state(blocked, review, unknown)
    return {
        "gate_request_id": _value(gate_request, "gate_request_id", ""),
        "freeze_manifest_id": _value(freeze_manifest, "freeze_manifest_id", ""),
        "claimed_compile_pass": claimed_compile_pass is True,
        "report_recommendation": recommendation,
        "claim_consistent": claim_consistent,
        "hash_match": bool(hash_match and freeze_hashes),
        "derived_hash_count": len(derived),
        "ref_hash_count": len(freeze_hashes),
        "result": result["validation_state"],
        "reasons": result["reasons"],
    }


# --- Combined bridge builder ---------------------------------------------------------

def build_compiler_v2_dispatch_bridge_result(
    compile_report,
    compiler_output,
    approval_ledger_entry,
    gate_request,
    freeze_manifest,
):
    """Reconcile a compile report against BOTH candidate control objects.

    Rolls up the approval-ledger sub-result, the dispatch-gate sub-result, and
    the report's own state with fail-closed precedence
    (BLOCKED > UNKNOWN > REVIEW_REQUIRED > PASS). Every readiness flag is forced
    false and operator_review_required is forced true; the bridge can never
    grant mock, live, public, or dispatch readiness. The returned packet is
    built to validate through validate_compiler_v2_dispatch_bridge_result.
    """
    approval = reconcile_report_with_approval_ledger_v2(
        compile_report, approval_ledger_entry, compiler_output
    )
    dispatch = reconcile_report_with_dispatch_gate_v2(
        compile_report, gate_request, freeze_manifest, compiler_output
    )
    report_state = validate_platform_payload_compile_report_v2(compile_report)["validation_state"]

    final = _rollup([approval["result"], dispatch["result"], report_state])

    output_id = _value(compiler_output, "compiler_output_id", "")
    report_id = _value(compile_report, "compile_report_id", "")
    return {
        "schema_version": "0174bp-v1",
        "bridge_result_id": f"bridge_v2_{report_id}" if report_id else "bridge_v2_unknown",
        "bridge_mode": ALLOWED_BRIDGE_MODE,
        "compiler_output_id": output_id,
        "compile_report_id": report_id,
        "derived_platform_payload_hashes": derive_platform_payload_hashes_v2(compiler_output),
        "approval_reconciliation": approval,
        "dispatch_reconciliation": dispatch,
        "final_recommendation": final,
        "mock_dispatch_ready": False,
        "dispatch_ready": False,
        "live_ready": False,
        "executable_dispatch": False,
        "public_ready": False,
        "live_eligibility": False,
        "live_api_enabled_now": False,
        "platform_api_allowed_now": False,
        "credential_read_allowed_now": False,
        "credentials_requested_now": False,
        "posting_enabled_now": False,
        "scheduler_enabled_now": False,
        "autonomous_replies_enabled_now": False,
        "dms_enabled_now": False,
        "scraping_enabled_now": False,
        "operator_review_required": True,
        "validation_state": final,
        "blocked_reasons": sorted(set(approval["reasons"] + dispatch["reasons"])) if final == BLOCKED else [],
    }


# --- Validator -----------------------------------------------------------------------

def _schema_state_bridge(packet):
    ok, message = _schema_ok(packet, BRIDGE_SCHEMA)
    if ok:
        return []
    return [f"schema:{message}"]


def validate_compiler_v2_dispatch_bridge_result(packet):
    """Validate a bridge result packet, fail-closed.

    BLOCKED on schema failure, any forbidden readiness flag set true, a declared
    PASS that contradicts non-PASS sub-results, runtime/secret hits, or wrong
    bridge mode. UNKNOWN when lineage/sub-results are missing. REVIEW_REQUIRED
    when a sub-result requires review. PASS only when both sub-results PASS.
    """
    blocked = _schema_state_bridge(packet)
    review = []
    unknown = []

    if _value(packet, "bridge_mode") != ALLOWED_BRIDGE_MODE:
        blocked.append("bridge_mode_must_be_local_reconciliation_dry_run_only")
    if _value(packet, "operator_review_required") is not True:
        blocked.append("operator_review_required_must_be_true")

    for flag in REQUIRED_FALSE_FLAGS_BRIDGE:
        if _value(packet, flag) is True:
            blocked.append(f"{flag}_must_be_false")

    blocked.extend(_unsafe_runtime_hits(packet, skip_keys=_RUNTIME_SCAN_SKIP_KEYS))
    blocked.extend(_secret_hits(packet))

    approval = _value(packet, "approval_reconciliation", {}) or {}
    dispatch = _value(packet, "dispatch_reconciliation", {}) or {}
    if not approval:
        unknown.append("approval_reconciliation_missing")
    if not dispatch:
        unknown.append("dispatch_reconciliation_missing")
    if not _value(packet, "compiler_output_id"):
        unknown.append("compiler_output_id_missing")
    if not _value(packet, "compile_report_id"):
        unknown.append("compile_report_id_missing")

    sub_states = [_value(approval, "result"), _value(dispatch, "result")]
    final = _value(packet, "final_recommendation")
    if final not in (PASS, BLOCKED, REVIEW_REQUIRED, UNKNOWN):
        blocked.append(f"invalid_final_recommendation:{final}")

    if BLOCKED in sub_states:
        blocked.append("sub_reconciliation_blocked")
    if UNKNOWN in sub_states:
        unknown.append("sub_reconciliation_unknown")
    if REVIEW_REQUIRED in sub_states:
        review.append("sub_reconciliation_review_required")

    # A bridge cannot PASS unless both sub-reconciliations PASS.
    if final == PASS and any(s != PASS for s in sub_states):
        blocked.append("final_pass_requires_all_sub_results_pass")

    return _apply_declared_state(packet, _state(blocked, review, unknown))


# Registry of bridge validators, keyed for data-driven hostile tests.
COMPILER_V2_DISPATCH_BRIDGE_VALIDATORS = {
    "compiler_v2_dispatch_bridge_result": validate_compiler_v2_dispatch_bridge_result,
}
