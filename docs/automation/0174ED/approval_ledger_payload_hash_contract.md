# Approval Ledger + Payload Hash Contract (0174ED)

Task: TASK_CONTENTOPS_0174ED_APPROVAL_LEDGER_AND_PAYLOAD_HASH_CONTRACT_V0
Model: APPROVAL_LEDGER_PAYLOAD_HASH_CONTRACT_0174ED (0174ED_APPROVAL_LEDGER_PAYLOAD_HASH_V1)
Source baseline commit: b07e220e4d5fdebeb47368dbc08a10f28c9c4bbd
Mode: Implementation Mode. Deterministic, stdlib-only, local authority layer.

> [!IMPORTANT]
> This module introduces NO live posting, NO dispatch, NO outbox creation, NO
> credential read or hydration, NO environment or `.env` read, NO keyring or
> browser-session read, NO OAuth, NO network call, NO Telegram behavior, NO
> LLM behavior, and NO scheduler. It is the deterministic approval/hash
> authority contract only.

## Strategic Posture
- Manual posting is the **fallback** path, not the strategic destination.
- **Automation is the main build path.**
- **Autonomous posting is forbidden.**
- **Supervised publishing is the final product.**

## What This Contract Proves
It proves that Jim approved an **exact payload**, not a vague idea. An approval
is bound to a deterministic sha256 **payload hash** computed over the exact
authority-bearing fields below. If any of those fields change, the hash
changes, and the prior approval is no longer valid for the new payload.

## Payload Hash Algorithm
- Algorithm: `sha256` over canonical JSON (sorted keys, compact separators).
- The hash includes explicit schema + version fields.
- The hash is computed over authority-bearing fields ONLY; incidental extra
  keys never affect it.

## Payload Hash Inputs (authority-bearing, non-secret)
- `payload_schema`
- `payload_schema_version`
- `platform`
- `payload_text`
- `platform_formatting`
- `thread_split`
- `disclosure_class`
- `destination_binding_id`
- `credential_handle_id`
- `media_manifest_hash`
- `visibility_class`
- `content_lane`
- `policy_snapshot_id`
- `platform_adapter_version`

## Payload Hash Excludes (never hashed or stored)
- `raw_credential`
- `raw_token`
- `api_key`
- `access_token`
- `refresh_token`
- `bearer_token`
- `client_secret`
- `raw_env_var`
- `dotenv_value`
- `secret_path`
- `raw_provider_response`
- `raw_sensitive_account_id`
- `local_absolute_path_if_sensitive`

A credential is represented ONLY by its symbolic `credential_handle_id` (a
0174EC handle id). No raw token, api key, env value, `.env` value, secret path,
raw provider response, raw sensitive account id, or sensitive local absolute
path is ever included in the hash or persisted.

## Core Objects
- **PlatformPayloadForApproval** -- the canonical authority-bearing payload
  dict (`canonical_payload_dict`).
- **ApprovalChallenge** -- an expiring, one-time challenge bound to an exact
  payload hash (`create_approval_challenge`).
- **ApprovalLedgerEntry** -- an append-only approval fact (`record_approval`).
- **ApprovalLedger** -- an append-only collection of approval + revocation
  facts; nothing is mutated in place.
- **Revocation event** -- an append-only revocation fact (`record_revocation`).
- **ApprovalValidationResult** -- the DERIVED validity result
  (`validate_approval_for_current_payload`).
- **Redacted audit summary** -- symbolic/redacted audit
  (`build_redacted_approval_audit`).

## Invariants
- Any change to payload text, platform, destination/account binding,
  credential handle id, media manifest hash, visibility, disclosure, or
  platform formatting changes the payload hash.
- Approval binds an exact payload hash.
- Approval can expire and can be revoked.
- Approval is invalid if the current payload hash differs from the approved
  hash, if the challenge is expired, or if any binding field differs.
- Approval validity is **derived, never assumed**.
- Approval does **not** authorize dispatch, does **not** create an outbox
  entry, and does **not** hydrate credentials in this task.
- Append-only: revocation and invalidation are new ledger facts or derived
  status, never mutation of a prior approval fact.
- Audit objects contain redacted values only; no raw credential/token/api-key
  is stored, hashed, prefixed, suffixed, fingerprinted, or logged.

## Authority Boundary
Approval state never implies dispatch-ready or live-ready. Every validation
result and audit reports `dispatch_ready = False` and `live_ready = False`.
Future supervised dispatch remains blocked / future-gated.

## Next Task
Recommended next task after PASS:
`TASK_CONTENTOPS_0174EE_DISPATCH_OUTBOX_AND_IDEMPOTENCY_CONTRACT_V0`

Next required gate: dispatch outbox + idempotency contract, then kill switch, rate/spend/retry policy, one-request/no-auto-retry supervised dispatch, and redacted immutable audit before any supervised live write; credential hydration remains a separate future operator-owned gate and is NOT enabled here
