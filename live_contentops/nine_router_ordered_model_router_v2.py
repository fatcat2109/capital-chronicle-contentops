"""Canonical 9router ordered model router with bounded retry and fallback.

Authority: ``CONTENTOPS_9ROUTER_ORDERED_MODEL_AUTHORITY_V2``. This supersedes
``CONTENTOPS_FINAL_PRELAUNCH_LLM_MODEL_AUTHORITY_V1``, which prohibited *all* fallback.
Ordered fallback performed by this router is now owner-authorized and is not a policy
violation. Silent provider-side substitution remains forbidden.

This module is the one authoritative place where ContentOps decides:

* which models may be used, and in what order;
* whether a failure is retryable, fallback-eligible, or terminal;
* how much attempt, time, and sleep budget a logical invocation may consume.

Three invariants shape the design.

**Bounded by construction.** A logical invocation allocates one immutable
:class:`RetryBudget` before its first provider call. Every attempt decrements it. There is
no path that resets the budget — not a model change, not a structured-output repair, not a
process restart that rehydrates a budget snapshot. The worst-case attempt count is finite
and declared up front.

**Fallback is for resilience, never for quality-gate bypass.** A transient infrastructure
failure may rotate models. An evidence, factual, permission, publication-authority,
freshness, or policy failure may not: rotating models to hunt for a passing answer is
exactly the failure mode this classifier exists to prevent. Those failures terminate.

**Identity is proven, never assumed.** If the gateway reports an effective model that
differs from the exact requested model, the output is rejected regardless of how good it
looks. If the gateway does not report identity at all, that is recorded honestly as
``MODEL_IDENTITY_NOT_PROVIDER_VERIFIABLE`` rather than being upgraded to a pass.
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from typing import Any, Callable, Mapping, Sequence

from live_contentops.credential_redaction_policy import (
    assert_no_secret_shaped_text,
    redact_text,
    sanitize_for_output,
)
from live_contentops.llm_cost_governor_v1 import COST_TERMINAL_FAILURE_CLASSES

SCHEMA_VERSION = "contentops.nine_router_ordered_model_router.v2"

AUTHORITY_ID = "CONTENTOPS_9ROUTER_ORDERED_MODEL_AUTHORITY_V2"
AUTHORITY_VERSION = "v2"
SUPERSEDES_AUTHORITY_ID = "CONTENTOPS_FINAL_PRELAUNCH_LLM_MODEL_AUTHORITY_V1"
GATEWAY = "9router"

#: The exact ordered model pool. Every entry is an opaque exact string; the router never
#: parses, normalises, or "corrects" a model ID. P0 remains the primary preference.
ORDERED_MODEL_POOL: tuple[str, ...] = (
    "new/claude-fable-5",
    "new/gpt-5.6-sol-xhigh",
    "new/claude-opus-5",
    "vx/gemini-3.1-pro-preview(high)",
)
PRIMARY_MODEL = ORDERED_MODEL_POOL[0]

#: Cheap leaf semantic labour may prefer the exact high-throughput Flash model without
#: changing the quality-first pool above. Final editorial and article-writing roles retain
#: the canonical quality ordering. Keeping this registry beside the canonical pool means the
#: provider adapter and router still share one authority surface.
NEWSROOM_LEAF_SCAN_ROLE = "rolling_x_newsroom_leaf_scan"
PASSIVE_INTERACTION_QUALITY_ROLE = "passive_interaction_quality_classification"
NEWSROOM_GLOBAL_EDITOR_ROLE = "rolling_x_newsroom_assignment"
ARTICLE_WRITING_ROLE = "article_writing"
GROUNDED_RESEARCH_ROLE = "v1_grounded_researcher"
ARTICLE_WRITING_CX_RESCUE_ROLE = "v1_article_writing_cx_utility_rescue"
NEWSROOM_LEAF_SCAN_MODEL = "vx/gemini-3.5-flash(high)"
GEMINI_PRO_MODEL = ORDERED_MODEL_POOL[-1]
CX_FINAL_FALLBACK_MODEL = "cx/gpt-5.6-sol(xhigh)"
V1_GROUNDED_RESEARCH_MODEL_LADDER: tuple[str, ...] = (
    "vx/gemini-3.1-pro-preview(high)",
    "vx/gemini-3.5-flash(high)",
)
NEWSROOM_LEAF_SCAN_MODEL_POOL: tuple[str, ...] = (
    NEWSROOM_LEAF_SCAN_MODEL,
    *ORDERED_MODEL_POOL,
)
V1_HIGH_QUALITY_MODEL_POOL: tuple[str, ...] = (
    *ORDERED_MODEL_POOL,
    CX_FINAL_FALLBACK_MODEL,
)
ARTICLE_WRITING_MODEL_POOL: tuple[str, ...] = V1_HIGH_QUALITY_MODEL_POOL
GROUNDED_RESEARCH_MODEL_POOL: tuple[str, ...] = V1_GROUNDED_RESEARCH_MODEL_LADDER
ARTICLE_WRITING_CX_RESCUE_MODEL_POOL: tuple[str, ...] = (CX_FINAL_FALLBACK_MODEL,)
ROLE_MODEL_POOLS: Mapping[str, tuple[str, ...]] = {
    NEWSROOM_LEAF_SCAN_ROLE: NEWSROOM_LEAF_SCAN_MODEL_POOL,
    PASSIVE_INTERACTION_QUALITY_ROLE: NEWSROOM_LEAF_SCAN_MODEL_POOL,
    # Article prose is final editorial work, so it uses the exact quality-first order. Flash
    # remains authorized only for the cheap semantic leaf role above.
    ARTICLE_WRITING_ROLE: ARTICLE_WRITING_MODEL_POOL,
    GROUNDED_RESEARCH_ROLE: GROUNDED_RESEARCH_MODEL_POOL,
    ARTICLE_WRITING_CX_RESCUE_ROLE: ARTICLE_WRITING_CX_RESCUE_MODEL_POOL,
}
AUTHORIZED_MODELS = frozenset(
    model
    for pool in (ORDERED_MODEL_POOL, *ROLE_MODEL_POOLS.values())
    for model in pool
)

# Temporary, process-only pre-launch incident seam. The canonical quality order above stays
# authoritative when these variables are absent, invalid, or expired. A 24-hour maximum keeps
# a build-time provider incident from silently becoming launch policy.
BUILD_ACCEPTANCE_GEMINI_INCIDENT_MODE_ENV = (
    "CONTENTOPS_BUILD_ACCEPTANCE_GEMINI_INCIDENT_MODE"
)
BUILD_ACCEPTANCE_GEMINI_INCIDENT_EXPIRES_ENV = (
    "CONTENTOPS_BUILD_ACCEPTANCE_GEMINI_INCIDENT_EXPIRES_AT_UTC"
)
BUILD_ACCEPTANCE_GEMINI_INCIDENT_MODES = frozenset(
    {"PRO_AND_FLASH", "PRO_ONLY", "FLASH_ONLY"}
)
MAX_BUILD_ACCEPTANCE_GEMINI_INCIDENT_DURATION = timedelta(hours=24)


def build_acceptance_gemini_incident(
    *, now_utc: datetime | None = None,
) -> dict[str, Any] | None:
    """Return a validated, short-lived Gemini incident override or ``None``.

    No arbitrary model identifier is accepted: the mode maps only to the two exact Gemini IDs
    already present in the canonical authority. Invalid configuration fails closed to normal
    quality-first routing.
    """
    mode = os.environ.get(BUILD_ACCEPTANCE_GEMINI_INCIDENT_MODE_ENV, "").strip()
    raw_expiry = os.environ.get(BUILD_ACCEPTANCE_GEMINI_INCIDENT_EXPIRES_ENV, "").strip()
    if mode not in BUILD_ACCEPTANCE_GEMINI_INCIDENT_MODES or not raw_expiry:
        return None
    try:
        expiry = datetime.fromisoformat(raw_expiry.replace("Z", "+00:00"))
    except ValueError:
        return None
    if expiry.tzinfo is None or expiry.utcoffset() != timedelta(0):
        return None
    now = now_utc or datetime.now(timezone.utc)
    if now.tzinfo is None:
        return None
    now = now.astimezone(timezone.utc)
    expiry = expiry.astimezone(timezone.utc)
    if expiry <= now or expiry - now > MAX_BUILD_ACCEPTANCE_GEMINI_INCIDENT_DURATION:
        return None
    return {
        "mode": mode,
        "expires_at_utc": expiry.isoformat().replace("+00:00", "Z"),
        "production_default_unchanged": True,
    }


def _incident_model_pool_for_role(role_task_id: str, mode: str) -> tuple[str, ...]:
    if str(role_task_id) == ARTICLE_WRITING_CX_RESCUE_ROLE:
        return ARTICLE_WRITING_CX_RESCUE_MODEL_POOL
    if mode == "PRO_AND_FLASH":
        return (
            (NEWSROOM_LEAF_SCAN_MODEL,)
            if str(role_task_id) == NEWSROOM_LEAF_SCAN_ROLE
            else (GEMINI_PRO_MODEL,)
        )
    if mode == "PRO_ONLY":
        return (GEMINI_PRO_MODEL,)
    return (NEWSROOM_LEAF_SCAN_MODEL,)

#: Per-model attempt ceilings, indexed by priority. P0/P1 get one retry each; P2/P3 get a
#: single attempt, because by the time the router reaches them the invocation has already
#: spent most of its global budget and a further same-model retry buys little.
PER_MODEL_MAX_ATTEMPTS: tuple[int, ...] = (2, 2, 1, 1)
NEWSROOM_LEAF_SCAN_PER_MODEL_MAX_ATTEMPTS: tuple[int, ...] = (2, 1, 1, 1, 1)
NEWSROOM_GLOBAL_EDITOR_PER_MODEL_MAX_ATTEMPTS: tuple[int, ...] = (1, 1, 1, 2)
V1_HIGH_QUALITY_PER_MODEL_MAX_ATTEMPTS: tuple[int, ...] = (2, 2, 2, 2, 2)
# The two-route grounded-research pool permits one attempt per provider plus at most one
# bounded same-model structured-output repair. Infrastructure failures never retry the same
# model, and Flash is the only fallback.
GROUNDED_RESEARCH_MAX_TOTAL_PROVIDER_ATTEMPTS = 3
GROUNDED_RESEARCH_MAX_FALLBACK_TRANSITIONS = 1
GROUNDED_RESEARCH_PER_MODEL_MAX_ATTEMPTS: tuple[int, ...] = (2, 2)

MAX_TOTAL_PROVIDER_ATTEMPTS = 6
MAX_FALLBACK_TRANSITIONS = 3
MAX_SAME_MODEL_RETRIES = 1
MAX_STRUCTURED_OUTPUT_REPAIR_ATTEMPTS = 1
MAX_CUMULATIVE_RETRY_SLEEP_SECONDS = 45.0
DEFAULT_WALL_CLOCK_BUDGET_SECONDS = 300.0
NEWSROOM_LEAF_SCAN_MAX_FALLBACK_TRANSITIONS = 4
V1_HIGH_QUALITY_MAX_FALLBACK_TRANSITIONS = 4
NEWSROOM_LEAF_SCAN_WALL_CLOCK_BUDGET_SECONDS = 1200.0
NEWSROOM_GLOBAL_EDITOR_WALL_CLOCK_BUDGET_SECONDS = 1200.0

# --- terminal dispositions -------------------------------------------------------------
ACCEPTED = "ACCEPTED"
RETRY_BUDGET_EXHAUSTED = "LLM_RETRY_BUDGET_EXHAUSTED"
POOL_EXHAUSTED = "BLOCKED_AUTHORIZED_MODEL_POOL_EXHAUSTED"
TERMINAL_NON_RETRYABLE = "LLM_TERMINAL_NON_RETRYABLE_FAILURE"
IDENTITY_REJECTED = "BLOCKED_MODEL_IDENTITY_MISMATCH"
IDENTITY_NOT_VERIFIABLE = "MODEL_IDENTITY_NOT_PROVIDER_VERIFIABLE"

# --- failure classes -------------------------------------------------------------------
#: Infrastructure failures. Retry the same model, or advance to the next authorized model.
RETRYABLE_CLASSES: frozenset[str] = frozenset(
    {
        "connection_timeout",
        "read_timeout",
        "connection_reset",
        "dns_or_upstream_connection_failure",
        "http_408_request_timeout",
        "http_429_rate_limited",
        "quota_exhausted",
        "http_500_internal",
        "http_502_bad_gateway",
        "http_503_unavailable",
        "http_504_gateway_timeout",
        "provider_temporarily_unavailable",
        "requested_model_temporarily_unavailable",
    }
)

#: Failures where rotating models would be an attempt to bypass a gate rather than survive
#: an outage. These terminate the invocation. This list is the safety core of the router.
NON_RETRYABLE_CLASSES: frozenset[str] = frozenset(
    {
        "evidence_failure",
        "factual_validation_failure",
        "fabricated_numeric_material",
        "permission_failure",
        "publication_authority_failure",
        "freshness_or_material_delta_failure",
        "capital_chronicle_authority_mismatch",
        "policy_violation",
        "invalid_authorization",
        "malformed_business_input",
        "http_401_unauthorized",
        "http_403_forbidden",
        "invalid_request_or_schema_or_configuration",
        *COST_TERMINAL_FAILURE_CLASSES,
    }
)

#: Structured-output failures get one bounded same-model repair, then become
#: fallback-eligible. They are neither plain-retryable nor terminal.
STRUCTURED_OUTPUT_CLASSES: frozenset[str] = frozenset(
    {"structured_output_malformed", "structured_output_schema_invalid"}
)

#: A model identity mismatch is never retried against the same model — the gateway just
#: told us it will not honour the exact request — but the pool may still be walked.
IDENTITY_MISMATCH_CLASS = "resolved_model_mismatch"

#: Quota-style failures where a same-model retry is pointless. The router skips straight to
#: the next authorized model rather than burning an attempt it knows will fail.
SKIP_SAME_MODEL_RETRY_CLASSES: frozenset[str] = frozenset(
    {"quota_exhausted", "requested_model_temporarily_unavailable"}
)


class ModelRouterError(RuntimeError):
    """Fail-closed router composition error."""


def _hash(value: Any) -> str:
    if isinstance(value, (bytes, bytearray)):
        return sha256(bytes(value)).hexdigest()
    if isinstance(value, str):
        return sha256(value.encode("utf-8")).hexdigest()
    return sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    ).hexdigest()


def authority_packet() -> dict[str, Any]:
    """The machine-readable statement of what this router is authorized to do."""
    incident = build_acceptance_gemini_incident()
    packet = {
        "authority_id": AUTHORITY_ID,
        "authority_version": AUTHORITY_VERSION,
        "supersedes": SUPERSEDES_AUTHORITY_ID,
        "supersedes_rule": "prior authority prohibited all fallback; ordered fallback is now authorized",
        "gateway": GATEWAY,
        "ordered_model_pool": list(ORDERED_MODEL_POOL),
        "primary_model": PRIMARY_MODEL,
        "global_quality_first_pool_unchanged": True,
        "role_specific_model_pools": {
            role: list(pool) for role, pool in ROLE_MODEL_POOLS.items()
        },
        "newsroom_leaf_scan_model": NEWSROOM_LEAF_SCAN_MODEL,
        "newsroom_leaf_scan_is_semantic_labor_only": True,
        "newsroom_global_editor_uses_quality_first_pool": True,
        "article_writing_uses_quality_first_pool": True,
        "v1_grounded_research_gateway": GATEWAY,
        "v1_grounded_research_model_ladder": list(V1_GROUNDED_RESEARCH_MODEL_LADDER),
        "v1_grounded_research_model_order_is_deterministic": True,
        "v1_grounded_research_grants_factual_or_numeric_authority": False,
        "v1_grounded_research_grants_publication_authority": False,
        "v1_cx_final_fallback_model": CX_FINAL_FALLBACK_MODEL,
        "v1_cx_final_fallback_roles": [ARTICLE_WRITING_ROLE],
        "v1_cx_utility_rescue_is_separate_single_model_invocation": True,
        "v1_high_quality_retry_policy": {
            "max_total_provider_attempts": MAX_TOTAL_PROVIDER_ATTEMPTS,
            "max_fallback_transitions": V1_HIGH_QUALITY_MAX_FALLBACK_TRANSITIONS,
            "max_same_model_retries": 0,
            "max_structured_output_repair_attempts": 1,
            "per_model_max_attempts": list(V1_HIGH_QUALITY_PER_MODEL_MAX_ATTEMPTS),
            "bounded": True,
        },
        "v1_grounded_research_retry_policy": {
            "max_total_provider_attempts": GROUNDED_RESEARCH_MAX_TOTAL_PROVIDER_ATTEMPTS,
            "max_fallback_transitions": GROUNDED_RESEARCH_MAX_FALLBACK_TRANSITIONS,
            "max_same_model_retries": 0,
            "max_structured_output_repair_attempts": 1,
            "per_model_max_attempts": list(GROUNDED_RESEARCH_PER_MODEL_MAX_ATTEMPTS),
            "bounded": True,
            "two_model_pool_aligned": True,
        },
        "temporary_build_acceptance_gemini_incident_supported": True,
        "temporary_build_acceptance_gemini_incident_max_hours": 24,
        "temporary_build_acceptance_gemini_incident": incident,
        "production_launch_uses_incident_override_by_default": False,
        "newsroom_global_editor_retry_policy": {
            "max_total_provider_attempts": 5,
            "max_fallback_transitions": 3,
            "max_same_model_retries": 0,
            "max_structured_output_repair_attempts": 1,
            "per_model_max_attempts": list(
                NEWSROOM_GLOBAL_EDITOR_PER_MODEL_MAX_ATTEMPTS
            ),
            "wall_clock_budget_seconds": NEWSROOM_GLOBAL_EDITOR_WALL_CLOCK_BUDGET_SECONDS,
            "bounded": True,
        },
        "fallback_is_owner_authorized": True,
        "fallback_is_for_bounded_resilience_not_quality_gate_bypass": True,
        "silent_provider_side_substitution_permitted": False,
        "unauthorized_model_accepted": False,
        "unbounded_retry_permitted": False,
        "retry_budget_policy": retry_budget_policy(),
        "retryable_classes": sorted(RETRYABLE_CLASSES),
        "non_retryable_classes": sorted(NON_RETRYABLE_CLASSES),
        "structured_output_classes": sorted(STRUCTURED_OUTPUT_CLASSES),
        "skip_same_model_retry_classes": sorted(SKIP_SAME_MODEL_RETRY_CLASSES),
        "grants_publication_authority": False,
        "grants_factual_or_numeric_authority": False,
    }
    packet["authority_logical_hash"] = _hash(packet)
    return packet


def retry_budget_policy() -> dict[str, Any]:
    """The declared default budget. Recorded on every invocation for auditability."""
    return {
        "max_total_provider_attempts": MAX_TOTAL_PROVIDER_ATTEMPTS,
        "max_fallback_transitions": MAX_FALLBACK_TRANSITIONS,
        "max_same_model_retries": MAX_SAME_MODEL_RETRIES,
        "per_model_max_attempts": {
            model: PER_MODEL_MAX_ATTEMPTS[index]
            for index, model in enumerate(ORDERED_MODEL_POOL)
        },
        "max_structured_output_repair_attempts": MAX_STRUCTURED_OUTPUT_REPAIR_ATTEMPTS,
        "structured_repair_counts_against_total_attempts": True,
        "max_cumulative_retry_sleep_seconds": MAX_CUMULATIVE_RETRY_SLEEP_SECONDS,
        "default_wall_clock_budget_seconds": DEFAULT_WALL_CLOCK_BUDGET_SECONDS,
        "budget_resets_on_model_change": False,
        "budget_resets_on_reconstruction": False,
    }


def model_pool_for_role(role_task_id: str) -> tuple[str, ...]:
    """Return the one canonical model ordering for a semantic role."""
    # The owner-locked V1 research ladder is exact and must not be replaced by the
    # temporary build-acceptance Gemini incident seam.
    if str(role_task_id) == GROUNDED_RESEARCH_ROLE:
        return GROUNDED_RESEARCH_MODEL_POOL
    incident = build_acceptance_gemini_incident()
    if incident is not None:
        return _incident_model_pool_for_role(role_task_id, str(incident["mode"]))
    return ROLE_MODEL_POOLS.get(str(role_task_id), ORDERED_MODEL_POOL)


def retry_budget_for_role(*, role_task_id: str, logical_invocation_id: str) -> "RetryBudget":
    """Allocate one immutable bounded budget appropriate to the canonical role pool."""
    if str(role_task_id) == ARTICLE_WRITING_CX_RESCUE_ROLE:
        return RetryBudget(
            logical_invocation_id=logical_invocation_id,
            max_total_provider_attempts=1,
            max_fallback_transitions=0,
            max_same_model_retries=0,
            max_structured_output_repair_attempts=0,
            per_model_max_attempts=(1,),
        )
    if str(role_task_id) == GROUNDED_RESEARCH_ROLE:
        return RetryBudget(
            logical_invocation_id=logical_invocation_id,
            max_total_provider_attempts=GROUNDED_RESEARCH_MAX_TOTAL_PROVIDER_ATTEMPTS,
            max_fallback_transitions=GROUNDED_RESEARCH_MAX_FALLBACK_TRANSITIONS,
            max_same_model_retries=0,
            max_structured_output_repair_attempts=1,
            per_model_max_attempts=GROUNDED_RESEARCH_PER_MODEL_MAX_ATTEMPTS,
        )
    if build_acceptance_gemini_incident() is not None:
        wall_clock_budget_seconds = DEFAULT_WALL_CLOCK_BUDGET_SECONDS
        if str(role_task_id) == NEWSROOM_LEAF_SCAN_ROLE:
            wall_clock_budget_seconds = NEWSROOM_LEAF_SCAN_WALL_CLOCK_BUDGET_SECONDS
        elif str(role_task_id) == NEWSROOM_GLOBAL_EDITOR_ROLE:
            wall_clock_budget_seconds = NEWSROOM_GLOBAL_EDITOR_WALL_CLOCK_BUDGET_SECONDS
        return RetryBudget(
            logical_invocation_id=logical_invocation_id,
            max_total_provider_attempts=2,
            max_fallback_transitions=0,
            max_same_model_retries=1,
            wall_clock_budget_seconds=wall_clock_budget_seconds,
            per_model_max_attempts=(2,),
        )
    if str(role_task_id) == NEWSROOM_LEAF_SCAN_ROLE:
        return RetryBudget(
            logical_invocation_id=logical_invocation_id,
            max_fallback_transitions=NEWSROOM_LEAF_SCAN_MAX_FALLBACK_TRANSITIONS,
            wall_clock_budget_seconds=NEWSROOM_LEAF_SCAN_WALL_CLOCK_BUDGET_SECONDS,
            per_model_max_attempts=NEWSROOM_LEAF_SCAN_PER_MODEL_MAX_ATTEMPTS,
        )
    if str(role_task_id) == NEWSROOM_GLOBAL_EDITOR_ROLE:
        return RetryBudget(
            logical_invocation_id=logical_invocation_id,
            max_total_provider_attempts=5,
            max_fallback_transitions=3,
            max_same_model_retries=0,
            wall_clock_budget_seconds=NEWSROOM_GLOBAL_EDITOR_WALL_CLOCK_BUDGET_SECONDS,
            per_model_max_attempts=NEWSROOM_GLOBAL_EDITOR_PER_MODEL_MAX_ATTEMPTS,
        )
    if str(role_task_id) == ARTICLE_WRITING_ROLE:
        # One structured repair may be spent on whichever normal V1 quality model produced the
        # malformed/defective output. Four infrastructure failures plus that one repair still
        # leave the sixth and final slot for CX. Infrastructure never burns a same-model retry.
        return RetryBudget(
            logical_invocation_id=logical_invocation_id,
            max_total_provider_attempts=6,
            max_fallback_transitions=V1_HIGH_QUALITY_MAX_FALLBACK_TRANSITIONS,
            max_same_model_retries=0,
            max_structured_output_repair_attempts=1,
            per_model_max_attempts=V1_HIGH_QUALITY_PER_MODEL_MAX_ATTEMPTS,
        )
    return RetryBudget(logical_invocation_id=logical_invocation_id)


# ---------------------------------------------------------------------------
# Failure classification
# ---------------------------------------------------------------------------


def classify_failure(exc: BaseException | None = None, *, status_code: int | None = None,
                     explicit_class: str | None = None) -> str:
    """Map an exception or HTTP status onto exactly one declared failure class.

    An unrecognised failure is deliberately **not** treated as retryable. Defaulting to
    retry on an unknown error is how unbounded retry loops start.
    """
    if explicit_class:
        return str(explicit_class)
    if status_code is not None:
        mapping = {
            408: "http_408_request_timeout",
            429: "http_429_rate_limited",
            401: "http_401_unauthorized",
            403: "http_403_forbidden",
            400: "invalid_request_or_schema_or_configuration",
            422: "invalid_request_or_schema_or_configuration",
            500: "http_500_internal",
            502: "http_502_bad_gateway",
            503: "http_503_unavailable",
            504: "http_504_gateway_timeout",
        }
        if int(status_code) in mapping:
            return mapping[int(status_code)]
        return "invalid_request_or_schema_or_configuration"
    if exc is None:
        return "unclassified_failure"
    if isinstance(exc, TimeoutError):
        return "read_timeout"
    if isinstance(exc, ConnectionResetError):
        return "connection_reset"
    if isinstance(exc, ConnectionRefusedError):
        return "dns_or_upstream_connection_failure"
    if isinstance(exc, ConnectionError):
        return "dns_or_upstream_connection_failure"
    text = str(exc).lower()
    for needle, klass in (
        ("timed out", "read_timeout"),
        ("timeout", "connection_timeout"),
        ("reset by peer", "connection_reset"),
        ("temporarily unavailable", "provider_temporarily_unavailable"),
        ("quota", "quota_exhausted"),
        ("rate limit", "http_429_rate_limited"),
        ("name or service not known", "dns_or_upstream_connection_failure"),
    ):
        if needle in text:
            return klass
    return "unclassified_failure"


def is_retryable(failure_class: str) -> bool:
    return str(failure_class) in RETRYABLE_CLASSES


def is_terminal(failure_class: str) -> bool:
    return str(failure_class) in NON_RETRYABLE_CLASSES


def is_fallback_eligible(failure_class: str) -> bool:
    """Whether this failure may advance the router to the next authorized model."""
    klass = str(failure_class)
    if klass in NON_RETRYABLE_CLASSES:
        return False
    return (
        klass in RETRYABLE_CLASSES
        or klass in STRUCTURED_OUTPUT_CLASSES
        or klass == IDENTITY_MISMATCH_CLASS
    )


# ---------------------------------------------------------------------------
# Retry budget
# ---------------------------------------------------------------------------


@dataclass
class RetryBudget:
    """The immutable-at-creation budget for one logical invocation.

    ``consumed_*`` fields move; the declared ceilings never do. Rehydrating a snapshot
    restores consumption as well as ceilings, so a process restart cannot hand an
    invocation a fresh budget.
    """

    logical_invocation_id: str
    max_total_provider_attempts: int = MAX_TOTAL_PROVIDER_ATTEMPTS
    max_fallback_transitions: int = MAX_FALLBACK_TRANSITIONS
    max_same_model_retries: int = MAX_SAME_MODEL_RETRIES
    max_structured_output_repair_attempts: int = MAX_STRUCTURED_OUTPUT_REPAIR_ATTEMPTS
    max_cumulative_retry_sleep_seconds: float = MAX_CUMULATIVE_RETRY_SLEEP_SECONDS
    wall_clock_budget_seconds: float = DEFAULT_WALL_CLOCK_BUDGET_SECONDS
    per_model_max_attempts: tuple[int, ...] = PER_MODEL_MAX_ATTEMPTS

    consumed_attempts: int = 0
    consumed_fallback_transitions: int = 0
    consumed_repair_attempts: int = 0
    consumed_sleep_seconds: float = 0.0
    attempts_by_model: dict[str, int] = field(default_factory=dict)
    started_monotonic: float | None = None

    def __post_init__(self) -> None:
        if self.max_total_provider_attempts < 1:
            raise ModelRouterError("max_total_provider_attempts_must_be_positive")
        if self.max_total_provider_attempts > MAX_TOTAL_PROVIDER_ATTEMPTS:
            # Tightening is allowed; widening the declared launch policy is not.
            raise ModelRouterError(
                f"max_total_provider_attempts_exceeds_declared_policy:{self.max_total_provider_attempts}"
            )

    def start(self, *, now: Callable[[], float] = time.monotonic) -> None:
        if self.started_monotonic is None:
            self.started_monotonic = now()

    def elapsed_seconds(self, *, now: Callable[[], float] = time.monotonic) -> float:
        if self.started_monotonic is None:
            return 0.0
        return max(0.0, now() - self.started_monotonic)

    def remaining_attempts(self) -> int:
        return max(0, self.max_total_provider_attempts - self.consumed_attempts)

    def remaining_sleep_seconds(self) -> float:
        return max(0.0, self.max_cumulative_retry_sleep_seconds - self.consumed_sleep_seconds)

    def remaining_wall_clock_seconds(self, *, now: Callable[[], float] = time.monotonic) -> float:
        return max(0.0, self.wall_clock_budget_seconds - self.elapsed_seconds(now=now))

    def attempts_for(self, model: str) -> int:
        return int(self.attempts_by_model.get(str(model), 0))

    def model_attempts_remaining(self, priority_index: int, model: str) -> int:
        ceiling = (
            self.per_model_max_attempts[priority_index]
            if priority_index < len(self.per_model_max_attempts)
            else 1
        )
        return max(0, ceiling - self.attempts_for(model))

    def exhausted_reason(self, *, now: Callable[[], float] = time.monotonic) -> str | None:
        """The first hard budget this invocation has hit, if any."""
        if self.remaining_attempts() <= 0:
            return "max_total_provider_attempts"
        if self.remaining_wall_clock_seconds(now=now) <= 0.0:
            return "wall_clock_budget_seconds"
        return None

    def record_attempt(self, model: str) -> None:
        self.consumed_attempts += 1
        self.attempts_by_model[str(model)] = self.attempts_for(model) + 1

    def record_fallback_transition(self) -> None:
        self.consumed_fallback_transitions += 1

    def record_repair_attempt(self) -> None:
        self.consumed_repair_attempts += 1

    def record_sleep(self, seconds: float) -> None:
        self.consumed_sleep_seconds += max(0.0, float(seconds))

    def snapshot(self) -> dict[str, Any]:
        return {
            "logical_invocation_id": self.logical_invocation_id,
            "max_total_provider_attempts": self.max_total_provider_attempts,
            "max_fallback_transitions": self.max_fallback_transitions,
            "max_same_model_retries": self.max_same_model_retries,
            "max_structured_output_repair_attempts": self.max_structured_output_repair_attempts,
            "max_cumulative_retry_sleep_seconds": self.max_cumulative_retry_sleep_seconds,
            "wall_clock_budget_seconds": self.wall_clock_budget_seconds,
            "per_model_max_attempts": list(self.per_model_max_attempts),
            "consumed_attempts": self.consumed_attempts,
            "consumed_fallback_transitions": self.consumed_fallback_transitions,
            "consumed_repair_attempts": self.consumed_repair_attempts,
            "consumed_sleep_seconds": round(self.consumed_sleep_seconds, 4),
            "attempts_by_model": dict(self.attempts_by_model),
            "remaining_attempt_budget": self.remaining_attempts(),
        }

    @classmethod
    def from_snapshot(cls, snapshot: Mapping[str, Any]) -> "RetryBudget":
        """Rehydrate after a process restart **without** restoring spent budget.

        This is the reconstruction invariant: consumption is carried forward. A restart is
        not a way to earn more attempts.
        """
        budget = cls(
            logical_invocation_id=str(snapshot["logical_invocation_id"]),
            max_total_provider_attempts=int(snapshot["max_total_provider_attempts"]),
            max_fallback_transitions=int(snapshot["max_fallback_transitions"]),
            max_same_model_retries=int(snapshot["max_same_model_retries"]),
            max_structured_output_repair_attempts=int(
                snapshot["max_structured_output_repair_attempts"]
            ),
            max_cumulative_retry_sleep_seconds=float(
                snapshot["max_cumulative_retry_sleep_seconds"]
            ),
            wall_clock_budget_seconds=float(snapshot["wall_clock_budget_seconds"]),
            per_model_max_attempts=tuple(snapshot["per_model_max_attempts"]),
        )
        budget.consumed_attempts = int(snapshot["consumed_attempts"])
        budget.consumed_fallback_transitions = int(snapshot["consumed_fallback_transitions"])
        budget.consumed_repair_attempts = int(snapshot["consumed_repair_attempts"])
        budget.consumed_sleep_seconds = float(snapshot["consumed_sleep_seconds"])
        budget.attempts_by_model = dict(snapshot.get("attempts_by_model") or {})
        return budget


# ---------------------------------------------------------------------------
# Provider result
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ProviderResult:
    """One provider attempt's observable outcome, already stripped of secret material."""

    text: str | None = None
    resolved_model: str | None = None
    provider_invocation_id: str | None = None
    status_code: int | None = None
    retry_after_seconds: float | None = None
    usage: Mapping[str, Any] | None = None
    cost: Mapping[str, Any] | None = None
    error: BaseException | None = None
    failure_class: str | None = None


#: A provider callable takes (prompt, model, timeout_seconds) and returns a ProviderResult.
ProviderCallable = Callable[[str, str, float], ProviderResult]

#: A validator takes response text and returns either the legacy three-item result or a
#: four-item result whose final value is a safe static validation diagnostic code.
ValidatorCallable = Callable[
    [str],
    "tuple[bool, str | None, Any] | tuple[bool, str | None, Any, str | None]",
]


def _default_validator(text: str) -> "tuple[bool, str | None, Any]":
    return (True, None, text)


# ---------------------------------------------------------------------------
# The router
# ---------------------------------------------------------------------------


def route_llm_invocation(
    *,
    logical_invocation_id: str,
    role_task_id: str,
    prompt: str,
    provider_call: ProviderCallable,
    work_item_id: str | None = None,
    prompt_template: str = "unspecified",
    prompt_version: str = "v1",
    governed_input: Any = None,
    validator: ValidatorCallable | None = None,
    budget: RetryBudget | None = None,
    timeout_seconds: float = 60.0,
    repair_prompt_builder: Callable[[str, str, str | None], str] | None = None,
    sleeper: Callable[[float], None] = time.sleep,
    clock: Callable[[], float] = time.monotonic,
    model_pool: Sequence[str] = ORDERED_MODEL_POOL,
) -> dict[str, Any]:
    """Run one logical LLM invocation under the ordered-pool bounded-retry policy.

    Returns a complete evidence record. The caller receives the accepted output only when
    ``terminal_disposition == "ACCEPTED"``; every other disposition is a fail-closed stop
    with the full attempt trail preserved.
    """
    if not logical_invocation_id:
        raise ModelRouterError("logical_invocation_id_required")
    unauthorized = [m for m in model_pool if m not in AUTHORIZED_MODELS]
    if unauthorized:
        raise ModelRouterError(f"unauthorized_model_in_pool:{','.join(unauthorized)}")

    validate = validator or _default_validator
    budget = budget or RetryBudget(logical_invocation_id=logical_invocation_id)
    budget.start(now=clock)

    prompt_hash = _hash(prompt)
    governed_input_hash = _hash(governed_input) if governed_input is not None else None

    attempts: list[dict[str, Any]] = []
    models_attempted: list[str] = []
    disposition = POOL_EXHAUSTED
    selected_model: str | None = None
    accepted_output: Any = None
    budget_exhausted_reason: str | None = None
    identity_verifiable = True
    previous_model: str | None = None

    for priority_index, model in enumerate(model_pool):
        if disposition == ACCEPTED:
            break
        # A model change is a fallback transition; it never refreshes the budget.
        if previous_model is not None:
            if budget.consumed_fallback_transitions >= budget.max_fallback_transitions:
                budget_exhausted_reason = "max_fallback_transitions"
                disposition = RETRY_BUDGET_EXHAUSTED
                break
            budget.record_fallback_transition()

        fallback_from = previous_model
        fallback_reason = attempts[-1]["failure_class"] if attempts and previous_model else None
        previous_model = model
        repair_used_for_model = False

        while True:
            hard_stop = budget.exhausted_reason(now=clock)
            if hard_stop:
                budget_exhausted_reason = hard_stop
                disposition = RETRY_BUDGET_EXHAUSTED
                break
            if budget.model_attempts_remaining(priority_index, model) <= 0:
                break

            if model not in models_attempted:
                models_attempted.append(model)
            attempt_number_for_model = budget.attempts_for(model) + 1
            budget.record_attempt(model)
            started = clock()

            record: dict[str, Any] = {
                "logical_invocation_id": logical_invocation_id,
                "work_item_id": work_item_id,
                "role_task_id": role_task_id,
                "gateway": GATEWAY,
                "provider": GATEWAY,
                "model_priority_index": priority_index,
                "model_ladder_position": priority_index + 1,
                "requested_model": model,
                "attempt_number_global": budget.consumed_attempts,
                "attempt_number_for_model": attempt_number_for_model,
                "retry_number_for_model": attempt_number_for_model - 1,
                "fallback_from": fallback_from,
                "fallback_reason": fallback_reason,
                "prompt_template": prompt_template,
                "prompt_version": prompt_version,
                "prompt_logical_hash": prompt_hash,
                "governed_input_hash": governed_input_hash,
                "retry_budget_snapshot": budget.snapshot(),
            }

            try:
                result = provider_call(prompt, model, timeout_seconds)
            except BaseException as exc:  # noqa: BLE001 - classified, never swallowed
                result = ProviderResult(error=exc, failure_class=classify_failure(exc))

            latency = round(clock() - started, 4)
            failure_class = result.failure_class or (
                classify_failure(result.error, status_code=result.status_code)
                if (result.error is not None or result.status_code not in (None, 200))
                else None
            )
            record.update(
                {
                    "resolved_model": result.resolved_model,
                    "provider_invocation_id": result.provider_invocation_id,
                    "provider_status_class": _status_class(result.status_code),
                    "retry_after_seconds": result.retry_after_seconds,
                    "latency_seconds": latency,
                    "usage": dict(result.usage) if result.usage else None,
                    "cost": dict(result.cost) if result.cost else None,
                    "remaining_attempt_budget": budget.remaining_attempts(),
                }
            )

            # --- identity invariant, checked before any output is trusted ---------------
            if failure_class is None and result.resolved_model is not None:
                if not _same_model_identity(model, result.resolved_model):
                    failure_class = IDENTITY_MISMATCH_CLASS
                    record["identity_mismatch"] = {
                        "requested_model": model,
                        "resolved_model": result.resolved_model,
                    }
                elif not _is_authorized_identity(result.resolved_model):
                    failure_class = IDENTITY_MISMATCH_CLASS
                    record["identity_mismatch"] = {
                        "requested_model": model,
                        "resolved_model": result.resolved_model,
                        "reason": "resolved_model_not_in_authorized_pool",
                    }
            if result.resolved_model is None:
                identity_verifiable = False
                record["model_identity_provider_verified"] = False
            else:
                record["model_identity_provider_verified"] = failure_class != IDENTITY_MISMATCH_CLASS

            # --- structured validation -------------------------------------------------
            parsed: Any = None
            validation_diagnostic_code: str | None = None
            if failure_class is None:
                validation_result = validate(result.text or "")
                if len(validation_result) == 3:
                    ok, validation_failure, parsed = validation_result
                elif len(validation_result) == 4:
                    ok, validation_failure, parsed, validation_diagnostic_code = validation_result
                else:
                    raise ModelRouterError("validator_result_shape_invalid")
                record["structured_validation_result"] = "PASS" if ok else "FAIL"
                if validation_diagnostic_code is not None:
                    record["structured_validation_diagnostic_code"] = str(
                        validation_diagnostic_code
                    )
                if not ok:
                    failure_class = validation_failure or "structured_output_malformed"
            else:
                record["structured_validation_result"] = "NOT_EVALUATED"

            if result.text is not None:
                record["output_hash"] = _hash(result.text)

            record["failure_class"] = failure_class
            record["disposition"] = "accepted" if failure_class is None else "rejected"
            attempts.append(_redact(record))

            if failure_class is None:
                disposition = ACCEPTED
                selected_model = model
                accepted_output = parsed if parsed is not None else result.text
                break

            # --- terminal: never rotate models to bypass a gate -------------------------
            if is_terminal(failure_class):
                disposition = TERMINAL_NON_RETRYABLE
                break

            hard_stop = budget.exhausted_reason(now=clock)
            if hard_stop:
                budget_exhausted_reason = hard_stop
                disposition = RETRY_BUDGET_EXHAUSTED
                break

            # --- bounded same-model structured repair ----------------------------------
            if failure_class in STRUCTURED_OUTPUT_CLASSES:
                can_repair = (
                    not repair_used_for_model
                    and budget.consumed_repair_attempts
                    < budget.max_structured_output_repair_attempts
                    and budget.model_attempts_remaining(priority_index, model) > 0
                )
                if can_repair:
                    repair_used_for_model = True
                    budget.record_repair_attempt()
                    if repair_prompt_builder is not None:
                        prompt = repair_prompt_builder(
                            prompt,
                            result.text or "",
                            validation_diagnostic_code,
                        )
                        prompt_hash = _hash(prompt)
                    continue
                break  # repair spent or unavailable -> fallback-eligible

            # --- retry vs advance ------------------------------------------------------
            if not is_fallback_eligible(failure_class):
                disposition = TERMINAL_NON_RETRYABLE
                break

            if failure_class == IDENTITY_MISMATCH_CLASS:
                break  # same model will keep resolving elsewhere; advance the pool

            if failure_class in SKIP_SAME_MODEL_RETRY_CLASSES:
                break  # a same-model retry is known-futile; advance the pool

            retry_after = float(result.retry_after_seconds or 0.0)
            if retry_after > 0.0:
                if retry_after > budget.remaining_sleep_seconds() or retry_after > budget.remaining_wall_clock_seconds(now=clock):
                    # Waiting would blow the budget: advance instead of sleeping.
                    break
                budget.record_sleep(retry_after)
                sleeper(retry_after)

            if budget.model_attempts_remaining(priority_index, model) <= 0:
                break
            if budget.attempts_for(model) > budget.max_same_model_retries:
                break

        if disposition in (ACCEPTED, TERMINAL_NON_RETRYABLE, RETRY_BUDGET_EXHAUSTED):
            break

    if disposition == ACCEPTED and not identity_verifiable:
        # Honest downgrade: connectivity and output are fine, identity is not provable.
        identity_note = IDENTITY_NOT_VERIFIABLE
    else:
        identity_note = None

    summary = {
        "schema_version": SCHEMA_VERSION,
        "authority_id": AUTHORITY_ID,
        "gateway": GATEWAY,
        "provider": GATEWAY,
        "logical_invocation_id": logical_invocation_id,
        "work_item_id": work_item_id,
        "role_task_id": role_task_id,
        "terminal_disposition": disposition,
        "selected_model": selected_model,
        "terminal_selected_route": selected_model,
        "models_attempted_in_order": models_attempted,
        "total_attempts": budget.consumed_attempts,
        "total_fallback_transitions": budget.consumed_fallback_transitions,
        "total_structured_repair_attempts": budget.consumed_repair_attempts,
        "total_retry_sleep_seconds": round(budget.consumed_sleep_seconds, 4),
        "total_elapsed_seconds": round(budget.elapsed_seconds(now=clock), 4),
        "total_usage": _sum_usage(attempts),
        "total_cost": _sum_cost(attempts),
        "budget_exhausted": budget_exhausted_reason is not None,
        "budget_exhausted_reason": budget_exhausted_reason,
        "model_identity_provider_verifiable": identity_verifiable,
        "model_identity_note": identity_note,
        "retry_budget_policy": {
            "max_total_provider_attempts": budget.max_total_provider_attempts,
            "max_fallback_transitions": budget.max_fallback_transitions,
            "max_same_model_retries": budget.max_same_model_retries,
            "per_model_max_attempts": {
                model: (
                    budget.per_model_max_attempts[index]
                    if index < len(budget.per_model_max_attempts)
                    else 1
                )
                for index, model in enumerate(model_pool)
            },
            "max_structured_output_repair_attempts": (
                budget.max_structured_output_repair_attempts
            ),
            "structured_repair_counts_against_total_attempts": True,
            "max_cumulative_retry_sleep_seconds": (
                budget.max_cumulative_retry_sleep_seconds
            ),
            "default_wall_clock_budget_seconds": budget.wall_clock_budget_seconds,
            "budget_resets_on_model_change": False,
            "budget_resets_on_reconstruction": False,
        },
        "final_retry_budget_snapshot": budget.snapshot(),
        "attempts": attempts,
        "output": accepted_output if disposition == ACCEPTED else None,
        "fallback_grants_publication_authority": False,
        "fallback_output_uses_same_downstream_gates": True,
    }
    assert_no_secret_shaped_text(json.dumps(sanitize_for_output(_summary_without_output(summary))))
    return summary


def _summary_without_output(summary: Mapping[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in summary.items() if k != "output"}


def _bare_model_id(value: str) -> str:
    """The model ID without its gateway routing prefix or reasoning-effort suffix.

    9router accepts ``new/claude-fable-5`` and reports the effective model back as
    ``claude-fable-5``. Comparing raw strings would flag every healthy call as a
    substitution, so identity is compared on the bare ID. A genuine swap to a different
    model still differs after normalisation and is still caught.

    The pool also carries an opaque ``(effort)`` suffix on some entries (e.g.
    ``vx/gemini-3.1-pro-preview(high)``) that selects a request-time reasoning-effort
    parameter rather than naming a distinct model. The gateway reports the resolved model
    without that suffix, so it is stripped here for the same reason the prefix is: to avoid
    flagging a healthy, correctly-routed call as an identity mismatch.
    """
    text = str(value).strip()
    bare = text.split("/", 1)[1] if "/" in text else text
    if bare.endswith(")") and "(" in bare:
        bare = bare[: bare.rindex("(")]
    return bare


def _same_model_identity(requested: str, resolved: str) -> bool:
    return _bare_model_id(requested) == _bare_model_id(resolved)


def _is_authorized_identity(resolved: str) -> bool:
    bare = _bare_model_id(resolved)
    return any(_bare_model_id(model) == bare for model in AUTHORIZED_MODELS)


def _status_class(status_code: int | None) -> str | None:
    if status_code is None:
        return None
    code = int(status_code)
    if code < 300:
        return "2xx_success"
    if code < 400:
        return "3xx_redirect"
    if code < 500:
        return f"4xx_client_{code}"
    return f"5xx_server_{code}"


def _redact(record: Mapping[str, Any]) -> dict[str, Any]:
    """Strip any secret-shaped material before an attempt record leaves the router."""
    cleaned = sanitize_for_output(dict(record))
    for key in ("fallback_reason", "failure_class"):
        value = cleaned.get(key)
        if isinstance(value, str):
            cleaned[key] = redact_text(value)
    return cleaned


def _sum_usage(attempts: Sequence[Mapping[str, Any]]) -> dict[str, Any] | None:
    totals: dict[str, float] = {}
    seen = False
    for row in attempts:
        usage = row.get("usage")
        if not isinstance(usage, Mapping):
            continue
        seen = True
        for key, value in usage.items():
            if isinstance(value, (int, float)):
                totals[key] = totals.get(key, 0.0) + float(value)
    return {k: round(v, 6) for k, v in totals.items()} if seen else None


def _sum_cost(attempts: Sequence[Mapping[str, Any]]) -> dict[str, Any] | None:
    totals: dict[str, float] = {}
    seen = False
    for row in attempts:
        cost = row.get("cost")
        if not isinstance(cost, Mapping):
            continue
        seen = True
        for key, value in cost.items():
            if isinstance(value, (int, float)):
                totals[key] = totals.get(key, 0.0) + float(value)
    return {k: round(v, 8) for k, v in totals.items()} if seen else None
