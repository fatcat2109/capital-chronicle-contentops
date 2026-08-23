"""Replay the exact failed oil/Treasury semantic review with the corrected contract."""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from live_contentops.rolling_x_grounded_article_media_builder_v1 import (
    resolve_editorial_worker_article_for_public_lock,
)
from live_contentops.tier1_editorial_quality_v1 import (
    audit_tier1_article,
    build_llm_editorial_review_prompt,
    combine_editorial_gates,
    review_tier1_article_with_llm,
)


FAILED_ROOT = ROOT / (
    "docs/automation/"
    "TASK_V1_POST_LAUNCH_4_32_DESKTOP_PRIMARY_HYBRID_THROUGHPUT_PROOF_V1"
)


def _read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _logical_hash(value: Any) -> str:
    return sha256(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), default=str
        ).encode("utf-8")
    ).hexdigest()


def _review_input(prompt: str) -> dict[str, Any]:
    return json.loads(prompt.split("ARTICLE:\n", 1)[1])


def build_receipt(*, live_review: bool) -> dict[str, Any]:
    failed_cycle_path = FAILED_ROOT / (
        "frontier_4/canonical_zero_write_rehearsal_attempt_2/"
        "rolling_x_newsroom_cycle_evidence_v1.json"
    )
    candidate_path = FAILED_ROOT / (
        "frontier_4/canonical_zero_write_rehearsal_attempt_2/"
        "rolling_x_grounded_article_media_candidate_4_v1.json"
    )
    viability_path = FAILED_ROOT / (
        "frontier_4/route_probe/rolling_x_ranked_viability_v1.json"
    )
    cycle = _read(failed_cycle_path)
    candidate = _read(candidate_path)
    viability = _read(viability_path)
    prior_history = list((cycle.get("editorial_cycle") or {}).get("review_history") or [])
    if not prior_history:
        raise ValueError("exact_prior_semantic_review_missing")
    prior_review = dict(prior_history[-1].get("llm_semantic_review") or {})
    raw_article = dict(candidate.get("article") or {})
    resolved = resolve_editorial_worker_article_for_public_lock(
        raw_article, viability=viability
    )
    prompt = build_llm_editorial_review_prompt(resolved)
    review_input = _review_input(prompt)
    deterministic = audit_tier1_article(
        resolved, media_assets=list((candidate.get("media") or {}).get("assets") or [])
    )
    after_review: Mapping[str, Any]
    if live_review:
        after_review = review_tier1_article_with_llm(
            resolved, llm_provider="9router"
        )
    else:
        after_review = {
            "status": "NOT_RUN",
            "decision": "NOT_RUN",
            "provider": "9router",
            "prompt_sha256": sha256(prompt.encode("utf-8")).hexdigest(),
            "publication_authority": False,
        }
    combined = combine_editorial_gates(deterministic, after_review)
    prior_issue_codes = [
        str(row.get("code") or "")
        for row in prior_review.get("issues") or []
        if isinstance(row, Mapping)
    ]
    result = {
        "schema_version": "contentops.v1_throughput_semantic_contract_replay.v1",
        "task": (
            "TASK_V1_THROUGHPUT_SOURCEABILITY_GROUNDED_DISCOVERY_AND_"
            "SEMANTIC_GATE_CLOSEOUT_V1"
        ),
        "exact_failed_candidate": {
            "cluster_id": (
                (cycle.get("candidate_walk") or {}).get("candidate_attempts") or [{}]
            )[3].get("cluster_id"),
            "article_title": raw_article.get("title"),
            "failed_cycle_path": failed_cycle_path.as_posix(),
            "failed_cycle_sha256": _logical_hash(cycle),
            "candidate_path": candidate_path.as_posix(),
            "candidate_sha256": _logical_hash(candidate),
            "viability_path": viability_path.as_posix(),
            "viability_sha256": _logical_hash(viability),
        },
        "before": {
            "deterministic_classification": prior_history[-1].get(
                "deterministic_review", {}
            ).get("classification"),
            "semantic_status": prior_review.get("status"),
            "semantic_decision": prior_review.get("decision"),
            "prompt_sha256": prior_review.get("prompt_sha256"),
            "review_sha256": prior_review.get("review_sha256"),
            "supported_claim_count_received": 0,
            "issue_codes": prior_issue_codes,
            "empty_supported_claim_contract_proven": "unsupported_claims"
            in prior_issue_codes,
            "rendered_citation_artifact_proven": "reader_facing_prose"
            in prior_issue_codes,
        },
        "after": {
            "deterministic_classification": deterministic.get("classification"),
            "semantic_status": after_review.get("status"),
            "semantic_decision": after_review.get("decision"),
            "combined_classification": combined.get("classification"),
            "prompt_sha256": after_review.get("prompt_sha256"),
            "review_sha256": after_review.get("review_sha256"),
            "supported_claim_count_received": len(
                review_input.get("supported_claims") or []
            ),
            "omitted_claim_count_received": len(
                review_input.get("omitted_unsupported_claims") or []
            ),
            "accepted_source_identity_count_received": len(
                review_input.get("accepted_source_identities") or []
            ),
            "evidence_document_id_count_received": len(
                review_input.get("evidence_document_ids") or []
            ),
            "semantic_review_contract_sha256": review_input.get(
                "semantic_review_contract_sha256"
            ),
            "reader_visible_prose_sha256": sha256(
                str(review_input.get("reader_visible_prose") or "").encode("utf-8")
            ).hexdigest(),
            "artificial_aljazeera_duplicate_absent": (
                "Aljazeera Al Jazeera"
                not in str(review_input.get("reader_visible_prose") or "")
            ),
            "issues": list(after_review.get("issues") or []),
            "material_failed_checks": list(
                after_review.get("material_failed_checks") or []
            ),
            "semantic_review_receipt": dict(after_review),
        },
        "ownership_reconciliation": {
            "desktop_high_primary_editorial_coordinator": True,
            "nine_router_semantic_review_retained_as_hard": True,
            "reason": (
                "The reviewer independently checks factual support, contradictions, fabricated "
                "numbers or quotes, misleading framing, and severe coherence after native worker "
                "source rendering. It cannot override a deterministic blocker and grants no "
                "publication authority. The failure was its incomplete input projection, not "
                "duplicate publication authority."
            ),
            "deterministic_gate_remains_hard": True,
            "semantic_review_cannot_override_deterministic_blockers": True,
            "authority_widened": False,
        },
        "execution": {
            "live_9router_call_performed": live_review,
            "model_or_route": "9router/editorial_review",
            "public_writes": 0,
            "unknown_write": 0,
            "publication_authority_granted": False,
        },
    }
    result["receipt_sha256"] = _logical_hash(result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--skip-live-review", action="store_true")
    args = parser.parse_args()
    receipt = build_receipt(live_review=not args.skip_live_review)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
