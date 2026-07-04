# 0174TM/TN/TO Kill Switch + Rate Policy + One-Request Dispatch Gate

Task: `TASK_CONTENTOPS_0174TM_TN_TO_KILL_SWITCH_RATE_POLICY_AND_ONE_REQUEST_SUPERVISED_DISPATCH_GATE_BATCH_V0`

Model: `SUPERVISED_DISPATCH_SAFETY_GATE_CONTRACT_0174TM_TN_TO` version `0174TM_TN_TO_SAFETY_GATE_V1`

Baseline commit: `905161770623e3dab9347fead84ae20f41ab7e4e`

## Role

This batch is LOCAL and deterministic. It performs NO live platform API call, NO Telegram send, NO LLM/provider call, NO network, NO env/credential read, NO credential hydration, NO scheduler, and NO auto retry. It NEVER dispatches.

## 0174TM Kill switch

Fail-closed by default: only an explicit `kill_switch_clear` state with a fresh policy snapshot is clear. Recognised states:

  * `credential_handle_disabled`
  * `destination_binding_disabled`
  * `dispatch_window_closed`
  * `global_dispatch_disabled`
  * `kill_switch_clear`
  * `operator_dispatch_disabled`
  * `platform_dispatch_disabled`

## 0174TN Rate / spend / retry policy

The only clear outcome is `rate_spend_retry_policy_clear_for_one_request_gate`. Required invariants:

  * `max_requests_per_gate_equals_1`
  * `auto_retry_allowed_false`
  * `scheduler_enabled_false`
  * `rate_limit_window_symbolic_only`
  * `spend_limit_symbolic_only`
  * `provider_budget_not_hydrated`
  * `credential_not_hydrated`
  * `no_backoff_loop`
  * `no_queue_worker`
  * `no_scheduled_retry`
  * `operator_reapproval_required_after_failure`

## 0174TO One-request supervised dispatch gate

Requires a complete dry run, a clear kill switch, a clear rate policy, the full deep cross-binding, and an explicit supervised request id. It produces a local `DispatchAuthorizationCandidate` (`one_request_dispatch_gate_candidate_created_not_dispatched`) that is NEVER live-executable and always `requires_operator_live_gate`. A registry suppresses duplicate request ids and idempotency fingerprints.

## R1 upstream safety-flag revalidation

The gate re-derives upstream safety truth directly from the flags on the dry run, kill switch evaluation, and rate/spend/retry evaluation. A `pass`/`clear` status can NOT hide a tampered claim of network/platform/Telegram/credential/LLM/scheduler/retry/dispatch or live-readiness behavior; any such claim blocks the candidate:

  * `dispatch_gate_dry_run_unsafe_behavior_claimed`
  * `dispatch_gate_kill_switch_unsafe_behavior_claimed`
  * `dispatch_gate_rate_policy_unsafe_behavior_claimed`

## Hard invariants

  * `kill_switch_clear_required_but_not_sufficient`
  * `rate_spend_retry_clear_required_but_not_sufficient`
  * `dry_run_complete_required_but_not_sufficient`
  * `one_request_candidate_is_not_dispatch`
  * `candidate_cannot_be_live_executable`
  * `operator_owned_live_gate_remains_future_separate_task`
  * `registry_suppresses_duplicate_request_id_and_fingerprint`
  * `dispatch_gate_revalidates_upstream_safety_flags`
  * `kill_switch_clear_metadata_cannot_hide_unsafe_behavior`
  * `rate_policy_clear_metadata_cannot_hide_retry_or_scheduler_behavior`
  * `dry_run_complete_metadata_cannot_hide_network_or_live_behavior`
  * `unsafe_upstream_behavior_claim_blocks_candidate`
  * `no_credential_hydration`
  * `no_platform_api`
  * `no_telegram_send`
  * `no_network`
  * `no_scheduler`
  * `no_retries`
  * `no_autonomous_posting`
  * `no_financial_advice_or_signal_framing`
  * `missing_ambiguous_or_stale_authority_blocks`

## Next required gate

a redacted immutable audit ledger + an operator-owned live gate readiness review that still performs NO live dispatch; credential hydration and live platform/Telegram dispatch remain separate future operator-owned gates and are NOT enabled here

Exact next task: `TASK_CONTENTOPS_0174TP_TQ_TR_REDACTED_IMMUTABLE_AUDIT_AND_OPERATOR_LIVE_GATE_READINESS_REVIEW_BATCH_V0`

Packet checksum: `f04b25c8ce53fe894143df476bc57ae23c0a23dc27f6effeab375fb01181e9b3`
