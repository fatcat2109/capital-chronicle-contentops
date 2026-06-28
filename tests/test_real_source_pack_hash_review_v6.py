"""Test V6 Real Source Pack Hash Review Packet."""
from __future__ import annotations

from live_contentops import real_source_pack_hash_review_v6 as hash_builder


def test_make_hash_review_packet():
    packet = hash_builder.make_hash_review_packet()
    
    assert packet["hash_review_status"] == "WAITING_FOR_OPERATOR_SOURCE_PACK"
    assert packet["runtime_truth"] is False
    assert packet["raw_hash_values_persisted"] is False
    assert packet["raw_source_urls_persisted"] is False
    assert packet["raw_source_excerpts_persisted"] is False
    assert packet["redacted_hash_presence_only"] is True
    assert packet["hash_count"] == 0
    assert packet["source_entry_count"] == 0
    assert packet["all_hashes_present"] is False
    assert packet["all_entries_redacted"] is True
    assert packet["valid_for_source_approval"] is False
    assert packet["valid_for_draft_generation"] is False
    assert packet["valid_for_publication"] is False
    assert packet["valid_for_dispatch"] is False
    assert packet["human_review_required"] is True
    assert packet["kill_switch_active"] is True
