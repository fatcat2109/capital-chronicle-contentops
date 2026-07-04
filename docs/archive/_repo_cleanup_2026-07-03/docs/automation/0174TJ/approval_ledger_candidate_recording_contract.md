# 0174TJ Approval Ledger Candidate Recording Contract

Local deterministic gate from 0174TI candidate to append-only ledger recording fact. The fact is local evidence only and never authorizes dispatch, mutates outbox state, calls Telegram, reads env, hydrates credentials, calls providers, or performs network behavior.

## Fact Classes

- `remote_operator_approval_recorded`
- `remote_operator_reject_recorded`
- `remote_operator_edit_request_recorded`
- `candidate_recording_blocked`
- `duplicate_ledger_fact_suppressed`

## Hash Rules

Recording fact hash is sha256 over candidate id/hash, source review ids, approval challenge id, outbox id, exact payload hash, platform, destination binding, operator ref, fact class, scope, expiration proof, and evidence refs.

## Duplicate Rules

Registry suppresses repeated recording fact hashes and returns `duplicate_ledger_fact_suppressed` without appending.

## Safety Flags

- `approval_authorizes_dispatch` = `false`
- `approval_ledger_recorded` = `false`
- `autonomous_posting_allowed` = `false`
- `credential_hydrated` = `false`
- `dispatch_ready` = `false`
- `env_read` = `false`
- `live_ready` = `false`
- `llm_provider_called` = `false`
- `network_performed` = `false`
- `outbox_mutated` = `false`
- `public_postable` = `false`
- `telegram_api_called` = `false`
- `telegram_polling_performed` = `false`
- `telegram_send_performed` = `false`
- `webhook_enabled` = `false`

## Next Gate

TASK_CONTENTOPS_0174TK_APPROVAL_LEDGER_REVOCATION_EXPIRATION_CONTRACT_V0
