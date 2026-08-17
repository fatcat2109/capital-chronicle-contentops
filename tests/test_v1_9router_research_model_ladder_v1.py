"""Owner-locked V1 grounded-research routing through 9Router.

All provider behavior here is injected and deterministic. No network, credential, article,
Capital Chronicle, browser, scheduler, or public-write action is performed.
"""
from __future__ import annotations

from live_contentops.nine_router_ordered_model_router_v2 import (
    ACCEPTED,
    GATEWAY,
    GROUNDED_RESEARCH_MODEL_POOL,
    GROUNDED_RESEARCH_PER_MODEL_MAX_ATTEMPTS,
    GROUNDED_RESEARCH_ROLE,
    MAX_TOTAL_PROVIDER_ATTEMPTS,
    POOL_EXHAUSTED,
    TERMINAL_NON_RETRYABLE,
    V1_GROUNDED_RESEARCH_MODEL_LADDER,
    V1_HIGH_QUALITY_MAX_FALLBACK_TRANSITIONS,
    ProviderResult,
    model_pool_for_role,
    retry_budget_for_role,
    route_llm_invocation,
)

EXPECTED_LADDER = (
    "cx/gpt-5.6-terra(high)",
    "vx/gemini-3.1-pro-preview(high)",
    "vx/gemini-3.5-flash(high)",
)


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


def _run(script, *, validator=None):
    calls: list[str] = []

    def provider(_prompt: str, model: str, _timeout: float) -> ProviderResult:
        calls.append(model)
        return script[model]

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


def test_primary_success_does_not_fallback() -> None:
    result, calls = _run({EXPECTED_LADDER[0]: _success(EXPECTED_LADDER[0])})
    assert result["terminal_disposition"] == ACCEPTED
    assert result["terminal_selected_route"] == EXPECTED_LADDER[0]
    assert calls == [EXPECTED_LADDER[0]]
    assert result["attempts"][0]["provider"] == GATEWAY == "9router"
    assert result["attempts"][0]["model_ladder_position"] == 1
    assert result["attempts"][0]["retry_number_for_model"] == 0


def test_primary_provider_failure_falls_back_to_gemini_pro() -> None:
    result, calls = _run(
        {
            EXPECTED_LADDER[0]: _unavailable(),
            EXPECTED_LADDER[1]: _success(EXPECTED_LADDER[1]),
        }
    )
    assert result["terminal_disposition"] == ACCEPTED
    assert result["terminal_selected_route"] == EXPECTED_LADDER[1]
    assert calls == list(EXPECTED_LADDER[:2])
    assert result["attempts"][1]["fallback_reason"] == "http_503_unavailable"


def test_primary_and_gemini_pro_failure_fall_back_to_flash() -> None:
    result, calls = _run(
        {
            EXPECTED_LADDER[0]: _unavailable(),
            EXPECTED_LADDER[1]: _unavailable(),
            EXPECTED_LADDER[2]: _success(EXPECTED_LADDER[2]),
        }
    )
    assert result["terminal_disposition"] == ACCEPTED
    assert result["terminal_selected_route"] == EXPECTED_LADDER[2]
    assert calls == list(EXPECTED_LADDER)


def test_all_three_provider_failures_terminalize_truthfully() -> None:
    result, calls = _run({model: _unavailable() for model in EXPECTED_LADDER})
    assert result["terminal_disposition"] == POOL_EXHAUSTED
    assert result["terminal_selected_route"] is None
    assert calls == list(EXPECTED_LADDER)
    assert result["models_attempted_in_order"] == list(EXPECTED_LADDER)


def test_evidence_rejection_does_not_trigger_model_shopping() -> None:
    result, calls = _run(
        {EXPECTED_LADDER[0]: _success(EXPECTED_LADDER[0])},
        validator=lambda _text: (False, "evidence_failure", None),
    )
    assert result["terminal_disposition"] == TERMINAL_NON_RETRYABLE
    assert calls == [EXPECTED_LADDER[0]]


def test_preexisting_research_retry_policy_is_preserved() -> None:
    budget = retry_budget_for_role(
        role_task_id=GROUNDED_RESEARCH_ROLE,
        logical_invocation_id="preserved-retry-policy",
    )
    assert budget.max_total_provider_attempts == MAX_TOTAL_PROVIDER_ATTEMPTS == 6
    assert budget.max_fallback_transitions == V1_HIGH_QUALITY_MAX_FALLBACK_TRANSITIONS == 4
    assert budget.max_same_model_retries == 0
    assert budget.max_structured_output_repair_attempts == 1
    assert budget.per_model_max_attempts == GROUNDED_RESEARCH_PER_MODEL_MAX_ATTEMPTS == (2, 2, 2)
    assert set(model_pool_for_role(GROUNDED_RESEARCH_ROLE)) == set(EXPECTED_LADDER)
