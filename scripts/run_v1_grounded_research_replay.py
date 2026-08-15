"""Replay the frozen genuine 12-candidate evidence failure with zero public writes.

This is acceptance tooling, not a production entrypoint. It reads the immutable newsroom-cycle
artifacts, invokes the canonical evidence/research and article/media seams, runs deterministic
editorial/release preparation, and never calls ``DurablePublicationCoordinator`` or a transport.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import html
import json
from pathlib import Path
import re
import time
from typing import Any, Mapping

from live_contentops import _eight_platform_substack_first_pipeline_impl_v1 as pipeline
from live_contentops.grounded_news_research_v1 import GroundedNewsResearchV1
from live_contentops.llm_cost_governor_v1 import (
    llm_cycle_budget_scope,
)
from live_contentops.nine_router_llm_seam_v2 import drain_invocation_log
from live_contentops.public_secondary_evidence_loader_v1 import (
    BoundedPublicSecondaryEvidenceLoader,
)
from live_contentops.rolling_x_grounded_article_media_builder_v1 import (
    build_rolling_x_grounded_article_and_media,
)
from live_contentops.rolling_x_targeted_evidence_adapter_v1 import (
    RollingXTargetedEvidenceAdapter,
)
from live_contentops.source_capability_registry_v2 import (
    capability_mode_for_product_mode,
    load_source_capability_registry,
    resolve_story_capabilities,
)


TASK_LABEL = (
    "TASK_CONTENTOPS_V1_GROUNDED_RESEARCH_YIELD_AND_BUDGET_AWARE_EVIDENCE_RECOVERY_V1"
)


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"artifact_not_object:{path.name}")
    return value


def _sha256_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )


def _logical_hash(value: Any) -> str:
    return sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode(
            "utf-8"
        )
    ).hexdigest()


def _current_research_request(old_request: Mapping[str, Any]) -> dict[str, Any]:
    """Rebind one frozen candidate to current product capability doctrine.

    Candidate/story/cutoff identity remains frozen. Requirements and adapter families are the
    implementation under test and therefore must come from the current registry rather than the
    old architecture whose failure this replay measures.
    """
    request = dict(old_request)
    product_mode = str(
        request.get("effective_article_mode")
        or request.get("resolved_article_mode")
        or "BREAKING_BRIEF"
    )
    capability_mode = capability_mode_for_product_mode(product_mode) or str(
        request.get("article_mode") or "straight_news"
    )
    capability = resolve_story_capabilities(
        {
            "story_type": str(request.get("story_type") or ""),
            "article_mode": capability_mode,
            "product_article_mode": product_mode,
        },
        load_source_capability_registry(),
    )
    if capability.get("status") != "PASS":
        raise ValueError("frozen_candidate_current_capability_unresolved")
    request.update(
        {
            "article_mode": capability.get("article_mode"),
            "required_evidence_capabilities": list(
                capability.get("required_evidence_capabilities") or []
            ),
            "optional_evidence_capabilities": list(
                capability.get("optional_evidence_capabilities") or []
            ),
            "source_adapter_families": list(
                capability.get("source_adapter_families") or []
            ),
            "freshness_policy": capability.get("freshness_policy"),
            "market_sensitive": bool(capability.get("market_sensitive")),
            "market_snapshot_required": bool(
                capability.get("market_snapshot_required")
            ),
            "capital_chronicle_numeric_or_analytical_authority_required": bool(
                capability.get("capital_chronicle_authority_required")
            ),
        }
    )
    request.pop("request_logical_hash", None)
    request["request_logical_hash"] = _logical_hash(request)
    return request


def _compact_provider_telemetry(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "logical_calls": len(rows),
        "provider_attempts": sum(
            int(row.get("total_attempts") or row.get("provider_attempt_count") or 0)
            for row in rows
        ),
        "tokens": {
            key: sum(
                int(
                    (
                        row.get("total_usage")
                        or row.get("token_usage")
                        or {}
                    ).get(key)
                    or 0
                )
                for row in rows
            )
            for key in ("prompt_tokens", "completion_tokens", "total_tokens")
        },
        "cost_usd": round(
            sum(
                float(
                    (row.get("total_cost") or row.get("cost") or {}).get("usd")
                    or 0.0
                )
                for row in rows
            ),
            8,
        ),
        "models": list(
            dict.fromkeys(
                str(model)
                for row in rows
                for model in row.get("models_attempted_in_order") or []
            )
        ),
    }


def _budget_telemetry(control_root: Path) -> dict[str, Any]:
    path = control_root / "llm_cost_ledger_v1.json"
    try:
        ledger = _load(path)
    except FileNotFoundError:
        return {"cycle_count": 0, "provider_attempts": 0, "accounted_tokens": 0}
    cycles = [
        dict(row)
        for row in (ledger.get("cycles") or {}).values()
        if isinstance(row, Mapping)
    ]
    return {
        "schema_version": ledger.get("schema_version"),
        "cycle_count": len(cycles),
        "provider_attempts": sum(int(row.get("provider_attempts") or 0) for row in cycles),
        "accounted_tokens": sum(int(row.get("accounted_tokens") or 0) for row in cycles),
        "raw_prompts_or_outputs_persisted": False,
    }


def _research_metrics(receipt: Mapping[str, Any]) -> dict[str, Any]:
    provenance = receipt.get("evidence_acquisition_provenance") or {}
    grounded = provenance.get("grounded_research") or {}
    packet = receipt.get("grounded_research_packet") or {}
    sources = [row for row in packet.get("sources") or [] if isinstance(row, Mapping)]
    telemetry = [
        row for row in grounded.get("telemetry") or [] if isinstance(row, Mapping)
    ]
    return {
        "research_status": packet.get("research_status") or receipt.get("status"),
        "grounding_mode": packet.get("grounding_mode"),
        "research_model_identity": packet.get("research_model_identity"),
        "research_calls": int(grounded.get("research_calls") or 0),
        "query_plan_calls": sum(
            str(row.get("phase") or "") in {"query_plan", "query_replan"}
            for row in telemetry
        ),
        "source_synthesis_calls": sum(
            str(row.get("phase") or "") == "source_synthesis" for row in telemetry
        ),
        "public_retrieval_requests": int(
            grounded.get("public_retrieval_requests") or 0
        ),
        "elapsed_seconds": grounded.get("elapsed_seconds"),
        "source_count": len(sources),
        "source_types": sorted(
            {str(row.get("source_type") or "") for row in sources} - {""}
        ),
        "source_authority_classes": sorted(
            {
                str(row.get("source_authority_class") or "")
                for row in sources
            }
            - {""}
        ),
        "source_identities": [
            {
                "source_ref": row.get("source_ref"),
                "source_title": row.get("source_title"),
                "publisher": row.get("publisher"),
                "source_url": row.get("source_url"),
                "evidence_document_id": row.get("evidence_document_id"),
                "evidence_packet_sha256": row.get("evidence_packet_sha256"),
            }
            for row in sources
        ],
        "retrieval_result": dict(grounded.get("retrieval_result") or {}),
        "infrastructure_failure_class": grounded.get(
            "infrastructure_failure_class"
        ),
        "global_infrastructure_exhausted": bool(
            grounded.get("global_infrastructure_exhausted")
        ),
        "phase_telemetry": telemetry,
        "cc_context_state": (
            (receipt.get("cc_context_bundle") or {}).get("state")
            or (packet.get("cc_context") or {}).get("state")
        ),
        "suggested_article_mode": packet.get("suggested_article_mode"),
    }


def _preview_html(article: Mapping[str, Any]) -> str:
    body = html.escape(str(article.get("substack_body_markdown") or ""))
    body = re.sub(r"^## (.+)$", r"<h2>\1</h2>", body, flags=re.MULTILINE)
    body = body.replace("\n\n", "</p><p>").replace("\n", "<br>")
    return """<!doctype html><meta charset=\"utf-8\"><title>{title}</title>
<style>body{{max-width:760px;margin:48px auto;font:18px/1.65 Georgia,serif;color:#17212b}}
h1,h2{{font-family:Arial,sans-serif;line-height:1.15}} .dek{{color:#506070}}</style>
<h1>{title}</h1><p class=\"dek\">{dek}</p><p>{body}</p>""".format(
        title=html.escape(str(article.get("title") or "")),
        dek=html.escape(str(article.get("subtitle") or article.get("dek") or "")),
        body=body,
    )


def run(args: argparse.Namespace) -> dict[str, Any]:
    source_dir = Path(args.source_cycle_dir).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    control_root = output_dir / "llm_control"

    cycle_path = source_dir / "rolling_x_newsroom_cycle_evidence_v1.json"
    viability_path = source_dir / "rolling_x_ranked_viability_v1.json"
    assignment_path = source_dir / "rolling_x_assignment_v1.json"
    intake_path = source_dir / "rolling_x_intake_v1.json"
    preselection_path = source_dir / "preselection_intelligence_v1.json"
    cycle = _load(cycle_path)
    old_viability = _load(viability_path)
    assignment = _load(assignment_path)
    intake = _load(intake_path)
    preselection = _load(preselection_path)
    cutoff = str((cycle.get("intake") or {}).get("cutoff_time_utc") or "")
    if not cutoff:
        cutoff = str(intake.get("cutoff_time_utc") or "")
    attempts = [
        row
        for row in old_viability.get("rank_attempts") or []
        if isinstance(row, Mapping)
    ]
    if len(attempts) != 12:
        raise ValueError("frozen_replay_requires_exactly_12_rank_attempts")
    if cycle.get("exact_next_blocker") != "ALL_RANKED_CLUSTERS_EVIDENCE_BLOCKED":
        raise ValueError("source_cycle_terminal_result_mismatch")
    full_rolling_headline_count = int(
        (cycle.get("critical_path_telemetry") or {}).get(
            "full_rolling_headline_count"
        )
        or (cycle.get("intake") or {}).get("counts", {}).get("accepted")
        or 0
    )
    if full_rolling_headline_count <= 0:
        raise ValueError("source_cycle_full_rolling_headline_count_mismatch")

    clusters = {
        str(row.get("cluster_id") or ""): dict(row)
        for row in preselection.get("ranked_clusters") or []
        if isinstance(row, Mapping)
    }
    replay_rows: list[dict[str, Any]] = []
    receipts: dict[str, dict[str, Any]] = {}
    frozen_rows: list[dict[str, Any]] = []
    drain_invocation_log()
    for attempt in attempts:
        rank = int(attempt.get("rank") or 0)
        cluster_id = str(attempt.get("cluster_id") or "")
        request = _current_research_request(attempt.get("request") or {})
        frozen_rows.append(
            {
                "rank": rank,
                "cluster_id": cluster_id,
                "headline_ids": list(attempt.get("headline_ids") or []),
                "request": request,
                "old_status": attempt.get("status"),
                "old_blockers": list(attempt.get("blockers") or []),
                "old_evidence_receipt_sha256": attempt.get("evidence_receipt_sha256"),
            }
        )
        checkpoint_path = output_dir / "candidate_checkpoints" / f"rank_{rank:02d}.json"
        checkpoint_source = checkpoint_path
        retry_ranks = {
            int(value) for value in str(args.retry_ranks or "").split(",") if value.strip()
        }
        if (
            not checkpoint_source.exists()
            and args.checkpoint_seed_dir
            and rank not in retry_ranks
        ):
            seeded = (
                Path(args.checkpoint_seed_dir).resolve(strict=True)
                / f"rank_{rank:02d}.json"
            )
            if seeded.exists():
                checkpoint_source = seeded
        if checkpoint_source.exists() and rank not in retry_ranks:
            checkpoint = _load(checkpoint_source)
            if (
                int(checkpoint.get("rank") or 0) != rank
                or str(checkpoint.get("cluster_id") or "") != cluster_id
                or str(checkpoint.get("request_logical_hash") or "")
                != str(request.get("request_logical_hash") or "")
            ):
                raise ValueError(f"candidate_checkpoint_binding_mismatch:{rank}")
            checkpoint_result = dict(checkpoint["candidate_result"])
            checkpoint_blockers = {
                str(value)
                for value in checkpoint_result.get("new_blockers") or []
            }
            # An operator pause is a transient, authoritative stop rather than a
            # research outcome.  Once the operator explicitly resumes, retry only
            # those paused ranks while preserving every completed candidate receipt.
            if "llm_operator_paused" not in checkpoint_blockers:
                replay_rows.append(checkpoint_result)
                receipts[cluster_id] = dict(checkpoint["evidence_receipt"])
                if checkpoint_source != checkpoint_path:
                    _write_json(checkpoint_path, checkpoint)
                continue
        public_loader = BoundedPublicSecondaryEvidenceLoader(
            evaluation_as_of_utc=cutoff,
            max_requests=6,
        )
        researcher = GroundedNewsResearchV1(
            evaluation_as_of_utc=cutoff,
            public_retriever=public_loader,
            max_queries=2,
        )
        adapter = RollingXTargetedEvidenceAdapter(
            capital_chronicle_root=args.capital_chronicle_root,
            evaluation_as_of_utc=cutoff,
            public_secondary_loader=public_loader,
            grounded_researcher=researcher,
        )
        drain_invocation_log()
        started = time.monotonic()
        with llm_cycle_budget_scope(
            f"v1-grounded-replay-rank-{rank}-{cluster_id}",
            control_root=control_root,
            now=datetime.now(timezone.utc),
        ):
            receipt = adapter(request)
        invocations = drain_invocation_log()
        receipts[cluster_id] = dict(receipt)
        metrics = _research_metrics(receipt)
        candidate_result = {
                "rank": rank,
                "cluster_id": cluster_id,
                "headline_ids": list(attempt.get("headline_ids") or []),
                "headline_proposition": (
                    ((request.get("story_context") or {}).get("leaf_summaries") or [None])[0]
                ),
                "old_evidence_result": attempt.get("status"),
                "old_blockers": list(attempt.get("blockers") or []),
                "new_grounded_research_result": receipt.get("status"),
                "new_blockers": list(receipt.get("blockers") or []),
                "effective_article_mode": request.get("effective_article_mode"),
                **metrics,
                "measured_elapsed_seconds": round(time.monotonic() - started, 3),
                "provider_telemetry": _compact_provider_telemetry(invocations),
            }
        replay_rows.append(candidate_result)
        _write_json(
            checkpoint_path,
            {
                "schema_version": "contentops.v1_grounded_candidate_replay_checkpoint.v1",
                "rank": rank,
                "cluster_id": cluster_id,
                "request_logical_hash": request.get("request_logical_hash"),
                "candidate_result": candidate_result,
                "evidence_receipt": receipt,
                "public_write_performed": False,
            },
        )

    frozen = {
        "schema_version": "contentops.frozen_12_candidate_replay_input.v1",
        "task_label": TASK_LABEL,
        "source_run_id": cycle.get("run_id"),
        "original_cutoff_utc": cutoff,
        "full_rolling_headline_count": full_rolling_headline_count,
        "ranked_candidate_count": 12,
        "source_artifacts": {
            path.name: {"path": str(path), "sha256": _sha256_file(path)}
            for path in (
                cycle_path,
                viability_path,
                assignment_path,
                intake_path,
                preselection_path,
            )
        },
        "ranked_candidates": frozen_rows,
        "public_write_authority": False,
    }
    _write_json(output_dir / "frozen_12_candidate_requests_v1.json", frozen)

    eligible = [row for row in replay_rows if row["new_grounded_research_result"] == "PASS"]
    e2e: dict[str, Any] = {
        "status": "NOT_RUN_NO_RESEARCH_ELIGIBLE_FROZEN_CANDIDATE",
        "public_writes": 0,
        "publishing_adapter_called": False,
    }
    e2e_result_path = output_dir / "zero_write_e2e" / "zero_write_e2e_result_v1.json"
    if eligible and e2e_result_path.exists():
        checkpointed_e2e = _load(e2e_result_path)
        selected = eligible[0]
        if (
            int(checkpointed_e2e.get("selected_rank") or 0) != int(selected["rank"])
            or str(checkpointed_e2e.get("selected_cluster_id") or "")
            != str(selected["cluster_id"])
            or int(checkpointed_e2e.get("public_writes") or 0) != 0
            or bool(checkpointed_e2e.get("publishing_adapter_called"))
            or bool(checkpointed_e2e.get("publication_coordinator_called"))
        ):
            raise ValueError("zero_write_e2e_checkpoint_binding_mismatch")
        e2e = checkpointed_e2e
    if eligible and e2e["status"] == "NOT_RUN_NO_RESEARCH_ELIGIBLE_FROZEN_CANDIDATE":
        selected_row = eligible[0]
        selected_id = str(selected_row["cluster_id"])
        old_attempt = next(
            row for row in attempts if str(row.get("cluster_id") or "") == selected_id
        )
        request = dict(old_attempt.get("request") or {})
        cluster = clusters.get(selected_id) or {
            "cluster_id": selected_id,
            "rank": selected_row["rank"],
            "headline_ids": selected_row["headline_ids"],
            "leaf_summaries": [selected_row.get("headline_proposition")],
        }
        receipt = receipts[selected_id]
        viability = {
            "schema_version": "capital_chronicle.rolling_x_evidence_viability.v1",
            "status": "SUCCESS",
            "decision": "SELECT_STORY",
            "reason_code": "FIRST_VIABLE_RANKED_CLUSTER_SELECTED",
            "selected_cluster_id": selected_id,
            "selected_rank": selected_row["rank"],
            "selected_headline_ids": selected_row["headline_ids"],
            "selected_cluster": cluster,
            "selected_evidence": receipt,
            "rank_attempts": [
                {
                    **dict(old_attempt),
                    "status": "VIABLE",
                    "blockers": [],
                    "evidence_receipt": receipt,
                }
            ],
            "publication_authority_granted": False,
        }
        e2e_dir = output_dir / "zero_write_e2e"
        e2e_dir.mkdir(parents=True, exist_ok=True)
        drain_invocation_log()
        with llm_cycle_budget_scope(
            f"v1-grounded-replay-writer-{selected_id}",
            control_root=control_root,
            now=datetime.now(timezone.utc),
        ):
            built = build_rolling_x_grounded_article_and_media(
                viability, output_dir=e2e_dir
            )
        writer_invocations = drain_invocation_log()
        editorial = pipeline._run_bounded_rolling_x_editorial_cycle(
            article=built["article"],
            media_assets=list((built.get("media") or {}).get("assets") or []),
            editorial_reviewer=lambda _article: (_ for _ in ()).throw(
                AssertionError("ordinary story semantic review must not run")
            ),
            article_reviser=lambda _article, _review, _round: (_ for _ in ()).throw(
                AssertionError("ordinary story revision must not run")
            ),
        )
        final_article = dict(editorial.get("article") or built["article"])
        readiness = {"destinations": {}, "all_required_destinations_ready": False}
        preparation = pipeline._prepare_rolling_x_release_candidate(
            run_id="v1-grounded-frozen-zero-write",
            output_dir=e2e_dir,
            intake=intake,
            assignment=assignment,
            viability=viability,
            article=final_article,
            media=built["media"],
            editorial_cycle=editorial,
            destination_readiness=readiness,
        )
        plan = pipeline._build_rolling_x_publication_plan(
            run_id="v1-grounded-frozen-zero-write",
            output_dir=e2e_dir,
            viability=viability,
            preparation=preparation,
            readiness=readiness,
        )
        (e2e_dir / "article_preview.html").write_text(
            _preview_html(final_article), encoding="utf-8"
        )
        body = str(final_article.get("substack_body_markdown") or "")
        e2e = {
            "status": (
                "PASS_ZERO_WRITE_E2E"
                if editorial.get("status") == "PASS"
                and preparation.get("classification")
                == "PASS_TEXT_IMAGE_RELEASE_CANDIDATE_REHEARSAL"
                else "BLOCKED_ZERO_WRITE_E2E"
            ),
            "selected_rank": selected_row["rank"],
            "selected_cluster_id": selected_id,
            "article_title": final_article.get("title"),
            "article_word_count": len(
                re.findall(r"\b[A-Za-z0-9][A-Za-z0-9'’-]*\b", body)
            ),
            "article_section_count": len(re.findall(r"^##\s+", body, flags=re.MULTILINE)),
            "writer_calls": int(
                (built.get("critical_path_telemetry") or {}).get(
                    "article_writer_semantic_calls"
                )
                or 0
            ),
            "semantic_review_calls": int(
                editorial.get("mandatory_semantic_review_calls") or 0
            ),
            "writer_provider_telemetry": _compact_provider_telemetry(
                writer_invocations
            ),
            "factual_gate": (
                (final_article.get("grounded_source_coverage") or {}).get("status")
            ),
            "reader_value_gate": (
                ((editorial.get("review_history") or [{}])[0].get("deterministic_review") or {})
                .get("reader_value_gate", {})
                .get("classification")
            ),
            "editorial_status": editorial.get("status"),
            "editorial_reason": editorial.get("reason_code"),
            "visual_count": int((built.get("media") or {}).get("media_asset_count") or 0),
            "visual_types": sorted(
                {
                    str(row.get("modality") or row.get("media_class") or "")
                    for row in (built.get("media") or {}).get("assets") or []
                }
                - {""}
            ),
            "release_preparation": preparation.get("classification"),
            "release_blockers": list(preparation.get("blockers") or []),
            "native_derivative_package_count": len(preparation.get("payloads") or {}),
            "native_package_count_including_canonical": 1
            + len(preparation.get("payloads") or {}),
            "publication_plan_destination_count": len(plan.get("destinations") or []),
            "publication_plan_hash": plan.get("plan_hash"),
            "article_markdown_path": str(e2e_dir / "canonical_article.md"),
            "article_preview_path": str(e2e_dir / "article_preview.html"),
            "public_writes": 0,
            "publishing_adapter_called": False,
            "publication_coordinator_called": False,
            "unknown_write": 0,
        }
        _write_json(e2e_result_path, e2e)
        _write_json(e2e_dir / "publication_plan_zero_write_v1.json", plan)

    total_sources = sum(int(row.get("source_count") or 0) for row in replay_rows)
    total_requests = sum(
        int(row.get("public_retrieval_requests") or 0) for row in replay_rows
    )
    total_research_calls = sum(int(row.get("research_calls") or 0) for row in replay_rows)
    replay_provider_attempts = sum(
        int((row.get("provider_telemetry") or {}).get("provider_attempts") or 0)
        for row in replay_rows
    )
    replay_accounted_tokens = sum(
        int(
            ((row.get("provider_telemetry") or {}).get("tokens") or {}).get(
                "total_tokens"
            )
            or 0
        )
        for row in replay_rows
    )
    cc_distribution = {
        state: sum(row.get("cc_context_state") == state for row in replay_rows)
        for state in (
            "CC_CONTEXT_AVAILABLE",
            "CC_CONTEXT_PARTIAL",
            "CC_CONTEXT_NOT_RELEVANT",
            "CC_CONTEXT_UNAVAILABLE",
        )
    }
    result = {
        "schema_version": "contentops.v1_grounded_research_vertical_slice_evidence.v1",
        "task_label": TASK_LABEL,
        "classification": (
            "PASS_V1_GROUNDED_RESEARCH_YIELD_RECOVERED"
            if eligible
            and int(e2e.get("writer_calls") or 0) == 1
            and e2e.get("factual_gate") == "PASS"
            and int(e2e.get("public_writes") or 0) == 0
            and not bool(e2e.get("publishing_adapter_called"))
            and not bool(e2e.get("publication_coordinator_called"))
            and (
                e2e.get("status") == "PASS_ZERO_WRITE_E2E"
                or (
                    e2e.get("status") == "BLOCKED_ZERO_WRITE_E2E"
                    and e2e.get("editorial_status") == "NO_PUBLICATION"
                )
            )
            else "BLOCKED_GROUNDED_RESEARCH_VERTICAL_SLICE"
        ),
        "created_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "source_run_id": cycle.get("run_id"),
        "original_cutoff_utc": cutoff,
        "full_rolling_headline_count": full_rolling_headline_count,
        "frozen_ranked_candidate_count": 12,
        "old_evidence_eligible_count": 0,
        "new_evidence_research_eligible_count": len(eligible),
        "research_calls": total_research_calls,
        "query_plan_calls": sum(
            int(row.get("query_plan_calls") or 0) for row in replay_rows
        ),
        "source_synthesis_calls": sum(
            int(row.get("source_synthesis_calls") or 0) for row in replay_rows
        ),
        "research_provider_attempts": replay_provider_attempts,
        "research_accounted_tokens": replay_accounted_tokens,
        "candidate_receipts_checkpointed": True,
        "average_sources_per_candidate": round(total_sources / 12.0, 3),
        "average_public_retrieval_requests_per_candidate": round(
            total_requests / 12.0, 3
        ),
        "cc_context_availability_distribution": cc_distribution,
        "candidate_results": replay_rows,
        "zero_write_e2e": e2e,
        "budget_telemetry": _budget_telemetry(control_root),
        "effective_grounding_implementation": (
            "DETERMINISTIC_LOCATOR_PLUS_BOUNDED_RETRIEVAL_THEN_SOURCE_SYNTHESIS"
        ),
        "native_provider_grounding_detected": False,
        "public_writes_during_acceptance": 0,
        "publishing_adapter_called": False,
        "publication_coordinator_called": False,
        "unknown_write": 0,
        "pending_reconciliation_created": 0,
    }
    _write_json(output_dir / "grounded_research_vertical_slice_evidence_v1.json", result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-cycle-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument(
        "--capital-chronicle-root", default=r"A:\Capital Chronicle\Main App"
    )
    parser.add_argument("--checkpoint-seed-dir")
    parser.add_argument(
        "--retry-ranks",
        default="",
        help="Comma-separated ranks that must not reuse checkpoint seeds.",
    )
    args = parser.parse_args()
    result = run(args)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if str(result.get("classification") or "").startswith("PASS") else 2


if __name__ == "__main__":
    raise SystemExit(main())
