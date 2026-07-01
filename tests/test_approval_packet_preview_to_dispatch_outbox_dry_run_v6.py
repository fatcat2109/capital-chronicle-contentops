"""Backend tests for V6 Approval Packet Preview to Dispatch Outbox Dry Run."""
from __future__ import annotations

import json
from pathlib import Path
from live_contentops.approval_packet_preview_to_dispatch_outbox_dry_run_v6 import build_dry_run_package

ROOT = Path(__file__).resolve().parents[1]
PACKET_PATH = ROOT / "docs" / "automation" / "V6_APPROVAL_PACKET_PREVIEW_TO_DISPATCH_OUTBOX_DRY_RUN" / "approval_packet_preview_to_dispatch_outbox_dry_run_packet.json"


def test_dry_run_packet_creation_and_contents() -> None:
    packet = build_dry_run_package()
    assert packet["packet_kind"] == "approval_packet_preview_to_dispatch_outbox_dry_run_v0"
    assert packet["dispatch_outbox_dry_run_status"] == "dispatch_outbox_dry_run_created_for_operator_review"
    assert "dispatch_outbox_dry_run_packet_id" in packet
    assert packet["dispatch_outbox_dry_run_packet_id"].startswith("outbox_dry_run_")
    assert len(packet["exact_payload_hash"]) == 64
    assert packet["dry_run_outbox_package_created"] is True
    assert packet["dry_run_entries_created"] is True
    assert packet["executable_outbox_entry_created"] is False
    assert packet["real_outbox_entry_created"] is False
    assert packet["dispatch_outbox_ready"] is False
    assert packet["dispatch_attempted"] is False
    assert packet["dispatch_request_count"] == 0
    assert packet["webhook_request_count"] == 0
    assert packet["platform_api_request_count"] == 0
    assert packet["scheduler_enabled"] is False
    assert packet["retry_enabled"] is False
    assert packet["kill_switch_required"] is True
    assert packet["kill_switch_active"] is True
    assert packet["exact_payload_hashes_preserved"] is True
    assert packet["actual_operator_approval_recorded"] is False
    assert packet["approval_ledger_entry_created"] is False
    assert packet["approval_record_created"] is False
    assert packet["approval_signature_present"] is False
    assert packet["approval_signature_required"] is True
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

    entries = packet["dry_run_entries"]
    required_keys = [
        "substack_manual_dry_run_entry",
        "discord_webhook_dry_run_entry",
        "telegram_operator_dry_run_entry",
        "x_manual_dry_run_entry",
        "linkedin_deferred_dry_run_entry",
        "threads_manual_dry_run_entry",
        "facebook_manual_dry_run_entry",
        "instagram_deferred_dry_run_entry",
        "youtube_deferred_dry_run_entry",
        "tiktok_deferred_dry_run_entry",
    ]
    for key in required_keys:
        assert key in entries
        e = entries[key]
        assert e["executable"] is False
        assert e["dispatchable"] is False
        assert e["approved"] is False
        assert e["approval_required"] is True
        assert e["no_public_url_claim"] is True
        assert e["no_metrics_claim"] is True
        assert e["no_network_request_made"] is True
        assert e["no_secret_material_present"] is True
        assert len(e["dry_run_payload_text"]) > 0
        assert len(e["dry_run_payload_hash"]) > 0
        assert len(e["request_body_hash_preview"]) > 0


def test_dry_run_packet_file_saved_correctly() -> None:
    assert PACKET_PATH.exists()
    data = json.loads(PACKET_PATH.read_text(encoding="utf-8"))
    assert data["dispatch_outbox_dry_run_status"] == "dispatch_outbox_dry_run_created_for_operator_review"
    assert data["source_approval_preview_packet_id"] == "approval_preview_28f5ef142e404225"
    assert data["source_approval_preview_exact_payload_hash"] == "b02ec50b38399194d087d12c1e168ceef64fc527ddab1885517ca542f7a72678"
