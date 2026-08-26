"""Native Desktop LLM-first selection over the canonical V1 supervisor.

The base Daily App supervisor remains the sole scheduler/store/runtime owner. This thin subclass
changes only the native Desktop PREPARE ordering used by the production composition:

zero-model prepared frontier -> external HIGH coordinator useful-candidate shortlist -> canonical
selected-shortlist preselection/evidence hydration -> existing hash-bound native HIGH worker
handoff -> existing COMPLETE path.

It does not create a second scheduler, store, evidence engine, model gateway, or publisher. The
selection phase grants no factual, numeric, evidence, permission, or public-write authority.
"""
from __future__ import annotations

import hashlib
import json
from contextvars import ContextVar
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

from live_contentops.daily_app_supervisor_v1 import (
    ContentOpsDailyAppSupervisor,
    NATIVE_DESKTOP_AUTOMATION_SESSION_BY_ID,
    SCHEDULED_EDITORIAL_OWNER_NATIVE_DESKTOP,
)
from live_contentops.source_capability_registry_v2 import CANONICAL_PRODUCT_MODES

SELECTION_REQUEST_SCHEMA_VERSION = "contentops.native_llm_first_selection_request.v1"
SELECTION_RETURN_SCHEMA_VERSION = "contentops.native_llm_first_selection_return.v1"
SELECTION_ARTIFACT_SCHEMA_VERSION = "contentops.native_llm_first_selection_artifact.v1"
COORDINATOR_MODEL = "gpt-5.6-sol"
COORDINATOR_REASONING_EFFORT = "HIGH"
MAX_SELECTION_CANDIDATES = 8
MAX_SELECTION_FALLBACKS = MAX_SELECTION_CANDIDATES - 1


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, default=str
    )


def _logical_hash(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _iso_utc(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


class NativeLlmFirstContentOpsDailyAppSupervisor(ContentOpsDailyAppSupervisor):
    """Canonical supervisor with a two-step native Desktop LLM-first PREPARE seam."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._canonical_newsroom_cycle = self._newsroom_cycle
        self._native_selection_binding: ContextVar[Optional[dict[str, Any]]] = ContextVar(
            f"contentops_native_llm_first_selection_{id(self)}", default=None
        )
        self._newsroom_cycle = self._native_llm_first_newsroom_cycle

    def _native_llm_first_newsroom_cycle(self, **kwargs: Any) -> Mapping[str, Any]:
        binding = self._native_selection_binding.get()
        if binding is None:
            return self._canonical_newsroom_cycle(**kwargs)
        phase = str(binding.get("phase") or "PREPARE").strip().upper()
        if phase not in {"PREPARE", "COMPLETE", "TERMINAL"}:
            raise ValueError("native_llm_first_resume_phase_invalid")

        rolling_input = dict(binding["rolling_input_override"])
        assignment = dict(binding["assignment_override"])
        story_types = dict(binding["story_type_by_cluster"])
        expected_input_hash = str(rolling_input.get("canonical_input_hash") or "")
        output_dir = Path(kwargs.get("output_dir") or self._output_root)
        full_intake_count = int(
            (rolling_input.get("counts") or {}).get("accepted_in_full_rolling_intake")
            or len(rolling_input.get("headlines") or [])
        )

        if phase == "PREPARE":
            if kwargs.get("native_desktop_prepare") is not True:
                raise ValueError("native_llm_first_selection_only_valid_for_desktop_prepare")
            from live_contentops.native_desktop_production_handoff_v1 import (
                WORKER_DECISION,
                write_json,
            )
            from live_contentops.native_llm_first_validate_after_v1 import (
                INITIAL_NEXT_BLOCKER,
                build_external_worker_request,
            )

            selection = dict(binding.get("selection") or {})
            worker_request, candidate, current_selection = build_external_worker_request(
                binding=binding,
                selection=selection,
                cutoff_utc=str(kwargs.get("cutoff_utc") or ""),
                candidate_index=0,
            )
            story_routing = {
                "status": "SUCCESS",
                "reason_code": None,
                "story_type_by_cluster": story_types,
                "llm_first_selection_precedes_capability_admission": True,
                "semantic_routing_grants_authority": False,
            }
            prevalidation = {
                "schema_version": "contentops.native_llm_first_prevalidation_handoff.v1",
                "ordering": "HIGH_SELECTION_THEN_FRESH_HIGH_WORKER_THEN_DETERMINISTIC_VALIDATE_AFTER",
                "candidate_plan_index": 0,
                "bounded_revision_count": 0,
                "selected_cluster_id": current_selection["selected_cluster_id"],
                "selected_headline_ids": list(candidate.get("headline_ids") or []),
                "selection_request_logical_hash": binding[
                    "selection_request_logical_hash"
                ],
                "selection_return_logical_hash": binding[
                    "selection_return_logical_hash"
                ],
                "native_llm_first_resume_binding": dict(binding["resume_binding"]),
                "worker_precedes_evidence_acquisition": True,
                "evidence_acquisition_requests_before_worker": 0,
                "locator_model_invocations_before_worker": 0,
                "public_write_authority": "ZERO",
                "publication_authority_granted": False,
            }
            output_dir.mkdir(parents=True, exist_ok=True)
            write_json(output_dir / "rolling_x_intake_v1.json", rolling_input)
            write_json(output_dir / "rolling_x_assignment_v1.json", assignment)
            write_json(output_dir / "rolling_x_story_routing_v1.json", story_routing)
            write_json(
                output_dir / "native_llm_first_prevalidation_v1.json", prevalidation
            )
            return {
                "schema_version": "contentops.rolling_x_newsroom_cycle.v1",
                "classification": "NO_PUBLICATION",
                "exact_next_blocker": "EDITORIAL_WORKER_UNAVAILABLE_OR_INVALID",
                "intake": rolling_input,
                "assignment": assignment,
                "story_routing": story_routing,
                "editorial_worker_routing": {
                    "decision": WORKER_DECISION,
                    "governed_input_hash": worker_request["governed_input_hash"],
                    "worker_request": worker_request,
                    "native_llm_first": True,
                    "actual_reasoning_effort": "HIGH",
                    "legacy_xhigh_schema_token_is_execution_authority": False,
                    "public_write_authority": "ZERO",
                },
                "native_llm_first_prevalidation": prevalidation,
                "native_llm_first_resume_binding": dict(binding["resume_binding"]),
                "native_llm_first_assignment_override_reused": True,
                "full_rolling_headline_count": full_intake_count,
                "high_admitted_shortlist_count": len(binding["selected_cluster_ids"]),
                "evidence_acquisition_requests": 0,
                "grounded_locator_model_invocations": 0,
                "public_write_performed": False,
                "unknown_write_detected": False,
                "critical_path_telemetry": {
                    "schema_version": "contentops.publication_critical_path_telemetry.v1",
                    "prepared_candidate_state_reused": False,
                    "full_rolling_headline_count": full_intake_count,
                    "full_universe_semantic_assignment_on_critical_path": False,
                    "bounded_prepared_frontier_semantic_assignment": False,
                    "exact_assignment_override_input_bound": True,
                    "native_llm_first_assignment_override_reused": True,
                    "assignment_semantic_calls": 0,
                    "story_type_semantic_calls": 0,
                    "article_writer_semantic_calls": 0,
                    "mandatory_semantic_review_calls": 0,
                    "candidates_attempted": 0,
                    "routine_semantic_calls": 0,
                    "public_write_performed": False,
                },
            }

        if phase == "TERMINAL":
            from live_contentops.native_desktop_production_handoff_v1 import write_json

            evidence = {
                "schema_version": "contentops.rolling_x_newsroom_cycle.v1",
                "classification": "NO_PUBLICATION",
                "exact_next_blocker": "BOUNDED_LLM_FIRST_CANDIDATE_ATTEMPTS_EXHAUSTED_AFTER_POST_GENERATION_VALIDATION",
                "intake": rolling_input,
                "assignment": assignment,
                "story_routing": {
                    "status": "SUCCESS",
                    "story_type_by_cluster": story_types,
                    "semantic_routing_grants_authority": False,
                },
                "native_llm_first_resume_binding": dict(binding["resume_binding"]),
                "native_llm_first_assignment_override_reused": True,
                "full_rolling_headline_count": full_intake_count,
                "full_universe_semantic_assignment_on_critical_path": False,
                "high_admitted_shortlist_count": len(binding["selected_cluster_ids"]),
                "public_write_performed": False,
                "unknown_write_detected": False,
            }
            write_json(output_dir / "rolling_x_newsroom_cycle_evidence_v1.json", evidence)
            return evidence

        external_provider = binding.get("external_provider")
        if external_provider is None:
            raise ValueError("native_llm_first_external_provider_required_for_complete")
        narrowed = dict(kwargs)
        supplied_input = narrowed.get("rolling_input")
        if isinstance(supplied_input, Mapping):
            supplied_hash = str(supplied_input.get("canonical_input_hash") or "")
            if supplied_hash and supplied_hash != expected_input_hash:
                raise ValueError("native_llm_first_complete_intake_binding_mismatch")
        narrowed["prepared_candidate_state"] = None
        narrowed["rolling_input"] = rolling_input
        narrowed["assignment_override"] = assignment
        narrowed["story_type_by_cluster"] = story_types
        narrowed["leaf_checkpoints"] = {}
        narrowed["global_checkpoint"] = None
        narrowed["publication_enabled"] = False
        narrowed["llm_first_editorial_provider"] = external_provider
        result = self._canonical_newsroom_cycle(**narrowed)
        if not isinstance(result, Mapping):
            return result
        annotated = {
            **dict(result),
            "full_rolling_headline_count": full_intake_count,
            "full_universe_semantic_assignment_on_critical_path": False,
            "bounded_prepared_frontier_semantic_assignment": False,
            "native_llm_first_assignment_override_reused": True,
            "high_admitted_shortlist_count": len(binding["selected_cluster_ids"]),
            "native_llm_first_selection": {
                "ordering": "HIGH_SELECTION_THEN_FRESH_HIGH_WORKER_THEN_DETERMINISTIC_VALIDATE_AFTER",
                "selection_request_logical_hash": binding[
                    "selection_request_logical_hash"
                ],
                "selection_return_logical_hash": binding[
                    "selection_return_logical_hash"
                ],
                "selected_cluster_id": binding["selected_cluster_id"],
                "selected_cluster_ids": list(binding["selected_cluster_ids"]),
                "selected_article_mode": binding["article_mode"],
                "canonical_rolling_input_hash": expected_input_hash,
                "full_prepared_frontier_reopened": False,
                "high_admitted_shortlist_count": len(binding["selected_cluster_ids"]),
                "semantic_assignment_provider_call_required": False,
                "story_type_semantic_call_required": False,
                "worker_precedes_deterministic_source_retrieval": True,
                "factual_or_numeric_authority_granted": False,
                "publication_authority_granted": False,
            },
            "native_llm_first_resume_binding": dict(binding["resume_binding"]),
        }
        evidence_path = output_dir / "rolling_x_newsroom_cycle_evidence_v1.json"
        if evidence_path.exists():
            from live_contentops.native_desktop_production_handoff_v1 import (
                read_json,
                write_json,
            )

            persisted = read_json(evidence_path)
            persisted.update(
                {
                    "full_rolling_headline_count": full_intake_count,
                    "full_universe_semantic_assignment_on_critical_path": False,
                    "native_llm_first_assignment_override_reused": True,
                    "high_admitted_shortlist_count": len(binding["selected_cluster_ids"]),
                    "native_llm_first_selection": annotated[
                        "native_llm_first_selection"
                    ],
                    "native_llm_first_resume_binding": dict(binding["resume_binding"]),
                }
            )
            telemetry = dict(persisted.get("critical_path_telemetry") or {})
            telemetry.update(
                {
                    "full_rolling_headline_count": full_intake_count,
                    "full_universe_semantic_assignment_on_critical_path": False,
                    "exact_assignment_override_input_bound": True,
                    "native_llm_first_assignment_override_reused": True,
                }
            )
            persisted["critical_path_telemetry"] = telemetry
            write_json(evidence_path, persisted)
        return annotated

    def _selection_artifact_path(self, opportunity_id: str) -> Path:
        return (
            self._output_root
            / opportunity_id
            / "native_desktop_llm_first_selection_v1.json"
        )

    def _selection_return_path(self, opportunity_id: str) -> Path:
        return (
            self._output_root
            / opportunity_id
            / "native_desktop_llm_first_selection_return_v1.json"
        )

    @staticmethod
    def _published_memory_projection(value: Any) -> list[dict[str, Any]]:
        """Project actual continuity shapes without inventing publication metadata."""
        if not isinstance(value, Mapping):
            return []
        memory = value.get("published_memory")
        projected: list[dict[str, Any]] = []
        if isinstance(memory, Mapping):
            rows = memory.get("articles") or memory.get("items") or []
            if isinstance(rows, list):
                for row in rows:
                    if not isinstance(row, Mapping):
                        continue
                    projected.append(
                        {
                            "title": row.get("title"),
                            "story_identity": row.get("story_identity"),
                            "update_chain_identity": row.get("update_chain_identity"),
                            "published_at_utc": row.get("published_at_utc"),
                        }
                    )
            for story_identity in memory.get("story_identities") or []:
                if str(story_identity):
                    projected.append({"story_identity": str(story_identity)})
            for chain_identity in memory.get("update_chain_identities") or []:
                if str(chain_identity):
                    projected.append({"update_chain_identity": str(chain_identity)})
        elif isinstance(memory, list):
            for row in memory:
                if not isinstance(row, Mapping):
                    continue
                projected.append(
                    {
                        "title": row.get("title"),
                        "story_identity": row.get("story_identity"),
                        "update_chain_identity": row.get("update_chain_identity"),
                        "published_at_utc": row.get("published_at_utc"),
                    }
                )
        deduped_reversed: list[dict[str, Any]] = []
        seen: set[str] = set()
        for row in reversed(projected):
            key = _canonical_json(row)
            if key in seen:
                continue
            seen.add(key)
            deduped_reversed.append(row)
            if len(deduped_reversed) >= 100:
                break
        return list(reversed(deduped_reversed))

    @staticmethod
    def _candidate_packet(
        prepared_state: Mapping[str, Any],
    ) -> list[dict[str, Any]]:
        assignment = prepared_state.get("assignment") or {}
        prepared_input = prepared_state.get("prepared_input") or {}
        headline_by_id = {
            str(row.get("headline_id") or ""): dict(row)
            for row in prepared_input.get("headlines") or []
            if isinstance(row, Mapping) and str(row.get("headline_id") or "")
        }
        packet: list[dict[str, Any]] = []
        for cluster in list(assignment.get("ranked_clusters") or [])[
            :MAX_SELECTION_CANDIDATES
        ]:
            if not isinstance(cluster, Mapping):
                continue
            headline_ids = [
                str(value)
                for value in cluster.get("headline_ids") or []
                if str(value)
            ]
            headlines = []
            for headline_id in headline_ids:
                row = headline_by_id.get(headline_id, {})
                external = (
                    row.get("external_content")
                    if isinstance(row.get("external_content"), Mapping)
                    else {}
                )
                headlines.append(
                    {
                        "headline_id": headline_id,
                        "headline_text": row.get("headline_text")
                        or external.get("headline_text"),
                        "source_timestamp_utc": row.get("source_timestamp_utc"),
                        "source_account": row.get("source_account")
                        or external.get("author_handle"),
                        "source_url": row.get("source_url")
                        or external.get("url_or_source_ref"),
                    }
                )
            packet.append(
                {
                    "cluster_id": str(cluster.get("cluster_id") or ""),
                    "deterministic_rank": int(
                        cluster.get("rank") or len(packet) + 1
                    ),
                    "headline_ids": headline_ids,
                    "headlines": headlines,
                    "why_now": cluster.get("why_now"),
                    "selection_case": cluster.get("selection_case"),
                    "update_chain": dict(cluster.get("update_chain") or {}),
                    "market_sensitive": bool(cluster.get("market_sensitive")),
                }
            )
        return packet

    def _build_selection_artifact(
        self,
        *,
        task_id: str,
        session: str,
        moment: datetime,
        window: Mapping[str, Any],
        prepared_state: Mapping[str, Any],
    ) -> dict[str, Any]:
        candidates = self._candidate_packet(prepared_state)
        continuity: Mapping[str, Any] = {}
        try:
            from live_contentops.codex_desktop_newsroom_operator_v1 import (
                load_terminal_editorial_continuity,
            )

            continuity = load_terminal_editorial_continuity(
                store_path=self._store_path, output_root=self._output_root
            )
        except Exception:
            continuity = {}
        coordinator_request = {
            "schema_version": SELECTION_REQUEST_SCHEMA_VERSION,
            "automation_id": task_id,
            "session": session,
            "canonical_opportunity_id": str(window["window_id"]),
            "selection_as_of_utc": _iso_utc(window["end"]),
            "opportunity_cutoff_utc": _iso_utc(window["end"]),
            "prepared_candidate_logical_hash": prepared_state.get(
                "prepared_candidate_logical_hash"
            ),
            "candidates": candidates,
            "published_memory": self._published_memory_projection(continuity),
            "allowed_article_modes": list(CANONICAL_PRODUCT_MODES),
            "instruction": (
                "Choose one primary useful current story/angle and optionally additional useful "
                "fallback candidates from this same list, in preferred order, so a hard failure "
                "of one candidate does not starve the opportunity. Omit filler and published "
                "duplicates. Give each admitted candidate one canonical article mode and concise "
                "rationale. Selection grants no factual, evidence, numeric, Capital Chronicle, "
                "permission, or public-write authority."
            ),
            "model": COORDINATOR_MODEL,
            "reasoning_effort": COORDINATOR_REASONING_EFFORT,
            "factual_or_numeric_authority_granted": False,
            "evidence_authority_granted": False,
            "publication_authority_granted": False,
        }
        coordinator_request["selection_request_logical_hash"] = _logical_hash(
            coordinator_request
        )
        artifact = {
            "schema_version": SELECTION_ARTIFACT_SCHEMA_VERSION,
            "coordinator_request": coordinator_request,
            "runtime_binding": {
                "window": {
                    "window_id": str(window["window_id"]),
                    "trigger": str(window.get("trigger") or "SCHEDULED"),
                    "start_utc": _iso_utc(window["start"]),
                    "end_utc": _iso_utc(window["end"]),
                    "session": str(window.get("session") or session),
                    "native_desktop_automation_id": task_id,
                    "native_desktop_zero_public_write": True,
                },
                "prepared_candidate_logical_hash": prepared_state.get(
                    "prepared_candidate_logical_hash"
                ),
                "prepared_input": dict(prepared_state.get("prepared_input") or {}),
                "assignment": dict(prepared_state.get("assignment") or {}),
                "story_type_by_cluster": dict(
                    (prepared_state.get("story_routing") or {}).get(
                        "story_type_by_cluster"
                    )
                    or {}
                ),
            },
            "expires_at_utc": _iso_utc(window["end"] + timedelta(hours=1)),
            "public_write_authority": "ZERO",
            "public_write_performed": False,
        }
        artifact["artifact_logical_hash"] = _logical_hash(artifact)
        return artifact

    def _persist_selection_artifact(self, artifact: Mapping[str, Any]) -> Path:
        opportunity_id = str(
            (artifact.get("coordinator_request") or {}).get(
                "canonical_opportunity_id"
            )
            or ""
        )
        path = self._selection_artifact_path(opportunity_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            existing = json.loads(path.read_text(encoding="utf-8"))
            if existing != artifact:
                raise ValueError("native_llm_first_selection_request_identity_conflict")
            return path
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(
            json.dumps(artifact, indent=2, sort_keys=True, default=str) + "\n",
            encoding="utf-8",
        )
        temporary.replace(path)
        return path

    def _persist_selection_return(
        self, *, opportunity_id: str, selection: Mapping[str, Any]
    ) -> Path:
        path = self._selection_return_path(opportunity_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        material = dict(selection)
        if path.exists():
            existing = json.loads(path.read_text(encoding="utf-8"))
            if existing != material:
                raise ValueError("native_llm_first_selection_return_identity_conflict")
            return path
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(
            json.dumps(material, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        temporary.replace(path)
        return path

    def _load_selection_artifact(
        self, *, task_id: str, session: str, opportunity_id: str
    ) -> dict[str, Any]:
        path = self._selection_artifact_path(opportunity_id)
        try:
            artifact = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, TypeError, ValueError) as exc:
            raise ValueError(
                "native_llm_first_selection_request_missing_or_invalid"
            ) from exc
        logical_hash = str(artifact.get("artifact_logical_hash") or "")
        material = {
            key: value
            for key, value in artifact.items()
            if key != "artifact_logical_hash"
        }
        request = artifact.get("coordinator_request") or {}
        if (
            artifact.get("schema_version") != SELECTION_ARTIFACT_SCHEMA_VERSION
            or logical_hash != _logical_hash(material)
            or request.get("schema_version") != SELECTION_REQUEST_SCHEMA_VERSION
            or str(request.get("automation_id") or "") != task_id
            or str(request.get("session") or "") != session
            or str(request.get("canonical_opportunity_id") or "") != opportunity_id
        ):
            raise ValueError("native_llm_first_selection_request_binding_invalid")
        return dict(artifact)

    @staticmethod
    def _validate_selection_return(
        selection: Mapping[str, Any], artifact: Mapping[str, Any]
    ) -> dict[str, Any]:
        request = artifact.get("coordinator_request") or {}
        candidate_ids = [
            str(row.get("cluster_id") or "")
            for row in request.get("candidates") or []
            if isinstance(row, Mapping) and str(row.get("cluster_id") or "")
        ]
        candidate_id_set = set(candidate_ids)

        primary = {
            "cluster_id": str(selection.get("selected_cluster_id") or ""),
            "article_mode": str(selection.get("article_mode") or ""),
            "selection_rationale": str(
                selection.get("selection_rationale") or ""
            ).strip(),
        }
        fallback_rows = selection.get("fallback_candidates") or []
        if not isinstance(fallback_rows, list) or len(fallback_rows) > MAX_SELECTION_FALLBACKS:
            raise ValueError("native_llm_first_fallback_candidates_invalid")
        fallbacks: list[dict[str, str]] = []
        for row in fallback_rows:
            if not isinstance(row, Mapping):
                raise ValueError("native_llm_first_fallback_candidate_invalid")
            fallbacks.append(
                {
                    "cluster_id": str(row.get("cluster_id") or ""),
                    "article_mode": str(row.get("article_mode") or ""),
                    "selection_rationale": str(
                        row.get("selection_rationale") or ""
                    ).strip(),
                }
            )

        plan = [primary, *fallbacks]
        plan_ids = [row["cluster_id"] for row in plan]
        if len(plan_ids) != len(set(plan_ids)):
            raise ValueError("native_llm_first_candidate_plan_duplicate")
        if any(cluster_id not in candidate_id_set for cluster_id in plan_ids):
            raise ValueError("native_llm_first_selected_cluster_invalid")
        if any(row["article_mode"] not in CANONICAL_PRODUCT_MODES for row in plan):
            raise ValueError("native_llm_first_selected_article_mode_invalid")
        if any(not row["selection_rationale"] for row in plan):
            raise ValueError("native_llm_first_selection_rationale_missing")

        normalized = {
            "schema_version": str(selection.get("schema_version") or ""),
            "canonical_opportunity_id": str(
                selection.get("canonical_opportunity_id") or ""
            ),
            "selection_request_logical_hash": str(
                selection.get("selection_request_logical_hash") or ""
            ),
            "selected_cluster_id": primary["cluster_id"],
            "article_mode": primary["article_mode"],
            "selection_rationale": primary["selection_rationale"],
            "fallback_candidates": fallbacks,
            "model": str(selection.get("model") or ""),
            "reasoning_effort": str(
                selection.get("reasoning_effort") or ""
            ).upper(),
            "public_write_attempted": selection.get("public_write_attempted"),
        }
        if normalized["schema_version"] != SELECTION_RETURN_SCHEMA_VERSION:
            raise ValueError("native_llm_first_selection_schema_invalid")
        if normalized["canonical_opportunity_id"] != str(
            request.get("canonical_opportunity_id") or ""
        ):
            raise ValueError("native_llm_first_selection_opportunity_id_mismatch")
        if normalized["selection_request_logical_hash"] != str(
            request.get("selection_request_logical_hash") or ""
        ):
            raise ValueError("native_llm_first_selection_request_hash_mismatch")
        if normalized["model"] != COORDINATOR_MODEL:
            raise ValueError("native_llm_first_coordinator_model_invalid")
        if normalized["reasoning_effort"] != COORDINATOR_REASONING_EFFORT:
            raise ValueError("native_llm_first_coordinator_effort_invalid")
        if normalized["public_write_attempted"] is not False:
            raise ValueError("native_llm_first_coordinator_public_write_attempted")
        normalized["selection_return_logical_hash"] = _logical_hash(normalized)
        return normalized

    @staticmethod
    def _selected_assignment_binding(
        *, artifact: Mapping[str, Any], selection: Mapping[str, Any]
    ) -> dict[str, Any]:
        runtime = artifact.get("runtime_binding") or {}
        source_assignment = dict(runtime.get("assignment") or {})
        prepared_input = dict(runtime.get("prepared_input") or {})
        source_clusters = {
            str(row.get("cluster_id") or ""): dict(row)
            for row in source_assignment.get("ranked_clusters") or []
            if isinstance(row, Mapping) and str(row.get("cluster_id") or "")
        }
        plan = [
            {
                "cluster_id": str(selection["selected_cluster_id"]),
                "article_mode": str(selection["article_mode"]),
                "selection_rationale": str(selection["selection_rationale"]),
            },
            *[
                dict(row)
                for row in selection.get("fallback_candidates") or []
                if isinstance(row, Mapping)
            ],
        ]
        selected_clusters: list[dict[str, Any]] = []
        selected_cluster_ids: list[str] = []
        selected_headline_ids: list[str] = []
        selected_leaf_ids: set[str] = set()
        for rank, plan_row in enumerate(plan, start=1):
            cluster_id = str(plan_row.get("cluster_id") or "")
            source = source_clusters.get(cluster_id)
            if source is None:
                raise ValueError(
                    "native_llm_first_selected_cluster_not_in_runtime_binding"
                )
            headline_ids = [
                str(value)
                for value in source.get("headline_ids") or []
                if str(value)
            ]
            if not headline_ids:
                raise ValueError("native_llm_first_selected_headline_ids_missing")
            if any(value in selected_headline_ids for value in headline_ids):
                raise ValueError("native_llm_first_selected_headline_overlap")
            selected_cluster_ids.append(cluster_id)
            selected_headline_ids.extend(headline_ids)
            selected_leaf_ids.update(
                str(value)
                for value in source.get("leaf_cluster_ids") or []
                if str(value)
            )
            selected_clusters.append(
                {
                    **source,
                    "rank": rank,
                    "article_mode": str(plan_row.get("article_mode") or ""),
                    "resolved_article_mode": str(plan_row.get("article_mode") or ""),
                    "llm_first_validate_after_selected": True,
                    "native_llm_first_selection_rationale": str(
                        plan_row.get("selection_rationale") or ""
                    ),
                }
            )

        prepared_rows = {
            str(row.get("headline_id") or ""): dict(row)
            for row in prepared_input.get("headlines") or []
            if isinstance(row, Mapping) and str(row.get("headline_id") or "")
        }
        if (
            not selected_headline_ids
            or len(prepared_rows) != len(prepared_input.get("headlines") or [])
            or any(headline_id not in prepared_rows for headline_id in selected_headline_ids)
        ):
            raise ValueError("native_llm_first_selected_input_binding_invalid")
        narrowed_input = {
            **prepared_input,
            "unique_headline_ids": list(selected_headline_ids),
            "headlines": [prepared_rows[value] for value in selected_headline_ids],
        }
        counts = dict(prepared_input.get("counts") or {})
        full_count = int(
            counts.get("accepted_in_full_rolling_intake")
            or counts.get("accepted")
            or len(prepared_rows)
        )
        counts.update(
            {
                "accepted_in_full_rolling_intake": full_count,
                "accepted": len(selected_headline_ids),
                "selected_for_native_llm_first": len(selected_headline_ids),
            }
        )
        narrowed_input["counts"] = counts
        from live_contentops.newsroom_assignment_scheduler_v1 import (
            _rolling_x_canonical_hash_material,
        )

        narrowed_input["canonical_input_hash"] = _logical_hash(
            _rolling_x_canonical_hash_material(narrowed_input)
        )

        selected_leaf_clusters = [
            dict(row)
            for row in source_assignment.get("leaf_clusters") or []
            if isinstance(row, Mapping)
            and str(row.get("leaf_cluster_id") or "") in selected_leaf_ids
        ]
        leaf_member_ids = {
            str(value)
            for row in selected_leaf_clusters
            for value in row.get("member_headline_ids") or []
            if str(value)
        }
        if selected_leaf_ids and leaf_member_ids != set(selected_headline_ids):
            raise ValueError("native_llm_first_selected_leaf_binding_invalid")

        input_binding = dict(source_assignment.get("input_binding") or {})
        input_binding.update(
            {
                "canonical_input_hash": narrowed_input["canonical_input_hash"],
                "input_ids": list(selected_headline_ids),
                "input_count": len(selected_headline_ids),
                "selected_count": len(selected_headline_ids),
                "held_count": 0,
                "selection_scope": (
                    "HIGH_SELECTED_USEFUL_SHORTLIST_FROM_ZERO_MODEL_PREPARED_FRONTIER"
                ),
            }
        )
        assignment = {
            **source_assignment,
            "schema_version": str(
                source_assignment.get("schema_version")
                or "capital_chronicle.rolling_x_newsroom_assignment.v1"
            ),
            "status": "SUCCESS",
            "decision": "SELECT_STORY",
            "reason_code": None,
            "assignment_method": (
                "NATIVE_LLM_FIRST_HIGH_SELECTION_FROM_ZERO_MODEL_PREPARED_FRONTIER"
            ),
            "input_binding": input_binding,
            "ranked_clusters": selected_clusters,
            "leaf_clusters": selected_leaf_clusters,
            "selected_cluster_id": selected_cluster_ids[0],
            "selected_cluster_ids": list(selected_cluster_ids),
            "selected_headline_ids": list(selected_headline_ids),
            "router_calls": [],
            "factual_or_numeric_authority_granted": False,
            "router_output_grants_publication_authority": False,
            "x_content_grants_evidence_authority": False,
            "native_llm_first_selection_request_logical_hash": selection[
                "selection_request_logical_hash"
            ],
            "native_llm_first_selection_return_logical_hash": selection[
                "selection_return_logical_hash"
            ],
        }
        # These checkpoints are valid only for the original prepared frontier.  The narrowed
        # assignment is deterministic selection authority, not a claim that the old semantic
        # router ran over the new input hash.
        for stale_key in (
            "compact_global_editor_input",
            "leaf_partitions",
            "router_summary",
            "assignment_logical_hash",
        ):
            assignment.pop(stale_key, None)
        assignment["assignment_logical_hash"] = _logical_hash(assignment)

        story_types = dict(runtime.get("story_type_by_cluster") or {})
        selected_story_types: dict[str, str] = {}
        for cluster_id in selected_cluster_ids:
            story_type = str(story_types.get(cluster_id) or "").strip()
            if not story_type:
                raise ValueError("native_llm_first_selected_story_type_missing")
            selected_story_types[cluster_id] = story_type

        resume_binding = {
            "schema_version": "contentops.native_llm_first_assignment_resume.v1",
            "assignment_override": assignment,
            "story_type_by_cluster": selected_story_types,
            "selected_cluster_ids": list(selected_cluster_ids),
            "rolling_input_canonical_hash": narrowed_input["canonical_input_hash"],
            "selection_request_logical_hash": selection[
                "selection_request_logical_hash"
            ],
            "selection_return_logical_hash": selection[
                "selection_return_logical_hash"
            ],
            "factual_or_numeric_authority_granted": False,
            "publication_authority_granted": False,
        }
        resume_binding["resume_binding_logical_hash"] = _logical_hash(resume_binding)
        return {
            "rolling_input_override": narrowed_input,
            "assignment_override": assignment,
            "story_type_by_cluster": selected_story_types,
            "resume_binding": resume_binding,
            "selected_cluster_id": selected_cluster_ids[0],
            "selected_cluster_ids": selected_cluster_ids,
            "article_mode": str(selection["article_mode"]),
            "selection_request_logical_hash": selection[
                "selection_request_logical_hash"
            ],
            "selection_return_logical_hash": selection[
                "selection_return_logical_hash"
            ],
            "selection": dict(selection),
        }

    def prepare_native_desktop_scheduled_opportunity(
        self,
        *,
        automation_id: str,
        now: Optional[datetime] = None,
        coordinator_selection: Optional[Mapping[str, Any]] = None,
    ) -> dict[str, Any]:
        """Probe selection first; hydrate only the HIGH-admitted useful shortlist."""
        task_id, session, moment, window = self._resolve_native_desktop_due_window(
            automation_id=automation_id, now=now
        )
        if coordinator_selection is None:
            if window is None:
                return {
                    "schema_version": (
                        "contentops.native_desktop_scheduled_opportunity.v1"
                    ),
                    "automation_id": task_id,
                    "session": session,
                    "execution_owner": SCHEDULED_EDITORIAL_OWNER_NATIVE_DESKTOP,
                    "executed": False,
                    "reason": "scheduled_opportunity_not_due",
                    "public_write_authority": "ZERO",
                    "public_write_performed": False,
                    "unknown_write_detected": False,
                }
            prepared = self._load_prepared_candidate_checkpoint(window["end"])
            if prepared is None:
                self._refresh_prepared_candidate_checkpoint(moment)
                prepared = self._load_prepared_candidate_checkpoint(window["end"])
            if not isinstance(prepared, Mapping) or not self._candidate_packet(prepared):
                return super().prepare_native_desktop_scheduled_opportunity(
                    automation_id=automation_id, now=moment
                )
            artifact = self._build_selection_artifact(
                task_id=task_id,
                session=session,
                moment=moment,
                window=window,
                prepared_state=prepared,
            )
            path = self._persist_selection_artifact(artifact)
            request = dict(artifact["coordinator_request"])
            return {
                "schema_version": "contentops.native_desktop_scheduled_opportunity.v1",
                "automation_id": task_id,
                "session": session,
                "execution_owner": SCHEDULED_EDITORIAL_OWNER_NATIVE_DESKTOP,
                "scheduled_at_utc": _iso_utc(window["start"]),
                "actual_start_utc": _iso_utc(moment),
                "canonical_opportunity_id": str(window["window_id"]),
                "runtime_run_id": str(window["window_id"]),
                "classification": "HIGH_SELECTION_REQUIRED",
                "executed": False,
                "coordinator_selection_request": request,
                "selection_artifact_path": str(path),
                "newsroom_cycle_invocations": 0,
                "evidence_acquisition_requests": 0,
                "semantic_assignment_provider_calls": 0,
                "story_type_semantic_calls": 0,
                "public_write_authority": "ZERO",
                "public_write_performed": False,
                "unknown_write_detected": False,
            }

        opportunity_id = str(
            coordinator_selection.get("canonical_opportunity_id") or ""
        ).strip()
        if not opportunity_id:
            raise ValueError("native_llm_first_selection_opportunity_id_missing")
        artifact = self._load_selection_artifact(
            task_id=task_id, session=session, opportunity_id=opportunity_id
        )
        if moment > _parse_utc(str(artifact.get("expires_at_utc") or "")):
            raise ValueError("native_llm_first_selection_request_expired")
        selection = self._validate_selection_return(coordinator_selection, artifact)
        selection_receipt_path = self._persist_selection_return(
            opportunity_id=opportunity_id, selection=selection
        )
        binding = self._selected_assignment_binding(
            artifact=artifact, selection=selection
        )
        window_binding = dict(
            (artifact.get("runtime_binding") or {}).get("window") or {}
        )
        window_for_prepare = {
            "window_id": opportunity_id,
            "trigger": str(window_binding.get("trigger") or "SCHEDULED"),
            "start": _parse_utc(str(window_binding.get("start_utc") or "")),
            "end": _parse_utc(str(window_binding.get("end_utc") or "")),
            "session": str(window_binding.get("session") or session),
            "native_desktop_automation_id": task_id,
            "native_desktop_zero_public_write": True,
        }
        token = self._native_selection_binding.set({**binding, "phase": "PREPARE"})
        try:
            outcome = self._execute_window(
                window_for_prepare, moment, split_phase_operation="PREPARE"
            )
        finally:
            self._native_selection_binding.reset(token)
        result = self._native_desktop_zero_write_result(
            task_id=task_id,
            session=session,
            moment=moment,
            window=window_for_prepare,
            outcome=outcome,
        )
        result["coordinator_selection"] = selection
        result["selection_artifact_path"] = str(
            self._selection_artifact_path(opportunity_id)
        )
        result["selection_return_path"] = str(selection_receipt_path)
        result["native_llm_first_ordering"] = (
            "HIGH_SELECTION_THEN_FRESH_HIGH_WORKER_THEN_DETERMINISTIC_VALIDATE_AFTER"
        )
        return result

    @staticmethod
    def _validated_native_resume_binding(
        value: Mapping[str, Any],
        *,
        intake: Mapping[str, Any] | None = None,
        viability: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        binding = dict(value)
        claimed_hash = str(binding.pop("resume_binding_logical_hash", "") or "")
        if (
            binding.get("schema_version")
            != "contentops.native_llm_first_assignment_resume.v1"
            or not claimed_hash
            or claimed_hash != _logical_hash(binding)
            or binding.get("factual_or_numeric_authority_granted") is not False
            or binding.get("publication_authority_granted") is not False
        ):
            raise ValueError("native_llm_first_resume_binding_invalid")
        assignment = dict(binding.get("assignment_override") or {})
        assignment_hash = str(assignment.pop("assignment_logical_hash", "") or "")
        if (
            not assignment_hash
            or assignment_hash != _logical_hash(assignment)
            or assignment.get("status") != "SUCCESS"
            or assignment.get("decision") != "SELECT_STORY"
        ):
            raise ValueError("native_llm_first_resume_assignment_invalid")
        assignment = {**assignment, "assignment_logical_hash": assignment_hash}
        admitted_ids = [str(value) for value in binding.get("selected_cluster_ids") or []]
        ranked_ids = [
            str(row.get("cluster_id") or "")
            for row in assignment.get("ranked_clusters") or []
            if isinstance(row, Mapping)
        ]
        story_types = {
            str(key): str(value)
            for key, value in dict(binding.get("story_type_by_cluster") or {}).items()
        }
        input_hash = str(binding.get("rolling_input_canonical_hash") or "")
        input_binding = dict(assignment.get("input_binding") or {})
        if (
            not admitted_ids
            or len(admitted_ids) != len(set(admitted_ids))
            or ranked_ids != admitted_ids
            or set(story_types) != set(admitted_ids)
            or len(input_hash) != 64
            or str(input_binding.get("canonical_input_hash") or "") != input_hash
        ):
            raise ValueError("native_llm_first_resume_scope_invalid")
        selected_headline_ids = [
            str(value) for value in assignment.get("selected_headline_ids") or []
        ]
        if intake is not None:
            if (
                str(intake.get("canonical_input_hash") or "") != input_hash
                or list(intake.get("unique_headline_ids") or []) != selected_headline_ids
            ):
                raise ValueError("native_llm_first_resume_intake_invalid")
        if viability is not None:
            selected_viability_id = str(viability.get("selected_cluster_id") or "")
            if selected_viability_id and selected_viability_id not in set(admitted_ids):
                raise ValueError("native_llm_first_resume_viability_outside_shortlist")
        binding["assignment_override"] = assignment
        return {**binding, "resume_binding_logical_hash": claimed_hash}

    def _persist_native_desktop_pending_handoff(
        self,
        *,
        window: Mapping[str, Any],
        attempt_number: int,
        attempt_run_id: str,
        attempt_output_dir: Path,
        attempt_result: Mapping[str, Any],
        prior_attempt_results: Sequence[Mapping[str, Any]],
        qualified_records: Sequence[Mapping[str, Any]],
        work_budget: int,
    ) -> dict[str, Any]:
        native_prevalidation = attempt_result.get("native_llm_first_prevalidation")
        if isinstance(native_prevalidation, Mapping):
            from live_contentops.native_desktop_production_handoff_v1 import (
                load_handoff_checkpoint,
                logical_hash,
                persist_handoff_checkpoint,
                read_json,
                validate_worker_request_binding,
            )
            from live_contentops.native_llm_first_validate_after_v1 import (
                INITIAL_HANDOFF_STATUS,
                INITIAL_NEXT_BLOCKER,
            )

            result = dict(attempt_result)
            route = dict(result.get("editorial_worker_routing") or {})
            worker_request = dict(route.get("worker_request") or {})
            governed_hash = str(
                route.get("governed_input_hash")
                or worker_request.get("governed_input_hash")
                or ""
            )
            worker_request = validate_worker_request_binding(
                worker_request, expected_governed_input_hash=governed_hash
            )
            current_path = self._native_desktop_handoff_path(str(window["window_id"]))
            sequence = 1
            if current_path.exists():
                sequence = int(
                    load_handoff_checkpoint(current_path).get("resume_sequence") or 0
                ) + 1
            intake_path = attempt_output_dir / "rolling_x_intake_v1.json"
            assignment_path = attempt_output_dir / "rolling_x_assignment_v1.json"
            story_path = attempt_output_dir / "rolling_x_story_routing_v1.json"
            prevalidation_path = attempt_output_dir / "native_llm_first_prevalidation_v1.json"
            if not all(
                path.is_file()
                for path in (intake_path, assignment_path, story_path, prevalidation_path)
            ):
                raise ValueError("native_llm_first_prevalidation_checkpoint_missing")
            intake = read_json(intake_path)
            semantic_material = {
                "leaf_checkpoints": {},
                "global_checkpoint": {},
                "story_type_by_cluster": dict(
                    (result.get("story_routing") or {}).get(
                        "story_type_by_cluster"
                    )
                    or {}
                ),
            }
            semantic_bindings = {
                **semantic_material,
                "canonical_input_hash": intake.get("canonical_input_hash"),
                "semantic_resume_mode": "NATIVE_LLM_FIRST_ASSIGNMENT_OVERRIDE",
                "semantic_resume_logical_hash": logical_hash(semantic_material),
            }
            prevalidation_state = {
                **dict(native_prevalidation),
                "candidate_plan_index": 0,
                "bounded_revision_count": 0,
                "current_candidate_worker_receipts": [],
                "prior_candidate_attempts": [],
                "intake_checkpoint_path": str(intake_path),
                "assignment_checkpoint_path": str(assignment_path),
                "story_routing_checkpoint_path": str(story_path),
                "prevalidation_checkpoint_path": str(prevalidation_path),
            }
            checkpoint = {
                "canonical_opportunity_id": str(window["window_id"]),
                "runtime_run_id": str(window["window_id"]),
                "automation_id": str(window.get("native_desktop_automation_id") or ""),
                "session": str(window.get("session") or ""),
                "attempt_number": int(attempt_number),
                "attempt_run_id": str(attempt_run_id),
                "work_budget": int(work_budget),
                "resume_sequence": sequence,
                "handoff_status": INITIAL_HANDOFF_STATUS,
                "exact_next_blocker": INITIAL_NEXT_BLOCKER,
                "governed_input_hash": governed_hash,
                "editorial_worker_request": worker_request,
                "same_xhigh_worker_revision_contract": {},
                "same_high_worker_revision_contract": {},
                "prepare_cycle_evidence_path": str(prevalidation_path),
                "prepare_cycle_evidence_sha256": logical_hash(
                    read_json(prevalidation_path)
                ),
                "intake_checkpoint_path": str(intake_path),
                "intake_checkpoint_sha256": logical_hash(intake),
                "prepared_candidate_checkpoint_path": str(
                    self._selection_artifact_path(str(window["window_id"]))
                ),
                "viability_checkpoint_path": None,
                "viability_logical_hash": None,
                "semantic_resume_bindings": semantic_bindings,
                "native_llm_first_resume_binding": dict(
                    native_prevalidation.get("native_llm_first_resume_binding") or {}
                ),
                "native_llm_first_prevalidation": prevalidation_state,
                "candidate_rank": 1,
                "candidate_cluster_id": native_prevalidation.get(
                    "selected_cluster_id"
                ),
                "candidate_headline_ids": list(
                    native_prevalidation.get("selected_headline_ids") or []
                ),
                "prior_attempt_results": [dict(row) for row in prior_attempt_results],
                "qualified_records": [dict(row) for row in qualified_records],
                "public_write_performed": False,
                "unknown_write_detected": False,
                "legacy_writer_fallback_used": False,
                "sdk_writer_substitution_used": False,
                "handoff_checkpoint_path": str(current_path),
            }
            return persist_handoff_checkpoint(current_path, checkpoint)

        native_resume_raw = attempt_result.get("native_llm_first_resume_binding")
        if not isinstance(native_resume_raw, Mapping):
            return super()._persist_native_desktop_pending_handoff(
                window=window,
                attempt_number=attempt_number,
                attempt_run_id=attempt_run_id,
                attempt_output_dir=attempt_output_dir,
                attempt_result=attempt_result,
                prior_attempt_results=prior_attempt_results,
                qualified_records=qualified_records,
                work_budget=work_budget,
            )
        from live_contentops.native_desktop_production_handoff_v1 import (
            WORKER_DECISION,
            load_handoff_checkpoint,
            logical_hash,
            persist_handoff_checkpoint,
            read_json,
            validate_same_worker_revision_contract,
            validate_worker_request_binding,
            validated_viability_checkpoint,
        )

        result = dict(attempt_result)
        reason = str(result.get("exact_next_blocker") or "")
        revision_contract = dict(result.get("same_xhigh_worker_revision_contract") or {})
        route = dict(result.get("editorial_worker_routing") or {})
        if reason == "SAME_XHIGH_WORKER_REVISION_REQUIRED":
            revision_contract = validate_same_worker_revision_contract(revision_contract)
            worker_request = dict(revision_contract.get("worker_request") or {})
            governed_hash = str(
                revision_contract.get("governed_input_hash")
                or worker_request.get("governed_input_hash")
                or ""
            )
            handoff_status = "SAME_XHIGH_WORKER_REVISION_REQUIRED"
        else:
            if route.get("decision") != WORKER_DECISION:
                raise ValueError("native_desktop_pending_worker_route_missing")
            worker_request = dict(route.get("worker_request") or {})
            governed_hash = str(
                route.get("governed_input_hash")
                or worker_request.get("governed_input_hash")
                or ""
            )
            handoff_status = (
                "XHIGH_REQUIRED_FOR_CANDIDATE_CONTINUATION"
                if reason == "NEXT_NATIVE_XHIGH_WORKER_REQUIRED"
                else "XHIGH_REQUIRED"
            )
        if (
            len(governed_hash) != 64
            or str(worker_request.get("governed_input_hash") or "") != governed_hash
        ):
            raise ValueError("native_desktop_pending_worker_hash_invalid")

        cycle_path = attempt_output_dir / "rolling_x_newsroom_cycle_evidence_v1.json"
        viability_path = attempt_output_dir / "rolling_x_ranked_viability_v1.json"
        intake_path = attempt_output_dir / "rolling_x_intake_v1.json"
        if not cycle_path.is_file() or not viability_path.is_file() or not intake_path.is_file():
            raise ValueError("native_desktop_pending_canonical_checkpoint_missing")
        viability = validated_viability_checkpoint(read_json(viability_path))
        intake = read_json(intake_path)
        native_resume = self._validated_native_resume_binding(
            native_resume_raw, intake=intake, viability=viability
        )
        worker_request = validate_worker_request_binding(
            worker_request,
            expected_governed_input_hash=governed_hash,
            viability=viability,
            allow_same_worker_revision=bool(revision_contract),
        )
        semantic_material = {
            "leaf_checkpoints": {},
            "global_checkpoint": {},
            "story_type_by_cluster": dict(
                native_resume.get("story_type_by_cluster") or {}
            ),
        }
        semantic_bindings = {
            **semantic_material,
            "canonical_input_hash": native_resume["rolling_input_canonical_hash"],
            "semantic_resume_mode": "NATIVE_LLM_FIRST_ASSIGNMENT_OVERRIDE",
            "semantic_resume_logical_hash": logical_hash(semantic_material),
        }

        current_path = self._native_desktop_handoff_path(str(window["window_id"]))
        sequence = 1
        if current_path.exists():
            sequence = int(load_handoff_checkpoint(current_path).get("resume_sequence") or 0) + 1
        checkpoint = {
            "canonical_opportunity_id": str(window["window_id"]),
            "runtime_run_id": str(window["window_id"]),
            "automation_id": str(window.get("native_desktop_automation_id") or ""),
            "session": str(window.get("session") or ""),
            "attempt_number": int(attempt_number),
            "attempt_run_id": str(attempt_run_id),
            "work_budget": int(work_budget),
            "resume_sequence": sequence,
            "handoff_status": handoff_status,
            "exact_next_blocker": (
                reason
                if reason in {
                    "SAME_XHIGH_WORKER_REVISION_REQUIRED",
                    "NEXT_NATIVE_XHIGH_WORKER_REQUIRED",
                }
                else WORKER_DECISION
            ),
            "governed_input_hash": governed_hash,
            "editorial_worker_request": worker_request,
            "same_xhigh_worker_revision_contract": revision_contract,
            "prepare_cycle_evidence_path": str(cycle_path),
            "prepare_cycle_evidence_sha256": logical_hash(read_json(cycle_path)),
            "intake_checkpoint_path": str(intake_path),
            "intake_checkpoint_sha256": logical_hash(intake),
            "prepared_candidate_checkpoint_path": str(
                attempt_output_dir / "rolling_x_prepared_candidate_state_v1.json"
            ),
            "viability_checkpoint_path": str(viability_path),
            "viability_logical_hash": viability.get("viability_logical_hash"),
            "semantic_resume_bindings": semantic_bindings,
            "native_llm_first_resume_binding": native_resume,
            "candidate_rank": viability.get("selected_rank"),
            "candidate_cluster_id": viability.get("selected_cluster_id"),
            "candidate_headline_ids": list(viability.get("selected_headline_ids") or []),
            "prior_attempt_results": [dict(row) for row in prior_attempt_results],
            "qualified_records": [dict(row) for row in qualified_records],
            "public_write_performed": bool(result.get("public_write_performed")),
            "unknown_write_detected": bool(result.get("unknown_write_detected")),
            "legacy_writer_fallback_used": False,
            "sdk_writer_substitution_used": False,
            "handoff_checkpoint_path": str(current_path),
        }
        return persist_handoff_checkpoint(current_path, checkpoint)

    def complete_native_desktop_scheduled_opportunity(
        self,
        *,
        automation_id: str,
        canonical_opportunity_id: str,
        worker_return: Mapping[str, Any],
        coordinator_review_receipt: Mapping[str, Any],
        now: Optional[datetime] = None,
    ) -> dict[str, Any]:
        task_id = str(automation_id or "").strip()
        session = NATIVE_DESKTOP_AUTOMATION_SESSION_BY_ID.get(task_id)
        if not session:
            raise ValueError("native_llm_first_automation_id_invalid")
        opportunity_id = str(canonical_opportunity_id or "").strip()
        artifact = self._load_selection_artifact(
            task_id=task_id, session=session, opportunity_id=opportunity_id
        )
        return_path = self._selection_return_path(opportunity_id)
        try:
            persisted_selection = json.loads(return_path.read_text(encoding="utf-8"))
        except (OSError, TypeError, ValueError) as exc:
            raise ValueError("native_llm_first_selection_return_missing_or_invalid") from exc
        if not isinstance(persisted_selection, Mapping):
            raise ValueError("native_llm_first_selection_return_missing_or_invalid")
        selection = self._validate_selection_return(persisted_selection, artifact)
        binding = self._selected_assignment_binding(artifact=artifact, selection=selection)

        from live_contentops.native_desktop_production_handoff_v1 import (
            load_handoff_checkpoint,
            persist_handoff_checkpoint,
        )
        from live_contentops.native_llm_first_validate_after_v1 import (
            INITIAL_HANDOFF_STATUS,
            INITIAL_NEXT_BLOCKER,
            REVISION_HANDOFF_STATUS,
            REVISION_NEXT_BLOCKER,
            NativeDesktopExternalLlmFirstProvider,
            build_external_worker_request,
            build_same_high_revision_contract,
            normalized_external_worker_receipt_for_failure,
            selection_for_candidate,
            validate_same_high_revision_contract,
        )
        from live_contentops.llm_first_validate_after_v1 import LlmFirstValidationError

        handoff_path = self._native_desktop_handoff_path(opportunity_id)
        handoff = load_handoff_checkpoint(handoff_path)
        prevalidation = handoff.get("native_llm_first_prevalidation")
        if not isinstance(prevalidation, Mapping):
            # Backward-compatible completion for old native evidence-first handoffs.
            token = self._native_selection_binding.set({**binding, "phase": "COMPLETE"})
            try:
                return super().complete_native_desktop_scheduled_opportunity(
                    automation_id=task_id,
                    canonical_opportunity_id=opportunity_id,
                    worker_return=worker_return,
                    coordinator_review_receipt=coordinator_review_receipt,
                    now=now,
                )
            finally:
                self._native_selection_binding.reset(token)

        stored_resume = dict(handoff.get("native_llm_first_resume_binding") or {})
        if stored_resume != dict(binding.get("resume_binding") or {}):
            raise ValueError("native_llm_first_complete_resume_binding_drift")
        candidate_index = int(prevalidation.get("candidate_plan_index") or 0)
        revision_count = int(prevalidation.get("bounded_revision_count") or 0)
        revision_contract = dict(handoff.get("same_high_worker_revision_contract") or {})
        if revision_count:
            validate_same_high_revision_contract(revision_contract)
        current_request, current_candidate, current_selection = build_external_worker_request(
            binding=binding,
            selection=selection,
            cutoff_utc=str(
                (artifact.get("coordinator_request") or {}).get(
                    "opportunity_cutoff_utc"
                )
                or ""
            ),
            candidate_index=candidate_index,
            revision_contract=revision_contract if revision_count else None,
        )
        if current_request != dict(handoff.get("editorial_worker_request") or {}):
            raise ValueError("native_llm_first_complete_worker_request_drift")
        resume_sequence = int(handoff.get("resume_sequence") or 1)
        provider_output_dir = self._output_root / opportunity_id / (
            f"split-phase-resume-{resume_sequence:02d}"
        )
        prior_current_receipts = [
            dict(row)
            for row in prevalidation.get("current_candidate_worker_receipts") or []
            if isinstance(row, Mapping)
        ]
        prior_candidate_attempts = [
            dict(row)
            for row in prevalidation.get("prior_candidate_attempts") or []
            if isinstance(row, Mapping)
        ]
        provider = NativeDesktopExternalLlmFirstProvider(
            output_dir=provider_output_dir,
            selected_selection=current_selection,
            expected_worker_request=current_request,
            worker_return=worker_return,
            candidate_index=candidate_index,
            revision_count=revision_count,
            prior_current_candidate_receipts=prior_current_receipts,
            prior_candidate_attempts=prior_candidate_attempts,
        )
        try:
            provider.prepare(
                ranked_clusters=binding["assignment_override"]["ranked_clusters"],
                intake=binding["rolling_input_override"],
                cutoff_utc=str(
                    (artifact.get("coordinator_request") or {}).get(
                        "opportunity_cutoff_utc"
                    )
                    or ""
                ),
                published_corpus=[],
            )
        except LlmFirstValidationError as exc:
            failure_receipt = normalized_external_worker_receipt_for_failure(
                worker_return=worker_return,
                expected_worker_request=current_request,
                revision=bool(revision_count),
            )
            current_receipts = [*prior_current_receipts, failure_receipt]
            attempts = [
                *prior_candidate_attempts,
                {
                    "cluster_id": current_selection["selected_cluster_id"],
                    "candidate_plan_index": candidate_index,
                    "status": "POST_GENERATION_VALIDATION_BLOCKED",
                    "blockers": list(exc.blockers),
                    "bounded_revision_count": revision_count,
                    "worker_receipt": failure_receipt,
                },
            ]
            updated = {
                key: value
                for key, value in handoff.items()
                if key != "handoff_logical_hash"
            }
            updated["resume_sequence"] = resume_sequence + 1
            updated["prior_candidate_attempts"] = attempts
            if revision_count == 0:
                contract = build_same_high_revision_contract(
                    governed_input_hash=current_request["governed_input_hash"],
                    worker_return=worker_return,
                    blockers=exc.blockers,
                    prior_bounded_revision_count=0,
                )
                revision_request, _candidate, _selection_row = build_external_worker_request(
                    binding=binding,
                    selection=selection,
                    cutoff_utc=str(
                        (artifact.get("coordinator_request") or {}).get(
                            "opportunity_cutoff_utc"
                        )
                        or ""
                    ),
                    candidate_index=candidate_index,
                    revision_contract=contract,
                )
                updated.update(
                    {
                        "handoff_status": REVISION_HANDOFF_STATUS,
                        "exact_next_blocker": REVISION_NEXT_BLOCKER,
                        "governed_input_hash": revision_request["governed_input_hash"],
                        "editorial_worker_request": revision_request,
                        "same_high_worker_revision_contract": contract,
                        "same_xhigh_worker_revision_contract": {},
                        "candidate_rank": candidate_index + 1,
                        "candidate_cluster_id": current_selection[
                            "selected_cluster_id"
                        ],
                        "candidate_headline_ids": list(
                            current_candidate.get("headline_ids") or []
                        ),
                        "native_llm_first_prevalidation": {
                            **dict(prevalidation),
                            "candidate_plan_index": candidate_index,
                            "bounded_revision_count": 1,
                            "selected_cluster_id": current_selection[
                                "selected_cluster_id"
                            ],
                            "selected_headline_ids": list(
                                current_candidate.get("headline_ids") or []
                            ),
                            "current_candidate_worker_receipts": current_receipts,
                            "prior_candidate_attempts": attempts,
                        },
                    }
                )
                persisted = persist_handoff_checkpoint(handoff_path, updated)
                return self._native_desktop_pending_handoff_outcome(persisted)

            next_index = candidate_index + 1
            try:
                next_selection = selection_for_candidate(
                    selection, candidate_index=next_index
                )
            except ValueError:
                token = self._native_selection_binding.set(
                    {**binding, "phase": "TERMINAL"}
                )
                try:
                    return super().complete_native_desktop_scheduled_opportunity(
                        automation_id=task_id,
                        canonical_opportunity_id=opportunity_id,
                        worker_return=worker_return,
                        coordinator_review_receipt=coordinator_review_receipt,
                        now=now,
                    )
                finally:
                    self._native_selection_binding.reset(token)

            fresh_request, next_candidate, _next_selection = build_external_worker_request(
                binding=binding,
                selection=selection,
                cutoff_utc=str(
                    (artifact.get("coordinator_request") or {}).get(
                        "opportunity_cutoff_utc"
                    )
                    or ""
                ),
                candidate_index=next_index,
            )
            updated.update(
                {
                    "handoff_status": INITIAL_HANDOFF_STATUS,
                    "exact_next_blocker": INITIAL_NEXT_BLOCKER,
                    "governed_input_hash": fresh_request["governed_input_hash"],
                    "editorial_worker_request": fresh_request,
                    "same_high_worker_revision_contract": {},
                    "same_xhigh_worker_revision_contract": {},
                    "candidate_rank": next_index + 1,
                    "candidate_cluster_id": next_selection["selected_cluster_id"],
                    "candidate_headline_ids": list(
                        next_candidate.get("headline_ids") or []
                    ),
                    "native_llm_first_prevalidation": {
                        **dict(prevalidation),
                        "candidate_plan_index": next_index,
                        "bounded_revision_count": 0,
                        "selected_cluster_id": next_selection["selected_cluster_id"],
                        "selected_headline_ids": list(
                            next_candidate.get("headline_ids") or []
                        ),
                        "current_candidate_worker_receipts": [],
                        "prior_candidate_attempts": attempts,
                    },
                }
            )
            persisted = persist_handoff_checkpoint(handoff_path, updated)
            return self._native_desktop_pending_handoff_outcome(persisted)

        token = self._native_selection_binding.set(
            {**binding, "phase": "COMPLETE", "external_provider": provider}
        )
        try:
            return super().complete_native_desktop_scheduled_opportunity(
                automation_id=task_id,
                canonical_opportunity_id=opportunity_id,
                worker_return=worker_return,
                coordinator_review_receipt=coordinator_review_receipt,
                now=now,
            )
        finally:
            self._native_selection_binding.reset(token)

    def execute_native_desktop_scheduled_opportunity(
        self,
        *,
        automation_id: str,
        now: Optional[datetime] = None,
        coordinator_selection: Optional[Mapping[str, Any]] = None,
    ) -> dict[str, Any]:
        return self.prepare_native_desktop_scheduled_opportunity(
            automation_id=automation_id,
            now=now,
            coordinator_selection=coordinator_selection,
        )
