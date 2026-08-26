"""Durable, hash-bound native Desktop PREPARE/COMPLETE editorial handoff.

This module contains no scheduler, provider bridge, writer, publisher, or authority grant.  It
only validates and persists the canonical newsroom cycle checkpoints needed for the Desktop
HIGH coordinator to pause one claimed opportunity while one fresh isolated HIGH worker runs,
then resume the same candidate without repeating semantic assignment or evidence acquisition.
"""
from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path
from typing import Any, Mapping


HANDOFF_SCHEMA_VERSION = "contentops.native_desktop_editorial_handoff.v1"
HANDOFF_FILE_NAME = "native_desktop_editorial_handoff_v1.json"
WORKER_DECISION = "SPAWN_ONE_FRESH_ISOLATED_XHIGH_EDITORIAL_WORKER"


def logical_hash(value: Any) -> str:
    return sha256(
        json.dumps(
            value,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
            default=str,
        ).encode("utf-8")
    ).hexdigest()


def read_json(path: str | Path) -> dict[str, Any]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, Mapping):
        raise ValueError("native_desktop_handoff_json_not_object")
    return dict(value)


def write_json(path: str | Path, value: Mapping[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(dict(value), indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )


def semantic_resume_bindings_from_probe(
    probe: Mapping[str, Any],
) -> dict[str, Any]:
    """Rebuild only accepted hash-bound semantic checkpoints from a probe receipt."""
    assignment = dict(probe.get("assignment") or {})
    canonical_input_hash = str(
        (assignment.get("input_binding") or {}).get("canonical_input_hash") or ""
    )
    global_input = dict(assignment.get("compact_global_editor_input") or {})
    leaf_partitions = [
        dict(row)
        for row in assignment.get("leaf_partitions") or []
        if isinstance(row, Mapping)
    ]
    leaf_clusters = [
        dict(row)
        for row in assignment.get("leaf_clusters") or []
        if isinstance(row, Mapping)
    ]
    router_calls = [
        dict(row)
        for row in assignment.get("router_calls") or []
        if isinstance(row, Mapping)
    ]
    global_summary = dict(assignment.get("router_summary") or {})
    story_types = {
        str(key): str(value)
        for key, value in dict(
            (probe.get("story_routing") or {}).get("story_type_by_cluster") or {}
        ).items()
    }
    if (
        not canonical_input_hash
        or not global_input
        or not leaf_partitions
        or not leaf_clusters
        or not global_summary
        or global_summary.get("terminal_disposition") != "ACCEPTED"
        or not story_types
    ):
        raise ValueError("probe_semantic_resume_checkpoint_missing_or_unaccepted")

    leaf_checkpoints: dict[str, dict[str, Any]] = {}
    for partition in leaf_partitions:
        partition_id = str(partition.get("partition_id") or "")
        if not partition_id:
            raise ValueError("probe_semantic_resume_checkpoint_partition_missing")
        summaries = [
            row
            for row in router_calls
            if row.get("role_task_id") == "rolling_x_newsroom_leaf_scan"
            and row.get("work_item_id") == partition_id
            and row.get("terminal_disposition") == "ACCEPTED"
        ]
        clusters = [
            row
            for row in leaf_clusters
            if str(row.get("partition_id") or "") == partition_id
        ]
        if len(summaries) != 1 or not clusters:
            raise ValueError("probe_semantic_resume_leaf_checkpoint_invalid")
        leaf_checkpoints[partition_id] = {
            "canonical_input_hash": canonical_input_hash,
            "partition_id": partition_id,
            "partition_index": partition.get("partition_index"),
            "headline_ids": list(partition.get("headline_ids") or []),
            "router_summary": summaries[0],
            "output": {"clusters": clusters},
        }

    global_attempts = [
        dict(row)
        for row in global_summary.get("attempts") or []
        if isinstance(row, Mapping)
    ]
    accepted_attempts = [
        row for row in global_attempts if row.get("disposition") == "accepted"
    ]
    if len(accepted_attempts) != 1:
        raise ValueError("probe_semantic_resume_global_checkpoint_invalid")
    accepted_attempt = accepted_attempts[0]
    ranked_clusters = [
        dict(row)
        for row in assignment.get("ranked_clusters") or []
        if isinstance(row, Mapping)
    ]
    global_output = {
        "decision": assignment.get("decision"),
        "selection_rationale": assignment.get("selection_rationale"),
        "selected_cluster_id": assignment.get("selected_cluster_id"),
        "selected_headline_ids": list(assignment.get("selected_headline_ids") or []),
        "ranked_clusters": ranked_clusters,
        "shortlist_count": len(ranked_clusters),
        "evaluated_leaf_cluster_count": len(leaf_clusters),
        "global_editor_used_compact_leaf_summaries_only": True,
        "attention_used_as_factual_truth": False,
        "router_output_grants_publication_authority": False,
    }
    global_output["global_result_logical_hash"] = logical_hash(global_output)
    global_checkpoint = {
        "canonical_input_hash": canonical_input_hash,
        "cutoff_time_utc": global_input.get("cutoff_time_utc"),
        "global_input_logical_hash": logical_hash(global_input),
        "ordered_leaf_cluster_ids": [
            str(row.get("id") or "")
            for row in global_input.get("leaf_cluster_summaries") or []
        ],
        "global_invocation_id": global_summary.get("logical_invocation_id"),
        "work_item_id": global_summary.get("work_item_id"),
        "role_task_id": global_summary.get("role_task_id"),
        "prompt_template": accepted_attempt.get("prompt_template"),
        "prompt_version": accepted_attempt.get("prompt_version"),
        "governed_input_hash": accepted_attempt.get("governed_input_hash"),
        "terminal_disposition": global_summary.get("terminal_disposition"),
        "selected_model": global_summary.get("selected_model"),
        "router_summary": global_summary,
        "output": global_output,
        "accepted_provider_identity": {
            "gateway": accepted_attempt.get("gateway"),
            "requested_model": accepted_attempt.get("requested_model"),
            "resolved_model": accepted_attempt.get("resolved_model"),
            "provider_invocation_id": accepted_attempt.get("provider_invocation_id"),
            "model_identity_provider_verified": accepted_attempt.get(
                "model_identity_provider_verified"
            ),
        },
        "global_result_logical_hash": global_output["global_result_logical_hash"],
    }
    return {
        "leaf_checkpoints": leaf_checkpoints,
        "global_checkpoint": global_checkpoint,
        "story_type_by_cluster": story_types,
        "canonical_input_hash": canonical_input_hash,
        "semantic_resume_logical_hash": logical_hash(
            {
                "leaf_checkpoints": leaf_checkpoints,
                "global_checkpoint": global_checkpoint,
                "story_type_by_cluster": story_types,
            }
        ),
    }


def validated_viability_checkpoint(value: Mapping[str, Any]) -> dict[str, Any]:
    checkpoint = dict(value)
    claimed_hash = str(checkpoint.pop("viability_logical_hash", "") or "")
    if (
        not claimed_hash
        or claimed_hash != logical_hash(checkpoint)
        or checkpoint.get("status") != "SUCCESS"
        or checkpoint.get("decision") != "SELECT_STORY"
        or not str(checkpoint.get("selected_cluster_id") or "")
        or not isinstance(checkpoint.get("selected_evidence"), Mapping)
    ):
        raise ValueError("probe_viability_checkpoint_invalid")
    return {**checkpoint, "viability_logical_hash": claimed_hash}


def validate_worker_request_binding(
    worker_request: Mapping[str, Any],
    *,
    expected_governed_input_hash: str,
    viability: Mapping[str, Any] | None = None,
    allow_same_worker_revision: bool = False,
) -> dict[str, Any]:
    """Require the exact bounded packet bytes and, when supplied, candidate evidence binding."""
    request = dict(worker_request)
    bounded_context = request.get("bounded_governed_context")
    expected_hash = str(expected_governed_input_hash or "")
    if (
        len(expected_hash) != 64
        or str(request.get("governed_input_hash") or "") != expected_hash
        or not isinstance(bounded_context, Mapping)
        or logical_hash(dict(bounded_context)) != expected_hash
        or request.get("model") != "gpt-5.6-sol"
        or str(request.get("reasoning_effort") or "").lower() != "high"
    ):
        raise ValueError("native_desktop_worker_request_binding_invalid")
    if allow_same_worker_revision:
        if (
            request.get("resume_same_isolated_worker") is not True
            or request.get("fresh_worker_creation") is not False
        ):
            raise ValueError("native_desktop_same_worker_revision_request_invalid")
    elif (
        request.get("fresh") is not True
        or request.get("isolated") is not True
        or request.get("resume_existing") is not False
    ):
        raise ValueError("native_desktop_fresh_worker_request_invalid")
    if viability is not None:
        selected_evidence = viability.get("selected_evidence")
        request_evidence = bounded_context.get("accepted_evidence_packet")
        if (
            not isinstance(selected_evidence, Mapping)
            or not isinstance(request_evidence, Mapping)
            or logical_hash(dict(selected_evidence))
            != logical_hash(dict(request_evidence))
        ):
            raise ValueError("native_desktop_worker_request_candidate_evidence_mismatch")
    return request


def validate_same_worker_revision_contract(
    revision_contract: Mapping[str, Any],
) -> dict[str, Any]:
    contract = dict(revision_contract)
    claimed_hash = str(contract.pop("revision_contract_hash", "") or "")
    prior_count = int(contract.get("prior_bounded_revision_count") or 0)
    required_count = int(contract.get("required_bounded_revision_count") or 0)
    maximum_count = int(contract.get("maximum_bounded_revision_count") or 0)
    if (
        not claimed_hash
        or logical_hash(contract) != claimed_hash
        or contract.get("decision") != "SAME_XHIGH_WORKER_REVISION_REQUIRED"
        or contract.get("same_worker_required") is not True
        or contract.get("fresh_replacement_worker_forbidden") is not True
        or contract.get("router_final_writer_forbidden") is not True
        or not str(contract.get("prior_worker_return_hash") or "")
        or required_count != prior_count + 1
        or not 0 <= prior_count < maximum_count
        or required_count > maximum_count
        or contract.get("public_write_authority") is not False
        or contract.get("publication_authority") is not False
    ):
        raise ValueError("native_desktop_same_worker_revision_contract_invalid")
    return {**contract, "revision_contract_hash": claimed_hash}


def persist_handoff_checkpoint(path: str | Path, value: Mapping[str, Any]) -> dict[str, Any]:
    payload = dict(value)
    payload["schema_version"] = HANDOFF_SCHEMA_VERSION
    payload["public_write_authority"] = "ZERO"
    payload["publication_authority_granted"] = False
    payload["opportunity_terminalized"] = False
    payload.pop("handoff_logical_hash", None)
    payload["handoff_logical_hash"] = logical_hash(payload)
    current_path = Path(path)
    if current_path.exists():
        existing = load_handoff_checkpoint(current_path)
        if str(existing.get("canonical_opportunity_id") or "") != str(
            payload.get("canonical_opportunity_id") or ""
        ):
            raise ValueError("native_desktop_handoff_opportunity_identity_conflict")
        if int(payload.get("resume_sequence") or 0) < int(
            existing.get("resume_sequence") or 0
        ):
            raise ValueError("native_desktop_handoff_resume_sequence_regression")
    write_json(current_path, payload)
    sequence = int(payload.get("resume_sequence") or 0)
    immutable_path = current_path.with_name(
        f"native_desktop_editorial_handoff_{sequence:02d}_v1.json"
    )
    if immutable_path.exists():
        if load_handoff_checkpoint(immutable_path) != payload:
            raise ValueError("native_desktop_handoff_sequence_identity_conflict")
    else:
        write_json(immutable_path, payload)
    return payload


def load_handoff_checkpoint(path: str | Path) -> dict[str, Any]:
    payload = read_json(path)
    claimed_hash = str(payload.pop("handoff_logical_hash", "") or "")
    if (
        payload.get("schema_version") != HANDOFF_SCHEMA_VERSION
        or not str(payload.get("canonical_opportunity_id") or "")
        or not str(payload.get("runtime_run_id") or "")
        or payload.get("public_write_authority") != "ZERO"
        or payload.get("publication_authority_granted") is not False
        or payload.get("opportunity_terminalized") is not False
        or claimed_hash != logical_hash(payload)
    ):
        raise ValueError("native_desktop_handoff_checkpoint_invalid")
    handoff_status = str(payload.get("handoff_status") or "")
    same_high_llm_first_revision = (
        handoff_status == "SAME_HIGH_WORKER_LLM_FIRST_REVISION_REQUIRED"
    )
    validate_worker_request_binding(
        dict(payload.get("editorial_worker_request") or {}),
        expected_governed_input_hash=str(payload.get("governed_input_hash") or ""),
        allow_same_worker_revision=(
            handoff_status == "SAME_XHIGH_WORKER_REVISION_REQUIRED"
            or same_high_llm_first_revision
        ),
    )
    if handoff_status == "SAME_XHIGH_WORKER_REVISION_REQUIRED":
        validate_same_worker_revision_contract(
            dict(payload.get("same_xhigh_worker_revision_contract") or {})
        )
    elif same_high_llm_first_revision:
        contract = dict(payload.get("same_high_worker_revision_contract") or {})
        contract_hash = str(contract.pop("revision_contract_hash", "") or "")
        if (
            contract.get("schema_version")
            != "contentops.native_llm_first_same_high_revision.v1"
            or contract.get("decision")
            != "SAME_HIGH_WORKER_LLM_FIRST_REVISION_REQUIRED"
            or not contract_hash
            or contract_hash != logical_hash(contract)
            or str(contract.get("governed_input_hash") or "")
            != str(payload.get("governed_input_hash") or "")
            or not str(contract.get("prior_worker_return_hash") or "")
            or not list(contract.get("blockers") or [])
            or int(contract.get("prior_bounded_revision_count") or 0) != 0
            or int(contract.get("required_bounded_revision_count") or 0) != 1
            or int(contract.get("maximum_bounded_revision_count") or 0) != 1
            or contract.get("same_worker_required") is not True
            or contract.get("fresh_replacement_worker_forbidden") is not True
            or contract.get("public_write_authority") != "ZERO"
            or contract.get("publication_authority_granted") is not False
        ):
            raise ValueError("native_llm_first_same_high_revision_contract_invalid")
    return {**payload, "handoff_logical_hash": claimed_hash}


class BoundNativeDesktopWorkerReturnBuilder:
    """Adapter for one supplied worker return; never invokes a model or provider."""

    def __init__(
        self,
        *,
        worker_return: Mapping[str, Any],
        expected_governed_input_hash: str,
        viability: Mapping[str, Any],
        same_worker_revision_contract: Mapping[str, Any] | None = None,
    ) -> None:
        self._worker_return = dict(worker_return)
        self._expected_hash = str(expected_governed_input_hash or "")
        self._viability = dict(viability)
        self._revision_contract = dict(same_worker_revision_contract or {})

    def _built(self, worker_viability: Mapping[str, Any], *, revision: bool) -> dict[str, Any]:
        from live_contentops.codex_desktop_newsroom_operator_v1 import (
            validate_editorial_worker_return,
            validate_same_xhigh_worker_revision_return,
        )
        from live_contentops.rolling_x_grounded_article_media_builder_v1 import (
            GroundedArticleBuilderError,
            resolve_editorial_worker_article_for_public_lock,
        )

        request = dict(worker_viability.get("editorial_worker_request") or {})
        request_hash = str(request.get("governed_input_hash") or "")
        if request_hash != self._expected_hash:
            raise GroundedArticleBuilderError("NEXT_NATIVE_XHIGH_WORKER_REQUIRED")
        try:
            validate_worker_request_binding(
                request,
                expected_governed_input_hash=self._expected_hash,
                viability=self._viability,
            )
            if revision:
                validation = validate_same_xhigh_worker_revision_return(
                    worker_return=self._worker_return,
                    revision_contract=self._revision_contract,
                )
            else:
                validation = validate_editorial_worker_return(
                    worker_return=self._worker_return,
                    expected_governed_input_hash=self._expected_hash,
                )
            raw_article = self._worker_return.get("article")
            if not isinstance(raw_article, Mapping):
                raw_article = self._worker_return.get("editorial_output")
            article = resolve_editorial_worker_article_for_public_lock(
                dict(raw_article or {}), viability=self._viability
            )
        except (TypeError, ValueError):
            raise GroundedArticleBuilderError(
                "EDITORIAL_WORKER_UNAVAILABLE_OR_INVALID"
            ) from None
        receipt = {**self._worker_return, "article": article}
        return {
            "schema_version": "contentops.rolling_x_grounded_article_media_builder.v1",
            "article": article,
            "media": {"assets": []},
            "critical_path_telemetry": {
                "article_writer_semantic_calls": 1,
                "article_writer_owner": "FRESH_NATIVE_CODEX_DESKTOP_HIGH",
                "legacy_writer_fallback_used": False,
            },
            "editorial_worker_receipt": receipt,
            "editorial_worker_validation": validation,
        }

    def __call__(self, worker_viability: Mapping[str, Any]) -> dict[str, Any]:
        return self._built(worker_viability, revision=False)

    @property
    def revise_same_worker(self) -> Any:
        return self._revise_same_worker if self._revision_contract else None

    def _revise_same_worker(self, worker_viability: Mapping[str, Any]) -> dict[str, Any]:
        return self._built(worker_viability, revision=True)


def build_hash_bound_coordinator_reviewer(
    review_receipt: Mapping[str, Any],
) -> Any:
    """Replay one HIGH coordinator review only for its exact deterministic prompt hash."""
    receipt = dict(review_receipt)
    expected_prompt_hash = str(receipt.get("prompt_sha256") or "")
    from live_contentops.tier1_editorial_quality_v1 import (
        validate_llm_editorial_review,
    )

    normalized = validate_llm_editorial_review(receipt)
    if (
        len(expected_prompt_hash) != 64
        or normalized.get("status") != "SUCCESS"
        or normalized.get("decision") != receipt.get("decision")
        or receipt.get("publication_authority") is not False
    ):
        raise ValueError("native_desktop_coordinator_review_receipt_invalid")
    replay_receipt = {
        **normalized,
        "provider": "NATIVE_CODEX_DESKTOP_HIGH_COORDINATOR",
        "prompt_sha256": expected_prompt_hash,
        "publication_authority": False,
    }

    def reviewer(article: Mapping[str, Any]) -> dict[str, Any]:
        from live_contentops.tier1_editorial_quality_v1 import (
            build_llm_editorial_review_prompt,
        )

        prompt = build_llm_editorial_review_prompt(article)
        actual_hash = sha256(prompt.encode("utf-8")).hexdigest()
        if actual_hash != expected_prompt_hash:
            raise ValueError("native_desktop_coordinator_review_prompt_hash_mismatch")
        return dict(replay_receipt)

    return reviewer
