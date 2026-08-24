"""Regression coverage for the bounded current-frontier rehearsal handoff."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.run_v1_current_multi_frontier_floor_rehearsal import (
    _StageAEvidenceReuseAcquirer,
    _new_state,
    _sha,
    _stage_a_ready_frontiers,
    _summary,
    _semantic_resume_checkpoints_from_probe,
    _validated_probe_viability_checkpoint,
)


def _accepted_summary(*, role: str, invocation: str, work_item: str) -> dict:
    return {
        "terminal_disposition": "ACCEPTED",
        "logical_invocation_id": invocation,
        "work_item_id": work_item,
        "role_task_id": role,
        "selected_model": "vx/gemini-3.1-pro-preview(high)",
        "model_identity_provider_verifiable": True,
        "attempts": [
            {
                "disposition": "accepted",
                "gateway": "9router",
                "requested_model": "vx/gemini-3.1-pro-preview(high)",
                "resolved_model": "gemini-3.1-pro-preview",
                "provider_invocation_id": "synthetic-provider-id",
                "model_identity_provider_verified": True,
                "prompt_template": (
                    "rolling_x_newsroom_leaf_scan"
                    if role == "rolling_x_newsroom_leaf_scan"
                    else "rolling_x_newsroom_compact_global_editor"
                ),
                "prompt_version": "v7",
                "governed_input_hash": f"governed-{role}",
            }
        ],
    }


def _probe() -> dict:
    leaf = _accepted_summary(
        role="rolling_x_newsroom_leaf_scan",
        invocation="leaf-invocation",
        work_item="partition-1",
    )
    global_summary = _accepted_summary(
        role="rolling_x_newsroom_assignment",
        invocation="global-invocation",
        work_item="global-work-item",
    )
    return {
        "assignment": {
            "input_binding": {"canonical_input_hash": "input-hash"},
            "compact_global_editor_input": {
                "cutoff_time_utc": "2026-08-22T00:00:00Z",
                "leaf_cluster_summaries": [{"id": "leaf-cluster-1"}],
            },
            "leaf_partitions": [
                {
                    "partition_id": "partition-1",
                    "partition_index": 0,
                    "headline_ids": ["headline-1"],
                }
            ],
            "leaf_clusters": [
                {
                    "partition_id": "partition-1",
                    "leaf_cluster_id": "leaf-cluster-1",
                    "member_headline_ids": ["headline-1"],
                }
            ],
            "router_calls": [leaf],
            "router_summary": global_summary,
            "decision": "SELECT_STORY",
            "selection_rationale": "Synthetic no-write checkpoint coverage.",
            "selected_cluster_id": "global-cluster-1",
            "selected_headline_ids": ["headline-1"],
            "ranked_clusters": [],
        },
        "story_routing": {
            "story_type_by_cluster": {"global-cluster-1": "STANDARD_NEWS_ANALYSIS"}
        },
    }


def test_worker_completion_reuses_exact_accepted_probe_checkpoints() -> None:
    leaf_checkpoints, global_checkpoint, story_types = _semantic_resume_checkpoints_from_probe(
        _probe()
    )

    assert set(leaf_checkpoints) == {"partition-1"}
    assert leaf_checkpoints["partition-1"]["router_summary"]["logical_invocation_id"] == (
        "leaf-invocation"
    )
    assert global_checkpoint["global_invocation_id"] == "global-invocation"
    assert global_checkpoint["terminal_disposition"] == "ACCEPTED"
    assert global_checkpoint["accepted_provider_identity"] == {
        "gateway": "9router",
        "requested_model": "vx/gemini-3.1-pro-preview(high)",
        "resolved_model": "gemini-3.1-pro-preview",
        "provider_invocation_id": "synthetic-provider-id",
        "model_identity_provider_verified": True,
    }
    assert story_types == {"global-cluster-1": "STANDARD_NEWS_ANALYSIS"}


def test_worker_completion_refuses_an_unaccepted_or_incomplete_probe() -> None:
    probe = _probe()
    probe["assignment"]["router_summary"]["terminal_disposition"] = "LLM_RETRY_BUDGET_EXHAUSTED"

    with pytest.raises(ValueError, match="probe_semantic_resume_checkpoint_missing_or_unaccepted"):
        _semantic_resume_checkpoints_from_probe(probe)


def test_worker_completion_reuses_only_the_exact_hash_bound_probe_viability() -> None:
    viability = {
        "status": "SUCCESS",
        "decision": "SELECT_STORY",
        "selected_cluster_id": "global-cluster-1",
        "selected_evidence": {"headline_ids": ["headline-1"]},
        "rank_attempts": [],
    }
    viability["viability_logical_hash"] = _sha(viability)

    reused = _validated_probe_viability_checkpoint(viability)

    assert reused == viability
    tampered = {**viability, "selected_cluster_id": "different-cluster"}
    with pytest.raises(ValueError, match="probe_viability_checkpoint_invalid"):
        _validated_probe_viability_checkpoint(tampered)


def test_summary_counts_only_current_input_members_when_durable_memory_is_seeded() -> None:
    state = {
        "full_current_headline_count": 3,
        "current_headline_ids": ["current-1", "current-2", "current-3"],
        "evaluated_headline_ids": ["historical-1", "historical-2", "current-1"],
        "qualified_article_records": [],
        "mvp_canary_artifact_records": [],
        "frontiers": [
            {
                "attempted_headline_ids": ["current-1"],
                "attempted_distinct_candidate_count": 1,
                "exact_headline_identity_coverage": True,
            }
        ],
        "pending_frontier": None,
    }

    summary = _summary(state)

    assert summary["classification"] == "IN_PROGRESS"
    assert summary["bounded_useful_universe_exhausted"] is False
    assert summary["remaining_held_identity_count"] == 2
    assert summary["attempted_headline_identity_count"] == 1
    assert summary["distinct_candidate_count"] == 1
    assert summary["no_repeat_proof"] is True


def test_stage_a_evidence_reuse_requires_exact_request_identity(tmp_path: Path) -> None:
    stage_root = tmp_path / "stage-a"
    cycle_path = stage_root / "frontier_1" / "rolling_x_newsroom_cycle_evidence_v1.json"
    cycle_path.parent.mkdir(parents=True)
    request = {
        "cluster_id": "stage-a-ready",
        "headline_ids": ["headline-ready"],
        "request_logical_hash": "request-hash",
    }
    receipt = {
        "status": "PASS",
        "cluster_id": "stage-a-ready",
        "headline_ids": ["headline-ready"],
        "evidence_documents": [{"document_id": "document-ready"}],
        "blockers": [],
        "publication_authority": False,
    }
    cycle_path.write_text(
        json.dumps(
            {
                "ranked_viability": {
                    "rank_attempts": [
                        {"request": request, "evidence_receipt": receipt}
                    ]
                },
                "source_route_health": {
                    "schema_version": "contentops.source_route_health.v1",
                    "routing_only": True,
                    "hosts": [],
                    "routes": [],
                },
            }
        ),
        encoding="utf-8",
    )
    acquirer = _StageAEvidenceReuseAcquirer(
        stage_a_root=stage_root,
        evaluation_as_of_utc="2026-08-23T23:46:33Z",
    )

    replayed = acquirer(request)
    manifest = acquirer.manifest()

    assert replayed == receipt
    assert manifest["cached_exact_request_count"] == 1
    assert manifest["cached_ready_receipt_count"] == 1
    assert manifest["reuse_hit_count"] == 1
    assert manifest["fallback_call_count"] == 0
    assert manifest[
        "request_identity_requires_cluster_headlines_and_logical_hash"
    ] is True
    assert manifest[
        "cached_model_output_grants_factual_or_publication_authority"
    ] is False


def test_stage_a_evidence_binding_requires_same_frozen_universe(
    tmp_path: Path,
) -> None:
    rolling = {
        "cutoff_time_utc": "2026-08-23T23:46:33Z",
        "headlines": [{"headline_id": "headline-ready"}],
    }
    stage_root = tmp_path / "stage-a"
    stage_root.mkdir()
    stage_input = stage_root / "frozen_current_rolling_input_v1.json"
    stage_input.write_text(json.dumps(rolling), encoding="utf-8")
    frontier = stage_root / "frontier_1"
    frontier.mkdir()
    (frontier / "rolling_x_prepared_candidate_state_v1.json").write_text(
        json.dumps({"prepared_candidate_count": 4}), encoding="utf-8"
    )
    (frontier / "rolling_x_newsroom_cycle_evidence_v1.json").write_text(
        json.dumps(
            {
                "evidence_ready_pool": {
                    "candidates": [
                        {"cluster_id": f"ready-{index}"}
                        for index in range(1, 5)
                    ]
                }
            }
        ),
        encoding="utf-8",
    )
    source_input = tmp_path / "rolling.json"
    source_input.write_text(json.dumps(rolling), encoding="utf-8")

    state = _new_state(
        tmp_path / "proof",
        "unused-glob",
        rolling_input_path=source_input,
        stage_a_evidence_root=stage_root,
    )

    assert state["stage_a_evidence_binding"][
        "stage_a_frozen_input_sha256"
    ] == _sha(rolling)
    assert state["stage_a_evidence_binding"]["ready_frontiers"] == (
        _stage_a_ready_frontiers(stage_root)
    )
    assert state["stage_a_evidence_binding"]["ready_frontier_cursor"] == 0
    different = tmp_path / "different.json"
    different.write_text(
        json.dumps(
            {
                "cutoff_time_utc": "2026-08-23T23:46:33Z",
                "headlines": [{"headline_id": "different"}],
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(
        ValueError, match="stage_a_evidence_rolling_input_identity_mismatch"
    ):
        _new_state(
            tmp_path / "proof-mismatch",
            "unused-glob",
            rolling_input_path=different,
            stage_a_evidence_root=stage_root,
        )
