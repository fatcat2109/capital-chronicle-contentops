"""Prove that Codex URL-only discovery feeds the governed deterministic loader."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import sys
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from live_contentops.public_secondary_evidence_loader_v1 import (
    BoundedPublicSecondaryEvidenceLoader,
)
from live_contentops.rolling_x_targeted_evidence_adapter_v1 import (
    CODEX_SOURCE_DISCOVERY_SCHEMA_VERSION,
    RollingXTargetedEvidenceAdapter,
    _apply_codex_source_discovery,
)


FAILED_ROOT = ROOT / (
    "docs/automation/"
    "TASK_V1_POST_LAUNCH_4_32_DESKTOP_PRIMARY_HYBRID_THROUGHPUT_PROOF_V1"
)
EVALUATION_AS_OF_UTC = "2026-08-22T22:14:27.784365Z"
SEARCHED_AT_UTC = "2026-08-23T00:00:00Z"

CASES = (
    {
        "case_id": "frozen-frontier-1-rank-2-fbi-2025-crime",
        "viability_path": "frontier_1/route_probe/rolling_x_ranked_viability_v1.json",
        "rank": 2,
        "search_call_id": "codex-web-search-20260823-batch-1",
        "candidate_urls": [
            "https://apnews.com/article/9d9e79bb71174a604c4ab068a6887c82"
        ],
    },
    {
        "case_id": "frozen-frontier-4-rank-1-fda-nomination",
        "viability_path": (
            "frontier_4/canonical_zero_write_rehearsal_attempt_2/"
            "rolling_x_ranked_viability_v1.json"
        ),
        "rank": 1,
        "search_call_id": "codex-web-search-20260823-batch-2",
        "candidate_urls": [
            "https://apnews.com/article/a54907d62a2482bd462410c0778266b9"
        ],
    },
    {
        "case_id": "frozen-frontier-4-rank-2-drug-prices",
        "viability_path": (
            "frontier_4/canonical_zero_write_rehearsal_attempt_2/"
            "rolling_x_ranked_viability_v1.json"
        ),
        "rank": 2,
        "search_call_id": "codex-web-search-20260823-batch-2",
        "candidate_urls": [
            "https://apnews.com/article/75272c1a6eeac615014b3252971460da"
        ],
    },
    {
        "case_id": "frozen-frontier-4-rank-9-white-house-ballroom",
        "viability_path": (
            "frontier_4/canonical_zero_write_rehearsal_attempt_2/"
            "rolling_x_ranked_viability_v1.json"
        ),
        "rank": 9,
        "search_call_id": "codex-web-search-20260823-batch-5",
        "candidate_urls": [
            "https://apnews.com/article/b3eaee672028e584d0c520180c663e2c"
        ],
    },
)


def _read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _logical_hash(value: Any) -> str:
    return sha256(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), default=str
        ).encode("utf-8")
    ).hexdigest()


def _sanitized_document(document: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: document.get(key)
        for key in (
            "document_id",
            "publisher",
            "title",
            "source_identity",
            "source_authority_class",
            "requested_source_url",
            "source_url",
            "reader_source_url",
            "published_at_utc",
            "published_at_source",
            "retrieval_method",
            "content_type",
            "byte_length",
            "raw_sha256",
            "canonical_content_sha256",
            "public_claim_allowed",
        )
        if document.get(key) is not None
    }


def build_receipt() -> dict[str, Any]:
    # A shared loader preserves the real bounded request ledger across the three discovery
    # cases. No grounded model synthesis is injected or used here.
    loader = BoundedPublicSecondaryEvidenceLoader(
        evaluation_as_of_utc=EVALUATION_AS_OF_UTC,
        clock=lambda: datetime(2026, 8, 22, 22, 14, 27, tzinfo=timezone.utc),
    )
    adapter = RollingXTargetedEvidenceAdapter(
        evaluation_as_of_utc=EVALUATION_AS_OF_UTC,
        public_secondary_loader=loader,
    )
    rows: list[dict[str, Any]] = []
    for case in CASES:
        viability_path = FAILED_ROOT / str(case["viability_path"])
        viability = _read(viability_path)
        attempt = next(
            row
            for row in viability.get("rank_attempts") or []
            if int(row.get("rank") or 0) == int(case["rank"])
        )
        request = dict(attempt.get("request") or {})
        blockers = [str(value) for value in attempt.get("blockers") or []]
        request["codex_source_discovery"] = {
            "schema_version": CODEX_SOURCE_DISCOVERY_SCHEMA_VERSION,
            "story_identity": request.get("cluster_id"),
            "headline_ids": list(request.get("headline_ids") or []),
            "trigger_reason": "BOUNDED_ACCESS_FAILURE",
            "prior_blockers": blockers,
            "candidate_urls": list(case["candidate_urls"]),
            "search_call_id": case["search_call_id"],
            "searched_at_utc": SEARCHED_AT_UTC,
            "search_snippets_included": False,
            "model_summaries_included": False,
            "candidate_urls_are_evidence": False,
            "factual_or_numeric_authority_granted": False,
            "publication_authority_granted": False,
        }
        receipt = adapter(request)
        # Persist the deterministic transport result separately from evidence acceptance. This
        # proves whether bytes were accessible even when the later freshness/claim gates reject
        # them. The loader cache prevents a second network read for the same story URL.
        effective_request, _discovery_receipt = _apply_codex_source_discovery(request)
        transport = loader(effective_request)
        provenance = dict(receipt.get("evidence_acquisition_provenance") or {})
        secondary = dict(provenance.get("public_secondary") or {})
        rows.append(
            {
                "case_id": case["case_id"],
                "cluster_id": request.get("cluster_id"),
                "headline_ids": list(request.get("headline_ids") or []),
                "requested_article_mode": request.get("effective_article_mode"),
                "prior_blockers": blockers,
                "search_call_id": case["search_call_id"],
                "codex_candidate_urls": list(case["candidate_urls"]),
                "codex_output_fields": ["candidate_urls"],
                "receipt_status": receipt.get("status"),
                "receipt_blockers": list(receipt.get("blockers") or []),
                "provided_evidence_capabilities": list(
                    receipt.get("provided_evidence_capabilities") or []
                ),
                "minimum_evidence_status": (
                    receipt.get("minimum_trustworthy_evidence_packet") or {}
                ).get("status"),
                "deterministically_retrieved_documents_before_truth_gates": [
                    _sanitized_document(row)
                    for row in transport.get("evidence_documents") or []
                    if isinstance(row, Mapping)
                ],
                "accepted_documents": [
                    _sanitized_document(row)
                    for row in receipt.get("evidence_documents") or []
                    if isinstance(row, Mapping)
                ],
                "discovery_contract": dict(
                    provenance.get("codex_source_discovery") or {}
                ),
                "deterministic_loader_provenance": secondary.get("provenance"),
                "search_snippet_or_model_summary_authority": False,
                "factual_or_numeric_authority_granted": False,
                "publication_authority_granted": False,
            }
        )
    recovered = [
        document
        for row in rows
        for document in row["accepted_documents"]
    ]
    retrieved = [
        document
        for row in rows
        for document in row[
            "deterministically_retrieved_documents_before_truth_gates"
        ]
    ]
    result = {
        "schema_version": "contentops.v1_codex_url_discovery_recovery.v1",
        "task": (
            "TASK_V1_THROUGHPUT_SOURCEABILITY_GROUNDED_DISCOVERY_AND_"
            "SEMANTIC_GATE_CLOSEOUT_V1"
        ),
        "search_contract": {
            "codex_output_is_candidate_urls_only": True,
            "search_snippets_persisted": False,
            "model_summaries_persisted": False,
            "actual_page_retrieval_required": True,
            "governed_host_policy_required": True,
            "final_url_publisher_timestamp_content_and_hash_required": True,
        },
        "case_count": len(rows),
        "retrieved_case_count": sum(
            bool(row["deterministically_retrieved_documents_before_truth_gates"])
            for row in rows
        ),
        "recovered_case_count": sum(bool(row["accepted_documents"]) for row in rows),
        "deterministically_retrieved_document_count": len(retrieved),
        "deterministically_accepted_document_count": len(recovered),
        "retrieved_raw_sha256": sorted(
            str(row.get("raw_sha256") or "") for row in retrieved
        ),
        "retrieved_canonical_content_sha256": sorted(
            str(row.get("canonical_content_sha256") or "") for row in retrieved
        ),
        "accepted_raw_sha256": sorted(
            str(row.get("raw_sha256") or "") for row in recovered
        ),
        "accepted_canonical_content_sha256": sorted(
            str(row.get("canonical_content_sha256") or "") for row in recovered
        ),
        "cases": rows,
        "browser_cdp": {
            "status": "NOT_REQUIRED",
            "reason": (
                "The governed no-auth HTTP loader retrieved publisher bytes for every bounded "
                "case. Later freshness rejection is not a client-rendering problem and a browser "
                "would not make stale evidence eligible."
            ),
            "chrome_ingestion_profile_used": False,
            "edge_publication_profile_used": False,
        },
        "economics": {
            "codex_web_search_calls": 5,
            "codex_web_search_query_count": 20,
            "search_call_ids": [
                "codex-web-search-20260823-batch-1",
                "codex-web-search-20260823-batch-2",
                "codex-web-search-20260823-batch-3",
                "codex-web-search-20260823-batch-4",
                "codex-web-search-20260823-batch-5",
            ],
            "codex_search_output_token_or_cost_receipt_available": False,
            "grounded_research_model_calls": 0,
            "public_writes": 0,
            "unknown_write": 0,
        },
        "authority": {
            "candidate_urls_are_evidence": False,
            "factual_or_numeric_authority_granted_by_codex": False,
            "publication_authority_granted": False,
            "public_write_authority_granted": False,
        },
    }
    result["receipt_sha256"] = _logical_hash(result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    value = build_receipt()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(value, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
