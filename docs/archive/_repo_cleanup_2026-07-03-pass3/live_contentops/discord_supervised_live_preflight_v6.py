"""Backend preflight builder for V6 Discord Supervised Live Preflight."""
from __future__ import annotations

import os
import json
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NORMALIZED_FILE = ROOT / "docs" / "automation" / "V6_DISCORD_SUPERVISED_LIVE_PREFLIGHT" / "normalized_candidate" / "normalized_discord_payload_candidate.json"
PREFLIGHT_DIR = ROOT / "docs" / "automation" / "V6_DISCORD_SUPERVISED_LIVE_PREFLIGHT"
PREFLIGHT_PACKET_FILE = PREFLIGHT_DIR / "discord_supervised_live_preflight_packet.json"
ENVELOPE_FILE = PREFLIGHT_DIR / "request_envelope_preview.json"
GO_PHRASE_FILE = PREFLIGHT_DIR / "operator_live_go_phrase.txt"

def build_preflight_packet() -> dict:
    PREFLIGHT_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Read normalized candidate
    if NORMALIZED_FILE.exists():
        normalized_data = json.loads(NORMALIZED_FILE.read_text(encoding="utf-8"))
    else:
        normalized_data = {
            "candidate_id": "",
            "blocked_reasons": ["blocked_missing_operator_source_artifact"],
            "payload_hash": "",
            "content_length": 0,
            "request_body_hash_preview": None
        }

    candidate_id = normalized_data.get("candidate_id", "")
    blocked_reasons = normalized_data.get("blocked_reasons", [])
    body_hash_preview = normalized_data.get("request_body_hash_preview", None)
    content_length = normalized_data.get("content_length", 0)
    payload_hash = normalized_data.get("payload_hash", "")

    if "blocked_missing_operator_source_artifact" in blocked_reasons:
        source_candidate_status = "blocked_missing_operator_source_artifact"
        payload_hash_preview_created = False
        exact_payload_preview_created = False
    elif blocked_reasons:
        source_candidate_status = "blocked_validation_failed"
        payload_hash_preview_created = True
        exact_payload_preview_created = True
    else:
        source_candidate_status = "ready_if_operator_source_valid_else_blocked"
        payload_hash_preview_created = True
        exact_payload_preview_created = True

    # 2. Write Go Phrase File
    go_phrase = "CAPITAL_CHRONICLE_SUPERVISED_DISCORD_PILOT_VERIFIED_GO_PHRASE_2026"
    GO_PHRASE_FILE.write_text(go_phrase, encoding="utf-8")

    # 3. Write Request Envelope Preview
    envelope = {
        "host": "discord.com",
        "method": "POST",
        "path_shape": "/api/webhooks/{webhook.id}/{webhook.token}",
        "body_hash_preview": body_hash_preview if body_hash_preview else "blocked_no_payload_hash",
        "allowed_mentions": {
            "parse": []
        },
        "content_length": content_length,
        "payload_hash_preview": payload_hash if payload_hash else "None"
    }
    ENVELOPE_FILE.write_text(json.dumps(envelope, sort_keys=True, indent=2), encoding="utf-8")

    # 4. Check credentialspresence
    webhook_present = "present" if os.environ.get("DISCORD_LIVE_ANNOUNCEMENTS_WEBHOOK") else "missing"
    channel_present = "present" if os.environ.get("DISCORD_LIVE_ANNOUNCEMENTS_CHANNEL_LABEL") else "missing"
    kill_switch_present = "present" if os.environ.get("CONTENTOPS_LIVE_KILL_SWITCH") else "missing"

    forbidden_financial = any("contains_forbidden_financial_advice" in r for r in blocked_reasons)

    packet = {
        "task_label": "TASK_CONTENTOPS_V6_EXPLICIT_LIVE_SCOPE_GATE_TO_DISCORD_SUPERVISED_LIVE_PREFLIGHT_HEAVY_BATCH_V0",
        "packet_kind": "discord_supervised_live_preflight_v0",
        "supervised_live_preflight_status": "created_for_operator_review",
        "discord_platform_family": "discord",
        "source_candidate_status": source_candidate_status,
        
        "normalized_discord_payload_candidate_created": True,
        "request_envelope_preview_created": True,
        "request_envelope_executable": False,
        "request_method_preview": "POST",
        "endpoint_allowlist_host": "discord.com",
        "endpoint_allowlist_path_shape": "/api/webhooks/{webhook.id}/{webhook.token}",
        "endpoint_token_redacted": True,
        "webhook_url_value_read_made": False,
        
        "credential_presence_check_performed": True,
        "credential_presence_key_names_only": True,
        "credential_value_read_made": False,
        "env_value_read_made": False,
        
        "credential_presence_states": {
            "DISCORD_LIVE_ANNOUNCEMENTS_WEBHOOK": webhook_present,
            "DISCORD_LIVE_ANNOUNCEMENTS_CHANNEL_LABEL": channel_present,
            "CONTENTOPS_LIVE_KILL_SWITCH": kill_switch_present
        },
        
        "destination_binding_status": "blocked_until_operator_confirms_destination",
        "payload_hash_preview_created": payload_hash_preview_created,
        "exact_payload_preview_created": exact_payload_preview_created,
        
        "operator_go_phrase_required": True,
        "operator_go_phrase_recorded": False,
        
        "approval_signature_present": False,
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
        "forbidden_financial_advice_or_signal_wording_present": forbidden_financial,

        # Known source values
        "source_explicit_live_scope_gate_packet_id": "explicit_live_scope_cc1a6320629a1ee0",
        "source_explicit_live_scope_gate_exact_payload_hash": "cc1a6320629a1ee0548afc8c8719116c5d20b282b4f00318b87047e7b7e6aeb8",
        "source_operator_recovery_packet_id": "operator_recovery_e30e17729faebb93",
        "source_operator_recovery_exact_hash": "e30e17729faebb933a21045ac03b6e1be640aa33b8f4d424a06bbf79655d1fe2",
        "source_dispatch_outbox_dry_run_packet_id": "outbox_dry_run_7cfc24c5b0c0eded",
        "source_dispatch_outbox_dry_run_exact_hash": "7cfc24c5b0c0ededb530c3d5ede21490ad49b0d46969e7d7ed3d8c7758769439"
    }

    # Sort keys excluding hash and id fields
    clean_dict = {k: v for k, v in packet.items() if k not in ["exact_payload_hash", "supervised_live_preflight_packet_id"]}
    serialized = json.dumps(clean_dict, sort_keys=True, indent=2)
    exact_payload_hash = hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    packet["exact_payload_hash"] = exact_payload_hash
    packet["supervised_live_preflight_packet_id"] = f"supervised_preflight_{exact_payload_hash[:16]}"

    PREFLIGHT_PACKET_FILE.write_text(json.dumps(packet, sort_keys=True, indent=2), encoding="utf-8")
    return packet

if __name__ == "__main__":
    build_preflight_packet()
    print("Preflight packet generated successfully.")
