"""Focused V1 Gemini-only model-authority and bounded-router regression tests.

These use injected providers only. They never read credentials, call a network, mutate a
runtime store, schedule work, or write to a public destination.
"""
from __future__ import annotations

import pytest

from live_contentops.nine_router_llm_seam_v2 import (
    CURRENT_V1_ROUTED_ROLE_IDS,
    integration_manifest,
)
from live_contentops.nine_router_ordered_model_router_v2 import (
    ACCEPTED,
    ARTICLE_WRITING_ROLE,
    AUTHORIZED_MODELS,
    GATEWAY,
    GROUNDED_RESEARCH_ROLE,
    ModelRouterError,
    NEWSROOM_GLOBAL_EDITOR_ROLE,
    NEWSROOM_LEAF_SCAN_ROLE,
    ORDERED_MODEL_POOL,
    PRIMARY_MODEL,
    RETRY_BUDGET_EXHAUSTED,
    TERMINAL_NON_RETRYABLE,
    V1_GEMINI_ONLY_MODEL_AUTHORITY_ID,
    ProviderResult,
    authority_packet,
    model_pool_for_role,
    retry_budget_for_role,
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


def test_authority_packet_is_permanent_gemini_only_and_preserves_native_xhigh_boundary() -> None:
    packet = authority_packet()
    assert packet["gateway"] == GATEWAY == "9router"
    assert packet["v1_model_authority_id"] == V1_GEMINI_ONLY_MODEL_AUTHORITY_ID
    assert packet["ordered_model_pool"] == [PRO, FLASH]
    assert packet["forbidden_non_gemini_v1_models_reachable"] is False
    assert packet["temporary_gemini_incident_override_supported"] is False
    assert packet["publication_qualified_article_uses_native_codex_desktop_xhigh"] is True
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
