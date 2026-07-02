"""Fail-closed V6 Discord supervised live-dispatch dry-run gate builder.

Local scaffold only: no Discord send, no webhook validation, no executable outbox,
no approval ledger write, no scheduler, no retry, no provider call, no platform API,
and no credential/env value read.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TASK_LABEL = "TASK_CONTENTOPS_V6_OPERATOR_GO_PACKET_TO_SUPERVISED_DISCORD_LIVE_DISPATCH_DRY_RUN_GATE_HEAVY_BATCH_V0"
SOURCE_TASK_LABEL = "TASK_CONTENTOPS_V6_DISCORD_SUPERVISED_PREFLIGHT_TO_OPERATOR_GO_PACKET_HEAVY_BATCH_V0"
SOURCE_GO_PACKET_ID = "operator_go_c13b509858c9cf17"
SOURCE_GO_PACKET_HASH = "c13b509858c9cf175a3cc7d172b64aefd8230e5a1419bba7522569181d911f39"
DISCORD_DOCS_REFERENCE = "https://discord.com/developers/docs/resources/webhook#execute-webhook"

GO_PACKET_FILE = ROOT / "docs" / "automation" / "V6_DISCORD_OPERATOR_GO_PACKET" / "discord_operator_go_packet.json"
GATE_DIR = ROOT / "docs" / "automation" / "V6_DISCORD_SUPERVISED_LIVE_DISPATCH_DRY_RUN_GATE"
GATE_PACKET_FILE = GATE_DIR / "discord_supervised_live_dispatch_dry_run_gate_packet.json"
ENVELOPE_FILE = GATE_DIR / "dry_run_request_envelope_preview.json"
SAFETY_FILE = GATE_DIR / "dry_run_safety_signature.json"


def _sha(payload: dict[str, Any]) -> str:
    clone = dict(payload)
    clone.pop("exact_payload_hash", None)
    clone.pop("dry_run_gate_packet_id", None)
    clone.pop("dry_run_request_envelope_hash", None)
    clone.pop("dry_run_safety_signature_hash", None)
    return hashlib.sha256(json.dumps(clone, sort_keys=True, indent=2).encode("utf-8")).hexdigest()


def _load_json(path: Path, fallback: dict[str, Any]) -> dict[str, Any]:
    if not path.exists():
        return fallback
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"json_object_required:{path}")
    return data


def _presence(key: str) -> str:
    return "present" if key in os.environ else "missing"


def _blocked_reasons(go_packet: dict[str, Any], credential_presence: dict[str, str]) -> list[str]:
    reasons = list(go_packet.get("blocked_reasons") or [])
    if go_packet.get("operator_go_packet_id") != SOURCE_GO_PACKET_ID:
        reasons.append("source_operator_go_packet_id_mismatch")
    if go_packet.get("exact_payload_hash") != SOURCE_GO_PACKET_HASH:
        reasons.append("source_operator_go_packet_hash_mismatch")
    if go_packet.get("operator_go_packet_status") != "created_for_operator_review":
        reasons.append("source_operator_go_packet_status_invalid")
    if not go_packet.get("operator_go_source_artifact_path"):
        reasons.append("blocked_missing_operator_go_source_artifact")
    if not go_packet.get("operator_go_phrase_recorded"):
        reasons.append("blocked_operator_go_phrase_not_recorded")
    if not go_packet.get("operator_go_phrase_valid"):
        reasons.append("blocked_operator_go_phrase_not_valid")
    if go_packet.get("destination_binding_status") != "confirmed":
        reasons.append("blocked_destination_binding_not_confirmed")
    if credential_presence.get("DISCORD_LIVE_ANNOUNCEMENTS_WEBHOOK") != "present":
        reasons.append("blocked_webhook_key_missing")
    if credential_presence.get("DISCORD_LIVE_ANNOUNCEMENTS_CHANNEL_LABEL") != "present":
        reasons.append("blocked_channel_label_key_missing")
    if credential_presence.get("CONTENTOPS_LIVE_KILL_SWITCH") != "present":
        reasons.append("blocked_kill_switch_key_missing")
    if go_packet.get("kill_switch_active") is not True:
        reasons.append("blocked_kill_switch_not_active")
    if go_packet.get("ready_for_dispatch") is not False or go_packet.get("live_action_allowed") is not False:
        reasons.append("source_go_packet_live_gate_not_locked")
    return sorted(set(reasons))


def build_discord_supervised_live_dispatch_dry_run_gate() -> dict[str, Any]:
    GATE_DIR.mkdir(parents=True, exist_ok=True)
    go_packet = _load_json(GO_PACKET_FILE, {})
    credential_presence = {
        "DISCORD_LIVE_ANNOUNCEMENTS_WEBHOOK": _presence("DISCORD_LIVE_ANNOUNCEMENTS_WEBHOOK"),
        "DISCORD_LIVE_ANNOUNCEMENTS_CHANNEL_LABEL": _presence("DISCORD_LIVE_ANNOUNCEMENTS_CHANNEL_LABEL"),
        "CONTENTOPS_LIVE_KILL_SWITCH": _presence("CONTENTOPS_LIVE_KILL_SWITCH"),
    }
    blockers = _blocked_reasons(go_packet, credential_presence)

    envelope = {
        "envelope_kind": "discord_supervised_live_dispatch_dry_run_preview_v0",
        "non_executable_preview_only": True,
        "request_envelope_executable": False,
        "method_label": "POST",
        "host_label": "discord.com",
        "path_shape_label": "/api/webhooks/{webhook.id}/{webhook.token}",
        "webhook_token_redacted": True,
        "webhook_value_read_made": False,
        "webhook_validation_performed": False,
        "body_value_stored": False,
        "body_hash_source": "blocked_until_operator_go_source_artifact_and_exact_phrase_valid",
        "allowed_mentions_parse_empty": True,
        "dispatch_request_count": 0,
        "webhook_request_count": 0,
    }
    envelope["dry_run_request_envelope_hash"] = _sha(envelope)
    ENVELOPE_FILE.write_text(json.dumps(envelope, sort_keys=True, indent=2), encoding="utf-8")

    safety = {
        "safety_signature_kind": "discord_supervised_live_dispatch_dry_run_safety_signature_v0",
        "review_only": True,
        "source_operator_go_packet_id": SOURCE_GO_PACKET_ID,
        "source_operator_go_packet_hash": SOURCE_GO_PACKET_HASH,
        "request_envelope_executable": False,
        "executable_outbox_entry_created": False,
        "approval_ledger_entry_created": False,
        "webhook_validation_performed": False,
        "discord_api_call_made": False,
        "platform_api_call_made": False,
        "provider_call_made": False,
        "credential_value_read_made": False,
        "env_value_read_made": False,
        "ready_for_dispatch": False,
        "live_action_allowed": False,
        "blocked_reasons": blockers,
    }
    safety["dry_run_safety_signature_hash"] = _sha(safety)
    SAFETY_FILE.write_text(json.dumps(safety, sort_keys=True, indent=2), encoding="utf-8")

    packet = {
        "task_label": TASK_LABEL,
        "packet_kind": "discord_supervised_live_dispatch_dry_run_gate_v0",
        "dry_run_gate_status": "blocked",
        "source_task_label": SOURCE_TASK_LABEL,
        "source_operator_go_packet_id": SOURCE_GO_PACKET_ID,
        "source_operator_go_packet_exact_payload_hash": SOURCE_GO_PACKET_HASH,
        "source_operator_go_packet_path": "docs/automation/V6_DISCORD_OPERATOR_GO_PACKET/discord_operator_go_packet.json",
        "source_operator_go_packet_status": go_packet.get("operator_go_packet_status", "missing"),
        "source_operator_go_phrase_required": bool(go_packet.get("operator_go_phrase_required")),
        "source_operator_go_phrase_recorded": bool(go_packet.get("operator_go_phrase_recorded")),
        "source_operator_go_phrase_valid": bool(go_packet.get("operator_go_phrase_valid")),
        "source_destination_binding_status": go_packet.get("destination_binding_status", "missing"),
        "discord_official_docs_reference": DISCORD_DOCS_REFERENCE,
        "official_docs_reference_read_for_shape_only": True,
        "dry_run_request_envelope_preview_created": True,
        "dry_run_request_envelope_hash": envelope["dry_run_request_envelope_hash"],
        "dry_run_safety_signature_created": True,
        "dry_run_safety_signature_hash": safety["dry_run_safety_signature_hash"],
        "credential_presence_check_performed": True,
        "credential_presence_key_names_only": True,
        "credential_presence_states": credential_presence,
        "credential_value_read_made": False,
        "env_value_read_made": False,
        "webhook_url_value_read_made": False,
        "webhook_validation_performed": False,
        "request_envelope_executable": False,
        "approval_ledger_entry_created": False,
        "executable_outbox_entry_created": False,
        "real_outbox_entry_created": False,
        "dispatch_outbox_ready": False,
        "dispatch_attempted": False,
        "dispatch_request_count": 0,
        "webhook_request_count": 0,
        "platform_api_request_count": 0,
        "scheduler_enabled": False,
        "retry_enabled": False,
        "kill_switch_required": True,
        "kill_switch_active": True,
        "ready_for_auto_publish": False,
        "ready_for_dispatch": False,
        "live_action_allowed": False,
        "public_url_verification_performed": False,
        "llm_provider_call_made": False,
        "provider_call_made": False,
        "platform_api_used": False,
        "public_url_fetch_made": False,
        "browser_session_used": False,
        "live_publish_performed_by_contentops": False,
        "enabled_publish_send_dispatch_approve_controls": False,
        "blocked_reasons": blockers,
    }
    packet["exact_payload_hash"] = _sha(packet)
    packet["dry_run_gate_packet_id"] = f"discord_dry_run_gate_{packet['exact_payload_hash'][:16]}"
    GATE_PACKET_FILE.write_text(json.dumps(packet, sort_keys=True, indent=2), encoding="utf-8")
    return packet


if __name__ == "__main__":
    build_discord_supervised_live_dispatch_dry_run_gate()
    print("Discord supervised live-dispatch dry-run gate generated successfully.")
