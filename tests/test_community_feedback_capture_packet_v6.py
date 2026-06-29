"""Unit tests for community feedback capture packet."""
from __future__ import annotations

from live_contentops import community_feedback_capture_packet_v6 as builder


def test_packet_structure():
    packet = builder.make_community_feedback_capture_packet()
    assert packet["community_feedback_capture_status"] == "COMMUNITY_FEEDBACK_CAPTURE_BLOCKED_WAITING_FOR_PUBLICATION_AUDIT_RECORD"
    assert packet["runtime_truth"] is False
    assert packet["publication_audit_record_contract_loaded"] is True
    assert packet["publication_audit_record_available"] is False
    assert packet["kill_switch_active"] is True
