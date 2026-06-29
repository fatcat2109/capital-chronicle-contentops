"""Unit tests for supervised dispatch packet."""
from __future__ import annotations

from live_contentops import supervised_dispatch_packet_v6 as builder


def test_packet_structure():
    packet = builder.make_supervised_dispatch_packet()
    assert packet["supervised_dispatch_status"] == "SUPERVISED_DISPATCH_BLOCKED_WAITING_FOR_VALID_OUTBOX_AND_AUTHORIZATION"
    assert packet["runtime_truth"] is False
    assert packet["outbox_entry_contract_loaded"] is True
    assert packet["valid_outbox_entry_available"] is False
    assert packet["kill_switch_active"] is True
