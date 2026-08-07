"""Generate the committed 9router model-router evidence packet.

Runs the deterministic fault-injection matrix, the bounded real four-model preflight, and a
real routed failover proof, then assembles the canonical run summary.

Real calls are deliberately spaced: rapid back-to-back probes trip upstream throttling on
the shared gateway, which would otherwise show up as a false model-unavailability result.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

from live_contentops.nine_router_ordered_model_router_v2 import (
    ORDERED_MODEL_POOL,
    RetryBudget,
    route_llm_invocation,
)
from live_contentops.nine_router_preflight_v2 import (
    PREFLIGHT_PROMPT,
    build_run_summary,
    run_preflight,
)
from live_contentops.nine_router_provider_adapter_v2 import call_nine_router

OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("evidence")
PROBE_SPACING_SECONDS = 6.0


def _spaced_call(prompt: str, model: str, timeout: float):
    result = call_nine_router(prompt, model, timeout, max_tokens=16, temperature=0.0)
    time.sleep(PROBE_SPACING_SECONDS)
    return result


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)

    # --- 1. Deterministic fault-injection matrix -------------------------------------
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/test_nine_router_ordered_model_router_v2.py",
            "tests/test_nine_router_provider_adapter_and_preflight_v2.py",
            "-q",
        ],
        capture_output=True,
        text=True,
    )
    tail = [line for line in proc.stdout.strip().splitlines() if line.strip()][-1:]
    fault_injection = {
        "runner": "pytest",
        "suites": [
            "tests/test_nine_router_ordered_model_router_v2.py",
            "tests/test_nine_router_provider_adapter_and_preflight_v2.py",
        ],
        "exit_code": proc.returncode,
        "summary_line": tail[0] if tail else "",
        "all_passed": proc.returncode == 0,
        "cases_covered": {
            "A_p0_first_try": "test_case_a_p0_succeeds_first_try",
            "B_p0_timeout_retry": "test_case_b_p0_timeout_then_p0_retry_succeeds",
            "C_quota_skip_to_p1": "test_case_c_p0_quota_skips_futile_retry_and_p1_succeeds",
            "D_p0_p1_fail_p2_succeeds": "test_case_d_p0_timeouts_then_p1_503s_then_p2_succeeds",
            "E_p0_p1_unavailable": "test_case_e_p0_and_p1_unavailable_p2_succeeds",
            "F_pool_exhausted": "test_case_f_entire_pool_unavailable_blocks_closed",
            "G_no_seventh_attempt": "test_case_g_six_attempt_budget_permits_no_seventh_provider_call",
            "H_sleep_budget": "test_case_h_retry_sleep_budget_stops_without_further_sleep_or_call",
            "I_structured_repair": "test_case_i_malformed_then_one_repair_attempt_succeeds",
            "J_repair_fails_fallback": "test_case_j_repair_fails_then_eligible_fallback",
            "K_no_rotation_on_gate_failure": "test_case_k_evidence_failure_never_rotates_models",
            "L_401_403_fail_closed": "test_case_l_401_and_403_fail_closed_without_a_model_carousel",
            "M_silent_substitution_rejected": "test_case_m_silent_substitution_to_another_model_is_rejected",
            "N_reconstruction_keeps_budget": "test_case_n_reconstruction_does_not_reset_the_consumed_budget",
        },
    }

    # --- 2. Real bounded four-model preflight ----------------------------------------
    preflight = run_preflight(provider_call=_spaced_call)

    # --- 3. Real routed failover proof over the live gateway --------------------------
    invocations: list[dict] = []
    healthy = [
        row["requested_model"]
        for row in preflight["per_model"]
        if row["health"] == "HEALTHY"
    ]
    unavailable = [
        row["requested_model"]
        for row in preflight["per_model"]
        if row["health"] == "TEMPORARILY_UNAVAILABLE"
    ]
    failover_proof = None
    if healthy and unavailable:
        # Order the pool so a genuinely unavailable model is tried first: the router must
        # advance to a healthy authorized model and accept its output.
        pool = [unavailable[0], healthy[0]]
        failover_proof = route_llm_invocation(
            logical_invocation_id="real_failover_proof",
            role_task_id="nine_router_failover_proof",
            prompt=PREFLIGHT_PROMPT,
            provider_call=_spaced_call,
            prompt_template="nine_router_preflight",
            prompt_version="v2",
            model_pool=pool,
            timeout_seconds=60.0,
            budget=RetryBudget(
                logical_invocation_id="real_failover_proof", max_total_provider_attempts=3
            ),
        )
        invocations.append(failover_proof)

    # --- 4. Real primary-model invocation through the full router ---------------------
    primary_proof = None
    if healthy:
        primary_proof = route_llm_invocation(
            logical_invocation_id="real_primary_proof",
            role_task_id="nine_router_preflight_probe",
            prompt=PREFLIGHT_PROMPT,
            provider_call=_spaced_call,
            prompt_template="nine_router_preflight",
            prompt_version="v2",
            model_pool=[healthy[0]],
            timeout_seconds=60.0,
            budget=RetryBudget(
                logical_invocation_id="real_primary_proof", max_total_provider_attempts=2
            ),
        )
        invocations.append(primary_proof)

    summary = build_run_summary(
        preflight=preflight,
        fault_injection=fault_injection,
        invocations=invocations,
        end_to_end={
            "real_failover_proof": failover_proof,
            "real_primary_model_proof": primary_proof,
            "note": (
                "Real calls exercise connectivity, exact-model acceptance, observable "
                "identity, response shape, and usage metadata. Retry/budget/exhaustion "
                "semantics are proven by deterministic fault injection so no paid failures "
                "are manufactured against real provider infrastructure."
            ),
        },
    )

    (OUT / "model_router_run_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "identity_disposition": preflight["model_identity_disposition"],
        "healthy": preflight["healthy_count"],
        "unavailable": preflight["unavailable_count"],
        "primary_model_healthy": preflight["primary_model_healthy"],
        "fault_injection_passed": fault_injection["all_passed"],
        "failover_disposition": (failover_proof or {}).get("terminal_disposition"),
        "failover_selected": (failover_proof or {}).get("selected_model"),
        "secret_redaction_status": summary["secret_redaction_status"],
    }, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
