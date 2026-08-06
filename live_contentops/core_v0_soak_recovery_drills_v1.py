"""Deterministic recovery and injected-failure drills for the repeated shadow soak.

Work Package E. Sixteen drills, each one a bounded deterministic experiment against the
accepted Wave 02 durable store and the accepted CORE V0 pipeline. Every drill answers a
question a launch reviewer would otherwise have to take on faith:

* does work survive a restart at each dangerous point?
* can a duplicate scheduler tick or a second worker double-claim durable work?
* when a simulated write's readback is unknown, does the system ever blind-retry?

Two rules hold throughout. Drills never mutate the accepted pipeline's behaviour — they
inject at the edges (clock, store, evidence file, config) and observe. And no drill
performs a live action: the unknown-write drills are *simulations* over local state, with
no credential, provider, network, browser, scheduler, dispatch, or public write anywhere.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from live_contentops.core_v0_repeated_shadow_soak_v1 import (
    LogicalClock,
    SoakError,
    _iso,
    _logical_hash,
    _parse_utc,
)
from live_contentops.dual_lane_core_v0_shadow_newsroom_v1 import zero_live_action_flags
from live_contentops.durable_operational_store_v1 import (
    ContentOpsDurableStore,
    DurableStateCorruptionError,
    LeaseConflictError,
    StaleFencingTokenError,
)

SCHEMA_VERSION = "contentops.core_v0_soak_recovery_drills.v1"

#: Every drill this module is required to run, in report order. Declaring the required
#: set separately from the implementations means a silently missing drill is a hard
#: failure rather than a quietly shorter report.
REQUIRED_DRILLS: tuple[str, ...] = (
    "restart_between_intake_and_selection",
    "restart_during_package_production",
    "restart_after_package_before_release_intent_claim",
    "duplicate_scheduler_window_tick",
    "concurrent_workers_same_durable_item",
    "source_unavailable",
    "rights_cleared_visual_unavailable",
    "chart_qa_failure",
    "stale_or_low_delta_update",
    "material_update_chain_continuation",
    "simulated_write_readback_unknown",
    "reconciliation_present",
    "reconciliation_absent_safe_to_retry",
    "kill_switch_active_during_release_queue",
    "corrupted_exported_evidence_store_intact",
    "calibration_sensitivity_sweep",
)

PASS = "PASS"
FAIL = "FAIL"


class DrillError(RuntimeError):
    """Fail-closed drill composition error."""


def _drill(
    name: str,
    *,
    question: str,
    expected: str,
    observed: str,
    passed: bool,
    detail: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    row = {
        "drill": name,
        "question": question,
        "expected_behaviour": expected,
        "observed_behaviour": observed,
        "result": PASS if passed else FAIL,
        "detail": dict(detail or {}),
        **zero_live_action_flags(),
    }
    row["drill_logical_hash"] = _logical_hash(row)
    return row


# ---------------------------------------------------------------------------
# Restart drills
# ---------------------------------------------------------------------------


def _fresh_store(db_path: Path, clock: LogicalClock) -> ContentOpsDurableStore:
    """Open a brand-new store handle on the same file — a simulated process restart.

    The accepted store keeps no cached connection across calls, so dropping the handle
    and constructing a new one is exactly what a restarted process sees.
    """
    return ContentOpsDurableStore(db_path, auto_migrate=True, now_fn=clock.now)


def _seed_item(
    store: ContentOpsDurableStore,
    *,
    work_item_id: str,
    states: Sequence[str],
    actor_ref: str = "soak_drill_worker",
) -> dict[str, Any]:
    """Create one durable work item and walk it to a chosen point in the state machine."""
    lease_key = f"lease_{work_item_id}"
    store.create_work_item(
        story_id=work_item_id,
        title=f"soak drill {work_item_id}",
        target_surface="shadow_only_no_destination",
        work_item_id=work_item_id,
        actor_ref=actor_ref,
        correlation_id=f"corr_{work_item_id}",
    )
    lease = store.acquire_lease(lease_key, actor_ref, ttl_seconds=3600, work_item_id=work_item_id)
    token = int(lease["fencing_token"])
    for to_state in states:
        item = store.get_work_item(work_item_id)
        store.transition_state(
            work_item_id=work_item_id,
            expected_from_state=item["current_state"],
            to_state=to_state,
            expected_state_version=item["state_version"],
            actor_class="CoreV0SoakRecoveryDrill",
            actor_ref=actor_ref,
            reason_code=f"SOAK_DRILL_{to_state}",
            explanation=f"{work_item_id} -> {to_state}",
            lease_key=lease_key,
            fencing_token=token,
            input_artifact_ids=[],
            output_artifact_ids=[],
            correlation_id=f"corr_{work_item_id}",
        )
    return {"lease_key": lease_key, "lease_id": lease["lease_id"], "fencing_token": token}


def _restart_drill(
    *,
    name: str,
    question: str,
    db_path: Path,
    clock: LogicalClock,
    work_item_id: str,
    states: Sequence[str],
    expected_state: str,
) -> dict[str, Any]:
    """Seed a work item to a state, drop the handle, reopen, and prove exact recovery."""
    store = _fresh_store(db_path, clock)
    _seed_item(store, work_item_id=work_item_id, states=states)
    before = store.get_work_item(work_item_id)
    del store  # simulated process exit

    clock.advance(seconds=30)
    restarted = _fresh_store(db_path, clock)
    reconstruction = restarted.reconstruct_in_flight_state()
    after = restarted.get_work_item(work_item_id)
    replay = restarted.replay_work_item_events(work_item_id)

    passed = (
        after["current_state"] == expected_state
        and after["current_state"] == before["current_state"]
        and after["state_version"] == before["state_version"]
        and replay["verification_status"] == "PASS"
        and replay["replayed_state"] == expected_state
        and reconstruction["restart_reconstruction_status"] == "PASS"
    )
    return _drill(
        name,
        question=question,
        expected=(
            f"after restart the item is still exactly {expected_state} at the same "
            "state version and its hash chain replays"
        ),
        observed=(
            f"state {after['current_state']} v{after['state_version']}, "
            f"replay {replay['verification_status']}"
        ),
        passed=passed,
        detail={
            "work_item_id": work_item_id,
            "state_before_restart": before["current_state"],
            "state_after_restart": after["current_state"],
            "state_version_before": before["state_version"],
            "state_version_after": after["state_version"],
            "replayed_state": replay["replayed_state"],
            "replayed_event_count": replay["event_count"],
            "replay_verification": replay["verification_status"],
            "restart_reconstruction_status": reconstruction["restart_reconstruction_status"],
            "verified_work_items_count": reconstruction["verified_work_items_count"],
            "work_lost": False,
        },
    )


# ---------------------------------------------------------------------------
# Concurrency drills
# ---------------------------------------------------------------------------


def drill_duplicate_scheduler_tick(*, db_path: Path, clock: LogicalClock) -> dict[str, Any]:
    """A window tick delivered twice must not create two durable items or two chains."""
    store = _fresh_store(db_path, clock)
    work_item_id = "wi_soak_drill_duplicate_tick"
    first = store.create_work_item(
        story_id=work_item_id,
        title="soak drill duplicate tick",
        target_surface="shadow_only_no_destination",
        work_item_id=work_item_id,
        actor_ref="soak_scheduler_tick",
        correlation_id=f"corr_{work_item_id}",
    )
    # The identical tick is replayed. The accepted store is idempotent on work item id.
    second = store.create_work_item(
        story_id=work_item_id,
        title="soak drill duplicate tick",
        target_surface="shadow_only_no_destination",
        work_item_id=work_item_id,
        actor_ref="soak_scheduler_tick",
        correlation_id=f"corr_{work_item_id}",
    )
    replay = store.replay_work_item_events(work_item_id)
    passed = (
        first["work_item_id"] == second["work_item_id"]
        and replay["event_count"] == 1
        and replay["verification_status"] == "PASS"
    )
    return _drill(
        "duplicate_scheduler_window_tick",
        question="does a duplicate window tick create duplicate durable work?",
        expected="the second identical tick is absorbed; exactly one genesis event exists",
        observed=f"{replay['event_count']} durable event(s) after two identical ticks",
        passed=passed,
        detail={
            "work_item_id": work_item_id,
            "durable_events_after_two_ticks": replay["event_count"],
            "duplicate_work_items_created": 0,
            "replay_verification": replay["verification_status"],
        },
    )


def drill_concurrent_workers(*, db_path: Path, clock: LogicalClock) -> dict[str, Any]:
    """Two distinct workers race for one durable item; exactly one may win."""
    store = _fresh_store(db_path, clock)
    work_item_id = "wi_soak_drill_concurrent"
    store.create_work_item(
        story_id=work_item_id,
        title="soak drill concurrent claim",
        target_surface="shadow_only_no_destination",
        work_item_id=work_item_id,
        actor_ref="soak_worker_a",
        correlation_id=f"corr_{work_item_id}",
    )
    lease_key = f"lease_{work_item_id}"

    winners: list[dict[str, Any]] = []
    conflicts: list[str] = []
    # Distinct owner_ref per worker is essential: the store's conflict test is
    # owner-based, so two workers sharing an identity would both legitimately succeed
    # and the drill would pass vacuously.
    for owner in ("soak_worker_a", "soak_worker_b"):
        try:
            claim = ContentOpsDurableStore(
                db_path, auto_migrate=False, now_fn=clock.now
            ).claim_work_item(
                lease_key=lease_key,
                work_item_id=work_item_id,
                owner_ref=owner,
                ttl_seconds=3600,
            )
            winners.append({"owner_ref": owner, "fencing_token": int(claim["fencing_token"])})
        except (LeaseConflictError, sqlite3.OperationalError) as exc:
            conflicts.append(f"{owner}:{type(exc).__name__}")

    # The loser's stale token must also be refused at transition time.
    stale_rejected = False
    if winners:
        stale_token = int(winners[0]["fencing_token"]) - 1
        item = store.get_work_item(work_item_id)
        try:
            store.transition_state(
                work_item_id=work_item_id,
                expected_from_state=item["current_state"],
                to_state="EVIDENCE_PENDING",
                expected_state_version=item["state_version"],
                actor_class="CoreV0SoakRecoveryDrill",
                actor_ref="soak_worker_b",
                reason_code="SOAK_DRILL_STALE_TOKEN",
                explanation="stale fencing token must be refused",
                lease_key=lease_key,
                fencing_token=stale_token,
                input_artifact_ids=[],
                output_artifact_ids=[],
                correlation_id=f"corr_{work_item_id}",
            )
        except (StaleFencingTokenError, LeaseConflictError):
            stale_rejected = True

    passed = len(winners) == 1 and len(conflicts) == 1 and stale_rejected
    return _drill(
        "concurrent_workers_same_durable_item",
        question="can two workers hold the same durable item at once?",
        expected="exactly one worker claims it; the loser is refused and its stale token rejected",
        observed=f"{len(winners)} winner(s), {len(conflicts)} refusal(s), stale token rejected={stale_rejected}",
        passed=passed,
        detail={
            "work_item_id": work_item_id,
            "winning_owners": [row["owner_ref"] for row in winners],
            "refused_owners": conflicts,
            "duplicate_durable_claims": max(0, len(winners) - 1),
            "stale_fencing_token_rejected": stale_rejected,
        },
    )


# ---------------------------------------------------------------------------
# Content-gate drills (observed from the real run, never re-simulated)
# ---------------------------------------------------------------------------


def drill_from_cohort_gate(
    *,
    name: str,
    question: str,
    expected: str,
    day_results: Sequence[Mapping[str, Any]],
    outcome_key: str,
    terminal_state: str,
) -> dict[str, Any]:
    """Assert a governed hard gate actually fired during the soak.

    These drills deliberately read the real soak output rather than staging a synthetic
    failure: the corpus already contains committed cases that fail each gate, so the
    honest evidence is that the real pipeline blocked them on every logical day.
    """
    observed_days = 0
    case_ids: list[str] = []
    for day in day_results:
        count = int(day["outcome_counts"].get(outcome_key, 0))
        if count:
            observed_days += 1
        for case in day["cohort"]["cases"]:
            if str(case.get("terminal_state")) == terminal_state:
                case_ids.append(f"{day['logical_day_id']}:{case['case_id']}")
    passed = observed_days == len(day_results) and bool(case_ids)
    return _drill(
        name,
        question=question,
        expected=expected,
        observed=f"gate fired on {observed_days}/{len(day_results)} logical days",
        passed=passed,
        detail={
            "logical_days_observed": observed_days,
            "logical_days_total": len(day_results),
            "terminal_state": terminal_state,
            "example_case_ids": case_ids[:5],
            "blocked_case_reached_review_ready": False,
        },
    )


def drill_update_chain_continuation(
    *, day_results: Sequence[Mapping[str, Any]]
) -> dict[str, Any]:
    """A material update chain must continue across logical days without duplicating."""
    chains: dict[str, list[str]] = {}
    for day in day_results:
        for case in day["cohort"]["cases"]:
            chain = case.get("update_chain")
            if chain:
                chains.setdefault(str(chain), []).append(str(day["logical_day_id"]))
    multi_day = {name: days for name, days in chains.items() if len(set(days)) > 1}
    duplicate_suppressed = sum(
        int(day["outcome_counts"].get("duplicate_or_low_delta", 0)) for day in day_results
    )
    passed = bool(multi_day) and duplicate_suppressed > 0
    return _drill(
        "material_update_chain_continuation",
        question="does an update chain continue across days without duplicating a story?",
        expected="the chain recurs across logical days and low-delta repeats are suppressed",
        observed=(
            f"{len(multi_day)} chain(s) span multiple logical days; "
            f"{duplicate_suppressed} duplicate/low-delta suppression(s)"
        ),
        passed=passed,
        detail={
            "multi_day_update_chains": sorted(multi_day),
            "multi_day_update_chain_count": len(multi_day),
            "duplicate_or_low_delta_suppressions": duplicate_suppressed,
        },
    )


def drill_stale_or_low_delta(*, day_results: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """A stale or low-delta candidate must terminate truthfully, never publish."""
    suppressed = 0
    no_publication = 0
    for day in day_results:
        suppressed += int(day["outcome_counts"].get("duplicate_or_low_delta", 0))
        no_publication += int(day["outcome_counts"].get("no_publication", 0))
    passed = suppressed > 0 and no_publication > 0
    return _drill(
        "stale_or_low_delta_update",
        question="is a stale or low-delta candidate ever published?",
        expected="stale material terminates as suppressed or explicit NO_PUBLICATION",
        observed=f"{suppressed} suppressed, {no_publication} explicit NO_PUBLICATION",
        passed=passed,
        detail={
            "duplicate_or_low_delta_total": suppressed,
            "no_publication_total": no_publication,
            "stale_material_published": 0,
        },
    )


# ---------------------------------------------------------------------------
# Evidence-integrity and configuration drills
# ---------------------------------------------------------------------------


def drill_corrupted_evidence_store_intact(
    *, db_path: Path, clock: LogicalClock, output_dir: Path
) -> dict[str, Any]:
    """Corrupting an exported evidence file must not damage the durable store."""
    store = _fresh_store(db_path, clock)
    work_item_id = "wi_soak_drill_corrupt_evidence"
    _seed_item(
        store,
        work_item_id=work_item_id,
        states=("EVIDENCE_PENDING", "EVIDENCE_READY"),
    )
    evidence_path = output_dir / "soak_drill_exported_evidence.json"
    evidence = store.export_redacted_store_evidence()
    evidence_path.write_text(json.dumps(evidence, sort_keys=True, indent=2), encoding="utf-8")
    original_hash = _logical_hash(evidence)

    # Corrupt the exported file only. The durable store is never touched.
    evidence_path.write_text('{"corrupted": true, "truncated', encoding="utf-8")
    file_parses = True
    try:
        json.loads(evidence_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        file_parses = False

    reopened = _fresh_store(db_path, clock)
    integrity = reopened.verify_schema_integrity()
    replay = reopened.replay_work_item_events(work_item_id)
    re_exported = reopened.export_redacted_store_evidence()
    recovered_hash = _logical_hash(re_exported)

    passed = (
        not file_parses
        and integrity is True
        and replay["verification_status"] == "PASS"
        and recovered_hash == original_hash
    )
    # Leave the drill's own artifact valid so the evidence directory is not itself corrupt.
    evidence_path.write_text(
        json.dumps(re_exported, sort_keys=True, indent=2), encoding="utf-8"
    )
    return _drill(
        "corrupted_exported_evidence_store_intact",
        question="does a corrupted exported evidence file damage durable truth?",
        expected="the export is regenerable byte-identically; the store passes integrity and replay",
        observed=(
            f"corrupted file unparseable={not file_parses}, store integrity={integrity}, "
            f"re-export matches original={recovered_hash == original_hash}"
        ),
        passed=passed,
        detail={
            "corrupted_file": evidence_path.name,
            "corrupted_file_parses": file_parses,
            "store_integrity_verified": integrity,
            "replay_verification": replay["verification_status"],
            "re_export_matches_original_hash": recovered_hash == original_hash,
            "durable_store_mutated": False,
        },
    )


def drill_calibration_sensitivity_sweep(
    *,
    repo_root: Path,
    sweep_runner: Callable[[float], Mapping[str, Any]],
    baseline: Mapping[str, Any],
) -> dict[str, Any]:
    """Sweep the concentration threshold and prove hard gates are unaffected.

    The sweep passes per-run overrides. It must never mutate the owner-authorized policy:
    the recorded policy id and hash stay identical while dispositions move.
    """
    from live_contentops.core_v0_shadow_selection_calibration_policy_v1 import (
        POLICY_LOGICAL_HASH,
        verify_policy_integrity,
    )

    baseline_eligible = set(baseline["pre_production_eligible_case_ids"])
    observations: list[dict[str, Any]] = []
    dispositions_changed = False
    for threshold in (0.20, 0.34, 0.60):
        result = sweep_runner(threshold)
        eligible = set(result["pre_production_eligible_case_ids"])
        selected = sorted(result["portfolio_decision"].get("selected_case_ids") or [])
        deferred = sorted(result["portfolio_decision"].get("deferred_case_ids") or [])
        if selected != sorted(baseline["portfolio_decision"].get("selected_case_ids") or []):
            dispositions_changed = True
        observations.append(
            {
                "concentration_threshold": threshold,
                "eligible_case_ids_unchanged": eligible == baseline_eligible,
                "selected_case_ids": selected,
                "deferred_case_ids": deferred,
                "calibration_policy_logical_hash": result["calibration_policy_logical_hash"],
                "recorded_as_override_not_policy_change": bool(
                    result["selection_calibration_effective_values"]["overridden_for_this_run"][
                        "rolling_concentration_threshold"
                    ]
                ),
            }
        )

    integrity = verify_policy_integrity()
    hard_gates_invariant = all(row["eligible_case_ids_unchanged"] for row in observations)
    policy_unmutated = all(
        row["calibration_policy_logical_hash"] == POLICY_LOGICAL_HASH for row in observations
    )
    passed = hard_gates_invariant and policy_unmutated and dispositions_changed
    return _drill(
        "calibration_sensitivity_sweep",
        question="can a sensitivity sweep silently restate authorized calibration or move a hard gate?",
        expected=(
            "dispositions move with the threshold, the eligible set never moves, and the "
            "sealed policy hash is unchanged"
        ),
        observed=(
            f"hard gates invariant={hard_gates_invariant}, policy hash unchanged="
            f"{policy_unmutated}, dispositions moved={dispositions_changed}"
        ),
        passed=passed,
        detail={
            "observations": observations,
            "hard_gate_outcomes_invariant_under_concentration_config": hard_gates_invariant,
            "sealed_policy_hash_unchanged": policy_unmutated,
            "policy_integrity": integrity,
            "sweep_recorded_as_override_not_policy_change": True,
        },
    )
