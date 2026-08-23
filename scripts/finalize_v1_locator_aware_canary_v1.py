"""Finalize the accepted locator-recovery canary without another model or public write.

This task-scoped runner resumes only deterministic release preparation after the one
bounded XHIGH editorial return.  It builds the eight derivative intents, refreshes the
nine exact destination identities/readiness states, and emits the owner launch-gate
record.  It has no publication adapter call path.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from live_contentops._eight_platform_substack_first_pipeline_impl_v1 import (
    _build_rolling_x_publication_plan,
    _prepare_rolling_x_release_candidate,
)
from live_contentops.destination_transport_registry_v1 import DestinationReadinessManager
from live_contentops.mvp_canary_acceptance_v1 import (
    MVP_CANARY_ACCEPTANCE_PROFILE,
    build_mvp_canary_launch_gate_record,
)
from live_contentops.production_orchestrator_v1 import ContentOpsProductionOrchestrator


def _read(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected_json_object:{path.name}")
    return value


def _write(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(dict(value), indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _safe_jit_row(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "destination": row.get("destination"),
        "surface": row.get("surface"),
        "readiness_state": row.get("readiness_state"),
        "write_eligible": row.get("write_eligible"),
        "identity_match": row.get("identity_match"),
        "destination_identity": row.get("destination_identity"),
        "probe_kind": row.get("probe_kind"),
        "sanitized_detail": dict(row.get("sanitized_detail") or {}),
    }


def finalize(*, source_root: Path, output_dir: Path, receipt_path: Path) -> dict[str, Any]:
    frontier = source_root / "frontier_1"
    prior_attempt = frontier / "canonical_zero_write_rehearsal_attempt_2"
    grounded = _read(prior_attempt / "rolling_x_grounded_article_media_v1.json")
    editorial = _read(prior_attempt / "editorial_quality_gate_v1.json")
    viability = _read(frontier / "route_probe" / "rolling_x_ranked_viability_v1.json")
    intake = _read(prior_attempt / "rolling_x_intake_v1.json")
    assignment = _read(prior_attempt / "rolling_x_assignment_v1.json")

    worker_validation = dict(grounded.get("editorial_worker_validation") or {})
    if worker_validation.get("classification") != "PASS_BOUND_XHIGH_EDITORIAL_RETURN":
        raise ValueError("accepted_xhigh_worker_return_required")
    if int(worker_validation.get("bounded_revision_count") or 0) != 1:
        raise ValueError("exactly_one_same_worker_revision_required")

    output_dir.mkdir(parents=True, exist_ok=True)
    run_id = "v1-locator-aware-current-canary-finalization-20260822"
    preparation = _prepare_rolling_x_release_candidate(
        run_id=run_id,
        output_dir=output_dir,
        intake=intake,
        assignment=assignment,
        viability=viability,
        article=dict(grounded.get("article") or {}),
        media=dict(grounded.get("media") or {}),
        editorial_cycle=dict(editorial.get("bounded_revision_cycle") or {}),
        destination_readiness={
            "status": "PENDING_EXACT_JIT",
            "all_required_destinations_ready": False,
            "destinations": {},
            "public_write_performed": False,
        },
        acceptance_profile=MVP_CANARY_ACCEPTANCE_PROFILE,
    )
    if preparation.get("classification") != "PASS_TEXT_IMAGE_RELEASE_CANDIDATE_REHEARSAL":
        raise ValueError("release_candidate_preparation_failed")
    derivative_destinations = tuple(sorted((preparation.get("payloads") or {}).keys()))
    if len(derivative_destinations) != 8:
        raise ValueError("exactly_eight_derivative_intents_required")

    attempt_identity = str((preparation.get("release_candidate_lock") or {}).get("lock_sha256"))
    jit_path = output_dir / "full_v1_transaction_preflight_v1.json"
    jit_reused = False
    if jit_path.is_file():
        jit = _read(jit_path)
        if str(jit.get("attempt_identity") or "") != attempt_identity:
            raise ValueError("existing_jit_attempt_identity_mismatch")
        jit_reused = True
    else:
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
        _write(jit_path, jit)

    plan = _build_rolling_x_publication_plan(
        run_id=run_id,
        output_dir=output_dir,
        viability=viability,
        preparation=preparation,
        readiness=jit,
    )
    _write(output_dir / "publication_plan_v1.json", plan)
    publication_destinations = tuple(
        str(row.get("destination")) for row in plan.get("destinations") or []
    )

    review_history = list((editorial.get("bounded_revision_cycle") or {}).get("review_history") or [])
    if not review_history:
        raise ValueError("mvp_canary_editorial_review_missing")
    editorial_gate = dict(review_history[-1].get("mvp_canary_editorial_gate") or {})
    media = dict((preparation.get("context") or {}).get("media") or {})
    media_assets = list(media.get("assets") or [])
    rights_or_zero_media_pass = bool(
        not media_assets
        or (
            media.get("status") == "PASS"
            and all(
                str(row.get("provenance_status") or "").upper()
                in {"VERIFIED", "PASS", "SOURCE_BACKED", "VERIFIED_SOURCE_BACKED"}
                for row in media_assets
                if isinstance(row, Mapping)
            )
        )
    )
    gate = build_mvp_canary_launch_gate_record(
        editorial_gate=editorial_gate,
        worker_validation=worker_validation,
        derivative_destinations=derivative_destinations,
        publication_plan_destinations=publication_destinations,
        jit_preflight=jit,
        rights_or_zero_media_pass=rights_or_zero_media_pass,
        public_write_count=0,
        unknown_write_count=0,
    )
    _write(output_dir / "mvp_canary_launch_gate_record_v1.json", gate)

    context = dict(preparation.get("context") or {})
    article = dict(context.get("article") or {})
    lock = dict(preparation.get("release_candidate_lock") or {})
    safe_jit = {
        str(destination): _safe_jit_row(dict(row or {}))
        for destination, row in (jit.get("destinations") or {}).items()
    }
    receipt = {
        "schema_version": "contentops.locator_aware_canary_recovery_receipt.v1",
        "task": "TASK_V1_LOCATOR_AWARE_EVIDENCE_YIELD_CANARY_RECOVERY_AND_CANARY_READY_V1",
        "classification": gate.get("classification"),
        "acceptance_profile": MVP_CANARY_ACCEPTANCE_PROFILE,
        "selected_cluster_id": viability.get("selected_cluster_id"),
        "governed_input_hash": worker_validation.get("governed_input_hash"),
        "evidence_document_ids": list(article.get("evidence_document_ids") or []),
        "article": {
            "title": article.get("title"),
            "effective_article_mode": article.get("effective_article_mode"),
            "word_count": article.get("word_count"),
            "canonical_markdown_sha256": article.get("article_markdown_sha256"),
            "canonical_html_sha256": article.get("article_html_sha256"),
            "editorial_seo_package_sha256": (
                context.get("editorial_seo_package") or {}
            ).get("editorial_seo_package_sha256"),
        },
        "editorial_worker": {
            "model": worker_validation.get("worker_model"),
            "reasoning_effort": worker_validation.get("worker_reasoning_effort"),
            "fresh_and_isolated": worker_validation.get("worker_fresh_and_isolated"),
            "bounded_revision_count": worker_validation.get("bounded_revision_count"),
            "same_worker_revision": worker_validation.get("same_xhigh_worker_revision"),
            "worker_return_hash": worker_validation.get("worker_return_hash"),
        },
        "release_candidate": {
            "classification": preparation.get("classification"),
            "lock_sha256": lock.get("lock_sha256"),
            "lock_verification": preparation.get("release_candidate_lock_verification"),
            "derivative_package_intent_count": len(derivative_destinations),
            "derivative_destinations": list(derivative_destinations),
            "derivative_payload_sha256": dict(lock.get("payload_sha256") or {}),
            "publication_plan_destination_count": len(publication_destinations),
            "publication_plan_destinations": list(publication_destinations),
            "article_media_count": len(media_assets),
            "delivery_only_media_count": len(media.get("delivery_only_assets") or []),
        },
        "jit_preflight": {
            "status": jit.get("status"),
            "all_required_destinations_ready": jit.get("all_required_destinations_ready"),
            "active_exact_destination_probes": jit.get("active_exact_destination_probes"),
            "existing_exact_attempt_receipt_reused": jit_reused,
            "destinations": safe_jit,
        },
        "launch_gate": gate,
        "public_write_count": 0,
        "provider_write_count": 0,
        "unknown_write_count": 0,
        "public_write_authority": False,
        "owner_public_write_grant_present": False,
        "raw_artifacts_committed": False,
    }
    _write(receipt_path, receipt)
    receipt["receipt_sha256"] = _sha256(receipt_path)
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    result = finalize(
        source_root=args.source_root.resolve(),
        output_dir=args.output_dir.resolve(),
        receipt_path=args.receipt.resolve(),
    )
    print(json.dumps({
        "classification": result["classification"],
        "jit_status": result["jit_preflight"]["status"],
        "derivative_package_intent_count": result["release_candidate"]["derivative_package_intent_count"],
        "publication_plan_destination_count": result["release_candidate"]["publication_plan_destination_count"],
        "public_write_count": result["public_write_count"],
        "unknown_write_count": result["unknown_write_count"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
