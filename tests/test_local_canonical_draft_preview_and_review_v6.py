"""Tests for local canonical draft preview and review builder."""
from __future__ import annotations

import json
from pathlib import Path
import pytest

from live_contentops.local_canonical_draft_preview_and_review_v6 import (
    ROOT,
    build_local_canonical_draft_preview,
)

AUTH_PATH = ROOT / "docs/automation/V6_NEXT_ARTICLE_DRAFT_AUTHORIZATION_AND_READINESS/next_article_draft_authorization_and_readiness_packet.json"
INTAKE_PATH = ROOT / "docs/automation/V6_NEXT_ARTICLE_SOURCE_PACK_INTAKE_AND_VALIDATION/next_article_source_pack_intake_validation_packet.json"
PACKET_PATH = ROOT / "docs/automation/V6_LOCAL_CANONICAL_DRAFT_PREVIEW_AND_REVIEW/local_canonical_draft_preview_and_review_packet.json"


def test_draft_preview_binds_to_auth_packet() -> None:
    auth = json.loads(AUTH_PATH.read_text(encoding="utf-8"))
    packet = build_local_canonical_draft_preview(auth)

    assert packet["packet_kind"] == "local_canonical_draft_preview_and_review_v0"
    assert packet["source_draft_authorization_packet_id"] == auth["draft_authorization_packet_id"]
    assert packet["source_draft_authorization_packet_hash"] == auth["exact_payload_hash"]
    assert packet["source_draft_readiness_packet_id"] == auth["draft_readiness_packet_id"]
    assert packet["source_draft_readiness_packet_hash"] == auth["exact_payload_hash"]
    assert packet["source_pack_intake_packet_id"] == auth["source_pack_intake_packet_id"]
    assert packet["source_pack_intake_packet_hash"] == auth["source_pack_intake_packet_hash"]
    assert packet["source_next_article_brief_packet_id"] == auth["source_next_article_brief_packet_id"]
    assert packet["source_next_article_brief_packet_hash"] == auth["source_next_article_brief_packet_hash"]
    assert packet["article_working_headline"] == auth["article_working_headline"]
    assert packet["local_draft_preview_packet_id"].endswith(packet["exact_payload_hash"][:16])
    assert packet["draft_review_packet_id"].endswith(packet["exact_payload_hash"][:16])


def test_draft_preview_status_and_metadata() -> None:
    packet = build_local_canonical_draft_preview()

    assert packet["draft_preview_status"] == "local_draft_preview_created_for_review"
    assert packet["draft_review_status"] == "pending_operator_review"
    assert packet["draft_generation_method"] == "deterministic_template_no_llm"
    assert packet["canonical_draft_created"] is True
    assert packet["article_body_created"] is True
    assert packet["final_article_approved"] is False

    assert packet["ready_for_llm_drafting"] is False
    assert packet["ready_for_provider_drafting"] is False
    assert packet["ready_for_auto_publish"] is False
    assert packet["ready_for_dispatch"] is False
    assert packet["live_action_allowed"] is False


def test_draft_preview_structured_fields() -> None:
    packet = build_local_canonical_draft_preview()

    assert "working_title" in packet
    assert "dek" in packet
    assert "thesis" in packet
    assert "audience_question" in packet
    assert len(packet["section_outline"]) > 0
    assert len(packet["draft_preview_sections"]) > 0
    assert len(packet["evidence_callouts"]) > 0
    assert len(packet["definitions_to_include"]) > 0
    assert len(packet["caveats_to_include"]) > 0
    assert "non_advisory_disclaimer" in packet
    assert len(packet["operator_review_questions"]) > 0


def test_draft_preview_checklist_and_readiness_locks() -> None:
    packet = build_local_canonical_draft_preview()

    assert packet["source_support_review_required"] is True
    assert packet["definitions_review_required"] is True
    assert packet["caveat_review_required"] is True
    assert packet["non_advisory_review_required"] is True
    assert packet["final_operator_approval_required"] is True

    assert packet["separate_final_approval_task_required"] is True
    assert packet["separate_platform_variant_task_required"] is True
    assert packet["separate_publish_authorization_required"] is True
    assert packet["public_url_verification_performed"] is False


def test_draft_preview_safety_flags() -> None:
    packet = build_local_canonical_draft_preview()

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


def test_draft_preview_refuses_invalid_inputs() -> None:
    auth = json.loads(AUTH_PATH.read_text(encoding="utf-8"))

    # Case 1: ready_for_local_canonical_draft_workflow is False
    bad_auth_1 = dict(auth)
    bad_auth_1["ready_for_local_canonical_draft_workflow"] = False
    with pytest.raises(ValueError):
        build_local_canonical_draft_preview(bad_auth_1)

    # Case 2: ready_for_llm_drafting is True
    bad_auth_2 = dict(auth)
    bad_auth_2["ready_for_llm_drafting"] = True
    with pytest.raises(ValueError):
        build_local_canonical_draft_preview(bad_auth_2)

    # Case 3: ready_for_auto_publish is True
    bad_auth_3 = dict(auth)
    bad_auth_3["ready_for_auto_publish"] = True
    with pytest.raises(ValueError):
        build_local_canonical_draft_preview(bad_auth_3)

    # Case 4: checklist coverage not complete
    bad_auth_4 = dict(auth)
    bad_auth_4["checklist_coverage_status"] = "missing_coverage"
    with pytest.raises(ValueError):
        build_local_canonical_draft_preview(bad_auth_4)


def test_committed_packet_matches_builder() -> None:
    committed = json.loads(PACKET_PATH.read_text(encoding="utf-8"))
    assert committed == build_local_canonical_draft_preview()
