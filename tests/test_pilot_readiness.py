import json
import os
import pytest
from pathlib import Path

def test_readiness_matrix_validity():
    matrix_path = Path(os.path.dirname(__file__)) / ".." / "docs" / "LIMITED_LIVE_PILOT_READINESS_MATRIX.json"
    assert matrix_path.exists(), "Readiness matrix JSON must exist"
    
    with open(matrix_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    assert "readiness_matrix" in data
    entries = data["readiness_matrix"]
    
    # ensure it parses and contains required fields
    for entry in entries:
        assert "component" in entry
        assert "status" in entry
        assert "evidence" in entry
        assert "blockers" in entry
        assert "required_next_action" in entry
        assert "can_use_live_keys_now" in entry
        assert "can_call_network_now" in entry
        assert "can_publish_now" in entry
        assert "human_approval_required" in entry
        
        # enforce absolute NO-GO constraints
        assert entry["can_use_live_keys_now"] is False, "NO-GO: live keys cannot be enabled"
        assert entry["can_call_network_now"] is False, "NO-GO: network cannot be enabled"
        assert entry["can_publish_now"] is False, "NO-GO: publish cannot be enabled"

        # explicitly enforce human approval requirement for live-adjacent items
        if entry["component"] in ["telegram_adapter", "x_adapter", "linkedin_adapter", "instagram_asset_export", "platform_credentials", "provider_gateway"]:
            assert entry["human_approval_required"] is True, f"NO-GO: human approval must be required for {entry['component']}"

def test_go_no_go_decision_packet():
    packet_path = Path(os.path.dirname(__file__)) / ".." / "docs" / "LIMITED_LIVE_PILOT_GO_NO_GO_PACKET.md"
    assert packet_path.exists(), "Decision packet must exist"
    content = packet_path.read_text(encoding="utf-8")
    
    assert "NO-GO" in content.upper(), "Decision packet must contain NO-GO language"
    assert "TASK_CONTENTOPS_0046_LIVE_PILOT_OPERATOR_PREREQUISITE_COLLECTION_AND_STAGING_ENV_DESIGN" in content, "Exact next task label must be preserved"
