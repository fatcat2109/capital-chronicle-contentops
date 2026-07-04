# 0174TI Telegram Approval Ledger Candidate Contract

Local-only bridge from 0174TH validation to approval-ledger candidate. Candidates are evidence only and cannot record ledger facts, mutate outbox state, dispatch, call Telegram, read env, hydrate credentials, call providers, or perform network behavior.

## Candidate Validity Classes

- `approval_ledger_candidate_valid_local_only`
- `approval_ledger_candidate_blocked`
- `approval_ledger_candidate_duplicate_suppressed`

## Candidate Intent Classes

- `approval_candidate`
- `reject_candidate`
- `edit_request_candidate`
- `blocked_candidate`

## Hash Rules

Candidate hash is sha256 over exact authority fields: validation id, challenge id, reply id, approval challenge id, outbox id, payload hash, platform binding, destination binding, operator identity, reply class, nonce/hash/sender/expiration/activity proofs.

## Non-Mutation Rules

Every candidate remains local-only. It cannot mutate approval ledger, outbox, dispatch state, live state, or public-postable state.

## Safety Flags

- `approval_ledger_mutated` = `false`
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

TASK_CONTENTOPS_0174TJ_APPROVAL_LEDGER_CANDIDATE_TO_LEDGER_RECORDING_CONTRACT_V0
