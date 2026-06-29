"""Unit tests for community feedback capture contract coordinator."""
from __future__ import annotations

from live_contentops import community_feedback_capture_contract_v6 as coordinator


def test_coordinator_outputs():
    packet = coordinator.make_community_feedback_capture_packet()
    contract = coordinator.make_community_feedback_capture_input_contract()
    template = coordinator.make_community_feedback_capture_blocked_template()
    output = coordinator.make_community_feedback_capture_blocked_output()
    matrix = coordinator.make_community_feedback_capture_gate_matrix()
    checklist = coordinator.make_community_feedback_capture_checklist()

    assert packet["community_feedback_capture_status"] == "COMMUNITY_FEEDBACK_CAPTURE_BLOCKED_WAITING_FOR_PUBLICATION_AUDIT_RECORD"
    assert contract["contract_status"] == "FUTURE_COMMUNITY_FEEDBACK_CAPTURE_INPUT_CONTRACT_ONLY"
    assert template["feedback_template_status"] == "BLOCKED_TEMPLATE_ONLY_NOT_FEEDBACK_CAPTURE"
    assert output["feedback_output_status"] == "BLOCKED_NO_COMMUNITY_FEEDBACK_CAPTURE_CREATED"
    assert len(matrix) == 6
    assert checklist["checklist_status"] == "COMMUNITY_FEEDBACK_CAPTURE_BLOCKED_PENDING_PUBLICATION_AUDIT_AND_SOURCE_BINDING"
