"""Codegen script to generate V5 TypeScript adapter for V6 Explicit Live Scope Gate Source Candidate."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GATE_PACKET_FILE = ROOT / "docs" / "automation" / "V6_OPERATOR_RECOVERY_TO_EXPLICIT_LIVE_SCOPE_GATE_SOURCE_CANDIDATE" / "operator_recovery_to_explicit_live_scope_gate_source_candidate_packet.json"
NORMALIZED_FILE = ROOT / "docs" / "automation" / "V6_OPERATOR_RECOVERY_TO_EXPLICIT_LIVE_SCOPE_GATE_SOURCE_CANDIDATE" / "normalized_candidate" / "normalized_dispatch_candidate.json"
TS_ADAPTER_FILE = ROOT / "ui" / "contentops_v5" / "src" / "data" / "explicitLiveScopeGateSourceCandidateAdapter.ts"

def generate_or_check_gate_adapter(verify_only: bool = False) -> dict:
    if not GATE_PACKET_FILE.exists():
        raise FileNotFoundError(f"Gate packet file not found at: {GATE_PACKET_FILE}")
    if not NORMALIZED_FILE.exists():
        raise FileNotFoundError(f"Normalized candidate file not found at: {NORMALIZED_FILE}")

    gate_data = json.loads(GATE_PACKET_FILE.read_text(encoding="utf-8"))
    normalized_data = json.loads(NORMALIZED_FILE.read_text(encoding="utf-8"))

    typescript_code = f"""// Capital Chronicle ContentOps V5 — Explicit Live Scope Gate & Source Candidate Adapter.
// This is a local-first read-only adapter generated from the V6 gate packet.
// Never manually edit. Use the Python codegen builder script.

export interface ExplicitLiveScopeGatePacket {{
  task_label: string;
  packet_kind: string;
  explicit_live_scope_gate_packet_id: string;
  exact_payload_hash: string;
  explicit_live_scope_gate_status: string;
  
  source_intake_parser_created: boolean;
  normalized_dispatch_candidate_created: boolean;
  normalized_candidate_status: string;
  discord_live_scope_candidate_created: boolean;
  official_docs_evidence_created: boolean;
  endpoint_allowlist_created: boolean;
  
  credential_presence_check_performed: boolean;
  credential_value_read_made: boolean;
  env_value_read_made: boolean;
  credential_presence_key_names_only: boolean;
  credential_presence_states: {{
    DISCORD_LIVE_ANNOUNCEMENTS_WEBHOOK: string;
    DISCORD_LIVE_ANNOUNCEMENTS_CHANNEL_LABEL: string;
  }};
  
  destination_binding_status: string;
  payload_hash_preview_created: boolean;
  exact_payload_preview_created: boolean;
  
  executable_outbox_entry_created: boolean;
  real_outbox_entry_created: boolean;
  approval_ledger_entry_created: boolean;
  approval_signature_present: boolean;
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

  source_operator_recovery_packet_id: string;
  source_operator_recovery_exact_hash: string;
  source_dispatch_outbox_dry_run_packet_id: string;
  source_dispatch_outbox_dry_run_exact_hash: string;
  source_approval_preview_packet_id: string;
  source_approval_preview_exact_hash: string;
  source_final_review_packet_id: string;
  source_final_review_exact_hash: string;
  
  endpoint_allowlist: Array<{{
    host: string;
    method: string;
    path_shape: string;
  }}>;
}}

export interface NormalizedDispatchCandidate {{
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

export const explicitLiveScopeGatePacket: ExplicitLiveScopeGatePacket = {json.dumps(gate_data, indent=2)};

export const normalizedDispatchCandidate: NormalizedDispatchCandidate = {json.dumps(normalized_data, indent=2)};
"""

    if verify_only:
        if not TS_ADAPTER_FILE.exists():
            return {"adapter_in_sync": False, "reason": "TypeScript file missing"}
        existing_content = TS_ADAPTER_FILE.read_text(encoding="utf-8")
        in_sync = existing_content.strip() == typescript_code.strip()
        return {"adapter_in_sync": in_sync, "packet_hash_matches": in_sync}

    TS_ADAPTER_FILE.parent.mkdir(parents=True, exist_ok=True)
    TS_ADAPTER_FILE.write_text(typescript_code, encoding="utf-8")
    return {"adapter_written": True}

if __name__ == "__main__":
    res = generate_or_check_gate_adapter()
    print(f"Codegen response: {res}")
