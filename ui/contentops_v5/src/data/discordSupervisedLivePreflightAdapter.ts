// Capital Chronicle ContentOps V5 — Discord Supervised Live Preflight Adapter.
// Generated from local preflight schema configurations. Do not manually edit.

export interface DiscordSupervisedLivePreflightPacket {
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
  credential_presence_states: {
    DISCORD_LIVE_ANNOUNCEMENTS_WEBHOOK: string;
    DISCORD_LIVE_ANNOUNCEMENTS_CHANNEL_LABEL: string;
    CONTENTOPS_LIVE_KILL_SWITCH: string;
  };
  
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
}

export interface RequestEnvelopePreview {
  host: string;
  method: string;
  path_shape: string;
  body_hash_preview: string;
  allowed_mentions: {
    parse: string[];
  };
  content_length: number;
  payload_hash_preview: string;
}

export interface NormalizedDiscordPayloadCandidate {
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
}

export const discordSupervisedLivePreflightPacket: DiscordSupervisedLivePreflightPacket = {
  "approval_ledger_entry_created": false,
  "approval_signature_present": false,
  "browser_session_used": false,
  "credential_presence_check_performed": true,
  "credential_presence_key_names_only": true,
  "credential_presence_states": {
    "CONTENTOPS_LIVE_KILL_SWITCH": "missing",
    "DISCORD_LIVE_ANNOUNCEMENTS_CHANNEL_LABEL": "missing",
    "DISCORD_LIVE_ANNOUNCEMENTS_WEBHOOK": "missing"
  },
  "credential_value_read_made": false,
  "destination_binding_status": "blocked_until_operator_confirms_destination",
  "discord_platform_family": "discord",
  "dispatch_attempted": false,
  "dispatch_outbox_ready": false,
  "dispatch_request_count": 0,
  "enabled_publish_send_dispatch_approve_controls": false,
  "endpoint_allowlist_host": "discord.com",
  "endpoint_allowlist_path_shape": "/api/webhooks/{webhook.id}/{webhook.token}",
  "endpoint_token_redacted": true,
  "env_value_read_made": false,
  "exact_payload_hash": "ef5371b837e94bd46030d91af3b2946a39a6e0466d076e6974d82c87e554cb25",
  "exact_payload_preview_created": false,
  "executable_outbox_entry_created": false,
  "forbidden_financial_advice_or_signal_wording_present": false,
  "kill_switch_active": true,
  "kill_switch_required": true,
  "live_action_allowed": false,
  "live_publish_performed_by_contentops": false,
  "llm_provider_call_made": false,
  "normalized_discord_payload_candidate_created": true,
  "operator_go_phrase_recorded": false,
  "operator_go_phrase_required": true,
  "packet_kind": "discord_supervised_live_preflight_v0",
  "payload_hash_preview_created": false,
  "platform_api_request_count": 0,
  "platform_api_used": false,
  "provider_call_made": false,
  "public_url_fetch_made": false,
  "public_url_verification_performed": false,
  "ready_for_auto_publish": false,
  "ready_for_dispatch": false,
  "real_outbox_entry_created": false,
  "request_envelope_executable": false,
  "request_envelope_preview_created": true,
  "request_method_preview": "POST",
  "retry_enabled": false,
  "scheduler_enabled": false,
  "source_candidate_status": "blocked_missing_operator_source_artifact",
  "source_dispatch_outbox_dry_run_exact_hash": "7cfc24c5b0c0ededb530c3d5ede21490ad49b0d46969e7d7ed3d8c7758769439",
  "source_dispatch_outbox_dry_run_packet_id": "outbox_dry_run_7cfc24c5b0c0eded",
  "source_explicit_live_scope_gate_exact_payload_hash": "cc1a6320629a1ee0548afc8c8719116c5d20b282b4f00318b87047e7b7e6aeb8",
  "source_explicit_live_scope_gate_packet_id": "explicit_live_scope_cc1a6320629a1ee0",
  "source_operator_recovery_exact_hash": "e30e17729faebb933a21045ac03b6e1be640aa33b8f4d424a06bbf79655d1fe2",
  "source_operator_recovery_packet_id": "operator_recovery_e30e17729faebb93",
  "supervised_live_preflight_packet_id": "supervised_preflight_ef5371b837e94bd4",
  "supervised_live_preflight_status": "created_for_operator_review",
  "task_label": "TASK_CONTENTOPS_V6_EXPLICIT_LIVE_SCOPE_GATE_TO_DISCORD_SUPERVISED_LIVE_PREFLIGHT_HEAVY_BATCH_V0",
  "webhook_request_count": 0,
  "webhook_url_value_read_made": false
};

export const normalizedDiscordPayloadCandidate: NormalizedDiscordPayloadCandidate = {
  "approval_required": true,
  "blocked_reasons": [
    "blocked_missing_operator_source_artifact"
  ],
  "candidate_id": "",
  "content_length": 0,
  "content_type": "",
  "dispatchable": false,
  "live_scope_required": true,
  "no_metrics_claim": true,
  "no_public_url_claim": true,
  "no_secret_material_present": true,
  "normalized_body_text": "",
  "operator_destination_label": "",
  "payload_hash": "3c3c41c599fb5d2464b8851f467ed13427647a0bb98076f16992a794648aaa04",
  "platform_family": "discord",
  "request_body_hash_preview": null,
  "safety_scan": "pending",
  "source_artifact_hash": "",
  "source_artifact_path": ""
};

export const requestEnvelopePreview: RequestEnvelopePreview = {
  "allowed_mentions": {
    "parse": []
  },
  "body_hash_preview": "blocked_no_payload_hash",
  "content_length": 0,
  "host": "discord.com",
  "method": "POST",
  "path_shape": "/api/webhooks/{webhook.id}/{webhook.token}",
  "payload_hash_preview": "3c3c41c599fb5d2464b8851f467ed13427647a0bb98076f16992a794648aaa04"
};

export const operatorLiveGoPhrase = "CAPITAL_CHRONICLE_SUPERVISED_DISCORD_PILOT_VERIFIED_GO_PHRASE_2026";
