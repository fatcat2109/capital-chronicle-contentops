"""Unit tests for V5 manual pilot trail reconciliation contract."""
from live_contentops.v5_manual_pilot_trail_reconciliation_contract import (
    build_v5_manual_pilot_trail_reconciliation_packet,
    TASK_LABEL,
    CONTRACT_VERSION,
    SOURCE_MANUAL_EXPORT_PACKET_HASH,
    SOURCE_OPERATOR_REVIEW_PACKET_HASH,
    SOURCE_OPERATOR_REVIEW_QUEUE_ID,
)


def test_packet_builds_deterministically():
    p1 = build_v5_manual_pilot_trail_reconciliation_packet()
    p2 = build_v5_manual_pilot_trail_reconciliation_packet()
    assert p1.packet_hash == p2.packet_hash
    assert p1.reconciliation_id == p2.reconciliation_id
    assert p1.task_label == TASK_LABEL
    assert p1.contract_version == CONTRACT_VERSION


def test_source_references_matched():
    p = build_v5_manual_pilot_trail_reconciliation_packet()
    assert p.source_manual_export_packet_hash == SOURCE_MANUAL_EXPORT_PACKET_HASH
    assert p.source_manual_export_packet_hash == "277fb7d44b247efc6021f038e362256f746cc039"
    assert p.source_operator_review_packet_hash == SOURCE_OPERATOR_REVIEW_PACKET_HASH
    assert p.source_operator_review_packet_hash == "473a376d9ff812ff830391e24d3cd75fd71b4faf576414f8b8a157b2ea9f284c"
    assert p.source_operator_review_queue_id == SOURCE_OPERATOR_REVIEW_QUEUE_ID
    assert p.source_operator_review_queue_id == "v5_operator_review_queue_473a376d9ff812ff830391e2"


def test_lifecycle_steps_are_correct():
    p = build_v5_manual_pilot_trail_reconciliation_packet()
    assert len(p.lifecycle_steps) == 8
    steps = {step.step_id: step for step in p.lifecycle_steps}
    assert "export_packet_prepared" in steps
    assert "operator_review_pending" in steps
    assert "checklist_pending" in steps
    assert "manual_publish_url_empty" in steps
    assert "manual_metrics_empty" in steps
    assert "off_system_operator_action_required" in steps
    assert "reconciliation_blocked_until_evidence_recorded" in steps
    assert "live_dispatch_disabled" in steps

    assert steps["export_packet_prepared"].status == "verified"
    assert steps["operator_review_pending"].status == "review"
    assert steps["checklist_pending"].status == "review"
    assert steps["manual_publish_url_empty"].status == "review"
    assert steps["manual_metrics_empty"].status == "review"
    assert steps["off_system_operator_action_required"].status == "review"
    assert steps["reconciliation_blocked_until_evidence_recorded"].status == "blocked"
    assert steps["live_dispatch_disabled"].status == "verified"


def test_placeholders_are_empty():
    p = build_v5_manual_pilot_trail_reconciliation_packet()
    assert len(p.placeholder_fields) == 6
    fields = {fld.field_id: fld for fld in p.placeholder_fields}
    assert "manual_publish_url" in fields
    assert "manual_publish_timestamp" in fields
    assert "manual_metrics_snapshot" in fields
    assert "platform_post_id" in fields
    assert "platform_permalink" in fields
    assert "operator_notes" in fields

    for fld in p.placeholder_fields:
        assert fld.value == ""
        assert fld.status == "empty_not_recorded"


def test_reconciliation_status_blocked():
    p = build_v5_manual_pilot_trail_reconciliation_packet()
    assert p.reconciliation_status == "blocked_reconciliation_pending_evidence"


def test_safety_flags_prohibit_live():
    p = build_v5_manual_pilot_trail_reconciliation_packet()
    flags = p.safety_flags
    assert flags["local_only"] is True
    assert flags["manual_only"] is True
    assert flags["no_platform_api"] is True
    assert flags["no_credentials"] is True
    assert flags["no_scheduler"] is True
    assert flags["no_live_dispatch"] is True
    assert flags["public_postable"] is False
    assert flags["dispatch_ready"] is False
    assert flags["approval_mutation"] is False
    assert flags["credential_values_loaded"] is False
    assert flags["network_performed"] is False


def test_disabled_live_actions():
    p = build_v5_manual_pilot_trail_reconciliation_packet()
    s = p.disabled_live_action_state
    assert s.live_dispatch_enabled is False
    assert s.publish_enabled is False
    assert s.send_enabled is False
    assert s.schedule_enabled is False
    assert s.connect_account_enabled is False
    assert s.verify_credentials_enabled is False
    assert s.sync_platform_enabled is False
    assert s.reason == "manual_pilot_trail_reconciliation_only_no_live_dispatch"
