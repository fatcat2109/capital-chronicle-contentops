# 0174TG Telegram Remote Operator Inbox Contract

This contract defines local redacted Telegram remote operator inbox messages. It does not define channel dispatch behavior.

## Role Separation

- Remote Operator Inbox: future operator review decisions.
- Channel Dispatch Destination: future public/channel send target.

0174TG implements only the first role.

## Message Model

`RemoteOperatorInboxMessage` binds redacted message text, operator identity ref, timestamp bucket, optional approval/outbox/payload refs, evidence refs, and safety flags. Raw Telegram updates are not stored.

## Intent Candidate Model

`ParsedOperatorIntentCandidate` maps exact local phrases to `approve`, `reject`, `edit_request`, `hold`, or `unknown`. Every candidate remains blocked and reports `valid_for_approval=false` and `valid_for_dispatch=false`.

## Dedupe / Replay

The registry is append-only. Dedupe uses message text hash, operator identity ref, timestamp bucket, and inbox message id. Duplicate replay is suppressed and creates no approval or dispatch.

## Safety Flags

- `approval_created` = `false`
- `autonomous_posting_allowed` = `false`
- `autonomous_reply_performed` = `false`
- `credential_hydrated` = `false`
- `dispatch_created` = `false`
- `dispatch_ready` = `false`
- `dm_performed` = `false`
- `env_read` = `false`
- `ledger_mutated` = `false`
- `live_ready` = `false`
- `network_performed` = `false`
- `outbox_mutated` = `false`
- `public_postable` = `false`
- `scheduler_enabled` = `false`
- `scraping_performed` = `false`
- `telegram_api_called` = `false`
- `telegram_polling_performed` = `false`
- `telegram_send_performed` = `false`
- `webhook_enabled` = `false`

## Next Gate

TASK_CONTENTOPS_0174TH_TELEGRAM_REVIEW_CHALLENGE_CONTRACT_V0
