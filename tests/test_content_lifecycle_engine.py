"""Unit tests for the Content Lifecycle Engine.

Part of TASK_CONTENTOPS_0175BE_CONTRACT_CHAIN_LIFECYCLE_SPINE_AND_OPERATOR_REVIEW_READ_MODEL_PRECHECK_V0.
"""
from __future__ import annotations

from pathlib import Path
import pytest
from live_contentops.content_lifecycle_engine import (
    list_lifecycle_stages,
    build_lifecycle_read_model,
    build_operator_review_summary,
    validate_lifecycle_invariants,
    build_contract_packet,
    write_contract_artifacts,
    LifecycleStage,
    TASK_LABEL,
    MATRIX_VERSION,
    SOURCE_BASELINE_COMMIT,
)


def test_canonical_stage_count():
    stages = list_lifecycle_stages()
    assert len(stages) == 16
    # Verify exact required stages are present
    stage_ids = [s.stage_id for s in stages]
    expected_ids = [
        "artifact_or_brief_intake",
        "content_intent",
        "draft_or_render",
        "operator_review_bundle",
        "approval_gate",
        "manual_export",
        "operator_audit_summary",
        "manual_publish_record_precheck",
        "manual_publish_record_stub",
        "metrics_precheck",
        "metrics_record_stub",
        "performance_audit_precheck",
        "performance_summary_stub",
        "content_feedback_precheck",
        "content_feedback_stub",
        "operator_review_brief_precheck",
    ]
    assert stage_ids == expected_ids


def test_stage_field_types_and_invariants():
    stages = list_lifecycle_stages()
    for s in stages:
        assert isinstance(s.stage_id, str)
        assert isinstance(s.stage_order, int)
        assert isinstance(s.stage_name, str)
        assert isinstance(s.lifecycle_phase, str)
        assert isinstance(s.source_task_label, str)
        assert isinstance(s.source_module, str)
        assert isinstance(s.source_packet_path, str)
        assert isinstance(s.upstream_stage_ids, list)
        assert isinstance(s.downstream_stage_ids, list)
        assert isinstance(s.platform_scope, str)
        assert isinstance(s.evidence_refs, list)
        assert isinstance(s.blocker_codes, list)
        assert s.required_future_gate is None or isinstance(s.required_future_gate, str)
        assert s.state in ("COMPLETED", "PENDING", "BLOCKED")
        assert isinstance(s.operator_action_required, bool)


def test_validate_invariants_pass():
    stages = list_lifecycle_stages()
    passed, errors = validate_lifecycle_invariants(stages, raise_exception=False)
    assert passed
    assert not errors


def test_validate_invariants_duplicate_order():
    stages = list_lifecycle_stages()
    # Modify order of one stage to duplicate another
    modified_stages = list(stages)
    s = modified_stages[1]
    modified_stages[1] = LifecycleStage(
        stage_id=s.stage_id,
        stage_order=stages[0].stage_order,  # duplicate
        stage_name=s.stage_name,
        lifecycle_phase=s.lifecycle_phase,
        source_task_label=s.source_task_label,
        source_module=s.source_module,
        source_packet_path=s.source_packet_path,
        upstream_stage_ids=s.upstream_stage_ids,
        downstream_stage_ids=s.downstream_stage_ids,
        platform_scope=s.platform_scope,
        evidence_refs=s.evidence_refs,
        blocker_codes=s.blocker_codes,
        required_future_gate=s.required_future_gate,
        state=s.state,
        operator_action_required=s.operator_action_required,
    )
    passed, errors = validate_lifecycle_invariants(modified_stages, raise_exception=False)
    assert not passed
    assert any("Duplicate stage_order found" in e for e in errors)


def test_validate_invariants_missing_upstream_ref():
    stages = list_lifecycle_stages()
    modified_stages = list(stages)
    s = modified_stages[1]
    modified_stages[1] = LifecycleStage(
        stage_id=s.stage_id,
        stage_order=s.stage_order,
        stage_name=s.stage_name,
        lifecycle_phase=s.lifecycle_phase,
        source_task_label=s.source_task_label,
        source_module=s.source_module,
        source_packet_path=s.source_packet_path,
        upstream_stage_ids=["nonexistent_upstream"],
        downstream_stage_ids=s.downstream_stage_ids,
        platform_scope=s.platform_scope,
        evidence_refs=s.evidence_refs,
        blocker_codes=s.blocker_codes,
        required_future_gate=s.required_future_gate,
        state=s.state,
        operator_action_required=s.operator_action_required,
    )
    passed, errors = validate_lifecycle_invariants(modified_stages, raise_exception=False)
    assert not passed
    assert any("references missing upstream ID 'nonexistent_upstream'" in e for e in errors)


def test_validate_invariants_missing_downstream_ref():
    stages = list_lifecycle_stages()
    modified_stages = list(stages)
    s = modified_stages[1]
    modified_stages[1] = LifecycleStage(
        stage_id=s.stage_id,
        stage_order=s.stage_order,
        stage_name=s.stage_name,
        lifecycle_phase=s.lifecycle_phase,
        source_task_label=s.source_task_label,
        source_module=s.source_module,
        source_packet_path=s.source_packet_path,
        upstream_stage_ids=s.upstream_stage_ids,
        downstream_stage_ids=["nonexistent_downstream"],
        platform_scope=s.platform_scope,
        evidence_refs=s.evidence_refs,
        blocker_codes=s.blocker_codes,
        required_future_gate=s.required_future_gate,
        state=s.state,
        operator_action_required=s.operator_action_required,
    )
    passed, errors = validate_lifecycle_invariants(modified_stages, raise_exception=False)
    assert not passed
    assert any("references missing downstream ID 'nonexistent_downstream'" in e for e in errors)


@pytest.mark.parametrize("safety_field", [
    "public_postable",
    "dispatch_ready",
    "live_api_called",
    "provider_api_called",
    "env_read",
    "credential_hydrated",
    "scheduler_enabled",
    "scraping_performed",
    "autonomous_reply_or_dm_enabled",
    "dqr_cleared_by_contentops",
    "readiness_cleared_by_contentops",
    "current_truth_promoted",
])
def test_validate_invariants_safety_violations(safety_field):
    stages = list_lifecycle_stages()
    modified_stages = list(stages)
    s = modified_stages[0]
    kwargs = {safety_field: True}
    modified_stages[0] = LifecycleStage(
        stage_id=s.stage_id,
        stage_order=s.stage_order,
        stage_name=s.stage_name,
        lifecycle_phase=s.lifecycle_phase,
        source_task_label=s.source_task_label,
        source_module=s.source_module,
        source_packet_path=s.source_packet_path,
        upstream_stage_ids=s.upstream_stage_ids,
        downstream_stage_ids=s.downstream_stage_ids,
        platform_scope=s.platform_scope,
        evidence_refs=s.evidence_refs,
        blocker_codes=s.blocker_codes,
        required_future_gate=s.required_future_gate,
        state=s.state,
        operator_action_required=s.operator_action_required,
        **kwargs
    )
    passed, errors = validate_lifecycle_invariants(modified_stages, raise_exception=False)
    assert not passed
    assert any("safety lock violation flags" in e for e in errors)
    with pytest.raises(ValueError, match="Content lifecycle validation failed"):
        validate_lifecycle_invariants(modified_stages, raise_exception=True)


def test_operator_review_summary_canonical():
    stages = list_lifecycle_stages()
    summary = build_operator_review_summary(stages)
    assert summary.total_stage_count == 16
    # 5 is approval_gate, 6 is manual_export, and all subsequent stages have blocker_codes (12 in total)
    assert summary.blocked_stage_count == 12
    assert summary.dispatch_ready_count == 0
    assert summary.public_postable_count == 0
    assert summary.all_safety_locks_active is True
    # The first stage where state != "COMPLETED" is "operator_review_bundle" (PENDING)
    assert summary.current_lifecycle_position == "operator_review_bundle"
    # The first blocked stage is "approval_gate"
    assert summary.next_blocker == "approval_gate"


def test_build_contract_packet():
    packet = build_contract_packet()
    assert packet["task_label"] == TASK_LABEL
    assert packet["matrix_version"] == MATRIX_VERSION
    assert packet["source_baseline_commit"] == SOURCE_BASELINE_COMMIT
    assert len(packet["stages"]) == 16
    assert isinstance(packet["packet_hash"], str)
    assert packet["packet_hash"] != ""


def test_write_contract_artifacts(tmp_path):
    # Call writing in a temporary path to verify it works without side-effects
    res = write_contract_artifacts(repo_root=tmp_path)
    assert "packet" in res
    assert Path(res["packet_path"]).exists()
    assert Path(res["runbook_path"]).exists()
