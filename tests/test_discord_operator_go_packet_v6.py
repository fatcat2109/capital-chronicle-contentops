"""Tests for V6 Discord Operator GO Packet scaffold."""
from __future__ import annotations

import json
import re
from pathlib import Path

from live_contentops.discord_operator_go_packet_v5_adapter_codegen_v6 import generate_operator_go_adapter
from live_contentops.discord_operator_go_packet_v6 import build_operator_go_packet

ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "docs" / "automation" / "V6_DISCORD_OPERATOR_GO_PACKET" / "discord_operator_go_packet.json"
ADAPTER = ROOT / "ui" / "contentops_v5" / "src" / "data" / "discordOperatorGoPacketAdapter.ts"
SURFACES = [
    ROOT / "ui" / "contentops_v5" / "src" / "views" / "ApprovalQueue.tsx",
    ROOT / "ui" / "contentops_v5" / "src" / "views" / "PlatformPreview.tsx",
    ROOT / "ui" / "contentops_v5" / "src" / "views" / "PreflightBundle.tsx",
    ROOT / "ui" / "contentops_v5" / "src" / "views" / "EvidenceVault.tsx",
    ROOT / "ui" / "contentops_v5" / "src" / "views" / "ManualExportPilotVerification.tsx",
]


def _compact(path: Path) -> str:
    return re.sub(r"\s+", "", path.read_text(encoding="utf-8").lower())


def test_operator_go_packet_fail_closed() -> None:
    packet = build_operator_go_packet()
    stored = json.loads(PACKET.read_text(encoding="utf-8"))
    assert stored == packet
    assert packet["packet_kind"] == "discord_operator_go_packet_v0"
    assert packet["operator_go_packet_status"] == "created_for_operator_review"
    for key in [
        "webhook_validation_performed",
        "request_envelope_executable",
        "approval_ledger_entry_created",
        "executable_outbox_entry_created",
        "dispatch_outbox_ready",
        "dispatch_attempted",
        "ready_for_dispatch",
        "live_action_allowed",
        "credential_value_read_made",
        "env_value_read_made",
        "llm_provider_call_made",
        "provider_call_made",
        "platform_api_used",
        "public_url_fetch_made",
        "browser_session_used",
    ]:
        assert packet[key] is False
    assert packet["dispatch_request_count"] == 0
    assert packet["webhook_request_count"] == 0
    assert packet["operator_go_phrase_required"] is True
    assert packet["operator_go_phrase_recorded"] is False
    assert packet["operator_go_phrase_valid"] is False


def test_operator_go_adapter_sync() -> None:
    assert generate_operator_go_adapter(verify_only=True) == {"adapter_in_sync": True, "packet_hash_matches": True}
    text = ADAPTER.read_text(encoding="utf-8")
    assert "discordOperatorGoPacket" in text
    assert "operatorGoPhraseValidationModel" in text
    assert "operatorGoSafetySignaturePreview" in text


def test_operator_go_ui_surfaces_guardrails() -> None:
    terms = [
        "operator_go_packet_status=created_for_operator_review",
        "webhook_validation_performed=false",
        "request_envelope_executable=false",
        "approval_ledger_entry_created=false",
        "executable_outbox_entry_created=false",
        "operator_go_phrase_required=true",
        "operator_go_phrase_recorded=false",
        "operator_go_phrase_valid=false",
        "credential_value_read_made=false",
        "env_value_read_made=false",
        "dispatch_request_count=0",
        "webhook_request_count=0",
        "ready_for_dispatch=false",
        "live_action_allowed=false",
    ]
    combined = "\n".join(_compact(path) for path in SURFACES)
    for term in terms:
        assert re.sub(r"\s+", "", term.lower()) in combined
    for path in SURFACES:
        assert "discordoperatorgopacketadapter" in _compact(path)
        assert "href=\"http" not in path.read_text(encoding="utf-8")
