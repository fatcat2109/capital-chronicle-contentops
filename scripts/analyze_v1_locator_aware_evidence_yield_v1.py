"""Build the exact sourceability/root-cause matrix for the failed 40-story day."""
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
from live_contentops.official_primary_evidence_loader_v1 import (
    OFFICIAL_HOSTS_BY_FAMILY,
)
from live_contentops.preselection_intelligence_v1 import _evidence_reachability
from live_contentops.public_secondary_evidence_loader_v1 import (
    REPUTABLE_SECONDARY_HOSTS,
)


KNOWN_PAYWALL_WAF_RISK_HOSTS = frozenset(
    {
        "bloomberg.com",
        "ft.com",
        "nytimes.com",
        "reuters.com",
        "wsj.com",
        "www.bloomberg.com",
        "www.ft.com",
        "www.nytimes.com",
        "www.reuters.com",
        "www.wsj.com",
    }
)


def _read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _urls(request: Mapping[str, Any]) -> list[str]:
    context = request.get("story_context") or {}
    return list(
        dict.fromkeys(
            str(value)
            for value in (
                list(context.get("public_source_urls") or [])
                + list(context.get("official_source_urls") or [])
                + [
                    row.get("url")
                    for row in (
                        list(context.get("public_source_url_bindings") or [])
                        + list(context.get("official_source_url_bindings") or [])
                    )
                    if isinstance(row, Mapping)
                ]
            )
            if str(value).startswith("https://")
        )
    )


def _hosts(urls: list[str]) -> list[str]:
    return sorted(
        {
            str(urlsplit(url).hostname or "").casefold()
            for url in urls
            if urlsplit(url).hostname
        }
    )


def _registered_official_families(hosts: list[str]) -> list[str]:
    host_set = set(hosts)
    return sorted(
        family
        for family, family_hosts in OFFICIAL_HOSTS_BY_FAMILY.items()
        if host_set.intersection(family_hosts)
    )


def _observations(hosts: list[str], blockers: list[str]) -> dict[str, Any]:
    text = " ".join(blockers).casefold()
    per_host: dict[str, dict[str, int]] = {}
    for host in hosts:
        row = {
            "http_401_count": int("401" in text),
            "http_403_count": int("403" in text),
            "http_404_count": int("404" in text),
            "paywall_count": int("paywall" in text),
            "waf_count": int("waf" in text or host in KNOWN_PAYWALL_WAF_RISK_HOSTS),
            "dead_link_count": int("dead-link" in text or "dead_link" in text),
            "successful_retrieval_count": 0,
        }
        if any(row.values()):
            per_host[host] = row
    return {"hosts": per_host}


def _access_classification(blockers: list[str], hosts: list[str]) -> list[str]:
    text = " ".join(blockers).casefold()
    values: list[str] = []
    for code in ("401", "403", "404"):
        if code in text:
            values.append("HTTP_" + code)
    if "paywall" in text:
        values.append("PAYWALL")
    if "waf" in text or set(hosts).intersection(KNOWN_PAYWALL_WAF_RISK_HOSTS):
        values.append("KNOWN_PAYWALL_OR_WAF_RISK")
    if "public_source_unavailable" in text:
        values.append("UNAVAILABLE_OR_NO_USABLE_BYTES")
    if "redirect_authority_invalid" in text:
        values.append("INVALID_CROSS_AUTHORITY_REDIRECT")
    if "nonpublic_address" in text:
        values.append("NONPUBLIC_ADDRESS_REJECTED")
    if "title_relevance" in text:
        values.append("TITLE_RELEVANCE_REJECTED")
    if not values:
        values.append("NO_EXPLICIT_TRANSPORT_FAILURE")
    return values


def _cause_flags(
    blockers: list[str], *, downstream_reason: str, attempted: bool
) -> dict[str, bool]:
    text = " ".join(blockers).casefold()
    return {
        "semantic_gate_input_contract_failure": (
            downstream_reason == "EDITORIAL_WORKER_REVISION_BUDGET_EXHAUSTED"
        ),
        "retrieval_or_access_failure": any(
            token in text
            for token in (
                "http error",
                "public_source_unavailable",
                "redirect_authority_invalid",
                "nonpublic_address",
                "paywall",
                "waf",
            )
        ),
        "freshness_failure": any(
            token in text
            for token in ("freshness", "after_evaluation_cutoff", "stale", "future")
        ),
        "request_budget_exhaustion": "budget" in text,
        "evidence_content_insufficiency": any(
            token in text
            for token in (
                "evidence_documents_missing",
                "minimum_trustworthy_evidence_missing",
                "supported_claims_missing",
                "relevant_text_unavailable",
            )
        ),
        "capability_mismatch_or_missing": "capability_missing" in text,
        "not_attempted": not attempted,
    }


def _primary_cause(flags: Mapping[str, bool]) -> str:
    for value in (
        "semantic_gate_input_contract_failure",
        "retrieval_or_access_failure",
        "freshness_failure",
        "request_budget_exhaustion",
        "evidence_content_insufficiency",
        "capability_mismatch_or_missing",
        "not_attempted",
    ):
        if flags.get(value):
            return value
    return "other"


def _network_and_model_economics(attempt: Mapping[str, Any]) -> dict[str, Any]:
    receipt = attempt.get("evidence_receipt") or {}
    provenance = receipt.get("evidence_acquisition_provenance") or {}
    grounded = provenance.get("grounded_research") or {}
    telemetry = [
        row for row in grounded.get("telemetry") or [] if isinstance(row, Mapping)
    ]
    return {
        "network_requests": int(attempt.get("story_evidence_network_requests") or 0),
        "network_reads_avoided": int(
            attempt.get("story_evidence_network_reads_avoided") or 0
        ),
        "public_retrieval_requests": int(grounded.get("public_retrieval_requests") or 0),
        "grounded_research_calls": int(grounded.get("research_calls") or 0),
        "grounded_research_tokens": int(
            sum(float((row.get("token_usage") or {}).get("total_tokens") or 0) for row in telemetry)
        ),
        "cost_receipt_present": any(bool(row.get("cost")) for row in telemetry),
    }


def _discovery_index(path: Path | None) -> dict[str, dict[str, Any]]:
    if path is None:
        return {}
    value = _read(path)
    return {
        str(row.get("cluster_id") or ""): dict(row)
        for row in value.get("cases") or []
        if isinstance(row, Mapping) and row.get("cluster_id")
    }


def _frontier_inputs(root: Path, frontier: int) -> tuple[dict[str, Any], dict[str, Any]]:
    if frontier == 4:
        directory = root / "frontier_4/canonical_zero_write_rehearsal_attempt_2"
    else:
        directory = root / f"frontier_{frontier}/route_probe"
    return (
        _read(directory / "rolling_x_ranked_viability_v1.json"),
        _read(directory / "rolling_x_newsroom_cycle_evidence_v1.json"),
    )


def build_matrix(root: Path, *, discovery_receipt_path: Path | None = None) -> dict[str, Any]:
    summary = _read(root / "multi_frontier_floor_rehearsal_summary_v1.json")
    frozen = _read(root / "frozen_current_rolling_input_v1.json")
    records_by_id = {
        str(row["headline_id"]): row for row in frozen.get("headlines") or []
    }
    discovery_by_cluster = _discovery_index(discovery_receipt_path)
    rows: list[dict[str, Any]] = []
    for frontier in range(1, 5):
        viability, cycle = _frontier_inputs(root, frontier)
        downstream_by_cluster = {
            str(row.get("cluster_id") or ""): dict(row)
            for row in (cycle.get("candidate_walk") or {}).get("candidate_attempts") or []
            if isinstance(row, Mapping)
        }
        for attempt in viability.get("rank_attempts") or []:
            request = attempt.get("request") or {}
            context = request.get("story_context") or {}
            cluster_id = str(attempt.get("cluster_id") or "")
            downstream = downstream_by_cluster.get(cluster_id, {})
            blockers = [str(value) for value in attempt.get("blockers") or []]
            urls = _urls(request)
            hosts = _hosts(urls)
            official_families = _registered_official_families(hosts)
            projection = _context_routed_official_locator_projection(
                {
                    "cluster_id": cluster_id,
                    "headline_ids": attempt.get("headline_ids") or [],
                },
                records_by_id,
            )
            receipt = attempt.get("evidence_receipt") or {}
            cc = receipt.get("capital_chronicle_publication_authority") or {}
            accepted_documents = [
                row
                for row in receipt.get("evidence_documents") or []
                if isinstance(row, Mapping)
            ]
            observed = _observations(hosts, blockers)
            current_sourceability = _evidence_reachability(
                {
                    **dict(context),
                    "story_type": request.get("story_type"),
                    "effective_article_mode": request.get("effective_article_mode"),
                },
                context.get("capital_chronicle_context") or {},
                sourceability_observations=observed,
            )
            prior_sourceability = dict(context.get("evidence_reachability") or {})
            required_capabilities = [
                str(value)
                for value in request.get("required_evidence_capabilities") or []
            ]
            obtained_capabilities = [
                str(value)
                for value in receipt.get("provided_evidence_capabilities") or []
            ]
            downstream_reason = str(downstream.get("terminal_reason") or "")
            flags = _cause_flags(
                blockers, downstream_reason=downstream_reason, attempted=True
            )
            discovery = discovery_by_cluster.get(cluster_id)
            if discovery and discovery.get("accepted_documents"):
                alternative_status = "DISCOVERED_URL_RETRIEVED_AND_ACCEPTED"
            elif discovery and discovery.get(
                "deterministically_retrieved_documents_before_truth_gates"
            ):
                alternative_status = "DISCOVERED_URL_RETRIEVED_BUT_TRUTH_GATE_REJECTED"
            elif accepted_documents:
                alternative_status = "EXISTING_DETERMINISTIC_DISCOVERY_ACCEPTED_SOURCE"
            else:
                alternative_status = "NOT_PROVEN_IN_BOUNDED_CODEX_SAMPLE"
            rows.append(
                {
                    "frontier": frontier,
                    "rank": int(attempt.get("rank") or 0),
                    "cluster_id": cluster_id,
                    "headline_ids": [
                        str(value) for value in attempt.get("headline_ids") or []
                    ],
                    "story_label": str(
                        downstream.get("candidate_title")
                        or context.get("why_now")
                        or "SANITIZED_STORY_LABEL_UNAVAILABLE"
                    ),
                    "story_type": str(
                        request.get("story_type") or "general_public_event"
                    ),
                    "capability_article_mode": str(
                        request.get("article_mode") or ""
                    ),
                    "status": str(attempt.get("status") or ""),
                    "downstream_terminal_reason": downstream_reason,
                    "mode_lineage": [
                        {
                            "requested_mode": row.get("requested_mode"),
                            "effective_mode": row.get("effective_mode"),
                            "acquisition_action": row.get("evidence_acquisition_action"),
                            "network_requests": int(
                                row.get("network_requests_performed") or 0
                            ),
                            "network_reads_avoided": int(
                                row.get("network_reads_avoided") or 0
                            ),
                            "status": row.get("status"),
                        }
                        for row in attempt.get("mode_attempts") or []
                        if isinstance(row, Mapping)
                    ],
                    "terminal_effective_mode": attempt.get("effective_article_mode"),
                    "source_urls": urls,
                    "source_hosts": hosts,
                    "registered_official_families": official_families,
                    "context_routed_official_families": list(
                        projection.get("families") or []
                    ),
                    "reputable_public_secondary_hosts": [
                        host for host in hosts if host in REPUTABLE_SECONDARY_HOSTS
                    ],
                    "capital_chronicle_governed_publication_packet": {
                        "state": cc.get("state"),
                        "authorized": cc.get("authorized") is True,
                        "packet_id": cc.get("packet_id"),
                        "packet_sha256": cc.get("packet_sha256"),
                    },
                    "direct_or_public_discovery_economics": _network_and_model_economics(
                        attempt
                    ),
                    "access_classification": _access_classification(blockers, hosts),
                    "required_evidence_capabilities": required_capabilities,
                    "obtained_evidence_capabilities": obtained_capabilities,
                    "missing_evidence_capabilities": sorted(
                        set(required_capabilities).difference(obtained_capabilities)
                    ),
                    "accepted_evidence_documents": [
                        {
                            "document_id": row.get("document_id"),
                            "publisher": row.get("publisher"),
                            "source_url": row.get("source_url"),
                            "published_at_utc": row.get("published_at_utc"),
                            "raw_sha256": row.get("raw_sha256"),
                            "canonical_content_sha256": row.get(
                                "canonical_content_sha256"
                            ),
                        }
                        for row in accepted_documents
                    ],
                    "accessible_alternative_public_source": {
                        "status": alternative_status,
                        "codex_search_call_id": (
                            discovery.get("search_call_id") if discovery else None
                        ),
                        "candidate_urls": (
                            discovery.get("codex_candidate_urls") if discovery else []
                        ),
                        "accepted_documents": (
                            discovery.get("accepted_documents") if discovery else []
                        ),
                    },
                    "expected_sourceability_before_expensive_acquisition": {
                        "before_score": prior_sourceability.get("score"),
                        "before_contract": prior_sourceability,
                        "after_score": current_sourceability.get("score"),
                        "after_contract": current_sourceability,
                    },
                    "cause_flags": flags,
                    "primary_terminal_cause": _primary_cause(flags),
                    "blockers": blockers,
                }
            )

    if len(rows) != 40:
        raise ValueError(f"exact_failed_story_count_invalid:{len(rows)}")

    evaluated = {str(value) for value in summary.get("evaluated_headline_ids") or []}
    held_candidates: list[dict[str, Any]] = []
    for headline_id, record in records_by_id.items():
        if headline_id in evaluated:
            continue
        external = record.get("external_content") or {}
        urls = [
            str(value)
            for value in external.get("official_source_urls") or []
            if str(value).startswith("https://")
        ]
        projection = _context_routed_official_locator_projection(
            {"headline_ids": [headline_id]}, records_by_id
        )
        held_candidates.append(
            {
                "headline_id": headline_id,
                "source_timestamp_utc": str(record.get("source_timestamp_utc") or ""),
                "story_label": " ".join(
                    str(external.get("headline_text") or "").split()
                )[:180],
                "source_urls": urls,
                "source_hosts": _hosts(urls),
                "registered_official_families": _registered_official_families(
                    _hosts(urls)
                ),
                "context_routed_surface_ids": list(projection.get("surface_ids") or []),
                "context_routed_families": list(projection.get("families") or []),
                "capital_chronicle_publication_packet_availability": "NOT_STORY_BOUND_OR_PROVEN",
                "network_requests": 0,
                "authority_granted": False,
            }
        )
    held_candidates.sort(
        key=lambda row: (
            -int(bool(row["context_routed_surface_ids"])),
            -int(bool(row["source_urls"])),
            str(row["source_timestamp_utc"]),
            str(row["headline_id"]),
        )
    )
    representative_held = held_candidates[:12]

    blocker_counts = Counter(
        blocker for row in rows for blocker in set(row.get("blockers") or [])
    )
    cause_counts = Counter(row["primary_terminal_cause"] for row in rows)
    flag_names = list(rows[0]["cause_flags"])
    flag_counts = {
        key: sum(bool(row["cause_flags"].get(key)) for row in rows)
        for key in flag_names
    }
    before_ranking = sorted(
        rows,
        key=lambda row: (
            -float(
                row["expected_sourceability_before_expensive_acquisition"].get(
                    "before_score"
                )
                or 0
            ),
            row["frontier"],
            row["rank"],
        ),
    )
    after_ranking = sorted(
        rows,
        key=lambda row: (
            -float(
                row["expected_sourceability_before_expensive_acquisition"].get(
                    "after_score"
                )
                or 0
            ),
            row["frontier"],
            row["rank"],
        ),
    )
    return {
        "schema_version": "contentops.v1_throughput_sourceability_failure_matrix.v1",
        "source_artifact_root": root.as_posix(),
        "source_rolling_input_sha256": summary.get("rolling_input_sha256"),
        "failed_story_count": len(rows),
        "held_identity_universe_count": int(
            summary.get("remaining_held_identity_count") or 0
        ),
        "primary_root_cause_distribution": dict(sorted(cause_counts.items())),
        "nonexclusive_root_cause_counts": flag_counts,
        "exact_terminal_blocker_distribution": dict(sorted(blocker_counts.items())),
        "mode_lineage_distribution": dict(
            sorted(
                Counter(
                    ">".join(
                        str(mode.get("effective_mode") or "")
                        for mode in row["mode_lineage"]
                    )
                    or str(row.get("terminal_effective_mode") or "")
                    for row in rows
                ).items()
            )
        ),
        "request_economics": {
            "network_requests": sum(
                row["direct_or_public_discovery_economics"]["network_requests"]
                for row in rows
            ),
            "network_reads_avoided": sum(
                row["direct_or_public_discovery_economics"]["network_reads_avoided"]
                for row in rows
            ),
            "public_retrieval_requests": sum(
                row["direct_or_public_discovery_economics"][
                    "public_retrieval_requests"
                ]
                for row in rows
            ),
            "grounded_research_calls": sum(
                row["direct_or_public_discovery_economics"]["grounded_research_calls"]
                for row in rows
            ),
            "grounded_research_tokens": sum(
                row["direct_or_public_discovery_economics"]["grounded_research_tokens"]
                for row in rows
            ),
            "cost_receipt_present": any(
                row["direct_or_public_discovery_economics"]["cost_receipt_present"]
                for row in rows
            ),
        },
        "sourceability_ranking_before_top_10": [
            {
                "cluster_id": row["cluster_id"],
                "frontier": row["frontier"],
                "rank": row["rank"],
                "score": row[
                    "expected_sourceability_before_expensive_acquisition"
                ].get("before_score"),
            }
            for row in before_ranking[:10]
        ],
        "sourceability_ranking_after_top_10": [
            {
                "cluster_id": row["cluster_id"],
                "frontier": row["frontier"],
                "rank": row["rank"],
                "score": row[
                    "expected_sourceability_before_expensive_acquisition"
                ].get("after_score"),
            }
            for row in after_ranking[:10]
        ],
        "representative_held_sample_method": (
            "ZERO_NETWORK_CONTEXT_ROUTE_AND_BOUND_URL_PRIORITY_THEN_STABLE_IDENTITY"
        ),
        "representative_held_sample_count": len(representative_held),
        "representative_held_candidates": representative_held,
        "authority": {
            "analysis_network_requests": 0,
            "analysis_provider_calls": 0,
            "factual_or_numeric_authority_granted": False,
            "publication_or_public_write_authority_granted": False,
        },
        "stories": sorted(rows, key=lambda row: (row["frontier"], row["rank"])),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-root", type=Path, required=True)
    parser.add_argument("--discovery-receipt", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    _write(
        args.output,
        build_matrix(
            args.artifact_root,
            discovery_receipt_path=args.discovery_receipt,
        ),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
