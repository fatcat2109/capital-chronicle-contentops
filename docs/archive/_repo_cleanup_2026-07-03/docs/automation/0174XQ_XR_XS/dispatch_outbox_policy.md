# Dispatch Outbox Policy

> [!IMPORTANT]
> Local dry-run outbox candidate policy only. No dispatch, credential hydration, platform/provider calls, network, or live-ready state.

- auto_retry_allowed: `False`
- autonomous_replies_or_dms: `False`
- can_dispatch_always_false: `True`
- credential_hydration_allowed: `False`
- credential_hydration_performed: `False`
- credential_read: `False`
- dispatch_mode: `dry_run_candidate_only`
- dispatch_outbox_policy_checksum: `b1db78d65e3230d4fd58a2125c61c7e1279ea0895f2b5941567dc3057039fc95`
- dotenv_read: `False`
- env_read: `False`
- idempotency_key_algorithm: `sha256`
- idempotency_key_binds: `["platform", "payload_hash", "destination_binding_id", "credential_handle_id", "approval_ledger_entry_id"]`
- is_local_only: `True`
- kill_switch_required: `True`
- live_dispatch_allowed: `False`
- live_post_performed: `False`
- live_ready_state_created: `False`
- llm_provider_api_called: `False`
- model: `DISPATCH_OUTBOX_POLICY_0174XQ_XR_XS`
- model_version: `0174XQ_XR_XS_DISPATCH_OUTBOX_POLICY_V1`
- network_performed: `False`
- platform_api_call_allowed: `False`
- platform_api_called: `False`
- platform_dispatch_performed: `False`
- provider_api_called: `False`
- public_ready_content_generated: `False`
- request_budget_required: `1`
- required_outbox_candidate_fields: `["outbox_candidate_id", "source_approval_ledger_entry_id", "source_challenge_candidate_id", "source_payload_id", "source_brief_id", "source_intent_id", "platform", "payload_class", "payload_hash", "payload_hash_short", "destination_binding_id", "credential_handle_id", "idempotency_key", "idempotency_key_algorithm", "dispatch_mode", "request_budget", "auto_retry_allowed", "kill_switch_required", "credential_hydration_allowed", "platform_api_call_allowed", "live_dispatch_allowed", "status", "blocked_reasons", "duplicate_suppression_status", "eligible_for_gate_matrix", "valid_for_dispatch", "can_dispatch", "provider_api_called", "platform_api_called", "live_post_performed", "audit_hash", "evidence_refs"]`
- scheduler_enabled: `False`
- scraping_performed: `False`
- source_baseline_commit: `2f80831bce881f26e6bff3109a4731aaaad3e167`
- status: `pass`
- substack_api_called: `False`
- substack_dispatch_status: `manual_export_no_api`
- supported_dispatch_prep_platforms: `["substack", "telegram", "x"]`
- task_label: `TASK_CONTENTOPS_0174XQ_XR_XS_DISPATCH_OUTBOX_CANDIDATE_CONTRACT_V0`
- telegram_api_called: `False`
- telegram_dispatch_status: `proven_frozen_no_send`
- valid_for_dispatch_always_false: `True`
- x_api_called: `False`
- x_dispatch_status: `dry_run_no_api`
