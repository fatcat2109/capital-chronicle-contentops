"""Aggregate bounded evidence-only opportunities into one production-day closeout receipt.

This offline verifier reads canonical cycle receipts only. It performs no retrieval, model call,
article generation, browser action, Capital Chronicle mutation, or public write.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence


SCHEMA_VERSION = "contentops.v1_evidence_foundation_closeout_receipt.v1"
ACCEPTANCE = "PASS_V1_EVIDENCE_FOUNDATION_4_ARTICLE_READY_ZERO_WRITER"
BASELINE = {
    "ready_candidate_count": 0,
    "network_requests": 110,
    "grounded_research_calls": 17,
    "grounded_research_prompt_tokens": 51553,
    "grounded_research_completion_tokens": 22184,
    "grounded_research_total_tokens": 73737,
}


def _sha256(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
            "utf-8"
        )
    ).hexdigest()


def _walk_key(value: Any, key: str) -> list[Any]:
    found: list[Any] = []
    if isinstance(value, Mapping):
        for child_key, child in value.items():
            if child_key == key:
                found.append(child)
            found.extend(_walk_key(child, key))
    elif isinstance(value, list):
        for child in value:
            found.extend(_walk_key(child, key))
    return found


def _attempts(cycle: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [
        dict(row)
        for row in (cycle.get("ranked_viability") or {}).get("rank_attempts") or []
        if isinstance(row, Mapping)
    ]


def _attempt_for_cluster(
    cycles: Sequence[Mapping[str, Any]], cluster_id: str
) -> Mapping[str, Any]:
    for cycle in cycles:
        for attempt in _attempts(cycle):
            if str(attempt.get("cluster_id") or "") == cluster_id:
                return attempt
    return {}


def _grounded_metrics(cycle: Mapping[str, Any]) -> dict[str, int]:
    calls = prompt = completion = total = 0
    for attempt in _attempts(cycle):
        provenance = dict(
            (attempt.get("evidence_receipt") or {}).get("evidence_acquisition_provenance")
            or {}
        )
        grounded = dict(provenance.get("grounded_research") or {})
        calls += int(grounded.get("research_calls") or 0)
        for row in grounded.get("telemetry") or []:
            if not isinstance(row, Mapping):
                continue
            usage = dict(row.get("token_usage") or {})
            prompt += int(usage.get("prompt_tokens") or 0)
            completion += int(usage.get("completion_tokens") or 0)
            total += int(usage.get("total_tokens") or 0)
    return {
        "calls": calls,
        "prompt_tokens": prompt,
        "completion_tokens": completion,
        "total_tokens": total,
    }


def _route_health_carry_forward(cycles: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Prove monotonic exact-route observations across opportunity snapshots."""
    best_shared = 0
    best_advanced = 0
    prior: dict[str, Mapping[str, Any]] = {}
    for cycle in cycles:
        rows = {
            str(row.get("route_identity_sha256") or ""): row
            for row in (cycle.get("source_route_health") or {}).get("routes") or []
            if isinstance(row, Mapping)
            and str(row.get("route_identity_sha256") or "")
        }
        if prior and rows:
            shared = set(prior).intersection(rows)
            advanced = {
                identity
                for identity in shared
                if sum(int(rows[identity].get(key) or 0) for key in ("success_count", "failure_count"))
                > sum(int(prior[identity].get(key) or 0) for key in ("success_count", "failure_count"))
            }
            best_shared = max(best_shared, len(shared))
            best_advanced = max(best_advanced, len(advanced))
        if rows:
            prior = rows
    explicit_input_hash = any(
        bool(cycle.get("source_route_health_input_sha256"))
        or bool(
            (cycle.get("prepared_candidate_state") or {}).get(
                "source_route_health_input_sha256"
            )
        )
        for cycle in cycles[1:]
    )
    return {
        "demonstrated": explicit_input_hash or (best_shared > 0 and best_advanced > 0),
        "explicit_input_hash_observed": explicit_input_hash,
        "maximum_shared_exact_routes_between_opportunities": best_shared,
        "maximum_advanced_exact_routes_between_opportunities": best_advanced,
    }


def build_closeout_receipt(
    cycles: Sequence[Mapping[str, Any]],
    *,
    excluded_candidate_clusters: Sequence[str] = (),
) -> dict[str, Any]:
    if not cycles:
        raise ValueError("evidence_foundation_cycle_receipts_missing")
    excluded = {str(value) for value in excluded_candidate_clusters if str(value)}
    candidates: list[dict[str, Any]] = []
    seen: set[str] = set()
    for cycle_index, cycle in enumerate(cycles, start=1):
        pool = dict(cycle.get("evidence_ready_pool") or {})
        for candidate_value in pool.get("candidates") or []:
            candidate = dict(candidate_value)
            cluster_id = str(candidate.get("cluster_id") or "")
            if not cluster_id or cluster_id in seen or cluster_id in excluded:
                continue
            seen.add(cluster_id)
            attempt = _attempt_for_cluster(cycles, cluster_id)
            documents = [
                dict(row)
                for row in (attempt.get("evidence_receipt") or {}).get(
                    "evidence_documents"
                )
                or []
                if isinstance(row, Mapping)
            ]
            candidate["production_day_opportunity_index"] = cycle_index
            candidate["sources"] = [
                {
                    "document_id": row.get("document_id"),
                    "publisher": row.get("publisher"),
                    "source_url": row.get("source_url"),
                    "canonical_content_sha256": row.get("canonical_content_sha256")
                    or row.get("raw_sha256"),
                    "freshness_state": row.get("freshness_state"),
                }
                for row in documents
            ]
            candidates.append(candidate)

    request_counts = [
        max(
            [int(value) for value in _walk_key(cycle.get("ranked_viability") or {}, "request_count_total")]
            or [0]
        )
        for cycle in cycles
    ]
    grounded_rows = [_grounded_metrics(cycle) for cycle in cycles]
    discovery_receipts: list[dict[str, Any]] = []
    abstentions: list[dict[str, Any]] = []
    health_suppression_observed = False
    for opportunity_index, cycle in enumerate(cycles, start=1):
        for attempt in _attempts(cycle):
            receipt = dict(attempt.get("evidence_receipt") or {})
            discovery = dict(receipt.get("autonomous_source_discovery") or {})
            if discovery:
                discovery_receipts.append(
                    {
                        "opportunity_index": opportunity_index,
                        "cluster_id": attempt.get("cluster_id"),
                        "status": discovery.get("status"),
                        "story_identity": discovery.get("story_identity"),
                        "resumed_story_identity": discovery.get("resumed_story_identity"),
                        "same_candidate_resumed": discovery.get("same_candidate_resumed"),
                        "search_text_grants_authority": discovery.get(
                            "search_snippet_or_model_summary_authority"
                        ),
                        "provider_receipt": discovery.get("provider_receipt"),
                        "deterministic_document_hashes": sorted(
                            str(row.get("canonical_content_sha256") or row.get("raw_sha256") or "")
                            for row in receipt.get("evidence_documents") or []
                            if isinstance(row, Mapping)
                            and str(row.get("canonical_content_sha256") or row.get("raw_sha256") or "")
                        ),
                    }
                )
            blockers = [str(value) for value in attempt.get("blockers") or []]
            health_suppression_observed = health_suppression_observed or any(
                "route_suppressed_by_recent_health" in value for value in blockers
            )
            if str(attempt.get("status") or "") != "VIABLE":
                abstentions.append(
                    {
                        "opportunity_index": opportunity_index,
                        "cluster_id": attempt.get("cluster_id"),
                        "blockers": blockers,
                    }
                )

    required_candidate_checks = all(
        candidate.get("evidence_status") == "PASS"
        and candidate.get("claim_contract_status") == "PASS"
        and candidate.get("freshness_pass") is True
        and int(candidate.get("supported_claim_count") or 0) >= 1
        and bool(candidate.get("evidence_document_hashes"))
        and not candidate.get("unresolved_blockers")
        and candidate.get("writer_invoked") is False
        and candidate.get("article_generated") is False
        for candidate in candidates[:4]
    )
    zero_write_checks = all(
        int(cycle.get("article_generation_attempts") or 0) == 0
        and int(cycle.get("editorial_worker_count_invoked") or 0) == 0
        and int(cycle.get("xhigh_worker_invocations") or 0) == 0
        and cycle.get("public_write_performed") is False
        and cycle.get("unknown_write_detected") is False
        and cycle.get("publishing_adapter_called") is False
        for cycle in cycles
    )
    discovery_demonstrated = any(
        row.get("status") == "SAME_CANDIDATE_RESUMED"
        and row.get("same_candidate_resumed") is True
        and row.get("story_identity") == row.get("resumed_story_identity")
        and row.get("search_text_grants_authority") is False
        for row in discovery_receipts
    )
    health_carry_forward = _route_health_carry_forward(cycles)
    route_health_reused = bool(health_carry_forward["demonstrated"]) and health_suppression_observed
    day_request_budget = 24 * len(cycles)
    total_requests = sum(request_counts)
    accepted = (
        len(candidates) >= 4
        and len({row["cluster_id"] for row in candidates[:4]}) == 4
        and required_candidate_checks
        and zero_write_checks
        and discovery_demonstrated
        and route_health_reused
        and total_requests <= day_request_budget
    )
    discovery_tokens = sum(
        int(((row.get("provider_receipt") or {}).get("turn_result_usage") or {}).get("total_tokens") or 0)
        for row in discovery_receipts
    )
    grounded = {
        key: sum(row[key] for row in grounded_rows)
        for key in ("calls", "prompt_tokens", "completion_tokens", "total_tokens")
    }
    receipt = {
        "schema_version": SCHEMA_VERSION,
        "classification": ACCEPTANCE if accepted else "EVIDENCE_FOUNDATION_NOT_ACCEPTED",
        "production_day_opportunity_count": len(cycles),
        "current_candidate_universe_count": max(
            int((cycle.get("critical_path_telemetry") or {}).get("full_rolling_headline_count") or 0)
            for cycle in cycles
        ),
        "ready_candidate_count": len(candidates),
        "ready_candidates": candidates,
        "excluded_semantic_duplicate_clusters": sorted(excluded),
        "bounded_economics": {
            "per_opportunity_request_ceiling": 24,
            "production_day_request_ceiling": day_request_budget,
            "network_requests_by_opportunity": request_counts,
            "network_requests": total_requests,
            "accepted_evidence_yield_per_request": round(len(candidates) / total_requests, 6)
            if total_requests
            else None,
            "grounded_research_calls": grounded["calls"],
            "grounded_research_prompt_tokens": grounded["prompt_tokens"],
            "grounded_research_completion_tokens": grounded["completion_tokens"],
            "grounded_research_total_tokens": grounded["total_tokens"],
            "url_discovery_calls": len(discovery_receipts),
            "url_discovery_total_tokens": discovery_tokens,
            "cost_receipt_available": False,
            "cost_savings_claimed": False,
            "baseline_55b": BASELINE,
        },
        "autonomous_discovery": {
            "demonstrated": discovery_demonstrated,
            "receipts": discovery_receipts,
            "candidate_urls_are_evidence": False,
            "deterministic_retrieval_and_hash_required": True,
        },
        "source_route_health": {
            "reused_across_opportunities": route_health_reused,
            "recent_exact_route_suppression_observed": health_suppression_observed,
            "carry_forward_proof": health_carry_forward,
            "routing_only": True,
            "authority_granted": False,
        },
        "abstentions": abstentions,
        "safety": {
            "writer_or_article_invocations": 0 if zero_write_checks else None,
            "public_writes": 0 if zero_write_checks else None,
            "unknown_write": 0 if zero_write_checks else None,
            "capital_chronicle_mutations": 0,
            "browser_or_cdp_uses": 0,
        },
        "checks": {
            "four_distinct_governed_candidates": len(candidates) >= 4,
            "candidate_contracts_pass": required_candidate_checks,
            "zero_writer_article_public_write": zero_write_checks,
            "autonomous_same_candidate_discovery_resume": discovery_demonstrated,
            "source_route_health_reuse": route_health_reused,
            "within_unchanged_production_day_request_economics": total_requests
            <= day_request_budget,
        },
    }
    receipt["receipt_sha256"] = _sha256(receipt)
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cycle", action="append", required=True, type=Path)
    parser.add_argument(
        "--exclude-cluster",
        action="append",
        default=[],
        help="Exclude a conservatively adjudicated semantic duplicate cluster from ready yield.",
    )
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    cycles = [json.loads(path.read_text(encoding="utf-8")) for path in args.cycle]
    receipt = build_closeout_receipt(
        cycles,
        excluded_candidate_clusters=args.exclude_cluster,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(receipt, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(receipt["classification"])
    return 0 if receipt["classification"] == ACCEPTANCE else 1


if __name__ == "__main__":
    raise SystemExit(main())
