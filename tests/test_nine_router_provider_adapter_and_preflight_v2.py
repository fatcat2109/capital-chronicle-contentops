"""Gateway adapter and Gemini-only preflight tests with no real network calls."""
from __future__ import annotations

import json

import pytest

from live_contentops.nine_router_ordered_model_router_v2 import (
    GATEWAY,
    ORDERED_MODEL_POOL,
    ProviderResult,
    is_fallback_eligible,
    is_terminal,
)
from live_contentops.nine_router_preflight_v2 import (
    HEALTHY,
    IDENTITY_UNVERIFIABLE,
    PREFLIGHT_PROMPT,
    UNAVAILABLE,
    build_run_summary,
    preflight_model,
    run_preflight,
)
from live_contentops.nine_router_provider_adapter_v2 import (
    ALLOWED_GATEWAY_HOSTS,
    ENV_API_KEY,
    ENV_BASE_URL,
    NineRouterAdapterError,
    _classify_http_error,
    _load_json_body,
    _parse_sse,
    call_nine_router,
    credential_presence,
    normalize_model_identity,
    resolve_base_url,
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


def test_plain_gateway_json_with_a_done_sentinel_parses_before_sse_detection() -> None:
    body = (
        '{"id":"chatcmpl_synthetic","model":"gemini-3.1-pro-preview",'
        '"choices":[{"message":{"content":"READY"}}],'
        '"usage":{"total_tokens":7}}data: [DONE]'
    )

    payload = _load_json_body(body)

    assert payload is not None
    assert payload["model"] == "gemini-3.1-pro-preview"
    assert payload["choices"][0]["message"]["content"] == "READY"


def test_true_sse_stream_accumulates_the_completion_text() -> None:
    stream = (
        'data: {"choices":[{"delta":{"content":"RE"}}]}\n'
        'data: {"choices":[{"delta":{"content":"ADY"}}]}\n'
        "data: [DONE]\n"
    )

    assert _load_json_body(stream) is None
    assert _parse_sse(stream) == "READY"


def test_gateway_host_and_scheme_allowlist_fail_closed(monkeypatch) -> None:
    monkeypatch.setenv(ENV_BASE_URL, "https://untrusted.example/v1")
    with pytest.raises(NineRouterAdapterError, match="gateway_host_not_in_allowlist"):
        resolve_base_url()

    monkeypatch.setenv(ENV_BASE_URL, "file:///not-a-gateway")
    with pytest.raises(NineRouterAdapterError, match="gateway_scheme_not_allowed"):
        resolve_base_url()

    monkeypatch.setenv(ENV_BASE_URL, "http://localhost:20128/v1")
    assert resolve_base_url() == "http://localhost:20128/v1"
    assert "localhost" in ALLOWED_GATEWAY_HOSTS


def test_missing_credential_and_presence_reporting_never_leak_a_value(monkeypatch) -> None:
    monkeypatch.delenv(ENV_API_KEY, raising=False)
    with pytest.raises(NineRouterAdapterError, match=f"{ENV_API_KEY}_missing"):
        call_nine_router("prompt", PRO, 5.0)

    monkeypatch.setenv(ENV_API_KEY, "sk-super-secret-value-abcdefghijklmnop")
    presence = credential_presence()
    rendered = json.dumps(presence, sort_keys=True)
    assert "sk-super-secret" not in rendered
    assert "abcdefghijklmnop" not in rendered
    assert presence[ENV_API_KEY] == "present_redacted"


def test_model_specific_403_or_404_can_fall_back_but_credential_403_cannot() -> None:
    for status in (403, 404):
        model_scoped = _classify_http_error(status, '{"error":{"type":"invalid_model"}}')
        assert model_scoped == "requested_model_temporarily_unavailable"
        assert is_fallback_eligible(model_scoped)
        assert not is_terminal(model_scoped)

    assert _classify_http_error(403, '{"error":{"message":"invalid api key"}}') == (
        "http_403_forbidden"
    )
    assert is_terminal(_classify_http_error(401, "invalid_model"))


def test_preflight_records_unavailability_and_a_real_identity_mismatch_without_upgrading_them() -> None:
    unavailable = preflight_model(
        PRO,
        provider_call=lambda _p, _m, _t: ProviderResult(
            failure_class="requested_model_temporarily_unavailable"
        ),
    )
    assert unavailable["health"] == UNAVAILABLE
    assert unavailable["success"] is False

    mismatch = preflight_model(
        PRO,
        provider_call=lambda _p, _m, _t: _success(FLASH),
    )
    assert mismatch["health"] == "MODEL_IDENTITY_MISMATCH"
    assert mismatch["model_identity_provider_verified"] is False


def test_preflight_and_summary_aggregate_only_the_two_authorized_gemini_routes() -> None:
    def mixed_health(_prompt: str, model: str, _timeout: float) -> ProviderResult:
        if model == FLASH:
            return ProviderResult(failure_class="requested_model_temporarily_unavailable")
        return _success(model)

    preflight = run_preflight(provider_call=mixed_health)
    assert preflight["authorized_models_probed"] == [PRO, FLASH]
    assert preflight["healthy_count"] == 1
    assert preflight["unavailable_count"] == 1

    summary = build_run_summary(
        preflight=preflight,
        invocations=[
            {
                "total_attempts": 2,
                "total_fallback_transitions": 1,
                "selected_model": FLASH,
                "attempts": [
                    {
                        "requested_model": PRO,
                        "failure_class": "read_timeout",
                        "latency_seconds": 1.0,
                    },
                    {
                        "requested_model": FLASH,
                        "failure_class": None,
                        "fallback_reason": "read_timeout",
                        "latency_seconds": 2.0,
                        "usage": {"total_tokens": 9},
                        "cost": {"usd": 0.01},
                    },
                ],
            }
        ],
    )
    assert summary["total_model_attempts"] == 2
    assert summary["fallback_count"] == 1
    assert summary["successful_calls_by_model"] == {FLASH: 1}
    assert summary["retries_by_error_class"] == {"read_timeout": 1}
    assert summary["observed_token_usage"] == {"total_tokens": 9.0}
    assert summary["observed_cost"] == {"usd": 0.01}


def test_preflight_prompt_and_seam_manifest_remain_deterministic_and_gemini_only() -> None:
    from live_contentops.nine_router_llm_seam_v2 import (
        DETERMINISTIC_STAGES_NOT_MODEL_ASSISTED,
        integration_manifest,
    )

    manifest = integration_manifest()
    assert len(PREFLIGHT_PROMPT) < 200
    assert "READY" in PREFLIGHT_PROMPT
    assert manifest["ordered_model_pool"] == [PRO, FLASH]
    assert manifest["separate_routers_per_task"] == 0
    assert manifest["per_module_retry_implementations"] == 0
    assert manifest["forbidden_non_gemini_v1_models_reachable"] is False
    assert "editorial_review_orchestrator_v2.run_editorial_review" in (
        DETERMINISTIC_STAGES_NOT_MODEL_ASSISTED
    )
