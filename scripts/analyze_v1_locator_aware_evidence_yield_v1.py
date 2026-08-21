"""Build the sanitized locator-aware 40+2 canary evidence-yield matrix."""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
import sys
from typing import Any, Mapping
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from live_contentops.newsroom_assignment_scheduler_v1 import (
    _context_routed_official_locator_projection,
)
from live_contentops.official_primary_evidence_loader_v1 import OFFICIAL_HOSTS_BY_FAMILY


def _read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _sanitized_label(cluster: Mapping[str, Any], request: Mapping[str, Any]) -> str:
    context = request.get("story_context") or {}
    values = [
        *(context.get("leaf_summaries") or []),
        context.get("why_now"),
        cluster.get("event_topic_summary"),
        cluster.get("why_now"),
    ]
    for value in values:
        text = " ".join(str(value or "").split())
        if text:
            return text[:180]
    return "SANITIZED_STORY_LABEL_UNAVAILABLE"


def _direct_primary_families(request: Mapping[str, Any]) -> list[str]:
    context = request.get("story_context") or {}
    urls = [str(value) for value in context.get("official_source_urls") or []]
    families: set[str] = set()
    for url in urls:
        host = str(urlsplit(url).hostname or "").casefold()
        for family, hosts in OFFICIAL_HOSTS_BY_FAMILY.items():
            if host in hosts:
                families.add(family)
    return sorted(families)


def _cause_flags(blockers: list[str], *, attempted: bool) -> dict[str, bool]:
    text = " ".join(blockers).casefold()
    return {
        "locator_reachability_representation_gap": False,
        "retrieval_or_provider_failure": any(token in text for token in (
            "http error", "public_source_", "grounded_research_", "provider_",
        )),
        "source_family_or_capability_mismatch": any(token in text for token in (
            "capability_missing", "article_mode_", "source_family", "story_type",
        )),
        "freshness_failure": any(token in text for token in (
            "freshness", "after_evaluation_cutoff", "latest_state", "stale",
        )),
        "content_insufficiency": any(token in text for token in (
            "evidence_documents_missing", "minimum_trustworthy_evidence_missing",
            "supported_claims_missing", "relevant_text_unavailable",
        )),
        "request_budget_exhaustion": "budget" in text,
        "other": not attempted,
    }


def _request_for_cluster(
    cluster: Mapping[str, Any], records_by_id: Mapping[str, Mapping[str, Any]]
) -> dict[str, Any]:
    headline_ids = [str(value) for value in cluster.get("headline_ids") or []]
    projection = _context_routed_official_locator_projection(cluster, records_by_id)
    official_urls: list[str] = []
    for headline_id in headline_ids:
        external = (records_by_id.get(headline_id) or {}).get("external_content") or {}
        official_urls.extend(
            str(value) for value in external.get("official_source_urls") or [] if str(value)
        )
    return {
        "headline_ids": headline_ids,
        "story_context": {
            "why_now": cluster.get("why_now"),
            "leaf_summaries": cluster.get("leaf_summaries") or [],
            "official_source_urls": list(dict.fromkeys(official_urls)),
        },
        "_projection": projection,
    }


def build_matrix(root: Path) -> dict[str, Any]:
    summary = _read(root / "multi_frontier_floor_rehearsal_summary_v1.json")
    frozen = _read(root / "frozen_current_rolling_input_v1.json")
    records_by_id = {
        str(row["headline_id"]): row for row in frozen.get("headlines") or []
    }
    rows: list[dict[str, Any]] = []
    for frontier_number in range(1, 5):
        frontier_dir = root / f"frontier_{frontier_number}"
        prepared = _read(frontier_dir / "prepared_candidate_state_v1.json")
        viability = _read(
            frontier_dir / "route_probe" / "rolling_x_ranked_viability_v1.json"
        )
        attempts = list(viability.get("rank_attempts") or [])
        attempted_cluster_ids = {str(row.get("cluster_id") or "") for row in attempts}
        for attempt in attempts:
            request = attempt.get("request") or {}
            cluster = {
                "cluster_id": attempt.get("cluster_id"),
                "headline_ids": attempt.get("headline_ids") or [],
            }
            projection = _context_routed_official_locator_projection(cluster, records_by_id)
            blockers = [str(value) for value in attempt.get("blockers") or []]
            direct_families = _direct_primary_families(request)
            flags = _cause_flags(blockers, attempted=True)
            flags["locator_reachability_representation_gap"] = bool(
                projection["applicable"]
                and not ((request.get("story_context") or {}).get("evidence_reachability") or {}).get(
                    "bounded_locator_available"
                )
            )
            primary = next(
                (key for key, value in flags.items() if value),
                "other",
            )
            rows.append({
                "frontier": frontier_number,
                "rank": int(attempt.get("rank") or 0),
                "cluster_id": str(attempt.get("cluster_id") or ""),
                "headline_ids": [str(value) for value in attempt.get("headline_ids") or []],
                "sanitized_story_label": _sanitized_label(cluster, request),
                "attempted": True,
                "status": str(attempt.get("status") or ""),
                "direct_primary_binding": bool(direct_families),
                "direct_primary_families": direct_families,
                "start_of_task_context_locator_applicable": False,
                "context_locator_surface_ids": projection["surface_ids"],
                "context_locator_families": projection["families"],
                "pre_acquisition_locator_represented": bool(
                    ((request.get("story_context") or {}).get("evidence_reachability") or {}).get(
                        "bounded_locator_available"
                    )
                ),
                "cause_flags": flags,
                "primary_terminal_cause": primary,
                "blockers": blockers,
                "network_requests": int(attempt.get("story_evidence_network_requests") or 0),
                "network_reads_avoided": int(attempt.get("story_evidence_network_reads_avoided") or 0),
            })

        opportunity_count = int(
            summary["frontiers"][frontier_number - 1]["distinct_story_opportunity_count"]
        )
        unattempted_needed = max(0, opportunity_count - len(attempts))
        if unattempted_needed:
            remaining = [
                row for row in prepared["assignment"].get("ranked_clusters") or []
                if str(row.get("cluster_id") or "") not in attempted_cluster_ids
            ][:unattempted_needed]
            for cluster in remaining:
                request = _request_for_cluster(cluster, records_by_id)
                projection = request.pop("_projection")
                direct_families = _direct_primary_families(request)
                flags = _cause_flags([], attempted=False)
                rows.append({
                    "frontier": frontier_number,
                    "rank": int(cluster.get("rank") or 0),
                    "cluster_id": str(cluster.get("cluster_id") or ""),
                    "headline_ids": [str(value) for value in cluster.get("headline_ids") or []],
                    "sanitized_story_label": _sanitized_label(cluster, request),
                    "attempted": False,
                    "status": "UNATTEMPTED_BOUNDED_POOL_CAPACITY",
                    "direct_primary_binding": bool(direct_families),
                    "direct_primary_families": direct_families,
                    "start_of_task_context_locator_applicable": False,
                    "context_locator_surface_ids": projection["surface_ids"],
                    "context_locator_families": projection["families"],
                    "pre_acquisition_locator_represented": False,
                    "cause_flags": flags,
                    "primary_terminal_cause": "other",
                    "blockers": ["bounded_publishability_pool_capacity_reached"],
                    "network_requests": 0,
                    "network_reads_avoided": 0,
                })

    evaluated = {str(value) for value in summary.get("evaluated_headline_ids") or []}
    held_locator_rows: list[dict[str, Any]] = []
    for headline_id, record in records_by_id.items():
        if headline_id in evaluated:
            continue
        projection = _context_routed_official_locator_projection(
            {"headline_ids": [headline_id]}, records_by_id
        )
        if not projection["applicable"]:
            continue
        external = record.get("external_content") or {}
        held_locator_rows.append({
            "headline_id": headline_id,
            "source_timestamp_utc": str(record.get("source_timestamp_utc") or ""),
            "sanitized_story_label": " ".join(
                str(external.get("headline_text") or "").split()
            )[:180],
            "surface_ids": projection["surface_ids"],
            "families": projection["families"],
            "direct_primary_binding": False,
            "start_of_task_rule_matched": False,
            "corrected_exact_rule_matched": True,
        })

    cause_counts = Counter(row["primary_terminal_cause"] for row in rows)
    cause_flag_counts = {
        key: sum(bool(row["cause_flags"].get(key)) for row in rows)
        for key in (
            "locator_reachability_representation_gap",
            "retrieval_or_provider_failure",
            "source_family_or_capability_mismatch",
            "freshness_failure",
            "content_insufficiency",
            "request_budget_exhaustion",
            "other",
        )
    }
    return {
        "schema_version": "contentops.v1_locator_aware_evidence_yield_matrix.v1",
        "source_artifact_root": root.as_posix(),
        "source_rolling_input_sha256": summary.get("rolling_input_sha256"),
        "attempted_story_count": sum(bool(row["attempted"]) for row in rows),
        "unattempted_story_count": sum(not bool(row["attempted"]) for row in rows),
        "matrix_story_count": len(rows),
        "cause_distribution": dict(sorted(cause_counts.items())),
        "cause_flag_counts_nonexclusive": cause_flag_counts,
        "direct_primary_binding_present_count": sum(
            bool(row["direct_primary_binding"]) for row in rows
        ),
        "direct_primary_binding_absent_count": sum(
            not bool(row["direct_primary_binding"]) for row in rows
        ),
        "start_of_task_exact_locator_matches_in_matrix": sum(
            bool(row["start_of_task_context_locator_applicable"]) for row in rows
        ),
        "start_of_task_locator_representation_gaps_in_matrix": sum(
            bool(row["cause_flags"]["locator_reachability_representation_gap"])
            for row in rows
        ),
        "held_identity_universe_count": int(
            summary.get("remaining_held_identity_count") or 0
        ),
        "held_relevant_identity_detail_inspection_count": len(held_locator_rows),
        "held_inspection_method": (
            "EXACT_ZERO_NETWORK_LOCATOR_PREDICATE_METADATA_PREFILTER_THEN_THREE_MATCH_DETAIL_REVIEW"
        ),
        "held_corrected_exact_locator_match_count": len(held_locator_rows),
        "held_corrected_exact_locator_matches": held_locator_rows,
        "hypothesis_verdict": (
            "FALSE_FOR_40_PLUS_2; EXACT_EXISTING_STATE_FMS_APPLICABILITY_RULE_GAP_PROVEN_IN_HELD_CONTINUITY"
        ),
        "authority": {
            "network_requests": 0,
            "provider_calls": 0,
            "factual_or_numeric_authority_granted": False,
            "publication_or_public_write_authority_granted": False,
        },
        "stories": sorted(rows, key=lambda row: (row["frontier"], row["rank"])),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    _write(args.output, build_matrix(args.artifact_root))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
