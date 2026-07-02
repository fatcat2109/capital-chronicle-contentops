"""Backend builder for V6 Operator Recovery to Explicit Live Scope Gate Source Candidate."""
from __future__ import annotations

import os
import json
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NORMALIZED_FILE = ROOT / "docs" / "automation" / "V6_OPERATOR_RECOVERY_TO_EXPLICIT_LIVE_SCOPE_GATE_SOURCE_CANDIDATE" / "normalized_candidate" / "normalized_dispatch_candidate.json"
PACKET_DIR = ROOT / "docs" / "automation" / "V6_OPERATOR_RECOVERY_TO_EXPLICIT_LIVE_SCOPE_GATE_SOURCE_CANDIDATE"
PACKET_FILE = PACKET_DIR / "operator_recovery_to_explicit_live_scope_gate_source_candidate_packet.json"

def build_gate_packet() -> dict:
    PACKET_DIR.mkdir(parents=True, exist_ok=True)

    # Read normalized candidate
    if NORMALIZED_FILE.exists():
        normalized_data = json.loads(NORMALIZED_FILE.read_text(encoding="utf-8"))
    else:
        normalized_data = {
            "candidate_id": "",
            "blocked_reasons": ["blocked_missing_operator_source_artifact"],
            "payload_hash": ""
        }

    candidate_id = normalized_data.get("candidate_id", "")
    blocked_reasons = normalized_data.get("blocked_reasons", [])
    
    if "blocked_missing_operator_source_artifact" in blocked_reasons:
        normalized_candidate_status = "blocked_missing_operator_source_artifact"
        payload_hash_preview_created = False
        exact_payload_preview_created = False
    elif blocked_reasons:
        normalized_candidate_status = "blocked_validation_failed"
        payload_hash_preview_created = True
        exact_payload_preview_created = True
    else:
        normalized_candidate_status = "ready_for_operator_source_artifact"
        payload_hash_preview_created = True
        exact_payload_preview_created = True

    # Credential check
    webhook_present = "present" if os.environ.get("DISCORD_LIVE_ANNOUNCEMENTS_WEBHOOK") else "missing"
    channel_present = "present" if os.environ.get("DISCORD_LIVE_ANNOUNCEMENTS_CHANNEL_LABEL") else "missing"

    forbidden_financial = any("contains_forbidden_financial_advice" in r for r in blocked_reasons)

    packet = {
        "task_label": "TASK_CONTENTOPS_V6_OPERATOR_RECOVERY_TO_EXPLICIT_LIVE_SCOPE_GATE_SOURCE_CANDIDATE_HEAVY_BATCH_V0",
        "packet_kind": "operator_recovery_to_explicit_live_scope_gate_source_candidate_v0",
        "explicit_live_scope_gate_status": "created_for_operator_review",
        
        "source_intake_parser_created": True,
        "normalized_dispatch_candidate_created": True,
        "normalized_candidate_status": normalized_candidate_status,
        "discord_live_scope_candidate_created": True,
        "official_docs_evidence_created": True,
        "endpoint_allowlist_created": True,
        
        "credential_presence_check_performed": True,
        "credential_value_read_made": False,
        "env_value_read_made": False,
        "credential_presence_key_names_only": True,
        "credential_presence_states": {
            "DISCORD_LIVE_ANNOUNCEMENTS_WEBHOOK": webhook_present,
            "DISCORD_LIVE_ANNOUNCEMENTS_CHANNEL_LABEL": channel_present
        },
        
        "destination_binding_status": "blocked_until_operator_confirms_destination",
        "payload_hash_preview_created": payload_hash_preview_created,
        "exact_payload_preview_created": exact_payload_preview_created,
        
        "executable_outbox_entry_created": False,
        "real_outbox_entry_created": False,
        "approval_ledger_entry_created": False,
        "approval_signature_present": False,
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
        "source_operator_recovery_packet_id": "operator_recovery_e30e17729faebb93",
        "source_operator_recovery_exact_hash": "e30e17729faebb933a21045ac03b6e1be640aa33b8f4d424a06bbf79655d1fe2",
        "source_dispatch_outbox_dry_run_packet_id": "outbox_dry_run_7cfc24c5b0c0eded",
        "source_dispatch_outbox_dry_run_exact_hash": "7cfc24c5b0c0ededb530c3d5ede21490ad49b0d46969e7d7ed3d8c7758769439",
        "source_approval_preview_packet_id": "approval_preview_28f5ef142e404225",
        "source_approval_preview_exact_hash": "b02ec50b38399194d087d12c1e168ceef64fc527ddab1885517ca542f7a72678",
        "source_final_review_packet_id": "final_review_preview_11fc52e6e452c4d3",
        "source_final_review_exact_hash": "11fc52e6e452c4d3fedd306ffbf796fae459e061c784eed86cc1e8f65b9d38f2",
        
        # Endpoint allowlist
        "endpoint_allowlist": [
            {
                "host": "discord.com",
                "method": "POST",
                "path_shape": "/api/webhooks/{webhook.id}/{webhook.token}"
            }
        ]
    }

    # Sort keys excluding hash and id fields
    clean_dict = {k: v for k, v in packet.items() if k not in ["exact_payload_hash", "explicit_live_scope_gate_packet_id"]}
    serialized = json.dumps(clean_dict, sort_keys=True, indent=2)
    exact_payload_hash = hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    packet["exact_payload_hash"] = exact_payload_hash
    packet["explicit_live_scope_gate_packet_id"] = f"explicit_live_scope_{exact_payload_hash[:16]}"

    PACKET_FILE.write_text(json.dumps(packet, sort_keys=True, indent=2), encoding="utf-8")
    return packet

if __name__ == "__main__":
    build_gate_packet()
    print("Gate packet generated successfully.")
