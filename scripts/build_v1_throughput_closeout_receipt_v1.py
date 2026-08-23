"""Build the exact zero-write V1 throughput closeout receipt from committed evidence."""
from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
from typing import Any, Iterable, Mapping

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

TASK = "TASK_V1_THROUGHPUT_SOURCEABILITY_GROUNDED_DISCOVERY_AND_SEMANTIC_GATE_CLOSEOUT_V1"
EVIDENCE_ROOT = ROOT / "docs" / "automation" / TASK


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"artifact_not_object:{path}")
    return value


def _logical_hash(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            default=str,
        ).encode("utf-8")
    ).hexdigest()


def _file_hash(path: Path) -> str:
    raw = path.read_bytes()
    # Git's text attribute normalizes CRLF checkout bytes to LF in the committed blob.
    # Evidence hashes must identify the committed form, not a workstation-specific checkout.
    if path.suffix.casefold() in {".json", ".md", ".py", ".txt"}:
        raw = raw.replace(b"\r\n", b"\n")
    return hashlib.sha256(raw).hexdigest()


def _model_economics(paths: Iterable[Path]) -> dict[str, int]:
    calls = prompt_tokens = completion_tokens = total_tokens = 0
    story_requests = reads_avoided = 0
    for path in paths:
        viability = _load(path)
        for attempt in viability.get("rank_attempts") or []:
            story_requests += int(attempt.get("story_evidence_network_requests") or 0)
            reads_avoided += int(attempt.get("story_evidence_network_reads_avoided") or 0)
            grounded = dict(
                (
                    (attempt.get("evidence_receipt") or {}).get(
                        "evidence_acquisition_provenance"
                    )
                    or {}
                ).get("grounded_research")
                or {}
            )
            calls += int(grounded.get("research_calls") or 0)
            for row in grounded.get("telemetry") or []:
                usage = dict(row.get("token_usage") or {})
                prompt_tokens += int(usage.get("prompt_tokens") or 0)
                completion_tokens += int(usage.get("completion_tokens") or 0)
                total_tokens += int(usage.get("total_tokens") or 0)
    return {
        "story_scoped_network_requests": story_requests,
        "story_scoped_network_reads_avoided": reads_avoided,
        "grounded_research_calls": calls,
        "grounded_research_prompt_tokens": prompt_tokens,
        "grounded_research_completion_tokens": completion_tokens,
        "grounded_research_total_tokens": total_tokens,
    }


def build() -> dict[str, Any]:
    failed_path = EVIDENCE_ROOT / "failed_40_sourceability_root_cause_matrix_v1.json"
    semantic_path = EVIDENCE_ROOT / "semantic_contract_exact_replay_v1.json"
    discovery_path = EVIDENCE_ROOT / "codex_url_discovery_recovery_v1.json"
    cc_path = EVIDENCE_ROOT / "cc_publication_interop_audit_v1.json"
    cc_requirements_path = EVIDENCE_ROOT / "CC_CONTENTOPS_PUBLICATION_INTEROP_REQUIREMENTS_V1.md"
    frozen_path = EVIDENCE_ROOT / "frozen_counterfactual_replay_receipt_v1.json"
    fresh_root = EVIDENCE_ROOT / "fresh_current_4_32_zero_write_rehearsal"
    fresh_summary_path = fresh_root / "multi_frontier_floor_rehearsal_summary_v1.json"
    fresh_ledger_path = fresh_root / "candidate_blocker_ledger_v1.json"

    failed = _load(failed_path)
    semantic = _load(semantic_path)
    discovery = _load(discovery_path)
    cc_audit = _load(cc_path)
    frozen = _load(frozen_path)
    fresh = _load(fresh_summary_path)
    fresh_ledger = _load(fresh_ledger_path)

    if (
        int(failed.get("failed_story_count") or 0) != 40
        or int(fresh.get("frontier_count") or 0) != 4
        or int(fresh_ledger.get("candidate_count") or 0) != 40
    ):
        raise ValueError("closeout_exact_universe_invariant_failed")
    if fresh.get("pending_frontier"):
        raise ValueError("fresh_rehearsal_not_terminal")

    evidence_blockers: Counter[str] = Counter()
    writer_blockers: Counter[str] = Counter()
    terminal_reasons: Counter[str] = Counter()
    for frontier in fresh_ledger.get("frontiers") or []:
        for candidate in frontier.get("candidates") or []:
            evidence_blockers.update(candidate.get("evidence_blockers") or [])
            writer_blockers.update(candidate.get("writer_blockers") or [])
            terminal_reasons[str(candidate.get("terminal_reason") or "UNKNOWN")] += 1

    final_viability_paths = [
        fresh_root
        / "frontier_1"
        / "canonical_zero_write_rehearsal_attempt_2"
        / "rolling_x_ranked_viability_v1.json",
        *[
            fresh_root
            / f"frontier_{number}"
            / "route_probe"
            / "rolling_x_ranked_viability_v1.json"
            for number in range(2, 5)
        ],
    ]
    all_viability_paths = sorted(
        fresh_root.glob("frontier_*/**/rolling_x_ranked_viability_v1.json")
    )
    final_model_economics = _model_economics(final_viability_paths)
    total_execution_economics = _model_economics(all_viability_paths)

    prior_economics = dict(failed.get("request_economics") or {})
    final_network_requests = int(fresh.get("story_scoped_network_request_total") or 0)
    prior_network_requests = int(prior_economics.get("network_requests") or 0)
    request_delta = final_network_requests - prior_network_requests
    request_delta_fraction = (
        request_delta / prior_network_requests if prior_network_requests else None
    )

    qualified_records = list(fresh.get("qualified_article_records") or [])
    derivative_intents = [
        intent
        for record in qualified_records
        for intent in record.get("derivative_package_intents") or []
    ]
    frontier_results = [
        {
            "frontier": row.get("frontier"),
            "classification": row.get("result_classification"),
            "exact_next_blocker": row.get("exact_next_blocker"),
            "attempted_distinct_candidate_count": row.get(
                "attempted_distinct_candidate_count"
            ),
            "public_requests": row.get("public_request_total"),
            "official_requests": row.get("official_request_total"),
            "worker_return_sha256": row.get("worker_return_sha256"),
            "bounded_revision_count": int(row.get("bounded_revision_count") or 0),
        }
        for row in fresh.get("frontiers") or []
    ]

    receipt = {
        "schema_version": "contentops.v1_throughput_sourceability_closeout_receipt.v1",
        "task": TASK,
        "classification": "DEGRADED_DAILY_OUTPUT_DEFICIT",
        "target_classification": "PASS_V1_THROUGHPUT_SOURCEABILITY_AND_4_32_CLOSEOUT",
        "target_classification_earned": False,
        "cc_producer_authority_gap_is_only_remaining_blocker": False,
        "failed_40_root_cause": {
            "failed_story_count": failed.get("failed_story_count"),
            "held_identity_universe_count": failed.get("held_identity_universe_count"),
            "primary_distribution": failed.get("primary_root_cause_distribution"),
            "nonexclusive_distribution": failed.get("nonexclusive_root_cause_counts"),
            "exact_terminal_blockers": failed.get("exact_terminal_blocker_distribution"),
            "mode_lineage_distribution": failed.get("mode_lineage_distribution"),
        },
        "sourceability_ranking": {
            "before_top_10": failed.get("sourceability_ranking_before_top_10"),
            "after_top_10": failed.get("sourceability_ranking_after_top_10"),
            "ranking_grants_factual_numeric_cc_or_publication_authority": False,
        },
        "semantic_gate": {
            "before": semantic.get("before"),
            "after": {
                key: value
                for key, value in dict(semantic.get("after") or {}).items()
                if key != "semantic_review_receipt"
            },
            "ownership_reconciliation": semantic.get("ownership_reconciliation"),
            "receipt_sha256": semantic.get("receipt_sha256"),
        },
        "codex_url_discovery": {
            "economics": discovery.get("economics"),
            "recovered_case_count": discovery.get("recovered_case_count"),
            "deterministically_retrieved_document_count": discovery.get(
                "deterministically_retrieved_document_count"
            ),
            "deterministically_accepted_document_count": discovery.get(
                "deterministically_accepted_document_count"
            ),
            "accepted_raw_sha256": discovery.get("accepted_raw_sha256"),
            "accepted_canonical_content_sha256": discovery.get(
                "accepted_canonical_content_sha256"
            ),
            "browser_cdp": discovery.get("browser_cdp"),
            "candidate_urls_are_evidence": False,
        },
        "capital_chronicle_interop": {
            "upstream_authority": cc_audit.get("upstream_authority"),
            "coverage": cc_audit.get("coverage"),
            "expected_utility": cc_audit.get("expected_utility"),
            "requirements_packet_path": str(cc_requirements_path),
            "requirements_packet_sha256": _file_hash(cc_requirements_path),
            "capital_chronicle_mutated": False,
        },
        "frozen_counterfactual_replay": {
            "replay_kind": frozen.get("replay_kind"),
            "frozen_universe": frozen.get("frozen_universe"),
            "canonical_replay_result": frozen.get("canonical_replay_result"),
            "economics": frozen.get("economics"),
            "safety": frozen.get("safety"),
            "receipt_sha256": frozen.get("receipt_sha256"),
        },
        "fresh_current_four_opportunity_rehearsal": {
            "input_mode": fresh.get("input_mode"),
            "rolling_input_sha256": fresh.get("rolling_input_sha256"),
            "frontier_count": fresh.get("frontier_count"),
            "frontiers": frontier_results,
            "attempted_distinct_story_count": fresh.get(
                "attempted_distinct_story_count"
            ),
            "qualified_count": fresh.get("qualified_count"),
            "qualified_article_records": qualified_records,
            "qualified_article_hashes": [
                str(record.get("article_body_sha256") or "")
                for record in qualified_records
            ],
            "qualified_derivative_intent_count": fresh.get(
                "qualified_derivative_intent_count"
            ),
            "derivative_intent_hashes": [
                str(intent.get("payload_sha256") or "") for intent in derivative_intents
            ],
            "remaining_build_deficit": fresh.get("remaining_build_deficit"),
            "remaining_held_identity_count": fresh.get(
                "remaining_held_identity_count"
            ),
            "xhigh_attempt_count": fresh.get("xhigh_attempt_count"),
            "xhigh_worker_return_count": fresh.get("xhigh_worker_return_count"),
            "xhigh_revision_count": fresh.get("xhigh_revision_count"),
            "all_abstentions": {
                "candidate_count": fresh_ledger.get("candidate_count"),
                "terminal_reason_distribution": dict(terminal_reasons),
                "evidence_blocker_distribution": dict(evidence_blockers),
                "writer_blocker_distribution": dict(writer_blockers),
                "candidate_blocker_ledger_sha256": fresh_ledger.get("ledger_sha256"),
            },
        },
        "economics_before_vs_after": {
            "failed_day": prior_economics,
            "fresh_final_four_opportunity_accounting": {
                "network_requests": final_network_requests,
                "public_retrieval_requests": sum(
                    int(row.get("public_request_total") or 0)
                    for row in fresh.get("frontiers") or []
                ),
                "official_requests": sum(
                    int(row.get("official_request_total") or 0)
                    for row in fresh.get("frontiers") or []
                ),
                "network_reads_avoided": fresh.get(
                    "story_scoped_network_reads_avoided"
                ),
                **final_model_economics,
                "xhigh_worker_tokens": "NOT_EXPOSED",
                "cost_receipt_present": False,
            },
            "network_request_delta": request_delta,
            "network_request_delta_fraction": request_delta_fraction,
            "total_execution_including_preserved_debug_attempts": {
                **total_execution_economics,
                "viability_artifact_count": len(all_viability_paths),
            },
        },
        "safety": {
            "public_writes": fresh.get("public_write_count"),
            "unknown_write": fresh.get("unknown_write_count"),
            "publication_provider_writes": 0,
            "fifth_routine_window_created": 0,
            "automation_enabled": False,
            "capital_chronicle_mutated": False,
            "branding_touched": False,
            "master_merged": False,
        },
        "exact_residual_blockers": [
            {
                "code": "EVIDENCE_REQUEST_BUDGET_EXHAUSTED_BEFORE_PUBLISHABILITY_POOL_CLOSURE",
                "frontier_count": 3,
                "detail": "Frontiers 2-4 ended before any evidence-viable editorial dispatch.",
            },
            {
                "code": "DESKTOP_EDITORIAL_WORKER_ARTICLE_RETURN_CONTRACT_INVALID_AFTER_ONE_BOUNDED_REVISION",
                "frontier_count": 1,
                "detail": (
                    "The sole evidence-viable story's XHIGH worker supplied prose under "
                    "editorial_output rather than the required article object; the canonical "
                    "builder therefore remained fail-closed after the one permitted same-worker revision."
                ),
            },
            {
                "code": "NO_EXACT_CURRENT_CC_PUBLICATION_PACKET_COVERAGE",
                "frontier_count": 4,
                "detail": (
                    "Current CC packet coverage was 0/40 failed stories and 0/453 held identities, "
                    "but this was not the only residual blocker."
                ),
            },
        ],
        "source_artifact_sha256": {
            path.relative_to(ROOT).as_posix(): _file_hash(path)
            for path in (
                failed_path,
                semantic_path,
                discovery_path,
                cc_path,
                frozen_path,
                fresh_summary_path,
                fresh_ledger_path,
            )
        },
    }
    receipt["receipt_sha256"] = _logical_hash(receipt)
    return receipt


def main() -> int:
    receipt = build()
    path = EVIDENCE_ROOT / "final_closeout_receipt_v1.json"
    path.write_text(
        json.dumps(receipt, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(receipt, indent=2, sort_keys=True, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
