"""Unit tests for approval queue exact payload review packet module."""
from __future__ import annotations

from live_contentops.approval_queue_exact_payload_review_packet_v6 import make_approval_queue_exact_payload_review_packet


def test_packet_structure():
    packet = make_approval_queue_exact_payload_review_packet()
    assert packet["approval_queue_review_status"] == "EXACT_PAYLOAD_REVIEW_BLOCKED_WAITING_FOR_APPROVAL_PACKET_AND_PAYLOADS"
    assert packet["runtime_truth"] is False
    assert packet["human_review_required"] is True
    assert packet["kill_switch_active"] is True
