"""Unit tests for next article planning packet."""
from __future__ import annotations

from live_contentops import next_article_planning_from_feedback_packet_v6 as builder


def test_packet_structure():
    packet = builder.make_next_article_planning_from_feedback_packet()
    assert packet["next_article_planning_status"] == "NEXT_ARTICLE_PLANNING_BLOCKED_WAITING_FOR_FEEDBACK_SUMMARY_BACKLOG"
    assert packet["runtime_truth"] is False
    assert packet["feedback_summary_backlog_contract_loaded"] is True
    assert packet["feedback_summary_available"] is False
    assert packet["kill_switch_active"] is True
