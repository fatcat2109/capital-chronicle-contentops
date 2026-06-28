"""Test feedback summarizer prompt contract generation."""
from __future__ import annotations

from live_contentops import feedback_summarizer_prompt_contract_v6 as pc


def test_generate_prompt_contract():
    packet = {
        "summary_packet_id": "summary_packet_123",
        "input_snapshot_refs": [
            "snap_001_discord_safe",
            "snap_002_substack_safe",
            "snap_003_unsafe_advice",
            "snap_004_personal_data"
        ]
    }
    contract = pc.generate_prompt_contract(packet)

    assert contract["source_summary_packet_id"] == "summary_packet_123"
    assert contract["active_input_snapshot_refs"] == ["snap_001_discord_safe", "snap_002_substack_safe"]
    assert contract["excluded_snapshot_refs"] == ["snap_004_personal_data"]
    assert contract["unsafe_snapshot_refs"] == ["snap_003_unsafe_advice"]
    assert "snap_004_personal_data" in contract["blocked_snapshot_refs"]
    assert "snap_003_unsafe_advice" in contract["blocked_snapshot_refs"]
    assert "dm_or_private_message_detected" in contract["blocked_ref_reason_map"]["snap_004_personal_data"]
    assert "unsafe_financial_advice_request_detected" in contract["blocked_ref_reason_map"]["snap_003_unsafe_advice"]

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

