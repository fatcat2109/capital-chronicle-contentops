"""Regression coverage for the bounded current-frontier rehearsal handoff."""
from __future__ import annotations

import pytest

from scripts.run_v1_current_multi_frontier_floor_rehearsal import (
    _sha,
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
