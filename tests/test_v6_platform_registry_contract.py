"""Tests for V6 platform registry Fast Ship posture."""
from __future__ import annotations

from live_contentops.v6_platform_registry_contract import build_registry


def test_meta_family_fast_ship_live_capable_when_credentials_present() -> None:
    packet = {
        "platform_rows": [
            {"platform": "Facebook Page", "capability_class": "credential_present_scope_proof_required", "live_write_eligible": False},
            {"platform": "Instagram Business", "capability_class": "credential_present_scope_proof_required", "live_write_eligible": False},
            {"platform": "Threads separate app/user", "capability_class": "credential_present_scope_proof_required", "live_write_eligible": False},
            {"platform": "Telegram operator inbox", "capability_class": "ready_api", "live_write_eligible": False},
        ]
    }

    registry = build_registry(packet)
    rows = {row["platform_id"]: row for row in registry["platforms"]}

    assert registry["live_write_allowed_now"] is True
    assert rows["facebook_page"]["current_execution_posture"] == "ready_api_live_capable_fast_ship"
    assert rows["instagram_business"]["current_execution_posture"] == "ready_api_live_capable_fast_ship"
    assert rows["threads"]["current_execution_posture"] == "ready_api_live_capable_fast_ship"
    assert rows["facebook_page"]["live_write_allowed_now"] is True
    assert rows["instagram_business"]["live_write_allowed_now"] is True
    assert rows["threads"]["live_write_allowed_now"] is True
    assert rows["telegram"]["current_execution_posture"] == "ready_api_but_live_disabled"
    assert rows["telegram"]["live_write_allowed_now"] is False
