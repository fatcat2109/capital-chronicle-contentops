"""Bounded no-write 9router preflight and canonical model-router run summary.

Two jobs, deliberately kept together because they produce one evidence artifact.

**Preflight** performs the smallest safe real call per authorized model: one tiny prompt
with a deterministic expected answer. It learns connectivity, exact-model acceptance,
observable model identity, latency, and usage/cost metadata. It does not try to prove the
retry algorithm — deterministic fault injection does that, without burning paid tokens on
manufactured failures.

**Run summary** assembles authority, policy, preflight, and fault-injection results into one
machine-readable packet with an explicit secret-redaction status.

Nothing here publishes, dispatches, touches a scheduler, or performs any platform action.
"""
from __future__ import annotations

import json
import time
from typing import Any, Callable, Mapping, Sequence

from live_contentops.credential_redaction_policy import (
    assert_no_secret_shaped_text,
    sanitize_for_output,
)
from live_contentops.nine_router_ordered_model_router_v2 import (
    ACCEPTED,
    AUTHORITY_ID,
    GATEWAY,
    IDENTITY_NOT_VERIFIABLE,
    ORDERED_MODEL_POOL,
    NEWSROOM_LEAF_SCAN_MODEL_POOL,
    PRIMARY_MODEL,
    ProviderResult,
    RetryBudget,
    authority_packet,
    retry_budget_policy,
    route_llm_invocation,
)
from live_contentops.nine_router_provider_adapter_v2 import (
    NineRouterAdapterError,
    call_nine_router,
    credential_presence,
    normalize_model_identity,
)

SCHEMA_VERSION = "contentops.nine_router_model_router_run_summary.v2"
TASK_LABEL = "TASK_CONTENTOPS_9ROUTER_ORDERED_MODEL_ROUTER_RETRY_BUDGET_AND_LIVE_PREFLIGHT_V1"
OPERATING_MODE = "SHADOW_ONLY_PROVIDER_PREFLIGHT"

#: The smallest prompt that still proves the model read the request and answered it. Kept
#: non-public and deterministic so a healthy model costs a handful of tokens to probe.
PREFLIGHT_PROMPT = (
    "Reply with exactly the single word READY and nothing else. Do not explain."
)
PREFLIGHT_EXPECTED = "READY"
PREFLIGHT_MAX_TOKENS = 16
PREFLIGHT_TIMEOUT_SECONDS = 60.0

HEALTHY = "HEALTHY"
UNAVAILABLE = "TEMPORARILY_UNAVAILABLE"
IDENTITY_UNVERIFIABLE = IDENTITY_NOT_VERIFIABLE
NOT_ATTEMPTED = "NOT_ATTEMPTED_NO_CREDENTIAL"


def preflight_model(
    model: str,
    *,
    provider_call: Callable[..., ProviderResult] | None = None,
    timeout_seconds: float = PREFLIGHT_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    """One bounded identity/connectivity probe for a single authorized model."""
    call = provider_call or (
        lambda prompt, mdl, timeout: call_nine_router(
            prompt, mdl, timeout, max_tokens=PREFLIGHT_MAX_TOKENS, temperature=0.0
        )
    )
    started = time.monotonic()
    try:
        result = call(PREFLIGHT_PROMPT, model, timeout_seconds)
    except NineRouterAdapterError as exc:
        return {
            "requested_model": model,
            "health": NOT_ATTEMPTED,
            "failure_class": "configuration_error",
            "detail": str(exc),
            "provider_call_performed": False,
        }
    latency = round(time.monotonic() - started, 4)

    text = (result.text or "").strip()
    observed = result.resolved_model
    # The gateway may report the effective model without its routing prefix.
    # Compare the canonical bare ID so a naming convention is not misreported as a
    # substitution, while a real swap still fails.
    identity_verified = observed is not None and normalize_model_identity(
        observed
    ) == normalize_model_identity(model)
    healthy = result.failure_class is None and bool(text)

    if not healthy:
        health = UNAVAILABLE
    elif observed is None:
        health = IDENTITY_UNVERIFIABLE
    elif not identity_verified:
        health = "MODEL_IDENTITY_MISMATCH"
    else:
        health = HEALTHY

    return {
        "requested_model": model,
        "model_priority_index": (
            list(ORDERED_MODEL_POOL).index(model)
            if model in ORDERED_MODEL_POOL
            else list(NEWSROOM_LEAF_SCAN_MODEL_POOL).index(model)
            if model in NEWSROOM_LEAF_SCAN_MODEL_POOL
            else None
        ),
        "gateway": GATEWAY,
        "health": health,
        "provider_call_performed": True,
        "success": healthy,
        "failure_class": result.failure_class,
        "provider_status_class": (
            f"{result.status_code // 100}xx" if result.status_code else None
        ),
        "provider_observed_effective_model": observed,
        "provider_observed_effective_model_normalized": normalize_model_identity(observed),
        "requested_model_normalized": normalize_model_identity(model),
        "model_identity_provider_verified": identity_verified,
        "model_identity_provider_verifiable": observed is not None,
        "provider_invocation_id": result.provider_invocation_id,
        "latency_seconds": latency,
        "usage": dict(result.usage) if result.usage else None,
        "cost": dict(result.cost) if result.cost else None,
        "response_matched_expected_token": text.upper().startswith(PREFLIGHT_EXPECTED),
        "response_char_count": len(text),
        "public_write_performed": False,
        "platform_action_performed": False,
    }


def run_preflight(
    *,
    models: Sequence[str] = ORDERED_MODEL_POOL,
    provider_call: Callable[..., ProviderResult] | None = None,
) -> dict[str, Any]:
    """Probe every authorized model once. A temporarily unavailable model is recorded, not fatal."""
    results = [preflight_model(model, provider_call=provider_call) for model in models]
    healthy = [row for row in results if row["health"] == HEALTHY]
    unverifiable = [row for row in results if row["health"] == IDENTITY_UNVERIFIABLE]
    mismatched = [row for row in results if row["health"] == "MODEL_IDENTITY_MISMATCH"]

    if mismatched:
        identity_disposition = "BLOCKED_MODEL_IDENTITY_MISMATCH"
    elif unverifiable and not healthy:
        identity_disposition = IDENTITY_UNVERIFIABLE
    elif healthy:
        identity_disposition = "MODEL_IDENTITY_PROVIDER_VERIFIED"
    else:
        identity_disposition = "NO_MODEL_REACHABLE"

    return {
        "schema_version": SCHEMA_VERSION,
        "gateway": GATEWAY,
        "authorized_models_probed": list(models),
        "credential_presence": credential_presence(),
        "per_model": results,
        "healthy_count": len(healthy),
        "unavailable_count": sum(1 for row in results if row["health"] == UNAVAILABLE),
        "identity_unverifiable_count": len(unverifiable),
        "identity_mismatch_count": len(mismatched),
        "model_identity_disposition": identity_disposition,
        "primary_model": PRIMARY_MODEL,
        "primary_model_healthy": any(
            row["requested_model"] == PRIMARY_MODEL and row["health"] == HEALTHY
            for row in results
        ),
        "total_probe_latency_seconds": round(
            sum(float(row.get("latency_seconds") or 0.0) for row in results), 4
        ),
        "public_write_performed": False,
        "platform_action_performed": False,
        "scheduler_mutated": False,
        "dispatch_performed": False,
    }


def build_run_summary(
    *,
    preflight: Mapping[str, Any] | None = None,
    fault_injection: Mapping[str, Any] | None = None,
    invocations: Sequence[Mapping[str, Any]] = (),
    end_to_end: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Assemble the canonical machine-readable model-router run summary."""
    authority = authority_packet()

    attempts_total = 0
    fallback_total = 0
    exhausted_total = 0
    successes_by_model: dict[str, int] = {}
    attempts_by_model: dict[str, int] = {}
    retries_by_error_class: dict[str, int] = {}
    fallback_reasons: dict[str, int] = {}
    latencies: list[float] = []
    usage_totals: dict[str, float] = {}
    cost_totals: dict[str, float] = {}

    for invocation in invocations:
        attempts_total += int(invocation.get("total_attempts") or 0)
        fallback_total += int(invocation.get("total_fallback_transitions") or 0)
        if invocation.get("budget_exhausted"):
            exhausted_total += 1
        selected = invocation.get("selected_model")
        if selected:
            successes_by_model[selected] = successes_by_model.get(selected, 0) + 1
        for row in invocation.get("attempts") or []:
            model = str(row.get("requested_model"))
            attempts_by_model[model] = attempts_by_model.get(model, 0) + 1
            klass = row.get("failure_class")
            if klass:
                retries_by_error_class[str(klass)] = retries_by_error_class.get(str(klass), 0) + 1
            reason = row.get("fallback_reason")
            if reason:
                fallback_reasons[str(reason)] = fallback_reasons.get(str(reason), 0) + 1
            if isinstance(row.get("latency_seconds"), (int, float)):
                latencies.append(float(row["latency_seconds"]))
            for source, totals in ((row.get("usage"), usage_totals), (row.get("cost"), cost_totals)):
                if isinstance(source, Mapping):
                    for key, value in source.items():
                        if isinstance(value, (int, float)):
                            totals[key] = totals.get(key, 0.0) + float(value)

    summary = {
        "schema_version": SCHEMA_VERSION,
        "task": TASK_LABEL,
        "operating_mode": OPERATING_MODE,
        "authority_id": authority["authority_id"],
        "authority_version": authority["authority_version"],
        "authority_logical_hash": authority["authority_logical_hash"],
        "supersedes_authority_id": authority["supersedes"],
        "gateway": GATEWAY,
        "ordered_model_pool": list(ORDERED_MODEL_POOL),
        "primary_model": PRIMARY_MODEL,
        "retry_budget_policy": retry_budget_policy(),
        "preflight": preflight,
        "fault_injection": fault_injection,
        "end_to_end_package": end_to_end,
        "total_model_attempts": attempts_total,
        "attempts_by_model": attempts_by_model,
        "successful_calls_by_model": successes_by_model,
        "fallback_count": fallback_total,
        "fallback_reasons": fallback_reasons,
        "retries_by_error_class": retries_by_error_class,
        "exhausted_budget_count": exhausted_total,
        "observed_latency_seconds": {
            "count": len(latencies),
            "min": round(min(latencies), 4) if latencies else None,
            "max": round(max(latencies), 4) if latencies else None,
            "mean": round(sum(latencies) / len(latencies), 4) if latencies else None,
        },
        "observed_token_usage": {k: round(v, 4) for k, v in usage_totals.items()} or None,
        "observed_cost": {k: round(v, 8) for k, v in cost_totals.items()} or None,
        "unbounded_retry_possible": False,
        "unauthorized_model_accepted": False,
        "fallback_bypasses_quality_gates": False,
        "public_write_performed": False,
        "platform_action_performed": False,
        "dispatch_performed": False,
        "scheduler_mutated": False,
        "capital_chronicle_authority_mutated": False,
        "work_package_f_started": False,
        "public_live_cohort_authorized_by_this_task": False,
    }

    blob = json.dumps(sanitize_for_output(summary), sort_keys=True)
    try:
        assert_no_secret_shaped_text(blob)
        summary["secret_redaction_status"] = "PASS_NO_SECRET_SHAPED_MATERIAL"
    except Exception as exc:  # pragma: no cover - defensive; must never pass silently
        summary["secret_redaction_status"] = f"FAIL_{type(exc).__name__}"
    return summary


def probe_with_router(
    *,
    logical_invocation_id: str = "preflight_router_probe",
    provider_call: Callable[..., ProviderResult] | None = None,
) -> dict[str, Any]:
    """Drive one real probe through the full router so ordering is exercised end to end."""
    call = provider_call or (
        lambda prompt, mdl, timeout: call_nine_router(
            prompt, mdl, timeout, max_tokens=PREFLIGHT_MAX_TOKENS, temperature=0.0
        )
    )

    def validator(text: str) -> tuple[bool, str | None, Any]:
        cleaned = (text or "").strip()
        if not cleaned:
            return (False, "structured_output_malformed", None)
        return (True, None, cleaned)

    return route_llm_invocation(
        logical_invocation_id=logical_invocation_id,
        role_task_id="nine_router_preflight_probe",
        prompt=PREFLIGHT_PROMPT,
        provider_call=call,
        prompt_template="nine_router_preflight",
        prompt_version="v2",
        validator=validator,
        budget=RetryBudget(logical_invocation_id=logical_invocation_id),
        timeout_seconds=PREFLIGHT_TIMEOUT_SECONDS,
    )
