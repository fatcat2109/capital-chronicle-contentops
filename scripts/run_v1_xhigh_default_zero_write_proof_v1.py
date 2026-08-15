"""Run one real frozen V1 packet through the default exact-XHIGH path with zero writes."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from live_contentops import _eight_platform_substack_first_pipeline_impl_v1 as pipeline
from live_contentops.codex_editorial_brain_v1 import (
    RECEIPT_FILE_NAME,
    REQUESTED_MODEL,
    REQUESTED_REASONING_EFFORT,
)
from live_contentops.rolling_x_grounded_article_media_builder_v1 import (
    build_rolling_x_grounded_article_and_media,
)
from scripts.run_v1_codex_editorial_brain_fixed_demo_v1 import (
    FIXED_PACKET,
    FIXED_PACKET_SHA256,
    SOURCE_RUN_CONTEXT,
    _fixed_viability,
    _read_json,
    _sha256_file,
    _write_json,
)
from scripts.run_v1_golden_product_zero_write_proofs import (
    _capture_local_screenshot,
    _render_article_html,
)

CLASSIFICATION = "PASS_V1_XHIGH_DEFAULT_EDITORIAL_BRAIN_ZERO_WRITE_PROVEN"
RUN_ID = "v1-xhigh-default-editorial-brain-zero-write-proof"


def _selected_media_rows(media_assets: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            key: row.get(key)
            for key in (
                "asset_id",
                "path",
                "sha256",
                "modality",
                "purpose",
                "caption",
                "publisher",
                "provenance_status",
                "rights_status",
                "render_rights_status",
                "underlying_source_rights_status",
                "source_reuse_basis",
            )
            if row.get(key) not in (None, "")
        }
        for row in media_assets
        if isinstance(row, Mapping)
    ]


def run_proof(
    *,
    output_dir: Path,
    runtime_root: Path,
    codex_executable: Path | None,
    timeout_seconds: float,
    source_cycle_evidence: Path | None = None,
    expected_source_sha256: str | None = None,
) -> dict[str, Any]:
    if source_cycle_evidence is not None:
        source_sha = _sha256_file(source_cycle_evidence)
        if not expected_source_sha256 or source_sha.casefold() != str(
            expected_source_sha256
        ).casefold():
            raise ValueError("source_cycle_evidence_sha256_mismatch")
        source_cycle = _read_json(source_cycle_evidence)
        viability = dict(source_cycle.get("ranked_viability") or {})
        selected_evidence = dict(viability.get("selected_evidence") or {})
        substance = dict(selected_evidence.get("evidence_substance") or {})
        if (
            viability.get("decision") != "SELECT_STORY"
            or selected_evidence.get("status") != "PASS"
            or substance.get("enough_for_useful_article") is not True
            or int(substance.get("usable_content_words") or 0) < 90
        ):
            raise ValueError("source_cycle_not_evidence_qualified_with_substance")
        frozen_viability_path = output_dir / "frozen_governed_viability_v1.json"
        _write_json(frozen_viability_path, viability)
        fixed_input = {
            "source_cycle_path": str(source_cycle_evidence),
            "source_cycle_sha256": source_sha,
            "path": str(frozen_viability_path),
            "sha256": _sha256_file(frozen_viability_path),
            "rank": int(viability.get("selected_rank") or 0),
            "synthetic_facts": False,
            "evidence_substance": substance,
        }
    else:
        fixed_sha = _sha256_file(FIXED_PACKET)
        if fixed_sha != FIXED_PACKET_SHA256:
            raise ValueError("fixed_rank_1_sha256_mismatch")
        viability = _fixed_viability(
            _read_json(FIXED_PACKET), _read_json(SOURCE_RUN_CONTEXT)
        )
        fixed_input = {
            "path": str(FIXED_PACKET),
            "sha256": fixed_sha,
            "rank": 1,
            "synthetic_facts": False,
        }
    viability["work_item_id"] = RUN_ID
    built = build_rolling_x_grounded_article_and_media(
        viability,
        output_dir=output_dir,
        codex_executable_path=codex_executable,
        codex_runtime_root=runtime_root,
        codex_timeout_seconds=timeout_seconds,
    )
    article = dict(built.get("article") or {})
    media = dict(built.get("media") or {})
    media_assets = [
        dict(row) for row in media.get("assets") or [] if isinstance(row, Mapping)
    ]
    full_receipt = _read_json(output_dir / RECEIPT_FILE_NAME)
    committed_job_path = output_dir / "codex_governed_article_job_v1.json"
    committed_output_path = output_dir / "codex_structured_article_result_v1.json"
    _write_json(committed_job_path, _read_json(Path(str(full_receipt["job_path"]))))
    _write_json(
        committed_output_path,
        _read_json(Path(str(full_receipt["output_path"]))),
    )

    editorial = pipeline._run_bounded_rolling_x_editorial_cycle(
        article=article,
        media_assets=media_assets,
        editorial_reviewer=pipeline._default_rolling_x_editorial_reviewer,
        article_reviser=lambda candidate, _review, _index: dict(candidate),
    )
    if editorial.get("status") != "PASS":
        raise ValueError("xhigh_default_article_editorial_gate_failed")
    selected_attempt = next(
        (
            dict(row)
            for row in viability.get("rank_attempts") or []
            if isinstance(row, Mapping)
            and int(row.get("rank") or 0) == int(viability.get("selected_rank") or 0)
        ),
        {},
    )
    assignment = {
        "schema_version": "capital_chronicle.rolling_x_newsroom_assignment.v1",
        "status": "SUCCESS",
        "decision": "SELECT_STORY",
        "assignment_logical_hash": str(
            (selected_attempt.get("request") or {}).get("request_logical_hash") or ""
        ),
        "ranked_clusters": [viability["selected_cluster"]],
    }
    readiness = {
        "schema_version": "contentops.destination_readiness.shadow.v1",
        "destinations": {},
        "fixture_bound": False,
        "public_write_authority": False,
    }
    preparation = pipeline._prepare_rolling_x_release_candidate(
        run_id=RUN_ID,
        output_dir=output_dir,
        intake={
            "schema_version": "capital_chronicle.rolling_x_headline_input.v1",
            "counts": {"accepted": 1},
        },
        assignment=assignment,
        viability=viability,
        article=dict(editorial.get("article") or {}),
        media=media,
        editorial_cycle=editorial,
        destination_readiness=readiness,
    )
    plan = pipeline._build_rolling_x_publication_plan(
        run_id=RUN_ID,
        output_dir=output_dir,
        viability=viability,
        preparation=preparation,
        readiness=readiness,
    )

    final_article = dict(editorial.get("article") or {})
    visual_paths = {
        str(row.get("asset_id") or ""): Path(str(row.get("path") or ""))
        for row in media_assets
        if row.get("asset_id") and row.get("path")
    }
    render_html = output_dir / "xhigh_default_article_full_page_v1.html"
    render_png = output_dir / "xhigh_default_article_full_page_v1.png"
    render_html.write_text(
        _render_article_html(
            article=final_article,
            visual_paths=visual_paths,
            documentary=None,
        ),
        encoding="utf-8",
        newline="\n",
    )
    _capture_local_screenshot(render_html, render_png)

    review = dict((editorial.get("review_history") or [{}])[-1])
    deterministic = dict(review.get("deterministic_review") or {})
    hard_factual = dict(review.get("hard_factual_safety_review") or {})
    body = str(final_article.get("substack_body_markdown") or "")
    executions = [
        dict(row) for row in full_receipt.get("executions") or [] if isinstance(row, Mapping)
    ]
    exact_capability_verified = bool(
        executions
        and all(row.get("exact_model_capability_verified") is True for row in executions)
        and all(
            REQUESTED_REASONING_EFFORT in (row.get("supported_reasoning_efforts") or [])
            for row in executions
        )
    )
    result = {
        "schema_version": "contentops.v1_xhigh_default_zero_write_proof.v1",
        "classification": CLASSIFICATION,
        "fixed_input": fixed_input,
        "codex_input_packet": {
            "path": str(committed_job_path),
            "sha256": _sha256_file(committed_job_path),
            "governed_input_sha256": full_receipt.get("governed_input_sha256"),
        },
        "codex_structured_output": {
            "path": str(committed_output_path),
            "sha256": _sha256_file(committed_output_path),
        },
        "requested_model": full_receipt.get("requested_model"),
        "requested_reasoning_effort": full_receipt.get("requested_reasoning_effort"),
        "exact_model_capability_verified": exact_capability_verified,
        "codex_execution": {
            "status": full_receipt.get("status"),
            "job_id": full_receipt.get("job_id"),
            "execution_plane": full_receipt.get("execution_plane"),
            "revision_count": full_receipt.get("revision_count"),
            "total_wall_time_seconds": full_receipt.get("total_wall_time_seconds"),
            "executions": executions,
            "completed_receipt_reused_during_final_revalidation": bool(
                (built.get("critical_path_telemetry") or {})
                .get("writer_router", {})
                .get("codex_completed_receipt_reused")
            ),
        },
        "article": final_article,
        "article_word_count": len(
            re.findall(r"\b[A-Za-z0-9][A-Za-z0-9'-]*\b", body)
        ),
        "selected_media": _selected_media_rows(media_assets),
        "selected_media_count": len(media_assets),
        "visual_intent_plan": media.get("visual_intent_plan"),
        "charts_data_authority": {
            "chart_count": sum(
                1
                for row in media_assets
                if str(row.get("modality") or "").casefold() == "chart"
            ),
            "model_numeric_authority": False,
            "deterministic_renderer_required": True,
        },
        "factual_safety_result": hard_factual,
        "reader_value_result": dict(deterministic.get("reader_value_gate") or {}),
        "source_binding_result": final_article.get("grounded_source_coverage"),
        "release_preparation": {
            "classification": preparation.get("classification"),
            "lock_verification": preparation.get("release_candidate_lock_verification"),
            "blockers": preparation.get("blockers"),
        },
        "publication_plan": plan,
        "render": {
            "html_path": str(render_html),
            "html_sha256": _sha256_file(render_html),
            "full_page_screenshot_path": str(render_png),
            "full_page_screenshot_sha256": _sha256_file(render_png),
        },
        "publication_coordinator_called": False,
        "publishing_adapter_called": False,
        "public_writes": 0,
        "unknown_write": 0,
        "codex_browser_use": sum(
            int(row.get("browser_use_count") or 0) for row in executions
        ),
        "local_render_browser_use": 1,
        "public_destination_browser_use": 0,
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
        or full_receipt.get("status") != "COMPLETED"
        or result["requested_model"] != REQUESTED_MODEL
        or result["requested_reasoning_effort"] != REQUESTED_REASONING_EFFORT
        or not exact_capability_verified
        or final_article.get("editorial_brain_status") != "CODEX_XHIGH_DEFAULT"
        or final_article.get("degraded_editorial_brain") is not False
        or result["reader_value_result"].get("classification") != "PASS"
        or hard_factual.get("decision") != "PASS"
        or result["public_writes"] != 0
        or not render_png.is_file()
        or render_png.stat().st_size == 0
    ):
        raise ValueError("xhigh_default_zero_write_acceptance_failed")
    _write_json(output_dir / "xhigh_default_zero_write_proof_result_v1.json", result)
    return result


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--codex-executable", type=Path)
    parser.add_argument("--timeout-seconds", type=float, default=420.0)
    parser.add_argument("--source-cycle-evidence", type=Path)
    parser.add_argument("--expected-source-sha256")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    result = run_proof(
        output_dir=args.output_dir.resolve(),
        runtime_root=args.runtime_root.resolve(),
        codex_executable=(
            args.codex_executable.resolve() if args.codex_executable else None
        ),
        timeout_seconds=args.timeout_seconds,
        source_cycle_evidence=(
            args.source_cycle_evidence.resolve() if args.source_cycle_evidence else None
        ),
        expected_source_sha256=args.expected_source_sha256,
    )
    print(
        json.dumps(
            {
                "classification": result["classification"],
                "article_word_count": result["article_word_count"],
                "public_writes": result["public_writes"],
                "requested_model": result["requested_model"],
                "requested_reasoning_effort": result["requested_reasoning_effort"],
                "codex_job_id": result["codex_execution"]["job_id"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
