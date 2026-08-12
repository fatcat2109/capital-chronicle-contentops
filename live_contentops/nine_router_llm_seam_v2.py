"""The single seam every ContentOps LLM call site uses to reach the canonical router.

Existing call sites already accept an injectable provider callable and expect a plain
``str`` back. This module preserves that contract exactly — :func:`routed_llm_text` is a
drop-in for the old ``call_live_provider(prompt, provider, timeout)`` shape — while routing
the call through the ordered pool with a bounded retry budget underneath.

Keeping the adaptation here means no call site grows its own retry loop, its own model list,
or its own failure classifier. There is one pool and one classifier, consumed by all of
them.

Deterministic stages stay deterministic. SEO generation, visual adaptation, operator
package assembly, and ``editorial_review_orchestrator_v2`` make no model call today and
must not be given one: several of them assert ``model_call_performed: False`` and one exists
specifically to reject LLM-derived numeric authority.
"""
from __future__ import annotations

from typing import Any, Callable, Mapping

from live_contentops.llm_operator_control_v1 import (
    assert_llm_operator_execution_enabled,
)
from live_contentops.llm_cost_governor_v1 import (
    LLMCostBudgetExceededError,
    reconcile_provider_attempt,
    reserve_logical_invocation,
    reserve_provider_attempt,
)
from live_contentops.nine_router_ordered_model_router_v2 import (
    ACCEPTED,
    ORDERED_MODEL_POOL,
    ProviderResult,
    RetryBudget,
    model_pool_for_role,
    retry_budget_for_role,
    route_llm_invocation,
)

SCHEMA_VERSION = "contentops.nine_router_llm_seam.v2"

#: Role/task IDs for the call sites that genuinely invoke a model today. Recorded on every
#: attempt so evidence can be grouped by newsroom stage.
ROLE_ARTICLE_WRITING = "article_writing"
ROLE_PLATFORM_VARIANTS = "platform_native_variant_generation"
ROLE_EDITORIAL_REVIEW = "tier1_editorial_review"
ROLE_IDEA_RANKING = "substack_idea_ranking"
ROLE_NEWSROOM_ASSIGNMENT = "rolling_x_newsroom_assignment"
ROLE_NEWSROOM_LEAF_SCAN = "rolling_x_newsroom_leaf_scan"
ROLE_EDITORIAL_REVISION = "rolling_x_editorial_revision"
ROLE_STRUCTURED_REPAIR = "structured_output_repair"

INTEGRATED_ROLES: tuple[str, ...] = (
    ROLE_ARTICLE_WRITING,
    ROLE_PLATFORM_VARIANTS,
    ROLE_EDITORIAL_REVIEW,
    ROLE_IDEA_RANKING,
    ROLE_NEWSROOM_ASSIGNMENT,
    ROLE_NEWSROOM_LEAF_SCAN,
    ROLE_EDITORIAL_REVISION,
    ROLE_STRUCTURED_REPAIR,
)

#: Stages that are deliberately deterministic. Listed explicitly so a future change that
#: adds a model call to one of them is a visible decision rather than a silent drift.
DETERMINISTIC_STAGES_NOT_MODEL_ASSISTED: tuple[str, ...] = (
    "core_v0_closure_capabilities_v1.build_seo_contract",
    "core_v0_platform_visual_adaptation_v1",
    "multi_story_platform_native_operator_packages_v1",
    "editorial_review_orchestrator_v2.run_editorial_review",
    "ai_research_canonical_article_engine_v6.deterministic_article_repair",
)


class RoutedInvocationError(RuntimeError):
    """The router returned a non-accepted terminal disposition."""

    def __init__(self, summary: Mapping[str, Any]) -> None:
        self.summary = dict(summary)
        disposition = summary.get("terminal_disposition")
        reason = summary.get("budget_exhausted_reason")
        models = ",".join(summary.get("models_attempted_in_order") or [])
        super().__init__(
            f"{disposition}"
            + (f":{reason}" if reason else "")
            + (f" after [{models}]" if models else "")
        )


#: Every routed invocation's evidence, appended in call order. Callers may drain this to
#: fold router evidence into their own packets without threading a collector through.
_INVOCATION_LOG: list[dict[str, Any]] = []


def drain_invocation_log() -> list[dict[str, Any]]:
    """Return and clear the accumulated routed-invocation evidence."""
    drained = list(_INVOCATION_LOG)
    _INVOCATION_LOG.clear()
    return drained


def peek_invocation_log() -> list[dict[str, Any]]:
    return list(_INVOCATION_LOG)


def _default_provider_call(prompt: str, model: str, timeout: float) -> ProviderResult:
    from live_contentops.nine_router_provider_adapter_v2 import call_nine_router

    return call_nine_router(prompt, model, timeout)


def routed_llm_invocation(
    *,
    prompt: str,
    role_task_id: str,
    logical_invocation_id: str,
    work_item_id: str | None = None,
    timeout_seconds: float = 60.0,
    validator: Callable[[str], "tuple[bool, str | None, Any]"] | None = None,
    provider_call: Callable[[str, str, float], ProviderResult] | None = None,
    governed_input: Any = None,
    prompt_template: str = "unspecified",
    prompt_version: str = "v1",
    budget: RetryBudget | None = None,
    repair_prompt_builder: Callable[[str, str, str | None], str] | None = None,
) -> dict[str, Any]:
    """Run one logical invocation through the canonical router and record its evidence."""
    # Check once before routing and again immediately before every provider attempt. The second
    # check closes the race where the operator activates STOP during a retry/fallback sequence.
    assert_llm_operator_execution_enabled()
    reserve_logical_invocation(logical_invocation_id)
    raw_provider_call = provider_call or _default_provider_call

    def guarded_provider_call(provider_prompt: str, model: str, timeout: float) -> ProviderResult:
        assert_llm_operator_execution_enabled()
        try:
            reservation = reserve_provider_attempt(
                provider_prompt, logical_invocation_id=logical_invocation_id
            )
        except LLMCostBudgetExceededError as exc:
            return ProviderResult(error=exc, failure_class=exc.failure_class)
        try:
            result = raw_provider_call(provider_prompt, model, timeout)
        except BaseException:
            # No trusted usage is available, so the conservative reservation remains charged.
            raise
        reconcile_provider_attempt(
            reservation,
            result.usage,
            failure_class=result.failure_class,
        )
        return result

    role_pool = model_pool_for_role(role_task_id)
    summary = route_llm_invocation(
        logical_invocation_id=logical_invocation_id,
        role_task_id=role_task_id,
        work_item_id=work_item_id,
        prompt=prompt,
        provider_call=guarded_provider_call,
        validator=validator,
        governed_input=governed_input,
        prompt_template=prompt_template,
        prompt_version=prompt_version,
        timeout_seconds=timeout_seconds,
        budget=budget or retry_budget_for_role(
            role_task_id=role_task_id,
            logical_invocation_id=logical_invocation_id,
        ),
        repair_prompt_builder=repair_prompt_builder,
        model_pool=role_pool,
    )
    _INVOCATION_LOG.append(summary)
    return summary


def routed_llm_text(
    prompt: str,
    provider: str = "9router",
    timeout_seconds: float = 60.0,
    *,
    role_task_id: str = ROLE_ARTICLE_WRITING,
    logical_invocation_id: str | None = None,
    work_item_id: str | None = None,
    provider_call: Callable[[str, str, float], ProviderResult] | None = None,
) -> str:
    """Drop-in replacement for the legacy ``call_live_provider`` text call.

    Same positional signature and same ``str`` return, so existing call sites and their
    monkeypatch-based tests keep working. Raises :class:`RoutedInvocationError` when the
    router terminates without an accepted result, which the call sites already treat as a
    provider failure.
    """
    invocation_id = logical_invocation_id or _derive_invocation_id(role_task_id, prompt)
    summary = routed_llm_invocation(
        prompt=prompt,
        role_task_id=role_task_id,
        logical_invocation_id=invocation_id,
        work_item_id=work_item_id,
        timeout_seconds=timeout_seconds,
        provider_call=provider_call,
        prompt_template=role_task_id,
    )
    if summary["terminal_disposition"] != ACCEPTED:
        raise RoutedInvocationError(summary)
    output = summary["output"]
    return output if isinstance(output, str) else str(output)


def _derive_invocation_id(role_task_id: str, prompt: str) -> str:
    from hashlib import sha256

    digest = sha256(f"{role_task_id}:{prompt}".encode("utf-8")).hexdigest()[:20]
    return f"inv_{role_task_id}_{digest}"


def integration_manifest() -> dict[str, Any]:
    """Declare which stages route through the canonical router and which stay deterministic."""
    return {
        "schema_version": SCHEMA_VERSION,
        "canonical_router": "live_contentops.nine_router_ordered_model_router_v2.route_llm_invocation",
        "canonical_seam": "live_contentops.nine_router_llm_seam_v2.routed_llm_text",
        "provider_adapter": "live_contentops.nine_router_provider_adapter_v2.call_nine_router",
        "ordered_model_pool": list(ORDERED_MODEL_POOL),
        "role_specific_model_pools": {
            role: list(model_pool_for_role(role)) for role in INTEGRATED_ROLES
        },
        "global_quality_first_pool_unchanged": True,
        "integrated_roles": list(INTEGRATED_ROLES),
        "integrated_call_sites": {
            ROLE_ARTICLE_WRITING: "ai_research_canonical_article_engine_v6.run_article_engine",
            ROLE_PLATFORM_VARIANTS: (
                "platform_native_variant_generator_live_v6.generate_live_platform_variants"
            ),
            ROLE_EDITORIAL_REVIEW: "tier1_editorial_quality_v1.review_tier1_article_with_llm",
            ROLE_IDEA_RANKING: "substack_first_north_star_pipeline_loop_v1.rank_ideas_with_llm",
            ROLE_NEWSROOM_ASSIGNMENT: (
                "newsroom_assignment_scheduler_v1 compact global editorial ranking"
            ),
            ROLE_NEWSROOM_LEAF_SCAN: (
                "newsroom_assignment_scheduler_v1 partitioned semantic leaf scan"
            ),
            ROLE_EDITORIAL_REVISION: (
                "_eight_platform_substack_first_pipeline_impl_v1 rolling-X bounded revision"
            ),
            ROLE_STRUCTURED_REPAIR: (
                "nine_router_ordered_model_router_v2 bounded same-model repair (in-router)"
            ),
        },
        "deterministic_stages_not_model_assisted": list(
            DETERMINISTIC_STAGES_NOT_MODEL_ASSISTED
        ),
        "per_module_retry_implementations": 0,
        "separate_routers_per_task": 0,
        "distinct_model_lists": 1,
    }
