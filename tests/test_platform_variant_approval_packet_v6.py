"""Unit tests for platform variant approval packet module."""
from __future__ import annotations

from live_contentops.platform_variant_approval_packet_v6 import make_platform_variant_approval_packet


def test_packet_structure():
    packet = make_platform_variant_approval_packet()
    assert packet["platform_variant_approval_contract_status"] == "APPROVAL_PACKET_CONTRACT_BLOCKED_WAITING_FOR_RENDERED_PLATFORM_VARIANTS"
    assert packet["runtime_truth"] is False
    assert packet["human_review_required"] is True
    assert packet["kill_switch_active"] is True
