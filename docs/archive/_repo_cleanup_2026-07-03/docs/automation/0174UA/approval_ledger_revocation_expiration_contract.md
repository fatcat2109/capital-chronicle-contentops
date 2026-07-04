# 0174UA Approval Ledger Revocation + Expiration Contract

- task_label: `TASK_CONTENTOPS_0174UA_APPROVAL_LEDGER_REVOCATION_EXPIRATION_CONTRACT_V0`
- source_baseline_commit: `dbf1030c64874f96032acd781ac3d7b430dac52c`
- mode: deterministic local contract only
- next heavy batch: `TASK_CONTENTOPS_0174UB_DISPATCH_OUTBOX_REVALIDATION_GATE_CONTRACT_V0`

## Contract Summary

0174UA records approval validity windows, revocation facts, expiration facts,
and validity assessments. Approval facts are evidence, not authority for
dispatch.

## Models

### ApprovalValidityWindow

Binds approval ledger entry id to exact payload hash, platform, payload class,
destination binding, credential handle, operator ref, approval time, expiration
time, max duration, evidence refs, safety flags, and blockers.

### ApprovalRevocationFact

Append-only fact for revoking approval evidence. Raw revocation detail is never
stored. Only `revocation_reason_detail_hash` is retained.

### ApprovalExpirationFact

Append-only evaluation fact. Marks `time_window_expired`,
`missing_validity_window`, `invalid_time_order`, `not_expired_yet`, or
`unknown_or_blocked`.

### ApprovalValidityAssessment

Evaluates candidate payload hash, platform, payload class, destination binding,
credential handle, revocation state, and expiration state.

`can_dispatch=false` always. Future dispatch requires 0174UB revalidation.

### ApprovalRevocationExpirationLedgerPacket

Deterministic redacted packet containing windows, facts, assessments, packet
hash, append-only flags, no-dispatch flags, evidence refs, safety flags, and
blocked reasons.

## Blocking Rules

- Exact payload hash mismatch blocks.
- Platform mismatch blocks.
- Payload class mismatch blocks.
- Destination binding mismatch blocks.
- Credential handle mismatch blocks.
- Revocation fact blocks.
- Expired window blocks.
- Missing validity window blocks.
- Invalid time order blocks.
- Unknown revocation reason fails closed.

## Redaction and Append-Only Rules

- Facts are append-only.
- Revocations never mutate old approvals.
- Expirations are derived evaluation facts.
- Raw revocation detail not persisted.
- U9 audit ledger records facts under `approval_ledger_fact`.
- Credential handles remain symbolic identifiers only.

## Safety Rules

- `approval_granted=false`
- `can_dispatch=false`
- `dispatch_ready=false`
- `live_dispatch_enabled=false`
- `public_postable=false`
- `current_truth_promoted=false`
- `dqr_cleared=false`
- `readiness_cleared=false`
- `llm_provider_called=false`
- `provider_api_called=false`
- `platform_api_called=false`
- `telegram_api_called=false`
- `credential_hydrated=false`
- `env_read=false`
- `network_performed=false`
- `scheduler_enabled=false`
- `autonomous_posting_allowed=false`
- `scraping_performed=false`
- `dm_or_reply_automation_allowed=false`
- `ingestion_repo_mutated=false`

## No-Live Boundary

No dispatch, approval grant, post, schedule, platform API, provider API,
Telegram API, credential/env read, scraping, DM/reply automation, UI edit, or
ingestion repo mutation is implemented.
