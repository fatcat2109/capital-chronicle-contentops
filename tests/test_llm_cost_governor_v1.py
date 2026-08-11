from __future__ import annotations

from datetime import datetime, timezone

import pytest

from live_contentops.llm_cost_governor_v1 import (
    CYCLE_LOGICAL_BUDGET_EXHAUSTED,
    HARD_MAX_LOGICAL_CALLS_PER_CYCLE,
    HARD_MAX_PROVIDER_ATTEMPTS_PER_CYCLE,
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
        result = _invoke("logical-b", unavailable)

    assert provider_calls == HARD_MAX_PROVIDER_ATTEMPTS_PER_CYCLE
    assert result["terminal_disposition"] == "LLM_TERMINAL_NON_RETRYABLE_FAILURE"
    assert result["attempts"][-1]["failure_class"] == (
        "llm_cycle_provider_attempt_budget_exhausted"
    )
    snapshot = budget_snapshot("cycle-attempts", control_root=tmp_path)
    assert snapshot["cycle"]["provider_attempts"] == HARD_MAX_PROVIDER_ATTEMPTS_PER_CYCLE


def test_cycle_token_ceiling_stops_next_network_attempt(tmp_path):
    provider_calls = 0

    def large_usage(prompt, model, timeout):
        nonlocal provider_calls
        provider_calls += 1
        return ProviderResult(
            text="accepted", resolved_model=model, usage={"total_tokens": 79_000}
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
            text="accepted", resolved_model=model, usage={"total_tokens": 79_000}
        )

    for index in range(5):
        with llm_cycle_budget_scope(
            f"daily-cycle-{index}", control_root=tmp_path, now=NOW
        ):
            assert _invoke(f"daily-logical-{index}", large_usage)[
                "terminal_disposition"
            ] == "ACCEPTED"

    with llm_cycle_budget_scope("daily-cycle-blocked", control_root=tmp_path, now=NOW):
        blocked = _invoke("daily-logical-blocked", large_usage)

    assert provider_calls == 5
    assert blocked["attempts"][0]["failure_class"] == "llm_daily_token_budget_exhausted"
    assert budget_snapshot("daily-cycle-4", control_root=tmp_path)["day"][
        "accounted_tokens"
    ] == 395_000
