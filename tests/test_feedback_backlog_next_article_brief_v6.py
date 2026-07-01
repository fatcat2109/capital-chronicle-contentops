"""Tests for feedback backlog to next article brief candidate v6."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from live_contentops.feedback_backlog_next_article_brief_v6 import (
    ROOT,
    build_feedback_backlog_next_article_brief_packet,
)

PACKET_PATH = ROOT / "docs/automation/V6_FEEDBACK_BACKLOG_REVIEW_TO_NEXT_ARTICLE_BRIEF/feedback_backlog_next_article_brief_packet.json"
BACKLOG_PATH = ROOT / "docs/automation/V6_OPERATOR_SUPPLIED_FEEDBACK_INTAKE_AND_BACKLOG/operator_feedback_backlog_summary_packet.json"


def test_next_article_brief_selects_highest_priority_backlog_candidate() -> None:
    backlog = json.loads(BACKLOG_PATH.read_text(encoding="utf-8"))
    packet = build_feedback_backlog_next_article_brief_packet(backlog)
    expected = sorted(
        backlog["backlog_candidates"],
        key=lambda candidate: (-candidate["priority_score"], candidate["candidate_id"]),
    )[0]

    assert packet["packet_kind"] == "feedback_backlog_next_article_brief_candidate_v0"
    assert packet["selection_method"] == "deterministic_highest_priority_score_then_candidate_id"
    assert packet["selected_backlog_candidate_id"] == expected["candidate_id"]
    assert packet["selected_priority_score"] == expected["priority_score"]
    assert packet["selected_source_feedback_item_ids"] == expected["source_feedback_item_ids"]
    assert packet["source_backlog_summary_packet_id"] == backlog["backlog_summary_packet_id"]
    assert packet["source_backlog_summary_hash"] == backlog["exact_payload_hash"]
    assert packet["next_article_brief_packet_id"].endswith(packet["exact_payload_hash"][:16])


def test_next_article_brief_is_review_only_and_blocks_live_controls() -> None:
    packet = build_feedback_backlog_next_article_brief_packet()

    assert packet["candidate_review_status"] == "ready_for_operator_review_only"
    assert packet["operator_review_required"] is True
    assert packet["source_pack_required_before_drafting"] is True
    assert packet["canonical_draft_created"] is False
    assert packet["brief_candidate"]["canonical_draft_requested"] is False
    assert packet["brief_candidate"]["publication_or_dispatch_requested"] is False
    assert packet["brief_candidate"]["not_financial_advice"] is True
    assert packet["blocked_controls"] == ["approve", "dispatch", "publish", "schedule", "send"]
    assert all(value is False for value in packet["non_readiness_claims"].values())


def test_next_article_brief_safety_flags_are_false() -> None:
    packet = build_feedback_backlog_next_article_brief_packet()

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
    assert packet["forbidden_financial_advice_or_signal_wording_present"] is False


def test_next_article_brief_rejects_signal_wording() -> None:
    backlog = json.loads(BACKLOG_PATH.read_text(encoding="utf-8"))
    backlog["backlog_candidates"][0]["article_angle"] = "Issue a buy signal."

    with pytest.raises(ValueError):
        build_feedback_backlog_next_article_brief_packet(backlog)


def test_committed_next_article_brief_packet_matches_builder() -> None:
    committed = json.loads(PACKET_PATH.read_text(encoding="utf-8"))
    assert committed == build_feedback_backlog_next_article_brief_packet()
