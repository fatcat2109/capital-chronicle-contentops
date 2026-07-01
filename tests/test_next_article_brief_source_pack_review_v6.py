"""Tests for next article brief source pack and review builder v6."""
from __future__ import annotations

import json
from pathlib import Path
import pytest

from live_contentops.next_article_brief_source_pack_review_v6 import (
    ROOT,
    build_next_article_brief_source_pack_review_packet,
)

PACKET_PATH = ROOT / "docs/automation/V6_NEXT_ARTICLE_BRIEF_SOURCE_PACK_AND_REVIEW/next_article_brief_source_pack_review_packet.json"
BRIEF_PATH = ROOT / "docs/automation/V6_FEEDBACK_BACKLOG_REVIEW_TO_NEXT_ARTICLE_BRIEF/feedback_backlog_next_article_brief_packet.json"


def test_source_pack_review_binds_to_brief_packet() -> None:
    brief = json.loads(BRIEF_PATH.read_text(encoding="utf-8"))
    packet = build_next_article_brief_source_pack_review_packet(brief)

    assert packet["packet_kind"] == "next_article_brief_source_pack_review_v0"
    assert packet["source_next_article_brief_packet_id"] == brief["next_article_brief_packet_id"]
    assert packet["source_next_article_brief_packet_hash"] == brief["exact_payload_hash"]
    assert packet["selected_backlog_candidate_id"] == brief["selected_backlog_candidate_id"]
    assert packet["article_working_headline"] == brief["brief_candidate"]["working_headline"]
    assert packet["source_pack_review_packet_id"].endswith(packet["exact_payload_hash"][:16])


def test_source_pack_review_checklist_and_status() -> None:
    packet = build_next_article_brief_source_pack_review_packet()

    assert packet["source_pack_status"] == "source_pack_required_pending_operator_collection"
    assert packet["operator_review_status"] == "pending_operator_review"
    assert len(packet["source_pack_checklist"]) == 5

    for item in packet["source_pack_checklist"]:
        assert item["status"] == "pending_operator_collection"
        assert item["required_before_drafting"] is True
        assert item["external_url"] is None
        assert item["evidence_path"] is None
        assert item["network_verified"] is False
        assert item["operator_supplied_only"] is True


def test_source_pack_review_not_ready_and_safety_flags() -> None:
    packet = build_next_article_brief_source_pack_review_packet()

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


def test_source_pack_review_rejects_financial_advice() -> None:
    brief = json.loads(BRIEF_PATH.read_text(encoding="utf-8"))
    brief["brief_candidate"]["working_headline"] = "Durable margins and a trade signal recommendation"

    with pytest.raises(ValueError):
        build_next_article_brief_source_pack_review_packet(brief)


def test_committed_source_pack_review_packet_matches_builder() -> None:
    committed = json.loads(PACKET_PATH.read_text(encoding="utf-8"))
    assert committed == build_next_article_brief_source_pack_review_packet()
