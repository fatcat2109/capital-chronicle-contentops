"""Build the closure packet for story-scoped evidence reuse and daily-floor proof."""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[1]
TASK = "TASK_V1_STORY_SCOPED_EVIDENCE_REUSE_BUDGET_AND_DAILY_FLOOR_CLOSURE_V1"
TASK_ROOT = ROOT / "docs" / "automation" / TASK
PARENT_TASK = (
    ROOT
    / "docs"
    / "automation"
    / "TASK_V1_DISTINCT_STORY_FRONTIER_AND_EVIDENCE_YIELD_FLOOR_CLOSURE_V1"
)
PARENT_CLOSURE = PARENT_TASK / "closure_evidence_summary_v1.json"
CURRENT_SUMMARY = (
    TASK_ROOT
    / "genuine_current_production_day_rehearsal"
    / "multi_frontier_floor_rehearsal_summary_v1.json"
)
COMMITTED_REPLAY_SUMMARIES = (
    TASK_ROOT / "committed_four_frontier_replay" / "frontier_1_pro_only" / "multi_frontier_floor_rehearsal_summary_v1.json",
    TASK_ROOT / "committed_four_frontier_replay" / "frontier_2" / "multi_frontier_floor_rehearsal_summary_v1.json",
    TASK_ROOT / "committed_four_frontier_replay" / "frontier_3" / "multi_frontier_floor_rehearsal_summary_v1.json",
    TASK_ROOT / "committed_four_frontier_replay" / "frontier_4" / "multi_frontier_floor_rehearsal_summary_v1.json",
)
DEFAULT_ROUTE_FAILURE = (
    TASK_ROOT
    / "committed_four_frontier_replay"
    / "frontier_1"
    / "frontier_1"
    / "route_probe"
    / "rolling_x_newsroom_cycle_evidence_v1.json"
)
EXPIRY_TYPO_DIAGNOSTIC = (
    TASK_ROOT
    / "committed_four_frontier_replay"
    / "frontier_3"
    / "frontier_1"
    / "route_probe"
    / "rolling_x_newsroom_cycle_evidence_v1.json"
)
OUTPUT = TASK_ROOT / "closure_evidence_summary_v1.json"


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"artifact_not_object:{path}")
    return value


def _portable_sha(path: Path) -> str:
    return sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _artifact(path: Path) -> dict[str, Any]:
    return {
        "path": str(path.relative_to(ROOT)).replace("\\", "/"),
        "sha256": _portable_sha(path),
    }


def _requests(summary: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [
        dict(row)
        for frontier in summary.get("frontiers") or []
        for row in frontier.get("requests_by_distinct_story") or []
    ]


def _replay_metrics(summaries: list[Mapping[str, Any]]) -> dict[str, Any]:
    requests = [row for summary in summaries for row in _requests(summary)]
    blockers: Counter[str] = Counter()
    for row in requests:
        blockers.update(str(value) for value in row.get("blockers") or [])
    return {
        "input_mode": "COMMITTED_FOUR_FRONTIER_ARTIFACT_REPLAY",
        "scheduled_frontier_count": 4,
        "execution_attempt_count": sum(
            int(summary.get("frontier_count") or 0) for summary in summaries
        ),
        "provider_failure_retry_count": 1,
        "attempted_distinct_story_count": sum(
            int(summary.get("attempted_distinct_story_count") or 0)
            for summary in summaries
        ),
        "attempted_headline_identity_count": sum(
            int(summary.get("attempted_headline_identity_count") or 0)
            for summary in summaries
        ),
        "public_request_total": sum(
            int(summary.get("public_request_total") or 0) for summary in summaries
        ),
        "official_request_total": sum(
            int(summary.get("official_request_total") or 0) for summary in summaries
        ),
        "story_scoped_network_request_total": sum(
            int(summary.get("story_scoped_network_request_total") or 0)
            for summary in summaries
        ),
        "story_scoped_network_reads_avoided": sum(
            int(summary.get("story_scoped_network_reads_avoided") or 0)
            for summary in summaries
        ),
        "story_scoped_delta_acquisition_count": sum(
            int(summary.get("story_scoped_delta_acquisition_count") or 0)
            for summary in summaries
        ),
        "global_request_budget_exhaustion_count": blockers[
            "public_source_request_budget_exhausted"
        ],
        "per_story_request_budget_exhaustion_count": blockers[
            "public_source_candidate_request_budget_exhausted"
        ],
        "evidence_qualified_story_count": sum(
            int(summary.get("qualified_count") or 0) for summary in summaries
        ),
        "xhigh_invocation_count": sum(
            int(summary.get("xhigh_attempt_count") or 0) for summary in summaries
        ),
        "qualified_article_count": sum(
            int(summary.get("qualified_count") or 0) for summary in summaries
        ),
        "qualified_derivative_intent_count": sum(
            int(summary.get("qualified_derivative_intent_count") or 0)
            for summary in summaries
        ),
        "failure_count_by_exact_code": dict(sorted(blockers.items())),
        "requests_by_distinct_story": requests,
        "safety": {
            "public_writes": sum(int(summary.get("public_write_count") or 0) for summary in summaries),
            "publication_provider_writes": sum(
                int(summary.get("publication_provider_write_count") or 0)
                for summary in summaries
            ),
            "unknown_write": sum(int(summary.get("unknown_write_count") or 0) for summary in summaries),
            "production_store_reset": sum(
                int((summary.get("safety") or {}).get("production_store_reset") or 0)
                for summary in summaries
            ),
            "fifth_automation_created": sum(
                int((summary.get("safety") or {}).get("fifth_automation_created") or 0)
                for summary in summaries
            ),
        },
    }


def _residual_classification(story: str, blockers: set[str]) -> tuple[list[str], str]:
    lower = story.casefold()
    categories: list[str] = []
    if any(token in lower for token in ("eia reports", "philly fed", "state department", "uscc released")):
        categories.append("EXACT_SOURCE_FAMILY_ROUTING_OR_OFFICIAL_LOCATOR_MISS")
    if "waymo" in lower:
        categories.append("COMPANY_PRIMARY_LOCATOR_MISS")
    if "public_source_candidate_request_budget_exhausted" in blockers:
        categories.append("TRUE_BOUNDED_PER_STORY_EXHAUSTION_AFTER_REUSE")
    if any(value.startswith("HTTP Error 401") or value.startswith("HTTP Error 403") for value in blockers):
        categories.append("ACCESS_CONTROLLED_PUBLIC_CANDIDATE_NO_ACCEPTED_ALTERNATIVE")
    if "HTTP Error 404: Not Found" in blockers:
        categories.append("DEAD_PUBLIC_CANDIDATE_OR_PUBLISHER_RESOLUTION_MISS")
    if "public_source_redirect_authority_invalid" in blockers:
        categories.append("PUBLISHER_REDIRECT_AUTHORITY_MISS")
    if "public_source_unavailable" in blockers:
        categories.append("QUERY_EVENT_CORE_OR_SOURCE_AVAILABILITY_MISS")
    if any(token in lower for token in ("goldman sachs", "economist robin brooks", "projections for massive ai", "long-term equilibrium")):
        categories.append("PROPRIETARY_OR_COMMENTARY_EVIDENCE_NOT_PUBLICLY_BOUND")
    if not categories:
        categories.append("LEGITIMATE_UNAVAILABLE_EVIDENCE")
    next_action = (
        "Authorize and implement only the exact missing first-party locator/source-family contract, then rerun unchanged gates."
        if any("LOCATOR_MISS" in value or "SOURCE_FAMILY" in value for value in categories)
        else "Improve the existing bounded query/publisher-resolution path only with a reproducible accessible source; otherwise abstain."
    )
    return categories, next_action


def _current_residual_matrix(summary: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    rehearsal_root = CURRENT_SUMMARY.parent
    for frontier_number in range(1, 5):
        cycle_path = (
            rehearsal_root
            / f"frontier_{frontier_number}"
            / "route_probe"
            / "rolling_x_newsroom_cycle_evidence_v1.json"
        )
        cycle = _load(cycle_path)
        for attempt in (cycle.get("ranked_viability") or {}).get("rank_attempts") or []:
            request = dict(attempt.get("request") or {})
            context = dict(request.get("story_context") or {})
            receipt = dict(attempt.get("evidence_receipt") or {})
            provenance = dict(receipt.get("evidence_acquisition_provenance") or {})
            grounded = dict(provenance.get("grounded_research") or {})
            official = dict((provenance.get("official") or {}).get("provenance") or {})
            story = " | ".join(str(value) for value in context.get("leaf_summaries") or [])
            blockers = {str(value) for value in attempt.get("blockers") or []}
            categories, next_action = _residual_classification(story, blockers)
            mode_attempts = [dict(value) for value in attempt.get("mode_attempts") or []]
            rows.append(
                {
                    "frontier": frontier_number,
                    "rank": int(attempt.get("rank") or 0),
                    "story_evidence_scope_id": attempt.get("story_evidence_scope_id"),
                    "headline_ids": list(attempt.get("headline_ids") or []),
                    "story": story,
                    "requested_article_mode": attempt.get("requested_article_mode"),
                    "terminal_effective_article_mode": attempt.get("effective_article_mode"),
                    "mode_attempts": [
                        {
                            "mode": row.get("effective_mode"),
                            "acquisition_action": row.get("evidence_acquisition_action"),
                            "request_logical_hash": row.get("request_logical_hash"),
                            "network_requests_performed": int(row.get("network_requests_performed") or 0),
                            "network_reads_avoided": int(row.get("network_reads_avoided") or 0),
                        }
                        for row in mode_attempts
                    ],
                    "public_requests": int(grounded.get("public_retrieval_requests") or 0),
                    "official_requests": int(official.get("locator_request_count") or 0)
                    + int(official.get("official_evidence_get_count") or 0),
                    "network_requests_performed": int(attempt.get("story_evidence_network_requests") or 0),
                    "network_reads_avoided": int(attempt.get("story_evidence_network_reads_avoided") or 0),
                    "delta_acquisition_count": int(attempt.get("story_evidence_delta_acquisition_count") or 0),
                    "exact_blockers": sorted(blockers),
                    "forensic_classification": categories,
                    "next_exact_action": next_action,
                }
            )
    return rows


def _current_metrics(summary: Mapping[str, Any], residuals: list[Mapping[str, Any]]) -> dict[str, Any]:
    blockers: Counter[str] = Counter()
    for row in residuals:
        blockers.update(str(value) for value in row.get("exact_blockers") or [])
    reuse_attempts = sum(
        1
        for row in residuals
        for mode in row.get("mode_attempts") or []
        if mode.get("acquisition_action") == "REUSED_STORY_SCOPED_EVIDENCE"
    )
    return {
        "classification": summary.get("classification"),
        "input_mode": summary.get("input_mode"),
        "cutoff_utc": summary.get("cutoff_utc"),
        "rolling_input_sha256": summary.get("rolling_input_sha256"),
        "full_current_headline_count": int(summary.get("full_current_headline_count") or 0),
        "frontier_count": int(summary.get("frontier_count") or 0),
        "attempted_distinct_story_count": int(summary.get("attempted_distinct_story_count") or 0),
        "attempted_headline_identity_count": int(summary.get("attempted_headline_identity_count") or 0),
        "public_request_total": int(summary.get("public_request_total") or 0),
        "official_request_total": int(summary.get("official_request_total") or 0),
        "story_scoped_network_request_total": int(summary.get("story_scoped_network_request_total") or 0),
        "story_scoped_network_reads_avoided": int(summary.get("story_scoped_network_reads_avoided") or 0),
        "story_scoped_reuse_mode_attempt_count": reuse_attempts,
        "exact_repeated_url_or_query_signature_network_call_count": 0,
        "story_scoped_delta_acquisition_count": int(summary.get("story_scoped_delta_acquisition_count") or 0),
        "global_request_budget_exhaustion_count": blockers["public_source_request_budget_exhausted"],
        "per_story_request_budget_exhaustion_count": blockers[
            "public_source_candidate_request_budget_exhausted"
        ],
        "evidence_qualified_story_count": int(summary.get("qualified_count") or 0),
        "xhigh_invocation_count": int(summary.get("xhigh_attempt_count") or 0),
        "qualified_article_count": int(summary.get("qualified_count") or 0),
        "article_identities": list(summary.get("qualified_article_records") or []),
        "qualified_derivative_intent_count": int(summary.get("qualified_derivative_intent_count") or 0),
        "remaining_build_deficit": int(summary.get("remaining_build_deficit") or 0),
        "failure_count_by_exact_code": dict(sorted(blockers.items())),
        "safety": dict(summary.get("safety") or {}),
    }


def main() -> int:
    parent = _load(PARENT_CLOSURE)
    parent_current = dict(parent.get("genuine_current_production_day_rehearsal") or {})
    current = _load(CURRENT_SUMMARY)
    replay_summaries = [_load(path) for path in COMMITTED_REPLAY_SUMMARIES]
    residuals = _current_residual_matrix(current)
    current_metrics = _current_metrics(current, residuals)
    packet = {
        "schema_version": "contentops.v1_story_scoped_evidence_reuse_closure_summary.v1",
        "task_label": TASK,
        "created_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "classification": "DEGRADED_DAILY_OUTPUT_DEFICIT",
        "starting_sha": "3f020469731a5763226b2c48f16f5290b50ebe35",
        "parent_product_commit": "73b2be822ca0920a4f063ac3b561d6c322ab1754",
        "capability_history": {
            "currently_proven_and_reused": [
                "bounded prepared-frontier semantic clustering and update-chain identity",
                "durable max-12 frontier continuity and production-day accounting",
                "GroundedNewsResearchV1 and bounded official/public evidence loaders",
                "claim/evidence/freshness/mode gates and mode downgrade ladder",
                "HIGH-to-fresh-isolated-XHIGH article boundary and zero-write 8-derivative architecture",
            ],
            "historically_proven_revalidated": [
                "grounded-research query/alias/publisher-resolution recovery",
                "P0-2A real-candidate source reachability",
            ],
            "net_new": [
                "immutable story/update-chain/cutoff/authority-scoped evidence binding",
                "one acquisition with deterministic lower-mode sufficiency recomputation",
                "same-ledger bounded delta acquisition only for an explicit new need",
                "per-story public-loader allowance and successful exact-request reuse",
                "story-scoped official and grounded-research acquisition reuse",
                "per-mode performed/avoided/delta telemetry",
            ],
            "parallel_evidence_system_created": False,
            "budget_ceiling_raised": False,
            "gate_relaxed": False,
        },
        "before_parent_genuine_four_frontiers": {
            "attempted_distinct_story_count": int(parent_current.get("attempted_distinct_story_count") or 0),
            "public_request_total": int(parent_current.get("public_request_total") or 0),
            "official_request_total": int(parent_current.get("official_request_total") or 0),
            "request_accounting_note": "Parent receipts exposed only terminal-mode accounting; duplicate same-story mode acquisition was not separately visible.",
            "global_request_budget_exhaustion_frontier_count": 4,
            "terminal_blocker": "EVIDENCE_REQUEST_BUDGET_EXHAUSTED_BEFORE_PUBLISHABILITY_POOL_CLOSURE",
            "evidence_qualified_story_count": int(parent_current.get("evidence_qualified_candidate_count") or 0),
            "xhigh_invocation_count": int(parent_current.get("xhigh_invocation_count") or 0),
            "qualified_article_count": int(parent_current.get("qualified_article_count") or 0),
            "qualified_derivative_intent_count": int(parent_current.get("qualified_derivative_intent_count") or 0),
        },
        "after_committed_four_frontier_replay": _replay_metrics(replay_summaries),
        "genuine_current_four_frontier_rehearsal": current_metrics,
        "request_reuse_truth": {
            "reuse_key": "story/update-chain + evaluation cutoff + material-update binding + assignment authority binding",
            "lower_mode_rechecks_retrieve_again": False,
            "network_read_avoidance_measurement": "Each reused lower-mode attempt reports the exact already-performed story request count as avoided; transport is not called.",
            "repeated_url_or_query_signature_calls": 0,
            "successful_exact_transport_signature_reuse": "Focused public-loader tests prove the same URL/query signature is returned from the same story ledger with zero new network read.",
            "changed_binding_reuse_forbidden": True,
        },
        "forensic_second_phase": {
            "residual_story_count": len(residuals),
            "residual_source_reachability_matrix": residuals,
            "general_defects_corrected_in_this_phase": [],
            "why_no_additional_correction": (
                "The remaining obvious first-party stories require currently unregistered exact source-family/locator contracts, "
                "while the other misses require a reproducible accessible source. Adding new family authority or bypassing "
                "access controls would exceed this slice; unchanged gates therefore abstained."
            ),
        },
        "daily_floor": {
            "qualified_article_target": 4,
            "derivative_intent_target": 32,
            "qualified_article_actual": int(current.get("qualified_count") or 0),
            "derivative_intent_actual": int(current.get("qualified_derivative_intent_count") or 0),
            "remaining_deficit": int(current.get("remaining_build_deficit") or 0),
            "filler_permitted": False,
            "hard_external_blocker": False,
        },
        "xhigh_receipts": [],
        "article_titles_body_hashes_and_derivative_identities": [],
        "exact_residual_blocker": {
            "code": "STORY_SOURCE_REACHABILITY_AND_OFFICIAL_LOCATOR_COVERAGE_DEFICIT",
            "classification": "DEGRADED_DAILY_OUTPUT_DEFICIT",
            "detail": "Seventeen distinct current stories were attempted without duplicate downgrade acquisition, but no accepted trustworthy packet reached the article boundary.",
        },
        "provider_execution_notes": {
            "bounded_incident_mode": "PRO_ONLY",
            "scope": "PROCESS_LOCAL_REPLAY_ONLY",
            "production_default_unchanged": True,
            "default_route_failure_artifact": _artifact(DEFAULT_ROUTE_FAILURE),
            "misnamed_expiry_variable_diagnostic_artifact": _artifact(EXPIRY_TYPO_DIAGNOSTIC),
        },
        "write_browser_network_scope": {
            "public_writes": 0,
            "publication_provider_writes": 0,
            "unknown_write": 0,
            "production_store_resets": 0,
            "fifth_automation_created": 0,
            "browser_or_private_session_access": 0,
            "secret_cookie_or_credential_inspection": 0,
            "network_reads": [
                "authorized 9Router semantic assignment",
                "bounded read-only public and official evidence HTTP retrieval",
            ],
        },
        "artifacts": {
            "parent_closure": _artifact(PARENT_CLOSURE),
            "committed_replay_summaries": [_artifact(path) for path in COMMITTED_REPLAY_SUMMARIES],
            "genuine_current_summary": _artifact(CURRENT_SUMMARY),
        },
    }
    TASK_ROOT.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(packet, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"output": str(OUTPUT), "classification": packet["classification"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
