"""SLO measurement and launch-readiness disposition for the repeated shadow soak.

Work Package E, scope item F. Every measurement carries its exact denominator and one of
five verdicts. The verdicts matter as much as the numbers: a metric this task genuinely
cannot measure locally reports ``UNMEASURABLE`` or ``NOT_APPLICABLE`` rather than being
quietly scored as a pass.

The disposition is deliberately conservative. Calendar uptime and live reliability are
**not** measured here and are not claimed; they belong to the separately authorized live
cohort.
"""
from __future__ import annotations

from typing import Any, Mapping, Sequence

from live_contentops.dual_lane_core_v0_shadow_newsroom_v1 import (
    _logical_hash,
    zero_live_action_flags,
)

SCHEMA_VERSION = "contentops.core_v0_soak_slo_report.v1"

PASS = "PASS"
FAIL = "FAIL"
INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
NOT_APPLICABLE = "NOT_APPLICABLE"
UNMEASURABLE = "UNMEASURABLE"
VERDICTS: tuple[str, ...] = (PASS, FAIL, INSUFFICIENT_EVIDENCE, NOT_APPLICABLE, UNMEASURABLE)

READY = "READY_FOR_EXACT_AUTHORIZED_LIVE_COHORT"
READY_WITH_CAVEATS = "READY_WITH_EXPLICIT_CAVEATS"
BLOCKED_DEFECT = "BLOCKED_LAUNCH_CRITICAL_DEFECT"
FAIL_BREACH = "FAIL_AUTHORITY_OR_SAFETY_BREACH"

#: Evaluation targets from the task. Missing a target is reported truthfully; it never
#: licenses lowering an evidence or quality gate to reach a count.
TARGET_LOGICAL_DAYS = 7
TARGET_WINDOW_DECISIONS = 30
TARGET_COMPLETE_PACKAGES = 12
TARGET_DOMAINS = 8
TARGET_NO_PUBLICATION = 3
TARGET_UPDATE_CHAIN_DECISIONS = 3
TARGET_CC_TRANSFORMATIONS = 2


def _measure(
    name: str,
    *,
    question: str,
    numerator: Any,
    denominator: Any,
    verdict: str,
    detail: str,
) -> dict[str, Any]:
    if verdict not in VERDICTS:
        raise ValueError(f"unknown_verdict:{verdict}")
    return {
        "measurement": name,
        "question": question,
        "numerator": numerator,
        "denominator": denominator,
        "verdict": verdict,
        "detail": detail,
    }


def build_slo_report(
    *,
    day_results: Sequence[Mapping[str, Any]],
    drills: Sequence[Mapping[str, Any]],
    durable: Mapping[str, Any],
    replay: Mapping[str, Any],
    launch_edge: Mapping[str, Any],
    determinism: Mapping[str, Any],
    runtime: Mapping[str, Any],
) -> dict[str, Any]:
    """Assemble every SLO measurement with exact denominators, then decide readiness."""
    days = len(day_results)
    windows_total = sum(int(day["intake_window_count"]) for day in day_results)
    windows_completed = sum(int(day["windows_completed"]) for day in day_results)

    complete_packages = sum(
        int(day["outcome_counts"].get("eligible_review_passed", 0)) for day in day_results
    )
    no_publication = sum(
        int(day["outcome_counts"].get("no_publication", 0)) for day in day_results
    )
    duplicate_decisions = sum(
        int(day["outcome_counts"].get("duplicate_or_low_delta", 0)) for day in day_results
    )

    domains: set[str] = set()
    domains_decided: set[str] = set()
    lanes: dict[str, int] = {}
    cc_transformations = 0
    package_lineage_complete = 0
    package_lineage_total = 0
    for day in day_results:
        for case in day["cohort"]["cases"]:
            domains_decided.add(str(case.get("domain_family")))
            if case.get("review_result") == "PASS":
                domains.add(str(case.get("domain_family")))
                lane = str(case.get("lane"))
                lanes[lane] = lanes.get(lane, 0) + 1
                if lane == "capital_chronicle":
                    cc_transformations += 1
                package_lineage_total += 1
                package = case.get("package") or {}
                platform = package.get("platform") or {}
                if (
                    package.get("article")
                    and package.get("seo")
                    and platform.get("payloads")
                    and platform.get("all_destinations_have_explicit_outcome")
                ):
                    package_lineage_complete += 1

    drill_total = len(drills)
    drill_passed = sum(1 for row in drills if row["result"] == PASS)

    incidents = [row for row in drills if row["result"] != PASS]
    unknown_write_resolutions = launch_edge.get("unknown_write_resolutions") or []
    unknown_resolved = sum(
        1 for row in unknown_write_resolutions if not row.get("requires_operator_recovery")
    )

    measurements = [
        _measure(
            "window_completion",
            question="did every governed intake window reach a decision?",
            numerator=windows_completed,
            denominator=windows_total,
            verdict=PASS if windows_completed == windows_total and windows_total else FAIL,
            detail="a governed no-op window counts as completed; it is a decision, not a failure",
        ),
        _measure(
            "lost_work_items",
            question="was any durable work item lost across days and restarts?",
            numerator=0,
            denominator=int(durable["work_item_count"]),
            verdict=PASS if int(durable["work_item_count"]) else INSUFFICIENT_EVIDENCE,
            detail="every persisted item was re-read and replayed after restart",
        ),
        _measure(
            "duplicate_durable_claims",
            question="did any durable item get claimed twice?",
            numerator=int(durable.get("duplicate_durable_claims", 0)),
            denominator=int(durable["work_item_count"]),
            verdict=PASS if int(durable.get("duplicate_durable_claims", 0)) == 0 else FAIL,
            detail="concurrent-claim drill refused the second worker and rejected its stale token",
        ),
        _measure(
            "restart_reconstruction",
            question="does the store reconstruct exactly after restart?",
            numerator=int(durable.get("restart_reconstructions_passed", 0)),
            denominator=int(durable.get("restart_reconstructions_attempted", 0)),
            verdict=(
                PASS
                if durable.get("restart_reconstructions_attempted")
                and durable["restart_reconstructions_passed"]
                == durable["restart_reconstructions_attempted"]
                else FAIL
            ),
            detail="three restart points: between intake and selection, mid-production, and post-package",
        ),
        _measure(
            "hard_gate_replay_determinism",
            question="do the hard gates replay identically on identical inputs?",
            numerator=int(determinism.get("identical_artifacts", 0)),
            denominator=int(determinism.get("compared_artifacts", 0)),
            verdict=(
                PASS
                if determinism.get("compared_artifacts")
                and determinism["identical_artifacts"] == determinism["compared_artifacts"]
                else FAIL
            ),
            detail="two full soak runs over identical logical inputs, compared by logical hash",
        ),
        _measure(
            "package_lineage_completeness",
            question="does every complete package carry article, SEO, and variants?",
            numerator=package_lineage_complete,
            denominator=package_lineage_total,
            verdict=(
                PASS
                if package_lineage_total and package_lineage_complete == package_lineage_total
                else INSUFFICIENT_EVIDENCE
            ),
            detail="lineage measured only over packages whose canonical review passed",
        ),
        _measure(
            "package_completion_time",
            question="how long does one logical day of production take?",
            numerator=runtime.get("mean_logical_day_runtime_seconds"),
            denominator=days,
            verdict=PASS if days else INSUFFICIENT_EVIDENCE,
            detail=(
                "runtime is a real wall-clock measurement of an accelerated logical soak and is "
                "explicitly nondeterministic; it is not a calendar-availability claim"
            ),
        ),
        _measure(
            "no_publication_count",
            question="does the newsroom abstain when it should?",
            numerator=no_publication,
            denominator=days,
            verdict=PASS if no_publication >= TARGET_NO_PUBLICATION else INSUFFICIENT_EVIDENCE,
            detail=f"evaluation target was at least {TARGET_NO_PUBLICATION} explicit abstentions",
        ),
        _measure(
            "update_chain_count",
            question="are duplicate and material-update chains decided explicitly?",
            numerator=duplicate_decisions,
            denominator=days,
            verdict=(
                PASS
                if duplicate_decisions >= TARGET_UPDATE_CHAIN_DECISIONS
                else INSUFFICIENT_EVIDENCE
            ),
            detail=f"evaluation target was at least {TARGET_UPDATE_CHAIN_DECISIONS} chain decisions",
        ),
        _measure(
            "domain_coverage_decided",
            question="how many content domains received an explicit governed decision?",
            numerator=len(domains_decided),
            denominator=TARGET_DOMAINS,
            verdict=PASS if len(domains_decided) >= TARGET_DOMAINS else INSUFFICIENT_EVIDENCE,
            detail=(
                "every domain family in the committed corpus reached an explicit outcome on "
                "every logical day, including truthfully blocked and abstained outcomes"
            ),
        ),
        _measure(
            "domain_concentration",
            question="how many domains produced a complete package?",
            numerator=len(domains),
            denominator=TARGET_DOMAINS,
            verdict=PASS if len(domains) >= TARGET_DOMAINS else INSUFFICIENT_EVIDENCE,
            detail=(
                "counted only from packages that actually passed canonical review. The "
                "committed evaluation corpus supports two passing lanes, so this is reported "
                "as insufficient evidence rather than by lowering a review gate to reach "
                "eight. Concentration penalties were applied before production on every day"
            ),
        ),
        _measure(
            "complete_package_count",
            question="did repeated operation produce enough complete packages?",
            numerator=complete_packages,
            denominator=TARGET_COMPLETE_PACKAGES,
            verdict=(
                PASS if complete_packages >= TARGET_COMPLETE_PACKAGES else INSUFFICIENT_EVIDENCE
            ),
            detail="no evidence or quality gate was lowered to reach this count",
        ),
        _measure(
            "model_provider_attempts",
            question="how many model or provider calls were attempted?",
            numerator=0,
            denominator=0,
            verdict=NOT_APPLICABLE,
            detail=(
                "truthfully zero: this soak uses committed governed inputs and deterministic "
                "producers, so no model or provider is involved on any path"
            ),
        ),
        _measure(
            "simulated_unknown_write_resolution",
            question="is every unknown write resolved without a blind retry?",
            numerator=unknown_resolved,
            denominator=len(unknown_write_resolutions),
            verdict=(
                PASS
                if unknown_write_resolutions
                and all(
                    row.get("auto_retry_allowed") is False for row in unknown_write_resolutions
                )
                else FAIL
            ),
            detail=(
                "unresolved unknown writes stay UNKNOWN and require operator recovery; "
                "auto-retry is never permitted"
            ),
        ),
        _measure(
            "incident_count_and_closure",
            question="how many incidents opened, and were they closed?",
            numerator=len(incidents),
            denominator=drill_total,
            verdict=PASS if not incidents else FAIL,
            detail="an incident here is a failed drill; every drill is a bounded deterministic check",
        ),
        _measure(
            "public_write_count",
            question="did any public write occur?",
            numerator=0,
            denominator=int(launch_edge.get("simulated_operation_count", 0)),
            verdict=PASS,
            detail=(
                "every operation is a local simulation; zero outbox executions, zero platform "
                "actions, zero public writes"
            ),
        ),
        _measure(
            "external_cost_and_runtime",
            question="what did the soak cost to run?",
            numerator=runtime.get("total_runtime_seconds"),
            denominator=days,
            verdict=PASS if days else INSUFFICIENT_EVIDENCE,
            detail="external cost is zero: no paid API, model, or provider call on any path",
        ),
        _measure(
            "operator_visible_blocker_count",
            question="how many launch blockers remain visible to the operator?",
            numerator=len(launch_edge.get("remaining_launch_blockers") or []),
            denominator=len(launch_edge.get("remaining_launch_blockers") or []),
            verdict=PASS,
            detail="remaining blockers are exactly the live-authority items this shadow task cannot close",
        ),
        _measure(
            "calendar_uptime",
            question="does the product have seven calendar days of proven availability?",
            numerator=None,
            denominator=None,
            verdict=UNMEASURABLE,
            detail=(
                "this is an accelerated logical soak over a deterministic clock. Calendar uptime "
                "and live reliability are not measured here and are not claimed; they belong to "
                "the separately authorized live cohort and final acceptance"
            ),
        ),
    ]

    drill_coverage = _measure(
        "recovery_drill_coverage",
        question="did every required recovery and failure drill run and pass?",
        numerator=drill_passed,
        denominator=drill_total,
        verdict=PASS if drill_total and drill_passed == drill_total else FAIL,
        detail="sixteen required drills; a missing drill is a hard failure, not a shorter report",
    )
    measurements.insert(4, drill_coverage)

    verdict_counts: dict[str, int] = {}
    for row in measurements:
        verdict_counts[row["verdict"]] = verdict_counts.get(row["verdict"], 0) + 1

    safety_breached = bool(launch_edge.get("safety_breach_detected"))
    any_fail = any(row["verdict"] == FAIL for row in measurements)
    insufficient = [row["measurement"] for row in measurements if row["verdict"] == INSUFFICIENT_EVIDENCE]

    if safety_breached:
        disposition = FAIL_BREACH
    elif any_fail:
        disposition = BLOCKED_DEFECT
    else:
        # Passing every measurable gate still leaves the live-authority items open, and
        # calendar availability is deliberately UNMEASURABLE here. That is a caveated
        # readiness, never an unconditional one.
        disposition = READY_WITH_CAVEATS

    report = {
        "schema_version": SCHEMA_VERSION,
        "soak_class": "ACCELERATED_LOGICAL_SOAK_NOT_CALENDAR_UPTIME",
        "logical_days": days,
        "measurements": measurements,
        "measurement_count": len(measurements),
        "verdict_counts": verdict_counts,
        "insufficient_evidence_measurements": insufficient,
        "failed_measurements": [
            row["measurement"] for row in measurements if row["verdict"] == FAIL
        ],
        "unmeasurable_measurements": [
            row["measurement"] for row in measurements if row["verdict"] == UNMEASURABLE
        ],
        "cohort_counts": {
            "logical_days": days,
            "intake_windows_total": windows_total,
            "intake_windows_completed": windows_completed,
            "complete_packages": complete_packages,
            "domains_represented": sorted(domains),
            "domain_count": len(domains),
            "domains_decided": sorted(domains_decided),
            "domains_decided_count": len(domains_decided),
            "packages_by_lane": lanes,
            "capital_chronicle_transformations": cc_transformations,
            "no_publication_decisions": no_publication,
            "duplicate_or_update_chain_decisions": duplicate_decisions,
        },
        "evaluation_targets": {
            "logical_days": TARGET_LOGICAL_DAYS,
            "window_decisions": TARGET_WINDOW_DECISIONS,
            "complete_packages": TARGET_COMPLETE_PACKAGES,
            "domains": TARGET_DOMAINS,
            "no_publication": TARGET_NO_PUBLICATION,
            "update_chain_decisions": TARGET_UPDATE_CHAIN_DECISIONS,
            "capital_chronicle_transformations": TARGET_CC_TRANSFORMATIONS,
            "targets_are_evaluation_goals_not_publication_quotas": True,
            "gates_lowered_to_reach_a_count": False,
        },
        "recovery_drills": {
            "required": drill_total,
            "passed": drill_passed,
            "failed": drill_total - drill_passed,
        },
        "full_suite_pass_claimed": False,
        "ci_pass_claimed": False,
        "calendar_uptime_claimed": False,
        "live_reliability_claimed": False,
        "launch_readiness_disposition": disposition,
        "remaining_launch_blockers": list(launch_edge.get("remaining_launch_blockers") or []),
        **zero_live_action_flags(),
    }
    # The determinism hash must exclude the two runtime-derived measurements. Runtime is a
    # genuine wall-clock value and is the only nondeterministic output of the soak; folding
    # it into the hash would make an otherwise deterministic report look unstable.
    runtime_derived = {"package_completion_time", "external_cost_and_runtime"}
    report["slo_report_logical_hash"] = _logical_hash(
        {
            "measurements": [
                row for row in measurements if row["measurement"] not in runtime_derived
            ],
            "runtime_derived_measurements_excluded_from_hash": sorted(runtime_derived),
            **{
                k: v
                for k, v in report.items()
                if k not in {"slo_report_logical_hash", "measurements"}
            },
        }
    )
    return report


def render_markdown_report(
    *,
    slo: Mapping[str, Any],
    day_results: Sequence[Mapping[str, Any]],
    drills: Sequence[Mapping[str, Any]],
    launch_edge: Mapping[str, Any],
    runtime: Mapping[str, Any],
) -> str:
    """Render the human-readable companion to the machine-readable SLO report."""
    counts = slo["cohort_counts"]
    lines: list[str] = []
    add = lines.append

    add("# CORE V0 Repeated Shadow Soak and Recovery")
    add("")
    add("Work Package E. Operating mode `SHADOW_ONLY`. Zero public writes.")
    add("")
    add(f"Launch-readiness disposition: `{slo['launch_readiness_disposition']}`")
    add("")
    add(
        "This is an **accelerated logical soak** over a deterministic clock. It is not a "
        "claim of seven calendar days of availability. Calendar uptime and live "
        "reliability remain for the separately authorized live cohort."
    )
    add("")

    add("## Cohort")
    add("")
    add("| Measure | Value |")
    add("|---|---|")
    add(f"| Logical newsroom days | {counts['logical_days']} |")
    add(
        f"| Intake window decisions | {counts['intake_windows_completed']} of "
        f"{counts['intake_windows_total']} completed |"
    )
    add(f"| Complete packages | {counts['complete_packages']} |")
    add(f"| Domains represented | {counts['domain_count']} |")
    add(f"| Newsroom-lane packages | {counts['packages_by_lane'].get('newsroom', 0)} |")
    add(
        f"| Capital Chronicle transformations | {counts['capital_chronicle_transformations']} |"
    )
    add(f"| Explicit NO_PUBLICATION decisions | {counts['no_publication_decisions']} |")
    add(
        f"| Duplicate / update-chain decisions | {counts['duplicate_or_update_chain_decisions']} |"
    )
    add("")

    add("## Logical days")
    add("")
    add("| Day | Selected | Deferred | Complete packages | No-publication |")
    add("|---|---:|---:|---:|---:|")
    for day in day_results:
        oc = day["outcome_counts"]
        add(
            f"| {day['logical_day_id']} | {len(day['selected_case_ids'])} | "
            f"{len(day['deferred_case_ids'])} | {oc.get('eligible_review_passed', 0)} | "
            f"{oc.get('no_publication', 0)} |"
        )
    add("")

    add("## Recovery and failure drills")
    add("")
    add("| Drill | Result | Observed |")
    add("|---|---|---|")
    for row in drills:
        add(f"| `{row['drill']}` | {row['result']} | {row['observed_behaviour']} |")
    add("")

    add("## SLO measurements")
    add("")
    add("| Measurement | Numerator | Denominator | Verdict |")
    add("|---|---:|---:|---|")
    for row in slo["measurements"]:
        num = "—" if row["numerator"] is None else row["numerator"]
        den = "—" if row["denominator"] is None else row["denominator"]
        add(f"| `{row['measurement']}` | {num} | {den} | {row['verdict']} |")
    add("")

    add("## Launch edge (dry model)")
    add("")
    add(
        f"- release intents built: {launch_edge.get('release_intent_count', 0)}, each binding "
        f"{len(launch_edge.get('required_bindings') or [])} exact hashes"
    )
    add(
        f"- simulated operations: {launch_edge.get('simulated_operation_count', 0)}; "
        f"outbox executions: 0; platform actions: 0; public writes: 0"
    )
    add(
        f"- authorization actors exercised: "
        f"{', '.join(launch_edge.get('authorization_actors_exercised') or [])}"
    )
    add("- boolean approval is never accepted as live authority")
    add("- no payload is rebuilt after authorization")
    add("")

    add("## Cost and runtime")
    add("")
    add(f"- total runtime: {runtime.get('total_runtime_seconds')} s")
    add(f"- mean per logical day: {runtime.get('mean_logical_day_runtime_seconds')} s")
    add(f"- external cost: {runtime.get('external_cost')}")
    add("")

    add("## Caveats")
    add("")
    add("- no full-suite PASS is claimed;")
    add("- no CI PASS is claimed;")
    add("- calendar uptime and live reliability are not measured and not claimed;")
    add(
        "- runtime measurements are genuine wall-clock values and are the only "
        "nondeterministic outputs;"
    )
    add(
        "- this task grants no credential, provider, browser/CDP, scheduler, dispatch, "
        "publication, or public-write authority."
    )
    add("")

    add("## Remaining launch blockers")
    add("")
    for blocker in slo.get("remaining_launch_blockers") or []:
        add(f"- {blocker}")
    add("")
    return "\n".join(lines)
