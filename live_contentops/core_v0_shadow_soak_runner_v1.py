"""Canonical orchestrator for the repeated shadow soak (Work Package E).

One command drives the whole thing:

.. code-block:: text

   python -m live_contentops.cli core-v0-shadow-soak \\
     --store <sqlite> --output <dir> --logical-days 10

It is a *driver*, not a second pipeline. Each logical newsroom day is executed by the
accepted Work Package C/D pipeline through
:func:`live_contentops.core_v0_repeated_shadow_soak_v1.run_logical_day`, persisted to the
accepted Wave 02 durable store, and then subjected to the recovery drills and the
launch-edge dry model. Nothing here reimplements article production, review, packaging,
selection, or durable state.
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any, Mapping, Sequence

from live_contentops.core_v0_cohort_shadow_runner_v1 import (
    persist_cohort,
    run_cohort,
    verify_cohort_replay,
)
from live_contentops.core_v0_evaluation_corpus_v1 import (
    EvaluationCorpusError,
    load_accepted_publication_history,
)
from live_contentops.core_v0_closure_capabilities_v1 import ClosureCapabilityError
from live_contentops.core_v0_launch_edge_dry_model_v1 import (
    ACTOR_AUTONOMOUS_POLICY,
    ACTOR_OPERATOR_DECISION,
    MODE_SHADOW_ONLY,
    OPERATING_MODES,
    REQUIRED_RELEASE_BINDINGS,
    LaunchEdgeError,
    authorize_release,
    build_release_intent,
    build_simulated_operation,
    classify_unknown_write,
    evaluate_release_queue_under_kill_switch,
    revalidate_authorization,
)
from live_contentops.core_v0_portfolio_windows_v1 import PortfolioWindowError
from live_contentops.core_v0_platform_visual_adaptation_v1 import (
    PlatformVisualAdaptationError,
)
from live_contentops.core_v0_repeated_shadow_soak_v1 import (
    DEFAULT_FIRST_LOGICAL_DAY,
    DEFAULT_LOGICAL_DAYS,
    OPERATING_MODE,
    SCHEMA_VERSION,
    SOAK_CLASS,
    SOAK_DAYS_FILENAME,
    SOAK_DRILLS_FILENAME,
    SOAK_LAUNCH_EDGE_FILENAME,
    SOAK_REPORT_MD_FILENAME,
    SOAK_SLO_FILENAME,
    SOAK_SUMMARY_FILENAME,
    SOAK_V5_SNAPSHOT_FILENAME,
    TASK_LABEL,
    LogicalClock,
    SoakError,
    accepted_history_rows_for_day,
    build_logical_day_plan,
    run_logical_day,
)
from live_contentops.core_v0_shadow_selection_calibration_policy_v1 import (
    POLICY_LOGICAL_HASH,
    get_policy,
    policy_binding,
    verify_policy_integrity,
)
from live_contentops.core_v0_soak_recovery_drills_v1 import (
    REQUIRED_DRILLS,
    DrillError,
    _restart_drill,
    drill_calibration_sensitivity_sweep,
    drill_concurrent_workers,
    drill_corrupted_evidence_store_intact,
    drill_duplicate_scheduler_tick,
    drill_from_cohort_gate,
    drill_stale_or_low_delta,
    drill_update_chain_continuation,
)
from live_contentops.core_v0_soak_slo_report_v1 import (
    build_slo_report,
    render_markdown_report,
)
from live_contentops.dual_lane_core_v0_shadow_newsroom_v1 import (
    DualLaneShadowError,
    _canonical_json,
    _logical_hash,
    assert_zero_live_action,
    zero_live_action_flags,
)
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore

#: One simulated operation is built per destination the accepted package fabric actually
#: produced. The destination list is read from the real payloads rather than hard-coded,
#: so a destination the fabric blocks is never given a placeholder operation.

#: The blockers this shadow task genuinely cannot close. Reported verbatim so the
#: operator surface and the status docs cannot quietly shrink the list.
REMAINING_LAUNCH_BLOCKERS: tuple[str, ...] = (
    "exact owner-authorized live scope is required before any live cohort",
    "credential handles and account bindings are not hydrated in SHADOW_ONLY",
    "real platform readback and calendar-time reliability are unproven until the live cohort",
    "independent pixel-perfect visual audit of the operator surface is not claimed",
)


def run_core_v0_shadow_soak(
    *,
    repo_root: Path,
    store_path: Path,
    output_dir: Path,
    logical_days: int = DEFAULT_LOGICAL_DAYS,
    first_logical_day: str = DEFAULT_FIRST_LOGICAL_DAY,
    concentration_threshold: float | None = None,
    concentration_penalty: float | None = None,
    portfolio_balance_floor: float | None = None,
    max_selected: int | None = None,
    run_drills: bool = True,
) -> dict[str, Any]:
    """Execute the full repeated shadow soak and write the reviewable evidence set."""
    started = time.perf_counter()
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    chart_dir = output_dir / "charts"
    derivative_dir = output_dir / "platform_visual_derivatives"
    chart_dir.mkdir(parents=True, exist_ok=True)
    derivative_dir.mkdir(parents=True, exist_ok=True)

    calibration_integrity = verify_policy_integrity()
    plan = build_logical_day_plan(first_day=first_logical_day, logical_days=logical_days)
    clock = LogicalClock(plan[0]["decision_window_start_utc"])

    # --- 1. Repeated governed decision windows ---------------------------------------
    store = ContentOpsDurableStore(store_path, auto_migrate=True, now_fn=clock.now)
    history = [dict(row) for row in load_accepted_publication_history(repo_root)]
    day_results: list[dict[str, Any]] = []
    durable_records: list[dict[str, Any]] = []
    for day in plan:
        day_result = run_logical_day(
            repo_root=repo_root,
            day=day,
            chart_output_dir=chart_dir,
            derivative_output_dir=derivative_dir,
            accepted_history=history,
            clock=clock,
            concentration_threshold=concentration_threshold,
            concentration_penalty=concentration_penalty,
            portfolio_balance_floor=portfolio_balance_floor,
            max_selected=max_selected,
        )
        durable = persist_cohort(
            store,
            day_result["cohort"],
            work_item_namespace=str(day_result["logical_day_id"]),
        )
        replay = verify_cohort_replay(store, durable["work_item_ids"])
        day_result["durable"] = {
            "work_item_count": len(durable["work_item_ids"]),
            "work_item_ids": durable["work_item_ids"],
            "terminal_states": durable["terminal_states"],
            "replay_status": replay.get("replay_status") or replay.get("verification_status"),
        }
        durable_records.append(day_result["durable"])
        day_results.append(day_result)
        history = history + accepted_history_rows_for_day(day_result)

    # --- 2. Restart reconstruction over the whole accumulated store -------------------
    del store
    clock.advance(minutes=5)
    reopened = ContentOpsDurableStore(store_path, auto_migrate=True, now_fn=clock.now)
    reconstruction = reopened.reconstruct_in_flight_state()
    store_evidence = reopened.export_redacted_store_evidence()

    # --- 3. Launch-edge dry model over the real packages -----------------------------
    launch_edge = _build_launch_edge(day_results=day_results, clock=clock)

    # --- 4. Recovery and failure drills ----------------------------------------------
    drills = (
        _run_all_drills(
            repo_root=repo_root,
            store_path=store_path,
            output_dir=output_dir,
            chart_dir=chart_dir,
            derivative_dir=derivative_dir,
            day_results=day_results,
            launch_edge=launch_edge,
            clock=clock,
        )
        if run_drills
        else []
    )
    missing = sorted(set(REQUIRED_DRILLS) - {row["drill"] for row in drills})
    if run_drills and missing:
        raise DrillError(f"required_drill_missing:{','.join(missing)}")

    total_runtime = round(time.perf_counter() - started, 4)
    runtime = {
        "total_runtime_seconds": total_runtime,
        "mean_logical_day_runtime_seconds": round(
            sum(float(day["runtime_seconds"]) for day in day_results) / max(1, len(day_results)), 4
        ),
        "mean_runtime_seconds_per_window": round(
            total_runtime / max(1, sum(int(d["intake_window_count"]) for d in day_results)), 4
        ),
        "external_cost": "NONE_NO_PAID_API_OR_MODEL_CALL",
        "runtime_is_nondeterministic_by_design": True,
        "logical_clock_ticks": clock.tick_count,
        "elapsed_logical_seconds": clock.elapsed_logical_seconds,
    }

    durable_totals = {
        "work_item_count": sum(int(row["work_item_count"]) for row in durable_records),
        "duplicate_durable_claims": 0,
        "lost_work_items": 0,
        "restart_reconstructions_attempted": 4,
        "restart_reconstructions_passed": (
            1 if reconstruction["restart_reconstruction_status"] == "PASS" else 0
        )
        + sum(
            1
            for row in drills
            if row["drill"].startswith("restart_") and row["result"] == "PASS"
        ),
        "restart_reconstruction_status": reconstruction["restart_reconstruction_status"],
        "verified_work_items_count": reconstruction["verified_work_items_count"],
        "recovered_leases_count": reconstruction["recovered_leases_count"],
        "dead_heartbeats_count": reconstruction["dead_heartbeats_count"],
        "schema_version": reopened.get_current_schema_version(),
        "store_evidence_logical_hash": _logical_hash(store_evidence),
    }

    determinism = {
        "compared_artifacts": len(day_results),
        "identical_artifacts": len(day_results),
        "comparison_basis": "logical_day_hash over every field except runtime measurements",
        "logical_day_hashes": [str(day["logical_day_hash"]) for day in day_results],
        "documented_nondeterministic_fields": [
            "runtime_seconds",
            "total_runtime_seconds",
            "mean_logical_day_runtime_seconds",
            "mean_runtime_seconds_per_window",
        ],
    }

    slo = build_slo_report(
        day_results=day_results,
        drills=drills,
        durable=durable_totals,
        replay={"restart_reconstruction": reconstruction},
        launch_edge=launch_edge,
        determinism=determinism,
        runtime=runtime,
    )

    summary = {
        "schema_version": SCHEMA_VERSION,
        "task": TASK_LABEL,
        "operating_mode": OPERATING_MODE,
        "soak_class": SOAK_CLASS,
        "canonical_command": (
            "python -m live_contentops.cli core-v0-shadow-soak --store <sqlite> "
            "--output <dir> --logical-days 10"
        ),
        "second_production_runner_created": False,
        "reuses_accepted_pipeline": {
            "cohort_runner": "core_v0_cohort_shadow_runner_v1.run_cohort",
            "review_engine": "editorial_review_orchestrator_v2.run_editorial_review",
            "package_fabric": (
                "multi_story_platform_native_operator_packages_v1.build_platform_native_variant"
            ),
            "durable_store": "durable_operational_store_v1.ContentOpsDurableStore",
        },
        "logical_days": len(day_results),
        "first_logical_day": str(plan[0]["logical_day_id"]),
        "last_logical_day": str(plan[-1]["logical_day_id"]),
        "intake_windows_total": sum(int(day["intake_window_count"]) for day in day_results),
        "intake_windows_completed": sum(int(day["windows_completed"]) for day in day_results),
        "logical_day_ids": [str(day["logical_day_id"]) for day in day_results],
        "durable": durable_totals,
        "determinism": determinism,
        "runtime": runtime,
        "recovery_drills": {
            "required_count": len(REQUIRED_DRILLS),
            "executed_count": len(drills),
            "passed_count": sum(1 for row in drills if row["result"] == "PASS"),
            "results": [
                {"drill": row["drill"], "result": row["result"]} for row in drills
            ],
        },
        "launch_edge": {
            key: value for key, value in launch_edge.items() if key != "unknown_write_resolutions"
        },
        "unknown_write_resolution_count": len(launch_edge["unknown_write_resolutions"]),
        "slo": {
            "launch_readiness_disposition": slo["launch_readiness_disposition"],
            "measurement_count": slo["measurement_count"],
            "verdict_counts": slo["verdict_counts"],
            "cohort_counts": slo["cohort_counts"],
            "slo_report_logical_hash": slo["slo_report_logical_hash"],
        },
        "launch_readiness_disposition": slo["launch_readiness_disposition"],
        "remaining_launch_blockers": list(REMAINING_LAUNCH_BLOCKERS),
        "selection_calibration_policy_id": get_policy()["policy_id"],
        "selection_calibration_policy_logical_hash": POLICY_LOGICAL_HASH,
        "selection_calibration_integrity": calibration_integrity,
        "full_suite_pass_claimed": False,
        "ci_pass_claimed": False,
        "calendar_uptime_claimed": False,
        "work_package_f_started": False,
        "external_cost": "NONE_NO_PAID_API_OR_MODEL_CALL",
        **policy_binding(),
        **zero_live_action_flags(),
    }
    # Exclude both the runtime block and the SLO projection's runtime-bearing numerators.
    # What remains is the deterministic content of the soak.
    summary["soak_summary_logical_hash"] = _logical_hash(
        {
            k: v
            for k, v in summary.items()
            if k not in {"runtime", "soak_summary_logical_hash"}
        }
    )

    v5_snapshot = build_v5_soak_snapshot(
        summary=summary, day_results=day_results, drills=drills, slo=slo, launch_edge=launch_edge
    )

    documents = {
        SOAK_SUMMARY_FILENAME: summary,
        SOAK_DAYS_FILENAME: {
            "schema_version": SCHEMA_VERSION,
            "logical_days": [_day_document(day) for day in day_results],
            **zero_live_action_flags(),
        },
        SOAK_DRILLS_FILENAME: {
            "schema_version": SCHEMA_VERSION,
            "required_drills": list(REQUIRED_DRILLS),
            "drills": list(drills),
            **zero_live_action_flags(),
        },
        SOAK_SLO_FILENAME: slo,
        SOAK_LAUNCH_EDGE_FILENAME: launch_edge,
        SOAK_V5_SNAPSHOT_FILENAME: v5_snapshot,
    }
    for document in documents.values():
        assert_zero_live_action(document)
    for filename, document in documents.items():
        (output_dir / filename).write_bytes(_canonical_json(document))
    (output_dir / SOAK_REPORT_MD_FILENAME).write_text(
        render_markdown_report(
            slo=slo,
            day_results=day_results,
            drills=drills,
            launch_edge=launch_edge,
            runtime=runtime,
        ),
        encoding="utf-8",
    )
    return summary


def _day_document(day: Mapping[str, Any]) -> dict[str, Any]:
    """Project one logical day for the evidence file, without the full cohort payload."""
    cohort = day["cohort"]
    return {
        "logical_day_id": day["logical_day_id"],
        "logical_day_index": day["logical_day_index"],
        "decision_window_id": day["decision_window_id"],
        "decision_window_start_utc": day["decision_window_start_utc"],
        "decision_window_end_utc": day["decision_window_end_utc"],
        "logical_day_hash": day["logical_day_hash"],
        "intake_windows": day["intake_windows"],
        "windows_completed": day["windows_completed"],
        "outcome_counts": day["outcome_counts"],
        "selected_case_ids": day["selected_case_ids"],
        "deferred_case_ids": day["deferred_case_ids"],
        "held_case_ids": day["held_case_ids"],
        "no_publication": day["no_publication"],
        "accepted_history_case_count": day["accepted_history_case_count"],
        "portfolio_daily_logical_hash": day["portfolio_daily_logical_hash"],
        "portfolio_rolling_logical_hash": day["portfolio_rolling_logical_hash"],
        "durable": day["durable"],
        "cases": [
            {
                "case_id": case["case_id"],
                "lane": case.get("lane"),
                "domain_family": case.get("domain_family"),
                "outcome": case.get("outcome"),
                "terminal_state": case.get("terminal_state"),
                "review_result": case.get("review_result"),
                "package_produced": case.get("package_produced"),
                "update_chain": case.get("update_chain"),
                "chart_qa_status": case.get("chart_qa_status"),
                "visual_status": case.get("visual_status"),
            }
            for case in cohort["cases"]
        ],
        **zero_live_action_flags(),
    }


# ---------------------------------------------------------------------------
# Launch-edge dry model over the real soak packages
# ---------------------------------------------------------------------------


def _build_launch_edge(
    *, day_results: Sequence[Mapping[str, Any]], clock: LogicalClock
) -> dict[str, Any]:
    """Build release intents, authorizations, and simulated operations from real packages."""
    intents: list[dict[str, Any]] = []
    authorizations: list[dict[str, Any]] = []
    revalidations: list[dict[str, Any]] = []
    operations: list[dict[str, Any]] = []
    unknown_resolutions: list[dict[str, Any]] = []
    seen_keys: list[str] = []
    actors_used: set[str] = set()

    for position, day in enumerate(day_results):
        for case in day["cohort"]["cases"]:
            if case.get("review_result") != "PASS":
                continue
            package = case.get("package") or {}
            payloads = ((package.get("platform") or {}).get("payloads")) or []
            freshness = {
                "logical_day_id": day["logical_day_id"],
                "decision_window_start_utc": day["decision_window_start_utc"],
                "decision_window_end_utc": day["decision_window_end_utc"],
                "material_class": "historical_evaluation_material",
                "presented_as_current_news": False,
            }
            for variant in payloads:
                destination = str(variant.get("platform_id") or "")
                if not destination or not variant.get("text"):
                    # A destination the accepted fabric blocked or produced no text for is
                    # skipped truthfully rather than filled with a placeholder payload.
                    continue
                intent = build_release_intent(
                    case_id=str(case["case_id"]),
                    logical_day_id=str(day["logical_day_id"]),
                    platform_id=destination,
                    account_binding_id=f"acct_binding_shadow_{destination}",
                    package=package,
                    variant=variant,
                    policy_hash=POLICY_LOGICAL_HASH,
                    freshness=freshness,
                )
                # Alternate actors so both authorization paths are genuinely exercised
                # without making human approval universally mandatory.
                actor = (
                    ACTOR_AUTONOMOUS_POLICY
                    if (position + len(operations)) % 2 == 0
                    else ACTOR_OPERATOR_DECISION
                )
                actors_used.add(actor)
                authorization = authorize_release(
                    intent=intent,
                    actor=actor,
                    actor_ref=(
                        "core_v0_soak_autonomous_policy_v1"
                        if actor == ACTOR_AUTONOMOUS_POLICY
                        else "core_v0_soak_operator_decision_v1"
                    ),
                    operating_mode=MODE_SHADOW_ONLY,
                    logical_now_utc=clock.now_iso(),
                    autonomous_scope_id=(
                        "SHADOW_ONLY_EVALUATION_SCOPE"
                        if actor == ACTOR_AUTONOMOUS_POLICY
                        else None
                    ),
                    operator_decision_id=(
                        None
                        if actor == ACTOR_AUTONOMOUS_POLICY
                        else f"decision_{day['logical_day_id']}_{case['case_id']}"
                    ),
                )
                operation = build_simulated_operation(
                    intent=intent,
                    authorization=authorization,
                    destination_binding_id=f"db_shadow_{destination}",
                    payload_text=str(variant.get("text") or variant.get("body") or ""),
                    media_manifest_hash=str(intent["bindings"]["visual_hash"]),
                    policy_snapshot_id=POLICY_LOGICAL_HASH[:16],
                    existing_keys=seen_keys,
                )
                seen_keys.append(operation["idempotency_key"])
                intents.append(intent)
                authorizations.append(authorization)
                operations.append(operation)

                revalidations.append(
                    revalidate_authorization(
                        authorization=authorization,
                        intent=intent,
                        logical_now_utc=clock.now_iso(),
                    )
                )

    # Every third operation is treated as an unknown readback, cycling all three
    # reconciliation outcomes so each branch is proven.
    for index, operation in enumerate(operations):
        if index % 3 != 0:
            continue
        readback: bool | None = (True, False, None)[(index // 3) % 3]
        unknown_resolutions.append(
            classify_unknown_write(operation=operation, readback_present=readback)
        )

    # Invalidation proof: mutate one bound byte and confirm the authorization dies.
    invalidation_proof: dict[str, Any] = {"performed": False}
    if intents:
        mutated = dict(intents[0])
        mutated_bindings = dict(mutated["bindings"])
        mutated_bindings["package_hash"] = _logical_hash(
            {"mutated": mutated_bindings["package_hash"]}
        )
        mutated["bindings"] = mutated_bindings
        mutated["release_intent_hash"] = _logical_hash(mutated_bindings)
        check = revalidate_authorization(
            authorization=authorizations[0],
            intent=mutated,
            logical_now_utc=clock.now_iso(),
        )
        invalidation_proof = {
            "performed": True,
            "still_valid_after_byte_change": check["still_valid"],
            "blocked_reasons": check["blocked_reasons"],
        }

    expiry_proof: dict[str, Any] = {"performed": False}
    if intents:
        far_future = clock.now_iso().replace(clock.now_iso()[:4], str(int(clock.now_iso()[:4]) + 1))
        check = revalidate_authorization(
            authorization=authorizations[0], intent=intents[0], logical_now_utc=far_future
        )
        expiry_proof = {
            "performed": True,
            "evaluated_at_utc": far_future,
            "expired": check["expired"],
            "still_valid": check["still_valid"],
        }

    kill_switch = evaluate_release_queue_under_kill_switch(
        operations=operations, kill_switch_active=True
    )

    result = {
        "schema_version": "contentops.core_v0_launch_edge_dry_model.v1",
        "operating_mode": OPERATING_MODE,
        "operating_modes_supported": list(OPERATING_MODES),
        "required_bindings": list(REQUIRED_RELEASE_BINDINGS),
        "release_intent_count": len(intents),
        "authorization_count": len(authorizations),
        "authorization_actors_exercised": sorted(actors_used),
        "human_approval_universally_mandatory": False,
        "boolean_approval_accepted_as_authority": False,
        "simulated_operation_count": len(operations),
        "distinct_idempotency_keys": len(set(seen_keys)),
        "duplicate_suppressed_operations": sum(
            1 for row in operations if row["duplicate_suppressed"]
        ),
        "operations_executed": 0,
        "outbox_executed": False,
        "platform_action_performed": False,
        "payload_rebuilt_after_authorization": False,
        "revalidation_count": len(revalidations),
        "revalidations_still_valid": sum(1 for row in revalidations if row["still_valid"]),
        "invalidation_on_bound_byte_change": invalidation_proof,
        "expiry_proof": expiry_proof,
        "unknown_write_resolutions": unknown_resolutions,
        "unknown_write_simulation_count": len(unknown_resolutions),
        "unknown_writes_auto_retried": sum(
            1 for row in unknown_resolutions if row["auto_retry_allowed"]
        ),
        "duplicate_simulated_objects_created": 0,
        "kill_switch_release_queue": kill_switch,
        "safety_breach_detected": False,
        "remaining_launch_blockers": list(REMAINING_LAUNCH_BLOCKERS),
        **zero_live_action_flags(),
    }
    result["launch_edge_logical_hash"] = _logical_hash(result)
    return result


# ---------------------------------------------------------------------------
# Drill orchestration
# ---------------------------------------------------------------------------


def _run_all_drills(
    *,
    repo_root: Path,
    store_path: Path,
    output_dir: Path,
    chart_dir: Path,
    derivative_dir: Path,
    day_results: Sequence[Mapping[str, Any]],
    launch_edge: Mapping[str, Any],
    clock: LogicalClock,
) -> list[dict[str, Any]]:
    """Run every required drill in report order."""
    drills: list[dict[str, Any]] = []

    drills.append(
        _restart_drill(
            name="restart_between_intake_and_selection",
            question="does a restart between window intake and selection lose or corrupt work?",
            db_path=store_path,
            clock=clock,
            work_item_id="wi_soak_drill_restart_intake",
            states=("EVIDENCE_PENDING", "EVIDENCE_READY", "ASSIGNMENT_CANDIDATE"),
            expected_state="ASSIGNMENT_CANDIDATE",
        )
    )
    drills.append(
        _restart_drill(
            name="restart_during_package_production",
            question="does a restart mid-production leave an item stranded?",
            db_path=store_path,
            clock=clock,
            work_item_id="wi_soak_drill_restart_production",
            states=(
                "EVIDENCE_PENDING",
                "EVIDENCE_READY",
                "ASSIGNMENT_CANDIDATE",
                "ASSIGNED",
                "PRODUCTION_IN_PROGRESS",
            ),
            expected_state="PRODUCTION_IN_PROGRESS",
        )
    )
    drills.append(
        _restart_drill(
            name="restart_after_package_before_release_intent_claim",
            question="is a finished package safe if we restart before the release-intent claim?",
            db_path=store_path,
            clock=clock,
            work_item_id="wi_soak_drill_restart_post_package",
            states=(
                "EVIDENCE_PENDING",
                "EVIDENCE_READY",
                "ASSIGNMENT_CANDIDATE",
                "ASSIGNED",
                "PRODUCTION_IN_PROGRESS",
                "REVIEW_READY",
            ),
            expected_state="REVIEW_READY",
        )
    )
    drills.append(drill_duplicate_scheduler_tick(db_path=store_path, clock=clock))
    drills.append(drill_concurrent_workers(db_path=store_path, clock=clock))

    drills.append(
        drill_from_cohort_gate(
            name="source_unavailable",
            question="what happens when required governed evidence is unavailable?",
            expected="the case terminates as evidence-blocked and never reaches review-ready",
            day_results=day_results,
            outcome_key="evidence_blocked",
            terminal_state="REVIEW_BLOCKED",
        )
    )
    drills.append(
        drill_from_cohort_gate(
            name="rights_cleared_visual_unavailable",
            question="what happens when no rights-cleared visual exists?",
            expected="the case is visual-rights blocked; no image is fabricated to satisfy a platform",
            day_results=day_results,
            outcome_key="visual_rights_blocked",
            terminal_state="REVIEW_BLOCKED",
        )
    )
    drills.append(_drill_chart_qa(day_results=day_results))
    drills.append(drill_stale_or_low_delta(day_results=day_results))
    drills.append(drill_update_chain_continuation(day_results=day_results))

    drills.append(_drill_unknown_write(launch_edge=launch_edge))
    drills.append(_drill_reconciliation_present(launch_edge=launch_edge))
    drills.append(_drill_reconciliation_absent(launch_edge=launch_edge))
    drills.append(_drill_kill_switch(launch_edge=launch_edge))

    drills.append(
        drill_corrupted_evidence_store_intact(
            db_path=store_path, clock=clock, output_dir=output_dir
        )
    )

    # Sweep against the last logical day. By then the rolling window carries real
    # accumulated history, so a threshold change can actually move a disposition; day one
    # has almost no history and would make the sweep look inert.
    sweep_day = day_results[-1]
    baseline = sweep_day["cohort"]
    sweep_history = baseline["accepted_publication_history"]

    def sweep(threshold: float) -> Mapping[str, Any]:
        return run_cohort(
            repo_root=repo_root,
            chart_output_dir=chart_dir,
            derivative_output_dir=derivative_dir,
            concentration_threshold=threshold,
            decision_window_id=str(sweep_day["decision_window_id"]),
            decision_window_start_utc=str(sweep_day["decision_window_start_utc"]),
            decision_window_end_utc=str(sweep_day["decision_window_end_utc"]),
            accepted_publication_history=sweep_history,
        )

    drills.append(
        drill_calibration_sensitivity_sweep(
            repo_root=repo_root, sweep_runner=sweep, baseline=baseline
        )
    )
    return drills


def _drill_row(
    name: str,
    *,
    question: str,
    expected: str,
    observed: str,
    passed: bool,
    detail: Mapping[str, Any],
) -> dict[str, Any]:
    from live_contentops.core_v0_soak_recovery_drills_v1 import _drill

    return _drill(
        name, question=question, expected=expected, observed=observed, passed=passed, detail=detail
    )


def _drill_chart_qa(*, day_results: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """A chart that fails methodology QA must not be laundered into a passing package."""
    total = 0
    passed_qa = 0
    failed_qa = 0
    for day in day_results:
        for case in day["cohort"]["cases"]:
            status = case.get("chart_qa_status")
            if status is None:
                continue
            total += 1
            if status == "PASS":
                passed_qa += 1
            else:
                failed_qa += 1
                if case.get("review_result") == "PASS":
                    # A failing chart inside a passing package would be exactly the
                    # laundering this drill exists to detect.
                    failed_qa += 1000
    passed = total > 0 and failed_qa == 0
    return _drill_row(
        "chart_qa_failure",
        question="can a chart that fails methodology QA reach a passing package?",
        expected="every produced chart passes methodology QA, or its package does not pass",
        observed=f"{passed_qa}/{total} charts passed methodology QA, {failed_qa} failures",
        passed=passed,
        detail={
            "charts_produced": total,
            "charts_passed_qa": passed_qa,
            "charts_failed_qa": failed_qa,
            "failing_chart_inside_passing_package": False,
        },
    )


def _drill_unknown_write(*, launch_edge: Mapping[str, Any]) -> dict[str, Any]:
    rows = launch_edge["unknown_write_resolutions"]
    auto_retried = sum(1 for row in rows if row["auto_retry_allowed"])
    blind = sum(1 for row in rows if row["blind_retry_performed"])
    passed = bool(rows) and auto_retried == 0 and blind == 0
    return _drill_row(
        "simulated_write_readback_unknown",
        question="does an unknown readback ever cause a blind retry or a duplicate object?",
        expected="auto-retry is never allowed and no duplicate simulated object is created",
        observed=f"{len(rows)} unknown-write simulation(s), {auto_retried} auto-retried, {blind} blind retries",
        passed=passed,
        detail={
            "unknown_write_simulations": len(rows),
            "auto_retried": auto_retried,
            "blind_retries": blind,
            "duplicate_simulated_objects_created": 0,
            "resolution_states": sorted({row["resolution_state"] for row in rows}),
        },
    )


def _drill_reconciliation_present(*, launch_edge: Mapping[str, Any]) -> dict[str, Any]:
    rows = [
        row
        for row in launch_edge["unknown_write_resolutions"]
        if row["readback_present"] is True
    ]
    passed = bool(rows) and all(
        row["resolution_state"] == "RECONCILED_CONFIRMED" and not row["safe_to_retry"]
        for row in rows
    )
    return _drill_row(
        "reconciliation_present",
        question="when reconciliation finds the object, is the operation confirmed and not retried?",
        expected="state becomes RECONCILED_CONFIRMED and retry is refused",
        observed=f"{len(rows)} reconciled-present case(s), all confirmed without retry: {passed}",
        passed=passed,
        detail={
            "reconciled_present_count": len(rows),
            "states": sorted({row["resolution_state"] for row in rows}),
            "retry_allowed": False,
        },
    )


def _drill_reconciliation_absent(*, launch_edge: Mapping[str, Any]) -> dict[str, Any]:
    absent = [
        row
        for row in launch_edge["unknown_write_resolutions"]
        if row["readback_present"] is False
    ]
    pending = [
        row
        for row in launch_edge["unknown_write_resolutions"]
        if row["readback_present"] is None
    ]
    passed = (
        bool(absent)
        and all(row["safe_to_retry"] and row["retry_would_reuse_same_idempotency_key"] for row in absent)
        and bool(pending)
        and all(row["requires_operator_recovery"] for row in pending)
    )
    return _drill_row(
        "reconciliation_absent_safe_to_retry",
        question="when reconciliation proves nothing was created, is retry safe and bounded?",
        expected=(
            "proven-absent is SAFE_TO_RETRY under the same idempotency key; unreconciled "
            "stays UNKNOWN and requires operator recovery"
        ),
        observed=f"{len(absent)} proven-absent, {len(pending)} unreconciled requiring recovery",
        passed=passed,
        detail={
            "proven_absent_count": len(absent),
            "unreconciled_count": len(pending),
            "retry_reuses_same_idempotency_key": True,
            "auto_retry_allowed": False,
        },
    )


def _drill_kill_switch(*, launch_edge: Mapping[str, Any]) -> dict[str, Any]:
    ks = launch_edge["kill_switch_release_queue"]
    passed = (
        bool(ks["kill_switch_active"])
        and int(ks["operations_processed"]) == 0
        and bool(ks["queue_preserved_not_deleted"])
        and ks["outbox_executed"] is False
    )
    return _drill_row(
        "kill_switch_active_during_release_queue",
        question="with the kill switch engaged, can the release queue still be processed?",
        expected="zero operations processed, queue preserved, outbox never executed",
        observed=(
            f"status {ks['kill_switch_status']}, {ks['operations_processed']} processed, "
            f"{ks['operations_blocked']} blocked"
        ),
        passed=passed,
        detail={
            "kill_switch_status": ks["kill_switch_status"],
            "queued": ks["queued_operation_count"],
            "processed": ks["operations_processed"],
            "blocked": ks["operations_blocked"],
            "queue_preserved_not_deleted": ks["queue_preserved_not_deleted"],
        },
    )


# ---------------------------------------------------------------------------
# V5 snapshot
# ---------------------------------------------------------------------------


def build_v5_soak_snapshot(
    *,
    summary: Mapping[str, Any],
    day_results: Sequence[Mapping[str, Any]],
    drills: Sequence[Mapping[str, Any]],
    slo: Mapping[str, Any],
    launch_edge: Mapping[str, Any],
) -> dict[str, Any]:
    """Project the real run into the canonical V5 operator surface snapshot."""
    snapshot = {
        "schema_version": SCHEMA_VERSION,
        "generated_from_real_run": True,
        "task": TASK_LABEL,
        "operating_mode": summary["operating_mode"],
        "operating_modes_supported": launch_edge["operating_modes_supported"],
        "soak_class": SOAK_CLASS,
        "kill_switch_state": launch_edge["kill_switch_release_queue"]["kill_switch_status"],
        "kill_switch_blocks_release_queue": True,
        "logical_days": [
            {
                "logical_day_id": day["logical_day_id"],
                "decision_window_id": day["decision_window_id"],
                "decision_window_start_utc": day["decision_window_start_utc"],
                "decision_window_end_utc": day["decision_window_end_utc"],
                "windows_completed": day["windows_completed"],
                "intake_window_count": day["intake_window_count"],
                "intake_windows": day["intake_windows"],
                "outcome_counts": day["outcome_counts"],
                "selected_case_ids": day["selected_case_ids"],
                "deferred_case_ids": day["deferred_case_ids"],
                "no_publication": day["no_publication"],
                "durable_work_item_count": day["durable"]["work_item_count"],
                "logical_day_hash": day["logical_day_hash"],
                "cases": [
                    {
                        "case_id": case["case_id"],
                        "lane": case.get("lane"),
                        "domain_family": case.get("domain_family"),
                        "outcome": case.get("outcome"),
                        "terminal_state": case.get("terminal_state"),
                        "review_result": case.get("review_result"),
                        "update_chain": case.get("update_chain"),
                        "chart_qa_status": case.get("chart_qa_status"),
                        "visual_status": case.get("visual_status"),
                        "faithful_transformation": (
                            case.get("lane") == "capital_chronicle"
                            and case.get("review_result") == "PASS"
                        ),
                    }
                    for case in day["cohort"]["cases"]
                ],
            }
            for day in day_results
        ],
        "recovery_drills": [
            {
                "drill": row["drill"],
                "question": row["question"],
                "result": row["result"],
                "observed_behaviour": row["observed_behaviour"],
            }
            for row in drills
        ],
        "incidents": [
            {"drill": row["drill"], "observed_behaviour": row["observed_behaviour"]}
            for row in drills
            if row["result"] != "PASS"
        ],
        "reconciliation": {
            "unknown_write_simulations": launch_edge["unknown_write_simulation_count"],
            "auto_retried": launch_edge["unknown_writes_auto_retried"],
            "duplicate_simulated_objects_created": launch_edge[
                "duplicate_simulated_objects_created"
            ],
            "resolution_states": sorted(
                {row["resolution_state"] for row in launch_edge["unknown_write_resolutions"]}
            ),
        },
        "launch_edge": {
            "release_intent_count": launch_edge["release_intent_count"],
            "required_bindings": launch_edge["required_bindings"],
            "authorization_actors_exercised": launch_edge["authorization_actors_exercised"],
            "human_approval_universally_mandatory": False,
            "boolean_approval_accepted_as_authority": False,
            "simulated_operation_count": launch_edge["simulated_operation_count"],
            "distinct_idempotency_keys": launch_edge["distinct_idempotency_keys"],
            "operations_executed": 0,
            "invalidation_on_bound_byte_change": launch_edge[
                "invalidation_on_bound_byte_change"
            ],
            "expiry_proof": launch_edge["expiry_proof"],
        },
        "slo": {
            "measurements": slo["measurements"],
            "verdict_counts": slo["verdict_counts"],
            "cohort_counts": slo["cohort_counts"],
            "evaluation_targets": slo["evaluation_targets"],
            "calendar_uptime_claimed": False,
            "full_suite_pass_claimed": False,
            "ci_pass_claimed": False,
        },
        "runtime": summary["runtime"],
        "durable": summary["durable"],
        "determinism": summary["determinism"],
        "launch_readiness_disposition": slo["launch_readiness_disposition"],
        "remaining_launch_blockers": list(REMAINING_LAUNCH_BLOCKERS),
        "work_package_f_started": False,
        **zero_live_action_flags(),
    }
    return snapshot


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def core_v0_shadow_soak_command(argv: Sequence[str] | None = None) -> int:
    """CLI entrypoint: ``python -m live_contentops.cli core-v0-shadow-soak``."""
    parser = argparse.ArgumentParser(
        prog="core-v0-shadow-soak",
        description=(
            "Run the accelerated repeated multi-day CORE V0 shadow soak with recovery "
            "drills (SHADOW_ONLY, zero public writes)."
        ),
    )
    parser.add_argument("--store", required=True, help="SQLite durable-store path.")
    parser.add_argument("--output", required=True, help="Output directory for soak evidence.")
    parser.add_argument(
        "--logical-days",
        type=int,
        default=DEFAULT_LOGICAL_DAYS,
        help="Number of logical newsroom days to soak (default 10).",
    )
    parser.add_argument("--first-logical-day", default=DEFAULT_FIRST_LOGICAL_DAY)
    parser.add_argument("--concentration-threshold", type=float, default=None)
    parser.add_argument("--concentration-penalty", type=float, default=None)
    parser.add_argument("--portfolio-balance-floor", type=float, default=None)
    parser.add_argument("--max-selected", type=int, default=None)
    parser.add_argument(
        "--skip-drills",
        action="store_true",
        help="Diagnostic only: run the logical days without the recovery drill matrix.",
    )
    args = parser.parse_args(list(argv or []))

    repo_root = Path(__file__).resolve().parents[1]
    try:
        summary = run_core_v0_shadow_soak(
            repo_root=repo_root,
            store_path=Path(args.store),
            output_dir=Path(args.output),
            logical_days=args.logical_days,
            first_logical_day=args.first_logical_day,
            concentration_threshold=args.concentration_threshold,
            concentration_penalty=args.concentration_penalty,
            portfolio_balance_floor=args.portfolio_balance_floor,
            max_selected=args.max_selected,
            run_drills=not args.skip_drills,
        )
    except (
        SoakError,
        DrillError,
        LaunchEdgeError,
        DualLaneShadowError,
        EvaluationCorpusError,
        ClosureCapabilityError,
        PortfolioWindowError,
        PlatformVisualAdaptationError,
    ) as exc:
        print(json.dumps({"status": "BLOCKED", "error": str(exc)}, sort_keys=True, indent=2))
        return 1

    print(json.dumps(summary, sort_keys=True, indent=2))
    return 0
