"""Unit tests for the Operator Review Lifecycle Read Model.

Part of TASK_CONTENTOPS_0175BE_CONTRACT_CHAIN_LIFECYCLE_SPINE_AND_OPERATOR_REVIEW_READ_MODEL_PRECHECK_V0.
"""
from __future__ import annotations

from live_contentops.content_lifecycle_engine import (
    build_lifecycle_read_model,
    list_lifecycle_stages,
)


def test_build_read_model_default():
    read_model = build_lifecycle_read_model()
    assert len(read_model) == 16
    for idx, stage_dict in enumerate(read_model):
        assert isinstance(stage_dict, dict)
        assert stage_dict["stage_order"] == idx + 1
        assert "stage_id" in stage_dict
        assert "stage_name" in stage_dict
        assert "lifecycle_phase" in stage_dict
        assert "state" in stage_dict
        # Ensure dict conversions are clean
        assert isinstance(stage_dict["upstream_stage_ids"], list)
        assert isinstance(stage_dict["downstream_stage_ids"], list)


def test_build_read_model_custom_stages():
    stages = list_lifecycle_stages()
    # reverse the stages list to see if build_lifecycle_read_model sorts them by order
    reversed_stages = list(reversed(stages))
    read_model = build_lifecycle_read_model(reversed_stages)
    assert len(read_model) == 16
    for idx, stage_dict in enumerate(read_model):
        assert stage_dict["stage_order"] == idx + 1  # Verify sorting by order is restored
