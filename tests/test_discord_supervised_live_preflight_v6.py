"""Backend preflight tests for V6 Discord Supervised Live Preflight."""
from __future__ import annotations

import json
from pathlib import Path
from live_contentops.discord_supervised_live_preflight_v6 import build_preflight_packet

ROOT = Path(__file__).resolve().parents[1]
PACKET_PATH = ROOT / "docs" / "automation" / "V6_DISCORD_SUPERVISED_LIVE_PREFLIGHT" / "discord_supervised_live_preflight_packet.json"
ENVELOPE_PATH = ROOT / "docs" / "automation" / "V6_DISCORD_SUPERVISED_LIVE_PREFLIGHT" / "request_envelope_preview.json"
GO_PHRASE_PATH = ROOT / "docs" / "automation" / "V6_DISCORD_SUPERVISED_LIVE_PREFLIGHT" / "operator_live_go_phrase.txt"


def test_preflight_packet_contents() -> None:
    packet = build_preflight_packet()
    assert packet["packet_kind"] == "discord_supervised_live_preflight_v0"
    assert packet["supervised_live_preflight_status"] == "created_for_operator_review"
    assert packet["normalized_discord_payload_candidate_created"] is True
    assert packet["request_envelope_preview_created"] is True
    assert packet["request_envelope_executable"] is False
    assert packet["request_method_preview"] == "POST"
    assert packet["endpoint_allowlist_host"] == "discord.com"
    assert packet["endpoint_allowlist_path_shape"] == "/api/webhooks/{webhook.id}/{webhook.token}"
    assert packet["endpoint_token_redacted"] is True
    assert packet["webhook_url_value_read_made"] is False
    assert packet["credential_presence_check_performed"] is True
    assert packet["credential_presence_key_names_only"] is True
    assert packet["credential_value_read_made"] is False
    assert packet["env_value_read_made"] is False
    
    assert "DISCORD_LIVE_ANNOUNCEMENTS_WEBHOOK" in packet["credential_presence_states"]
    assert "DISCORD_LIVE_ANNOUNCEMENTS_CHANNEL_LABEL" in packet["credential_presence_states"]
    assert "CONTENTOPS_LIVE_KILL_SWITCH" in packet["credential_presence_states"]
    
    assert packet["operator_go_phrase_required"] is True
    assert packet["operator_go_phrase_recorded"] is False
    assert packet["approval_signature_present"] is False
    assert packet["approval_ledger_entry_created"] is False
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
    assert packet["ready_for_auto_publish"] is False
    assert packet["ready_for_dispatch"] is False
    assert packet["live_action_allowed"] is False
    assert packet["public_url_verification_performed"] is False
    assert packet["llm_provider_call_made"] is False
    assert packet["provider_call_made"] is False
    assert packet["platform_api_used"] is False
    assert packet["public_url_fetch_made"] is False
    assert packet["browser_session_used"] is False
    assert packet["live_publish_performed_by_contentops"] is False
    assert packet["enabled_publish_send_dispatch_approve_controls"] is False

    assert packet["source_explicit_live_scope_gate_packet_id"] == "explicit_live_scope_cc1a6320629a1ee0"
    assert packet["source_explicit_live_scope_gate_exact_payload_hash"] == "cc1a6320629a1ee0548afc8c8719116c5d20b282b4f00318b87047e7b7e6aeb8"


def test_files_exist() -> None:
    assert PACKET_PATH.exists()
    assert ENVELOPE_PATH.exists()
    assert GO_PHRASE_PATH.exists()

    env_data = json.loads(ENVELOPE_PATH.read_text(encoding="utf-8"))
    assert env_data["host"] == "discord.com"
    assert env_data["method"] == "POST"
    assert env_data["path_shape"] == "/api/webhooks/{webhook.id}/{webhook.token}"
    assert env_data["body_hash_preview"] == "blocked_no_payload_hash"
    
    go_phrase = GO_PHRASE_PATH.read_text(encoding="utf-8").strip()
    assert go_phrase == "CAPITAL_CHRONICLE_SUPERVISED_DISCORD_PILOT_VERIFIED_GO_PHRASE_2026"
