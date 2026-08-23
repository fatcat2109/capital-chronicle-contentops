"""Validate one frozen Italy Desktop-primary canary with zero public writes."""

# ruff: noqa: E402
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from live_contentops._eight_platform_substack_first_pipeline_impl_v1 import (
    _build_rolling_x_publication_plan,
    _run_rolling_x_newsroom_cycle,
)
from live_contentops.codex_desktop_newsroom_operator_v1 import (
    arbitrate_hybrid_editorial_execution,
    build_hybrid_editorial_run_identity,
)
from live_contentops.destination_transport_registry_v1 import (
    DestinationReadinessManager,
    V1_REQUIRED_PUBLICATION_DESTINATIONS,
)
from live_contentops.mvp_canary_acceptance_v1 import (
    MVP_CANARY_ACCEPTANCE_PROFILE,
    evaluate_mvp_canary_minimum_useful_floor,
)
from live_contentops.production_orchestrator_v1 import ContentOpsProductionOrchestrator
from live_contentops.rolling_x_grounded_article_media_builder_v1 import (
    build_rolling_x_grounded_article_and_media,
    extract_governed_story_context,
    normalize_article_transport_representation,
    resolve_article_transport_envelope,
)
from scripts.prove_v1_official_codex_direct_provider_canary_v1 import (
    _ready_override,
    _safe_jit,
)
from scripts.run_v1_current_multi_frontier_floor_rehearsal import (
    _semantic_resume_checkpoints_from_probe,
)
from live_contentops.tier1_editorial_quality_v1 import LLM_REVIEW_CHECKS


TASK = "TASK_V1_DESKTOP_PRIMARY_HYBRID_EDITORIAL_PARITY_AND_FINAL_CANARY_READY_V1"
CLASSIFICATION = "PASS_DESKTOP_PRIMARY_HYBRID_EDITORIAL_PARITY_AND_FINAL_CANARY_READY"
EXPECTED_TITLE = "State Department Approves Possible APKWS II Sale to Italy"
EXPECTED_EVIDENCE_ID = "official-primary-ffb8e742e0932254c29d"
EXPECTED_MODE = "DATA_OR_DOCUMENT_LENS"
CANONICAL_URL = (
    "https://capitalchronicle.substack.com/p/"
    "state-department-approves-possible-apkws-ii-sale-italy"
)


def _read(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected_json_object:{path}")
    return value


def _write(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(dict(value), indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _hash(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, default=str
        ).encode("utf-8")
    ).hexdigest()


def _file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class _DesktopWorkerArticleBuilder:
    """Project one already-completed Desktop worker return through the canonical builder."""

    def __init__(self, *, worker_return: Mapping[str, Any], output_dir: Path) -> None:
        self.worker_return = dict(worker_return)
        self.output_dir = output_dir
        self.call_count = 0

    def __call__(self, viability: Mapping[str, Any]) -> dict[str, Any]:
        self.call_count += 1
        if self.call_count != 1:
            raise ValueError("desktop_canary_exactly_one_worker_return_required")
        worker_request = dict(viability.get("editorial_worker_request") or {})
        governed_input_hash = str(worker_request.get("governed_input_hash") or "")
        if governed_input_hash != str(self.worker_return.get("governed_input_hash") or ""):
            raise ValueError("desktop_canary_governed_input_hash_mismatch")
        generated = normalize_article_transport_representation(
            resolve_article_transport_envelope(self.worker_return),
            context=extract_governed_story_context(viability),
        )
        built = build_rolling_x_grounded_article_and_media(
            viability,
            output_dir=self.output_dir,
            article_generator=lambda _prompt: generated,
            required_asset_count=0,
        )
        bound_return = {
            key: value
            for key, value in self.worker_return.items()
            if key != "article"
        }
        bound_return["article"] = dict(built["article"])
        return {
            **built,
            "editorial_worker_receipt": bound_return,
            "desktop_worker_execution_receipt": {
                key: self.worker_return.get(key)
                for key in (
                    "model",
                    "reasoning_effort",
                    "fresh",
                    "isolated",
                    "bounded_revision_count",
                    "public_write_attempted",
                    "worker_task_name",
                    "worker_task_hash",
                    "creation_method",
                )
            },
        }


def _title_occurrences(payload: Mapping[str, Any]) -> int:
    public_text = str(payload.get("full_text") or payload.get("text") or "")
    return public_text.count(EXPECTED_TITLE)


def prove(
    *,
    source_artifact_dir: Path,
    worker_return_path: Path,
    coordinator_review_path: Path,
    output_dir: Path,
    evidence_dir: Path,
) -> dict[str, Any]:
    worker_return = _read(worker_return_path)
    coordinator_review = _read(coordinator_review_path)
    if (
        worker_return.get("model") != "gpt-5.6-sol"
        or str(worker_return.get("reasoning_effort") or "").upper() != "XHIGH"
        or worker_return.get("fresh") is not True
        or worker_return.get("isolated") is not True
        or int(worker_return.get("bounded_revision_count") or 0) not in {0, 1}
        or worker_return.get("public_write_attempted") is not False
    ):
        raise ValueError("desktop_canary_worker_receipt_invalid")
    if int(worker_return.get("bounded_revision_count") or 0) == 1 and len(
        str(worker_return.get("same_worker_revision_of_return_hash") or "")
    ) != 64:
        raise ValueError("desktop_canary_same_worker_revision_binding_required")
    review_checks = dict(coordinator_review.get("checks") or {})
    if (
        coordinator_review.get("schema_version")
        != "contentops.desktop_high_coordinator_final_review.v1"
        or coordinator_review.get("coordinator_model") != "gpt-5.6-sol"
        or str(coordinator_review.get("coordinator_reasoning_effort") or "").upper()
        != "HIGH"
        or coordinator_review.get("same_fresh_standalone_task") is not True
        or coordinator_review.get("governed_input_hash")
        != worker_return.get("governed_input_hash")
        or coordinator_review.get("status") != "SUCCESS"
        or coordinator_review.get("decision") != "PASS"
        or set(review_checks) != set(LLM_REVIEW_CHECKS)
        or any(review_checks.get(check) is not True for check in (
            "material_claims_supported",
            "no_factual_contradiction",
            "no_fabricated_numbers",
            "material_evidence_matches",
            "no_misleading_framing",
            "severe_coherence_ok",
            "no_unsupported_certainty",
            "no_fabricated_quotes",
            "no_financial_advice",
        ))
        or int(coordinator_review.get("xhigh_worker_count") or 0) != 1
        or int(coordinator_review.get("bounded_revision_count") or 0) != 1
        or coordinator_review.get("new_worker_created") is not False
        or coordinator_review.get("new_evidence_acquired") is not False
        or coordinator_review.get("public_write_attempted") is not False
        or coordinator_review.get("publication_authority") is not False
    ):
        raise ValueError("desktop_high_coordinator_review_invalid")

    probe = _read(source_artifact_dir / "rolling_x_newsroom_cycle_evidence_v1.json")
    rolling = _read(source_artifact_dir / "rolling_x_intake_v1.json")
    prepared = _read(source_artifact_dir / "rolling_x_prepared_candidate_state_v1.json")
    viability = _read(source_artifact_dir / "rolling_x_ranked_viability_v1.json")
    evidence_ids = {
        str(row.get("document_id") or "")
        for row in (viability.get("selected_evidence") or {}).get("evidence_documents") or []
        if isinstance(row, Mapping)
    }
    if evidence_ids != {EXPECTED_EVIDENCE_ID}:
        raise ValueError("exact_italy_evidence_identity_required")
    leaf_checkpoints, global_checkpoint, story_types = (
        _semantic_resume_checkpoints_from_probe(probe)
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    builder = _DesktopWorkerArticleBuilder(
        worker_return=worker_return,
        output_dir=output_dir,
    )

    def desktop_high_review(article: Mapping[str, Any]) -> dict[str, Any]:
        if _hash(dict(article)) != str(
            coordinator_review.get("integrated_article_sha256") or ""
        ):
            raise ValueError("desktop_high_coordinator_article_binding_mismatch")
        return {
            **coordinator_review,
            "provider": "DESKTOP_HIGH_COORDINATOR_FRESH_STANDALONE",
            "publication_authority": False,
        }
    # This proof is intentionally bound to the exact accepted Italy packet that the
    # Desktop worker received.  Seed the canonical viability checkpoint so replay does
    # not refetch an equivalent page with new transport bytes/identity metadata.
    _write(output_dir / "rolling_x_ranked_viability_v1.json", viability)
    run_id = "v1-desktop-primary-hybrid-italy-final-zero-write-canary"
    result = _run_rolling_x_newsroom_cycle(
        run_id=run_id,
        output_dir=output_dir,
        cutoff_utc=str(rolling.get("cutoff_time_utc") or ""),
        rolling_input=rolling,
        prepared_candidate_state=prepared,
        leaf_checkpoints=leaf_checkpoints,
        global_checkpoint=global_checkpoint,
        story_type_by_cluster=story_types,
        article_builder=builder,
        editorial_reviewer=desktop_high_review,
        publication_enabled=True,
        operating_mode="KILL_SWITCH",
        destination_readiness_override=_ready_override(),
        acceptance_profile=MVP_CANARY_ACCEPTANCE_PROFILE,
    )
    if result.get("classification") != "PASS_PUBLICATION_PLAN_READY":
        raise ValueError(
            "desktop_primary_canary_pipeline_failed:"
            + str(result.get("exact_next_blocker") or result.get("classification"))
        )
    preparation = dict(result.get("release_candidate_preparation") or {})
    context = dict(preparation.get("context") or {})
    article = dict(context.get("article") or {})
    payloads = dict(preparation.get("payloads") or {})
    if article.get("title") != EXPECTED_TITLE:
        raise ValueError("exact_canary_title_mismatch")
    if article.get("effective_article_mode") != EXPECTED_MODE:
        raise ValueError("exact_canary_mode_mismatch")
    if set(article.get("evidence_document_ids") or []) != {EXPECTED_EVIDENCE_ID}:
        raise ValueError("exact_canary_article_evidence_identity_mismatch")
    source_resolution = dict(article.get("source_reference_resolution") or {})
    if (
        source_resolution.get("status") != "PASS"
        or int(source_resolution.get("unknown_source_handle_count") or 0) != 0
        or int(source_resolution.get("unbound_source_url_count") or 0) != 0
        or "[[SOURCE:" in str(article.get("substack_body_markdown") or "")
    ):
        raise ValueError("desktop_canary_source_resolution_invalid")
    usefulness = evaluate_mvp_canary_minimum_useful_floor(article)
    if usefulness.get("classification") != "PASS":
        raise ValueError("desktop_canary_mode_aware_usefulness_failed")
    if len(payloads) != 8 or sorted(payloads) != sorted(
        set(V1_REQUIRED_PUBLICATION_DESTINATIONS) - {"substack"}
    ):
        raise ValueError("desktop_canary_exact_eight_derivatives_required")
    title_occurrences = {
        destination: _title_occurrences(payload)
        for destination, payload in sorted(payloads.items())
    }
    if any(count != 1 for count in title_occurrences.values()):
        raise ValueError("desktop_canary_derivative_title_equivalence_not_removed")

    media = dict(context.get("media") or {})
    if int(media.get("article_media_count") or 0) != 0:
        raise ValueError("desktop_canary_article_media_must_be_zero")
    lock = dict(preparation.get("release_candidate_lock") or {})
    attempt_identity = str(lock.get("lock_sha256") or "")
    orchestrator = ContentOpsProductionOrchestrator()
    readiness_manager = DestinationReadinessManager(
        store=None,
        edge_runtime_ensurer=lambda **kwargs: orchestrator.execute(
            "ensure_canonical_edge_publishing_runtime", **kwargs
        ),
    )
    jit = readiness_manager.verify_full_v1_transaction_preflight(
        attempt_identity=attempt_identity,
        persist=False,
    )
    _write(output_dir / "full_v1_transaction_preflight_v1.json", jit)
    if (
        jit.get("status") != "READY"
        or jit.get("all_required_destinations_ready") is not True
        or int(jit.get("unknown_write_count") or 0) != 0
        or jit.get("public_write_performed") is not False
    ):
        raise ValueError("desktop_canary_current_nine_surface_jit_not_ready")
    plan = _build_rolling_x_publication_plan(
        run_id=run_id,
        output_dir=output_dir,
        viability=viability,
        preparation=preparation,
        readiness=jit,
    )
    _write(output_dir / "publication_plan_current_jit_v1.json", plan)
    if {
        str(row.get("destination") or "")
        for row in plan.get("destinations") or []
        if isinstance(row, Mapping)
    } != set(V1_REQUIRED_PUBLICATION_DESTINATIONS):
        raise ValueError("desktop_canary_exact_nine_destination_plan_required")

    grounded = _read(output_dir / "rolling_x_grounded_article_media_v1.json")
    worker_validation = dict(grounded.get("editorial_worker_validation") or {})
    if worker_validation.get("classification") != "PASS_BOUND_XHIGH_EDITORIAL_RETURN":
        raise ValueError("desktop_canary_bound_worker_validation_failed")
    now = datetime.now(timezone.utc)
    run_identity = build_hybrid_editorial_run_identity(
        runtime_run_id=run_id,
        production_day_id="2026-08-22",
        opportunity_id="OWNER_BOUNDED_DESKTOP_PARITY_CANARY",
        story_identity=EXPECTED_EVIDENCE_ID,
        governed_input_hash=str(worker_return.get("governed_input_hash") or ""),
    )
    arbitration = arbitrate_hybrid_editorial_execution(
        run_identity=run_identity,
        observed_at_utc=now,
        valid_window_ends_at_utc=now + timedelta(minutes=1),
        desktop_primary_receipt={
            "canonical_run_identity": run_identity["canonical_run_identity"],
            "state": "ACCEPTED",
            "completed_at_utc": now,
        },
    )
    if arbitration.get("decision") != "ACCEPT_DESKTOP_PRIMARY":
        raise ValueError("desktop_canary_primary_arbitration_failed")

    old_article = _read(source_artifact_dir / "article_manifest_v1.json")
    old_usefulness = evaluate_mvp_canary_minimum_useful_floor(old_article)
    old_payloads = _read(source_artifact_dir / "native_payloads_rehearsal_v1.json")
    source_documents = list(
        (viability.get("selected_evidence") or {}).get("evidence_documents") or []
    )
    source_words = sum(
        len(str(row.get("canonical_content_text") or "").split())
        for row in source_documents
        if isinstance(row, Mapping)
    )

    article_markdown_path = output_dir / "canonical_article.md"
    article_html_path = output_dir / "canonical_article.html"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    (evidence_dir / "article.md").write_bytes(article_markdown_path.read_bytes())
    (evidence_dir / "canonical_article.html").write_bytes(article_html_path.read_bytes())
    _write(evidence_dir / "derivative_payloads_v1.json", payloads)
    receipt = {
        "schema_version": "contentops.desktop_primary_hybrid_final_canary_receipt.v1",
        "task": TASK,
        "classification": CLASSIFICATION,
        "source_artifact_dir": str(source_artifact_dir),
        "source_evidence_id": EXPECTED_EVIDENCE_ID,
        "evidence_projection": {
            "classification": "SUFFICIENT_EXISTING_BOUNDED_PROJECTION_NO_CHANGE_REQUIRED",
            "accepted_source_document_count": len(source_documents),
            "accepted_source_canonical_content_word_count": source_words,
            "new_evidence_acquired": False,
            "projection_code_changed": False,
        },
        "desktop_coordinator": {
            "model": "gpt-5.6-sol",
            "reasoning_effort": "HIGH",
            "fresh_standalone_task": True,
            "calendar_time_automation_execution_claimed": False,
            "final_review": coordinator_review,
            "final_review_sha256": _hash(coordinator_review),
        },
        "desktop_worker": {
            "model": worker_return.get("model"),
            "reasoning_effort": worker_return.get("reasoning_effort"),
            "fresh": worker_return.get("fresh"),
            "isolated": worker_return.get("isolated"),
            "bounded_revision_count": worker_return.get("bounded_revision_count"),
            "worker_task_name": worker_return.get("worker_task_name"),
            "worker_task_hash": worker_return.get("worker_task_hash"),
            "creation_method": worker_return.get("creation_method"),
            "worker_return_sha256": _hash(worker_return),
            "validation": worker_validation,
            "public_write_attempted": False,
        },
        "governed_input_hash": worker_return.get("governed_input_hash"),
        "hybrid_arbitration": arbitration,
        "article": {
            "title": article.get("title"),
            "effective_article_mode": article.get("effective_article_mode"),
            "canonical_url": article.get("canonical_url"),
            "evidence_document_ids": article.get("evidence_document_ids"),
            "canonical_markdown_sha256": _file_hash(article_markdown_path),
            "canonical_html_sha256": _file_hash(article_html_path),
            "resolved_article_sha256": _hash(article),
            "source_reference_resolution": source_resolution,
            "mode_aware_minimum_usefulness": usefulness,
            "institutional_edge_validation": article.get(
                "institutional_edge_editorial_validation"
            ),
            "canonical_article_media_count": int(media.get("article_media_count") or 0),
        },
        "sdk_comparison": {
            "sdk_canonical_markdown_sha256": _file_hash(
                source_artifact_dir / "canonical_article.md"
            ),
            "sdk_mode_aware_minimum_usefulness": old_usefulness,
            "sdk_derivative_title_occurrences": {
                destination: _title_occurrences(payload)
                for destination, payload in sorted(old_payloads.items())
                if isinstance(payload, Mapping)
            },
            "desktop_canonical_markdown_sha256": _file_hash(article_markdown_path),
            "desktop_derivative_title_occurrences": title_occurrences,
            "comparison_is_quality_semantics_not_wording": True,
        },
        "release": {
            "release_lock_sha256": attempt_identity,
            "derivative_package_count": len(payloads),
            "derivative_destinations": sorted(payloads),
            "derivative_payload_sha256": {
                destination: _hash(payload)
                for destination, payload in sorted(payloads.items())
            },
            "publication_plan_destination_count": len(plan.get("destinations") or []),
            "derivative_title_occurrences": title_occurrences,
        },
        "jit_preflight": _safe_jit(jit),
        "model_worker_count": 1,
        "public_write_count": 0,
        "provider_publication_write_count": 0,
        "unknown_write_count": 0,
        "owner_public_write_grant_present": False,
        "automation_enablement_authorized": False,
        "four_thirty_two_campaign_started": False,
    }
    _write(evidence_dir / "canary_receipt_v1.json", receipt)
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-artifact-dir", type=Path, required=True)
    parser.add_argument("--worker-return", type=Path, required=True)
    parser.add_argument("--coordinator-review", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--evidence-dir", type=Path, required=True)
    args = parser.parse_args()
    receipt = prove(
        source_artifact_dir=args.source_artifact_dir.resolve(),
        worker_return_path=args.worker_return.resolve(),
        coordinator_review_path=args.coordinator_review.resolve(),
        output_dir=args.output_dir.resolve(),
        evidence_dir=args.evidence_dir.resolve(),
    )
    print(
        json.dumps(
            {
                "classification": receipt["classification"],
                "article": receipt["article"],
                "release": receipt["release"],
                "jit_status": receipt["jit_preflight"]["status"],
                "public_write_count": receipt["public_write_count"],
                "unknown_write_count": receipt["unknown_write_count"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
