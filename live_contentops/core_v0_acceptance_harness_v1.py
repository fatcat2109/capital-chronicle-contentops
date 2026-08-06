"""Canonical local acceptance harness for CORE V0 shadow and live-cohort evidence.

Work Package E, scope item H. One command validates an accepted evidence directory:

.. code-block:: text

   python -m live_contentops.cli core-v0-acceptance --evidence <dir> --store <sqlite>

This exists so Work Package G has a single deterministic oracle it can point at accepted
shadow evidence today and at live-cohort evidence later, instead of running the noisy
monolithic historical repository suite as a launch gate.

Every check returns ``PASS``, ``FAIL``, or ``NOT_APPLICABLE`` with the exact reason. A
check that cannot be evaluated against the supplied evidence is reported as
``NOT_APPLICABLE`` rather than silently skipped or counted as a pass.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Mapping, Sequence

SCHEMA_VERSION = "contentops.core_v0_acceptance_harness.v1"
TASK_LABEL = "TASK_CONTENTOPS_CORE_V0_REPEATED_SHADOW_SOAK_AND_RECOVERY_V1"

PASS = "PASS"
FAIL = "FAIL"
NOT_APPLICABLE = "NOT_APPLICABLE"

#: The gates Work Package G must be able to re-verify. Named here so a missing gate is a
#: visible NOT_APPLICABLE rather than a shorter, flattering report.
REQUIRED_GATES: tuple[str, ...] = (
    "one_canonical_execution_path",
    "durable_replay",
    "authority_and_policy_bindings",
    "package_lineage",
    "no_secret_posture",
    "release_authorization_integrity",
    "idempotency",
    "unknown_write_and_reconciliation",
    "mode_and_kill_switch_behaviour",
    "v5_snapshot_consistency",
    "accepted_evidence_packet_completeness",
)

#: Files an accepted soak evidence directory must contain.
REQUIRED_EVIDENCE_FILES: tuple[str, ...] = (
    "soak_run_summary.json",
    "soak_logical_days.json",
    "soak_recovery_drills.json",
    "soak_slo_report.json",
    "soak_launch_edge.json",
    "v5_soak_snapshot.json",
    "soak_report.md",
)

_LIVE_FLAGS: tuple[str, ...] = (
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
)

_SECRET_RE = re.compile(
    r"(?i)(bearer\s+[A-Za-z0-9._\-]{20,}|eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"
    r"|\b\d{6,12}:[A-Za-z0-9_-]{30,}\b|(?:api[_-]?key|password|secret|access[_-]?token)"
    r"\"?\s*[:=]\s*\"[^\"]{12,})"
)


class AcceptanceError(RuntimeError):
    """Fail-closed acceptance harness error."""


def _gate(name: str, *, status: str, reason: str, detail: Mapping[str, Any] | None = None) -> dict[str, Any]:
    if status not in (PASS, FAIL, NOT_APPLICABLE):
        raise AcceptanceError(f"unknown_gate_status:{status}")
    return {"gate": name, "status": status, "reason": reason, "detail": dict(detail or {})}


def _walk_live_flags(node: Any, offenders: list[str], path: str = "") -> None:
    if isinstance(node, Mapping):
        for key, value in node.items():
            if key in _LIVE_FLAGS and value is not False:
                offenders.append(f"{path}.{key}={value!r}")
            _walk_live_flags(value, offenders, f"{path}.{key}")
    elif isinstance(node, (list, tuple)):
        for index, child in enumerate(node):
            _walk_live_flags(child, offenders, f"{path}[{index}]")


def run_acceptance(
    *,
    evidence_dir: Path,
    store_path: Path | None = None,
) -> dict[str, Any]:
    """Validate one accepted evidence directory against every required gate."""
    evidence_dir = Path(evidence_dir)
    if not evidence_dir.is_dir():
        raise AcceptanceError(f"evidence_dir_not_found:{evidence_dir}")

    present = {name for name in REQUIRED_EVIDENCE_FILES if (evidence_dir / name).is_file()}
    missing = [name for name in REQUIRED_EVIDENCE_FILES if name not in present]

    def load(name: str) -> Mapping[str, Any] | None:
        if name not in present:
            return None
        return json.loads((evidence_dir / name).read_text(encoding="utf-8"))

    summary = load("soak_run_summary.json")
    days = load("soak_logical_days.json")
    drills = load("soak_recovery_drills.json")
    slo = load("soak_slo_report.json")
    edge = load("soak_launch_edge.json")
    v5 = load("v5_soak_snapshot.json")

    gates: list[dict[str, Any]] = []

    # --- accepted evidence packet completeness ---------------------------------------
    gates.append(
        _gate(
            "accepted_evidence_packet_completeness",
            status=PASS if not missing else FAIL,
            reason=(
                "every required evidence file is present"
                if not missing
                else f"missing evidence files: {', '.join(missing)}"
            ),
            detail={"present": sorted(present), "missing": missing},
        )
    )

    # --- one canonical execution path -------------------------------------------------
    if summary is None:
        gates.append(
            _gate(
                "one_canonical_execution_path",
                status=NOT_APPLICABLE,
                reason="no run summary supplied",
            )
        )
    else:
        second_runner = bool(summary.get("second_production_runner_created"))
        reuses = summary.get("reuses_accepted_pipeline") or {}
        ok = not second_runner and bool(reuses.get("cohort_runner")) and bool(
            reuses.get("durable_store")
        )
        gates.append(
            _gate(
                "one_canonical_execution_path",
                status=PASS if ok else FAIL,
                reason=(
                    "the run reuses the accepted cohort runner, review engine, package "
                    "fabric, and durable store; no second production runner exists"
                    if ok
                    else "the evidence does not prove a single canonical execution path"
                ),
                detail={
                    "second_production_runner_created": second_runner,
                    "reuses_accepted_pipeline": reuses,
                    "canonical_command": summary.get("canonical_command"),
                },
            )
        )

    # --- durable replay ---------------------------------------------------------------
    gates.append(_durable_gate(summary=summary, store_path=store_path))

    # --- authority and policy bindings ------------------------------------------------
    if summary is None:
        gates.append(
            _gate(
                "authority_and_policy_bindings",
                status=NOT_APPLICABLE,
                reason="no run summary supplied",
            )
        )
    else:
        from live_contentops.core_v0_shadow_selection_calibration_policy_v1 import (
            POLICY_LOGICAL_HASH,
            verify_policy_integrity,
        )

        integrity = verify_policy_integrity()
        bound = str(summary.get("selection_calibration_policy_logical_hash") or "")
        live_ok = summary.get("calibration_policy_authorized_for_live_publication") is False
        ok = bound == POLICY_LOGICAL_HASH and live_ok
        gates.append(
            _gate(
                "authority_and_policy_bindings",
                status=PASS if ok else FAIL,
                reason=(
                    "the recorded calibration policy hash matches the sealed policy and is "
                    "not authorized for live publication"
                    if ok
                    else "calibration policy binding does not match the sealed policy"
                ),
                detail={
                    "recorded_policy_logical_hash": bound,
                    "sealed_policy_logical_hash": POLICY_LOGICAL_HASH,
                    "policy_integrity_status": integrity.get("status", "VERIFIED"),
                    "authorized_for_live_publication": not live_ok,
                },
            )
        )

    # --- package lineage --------------------------------------------------------------
    gates.append(_lineage_gate(slo=slo, days=days))

    # --- no-secret posture ------------------------------------------------------------
    offenders: list[str] = []
    secret_hits: list[str] = []
    for path in sorted(evidence_dir.glob("*.json")):
        text = path.read_text(encoding="utf-8")
        if _SECRET_RE.search(text):
            secret_hits.append(path.name)
        _walk_live_flags(json.loads(text), offenders, path.name)
    gates.append(
        _gate(
            "no_secret_posture",
            status=PASS if not secret_hits and not offenders else FAIL,
            reason=(
                "no secret-shaped material and no live-authority flag set true in any artifact"
                if not secret_hits and not offenders
                else f"secrets in {secret_hits}; live flags set: {offenders[:5]}"
            ),
            detail={
                "files_scanned": len(list(evidence_dir.glob("*.json"))),
                "files_with_secret_shaped_material": secret_hits,
                "live_authority_flags_set_true": offenders[:20],
            },
        )
    )

    # --- release authorization integrity ----------------------------------------------
    gates.append(_release_gate(edge=edge))

    # --- idempotency ------------------------------------------------------------------
    if edge is None:
        gates.append(
            _gate("idempotency", status=NOT_APPLICABLE, reason="no launch-edge evidence supplied")
        )
    else:
        ops = int(edge.get("simulated_operation_count") or 0)
        keys = int(edge.get("distinct_idempotency_keys") or 0)
        ok = ops > 0 and keys == ops
        gates.append(
            _gate(
                "idempotency",
                status=PASS if ok else FAIL,
                reason=(
                    f"all {ops} operations carry distinct idempotency keys"
                    if ok
                    else f"{ops} operations but {keys} distinct keys"
                ),
                detail={
                    "simulated_operation_count": ops,
                    "distinct_idempotency_keys": keys,
                    "duplicate_suppressed_operations": edge.get(
                        "duplicate_suppressed_operations"
                    ),
                },
            )
        )

    # --- unknown write and reconciliation ---------------------------------------------
    gates.append(_reconciliation_gate(edge=edge))

    # --- mode and kill switch ---------------------------------------------------------
    gates.append(_mode_gate(edge=edge, summary=summary))

    # --- V5 snapshot consistency ------------------------------------------------------
    gates.append(_v5_gate(v5=v5, summary=summary, slo=slo, drills=drills))

    missing_gates = sorted(set(REQUIRED_GATES) - {row["gate"] for row in gates})
    for name in missing_gates:
        gates.append(
            _gate(name, status=NOT_APPLICABLE, reason="gate not evaluated against this evidence")
        )

    failed = [row["gate"] for row in gates if row["status"] == FAIL]
    not_applicable = [row["gate"] for row in gates if row["status"] == NOT_APPLICABLE]
    result = {
        "schema_version": SCHEMA_VERSION,
        "task": TASK_LABEL,
        "evidence_dir": str(evidence_dir),
        "store_path": str(store_path) if store_path else None,
        "required_gates": list(REQUIRED_GATES),
        "gates": gates,
        "gate_count": len(gates),
        "passed_count": sum(1 for row in gates if row["status"] == PASS),
        "failed_gates": failed,
        "not_applicable_gates": not_applicable,
        "acceptance_status": PASS if not failed else FAIL,
        "runs_noisy_historical_full_suite_as_launch_oracle": False,
        "full_suite_pass_claimed": False,
        "ci_pass_claimed": False,
    }
    return result


def _durable_gate(*, summary: Mapping[str, Any] | None, store_path: Path | None) -> dict[str, Any]:
    if store_path is None:
        if summary is None:
            return _gate(
                "durable_replay", status=NOT_APPLICABLE, reason="no store and no summary supplied"
            )
        durable = summary.get("durable") or {}
        ok = (
            durable.get("restart_reconstruction_status") == "PASS"
            and int(durable.get("lost_work_items", 1)) == 0
            and int(durable.get("duplicate_durable_claims", 1)) == 0
        )
        return _gate(
            "durable_replay",
            status=PASS if ok else FAIL,
            reason=(
                "the recorded run reconstructed after restart with no lost or double-claimed work"
                if ok
                else "recorded durable evidence does not prove clean reconstruction"
            ),
            detail={
                "verified_from": "run_summary_only_no_store_supplied",
                **{
                    key: durable.get(key)
                    for key in (
                        "work_item_count",
                        "lost_work_items",
                        "duplicate_durable_claims",
                        "restart_reconstruction_status",
                    )
                },
            },
        )

    from live_contentops.durable_operational_store_v1 import (
        ContentOpsDurableStore,
        DurableStoreError,
    )

    try:
        store = ContentOpsDurableStore(Path(store_path), auto_migrate=True)
        integrity = store.verify_schema_integrity()
        migrations = store.verify_applied_migrations()
        reconstruction = store.reconstruct_in_flight_state()
        evidence = store.export_redacted_store_evidence()
    except (DurableStoreError, OSError) as exc:
        return _gate(
            "durable_replay",
            status=FAIL,
            reason=f"durable store could not be reopened and replayed: {exc}",
            detail={"store_path": str(store_path)},
        )

    ok = (
        integrity is True
        and migrations is True
        and reconstruction["restart_reconstruction_status"] == "PASS"
    )
    return _gate(
        "durable_replay",
        status=PASS if ok else FAIL,
        reason=(
            "the store reopened independently, passed integrity and migration checks, and "
            "every work item replayed from its hash chain"
            if ok
            else "the store did not replay cleanly on reopen"
        ),
        detail={
            "verified_from": "independent_store_reopen",
            "schema_version": store.get_current_schema_version(),
            "integrity_verified": integrity,
            "migrations_verified": migrations,
            "restart_reconstruction_status": reconstruction["restart_reconstruction_status"],
            "verified_work_items_count": reconstruction["verified_work_items_count"],
            "counts": evidence.get("counts"),
            "redaction_guarantee": evidence.get("redaction_guarantee"),
        },
    )


def _lineage_gate(
    *, slo: Mapping[str, Any] | None, days: Mapping[str, Any] | None
) -> dict[str, Any]:
    if slo is None:
        return _gate("package_lineage", status=NOT_APPLICABLE, reason="no SLO report supplied")
    row = next(
        (
            item
            for item in slo.get("measurements") or []
            if item["measurement"] == "package_lineage_completeness"
        ),
        None,
    )
    if row is None:
        return _gate(
            "package_lineage", status=NOT_APPLICABLE, reason="lineage measurement not present"
        )
    blocked_reaching_review_ready = 0
    if days is not None:
        for day in days.get("logical_days") or []:
            for case in day.get("cases") or []:
                if case.get("review_result") != "PASS" and case.get("terminal_state") == "REVIEW_READY":
                    blocked_reaching_review_ready += 1
    ok = row["verdict"] in (PASS,) and blocked_reaching_review_ready == 0
    return _gate(
        "package_lineage",
        status=PASS if ok else FAIL,
        reason=(
            "every complete package carries article, SEO, and explicit per-destination "
            "outcomes, and no blocked case reached review-ready"
            if ok
            else f"lineage verdict {row['verdict']}; "
            f"{blocked_reaching_review_ready} blocked case(s) reached review-ready"
        ),
        detail={
            "lineage_numerator": row["numerator"],
            "lineage_denominator": row["denominator"],
            "lineage_verdict": row["verdict"],
            "blocked_cases_reaching_review_ready": blocked_reaching_review_ready,
        },
    )


def _release_gate(*, edge: Mapping[str, Any] | None) -> dict[str, Any]:
    if edge is None:
        return _gate(
            "release_authorization_integrity",
            status=NOT_APPLICABLE,
            reason="no launch-edge evidence supplied",
        )
    from live_contentops.core_v0_launch_edge_dry_model_v1 import REQUIRED_RELEASE_BINDINGS

    bindings = list(edge.get("required_bindings") or [])
    invalidation = edge.get("invalidation_on_bound_byte_change") or {}
    expiry = edge.get("expiry_proof") or {}
    ok = (
        set(bindings) == set(REQUIRED_RELEASE_BINDINGS)
        and edge.get("boolean_approval_accepted_as_authority") is False
        and edge.get("payload_rebuilt_after_authorization") is False
        and invalidation.get("still_valid_after_byte_change") is False
        and expiry.get("expired") is True
        and int(edge.get("release_intent_count") or 0) > 0
    )
    return _gate(
        "release_authorization_integrity",
        status=PASS if ok else FAIL,
        reason=(
            "release authorization binds all eight required hashes, refuses boolean "
            "authority, never rebuilds a payload after authorization, and is invalidated "
            "both by a bound-byte change and by expiry"
            if ok
            else "release authorization integrity is not fully proven by this evidence"
        ),
        detail={
            "release_intent_count": edge.get("release_intent_count"),
            "required_bindings": bindings,
            "bindings_complete": set(bindings) == set(REQUIRED_RELEASE_BINDINGS),
            "boolean_approval_accepted_as_authority": edge.get(
                "boolean_approval_accepted_as_authority"
            ),
            "payload_rebuilt_after_authorization": edge.get(
                "payload_rebuilt_after_authorization"
            ),
            "invalidated_by_bound_byte_change": invalidation.get(
                "still_valid_after_byte_change"
            )
            is False,
            "expiry_enforced": expiry.get("expired"),
        },
    )


def _reconciliation_gate(*, edge: Mapping[str, Any] | None) -> dict[str, Any]:
    if edge is None:
        return _gate(
            "unknown_write_and_reconciliation",
            status=NOT_APPLICABLE,
            reason="no launch-edge evidence supplied",
        )
    rows = edge.get("unknown_write_resolutions") or []
    auto_retried = int(edge.get("unknown_writes_auto_retried") or 0)
    duplicates = int(edge.get("duplicate_simulated_objects_created") or 0)
    states = {str(row.get("resolution_state")) for row in rows}
    ok = bool(rows) and auto_retried == 0 and duplicates == 0 and len(states) >= 3
    return _gate(
        "unknown_write_and_reconciliation",
        status=PASS if ok else FAIL,
        reason=(
            "every unknown write is classified deterministically, all three reconciliation "
            "outcomes are exercised, and no blind retry or duplicate object occurred"
            if ok
            else "unknown-write handling is not fully proven by this evidence"
        ),
        detail={
            "unknown_write_simulations": len(rows),
            "resolution_states": sorted(states),
            "auto_retried": auto_retried,
            "duplicate_simulated_objects_created": duplicates,
        },
    )


def _mode_gate(
    *, edge: Mapping[str, Any] | None, summary: Mapping[str, Any] | None
) -> dict[str, Any]:
    if edge is None:
        return _gate(
            "mode_and_kill_switch_behaviour",
            status=NOT_APPLICABLE,
            reason="no launch-edge evidence supplied",
        )
    from live_contentops.core_v0_launch_edge_dry_model_v1 import OPERATING_MODES

    modes = list(edge.get("operating_modes_supported") or [])
    kill = edge.get("kill_switch_release_queue") or {}
    ok = (
        set(modes) == set(OPERATING_MODES)
        and edge.get("human_approval_universally_mandatory") is False
        and int(kill.get("operations_processed", 1)) == 0
        and bool(kill.get("queue_preserved_not_deleted"))
        and kill.get("outbox_executed") is False
    )
    if summary is not None:
        ok = ok and summary.get("operating_mode") == "SHADOW_ONLY"
    return _gate(
        "mode_and_kill_switch_behaviour",
        status=PASS if ok else FAIL,
        reason=(
            "all four operating modes are declared, human approval is not universally "
            "mandatory, and an engaged kill switch blocks the queue without deleting it"
            if ok
            else "mode or kill-switch behaviour is not fully proven by this evidence"
        ),
        detail={
            "operating_modes_supported": modes,
            "operating_mode": (summary or {}).get("operating_mode"),
            "human_approval_universally_mandatory": edge.get(
                "human_approval_universally_mandatory"
            ),
            "kill_switch_status": kill.get("kill_switch_status"),
            "operations_processed_under_kill_switch": kill.get("operations_processed"),
            "queue_preserved_not_deleted": kill.get("queue_preserved_not_deleted"),
        },
    )


def _v5_gate(
    *,
    v5: Mapping[str, Any] | None,
    summary: Mapping[str, Any] | None,
    slo: Mapping[str, Any] | None,
    drills: Mapping[str, Any] | None,
) -> dict[str, Any]:
    if v5 is None:
        return _gate(
            "v5_snapshot_consistency", status=NOT_APPLICABLE, reason="no V5 snapshot supplied"
        )
    problems: list[str] = []
    if not v5.get("generated_from_real_run"):
        problems.append("snapshot not marked as generated from a real run")
    if summary is not None and v5.get("launch_readiness_disposition") != summary.get(
        "launch_readiness_disposition"
    ):
        problems.append("snapshot disposition disagrees with the run summary")
    if slo is not None and len(v5.get("slo", {}).get("measurements") or []) != len(
        slo.get("measurements") or []
    ):
        problems.append("snapshot SLO measurement count disagrees with the SLO report")
    if drills is not None and len(v5.get("recovery_drills") or []) != len(
        drills.get("drills") or []
    ):
        problems.append("snapshot drill count disagrees with the drill report")
    if summary is not None and len(v5.get("logical_days") or []) != int(
        summary.get("logical_days") or -1
    ):
        problems.append("snapshot logical-day count disagrees with the run summary")
    return _gate(
        "v5_snapshot_consistency",
        status=PASS if not problems else FAIL,
        reason=(
            "the operator snapshot was generated from the real run and agrees with the "
            "run summary, SLO report, and drill report"
            if not problems
            else "; ".join(problems)
        ),
        detail={
            "generated_from_real_run": v5.get("generated_from_real_run"),
            "logical_days": len(v5.get("logical_days") or []),
            "recovery_drills": len(v5.get("recovery_drills") or []),
            "slo_measurements": len(v5.get("slo", {}).get("measurements") or []),
            "problems": problems,
        },
    )


def core_v0_acceptance_command(argv: Sequence[str] | None = None) -> int:
    """CLI entrypoint: ``python -m live_contentops.cli core-v0-acceptance``."""
    parser = argparse.ArgumentParser(
        prog="core-v0-acceptance",
        description=(
            "Validate an accepted CORE V0 shadow or live-cohort evidence directory against "
            "every required launch gate."
        ),
    )
    parser.add_argument("--evidence", required=True, help="Evidence directory to validate.")
    parser.add_argument(
        "--store",
        default=None,
        help="Optional durable store to reopen and replay independently.",
    )
    args = parser.parse_args(list(argv or []))

    try:
        result = run_acceptance(
            evidence_dir=Path(args.evidence),
            store_path=Path(args.store) if args.store else None,
        )
    except AcceptanceError as exc:
        print(json.dumps({"status": "BLOCKED", "error": str(exc)}, sort_keys=True, indent=2))
        return 1

    print(json.dumps(result, sort_keys=True, indent=2))
    return 0 if result["acceptance_status"] == PASS else 1
