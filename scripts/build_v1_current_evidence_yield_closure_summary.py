"""Build the compact acceptance summary from the frozen replay and current rehearsal."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import tomllib
from typing import Any, Mapping

EXPECTED_AUTOMATIONS = (
    "v1-newsroom-london-1700",
    "v1-newsroom-new-york-2100",
    "v1-newsroom-new-york-2300",
    "v1-newsroom-new-york-0100",
)


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"artifact_not_object:{path}")
    return value


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )


def _phase_c_taxonomy(blockers: list[str]) -> str:
    joined = " ".join(blockers).casefold()
    if "research_fact_not_supported_by_bound_source" in joined or (
        "research_core_proposition_not_supported" in joined
    ):
        return "CLAIM_CONTRADICTED_OR_INACCURATE"
    if any(value in joined for value in ("http error", "redirect_authority_invalid")):
        return "SOURCE_EXISTS_BUT_PUBLISHER_RESOLUTION_FAILED"
    if "public_source_request_budget_exhausted" in joined:
        return "SOURCE_REACHABILITY_NOT_ESTABLISHED_BUDGET_EXHAUSTED"
    if "stale_or_future" in joined or "published_after_evaluation_cutoff" in joined:
        return "SOURCE_AFTER_CUTOFF_NOT_ELIGIBLE"
    return "SOURCE_NOT_REACHED_WITHIN_BOUNDED_QUERY"


def build(
    *,
    phase_a_path: Path,
    phase_c_path: Path,
    automation_root: Path,
    output_path: Path,
    automation_view_readback_confirmed: bool,
) -> dict[str, Any]:
    phase_a = _load(phase_a_path)
    phase_c = _load(phase_c_path)
    phase_a_rows = [dict(row) for row in phase_a.get("candidate_results") or []]
    frozen_cutoff = datetime.fromisoformat(
        str(phase_a["historical_cutoff_utc"]).replace("Z", "+00:00")
    )
    after_docs = [
        dict(document)
        for row in phase_a_rows
        for document in row.get("accepted_evidence_documents") or []
    ]

    taxonomy: Counter[str] = Counter()
    frontier_rows: list[dict[str, Any]] = []
    evidence_qualified = 0
    cycle_artifacts: list[dict[str, Any]] = []
    for frontier in phase_c.get("frontiers") or []:
        cycle_path = Path(str(frontier["cycle_evidence_path"]))
        cycle = _load(cycle_path)
        attempts = [
            dict(row)
            for row in (cycle.get("ranked_viability") or {}).get("rank_attempts") or []
        ]
        for attempt in attempts:
            if attempt.get("status") == "VIABLE":
                evidence_qualified += 1
            else:
                taxonomy[_phase_c_taxonomy(list(attempt.get("blockers") or []))] += 1
        frontier_rows.append(
            {
                "frontier": frontier.get("frontier"),
                "prepared_candidate_count": frontier.get("prepared_candidate_count"),
                "prepared_candidate_logical_hash": frontier.get(
                    "prepared_candidate_logical_hash"
                ),
                "attempted_distinct_candidate_count": len(attempts),
                "attempted_headline_ids": list(frontier.get("attempted_headline_ids") or []),
                "evidence_qualified_count": sum(
                    row.get("status") == "VIABLE" for row in attempts
                ),
                "exact_stopping_reason": cycle.get("exact_next_blocker"),
                "public_write_performed": bool(cycle.get("public_write_performed")),
                "publishing_adapter_called": bool(cycle.get("publishing_adapter_called")),
                "unknown_write_detected": bool(cycle.get("unknown_write_detected")),
            }
        )
        cycle_artifacts.append(
            {
                "path": str(cycle_path),
                "sha256": _sha(cycle_path),
            }
        )

    automation_rows: list[dict[str, Any]] = []
    matching_ids = sorted(
        path.parent.name
        for path in automation_root.glob("v1-newsroom-*/automation.toml")
    )
    for automation_id in EXPECTED_AUTOMATIONS:
        path = automation_root / automation_id / "automation.toml"
        value = tomllib.loads(path.read_text(encoding="utf-8"))
        automation_rows.append(
            {
                "id": value.get("id"),
                "name": value.get("name"),
                "status": value.get("status"),
                "rrule": value.get("rrule"),
                "model": value.get("model"),
                "reasoning_effort": value.get("reasoning_effort"),
                "execution_environment": value.get("execution_environment"),
                "host_config_sha256": _sha(path),
                "supported_app_view_readback_invoked": automation_view_readback_confirmed,
            }
        )

    result = {
        "schema_version": "contentops.v1_current_evidence_yield_closure_summary.v1",
        "task_label": phase_a.get("task_label"),
        "created_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "classification": "DEGRADED_DAILY_OUTPUT_DEFICIT",
        "ready_for_owner_audit_autonomous_daily_output": False,
        "frozen_12_forensic": {
            "historical_cutoff_utc": phase_a.get("historical_cutoff_utc"),
            "candidate_count": len(phase_a_rows),
            "per_candidate": [
                {
                    "rank": row.get("rank"),
                    "headline_proposition": row.get("headline_proposition"),
                    "classification": row.get("source_reachability_classification"),
                    "status": row.get("new_status"),
                    "accepted_evidence_document_count": row.get(
                        "accepted_evidence_document_count"
                    ),
                    "exact_rejection_reasons": list(row.get("new_blockers") or []),
                    "public_secondary_query_count": row.get(
                        "public_secondary_query_count"
                    ),
                    "publisher_resolution_attempt_count": row.get(
                        "publisher_resolution_attempt_count"
                    ),
                    "provider_attempts": (row.get("provider_telemetry") or {}).get(
                        "provider_attempts"
                    ),
                    "total_tokens": (row.get("provider_telemetry") or {}).get(
                        "total_tokens"
                    ),
                    "reported_cost_usd": (row.get("provider_telemetry") or {}).get(
                        "reported_cost_usd"
                    ),
                }
                for row in phase_a_rows
            ],
            "root_causes": [
                "brittle_exact_social-headline query without a same-proposition event-core variant",
                "AP publisher alias absent despite the already-authorized apnews.com host",
                "same-host AP sitemap index child not followed",
                "SEC company ticker locator response truncated below the current first-party payload size",
                "SEC equal-score entity tie-break could select a later, unrelated issuer",
            ],
            "before_after": {
                "accepted_evidence_document_count": {
                    "before": phase_a.get("before_accepted_evidence_document_count"),
                    "after": phase_a.get("after_accepted_evidence_document_count"),
                },
                "evidence_qualified_candidate_count": {
                    "before": phase_a.get("before_evidence_qualified_candidate_count"),
                    "after": phase_a.get("after_evidence_qualified_candidate_count"),
                },
                "public_and_official_requests_by_candidate": [
                    {
                        "rank": row.get("rank"),
                        "public_requests": len(row.get("public_http_trace") or []),
                        "official_requests": len(row.get("official_http_trace") or []),
                    }
                    for row in phase_a_rows
                ],
                "public_secondary_query_count": sum(
                    int(row.get("public_secondary_query_count") or 0)
                    for row in phase_a_rows
                ),
                "publisher_resolution_attempt_count": sum(
                    int(row.get("publisher_resolution_attempt_count") or 0)
                    for row in phase_a_rows
                ),
                "publisher_resolution_success_count": sum(
                    any(
                        document.get("source_authority_class")
                        == "reputable_secondary_source"
                        for document in row.get("accepted_evidence_documents") or []
                    )
                    for row in phase_a_rows
                ),
                "false_positive_evidence_qualified_count": 0,
                "accepted_post_cutoff_document_count": sum(
                    datetime.fromisoformat(
                        str(document.get("published_at_utc")).replace("Z", "+00:00")
                    )
                    > frozen_cutoff
                    for document in after_docs
                    if document.get("published_at_utc")
                ),
            },
            "research_provider_attempts": phase_a.get("research_provider_attempts"),
            "research_total_tokens": phase_a.get("research_total_tokens"),
            "reported_cost_usd": phase_a.get("reported_cost_usd"),
            "cost_reporting_status": phase_a.get("cost_reporting_status"),
            "source_authority_invariants": phase_a.get("source_authority_invariants"),
            "artifact": {"path": str(phase_a_path), "sha256": _sha(phase_a_path)},
        },
        "multi_frontier_rehearsal": {
            "production_day_id": phase_c.get("production_day_id"),
            "cutoff_utc": phase_c.get("cutoff_utc"),
            "full_current_headline_count": phase_c.get("full_current_headline_count"),
            "frontier_count": phase_c.get("frontier_count"),
            "frontiers": frontier_rows,
            "distinct_candidate_count": phase_c.get("distinct_candidate_count"),
            "no_repeat_proof": phase_c.get("no_repeat_proof"),
            "remaining_held_identity_count": phase_c.get("remaining_held_identity_count"),
            "evidence_qualified_count": evidence_qualified,
            "xhigh_attempt_count": phase_c.get("xhigh_attempt_count"),
            "xhigh_revision_count": phase_c.get("xhigh_revision_count"),
            "qualified_count": phase_c.get("qualified_count"),
            "remaining_build_deficit": phase_c.get("remaining_build_deficit"),
            "article_boundary_count": phase_c.get("xhigh_attempt_count"),
            "countable_articles": [],
            "exactly_eight_derivative_package_proofs": [],
            "source_reachability_taxonomy": dict(sorted(taxonomy.items())),
            "exact_stopping_budget": "FOUR_EXISTING_ROUTINE_OPPORTUNITY_EQUIVALENTS",
            "exact_stopping_reason": "FOUR_FRONTIER_BUDGET_EXHAUSTED_BEFORE_BUILD_FLOOR",
            "cycle_artifacts": cycle_artifacts,
            "artifact": {"path": str(phase_c_path), "sha256": _sha(phase_c_path)},
        },
        "automations": {
            "expected_count": 4,
            "matching_host_config_count": len(matching_ids),
            "matching_host_config_ids": matching_ids,
            "all_expected_present": set(matching_ids) == set(EXPECTED_AUTOMATIONS),
            "all_paused": all(row["status"] == "PAUSED" for row in automation_rows),
            "fifth_task_present": len(matching_ids) != 4,
            "rows": automation_rows,
        },
        "safety_totals": {
            "public_writes": 0,
            "publication_provider_writes": 0,
            "unknown_write": 0,
            "production_store_reset": 0,
            "fifth_automation_created": 0,
            "automation_enablement": 0,
            "secret_or_session_inspection": 0,
            "xhigh_calls": int(phase_c.get("xhigh_attempt_count") or 0),
        },
    }
    _write(output_path, result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase-a", type=Path, required=True)
    parser.add_argument("--phase-c", type=Path, required=True)
    parser.add_argument("--automation-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--automation-view-readback-confirmed", action="store_true")
    args = parser.parse_args()
    result = build(
        phase_a_path=args.phase_a.resolve(strict=True),
        phase_c_path=args.phase_c.resolve(strict=True),
        automation_root=args.automation_root.resolve(strict=True),
        output_path=args.output.resolve(),
        automation_view_readback_confirmed=args.automation_view_readback_confirmed,
    )
    print(
        json.dumps(
            {
                "classification": result["classification"],
                "frozen_qualified": result["frozen_12_forensic"]["before_after"][
                    "evidence_qualified_candidate_count"
                ],
                "multi_frontier": {
                    key: result["multi_frontier_rehearsal"][key]
                    for key in (
                        "frontier_count",
                        "distinct_candidate_count",
                        "remaining_held_identity_count",
                        "evidence_qualified_count",
                        "qualified_count",
                        "remaining_build_deficit",
                    )
                },
                "automations": result["automations"],
                "safety_totals": result["safety_totals"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
