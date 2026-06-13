"""Provider gateway DRY-RUN facade contract validators (SCD, 0174BA).

Local-only, deterministic, fail-closed. This module defines the CONTRACT and
VALIDATION for a provider-gateway DRY-RUN facade. It proves that a future
provider call cannot even be *planned* unless BOTH:

    1. the referenced SCDLLMQuotaRetryPolicy summary is PASS, and
    2. the referenced SCDCanonicalWriterPromptPack / SCDTargetedRepairPromptPack
       summary is PASS.

It NEVER calls a provider/LLM/API, never opens a network socket, never reads
credentials or env, never constructs a real provider client, never uses a
Telegram bot / webhook / OAuth, never schedules, never opens a browser, and
never enables live or public posting. The build_* helpers only rearrange
supplied local fields into a NON-EXECUTABLE call plan and a spend-ledger
ENVELOPE (estimates only); they invent nothing and perform no I/O.

Domain objects validated here:

    SCDProviderGatewayDryRunInput
    SCDProviderGatewayCallPlan
    SCDProviderGatewaySpendLedgerEntry
    SCDProviderGatewayDryRunResult
    SCDProviderGatewayGateReport

A dry-run PASS means only "dry-run call plan is safe for future provider-gate
review" -- never provider-ready, live-ready, or public-ready.

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
from live_contentops.scd_dispatch_gate import NETWORK_API_PATTERNS
from live_contentops.scd_llm_quota_retry_policy import LOOP_LANGUAGE_PATTERNS

# Flags that must NEVER be true on any gateway dry-run object. A dry run can
# never be executable and can never touch a provider / network / credential.
FORBIDDEN_FALSE_FLAGS = (
    "executable",
    "provider_api_allowed",
    "network_allowed",
    "credentials_required",
    "credential_lookup_performed",
    "env_read_performed",
    "api_key_present",
)

# Readiness flags that must never be true: a dry run is never provider/live/
# public ready by itself.
FORBIDDEN_READY_FLAGS = ("provider_ready", "live_ready", "public_ready")

# Spend-ledger fields that must all be present (estimates are required even in a
# dry run so the future provider gate can budget against them).
REQUIRED_SPEND_FIELDS = (
    "estimated_input_tokens",
    "estimated_output_tokens",
    "estimated_cost",
    "provider_name",
    "model_name",
    "stage_name",
    "packet_ref",
    "cache_key_ref",
)

# The only two operations a dry run may plan.
VALID_OPERATIONS = ("canonical_generation", "targeted_repair")


def _scan(text, patterns):
    return _find_language(text, patterns)


def _all_unsafe_text(text):
    """Return all forbidden/authority/metric/api/loop hits in a single string."""
    hits = []
    hits += [f"forbidden language: {h}" for h in _scan(text, FORBIDDEN_LANGUAGE)]
    hits += [f"invented authority: {h}" for h in _scan(text, INVENTED_AUTHORITY_PATTERNS)]
    hits += [f"invented metric: {h}" for h in _scan(text, INVENTED_METRIC_PATTERNS)]
    hits += [f"telegram/api implication: {h}" for h in _scan(text, TELEGRAM_API_PATTERNS)]
    hits += [f"network/api/oauth implication: {h}" for h in _scan(text, NETWORK_API_PATTERNS)]
    hits += [f"forbidden loop language: {h}" for h in _scan(text, LOOP_LANGUAGE_PATTERNS)]
    return hits


def _scan_all_strings(obj):
    """Recursively scan keys + string values for any unsafe language."""
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


def _forbidden_flag_blocks(payload):
    return [f"{flag} must be false" for flag in FORBIDDEN_FALSE_FLAGS if payload.get(flag)]


def _ready_flag_blocks(payload):
    return [f"{flag} must be false" for flag in FORBIDDEN_READY_FLAGS if payload.get(flag)]


def _stable_hash(value):
    """Deterministic sha256 over canonical JSON of the supplied value."""
    blob = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return "sha256:" + hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _quota_summary_blocks(summary):
    """The referenced quota policy summary must be a PASS SCDLLMQuotaRetryPolicy."""
    blocks = []
    if not summary:
        blocks.append("quota_policy_summary missing")
        return blocks
    if summary.get("validation_state") != PASS:
        blocks.append("quota policy summary is not PASS")
    for flag in ("provider_api_allowed", "network_allowed", "credentials_required"):
        if summary.get(flag):
            blocks.append(f"quota policy {flag} must be false")
    if summary.get("max_generation_attempts") != 1:
        blocks.append("quota policy max_generation_attempts must be 1")
    repair = summary.get("max_targeted_repair_attempts")
    if not isinstance(repair, int) or isinstance(repair, bool) or repair < 0 or repair > 1:
        blocks.append("quota policy max_targeted_repair_attempts must be 0 or 1")
    return blocks


def _prompt_pack_blocks(summary):
    """The referenced prompt-pack summary must be PASS (canonical or repair)."""
    blocks = []
    if not summary:
        blocks.append("prompt_pack_summary missing")
        return blocks
    if summary.get("validation_state") != PASS:
        blocks.append("prompt pack summary is not PASS")
    if summary.get("platform_variants_requested"):
        blocks.append("platform variants are forbidden in the gateway dry run")
    return blocks


def _operation_attempt_blocks(payload):
    """Bound the requested operation's attempt/prior-attempt counters."""
    blocks = []
    op = payload.get("requested_operation")
    if op not in VALID_OPERATIONS:
        blocks.append(f"requested_operation must be one of {VALID_OPERATIONS}")
        return blocks
    attempt = payload.get("attempt_index")
    prior = payload.get("prior_attempt_count")
    if not isinstance(attempt, int) or isinstance(attempt, bool):
        blocks.append("attempt_index must be an integer")
        return blocks
    if not isinstance(prior, int) or isinstance(prior, bool):
        blocks.append("prior_attempt_count must be an integer")
        return blocks
    if op == "canonical_generation":
        if attempt != 1:
            blocks.append("canonical_generation requires attempt_index == 1")
        if prior != 0:
            blocks.append("canonical_generation requires prior_attempt_count == 0")
    elif op == "targeted_repair":
        if attempt > 1:
            blocks.append("targeted_repair requires attempt_index <= 1")
        if prior > 1:
            blocks.append("targeted_repair requires prior_attempt_count <= 1")
    return blocks


def validate_provider_gateway_dry_run_input(payload):
    ok, msg = _schema_ok(payload, "scd_provider_gateway_dry_run_input.schema.json")
    if not ok:
        return {"validation_state": BLOCKED, "reasons": [f"schema: {msg}"]}

    blocked, review, unknown = [], [], []

    blocked += _scan_secrets(payload)
    blocked += _scan_all_strings(payload)
    blocked += _forbidden_flag_blocks(payload)
    blocked += _ready_flag_blocks(payload)

    blocked += _quota_summary_blocks(payload.get("quota_policy_summary"))
    blocked += _prompt_pack_blocks(payload.get("prompt_pack_summary"))
    blocked += _operation_attempt_blocks(payload)

    # Spend estimate must be present (missing estimate -> BLOCKED).
    for field in ("estimated_input_tokens", "estimated_output_tokens", "estimated_cost"):
        if payload.get(field) is None:
            blocked.append(f"{field} missing; spend estimate required")

    # Cache key must be present (missing -> UNKNOWN lineage).
    if not payload.get("prompt_pack_cache_key"):
        unknown.append("prompt_pack_cache_key missing; cache lineage unknown")

    # A cache hit on a stale prompt version is safe but needs human review.
    if payload.get("cache_lookup_state") == "cache_hit_stale_prompt_version":
        review.append("cache hit on stale prompt version; confirm reuse")

    return _result(blocked, review, unknown)


def validate_provider_gateway_call_plan(payload):
    ok, msg = _schema_ok(payload, "scd_provider_gateway_call_plan.schema.json")
    if not ok:
        return {"validation_state": BLOCKED, "reasons": [f"schema: {msg}"]}

    blocked, review, unknown = [], [], []

    blocked += _scan_secrets(payload)
    blocked += _scan_all_strings(payload)
    blocked += _forbidden_flag_blocks(payload)
    blocked += _ready_flag_blocks(payload)

    # A call plan is ALWAYS non-executable and dry-run-only.
    if payload.get("executable") is not False:
        blocked.append("executable must be false")
    if payload.get("dry_run_only") is not True:
        blocked.append("dry_run_only must be true")

    if payload.get("requested_operation") not in VALID_OPERATIONS:
        blocked.append(f"requested_operation must be one of {VALID_OPERATIONS}")

    # Lineage refs binding the plan to its inputs.
    for ref in ("prompt_pack_ref", "quota_policy_ref"):
        if not payload.get(ref):
            blocked.append(f"{ref} missing; call plan not bound")
    if not payload.get("cache_key_ref"):
        unknown.append("cache_key_ref missing; cache lineage unknown")

    return _result(blocked, review, unknown)


def validate_provider_gateway_spend_ledger_entry(payload):
    ok, msg = _schema_ok(payload, "scd_provider_gateway_spend_ledger_entry.schema.json")
    if not ok:
        return {"validation_state": BLOCKED, "reasons": [f"schema: {msg}"]}

    blocked, review, unknown = [], [], []

    blocked += _scan_secrets(payload)
    blocked += _scan_all_strings(payload)
    blocked += _forbidden_flag_blocks(payload)
    blocked += _ready_flag_blocks(payload)

    # Every spend field is required (estimates only; no live spend here).
    for field in REQUIRED_SPEND_FIELDS:
        if payload.get(field) is None:
            blocked.append(f"{field} missing; spend ledger entry incomplete")

    # Numeric estimates must be non-negative numbers (not bools).
    for field in ("estimated_input_tokens", "estimated_output_tokens", "estimated_cost"):
        value = payload.get(field)
        if value is not None:
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                blocked.append(f"{field} must be a non-negative number")
            elif value < 0:
                blocked.append(f"{field} must be a non-negative number")

    # A spend entry records an ESTIMATE only; actuals imply a real call.
    if payload.get("actual_cost") is not None or payload.get("actual_input_tokens") is not None:
        blocked.append("actual spend present; dry-run ledger records estimates only")

    return _result(blocked, review, unknown)


def validate_provider_gateway_dry_run_result(payload):
    ok, msg = _schema_ok(payload, "scd_provider_gateway_dry_run_result.schema.json")
    if not ok:
        return {"validation_state": BLOCKED, "reasons": [f"schema: {msg}"]}

    blocked, review, unknown = [], [], []

    blocked += _scan_secrets(payload)
    blocked += _scan_all_strings(payload)
    blocked += _forbidden_flag_blocks(payload)
    blocked += _ready_flag_blocks(payload)

    # The result must be non-executable and dry-run-only.
    if payload.get("executable") is not False:
        blocked.append("executable must be false")
    if payload.get("dry_run_only") is not True:
        blocked.append("dry_run_only must be true")

    # An embedded call plan, if present, must itself validate as non-BLOCKED.
    plan = payload.get("call_plan")
    if isinstance(plan, dict):
        plan_state = validate_provider_gateway_call_plan(plan)["validation_state"]
        if plan_state == BLOCKED:
            blocked.append("embedded call_plan is BLOCKED")
        elif plan_state == UNKNOWN:
            unknown.append("embedded call_plan lineage UNKNOWN")

    # An embedded spend ledger entry, if present, must itself validate.
    entry = payload.get("spend_ledger_entry")
    if isinstance(entry, dict):
        entry_state = validate_provider_gateway_spend_ledger_entry(entry)["validation_state"]
        if entry_state == BLOCKED:
            blocked.append("embedded spend_ledger_entry is BLOCKED")

    # Lineage refs binding the result.
    for ref in ("call_plan_ref", "spend_ledger_entry_ref"):
        if not payload.get(ref):
            unknown.append(f"{ref} missing; result lineage unknown")

    return _result(blocked, review, unknown)


def validate_provider_gateway_gate_report(payload):
    ok, msg = _schema_ok(payload, "scd_provider_gateway_gate_report.schema.json")
    if not ok:
        return {"validation_state": BLOCKED, "reasons": [f"schema: {msg}"]}

    blocked, review, unknown = [], [], []

    blocked += _scan_secrets(payload)
    blocked += _scan_all_strings(payload)
    blocked += _forbidden_flag_blocks(payload)
    blocked += _ready_flag_blocks(payload)

    # The report rolls up sub-results; it can never claim provider/live ready.
    if payload.get("provider_ready") or payload.get("live_ready") or payload.get("public_ready"):
        blocked.append("gate report can never be provider/live/public ready")

    # Fail-closed roll-up: any BLOCKED sub-result forces the report BLOCKED.
    sub_results = (
        "input_result",
        "call_plan_result",
        "spend_ledger_result",
        "dry_run_result",
    )
    states = [payload.get(r) for r in sub_results]
    if any(s == BLOCKED for s in states):
        if payload.get("validation_state") != BLOCKED:
            blocked.append("a sub-result is BLOCKED but report not BLOCKED")
    if BLOCKED not in states and payload.get("final_recommendation") == PASS:
        # Contradiction guard: a PASS recommendation requires every sub PASS.
        if any(s != PASS for s in states):
            blocked.append("final_recommendation PASS but a sub-result is not PASS")

    # A dry-run gate report must always require future operator review.
    if payload.get("operator_review_required") is not True:
        blocked.append("operator_review_required must be true")
    if payload.get("ready_for_future_provider_gate_review") is not True:
        review.append("ready_for_future_provider_gate_review should be true")

    return _result(blocked, review, unknown)


def _ref(value, default):
    """Best-effort lineage ref extraction from a string or dict component."""
    if isinstance(value, str) and value:
        return value
    if isinstance(value, dict):
        for key in ("cache_key_id", "policy_id", "prompt_pack_id", "id"):
            if value.get(key):
                return value[key]
    return default


def build_provider_gateway_call_plan(input_packet):
    """Rearrange supplied local fields into a NON-EXECUTABLE call plan.

    Pure function: no I/O, no network, no provider client. Every executable /
    provider / network / credential flag is hardwired to its safe value; this
    helper invents nothing beyond a deterministic id.
    """
    quota = input_packet.get("quota_policy_summary", {}) or {}
    pack = input_packet.get("prompt_pack_summary", {}) or {}
    prompt_pack_ref = _ref(pack, pack.get("prompt_pack_id", "unknown_prompt_pack"))
    quota_policy_ref = _ref(quota, quota.get("policy_id", "unknown_quota_policy"))
    cache_key_ref = _ref(input_packet.get("prompt_pack_cache_key"), "")
    plan = {
        "schema_version": "1.0",
        "executable": False,
        "provider_api_allowed": False,
        "network_allowed": False,
        "credentials_required": False,
        "credential_lookup_performed": False,
        "env_read_performed": False,
        "api_key_present": False,
        "dry_run_only": True,
        "requested_operation": input_packet.get("requested_operation"),
        "prompt_pack_ref": prompt_pack_ref,
        "quota_policy_ref": quota_policy_ref,
        "cache_key_ref": cache_key_ref,
        "spend_ledger_entry_ref": None,
        "blocked_reasons": [],
        "review_reasons": [],
        "unknown_reasons": [],
    }
    plan["call_plan_id"] = "call_plan:" + _stable_hash(plan)
    plan["validation_state"] = validate_provider_gateway_call_plan(plan)["validation_state"]
    return plan


def build_spend_ledger_entry(input_packet, call_plan):
    """Build an ESTIMATES-ONLY spend ledger envelope. No actual spend, no I/O."""
    pack = input_packet.get("prompt_pack_summary", {}) or {}
    entry = {
        "schema_version": "1.0",
        "estimated_input_tokens": input_packet.get("estimated_input_tokens"),
        "estimated_output_tokens": input_packet.get("estimated_output_tokens"),
        "estimated_cost": input_packet.get("estimated_cost"),
        "provider_name": _ref(input_packet.get("provider_profile_stub"), "unknown_provider"),
        "model_name": _ref(input_packet.get("model_config_stub"), "unknown_model"),
        "stage_name": input_packet.get("requested_operation"),
        "packet_ref": _ref(pack, "unknown_prompt_pack"),
        "cache_key_ref": call_plan.get("cache_key_ref"),
    }
    entry["spend_ledger_entry_id"] = "spend:" + _stable_hash(entry)
    entry["validation_state"] = validate_provider_gateway_spend_ledger_entry(entry)["validation_state"]
    return entry


def build_provider_gateway_dry_run_result(input_packet, call_plan, spend_entry):
    """Assemble a NON-EXECUTABLE dry-run result. Never provider/live/public ready."""
    call_plan = dict(call_plan)
    call_plan["spend_ledger_entry_ref"] = spend_entry.get("spend_ledger_entry_id")
    result = {
        "schema_version": "1.0",
        "executable": False,
        "dry_run_only": True,
        "provider_ready": False,
        "live_ready": False,
        "public_ready": False,
        "requested_operation": input_packet.get("requested_operation"),
        "call_plan": call_plan,
        "spend_ledger_entry": spend_entry,
        "call_plan_ref": call_plan.get("call_plan_id"),
        "spend_ledger_entry_ref": spend_entry.get("spend_ledger_entry_id"),
        "final_recommendation": UNKNOWN,
    }
    result["result_id"] = "dry_run_result:" + _stable_hash(result)
    state = validate_provider_gateway_dry_run_result(result)["validation_state"]
    result["final_recommendation"] = state
    result["validation_state"] = state
    return result


# Registry of provider-gateway dry-run validators, in choreography order.
PROVIDER_GATEWAY_DRY_RUN_VALIDATORS = {
    "provider_gateway_dry_run_input": validate_provider_gateway_dry_run_input,
    "provider_gateway_call_plan": validate_provider_gateway_call_plan,
    "provider_gateway_spend_ledger_entry": validate_provider_gateway_spend_ledger_entry,
    "provider_gateway_dry_run_result": validate_provider_gateway_dry_run_result,
    "provider_gateway_gate_report": validate_provider_gateway_gate_report,
}
