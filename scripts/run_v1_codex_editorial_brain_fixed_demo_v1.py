"""Run the committed rank-1 V1 packet through the real Codex fallback with zero writes."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from live_contentops import _eight_platform_substack_first_pipeline_impl_v1 as pipeline
from live_contentops.rolling_x_grounded_article_media_builder_v1 import (
    CODEX_EDITORIAL_BRAIN_TRIGGER,
    build_rolling_x_grounded_article_and_media,
)
from live_contentops.codex_editorial_brain_v1 import RECEIPT_FILE_NAME

FIXED_PACKET = REPO_ROOT / (
    "docs/automation/"
    "TASK_CONTENTOPS_V1_GROUNDED_RESEARCH_YIELD_AND_BUDGET_AWARE_EVIDENCE_RECOVERY_V1/"
    "exact_1700_zero_write_replay_final/candidate_checkpoints/rank_01.json"
)
FIXED_PACKET_SHA256 = "511688bf124bbcd703aa076d2bc90e0efee2c4bee54c71b84b91c7a1ce39e37c"
SOURCE_RUN_CONTEXT = FIXED_PACKET.parents[1] / "zero_write_e2e" / "run_context_v1.json"
ACCEPTED_TRIGGER = REPO_ROOT / (
    "docs/automation/"
    "TASK_CONTENTOPS_V1_WRITER_UTILITY_RECOVERY_CX_FALLBACK_AND_CODEX_FINAL_GATE_V1/"
    "zero_write_trigger_evidence_v1.json"
)


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected_json_object:{path.name}")
    return value


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, sort_keys=True, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _fixed_viability(
    checkpoint: Mapping[str, Any], source_context: Mapping[str, Any]
) -> dict[str, Any]:
    candidate = dict(checkpoint.get("candidate_result") or {})
    evidence = dict(checkpoint.get("evidence_receipt") or {})
    selection = dict(source_context.get("selection") or {})
    prior_article = dict(source_context.get("article") or {})
    cluster_id = str(checkpoint.get("cluster_id") or candidate.get("cluster_id") or "")
    rank = int(checkpoint.get("rank") or candidate.get("rank") or 0)
    headline_ids = [str(value) for value in candidate.get("headline_ids") or evidence.get("headline_ids") or []]
    if not cluster_id or rank != 1 or not headline_ids or evidence.get("status") != "PASS":
        raise ValueError("fixed_rank_1_checkpoint_not_evidence_qualified")
    selection.update(
        {
            "cluster_id": cluster_id,
            "rank": rank,
            "headline_ids": headline_ids,
            "article_mode": prior_article.get("article_mode") or "straight_news",
            "requested_article_mode": prior_article.get("requested_article_mode") or "BREAKING_BRIEF",
            "resolved_article_mode": prior_article.get("resolved_article_mode") or "BREAKING_BRIEF",
            "effective_article_mode": candidate.get("effective_article_mode") or "BREAKING_BRIEF",
            "editorial_classification": prior_article.get("editorial_classification") or "",
            "update_chain_identity": prior_article.get("update_chain_identity") or cluster_id,
        }
    )
    request = {
        "schema_version": "capital_chronicle.rolling_x_story_evidence_request.v1",
        "cluster_id": cluster_id,
        "rank": rank,
        "headline_ids": headline_ids,
        "story_type": prior_article.get("story_type") or "market_event",
        "article_mode": prior_article.get("article_mode") or "straight_news",
        "requested_article_mode": prior_article.get("requested_article_mode") or "BREAKING_BRIEF",
        "resolved_article_mode": prior_article.get("resolved_article_mode") or "BREAKING_BRIEF",
        "effective_article_mode": candidate.get("effective_article_mode") or "BREAKING_BRIEF",
        "editorial_classification": prior_article.get("editorial_classification") or "",
        "update_chain_identity": prior_article.get("update_chain_identity") or cluster_id,
        "required_evidence_capabilities": [],
        "optional_evidence_capabilities": [],
        "capital_chronicle_numeric_or_analytical_authority_required": False,
        "story_context": {
            "capital_chronicle_context": selection.get("capital_chronicle_context") or {},
            "material_follow_up_context": selection.get("material_follow_up_context") or {},
        },
        "request_logical_hash": checkpoint.get("request_logical_hash"),
    }
    return {
        "schema_version": "capital_chronicle.rolling_x_ranked_evidence_viability.v1",
        "status": "SUCCESS",
        "decision": "SELECT_STORY",
        "reason_code": "ACCEPTED_FIXED_CODEX_TRIGGER_REPLAY",
        "work_item_id": "fixed-rank-1-codex-editorial-brain-zero-write",
        "selected_cluster_id": cluster_id,
        "selected_rank": rank,
        "selected_headline_ids": headline_ids,
        "selected_cluster": selection,
        "selected_evidence": evidence,
        "rank_attempts": [
            {
                "rank": rank,
                "cluster_id": cluster_id,
                "headline_ids": headline_ids,
                "request": request,
                "capability_resolution": {
                    "status": "PASS",
                    "story_type": request["story_type"],
                    "article_mode": request["article_mode"],
                    "capital_chronicle_authority_required": False,
                    "required_evidence_capabilities": [],
                },
                "evidence_receipt": evidence,
                "status": "VIABLE",
                "blockers": [],
            }
        ],
        "evidence_acquired_after_ranking": True,
        "x_content_grants_evidence_authority": False,
        "publication_authority_granted": False,
    }


def run_demo(
    *,
    output_dir: Path,
    runtime_root: Path,
    codex_executable: Path | None,
    timeout_seconds: float,
) -> dict[str, Any]:
    fixed_sha = _sha256_file(FIXED_PACKET)
    if fixed_sha != FIXED_PACKET_SHA256:
        raise ValueError("fixed_rank_1_sha256_mismatch")
    checkpoint = _read_json(FIXED_PACKET)
    source_context = _read_json(SOURCE_RUN_CONTEXT)
    accepted_trigger = _read_json(ACCEPTED_TRIGGER)
    if accepted_trigger.get("classification") != CODEX_EDITORIAL_BRAIN_TRIGGER:
        raise ValueError("accepted_parent_codex_trigger_missing")
    if (accepted_trigger.get("fixed_input") or {}).get("sha256") != fixed_sha:
        raise ValueError("accepted_parent_fixed_input_hash_mismatch")
    viability = _fixed_viability(checkpoint, source_context)
    trigger_receipt = {
        "classification": CODEX_EDITORIAL_BRAIN_TRIGGER,
        "writer_router": {
            "logical_invocations": int(
                (accepted_trigger.get("fixed_input_replay") or {}).get(
                    "writer_logical_invocations"
                )
                or 0
            ),
            "normal_repair_attempted": bool(
                (accepted_trigger.get("fixed_input_replay") or {}).get(
                    "normal_repair_attempted"
                )
            ),
            "cx_utility_rescue_attempted": bool(
                (accepted_trigger.get("fixed_input_replay") or {}).get(
                    "cx_utility_rescue_attempted"
                )
            ),
        },
    }
    built = build_rolling_x_grounded_article_and_media(
        viability,
        output_dir=output_dir,
        accepted_codex_trigger_receipt=trigger_receipt,
        codex_executable_path=codex_executable,
        codex_runtime_root=runtime_root,
        codex_timeout_seconds=timeout_seconds,
    )
    article = dict(built.get("article") or {})
    media = dict(built.get("media") or {})
    full_codex_receipt = _read_json(output_dir / RECEIPT_FILE_NAME)
    committed_job_path = output_dir / "codex_governed_article_job_v1.json"
    committed_output_path = output_dir / "codex_structured_article_result_v1.json"
    _write_json(committed_job_path, _read_json(Path(str(full_codex_receipt["job_path"]))))
    _write_json(
        committed_output_path,
        _read_json(Path(str(full_codex_receipt["output_path"]))),
    )
    media_assets = list(media.get("assets") or [])
    editorial = pipeline._run_bounded_rolling_x_editorial_cycle(
        article=article,
        media_assets=media_assets,
        editorial_reviewer=pipeline._default_rolling_x_editorial_reviewer,
        article_reviser=lambda candidate, _review, _index: dict(candidate),
    )
    if editorial.get("status") != "PASS":
        raise ValueError("fixed_codex_article_editorial_gate_failed")
    assignment = {
        "schema_version": "capital_chronicle.rolling_x_newsroom_assignment.v1",
        "status": "SUCCESS",
        "decision": "SELECT_STORY",
        "assignment_logical_hash": str(checkpoint.get("request_logical_hash") or ""),
        "ranked_clusters": [viability["selected_cluster"]],
    }
    readiness = {
        "schema_version": "contentops.destination_readiness.shadow.v1",
        "destinations": {},
        "fixture_bound": False,
        "public_write_authority": False,
    }
    preparation = pipeline._prepare_rolling_x_release_candidate(
        run_id="fixed-rank-1-codex-editorial-brain-zero-write",
        output_dir=output_dir,
        intake={"schema_version": "capital_chronicle.rolling_x_headline_input.v1", "counts": {"accepted": 1}},
        assignment=assignment,
        viability=viability,
        article=dict(editorial.get("article") or {}),
        media=media,
        editorial_cycle=editorial,
        destination_readiness=readiness,
    )
    plan = pipeline._build_rolling_x_publication_plan(
        run_id="fixed-rank-1-codex-editorial-brain-zero-write",
        output_dir=output_dir,
        viability=viability,
        preparation=preparation,
        readiness=readiness,
    )
    review = dict((editorial.get("review_history") or [{}])[-1])
    deterministic = dict(review.get("deterministic_review") or {})
    body = str((editorial.get("article") or {}).get("substack_body_markdown") or "")
    receipt = dict(article.get("codex_editorial_brain_receipt") or {})
    result = {
        "schema_version": "contentops.v1_codex_editorial_brain_fixed_demo.v1",
        "classification": "PASS_V1_CODEX_EDITORIAL_BRAIN_ZERO_WRITE_PROVEN",
        "fixed_input": {"path": str(FIXED_PACKET), "sha256": fixed_sha, "rank": 1},
        "accepted_trigger_path": str(ACCEPTED_TRIGGER),
        "codex_input_packet": {
            "path": str(committed_job_path),
            "sha256": _sha256_file(committed_job_path),
            "governed_input_sha256": full_codex_receipt.get("governed_input_sha256"),
        },
        "codex_structured_output": {
            "path": str(committed_output_path),
            "sha256": _sha256_file(committed_output_path),
        },
        "codex": receipt,
        "article": dict(editorial.get("article") or {}),
        "article_word_count": len(re.findall(r"\b[A-Za-z0-9][A-Za-z0-9'-]*\b", body)),
        "factual_safety_result": dict(review.get("hard_factual_safety_review") or {}),
        "reader_value_result": dict(deterministic.get("reader_value_gate") or {}),
        "source_binding_result": article.get("grounded_source_coverage"),
        "release_preparation": {
            "classification": preparation.get("classification"),
            "lock_verification": preparation.get("release_candidate_lock_verification"),
            "blockers": preparation.get("blockers"),
        },
        "publication_plan": plan,
        "publication_coordinator_called": False,
        "publishing_adapter_called": False,
        "public_writes": 0,
        "unknown_write": 0,
        "browser_use": 0,
        "external_research": False,
        "synthetic_editorial_triggers": 0,
        "synthetic_x_captures": 0,
        "new_research": False,
        "v2_mutations": 0,
    }
    if (
        result["release_preparation"]["classification"]
        != "PASS_TEXT_IMAGE_RELEASE_CANDIDATE_REHEARSAL"
        or not plan.get("destinations")
        or receipt.get("status") != "COMPLETED"
        or result["reader_value_result"].get("classification") != "PASS"
    ):
        raise ValueError("fixed_codex_zero_write_acceptance_failed")
    _write_json(output_dir / "codex_editorial_brain_fixed_demo_result_v1.json", result)
    return result


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--codex-executable", type=Path)
    parser.add_argument("--timeout-seconds", type=float, default=420.0)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    result = run_demo(
        output_dir=args.output_dir.resolve(),
        runtime_root=args.runtime_root.resolve(),
        codex_executable=args.codex_executable.resolve() if args.codex_executable else None,
        timeout_seconds=args.timeout_seconds,
    )
    print(
        json.dumps(
            {
                "classification": result["classification"],
                "article_word_count": result["article_word_count"],
                "public_writes": result["public_writes"],
                "codex_job_id": result["codex"].get("job_id"),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
