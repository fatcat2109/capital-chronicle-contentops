"""Operator replay console read-only view-model validators (SCD, 0174AV).

Local-only, deterministic, fail-closed. This module defines the CONTRACT and
VALIDATION for projecting a pipeline replay report into a screenshot-ready,
evidence-grade, DISPLAY-ONLY operator console packet.

This is NOT UI implementation. No HTML/CSS/JS, no browser, no screenshots, no
network, no providers, no credentials, no platform APIs, no scheduler, no live
dispatch. The projection helper only transforms supplied local dictionaries
into read-only view-model dictionaries.

Domain objects validated here:

    SCDOperatorReplayConsoleInput
    SCDReplayStageStatusChip
    SCDOperatorReplayConsoleViewModel
    SCDReplayEvidenceBundle
    SCDCopySafeExportBundle

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

# allow_* flags on the console input that must all be false.
FORBIDDEN_ALLOW_FLAGS = (
    "allow_provider_api",
    "allow_network",
    "allow_credentials",
    "allow_platform_api",
    "allow_live_dispatch",
    "allow_browser_automation",
    "allow_ui_runtime_execution",
)

# Readiness flags that must never be true on any 0174AV object.
FORBIDDEN_READY_FLAGS = ("public_ready", "live_ready", "executable_dispatch", "live_eligibility")

# Status -> severity mapping (deterministic).
STATUS_SEVERITY = {
    PASS: "pass",
    BLOCKED: "blocked",
    REVIEW_REQUIRED: "review",
    UNKNOWN: "unknown",
}


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


def _common_display_blocks(payload):
    """Shared invariants for display-only objects with the standard flag set."""
    blocked = []
    blocked += _ready_flag_blocks(payload)
    blocked += _scan_secrets(payload)
    blocked += _scan_all_strings(payload)
    if "manual_publish_only" in payload and payload.get("manual_publish_only") is not True:
        blocked.append("manual_publish_only must be true")
    if "mock_only" in payload and payload.get("mock_only") is not True:
        blocked.append("mock_only must be true")
    if payload.get("api_gate_required"):
        blocked.append("api_gate_required must be false")
    if "action_enabled" in payload and payload.get("action_enabled"):
        blocked.append("action_enabled must be false")
    if "display_only" in payload and payload.get("display_only") is not True:
        blocked.append("display_only must be true")
    return blocked


def validate_operator_replay_console_input(payload):
    ok, msg = _schema_ok(payload, "scd_operator_replay_console_input.schema.json")
    if not ok:
        return {"validation_state": BLOCKED, "reasons": [f"schema: {msg}"]}

    blocked, review, unknown = [], [], []

    blocked += _scan_secrets(payload)
    blocked += _scan_all_strings(payload)

    if payload.get("expected_manual_publish_only") is not True:
        blocked.append("expected_manual_publish_only must be true")
    if payload.get("expected_mock_only") is not True:
        blocked.append("expected_mock_only must be true")

    for flag in FORBIDDEN_ALLOW_FLAGS:
        if payload.get(flag):
            blocked.append(f"{flag} must be false")

    if not payload.get("pipeline_replay_report_id"):
        unknown.append("missing pipeline_replay_report_id")
    if not payload.get("evidence_manifest_id"):
        review.append("missing evidence_manifest_id; confirm evidence lineage")

    return _result(blocked, review, unknown)


def validate_replay_stage_status_chip(payload):
    ok, msg = _schema_ok(payload, "scd_replay_stage_status_chip.schema.json")
    if not ok:
        return {"validation_state": BLOCKED, "reasons": [f"schema: {msg}"]}

    blocked, review, unknown = [], [], []

    blocked += _common_display_blocks(payload)

    status = payload.get("status")
    severity = payload.get("severity")
    if status in STATUS_SEVERITY and severity != STATUS_SEVERITY[status]:
        # neutral is tolerated only for non-authoritative placeholders
        if not (severity == "neutral" and status == UNKNOWN):
            blocked.append(f"severity {severity} does not match status {status}")

    # A BLOCKED stage must be marked as a blocking stage.
    if status == BLOCKED and payload.get("is_blocking_stage") is not True:
        blocked.append("BLOCKED stage chip must set is_blocking_stage true")

    if not payload.get("packet_ref"):
        unknown.append("stage chip missing packet_ref")

    return _result(blocked, review, unknown)


def validate_operator_replay_console_view_model(payload):
    ok, msg = _schema_ok(payload, "scd_operator_replay_console_view_model.schema.json")
    if not ok:
        return {"validation_state": BLOCKED, "reasons": [f"schema: {msg}"]}

    blocked, review, unknown = [], [], []

    blocked += _common_display_blocks(payload)

    chips = payload.get("stage_status_chips", []) or []
    statuses = [c.get("status") for c in chips]
    headline = payload.get("headline_status")

    # Fail-closed precedence: BLOCKED > UNKNOWN > REVIEW_REQUIRED > PASS.
    if BLOCKED in statuses:
        expected = BLOCKED
    elif UNKNOWN in statuses:
        expected = UNKNOWN
    elif REVIEW_REQUIRED in statuses:
        expected = REVIEW_REQUIRED
    elif statuses:
        expected = PASS
    else:
        expected = None

    if headline == PASS and expected != PASS:
        blocked.append(f"headline PASS contradicts chip roll-up (expected {expected})")
    if expected == BLOCKED and headline != BLOCKED:
        blocked.append("a chip is BLOCKED; headline must be BLOCKED")

    # Current-vs-historical truth must be explicit.
    cvh = payload.get("current_vs_historical_truth", {})
    if cvh.get("current_state_is_authoritative") is not True:
        blocked.append("current_state_is_authoritative must be true")
    if cvh.get("stale_or_historical_refs_separated") is not True:
        blocked.append("stale_or_historical_refs_separated must be true")
    if not cvh.get("current_replay_report_ref"):
        unknown.append("missing current_replay_report_ref")

    # PASS view model requires evidence + copy-safe export refs.
    if headline == PASS:
        if not payload.get("evidence_bundle_ref"):
            blocked.append("PASS view model requires evidence_bundle_ref")
        if not payload.get("copy_safe_export_bundle_ref"):
            blocked.append("PASS view model requires copy_safe_export_bundle_ref")

    if not chips:
        unknown.append("no stage_status_chips")

    # Surface non-blocking roll-ups when otherwise clean.
    if not blocked:
        if expected == UNKNOWN:
            unknown.append("a chip is UNKNOWN; headline should be UNKNOWN")
        elif expected == REVIEW_REQUIRED:
            review.append("a chip is REVIEW_REQUIRED; headline should be REVIEW_REQUIRED")

    return _result(blocked, review, unknown)


def validate_replay_evidence_bundle(payload):
    ok, msg = _schema_ok(payload, "scd_replay_evidence_bundle.schema.json")
    if not ok:
        return {"validation_state": BLOCKED, "reasons": [f"schema: {msg}"]}

    blocked, review, unknown = [], [], []

    blocked += _common_display_blocks(payload)

    # Redaction proof must affirmatively assert safety.
    for flag in ("secrets_redacted", "tokens_absent", "credentials_absent", "endpoints_absent", "raw_payloads_redacted"):
        if payload.get(flag) is not True:
            blocked.append(f"{flag} must be true")

    if not payload.get("protected_path_statement"):
        blocked.append("protected_path_statement must be present")

    # Completeness: incomplete -> review; missing refs -> review/unknown.
    if payload.get("evidence_complete") is not True:
        review.append("evidence_complete is not true")
    if payload.get("missing_evidence_refs"):
        review.append("missing_evidence_refs is non-empty")
    if not payload.get("pipeline_replay_report_id"):
        unknown.append("missing pipeline_replay_report_id; evidence lineage unknown")
    if not payload.get("stage_packet_hash_refs"):
        unknown.append("no stage_packet_hash_refs")

    return _result(blocked, review, unknown)


def validate_copy_safe_export_bundle(payload):
    ok, msg = _schema_ok(payload, "scd_copy_safe_export_bundle.schema.json")
    if not ok:
        return {"validation_state": BLOCKED, "reasons": [f"schema: {msg}"]}

    blocked, review, unknown = [], [], []

    blocked += _common_display_blocks(payload)

    # Contains-* flags must all be false.
    for flag in (
        "contains_credentials",
        "contains_tokens",
        "contains_platform_endpoints",
        "contains_raw_secret_material",
        "contains_unredacted_operator_identity",
        "contains_live_dispatch_instruction",
        "contains_public_ready_claim",
    ):
        if payload.get(flag):
            blocked.append(f"{flag} must be false")

    # Required content guarantees.
    for flag in (
        "manual_publish_only_notice_included",
        "limitations_included",
        "citations_or_evidence_refs_included",
        "financial_advice_absent",
        "signal_language_absent",
    ):
        if payload.get(flag) is not True:
            blocked.append(f"{flag} must be true")

    if not payload.get("console_input_id"):
        unknown.append("missing console_input_id; export lineage unknown")

    return _result(blocked, review, unknown)


# --- Deterministic local projection helpers ------------------------------------------

def build_stage_status_chips(stage_results, console_input_id="cin_unknown"):
    """Project replay-report stage_results into read-only status chips.

    Invents nothing: copies stage_name/result/reasons from the supplied list and
    derives only deterministic display fields (severity, is_blocking_stage).
    """
    chips = []
    for idx, sr in enumerate(stage_results or []):
        status = sr.get("result", UNKNOWN)
        chips.append({
            "schema_version": "1.0",
            "stage_chip_id": f"chip_{idx}_{sr.get('stage_name', 'unknown')}",
            "console_input_id": console_input_id,
            "stage_name": sr.get("stage_name", "unknown"),
            "stage_order_index": idx,
            "display_label": sr.get("stage_name", "unknown"),
            "status": status,
            "severity": STATUS_SEVERITY.get(status, "neutral"),
            "status_text": status,
            "reason_summary": "; ".join(sr.get("reasons", []) or []),
            "evidence_ref": "",
            "packet_ref": sr.get("stage_name", "unknown"),
            "packet_hash_ref": "",
            "is_current_stage": False,
            "is_blocking_stage": status == BLOCKED,
            "action_enabled": False,
            "action_label": "",
            "manual_publish_only": True,
            "mock_only": True,
            "public_ready": False,
            "live_ready": False,
            "executable_dispatch": False,
            "api_gate_required": False,
            "validation_state": PASS,
        })
    return chips


def project_replay_console_view_model(console_input, replay_report, safety_summary, evidence_manifest):
    """Deterministically project supplied packets into a read-only view model.

    Invents nothing: derives the headline from the replay report's stage roll-up
    and copies refs from the supplied packets. No URLs, credentials, endpoints,
    tokens, platform actions, or UI runtime actions are created.
    Returns {"stage_status_chips": [...], "headline_status": <STATE>, "safety_counters": {...}}.
    """
    stage_results = replay_report.get("stage_results", []) or []
    cin_id = console_input.get("console_input_id", "cin_unknown")
    chips = build_stage_status_chips(stage_results, cin_id)
    statuses = [c["status"] for c in chips]

    if BLOCKED in statuses:
        headline = BLOCKED
    elif UNKNOWN in statuses:
        headline = UNKNOWN
    elif REVIEW_REQUIRED in statuses:
        headline = REVIEW_REQUIRED
    elif statuses:
        headline = PASS
    else:
        headline = UNKNOWN

    counters = {
        "pass_count": statuses.count(PASS),
        "blocked_count": statuses.count(BLOCKED),
        "review_required_count": statuses.count(REVIEW_REQUIRED),
        "unknown_count": statuses.count(UNKNOWN),
        "total_stages": len(statuses),
    }
    return {
        "stage_status_chips": chips,
        "headline_status": headline,
        "safety_counters": counters,
    }


# Registry of operator-replay-console validators, in choreography order.
OPERATOR_REPLAY_CONSOLE_VALIDATORS = {
    "operator_replay_console_input": validate_operator_replay_console_input,
    "replay_stage_status_chip": validate_replay_stage_status_chip,
    "operator_replay_console_view_model": validate_operator_replay_console_view_model,
    "replay_evidence_bundle": validate_replay_evidence_bundle,
    "copy_safe_export_bundle": validate_copy_safe_export_bundle,
}
