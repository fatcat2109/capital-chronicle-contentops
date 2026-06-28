"""V6 Real Source Pack Hash Review Packet Generator.

Creates the redacted hash-presence review structures.
"""
from __future__ import annotations

from typing import Any


def make_hash_review_packet() -> dict[str, Any]:
    """Generates a default redacted hash review packet."""
    return {
        "hash_review_status": "WAITING_FOR_OPERATOR_SOURCE_PACK",
        "runtime_truth": False,
        "raw_hash_values_persisted": False,
        "raw_source_urls_persisted": False,
        "raw_source_excerpts_persisted": False,
        "redacted_hash_presence_only": True,
        "hash_count": 0,
        "source_entry_count": 0,
        "all_hashes_present": False,
        "all_entries_redacted": True,
        "valid_for_source_approval": False,
        "valid_for_draft_generation": False,
        "valid_for_publication": False,
        "valid_for_dispatch": False,
        "human_review_required": True,
        "kill_switch_active": True
    }
