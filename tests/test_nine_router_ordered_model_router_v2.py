"""Deterministic fault-injection matrix for the canonical 9router ordered model router.

Every case here is a bounded synthetic experiment against a fake provider. No network call,
no credential read, no cost. The matrix exists so the real-provider preflight never has to
manufacture paid failures to prove the retry algorithm.

Cases A–N map one-to-one onto the authorized validation matrix.
"""
from __future__ import annotations

import json

import pytest

from live_contentops.nine_router_ordered_model_router_v2 import (
    ACCEPTED,
    AUTHORITY_ID,
    AUTHORIZED_MODELS,
    GATEWAY,
    IDENTITY_MISMATCH_CLASS,
    IDENTITY_NOT_VERIFIABLE,
    IDENTITY_REJECTED,
    MAX_TOTAL_PROVIDER_ATTEMPTS,
    NON_RETRYABLE_CLASSES,
    ORDERED_MODEL_POOL,
    POOL_EXHAUSTED,
    PRIMARY_MODEL,
    RETRY_BUDGET_EXHAUSTED,
    RETRYABLE_CLASSES,
    SUPERSEDES_AUTHORITY_ID,
    TERMINAL_NON_RETRYABLE,
    ModelRouterError,
    ProviderResult,
    RetryBudget,
    authority_packet,
    classify_failure,
    is_fallback_eligible,
    is_retryable,
    is_terminal,
    retry_budget_policy,
    route_llm_invocation,
)

P0, P1, P2, P3 = ORDERED_MODEL_POOL


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
        "new/claude-fable-5",
        "new/gpt-5.6-sol-xhigh",
        "new/claude-opus-5",
        "vx/gemini-3.1-pro-preview(high)",
    )
    assert PRIMARY_MODEL == "new/claude-fable-5"
    assert len(ORDERED_MODEL_POOL) == 4
    assert len(AUTHORIZED_MODELS) == 5
    assert "vx/gemini-3.5-flash(high)" in AUTHORIZED_MODELS


def test_declared_retry_budget_defaults() -> None:
    policy = retry_budget_policy()
    assert policy["max_total_provider_attempts"] == 6
    assert policy["max_fallback_transitions"] == 3
    assert policy["max_same_model_retries"] == 1
    assert policy["max_structured_output_repair_attempts"] == 1
    assert policy["structured_repair_counts_against_total_attempts"] is True
    assert policy["max_cumulative_retry_sleep_seconds"] == 45.0
    assert policy["default_wall_clock_budget_seconds"] == 300.0
    assert policy["per_model_max_attempts"] == {P0: 2, P1: 2, P2: 1, P3: 1}
    assert policy["budget_resets_on_model_change"] is False
    assert policy["budget_resets_on_reconstruction"] is False


def test_router_refuses_an_unauthorized_model_in_the_pool() -> None:
    with pytest.raises(ModelRouterError, match="unauthorized_model_in_pool"):
        run(scripted({}), model_pool=["new/claude-fable-5", "some/unlisted-model"])


def test_budget_cannot_be_widened_beyond_declared_policy() -> None:
    RetryBudget(logical_invocation_id="i", max_total_provider_attempts=3)  # tightening is fine
    with pytest.raises(ModelRouterError, match="exceeds_declared_policy"):
        RetryBudget(logical_invocation_id="i", max_total_provider_attempts=7)


# ---------------------------------------------------------------------------
# Failure classification
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "klass",
    ["connection_timeout", "read_timeout", "http_429_rate_limited", "http_503_unavailable"],
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


def test_case_c_p0_quota_skips_futile_retry_and_p1_succeeds() -> None:
    provider = scripted({P0: [fail("quota_exhausted")], P1: [good(P1)]})
    result = run(provider)
    assert result["terminal_disposition"] == ACCEPTED
    assert result["selected_model"] == P1
    # A quota-exhausted model must not burn its same-model retry.
    assert result["total_attempts"] == 2
    assert [m for m, _ in provider.calls] == [P0, P1]
    assert result["total_fallback_transitions"] == 1
    assert result["attempts"][0]["failure_class"] == "quota_exhausted"
    assert result["attempts"][1]["fallback_from"] == P0
    assert result["attempts"][1]["fallback_reason"] == "quota_exhausted"


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
    assert result["total_attempts"] == 5
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


def test_case_g_six_attempt_budget_permits_no_seventh_provider_call() -> None:
    """The central bound: whatever the failure pattern, attempt seven never happens."""
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
    # No seventh call, explicitly.
    assert len(provider.calls) != 7
    assert all(row["attempt_number_global"] <= 6 for row in result["attempts"])


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
    assert sum(sleeper.slept) == 0.0, "must not sleep past the budget"
    assert result["total_retry_sleep_seconds"] <= 45.0
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
        clock.advance(120.0)
        return fail("read_timeout")

    result = run(slow, clock=clock, sleeper=RecordingSleeper())
    assert result["budget_exhausted"] is True
    assert result["budget_exhausted_reason"] == "wall_clock_budget_seconds"
    assert result["terminal_disposition"] == RETRY_BUDGET_EXHAUSTED


def test_fallback_transition_ceiling_is_enforced() -> None:
    provider = scripted({m: [fail("quota_exhausted")] for m in ORDERED_MODEL_POOL})
    result = run(provider)
    assert result["total_fallback_transitions"] <= 3


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
        "latency_seconds",
        "disposition",
    )
    for row in result["attempts"]:
        for key in required:
            assert key in row, f"attempt missing {key}"
    assert result["attempts"][-1]["usage"] == {"total_tokens": 10}
    assert result["attempts"][-1]["provider_invocation_id"] == f"inv_{P1}"
    assert result["attempts"][-1]["output_hash"]


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
