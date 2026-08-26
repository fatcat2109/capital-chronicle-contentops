from __future__ import annotations

import subprocess
from pathlib import Path

NATIVE_PATH = Path("live_contentops/native_llm_first_daily_app_supervisor_v1.py")
TEST_PATH = Path("tests/test_native_llm_first_daily_app_supervisor_v1.py")
EXPECTED_NATIVE_BLOB = "1bc44424e750e4358a600a88dd17ef1b2f9babeb"
EXPECTED_TEST_BLOB = "53470ac6cb3da23e6d1151c390def70bb4e38d60"


def git_blob(path: Path) -> str:
    return subprocess.check_output(["git", "hash-object", str(path)], text=True).strip()


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one match, found {count}")
    return text.replace(old, new, 1)


def replace_between(text: str, start: str, end: str, replacement: str, label: str) -> str:
    first = text.find(start)
    if first < 0:
        raise RuntimeError(f"{label}: start marker missing")
    second = text.find(end, first)
    if second < 0:
        raise RuntimeError(f"{label}: end marker missing")
    return text[:first] + replacement + text[second:]


if git_blob(NATIVE_PATH) != EXPECTED_NATIVE_BLOB:
    raise RuntimeError("native supervisor blob drifted; refusing one-shot correction")
if git_blob(TEST_PATH) != EXPECTED_TEST_BLOB:
    raise RuntimeError("native supervisor test blob drifted; refusing one-shot correction")

text = NATIVE_PATH.read_text(encoding="utf-8")
text = replace_once(
    text,
    "from typing import Any, Mapping, Optional\n",
    "from typing import Any, Mapping, Optional, Sequence\n",
    "typing import",
)
text = replace_once(
    text,
    "from live_contentops.daily_app_supervisor_v1 import (\n    ContentOpsDailyAppSupervisor,\n    SCHEDULED_EDITORIAL_OWNER_NATIVE_DESKTOP,\n)\n",
    "from live_contentops.daily_app_supervisor_v1 import (\n    ContentOpsDailyAppSupervisor,\n    NATIVE_DESKTOP_AUTOMATION_SESSION_BY_ID,\n    SCHEDULED_EDITORIAL_OWNER_NATIVE_DESKTOP,\n)\n",
    "daily supervisor import",
)

new_cycle = '''    def _native_llm_first_newsroom_cycle(self, **kwargs: Any) -> Mapping[str, Any]:
        binding = self._native_selection_binding.get()
        if binding is None:
            return self._canonical_newsroom_cycle(**kwargs)
        phase = str(binding.get("phase") or "PREPARE").strip().upper()
        if phase not in {"PREPARE", "COMPLETE"}:
            raise ValueError("native_llm_first_resume_phase_invalid")
        if phase == "PREPARE" and kwargs.get("native_desktop_prepare") is not True:
            raise ValueError("native_llm_first_selection_only_valid_for_desktop_prepare")

        narrowed = dict(kwargs)
        rolling_input = dict(binding["rolling_input_override"])
        expected_input_hash = str(rolling_input.get("canonical_input_hash") or "")
        supplied_input = narrowed.get("rolling_input")
        if phase == "COMPLETE" and isinstance(supplied_input, Mapping):
            supplied_hash = str(supplied_input.get("canonical_input_hash") or "")
            if supplied_hash and supplied_hash != expected_input_hash:
                raise ValueError("native_llm_first_complete_intake_binding_mismatch")

        # The HIGH selection packet is the complete candidate universe for this opportunity
        # continuation.  Narrow both the rolling input and assignment so the canonical
        # publishability pool cannot synthesize reserve candidates from the full intake.
        narrowed["prepared_candidate_state"] = None
        narrowed["rolling_input"] = rolling_input
        narrowed["assignment_override"] = dict(binding["assignment_override"])
        narrowed["story_type_by_cluster"] = dict(binding["story_type_by_cluster"])
        # Historical semantic checkpoints were produced for the pre-selection frontier and are
        # intentionally not replayed against the newly narrowed input. Assignment override is the
        # exact deterministic resume authority for this path.
        narrowed["leaf_checkpoints"] = {}
        narrowed["global_checkpoint"] = None
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
                "canonical_rolling_input_hash": expected_input_hash,
                "full_prepared_frontier_reopened": False,
                "high_admitted_shortlist_count": len(binding["selected_cluster_ids"]),
                "semantic_assignment_provider_call_required": False,
                "story_type_semantic_call_required": False,
                "factual_or_numeric_authority_granted": False,
                "publication_authority_granted": False,
            },
            "native_llm_first_resume_binding": dict(binding["resume_binding"]),
        }

'''
text = replace_between(
    text,
    "    def _native_llm_first_newsroom_cycle(self, **kwargs: Any) -> Mapping[str, Any]:\n",
    "    def _selection_artifact_path(self, opportunity_id: str) -> Path:\n",
    new_cycle,
    "native cycle",
)

text = replace_once(
    text,
    '                "assignment": dict(prepared_state.get("assignment") or {}),\n',
    '                "prepared_input": dict(prepared_state.get("prepared_input") or {}),\n                "assignment": dict(prepared_state.get("assignment") or {}),\n',
    "prepared input runtime binding",
)

text = replace_once(
    text,
    '        normalized = {\n            "schema_version": str(selection.get("schema_version") or ""),\n',
    '        normalized = {\n            "schema_version": str(selection.get("schema_version") or ""),\n            "canonical_opportunity_id": str(\n                selection.get("canonical_opportunity_id") or ""\n            ),\n',
    "selection opportunity normalization",
)
text = replace_once(
    text,
    '        if normalized["schema_version"] != SELECTION_RETURN_SCHEMA_VERSION:\n            raise ValueError("native_llm_first_selection_schema_invalid")\n        if normalized["selection_request_logical_hash"] != str(\n',
    '        if normalized["schema_version"] != SELECTION_RETURN_SCHEMA_VERSION:\n            raise ValueError("native_llm_first_selection_schema_invalid")\n        if normalized["canonical_opportunity_id"] != str(\n            request.get("canonical_opportunity_id") or ""\n        ):\n            raise ValueError("native_llm_first_selection_opportunity_id_mismatch")\n        if normalized["selection_request_logical_hash"] != str(\n',
    "selection opportunity validation",
)

new_binding = '''    @staticmethod
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
        }

'''
text = replace_between(
    text,
    "    @staticmethod\n    def _selected_assignment_binding(\n",
    "    def prepare_native_desktop_scheduled_opportunity(\n",
    new_binding,
    "selected assignment binding",
)

text = replace_once(
    text,
    "        token = self._native_selection_binding.set(binding)\n",
    '        token = self._native_selection_binding.set({**binding, "phase": "PREPARE"})\n',
    "prepare binding phase",
)

insert_methods = '''    @staticmethod
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
        binding = self._selected_assignment_binding(
            artifact=artifact, selection=selection
        )
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

'''
marker = "    def execute_native_desktop_scheduled_opportunity(\n"
if marker not in text:
    raise RuntimeError("execute method marker missing")
text = text.replace(marker, insert_methods + marker, 1)

NATIVE_PATH.write_text(text, encoding="utf-8")

# Append focused host regressions to the existing exact PR30 test family so normal ci-fast runs
# them without creating another test-routing surface.
tests = TEST_PATH.read_text(encoding="utf-8")
if "PR30_HOST_STATIC_REGRESSIONS_V1" in tests:
    raise RuntimeError("host regression block already present")
tests += r'''

# PR30_HOST_STATIC_REGRESSIONS_V1

def _pool_valid_prepared_state() -> dict:
    import copy

    state = copy.deepcopy(_prepared_state())
    prepared_input = state["prepared_input"]
    prepared_input.update(
        {
            "schema_version": "capital_chronicle.rolling_x_headline_input.v1",
            "cutoff_time_utc": "2026-08-26T11:00:00Z",
            "window_start_utc": "2026-08-25T11:00:00Z",
            "window_hours": 24.0,
            "counts": {"accepted_in_full_rolling_intake": 1093, "accepted": 3},
        }
    )
    from live_contentops.native_llm_first_daily_app_supervisor_v1 import _logical_hash
    from live_contentops.newsroom_assignment_scheduler_v1 import (
        _rolling_x_canonical_hash_material,
    )

    prepared_input["canonical_input_hash"] = _logical_hash(
        _rolling_x_canonical_hash_material(prepared_input)
    )
    state["assignment"]["input_binding"]["canonical_input_hash"] = prepared_input[
        "canonical_input_hash"
    ]
    for index, leaf in enumerate(state["assignment"]["leaf_clusters"], start=1):
        member = leaf["member_headline_ids"][0]
        leaf.update(
            {
                "partition_id": f"partition-{index}",
                "partition_index": index,
                "canonical_representative_headline_id": member,
                "event_topic_summary": f"summary-{member}",
            }
        )
    return state


def test_selected_shortlist_narrows_real_publishability_pool_before_evidence(tmp_path: Path):
    from live_contentops.newsroom_assignment_scheduler_v1 import (
        build_bounded_rolling_x_publishability_pool,
    )

    state = _pool_valid_prepared_state()
    supervisor = _supervisor(tmp_path, lambda **_kwargs: {})
    supervisor._load_prepared_candidate_checkpoint = lambda _cutoff: state
    probe = supervisor.prepare_native_desktop_scheduled_opportunity(
        automation_id="v1-newsroom-london-1700", now=NOW
    )
    artifact = supervisor._load_selection_artifact(
        task_id="v1-newsroom-london-1700",
        session="london_1700_bangkok",
        opportunity_id=probe["canonical_opportunity_id"],
    )
    selection = supervisor._validate_selection_return(_selection_from_probe(probe), artifact)
    binding = supervisor._selected_assignment_binding(artifact=artifact, selection=selection)

    narrowed = binding["rolling_input_override"]
    assignment = binding["assignment_override"]
    assert narrowed["unique_headline_ids"] == ["headline-b"]
    assert [row["headline_id"] for row in narrowed["headlines"]] == ["headline-b"]
    assert narrowed["counts"]["accepted_in_full_rolling_intake"] == 1093
    assert narrowed["counts"]["accepted"] == 1
    assert assignment["input_binding"]["canonical_input_hash"] == narrowed[
        "canonical_input_hash"
    ]
    assert assignment["input_binding"]["input_ids"] == ["headline-b"]

    pooled = build_bounded_rolling_x_publishability_pool(
        assignment=assignment, rolling_input=narrowed
    )
    assert [row["cluster_id"] for row in pooled["ranked_clusters"]] == ["cluster-b"]
    assert pooled["publishability_candidate_pool"]["combined_candidate_count"] == 1
    assert pooled["publishability_candidate_pool"]["full_universe_expansion_performed"] is False
    assert "cluster-a" not in pooled["publishability_candidate_pool"]["candidate_order"]
    assert "cluster-c" not in pooled["publishability_candidate_pool"]["candidate_order"]


def test_selection_return_file_is_self_replayable_and_opportunity_bound(tmp_path: Path):
    import json

    supervisor = _supervisor(tmp_path, lambda **_kwargs: {})
    probe = supervisor.prepare_native_desktop_scheduled_opportunity(
        automation_id="v1-newsroom-london-1700", now=NOW
    )
    artifact = supervisor._load_selection_artifact(
        task_id="v1-newsroom-london-1700",
        session="london_1700_bangkok",
        opportunity_id=probe["canonical_opportunity_id"],
    )
    selection = supervisor._validate_selection_return(_selection_from_probe(probe), artifact)
    path = supervisor._persist_selection_return(
        opportunity_id=probe["canonical_opportunity_id"], selection=selection
    )
    persisted = json.loads(path.read_text(encoding="utf-8"))
    assert persisted["canonical_opportunity_id"] == probe["canonical_opportunity_id"]
    assert supervisor._validate_selection_return(persisted, artifact) == selection


def test_complete_phase_reuses_narrow_assignment_and_drops_old_semantic_checkpoints(tmp_path: Path):
    cycle_calls = []
    supervisor = _supervisor(
        tmp_path,
        lambda **kwargs: cycle_calls.append(kwargs)
        or {"classification": "PASS_PUBLICATION_PLAN_READY"},
    )
    state = _pool_valid_prepared_state()
    artifact = supervisor._build_selection_artifact(
        task_id="v1-newsroom-london-1700",
        session="london_1700_bangkok",
        moment=NOW,
        window=WINDOW,
        prepared_state=state,
    )
    request = artifact["coordinator_request"]
    selection = supervisor._validate_selection_return(
        {
            "schema_version": SELECTION_RETURN_SCHEMA_VERSION,
            "canonical_opportunity_id": WINDOW["window_id"],
            "selection_request_logical_hash": request["selection_request_logical_hash"],
            "selected_cluster_id": "cluster-b",
            "article_mode": "STANDARD_NEWS_ANALYSIS",
            "selection_rationale": "B is useful.",
            "fallback_candidates": [],
            "model": COORDINATOR_MODEL,
            "reasoning_effort": "HIGH",
            "public_write_attempted": False,
        },
        artifact,
    )
    binding = supervisor._selected_assignment_binding(artifact=artifact, selection=selection)
    token = supervisor._native_selection_binding.set({**binding, "phase": "COMPLETE"})
    try:
        result = supervisor._native_llm_first_newsroom_cycle(
            run_id="resume",
            output_dir=tmp_path,
            cutoff_utc="2026-08-26T11:00:00Z",
            rolling_input=binding["rolling_input_override"],
            prepared_candidate_state={"must": "drop"},
            leaf_checkpoints={"old": {"must": "drop"}},
            global_checkpoint={"old": "must_drop"},
            story_type_by_cluster={"wrong": "value"},
            publication_enabled=False,
        )
    finally:
        supervisor._native_selection_binding.reset(token)
    assert result["classification"] == "PASS_PUBLICATION_PLAN_READY"
    call = cycle_calls[0]
    assert call["prepared_candidate_state"] is None
    assert call["rolling_input"]["unique_headline_ids"] == ["headline-b"]
    assert call["assignment_override"]["selected_cluster_ids"] == ["cluster-b"]
    assert call["leaf_checkpoints"] == {}
    assert call["global_checkpoint"] is None
    assert call["story_type_by_cluster"] == {"cluster-b": "company_sector_event"}
    assert result["native_llm_first_resume_binding"]["rolling_input_canonical_hash"] == call[
        "rolling_input"
    ]["canonical_input_hash"]


def test_native_pending_handoff_uses_assignment_resume_not_probe_semantic_checkpoint(
    monkeypatch, tmp_path: Path
):
    import json
    import live_contentops.native_desktop_production_handoff_v1 as handoff

    state = _pool_valid_prepared_state()
    supervisor = _supervisor(tmp_path, lambda **_kwargs: {})
    artifact = supervisor._build_selection_artifact(
        task_id="v1-newsroom-london-1700",
        session="london_1700_bangkok",
        moment=NOW,
        window=WINDOW,
        prepared_state=state,
    )
    request = artifact["coordinator_request"]
    selection = supervisor._validate_selection_return(
        {
            "schema_version": SELECTION_RETURN_SCHEMA_VERSION,
            "canonical_opportunity_id": WINDOW["window_id"],
            "selection_request_logical_hash": request["selection_request_logical_hash"],
            "selected_cluster_id": "cluster-b",
            "article_mode": "BREAKING_BRIEF",
            "selection_rationale": "B is useful.",
            "fallback_candidates": [],
            "model": COORDINATOR_MODEL,
            "reasoning_effort": "HIGH",
            "public_write_attempted": False,
        },
        artifact,
    )
    binding = supervisor._selected_assignment_binding(artifact=artifact, selection=selection)
    attempt = tmp_path / "attempt"
    attempt.mkdir(parents=True)
    (attempt / "rolling_x_newsroom_cycle_evidence_v1.json").write_text("{}\n", encoding="utf-8")
    (attempt / "rolling_x_intake_v1.json").write_text(
        json.dumps(binding["rolling_input_override"]), encoding="utf-8"
    )
    (attempt / "rolling_x_ranked_viability_v1.json").write_text("{}\n", encoding="utf-8")

    viability = {
        "status": "SUCCESS",
        "decision": "SELECT_STORY",
        "selected_cluster_id": "cluster-b",
        "selected_headline_ids": ["headline-b"],
        "selected_evidence": {},
        "viability_logical_hash": "fixture",
    }
    monkeypatch.setattr(handoff, "validated_viability_checkpoint", lambda _value: viability)
    monkeypatch.setattr(
        handoff,
        "validate_worker_request_binding",
        lambda request, **_kwargs: dict(request),
    )
    monkeypatch.setattr(
        handoff,
        "persist_handoff_checkpoint",
        lambda _path, value: {**dict(value), "handoff_logical_hash": "persisted"},
    )
    monkeypatch.setattr(
        handoff,
        "semantic_resume_bindings_from_probe",
        lambda _probe: (_ for _ in ()).throw(AssertionError("legacy semantic extractor called")),
    )
    governed_hash = "a" * 64
    result = supervisor._persist_native_desktop_pending_handoff(
        window=WINDOW,
        attempt_number=1,
        attempt_run_id=WINDOW["window_id"],
        attempt_output_dir=attempt,
        attempt_result={
            "exact_next_blocker": "EDITORIAL_WORKER_UNAVAILABLE_OR_INVALID",
            "editorial_worker_routing": {
                "decision": handoff.WORKER_DECISION,
                "governed_input_hash": governed_hash,
                "worker_request": {"governed_input_hash": governed_hash},
            },
            "native_llm_first_resume_binding": binding["resume_binding"],
            "public_write_performed": False,
            "unknown_write_detected": False,
        },
        prior_attempt_results=[],
        qualified_records=[],
        work_budget=1,
    )
    assert result["semantic_resume_bindings"]["semantic_resume_mode"] == (
        "NATIVE_LLM_FIRST_ASSIGNMENT_OVERRIDE"
    )
    assert result["semantic_resume_bindings"]["leaf_checkpoints"] == {}
    assert result["semantic_resume_bindings"]["global_checkpoint"] == {}
    assert result["native_llm_first_resume_binding"]["selected_cluster_ids"] == ["cluster-b"]
'''
TEST_PATH.write_text(tests, encoding="utf-8")

print("PR30 host static correction applied deterministically")
