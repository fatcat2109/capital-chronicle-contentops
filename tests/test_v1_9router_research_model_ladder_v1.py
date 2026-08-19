"""Owner-locked V1 grounded-research routing through 9Router.

All provider behavior here is injected and deterministic. No network, credential, article,
Capital Chronicle, browser, scheduler, or public-write action is performed.
"""
from __future__ import annotations

from live_contentops.nine_router_ordered_model_router_v2 import (
    ACCEPTED,
    GATEWAY,
    GROUNDED_RESEARCH_MAX_FALLBACK_TRANSITIONS,
    GROUNDED_RESEARCH_MAX_TOTAL_PROVIDER_ATTEMPTS,
    GROUNDED_RESEARCH_MODEL_POOL,
    GROUNDED_RESEARCH_PER_MODEL_MAX_ATTEMPTS,
    GROUNDED_RESEARCH_ROLE,
    POOL_EXHAUSTED,
    TERMINAL_NON_RETRYABLE,
    V1_GROUNDED_RESEARCH_MODEL_LADDER,
    ProviderResult,
    authority_packet,
    model_pool_for_role,
    retry_budget_for_role,
    route_llm_invocation,
)

EXPECTED_LADDER = (
    "vx/gemini-3.1-pro-preview(high)",
    "vx/gemini-3.5-flash(high)",
)
TERRA = "cx/gpt-5.6-terra(high)"


def _success(model: str) -> ProviderResult:
    return ProviderResult(
        text="NONCE_OK",
        resolved_model=model,
        status_code=200,
        usage={"total_tokens": 2},
    )


def _unavailable() -> ProviderResult:
    return ProviderResult(
        status_code=503,
        failure_class="http_503_unavailable",
    )


def _rate_limited() -> ProviderResult:
    return ProviderResult(status_code=429, failure_class="http_429_rate_limited")


def _unauthorized() -> ProviderResult:
    return ProviderResult(status_code=401, failure_class="http_401_unauthorized")


def _run(script, *, validator=None):
    calls: list[str] = []

    def provider(_prompt: str, model: str, _timeout: float) -> ProviderResult:
        calls.append(model)
        response = script[model]
        if isinstance(response, list):
            return response.pop(0)
        return response

    logical_id = "v1-research-owner-ladder-test"
    result = route_llm_invocation(
        logical_invocation_id=logical_id,
        role_task_id=GROUNDED_RESEARCH_ROLE,
        prompt="Return NONCE_OK",
        provider_call=provider,
        validator=validator,
        budget=retry_budget_for_role(
            role_task_id=GROUNDED_RESEARCH_ROLE,
            logical_invocation_id=logical_id,
        ),
        model_pool=model_pool_for_role(GROUNDED_RESEARCH_ROLE),
        sleeper=lambda _seconds: None,
    )
    return result, calls


def test_exact_owner_ladder_is_immutable_and_ignores_incident_override(monkeypatch) -> None:
    monkeypatch.setenv("CONTENTOPS_BUILD_ACCEPTANCE_GEMINI_INCIDENT_MODE", "FLASH_ONLY")
    monkeypatch.setenv(
        "CONTENTOPS_BUILD_ACCEPTANCE_GEMINI_INCIDENT_EXPIRES_AT_UTC",
        "2099-01-01T00:00:00Z",
    )
    assert V1_GROUNDED_RESEARCH_MODEL_LADDER == EXPECTED_LADDER
    assert GROUNDED_RESEARCH_MODEL_POOL is V1_GROUNDED_RESEARCH_MODEL_LADDER
    assert model_pool_for_role(GROUNDED_RESEARCH_ROLE) is GROUNDED_RESEARCH_MODEL_POOL
    assert TERRA not in model_pool_for_role(GROUNDED_RESEARCH_ROLE)


def test_primary_success_does_not_fallback() -> None:
    result, calls = _run({EXPECTED_LADDER[0]: _success(EXPECTED_LADDER[0])})
    assert result["terminal_disposition"] == ACCEPTED
    assert result["terminal_selected_route"] == EXPECTED_LADDER[0]
    assert calls == [EXPECTED_LADDER[0]]
    assert result["attempts"][0]["provider"] == GATEWAY == "9router"
    assert result["attempts"][0]["model_ladder_position"] == 1
    assert result["attempts"][0]["retry_number_for_model"] == 0


def test_eligible_pro_failure_falls_back_to_flash_and_has_no_third_route() -> None:
    result, calls = _run(
        {
            EXPECTED_LADDER[0]: _rate_limited(),
            EXPECTED_LADDER[1]: _success(EXPECTED_LADDER[1]),
        }
    )
    assert result["terminal_disposition"] == ACCEPTED
    assert result["terminal_selected_route"] == EXPECTED_LADDER[1]
    assert calls == list(EXPECTED_LADDER)
    assert TERRA not in calls
    assert result["attempts"][1]["fallback_reason"] == "http_429_rate_limited"


def test_both_provider_failures_terminalize_truthfully_without_terra() -> None:
    result, calls = _run({model: _unavailable() for model in EXPECTED_LADDER})
    assert result["terminal_disposition"] == POOL_EXHAUSTED
    assert result["terminal_selected_route"] is None
    assert calls == list(EXPECTED_LADDER)
    assert result["models_attempted_in_order"] == list(EXPECTED_LADDER)
    assert TERRA not in calls


def test_true_pro_401_is_terminal_without_flash() -> None:
    result, calls = _run({EXPECTED_LADDER[0]: _unauthorized()})
    assert result["terminal_disposition"] == TERMINAL_NON_RETRYABLE
    assert calls == [EXPECTED_LADDER[0]]


def test_evidence_rejection_does_not_trigger_model_shopping() -> None:
    result, calls = _run(
        {EXPECTED_LADDER[0]: _success(EXPECTED_LADDER[0])},
        validator=lambda _text: (False, "evidence_failure", None),
    )
    assert result["terminal_disposition"] == TERMINAL_NON_RETRYABLE
    assert calls == [EXPECTED_LADDER[0]]


def test_structured_output_repair_remains_bounded_on_pro() -> None:
    validations = iter(
        (
            (False, "structured_output_malformed", None),
            (True, None, "NONCE_OK"),
        )
    )
    result, calls = _run(
        {EXPECTED_LADDER[0]: [_success(EXPECTED_LADDER[0]), _success(EXPECTED_LADDER[0])]},
        validator=lambda _text: next(validations),
    )
    assert result["terminal_disposition"] == ACCEPTED
    assert calls == [EXPECTED_LADDER[0], EXPECTED_LADDER[0]]
    assert result["total_structured_repair_attempts"] == 1
    assert result["total_attempts"] == 2


def test_grounded_research_authority_packet_and_budget_match_two_model_pool() -> None:
    budget = retry_budget_for_role(
        role_task_id=GROUNDED_RESEARCH_ROLE,
        logical_invocation_id="preserved-retry-policy",
    )
    assert budget.max_total_provider_attempts == GROUNDED_RESEARCH_MAX_TOTAL_PROVIDER_ATTEMPTS == 3
    assert budget.max_fallback_transitions == GROUNDED_RESEARCH_MAX_FALLBACK_TRANSITIONS == 1
    assert budget.max_same_model_retries == 0
    assert budget.max_structured_output_repair_attempts == 1
    assert budget.per_model_max_attempts == GROUNDED_RESEARCH_PER_MODEL_MAX_ATTEMPTS == (2, 2)
    assert model_pool_for_role(GROUNDED_RESEARCH_ROLE) == EXPECTED_LADDER
    packet = authority_packet()
    assert packet["v1_grounded_research_model_ladder"] == list(EXPECTED_LADDER)
    assert packet["role_specific_model_pools"][GROUNDED_RESEARCH_ROLE] == list(EXPECTED_LADDER)
    assert packet["v1_grounded_research_retry_policy"] == {
        "max_total_provider_attempts": 3,
        "max_fallback_transitions": 1,
        "max_same_model_retries": 0,
        "max_structured_output_repair_attempts": 1,
        "per_model_max_attempts": [2, 2],
        "bounded": True,
        "two_model_pool_aligned": True,
    }
