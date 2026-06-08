import json
import os
import pytest
from live_contentops.prompt_injection import generate_prompt_packet

def load_fixture(name: str) -> dict:
    base_dir = os.path.dirname(__file__)
    path = os.path.join(base_dir, "fixtures", "editorial", name)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def test_generate_prompt_packet():
    req = load_fixture("prompt_packet_input.json")
    packet = generate_prompt_packet(req)
    
    assert packet["prompt_packet_id"].startswith("prompt_")
    assert packet["target_platforms"] == ["linkedin"]
    
    # Check flags
    assert packet["advisory_only"] is True
    assert packet["approval_granted"] is False
    assert packet["publish_ready"] is False
    assert packet["provider_call_allowed"] is False
    assert packet["search_call_allowed"] is False
    assert packet["platform_action_allowed"] is False
    
    # Check sections
    sections = packet["prompt_sections"]
    assert "Grounded search is research context only" in sections["system_boundary_section"]
    assert "LLM output is not authority" in sections["system_boundary_section"]
    assert "No approval/publishing/trading authority is granted" in sections["system_boundary_section"]
    
    # Cost policy
    notes = packet["cost_policy_notes"]
    assert any("One search context per content packet" in n for n in notes)
    assert any("No live search in this task" in n for n in notes)
    
    # Blocked claims
    assert "invent facts" in packet["blocked_claims"]
    
    # Not public postable
    assert packet["no_public_post_reason"] is not None
