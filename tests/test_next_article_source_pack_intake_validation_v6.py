"""Tests for next article source pack intake and validation builder v6."""
from __future__ import annotations

import json
from pathlib import Path
import pytest

from live_contentops.next_article_source_pack_intake_validation_v6 import (
    ROOT,
    build_next_article_source_pack_intake_validation_packet,
)

PACKET_PATH = ROOT / "docs/automation/V6_NEXT_ARTICLE_SOURCE_PACK_INTAKE_AND_VALIDATION/next_article_source_pack_intake_validation_packet.json"
REVIEW_PATH = ROOT / "docs/automation/V6_NEXT_ARTICLE_BRIEF_SOURCE_PACK_AND_REVIEW/next_article_brief_source_pack_review_packet.json"


def test_source_pack_intake_binds_to_review_packet() -> None:
    review = json.loads(REVIEW_PATH.read_text(encoding="utf-8"))
    packet = build_next_article_source_pack_intake_validation_packet(review)

    assert packet["packet_kind"] == "next_article_source_pack_intake_validation_v0"
    assert packet["source_pack_review_packet_id"] == review["source_pack_review_packet_id"]
    assert packet["source_pack_review_packet_hash"] == review["exact_payload_hash"]
    assert packet["source_next_article_brief_packet_id"] == review["source_next_article_brief_packet_id"]
    assert packet["source_next_article_brief_packet_hash"] == review["source_next_article_brief_packet_hash"]
    assert packet["article_working_headline"] == review["article_working_headline"]
    assert packet["source_pack_intake_packet_id"].endswith(packet["exact_payload_hash"][:16])
    assert packet["source_pack_validation_packet_id"].endswith(packet["exact_payload_hash"][:16])


def test_source_pack_intake_validation_status_and_coverage() -> None:
    packet = build_next_article_source_pack_intake_validation_packet()

    assert packet["intake_status"] == "operator_source_pack_supplied_for_review"
    assert packet["validation_status"] == "local_metadata_validation_pending_operator_review"
    assert packet["source_pack_collection_status"] == "operator_supplied_complete_pending_review"
    assert packet["checklist_coverage_status"] == "complete_coverage"
    assert len(packet["covered_check_ids"]) == 5
    assert len(packet["missing_check_ids"]) == 0
    assert packet["source_entry_count"] == 5
    assert packet["source_url_count"] == 1
    assert packet["network_verified_url_count"] == 0
    assert packet["api_verified_source_count"] == 0


def test_source_entries_metadata_safety() -> None:
    packet = build_next_article_source_pack_intake_validation_packet()

    for entry in packet["source_entries"]:
        assert entry["operator_supplied_only"] is True
        assert entry["source_url_network_verified"] is False
        assert entry["source_api_used"] is False
        assert entry["source_scraped"] is False
        assert entry["validation_status"] == "pending_operator_review"


def test_source_pack_intake_not_ready_and_safety_flags() -> None:
    packet = build_next_article_source_pack_intake_validation_packet()

    assert packet["ready_for_llm_drafting"] is False
    assert packet["ready_for_canonical_draft"] is False
    assert packet["ready_for_auto_publish"] is False
    assert packet["ready_for_dispatch"] is False
    assert packet["live_action_allowed"] is False
    assert packet["enabled_publish_send_dispatch_approve_controls"] is False

    for field in [
        "network_call_made",
        "provider_call_made",
        "llm_provider_call_made",
        "env_value_read_made",
        "credential_read_made",
        "browser_session_used",
        "public_url_fetch_made",
        "platform_api_used",
        "live_publish_performed_by_contentops",
    ]:
        assert packet[field] is False


def test_source_pack_intake_rejects_financial_advice() -> None:
    review = json.loads(REVIEW_PATH.read_text(encoding="utf-8"))
    review["article_working_headline"] = "Margin checklist with buy recommendations"

    with pytest.raises(ValueError):
        build_next_article_source_pack_intake_validation_packet(review)


def test_committed_source_pack_intake_packet_matches_builder() -> None:
    committed = json.loads(PACKET_PATH.read_text(encoding="utf-8"))
    assert committed == build_next_article_source_pack_intake_validation_packet()
