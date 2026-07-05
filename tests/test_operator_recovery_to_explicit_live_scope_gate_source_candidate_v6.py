"""Backend tests for V6 Explicit Live Scope Gate Packet."""
from __future__ import annotations

import json
from pathlib import Path
from live_contentops.operator_recovery_to_explicit_live_scope_gate_source_candidate_v6 import build_gate_packet

ROOT = Path(__file__).resolve().parents[1]
PACKET_PATH = ROOT / "docs" / "automation" / "V6_OPERATOR_RECOVERY_TO_EXPLICIT_LIVE_SCOPE_GATE_SOURCE_CANDIDATE" / "operator_recovery_to_explicit_live_scope_gate_source_candidate_packet.json"


def test_gate_packet_contents() -> None:
    packet = build_gate_packet()
    assert packet["packet_kind"] == "operator_recovery_to_explicit_live_scope_gate_source_candidate_v0"
    assert packet["explicit_live_scope_gate_status"] == "created_for_operator_review"
    assert packet["source_intake_parser_created"] is True
    assert packet["normalized_dispatch_candidate_created"] is True
    assert packet["discord_live_scope_candidate_created"] is True
    assert packet["official_docs_evidence_created"] is True
    assert packet["endpoint_allowlist_created"] is True
    assert packet["credential_presence_check_performed"] is True
    assert packet["credential_value_read_made"] is False
    assert packet["env_value_read_made"] is False
    assert packet["credential_presence_key_names_only"] is True
    assert "DISCORD_LIVE_ANNOUNCEMENTS_WEBHOOK" in packet["credential_presence_states"]
    assert "DISCORD_LIVE_ANNOUNCEMENTS_CHANNEL_LABEL" in packet["credential_presence_states"]
    assert packet["destination_binding_status"] == "blocked_until_operator_confirms_destination"
    assert packet["executable_outbox_entry_created"] is False
    assert packet["real_outbox_entry_created"] is False
    assert packet["approval_ledger_entry_created"] is False
    assert packet["approval_signature_present"] is False
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
    assert packet["forbidden_financial_advice_or_signal_wording_present"] is False

    assert packet["source_operator_recovery_packet_id"] == "operator_recovery_e30e17729faebb93"
    assert packet["source_operator_recovery_exact_hash"] == "e30e17729faebb933a21045ac03b6e1be640aa33b8f4d424a06bbf79655d1fe2"


def test_gate_packet_file_saved() -> None:
    assert PACKET_PATH.exists()
    data = json.loads(PACKET_PATH.read_text(encoding="utf-8"))
    assert data["explicit_live_scope_gate_status"] == "created_for_operator_review"
    assert data["exact_payload_hash"] == "17d6a329de18bffac658ef7ea8849b66799317fefa9347316829977408ab9a3f"
