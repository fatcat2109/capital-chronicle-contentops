"""Run one fresh canonical four-candidate evidence-only batch/tail proof.

The proof explicitly enables URL discovery while mechanically stopping before every writer,
article, derivative, browser, provider-write, and publication boundary.
"""
from __future__ import annotations

import argparse
from collections import Counter
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
from live_contentops.newsroom_production_day_v1 import newsroom_production_day_id
from live_contentops.quota_efficient_source_discovery_v1 import (
    DEVELOPMENT_PROOF_MAX_ACCOUNTED_TOKENS,
    DEVELOPMENT_PROOF_MAX_DETERMINISTIC_NETWORK_REQUESTS,
    DEVELOPMENT_PROOF_MAX_DISCOVERY_TURNS,
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
DEVELOPMENT_PROOF_BUDGET = {
    "max_batch_turns": DEVELOPMENT_PROOF_MAX_DISCOVERY_TURNS,
    "max_tail_turns": DEVELOPMENT_PROOF_MAX_DISCOVERY_TURNS,
    "max_total_turns": DEVELOPMENT_PROOF_MAX_DISCOVERY_TURNS,
    "max_accounted_tokens": DEVELOPMENT_PROOF_MAX_ACCOUNTED_TOKENS,
    "max_deterministic_network_requests": (
        DEVELOPMENT_PROOF_MAX_DETERMINISTIC_NETWORK_REQUESTS
    ),
    "max_locator_model_invocations": DEVELOPMENT_PROOF_MAX_DISCOVERY_TURNS,
    "max_deterministic_requests_per_candidate": 16,
}


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


def _ready_contract(evidence: Mapping[str, Any]) -> dict[str, Any]:
    tier = str(evidence.get("evidence_review_tier") or "")
    documents = {
        str(row.get("document_id") or row.get("evidence_id") or ""): dict(row)
        for row in evidence.get("evidence_documents") or []
        if isinstance(row, Mapping)
        and str(row.get("document_id") or row.get("evidence_id") or "")
    }
    blockers = [str(value) for value in evidence.get("blockers") or []]

    def accepted_document(document_id: str) -> bool:
        row = documents.get(document_id) or {}
        return bool(
            document_id
            and row.get("source_url")
            and (row.get("source_identity") or row.get("publisher"))
            and str(row.get("source_url") or "").startswith("https://")
            and (row.get("canonical_content_sha256") or row.get("raw_sha256"))
            and row.get("freshness_state") == "FRESH_CURRENT_OPERATOR_READINESS"
            and row.get("public_claim_allowed") is True
        )

    if tier == "ORDINARY_MINIMUM":
        packet = dict(evidence.get("minimum_trustworthy_evidence_packet") or {})
        document_id = str(packet.get("evidence_document_id") or "")
        passed = bool(
            packet.get("status") == "PASS"
            and packet.get("risk_tier") == "ORDINARY"
            and len(str(packet.get("core_factual_proposition") or "").strip()) >= 8
            and str(packet.get("source_url") or "").startswith("https://")
            and packet.get("evidence_packet_sha256")
            and accepted_document(document_id)
            and not blockers
        )
        return {
            "kind": "ORDINARY_MINIMUM_TRUSTWORTHY_EVIDENCE_PACKET",
            "status": "PASS" if passed else "BLOCKED",
            "contract_sha256": packet.get("evidence_packet_sha256"),
            "accepted_document_ids": [document_id] if document_id else [],
            "supported_claim_count": 0,
            "fabricated_claim_count": 0,
        }

    contract = dict(evidence.get("claim_evidence_contract") or {})
    supported = [
        dict(row)
        for row in contract.get("supported_claims") or []
        if isinstance(row, Mapping)
    ]
    document_ids = sorted(
        {
            str(document_id)
            for row in supported
            for document_id in row.get("evidence_document_ids") or []
            if str(document_id)
        }
    )
    passed = bool(
        tier == "ENHANCED"
        and contract.get("status") == "PASS"
        and int(contract.get("supported_claim_count") or 0) >= 1
        and int(contract.get("fabricated_claim_count") or 0) == 0
        and contract.get("claim_contract_sha256")
        and document_ids
        and all(accepted_document(document_id) for document_id in document_ids)
        and not blockers
    )
    return {
        "kind": "ENHANCED_CLAIM_EVIDENCE_CONTRACT",
        "status": "PASS" if passed else "BLOCKED",
        "contract_sha256": contract.get("claim_contract_sha256"),
        "accepted_document_ids": document_ids,
        "supported_claim_count": int(contract.get("supported_claim_count") or 0),
        "fabricated_claim_count": int(contract.get("fabricated_claim_count") or 0),
    }


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
        contract_acceptance = _ready_contract(evidence)
        accepted_document_ids = set(
            contract_acceptance.get("accepted_document_ids") or []
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
            and str(row.get("document_id") or row.get("evidence_id") or "")
            in accepted_document_ids
        ]
        candidates.append(
            {
                **candidate,
                "claim_contract_status": (
                    (evidence.get("claim_evidence_contract") or {}).get("status")
                ),
                "minimum_packet_status": (
                    (evidence.get("minimum_trustworthy_evidence_packet") or {}).get(
                        "status"
                    )
                ),
                "ready_contract_kind": contract_acceptance.get("kind"),
                "ready_contract_status": contract_acceptance.get("status"),
                "ready_contract_sha256": contract_acceptance.get(
                    "contract_sha256"
                ),
                "supported_claim_count": int(
                    contract_acceptance.get("supported_claim_count") or 0
                ),
                "fabricated_claim_count": int(
                    contract_acceptance.get("fabricated_claim_count") or 0
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
    host_runtime_required = bool(
        str(accounting.get("terminal_provider_blocker") or "")
        in host_runtime_failure_codes
    )
    batch_turns = int(accounting.get("batch_discovery_turns") or 0)
    tail_turns = int(accounting.get("tail_discovery_turns") or 0)
    total_turns = int(accounting.get("total_discovery_turns") or 0)
    discovery_tokens = int(accounting.get("accounted_discovery_tokens") or 0)
    deterministic_requests = int(
        accounting.get("deterministic_network_requests") or 0
    )
    locator_model_invocations = int(
        accounting.get("total_locator_model_invocations")
        or accounting.get("total_discovery_turns")
        or 0
    )
    distinct_candidate_ids = {
        str(row.get("cluster_id") or "") for row in candidates
    } - {""}
    candidate_contracts_pass = bool(
        len(candidates) >= 4
        and len(distinct_candidate_ids) >= 4
        and all(
            row.get("evidence_status") == "PASS"
            and row.get("ready_contract_status") == "PASS"
            and row.get("ready_contract_sha256")
            and row.get("freshness_pass") is True
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
        and batch_turns + tail_turns == total_turns
        and locator_model_invocations <= DEVELOPMENT_PROOF_MAX_DISCOVERY_TURNS
        and discovery_tokens <= DEVELOPMENT_PROOF_MAX_ACCOUNTED_TOKENS
        and deterministic_requests
        <= DEVELOPMENT_PROOF_MAX_DETERMINISTIC_NETWORK_REQUESTS
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
            "hard_token_ceiling": DEVELOPMENT_PROOF_MAX_ACCOUNTED_TOKENS,
            "deterministic_network_requests": deterministic_requests,
            "deterministic_network_request_ceiling": (
                DEVELOPMENT_PROOF_MAX_DETERMINISTIC_NETWORK_REQUESTS
            ),
            "unified_discovery_turn_ceiling": (
                DEVELOPMENT_PROOF_MAX_DISCOVERY_TURNS
            ),
            "locator_model_invocations": locator_model_invocations,
            "baseline_discovery_turns": BASELINE_TURNS,
            "baseline_accounted_discovery_tokens": BASELINE_TOKENS,
            "discovery_turn_delta": locator_model_invocations - BASELINE_TURNS,
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
    frozen_ids = {
        str(value) for value in rolling_input.get("unique_headline_ids") or [] if str(value)
    }
    production_day_id = newsroom_production_day_id(cutoff)
    runtime_output_dir.mkdir(parents=True, exist_ok=True)
    _write(runtime_output_dir / "frozen_current_rolling_input_v1.json", rolling_input)
    evaluated_headline_ids: set[str] = set()
    attempted_story_ids: set[str] = set()
    repeated_headline_ids: set[str] = set()
    repeated_story_ids: set[str] = set()
    ready_by_cluster: dict[str, dict[str, Any]] = {}
    prior_accounting: dict[str, Any] | None = None
    frontiers: list[dict[str, Any]] = []
    final_source_route_health = dict(source_route_health)
    termination_reason: str | None = None

    for frontier_number in range(1, DEVELOPMENT_PROOF_MAX_DISCOVERY_TURNS + 1):
        prepared_state = build_prepared_rolling_x_candidate_state(
            rolling_input=rolling_input,
            prepared_at_utc=cutoff,
            evaluated_headline_ids=sorted(evaluated_headline_ids),
            autonomous_source_discovery_available=True,
            source_route_health=final_source_route_health,
        )
        prepared_headline_ids = [
            str(value)
            for value in (
                (prepared_state.get("prepared_frontier") or {}).get(
                    "selected_headline_ids"
                )
                or (prepared_state.get("prepared_input") or {}).get(
                    "unique_headline_ids"
                )
                or []
            )
            if str(value)
        ]
        if not prepared_headline_ids:
            termination_reason = "NO_UNSEEN_PREPARED_CANDIDATES_REMAIN"
            break
        frontier_dir = runtime_output_dir / f"frontier_{frontier_number}"
        remaining_target = max(1, 4 - len(ready_by_cluster))
        remaining_after_frontier = frozen_ids.difference(evaluated_headline_ids).difference(
            prepared_headline_ids
        )
        prior_turn_count = int(
            (prior_accounting or {}).get("total_discovery_turns") or 0
        )
        prior_locator_attempt_count = len(
            (prior_accounting or {}).get("locator_attempts") or []
        )
        cycle_kwargs: dict[str, Any] = {
            "run_id": (
                "v1-quota-efficient-batch-tail-current-universe-proof-"
                f"frontier-{frontier_number}"
            ),
            "output_dir": frontier_dir,
            "cutoff_utc": cutoff,
            "rolling_input": rolling_input,
            "prepared_candidate_state": prepared_state,
            "publication_enabled": False,
            "operating_mode": "KILL_SWITCH",
            "autonomous_source_discovery_enabled": True,
            "evidence_only_target_count": remaining_target,
            "published_corpus": [],
            "cc_catalog": {"stores": [], "root_exists": False},
            "newsroom_production_day_id": production_day_id,
            "quota_discovery_budget": DEVELOPMENT_PROOF_BUDGET,
            "quota_discovery_fresh_unseen_available": bool(
                remaining_after_frontier
            ),
        }
        if final_source_route_health:
            cycle_kwargs["source_route_health"] = final_source_route_health
        if prior_accounting is not None:
            cycle_kwargs["quota_discovery_prior_accounting"] = prior_accounting
        cycle = run_rolling_x_newsroom_cycle(**cycle_kwargs)
        single_receipt = build_acceptance_receipt(
            cycle,
            cutoff_utc=cutoff,
            prepared_state=prepared_state,
            runtime_output_dir=frontier_dir,
        )
        _write(frontier_dir / "frontier_acceptance_receipt_v1.json", single_receipt)
        attempts = _attempts(cycle)
        frontier_story_ids = {
            str(row.get("cluster_id") or "") for row in attempts
        } - {""}
        frontier_headline_ids = {
            str(value)
            for row in attempts
            for value in row.get("headline_ids") or []
            if str(value)
        }
        repeated_story_ids.update(frontier_story_ids.intersection(attempted_story_ids))
        repeated_headline_ids.update(
            frontier_headline_ids.intersection(evaluated_headline_ids)
        )
        attempted_story_ids.update(frontier_story_ids)
        evaluated_headline_ids.update(frontier_headline_ids)
        new_ready_ids: list[str] = []
        for candidate in single_receipt.get("ready_candidates") or []:
            cluster_id = str(candidate.get("cluster_id") or "")
            if cluster_id and cluster_id not in ready_by_cluster:
                ready_by_cluster[cluster_id] = dict(candidate)
                new_ready_ids.append(cluster_id)
        current_accounting = cycle.get("quota_efficient_source_discovery")
        if isinstance(current_accounting, Mapping):
            prior_accounting = dict(current_accounting)
        frontier_turns = [
            {
                "turn_number": int(row.get("turn_number") or 0),
                "pass_kind": str(row.get("pass_kind") or ""),
                "candidate_story_count": int(
                    row.get("candidate_story_count") or 0
                ),
                "urls_resolved_count": int(
                    row.get("urls_resolved_count")
                    or row.get("resolved_story_count")
                    or 0
                ),
                "ready_candidate_gain": int(
                    row.get("ready_candidate_gain") or 0
                ),
                "accounted_discovery_tokens": int(
                    row.get("accounted_discovery_tokens") or 0
                ),
                "deterministic_network_requests": int(
                    row.get("deterministic_network_requests") or 0
                ),
                "marginal_url_yield": float(
                    row.get("marginal_url_yield") or 0.0
                ),
                "marginal_ready_yield": float(
                    row.get("marginal_ready_yield") or 0.0
                ),
                "status": str(row.get("status") or ""),
                "failure_code": row.get("failure_code"),
            }
            for row in (prior_accounting or {}).get("turns") or []
            if isinstance(row, Mapping)
            and int(row.get("turn_number") or 0) > prior_turn_count
        ]
        frontier_locator_attempts = [
            dict(row)
            for row in (prior_accounting or {}).get("locator_attempts") or []
            if isinstance(row, Mapping)
        ][prior_locator_attempt_count:]
        current_health = cycle.get("source_route_health")
        if isinstance(current_health, Mapping):
            final_source_route_health = dict(current_health)
        frontiers.append(
            {
                "frontier": frontier_number,
                "prepared_candidate_count": int(
                    prepared_state.get("prepared_candidate_count") or 0
                ),
                "prepared_headline_ids": prepared_headline_ids,
                "attempted_story_ids": sorted(frontier_story_ids),
                "attempted_headline_ids": sorted(frontier_headline_ids),
                "new_ready_candidate_ids": sorted(new_ready_ids),
                "ready_candidate_count_after_frontier": len(ready_by_cluster),
                "evaluated_distinct_story_count_after_frontier": len(
                    attempted_story_ids
                ),
                "evaluated_distinct_headline_count_after_frontier": len(
                    evaluated_headline_ids
                ),
                "remaining_unseen_headline_count_after_frontier": len(
                    frozen_ids.difference(evaluated_headline_ids)
                ),
                "discovery_turns": frontier_turns,
                "locator_attempts": frontier_locator_attempts,
                "abstentions": list(single_receipt.get("abstentions") or []),
                "exact_next_blocker": single_receipt.get("exact_remaining_blocker"),
                "cycle_evidence_path": str(
                    frontier_dir / "rolling_x_newsroom_cycle_evidence_v1.json"
                ),
                "cycle_evidence_sha256": single_receipt.get(
                    "runtime_cycle_evidence_sha256"
                ),
                "budget_before": dict(
                    (
                        (cycle_kwargs.get("quota_discovery_prior_accounting") or {}).get(
                            "remaining_budget"
                        )
                        or {
                            "batch_turns": DEVELOPMENT_PROOF_MAX_DISCOVERY_TURNS,
                            "tail_turns": DEVELOPMENT_PROOF_MAX_DISCOVERY_TURNS,
                            "total_turns": DEVELOPMENT_PROOF_MAX_DISCOVERY_TURNS,
                            "accounted_discovery_tokens": (
                                DEVELOPMENT_PROOF_MAX_ACCOUNTED_TOKENS
                            ),
                            "deterministic_network_requests": (
                                DEVELOPMENT_PROOF_MAX_DETERMINISTIC_NETWORK_REQUESTS
                            ),
                        }
                    )
                ),
                "budget_after": dict(
                    (prior_accounting or {}).get("remaining_budget") or {}
                ),
                "safety": dict(single_receipt.get("safety") or {}),
                "sourceability_parity": dict(
                    single_receipt.get("sourceability_parity") or {}
                ),
            }
        )
        if len(ready_by_cluster) >= 4:
            break
        if not frontier_headline_ids:
            termination_reason = "FRONTIER_PRODUCED_NO_EVALUATED_IDENTITIES"
            break
        if bool(
            (prior_accounting or {}).get("terminal_budget_blocker")
            or (prior_accounting or {}).get("terminal_provider_blocker")
        ):
            termination_reason = str(
                (prior_accounting or {}).get("terminal_budget_blocker")
                or (prior_accounting or {}).get("terminal_provider_blocker")
            )
            break

    accounting = dict(prior_accounting or {})
    ready_candidates = list(ready_by_cluster.values())
    batch_turns = int(accounting.get("batch_discovery_turns") or 0)
    tail_turns = int(accounting.get("tail_discovery_turns") or 0)
    total_turns = int(accounting.get("total_discovery_turns") or 0)
    discovery_tokens = int(accounting.get("accounted_discovery_tokens") or 0)
    deterministic_requests = int(
        accounting.get("deterministic_network_requests") or 0
    )
    locator_model_invocations = int(
        accounting.get("total_locator_model_invocations")
        or accounting.get("total_discovery_turns")
        or 0
    )
    host_runtime_required = bool(
        str(accounting.get("terminal_provider_blocker") or "")
        in {
            "CHATGPT_AUTH_REQUIRED_API_KEY_FALLBACK_FORBIDDEN",
            "OPENAI_CODEX_SDK_NOT_INSTALLED",
            "OPENAI_CODEX_SDK_VERSION_MISMATCH",
            "CODEX_MODEL_OR_EFFORT_UNAVAILABLE",
            "CHATGPT_USAGE_LIMIT_REACHED",
        }
    )
    safety_keys = (
        "writer_calls",
        "article_generation",
        "derivative_generation",
        "public_writes",
        "provider_write_calls",
        "unknown_write",
    )
    safety = {
        key: sum(int((row.get("safety") or {}).get(key) or 0) for row in frontiers)
        for key in safety_keys
    }
    safety.update(
        {
            "browser_or_cdp_publication_actions": 0,
            "automation_mutations": 0,
            "capital_chronicle_mutations": 0,
            "v2_mutations": 0,
            "secret_or_session_reads": 0,
        }
    )
    safety_pass = all(int(safety.get(key) or 0) == 0 for key in safety_keys)
    candidate_contracts_pass = bool(
        len(ready_candidates) >= 4
        and all(
            row.get("ready_contract_status") == "PASS"
            and row.get("ready_contract_sha256")
            and int(row.get("source_url_count") or 0) >= 1
            and int(row.get("fabricated_claim_count") or 0) == 0
            and not row.get("unresolved_blockers")
            for row in ready_candidates[:4]
        )
    )
    economics_pass = bool(
        accounting.get("status") == "PASS"
        and accounting.get("accounting_complete") is True
        and batch_turns + tail_turns == total_turns
        and locator_model_invocations <= DEVELOPMENT_PROOF_MAX_DISCOVERY_TURNS
        and discovery_tokens <= DEVELOPMENT_PROOF_MAX_ACCOUNTED_TOKENS
        and deterministic_requests
        <= DEVELOPMENT_PROOF_MAX_DETERMINISTIC_NETWORK_REQUESTS
    )
    identity_isolation_pass = not repeated_story_ids and not repeated_headline_ids
    classification = (
        HOST_PROOF_REQUIRED
        if host_runtime_required
        else PASS_CLASSIFICATION
        if candidate_contracts_pass
        and economics_pass
        and identity_isolation_pass
        and safety_pass
        else ECONOMICS_FAILURE
        if not economics_pass
        else "FAIL_V1_EVIDENCE_READY_POOL_NOT_ACCEPTED"
    )
    remaining_held_ids = sorted(frozen_ids.difference(evaluated_headline_ids))
    blocker_distribution = Counter(
        str(blocker)
        for frontier in frontiers
        for abstention in frontier.get("abstentions") or []
        if isinstance(abstention, Mapping)
        for blocker in abstention.get("blockers") or []
        if str(blocker)
    )
    per_turn_yield = [
        dict(turn)
        for frontier in frontiers
        for turn in frontier.get("discovery_turns") or []
        if isinstance(turn, Mapping)
    ]
    per_locator_yield = [
        dict(attempt)
        for frontier in frontiers
        for attempt in frontier.get("locator_attempts") or []
        if isinstance(attempt, Mapping)
    ]
    exact_blocker = None
    if classification != PASS_CLASSIFICATION:
        exact_blocker = (
            accounting.get("terminal_budget_blocker")
            or accounting.get("terminal_provider_blocker")
            or (
                "FRONTIER_IDENTITY_REPEATED"
                if not identity_isolation_pass
                else termination_reason
                or "FOUR_READY_TARGET_NOT_REACHED_AFTER_BOUNDED_PRODUCTION_DAY"
            )
        )
    receipt = {
        "schema_version": (
            "contentops.v1_quota_efficient_batch_tail_production_day_acceptance.v1"
        ),
        "classification": classification,
        "cutoff_utc": cutoff,
        "newsroom_production_day_id": production_day_id,
        "frozen_current_universe_sha256": _hash(rolling_input),
        "current_candidate_universe_count": len(frozen_ids),
        "frontier_count": len(frontiers),
        "termination_reason": termination_reason,
        "frontiers": frontiers,
        "evaluated_headline_ids": sorted(evaluated_headline_ids),
        "evaluated_headline_count": len(evaluated_headline_ids),
        "attempted_story_ids": sorted(attempted_story_ids),
        "repeated_headline_ids": sorted(repeated_headline_ids),
        "repeated_story_ids": sorted(repeated_story_ids),
        "remaining_held_headline_ids": remaining_held_ids,
        "remaining_held_identity_count": len(remaining_held_ids),
        "blocker_distribution": dict(sorted(blocker_distribution.items())),
        "ready_distinct_candidate_count": len(ready_candidates),
        "ready_candidates": ready_candidates,
        "discovery": accounting,
        "production_day_budget": {
            "consumed": {
                "batch_turns": batch_turns,
                "tail_turns": tail_turns,
                "total_turns": total_turns,
                "locator_model_invocations": locator_model_invocations,
                "accounted_discovery_tokens": discovery_tokens,
                "deterministic_network_requests": deterministic_requests,
            },
            "unused": dict(accounting.get("remaining_budget") or {}),
            "hard_ceiling": {
                "allocation": "COMPLETION_FIRST_ADAPTIVE_UNIFIED_TURN_POOL",
                "total_turns": DEVELOPMENT_PROOF_MAX_DISCOVERY_TURNS,
                "locator_model_invocations": DEVELOPMENT_PROOF_MAX_DISCOVERY_TURNS,
                "accounted_discovery_tokens": (
                    DEVELOPMENT_PROOF_MAX_ACCOUNTED_TOKENS
                ),
                "deterministic_network_requests": (
                    DEVELOPMENT_PROOF_MAX_DETERMINISTIC_NETWORK_REQUESTS
                ),
            },
        },
        "per_turn_yield": per_turn_yield,
        "per_locator_yield": per_locator_yield,
        "actual_consumption_at_fourth_ready_candidate": (
            {
                "batch_turns": batch_turns,
                "tail_turns": tail_turns,
                "total_turns": total_turns,
                "locator_model_invocations": locator_model_invocations,
                "accounted_discovery_tokens": discovery_tokens,
                "deterministic_network_requests": deterministic_requests,
            }
            if len(ready_candidates) >= 4
            else None
        ),
        "allocation_policy": {
            "completion_first": True,
            "stop_at_four_ready_candidates": True,
            "prefer_fresh_unseen_batches_while_marginal_url_yield_useful": True,
            "tail_requires_prior_url_and_concrete_access_failure": True,
            "sourceability_and_route_health_are_routing_only": True,
            "development_guardrail_is_not_production_budget": True,
        },
        "accepted_baseline_comparison": {
            "locator_model_invocations": locator_model_invocations,
            "baseline_discovery_turns": BASELINE_TURNS,
            "baseline_accounted_discovery_tokens": BASELINE_TOKENS,
            "discovery_turn_delta": locator_model_invocations - BASELINE_TURNS,
            "accounted_discovery_token_delta": discovery_tokens - BASELINE_TOKENS,
            "monetary_savings_claimed": False,
        },
        "source_route_health": final_source_route_health,
        "safety": safety,
        "checks": {
            "four_distinct_governed_candidates": len(ready_candidates) >= 4,
            "mode_risk_proportional_contracts_pass": candidate_contracts_pass,
            "production_day_shared_economics_pass": economics_pass,
            "frontier_identity_isolation_pass": identity_isolation_pass,
            "zero_writer_article_derivative_public_write": safety_pass,
            "model_output_is_never_evidence": accounting.get(
                "candidate_urls_are_evidence"
            )
            is False,
            "genuine_host_or_provider_dependency_unavailable": (
                host_runtime_required
            ),
        },
        "exact_remaining_blocker": exact_blocker,
    }
    receipt["receipt_sha256"] = _hash(receipt)
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
