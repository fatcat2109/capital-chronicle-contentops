"""Codegen script to generate V5 TypeScript adapter for V6 Discord Supervised Live Preflight."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PREFLIGHT_PACKET_FILE = ROOT / "docs" / "automation" / "V6_DISCORD_SUPERVISED_LIVE_PREFLIGHT" / "discord_supervised_live_preflight_packet.json"
NORMALIZED_FILE = ROOT / "docs" / "automation" / "V6_DISCORD_SUPERVISED_LIVE_PREFLIGHT" / "normalized_candidate" / "normalized_discord_payload_candidate.json"
ENVELOPE_FILE = ROOT / "docs" / "automation" / "V6_DISCORD_SUPERVISED_LIVE_PREFLIGHT" / "request_envelope_preview.json"
GO_PHRASE_FILE = ROOT / "docs" / "automation" / "V6_DISCORD_SUPERVISED_LIVE_PREFLIGHT" / "operator_live_go_phrase.txt"
TS_ADAPTER_FILE = ROOT / "ui" / "contentops_v5" / "src" / "data" / "discordSupervisedLivePreflightAdapter.ts"

def generate_preflight_adapter(verify_only: bool = False) -> dict:
    if not PREFLIGHT_PACKET_FILE.exists():
        raise FileNotFoundError(f"Preflight packet file missing: {PREFLIGHT_PACKET_FILE}")
    if not NORMALIZED_FILE.exists():
        raise FileNotFoundError(f"Normalized candidate file missing: {NORMALIZED_FILE}")
    if not ENVELOPE_FILE.exists():
        raise FileNotFoundError(f"Envelope file missing: {ENVELOPE_FILE}")
    if not GO_PHRASE_FILE.exists():
        raise FileNotFoundError(f"Go phrase file missing: {GO_PHRASE_FILE}")

    preflight_data = json.loads(PREFLIGHT_PACKET_FILE.read_text(encoding="utf-8"))
    normalized_data = json.loads(NORMALIZED_FILE.read_text(encoding="utf-8"))
    envelope_data = json.loads(ENVELOPE_FILE.read_text(encoding="utf-8"))
    go_phrase = GO_PHRASE_FILE.read_text(encoding="utf-8").strip()

    typescript_code = f"""// Capital Chronicle ContentOps V5 — Discord Supervised Live Preflight Adapter.
// Generated from local preflight schema configurations. Do not manually edit.

export interface DiscordSupervisedLivePreflightPacket {{
  task_label: string;
  packet_kind: string;
  supervised_live_preflight_packet_id: string;
  exact_payload_hash: string;
  supervised_live_preflight_status: string;
  discord_platform_family: string;
  source_candidate_status: string;
  
  normalized_discord_payload_candidate_created: boolean;
  request_envelope_preview_created: boolean;
  request_envelope_executable: boolean;
  request_method_preview: string;
  endpoint_allowlist_host: string;
  endpoint_allowlist_path_shape: string;
  endpoint_token_redacted: boolean;
  webhook_url_value_read_made: boolean;
  
  credential_presence_check_performed: boolean;
  credential_presence_key_names_only: boolean;
  credential_value_read_made: boolean;
  env_value_read_made: boolean;
  credential_presence_states: {{
    DISCORD_LIVE_ANNOUNCEMENTS_WEBHOOK: string;
    DISCORD_LIVE_ANNOUNCEMENTS_CHANNEL_LABEL: string;
    CONTENTOPS_LIVE_KILL_SWITCH: string;
  }};
  
  destination_binding_status: string;
  payload_hash_preview_created: boolean;
  exact_payload_preview_created: boolean;
  
  operator_go_phrase_required: boolean;
  operator_go_phrase_recorded: boolean;
  
  approval_signature_present: boolean;
  approval_ledger_entry_created: boolean;
  executable_outbox_entry_created: boolean;
  real_outbox_entry_created: boolean;
  
  dispatch_outbox_ready: boolean;
  dispatch_attempted: boolean;
  dispatch_request_count: number;
  webhook_request_count: number;
  platform_api_request_count: number;
  scheduler_enabled: boolean;
  retry_enabled: boolean;
  kill_switch_required: boolean;
  kill_switch_active: boolean;
  ready_for_auto_publish: boolean;
  ready_for_dispatch: boolean;
  live_action_allowed: boolean;
  public_url_verification_performed: boolean;
  llm_provider_call_made: boolean;
  provider_call_made: boolean;
  platform_api_used: boolean;
  public_url_fetch_made: boolean;
  browser_session_used: boolean;
  live_publish_performed_by_contentops: boolean;
  enabled_publish_send_dispatch_approve_controls: boolean;
  forbidden_financial_advice_or_signal_wording_present: boolean;

  source_explicit_live_scope_gate_packet_id: string;
  source_explicit_live_scope_gate_exact_payload_hash: string;
  source_operator_recovery_packet_id: string;
  source_operator_recovery_exact_hash: string;
  source_dispatch_outbox_dry_run_packet_id: string;
  source_dispatch_outbox_dry_run_exact_hash: string;
}}

export interface RequestEnvelopePreview {{
  host: string;
  method: string;
  path_shape: string;
  body_hash_preview: string;
  allowed_mentions: {{
    parse: string[];
  }};
  content_length: number;
  payload_hash_preview: string;
}}

export interface NormalizedDiscordPayloadCandidate {{
  candidate_id: string;
  source_artifact_path: string;
  source_artifact_hash: string;
  platform_family: string;
  content_length: number;
  content_type: string;
  operator_destination_label: string;
  normalized_body_text: string;
  payload_hash: string;
  request_body_hash_preview: string | null;
  safety_scan: string;
  blocked_reasons: string[];
  dispatchable: boolean;
  approval_required: boolean;
  live_scope_required: boolean;
  no_public_url_claim: boolean;
  no_metrics_claim: boolean;
  no_secret_material_present: boolean;
}}

export const discordSupervisedLivePreflightPacket: DiscordSupervisedLivePreflightPacket = {json.dumps(preflight_data, indent=2)};

export const normalizedDiscordPayloadCandidate: NormalizedDiscordPayloadCandidate = {json.dumps(normalized_data, indent=2)};

export const requestEnvelopePreview: RequestEnvelopePreview = {json.dumps(envelope_data, indent=2)};

export const operatorLiveGoPhrase = {json.dumps(go_phrase)};
"""

    if verify_only:
        if not TS_ADAPTER_FILE.exists():
            return {"adapter_in_sync": False, "reason": "Adapter file missing"}
        existing = TS_ADAPTER_FILE.read_text(encoding="utf-8")
        in_sync = existing.strip() == typescript_code.strip()
        return {"adapter_in_sync": in_sync, "packet_hash_matches": in_sync}

    TS_ADAPTER_FILE.parent.mkdir(parents=True, exist_ok=True)
    TS_ADAPTER_FILE.write_text(typescript_code, encoding="utf-8")
    return {"adapter_written": True}

if __name__ == "__main__":
    res = generate_preflight_adapter()
    print(f"Preflight codegen response: {res}")
