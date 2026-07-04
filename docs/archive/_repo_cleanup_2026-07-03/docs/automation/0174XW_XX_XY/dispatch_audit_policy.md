# Dispatch Audit Policy

> [!IMPORTANT]
> Local redacted audit dry-run only. Provider not called, raw request/response not persisted, token not logged, and no live-ready state.

- audit_status_map: `{"blocked": "blocked_audit_recorded", "duplicate_suppressed": "duplicate_suppressed_audit_recorded", "local_dry_run_gate_passed_not_live_ready": "local_audit_dry_run_recorded"}`
- autonomous_replies_or_dms: `False`
- credential_hydration_performed: `False`
- credential_read: `False`
- dispatch_audit_policy_checksum: `ebef692595cfe8b48d96f072ceada967fadfe8a5a7419ea3f455965068268609`
- dotenv_read: `False`
- env_read: `False`
- fixed_event_values: `{"auto_retry_allowed": false, "can_dispatch": false, "credential_hydration_performed": false, "dispatch_mode": "audit_dry_run_only", "final_url_verified": null, "live_post_performed": false, "live_ready_state_created": false, "manual_fallback_required": true, "platform_dispatch_performed": false, "provider_response_class": "not_called", "provider_response_redacted": {}, "raw_request_persisted": false, "raw_response_persisted": false, "redaction_status": "pass", "request_budget_allowed": 1, "request_budget_used": 0, "retry_count": 0, "token_logged": false, "valid_for_live_dispatch": false}`
- is_local_only: `True`
- live_post_performed: `False`
- live_ready_state_created: `False`
- llm_provider_api_called: `False`
- manual_fallback_required_always: `True`
- model: `DISPATCH_AUDIT_POLICY_0174XW_XX_XY`
- model_version: `0174XW_XX_XY_DISPATCH_AUDIT_POLICY_V1`
- network_performed: `False`
- platform_api_called: `False`
- platform_dispatch_performed: `False`
- provider_api_called: `False`
- provider_response_class_always: `not_called`
- public_ready_content_generated: `False`
- raw_request_persisted: `False`
- raw_response_persisted: `False`
- redaction_status_always: `pass`
- request_budget_used_always: `0`
- required_audit_event_fields: `["audit_event_id", "source_gate_matrix_id", "source_outbox_candidate_id", "source_approval_ledger_entry_id", "platform", "payload_class", "payload_hash", "payload_hash_short", "destination_binding_id", "credential_handle_id", "idempotency_key", "request_budget_used", "request_budget_allowed", "auto_retry_allowed", "dispatch_mode", "gate_matrix_status", "provider_response_class", "provider_response_redacted", "raw_request_persisted", "raw_response_persisted", "token_logged", "retry_count", "final_url_verified", "redaction_status", "manual_fallback_required", "valid_for_live_dispatch", "can_dispatch", "platform_dispatch_performed", "live_post_performed", "credential_hydration_performed", "live_ready_state_created", "blocked_reasons", "required_future_gates", "audit_hash", "evidence_refs"]`
- scheduler_enabled: `False`
- scraping_performed: `False`
- source_baseline_commit: `f38b489cd6ec54012ddff7ed7010625c6609d2d6`
- status: `pass`
- substack_api_called: `False`
- substack_dispatch_status: `manual_export_no_api`
- task_label: `TASK_CONTENTOPS_0174XW_XX_XY_DISPATCH_AUDIT_DRY_RUN_CONTRACT_V0`
- telegram_api_called: `False`
- telegram_dispatch_status: `proven_frozen_no_send`
- token_logged: `False`
- x_api_called: `False`
- x_dispatch_status: `dry_run_no_api`
