# Live Read-Only Research Runbook & Approval Gate Dry-Run V0

## Critical Safety Warning
> [!CAUTION]
> **NOT LIVE, NOT APPROVED, NOT PUBLIC-POSTABLE.**
> This module is a local-only dry-run contract mapping and validating future validation criteria.
> No live reads, API calls, environment/credential reads, browser sessions, scheduler behavior, or posting are authorized.

- **Task Label**: `TASK_CONTENTOPS_0174UQ_LIVE_READ_ONLY_RESEARCH_RUNBOOK_AND_APPROVAL_GATE_DRY_RUN_V0`
- **Source Baseline Commit**: `9656aa43fd7778e5002925f94888f0707398abf2`
- **Matrix/Packet ID**: `live_read_only_research_runbook_approval_gate_dry_run_packet_8518cbd3e3b2573530482d28`
- **Packet Hash**: `8518cbd3e3b2573530482d28b392e5499bf8b83b276562e02794c4156eba51d5`
- **Next Required Gate**: `TASK_CONTENTOPS_0174UR_LOCAL_PREFLIGHT_SIMULATION_OF_LIVE_READ_ADAPTERS_V0`

## 1. Runbook Validation Decisions Matrix

| Platform ID | Gate Status | Precheck Status | Approval Status | Evidence Status | Allowlist Status | Budget Status | Kill Switch Status |
|---|---|---|---|---|---|---|---|
| `x` | `blocked` | `blocked_precheck` | `schema_blocked` | `dry_run_schema_blocked` | `allowlist_symbolic` | `request_budget_within_symbolic_limit` | `kill_switch_closed_verified` |
| `telegram_remote_operator` | `not_ready` | `not_ready` | `schema_not_ready` | `dry_run_schema_not_ready` | `allowlist_symbolic` | `request_budget_within_symbolic_limit` | `kill_switch_closed_verified` |
| `telegram_channel_destination` | `not_ready` | `not_ready` | `schema_not_ready` | `dry_run_schema_not_ready` | `allowlist_symbolic` | `request_budget_within_symbolic_limit` | `kill_switch_closed_verified` |
| `substack_newsletter` | `manual_only` | `manual_only` | `manual_only` | `manual_only` | `manual_no_api` | `manual_no_api` | `manual_stop_policy` |
| `linkedin` | `blocked` | `blocked_precheck` | `schema_blocked` | `dry_run_schema_blocked` | `allowlist_symbolic` | `request_budget_within_symbolic_limit` | `kill_switch_closed_verified` |
| `threads` | `blocked` | `blocked_precheck` | `schema_blocked` | `dry_run_schema_blocked` | `allowlist_symbolic` | `request_budget_within_symbolic_limit` | `kill_switch_closed_verified` |
| `instagram` | `blocked` | `blocked_precheck` | `schema_blocked` | `dry_run_schema_blocked` | `allowlist_symbolic` | `request_budget_within_symbolic_limit` | `kill_switch_closed_verified` |
| `facebook_page` | `blocked` | `blocked_precheck` | `schema_blocked` | `dry_run_schema_blocked` | `allowlist_symbolic` | `request_budget_within_symbolic_limit` | `kill_switch_closed_verified` |
| `tiktok` | `blocked` | `blocked_precheck` | `schema_blocked` | `dry_run_schema_blocked` | `allowlist_symbolic` | `request_budget_within_symbolic_limit` | `kill_switch_closed_verified` |
| `youtube` | `not_ready` | `not_ready` | `schema_not_ready` | `dry_run_schema_not_ready` | `allowlist_symbolic` | `request_budget_within_symbolic_limit` | `kill_switch_closed_verified` |

## 2. Operator Review Checklist

- [ ] 1. Verify the targeted platform role and endpoint family.
- [ ] 2. Confirm that the platform-specific endpoint is present in the allowlist registry.
- [ ] 3. Assert that the request budget is symbolic and does not exceed limit (max 1 request).
- [ ] 4. Verify that credential policy is strictly limited to key names, never raw secret values.
- [ ] 5. Inspect the redaction proof and confirm that no raw response bodies are stored or logged.
- [ ] 6. Confirm the kill switch status is closed and safety flags are fully locked.
- [ ] 7. Ensure human operator approval ref is recorded and active before any future validation progression.

## 3. Required Verification Checklists

### Approval Gate Checklist
- [ ] Verify approval validation field presence for kind `explicit_task_label`.
- [ ] Verify approval validation field presence for kind `platform_id`.
- [ ] Verify approval validation field presence for kind `endpoint_family`.
- [ ] Verify approval validation field presence for kind `endpoint_allowlist`.
- [ ] Verify approval validation field presence for kind `credential_policy`.
- [ ] Verify approval validation field presence for kind `credential_handle_key_names_only`.
- [ ] Verify approval validation field presence for kind `request_budget`.
- [ ] Verify approval validation field presence for kind `timeout_seconds`.
- [ ] Verify approval validation field presence for kind `redaction_policy`.
- [ ] Verify approval validation field presence for kind `secret_output_prohibition`.
- [ ] Verify approval validation field presence for kind `no_raw_response_logging`.
- [ ] Verify approval validation field presence for kind `kill_switch_state`.
- [ ] Verify approval validation field presence for kind `stop_conditions`.
- [ ] Verify approval validation field presence for kind `rollback_or_abort_policy`.
- [ ] Verify approval validation field presence for kind `evidence_packet_schema`.
- [ ] Verify approval validation field presence for kind `operator_approval_ref`.
- [ ] Verify approval validation field presence for kind `live_read_boundary`.
- [ ] Verify approval validation field presence for kind `live_write_prohibition`.
- [ ] Verify approval validation field presence for kind `env_read_boundary`.
- [ ] Verify approval validation field presence for kind `audit_chain_requirement`.

### Evidence Packet Checklist
- [ ] Enforce evidence structure verification for kind `task_identity`.
- [ ] Enforce evidence structure verification for kind `live_or_dry_run_classification`.
- [ ] Enforce evidence structure verification for kind `platform_identity`.
- [ ] Enforce evidence structure verification for kind `endpoint_family`.
- [ ] Enforce evidence structure verification for kind `endpoint_allowlist`.
- [ ] Enforce evidence structure verification for kind `request_budget`.
- [ ] Enforce evidence structure verification for kind `request_count`.
- [ ] Enforce evidence structure verification for kind `timeout_seconds`.
- [ ] Enforce evidence structure verification for kind `credential_policy`.
- [ ] Enforce evidence structure verification for kind `credential_key_names_only`.
- [ ] Enforce evidence structure verification for kind `credential_presence_classification`.
- [ ] Enforce evidence structure verification for kind `secret_redaction_proof`.
- [ ] Enforce evidence structure verification for kind `no_secret_output_confirmation`.
- [ ] Enforce evidence structure verification for kind `no_raw_response_logging_confirmation`.
- [ ] Enforce evidence structure verification for kind `response_status_classification`.
- [ ] Enforce evidence structure verification for kind `response_shape_classification`.
- [ ] Enforce evidence structure verification for kind `response_body_redaction_classification`.
- [ ] Enforce evidence structure verification for kind `evidence_artifact_ref`.
- [ ] Enforce evidence structure verification for kind `evidence_artifact_hash`.
- [ ] Enforce evidence structure verification for kind `source_payload_hash`.
- [ ] Enforce evidence structure verification for kind `request_started_at`.
- [ ] Enforce evidence structure verification for kind `request_finished_at`.
- [ ] Enforce evidence structure verification for kind `duration_ms_classification`.
- [ ] Enforce evidence structure verification for kind `failure_or_timeout_classification`.
- [ ] Enforce evidence structure verification for kind `stop_condition_triggered`.
- [ ] Enforce evidence structure verification for kind `abort_policy_result`.
- [ ] Enforce evidence structure verification for kind `operator_approval_ref`.
- [ ] Enforce evidence structure verification for kind `kill_switch_state`.
- [ ] Enforce evidence structure verification for kind `audit_entry_ref`.
- [ ] Enforce evidence structure verification for kind `safety_flags`.

### Redaction Proof & Security Checklist
- [ ] Enforce that no raw response logging is enabled for all templates.
- [ ] Enforce that all secret outputs are completely blocked.
- [ ] Verify credential policy key names only (values strictly hidden).
- [ ] Check that the stop condition triggered matches symbolics (`on_error`, `on_budget_exhausted`).
- [ ] Verify the kill switch state remains closed.

## 4. Platform Blockers & Gaps Summary

### Platform `x`
- **Role/Endpoint Family**: `x_api_read_only_symbolic`
- **Blocked Reasons**:
  - `platform_readiness_blocked_in_um`
  - `credential_boundary_unverified`
  - `x_app_access_gap`
  - `spend_gate_unresolved`
  - `rate_budget_gap`
  - `read_only_endpoint_proof_gap`
  - `precheck_failed_closed_in_precheck`
  - `approval_schema_failed_in_approval`
- **Missing Proofs**:
  - `redaction_proof_missing`
  - `x_app_access_gap`
  - `spend_gate_unresolved`
  - `rate_budget_gap`
  - `read_only_endpoint_proof_gap`

### Platform `telegram_remote_operator`
- **Role/Endpoint Family**: `telegram_bot_getupdates_or_webhook_symbolic`
- **Blocked Reasons**:
  - `platform_readiness_requires_human_review_in_um`
  - `credential_boundary_unverified`
  - `no_arbitrary_dm_allowed`
  - `operator_inbox_proof_required`
  - `precheck_not_ready_in_precheck`
  - `approval_schema_not_ready_in_approval`
- **Missing Proofs**:
  - `redaction_proof_missing`
  - `no_arbitrary_dm_allowed`
  - `operator_inbox_proof_required`

### Platform `telegram_channel_destination`
- **Role/Endpoint Family**: `telegram_bot_getchat_symbolic`
- **Blocked Reasons**:
  - `platform_readiness_requires_human_review_in_um`
  - `credential_boundary_unverified`
  - `channel_admin_proof_required`
  - `bot_permission_gap`
  - `channel_state_symbolic_only`
  - `precheck_not_ready_in_precheck`
  - `approval_schema_not_ready_in_approval`
- **Missing Proofs**:
  - `redaction_proof_missing`
  - `channel_admin_proof_required`
  - `bot_permission_gap`
  - `channel_state_symbolic_only`

### Platform `substack_newsletter`
- **Role/Endpoint Family**: `manual_export_no_api`
- **Blocked Reasons**:
  - `manual_export_only`
- **Missing Proofs**:
  - `manual_export_only`

### Platform `linkedin`
- **Role/Endpoint Family**: `linkedin_api_read_only_symbolic`
- **Blocked Reasons**:
  - `platform_readiness_blocked_in_um`
  - `credential_boundary_unverified`
  - `linkedin_organization_page_proof_missing`
  - `precheck_failed_closed_in_precheck`
  - `approval_schema_failed_in_approval`
- **Missing Proofs**:
  - `redaction_proof_missing`
  - `linkedin_organization_page_proof_missing`

### Platform `threads`
- **Role/Endpoint Family**: `meta_threads_read_only_symbolic`
- **Blocked Reasons**:
  - `platform_readiness_blocked_in_um`
  - `credential_boundary_unverified`
  - `meta_app_review_closed`
  - `meta_app_account_proof_required`
  - `precheck_failed_closed_in_precheck`
  - `approval_schema_failed_in_approval`
- **Missing Proofs**:
  - `redaction_proof_missing`
  - `meta_app_review_closed`
  - `meta_app_account_proof_required`

### Platform `instagram`
- **Role/Endpoint Family**: `meta_instagram_read_only_symbolic`
- **Blocked Reasons**:
  - `platform_readiness_blocked_in_um`
  - `credential_boundary_unverified`
  - `meta_app_review_closed`
  - `meta_app_account_proof_required`
  - `precheck_failed_closed_in_precheck`
  - `approval_schema_failed_in_approval`
- **Missing Proofs**:
  - `redaction_proof_missing`
  - `meta_app_review_closed`
  - `meta_app_account_proof_required`

### Platform `facebook_page`
- **Role/Endpoint Family**: `meta_facebook_page_read_only_symbolic`
- **Blocked Reasons**:
  - `platform_readiness_blocked_in_um`
  - `credential_boundary_unverified`
  - `meta_app_review_closed`
  - `meta_app_account_proof_required`
  - `precheck_failed_closed_in_precheck`
  - `approval_schema_failed_in_approval`
- **Missing Proofs**:
  - `redaction_proof_missing`
  - `meta_app_review_closed`
  - `meta_app_account_proof_required`

### Platform `tiktok`
- **Role/Endpoint Family**: `tiktok_read_only_symbolic`
- **Blocked Reasons**:
  - `platform_readiness_blocked_in_um`
  - `credential_boundary_unverified`
  - `tiktok_app_audit_closed`
  - `creator_account_proof_required`
  - `video_publish_proof_required`
  - `precheck_failed_closed_in_precheck`
  - `approval_schema_failed_in_approval`
- **Missing Proofs**:
  - `redaction_proof_missing`
  - `tiktok_app_audit_closed`
  - `creator_account_proof_required`
  - `video_publish_proof_required`

### Platform `youtube`
- **Role/Endpoint Family**: `youtube_data_api_read_only_symbolic`
- **Blocked Reasons**:
  - `platform_readiness_requires_human_review_in_um`
  - `credential_boundary_unverified`
  - `youtube_quota_unresolved`
  - `youtube_oauth_flow_closed`
  - `upload_proof_required`
  - `precheck_not_ready_in_precheck`
  - `approval_schema_not_ready_in_approval`
- **Missing Proofs**:
  - `redaction_proof_missing`
  - `youtube_quota_unresolved`
  - `youtube_oauth_flow_closed`
  - `upload_proof_required`
