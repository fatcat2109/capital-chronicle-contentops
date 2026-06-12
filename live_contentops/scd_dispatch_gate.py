"""Approval ledger and one-button supervised dispatch gate validators (SCD, 0174AS).

Local-only, deterministic, fail-closed. This module defines the CONTRACT and
VALIDATION for binding approved content, compiled platform payloads, an operator
decision, immutable hashes, and a MOCK-ONLY dispatch packet.

It NEVER connects to a platform, never calls a provider/LLM/network/API, never
uses a Telegram bot / sendMessage / webhook / OAuth, never reads credentials or
env, never schedules, and never enables live or public publishing.

Domain objects validated here:

    SCDOperatorDecisionPacket
    SCDApprovalLedgerEntry
    SCDDispatchFreezeManifest
    SCDOneButtonDispatchGateRequest
    SCDOneButtonDispatchGateResult

Plus a deterministic local hash helper, canonical_json_sha256(), that uses only
json + hashlib over canonical (sorted-key) JSON. No I/O, no network.

Validators return {"validation_state": <STATE>, "reasons": [...]}.
"""
import hashlib
import json

from live_contentops.scd_domain_model import (
    PASS,
    BLOCKED,
    REVIEW_REQUIRED,
    UNKNOWN,
    FORBIDDEN_LANGUAGE,
    _schema_ok,
    _find_language,
    _scan_secrets,
    _result,
)
from live_contentops.scd_editorial_workbench import (
    INVENTED_AUTHORITY_PATTERNS,
    INVENTED_METRIC_PATTERNS,
)
from live_contentops.scd_platform_payload_compiler import TELEGRAM_API_PATTERNS

# Network / OAuth / webhook implication patterns -> BLOCKED.
NETWORK_API_PATTERNS = [
    r"\bapi[_-]?key\b", r"\baccess[_-]?token\b", r"\bbearer\b", r"\boauth\b",
    r"\bwebhook\b", r"\bclient[_-]?secret\b", r"https?://", r"\.post\(",
    r"\bchat_id\b", r"\bsendmessage\b",
]

# Flags that must never be true on any 0174AS object.
FORBIDDEN_TRUE_FLAGS = ("public_ready", "live_ready", "executable_dispatch", "live_eligibility")


def canonical_json_sha256(obj):
    """Deterministic SHA-256 over canonical JSON (sorted keys, no whitespace).

    Pure function: no I/O, no network. Identical objects with different key
    order produce the same hash.
    """
    canonical = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return "canonical_json_sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _scan(text, patterns):
    return _find_language(text, patterns)


def _all_unsafe_text(text):
    hits = []
    hits += [f"forbidden language: {h}" for h in _scan(text, FORBIDDEN_LANGUAGE)]
    hits += [f"invented authority: {h}" for h in _scan(text, INVENTED_AUTHORITY_PATTERNS)]
    hits += [f"invented metric: {h}" for h in _scan(text, INVENTED_METRIC_PATTERNS)]
    hits += [f"telegram/api implication: {h}" for h in _scan(text, TELEGRAM_API_PATTERNS)]
    hits += [f"network/api/oauth implication: {h}" for h in _scan(text, NETWORK_API_PATTERNS)]
    return hits


def _scan_all_strings(obj):
    """Collect every string (keys + values) and scan for unsafe/secret content."""
    found = []

    def walk(node):
        if isinstance(node, dict):
            for k, v in node.items():
                if isinstance(k, str):
                    found.extend(_all_unsafe_text(k))
                walk(v)
        elif isinstance(node, list):
            for item in node:
                walk(item)
        elif isinstance(node, str):
            found.extend(_all_unsafe_text(node))

    walk(obj)
    return found


def _forbidden_flags(payload):
    return [f"{flag} must be false" for flag in FORBIDDEN_TRUE_FLAGS if payload.get(flag)]


def validate_operator_decision_packet(payload):
    ok, msg = _schema_ok(payload, "scd_operator_decision_packet.schema.json")
    if not ok:
        return {"validation_state": BLOCKED, "reasons": [f"schema: {msg}"]}

    blocked, review, unknown = [], [], []

    blocked += _forbidden_flags(payload)
    blocked += _scan_secrets(payload)
    blocked += _scan_all_strings(payload)

    # Mandatory acknowledgements.
    for flag in (
        "manual_publish_only_acknowledged",
        "no_financial_advice_acknowledged",
        "no_live_dispatch_acknowledged",
        "approval_valid_for_mock_dispatch_only",
    ):
        if payload.get(flag) is not True:
            blocked.append(f"{flag} must be true")

    # Full operator attestation required to approve.
    att = payload.get("operator_attestation", {})
    decision = payload.get("decision_type")
    if decision == "approve_mock_dispatch":
        for flag in (
            "reviewed_content",
            "reviewed_citations",
            "reviewed_limitations",
            "reviewed_platform_payloads",
            "understands_manual_publish_only",
        ):
            if att.get(flag) is not True:
                blocked.append(f"attestation {flag} must be true to approve")
        if not payload.get("related_content_refs"):
            unknown.append("approve decision missing related_content_refs")

    if not payload.get("operator_id_ref"):
        unknown.append("operator_id_ref missing; decision lineage unknown")

    return _result(blocked, review, unknown)


def validate_approval_ledger_entry(payload):
    ok, msg = _schema_ok(payload, "scd_approval_ledger_entry.schema.json")
    if not ok:
        return {"validation_state": BLOCKED, "reasons": [f"schema: {msg}"]}

    blocked, review, unknown = [], [], []

    blocked += _forbidden_flags(payload)
    blocked += _scan_secrets(payload)
    blocked += _scan_all_strings(payload)

    # Append-only / immutable / redaction invariants.
    if payload.get("append_only") is not True:
        blocked.append("append_only must be true")
    if payload.get("immutable_after_write") is not True:
        blocked.append("immutable_after_write must be true")
    if payload.get("secrets_redacted") is not True:
        blocked.append("secrets_redacted must be true")

    # Hash-chain integrity: sequence > 1 requires a previous hash.
    seq = payload.get("ledger_sequence")
    prev = payload.get("previous_ledger_entry_hash")
    if isinstance(seq, int) and seq > 1 and not prev:
        unknown.append("ledger_sequence > 1 but previous_ledger_entry_hash missing")
    if isinstance(seq, int) and seq == 1 and prev:
        review.append("genesis entry (sequence 1) should have null previous hash")

    # Lineage completeness for an approved entry.
    state = payload.get("decision_state")
    if state == "approved_mock_only":
        for ref in ("operator_decision_id", "canonical_post_id", "compiler_output_id"):
            if not payload.get(ref):
                unknown.append(f"approved entry missing {ref}")
        if not payload.get("platform_payload_hash_refs"):
            unknown.append("approved entry missing platform_payload_hash_refs")
    if state == "blocked":
        blocked.append("ledger entry decision_state is blocked")

    return _result(blocked, review, unknown)


def validate_dispatch_freeze_manifest(payload):
    ok, msg = _schema_ok(payload, "scd_dispatch_freeze_manifest.schema.json")
    if not ok:
        return {"validation_state": BLOCKED, "reasons": [f"schema: {msg}"]}

    blocked, review, unknown = [], [], []

    blocked += _forbidden_flags(payload)
    blocked += _scan_secrets(payload)
    blocked += _scan_all_strings(payload)

    if payload.get("manual_publish_only") is not True:
        blocked.append("manual_publish_only must be true")
    if payload.get("freeze_algorithm") != "canonical_json_sha256":
        blocked.append("freeze_algorithm must be canonical_json_sha256")

    # Any mutation after freeze is a hard block.
    if payload.get("mutation_after_freeze_detected"):
        blocked.append("mutation_after_freeze_detected is true")

    # Incomplete freeze cannot pass.
    if payload.get("freeze_complete") is not True:
        review.append("freeze_complete is not true; manifest incomplete")

    # Required hash refs for a complete freeze.
    if payload.get("freeze_complete") is True:
        for h in ("canonical_post_hash", "approval_packet_hash", "operator_decision_hash", "ledger_entry_hash"):
            if not payload.get(h):
                unknown.append(f"complete freeze missing {h}")
        if not payload.get("platform_payload_hashes"):
            unknown.append("complete freeze missing platform_payload_hashes")

    return _result(blocked, review, unknown)


def validate_one_button_dispatch_gate_request(payload):
    ok, msg = _schema_ok(payload, "scd_one_button_dispatch_gate_request.schema.json")
    if not ok:
        return {"validation_state": BLOCKED, "reasons": [f"schema: {msg}"]}

    blocked, review, unknown = [], [], []

    blocked += _forbidden_flags(payload)
    blocked += _scan_secrets(payload)
    blocked += _scan_all_strings(payload)

    if payload.get("manual_publish_only") is not True:
        blocked.append("manual_publish_only must be true")

    pre = payload.get("precondition_summary", {})
    precondition_flags = [
        "content_pass",
        "editorial_pass_or_reviewed",
        "platform_compile_pass",
        "approval_packet_pass",
        "operator_approved",
        "freeze_manifest_complete",
        "kill_switch_clear_for_mock",
        "no_blocked_states",
    ]
    all_pre_pass = all(pre.get(f) is True for f in precondition_flags)

    # One-button may only be enabled when ALL preconditions pass.
    if payload.get("one_button_enabled") and not all_pre_pass:
        failing = [f for f in precondition_flags if pre.get(f) is not True]
        blocked.append(f"one_button_enabled while preconditions fail: {failing}")

    # If no_blocked_states is explicitly false, the request is blocked.
    if pre.get("no_blocked_states") is False:
        blocked.append("precondition no_blocked_states is false")

    # Lineage refs needed to bind the gate.
    if not payload.get("freeze_manifest_id") or not payload.get("approval_ledger_entry_id"):
        unknown.append("missing freeze_manifest_id or approval_ledger_entry_id")
    if not payload.get("operator_decision_id"):
        unknown.append("missing operator_decision_id")

    # Ambiguous-but-safe precondition -> review (when not enabling the button).
    if not all_pre_pass and not payload.get("one_button_enabled") and not blocked:
        missing = [f for f in precondition_flags if pre.get(f) is not True]
        review.append(f"preconditions incomplete (button disabled): {missing}")

    return _result(blocked, review, unknown)


def validate_one_button_dispatch_gate_result(payload):
    ok, msg = _schema_ok(payload, "scd_one_button_dispatch_gate_result.schema.json")
    if not ok:
        return {"validation_state": BLOCKED, "reasons": [f"schema: {msg}"]}

    blocked, review, unknown = [], [], []

    blocked += _forbidden_flags(payload)
    blocked += _scan_secrets(payload)
    blocked += _scan_all_strings(payload)

    if payload.get("manual_publish_only") is not True:
        blocked.append("manual_publish_only must be true")

    state = payload.get("result_state")
    # A "ready" result cannot coexist with any live/public/executable flag
    # (already covered by _forbidden_flags, but assert contract intent).
    ready_states = ("mock_dispatch_packet_ready", "manual_export_ready")
    if state in ready_states:
        if payload.get("dispatch_packet_ref") is None and state == "mock_dispatch_packet_ready":
            unknown.append("mock_dispatch ready but no dispatch_packet_ref")
        if not payload.get("frozen_hash_refs"):
            review.append("ready result without frozen_hash_refs")
    if state == "blocked" and payload.get("validation_state") != BLOCKED:
        blocked.append("result_state blocked but validation_state not BLOCKED")

    if not payload.get("gate_request_id"):
        unknown.append("missing gate_request_id; result lineage unknown")

    return _result(blocked, review, unknown)


def validate_gate_binding(gate_request, gate_result):
    """Cross-object: result cannot be 'ready' if the request is not PASS.

    Fail-closed: any non-PASS request forces the binding to fail, and live
    readiness is never granted.
    """
    req_res = validate_one_button_dispatch_gate_request(gate_request)
    res_res = validate_one_button_dispatch_gate_result(gate_result)
    ready = res_res["validation_state"] == PASS and req_res["validation_state"] == PASS
    reasons = []
    if req_res["validation_state"] != PASS:
        ready = False
        reasons.append(f"gate_request not PASS: {req_res['validation_state']}")
    if res_res["validation_state"] != PASS:
        ready = False
        reasons.append(f"gate_result not PASS: {res_res['validation_state']}")
    return {
        "mock_dispatch_ready": ready,
        "live_ready": False,
        "executable_dispatch": False,
        "request_result": req_res,
        "result_result": res_res,
        "reasons": reasons or ["ok"],
    }


# Registry of dispatch-gate validators, in choreography order.
DISPATCH_GATE_VALIDATORS = {
    "operator_decision_packet": validate_operator_decision_packet,
    "approval_ledger_entry": validate_approval_ledger_entry,
    "dispatch_freeze_manifest": validate_dispatch_freeze_manifest,
    "one_button_dispatch_gate_request": validate_one_button_dispatch_gate_request,
    "one_button_dispatch_gate_result": validate_one_button_dispatch_gate_result,
}
