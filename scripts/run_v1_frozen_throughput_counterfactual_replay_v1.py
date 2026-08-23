"""Package the frozen failed article with corrected post-worker contracts only.

This is deliberately a counterfactual replay, not a new production day. It preserves the exact
old governed worker input and accepted evidence, reprojects that worker return through the fixed
public-lock/semantic contract, reuses the captured PASS semantic receipt by prompt hash, and runs
the deterministic package compiler. It performs no new model, source, or public call.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from live_contentops._eight_platform_substack_first_pipeline_impl_v1 import (  # noqa: E402
    _build_rolling_x_publication_plan,
    _prepare_rolling_x_release_candidate,
    _run_bounded_rolling_x_editorial_cycle,
)
from live_contentops.capital_chronicle_institutional_edge_v1 import (  # noqa: E402
    validate_institutional_edge_article,
)
from live_contentops.codex_desktop_newsroom_operator_v1 import (  # noqa: E402
    validate_same_xhigh_worker_revision_return,
)
from live_contentops.newsroom_production_day_v1 import (  # noqa: E402
    persist_qualified_article_record,
    qualify_zero_write_article,
)
from live_contentops.rolling_x_grounded_article_media_builder_v1 import (  # noqa: E402
    resolve_editorial_worker_article_for_public_lock,
)
from live_contentops.tier1_editorial_quality_v1 import (  # noqa: E402
    build_llm_editorial_review_prompt,
)
from scripts.run_v1_current_multi_frontier_floor_rehearsal import (  # noqa: E402
    _load,
    _ready,
    _write,
)


SOURCE_ROOT = ROOT / (
    "docs/automation/"
    "TASK_V1_POST_LAUNCH_4_32_DESKTOP_PRIMARY_HYBRID_THROUGHPUT_PROOF_V1"
)


def _sha(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode(
            "utf-8"
        )
    ).hexdigest()


def _semantic_reviewer(semantic_receipt: Mapping[str, Any]):
    review = dict(
        (semantic_receipt.get("after") or {}).get("semantic_review_receipt") or {}
    )
    expected_prompt_sha256 = str(review.get("prompt_sha256") or "")
    if review.get("decision") != "PASS" or not expected_prompt_sha256:
        raise ValueError("semantic_review_replay_receipt_not_pass")

    def reviewer(article: Mapping[str, Any]) -> dict[str, Any]:
        prompt = build_llm_editorial_review_prompt(article)
        observed = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
        if observed != expected_prompt_sha256:
            raise ValueError("semantic_review_replay_prompt_hash_mismatch")
        return dict(review)

    return reviewer


def run_replay(
    *,
    replay_root: Path,
    semantic_receipt_path: Path,
    failure_matrix_path: Path,
    discovery_receipt_path: Path,
) -> dict[str, Any]:
    if replay_root.exists() and any(replay_root.iterdir()):
        raise ValueError("frozen_counterfactual_replay_root_must_be_new")
    replay_root.mkdir(parents=True, exist_ok=True)

    probe_path = SOURCE_ROOT / (
        "frontier_4/route_probe/rolling_x_newsroom_cycle_evidence_v1.json"
    )
    viability_path = SOURCE_ROOT / (
        "frontier_4/route_probe/rolling_x_ranked_viability_v1.json"
    )
    candidate_path = SOURCE_ROOT / (
        "frontier_4/canonical_zero_write_rehearsal_attempt_2/"
        "rolling_x_grounded_article_media_candidate_4_v1.json"
    )
    revision_contract_path = SOURCE_ROOT / (
        "frontier_4/canonical_zero_write_rehearsal/"
        "same_xhigh_worker_revision_contract_v1.json"
    )
    worker_request_path = SOURCE_ROOT / "frontier_4/editorial_worker_request_v1.json"
    source_summary_path = SOURCE_ROOT / "multi_frontier_floor_rehearsal_summary_v1.json"

    probe = _load(probe_path)
    viability = _load(viability_path)
    candidate = _load(candidate_path)
    revision_contract = _load(revision_contract_path)
    worker_request = _load(worker_request_path)
    source_summary = _load(source_summary_path)
    semantic = _load(semantic_receipt_path)
    failure_matrix = _load(failure_matrix_path)
    discovery = _load(discovery_receipt_path)

    worker_return = dict(candidate.get("editorial_worker_receipt") or {})
    worker_validation = validate_same_xhigh_worker_revision_return(
        worker_return=worker_return,
        revision_contract=revision_contract,
        expected_editorial_packet=dict(
            (worker_request.get("bounded_governed_context") or {}).get(
                "institutional_edge_editorial_packet"
            )
            or {}
        ),
        accepted_evidence_packet=dict(viability.get("selected_evidence") or {}),
    )
    article = resolve_editorial_worker_article_for_public_lock(
        dict(candidate.get("article") or {}), viability=viability
    )
    media = dict(candidate.get("media") or {})
    editorial = _run_bounded_rolling_x_editorial_cycle(
        article=article,
        media_assets=list(media.get("assets") or []),
        editorial_reviewer=_semantic_reviewer(semantic),
        article_reviser=lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("counterfactual_semantic_pass_must_not_revise")
        ),
        native_xhigh_worker_return=worker_return,
        native_xhigh_worker_validation=worker_validation,
        native_xhigh_worker_request=worker_request,
    )
    if editorial.get("status") != "PASS":
        raise ValueError("frozen_counterfactual_editorial_not_pass")
    final_article = dict(editorial.get("article") or {})
    institutional = validate_institutional_edge_article(
        final_article,
        editorial_packet=dict(
            (worker_request.get("bounded_governed_context") or {}).get(
                "institutional_edge_editorial_packet"
            )
            or {}
        ),
        accepted_evidence_packet=dict(viability.get("selected_evidence") or {}),
    )
    final_article["institutional_edge_editorial_validation"] = institutional
    if institutional.get("classification") != "PASS":
        raise ValueError("frozen_counterfactual_institutional_gate_not_pass")

    built = {
        "schema_version": "contentops.rolling_x_grounded_article_media_builder.v1",
        "article": final_article,
        "media": media,
        "critical_path_telemetry": {
            "article_writer_semantic_calls": 0,
            "frozen_worker_receipt_reused": True,
        },
        "editorial_worker_receipt": worker_return,
        "editorial_worker_validation": worker_validation,
    }
    _write(replay_root / "rolling_x_grounded_article_media_v1.json", built)
    preparation = _prepare_rolling_x_release_candidate(
        run_id="v1-frozen-throughput-counterfactual-replay",
        output_dir=replay_root,
        intake=dict(probe.get("intake") or {}),
        assignment=dict(probe.get("assignment") or {}),
        viability=viability,
        article=final_article,
        media=media,
        editorial_cycle=editorial,
        destination_readiness=_ready(),
    )
    if preparation.get("classification") != "PASS_TEXT_IMAGE_RELEASE_CANDIDATE_REHEARSAL":
        raise ValueError(
            "frozen_counterfactual_release_candidate_not_pass:"
            + "|".join(str(value) for value in preparation.get("blockers") or [])
        )
    plan = _build_rolling_x_publication_plan(
        run_id="v1-frozen-throughput-counterfactual-replay",
        output_dir=replay_root,
        viability=viability,
        preparation=preparation,
        readiness=_ready(),
    )
    result = {
        "schema_version": "contentops.rolling_x_newsroom_cycle.v1",
        "run_id": "v1-frozen-throughput-counterfactual-replay",
        "classification": "PASS_PUBLICATION_PLAN_READY",
        "article": final_article,
        "media": media,
        "editorial_cycle": editorial,
        "editorial_worker_routing": dict(probe.get("editorial_worker_routing") or {}),
        "release_candidate_preparation": preparation,
        "release_candidate": preparation,
        "publication_lifecycle_plan": plan,
        "publishing_adapter_called": False,
        "public_write_performed": False,
        "unknown_write_detected": False,
        "unknown_write_count": 0,
        "exact_next_blocker": None,
    }
    _write(replay_root / "rolling_x_newsroom_cycle_evidence_v1.json", result)
    qualified = qualify_zero_write_article(
        result=result,
        output_dir=replay_root,
        production_day_id=str(source_summary.get("production_day_id") or "frozen-replay"),
        parent_window_id="frozen-counterfactual-frontier-4",
    )
    if qualified.get("qualified") is not True:
        raise ValueError(
            "frozen_counterfactual_article_not_qualified:"
            + "|".join(qualified.get("qualification_blockers") or [])
        )
    qualified_path = persist_qualified_article_record(replay_root, qualified)

    recovered = [
        dict(row)
        for row in (discovery.get("cases") or [])
        if isinstance(row, Mapping) and row.get("receipt_status") == "PASS"
    ]
    receipt = {
        "schema_version": "contentops.v1_frozen_failed_frontier_counterfactual_replay.v1",
        "task": (
            "TASK_V1_THROUGHPUT_SOURCEABILITY_GROUNDED_DISCOVERY_AND_"
            "SEMANTIC_GATE_CLOSEOUT_V1"
        ),
        "replay_kind": "DETERMINISTIC_COUNTERFACTUAL_NOT_NEW_PRODUCTION_DAY",
        "frozen_universe": {
            "rolling_input_sha256": source_summary.get("rolling_input_sha256"),
            "failed_story_count": failure_matrix.get("failed_story_count"),
            "held_identity_count": failure_matrix.get("held_identity_universe_count"),
            "frontier_count": source_summary.get("frontier_count"),
            "attempted_distinct_story_count": source_summary.get(
                "attempted_distinct_story_count"
            ),
            "original_evidence_viable_story_count": 1,
            "counterfactual_new_evidence_viable_story_count": len(recovered),
            "counterfactual_total_evidence_viable_story_count": 1 + len(recovered),
        },
        "semantic_closeout": {
            "before": dict(semantic.get("before") or {}),
            "after": {
                key: value
                for key, value in dict(semantic.get("after") or {}).items()
                if key != "semantic_review_receipt"
            },
            "semantic_receipt_reused_by_exact_prompt_hash": True,
            "new_model_calls": 0,
        },
        "discovery_closeout": {
            "recovered_case_count": len(recovered),
            "recovered_cases": [
                {
                    "case_id": row.get("case_id"),
                    "cluster_id": row.get("cluster_id"),
                    "candidate_urls": list(row.get("codex_candidate_urls") or []),
                    "accepted_documents": list(row.get("accepted_documents") or []),
                    "minimum_evidence_status": row.get("minimum_evidence_status"),
                    "provided_evidence_capabilities": list(
                        row.get("provided_evidence_capabilities") or []
                    ),
                }
                for row in recovered
            ],
        },
        "canonical_replay_result": {
            "classification": result["classification"],
            "qualified_count": 1,
            "qualified_derivative_intent_count": qualified.get(
                "derivative_package_intent_count"
            ),
            "remaining_build_deficit": 3,
            "qualified_article_record": {
                **qualified,
                "record_path": str(qualified_path),
            },
            "article_sha256": qualified.get("article_body_sha256"),
            "accepted_evidence_sha256": qualified.get("accepted_evidence_sha256"),
            "package_payload_sha256": dict(
                (preparation.get("release_candidate_lock") or {}).get("payload_sha256")
                or {}
            ),
        },
        "economics": {
            "failed_day_observed_network_requests": (
                failure_matrix.get("request_economics") or {}
            ).get("network_requests"),
            "failed_day_observed_public_retrieval_requests": (
                failure_matrix.get("request_economics") or {}
            ).get("public_retrieval_requests"),
            "failed_day_observed_grounded_research_calls": (
                failure_matrix.get("request_economics") or {}
            ).get("grounded_research_calls"),
            "failed_day_observed_grounded_research_tokens": (
                failure_matrix.get("request_economics") or {}
            ).get("grounded_research_tokens"),
            "canonical_counterfactual_resume_network_requests": 0,
            "canonical_counterfactual_resume_new_model_calls": 0,
            "prior_discovery_proof_public_http_requests": (
                discovery.get("deterministically_retrieved_document_count")
            ),
            "prior_codex_web_search_calls": (
                discovery.get("economics") or {}
            ).get("codex_web_search_calls"),
            "prior_codex_web_search_queries": (
                discovery.get("economics") or {}
            ).get("codex_web_search_query_count"),
            "full_day_counterfactual_request_total": "NOT_CLAIMED_WITHOUT_RERUNNING_ALL_40",
        },
        "safety": {
            "public_writes": 0,
            "publication_provider_writes": 0,
            "unknown_write": 0,
            "fifth_automation_created": 0,
            "publication_authority_granted_by_replay": False,
        },
        "source_hashes": {
            "probe": _sha(probe),
            "viability": _sha(viability),
            "candidate": _sha(candidate),
            "revision_contract": _sha(revision_contract),
            "worker_request": _sha(worker_request),
            "semantic_receipt": _sha(semantic),
            "discovery_receipt": _sha(discovery),
            "failure_matrix": _sha(failure_matrix),
        },
    }
    receipt["receipt_sha256"] = _sha(receipt)
    return receipt


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--replay-root", type=Path, required=True)
    parser.add_argument("--semantic-receipt", type=Path, required=True)
    parser.add_argument("--failure-matrix", type=Path, required=True)
    parser.add_argument("--discovery-receipt", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    receipt = run_replay(
        replay_root=args.replay_root.resolve(),
        semantic_receipt_path=args.semantic_receipt.resolve(),
        failure_matrix_path=args.failure_matrix.resolve(),
        discovery_receipt_path=args.discovery_receipt.resolve(),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "classification": receipt["canonical_replay_result"]["classification"],
        "qualified_count": receipt["canonical_replay_result"]["qualified_count"],
        "qualified_derivative_intent_count": receipt["canonical_replay_result"][
            "qualified_derivative_intent_count"
        ],
        "receipt_sha256": receipt["receipt_sha256"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
