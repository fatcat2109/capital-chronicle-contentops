"""Unit tests for feedback summary backlog packet."""
from __future__ import annotations

from live_contentops import feedback_summary_backlog_packet_v6 as builder


def test_packet_structure():
    packet = builder.make_feedback_summary_backlog_packet()
    assert packet["feedback_summary_backlog_status"] == "FEEDBACK_SUMMARY_BACKLOG_BLOCKED_WAITING_FOR_FEEDBACK_CAPTURE"
    assert packet["runtime_truth"] is False
    assert packet["community_feedback_capture_contract_loaded"] is True
    assert packet["community_feedback_capture_available"] is False
    assert packet["kill_switch_active"] is True
