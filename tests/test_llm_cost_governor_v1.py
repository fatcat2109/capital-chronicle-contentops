from __future__ import annotations

from datetime import datetime, timezone

import pytest

from live_contentops.llm_cost_governor_v1 import (
    CYCLE_LOGICAL_BUDGET_EXHAUSTED,
    HARD_MAX_LOGICAL_CALLS_PER_CYCLE,
    HARD_MAX_PROVIDER_ATTEMPTS_PER_CYCLE,
    HARD_MAX_TOKENS_PER_CYCLE,
    LLMCostBudgetExceededError,
    budget_snapshot,
    llm_cycle_budget_scope,
    reserve_logical_invocation,
    reserve_provider_attempt,
)
from live_contentops.nine_router_llm_seam_v2 import (
    ROLE_ARTICLE_WRITING,
    routed_llm_invocation,
)
from live_contentops.nine_router_ordered_model_router_v2 import (
    V1_HIGH_QUALITY_MODEL_POOL,
    ProviderResult,
    model_pool_for_role,
)


NOW = datetime(2026, 8, 11, 12, 0, tzinfo=timezone.utc)


def _invoke(invocation_id, provider):
    return routed_llm_invocation(
        prompt="bounded governed prompt",
        role_task_id=ROLE_ARTICLE_WRITING,
        logical_invocation_id=invocation_id,
        provider_call=provider,
    )


def test_authorized_hard_ceiling_values_are_exact():
    assert HARD_MAX_LOGICAL_CALLS_PER_CYCLE == 6
    assert HARD_MAX_PROVIDER_ATTEMPTS_PER_CYCLE == 12
    assert HARD_MAX_TOKENS_PER_CYCLE == 250_000


def test_cycle_logical_call_budget_is_shared_and_cannot_reset(tmp_path):
    calls = 0

    def provider(prompt, model, timeout):
        nonlocal calls
        calls += 1
        return ProviderResult(
            text="accepted", resolved_model=model, usage={"total_tokens": 10}
        )

    with llm_cycle_budget_scope("cycle-logical", control_root=tmp_path, now=NOW):
        for index in range(HARD_MAX_LOGICAL_CALLS_PER_CYCLE):
            assert _invoke(f"logical-{index}", provider)["terminal_disposition"] == "ACCEPTED"
        with pytest.raises(LLMCostBudgetExceededError) as exc:
            _invoke("logical-over-hard-max", provider)

    assert exc.value.failure_class == CYCLE_LOGICAL_BUDGET_EXHAUSTED
    assert calls == HARD_MAX_LOGICAL_CALLS_PER_CYCLE
    snapshot = budget_snapshot("cycle-logical", control_root=tmp_path)
    assert len(snapshot["cycle"]["logical_invocation_ids"]) == HARD_MAX_LOGICAL_CALLS_PER_CYCLE


def test_provider_attempt_budget_spans_retries_model_changes_and_next_call(tmp_path):
    # CC-268: since 17 Aug (8f6e4422) every role routes over the two authorized Gemini models, and
    # a retryable failure makes one attempt per model. Six calls therefore use exactly the
    # 12-attempt cycle budget, and the seventh is refused before any provider call.
    pool = list(model_pool_for_role(ROLE_ARTICLE_WRITING))
    provider_calls = 0

    def unavailable(prompt, model, timeout):
        nonlocal provider_calls
        provider_calls += 1
        return ProviderResult(
            failure_class="read_timeout",
            resolved_model=None,
            usage={"total_tokens": 1},
        )

    with llm_cycle_budget_scope("cycle-attempts", control_root=tmp_path, now=NOW):
        results = [
            _invoke(f"logical-{index}", unavailable)
            for index in range(HARD_MAX_LOGICAL_CALLS_PER_CYCLE)
        ]
        calls_before_refusal = provider_calls
        with pytest.raises(LLMCostBudgetExceededError):
            _invoke("logical-over-budget", unavailable)

    assert len(pool) * HARD_MAX_LOGICAL_CALLS_PER_CYCLE == HARD_MAX_PROVIDER_ATTEMPTS_PER_CYCLE
    assert all(r["models_attempted_in_order"] == pool for r in results)
    assert provider_calls == calls_before_refusal == HARD_MAX_PROVIDER_ATTEMPTS_PER_CYCLE
    snapshot = budget_snapshot("cycle-attempts", control_root=tmp_path)
    assert snapshot["cycle"]["provider_attempts"] == HARD_MAX_PROVIDER_ATTEMPTS_PER_CYCLE


def test_proven_pre_generation_model_rejections_release_only_token_reservations(tmp_path):
    provider_calls = 0

    def unavailable(prompt, model, timeout):
        nonlocal provider_calls
        provider_calls += 1
        return ProviderResult(
            failure_class="requested_model_temporarily_unavailable",
            resolved_model=None,
            usage=None,
        )

    def accepted(prompt, model, timeout):
        nonlocal provider_calls
        provider_calls += 1
        return ProviderResult(
            text="accepted",
            resolved_model=model,
            usage={"total_tokens": 10},
        )

    with llm_cycle_budget_scope("cycle-pre-generation", control_root=tmp_path, now=NOW):
        exhausted = _invoke("unavailable-pool", unavailable)
        after_rejections = budget_snapshot("cycle-pre-generation", control_root=tmp_path)
        success = _invoke("quality-fallback-still-funded", accepted)

    assert exhausted["terminal_disposition"] == "BLOCKED_AUTHORIZED_MODEL_POOL_EXHAUSTED"
    assert after_rejections["cycle"]["accounted_tokens"] == 0
    assert after_rejections["cycle"]["provider_attempts"] == len(V1_HIGH_QUALITY_MODEL_POOL)
    assert success["terminal_disposition"] == "ACCEPTED"
    assert provider_calls == len(V1_HIGH_QUALITY_MODEL_POOL) + 1
    final = budget_snapshot("cycle-pre-generation", control_root=tmp_path)
    assert final["cycle"]["accounted_tokens"] == 10
    assert final["cycle"]["provider_attempts"] == len(V1_HIGH_QUALITY_MODEL_POOL) + 1


def test_the_thirteenth_provider_attempt_in_a_cycle_is_refused(tmp_path):
    # The refusal path the test above can no longer reach through the router (see CC-268 there).
    with llm_cycle_budget_scope("cycle-attempt-cap", control_root=tmp_path, now=NOW):
        reserve_logical_invocation("logical-cap")
        for _ in range(HARD_MAX_PROVIDER_ATTEMPTS_PER_CYCLE):
            reserve_provider_attempt("bounded governed prompt", logical_invocation_id="logical-cap")
        with pytest.raises(LLMCostBudgetExceededError) as exc:
            reserve_provider_attempt("bounded governed prompt", logical_invocation_id="logical-cap")
    assert exc.value.failure_class == "llm_cycle_provider_attempt_budget_exhausted"
    snapshot = budget_snapshot("cycle-attempt-cap", control_root=tmp_path)
    assert snapshot["cycle"]["provider_attempts"] == HARD_MAX_PROVIDER_ATTEMPTS_PER_CYCLE


def test_accepted_fallback_caches_model_scoped_unavailability_for_same_cycle(tmp_path):
    # CC-268: written against a four-model ladder; the live pool is two Gemini models since 17 Aug
    # (8f6e4422), so the ladder comes from the router and the last model is the one that accepts.
    pool = list(model_pool_for_role(ROLE_ARTICLE_WRITING))
    assert len(pool) >= 2
    accepting = pool[-1]
    provider_models = []

    def provider(prompt, model, timeout):
        provider_models.append(model)
        if model != accepting:
            return ProviderResult(
                failure_class="requested_model_temporarily_unavailable",
                usage=None,
            )
        return ProviderResult(
            text="accepted", resolved_model=model, usage={"total_tokens": 10}
        )

    with llm_cycle_budget_scope("cycle-model-cache", control_root=tmp_path, now=NOW):
        first = _invoke("global-editor", provider)
        second = _invoke("article-writer", provider)

    assert first["terminal_disposition"] == "ACCEPTED"
    assert second["terminal_disposition"] == "ACCEPTED"
    assert provider_models == [*pool, accepting]
    assert second["cycle_cached_unavailable_models_skipped"] == pool[:-1]
    assert second["models_attempted_in_order"] == [accepting]
    assert second["provider_network_calls_skipped_by_cycle_unavailability_cache"] == len(pool) - 1
    snapshot = budget_snapshot("cycle-model-cache", control_root=tmp_path)
    assert snapshot["cycle"]["provider_attempts"] == len(pool) + 1


def test_terminal_pool_exhaustion_does_not_poison_later_invocation(tmp_path):
    provider_calls = 0
    accept = False

    def provider(prompt, model, timeout):
        nonlocal provider_calls
        provider_calls += 1
        if not accept:
            return ProviderResult(
                failure_class="requested_model_temporarily_unavailable",
                usage=None,
            )
        return ProviderResult(
            text="accepted", resolved_model=model, usage={"total_tokens": 10}
        )

    with llm_cycle_budget_scope("cycle-no-poison", control_root=tmp_path, now=NOW):
        exhausted = _invoke("pool-exhausted", provider)
        accept = True
        recovered = _invoke("later-recovered", provider)

    assert exhausted["terminal_disposition"] == "BLOCKED_AUTHORIZED_MODEL_POOL_EXHAUSTED"
    assert recovered["terminal_disposition"] == "ACCEPTED"
    assert recovered["cycle_cached_unavailable_models_skipped"] == []
    assert provider_calls == len(V1_HIGH_QUALITY_MODEL_POOL) + 1


def test_untrusted_transport_failure_without_usage_retains_reservation(tmp_path):
    def ambiguous_transport(prompt, model, timeout):
        return ProviderResult(failure_class="read_timeout", resolved_model=None, usage=None)

    with llm_cycle_budget_scope("cycle-ambiguous-usage", control_root=tmp_path, now=NOW):
        _invoke("ambiguous-transport", ambiguous_transport)

    snapshot = budget_snapshot("cycle-ambiguous-usage", control_root=tmp_path)
    assert snapshot["cycle"]["accounted_tokens"] > 0


def test_cycle_token_ceiling_stops_next_network_attempt(tmp_path):
    provider_calls = 0

    def large_usage(prompt, model, timeout):
        nonlocal provider_calls
        provider_calls += 1
        return ProviderResult(
            text="accepted", resolved_model=model, usage={"total_tokens": 249_000}
        )

    with llm_cycle_budget_scope("cycle-tokens", control_root=tmp_path, now=NOW):
        assert _invoke("large-usage", large_usage)["terminal_disposition"] == "ACCEPTED"
        blocked = _invoke("after-large-usage", large_usage)

    assert provider_calls == 1
    assert blocked["attempts"][0]["failure_class"] == "llm_cycle_token_budget_exhausted"


def test_active_day_usage_is_telemetry_and_does_not_block_independent_cycles(tmp_path):
    provider_calls = 0

    def large_usage(prompt, model, timeout):
        nonlocal provider_calls
        provider_calls += 1
        return ProviderResult(
            text="accepted", resolved_model=model, usage={"total_tokens": 249_000}
        )

    for index in range(8):
        with llm_cycle_budget_scope(
            f"daily-cycle-{index}", control_root=tmp_path, now=NOW
        ):
            assert _invoke(f"daily-logical-{index}", large_usage)[
                "terminal_disposition"
            ] == "ACCEPTED"

    with llm_cycle_budget_scope("daily-cycle-continued", control_root=tmp_path, now=NOW):
        continued = _invoke("daily-logical-continued", large_usage)

    assert provider_calls == 9
    assert continued["terminal_disposition"] == "ACCEPTED"
    snapshot = budget_snapshot("daily-cycle-continued", control_root=tmp_path)
    assert snapshot["day"]["accounted_tokens"] == 2_241_000
    assert snapshot["limits"]["active_day_tokens"] == (
        "TELEMETRY_ONLY_PROVIDER_QUOTA_GOVERNS"
    )


def test_active_day_telemetry_does_not_weaken_cycle_caps(tmp_path):
    provider_calls = 0

    def large_usage(prompt, model, timeout):
        nonlocal provider_calls
        provider_calls += 1
        return ProviderResult(
            text="accepted", resolved_model=model, usage={"total_tokens": 249_000}
        )

    for index in range(8):
        with llm_cycle_budget_scope(
            f"telemetry-cycle-{index}", control_root=tmp_path, now=NOW
        ):
            assert _invoke(f"telemetry-logical-{index}", large_usage)[
                "terminal_disposition"
            ] == "ACCEPTED"

    with llm_cycle_budget_scope(
        "telemetry-cycle-continued", control_root=tmp_path, now=NOW
    ):
        continued = _invoke("telemetry-logical-continued", large_usage)

    assert continued["terminal_disposition"] == "ACCEPTED"
    assert provider_calls == 9
    snapshot = budget_snapshot("telemetry-cycle-continued", control_root=tmp_path)
    assert snapshot["limits"]["hard_max_cycle_tokens"] == 250_000
    assert snapshot["limits"]["hard_max_provider_attempts"] == 12
