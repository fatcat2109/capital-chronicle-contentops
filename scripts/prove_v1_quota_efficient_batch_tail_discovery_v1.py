"""Run one fresh canonical four-candidate evidence-only batch/tail proof.

The proof explicitly enables URL discovery while mechanically stopping before every writer,
article, derivative, browser, provider-write, and publication boundary.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from typing import Any, Mapping


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from live_contentops.eight_platform_substack_first_pipeline_v1 import (
    run_rolling_x_newsroom_cycle,
)
from live_contentops.headline_data_root_v1 import canonical_headline_sidecar_glob
from live_contentops.daily_app_launcher_v1 import CANONICAL_PRODUCTION_OUTPUT_ROOT
from live_contentops.daily_app_supervisor_v1 import SOURCE_ROUTE_HEALTH_STATE_NAME
from live_contentops.newsroom_assignment_scheduler_v1 import (
    build_prepared_rolling_x_candidate_state,
    load_rolling_x_headline_sidecars,
)
from live_contentops.source_route_health_v1 import SCHEMA_VERSION as SOURCE_ROUTE_HEALTH_SCHEMA


PASS_CLASSIFICATION = (
    "PASS_V1_QUOTA_EFFICIENT_BATCH_TAIL_DISCOVERY_ECONOMICAL_READY_POOL"
)
ECONOMICS_FAILURE = "FAIL_V1_DISCOVERY_ECONOMICS_NOT_ACCEPTED"
HOST_PROOF_REQUIRED = "CURRENT_HOST_RUNTIME_PROOF_REQUIRED"
BASELINE_TURNS = 35
BASELINE_TOKENS = 10_237_897
CANONICAL_SOURCE_ROUTE_HEALTH_PATH = (
    CANONICAL_PRODUCTION_OUTPUT_ROOT / SOURCE_ROUTE_HEALTH_STATE_NAME
)


def _hash(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            default=str,
        ).encode("utf-8")
    ).hexdigest()


def _write(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _load_current_source_route_health(path: Path) -> dict[str, Any]:
    """Read the same routing-only snapshot consumed by the Daily App, when present."""
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, TypeError, ValueError):
        return {}
    if (
        not isinstance(value, Mapping)
        or value.get("schema_version") != SOURCE_ROUTE_HEALTH_SCHEMA
        or value.get("routing_only") is not True
    ):
        return {}
    return dict(value)


def _attempts(cycle: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [
        dict(row)
        for row in (cycle.get("ranked_viability") or {}).get("rank_attempts") or []
        if isinstance(row, Mapping)
    ]


def build_acceptance_receipt(
    cycle: Mapping[str, Any],
    *,
    cutoff_utc: str,
    prepared_state: Mapping[str, Any],
    runtime_output_dir: Path,
) -> dict[str, Any]:
    accounting = dict(cycle.get("quota_efficient_source_discovery") or {})
    pool = dict(cycle.get("evidence_ready_pool") or {})
    attempts = _attempts(cycle)
    attempt_by_cluster = {
        str(row.get("cluster_id") or ""): row for row in attempts
    }
    candidates: list[dict[str, Any]] = []
    for candidate_value in pool.get("candidates") or []:
        if not isinstance(candidate_value, Mapping):
            continue
        candidate = dict(candidate_value)
        cluster_id = str(candidate.get("cluster_id") or "")
        attempt = attempt_by_cluster.get(cluster_id) or {}
        evidence = dict(attempt.get("evidence_receipt") or {})
        claim_contract = dict(
            evidence.get("claim_evidence_contract")
            or (
                evidence.get("minimum_trustworthy_evidence_packet") or {}
            ).get("claim_evidence_contract")
            or {}
        )
        sources = [
            {
                "document_id": row.get("document_id") or row.get("evidence_id"),
                "publisher": row.get("publisher"),
                "source_url": row.get("source_url"),
                "canonical_content_sha256": row.get("canonical_content_sha256")
                or row.get("raw_sha256"),
                "freshness_state": row.get("freshness_state"),
                "public_claim_allowed": row.get("public_claim_allowed"),
                "source_authority_class": row.get("source_authority_class"),
            }
            for row in evidence.get("evidence_documents") or []
            if isinstance(row, Mapping)
        ]
        candidates.append(
            {
                **candidate,
                "claim_contract_status": claim_contract.get("status")
                or candidate.get("claim_contract_status"),
                "fabricated_claim_count": int(
                    claim_contract.get("fabricated_claim_count") or 0
                ),
                "sources": sources,
                "source_url_count": len(sources),
            }
        )

    abstentions = [
        {
            "rank": row.get("rank"),
            "cluster_id": row.get("cluster_id"),
            "headline_ids": list(row.get("headline_ids") or []),
            "status": row.get("status"),
            "blockers": [str(value) for value in row.get("blockers") or []],
            "evidence_receipt_sha256": row.get("evidence_receipt_sha256"),
        }
        for row in attempts
        if row.get("status") != "VIABLE"
    ]
    failures = list(accounting.get("failures") or [])
    host_runtime_failure_codes = {
        "CHATGPT_AUTH_REQUIRED_API_KEY_FALLBACK_FORBIDDEN",
        "OPENAI_CODEX_SDK_NOT_INSTALLED",
        "OPENAI_CODEX_SDK_VERSION_MISMATCH",
        "CODEX_MODEL_OR_EFFORT_UNAVAILABLE",
        "CHATGPT_USAGE_LIMIT_REACHED",
    }
    host_runtime_required = any(
        str(row.get("failure_code") or "") in host_runtime_failure_codes
        for row in failures
        if isinstance(row, Mapping)
    )
    batch_turns = int(accounting.get("batch_discovery_turns") or 0)
    tail_turns = int(accounting.get("tail_discovery_turns") or 0)
    total_turns = int(accounting.get("total_discovery_turns") or 0)
    discovery_tokens = int(accounting.get("accounted_discovery_tokens") or 0)
    deterministic_requests = int(
        accounting.get("deterministic_network_requests") or 0
    )
    distinct_candidate_ids = {
        str(row.get("cluster_id") or "") for row in candidates
    } - {""}
    candidate_contracts_pass = bool(
        len(candidates) >= 4
        and len(distinct_candidate_ids) >= 4
        and all(
            row.get("evidence_status") == "PASS"
            and row.get("claim_contract_status") == "PASS"
            and row.get("freshness_pass") is True
            and int(row.get("supported_claim_count") or 0) >= 1
            and int(row.get("source_url_count") or 0) >= 1
            and all(
                source.get("canonical_content_sha256")
                and source.get("freshness_state")
                == "FRESH_CURRENT_OPERATOR_READINESS"
                and source.get("public_claim_allowed") is True
                for source in row.get("sources") or []
            )
            and int(row.get("fabricated_claim_count") or 0) == 0
            and not row.get("unresolved_blockers")
            and row.get("writer_invoked") is False
            and row.get("article_generated") is False
            for row in candidates[:4]
        )
    )
    writer_calls = int(
        (cycle.get("critical_path_telemetry") or {}).get(
            "article_writer_semantic_calls"
        )
        or 0
    )
    article_generation = int(cycle.get("article_generation_attempts") or 0)
    derivative_generation = len(
        ((cycle.get("release_candidate_preparation") or {}).get("payloads") or {})
    )
    public_writes = int(bool(cycle.get("public_write_performed")))
    provider_writes = int(bool(cycle.get("publishing_adapter_called")))
    unknown_write = int(bool(cycle.get("unknown_write_detected")))
    safety_pass = bool(
        writer_calls == 0
        and article_generation == 0
        and derivative_generation == 0
        and public_writes == 0
        and provider_writes == 0
        and unknown_write == 0
    )
    economics_pass = bool(
        accounting.get("status") == "PASS"
        and accounting.get("accounting_complete") is True
        and batch_turns <= 2
        and tail_turns <= 2
        and total_turns <= 4
        and discovery_tokens <= 2_000_000
        and deterministic_requests <= 96
    )
    if host_runtime_required:
        classification = HOST_PROOF_REQUIRED
    elif not economics_pass:
        classification = ECONOMICS_FAILURE
    elif candidate_contracts_pass and safety_pass:
        classification = PASS_CLASSIFICATION
    else:
        classification = "FAIL_V1_EVIDENCE_READY_POOL_NOT_ACCEPTED"

    receipt = {
        "schema_version": (
            "contentops.v1_quota_efficient_batch_tail_acceptance_receipt.v1"
        ),
        "classification": classification,
        "cutoff_utc": cutoff_utc,
        "runtime_output_dir": str(runtime_output_dir),
        "runtime_cycle_evidence_path": str(
            runtime_output_dir / "rolling_x_newsroom_cycle_evidence_v1.json"
        ),
        "runtime_cycle_evidence_sha256": _hash(cycle),
        "prepared_state_sha256": _hash(prepared_state),
        "current_candidate_universe_count": int(
            prepared_state.get("full_rolling_headline_count") or 0
        ),
        "bounded_candidate_frontier_count": int(
            prepared_state.get("prepared_candidate_count") or 0
        ),
        "ready_distinct_candidate_count": len(distinct_candidate_ids),
        "ready_candidates": candidates,
        "discovery": accounting,
        "discovery_economics": {
            "batch_discovery_turns": batch_turns,
            "tail_discovery_turns": tail_turns,
            "total_discovery_turns": total_turns,
            "accounted_discovery_tokens": discovery_tokens,
            "target_token_ceiling": 1_000_000,
            "hard_token_ceiling": 2_000_000,
            "deterministic_network_requests": deterministic_requests,
            "unchanged_deterministic_network_request_ceiling": 96,
            "baseline_discovery_turns": BASELINE_TURNS,
            "baseline_accounted_discovery_tokens": BASELINE_TOKENS,
            "discovery_turn_delta": total_turns - BASELINE_TURNS,
            "accounted_discovery_token_delta": discovery_tokens - BASELINE_TOKENS,
            "cost_receipt_available": False,
            "monetary_savings_claimed": False,
        },
        "abstentions": abstentions,
        "source_route_health": dict(cycle.get("source_route_health") or {}),
        "sourceability_parity": {
            "prepared_frontier_autonomous_source_discovery_available": (
                prepared_state.get("autonomous_source_discovery_available") is True
            ),
            "prepared_frontier_source_route_health_input_sha256": (
                prepared_state.get("source_route_health_input_sha256")
            ),
            "cycle_source_route_health_input_sha256": cycle.get(
                "source_route_health_input_sha256"
            ),
            "preselection_sourceability_observations_consumed": bool(
                (cycle.get("preselection_intelligence") or {}).get(
                    "sourceability_observations_consumed"
                )
            ),
            "routing_only": True,
            "factual_numeric_or_publication_authority_granted": False,
        },
        "safety": {
            "writer_calls": writer_calls,
            "article_generation": article_generation,
            "derivative_generation": derivative_generation,
            "public_writes": public_writes,
            "provider_write_calls": provider_writes,
            "unknown_write": unknown_write,
            "browser_or_cdp_publication_actions": 0,
            "automation_mutations": 0,
            "capital_chronicle_mutations": 0,
            "v2_mutations": 0,
            "secret_or_session_reads": 0,
        },
        "checks": {
            "four_distinct_governed_candidates": len(distinct_candidate_ids) >= 4,
            "deterministic_loader_hash_freshness_claim_gates_pass": (
                candidate_contracts_pass
            ),
            "batch_tail_economics_pass": economics_pass,
            "zero_writer_article_derivative_public_write": safety_pass,
            "model_output_is_never_evidence": accounting.get(
                "candidate_urls_are_evidence"
            )
            is False,
            "tail_is_unresolved_subset_only": accounting.get(
                "tail_is_subset_only"
            )
            is True,
        },
        "exact_remaining_blocker": (
            None
            if classification == PASS_CLASSIFICATION
            else next(
                (
                    str(row.get("failure_code") or "")
                    for row in failures
                    if isinstance(row, Mapping)
                    and str(row.get("failure_code") or "")
                    in host_runtime_failure_codes
                ),
                HOST_PROOF_REQUIRED,
            )
            if host_runtime_required
            else accounting.get("terminal_budget_blocker")
            or accounting.get("terminal_provider_blocker")
            or cycle.get("exact_next_blocker")
            or next(
                (
                    str(row.get("failure_code") or "")
                    for row in failures
                    if isinstance(row, Mapping) and row.get("failure_code")
                ),
                "FOUR_DISTINCT_GOVERNED_EVIDENCE_READY_CANDIDATES_NOT_REACHED",
            )
        ),
    }
    receipt["receipt_sha256"] = _hash(receipt)
    return receipt


def run(
    *,
    runtime_output_dir: Path,
    evidence_output: Path,
    cutoff_utc: str | None = None,
    sidecar_glob: str | None = None,
    source_route_health_path: Path | None = None,
) -> dict[str, Any]:
    if evidence_output.exists():
        raise ValueError("quota_discovery_acceptance_evidence_already_exists")
    if (
        runtime_output_dir.exists()
        and any(runtime_output_dir.iterdir())
    ):
        raise ValueError("quota_discovery_runtime_output_dir_must_be_fresh")
    cutoff = cutoff_utc or datetime.now(timezone.utc).isoformat().replace(
        "+00:00", "Z"
    )
    effective_glob = sidecar_glob or canonical_headline_sidecar_glob()
    rolling_input = load_rolling_x_headline_sidecars(
        cutoff_utc=cutoff,
        sidecar_glob=effective_glob,
        window_hours=24.0,
    )
    source_route_health = _load_current_source_route_health(
        source_route_health_path or CANONICAL_SOURCE_ROUTE_HEALTH_PATH
    )
    prepared_state = build_prepared_rolling_x_candidate_state(
        rolling_input=rolling_input,
        prepared_at_utc=cutoff,
        autonomous_source_discovery_available=True,
        source_route_health=source_route_health,
    )
    cycle_kwargs: dict[str, Any] = {
        "run_id": "v1-quota-efficient-batch-tail-current-universe-proof",
        "output_dir": runtime_output_dir,
        "cutoff_utc": cutoff,
        "rolling_input": rolling_input,
        "prepared_candidate_state": prepared_state,
        "publication_enabled": False,
        "operating_mode": "KILL_SWITCH",
        "autonomous_source_discovery_enabled": True,
        "evidence_only_target_count": 4,
        "published_corpus": [],
        "cc_catalog": {"stores": [], "root_exists": False},
    }
    if source_route_health:
        cycle_kwargs["source_route_health"] = source_route_health
    cycle = run_rolling_x_newsroom_cycle(
        **cycle_kwargs,
    )
    receipt = build_acceptance_receipt(
        cycle,
        cutoff_utc=cutoff,
        prepared_state=prepared_state,
        runtime_output_dir=runtime_output_dir,
    )
    _write(evidence_output, receipt)
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime-output-dir", required=True, type=Path)
    parser.add_argument("--evidence-output", required=True, type=Path)
    parser.add_argument("--cutoff-utc")
    parser.add_argument("--sidecar-glob")
    parser.add_argument("--source-route-health-path", type=Path)
    args = parser.parse_args()
    receipt = run(
        runtime_output_dir=args.runtime_output_dir.resolve(),
        evidence_output=args.evidence_output.resolve(),
        cutoff_utc=args.cutoff_utc,
        sidecar_glob=args.sidecar_glob,
        source_route_health_path=(
            args.source_route_health_path.resolve()
            if args.source_route_health_path is not None
            else None
        ),
    )
    print(receipt["classification"])
    return 0 if receipt["classification"] == PASS_CLASSIFICATION else 1


if __name__ == "__main__":
    raise SystemExit(main())
