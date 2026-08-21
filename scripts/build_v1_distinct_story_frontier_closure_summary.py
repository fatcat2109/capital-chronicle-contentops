"""Build the auditable closure packet for the distinct-story frontier task."""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[1]
TASK = "TASK_V1_DISTINCT_STORY_FRONTIER_AND_EVIDENCE_YIELD_FLOOR_CLOSURE_V1"
TASK_ROOT = ROOT / "docs" / "automation" / TASK
PARENT_TASK_ROOT = (
    ROOT
    / "docs"
    / "automation"
    / "TASK_V1_CURRENT_EVIDENCE_YIELD_REACHABILITY_AND_MULTI_FRONTIER_DAILY_FLOOR_CLOSURE_V1"
)
PARENT_CLOSURE = PARENT_TASK_ROOT / "closure_evidence_summary_v1.json"
PARENT_REPLAY = TASK_ROOT / "parent_frozen_multi_frontier_replay" / "multi_frontier_floor_rehearsal_summary_v1.json"
CURRENT_REHEARSAL = TASK_ROOT / "genuine_current_production_day_rehearsal" / "multi_frontier_floor_rehearsal_summary_v1.json"
INITIAL_PROVIDER_FAILURE = (
    TASK_ROOT
    / "parent_replay_initial_global_provider_failure"
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


def _sha(path: Path) -> str:
    # Evidence JSON/Markdown is committed as LF by repository attributes. Normalize here so
    # hashes created from a Windows worktree bind the exact portable committed bytes.
    normalized = path.read_bytes().replace(b"\r\n", b"\n")
    return sha256(normalized).hexdigest()


def _artifact(path: Path) -> dict[str, Any]:
    return {
        "path": str(path.relative_to(ROOT)).replace("\\", "/"),
        "sha256": _sha(path),
    }


def _attempt_requests_and_failures(attempts: list[Mapping[str, Any]]) -> tuple[int, int, Counter[str]]:
    public = 0
    official = 0
    failures: Counter[str] = Counter()
    for attempt in attempts:
        receipt = dict(attempt.get("evidence_receipt") or {})
        provenance = dict(receipt.get("evidence_acquisition_provenance") or {})
        grounded = dict(provenance.get("grounded_research") or {})
        official_provenance = dict((provenance.get("official") or {}).get("provenance") or {})
        public += int(grounded.get("public_retrieval_requests") or 0)
        official += int(official_provenance.get("locator_request_count") or 0)
        official += int(official_provenance.get("official_evidence_get_count") or 0)
        failures.update(str(value) for value in attempt.get("blockers") or [])
    return public, official, failures


def _parent_before() -> dict[str, Any]:
    parent = _load(PARENT_CLOSURE)
    public = 0
    official = 0
    failures: Counter[str] = Counter()
    cycle_artifacts = []
    for path in sorted(
        (PARENT_TASK_ROOT / "phase_c_current_multi_frontier_rehearsal").glob(
            "frontier_*/route_probe/rolling_x_newsroom_cycle_evidence_v1.json"
        )
    ):
        cycle = _load(path)
        viability = dict(cycle.get("ranked_viability") or {})
        row_public, row_official, row_failures = _attempt_requests_and_failures(
            list(viability.get("rank_attempts") or [])
        )
        public += row_public
        official += row_official
        failures.update(row_failures)
        cycle_artifacts.append(_artifact(path))
    multi = dict(parent.get("multi_frontier_rehearsal") or {})
    return {
        "full_current_headline_count": int(multi.get("full_current_headline_count") or 0),
        "frontier_count": int(multi.get("frontier_count") or 0),
        "prepared_headline_identity_slot_count": 48,
        "distinct_story_opportunity_count": 48,
        "candidate_slots_saved_by_semantic_clustering": 0,
        "attempted_distinct_story_count": 48,
        "attempted_headline_identity_count": int(multi.get("distinct_candidate_count") or 0),
        "public_request_total": public,
        "official_request_total": official,
        "evidence_failure_count_by_exact_code": dict(sorted(failures.items())),
        "evidence_qualified_candidate_count": int(multi.get("evidence_qualified_count") or 0),
        "xhigh_invocation_count": int(multi.get("xhigh_attempt_count") or 0),
        "qualified_article_count": int(multi.get("qualified_count") or 0),
        "qualified_derivative_intent_count": 0,
        "remaining_build_deficit": int(multi.get("remaining_build_deficit") or 0),
        "terminal_blocker": "EVIDENCE_REQUEST_BUDGET_EXHAUSTED_BEFORE_PUBLISHABILITY_POOL_CLOSURE",
        "cycle_artifacts": cycle_artifacts,
    }


def _failure_counts(summary: Mapping[str, Any]) -> dict[str, int]:
    failures: Counter[str] = Counter()
    for frontier in summary.get("frontiers") or []:
        for request in frontier.get("requests_by_distinct_story") or []:
            failures.update(str(value) for value in request.get("blockers") or [])
    return dict(sorted(failures.items()))


def _collapse_counts(summary: Mapping[str, Any]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for frontier in summary.get("frontiers") or []:
        for row in frontier.get("duplicate_update_chain_collapse_matrix") or []:
            counts[str(row.get("relationship") or "unknown")] += 1
    return dict(sorted(counts.items()))


def _rehearsal_metrics(summary: Mapping[str, Any]) -> dict[str, Any]:
    frontiers = list(summary.get("frontiers") or [])
    return {
        "classification": summary.get("classification"),
        "input_mode": summary.get("input_mode"),
        "full_current_headline_count": int(summary.get("full_current_headline_count") or 0),
        "frontier_count": int(summary.get("frontier_count") or 0),
        "prepared_headline_identity_slot_count": int(
            summary.get("prepared_headline_identity_slot_count") or 0
        ),
        "distinct_story_opportunity_count": int(
            summary.get("distinct_story_opportunity_count") or 0
        ),
        "candidate_slots_saved_by_semantic_clustering": int(
            summary.get("candidate_slots_saved_by_semantic_clustering") or 0
        ),
        "attempted_distinct_story_count": int(
            summary.get("attempted_distinct_story_count") or 0
        ),
        "attempted_headline_identity_count": int(
            summary.get("attempted_headline_identity_count") or 0
        ),
        "collapse_relationship_count": _collapse_counts(summary),
        "public_request_total": int(summary.get("public_request_total") or 0),
        "official_request_total": int(summary.get("official_request_total") or 0),
        "requests_by_distinct_story": [
            request
            for frontier in frontiers
            for request in frontier.get("requests_by_distinct_story") or []
        ],
        "evidence_failure_count_by_exact_code": _failure_counts(summary),
        "evidence_qualified_candidate_count": int(summary.get("qualified_count") or 0),
        "xhigh_invocation_count": int(summary.get("xhigh_attempt_count") or 0),
        "qualified_article_count": int(summary.get("qualified_count") or 0),
        "qualified_article_identities": [
            row.get("article_id") for row in summary.get("qualified_article_records") or []
        ],
        "qualified_derivative_intent_count": int(
            summary.get("qualified_derivative_intent_count") or 0
        ),
        "qualified_derivative_intent_identities": [
            intent.get("intent_id")
            for article in summary.get("qualified_article_records") or []
            for intent in article.get("derivative_intents") or []
        ],
        "remaining_build_deficit": int(summary.get("remaining_build_deficit") or 0),
        "build_floor_satisfied": bool(summary.get("build_floor_satisfied")),
        "exact_next_blocker_taxonomy": list(
            summary.get("exact_next_blocker_taxonomy") or []
        ),
        "exact_headline_identity_coverage_all_frontiers": bool(
            summary.get("exact_headline_identity_coverage_all_frontiers")
        ),
        "no_repeat_proof": bool(summary.get("no_repeat_proof")),
        "remaining_held_identity_count": int(
            summary.get("remaining_held_identity_count") or 0
        ),
        "safety": dict(summary.get("safety") or {}),
    }


def main() -> int:
    parent_replay = _load(PARENT_REPLAY)
    current = _load(CURRENT_REHEARSAL)
    initial = _load(INITIAL_PROVIDER_FAILURE)
    packet = {
        "schema_version": "contentops.v1_distinct_story_frontier_closure_summary.v1",
        "task_label": TASK,
        "created_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "classification": "DEGRADED_DAILY_OUTPUT_DEFICIT",
        "starting_sha": "bbd2ef9b104a01d7cbb14743b976ff30932a3e08",
        "capability_history": {
            "reused": [
                "existing semantic leaf/global assignment and update-chain relationship contract",
                "max-12 durable prepared-frontier and evaluated-headline continuity",
                "bounded official/public evidence loaders, grounded research, publisher resolution, and claim binding",
                "existing zero-write article/XHIGH/publication architecture",
            ],
            "net_new": [
                "bounded prepared-frontier semantic assignment before evidence walking",
                "prepared identity-to-story collapse and per-story request telemetry",
                "parent-input replay aggregation for four committed frontier artifacts",
            ],
            "parallel_system_created": False,
        },
        "parent_before": _parent_before(),
        "parent_after_distinct_story_replay": _rehearsal_metrics(parent_replay),
        "genuine_current_production_day_rehearsal": _rehearsal_metrics(current),
        "initial_default_quality_route_failure": {
            "classification": initial.get("classification"),
            "exact_next_blocker": initial.get("exact_next_blocker"),
            "leaf_distinct_story_count": len(
                (initial.get("assignment") or {}).get("leaf_clusters") or []
            ),
            "ranked_story_count": len(
                (initial.get("assignment") or {}).get("ranked_clusters") or []
            ),
            "evidence_attempt_count": len(
                (initial.get("ranked_viability") or {}).get("rank_attempts") or []
            ),
            "public_write_performed": bool(initial.get("public_write_performed")),
            "unknown_write_detected": bool(initial.get("unknown_write_detected")),
            "artifact": _artifact(INITIAL_PROVIDER_FAILURE),
        },
        "provider_incident_replay_contract": {
            "mode": "PRO_ONLY",
            "scope": "SHORT_LIVED_PROCESS_LOCAL_EXISTING_REPOSITORY_SEAM",
            "production_default_unchanged": True,
            "arbitrary_model_identifier_permitted": False,
        },
        "daily_floor": {
            "qualified_article_target": 4,
            "derivative_intent_target": 32,
            "qualified_article_actual": int(current.get("qualified_count") or 0),
            "derivative_intent_actual": int(
                current.get("qualified_derivative_intent_count") or 0
            ),
            "remaining_deficit": int(current.get("remaining_build_deficit") or 0),
            "filler_permitted": False,
        },
        "exact_remaining_product_blocker": {
            "code": "DISTINCT_STORY_EVIDENCE_REACHABILITY_EXHAUSTED_BEFORE_QUALIFIED_YIELD",
            "detail": (
                "The bounded frontier now spends evidence work on semantic story/update chains, "
                "but current ranked stories still fail trustworthy-source acquisition through "
                "query miss, access denial, redirect/publisher resolution, stale official evidence, "
                "or the unchanged per-story/global request ledger before a viable packet forms."
            ),
            "evidence_gate_relaxed": False,
            "request_ceiling_raised": False,
        },
        "write_browser_network_scope": {
            "public_writes": 0,
            "publication_provider_writes": 0,
            "unknown_write": 0,
            "browser_or_private_session_access": 0,
            "secret_or_cookie_inspection": 0,
            "network_reads": [
                "authorized 9Router semantic assignment",
                "bounded public and official evidence HTTP retrieval",
            ],
        },
        "recommended_next_product_gate": (
            "Bounded source-reachability/query/publisher-resolution closure on the demonstrated "
            "distinct current story chains, followed by the same four-frontier zero-write floor rehearsal; "
            "do not enable Automations while the 4/32 build floor remains unproven."
        ),
        "artifacts": {
            "parent_closure": _artifact(PARENT_CLOSURE),
            "parent_after_replay": _artifact(PARENT_REPLAY),
            "genuine_current_rehearsal": _artifact(CURRENT_REHEARSAL),
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
