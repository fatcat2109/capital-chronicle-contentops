"""Tests for V6 Discord supervised live-dispatch dry-run gate."""
from __future__ import annotations

import json
import re
from pathlib import Path

from live_contentops.discord_supervised_live_dispatch_dry_run_gate_v5_adapter_codegen_v6 import (
    generate_dry_run_gate_adapter,
)
from live_contentops.discord_supervised_live_dispatch_dry_run_gate_v6 import (
    build_discord_supervised_live_dispatch_dry_run_gate,
)

ROOT = Path(__file__).resolve().parents[1]
PACKET_DIR = ROOT / "docs" / "automation" / "V6_DISCORD_SUPERVISED_LIVE_DISPATCH_DRY_RUN_GATE"
PACKET = PACKET_DIR / "discord_supervised_live_dispatch_dry_run_gate_packet.json"
ENVELOPE = PACKET_DIR / "dry_run_request_envelope_preview.json"
SAFETY = PACKET_DIR / "dry_run_safety_signature.json"
ADAPTER = ROOT / "ui" / "contentops_v5" / "src" / "data" / "discordSupervisedLiveDispatchDryRunGateAdapter.ts"
SURFACES = [
    ROOT / "ui" / "contentops_v5" / "src" / "views" / "ApprovalQueue.tsx",
    ROOT / "ui" / "contentops_v5" / "src" / "views" / "PlatformPreview.tsx",
    ROOT / "ui" / "contentops_v5" / "src" / "views" / "PreflightBundle.tsx",
    ROOT / "ui" / "contentops_v5" / "src" / "views" / "EvidenceVault.tsx",
    ROOT / "ui" / "contentops_v5" / "src" / "views" / "ManualExportPilotVerification.tsx",
]


def _compact(path: Path) -> str:
    return re.sub(r"\s+", "", path.read_text(encoding="utf-8").lower())


def test_dry_run_gate_packet_fail_closed() -> None:
    packet = build_discord_supervised_live_dispatch_dry_run_gate()
    stored = json.loads(PACKET.read_text(encoding="utf-8"))
    envelope = json.loads(ENVELOPE.read_text(encoding="utf-8"))
    safety = json.loads(SAFETY.read_text(encoding="utf-8"))

    assert stored == packet
    assert packet["packet_kind"] == "discord_supervised_live_dispatch_dry_run_gate_v0"
    assert packet["dry_run_gate_status"] == "blocked"
    assert packet["credential_presence_key_names_only"] is True
    assert packet["credential_presence_check_performed"] is True
    for key in [
        "webhook_url_value_read_made",
        "webhook_validation_performed",
        "request_envelope_executable",
        "approval_ledger_entry_created",
        "executable_outbox_entry_created",
        "real_outbox_entry_created",
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
        "live_publish_performed_by_contentops",
        "enabled_publish_send_dispatch_approve_controls",
    ]:
        assert packet[key] is False
    assert packet["dispatch_request_count"] == 0
    assert packet["webhook_request_count"] == 0
    assert packet["platform_api_request_count"] == 0
    assert envelope["request_envelope_executable"] is False
    assert envelope["webhook_value_read_made"] is False
    assert envelope["webhook_request_count"] == 0
    assert safety["discord_api_call_made"] is False
    assert safety["platform_api_call_made"] is False
    assert safety["provider_call_made"] is False


def test_dry_run_gate_adapter_sync() -> None:
    assert generate_dry_run_gate_adapter(verify_only=True) == {"adapter_in_sync": True, "packet_hash_matches": True}
    text = ADAPTER.read_text(encoding="utf-8")
    assert "discordSupervisedLiveDispatchDryRunGatePacket" in text
    assert "discordDryRunRequestEnvelopePreview" in text
    assert "discordDryRunSafetySignature" in text
    assert "DISCORD_LIVE_ANNOUNCEMENTS_WEBHOOK" in text
    assert "webhook.id}/{webhook.token}" in text


def test_dry_run_gate_ui_surfaces_guardrails() -> None:
    terms = [
        "dry_run_gate_status=blocked",
        "request_envelope_executable=false",
        "dispatch_attempted=false",
        "dispatch_request_count=0",
        "webhook_request_count=0",
        "ready_for_dispatch=false",
        "live_action_allowed=false",
        "credential_value_read_made=false",
        "env_value_read_made=false",
    ]
    combined = "\n".join(_compact(path) for path in SURFACES)
    for term in terms:
        assert re.sub(r"\s+", "", term.lower()) in combined
    for path in SURFACES:
        compact = _compact(path)
        assert "discordsupervisedlivedispatchdryrungateadapter" in compact
        assert "v6discordsupervisedlive-dispatchdry-rungate" in compact
        assert "href=\"http" not in path.read_text(encoding="utf-8")
