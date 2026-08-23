"""Run the single current-head Italy direct-provider canary with zero public writes."""

# ruff: noqa: E402
from __future__ import annotations

import argparse
import hashlib
import json
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
from live_contentops.claim_evidence_contract_v1 import build_claim_evidence_contract
from live_contentops.destination_transport_registry_v1 import (
    DestinationReadinessManager,
    V1_REQUIRED_PUBLICATION_DESTINATIONS,
)
from live_contentops.mvp_canary_acceptance_v1 import MVP_CANARY_ACCEPTANCE_PROFILE
from live_contentops.official_codex_provider_v1 import (
    MODEL,
    EFFORT,
    OfficialCodexEditorialArticleBuilder,
)
from live_contentops.production_orchestrator_v1 import ContentOpsProductionOrchestrator
from scripts.run_v1_current_multi_frontier_floor_rehearsal import (
    _semantic_resume_checkpoints_from_probe,
)


TASK = (
    "TASK_V1_OFFICIAL_CODEX_ARTICLE_CONTRACT_RELIABILITY_AND_AUTONOMOUS_CANARY_CLOSEOUT_V1"
)
CLASSIFICATION = (
    "PASS_OFFICIAL_CODEX_DIRECT_PROVIDER_CURRENT_HEAD_CANARY_VERTICAL_PROOF"
)
EXPECTED_TITLE = "State Department Approves Possible APKWS II Sale to Italy"
EXPECTED_EVIDENCE_ID = "official-primary-ffb8e742e0932254c29d"
EXPECTED_MODE = "DATA_OR_DOCUMENT_LENS"


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


def _ready_override() -> dict[str, Any]:
    return {
        "all_required_destinations_ready": True,
        "destinations": {
            destination: {
                "readiness_state": "READY_REHEARSAL_OVERRIDE_NO_WRITE_AUTHORITY",
                "write_eligible": True,
                "identity_match": True,
            }
            for destination in V1_REQUIRED_PUBLICATION_DESTINATIONS
        },
        "fixture_bound": True,
        "publication_authority": False,
    }


def _rebuild_current_viability(
    source_root: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    route_probe = source_root / "route_probe"
    viability = _read(route_probe / "rolling_x_ranked_viability_v1.json")
    selected_rank = int(viability.get("selected_rank") or 0)
    selected_attempt = next(
        dict(row)
        for row in viability.get("rank_attempts") or []
        if int(row.get("rank") or 0) == selected_rank
    )
    request = dict(selected_attempt.get("request") or {})
    selected_evidence = dict(viability.get("selected_evidence") or {})
    documents = [
        dict(row)
        for row in selected_evidence.get("evidence_documents") or []
        if isinstance(row, Mapping)
    ]
    if [str(row.get("document_id") or "") for row in documents] != [
        EXPECTED_EVIDENCE_ID
    ]:
        raise ValueError("exact_italy_evidence_identity_required")
    # Revalidate the prior accepted evidence-derived propositions against the current exact
    # document bytes. The rejected numeric-scope residual is deliberately not admitted as a
    # candidate. This is a current-code rebuild, not a mutation of model input or output.
    prior_contract = dict(selected_evidence.get("claim_evidence_contract") or {})
    prior_evidence_claims = [
        str(row.get("claim_text") or "")
        for row in prior_contract.get("supported_claims") or []
        if row.get("support_status") != "SUPPORTED_WITH_NUMERIC_SCOPE_OMITTED"
        and str(row.get("claim_text") or "")
    ]
    story_context = dict(request.get("story_context") or {})
    story_context["leaf_summaries"] = list(
        dict.fromkeys(
            [
                *prior_evidence_claims,
                *[
                    str(value)
                    for value in story_context.get("leaf_summaries") or []
                    if str(value)
                ],
            ]
        )
    )
    request["story_context"] = story_context
    contract = build_claim_evidence_contract(request, documents)
    forbidden = ("Norway", "South Korea", "simultaneously", "coordinated")
    if any(
        row.get("support_status") == "SUPPORTED_WITH_NUMERIC_SCOPE_OMITTED"
        and any(marker in str(row.get("claim_text") or "") for marker in forbidden)
        for row in contract.get("supported_claims") or []
    ):
        raise ValueError("false_residual_claim_support_survived_current_rebuild")
    selected_evidence["claim_evidence_contract"] = contract
    selected_evidence["status"] = (
        "PASS" if contract.get("status") == "PASS" else "BLOCKED"
    )
    selected_evidence["blockers"] = list(contract.get("blocked_claims") or [])
    if selected_evidence["status"] != "PASS":
        raise ValueError("corrected_italy_claim_contract_blocked")
    viability["selected_evidence"] = selected_evidence
    for index, row in enumerate(viability.get("rank_attempts") or []):
        if int(row.get("rank") or 0) != selected_rank:
            continue
        corrected_attempt = dict(row)
        corrected_attempt["evidence_receipt"] = selected_evidence
        corrected_attempt["evidence_receipt_sha256"] = _hash(selected_evidence)
        viability["rank_attempts"][index] = corrected_attempt
    viability.pop("viability_logical_hash", None)
    viability["viability_logical_hash"] = _hash(viability)
    return viability, contract


def _safe_jit(jit: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "status": jit.get("status"),
        "all_required_destinations_ready": jit.get("all_required_destinations_ready"),
        "active_exact_destination_probes": jit.get("active_exact_destination_probes"),
        "attempt_identity": jit.get("attempt_identity"),
        "destinations": {
            str(name): {
                "destination": row.get("destination"),
                "surface": row.get("surface"),
                "readiness_state": row.get("readiness_state"),
                "write_eligible": row.get("write_eligible"),
                "identity_match": row.get("identity_match"),
                "destination_identity": row.get("destination_identity"),
                "probe_kind": row.get("probe_kind"),
                "sanitized_detail": dict(row.get("sanitized_detail") or {}),
            }
            for name, row in (jit.get("destinations") or {}).items()
        },
        "public_write_performed": False,
    }


def prove(
    *,
    source_root: Path,
    output_dir: Path,
    receipt_path: Path,
    resume_existing: bool = False,
) -> dict[str, Any]:
    if resume_existing:
        result = _read(output_dir / "rolling_x_newsroom_cycle_evidence_v1.json")
        viability = _read(output_dir / "rolling_x_ranked_viability_v1.json")
        claim_contract = dict(
            (viability.get("selected_evidence") or {}).get(
                "claim_evidence_contract"
            )
            or {}
        )
        grounded_for_preflight = _read(
            output_dir / "rolling_x_grounded_article_media_v1.json"
        )
        completed_turn = dict(
            (
                grounded_for_preflight.get("editorial_worker_receipt") or {}
            ).get("official_codex_turn_receipt")
            or {}
        )
        preflight = {
            "status": "PASS_REUSED_COMPLETED_TURN_RECEIPT_NO_NEW_MODEL_CALL",
            "provider": completed_turn.get("provider"),
            "transport": completed_turn.get("transport"),
            "sdk_version": completed_turn.get("sdk_version"),
            "auth_classification": completed_turn.get("auth_classification"),
            "api_key_fallback_calls": completed_turn.get("api_key_fallback_calls"),
            "model": completed_turn.get("model"),
            "reasoning_effort": completed_turn.get("reasoning_effort"),
        }
    else:
        route_probe = source_root / "route_probe"
        probe = _read(route_probe / "rolling_x_newsroom_cycle_evidence_v1.json")
        rolling = dict(probe.get("intake") or {})
        prepared = _read(route_probe / "rolling_x_prepared_candidate_state_v1.json")
        viability, claim_contract = _rebuild_current_viability(source_root)
        leaf_checkpoints, global_checkpoint, story_types = (
            _semantic_resume_checkpoints_from_probe(probe)
        )
        output_dir.mkdir(parents=True, exist_ok=True)
        _write(output_dir / "rolling_x_ranked_viability_v1.json", viability)
        with OfficialCodexEditorialArticleBuilder(
            output_dir=output_dir,
            required_title=EXPECTED_TITLE,
        ) as article_builder:
            preflight = article_builder.preflight()
            result = _run_rolling_x_newsroom_cycle(
                run_id="v1-official-codex-direct-provider-italy-current-head-canary",
                output_dir=output_dir,
                cutoff_utc=str(rolling.get("cutoff_time_utc") or ""),
                rolling_input=rolling,
                prepared_candidate_state=prepared,
                leaf_checkpoints=leaf_checkpoints,
                global_checkpoint=global_checkpoint,
                story_type_by_cluster=story_types,
                article_builder=article_builder,
                publication_enabled=True,
                operating_mode="KILL_SWITCH",
                destination_readiness_override=_ready_override(),
                acceptance_profile=MVP_CANARY_ACCEPTANCE_PROFILE,
            )
    if result.get("classification") != "PASS_PUBLICATION_PLAN_READY":
        raise ValueError(
            "direct_provider_canary_pipeline_failed:"
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
    if "[[SOURCE:" in str(article.get("substack_body_markdown") or ""):
        raise ValueError("raw_source_marker_reached_canonical_article")
    public_copy = "\n".join(
        str(article.get(key) or "")
        for key in (
            "title",
            "subtitle",
            "seo_title",
            "meta_description",
            "social_lede",
            "substack_body_markdown",
        )
    )
    epistemic_claims = list(article.get("epistemic_claims") or [])
    if not epistemic_claims or any(
        " ".join(str(row.get("text") or "").split()).casefold()
        not in " ".join(public_copy.split()).casefold()
        for row in epistemic_claims
        if isinstance(row, Mapping)
    ):
        raise ValueError("epistemic_claims_must_be_present_in_public_copy")
    institutional = dict(article.get("institutional_edge_editorial_validation") or {})
    if institutional.get("classification") != "PASS":
        raise ValueError("institutional_edge_validation_must_pass")
    structured = dict(article.get("structured_data_packet") or {})
    if (
        structured.get("headline") != article.get("title")
        or structured.get("description") != article.get("meta_description")
        or structured.get("author") != "Capital Chronicle"
        or structured.get("publisher") != "Capital Chronicle"
        or structured.get("publication_time_binding")
        != "COORDINATOR_MUST_BIND_EXACT_TIMESTAMP_BEFORE_EMISSION"
        or structured.get("eligible_for_emission") is not False
    ):
        raise ValueError("structured_data_visible_identity_date_binding_invalid")
    if any(
        marker.casefold() in public_copy.casefold()
        for marker in ("Norway", "South Korea", "simultaneously", "coordinated")
    ):
        raise ValueError("false_multi_country_residual_reintroduced")
    if len(payloads) != 8 or "pending-publication" in json.dumps(payloads):
        raise ValueError("exact_eight_real_path_derivative_packages_required")
    media = dict(context.get("media") or {})
    if int(media.get("article_media_count") or 0) != 0:
        raise ValueError("canonical_substack_media_must_be_zero")
    if any(
        row.get("canonical_article_media")
        for row in media.get("delivery_only_assets") or []
    ):
        raise ValueError("delivery_only_card_became_canonical_media")

    lock = dict(preparation.get("release_candidate_lock") or {})
    attempt_identity = str(lock.get("lock_sha256") or "")
    jit_path = output_dir / "full_v1_transaction_preflight_v1.json"
    if resume_existing and jit_path.exists():
        jit = _read(jit_path)
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
    if (
        str(jit.get("status") or "") != "READY"
        or jit.get("all_required_destinations_ready") is not True
        or int(jit.get("unknown_write_count") or 0) != 0
        or jit.get("public_write_performed") is not False
    ):
        raise ValueError("full_v1_transaction_preflight_not_ready")
    plan = _build_rolling_x_publication_plan(
        run_id="v1-official-codex-direct-provider-italy-current-head-canary",
        output_dir=output_dir,
        viability=viability,
        preparation=preparation,
        readiness=jit,
    )
    _write(output_dir / "publication_plan_current_jit_v1.json", plan)
    plan_destinations = {
        str(row.get("destination") or "")
        for row in plan.get("destinations") or []
        if isinstance(row, dict)
    }
    if plan_destinations != set(V1_REQUIRED_PUBLICATION_DESTINATIONS):
        raise ValueError("publication_plan_exact_nine_destinations_required")
    grounded = _read(output_dir / "rolling_x_grounded_article_media_v1.json")
    worker = dict(grounded.get("editorial_worker_receipt") or {})
    validation = dict(grounded.get("editorial_worker_validation") or {})
    turn = dict(worker.get("official_codex_turn_receipt") or {})
    initial_turn = dict(worker.get("initial_official_codex_turn_receipt") or turn)
    revision_count = int(validation.get("bounded_revision_count") or 0)
    direct_turns = 1 + revision_count
    if direct_turns not in {1, 2} or revision_count not in {0, 1}:
        raise ValueError("direct_provider_turn_budget_invalid")
    canonical_url = str(article.get("canonical_url") or "")
    receipt = {
        "schema_version": "contentops.official_codex_direct_provider_canary_receipt.v1",
        "task": TASK,
        "classification": CLASSIFICATION,
        "fetched_starting_branch_commit": (
            "626e4f35252b52025ce2a15c9634fcb38f4d4f86"
        ),
        "provider_preflight": preflight,
        "provider": {
            "transport": turn.get("transport"),
            "sdk_version": turn.get("sdk_version"),
            "runtime_version": turn.get("runtime_version"),
            "auth_classification": turn.get("auth_classification"),
            "api_key_fallback_calls": turn.get("api_key_fallback_calls"),
            "model": MODEL,
            "reasoning_effort": EFFORT.upper(),
            "fresh_isolated_thread_count": 1,
            "direct_turn_count": direct_turns,
            "same_thread_revision_count": revision_count,
            "thread_id_hash": turn.get("thread_id_hash"),
            "turn_result_is_primary_authority": turn.get(
                "turn_result_is_primary_authority"
            ),
            "thread_read_include_turns": turn.get("thread_read_include_turns"),
            "post_turn_metadata_status": turn.get("post_turn_metadata_status"),
            "usage": turn.get("turn_result_usage"),
            "duration_ms": turn.get("turn_result_duration_ms"),
            "raw_turn_result_sha256": turn.get("turn_result_final_response_sha256"),
            "transport_schema_sha256": turn.get("transport_schema_sha256"),
            "transport_schema_top_level_property_count": turn.get(
                "transport_schema_top_level_property_count"
            ),
            "developer_instruction_sha256": turn.get(
                "developer_instruction_sha256"
            ),
            "provider_input_identity_sha256": turn.get(
                "provider_input_identity_sha256"
            ),
            "raw_model_article_sha256": worker.get("raw_model_article_sha256"),
            "raw_worker_body_sha256": worker.get("raw_worker_body_sha256"),
            "resolved_public_body_sha256": worker.get("resolved_public_body_sha256"),
            "gemini_formatter_calls": turn.get("gemini_formatter_calls"),
            "initial_turn": {
                "turn_index": initial_turn.get("turn_index"),
                "turn_result_final_response_sha256": initial_turn.get(
                    "turn_result_final_response_sha256"
                ),
                "structured_output_sha256": initial_turn.get(
                    "structured_output_sha256"
                ),
                "normalized_article_sha256": initial_turn.get(
                    "normalized_article_sha256"
                ),
                "usage": initial_turn.get("turn_result_usage"),
                "duration_ms": initial_turn.get("turn_result_duration_ms"),
            },
            "revision_turn": (
                {
                    "turn_index": turn.get("turn_index"),
                    "turn_result_final_response_sha256": turn.get(
                        "turn_result_final_response_sha256"
                    ),
                    "structured_output_sha256": turn.get(
                        "structured_output_sha256"
                    ),
                    "normalized_article_sha256": turn.get(
                        "normalized_article_sha256"
                    ),
                    "usage": turn.get("turn_result_usage"),
                    "duration_ms": turn.get("turn_result_duration_ms"),
                }
                if revision_count
                else None
            ),
            "initial_deterministic_blockers": list(
                worker.get("initial_deterministic_blockers") or []
            ),
        },
        "claim_correction": {
            "claim_contract_sha256": claim_contract.get("claim_contract_sha256"),
            "supported_claim_count": claim_contract.get("supported_claim_count"),
            "omitted_claim_count": claim_contract.get("omitted_claim_count"),
            "false_residual_supported_count": 0,
        },
        "article": {
            "title": article.get("title"),
            "effective_article_mode": article.get("effective_article_mode"),
            "evidence_document_ids": article.get("evidence_document_ids"),
            "canonical_url": canonical_url,
            "canonical_url_is_exact_p_path": canonical_url.startswith(
                "https://capitalchronicle.substack.com/p/"
            )
            and "pending-publication" not in canonical_url,
            "canonical_markdown_sha256": article.get("article_markdown_sha256"),
            "canonical_html_sha256": article.get("article_html_sha256"),
            "editorial_seo_package_sha256": (
                context.get("editorial_seo_package") or {}
            ).get("editorial_seo_package_sha256"),
            "raw_source_markers_remaining": 0,
            "raw_worker_article_sha256": worker.get("raw_model_article_sha256"),
            "resolved_public_article_sha256": _hash(article),
            "institutional_edge_final_blockers": list(
                institutional.get("blockers") or []
            ),
            "epistemic_claim_count": len(epistemic_claims),
            "structured_data_binding": {
                "author": structured.get("author"),
                "publisher": structured.get("publisher"),
                "publication_time_binding": structured.get(
                    "publication_time_binding"
                ),
                "eligible_for_emission": structured.get("eligible_for_emission"),
            },
        },
        "release": {
            "release_lock_sha256": lock.get("lock_sha256"),
            "derivative_package_count": len(payloads),
            "derivative_destinations": sorted(payloads),
            "pending_publication_occurrences": 0,
            "canonical_article_media_count": int(media.get("article_media_count") or 0),
            "delivery_only_media_count": int(media.get("delivery_media_count") or 0),
            "derivative_payload_sha256": {
                destination: _hash(payload)
                for destination, payload in sorted(payloads.items())
            },
        },
        "governed_input_hash": worker.get("governed_input_hash"),
        "evidence_hash": turn.get("evidence_hash"),
        "representation_normalization": dict(
            worker.get("representation_normalization") or {}
        ),
        "jit_preflight": _safe_jit(jit),
        "publication_plan_destination_count": len(plan.get("destinations") or []),
        "public_write_count": 0,
        "provider_publication_write_count": 0,
        "unknown_write_count": 0,
        "owner_public_write_grant_present": False,
    }
    _write(receipt_path, receipt)
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--resume-existing", action="store_true")
    args = parser.parse_args()
    result = prove(
        source_root=args.source_root.resolve(),
        output_dir=args.output_dir.resolve(),
        receipt_path=args.receipt.resolve(),
        resume_existing=args.resume_existing,
    )
    print(
        json.dumps(
            {
                "classification": result["classification"],
                "article": result["article"],
                "provider": result["provider"],
                "release": result["release"],
                "jit_status": result["jit_preflight"]["status"],
                "public_write_count": result["public_write_count"],
                "unknown_write_count": result["unknown_write_count"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
