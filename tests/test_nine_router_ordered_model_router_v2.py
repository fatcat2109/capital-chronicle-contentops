"""Focused V1 Gemini-only model-authority and bounded-router regression tests.

These use injected providers only. They never read credentials, call a network, mutate a
runtime store, schedule work, or write to a public destination.
"""
from __future__ import annotations

import json

import pytest

from live_contentops.nine_router_llm_seam_v2 import (
    CURRENT_V1_ROUTED_ROLE_IDS,
    integration_manifest,
)
from live_contentops.nine_router_ordered_model_router_v2 import (
    ACCEPTED,
    ARTICLE_WRITING_ROLE,
    AUTHORIZED_MODELS,
    DEFAULT_WALL_CLOCK_BUDGET_SECONDS,
    GATEWAY,
    GROUNDED_RESEARCH_ROLE,
    MAX_TOTAL_PROVIDER_ATTEMPTS,
    ModelRouterError,
    NEWSROOM_GLOBAL_EDITOR_ROLE,
    NEWSROOM_LEAF_SCAN_ROLE,
    NON_RETRYABLE_CLASSES,
    ORDERED_MODEL_POOL,
    PRIMARY_MODEL,
    RETRY_BUDGET_EXHAUSTED,
    RetryBudget,
    TERMINAL_NON_RETRYABLE,
    V1_GEMINI_ONLY_MODEL_AUTHORITY_ID,
    ProviderResult,
    authority_packet,
    classify_failure,
    is_fallback_eligible,
    is_terminal,
    model_pool_for_role,
    retry_budget_for_role,
    retry_budget_policy,
    route_llm_invocation,
)

PRO, FLASH = ORDERED_MODEL_POOL
ALLOWED = {PRO, FLASH}
FORBIDDEN_V1_MODELS = {
    "new/claude-fable-5",
    "new/claude-opus-5",
    "new/gpt-5.6-sol-xhigh",
    "cx/gpt-5.6-sol(xhigh)",
    "cx/gpt-5.6-terra(high)",
}


def _success(model: str) -> ProviderResult:
    return ProviderResult(
        text='{"ok": true}',
        resolved_model=model,
        status_code=200,
        usage={"total_tokens": 2},
        provider_invocation_id=f"inv_{model}",
    )


def _scripted(outcomes: dict[str, list[ProviderResult]]):
    calls: list[str] = []

    def provider(_prompt: str, model: str, _timeout: float) -> ProviderResult:
        calls.append(model)
        values = outcomes[model]
        return values.pop(0) if len(values) > 1 else values[0]

    provider.calls = calls  # type: ignore[attr-defined]
    return provider


def _run(role: str, provider) -> dict:
    invocation_id = f"gemini-only-{role}"
    return route_llm_invocation(
        logical_invocation_id=invocation_id,
        role_task_id=role,
        prompt="synthetic model-authority test",
        provider_call=provider,
        model_pool=model_pool_for_role(role),
        budget=retry_budget_for_role(
            role_task_id=role,
            logical_invocation_id=invocation_id,
        ),
    )


def test_current_v1_routed_call_graph_reaches_only_the_two_gemini_models() -> None:
    """The seam-declared V1 call graph cannot select Fable, Opus, GPT/CX, or Terra."""
    manifest = integration_manifest()

    assert ORDERED_MODEL_POOL == (
        "vx/gemini-3.1-pro-preview(high)",
        "vx/gemini-3.5-flash(high)",
    )
    assert PRIMARY_MODEL == PRO
    assert AUTHORIZED_MODELS == ALLOWED
    assert not (AUTHORIZED_MODELS & FORBIDDEN_V1_MODELS)
    assert manifest["v1_gemini_only_model_authority"] is True
    assert manifest["forbidden_non_gemini_v1_models_reachable"] is False
    assert set(manifest["current_v1_routed_role_ids"]) == set(CURRENT_V1_ROUTED_ROLE_IDS)

    for role in CURRENT_V1_ROUTED_ROLE_IDS:
        pool = model_pool_for_role(role)
        assert pool
        assert set(pool) <= ALLOWED, role
        assert not (set(pool) & FORBIDDEN_V1_MODELS), role
        assert manifest["role_specific_model_pools"][role] == list(pool)


def test_role_ordering_matches_the_owner_authority() -> None:
    assert model_pool_for_role(NEWSROOM_LEAF_SCAN_ROLE) == (FLASH, PRO)
    assert model_pool_for_role(NEWSROOM_GLOBAL_EDITOR_ROLE) == (PRO, FLASH)
    assert model_pool_for_role(GROUNDED_RESEARCH_ROLE) == (PRO, FLASH)
    assert model_pool_for_role(ARTICLE_WRITING_ROLE) == (PRO, FLASH)
    assert model_pool_for_role("unlisted_future_v1_semantic_role") == (PRO, FLASH)


def test_authority_packet_is_permanent_gemini_only_and_owns_current_article_path() -> None:
    packet = authority_packet()
    assert packet["gateway"] == GATEWAY == "9router"
    assert packet["v1_model_authority_id"] == V1_GEMINI_ONLY_MODEL_AUTHORITY_ID
    assert packet["ordered_model_pool"] == [PRO, FLASH]
    assert packet["forbidden_non_gemini_v1_models_reachable"] is False
    assert packet["temporary_gemini_incident_override_supported"] is False
    assert packet["publication_qualified_article_uses_native_codex_desktop_xhigh"] is False
    assert packet["publication_qualified_article_uses_9router_gemini"] is True
    assert packet["codex_runtime_model_calls_required"] is False
    assert packet["grants_factual_or_numeric_authority"] is False
    assert packet["grants_publication_authority"] is False


def test_leaf_falls_back_flash_to_pro_only_for_eligible_provider_failure() -> None:
    provider = _scripted(
        {
            FLASH: [ProviderResult(failure_class="requested_model_temporarily_unavailable")],
            PRO: [_success(PRO)],
        }
    )
    result = _run(NEWSROOM_LEAF_SCAN_ROLE, provider)
    assert result["terminal_disposition"] == ACCEPTED
    assert result["selected_model"] == PRO
    assert provider.calls == [FLASH, PRO]
    assert set(result["models_attempted_in_order"]) <= ALLOWED


def test_global_assignment_and_grounded_research_fall_back_pro_to_flash_only() -> None:
    for role in (NEWSROOM_GLOBAL_EDITOR_ROLE, GROUNDED_RESEARCH_ROLE):
        provider = _scripted(
            {
                PRO: [ProviderResult(failure_class="requested_model_temporarily_unavailable")],
                FLASH: [_success(FLASH)],
            }
        )
        result = _run(role, provider)
        assert result["terminal_disposition"] == ACCEPTED
        assert result["selected_model"] == FLASH
        assert provider.calls == [PRO, FLASH]
        assert result["models_attempted_in_order"] == [PRO, FLASH]


def test_terminal_evidence_failure_never_rotates_models() -> None:
    provider = _scripted(
        {
            PRO: [ProviderResult(failure_class="evidence_failure")],
            FLASH: [_success(FLASH)],
        }
    )
    result = _run(GROUNDED_RESEARCH_ROLE, provider)
    assert result["terminal_disposition"] == TERMINAL_NON_RETRYABLE
    assert provider.calls == [PRO]
    assert result["models_attempted_in_order"] == [PRO]


def test_identity_mismatch_advances_only_to_the_other_authorized_gemini_model() -> None:
    provider = _scripted(
        {
            PRO: [_success(FLASH)],
            FLASH: [_success(FLASH)],
        }
    )
    result = _run(NEWSROOM_GLOBAL_EDITOR_ROLE, provider)
    assert result["terminal_disposition"] == ACCEPTED
    assert result["selected_model"] == FLASH
    assert provider.calls == [PRO, FLASH]
    assert all(model in ALLOWED for model in result["models_attempted_in_order"])


def test_budgets_are_finite_and_cannot_expand_the_authorized_pool() -> None:
    provider = _scripted(
        {
            PRO: [ProviderResult(failure_class="requested_model_temporarily_unavailable")],
            FLASH: [ProviderResult(failure_class="requested_model_temporarily_unavailable")],
        }
    )
    result = _run(ARTICLE_WRITING_ROLE, provider)
    assert result["terminal_disposition"] in {
        RETRY_BUDGET_EXHAUSTED,
        "BLOCKED_AUTHORIZED_MODEL_POOL_EXHAUSTED",
    }
    assert set(provider.calls) <= ALLOWED
    assert len(provider.calls) <= 2

    with pytest.raises(ModelRouterError, match="unauthorized_model_in_pool"):
        route_llm_invocation(
            logical_invocation_id="refuse-non-gemini",
            role_task_id=NEWSROOM_GLOBAL_EDITOR_ROLE,
            prompt="synthetic",
            provider_call=provider,
            model_pool=(PRO, "new/claude-fable-5"),
        )


def test_generic_router_budget_contract_remains_finite_across_the_two_gemini_routes() -> None:
    """The generic safety contract survives the authority-pool reduction intact."""
    policy = retry_budget_policy()
    assert policy["max_total_provider_attempts"] == MAX_TOTAL_PROVIDER_ATTEMPTS
    assert policy["max_total_provider_attempts"] < 7
    assert policy["budget_resets_on_model_change"] is False
    assert policy["budget_resets_on_reconstruction"] is False
    assert policy["default_wall_clock_budget_seconds"] == DEFAULT_WALL_CLOCK_BUDGET_SECONDS
    assert set(policy["per_model_max_attempts"]) == ALLOWED

    with pytest.raises(ModelRouterError, match="exceeds_declared_policy"):
        RetryBudget(logical_invocation_id="cannot-widen", max_total_provider_attempts=7)


@pytest.mark.parametrize(
    "failure_class",
    (
        "evidence_failure",
        "factual_validation_failure",
        "permission_failure",
        "publication_authority_failure",
        "capital_chronicle_authority_mismatch",
    ),
)
def test_truth_and_authority_failures_are_terminal_without_a_gemini_carousel(
    failure_class: str,
) -> None:
    assert failure_class in NON_RETRYABLE_CLASSES
    assert is_terminal(failure_class)
    assert not is_fallback_eligible(failure_class)
    provider = _scripted(
        {
            PRO: [ProviderResult(failure_class=failure_class)],
            FLASH: [_success(FLASH)],
        }
    )

    result = _run(GROUNDED_RESEARCH_ROLE, provider)

    assert result["terminal_disposition"] == TERMINAL_NON_RETRYABLE
    assert provider.calls == [PRO]
    assert result["models_attempted_in_order"] == [PRO]
    assert result["output"] is None


def test_retryable_timeout_gets_one_same_model_retry_before_fallback() -> None:
    provider = _scripted(
        {
            PRO: [ProviderResult(failure_class="read_timeout"), _success(PRO)],
            FLASH: [_success(FLASH)],
        }
    )

    result = route_llm_invocation(
        logical_invocation_id="same-model-retry",
        role_task_id="generic_router_regression",
        prompt="synthetic",
        provider_call=provider,
        model_pool=(PRO, FLASH),
        budget=RetryBudget(logical_invocation_id="same-model-retry"),
    )

    assert result["terminal_disposition"] == ACCEPTED
    assert result["selected_model"] == PRO
    assert provider.calls == [PRO, PRO]
    assert result["total_attempts"] == 2
    assert result["total_fallback_transitions"] == 0


def test_model_transition_does_not_reset_shared_attempt_budget() -> None:
    provider = _scripted(
        {
            PRO: [ProviderResult(failure_class="read_timeout")],
            FLASH: [ProviderResult(failure_class="read_timeout")],
        }
    )
    budget = RetryBudget(
        logical_invocation_id="no-budget-reset-on-transition",
        max_total_provider_attempts=2,
    )

    result = route_llm_invocation(
        logical_invocation_id="no-budget-reset-on-transition",
        role_task_id="generic_router_regression",
        prompt="synthetic",
        provider_call=provider,
        model_pool=(PRO, FLASH),
        budget=budget,
    )

    assert result["terminal_disposition"] == RETRY_BUDGET_EXHAUSTED
    assert provider.calls == [PRO, PRO]
    assert result["models_attempted_in_order"] == [PRO]
    assert result["final_retry_budget_snapshot"]["consumed_attempts"] == 2


def test_reconstructed_budget_carries_consumption_into_the_flash_fallback() -> None:
    original = RetryBudget(logical_invocation_id="reconstructed")
    original.record_attempt(PRO)
    original.record_attempt(PRO)
    resumed = RetryBudget.from_snapshot(original.snapshot())
    provider = _scripted({PRO: [_success(PRO)], FLASH: [_success(FLASH)]})

    result = route_llm_invocation(
        logical_invocation_id="reconstructed",
        role_task_id="generic_router_regression",
        prompt="synthetic",
        provider_call=provider,
        model_pool=(PRO, FLASH),
        budget=resumed,
    )

    assert result["terminal_disposition"] == ACCEPTED
    assert provider.calls == [FLASH]
    assert result["selected_model"] == FLASH
    assert result["total_attempts"] == 3
    assert result["attempts"][0]["attempt_number_global"] == 3


class _RecordingClock:
    def __init__(self) -> None:
        self.value = 0.0
        self.sleeps: list[float] = []

    def __call__(self) -> float:
        return self.value

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.value += seconds


def test_retry_after_is_bounded_and_recorded_in_the_single_shared_budget() -> None:
    clock = _RecordingClock()
    provider = _scripted(
        {
            PRO: [
                ProviderResult(failure_class="http_429_rate_limited", retry_after_seconds=2.0),
                _success(PRO),
            ],
            FLASH: [_success(FLASH)],
        }
    )

    result = route_llm_invocation(
        logical_invocation_id="bounded-sleep",
        role_task_id="generic_router_regression",
        prompt="synthetic",
        provider_call=provider,
        model_pool=(PRO, FLASH),
        budget=RetryBudget(logical_invocation_id="bounded-sleep"),
        clock=clock,
        sleeper=clock.sleep,
    )

    assert result["terminal_disposition"] == ACCEPTED
    assert provider.calls == [PRO, PRO]
    assert clock.sleeps == [2.0]
    assert result["total_retry_sleep_seconds"] == 2.0


def test_elapsed_wall_clock_budget_stops_before_any_provider_call() -> None:
    clock = _RecordingClock()
    budget = RetryBudget(
        logical_invocation_id="wall-clock-stop",
        wall_clock_budget_seconds=1.0,
    )
    budget.start(now=clock)
    clock.value = 2.0
    provider = _scripted({PRO: [_success(PRO)], FLASH: [_success(FLASH)]})

    result = route_llm_invocation(
        logical_invocation_id="wall-clock-stop",
        role_task_id="generic_router_regression",
        prompt="synthetic",
        provider_call=provider,
        model_pool=(PRO, FLASH),
        budget=budget,
        clock=clock,
    )

    assert result["terminal_disposition"] == RETRY_BUDGET_EXHAUSTED
    assert result["budget_exhausted_reason"] == "wall_clock_budget_seconds"
    assert provider.calls == []


def test_structured_repair_counts_once_and_retains_the_failed_attempt_evidence() -> None:
    provider = _scripted(
        {
            PRO: [
                ProviderResult(text="broken", resolved_model=PRO, status_code=200),
                ProviderResult(text='{"ok": true}', resolved_model=PRO, status_code=200),
            ],
            FLASH: [_success(FLASH)],
        }
    )

    def json_validator(text: str):
        try:
            return True, None, json.loads(text), None
        except json.JSONDecodeError:
            return False, "structured_output_malformed", None, "synthetic_json_required"

    result = route_llm_invocation(
        logical_invocation_id="structured-repair",
        role_task_id="generic_router_regression",
        prompt="synthetic",
        provider_call=provider,
        model_pool=(PRO, FLASH),
        budget=RetryBudget(logical_invocation_id="structured-repair"),
        validator=json_validator,
    )

    assert result["terminal_disposition"] == ACCEPTED
    assert result["total_structured_repair_attempts"] == 1
    assert result["total_attempts"] == 2
    assert result["output"] == {"ok": True}
    assert result["attempts"][0]["disposition"] == "rejected"
    assert result["attempts"][0]["output_hash"]
    assert result["attempts"][0]["structured_validation_diagnostic_code"] == (
        "synthetic_json_required"
    )


def test_unlisted_identity_is_rejected_then_only_the_other_gemini_route_is_tried() -> None:
    provider = _scripted(
        {
            PRO: [_success("unlisted-provider-model")],
            FLASH: [_success(FLASH)],
        }
    )

    result = _run(NEWSROOM_GLOBAL_EDITOR_ROLE, provider)

    assert result["terminal_disposition"] == ACCEPTED
    assert result["selected_model"] == FLASH
    assert provider.calls == [PRO, FLASH]
    assert result["attempts"][0]["failure_class"] == "resolved_model_mismatch"
    assert result["models_attempted_in_order"] == [PRO, FLASH]


def test_completed_evidence_is_hashed_redacted_and_never_grants_publication_authority() -> None:
    provider = _scripted(
        {
            PRO: [ProviderResult(failure_class="requested_model_temporarily_unavailable")],
            FLASH: [_success(FLASH)],
        }
    )

    result = route_llm_invocation(
        logical_invocation_id="evidence-fields",
        role_task_id="generic_router_regression",
        prompt="synthetic sk-super-secret-value-abcdefghijklmnop",
        provider_call=provider,
        work_item_id="work-item",
        governed_input={"approved": True},
        model_pool=(PRO, FLASH),
        budget=RetryBudget(logical_invocation_id="evidence-fields"),
    )

    first = result["attempts"][0]
    assert result["terminal_disposition"] == ACCEPTED
    assert first["prompt_logical_hash"]
    assert first["governed_input_hash"]
    assert first["requested_model"] == PRO
    assert first["retry_budget_snapshot"]["consumed_attempts"] == 1
    assert result["fallback_grants_publication_authority"] is False
    assert result["fallback_output_uses_same_downstream_gates"] is True
    assert "sk-super-secret" not in json.dumps(result, sort_keys=True)


def test_unknown_failure_and_non_200_statuses_never_become_an_eligible_fallback() -> None:
    assert classify_failure(RuntimeError("unrecognized")) == "unclassified_failure"
    assert not is_fallback_eligible("unclassified_failure")
    assert classify_failure(status_code=401) == "http_401_unauthorized"
    assert classify_failure(status_code=403) == "http_403_forbidden"
    assert is_terminal("http_401_unauthorized")
    assert is_terminal("http_403_forbidden")
