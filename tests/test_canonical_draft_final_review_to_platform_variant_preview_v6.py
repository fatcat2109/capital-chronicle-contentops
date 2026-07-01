"""Backend tests for V6 Canonical Draft Final Review and Platform Variant Preview."""
from __future__ import annotations

import json
from pathlib import Path
from live_contentops.canonical_draft_final_review_to_platform_variant_preview_v6 import build_packet

ROOT = Path(__file__).resolve().parents[1]
PACKET_PATH = ROOT / "docs" / "automation" / "V6_CANONICAL_DRAFT_FINAL_REVIEW_TO_PLATFORM_VARIANT_PREVIEW" / "canonical_draft_final_review_to_platform_variant_preview_packet.json"


def test_packet_creation_and_contents() -> None:
    packet = build_packet()
    assert packet["packet_kind"] == "canonical_draft_final_review_to_platform_variant_preview_v0"
    assert packet["canonical_draft_final_review_status"] == "ready_for_operator_final_review"
    assert packet["final_article_approved"] is False
    assert packet["operator_final_approval_required"] is True
    assert packet["platform_variant_preview_status"] == "platform_variant_preview_created_for_operator_review"
    assert packet["platform_variants_created"] is True
    assert packet["platform_variants_are_preview_only"] is True
    assert packet["platform_payloads_approved"] is False
    assert packet["approval_record_created"] is False
    assert packet["outbox_entry_created"] is False
    assert packet["ready_for_auto_publish"] is False
    assert packet["ready_for_dispatch"] is False
    assert packet["live_action_allowed"] is False
    assert packet["public_url_verification_performed"] is False
    assert packet["llm_provider_call_made"] is False
    assert packet["provider_call_made"] is False
    assert packet["platform_api_used"] is False
    assert packet["network_call_made"] is False
    assert packet["public_url_fetch_made"] is False
    assert packet["env_value_read_made"] is False
    assert packet["credential_read_made"] is False
    assert packet["browser_session_used"] is False
    assert packet["live_publish_performed_by_contentops"] is False
    assert packet["enabled_publish_send_dispatch_approve_controls"] is False
    assert packet["forbidden_financial_advice_or_signal_wording_present"] is False

    # Check 10 required platform preview variants
    variants = packet["preview_variants"]
    required_keys = [
        "substack_canonical_preview",
        "discord_drop_preview",
        "telegram_operator_preview",
        "x_manual_preview",
        "linkedin_personal_deferred_preview",
        "threads_preview",
        "facebook_page_preview",
        "instagram_caption_preview",
        "youtube_metadata_future_preview",
        "tiktok_metadata_deferred_preview",
    ]
    for key in required_keys:
        assert key in variants
        assert variants[key]["status"] == "preview_only"
        assert len(variants[key]["title"]) > 0
        assert len(variants[key]["body"]) > 0


def test_packet_file_saved_correctly() -> None:
    assert PACKET_PATH.exists()
    data = json.loads(PACKET_PATH.read_text(encoding="utf-8"))
    assert data["canonical_draft_final_review_status"] == "ready_for_operator_final_review"
    assert data["source_local_draft_preview_packet_id"] == "local_draft_preview_1f81b17970b6c151"
    assert data["source_exact_payload_hash"] == "1f81b17970b6c151d301c63af23e7adcc814e6ddf65bcd4e9a6b2c5def0c8b97"
