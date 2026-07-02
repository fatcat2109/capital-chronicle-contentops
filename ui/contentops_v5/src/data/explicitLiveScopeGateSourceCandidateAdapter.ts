// Capital Chronicle ContentOps V5 — Explicit Live Scope Gate & Source Candidate Adapter.
// This is a local-first read-only adapter generated from the V6 gate packet.
// Never manually edit. Use the Python codegen builder script.

export interface ExplicitLiveScopeGatePacket {
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
  credential_presence_states: {
    DISCORD_LIVE_ANNOUNCEMENTS_WEBHOOK: string;
    DISCORD_LIVE_ANNOUNCEMENTS_CHANNEL_LABEL: string;
  };
  
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
  
  endpoint_allowlist: Array<{
    host: string;
    method: string;
    path_shape: string;
  }>;
}

export interface NormalizedDispatchCandidate {
  candidate_id: string;
  source_artifact_path: string;
  source_artifact_hash: string;
  platform_family: string;
  content_type: string;
  operator_destination_label: string;
  normalized_body_text: string;
  payload_hash: string;
  safety_scan: string;
  blocked_reasons: string[];
  dispatchable: boolean;
  approval_required: boolean;
  live_scope_required: boolean;
  no_public_url_claim: boolean;
  no_metrics_claim: boolean;
  no_secret_material_present: boolean;
}

export const explicitLiveScopeGatePacket: ExplicitLiveScopeGatePacket = {
  "approval_ledger_entry_created": false,
  "approval_signature_present": false,
  "browser_session_used": false,
  "credential_presence_check_performed": true,
  "credential_presence_key_names_only": true,
  "credential_presence_states": {
    "DISCORD_LIVE_ANNOUNCEMENTS_CHANNEL_LABEL": "missing",
    "DISCORD_LIVE_ANNOUNCEMENTS_WEBHOOK": "missing"
  },
  "credential_value_read_made": false,
  "destination_binding_status": "blocked_until_operator_confirms_destination",
  "discord_live_scope_candidate_created": true,
  "dispatch_attempted": false,
  "dispatch_outbox_ready": false,
  "dispatch_request_count": 0,
  "enabled_publish_send_dispatch_approve_controls": false,
  "endpoint_allowlist": [
    {
      "host": "discord.com",
      "method": "POST",
      "path_shape": "/api/webhooks/{webhook.id}/{webhook.token}"
    }
  ],
  "endpoint_allowlist_created": true,
  "env_value_read_made": false,
  "exact_payload_hash": "cc1a6320629a1ee0548afc8c8719116c5d20b282b4f00318b87047e7b7e6aeb8",
  "exact_payload_preview_created": false,
  "executable_outbox_entry_created": false,
  "explicit_live_scope_gate_packet_id": "explicit_live_scope_cc1a6320629a1ee0",
  "explicit_live_scope_gate_status": "created_for_operator_review",
  "forbidden_financial_advice_or_signal_wording_present": false,
  "kill_switch_active": true,
  "kill_switch_required": true,
  "live_action_allowed": false,
  "live_publish_performed_by_contentops": false,
  "llm_provider_call_made": false,
  "normalized_candidate_status": "blocked_missing_operator_source_artifact",
  "normalized_dispatch_candidate_created": true,
  "official_docs_evidence_created": true,
  "packet_kind": "operator_recovery_to_explicit_live_scope_gate_source_candidate_v0",
  "payload_hash_preview_created": false,
  "platform_api_request_count": 0,
  "platform_api_used": false,
  "provider_call_made": false,
  "public_url_fetch_made": false,
  "public_url_verification_performed": false,
  "ready_for_auto_publish": false,
  "ready_for_dispatch": false,
  "real_outbox_entry_created": false,
  "retry_enabled": false,
  "scheduler_enabled": false,
  "source_approval_preview_exact_hash": "b02ec50b38399194d087d12c1e168ceef64fc527ddab1885517ca542f7a72678",
  "source_approval_preview_packet_id": "approval_preview_28f5ef142e404225",
  "source_dispatch_outbox_dry_run_exact_hash": "7cfc24c5b0c0ededb530c3d5ede21490ad49b0d46969e7d7ed3d8c7758769439",
  "source_dispatch_outbox_dry_run_packet_id": "outbox_dry_run_7cfc24c5b0c0eded",
  "source_final_review_exact_hash": "11fc52e6e452c4d3fedd306ffbf796fae459e061c784eed86cc1e8f65b9d38f2",
  "source_final_review_packet_id": "final_review_preview_11fc52e6e452c4d3",
  "source_intake_parser_created": true,
  "source_operator_recovery_exact_hash": "e30e17729faebb933a21045ac03b6e1be640aa33b8f4d424a06bbf79655d1fe2",
  "source_operator_recovery_packet_id": "operator_recovery_e30e17729faebb93",
  "task_label": "TASK_CONTENTOPS_V6_OPERATOR_RECOVERY_TO_EXPLICIT_LIVE_SCOPE_GATE_SOURCE_CANDIDATE_HEAVY_BATCH_V0",
  "webhook_request_count": 0
};

export const normalizedDispatchCandidate: NormalizedDispatchCandidate = {
  "approval_required": true,
  "blocked_reasons": [
    "blocked_missing_operator_source_artifact"
  ],
  "candidate_id": "",
  "content_type": "",
  "dispatchable": false,
  "live_scope_required": true,
  "no_metrics_claim": true,
  "no_public_url_claim": true,
  "no_secret_material_present": true,
  "normalized_body_text": "",
  "operator_destination_label": "",
  "payload_hash": "bd87835f6885c74fa48b3bb52ee6bb4ead8caed357abe2df8e55e99f8ca38184",
  "platform_family": "discord",
  "safety_scan": "pending",
  "source_artifact_hash": "",
  "source_artifact_path": ""
};
