"""Gateway adapter and Gemini-only preflight tests with no real network calls."""
from __future__ import annotations

import pytest

from live_contentops.nine_router_ordered_model_router_v2 import (
    GATEWAY,
    ORDERED_MODEL_POOL,
    ProviderResult,
)
from live_contentops.nine_router_preflight_v2 import (
    HEALTHY,
    IDENTITY_UNVERIFIABLE,
    build_run_summary,
    preflight_model,
    run_preflight,
)
from live_contentops.nine_router_provider_adapter_v2 import (
    ENV_API_KEY,
    NineRouterAdapterError,
    _classify_http_error,
    call_nine_router,
    normalize_model_identity,
    split_model_and_effort,
)

PRO, FLASH = ORDERED_MODEL_POOL


def _success(model: str) -> ProviderResult:
    return ProviderResult(
        text="READY",
        resolved_model=model,
        status_code=200,
        usage={"total_tokens": 7},
        provider_invocation_id="inv_1",
    )


def test_exact_gemini_effort_and_identity_are_preserved_at_the_wire_boundary() -> None:
    assert split_model_and_effort(PRO) == ("vx/gemini-3.1-pro-preview", "high")
    assert split_model_and_effort(FLASH) == ("vx/gemini-3.5-flash", "high")
    assert normalize_model_identity(PRO) == "gemini-3.1-pro-preview"
    assert normalize_model_identity(FLASH) == "gemini-3.5-flash"


def test_adapter_refuses_an_unapproved_model_before_any_network_call(monkeypatch) -> None:
    monkeypatch.setenv(ENV_API_KEY, "dummy")
    with pytest.raises(NineRouterAdapterError, match="unauthorized_model"):
        call_nine_router("prompt", "new/claude-fable-5", 5.0)


def test_model_scoped_403_can_fall_back_but_credential_403_is_terminal() -> None:
    assert _classify_http_error(
        403, '{"error":{"code":"permission_denied","type":"invalid_model"}}'
    ) == "requested_model_temporarily_unavailable"
    assert _classify_http_error(403, '{"error":{"message":"invalid api key"}}') == (
        "http_403_forbidden"
    )


def test_preflight_records_two_authorized_gemini_models_without_public_actions() -> None:
    result = run_preflight(provider_call=lambda _p, model, _t: _success(model))
    assert result["authorized_models_probed"] == [PRO, FLASH]
    assert len(result["per_model"]) == 2
    assert result["healthy_count"] == 2
    assert result["public_write_performed"] is False
    assert result["dispatch_performed"] is False
    assert result["scheduler_mutated"] is False


def test_preflight_never_upgrades_unverifiable_identity_to_healthy() -> None:
    row = preflight_model(
        PRO,
        provider_call=lambda _p, _m, _t: ProviderResult(text="READY", resolved_model=None),
    )
    assert row["health"] == IDENTITY_UNVERIFIABLE
    assert row["model_identity_provider_verified"] is False


def test_preflight_accepts_exact_provider_identity() -> None:
    row = preflight_model(PRO, provider_call=lambda _p, _m, _t: _success(PRO))
    assert row["health"] == HEALTHY
    assert row["model_identity_provider_verified"] is True


def test_run_summary_keeps_gateway_and_zero_write_safety_contract() -> None:
    summary = build_run_summary()
    assert summary["gateway"] == GATEWAY
    assert summary["ordered_model_pool"] == [PRO, FLASH]
    assert summary["public_write_performed"] is False
    assert summary["platform_action_performed"] is False
    assert summary["dispatch_performed"] is False
    assert summary["scheduler_mutated"] is False
    assert summary["capital_chronicle_authority_mutated"] is False
