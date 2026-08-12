from __future__ import annotations

from datetime import datetime, timezone

import pytest

from live_contentops.llm_cost_governor_v1 import (
    CYCLE_LOGICAL_BUDGET_EXHAUSTED,
    HARD_MAX_LOGICAL_CALLS_PER_CYCLE,
    HARD_MAX_PROVIDER_ATTEMPTS_PER_CYCLE,
    HARD_MAX_TOKENS_PER_ACTIVE_DAY,
    HARD_MAX_TOKENS_PER_CYCLE,
    LLMCostBudgetExceededError,
    budget_snapshot,
    llm_cycle_budget_scope,
)
from live_contentops.nine_router_llm_seam_v2 import (
    ROLE_ARTICLE_WRITING,
    routed_llm_invocation,
)
from live_contentops.nine_router_ordered_model_router_v2 import ProviderResult


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
    assert HARD_MAX_TOKENS_PER_ACTIVE_DAY == 2_000_000


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
        _invoke("logical-a", unavailable)
        _invoke("logical-b", unavailable)
        result = _invoke("logical-c", unavailable)

    assert provider_calls == HARD_MAX_PROVIDER_ATTEMPTS_PER_CYCLE
    assert result["terminal_disposition"] == "LLM_TERMINAL_NON_RETRYABLE_FAILURE"
    assert result["attempts"][-1]["failure_class"] == (
        "llm_cycle_provider_attempt_budget_exhausted"
    )
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
    assert after_rejections["cycle"]["provider_attempts"] == 4
    assert success["terminal_disposition"] == "ACCEPTED"
    assert provider_calls == 5
    final = budget_snapshot("cycle-pre-generation", control_root=tmp_path)
    assert final["cycle"]["accounted_tokens"] == 10
    assert final["cycle"]["provider_attempts"] == 5


def test_accepted_fallback_caches_model_scoped_unavailability_for_same_cycle(tmp_path):
    provider_models = []

    def provider(prompt, model, timeout):
        provider_models.append(model)
        if model != "vx/gemini-3.1-pro-preview(high)":
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
    assert provider_models == [
        "new/claude-fable-5",
        "new/gpt-5.6-sol-xhigh",
        "new/claude-opus-5",
        "vx/gemini-3.1-pro-preview(high)",
        "vx/gemini-3.1-pro-preview(high)",
    ]
    assert second["cycle_cached_unavailable_models_skipped"] == [
        "new/claude-fable-5",
        "new/gpt-5.6-sol-xhigh",
        "new/claude-opus-5",
    ]
    assert second["models_attempted_in_order"] == [
        "vx/gemini-3.1-pro-preview(high)"
    ]
    assert second["provider_network_calls_skipped_by_cycle_unavailability_cache"] == 3
    snapshot = budget_snapshot("cycle-model-cache", control_root=tmp_path)
    assert snapshot["cycle"]["provider_attempts"] == 5


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
    assert provider_calls == 5


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


def test_daily_token_budget_persists_across_independent_cycle_scopes(tmp_path):
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

    with llm_cycle_budget_scope("daily-cycle-blocked", control_root=tmp_path, now=NOW):
        blocked = _invoke("daily-logical-blocked", large_usage)

    assert provider_calls == 8
    assert blocked["attempts"][0]["failure_class"] == "llm_daily_token_budget_exhausted"
    assert budget_snapshot("daily-cycle-7", control_root=tmp_path)["day"][
        "accounted_tokens"
    ] == 1_992_000
