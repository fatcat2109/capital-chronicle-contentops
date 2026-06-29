"""Unit tests for outbox entry packet module."""
from __future__ import annotations

from live_contentops.outbox_entry_packet_v6 import make_outbox_entry_packet


def test_packet_structure():
    packet = make_outbox_entry_packet()
    assert packet["outbox_entry_status"] == "OUTBOX_ENTRY_BLOCKED_WAITING_FOR_APPROVED_EXACT_PAYLOAD_REVIEW"
    assert packet["runtime_truth"] is False
    assert packet["human_review_required"] is True
    assert packet["kill_switch_active"] is True
