from __future__ import annotations

from datetime import datetime, timezone
import importlib
from pathlib import Path

import pytest

from live_contentops.daily_app_supervisor_v1 import (
    ContentOpsDailyAppSupervisor,
    SCHEDULED_EDITORIAL_OWNER_NATIVE_DESKTOP,
)
from live_contentops.native_desktop_production_handoff_v1 import (
    BoundNativeDesktopWorkerReturnBuilder,
    WORKER_DECISION,
    load_handoff_checkpoint,
    logical_hash,
    semantic_resume_bindings_from_probe,
    write_json,
)


NOW = datetime(2026, 8, 24, 14, 5, tzinfo=timezone.utc)
AUTOMATION_ID = "v1-newsroom-new-york-2100"


def _review_receipt(decision: str = "PASS"):
    from live_contentops.tier1_editorial_quality_v1 import LLM_REVIEW_CHECKS

    checks = {name: True for name in LLM_REVIEW_CHECKS}
    issues = []
    if decision == "NEEDS_REVISION":
        checks["material_claims_supported"] = False
        issues = [
            {
                "code": "material_claims_supported",
                "evidence": "Controlled revision fixture.",
            }
        ]
    return {
        "status": "SUCCESS",
        "decision": decision,
        "mode": "straight_news",
        "checks": checks,
        "prompt_sha256": "d" * 64,
        "issues": issues,
        "summary": "Controlled HIGH coordinator review.",
        "publication_authority": False,
    }


def _evidence(cluster_id: str):
    return {
        "evidence_documents": [
            {
                "evidence_id": f"evidence-{cluster_id}",
                "source_id": f"source-{cluster_id}",
                "url": f"https://example.com/official/{cluster_id}",
            }
        ]
    }


def _worker_route(cluster_id: str = "cluster-1"):
    bounded_context = {
        "accepted_evidence_packet": _evidence(cluster_id),
        "exact_source_handles": [f"source-{cluster_id}"],
    }
    governed_hash = logical_hash(bounded_context)
    request = {
        "schema_version": "contentops.editorial_worker_request.v1",
        "model": "gpt-5.6-sol",
        "reasoning_effort": "xhigh",
        "fresh": True,
        "isolated": True,
        "resume_existing": False,
        "governed_input_hash": governed_hash,
        "bounded_governed_context": bounded_context,
    }
    return {
        "decision": WORKER_DECISION,
        "governed_input_hash": governed_hash,
        "worker_request": request,
    }


def _probe(route=None, cluster_id: str = "cluster-1"):
    route = route or _worker_route(cluster_id=cluster_id)
    global_input = {
        "cutoff_time_utc": "2026-08-24T15:00:00Z",
        "leaf_cluster_summaries": [{"id": cluster_id}],
    }
    global_attempt = {
        "disposition": "accepted",
        "prompt_template": "global-template",
        "prompt_version": "v1",
        "governed_input_hash": "b" * 64,
        "gateway": "controlled-test",
        "requested_model": "gpt-5.6-sol",
        "resolved_model": "gpt-5.6-sol",
        "provider_invocation_id": "provider-global-1",
        "model_identity_provider_verified": True,
    }
    leaf_summary = {
        "role_task_id": "rolling_x_newsroom_leaf_scan",
        "work_item_id": "partition-1",
        "terminal_disposition": "ACCEPTED",
    }
    global_summary = {
        "role_task_id": "rolling_x_newsroom_global_editor",
        "work_item_id": "global-1",
        "logical_invocation_id": "global-invocation-1",
        "terminal_disposition": "ACCEPTED",
        "selected_model": "gpt-5.6-sol",
        "attempts": [global_attempt],
    }
    return {
        "schema_version": "contentops.rolling_x_newsroom_cycle.v1",
        "run_id": "controlled-probe",
        "classification": "NO_PUBLICATION",
        "exact_next_blocker": "EDITORIAL_WORKER_UNAVAILABLE_OR_INVALID",
        "assignment": {
            "input_binding": {"canonical_input_hash": "c" * 64},
            "compact_global_editor_input": global_input,
            "leaf_partitions": [
                {
                    "partition_id": "partition-1",
                    "partition_index": 0,
                    "headline_ids": ["headline-1"],
                }
            ],
            "leaf_clusters": [
                {
                    "id": cluster_id,
                    "partition_id": "partition-1",
                    "headline_ids": ["headline-1"],
                }
            ],
            "router_calls": [leaf_summary],
            "router_summary": global_summary,
            "decision": "SELECT_STORY",
            "selection_rationale": "controlled",
            "selected_cluster_id": cluster_id,
            "selected_headline_ids": ["headline-1"],
            "ranked_clusters": [{"id": cluster_id}],
        },
        "story_routing": {"story_type_by_cluster": {cluster_id: "NEWS"}},
        "editorial_worker_routing": route,
        "public_write_performed": False,
        "unknown_write_detected": False,
    }


def _viability(cluster_id: str = "cluster-1"):
    value = {
        "schema_version": "contentops.rolling_x_ranked_viability.v1",
        "status": "SUCCESS",
        "decision": "SELECT_STORY",
        "selected_rank": 1,
        "selected_cluster_id": cluster_id,
        "selected_headline_ids": ["headline-1"],
        "selected_evidence": _evidence(cluster_id),
    }
    return {**value, "viability_logical_hash": logical_hash(value)}


class ControlledSplitCycle:
    def __init__(self, complete_behavior: str = "PASS"):
        self.calls = []
        self.complete_behavior = complete_behavior

    def __call__(self, **kwargs):
        self.calls.append(dict(kwargs))
        output_dir = Path(kwargs["output_dir"])
        output_dir.mkdir(parents=True, exist_ok=True)
        if kwargs.get("native_desktop_prepare") is True:
            if self.complete_behavior == "PROVIDER_EXHAUSTED":
                value = {
                    "schema_version": "contentops.rolling_x_newsroom_cycle.v1",
                    "run_id": kwargs["run_id"],
                    "classification": "BLOCKED",
                    "exact_next_blocker": "ROLLING_X_LEAF_ASSIGNMENT_BLOCKED",
                    "public_write_performed": False,
                    "unknown_write_detected": False,
                    "editorial_worker_count_requested": 0,
                }
                write_json(
                    output_dir / "rolling_x_newsroom_cycle_evidence_v1.json",
                    value,
                )
                return value
            value = _probe()
            value["run_id"] = kwargs["run_id"]
            if self.complete_behavior == "PENDING_PUBLIC_WRITE":
                value["public_write_performed"] = True
            if self.complete_behavior == "PENDING_UNKNOWN_WRITE":
                value["unknown_write_detected"] = True
            write_json(output_dir / "rolling_x_intake_v1.json", {"headlines": []})
            write_json(output_dir / "rolling_x_ranked_viability_v1.json", _viability())
            write_json(output_dir / "rolling_x_newsroom_cycle_evidence_v1.json", value)
            return value
        assert kwargs.get("article_builder") is not None
        assert kwargs.get("editorial_reviewer") is not None
        assert kwargs.get("rolling_input") == {"headlines": []}
        assert kwargs.get("leaf_checkpoints")
        assert kwargs.get("global_checkpoint")
        assert kwargs.get("story_type_by_cluster") == {"cluster-1": "NEWS"}
        if self.complete_behavior == "NEXT_CANDIDATE":
            route = _worker_route(cluster_id="cluster-2")
            value = _probe(route=route, cluster_id="cluster-2")
            value.update(
                {
                    "run_id": kwargs["run_id"],
                    "exact_next_blocker": "NEXT_NATIVE_XHIGH_WORKER_REQUIRED",
                }
            )
            write_json(output_dir / "rolling_x_intake_v1.json", {"headlines": []})
            write_json(
                output_dir / "rolling_x_ranked_viability_v1.json",
                _viability(cluster_id="cluster-2"),
            )
            write_json(output_dir / "rolling_x_newsroom_cycle_evidence_v1.json", value)
            return value
        if self.complete_behavior == "SAME_WORKER_REVISION":
            value = _probe()
            initial_request = _worker_route()["worker_request"]
            revision_request = {
                "model": "gpt-5.6-sol",
                "reasoning_effort": "xhigh",
                "resume_same_isolated_worker": True,
                "fresh_worker_creation": False,
                "governed_input_hash": _worker_route()["governed_input_hash"],
                "bounded_governed_context": initial_request[
                    "bounded_governed_context"
                ],
            }
            revision_contract = {
                "schema_version": (
                    "contentops.same_xhigh_worker_revision_contract.v1"
                ),
                "decision": "SAME_XHIGH_WORKER_REVISION_REQUIRED",
                "governed_input_hash": _worker_route()["governed_input_hash"],
                "prior_worker_return_hash": "f" * 64,
                "prior_bounded_revision_count": 0,
                "required_bounded_revision_count": 1,
                "maximum_bounded_revision_count": 1,
                "same_worker_required": True,
                "fresh_replacement_worker_forbidden": True,
                "router_final_writer_forbidden": True,
                "worker_request": revision_request,
                "immutable_evidence_identity": {},
                "deterministic_blockers": {},
                "semantic_review": {},
                "public_write_authority": False,
                "publication_authority": False,
            }
            revision_contract["revision_contract_hash"] = logical_hash(
                revision_contract
            )
            value.update(
                {
                    "run_id": kwargs["run_id"],
                    "exact_next_blocker": "SAME_XHIGH_WORKER_REVISION_REQUIRED",
                    "same_xhigh_worker_revision_contract": revision_contract,
                }
            )
            write_json(output_dir / "rolling_x_intake_v1.json", {"headlines": []})
            write_json(output_dir / "rolling_x_ranked_viability_v1.json", _viability())
            write_json(output_dir / "rolling_x_newsroom_cycle_evidence_v1.json", value)
            return value
        value = {
            "run_id": kwargs["run_id"],
            "classification": "PASS_PUBLICATION_PLAN_READY",
            # Successful canonical receipts retain the worker route as audit evidence. This
            # must not be mistaken for a new pending-worker decision during COMPLETE.
            "editorial_worker_routing": _worker_route(),
            "public_write_performed": False,
            "unknown_write_detected": False,
        }
        write_json(output_dir / "rolling_x_newsroom_cycle_evidence_v1.json", value)
        return value


def _supervisor(tmp_path: Path, cycle):
    return ContentOpsDailyAppSupervisor(
        store_path=tmp_path / "store.sqlite3",
        output_root=tmp_path / "out",
        operating_mode="SHADOW_ONLY",
        clock=lambda: NOW,
        newsroom_cycle=cycle,
        scheduled_editorial_owner=SCHEDULED_EDITORIAL_OWNER_NATIVE_DESKTOP,
    )


def test_semantic_resume_bindings_are_exact_and_hash_bound():
    bindings = semantic_resume_bindings_from_probe(_probe())

    assert bindings["canonical_input_hash"] == "c" * 64
    assert list(bindings["leaf_checkpoints"]) == ["partition-1"]
    assert bindings["global_checkpoint"]["terminal_disposition"] == "ACCEPTED"
    assert bindings["story_type_by_cluster"] == {"cluster-1": "NEWS"}
    assert len(bindings["semantic_resume_logical_hash"]) == 64


def test_public_canonical_facade_exposes_prepare_probe_only_with_explicit_flag(
    tmp_path, monkeypatch
):
    public_module = importlib.import_module(
        "live_contentops.eight_platform_substack_first_pipeline_v1"
    )
    calls = []

    def controlled_execute(name, **kwargs):
        calls.append((name, dict(kwargs)))
        return {
            "classification": "NO_PUBLICATION",
            "editorial_worker_routing": _worker_route(),
            "public_write_performed": False,
        }

    monkeypatch.setattr(public_module, "_execute", controlled_execute)
    result = public_module.run_rolling_x_newsroom_cycle(
        run_id="prepare-probe",
        output_dir=tmp_path,
        cutoff_utc="2026-08-24T15:00:00Z",
        publication_enabled=True,
        native_desktop_prepare=True,
    )

    assert result["editorial_execution_route"] == "DESKTOP_PRIMARY"
    assert result["desktop_primary_routine_authority"] is True
    assert calls[0][1]["article_builder"] is None


def test_bound_worker_return_never_crosses_candidate_hashes():
    from live_contentops.rolling_x_grounded_article_media_builder_v1 import (
        GroundedArticleBuilderError,
    )

    first_route = _worker_route()
    builder = BoundNativeDesktopWorkerReturnBuilder(
        worker_return={"governed_input_hash": first_route["governed_input_hash"]},
        expected_governed_input_hash=first_route["governed_input_hash"],
        viability=_viability(),
    )
    with pytest.raises(
        GroundedArticleBuilderError,
        match="NEXT_NATIVE_XHIGH_WORKER_REQUIRED",
    ):
        builder(
            {
                "editorial_worker_request": _worker_route("cluster-2")[
                    "worker_request"
                ]
            }
        )


def test_bound_worker_return_hash_mismatch_fails_closed():
    from live_contentops.rolling_x_grounded_article_media_builder_v1 import (
        GroundedArticleBuilderError,
    )

    route = _worker_route()
    builder = BoundNativeDesktopWorkerReturnBuilder(
        worker_return={"governed_input_hash": "0" * 64},
        expected_governed_input_hash=route["governed_input_hash"],
        viability=_viability(),
    )
    with pytest.raises(
        GroundedArticleBuilderError,
        match="EDITORIAL_WORKER_UNAVAILABLE_OR_INVALID",
    ):
        builder({"editorial_worker_request": route["worker_request"]})


def test_prepare_is_durable_resumable_duplicate_safe_and_releases_lease(tmp_path):
    cycle = ControlledSplitCycle()
    supervisor = _supervisor(tmp_path, cycle)

    first = supervisor.prepare_native_desktop_scheduled_opportunity(
        automation_id=AUTOMATION_ID,
        now=NOW,
    )
    duplicate = supervisor.prepare_native_desktop_scheduled_opportunity(
        automation_id=AUTOMATION_ID,
        now=NOW,
    )

    assert first["classification"] == "XHIGH_REQUIRED"
    assert first["exact_next_blocker"] == WORKER_DECISION
    assert first["governed_input_hash"] == _worker_route()["governed_input_hash"]
    assert first["canonical_opportunity_id"] == first["runtime_run_id"]
    assert first["terminal_state"] == "EVIDENCE_PENDING"
    assert first["opportunity_resumable"] is True
    assert first["public_write_authority"] == "ZERO"
    assert duplicate["governed_input_hash"] == first["governed_input_hash"]
    assert len(cycle.calls) == 1
    assert supervisor._window_state(first["canonical_opportunity_id"]) == "EVIDENCE_PENDING"
    checkpoint = load_handoff_checkpoint(first["handoff_checkpoint_path"])
    assert checkpoint["canonical_opportunity_id"] == first["canonical_opportunity_id"]
    assert checkpoint["semantic_resume_bindings"]["leaf_checkpoints"]
    with supervisor._store.get_read_only_connection() as connection:
        active = connection.execute(
            "SELECT COUNT(*) FROM leases WHERE lease_key=? AND status='ACTIVE'",
            (first["canonical_opportunity_id"],),
        ).fetchone()[0]
    assert active == 0


@pytest.mark.parametrize(
    ("behavior", "expected_blocker", "write_key"),
    [
        (
            "PENDING_PUBLIC_WRITE",
            "NATIVE_DESKTOP_ZERO_WRITE_CONTRACT_VIOLATION",
            "public_write_performed",
        ),
        ("PENDING_UNKNOWN_WRITE", "UNKNOWN_WRITE", "unknown_write_detected"),
    ],
)
def test_prepare_never_masks_write_truth_behind_pending_handoff(
    tmp_path, behavior, expected_blocker, write_key
):
    cycle = ControlledSplitCycle(complete_behavior=behavior)
    supervisor = _supervisor(tmp_path, cycle)

    result = supervisor.prepare_native_desktop_scheduled_opportunity(
        automation_id=AUTOMATION_ID, now=NOW
    )

    assert result["classification"] == "BLOCKED"
    assert result["exact_next_blocker"] == expected_blocker
    assert result[write_key] is True
    assert result["retry_authorized"] is False
    assert result.get("opportunity_resumable") is not True
    assert not (tmp_path / "out" / result["canonical_opportunity_id"] / (
        "native_desktop_editorial_handoff_v1.json"
    )).exists()


def test_provider_exhaustion_before_article_boundary_terminalizes_without_xhigh(
    tmp_path,
):
    cycle = ControlledSplitCycle(complete_behavior="PROVIDER_EXHAUSTED")
    supervisor = _supervisor(tmp_path, cycle)

    result = supervisor.prepare_native_desktop_scheduled_opportunity(
        automation_id=AUTOMATION_ID, now=NOW
    )

    assert result["classification"] == "BLOCKED"
    assert result["terminal_state"] == "REJECTED"
    assert result.get("editorial_worker_request") is None
    assert len(cycle.calls) == 1
    assert not (tmp_path / "out" / result["canonical_opportunity_id"] / (
        "native_desktop_editorial_handoff_v1.json"
    )).exists()


def test_complete_reuses_same_opportunity_and_semantic_checkpoints(
    tmp_path, monkeypatch
):
    from live_contentops import newsroom_production_day_v1 as production

    cycle = ControlledSplitCycle()
    supervisor = _supervisor(tmp_path, cycle)
    monkeypatch.setattr(production, "bounded_deficit_work_needed", lambda **_kwargs: 1)
    prepared = supervisor.prepare_native_desktop_scheduled_opportunity(
        automation_id=AUTOMATION_ID,
        now=NOW,
    )
    monkeypatch.setattr(
        production,
        "qualify_zero_write_article",
        lambda **_kwargs: {"qualified": True, "article_identity": "article-1"},
    )
    monkeypatch.setattr(production, "persist_qualified_article_record", lambda *_args: None)
    monkeypatch.setattr(
        production, "qualified_records_as_published_memory", lambda *_args, **_kwargs: []
    )
    result = supervisor.complete_native_desktop_scheduled_opportunity(
        automation_id=AUTOMATION_ID,
        canonical_opportunity_id=prepared["canonical_opportunity_id"],
        worker_return={
            "governed_input_hash": prepared["governed_input_hash"],
            "article": {},
        },
        coordinator_review_receipt=_review_receipt(),
        now=NOW,
    )

    assert result["canonical_opportunity_id"] == prepared["canonical_opportunity_id"]
    assert result["runtime_run_id"] == prepared["runtime_run_id"]
    assert result["classification"] == "PASS_PUBLICATION_PLAN_READY"
    assert result["terminal_state"] == "EVIDENCE_READY"
    assert result["public_write_performed"] is False
    assert result["unknown_write_detected"] is False
    assert len(cycle.calls) == 2
    assert cycle.calls[1]["run_id"] == cycle.calls[0]["run_id"]
    assert cycle.calls[1]["output_dir"] != cycle.calls[0]["output_dir"]

    duplicate = supervisor.complete_native_desktop_scheduled_opportunity(
        automation_id=AUTOMATION_ID,
        canonical_opportunity_id=prepared["canonical_opportunity_id"],
        worker_return={
            "governed_input_hash": prepared["governed_input_hash"],
            "article": {},
        },
        coordinator_review_receipt=_review_receipt(),
        now=NOW,
    )
    assert duplicate["executed"] is False
    assert duplicate["reason"] == "already_executed_terminal_state"
    assert len(cycle.calls) == 2


def test_complete_can_return_next_candidate_worker_request_in_same_opportunity(
    tmp_path, monkeypatch
):
    from live_contentops import newsroom_production_day_v1 as production

    monkeypatch.setattr(production, "bounded_deficit_work_needed", lambda **_kwargs: 1)
    cycle = ControlledSplitCycle(complete_behavior="NEXT_CANDIDATE")
    supervisor = _supervisor(tmp_path, cycle)
    prepared = supervisor.prepare_native_desktop_scheduled_opportunity(
        automation_id=AUTOMATION_ID, now=NOW
    )
    result = supervisor.complete_native_desktop_scheduled_opportunity(
        automation_id=AUTOMATION_ID,
        canonical_opportunity_id=prepared["canonical_opportunity_id"],
        worker_return={
            "governed_input_hash": prepared["governed_input_hash"],
            "article": {},
        },
        coordinator_review_receipt=_review_receipt(),
        now=NOW,
    )

    assert result["classification"] == "XHIGH_REQUIRED_FOR_CANDIDATE_CONTINUATION"
    assert result["exact_next_blocker"] == "NEXT_NATIVE_XHIGH_WORKER_REQUIRED"
    assert result["governed_input_hash"] == _worker_route("cluster-2")[
        "governed_input_hash"
    ]
    assert result["resume_sequence"] == 2
    assert result["canonical_opportunity_id"] == prepared["canonical_opportunity_id"]
    assert supervisor._window_state(prepared["canonical_opportunity_id"]) == "EVIDENCE_PENDING"


def test_complete_can_pause_for_one_same_worker_revision(tmp_path, monkeypatch):
    from live_contentops import newsroom_production_day_v1 as production

    monkeypatch.setattr(production, "bounded_deficit_work_needed", lambda **_kwargs: 1)
    cycle = ControlledSplitCycle(complete_behavior="SAME_WORKER_REVISION")
    supervisor = _supervisor(tmp_path, cycle)
    prepared = supervisor.prepare_native_desktop_scheduled_opportunity(
        automation_id=AUTOMATION_ID, now=NOW
    )
    result = supervisor.complete_native_desktop_scheduled_opportunity(
        automation_id=AUTOMATION_ID,
        canonical_opportunity_id=prepared["canonical_opportunity_id"],
        worker_return={
            "governed_input_hash": prepared["governed_input_hash"],
            "article": {},
        },
        coordinator_review_receipt=_review_receipt("NEEDS_REVISION"),
        now=NOW,
    )

    assert result["classification"] == "SAME_XHIGH_WORKER_REVISION_REQUIRED"
    assert result["exact_next_blocker"] == "SAME_XHIGH_WORKER_REVISION_REQUIRED"
    assert result["governed_input_hash"] == prepared["governed_input_hash"]
    assert result["resume_sequence"] == 2
    assert supervisor._window_state(prepared["canonical_opportunity_id"]) == "EVIDENCE_PENDING"
