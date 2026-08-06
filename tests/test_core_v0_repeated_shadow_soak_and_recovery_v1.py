"""Focused tests for the Work Package E repeated shadow soak and recovery.

These tests are the launch oracle for this task. They deliberately do not run the noisy
monolithic historical repository suite; they exercise the new soak, drill, launch-edge,
and SLO logic plus the exact seams where it touches the accepted pipeline.

One full soak is executed once per session (module-scoped fixture) because it is the real
end-to-end artifact every assertion reads.
"""
from __future__ import annotations

import json
import pathlib
import sqlite3

import pytest

from live_contentops.core_v0_launch_edge_dry_model_v1 import (
    ACTOR_AUTONOMOUS_POLICY,
    ACTOR_OPERATOR_DECISION,
    AUTHORIZATION_ACTORS,
    MODE_AUTONOMOUS_DEFAULT,
    MODE_KILL_SWITCH,
    MODE_SHADOW_ONLY,
    MODE_SUPERVISED_OPERATOR_GATE,
    OPERATING_MODES,
    RECONCILED_ABSENT_SAFE_TO_RETRY,
    RECONCILED_CONFIRMED,
    RECONCILIATION_PENDING,
    REQUIRED_RELEASE_BINDINGS,
    LaunchEdgeError,
    authorize_release,
    build_release_intent,
    build_simulated_operation,
    classify_unknown_write,
    evaluate_release_queue_under_kill_switch,
    revalidate_authorization,
)
from live_contentops.core_v0_repeated_shadow_soak_v1 import (
    DEFAULT_LOGICAL_DAYS,
    INTAKE_WINDOWS,
    SOAK_CLASS,
    LogicalClock,
    SoakError,
    accepted_history_rows_for_day,
    build_logical_day_plan,
)
from live_contentops.core_v0_shadow_soak_runner_v1 import (
    REMAINING_LAUNCH_BLOCKERS,
    run_core_v0_shadow_soak,
)
from live_contentops.core_v0_soak_recovery_drills_v1 import REQUIRED_DRILLS
from live_contentops.core_v0_soak_slo_report_v1 import (
    BLOCKED_DEFECT,
    FAIL,
    FAIL_BREACH,
    INSUFFICIENT_EVIDENCE,
    NOT_APPLICABLE,
    PASS,
    READY,
    READY_WITH_CAVEATS,
    UNMEASURABLE,
    VERDICTS,
)
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

#: Three logical days is enough to prove repetition, accumulation, and every drill while
#: keeping the suite fast. The full ten-day run is exercised by the canonical command.
TEST_LOGICAL_DAYS = 3


@pytest.fixture(scope="module")
def soak(tmp_path_factory):
    root = tmp_path_factory.mktemp("wp_e_soak")
    output = root / "out"
    summary = run_core_v0_shadow_soak(
        repo_root=REPO_ROOT,
        store_path=root / "store.sqlite",
        output_dir=output,
        logical_days=TEST_LOGICAL_DAYS,
    )
    return {
        "summary": summary,
        "output_dir": output,
        "store_path": root / "store.sqlite",
        "days": json.loads((output / "soak_logical_days.json").read_text(encoding="utf-8")),
        "drills": json.loads((output / "soak_recovery_drills.json").read_text(encoding="utf-8")),
        "slo": json.loads((output / "soak_slo_report.json").read_text(encoding="utf-8")),
        "launch_edge": json.loads((output / "soak_launch_edge.json").read_text(encoding="utf-8")),
        "v5": json.loads((output / "v5_soak_snapshot.json").read_text(encoding="utf-8")),
    }


# ---------------------------------------------------------------------------
# Logical clock and day plan
# ---------------------------------------------------------------------------


def test_logical_clock_is_deterministic_and_monotonic() -> None:
    clock = LogicalClock("2026-07-15T00:00:00Z")
    assert clock.now_iso() == "2026-07-15T00:00:00Z"
    clock.advance(hours=2, minutes=30)
    assert clock.now_iso() == "2026-07-15T02:30:00Z"
    clock.set_to("2026-07-16T00:00:00Z")
    assert clock.now_iso() == "2026-07-16T00:00:00Z"
    assert clock.elapsed_logical_seconds == 86400


def test_logical_clock_refuses_to_move_backwards() -> None:
    clock = LogicalClock("2026-07-15T00:00:00Z")
    clock.advance(days=1)
    with pytest.raises(SoakError, match="cannot_move_backwards"):
        clock.set_to("2026-07-15T00:00:00Z")
    with pytest.raises(SoakError, match="cannot_move_backwards"):
        clock.advance(seconds=-1)


def test_day_plan_covers_required_days_and_windows() -> None:
    plan = build_logical_day_plan(logical_days=DEFAULT_LOGICAL_DAYS)
    assert len(plan) == DEFAULT_LOGICAL_DAYS
    total_windows = sum(day["intake_window_count"] for day in plan)
    # The task requires at least 30 window decisions across 7-10 logical days.
    assert total_windows >= 30
    assert all(day["intake_window_count"] == len(INTAKE_WINDOWS) for day in plan)
    # Windows are half-open and contiguous within the day.
    for day in plan:
        assert day["decision_window_start_utc"] < day["decision_window_end_utc"]
        assert day["decision_window_id"] == day["logical_day_id"]
        assert day["intake_windows"][0]["window_opens_utc"] == day["decision_window_start_utc"]


def test_day_plan_rejects_nonsense_inputs() -> None:
    with pytest.raises(SoakError, match="logical_days_must_be_positive"):
        build_logical_day_plan(logical_days=0)


# ---------------------------------------------------------------------------
# Repeated operation
# ---------------------------------------------------------------------------


def test_soak_runs_every_logical_day_and_completes_every_window(soak) -> None:
    summary = soak["summary"]
    assert summary["logical_days"] == TEST_LOGICAL_DAYS
    assert summary["intake_windows_completed"] == summary["intake_windows_total"]
    assert summary["intake_windows_total"] == TEST_LOGICAL_DAYS * len(INTAKE_WINDOWS)
    assert len(set(summary["logical_day_ids"])) == TEST_LOGICAL_DAYS


def test_soak_does_not_create_a_second_production_runner(soak) -> None:
    summary = soak["summary"]
    assert summary["second_production_runner_created"] is False
    reuses = summary["reuses_accepted_pipeline"]
    assert reuses["cohort_runner"] == "core_v0_cohort_shadow_runner_v1.run_cohort"
    assert reuses["review_engine"] == "editorial_review_orchestrator_v2.run_editorial_review"
    assert reuses["durable_store"] == "durable_operational_store_v1.ContentOpsDurableStore"


def test_each_logical_day_is_a_genuinely_different_decision(soak) -> None:
    days = soak["days"]["logical_days"]
    hashes = [day["logical_day_hash"] for day in days]
    assert len(set(hashes)) == len(hashes), "each logical day must be a distinct decision"
    # Accepted history must accumulate, which is what makes later days different.
    counts = [day["accepted_history_case_count"] for day in days]
    assert counts == sorted(counts)
    assert counts[-1] > counts[0]


def test_every_case_reaches_an_explicit_outcome_on_every_day(soak) -> None:
    for day in soak["days"]["logical_days"]:
        for case in day["cases"]:
            assert case["outcome"], f"{case['case_id']} has no outcome"
            assert case["terminal_state"], f"{case['case_id']} has no terminal state"
        # A blocked case must never reach the review-ready terminal state.
        for case in day["cases"]:
            if case["review_result"] != "PASS":
                assert case["terminal_state"] != "REVIEW_READY"


def test_soak_produces_abstentions_and_duplicate_decisions(soak) -> None:
    counts = soak["slo"]["cohort_counts"]
    assert counts["no_publication_decisions"] >= TEST_LOGICAL_DAYS
    assert counts["duplicate_or_update_chain_decisions"] >= TEST_LOGICAL_DAYS
    assert counts["complete_packages"] > 0


def test_both_lanes_produce_packages(soak) -> None:
    lanes = soak["slo"]["cohort_counts"]["packages_by_lane"]
    assert lanes.get("newsroom", 0) > 0
    assert lanes.get("capital_chronicle", 0) > 0
    assert soak["slo"]["cohort_counts"]["capital_chronicle_transformations"] > 0


def test_every_domain_family_receives_an_explicit_decision(soak) -> None:
    counts = soak["slo"]["cohort_counts"]
    # Nine governed domain families, all decided; the task target was at least eight.
    assert counts["domains_decided_count"] >= 8


def test_accepted_history_projection_only_includes_selected_and_passing() -> None:
    day_result = {
        "logical_day_id": "2026-07-15",
        "decision_window_start_utc": "2026-07-15T00:00:00Z",
        "selected_case_ids": ["a", "b"],
        "cohort": {
            "cases": [
                {"case_id": "a", "review_result": "PASS", "lane": "newsroom"},
                {"case_id": "b", "review_result": "REVIEW_BLOCKED", "lane": "newsroom"},
                {"case_id": "c", "review_result": "PASS", "lane": "newsroom"},
            ]
        },
    }
    rows = accepted_history_rows_for_day(day_result)
    assert [row["case_id"] for row in rows] == ["2026-07-15-a"]
    assert rows[0]["disposition"] == "SELECTED"
    assert rows[0]["presented_as_current_news"] is False


# ---------------------------------------------------------------------------
# Durability, restart, and determinism
# ---------------------------------------------------------------------------


def test_no_durable_work_item_is_lost_or_double_claimed(soak) -> None:
    durable = soak["summary"]["durable"]
    assert durable["work_item_count"] > 0
    assert durable["lost_work_items"] == 0
    assert durable["duplicate_durable_claims"] == 0
    assert durable["restart_reconstruction_status"] == "PASS"
    assert durable["schema_version"] == 4


def test_store_reopens_and_replays_independently(soak) -> None:
    store = ContentOpsDurableStore(soak["store_path"], auto_migrate=True)
    assert store.verify_schema_integrity() is True
    assert store.verify_applied_migrations() is True
    reconstruction = store.reconstruct_in_flight_state()
    assert reconstruction["restart_reconstruction_status"] == "PASS"
    assert reconstruction["verified_work_items_count"] >= soak["summary"]["durable"][
        "work_item_count"
    ]


def test_exported_store_evidence_is_redacted(soak) -> None:
    store = ContentOpsDurableStore(soak["store_path"], auto_migrate=True)
    evidence = store.export_redacted_store_evidence()
    assert evidence["redaction_guarantee"].startswith("PASS_NO_SECRETS")
    blob = json.dumps(evidence)
    assert "[REDACTED_TITLE]" in blob
    assert "[REDACTED_ACTOR_REF]" in blob


def test_determinism_is_declared_with_its_exceptions(soak) -> None:
    determinism = soak["summary"]["determinism"]
    assert determinism["identical_artifacts"] == determinism["compared_artifacts"]
    # Runtime is the only permitted nondeterministic output and must be named explicitly.
    assert "runtime_seconds" in determinism["documented_nondeterministic_fields"]
    assert soak["summary"]["runtime"]["runtime_is_nondeterministic_by_design"] is True


def test_repeated_soak_is_byte_identical_except_runtime(tmp_path) -> None:
    """Two runs over identical logical inputs must agree on every logical hash."""
    outputs = []
    for index in range(2):
        out = tmp_path / f"run{index}"
        summary = run_core_v0_shadow_soak(
            repo_root=REPO_ROOT,
            store_path=tmp_path / f"store{index}.sqlite",
            output_dir=out,
            logical_days=2,
            run_drills=False,
        )
        outputs.append((summary, out))

    first, second = outputs
    assert first[0]["soak_summary_logical_hash"] == second[0]["soak_summary_logical_hash"]
    assert first[0]["logical_day_ids"] == second[0]["logical_day_ids"]
    for name in ("soak_logical_days.json", "soak_launch_edge.json"):
        assert (first[1] / name).read_bytes() == (second[1] / name).read_bytes(), name
    # Runtime genuinely varies and must not be asserted equal.
    assert set(first[0]["runtime"]) == set(second[0]["runtime"])


# ---------------------------------------------------------------------------
# Recovery and failure drills
# ---------------------------------------------------------------------------


def test_every_required_drill_ran_and_passed(soak) -> None:
    drills = soak["drills"]["drills"]
    executed = {row["drill"] for row in drills}
    assert executed == set(REQUIRED_DRILLS), f"missing: {set(REQUIRED_DRILLS) - executed}"
    assert len(REQUIRED_DRILLS) == 16
    failed = [row["drill"] for row in drills if row["result"] != PASS]
    assert not failed, f"failed drills: {failed}"


def test_each_drill_states_its_question_and_observation(soak) -> None:
    for row in soak["drills"]["drills"]:
        assert row["question"].endswith("?")
        assert row["expected_behaviour"]
        assert row["observed_behaviour"]
        assert row["drill_logical_hash"]


def test_restart_drills_cover_all_three_required_points(soak) -> None:
    by_name = {row["drill"]: row for row in soak["drills"]["drills"]}
    for name, expected_state in (
        ("restart_between_intake_and_selection", "ASSIGNMENT_CANDIDATE"),
        ("restart_during_package_production", "PRODUCTION_IN_PROGRESS"),
        ("restart_after_package_before_release_intent_claim", "REVIEW_READY"),
    ):
        detail = by_name[name]["detail"]
        assert detail["state_after_restart"] == expected_state
        assert detail["state_before_restart"] == detail["state_after_restart"]
        assert detail["replay_verification"] == "PASS"
        assert detail["work_lost"] is False


def test_duplicate_tick_creates_no_duplicate_durable_work(soak) -> None:
    detail = next(
        row for row in soak["drills"]["drills"] if row["drill"] == "duplicate_scheduler_window_tick"
    )["detail"]
    assert detail["duplicate_work_items_created"] == 0
    assert detail["durable_events_after_two_ticks"] == 1


def test_concurrent_claim_has_exactly_one_winner(soak) -> None:
    detail = next(
        row
        for row in soak["drills"]["drills"]
        if row["drill"] == "concurrent_workers_same_durable_item"
    )["detail"]
    assert len(detail["winning_owners"]) == 1
    assert len(detail["refused_owners"]) == 1
    assert detail["duplicate_durable_claims"] == 0
    assert detail["stale_fencing_token_rejected"] is True


def test_corrupted_evidence_does_not_damage_durable_truth(soak) -> None:
    detail = next(
        row
        for row in soak["drills"]["drills"]
        if row["drill"] == "corrupted_exported_evidence_store_intact"
    )["detail"]
    assert detail["corrupted_file_parses"] is False
    assert detail["store_integrity_verified"] is True
    assert detail["replay_verification"] == "PASS"
    assert detail["re_export_matches_original_hash"] is True
    assert detail["durable_store_mutated"] is False


def test_calibration_sweep_moves_dispositions_but_never_the_policy(soak) -> None:
    detail = next(
        row for row in soak["drills"]["drills"] if row["drill"] == "calibration_sensitivity_sweep"
    )["detail"]
    assert detail["hard_gate_outcomes_invariant_under_concentration_config"] is True
    assert detail["sealed_policy_hash_unchanged"] is True
    assert detail["sweep_recorded_as_override_not_policy_change"] is True
    for row in detail["observations"]:
        assert row["eligible_case_ids_unchanged"] is True
        assert row["recorded_as_override_not_policy_change"] is True


def test_content_gates_fire_on_every_logical_day(soak) -> None:
    by_name = {row["drill"]: row for row in soak["drills"]["drills"]}
    for name in ("source_unavailable", "rights_cleared_visual_unavailable"):
        detail = by_name[name]["detail"]
        assert detail["logical_days_observed"] == detail["logical_days_total"]
        assert detail["blocked_case_reached_review_ready"] is False


def test_chart_qa_failure_never_reaches_a_passing_package(soak) -> None:
    detail = next(
        row for row in soak["drills"]["drills"] if row["drill"] == "chart_qa_failure"
    )["detail"]
    assert detail["failing_chart_inside_passing_package"] is False
    assert detail["charts_failed_qa"] == 0


def test_update_chain_continues_across_days(soak) -> None:
    detail = next(
        row
        for row in soak["drills"]["drills"]
        if row["drill"] == "material_update_chain_continuation"
    )["detail"]
    assert detail["multi_day_update_chain_count"] > 0
    assert detail["duplicate_or_low_delta_suppressions"] > 0


# ---------------------------------------------------------------------------
# Launch-edge dry model
# ---------------------------------------------------------------------------


def test_release_intent_binds_all_eight_required_hashes() -> None:
    intent = build_release_intent(
        case_id="c1",
        logical_day_id="2026-07-15",
        platform_id="substack",
        account_binding_id="acct_1",
        package={"article": {"headline": "h"}, "evidence": [{"claim": "x"}]},
        variant={"text": "body"},
        policy_hash="policy_hash_value",
        freshness={"window": "2026-07-15"},
    )
    assert set(intent["bindings"]) == set(REQUIRED_RELEASE_BINDINGS)
    assert len(REQUIRED_RELEASE_BINDINGS) == 8
    assert intent["release_intent_hash"]
    assert intent["boolean_approval_accepted_as_authority"] is False


def test_release_intent_refuses_a_missing_binding() -> None:
    with pytest.raises(LaunchEdgeError, match="release_intent_missing_bindings"):
        build_release_intent(
            case_id="c1",
            logical_day_id="2026-07-15",
            platform_id="",  # missing platform binding
            account_binding_id="acct_1",
            package={"a": 1},
            variant={"v": 1},
            policy_hash="ph",
            freshness={"f": 1},
        )


def test_both_authorization_actors_are_supported_without_mandatory_human_approval(soak) -> None:
    actors = soak["launch_edge"]["authorization_actors_exercised"]
    assert set(actors) == set(AUTHORIZATION_ACTORS)
    assert ACTOR_AUTONOMOUS_POLICY in actors
    assert ACTOR_OPERATOR_DECISION in actors
    assert soak["launch_edge"]["human_approval_universally_mandatory"] is False
    assert soak["launch_edge"]["boolean_approval_accepted_as_authority"] is False


def test_all_four_operating_modes_are_declared(soak) -> None:
    modes = soak["launch_edge"]["operating_modes_supported"]
    assert set(modes) == set(OPERATING_MODES)
    for mode in (
        MODE_AUTONOMOUS_DEFAULT,
        MODE_SUPERVISED_OPERATOR_GATE,
        MODE_SHADOW_ONLY,
        MODE_KILL_SWITCH,
    ):
        assert mode in modes


def test_autonomous_actor_requires_an_exact_owner_authorized_scope() -> None:
    intent = build_release_intent(
        case_id="c1",
        logical_day_id="2026-07-15",
        platform_id="substack",
        account_binding_id="acct_1",
        package={"a": 1},
        variant={"v": 1},
        policy_hash="ph",
        freshness={"f": 1},
    )
    without = authorize_release(
        intent=intent,
        actor=ACTOR_AUTONOMOUS_POLICY,
        actor_ref="policy",
        operating_mode=MODE_SHADOW_ONLY,
        logical_now_utc="2026-07-15T00:00:00Z",
    )
    assert "autonomous_policy_requires_exact_owner_authorized_live_scope" in without[
        "blocked_reasons"
    ]
    operator = authorize_release(
        intent=intent,
        actor=ACTOR_OPERATOR_DECISION,
        actor_ref="op",
        operating_mode=MODE_SUPERVISED_OPERATOR_GATE,
        logical_now_utc="2026-07-15T00:00:00Z",
    )
    assert "operator_decision_requires_exact_decision_id" in operator["blocked_reasons"]


def test_authorization_never_grants_live_dispatch_from_this_task() -> None:
    intent = build_release_intent(
        case_id="c1",
        logical_day_id="2026-07-15",
        platform_id="substack",
        account_binding_id="acct_1",
        package={"a": 1},
        variant={"v": 1},
        policy_hash="ph",
        freshness={"f": 1},
    )
    auth = authorize_release(
        intent=intent,
        actor=ACTOR_AUTONOMOUS_POLICY,
        actor_ref="policy",
        operating_mode=MODE_SHADOW_ONLY,
        logical_now_utc="2026-07-15T00:00:00Z",
        autonomous_scope_id="scope",
    )
    assert auth["valid_for_live_dispatch_now"] is False
    assert "shadow_only_task_grants_no_live_dispatch_authority" in auth["blocked_reasons"]


def test_authorization_is_invalidated_by_any_bound_byte_change(soak) -> None:
    proof = soak["launch_edge"]["invalidation_on_bound_byte_change"]
    assert proof["performed"] is True
    assert proof["still_valid_after_byte_change"] is False
    assert "bound_bytes_changed_authorization_invalidated" in proof["blocked_reasons"]


def test_authorization_expires(soak) -> None:
    proof = soak["launch_edge"]["expiry_proof"]
    assert proof["performed"] is True
    assert proof["expired"] is True
    assert proof["still_valid"] is False


def test_no_payload_is_rebuilt_after_authorization(soak) -> None:
    assert soak["launch_edge"]["payload_rebuilt_after_authorization"] is False


def test_one_simulated_operation_per_applicable_destination(soak) -> None:
    edge = soak["launch_edge"]
    assert edge["simulated_operation_count"] > 0
    # Operation-level idempotency: every operation has its own distinct key.
    assert edge["distinct_idempotency_keys"] == edge["simulated_operation_count"]
    assert edge["operations_executed"] == 0
    assert edge["outbox_executed"] is False
    assert edge["platform_action_performed"] is False


def test_repeated_operation_for_identical_bytes_is_suppressed() -> None:
    intent = build_release_intent(
        case_id="c1",
        logical_day_id="2026-07-15",
        platform_id="substack",
        account_binding_id="acct_1",
        package={"a": 1},
        variant={"v": 1},
        policy_hash="ph",
        freshness={"f": 1},
    )
    auth = authorize_release(
        intent=intent,
        actor=ACTOR_AUTONOMOUS_POLICY,
        actor_ref="policy",
        operating_mode=MODE_SHADOW_ONLY,
        logical_now_utc="2026-07-15T00:00:00Z",
        autonomous_scope_id="scope",
    )
    kwargs = dict(
        intent=intent,
        authorization=auth,
        destination_binding_id="db1",
        payload_text="hello",
        media_manifest_hash="mh",
        policy_snapshot_id="v1",
    )
    first = build_simulated_operation(**kwargs)
    second = build_simulated_operation(**kwargs, existing_keys=[first["idempotency_key"]])
    assert first["idempotency_key"] == second["idempotency_key"]
    assert first["duplicate_suppressed"] is False
    assert second["duplicate_suppressed"] is True


@pytest.mark.parametrize(
    "readback,expected_state,safe_to_retry,recovery",
    [
        (True, RECONCILED_CONFIRMED, False, False),
        (False, RECONCILED_ABSENT_SAFE_TO_RETRY, True, False),
        (None, RECONCILIATION_PENDING, False, True),
    ],
)
def test_unknown_write_classification_never_blind_retries(
    readback, expected_state, safe_to_retry, recovery
) -> None:
    operation = {"operation_id": "op_1", "idempotency_key": "key_1"}
    result = classify_unknown_write(operation=operation, readback_present=readback)
    assert result["resolution_state"] == expected_state
    assert result["safe_to_retry"] is safe_to_retry
    assert result["requires_operator_recovery"] is recovery
    # The invariant that matters: never an automatic retry, never a duplicate object.
    assert result["auto_retry_allowed"] is False
    assert result["blind_retry_performed"] is False
    assert result["duplicate_simulated_object_created"] is False
    assert result["retry_would_reuse_same_idempotency_key"] is True


def test_soak_exercises_all_three_reconciliation_outcomes(soak) -> None:
    states = {
        row["resolution_state"] for row in soak["launch_edge"]["unknown_write_resolutions"]
    }
    assert states == {
        RECONCILED_CONFIRMED,
        RECONCILED_ABSENT_SAFE_TO_RETRY,
        RECONCILIATION_PENDING,
    }
    assert soak["launch_edge"]["unknown_writes_auto_retried"] == 0
    assert soak["launch_edge"]["duplicate_simulated_objects_created"] == 0


def test_kill_switch_blocks_the_release_queue_without_deleting_it() -> None:
    result = evaluate_release_queue_under_kill_switch(
        operations=[{"operation_id": "op_1"}, {"operation_id": "op_2"}],
        kill_switch_active=True,
    )
    assert result["operations_processed"] == 0
    assert result["operations_blocked"] == 2
    assert result["queue_preserved_not_deleted"] is True
    assert result["outbox_executed"] is False


# ---------------------------------------------------------------------------
# SLO report and launch readiness
# ---------------------------------------------------------------------------


def test_every_measurement_has_a_denominator_and_a_legal_verdict(soak) -> None:
    measurements = soak["slo"]["measurements"]
    assert len(measurements) >= 17
    for row in measurements:
        assert row["verdict"] in VERDICTS
        assert row["question"].endswith("?")
        assert row["detail"]
        if row["verdict"] in (PASS, FAIL):
            # A pass or fail must be backed by an actual counted denominator.
            assert row["denominator"] is not None


def test_required_measurements_are_all_present(soak) -> None:
    names = {row["measurement"] for row in soak["slo"]["measurements"]}
    for required in (
        "window_completion",
        "lost_work_items",
        "duplicate_durable_claims",
        "restart_reconstruction",
        "hard_gate_replay_determinism",
        "package_lineage_completeness",
        "package_completion_time",
        "no_publication_count",
        "update_chain_count",
        "domain_concentration",
        "complete_package_count",
        "model_provider_attempts",
        "simulated_unknown_write_resolution",
        "incident_count_and_closure",
        "public_write_count",
        "external_cost_and_runtime",
        "operator_visible_blocker_count",
    ):
        assert required in names, required


def test_calendar_uptime_is_unmeasurable_and_never_claimed(soak) -> None:
    row = next(
        r for r in soak["slo"]["measurements"] if r["measurement"] == "calendar_uptime"
    )
    assert row["verdict"] == UNMEASURABLE
    assert soak["slo"]["calendar_uptime_claimed"] is False
    assert soak["slo"]["live_reliability_claimed"] is False
    assert soak["summary"]["soak_class"] == SOAK_CLASS
    assert "NOT_CALENDAR_UPTIME" in SOAK_CLASS


def test_model_provider_attempts_is_truthfully_not_applicable(soak) -> None:
    row = next(
        r for r in soak["slo"]["measurements"] if r["measurement"] == "model_provider_attempts"
    )
    assert row["verdict"] == NOT_APPLICABLE
    assert row["numerator"] == 0


def test_no_full_suite_or_ci_pass_is_claimed(soak) -> None:
    for document in (soak["summary"], soak["slo"], soak["v5"]["slo"]):
        assert document["full_suite_pass_claimed"] is False
        assert document["ci_pass_claimed"] is False


def test_launch_readiness_disposition_is_one_of_exactly_four(soak) -> None:
    disposition = soak["summary"]["launch_readiness_disposition"]
    assert disposition in (READY, READY_WITH_CAVEATS, BLOCKED_DEFECT, FAIL_BREACH)
    # An unqualified READY would be untrue while live authority is still outstanding.
    assert disposition == READY_WITH_CAVEATS
    assert soak["slo"]["launch_readiness_disposition"] == disposition


def test_remaining_launch_blockers_are_reported_verbatim(soak) -> None:
    assert soak["summary"]["remaining_launch_blockers"] == list(REMAINING_LAUNCH_BLOCKERS)
    assert soak["slo"]["remaining_launch_blockers"] == list(REMAINING_LAUNCH_BLOCKERS)
    joined = " ".join(REMAINING_LAUNCH_BLOCKERS)
    assert "owner-authorized live scope" in joined
    assert "credential" in joined


def test_evaluation_targets_never_lowered_a_gate(soak) -> None:
    targets = soak["slo"]["evaluation_targets"]
    assert targets["targets_are_evaluation_goals_not_publication_quotas"] is True
    assert targets["gates_lowered_to_reach_a_count"] is False


def test_markdown_report_is_written_and_readable(soak) -> None:
    text = (soak["output_dir"] / "soak_report.md").read_text(encoding="utf-8")
    assert "# CORE V0 Repeated Shadow Soak and Recovery" in text
    assert soak["summary"]["launch_readiness_disposition"] in text
    assert "accelerated logical soak" in text
    assert "not a claim of seven calendar days" in text
    # Every drill must be visible to a human reader, not just the machine report.
    for drill in REQUIRED_DRILLS:
        assert drill in text


# ---------------------------------------------------------------------------
# Safety posture
# ---------------------------------------------------------------------------


def test_no_live_action_flag_is_ever_true(soak) -> None:
    for name in (
        "soak_run_summary.json",
        "soak_logical_days.json",
        "soak_recovery_drills.json",
        "soak_slo_report.json",
        "soak_launch_edge.json",
        "v5_soak_snapshot.json",
    ):
        blob = json.loads((soak["output_dir"] / name).read_text(encoding="utf-8"))
        _assert_no_live_flags(blob, name)


def _assert_no_live_flags(node, where: str) -> None:
    flags = {
        "publication_authority",
        "dispatch_authority",
        "public_write_authority",
        "approval_captured",
        "credential_read_performed",
        "provider_call_performed",
        "network_call_performed",
        "browser_or_cdp_action_performed",
        "scheduler_or_outbox_action_performed",
        "public_write_performed",
        "upstream_write_performed",
    }
    if isinstance(node, dict):
        for key, value in node.items():
            if key in flags:
                assert value is False, f"{where}: {key} is not False"
            _assert_no_live_flags(value, where)
    elif isinstance(node, list):
        for child in node:
            _assert_no_live_flags(child, where)


def test_no_secret_shaped_material_in_any_artifact(soak) -> None:
    import re

    secret = re.compile(
        r"(?i)(bearer\s+[A-Za-z0-9._\-]{20,}|eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"
        r"|\b\d{6,12}:[A-Za-z0-9_-]{30,}\b|api[_-]?key\"?\s*[:=]\s*\"[^\"]{12,})"
    )
    for path in sorted(soak["output_dir"].glob("*.json")):
        text = path.read_text(encoding="utf-8")
        assert not secret.search(text), f"secret-shaped material in {path.name}"


def test_soak_reports_zero_cost_and_zero_public_writes(soak) -> None:
    assert soak["summary"]["external_cost"] == "NONE_NO_PAID_API_OR_MODEL_CALL"
    assert soak["summary"]["runtime"]["external_cost"] == "NONE_NO_PAID_API_OR_MODEL_CALL"
    public = next(
        r for r in soak["slo"]["measurements"] if r["measurement"] == "public_write_count"
    )
    assert public["numerator"] == 0
    assert public["verdict"] == PASS


def test_work_package_f_is_not_started(soak) -> None:
    assert soak["summary"]["work_package_f_started"] is False
    assert soak["v5"]["work_package_f_started"] is False


def test_selection_calibration_policy_is_unmutated(soak) -> None:
    from live_contentops.core_v0_shadow_selection_calibration_policy_v1 import (
        POLICY_LOGICAL_HASH,
    )

    assert soak["summary"]["selection_calibration_policy_logical_hash"] == POLICY_LOGICAL_HASH
    assert soak["summary"]["calibration_policy_authorized_for_live_publication"] is False


# ---------------------------------------------------------------------------
# V5 snapshot
# ---------------------------------------------------------------------------


def test_v5_snapshot_is_generated_from_the_real_run(soak) -> None:
    v5 = soak["v5"]
    assert v5["generated_from_real_run"] is True
    assert v5["operating_mode"] == "SHADOW_ONLY"
    assert len(v5["logical_days"]) == TEST_LOGICAL_DAYS
    assert len(v5["recovery_drills"]) == len(REQUIRED_DRILLS)
    assert v5["launch_readiness_disposition"] == soak["summary"]["launch_readiness_disposition"]


def test_v5_snapshot_shows_kill_switch_and_modes(soak) -> None:
    v5 = soak["v5"]
    assert v5["kill_switch_blocks_release_queue"] is True
    assert set(v5["operating_modes_supported"]) == set(OPERATING_MODES)


def test_v5_snapshot_carries_slo_denominators_and_blockers(soak) -> None:
    v5 = soak["v5"]
    assert v5["slo"]["measurements"]
    for row in v5["slo"]["measurements"]:
        assert row["verdict"] in VERDICTS
    assert v5["remaining_launch_blockers"] == list(REMAINING_LAUNCH_BLOCKERS)


def test_v5_snapshot_marks_capital_chronicle_transformation_fidelity(soak) -> None:
    faithful = [
        case
        for day in soak["v5"]["logical_days"]
        for case in day["cases"]
        if case["faithful_transformation"]
    ]
    assert faithful, "at least one faithful Capital Chronicle transformation must be shown"
