"""Test feedback summarizer prompt contract generation."""
from __future__ import annotations

from live_contentops import feedback_summarizer_prompt_contract_v6 as pc


def test_generate_prompt_contract():
    packet = {
        "summary_packet_id": "summary_packet_123",
        "input_snapshot_refs": ["snap_001", "snap_002"]
    }
    contract = pc.generate_prompt_contract(packet)

    assert contract["source_summary_packet_id"] == "summary_packet_123"
    assert contract["input_snapshot_refs"] == ["snap_001", "snap_002"]
    assert contract["provider_call_performed"] is False
    assert contract["provider_credentials_hydrated"] is False
    assert contract["human_review_required"] is True
    assert contract["dispatch_allowed_now"] is False
    assert contract["public_postable"] is False
    assert "ghp_" not in str(contract)
    assert ".env" not in str(contract)
    assert "sk-proj-" not in str(contract)
    assert len(contract["required_caveats"]) > 0
    assert len(contract["blocked_topic_rules"]) > 0
