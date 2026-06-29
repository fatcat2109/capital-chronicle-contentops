"""Unit tests for publication audit record packet."""
from __future__ import annotations

from live_contentops import publication_audit_record_packet_v6 as builder


def test_packet_structure():
    packet = builder.make_publication_audit_record_packet()
    assert packet["publication_audit_record_status"] == "PUBLICATION_AUDIT_RECORD_BLOCKED_WAITING_FOR_SUPERVISED_DISPATCH_RESULT"
    assert packet["runtime_truth"] is False
    assert packet["supervised_dispatch_contract_loaded"] is True
    assert packet["supervised_dispatch_success_available"] is False
    assert packet["kill_switch_active"] is True
