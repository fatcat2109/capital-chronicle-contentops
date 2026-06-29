"""Unit tests for feedback summary backlog contract coordinator."""
from __future__ import annotations

from live_contentops import feedback_summary_backlog_contract_v6 as coordinator


def test_coordinator_outputs():
    packet = coordinator.make_feedback_summary_backlog_packet()
    contract = coordinator.make_feedback_summary_backlog_input_contract()
    template = coordinator.make_feedback_summary_backlog_blocked_template()
    output = coordinator.make_feedback_summary_backlog_blocked_output()
    matrix = coordinator.make_feedback_summary_backlog_gate_matrix()
    checklist = coordinator.make_feedback_summary_backlog_checklist()

    assert packet["feedback_summary_backlog_status"] == "FEEDBACK_SUMMARY_BACKLOG_BLOCKED_WAITING_FOR_FEEDBACK_CAPTURE"
    assert contract["contract_status"] == "FUTURE_FEEDBACK_SUMMARY_BACKLOG_INPUT_CONTRACT_ONLY"
    assert template["feedback_template_status"] == "BLOCKED_TEMPLATE_ONLY_NOT_FEEDBACK_SUMMARY"
    assert output["feedback_output_status"] == "BLOCKED_NO_FEEDBACK_SUMMARY_CREATED"
    assert len(matrix) == 4
    assert checklist["checklist_status"] == "FEEDBACK_SUMMARY_BACKLOG_BLOCKED_PENDING_FEEDBACK_CAPTURE_AND_POLICIES"
