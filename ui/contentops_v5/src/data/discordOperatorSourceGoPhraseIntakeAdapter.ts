// Capital Chronicle ContentOps V5 — Discord Operator Source + GO Phrase Intake Adapter.
// Generated from local fail-closed intake artifacts. Do not manually edit.

export const discordOperatorSourceGoPhraseIntakePacket = {
  "approval_ledger_entry_created": false,
  "blocked_reasons": [
    "blocked_contentops_live_kill_switch_key_missing",
    "blocked_destination_binding_not_confirmed",
    "blocked_destination_label_missing",
    "blocked_discord_live_announcements_channel_label_key_missing",
    "blocked_discord_live_announcements_webhook_key_missing",
    "blocked_kill_switch_not_active",
    "blocked_missing_operator_source_artifact",
    "blocked_operator_go_phrase_not_recorded",
    "blocked_operator_go_phrase_not_valid"
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
  "destination_binding_confirmed": false,
  "destination_label": "",
  "destination_proof_hash": "6fa5036480cb8cb5067f659062dd85d700c7b9bd8cf53551447cf13693f2b43b",
  "dispatch_attempted": false,
  "dispatch_outbox_ready": false,
  "dispatch_request_count": 0,
  "enabled_publish_send_dispatch_approve_controls": false,
  "env_value_read_made": false,
  "exact_payload_hash": "ca679bca13842222c0ac50ccaf74da9e463963180a2f557ff738aa03a8279f73",
  "executable_outbox_entry_created": false,
  "intake_packet_id": "discord_source_go_intake_ca679bca13842222",
  "intake_status": "blocked",
  "kill_switch_active": false,
  "kill_switch_required": true,
  "live_action_allowed": false,
  "live_publish_performed_by_contentops": false,
  "llm_provider_call_made": false,
  "normalized_candidate_hash": "8cd7d29208765fec50e495e81a479b04ecb85b1352243c6ddfb4d0a55fc6a22a",
  "normalized_candidate_id": "discord_operator_source_go_8cd7d29208765fec",
  "operator_go_phrase_expected_hash": "6bcb999238cff59929d6be1675b003f6f48533710b245aec7d93a1348168be28",
  "operator_go_phrase_recorded": false,
  "operator_go_phrase_valid": false,
  "operator_go_phrase_value_stored": false,
  "operator_source_artifact_hash": "",
  "operator_source_artifact_path": "",
  "packet_kind": "discord_operator_source_go_phrase_intake_v0",
  "phrase_evidence_hash": "0ab8aad39aa40bf75b6da54ceb8e8203380db4ff12806948eaba8f1b8274ad4f",
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
  "safety_signature_hash": "22f32cd92c860102e9f70d49a8cd48ee021c935d1d5b995d9624dbdb2a2e866c",
  "scheduler_enabled": false,
  "source_dry_run_gate_exact_payload_hash": "f9d4f7f1945dc120e02c372436122068a76d3b8d117b5cf88b17c45ffe49838a",
  "source_dry_run_gate_packet_id": "discord_dry_run_gate_f9d4f7f1945dc120",
  "source_dry_run_gate_path": "docs/automation/V6_DISCORD_SUPERVISED_LIVE_DISPATCH_DRY_RUN_GATE/discord_supervised_live_dispatch_dry_run_gate_packet.json",
  "source_task_label": "TASK_CONTENTOPS_V6_OPERATOR_GO_PACKET_TO_SUPERVISED_DISCORD_LIVE_DISPATCH_DRY_RUN_GATE_HEAVY_BATCH_V0",
  "task_label": "TASK_CONTENTOPS_V6_SUPERVISED_DISCORD_DRY_RUN_GATE_TO_OPERATOR_SOURCE_ARTIFACT_AND_GO_PHRASE_INTAKE_V0",
  "webhook_request_count": 0,
  "webhook_url_value_read_made": false,
  "webhook_validation_performed": false
};

export const normalizedOperatorSourceGoPhraseCandidate = {
  "blocked_reasons": [
    "blocked_contentops_live_kill_switch_key_missing",
    "blocked_destination_binding_not_confirmed",
    "blocked_destination_label_missing",
    "blocked_discord_live_announcements_channel_label_key_missing",
    "blocked_discord_live_announcements_webhook_key_missing",
    "blocked_kill_switch_not_active",
    "blocked_missing_operator_source_artifact",
    "blocked_operator_go_phrase_not_recorded",
    "blocked_operator_go_phrase_not_valid"
  ],
  "body_hash_preview": "",
  "body_value_stored": false,
  "candidate_hash": "8cd7d29208765fec50e495e81a479b04ecb85b1352243c6ddfb4d0a55fc6a22a",
  "candidate_id": "discord_operator_source_go_8cd7d29208765fec",
  "candidate_kind": "discord_operator_source_go_phrase_candidate_v0",
  "candidate_status": "blocked",
  "content_type": "",
  "destination_binding_confirmed": false,
  "destination_label": "",
  "dispatchable": false,
  "go_phrase_present": false,
  "go_phrase_valid": false,
  "go_phrase_value_stored": false,
  "kill_switch_active": false,
  "platform_family": "discord",
  "source_artifact_hash": "",
  "source_artifact_path": ""
};

export const operatorGoPhraseEvidence = {
  "expected_phrase_hash": "6bcb999238cff59929d6be1675b003f6f48533710b245aec7d93a1348168be28",
  "phrase_evidence_hash": "0ab8aad39aa40bf75b6da54ceb8e8203380db4ff12806948eaba8f1b8274ad4f",
  "phrase_evidence_kind": "discord_operator_go_phrase_evidence_v0",
  "phrase_exact_match": false,
  "phrase_present": false,
  "phrase_value_logged": false,
  "phrase_value_stored": false
};

export const discordDestinationBindingProof = {
  "destination_binding_confirmed": false,
  "destination_label": "",
  "destination_proof_hash": "6fa5036480cb8cb5067f659062dd85d700c7b9bd8cf53551447cf13693f2b43b",
  "destination_proof_kind": "discord_destination_binding_proof_v0",
  "platform_api_request_count": 0,
  "webhook_url_value_read_made": false,
  "webhook_validation_performed": false
};

export const operatorSourceGoPhraseSafetySignature = {
  "approval_ledger_entry_created": false,
  "blocked_reasons": [
    "blocked_contentops_live_kill_switch_key_missing",
    "blocked_destination_binding_not_confirmed",
    "blocked_destination_label_missing",
    "blocked_discord_live_announcements_channel_label_key_missing",
    "blocked_discord_live_announcements_webhook_key_missing",
    "blocked_kill_switch_not_active",
    "blocked_missing_operator_source_artifact",
    "blocked_operator_go_phrase_not_recorded",
    "blocked_operator_go_phrase_not_valid"
  ],
  "credential_value_read_made": false,
  "discord_api_call_made": false,
  "env_value_read_made": false,
  "executable_outbox_entry_created": false,
  "live_action_allowed": false,
  "platform_api_call_made": false,
  "provider_call_made": false,
  "ready_for_dispatch": false,
  "request_envelope_executable": false,
  "review_only": true,
  "safety_signature_hash": "22f32cd92c860102e9f70d49a8cd48ee021c935d1d5b995d9624dbdb2a2e866c",
  "safety_signature_kind": "discord_operator_source_go_phrase_intake_safety_signature_v0",
  "source_dry_run_gate_hash": "f9d4f7f1945dc120e02c372436122068a76d3b8d117b5cf88b17c45ffe49838a",
  "source_dry_run_gate_packet_id": "discord_dry_run_gate_f9d4f7f1945dc120",
  "webhook_validation_performed": false
};
