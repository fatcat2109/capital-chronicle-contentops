"""Mock dispatch execution and redacted audit binding validators (SCD, 0174AT).

Local-only, deterministic, fail-closed. This module defines the CONTRACT and
VALIDATION for proving the end-to-end choreography can produce a MOCK-ONLY
dispatch record and audit evidence WITHOUT touching any real platform.

It NEVER connects to a platform, never calls a provider/LLM/network/API, never
uses a Telegram bot / sendMessage / webhook / OAuth, never reads credentials or
env, never schedules, never opens a browser, and never enables live or public
publishing or real dispatch.

Domain objects validated here:

    SCDMockDispatchExecutionRequest
    SCDMockDispatchExecutionRecord
    SCDManualExportPacket
    SCDRedactedAuditBindingPacket
    SCDMockDispatchRunReport

Plus deterministic local helpers that create MOCK-ONLY records and invent no
platform result, URL, credential, token, or endpoint.

Validators return {"validation_state": <STATE>, "reasons": [...]}.
"""
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
from live_contentops.scd_dispatch_gate import NETWORK_API_PATTERNS

# Capability-allow flags that must be false on the request.
FORBIDDEN_ALLOW_FLAGS = (
    "network_allowed",
    "credential_access_allowed",
    "platform_api_allowed",
    "live_execution_allowed",
)

# Capability-used flags that must be false on the record.
FORBIDDEN_USED_FLAGS = (
    "network_accessed",
    "credential_accessed",
    "platform_api_called",
    "telegram_bot_used",
    "webhook_used",
    "live_execution",
    "public_post_created",
)

# Readiness flags that must never be true on any 0174AT object.
FORBIDDEN_READY_FLAGS = ("public_ready", "live_ready", "executable_dispatch", "live_eligibility")


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


def _ready_flag_blocks(payload):
    return [f"{flag} must be false" for flag in FORBIDDEN_READY_FLAGS if payload.get(flag)]


def validate_mock_dispatch_execution_request(payload):
    ok, msg = _schema_ok(payload, "scd_mock_dispatch_execution_request.schema.json")
    if not ok:
        return {"validation_state": BLOCKED, "reasons": [f"schema: {msg}"]}

    blocked, review, unknown = [], [], []

    blocked += _ready_flag_blocks(payload)
    blocked += _scan_secrets(payload)
    blocked += _scan_all_strings(payload)

    # mock_only / manual_publish_only must be true.
    if payload.get("mock_only") is not True:
        blocked.append("mock_only must be true")
    if payload.get("manual_publish_only") is not True:
        blocked.append("manual_publish_only must be true")

    # Capability-allow flags must all be false.
    for flag in FORBIDDEN_ALLOW_FLAGS:
        if payload.get(flag):
            blocked.append(f"{flag} must be false")

    pre = payload.get("precondition_summary", {})
    # GateResult not PASS blocks execution.
    if pre.get("gate_result_pass") is False:
        blocked.append("gate_result_pass is false; cannot execute mock dispatch")
    if pre.get("no_blocked_states") is False:
        blocked.append("precondition no_blocked_states is false")
    if pre.get("dispatch_packet_not_live") is False:
        blocked.append("dispatch_packet_not_live is false")

    # Soft preconditions: false -> review (recoverable), not a hard block.
    for soft in ("freeze_manifest_complete", "approval_ledger_pass", "payload_hashes_present", "kill_switch_clear_for_mock"):
        if pre.get(soft) is False:
            review.append(f"soft precondition {soft} is false; operator review needed")

    # Missing upstream lineage refs -> UNKNOWN.
    for ref in ("gate_result_id", "dispatch_packet_id", "freeze_manifest_id", "approval_ledger_entry_id"):
        if not payload.get(ref):
            unknown.append(f"missing {ref}")
    if pre.get("payload_hashes_present") is True and not payload.get("frozen_payload_hash_refs"):
        unknown.append("payload_hashes_present asserted but frozen_payload_hash_refs empty")
    if not payload.get("frozen_payload_hash_refs"):
        unknown.append("frozen_payload_hash_refs missing")

    # Ambiguous-but-safe precondition -> review (when not blocked/unknown).
    precondition_flags = [
        "gate_result_pass",
        "freeze_manifest_complete",
        "approval_ledger_pass",
        "dispatch_packet_not_live",
        "payload_hashes_present",
        "kill_switch_clear_for_mock",
        "no_blocked_states",
    ]
    if any(pre.get(f) is None for f in precondition_flags) and not blocked:
        review.append("a precondition is ambiguous (None); operator review needed")

    return _result(blocked, review, unknown)


def validate_mock_dispatch_execution_record(payload):
    ok, msg = _schema_ok(payload, "scd_mock_dispatch_execution_record.schema.json")
    if not ok:
        return {"validation_state": BLOCKED, "reasons": [f"schema: {msg}"]}

    blocked, review, unknown = [], [], []

    blocked += _ready_flag_blocks(payload)
    blocked += _scan_secrets(payload)
    blocked += _scan_all_strings(payload)

    # Capability-used flags must all be false.
    for flag in FORBIDDEN_USED_FLAGS:
        if payload.get(flag):
            blocked.append(f"{flag} must be false")

    if payload.get("operator_review_required") is not True:
        blocked.append("operator_review_required must be true")

    state = payload.get("execution_state")
    if state == "blocked":
        blocked.append("execution_state is blocked")

    # Lineage / completeness.
    if not payload.get("mock_execution_request_id"):
        unknown.append("mock_execution_request_id missing; record lineage unknown")
    if state in ("mock_record_created", "manual_export_created"):
        if not payload.get("redacted_audit_event_ref"):
            unknown.append("created record missing redacted_audit_event_ref")
        if not payload.get("platform_results"):
            unknown.append("created record missing platform_results")
    if not payload.get("frozen_hash_refs"):
        review.append("record without frozen_hash_refs")

    return _result(blocked, review, unknown)


def validate_manual_export_packet(payload):
    ok, msg = _schema_ok(payload, "scd_manual_export_packet.schema.json")
    if not ok:
        return {"validation_state": BLOCKED, "reasons": [f"schema: {msg}"]}

    blocked, review, unknown = [], [], []

    blocked += _ready_flag_blocks(payload)
    blocked += _scan_secrets(payload)
    blocked += _scan_all_strings(payload)

    if payload.get("export_mode") != "manual_only":
        blocked.append("export_mode must be manual_only")

    # Export must not contain credentials / tokens / endpoints.
    for flag in ("export_contains_credentials", "export_contains_tokens", "export_contains_platform_endpoint"):
        if payload.get(flag):
            blocked.append(f"{flag} must be false")

    # Required content guarantees.
    for flag in (
        "limitations_included",
        "citations_included",
        "financial_advice_absent",
        "signal_language_absent",
        "manual_publish_only_notice_included",
    ):
        if payload.get(flag) is not True:
            blocked.append(f"{flag} must be true")

    if not payload.get("mock_execution_record_id"):
        unknown.append("mock_execution_record_id missing; export lineage unknown")
    if not payload.get("platform_payload_refs"):
        review.append("no platform_payload_refs; confirm export content")

    return _result(blocked, review, unknown)


def validate_redacted_audit_binding_packet(payload):
    ok, msg = _schema_ok(payload, "scd_redacted_audit_binding_packet.schema.json")
    if not ok:
        return {"validation_state": BLOCKED, "reasons": [f"schema: {msg}"]}

    blocked, review, unknown = [], [], []

    blocked += _scan_secrets(payload)
    blocked += _scan_all_strings(payload)

    # Capability-used flags must all be false.
    for flag in ("network_accessed", "credential_accessed", "platform_api_called", "webhook_used", "live_execution"):
        if payload.get(flag):
            blocked.append(f"{flag} must be false")

    # Redaction proof must affirmatively assert safety.
    proof = payload.get("redaction_proof", {})
    for flag in (
        "secrets_scanned",
        "tokens_absent",
        "credentials_absent",
        "endpoints_absent",
        "raw_payloads_redacted",
        "operator_identity_redacted_or_ref_only",
    ):
        if proof.get(flag) is not True:
            blocked.append(f"redaction_proof.{flag} must be true")

    if payload.get("audit_event_type") == "blocked_execution_attempt":
        # A blocked attempt is a valid audit record but never PASS-ready content.
        review.append("audit event records a blocked execution attempt")

    if not payload.get("redacted_audit_event_id") or not payload.get("mock_execution_record_id"):
        unknown.append("audit binding lineage incomplete")
    if not payload.get("related_packet_refs"):
        unknown.append("no related_packet_refs; binding lineage unknown")

    return _result(blocked, review, unknown)


def validate_mock_dispatch_run_report(payload):
    ok, msg = _schema_ok(payload, "scd_mock_dispatch_run_report.schema.json")
    if not ok:
        return {"validation_state": BLOCKED, "reasons": [f"schema: {msg}"]}

    blocked, review, unknown = [], [], []

    blocked += _ready_flag_blocks(payload)
    blocked += _scan_secrets(payload)
    blocked += _scan_all_strings(payload)

    if payload.get("manual_publish_only") is not True:
        blocked.append("manual_publish_only must be true")

    # api_gate_required true cannot final PASS.
    rec = payload.get("final_recommendation")
    if payload.get("api_gate_required") and rec == PASS:
        blocked.append("api_gate_required is true; final PASS not allowed")

    per_platform = payload.get("per_platform_mock_results", []) or []
    results = [r.get("result") for r in per_platform]

    # Fail-closed precedence: report cannot PASS unless every platform is PASS.
    if rec == PASS and any(r != PASS for r in results):
        blocked.append("final PASS requires all per-platform results to be PASS")
    if BLOCKED in results and rec == PASS:
        blocked.append("final PASS contradicts a BLOCKED per-platform result")

    if rec not in (PASS, BLOCKED, REVIEW_REQUIRED, UNKNOWN):
        blocked.append(f"invalid final_recommendation: {rec}")

    if not per_platform:
        unknown.append("no per_platform_mock_results")
    if not payload.get("mock_execution_request_id"):
        unknown.append("mock_execution_request_id missing; report lineage unknown")

    if rec == REVIEW_REQUIRED and not blocked:
        review.append("run report recommends operator review")

    return _result(blocked, review, unknown)


# --- Deterministic local mock helpers ------------------------------------------------

def create_mock_dispatch_record(request_packet, gate_result_packet):
    """Create a MOCK-ONLY execution record from a request + gate result.

    Invents nothing: no platform result, URL, credential, token, or endpoint.
    All capability-used flags are hard-coded false. Platform results are copied
    from supplied platform_targets as 'PASS' placeholders only when the gate
    result is already PASS; otherwise the record is marked blocked.
    """
    gate_pass = gate_result_packet.get("validation_state") == PASS
    targets = request_packet.get("platform_targets", []) or []
    state = "mock_record_created" if gate_pass else "blocked"
    platform_results = (
        [{"platform_id": p, "result": "PASS"} for p in targets] if gate_pass else []
    )
    return {
        "schema_version": "1.0",
        "mock_execution_record_id": "mer_" + request_packet.get("mock_execution_request_id", "unknown"),
        "mock_execution_request_id": request_packet.get("mock_execution_request_id", ""),
        "created_at": "1970-01-01T00:00:00Z",
        "execution_state": state,
        "platform_results": platform_results,
        "dispatch_packet_ref": request_packet.get("dispatch_packet_id", ""),
        "manual_export_packet_ref": "",
        "redacted_audit_event_ref": gate_result_packet.get("redacted_audit_event_ref", ""),
        "frozen_hash_refs": list(request_packet.get("frozen_payload_hash_refs", []) or []),
        "execution_mode": "mock_only",
        "network_accessed": False,
        "credential_accessed": False,
        "platform_api_called": False,
        "telegram_bot_used": False,
        "webhook_used": False,
        "live_execution": False,
        "public_post_created": False,
        "operator_review_required": True,
        "validation_state": "PASS" if gate_pass else "BLOCKED",
        "blocked_reasons": [] if gate_pass else ["gate result not PASS"],
    }


def create_manual_export_packet(record_packet, platform_payload_refs):
    """Create a MOCK-ONLY manual export packet. Invents no credentials/tokens."""
    return {
        "schema_version": "1.0",
        "manual_export_packet_id": "mep_" + record_packet.get("mock_execution_record_id", "unknown"),
        "mock_execution_record_id": record_packet.get("mock_execution_record_id", ""),
        "platform_payload_refs": list(platform_payload_refs or []),
        "platform_payload_hash_refs": list(record_packet.get("frozen_hash_refs", []) or []),
        "export_surfaces": ["local_json_packet", "operator_review_packet"],
        "export_mode": "manual_only",
        "export_contains_credentials": False,
        "export_contains_tokens": False,
        "export_contains_platform_endpoint": False,
        "limitations_included": True,
        "citations_included": True,
        "financial_advice_absent": True,
        "signal_language_absent": True,
        "manual_publish_only_notice_included": True,
        "public_ready": False,
        "live_ready": False,
        "executable_dispatch": False,
        "validation_state": "PASS",
        "blocked_reasons": [],
    }


def bind_redacted_audit_event(record_packet, audit_event_packet):
    """Bind a MOCK record to a redacted audit event. Asserts redaction proof."""
    return {
        "schema_version": "1.0",
        "audit_binding_id": "abp_" + record_packet.get("mock_execution_record_id", "unknown"),
        "mock_execution_record_id": record_packet.get("mock_execution_record_id", ""),
        "redacted_audit_event_id": audit_event_packet.get("audit_event_id", ""),
        "dispatch_packet_id": record_packet.get("dispatch_packet_ref", ""),
        "freeze_manifest_id": "",
        "approval_ledger_entry_id": "",
        "operator_decision_id": "",
        "audit_event_type": "mock_dispatch_created",
        "related_packet_refs": list(audit_event_packet.get("related_packet_refs", []) or []),
        "redaction_proof": {
            "secrets_scanned": True,
            "tokens_absent": True,
            "credentials_absent": True,
            "endpoints_absent": True,
            "raw_payloads_redacted": True,
            "operator_identity_redacted_or_ref_only": True,
        },
        "network_accessed": False,
        "credential_accessed": False,
        "platform_api_called": False,
        "webhook_used": False,
        "live_execution": False,
        "validation_state": "PASS",
        "blocked_reasons": [],
    }


# Registry of mock-dispatch validators, in choreography order.
MOCK_DISPATCH_VALIDATORS = {
    "mock_dispatch_execution_request": validate_mock_dispatch_execution_request,
    "mock_dispatch_execution_record": validate_mock_dispatch_execution_record,
    "manual_export_packet": validate_manual_export_packet,
    "redacted_audit_binding_packet": validate_redacted_audit_binding_packet,
    "mock_dispatch_run_report": validate_mock_dispatch_run_report,
}
