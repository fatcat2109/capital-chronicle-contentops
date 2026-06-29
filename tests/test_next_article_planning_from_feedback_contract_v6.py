"""Unit tests for next article planning from feedback contract coordinator."""
from __future__ import annotations

from live_contentops import next_article_planning_from_feedback_contract_v6 as coordinator


def test_coordinator_outputs():
    packet = coordinator.make_next_article_planning_from_feedback_packet()
    contract = coordinator.make_next_article_planning_from_feedback_input_contract()
    template = coordinator.make_next_article_planning_blocked_template()
    output = coordinator.make_next_article_planning_blocked_output()
    matrix = coordinator.make_next_article_planning_gate_matrix()
    checklist = coordinator.make_next_article_planning_checklist()

    assert packet["next_article_planning_status"] == "NEXT_ARTICLE_PLANNING_BLOCKED_WAITING_FOR_FEEDBACK_SUMMARY_BACKLOG"
    assert contract["contract_status"] == "FUTURE_NEXT_ARTICLE_PLANNING_FROM_FEEDBACK_INPUT_CONTRACT_ONLY"
    assert template["feedback_template_status"] == "BLOCKED_TEMPLATE_ONLY_NOT_NEXT_ARTICLE_PLANNING"
    assert output["feedback_output_status"] == "BLOCKED_NO_NEXT_ARTICLE_PLANNING_CREATED"
    assert len(matrix) == 4
    assert checklist["checklist_status"] == "NEXT_ARTICLE_PLANNING_BLOCKED_PENDING_FEEDBACK_SUMMARY_AND_PLANNING_POLICY"
