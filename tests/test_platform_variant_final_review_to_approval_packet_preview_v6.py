"""Backend tests for V6 Platform Variant Final Review to Approval Packet Preview."""
from __future__ import annotations

import json
from pathlib import Path
from live_contentops.platform_variant_final_review_to_approval_packet_preview_v6 import build_packet

ROOT = Path(__file__).resolve().parents[1]
PACKET_PATH = ROOT / "docs" / "automation" / "V6_PLATFORM_VARIANT_FINAL_REVIEW_TO_APPROVAL_PACKET_PREVIEW" / "platform_variant_final_review_to_approval_packet_preview.json"


def test_packet_creation_and_contents() -> None:
    packet = build_packet()
    assert packet["packet_kind"] == "platform_variant_final_review_to_approval_packet_preview_v0"
    assert packet["platform_variant_final_review_status"] == "ready_for_operator_approval_packet_review"
    assert packet["approval_packet_preview_status"] == "approval_packet_preview_created_for_operator_review"
    assert packet["exact_platform_payload_previews_created"] is True
    assert packet["exact_payload_hashes_created"] is True
    assert packet["approval_packet_preview_created"] is True
    assert packet["actual_operator_approval_recorded"] is False
    assert packet["approval_ledger_entry_created"] is False
    assert packet["approval_record_created"] is False
    assert packet["approval_signature_present"] is False
    assert packet["approval_signature_required"] is True
    assert packet["outbox_entry_created"] is False
    assert packet["dispatch_outbox_ready"] is False
    assert packet["platform_payloads_approved"] is False
    assert packet["final_article_approved"] is False
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

    # Check 10 required platform preview targets
    targets = packet["approval_targets"]
    required_keys = [
        "substack_approval_preview",
        "discord_approval_preview",
        "telegram_approval_preview",
        "x_approval_preview",
        "linkedin_approval_preview",
        "threads_approval_preview",
        "facebook_approval_preview",
        "instagram_approval_preview",
        "youtube_approval_preview",
        "tiktok_approval_preview",
    ]
    for key in required_keys:
        assert key in targets
        t = targets[key]
        assert t["approval_required"] is True
        assert t["approved"] is False
        assert t["dispatchable"] is False
        assert t["no_public_url_claim"] is True
        assert t["no_metrics_claim"] is True
        assert len(t["exact_preview_text"]) > 0
        assert len(t["payload_hash"]) > 0


def test_packet_file_saved_correctly() -> None:
    assert PACKET_PATH.exists()
    data = json.loads(PACKET_PATH.read_text(encoding="utf-8"))
    assert data["platform_variant_final_review_status"] == "ready_for_operator_approval_packet_review"
    assert data["source_final_review_packet_id"] == "final_review_preview_11fc52e6e452c4d3"
    assert data["source_final_review_hash"] == "11fc52e6e452c4d3fedd306ffbf796fae459e061c784eed86cc1e8f65b9d38f2"
