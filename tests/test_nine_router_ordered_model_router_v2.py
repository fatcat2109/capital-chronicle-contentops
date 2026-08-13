"""Deterministic fault-injection matrix for the canonical 9router ordered model router.

Every case here is a bounded synthetic experiment against a fake provider. No network call,
no credential read, no cost. The matrix exists so the real-provider preflight never has to
manufacture paid failures to prove the retry algorithm.

Cases A–N map one-to-one onto the authorized validation matrix.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import pytest

from live_contentops.nine_router_ordered_model_router_v2 import (
    ACCEPTED,
    ARTICLE_WRITING_MODEL_POOL,
    ARTICLE_WRITING_ROLE,
    AUTHORITY_ID,
    AUTHORIZED_MODELS,
    BUILD_ACCEPTANCE_GEMINI_INCIDENT_EXPIRES_ENV,
    BUILD_ACCEPTANCE_GEMINI_INCIDENT_MODE_ENV,
    GATEWAY,
    GEMINI_PRO_MODEL,
    IDENTITY_MISMATCH_CLASS,
    IDENTITY_NOT_VERIFIABLE,
    MAX_TOTAL_PROVIDER_ATTEMPTS,
    MAX_DECLARED_PROVIDER_ATTEMPTS,
    NEWSROOM_GLOBAL_EDITOR_PER_MODEL_MAX_ATTEMPTS,
    NEWSROOM_GLOBAL_EDITOR_ROLE,
    NEWSROOM_GLOBAL_EDITOR_WALL_CLOCK_BUDGET_SECONDS,
    NEWSROOM_LEAF_SCAN_MAX_FALLBACK_TRANSITIONS,
    NEWSROOM_LEAF_SCAN_MODEL,
    NEWSROOM_LEAF_SCAN_MODEL_POOL,
    NEWSROOM_LEAF_SCAN_PER_MODEL_MAX_ATTEMPTS,
    NEWSROOM_LEAF_SCAN_ROLE,
    NEWSROOM_LEAF_SCAN_WALL_CLOCK_BUDGET_SECONDS,
    NON_RETRYABLE_CLASSES,
    ORDERED_MODEL_POOL,
    POOL_EXHAUSTED,
    PRIMARY_MODEL,
    RETRY_BUDGET_EXHAUSTED,
    SUPERSEDES_AUTHORITY_ID,
    TERMINAL_NON_RETRYABLE,
    BLOCKED_EXACT_CREATIVE_MODEL,
    V2_CREATIVE_EDITOR_ROLE,
    V2_CREATIVE_MODEL,
    V2_CREATIVE_MODEL_POOL,
    V2_CREATIVE_REVISION_AUTHOR_ROLE,
    V2_MOTION_CODE_AUTHOR_ROLE,
    ModelRouterError,
    ProviderResult,
    RetryBudget,
    authority_packet,
    build_acceptance_gemini_incident,
    classify_failure,
    is_fallback_eligible,
    is_retryable,
    is_terminal,
    model_pool_for_role,
    retry_budget_policy,
    retry_budget_for_role,
    route_llm_invocation,
)

P0, P1, P2, P3 = ORDERED_MODEL_POOL


def _enable_gemini_incident(monkeypatch, mode: str = "PRO_AND_FLASH") -> None:
    now = datetime.now(timezone.utc)
    monkeypatch.setenv(BUILD_ACCEPTANCE_GEMINI_INCIDENT_MODE_ENV, mode)
    monkeypatch.setenv(
        BUILD_ACCEPTANCE_GEMINI_INCIDENT_EXPIRES_ENV,
        (now + timedelta(hours=1)).isoformat().replace("+00:00", "Z"),
    )


class FakeClock:
    """A deterministic monotonic clock; tests advance it explicitly."""

    def __init__(self) -> None:
        self.t = 0.0

    def __call__(self) -> float:
        return self.t

    def advance(self, seconds: float) -> None:
        self.t += seconds


class RecordingSleeper:
    """Records requested sleeps instead of actually sleeping."""

    def __init__(self, clock: FakeClock | None = None) -> None:
        self.slept: list[float] = []
        self.clock = clock

    def __call__(self, seconds: float) -> None:
        self.slept.append(seconds)
        if self.clock is not None:
            self.clock.advance(seconds)


def scripted(script):
    """Build a provider callable from {model: [outcome, ...]} or a flat callable."""
    calls: list[tuple[str, int]] = []
    counters: dict[str, int] = {}

    def provider(prompt: str, model: str, timeout: float) -> ProviderResult:
        index = counters.get(model, 0)
        counters[model] = index + 1
        calls.append((model, index))
        outcomes = script.get(model)
        if outcomes is None:
            return ProviderResult(
                failure_class="provider_temporarily_unavailable", resolved_model=None
            )
        outcome = outcomes[min(index, len(outcomes) - 1)]
        return outcome(prompt) if callable(outcome) else outcome

    provider.calls = calls  # type: ignore[attr-defined]
    return provider


def good(model: str, text: str = '{"ok": true}') -> ProviderResult:
    return ProviderResult(
        text=text,
        resolved_model=model,
        provider_invocation_id=f"inv_{model}",
        status_code=200,
        usage={"total_tokens": 10},
        cost={"usd": 0.0001},
    )


def fail(klass: str, *, status: int | None = None, retry_after: float | None = None):
    return ProviderResult(
        failure_class=klass, status_code=status, retry_after_seconds=retry_after,
        resolved_model=None,
    )


def run(provider, **kwargs):
    clock = kwargs.pop("clock", None) or FakeClock()
    sleeper = kwargs.pop("sleeper", None) or RecordingSleeper(clock)
    return route_llm_invocation(
        logical_invocation_id=kwargs.pop("iid", "inv_test"),
        role_task_id=kwargs.pop("role", "article_writing"),
        prompt=kwargs.pop("prompt", "test prompt"),
        provider_call=provider,
        clock=clock,
        sleeper=sleeper,
        **kwargs,
    )


# ---------------------------------------------------------------------------
# Authority and policy
# ---------------------------------------------------------------------------


def test_authority_declares_v2_and_supersedes_v1() -> None:
    packet = authority_packet()
    assert packet["authority_id"] == AUTHORITY_ID == "CONTENTOPS_9ROUTER_ORDERED_MODEL_AUTHORITY_V2"
    assert packet["supersedes"] == SUPERSEDES_AUTHORITY_ID
    assert packet["gateway"] == GATEWAY == "9router"
    assert packet["fallback_is_owner_authorized"] is True
    assert packet["fallback_is_for_bounded_resilience_not_quality_gate_bypass"] is True
    assert packet["silent_provider_side_substitution_permitted"] is False
    assert packet["unbounded_retry_permitted"] is False
    assert packet["grants_publication_authority"] is False
    assert packet["authority_logical_hash"]


def test_exact_ordered_pool_is_the_four_authorized_models() -> None:
    assert ORDERED_MODEL_POOL == (
        "new/gpt-5.6-sol-xhigh",
        "new/qwen3.8-max-preview",
        "new/claude-opus-5",
        "vx/gemini-3.1-pro-preview(high)",
    )
    assert PRIMARY_MODEL == "new/gpt-5.6-sol-xhigh"
    assert "new/claude-fable-5" not in AUTHORIZED_MODELS
    assert len(ORDERED_MODEL_POOL) == 4
    assert len(AUTHORIZED_MODELS) == 5
    assert "vx/gemini-3.5-flash(high)" in AUTHORIZED_MODELS
    assert ARTICLE_WRITING_MODEL_POOL is ORDERED_MODEL_POOL
    assert model_pool_for_role(ARTICLE_WRITING_ROLE) is ORDERED_MODEL_POOL
    assert authority_packet()["article_writing_uses_quality_first_pool"] is True


def test_temporary_gemini_incident_routes_leaf_to_flash_and_quality_to_pro(monkeypatch) -> None:
    _enable_gemini_incident(monkeypatch)

    assert model_pool_for_role(NEWSROOM_LEAF_SCAN_ROLE) == (NEWSROOM_LEAF_SCAN_MODEL,)
    assert model_pool_for_role(NEWSROOM_GLOBAL_EDITOR_ROLE) == (GEMINI_PRO_MODEL,)
    assert model_pool_for_role(ARTICLE_WRITING_ROLE) == (GEMINI_PRO_MODEL,)
    budget = retry_budget_for_role(
        role_task_id=ARTICLE_WRITING_ROLE,
        logical_invocation_id="incident-quality",
    )
    assert budget.max_total_provider_attempts == 4
    assert budget.max_fallback_transitions == 0
    assert budget.per_model_max_attempts == (4,)
    packet = authority_packet()
    assert packet["ordered_model_pool"] == list(ORDERED_MODEL_POOL)
    assert packet["temporary_build_acceptance_gemini_incident"]["mode"] == "PRO_AND_FLASH"
    assert packet["production_launch_uses_incident_override_by_default"] is False

    provider = scripted({GEMINI_PRO_MODEL: [good(GEMINI_PRO_MODEL)]})
    result = route_llm_invocation(
        logical_invocation_id="incident-direct-quality",
        role_task_id=ARTICLE_WRITING_ROLE,
        prompt="bounded incident test",
        provider_call=provider,
        model_pool=model_pool_for_role(ARTICLE_WRITING_ROLE),
        budget=retry_budget_for_role(
            role_task_id=ARTICLE_WRITING_ROLE,
            logical_invocation_id="incident-direct-quality",
        ),
    )
    assert result["terminal_disposition"] == ACCEPTED
    assert [model for model, _ in provider.calls] == [GEMINI_PRO_MODEL]


@pytest.mark.parametrize(
    ("mode", "expected"),
    (("PRO_ONLY", GEMINI_PRO_MODEL), ("FLASH_ONLY", NEWSROOM_LEAF_SCAN_MODEL)),
)
def test_single_verified_gemini_incident_uses_that_exact_model_for_all_roles(
    monkeypatch, mode: str, expected: str,
) -> None:
    _enable_gemini_incident(monkeypatch, mode)
    assert model_pool_for_role(NEWSROOM_LEAF_SCAN_ROLE) == (expected,)
    assert model_pool_for_role(ARTICLE_WRITING_ROLE) == (expected,)
    assert model_pool_for_role("tier1_editorial_review") == (expected,)


def test_gemini_incident_invalid_or_expired_configuration_restores_canonical_pool(
    monkeypatch,
) -> None:
    now = datetime.now(timezone.utc)
    monkeypatch.setenv(BUILD_ACCEPTANCE_GEMINI_INCIDENT_MODE_ENV, "PRO_AND_FLASH")
    for expiry in (
        now - timedelta(seconds=1),
        now + timedelta(hours=25),
    ):
        monkeypatch.setenv(
            BUILD_ACCEPTANCE_GEMINI_INCIDENT_EXPIRES_ENV,
            expiry.isoformat().replace("+00:00", "Z"),
        )
        assert build_acceptance_gemini_incident(now_utc=now) is None
        assert model_pool_for_role(ARTICLE_WRITING_ROLE) is ORDERED_MODEL_POOL

    monkeypatch.setenv(BUILD_ACCEPTANCE_GEMINI_INCIDENT_MODE_ENV, "ARBITRARY_MODEL")
    monkeypatch.setenv(
        BUILD_ACCEPTANCE_GEMINI_INCIDENT_EXPIRES_ENV,
        (now + timedelta(hours=1)).isoformat().replace("+00:00", "Z"),
    )
    assert build_acceptance_gemini_incident(now_utc=now) is None
    assert model_pool_for_role(ARTICLE_WRITING_ROLE) is ORDERED_MODEL_POOL


@pytest.mark.parametrize(
    "role",
    (V2_CREATIVE_EDITOR_ROLE, V2_MOTION_CODE_AUTHOR_ROLE, V2_CREATIVE_REVISION_AUTHOR_ROLE),
)
def test_creative_roles_are_exact_gpt56_singletons_even_during_incident(monkeypatch, role) -> None:
    _enable_gemini_incident(monkeypatch, "FLASH_ONLY")
    assert model_pool_for_role(role) == V2_CREATIVE_MODEL_POOL == (V2_CREATIVE_MODEL,)
    budget = retry_budget_for_role(role_task_id=role, logical_invocation_id=f"creative-{role}")
    assert budget.max_total_provider_attempts == 4
    assert budget.max_fallback_transitions == 0
    assert budget.max_same_model_retries == 3
    assert budget.per_model_max_attempts == (4,)


def test_declared_retry_budget_defaults() -> None:
    policy = retry_budget_policy()
    assert policy["max_total_provider_attempts"] == 16
    assert policy["max_fallback_transitions"] == 3
    assert policy["max_same_model_retries"] == 3
    assert policy["max_structured_output_repair_attempts"] == 1
    assert policy["structured_repair_counts_against_total_attempts"] is True
    assert policy["max_cumulative_retry_sleep_seconds"] == 1800.0
    assert policy["default_wall_clock_budget_seconds"] == 2400.0
    assert policy["per_model_max_attempts"] == {P0: 4, P1: 4, P2: 4, P3: 4}
    assert policy["budget_resets_on_model_change"] is False
    assert policy["budget_resets_on_reconstruction"] is False


def test_role_specific_wall_clock_budgets_are_finite_and_do_not_change_attempt_bounds() -> None:
    from live_contentops.nine_router_ordered_model_router_v2 import retry_budget_for_role

    leaf = retry_budget_for_role(
        role_task_id="rolling_x_newsroom_leaf_scan",
        logical_invocation_id="leaf-budget-test",
    )
    editor = retry_budget_for_role(
        role_task_id="rolling_x_newsroom_assignment",
        logical_invocation_id="editor-budget-test",
    )
    generic = retry_budget_for_role(
        role_task_id="article_writing",
        logical_invocation_id="generic-budget-test",
    )
    assert leaf.wall_clock_budget_seconds == NEWSROOM_LEAF_SCAN_WALL_CLOCK_BUDGET_SECONDS == 3000.0
    assert editor.wall_clock_budget_seconds == NEWSROOM_GLOBAL_EDITOR_WALL_CLOCK_BUDGET_SECONDS == 2400.0
    assert generic.wall_clock_budget_seconds == 2400.0
    assert leaf.max_total_provider_attempts == MAX_DECLARED_PROVIDER_ATTEMPTS == 20
    assert leaf.max_fallback_transitions == NEWSROOM_LEAF_SCAN_MAX_FALLBACK_TRANSITIONS
    assert leaf.per_model_max_attempts == NEWSROOM_LEAF_SCAN_PER_MODEL_MAX_ATTEMPTS == (4, 4, 4, 4, 4)
    assert editor.max_total_provider_attempts == 16
    assert editor.max_fallback_transitions == 3
    assert editor.max_same_model_retries == 3
    assert editor.max_structured_output_repair_attempts == 1
    assert editor.per_model_max_attempts == NEWSROOM_GLOBAL_EDITOR_PER_MODEL_MAX_ATTEMPTS == (4, 4, 4, 4)
    assert generic.max_total_provider_attempts == MAX_TOTAL_PROVIDER_ATTEMPTS
    assert generic.max_same_model_retries == 3
    assert generic.per_model_max_attempts == (4, 4, 4, 4)


def test_global_editor_authority_packet_declares_exact_bounded_repair_policy() -> None:
    policy = authority_packet()["newsroom_global_editor_retry_policy"]

    assert policy == {
        "max_total_provider_attempts": 16,
        "max_fallback_transitions": 3,
        "max_same_model_retries": 3,
        "max_structured_output_repair_attempts": 1,
        "per_model_max_attempts": [4, 4, 4, 4],
        "wall_clock_budget_seconds": 2400.0,
        "bounded": True,
    }


def test_router_refuses_an_unauthorized_model_in_the_pool() -> None:
    with pytest.raises(ModelRouterError, match="unauthorized_model_in_pool"):
        run(scripted({}), model_pool=[P0, "some/unlisted-model"])


def test_budget_cannot_be_widened_beyond_declared_policy() -> None:
    RetryBudget(logical_invocation_id="i", max_total_provider_attempts=3)  # tightening is fine
    with pytest.raises(ModelRouterError, match="exceeds_declared_policy"):
        RetryBudget(logical_invocation_id="i", max_total_provider_attempts=21)


# ---------------------------------------------------------------------------
# Failure classification
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "klass",
    [
        "connection_timeout",
        "read_timeout",
        "http_429_rate_limited",
        "http_503_unavailable",
        "quota_exhausted",
    ],
)
def test_infrastructure_classes_are_retryable(klass) -> None:
    assert is_retryable(klass)
    assert is_fallback_eligible(klass)
    assert not is_terminal(klass)


@pytest.mark.parametrize("klass", sorted(NON_RETRYABLE_CLASSES))
def test_gate_failures_are_terminal_and_never_fallback_eligible(klass) -> None:
    assert is_terminal(klass)
    assert not is_fallback_eligible(klass), f"{klass} must never rotate models"
    assert not is_retryable(klass)


def test_unknown_failure_is_not_treated_as_retryable() -> None:
    # Defaulting unknown errors to "retry" is how unbounded loops start.
    assert classify_failure(RuntimeError("something weird")) == "unclassified_failure"
    assert not is_retryable("unclassified_failure")
    assert not is_fallback_eligible("unclassified_failure")


def test_http_status_classification() -> None:
    assert classify_failure(status_code=429) == "http_429_rate_limited"
    assert classify_failure(status_code=503) == "http_503_unavailable"
    assert classify_failure(status_code=401) == "http_401_unauthorized"
    assert classify_failure(status_code=403) == "http_403_forbidden"
    assert is_terminal(classify_failure(status_code=401))
    assert is_terminal(classify_failure(status_code=403))


# ---------------------------------------------------------------------------
# A–N fault-injection matrix
# ---------------------------------------------------------------------------


def test_case_a_p0_succeeds_first_try() -> None:
    provider = scripted({P0: [good(P0)]})
    result = run(provider)
    assert result["terminal_disposition"] == ACCEPTED
    assert result["selected_model"] == P0
    assert result["total_attempts"] == 1
    assert result["total_fallback_transitions"] == 0
    assert result["models_attempted_in_order"] == [P0]
    assert result["budget_exhausted"] is False


def test_case_b_p0_timeout_then_p0_retry_succeeds() -> None:
    provider = scripted({P0: [fail("read_timeout"), good(P0)]})
    result = run(provider)
    assert result["terminal_disposition"] == ACCEPTED
    assert result["selected_model"] == P0
    assert result["total_attempts"] == 2
    assert result["total_fallback_transitions"] == 0, "a same-model retry is not a fallback"
    assert result["models_attempted_in_order"] == [P0]


def test_case_c_p0_quota_consumes_same_model_retries_then_p1_succeeds() -> None:
    provider = scripted({P0: [fail("quota_exhausted")], P1: [good(P1)]})
    result = run(provider)
    assert result["terminal_disposition"] == ACCEPTED
    assert result["selected_model"] == P1
    assert result["total_attempts"] == 5
    assert [m for m, _ in provider.calls] == [P0, P0, P0, P0, P1]
    assert result["total_fallback_transitions"] == 1
    assert result["attempts"][0]["failure_class"] == "quota_exhausted"
    assert result["attempts"][4]["fallback_from"] == P0
    assert result["attempts"][4]["fallback_reason"] == "quota_exhausted"


def test_case_d_p0_timeouts_then_p1_503s_then_p2_succeeds() -> None:
    provider = scripted(
        {
            P0: [fail("read_timeout"), fail("read_timeout")],
            P1: [fail("http_503_unavailable"), fail("http_503_unavailable")],
            P2: [good(P2)],
        }
    )
    result = run(provider)
    assert result["terminal_disposition"] == ACCEPTED
    assert result["selected_model"] == P2
    assert result["total_attempts"] == 9
    assert result["models_attempted_in_order"] == [P0, P1, P2]
    assert result["total_fallback_transitions"] == 2


def test_case_e_p0_and_p1_unavailable_p2_succeeds() -> None:
    provider = scripted(
        {
            P0: [fail("provider_temporarily_unavailable")],
            P1: [fail("requested_model_temporarily_unavailable")],
            P2: [good(P2)],
        }
    )
    result = run(provider)
    assert result["terminal_disposition"] == ACCEPTED
    assert result["selected_model"] == P2
    assert result["models_attempted_in_order"] == [P0, P1, P2]


def test_case_f_entire_pool_unavailable_blocks_closed() -> None:
    provider = scripted(
        {
            P0: [fail("provider_temporarily_unavailable")],
            P1: [fail("provider_temporarily_unavailable")],
            P2: [fail("provider_temporarily_unavailable")],
            P3: [fail("provider_temporarily_unavailable")],
        }
    )
    result = run(provider)
    assert result["terminal_disposition"] in (POOL_EXHAUSTED, RETRY_BUDGET_EXHAUSTED)
    assert result["selected_model"] is None
    assert result["output"] is None
    assert result["models_attempted_in_order"] == list(ORDERED_MODEL_POOL)
    assert result["total_attempts"] <= MAX_TOTAL_PROVIDER_ATTEMPTS


def test_case_g_sixteen_attempt_budget_permits_no_seventeenth_provider_call() -> None:
    """The central bound: whatever the failure pattern, attempt seventeen never happens."""
    provider = scripted(
        {
            P0: [fail("read_timeout")] * 9,
            P1: [fail("read_timeout")] * 9,
            P2: [fail("read_timeout")] * 9,
            P3: [fail("read_timeout")] * 9,
        }
    )
    result = run(provider)
    assert len(provider.calls) <= MAX_TOTAL_PROVIDER_ATTEMPTS
    assert result["total_attempts"] <= MAX_TOTAL_PROVIDER_ATTEMPTS
    assert len(result["attempts"]) == result["total_attempts"]
    assert result["terminal_disposition"] in (RETRY_BUDGET_EXHAUSTED, POOL_EXHAUSTED)
    assert len(provider.calls) == 16
    assert all(row["attempt_number_global"] <= 16 for row in result["attempts"])


def test_case_g_budget_is_not_reset_by_a_model_change() -> None:
    provider = scripted({m: [fail("read_timeout")] * 9 for m in ORDERED_MODEL_POOL})
    result = run(provider)
    globals_seen = [row["attempt_number_global"] for row in result["attempts"]]
    assert globals_seen == sorted(globals_seen)
    assert globals_seen == list(range(1, len(globals_seen) + 1)), "counter must be continuous"


def test_case_h_retry_sleep_budget_stops_without_further_sleep_or_call() -> None:
    clock = FakeClock()
    sleeper = RecordingSleeper(clock)
    # Retry-After far exceeds the remaining sleep budget, so the router must advance
    # rather than sleep, and must never sleep beyond the declared ceiling.
    provider = scripted(
        {
            P0: [fail("http_429_rate_limited", retry_after=600.0)],
            P1: [fail("http_429_rate_limited", retry_after=600.0)],
            P2: [fail("http_429_rate_limited", retry_after=600.0)],
            P3: [fail("http_429_rate_limited", retry_after=600.0)],
        }
    )
    result = run(provider, clock=clock, sleeper=sleeper)
    assert sum(sleeper.slept) == 1800.0
    assert result["total_retry_sleep_seconds"] <= 1800.0
    assert result["terminal_disposition"] in (POOL_EXHAUSTED, RETRY_BUDGET_EXHAUSTED)


def test_retry_after_within_budget_is_honoured() -> None:
    clock = FakeClock()
    sleeper = RecordingSleeper(clock)
    provider = scripted({P0: [fail("http_429_rate_limited", retry_after=2.0), good(P0)]})
    result = run(provider, clock=clock, sleeper=sleeper)
    assert sleeper.slept == [2.0]
    assert result["terminal_disposition"] == ACCEPTED
    assert result["total_retry_sleep_seconds"] == 2.0


def _json_validator(text: str):
    try:
        return (True, None, json.loads(text))
    except json.JSONDecodeError:
        return (False, "structured_output_malformed", None)


def test_case_i_malformed_then_one_repair_attempt_succeeds() -> None:
    provider = scripted({P0: [good(P0, text="not json at all"), good(P0, text='{"ok": 1}')]})
    result = run(provider, validator=_json_validator)
    assert result["terminal_disposition"] == ACCEPTED
    assert result["selected_model"] == P0
    assert result["total_structured_repair_attempts"] == 1
    # The repair is a real provider attempt and consumes the shared budget.
    assert result["total_attempts"] == 2
    assert result["attempts"][0]["structured_validation_result"] == "FAIL"
    assert result["attempts"][1]["structured_validation_result"] == "PASS"
    assert result["output"] == {"ok": 1}


def test_case_i_failed_attempt_is_never_discarded_from_evidence() -> None:
    provider = scripted({P0: [good(P0, text="broken"), good(P0, text='{"ok": 1}')]})
    result = run(provider, validator=_json_validator)
    assert len(result["attempts"]) == 2
    assert result["attempts"][0]["output_hash"], "failed raw response must still be hashed"
    assert result["attempts"][0]["disposition"] == "rejected"


def test_safe_structured_validation_diagnostic_is_recorded_and_given_to_one_repair() -> None:
    prompts = []

    def provider(prompt: str, model: str, timeout: float) -> ProviderResult:
        prompts.append(prompt)
        return good(model, text="invalid") if len(prompts) == 1 else good(model)

    def validator(text: str):
        if text == "invalid":
            return False, "structured_output_schema_invalid", None, "global_rank_invalid"
        return True, None, {"ok": True}, None

    def repair(prompt: str, invalid_output: str, diagnostic_code: str | None) -> str:
        assert diagnostic_code == "global_rank_invalid"
        return prompt + "\nprevious_validation_failure_code=" + str(diagnostic_code)

    result = run(provider, validator=validator, repair_prompt_builder=repair)

    assert result["terminal_disposition"] == ACCEPTED
    assert result["total_attempts"] == 2
    assert result["total_structured_repair_attempts"] == 1
    assert result["attempts"][0]["structured_validation_diagnostic_code"] == "global_rank_invalid"
    assert '"invalid"' not in json.dumps(result["attempts"])
    assert "previous_validation_failure_code=global_rank_invalid" in prompts[1]


def _run_leaf(provider):
    from live_contentops.nine_router_ordered_model_router_v2 import retry_budget_for_role

    return run(
        provider,
        iid="inv_leaf_policy",
        role=NEWSROOM_LEAF_SCAN_ROLE,
        model_pool=NEWSROOM_LEAF_SCAN_MODEL_POOL,
        budget=retry_budget_for_role(
            role_task_id=NEWSROOM_LEAF_SCAN_ROLE,
            logical_invocation_id="inv_leaf_policy",
        ),
        validator=_json_validator,
    )


def _run_global_editor(provider):
    from live_contentops.nine_router_ordered_model_router_v2 import retry_budget_for_role

    return run(
        provider,
        iid="inv_global_policy",
        role=NEWSROOM_GLOBAL_EDITOR_ROLE,
        model_pool=ORDERED_MODEL_POOL,
        budget=retry_budget_for_role(
            role_task_id=NEWSROOM_GLOBAL_EDITOR_ROLE,
            logical_invocation_id="inv_global_policy",
        ),
        validator=_json_validator,
    )


def test_global_editor_infrastructure_failures_get_three_same_model_retries() -> None:
    provider = scripted({model: [fail("http_503_unavailable")] for model in ORDERED_MODEL_POOL})

    result = _run_global_editor(provider)

    assert [model for model, _ in provider.calls] == [
        model for model in ORDERED_MODEL_POOL for _ in range(4)
    ]
    assert [index for _, index in provider.calls] == [0, 1, 2, 3] * 4
    assert result["total_attempts"] == 16
    assert result["total_structured_repair_attempts"] == 0
    assert result["total_fallback_transitions"] == 3


def test_global_editor_final_model_gets_exactly_one_structured_repair() -> None:
    provider = scripted({
        P0: [fail("http_503_unavailable")],
        P1: [fail("http_502_bad_gateway")],
        P2: [fail("requested_model_temporarily_unavailable")],
        P3: [good(P3, text="broken"), good(P3, text='{"ok": 1}')],
    })

    result = _run_global_editor(provider)

    assert result["terminal_disposition"] == ACCEPTED
    assert result["selected_model"] == P3
    assert result["total_attempts"] == 14
    assert result["total_structured_repair_attempts"] == 1
    assert result["total_fallback_transitions"] == 3
    assert provider.calls == (
        [(P0, index) for index in range(4)]
        + [(P1, index) for index in range(4)]
        + [(P2, index) for index in range(4)]
        + [(P3, 0), (P3, 1)]
    )


def test_global_editor_structured_repair_is_single_and_pool_remains_bounded() -> None:
    provider = scripted({
        model: [good(model, text="broken")]
        for model in ORDERED_MODEL_POOL
    })

    result = _run_global_editor(provider)

    assert result["terminal_disposition"] in (RETRY_BUDGET_EXHAUSTED, POOL_EXHAUSTED)
    assert result["total_attempts"] == 5
    assert result["total_structured_repair_attempts"] == 1
    assert len(provider.calls) == 5
    assert provider.calls[:2] == [(P0, 0), (P0, 1)]
    assert provider.calls[-1] == (P3, 0)


def test_leaf_flash_structured_failure_gets_one_same_model_repair_without_fallback() -> None:
    provider = scripted({
        NEWSROOM_LEAF_SCAN_MODEL: [
            good(NEWSROOM_LEAF_SCAN_MODEL, text="broken"),
            good(NEWSROOM_LEAF_SCAN_MODEL, text='{"ok": 1}'),
        ],
    })

    result = _run_leaf(provider)

    assert result["terminal_disposition"] == ACCEPTED
    assert result["selected_model"] == NEWSROOM_LEAF_SCAN_MODEL
    assert result["total_attempts"] == 2
    assert result["total_structured_repair_attempts"] == 1
    assert result["total_fallback_transitions"] == 0
    assert provider.calls == [
        (NEWSROOM_LEAF_SCAN_MODEL, 0),
        (NEWSROOM_LEAF_SCAN_MODEL, 1),
    ]


def test_leaf_models_get_bounded_retries_under_the_twenty_attempt_leaf_ceiling() -> None:
    flash = NEWSROOM_LEAF_SCAN_MODEL
    gpt, qwen, opus, gemini_pro = ORDERED_MODEL_POOL
    provider = scripted({
        flash: [good(flash, text="broken"), good(flash, text="still broken")],
        gpt: [fail("http_503_unavailable"), good(gpt)],
        qwen: [fail("http_502_bad_gateway")],
        opus: [fail("requested_model_temporarily_unavailable")],
        gemini_pro: [good(gemini_pro, text="also broken")],
    })

    result = _run_leaf(provider)

    assert provider.calls.count((gpt, 0)) == 1
    assert provider.calls.count((gpt, 1)) == 1
    assert result["total_attempts"] == 4
    assert result["total_attempts"] <= MAX_DECLARED_PROVIDER_ATTEMPTS
    assert result["total_fallback_transitions"] == 1
    assert result["total_fallback_transitions"] <= NEWSROOM_LEAF_SCAN_MAX_FALLBACK_TRANSITIONS
    assert result["terminal_disposition"] == ACCEPTED


@pytest.mark.parametrize(
    "role",
    (V2_CREATIVE_EDITOR_ROLE, V2_MOTION_CODE_AUTHOR_ROLE, V2_CREATIVE_REVISION_AUTHOR_ROLE),
)
def test_creative_role_retries_exact_model_four_times_then_blocks(role) -> None:
    provider = scripted({V2_CREATIVE_MODEL: [fail("requested_model_temporarily_unavailable")]})
    iid = f"creative-exhaustion-{role}"
    result = run(
        provider,
        iid=iid,
        role=role,
        model_pool=model_pool_for_role(role),
        budget=retry_budget_for_role(role_task_id=role, logical_invocation_id=iid),
    )
    assert result["terminal_disposition"] == BLOCKED_EXACT_CREATIVE_MODEL
    assert result["models_attempted_in_order"] == [V2_CREATIVE_MODEL]
    assert result["total_attempts"] == 4
    assert result["total_fallback_transitions"] == 0
    assert [row["retry_number"] for row in result["attempts"]] == [0, 1, 2, 3]
    assert [row["attempt_kind"] for row in result["attempts"]] == [
        "initial", "retry", "retry", "retry"
    ]


def test_case_j_repair_fails_then_eligible_fallback() -> None:
    provider = scripted(
        {P0: [good(P0, text="broken"), good(P0, text="still broken")], P1: [good(P1)]}
    )
    result = run(provider, validator=_json_validator)
    assert result["terminal_disposition"] == ACCEPTED
    assert result["selected_model"] == P1
    assert result["total_structured_repair_attempts"] == 1
    assert result["models_attempted_in_order"] == [P0, P1]


def test_case_k_evidence_failure_never_rotates_models() -> None:
    """The safety core: a factual/evidence failure must not trigger a model carousel."""
    for klass in (
        "evidence_failure",
        "factual_validation_failure",
        "fabricated_numeric_material",
        "permission_failure",
        "publication_authority_failure",
        "freshness_or_material_delta_failure",
        "capital_chronicle_authority_mismatch",
        "policy_violation",
    ):
        provider = scripted({m: [fail(klass)] for m in ORDERED_MODEL_POOL})
        result = run(provider, iid=f"inv_{klass}")
        assert result["terminal_disposition"] == TERMINAL_NON_RETRYABLE, klass
        assert result["total_attempts"] == 1, f"{klass} must stop after one attempt"
        assert result["models_attempted_in_order"] == [P0], f"{klass} must not rotate"
        assert result["total_fallback_transitions"] == 0
        assert result["output"] is None


def test_case_l_401_and_403_fail_closed_without_a_model_carousel() -> None:
    for status, klass in ((401, "http_401_unauthorized"), (403, "http_403_forbidden")):
        provider = scripted({m: [fail(klass, status=status)] for m in ORDERED_MODEL_POOL})
        result = run(provider, iid=f"inv_{status}")
        assert result["terminal_disposition"] == TERMINAL_NON_RETRYABLE
        assert result["total_attempts"] == 1
        assert result["models_attempted_in_order"] == [P0]
        assert result["attempts"][0]["provider_status_class"] == f"4xx_client_{status}"


def test_case_m_silent_substitution_to_another_model_is_rejected() -> None:
    """P0 'succeeds' but the gateway resolved a different model: reject the output."""
    substituted = ProviderResult(
        text='{"ok": true}', resolved_model=P2, status_code=200, provider_invocation_id="inv_x"
    )
    provider = scripted({P0: [substituted], P1: [good(P1)]})
    result = run(provider)
    assert result["attempts"][0]["failure_class"] == IDENTITY_MISMATCH_CLASS
    assert result["attempts"][0]["disposition"] == "rejected"
    assert result["attempts"][0]["identity_mismatch"]["requested_model"] == P0
    assert result["attempts"][0]["identity_mismatch"]["resolved_model"] == P2
    # The router continues only under the authorized fallback policy.
    assert result["selected_model"] == P1
    assert result["terminal_disposition"] == ACCEPTED


def test_case_m_resolution_to_an_unlisted_model_is_rejected() -> None:
    rogue = ProviderResult(text='{"ok": true}', resolved_model="vendor/secret-cheap-model", status_code=200)
    provider = scripted({m: [rogue] for m in ORDERED_MODEL_POOL})
    result = run(provider)
    assert result["terminal_disposition"] in (POOL_EXHAUSTED, RETRY_BUDGET_EXHAUSTED)
    assert result["selected_model"] is None
    assert result["output"] is None
    for row in result["attempts"]:
        assert row["failure_class"] == IDENTITY_MISMATCH_CLASS
        assert row["model_identity_provider_verified"] is False


def test_identity_not_verifiable_is_recorded_honestly_not_upgraded_to_pass() -> None:
    silent = ProviderResult(text='{"ok": true}', status_code=200, resolved_model=None)
    result = run(scripted({P0: [silent]}))
    assert result["terminal_disposition"] == ACCEPTED
    assert result["model_identity_provider_verifiable"] is False
    assert result["model_identity_note"] == IDENTITY_NOT_VERIFIABLE
    assert result["attempts"][0]["model_identity_provider_verified"] is False


def test_case_n_reconstruction_does_not_reset_the_consumed_budget() -> None:
    provider = scripted({P0: [fail("read_timeout"), fail("read_timeout")], P1: [fail("read_timeout")]})
    first = run(provider, budget=RetryBudget(logical_invocation_id="inv_durable"))
    snapshot = first["final_retry_budget_snapshot"]
    consumed = snapshot["consumed_attempts"]
    assert consumed >= 3

    # Simulated process restart: rehydrate the budget from its durable snapshot.
    rehydrated = RetryBudget.from_snapshot(snapshot)
    assert rehydrated.consumed_attempts == consumed
    assert rehydrated.remaining_attempts() == MAX_TOTAL_PROVIDER_ATTEMPTS - consumed

    resumed_provider = scripted({m: [fail("read_timeout")] * 9 for m in ORDERED_MODEL_POOL})
    second = run(resumed_provider, budget=rehydrated, iid="inv_durable")
    # Total across both halves must still respect the single global ceiling.
    assert consumed + len(resumed_provider.calls) <= MAX_TOTAL_PROVIDER_ATTEMPTS
    assert second["final_retry_budget_snapshot"]["consumed_attempts"] <= MAX_TOTAL_PROVIDER_ATTEMPTS


def test_reconstruction_with_budget_already_spent_makes_no_call_at_all() -> None:
    spent = RetryBudget(logical_invocation_id="inv_spent")
    spent.consumed_attempts = MAX_TOTAL_PROVIDER_ATTEMPTS
    provider = scripted({m: [good(m)] for m in ORDERED_MODEL_POOL})
    result = run(provider, budget=spent)
    assert len(provider.calls) == 0, "an exhausted budget must not authorize a fresh call"
    assert result["terminal_disposition"] == RETRY_BUDGET_EXHAUSTED
    assert result["budget_exhausted"] is True


def test_wall_clock_budget_stops_the_invocation() -> None:
    clock = FakeClock()

    def slow(prompt: str, model: str, timeout: float) -> ProviderResult:
        clock.advance(700.0)
        return fail("read_timeout")

    result = run(slow, clock=clock, sleeper=RecordingSleeper())
    assert result["budget_exhausted"] is True
    assert result["budget_exhausted_reason"] == "wall_clock_budget_seconds"
    assert result["terminal_disposition"] == RETRY_BUDGET_EXHAUSTED


def test_fallback_transition_ceiling_is_enforced() -> None:
    provider = scripted({m: [fail("quota_exhausted")] for m in ORDERED_MODEL_POOL})
    result = run(provider)
    assert result["terminal_disposition"] in (POOL_EXHAUSTED, RETRY_BUDGET_EXHAUSTED)
    assert result["models_attempted_in_order"] == list(ORDERED_MODEL_POOL)
    assert result["total_attempts"] == 16
    assert result["total_fallback_transitions"] == 3


# ---------------------------------------------------------------------------
# Evidence completeness and redaction
# ---------------------------------------------------------------------------


def test_every_attempt_binds_the_required_evidence_fields() -> None:
    provider = scripted({P0: [fail("read_timeout")], P1: [good(P1)]})
    result = run(provider, work_item_id="wi_1", role="article_writing", governed_input={"a": 1})
    required = (
        "logical_invocation_id",
        "work_item_id",
        "role_task_id",
        "gateway",
        "model_priority_index",
        "requested_model",
        "attempt_number_global",
        "attempt_number_for_model",
        "attempt_kind",
        "retry_number",
        "retry_budget_snapshot",
        "remaining_attempt_budget",
        "fallback_from",
        "fallback_reason",
        "failure_class",
        "provider_status_class",
        "retry_after_seconds",
        "prompt_template",
        "prompt_version",
        "prompt_logical_hash",
        "governed_input_hash",
        "structured_validation_result",
        "structured_validation_failure_class",
        "output_present",
        "output_character_length",
        "output_utf8_byte_length",
        "output_hash",
        "provider_finish_reason",
        "provider_truncation_indicated",
        "latency_seconds",
        "disposition",
    )
    for row in result["attempts"]:
        for key in required:
            assert key in row, f"attempt missing {key}"
    assert result["attempts"][-1]["usage"] == {"total_tokens": 10}
    assert result["attempts"][-1]["provider_invocation_id"] == f"inv_{P1}"
    assert result["attempts"][-1]["output_hash"]


def test_attempt_diagnostics_record_output_shape_finish_reason_and_schema_category() -> None:
    provider = scripted({P0: [ProviderResult(
        text='{"partial":', resolved_model=P0, status_code=200,
        finish_reason="length", usage={"completion_tokens": 16000},
    )]})

    def validator(text: str):
        del text
        return False, "structured_output_schema_invalid", None, "json_truncated"

    result = run(provider, validator=validator)
    row = result["attempts"][0]
    assert row["output_present"] is True
    assert row["output_character_length"] == len('{"partial":')
    assert row["output_utf8_byte_length"] == len('{"partial":'.encode("utf-8"))
    assert row["output_hash"]
    assert row["provider_finish_reason"] == "length"
    assert row["provider_truncation_indicated"] is True
    assert row["structured_validation_result"] == "FAIL"
    assert row["structured_validation_failure_class"] == "structured_output_schema_invalid"
    assert row["structured_validation_diagnostic_code"] == "json_truncated"
    assert row["parser_or_schema_failure_category"] == "json_truncated"


def test_validator_parse_exception_becomes_sanitized_attempt_diagnostic() -> None:
    def validator(text: str):
        return True, None, json.loads(text)

    result = run(scripted({P0: [good(P0, text="not-json")]}), validator=validator)
    row = result["attempts"][0]
    assert row["structured_validation_result"] == "FAIL"
    assert row["failure_class"] == "structured_output_schema_invalid"
    assert row["structured_validation_diagnostic_code"] == "validator_exception_jsondecodeerror"


def test_completed_invocation_records_required_totals() -> None:
    provider = scripted({P0: [fail("read_timeout")], P1: [good(P1)]})
    result = run(provider)
    for key in (
        "selected_model",
        "models_attempted_in_order",
        "total_attempts",
        "total_fallback_transitions",
        "total_retry_sleep_seconds",
        "total_elapsed_seconds",
        "total_usage",
        "total_cost",
        "terminal_disposition",
        "budget_exhausted",
    ):
        assert key in result, key
    assert result["total_usage"] == {"total_tokens": 10.0}
    assert result["total_cost"] == {"usd": 0.0001}


def test_no_raw_prompt_is_embedded_in_attempt_evidence() -> None:
    secret_prompt = "SENSITIVE-EDITORIAL-PROMPT-BODY-DO-NOT-DUPLICATE"
    result = run(scripted({P0: [good(P0)]}), prompt=secret_prompt)
    blob = json.dumps(result["attempts"])
    assert secret_prompt not in blob
    assert result["attempts"][0]["prompt_logical_hash"]


def test_router_output_contains_no_secret_shaped_material() -> None:
    leaky = ProviderResult(
        failure_class="provider_temporarily_unavailable",
        resolved_model=None,
    )
    result = run(scripted({m: [leaky] for m in ORDERED_MODEL_POOL}))
    blob = json.dumps(result)
    for needle in ("Bearer ", "api_key=", "NINE_ROUTER_API_KEY="):
        assert needle not in blob


def test_fallback_success_does_not_create_publication_authority() -> None:
    provider = scripted({P0: [fail("read_timeout")], P1: [good(P1)]})
    result = run(provider)
    assert result["selected_model"] == P1
    assert result["fallback_grants_publication_authority"] is False
    assert result["fallback_output_uses_same_downstream_gates"] is True
