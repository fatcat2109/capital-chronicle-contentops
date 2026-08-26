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
from typing import Any, Mapping, Optional

from live_contentops.daily_app_supervisor_v1 import (
    ContentOpsDailyAppSupervisor,
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
        if kwargs.get("native_desktop_prepare") is not True:
            raise ValueError("native_llm_first_selection_only_valid_for_desktop_prepare")
        narrowed = dict(kwargs)
        # The full prepared frontier was selection input only. Once HIGH returns its bounded
        # useful shortlist, canonical preselection/evidence may walk only those admitted stories.
        narrowed["prepared_candidate_state"] = None
        narrowed["assignment_override"] = dict(binding["assignment_override"])
        narrowed["story_type_by_cluster"] = dict(binding["story_type_by_cluster"])
        result = self._canonical_newsroom_cycle(**narrowed)
        if not isinstance(result, Mapping):
            return result
        return {
            **dict(result),
            "native_llm_first_selection": {
                "ordering": "HIGH_SELECTION_THEN_SELECTED_STORY_DETERMINISTIC_HYDRATION",
                "selection_request_logical_hash": binding[
                    "selection_request_logical_hash"
                ],
                "selection_return_logical_hash": binding[
                    "selection_return_logical_hash"
                ],
                "selected_cluster_id": binding["selected_cluster_id"],
                "selected_cluster_ids": list(binding["selected_cluster_ids"]),
                "selected_article_mode": binding["article_mode"],
                "full_prepared_frontier_reopened": False,
                "high_admitted_shortlist_count": len(binding["selected_cluster_ids"]),
                "semantic_assignment_provider_call_required": False,
                "story_type_semantic_call_required": False,
                "factual_or_numeric_authority_granted": False,
                "publication_authority_granted": False,
            },
        }

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
            selected_cluster_ids.append(cluster_id)
            for headline_id in headline_ids:
                if headline_id not in selected_headline_ids:
                    selected_headline_ids.append(headline_id)
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

        input_binding = dict(source_assignment.get("input_binding") or {})
        input_binding.update(
            {
                "input_ids": selected_headline_ids,
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
            "leaf_clusters": [
                dict(row)
                for row in source_assignment.get("leaf_clusters") or []
                if isinstance(row, Mapping)
                and (
                    not selected_leaf_ids
                    or str(row.get("leaf_cluster_id") or "") in selected_leaf_ids
                )
            ],
            "selected_cluster_id": selected_cluster_ids[0],
            "selected_cluster_ids": selected_cluster_ids,
            "selected_headline_ids": selected_headline_ids,
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
        assignment.pop("assignment_logical_hash", None)
        assignment["assignment_logical_hash"] = _logical_hash(assignment)

        story_types = dict(runtime.get("story_type_by_cluster") or {})
        selected_story_types: dict[str, str] = {}
        for cluster_id in selected_cluster_ids:
            story_type = str(story_types.get(cluster_id) or "").strip()
            if not story_type:
                raise ValueError("native_llm_first_selected_story_type_missing")
            selected_story_types[cluster_id] = story_type
        return {
            "assignment_override": assignment,
            "story_type_by_cluster": selected_story_types,
            "selected_cluster_id": selected_cluster_ids[0],
            "selected_cluster_ids": selected_cluster_ids,
            "article_mode": str(selection["article_mode"]),
            "selection_request_logical_hash": selection[
                "selection_request_logical_hash"
            ],
            "selection_return_logical_hash": selection[
                "selection_return_logical_hash"
            ],
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
        token = self._native_selection_binding.set(binding)
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
            "HIGH_SELECTION_THEN_SELECTED_STORY_DETERMINISTIC_HYDRATION"
        )
        return result

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
