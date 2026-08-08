"""Tests for the 9router provider adapter and the bounded no-write preflight.

These cover the adapter's parsing, allowlist, redaction, and error-classification behaviour
against synthetic responses shaped like the real gateway's. No network call is made here;
the real four-model preflight is executed separately and its result is committed as
evidence.
"""
from __future__ import annotations

import json

import pytest

from live_contentops.nine_router_ordered_model_router_v2 import (
    ACCEPTED,
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

P0, P1, P2, P3 = ORDERED_MODEL_POOL

#: A real gateway body: plain JSON with a trailing SSE sentinel appended.
REAL_BODY = (
    '{"id":"chatcmpl-msg_abc","object":"chat.completion","created":1786074773,'
    '"model":"claude-fable-5","choices":[{"index":0,"message":{"role":"assistant",'
    '"content":"READY"},"finish_reason":"stop"}],'
    '"usage":{"prompt_tokens":2559,"completion_tokens":4,"total_tokens":2563}}data: [DONE]'
)


def test_gateway_body_with_trailing_done_sentinel_parses_as_json() -> None:
    """The gateway appends ``data: [DONE]`` to a plain JSON body; that must not break parsing."""
    payload = _load_json_body(REAL_BODY)
    assert payload is not None
    assert payload["model"] == "claude-fable-5"
    assert payload["choices"][0]["message"]["content"] == "READY"
    assert payload["usage"]["total_tokens"] == 2563


def test_true_sse_stream_still_accumulates() -> None:
    stream = (
        'data: {"choices":[{"delta":{"content":"RE"}}]}\n'
        'data: {"choices":[{"delta":{"content":"ADY"}}]}\n'
        "data: [DONE]\n"
    )
    assert _load_json_body(stream) is None
    assert _parse_sse(stream) == "READY"


def test_split_model_and_effort_extracts_the_trailing_selector() -> None:
    """The gateway builds its Vertex endpoint by appending the model string directly, so a
    trailing "(high)" produces an Invalid Endpoint name (HTTP 400) rather than routing to a
    high-effort variant. The wire request must carry the bare model plus a separate
    ``reasoning_effort`` field; the pool entry itself stays one opaque authorized string.
    """
    assert split_model_and_effort("vx/gemini-3.1-pro-preview(high)") == (
        "vx/gemini-3.1-pro-preview",
        "high",
    )
    assert split_model_and_effort("new/claude-fable-5") == ("new/claude-fable-5", None)


def test_model_identity_normalisation_strips_the_routing_prefix() -> None:
    # The gateway accepts "new/claude-fable-5" and reports "claude-fable-5".
    assert normalize_model_identity("new/claude-fable-5") == "claude-fable-5"
    assert normalize_model_identity("claude-fable-5") == "claude-fable-5"
    # The trailing "(high)" selects a request-time reasoning-effort parameter, not a
    # distinct model, so it is stripped along with the gateway prefix.
    assert normalize_model_identity("vx/gemini-3.1-pro-preview(high)") == "gemini-3.1-pro-preview"
    assert normalize_model_identity(None) is None
    # A genuine substitution still differs after normalisation.
    assert normalize_model_identity("new/claude-opus-5") != normalize_model_identity(
        "new/claude-fable-5"
    )


def test_gateway_host_allowlist_fails_closed(monkeypatch) -> None:
    monkeypatch.setenv(ENV_BASE_URL, "https://evil.example.com/v1")
    with pytest.raises(NineRouterAdapterError, match="gateway_host_not_in_allowlist"):
        resolve_base_url()
    monkeypatch.setenv(ENV_BASE_URL, "http://localhost:20128/v1")
    assert resolve_base_url() == "http://localhost:20128/v1"
    assert "localhost" in ALLOWED_GATEWAY_HOSTS


def test_non_http_scheme_is_refused(monkeypatch) -> None:
    monkeypatch.setenv(ENV_BASE_URL, "file:///etc/passwd")
    with pytest.raises(NineRouterAdapterError, match="gateway_scheme_not_allowed"):
        resolve_base_url()


def test_unauthorized_model_is_refused_before_any_network_call(monkeypatch) -> None:
    monkeypatch.setenv(ENV_API_KEY, "dummy")
    with pytest.raises(NineRouterAdapterError, match="unauthorized_model"):
        call_nine_router("prompt", "vendor/cheap-unlisted-model", 5.0)


def test_missing_credential_fails_closed(monkeypatch) -> None:
    monkeypatch.delenv(ENV_API_KEY, raising=False)
    with pytest.raises(NineRouterAdapterError, match=f"{ENV_API_KEY}_missing"):
        call_nine_router("prompt", P0, 5.0)


def test_credential_presence_reports_presence_only(monkeypatch) -> None:
    monkeypatch.setenv(ENV_API_KEY, "sk-super-secret-value-abcdefghijklmnop")
    presence = credential_presence()
    blob = json.dumps(presence)
    assert "sk-super-secret" not in blob
    assert "abcdefghijklmnop" not in blob
    assert presence[ENV_API_KEY] in ("present_redacted", "missing")


def test_model_scoped_403_is_fallback_eligible_but_credential_403_is_terminal() -> None:
    """A gateway that lacks one model must be failed over, not treated as an auth failure."""
    model_scoped = _classify_http_error(
        403, '{"error":{"code":"permission_denied","type":"invalid_model"}}'
    )
    assert model_scoped == "requested_model_temporarily_unavailable"
    assert is_fallback_eligible(model_scoped)
    assert not is_terminal(model_scoped)

    credential = _classify_http_error(403, '{"error":{"message":"invalid api key"}}')
    assert credential == "http_403_forbidden"
    assert is_terminal(credential), "an ambiguous 403 must stay fail-closed"

    assert is_terminal(_classify_http_error(401, "anything at all, including invalid_model"))


# ---------------------------------------------------------------------------
# Preflight
# ---------------------------------------------------------------------------


def _fake(text="READY", model=P0, **kw):
    return lambda prompt, m, t: ProviderResult(
        text=text, resolved_model=model, status_code=200,
        usage={"total_tokens": 7}, provider_invocation_id="inv_1", **kw
    )


def test_preflight_marks_a_verified_model_healthy() -> None:
    row = preflight_model(P0, provider_call=_fake(model="claude-fable-5"))
    assert row["health"] == HEALTHY
    assert row["model_identity_provider_verified"] is True
    assert row["response_matched_expected_token"] is True
    assert row["usage"] == {"total_tokens": 7}
    assert row["public_write_performed"] is False
    assert row["platform_action_performed"] is False


def test_preflight_records_unavailability_honestly() -> None:
    def unavailable(prompt, model, timeout):
        return ProviderResult(failure_class="requested_model_temporarily_unavailable")

    row = preflight_model(P1, provider_call=unavailable)
    assert row["health"] == UNAVAILABLE
    assert row["success"] is False
    assert row["failure_class"] == "requested_model_temporarily_unavailable"


def test_preflight_never_upgrades_unverifiable_identity_to_pass() -> None:
    def silent(prompt, model, timeout):
        return ProviderResult(text="READY", resolved_model=None, status_code=200)

    row = preflight_model(P0, provider_call=silent)
    assert row["health"] == IDENTITY_UNVERIFIABLE
    assert row["model_identity_provider_verifiable"] is False
    assert row["model_identity_provider_verified"] is False


def test_preflight_flags_a_genuine_substitution() -> None:
    row = preflight_model(P0, provider_call=_fake(model="claude-opus-5"))
    assert row["health"] == "MODEL_IDENTITY_MISMATCH"
    assert row["model_identity_provider_verified"] is False


def test_run_preflight_summarises_all_four_models() -> None:
    result = run_preflight(provider_call=_fake(model="claude-fable-5"))
    assert len(result["per_model"]) == 4
    assert result["authorized_models_probed"] == list(ORDERED_MODEL_POOL)
    assert result["public_write_performed"] is False
    assert result["dispatch_performed"] is False
    assert result["scheduler_mutated"] is False


def test_run_preflight_allows_degraded_pool_when_authorized_models_remain_healthy() -> None:
    unavailable_models = {P1, P3}

    def mixed_health(prompt, model, timeout):
        if model in unavailable_models:
            return ProviderResult(failure_class="requested_model_temporarily_unavailable")
        return ProviderResult(text="READY", resolved_model=model, status_code=200)

    result = run_preflight(provider_call=mixed_health)

    assert result["healthy_count"] == 2
    assert result["unavailable_count"] == 2
    assert result["primary_model_healthy"] is True
    assert result["model_identity_disposition"] == "MODEL_IDENTITY_PROVIDER_VERIFIED"
    assert result["public_write_performed"] is False


def test_preflight_prompt_is_tiny_and_deterministic() -> None:
    assert len(PREFLIGHT_PROMPT) < 200
    assert "READY" in PREFLIGHT_PROMPT


# ---------------------------------------------------------------------------
# Run summary
# ---------------------------------------------------------------------------


def test_run_summary_declares_authority_pool_and_policy() -> None:
    summary = build_run_summary()
    assert summary["authority_id"] == "CONTENTOPS_9ROUTER_ORDERED_MODEL_AUTHORITY_V2"
    assert summary["supersedes_authority_id"] == "CONTENTOPS_FINAL_PRELAUNCH_LLM_MODEL_AUTHORITY_V1"
    assert summary["ordered_model_pool"] == list(ORDERED_MODEL_POOL)
    assert summary["primary_model"] == P0
    assert summary["retry_budget_policy"]["max_total_provider_attempts"] == 6
    assert summary["authority_logical_hash"]


def test_run_summary_aggregates_invocation_evidence() -> None:
    invocations = [
        {
            "total_attempts": 2,
            "total_fallback_transitions": 1,
            "budget_exhausted": False,
            "selected_model": P1,
            "attempts": [
                {
                    "requested_model": P0,
                    "failure_class": "read_timeout",
                    "latency_seconds": 1.0,
                },
                {
                    "requested_model": P1,
                    "failure_class": None,
                    "fallback_reason": "read_timeout",
                    "latency_seconds": 2.0,
                    "usage": {"total_tokens": 10},
                    "cost": {"usd": 0.01},
                },
            ],
        }
    ]
    summary = build_run_summary(invocations=invocations)
    assert summary["total_model_attempts"] == 2
    assert summary["fallback_count"] == 1
    assert summary["successful_calls_by_model"] == {P1: 1}
    assert summary["retries_by_error_class"] == {"read_timeout": 1}
    assert summary["fallback_reasons"] == {"read_timeout": 1}
    assert summary["observed_token_usage"] == {"total_tokens": 10.0}
    assert summary["observed_cost"] == {"usd": 0.01}
    assert summary["observed_latency_seconds"]["mean"] == 1.5


def test_run_summary_asserts_safety_posture_and_redaction() -> None:
    summary = build_run_summary()
    assert summary["secret_redaction_status"] == "PASS_NO_SECRET_SHAPED_MATERIAL"
    assert summary["unbounded_retry_possible"] is False
    assert summary["unauthorized_model_accepted"] is False
    assert summary["fallback_bypasses_quality_gates"] is False
    assert summary["public_write_performed"] is False
    assert summary["platform_action_performed"] is False
    assert summary["dispatch_performed"] is False
    assert summary["scheduler_mutated"] is False
    assert summary["capital_chronicle_authority_mutated"] is False
    assert summary["work_package_f_started"] is False
    assert summary["public_live_cohort_authorized_by_this_task"] is False


# ---------------------------------------------------------------------------
# Seam integration
# ---------------------------------------------------------------------------


def test_seam_declares_one_router_one_pool_and_no_per_module_retries() -> None:
    from live_contentops.nine_router_llm_seam_v2 import integration_manifest

    manifest = integration_manifest()
    assert manifest["separate_routers_per_task"] == 0
    assert manifest["per_module_retry_implementations"] == 0
    assert manifest["distinct_model_lists"] == 1
    assert manifest["ordered_model_pool"] == list(ORDERED_MODEL_POOL)
    assert len(manifest["integrated_call_sites"]) == 7


def test_seam_preserves_deterministic_stages() -> None:
    from live_contentops.nine_router_llm_seam_v2 import (
        DETERMINISTIC_STAGES_NOT_MODEL_ASSISTED,
    )

    # These stages must never be given a model call: several assert model_call_performed
    # is False, and the editorial orchestrator exists to reject LLM numeric authority.
    for stage in (
        "core_v0_closure_capabilities_v1.build_seo_contract",
        "core_v0_platform_visual_adaptation_v1",
        "editorial_review_orchestrator_v2.run_editorial_review",
    ):
        assert stage in DETERMINISTIC_STAGES_NOT_MODEL_ASSISTED


def test_seam_returns_text_and_records_evidence() -> None:
    from live_contentops.nine_router_llm_seam_v2 import (
        drain_invocation_log,
        routed_llm_text,
    )

    drain_invocation_log()
    text = routed_llm_text(
        "prompt", "9router", 5.0, provider_call=_fake(model="claude-fable-5")
    )
    assert text == "READY"
    log = drain_invocation_log()
    assert len(log) == 1
    assert log[0]["terminal_disposition"] == ACCEPTED
    assert log[0]["selected_model"] == P0


def test_seam_raises_when_the_router_terminates_without_acceptance() -> None:
    from live_contentops.nine_router_llm_seam_v2 import (
        RoutedInvocationError,
        drain_invocation_log,
        routed_llm_text,
    )

    def blocked(prompt, model, timeout):
        return ProviderResult(failure_class="evidence_failure")

    drain_invocation_log()
    with pytest.raises(RoutedInvocationError, match="LLM_TERMINAL_NON_RETRYABLE_FAILURE"):
        routed_llm_text("prompt", "9router", 5.0, provider_call=blocked)
    log = drain_invocation_log()
    assert log[0]["models_attempted_in_order"] == [P0], "a gate failure must not rotate models"
