"""Review-only V6 Discord Operator GO Packet builder.

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
TASK_LABEL = "TASK_CONTENTOPS_V6_DISCORD_SUPERVISED_PREFLIGHT_TO_OPERATOR_GO_PACKET_HEAVY_BATCH_V0"
SOURCE_TASK_LABEL = "TASK_CONTENTOPS_V6_EXPLICIT_LIVE_SCOPE_GATE_TO_DISCORD_SUPERVISED_LIVE_PREFLIGHT_HEAVY_BATCH_V0"
SOURCE_PREFLIGHT_PACKET_ID = "supervised_preflight_ef5371b837e94bd4"
SOURCE_PREFLIGHT_EXACT_PAYLOAD_HASH = "ef5371b837e94bd46030d91af3b2946a39a6e0466d076e6974d82c87e554cb25"
GO_PHRASE = "CAPITAL_CHRONICLE_SUPERVISED_DISCORD_PILOT_VERIFIED_GO_PHRASE_2026"

PREFLIGHT_PACKET_FILE = ROOT / "docs" / "automation" / "V6_DISCORD_SUPERVISED_LIVE_PREFLIGHT" / "discord_supervised_live_preflight_packet.json"
GO_PACKET_DIR = ROOT / "docs" / "automation" / "V6_DISCORD_OPERATOR_GO_PACKET"
GO_INBOX_DIR = GO_PACKET_DIR / "inbox"
GO_NORMALIZED_FILE = GO_PACKET_DIR / "normalized_candidate" / "normalized_operator_go_source_candidate.json"
GO_PACKET_FILE = GO_PACKET_DIR / "discord_operator_go_packet.json"
GO_PHRASE_VALIDATION_FILE = GO_PACKET_DIR / "operator_go_phrase_validation_model.json"
SAFETY_SIGNATURE_FILE = GO_PACKET_DIR / "safety_signature_preview.json"


def _sha(payload: dict[str, Any]) -> str:
    clone = dict(payload)
    clone.pop("exact_payload_hash", None)
    clone.pop("operator_go_packet_id", None)
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


def build_operator_go_packet() -> dict[str, Any]:
    GO_PACKET_DIR.mkdir(parents=True, exist_ok=True)
    GO_INBOX_DIR.mkdir(parents=True, exist_ok=True)
    GO_NORMALIZED_FILE.parent.mkdir(parents=True, exist_ok=True)

    preflight = _load_json(PREFLIGHT_PACKET_FILE, {})
    source = _load_json(
        GO_NORMALIZED_FILE,
        {
            "candidate_id": "",
            "source_artifact_path": "",
            "source_artifact_hash": "",
            "normalized_body_text": "",
            "blocked_reasons": ["blocked_missing_operator_go_source_artifact"],
            "safety_scan": "pending",
            "payload_hash": "",
        },
    )
    blocked_reasons = list(source.get("blocked_reasons") or [])
    if not source.get("candidate_id"):
        blocked_reasons.append("blocked_missing_operator_go_source_artifact")
    if preflight.get("supervised_live_preflight_packet_id") != SOURCE_PREFLIGHT_PACKET_ID:
        blocked_reasons.append("source_preflight_packet_id_mismatch")
    if preflight.get("exact_payload_hash") != SOURCE_PREFLIGHT_EXACT_PAYLOAD_HASH:
        blocked_reasons.append("source_preflight_hash_mismatch")
    if preflight.get("ready_for_dispatch") is not False or preflight.get("live_action_allowed") is not False:
        blocked_reasons.append("source_preflight_live_gate_not_locked")

    phrase_model = {
        "operator_go_phrase_required": True,
        "operator_go_phrase_recorded": False,
        "operator_go_phrase_exact_match_required": True,
        "operator_go_phrase_expected_hash": hashlib.sha256(GO_PHRASE.encode("utf-8")).hexdigest(),
        "operator_go_phrase_value_stored": False,
        "operator_go_phrase_value_logged": False,
        "operator_go_phrase_valid": False,
        "validation_scope": "review_only_model_no_live_send",
    }
    phrase_model["validation_model_hash"] = _sha(phrase_model)
    GO_PHRASE_VALIDATION_FILE.write_text(json.dumps(phrase_model, sort_keys=True, indent=2), encoding="utf-8")

    safety_signature = {
        "review_only": True,
        "source_preflight_hash": SOURCE_PREFLIGHT_EXACT_PAYLOAD_HASH,
        "operator_source_payload_hash": source.get("payload_hash", ""),
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
        "blocked_reasons": sorted(set(blocked_reasons)),
    }
    safety_signature["safety_signature_hash"] = _sha(safety_signature)
    SAFETY_SIGNATURE_FILE.write_text(json.dumps(safety_signature, sort_keys=True, indent=2), encoding="utf-8")

    packet = {
        "task_label": TASK_LABEL,
        "packet_kind": "discord_operator_go_packet_v0",
        "operator_go_packet_status": "created_for_operator_review",
        "source_task_label": SOURCE_TASK_LABEL,
        "source_supervised_live_preflight_packet_id": SOURCE_PREFLIGHT_PACKET_ID,
        "source_supervised_live_preflight_exact_payload_hash": SOURCE_PREFLIGHT_EXACT_PAYLOAD_HASH,
        "source_preflight_packet_path": "docs/automation/V6_DISCORD_SUPERVISED_LIVE_PREFLIGHT/discord_supervised_live_preflight_packet.json",
        "source_candidate_status": source.get("safety_scan", "pending"),
        "operator_go_source_candidate_id": source.get("candidate_id", ""),
        "operator_go_source_candidate_hash": source.get("payload_hash", ""),
        "operator_go_source_artifact_path": source.get("source_artifact_path", ""),
        "operator_go_source_artifact_hash": source.get("source_artifact_hash", ""),
        "operator_go_phrase_validation_model_created": True,
        "operator_go_phrase_required": True,
        "operator_go_phrase_recorded": False,
        "operator_go_phrase_valid": False,
        "operator_go_phrase_value_stored": False,
        "safety_signature_preview_created": True,
        "safety_signature_hash": safety_signature["safety_signature_hash"],
        "destination_binding_status": "blocked_until_operator_confirms_destination",
        "credential_presence_check_performed": True,
        "credential_presence_key_names_only": True,
        "credential_presence_states": {
            "DISCORD_LIVE_ANNOUNCEMENTS_WEBHOOK": _presence("DISCORD_LIVE_ANNOUNCEMENTS_WEBHOOK"),
            "DISCORD_LIVE_ANNOUNCEMENTS_CHANNEL_LABEL": _presence("DISCORD_LIVE_ANNOUNCEMENTS_CHANNEL_LABEL"),
            "CONTENTOPS_LIVE_KILL_SWITCH": _presence("CONTENTOPS_LIVE_KILL_SWITCH"),
        },
        "credential_value_read_made": False,
        "env_value_read_made": False,
        "webhook_validation_performed": False,
        "webhook_url_value_read_made": False,
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
        "blocked_reasons": sorted(set(blocked_reasons)),
    }
    packet["exact_payload_hash"] = _sha(packet)
    packet["operator_go_packet_id"] = f"operator_go_{packet['exact_payload_hash'][:16]}"
    GO_PACKET_FILE.write_text(json.dumps(packet, sort_keys=True, indent=2), encoding="utf-8")
    return packet


if __name__ == "__main__":
    build_operator_go_packet()
    print("Operator GO packet generated successfully.")
