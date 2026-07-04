# Approval Ledger Policy

> [!IMPORTANT]
> Local append-only fixture contract. No dispatch, outbox creation, platform/provider call, network, or credential/env read.

- ambiguous_requires_clarification: `True`
- append_only_fixture_output_only: `True`
- approval_ledger_policy_checksum: `73b965e52274ccd7bc2f441b210fbd3fd998a115eeb16ed173eeee79f10a2d0d`
- autonomous_replies_or_dms: `False`
- can_create_outbox_always_false: `True`
- can_dispatch_always_false: `True`
- credential_read: `False`
- dispatch_outbox_mutated: `False`
- dotenv_read: `False`
- edit_routes_to_revision: `True`
- env_read: `False`
- event_classes: `["approval_candidate", "rejected_event", "edit_request_event", "hold_event", "blocked_event"]`
- expiration_policy: `future_required_not_active`
- hold_pauses_eligibility: `True`
- is_local_only: `True`
- live_post_performed: `False`
- llm_provider_api_called: `False`
- mismatch_fails_closed: `True`
- model: `APPROVAL_LEDGER_POLICY_0174XN_XO_XP`
- model_version: `0174XN_XO_XP_APPROVAL_LEDGER_POLICY_V1`
- network_performed: `False`
- only_explicit_approve_exact_hash_can_create_approval: `True`
- platform_api_called: `False`
- platform_dispatch_performed: `False`
- provider_api_called: `False`
- public_postable_always_false: `True`
- public_ready_content_generated: `False`
- reject_creates_rejected_event: `True`
- replay_fails_closed: `True`
- required_ledger_fields: `["ledger_entry_id", "approved_at_order", "operator_id", "approval_channel", "source_challenge_candidate_id", "source_payload_id", "source_brief_id", "source_intent_id", "platform", "payload_class", "payload_hash", "payload_hash_short", "destination_binding_id", "credential_handle_id", "media_manifest_hash", "approval_text_redacted", "approval_method", "prior_payload_hash", "revoked", "expiration_policy", "valid_for_dispatch", "eligible_for_outbox_candidate", "blocked_reasons", "audit_hash", "human_review_required", "no_financial_advice", "no_signal_language", "public_postable", "can_dispatch", "can_create_outbox", "platform_api_called"]`
- required_response_fields: `["response_id", "source_challenge_candidate_id", "operator_id", "response_channel", "response_text_redacted", "response_class", "response_payload_hash_short", "received_at_order", "replay_status", "redaction_status", "trust_status"]`
- response_classes: `["explicit_approve", "explicit_reject", "explicit_edit_request", "explicit_hold", "ambiguous"]`
- scheduler_enabled: `False`
- scraping_performed: `False`
- source_baseline_commit: `a763e3aaa1cf079a472b9fe0f8748c36dae60a50`
- status: `pass`
- substack_api_called: `False`
- task_label: `TASK_CONTENTOPS_0174XN_XO_XP_APPROVAL_LEDGER_CONTRACT_V0`
- telegram_api_called: `False`
- unknown_challenge_fails_closed: `True`
- valid_approval_can_be_outbox_candidate: `True`
- valid_for_dispatch_always_false: `True`
- x_api_called: `False`
