// Capital Chronicle ContentOps V5 — Discord Operator GO Packet Adapter.
// Generated from local review-only GO packet artifacts. Do not manually edit.

export const discordOperatorGoPacket = {
  "approval_ledger_entry_created": false,
  "blocked_reasons": [
    "blocked_missing_operator_go_source_artifact",
    "blocked_missing_operator_source_artifact"
  ],
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
  "dispatch_attempted": false,
  "dispatch_outbox_ready": false,
  "dispatch_request_count": 0,
  "enabled_publish_send_dispatch_approve_controls": false,
  "env_value_read_made": false,
  "exact_payload_hash": "c13b509858c9cf175a3cc7d172b64aefd8230e5a1419bba7522569181d911f39",
  "executable_outbox_entry_created": false,
  "kill_switch_active": true,
  "kill_switch_required": true,
  "live_action_allowed": false,
  "live_publish_performed_by_contentops": false,
  "llm_provider_call_made": false,
  "operator_go_packet_id": "operator_go_c13b509858c9cf17",
  "operator_go_packet_status": "created_for_operator_review",
  "operator_go_phrase_recorded": false,
  "operator_go_phrase_required": true,
  "operator_go_phrase_valid": false,
  "operator_go_phrase_validation_model_created": true,
  "operator_go_phrase_value_stored": false,
  "operator_go_source_artifact_hash": "",
  "operator_go_source_artifact_path": "",
  "operator_go_source_candidate_hash": "3c3c41c599fb5d2464b8851f467ed13427647a0bb98076f16992a794648aaa04",
  "operator_go_source_candidate_id": "",
  "packet_kind": "discord_operator_go_packet_v0",
  "platform_api_request_count": 0,
  "platform_api_used": false,
  "provider_call_made": false,
  "public_url_fetch_made": false,
  "public_url_verification_performed": false,
  "ready_for_auto_publish": false,
  "ready_for_dispatch": false,
  "real_outbox_entry_created": false,
  "request_envelope_executable": false,
  "retry_enabled": false,
  "safety_signature_hash": "af6b7d26bb5727c0a93bedef931a60c6d20070fe75cff154a75470874ef4a5b8",
  "safety_signature_preview_created": true,
  "scheduler_enabled": false,
  "source_candidate_status": "pending",
  "source_preflight_packet_path": "docs/automation/V6_DISCORD_SUPERVISED_LIVE_PREFLIGHT/discord_supervised_live_preflight_packet.json",
  "source_supervised_live_preflight_exact_payload_hash": "ef5371b837e94bd46030d91af3b2946a39a6e0466d076e6974d82c87e554cb25",
  "source_supervised_live_preflight_packet_id": "supervised_preflight_ef5371b837e94bd4",
  "source_task_label": "TASK_CONTENTOPS_V6_EXPLICIT_LIVE_SCOPE_GATE_TO_DISCORD_SUPERVISED_LIVE_PREFLIGHT_HEAVY_BATCH_V0",
  "task_label": "TASK_CONTENTOPS_V6_DISCORD_SUPERVISED_PREFLIGHT_TO_OPERATOR_GO_PACKET_HEAVY_BATCH_V0",
  "webhook_request_count": 0,
  "webhook_url_value_read_made": false,
  "webhook_validation_performed": false
};

export const normalizedOperatorGoSourceCandidate = {
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

export const operatorGoPhraseValidationModel = {
  "operator_go_phrase_exact_match_required": true,
  "operator_go_phrase_expected_hash": "6bcb999238cff59929d6be1675b003f6f48533710b245aec7d93a1348168be28",
  "operator_go_phrase_recorded": false,
  "operator_go_phrase_required": true,
  "operator_go_phrase_valid": false,
  "operator_go_phrase_value_logged": false,
  "operator_go_phrase_value_stored": false,
  "validation_model_hash": "706eaa0d00fa84c1be2056d7bbd2d00da0c4080dd7ca2b2d82639c0d5a4b81e6",
  "validation_scope": "review_only_model_no_live_send"
};

export const operatorGoSafetySignaturePreview = {
  "approval_ledger_entry_created": false,
  "blocked_reasons": [
    "blocked_missing_operator_go_source_artifact",
    "blocked_missing_operator_source_artifact"
  ],
  "credential_value_read_made": false,
  "discord_api_call_made": false,
  "env_value_read_made": false,
  "executable_outbox_entry_created": false,
  "live_action_allowed": false,
  "operator_source_payload_hash": "3c3c41c599fb5d2464b8851f467ed13427647a0bb98076f16992a794648aaa04",
  "platform_api_call_made": false,
  "provider_call_made": false,
  "ready_for_dispatch": false,
  "request_envelope_executable": false,
  "review_only": true,
  "safety_signature_hash": "af6b7d26bb5727c0a93bedef931a60c6d20070fe75cff154a75470874ef4a5b8",
  "source_preflight_hash": "ef5371b837e94bd46030d91af3b2946a39a6e0466d076e6974d82c87e554cb25",
  "webhook_validation_performed": false
};
