"""Tests for next article draft authorization and readiness builder."""
from __future__ import annotations

import json
from pathlib import Path
import pytest

from live_contentops.next_article_draft_authorization_and_readiness_v6 import (
    ROOT,
    build_next_article_draft_authorization_packet,
)

INTAKE_PATH = ROOT / "docs/automation/V6_NEXT_ARTICLE_SOURCE_PACK_INTAKE_AND_VALIDATION/next_article_source_pack_intake_validation_packet.json"
PACKET_PATH = ROOT / "docs/automation/V6_NEXT_ARTICLE_DRAFT_AUTHORIZATION_AND_READINESS/next_article_draft_authorization_and_readiness_packet.json"


def test_draft_authorization_binds_to_intake_packet() -> None:
    intake = json.loads(INTAKE_PATH.read_text(encoding="utf-8"))
    packet = build_next_article_draft_authorization_packet(intake)

    assert packet["packet_kind"] == "next_article_draft_authorization_and_readiness_v0"
    assert packet["source_pack_intake_packet_id"] == intake["source_pack_intake_packet_id"]
    assert packet["source_pack_intake_packet_hash"] == intake["exact_payload_hash"]
    assert packet["source_pack_review_packet_id"] == intake["source_pack_review_packet_id"]
    assert packet["source_pack_review_packet_hash"] == intake["source_pack_review_packet_hash"]
    assert packet["source_next_article_brief_packet_id"] == intake["source_next_article_brief_packet_id"]
    assert packet["source_next_article_brief_packet_hash"] == intake["source_next_article_brief_packet_hash"]
    assert packet["article_working_headline"] == intake["article_working_headline"]
    assert packet["draft_authorization_packet_id"].endswith(packet["exact_payload_hash"][:16])
    assert packet["draft_readiness_packet_id"].endswith(packet["exact_payload_hash"][:16])


def test_draft_authorization_checklist_coverage() -> None:
    packet = build_next_article_draft_authorization_packet()

    assert packet["checklist_coverage_status"] == "complete_coverage"
    assert len(packet["missing_check_ids"]) == 0
    assert packet["source_entry_count"] == 5
    assert packet["network_verified_url_count"] == 0
    assert packet["api_verified_source_count"] == 0
    assert packet["operator_authorization_recorded"] is True
    assert packet["authorization_scope"] == "local_canonical_draft_preparation_only"


def test_draft_authorization_readiness_semantics() -> None:
    packet = build_next_article_draft_authorization_packet()

    assert packet["ready_for_local_canonical_draft_workflow"] is True
    assert packet["ready_for_llm_drafting"] is False
    assert packet["ready_for_provider_drafting"] is False
    assert packet["canonical_draft_created"] is False
    assert packet["article_body_created"] is False
    assert packet["ready_for_auto_publish"] is False
    assert packet["ready_for_dispatch"] is False
    assert packet["live_action_allowed"] is False

    assert packet["separate_drafting_task_required"] is True
    assert packet["separate_llm_scope_required"] is True
    assert packet["separate_publish_authorization_required"] is True
    assert packet["human_review_required_before_draft_generation"] is True


def test_draft_authorization_safety_flags() -> None:
    packet = build_next_article_draft_authorization_packet()

    for field in [
        "llm_provider_call_made",
        "provider_call_made",
        "platform_api_used",
        "network_call_made",
        "public_url_fetch_made",
        "env_value_read_made",
        "credential_read_made",
        "browser_session_used",
        "live_publish_performed_by_contentops",
        "enabled_publish_send_dispatch_approve_controls",
    ]:
        assert packet[field] is False


def test_draft_authorization_refuses_invalid_inputs() -> None:
    intake = json.loads(INTAKE_PATH.read_text(encoding="utf-8"))

    # Case 1: Incomplete coverage / missing checks
    bad_intake_1 = dict(intake)
    bad_intake_1["missing_check_ids"] = ["primary_source_references_required"]
    with pytest.raises(ValueError):
        build_next_article_draft_authorization_packet(bad_intake_1)

    # Case 2: Nonzero network verified count
    bad_intake_2 = dict(intake)
    bad_intake_2["network_verified_url_count"] = 1
    with pytest.raises(ValueError):
        build_next_article_draft_authorization_packet(bad_intake_2)

    # Case 3: Ready for auto publish
    bad_intake_3 = dict(intake)
    bad_intake_3["ready_for_auto_publish"] = True
    with pytest.raises(ValueError):
        build_next_article_draft_authorization_packet(bad_intake_3)

    # Case 4: Live action allowed
    bad_intake_4 = dict(intake)
    bad_intake_4["live_action_allowed"] = True
    with pytest.raises(ValueError):
        build_next_article_draft_authorization_packet(bad_intake_4)


def test_committed_packet_matches_builder() -> None:
    committed = json.loads(PACKET_PATH.read_text(encoding="utf-8"))
    assert committed == build_next_article_draft_authorization_packet()
