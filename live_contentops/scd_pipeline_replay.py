"""End-to-end mock pipeline replay orchestrator validators (SCD, 0174AU).

Local-only, deterministic, fail-closed. This module defines the CONTRACT and
VALIDATION for replaying the full SCD choreography (0174AP-0174AT) as one chain
while staying fail-closed.

It NEVER connects to a platform, never calls a provider/LLM/network/API, never
uses a Telegram bot / sendMessage / webhook / OAuth, never reads credentials or
env, never schedules, never opens a browser, and never creates a post or live
dispatch. The replay helper only validates supplied local dictionaries.

Domain objects validated here:

    SCDPipelineReplayInput
    SCDPipelineStageReplayResult
    SCDPipelineReplaySafetySummary
    SCDPipelineReplayEvidenceManifest
    SCDPipelineReplayReport

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

# Canonical, recognized pipeline stage order.
PIPELINE_STAGE_ORDER = [
    "content_intent",
    "editorial_workbench",
    "canonical_post_or_output",
    "platform_payload_compile",
    "approval_packet",
    "approval_ledger",
    "freeze_manifest",
    "one_button_gate",
    "mock_dispatch",
    "manual_export",
    "redacted_audit_binding",
    "mock_run_report",
]

# allow_* flags on the input that must all be false.
FORBIDDEN_ALLOW_FLAGS = (
    "allow_provider_api",
    "allow_network",
    "allow_credentials",
    "allow_platform_api",
    "allow_live_dispatch",
    "allow_browser_automation",
)

# Readiness flags that must never be true on any 0174AU object.
FORBIDDEN_READY_FLAGS = ("public_ready", "live_ready", "executable_dispatch", "live_eligibility")

# All no_* assertions required for a PASS safety summary.
SAFETY_ASSERTIONS = (
    "no_provider_api_used",
    "no_network_used",
    "no_credentials_accessed",
    "no_platform_api_called",
    "no_browser_automation_used",
    "no_scheduler_used",
    "no_live_dispatch_created",
    "no_public_post_created",
    "no_telegram_bot_used",
    "no_webhook_used",
    "no_financial_advice_detected",
    "no_signal_language_detected",
    "all_live_flags_false",
    "all_public_flags_false",
    "all_executable_flags_false",
)


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


def validate_pipeline_replay_input(payload):
    ok, msg = _schema_ok(payload, "scd_pipeline_replay_input.schema.json")
    if not ok:
        return {"validation_state": BLOCKED, "reasons": [f"schema: {msg}"]}

    blocked, review, unknown = [], [], []

    blocked += _scan_secrets(payload)
    blocked += _scan_all_strings(payload)

    if payload.get("replay_mode") not in ("mock_only", "dry_run_validation_only"):
        blocked.append("replay_mode must be mock_only or dry_run_validation_only")

    # All allow_* flags must be false.
    for flag in FORBIDDEN_ALLOW_FLAGS:
        if payload.get(flag):
            blocked.append(f"{flag} must be false")

    if payload.get("expected_manual_publish_only") is not True:
        blocked.append("expected_manual_publish_only must be true")
    if payload.get("expected_mock_only") is not True:
        blocked.append("expected_mock_only must be true")

    # Stage order must be recognized (subset of canonical order, same order).
    order = payload.get("stage_order", []) or []
    for stage in order:
        if stage not in PIPELINE_STAGE_ORDER:
            blocked.append(f"unrecognized stage in stage_order: {stage}")
    canonical_index = {s: i for i, s in enumerate(PIPELINE_STAGE_ORDER)}
    known = [s for s in order if s in canonical_index]
    if known != sorted(known, key=lambda s: canonical_index[s]):
        blocked.append("stage_order is not in canonical deterministic order")

    # Missing required stage packet refs -> UNKNOWN.
    if not payload.get("stage_packet_refs"):
        unknown.append("missing stage_packet_refs")
    if not order:
        unknown.append("missing stage_order")
    if payload.get("stage_packet_refs") and order and len(payload["stage_packet_refs"]) != len(order):
        review.append("stage_packet_refs count does not match stage_order count")

    return _result(blocked, review, unknown)


def validate_pipeline_stage_replay_result(payload):
    ok, msg = _schema_ok(payload, "scd_pipeline_stage_replay_result.schema.json")
    if not ok:
        return {"validation_state": BLOCKED, "reasons": [f"schema: {msg}"]}

    blocked, review, unknown = [], [], []

    blocked += _ready_flag_blocks(payload)
    blocked += _scan_secrets(payload)
    blocked += _scan_all_strings(payload)

    if payload.get("manual_publish_only") is not True:
        blocked.append("manual_publish_only must be true")
    if payload.get("mock_only") is not True:
        blocked.append("mock_only must be true")
    if payload.get("api_gate_required"):
        blocked.append("api_gate_required must be false")

    stage = payload.get("stage_name")
    if stage not in PIPELINE_STAGE_ORDER:
        blocked.append(f"unrecognized stage_name: {stage}")

    # The stage's own recorded validation_state drives roll-up downstream.
    state = payload.get("validation_state")
    if state == BLOCKED:
        blocked.append(f"stage {stage} validation_state is BLOCKED")
    elif state == UNKNOWN:
        unknown.append(f"stage {stage} validation_state is UNKNOWN")
    elif state == REVIEW_REQUIRED:
        review.append(f"stage {stage} validation_state is REVIEW_REQUIRED")

    if not payload.get("packet_ref"):
        unknown.append("stage missing packet_ref")

    return _result(blocked, review, unknown)


def validate_pipeline_replay_safety_summary(payload):
    ok, msg = _schema_ok(payload, "scd_pipeline_replay_safety_summary.schema.json")
    if not ok:
        return {"validation_state": BLOCKED, "reasons": [f"schema: {msg}"]}

    blocked, review, unknown = [], [], []

    blocked += _scan_secrets(payload)
    blocked += _scan_all_strings(payload)

    if payload.get("api_gate_required"):
        blocked.append("api_gate_required must be false")

    # Every no_* / all_*_false assertion must be true.
    for flag in SAFETY_ASSERTIONS:
        if payload.get(flag) is not True:
            blocked.append(f"safety assertion {flag} must be true")

    return _result(blocked, review, unknown)


def validate_pipeline_replay_evidence_manifest(payload):
    ok, msg = _schema_ok(payload, "scd_pipeline_replay_evidence_manifest.schema.json")
    if not ok:
        return {"validation_state": BLOCKED, "reasons": [f"schema: {msg}"]}

    blocked, review, unknown = [], [], []

    blocked += _scan_secrets(payload)
    blocked += _scan_all_strings(payload)

    if payload.get("hash_algorithm") != "canonical_json_sha256":
        blocked.append("hash_algorithm must be canonical_json_sha256")

    # Mutation after replay is a hard block.
    if payload.get("mutation_after_replay_detected"):
        blocked.append("mutation_after_replay_detected is true")

    # Completeness: incomplete -> review; missing refs -> review.
    if payload.get("evidence_complete") is not True:
        review.append("evidence_complete is not true")
    if payload.get("missing_evidence_refs"):
        review.append("missing_evidence_refs is non-empty")

    if not payload.get("stage_packet_hash_refs"):
        unknown.append("no stage_packet_hash_refs; evidence lineage unknown")

    return _result(blocked, review, unknown)


def validate_pipeline_replay_report(payload):
    ok, msg = _schema_ok(payload, "scd_pipeline_replay_report.schema.json")
    if not ok:
        return {"validation_state": BLOCKED, "reasons": [f"schema: {msg}"]}

    blocked, review, unknown = [], [], []

    blocked += _ready_flag_blocks(payload)
    blocked += _scan_secrets(payload)
    blocked += _scan_all_strings(payload)

    if payload.get("manual_publish_only") is not True:
        blocked.append("manual_publish_only must be true")
    if payload.get("mock_only") is not True:
        blocked.append("mock_only must be true")
    if payload.get("api_gate_required"):
        blocked.append("api_gate_required must be false")

    stage_results = payload.get("stage_results", []) or []
    results = [r.get("result") for r in stage_results]
    rec = payload.get("final_recommendation")

    # Fail-closed precedence: BLOCKED > UNKNOWN > REVIEW_REQUIRED > PASS.
    if BLOCKED in results:
        expected = BLOCKED
    elif UNKNOWN in results:
        expected = UNKNOWN
    elif REVIEW_REQUIRED in results:
        expected = REVIEW_REQUIRED
    elif results:
        expected = PASS
    else:
        expected = None

    if rec == PASS and expected != PASS:
        blocked.append(f"final PASS contradicts stage roll-up (expected {expected})")
    if expected == BLOCKED and rec != BLOCKED:
        blocked.append("a stage is BLOCKED; final must be BLOCKED")

    if rec not in (PASS, BLOCKED, REVIEW_REQUIRED, UNKNOWN):
        blocked.append(f"invalid final_recommendation: {rec}")

    if not stage_results:
        unknown.append("no stage_results")
    if not payload.get("safety_summary_ref"):
        unknown.append("missing safety_summary_ref")
    if not payload.get("evidence_manifest_ref"):
        unknown.append("missing evidence_manifest_ref")

    # Surface non-blocking roll-ups when the report itself is otherwise clean.
    if not blocked:
        if expected == UNKNOWN:
            unknown.append("a stage is UNKNOWN; final should be UNKNOWN")
        elif expected == REVIEW_REQUIRED:
            review.append("a stage is REVIEW_REQUIRED; final should be REVIEW_REQUIRED")

    return _result(blocked, review, unknown)


# --- Deterministic local replay helper ----------------------------------------------

# Maps a stage name to a (module_registry, key) for reuse of existing validators.
# Imported lazily inside the helper to avoid import cycles and keep this module
# importable on its own.
def _stage_validator_for(stage_name):
    from live_contentops.scd_dispatch_gate import DISPATCH_GATE_VALIDATORS
    from live_contentops.scd_mock_dispatch import MOCK_DISPATCH_VALIDATORS
    from live_contentops.scd_platform_payload_compiler import COMPILER_VALIDATORS
    from live_contentops.scd_editorial_workbench import EDITORIAL_VALIDATORS

    mapping = {
        "editorial_workbench": EDITORIAL_VALIDATORS.get("editorial_workbench_request"),
        "canonical_post_or_output": EDITORIAL_VALIDATORS.get("editorial_workbench_output"),
        "platform_payload_compile": COMPILER_VALIDATORS.get("platform_payload_compiler_output"),
        "approval_ledger": DISPATCH_GATE_VALIDATORS.get("approval_ledger_entry"),
        "freeze_manifest": DISPATCH_GATE_VALIDATORS.get("dispatch_freeze_manifest"),
        "one_button_gate": DISPATCH_GATE_VALIDATORS.get("one_button_dispatch_gate_result"),
        "mock_dispatch": MOCK_DISPATCH_VALIDATORS.get("mock_dispatch_execution_record"),
        "manual_export": MOCK_DISPATCH_VALIDATORS.get("manual_export_packet"),
        "redacted_audit_binding": MOCK_DISPATCH_VALIDATORS.get("redacted_audit_binding_packet"),
        "mock_run_report": MOCK_DISPATCH_VALIDATORS.get("mock_dispatch_run_report"),
    }
    return mapping.get(stage_name)


def replay_scd_pipeline(stage_packets):
    """Deterministically replay supplied stage packets through existing validators.

    `stage_packets` is an ordered list of {"stage_name": ..., "packet": {...}}.
    Invents nothing: no stage refs, URLs, credentials, endpoints, tokens, or
    platform results are created. Reuses existing module validators where a
    mapping exists; otherwise records UNKNOWN for that stage (no fabrication).
    Returns {"stage_results": [...], "final_recommendation": <STATE>}.
    """
    stage_results = []
    for entry in stage_packets:
        stage_name = entry.get("stage_name")
        packet = entry.get("packet", {})
        validator = _stage_validator_for(stage_name)
        if validator is None:
            state = UNKNOWN
            reasons = [f"no reusable validator mapped for stage {stage_name}"]
        else:
            res = validator(packet)
            state = res.get("validation_state", UNKNOWN)
            reasons = res.get("reasons", [])
        stage_results.append({
            "stage_name": stage_name,
            "result": state,
            "reasons": reasons,
        })

    results = [r["result"] for r in stage_results]
    if BLOCKED in results:
        final = BLOCKED
    elif UNKNOWN in results:
        final = UNKNOWN
    elif REVIEW_REQUIRED in results:
        final = REVIEW_REQUIRED
    elif results:
        final = PASS
    else:
        final = UNKNOWN
    return {"stage_results": stage_results, "final_recommendation": final}


# Registry of pipeline-replay validators, in choreography order.
PIPELINE_REPLAY_VALIDATORS = {
    "pipeline_replay_input": validate_pipeline_replay_input,
    "pipeline_stage_replay_result": validate_pipeline_stage_replay_result,
    "pipeline_replay_safety_summary": validate_pipeline_replay_safety_summary,
    "pipeline_replay_evidence_manifest": validate_pipeline_replay_evidence_manifest,
    "pipeline_replay_report": validate_pipeline_replay_report,
}
