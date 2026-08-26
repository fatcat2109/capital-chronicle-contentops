"""Native Desktop external-worker seam for the accepted LLM-first validate-after path.

This module reuses the PR29 deterministic post-generation verification and canonical cached
article/evidence adapters. It does not invoke a model, acquire evidence before the worker, create
a scheduler/store/publisher, or grant factual/numeric/public-write authority.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from live_contentops.llm_first_validate_after_v1 import (
    ARTICLE_MODES,
    LlmFirstValidateAfterProvider,
    LlmFirstValidationError,
    MODEL,
    WORKER_SCHEMA,
)
from live_contentops.native_desktop_production_handoff_v1 import (
    logical_hash,
    validate_worker_request_binding,
)

WORKER_REQUEST_SCHEMA_VERSION = "contentops.native_llm_first_external_worker_request.v1"
WORKER_RETURN_SCHEMA_VERSION = "contentops.native_llm_first_external_worker_return.v1"
REVISION_CONTRACT_SCHEMA_VERSION = "contentops.native_llm_first_same_high_revision.v1"
INITIAL_HANDOFF_STATUS = "LLM_FIRST_HIGH_WORKER_REQUIRED_PRE_VALIDATION"
REVISION_HANDOFF_STATUS = "SAME_HIGH_WORKER_LLM_FIRST_REVISION_REQUIRED"
INITIAL_NEXT_BLOCKER = "SPAWN_ONE_FRESH_ISOLATED_HIGH_LLM_FIRST_EDITORIAL_WORKER"
REVISION_NEXT_BLOCKER = "RESUME_SAME_ISOLATED_HIGH_LLM_FIRST_EDITORIAL_WORKER"


def _plan_rows(selection: Mapping[str, Any]) -> list[dict[str, str]]:
    rows = [
        {
            "cluster_id": str(selection.get("selected_cluster_id") or ""),
            "article_mode": str(selection.get("article_mode") or ""),
            "selection_rationale": str(selection.get("selection_rationale") or "").strip(),
        }
    ]
    rows.extend(
        {
            "cluster_id": str(row.get("cluster_id") or ""),
            "article_mode": str(row.get("article_mode") or ""),
            "selection_rationale": str(row.get("selection_rationale") or "").strip(),
        }
        for row in selection.get("fallback_candidates") or []
        if isinstance(row, Mapping)
    )
    if (
        not rows
        or any(not row["cluster_id"] for row in rows)
        or len({row["cluster_id"] for row in rows}) != len(rows)
        or any(row["article_mode"] not in ARTICLE_MODES for row in rows)
        or any(not row["selection_rationale"] for row in rows)
    ):
        raise ValueError("native_llm_first_external_candidate_plan_invalid")
    return rows


def selection_for_candidate(
    selection: Mapping[str, Any], *, candidate_index: int
) -> dict[str, Any]:
    plan = _plan_rows(selection)
    if not 0 <= int(candidate_index) < len(plan):
        raise ValueError("native_llm_first_external_candidate_index_invalid")
    current = plan[int(candidate_index)]
    return {
        "schema_version": str(selection.get("schema_version") or ""),
        "canonical_opportunity_id": str(selection.get("canonical_opportunity_id") or ""),
        "selection_request_logical_hash": str(
            selection.get("selection_request_logical_hash") or ""
        ),
        "selection_return_logical_hash": str(
            selection.get("selection_return_logical_hash") or ""
        ),
        "selected_cluster_id": current["cluster_id"],
        "article_mode": current["article_mode"],
        "selection_rationale": current["selection_rationale"],
        "fallback_candidates": [dict(row) for row in plan[int(candidate_index) + 1 :]],
        "model": str(selection.get("model") or MODEL),
        "reasoning_effort": str(selection.get("reasoning_effort") or "HIGH").upper(),
        "public_write_attempted": False,
        "native_candidate_plan_index": int(candidate_index),
    }


def _candidate_packet(
    *, binding: Mapping[str, Any], selection: Mapping[str, Any], candidate_index: int
) -> tuple[dict[str, Any], dict[str, Any]]:
    assignment = dict(binding.get("assignment_override") or {})
    intake = dict(binding.get("rolling_input_override") or {})
    current_selection = selection_for_candidate(selection, candidate_index=candidate_index)
    candidates = LlmFirstValidateAfterProvider._candidate_packet(
        list(assignment.get("ranked_clusters") or []), intake
    )
    selected_id = current_selection["selected_cluster_id"]
    candidate = next(
        (
            dict(row)
            for row in candidates
            if str(row.get("cluster_id") or "") == selected_id
        ),
        None,
    )
    if candidate is None:
        raise ValueError("native_llm_first_external_selected_candidate_missing")
    return candidate, current_selection


def build_external_worker_request(
    *,
    binding: Mapping[str, Any],
    selection: Mapping[str, Any],
    cutoff_utc: str,
    candidate_index: int,
    revision_contract: Mapping[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    candidate, current_selection = _candidate_packet(
        binding=binding, selection=selection, candidate_index=candidate_index
    )
    governed = LlmFirstValidateAfterProvider._worker_governed_input(
        candidate=candidate,
        selection=current_selection,
        cutoff_utc=cutoff_utc,
    )
    governed_hash = logical_hash(governed)
    revision = dict(revision_contract or {})
    request: dict[str, Any] = {
        "schema_version": WORKER_REQUEST_SCHEMA_VERSION,
        "governed_input_hash": governed_hash,
        "bounded_governed_context": governed,
        "model": MODEL,
        "reasoning_effort": "high",
        "output_schema": WORKER_SCHEMA,
        "candidate_plan_index": int(candidate_index),
        "candidate_cluster_id": current_selection["selected_cluster_id"],
        "article_mode": current_selection["article_mode"],
        "instruction": (
            "Research and write one useful current Capital Chronicle article from the exact "
            "bounded governed context. Use read-only web research. Return the strict worker "
            "output with article, cited_sources, and material_claim_bindings. Use one to three "
            "exact allowed HTTPS pages and exact [[SOURCE:SOURCE_N]] body markers. Every material "
            "fact, number, quote, or causal assertion must have a verbatim public-copy claim_text "
            "and a short exact source support_excerpt. Worker-declared source timestamps grant "
            "zero authority. Do not attempt any public/provider publication write."
        ),
        "public_write_authority": "ZERO",
        "publication_authority_granted": False,
        "factual_or_numeric_authority_granted": False,
    }
    if revision:
        request.update(
            {
                "fresh": False,
                "isolated": True,
                "resume_existing": True,
                "resume_same_isolated_worker": True,
                "fresh_worker_creation": False,
                "deterministic_validation_deltas": list(revision.get("blockers") or []),
                "revision_contract_hash": revision.get("revision_contract_hash"),
                "instruction": (
                    "Resume the SAME isolated HIGH worker. Revise only from the supplied "
                    "deterministic validation deltas. Remove or narrow unsupported material, "
                    "replace unverifiable citations with exact allowed public pages, and return "
                    "the complete strict worker output. Do not expand factual scope or attempt "
                    "any public/provider publication write."
                ),
            }
        )
        validate_worker_request_binding(
            request,
            expected_governed_input_hash=governed_hash,
            allow_same_worker_revision=True,
        )
    else:
        request.update(
            {
                "fresh": True,
                "isolated": True,
                "resume_existing": False,
            }
        )
        validate_worker_request_binding(
            request,
            expected_governed_input_hash=governed_hash,
        )
    return request, candidate, current_selection


def build_same_high_revision_contract(
    *,
    governed_input_hash: str,
    worker_return: Mapping[str, Any],
    blockers: Sequence[str],
    prior_bounded_revision_count: int,
) -> dict[str, Any]:
    prior_count = int(prior_bounded_revision_count)
    if prior_count != 0:
        raise ValueError("native_llm_first_same_high_revision_budget_exhausted")
    material = {
        "schema_version": REVISION_CONTRACT_SCHEMA_VERSION,
        "decision": REVISION_HANDOFF_STATUS,
        "governed_input_hash": str(governed_input_hash or ""),
        "prior_worker_return_hash": logical_hash(dict(worker_return)),
        "blockers": sorted({str(value) for value in blockers if str(value)}),
        "prior_bounded_revision_count": prior_count,
        "required_bounded_revision_count": prior_count + 1,
        "maximum_bounded_revision_count": 1,
        "same_worker_required": True,
        "fresh_replacement_worker_forbidden": True,
        "public_write_authority": "ZERO",
        "publication_authority_granted": False,
    }
    if len(material["governed_input_hash"]) != 64 or not material["blockers"]:
        raise ValueError("native_llm_first_same_high_revision_contract_invalid")
    material["revision_contract_hash"] = logical_hash(material)
    return material


def validate_same_high_revision_contract(value: Mapping[str, Any]) -> dict[str, Any]:
    contract = dict(value)
    claimed = str(contract.pop("revision_contract_hash", "") or "")
    if (
        contract.get("schema_version") != REVISION_CONTRACT_SCHEMA_VERSION
        or contract.get("decision") != REVISION_HANDOFF_STATUS
        or not claimed
        or claimed != logical_hash(contract)
        or len(str(contract.get("governed_input_hash") or "")) != 64
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
    return {**contract, "revision_contract_hash": claimed}


def _normalized_external_receipt(
    *,
    worker_return: Mapping[str, Any],
    governed_input_hash: str,
    revision: bool,
) -> tuple[dict[str, Any], dict[str, Any]]:
    raw = dict(worker_return)
    if raw.get("schema_version") != WORKER_RETURN_SCHEMA_VERSION:
        raise ValueError("native_llm_first_external_worker_return_schema_invalid")
    if (
        str(raw.get("governed_input_hash") or "") != governed_input_hash
        or raw.get("model") != MODEL
        or str(raw.get("reasoning_effort") or "").upper() != "HIGH"
        or raw.get("public_write_attempted") is not False
    ):
        raise ValueError("native_llm_first_external_worker_return_binding_invalid")
    if revision:
        if (
            raw.get("resume_same_isolated_worker") is not True
            or raw.get("fresh_worker_creation") is not False
        ):
            raise ValueError("native_llm_first_external_revision_identity_invalid")
    elif (
        raw.get("fresh") is not True
        or raw.get("isolated") is not True
        or raw.get("resume_existing") is not False
    ):
        raise ValueError("native_llm_first_external_fresh_worker_identity_invalid")
    output = raw.get("output")
    if not isinstance(output, Mapping):
        output = {
            key: raw.get(key)
            for key in ("article", "cited_sources", "material_claim_bindings")
        }
    if not isinstance(output.get("article"), Mapping):
        raise ValueError("native_llm_first_external_worker_article_missing")
    if not isinstance(output.get("cited_sources"), list) or not isinstance(
        output.get("material_claim_bindings"), list
    ):
        raise ValueError("native_llm_first_external_worker_evidence_contract_missing")
    receipt = {
        "model": MODEL,
        "reasoning_effort": "HIGH",
        "public_write_attempted": False,
        "model_turn_completed": True,
        "turn_result_usage": dict(raw.get("usage") or {}),
        "turn_result_duration_ms": raw.get("duration_ms"),
        "provider_input_identity": {
            "role": (
                "V1_LLM_FIRST_EDITORIAL_REVISION"
                if revision
                else "V1_LLM_FIRST_EDITORIAL_WRITER"
            ),
            "governed_input_hash": governed_input_hash,
            "execution_surface": "NATIVE_CODEX_DESKTOP_EXTERNAL_WORKER",
        },
        "native_worker_return_hash": logical_hash(raw),
    }
    return dict(output), receipt


def _native_coordinator_receipt(selection: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "model": MODEL,
        "reasoning_effort": "HIGH",
        "public_write_attempted": False,
        "model_turn_completed": True,
        "turn_result_usage": {},
        "provider_input_identity": {
            "role": "V1_LLM_FIRST_COORDINATOR_SELECTION",
            "governed_input_hash": str(
                selection.get("selection_request_logical_hash") or ""
            ),
            "identity_kind": "NATIVE_SELECTION_REQUEST_LOGICAL_HASH",
            "execution_surface": "NATIVE_CODEX_DESKTOP_COORDINATOR",
        },
        "native_selection_return_logical_hash": selection.get(
            "selection_return_logical_hash"
        ),
    }


class NativeDesktopExternalLlmFirstProvider(LlmFirstValidateAfterProvider):
    """Bind one externally executed native HIGH worker return to PR29 validation."""

    def __init__(
        self,
        *,
        output_dir: Path,
        selected_selection: Mapping[str, Any],
        expected_worker_request: Mapping[str, Any],
        worker_return: Mapping[str, Any],
        candidate_index: int,
        revision_count: int = 0,
        prior_current_candidate_receipts: Sequence[Mapping[str, Any]] | None = None,
        prior_candidate_attempts: Sequence[Mapping[str, Any]] | None = None,
    ) -> None:
        super().__init__(output_dir=output_dir, published_memory=[])
        self._native_selection = dict(selected_selection)
        self._expected_worker_request = dict(expected_worker_request)
        self._external_worker_return = dict(worker_return)
        self._candidate_index = int(candidate_index)
        self._revision_count = int(revision_count)
        self._prior_current_candidate_receipts = [
            dict(row) for row in (prior_current_candidate_receipts or [])
            if isinstance(row, Mapping)
        ]
        self._prior_candidate_attempts = [
            dict(row) for row in (prior_candidate_attempts or [])
            if isinstance(row, Mapping)
        ]
        self.external_worker_receipt: dict[str, Any] | None = None

    def prepare(
        self,
        *,
        ranked_clusters: Sequence[Mapping[str, Any]],
        intake: Mapping[str, Any],
        cutoff_utc: str,
        published_corpus: Sequence[Any],
    ) -> dict[str, Any]:
        if self._prepared is not None:
            return self.summary()
        candidates = self._candidate_packet(ranked_clusters, intake)
        selected_id = str(self._native_selection.get("selected_cluster_id") or "")
        candidate = next(
            (dict(row) for row in candidates if str(row.get("cluster_id") or "") == selected_id),
            None,
        )
        if candidate is None:
            raise LlmFirstValidationError(["native_external_selected_candidate_missing"])
        governed = self._worker_governed_input(
            candidate=candidate,
            selection=self._native_selection,
            cutoff_utc=cutoff_utc,
        )
        governed_hash = logical_hash(governed)
        expected_hash = str(self._expected_worker_request.get("governed_input_hash") or "")
        if governed_hash != expected_hash:
            raise LlmFirstValidationError(["native_external_worker_governed_input_drift"])
        revision = self._revision_count > 0
        output, current_receipt = _normalized_external_receipt(
            worker_return=self._external_worker_return,
            governed_input_hash=governed_hash,
            revision=revision,
        )
        self.external_worker_receipt = current_receipt
        verified = self._verify(output, candidate=candidate, cutoff_utc=cutoff_utc)
        verified["governed_input_hash"] = governed_hash
        worker_receipts = [*self._prior_current_candidate_receipts, current_receipt]
        attempts = [
            *self._prior_candidate_attempts,
            {
                "cluster_id": selected_id,
                "status": "PASS",
                "native_candidate_plan_index": self._candidate_index,
                "bounded_revision_count": self._revision_count,
                "worker_receipts": worker_receipts,
            },
        ]
        self._selected_cluster_id = selected_id
        self._prepared = {
            **verified,
            "selection": dict(self._native_selection),
            "coordinator_receipt": _native_coordinator_receipt(self._native_selection),
            "coordinator_checkpoint_reused": True,
            "worker_receipts": worker_receipts,
            "candidate_attempts": attempts,
            "native_external_worker": True,
            "native_candidate_plan_index": self._candidate_index,
            "native_bounded_revision_count": self._revision_count,
        }
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / "native_llm_first_external_verified_v1.json").write_text(
            json.dumps(self._prepared, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        return self.summary()

    def summary(self) -> dict[str, Any]:
        summary = super().summary()
        return {
            **summary,
            "execution_surface": "NATIVE_CODEX_DESKTOP_EXTERNAL_WORKER",
            "coordinator_execution_surface": "NATIVE_CODEX_DESKTOP_COORDINATOR",
            "native_candidate_plan_index": self._candidate_index,
            "native_bounded_revision_count": self._revision_count,
            "worker_precedes_deterministic_source_retrieval": True,
        }

    def article_builder(self, viability: Mapping[str, Any]) -> dict[str, Any]:
        built = super().article_builder(viability)
        receipt = dict(built.get("editorial_worker_receipt") or {})
        receipt["bounded_revision_count"] = self._revision_count
        if self._revision_count:
            receipt.update(
                {
                    "fresh": False,
                    "resume_existing": True,
                    "resume_same_isolated_worker": True,
                    "fresh_worker_creation": False,
                }
            )
        built["editorial_worker_receipt"] = receipt
        return built


def normalized_external_worker_receipt_for_failure(
    *,
    worker_return: Mapping[str, Any],
    expected_worker_request: Mapping[str, Any],
    revision: bool,
) -> dict[str, Any]:
    _output, receipt = _normalized_external_receipt(
        worker_return=worker_return,
        governed_input_hash=str(expected_worker_request.get("governed_input_hash") or ""),
        revision=revision,
    )
    return receipt
