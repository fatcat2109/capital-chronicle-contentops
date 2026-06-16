# Dispatch Outbox + Idempotency + Preflight Contract (0174EE)

Task: TASK_CONTENTOPS_0174EE_DISPATCH_OUTBOX_IDEMPOTENCY_AND_PREFLIGHT_CONTRACT_BATCH_V0
Model: DISPATCH_OUTBOX_IDEMPOTENCY_CONTRACT_0174EE (0174EE_DISPATCH_OUTBOX_IDEMPOTENCY_V1)
Source baseline commit: b07848e61fef10917a38e344743f00a9de655cbb
Mode: Implementation Mode. Deterministic, stdlib-only, local authority layer.

> [!IMPORTANT]
> This module introduces NO live dispatch, NO posting, NO platform API call, NO
> network call, NO credential read or hydration, NO environment or `.env` read,
> NO keyring or browser-session read, NO OAuth, NO Telegram behavior, NO LLM
> behavior, NO scheduler, and NO auto retry. It is the deterministic local
> dispatch-outbox + idempotency + preflight authority contract only.

## Strategic Posture
- Manual posting is the **fallback** path, not the strategic destination.
- **Automation is the main build path.**
- **Autonomous posting is forbidden.**
- **Supervised publishing is the final product.**

## What This Contract Proves
0174ED proved Jim approved an **exact payload hash**. 0174EE proves that exact,
validated approval can be represented as a **single local outbox candidate**
without duplicate dispatch risk. It consumes 0174ED outputs (current payload,
approval ledger entry, and the `validate_approval_for_current_payload` result);
it does not bypass them. It is still **not live-ready**.

## Idempotency Key Algorithm
- Algorithm: `sha256` over canonical JSON (sorted keys, compact separators).
- Computed over authority-bearing fields ONLY; incidental extra keys never
  affect it. Fail-closed: a candidate carrying forbidden material is refused.

## Idempotency Key Inputs (authority-bearing, non-secret)
- `outbox_schema`
- `outbox_schema_version`
- `payload_hash`
- `platform`
- `destination_binding_id`
- `credential_handle_id`
- `media_manifest_hash`
- `visibility_class`
- `dispatch_intent_class`
- `content_lane`
- `policy_snapshot_id`
- `platform_adapter_version`
- `approval_ledger_entry_id`
- `challenge_id`
- `operator_id`

## Idempotency Key Excludes (never keyed or stored)
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
- `raw_platform_response`
- `raw_sensitive_account_id`
- `request_headers`
- `cookies`
- `browser_session_data`
- `local_absolute_path_if_sensitive`

A credential is represented ONLY by its symbolic `credential_handle_id` (a
0174EC handle id). No raw token, api key, env value, `.env` value, secret path,
raw provider/platform response, request headers, cookies, browser-session data,
raw sensitive account id, or sensitive local absolute path is ever keyed or
persisted.

## Core Objects
- **DispatchOutboxCandidate** -- canonical authority-bearing candidate built
  from 0174ED outputs (`build_outbox_candidate`).
- **DispatchPreflightResult** -- the fail-closed decision
  (`run_dispatch_preflight`).
- **DispatchOutboxEntry** -- an append-ready local outbox record
  (`build_outbox_entry`); state `local_outbox_record_created_not_dispatched`.
- **DispatchIdempotencyRecord** -- key -> first entry record
  (`build_idempotency_record`).
- **DispatchOutboxRegistry** -- append-only registry enforcing idempotency-key
  uniqueness with deterministic duplicate suppression.
- **RedactedOutboxAudit** -- symbolic/redacted audit
  (`build_redacted_outbox_audit`).

## Outbox Creation Is Blocked Unless
1. approval validation status is PASS;
2. approval validity class is `approval_valid_for_payload_not_dispatch`;
3. current payload hash matches the approved hash;
4. binding match is true;
5. expired is false;
6. revoked is false;
7. upstream `dispatch_ready`/`live_ready`/`approval_authorizes_dispatch` are
   false;
8. all required authority fields are present (no inferred readiness);
9. a gate/kill-switch snapshot is present AND symbolically allows local outbox
   candidacy;
10. the credential handle is symbolic only;
11. no forbidden/raw credential-shaped value is present;
12. the idempotency key is not already active (else duplicate suppression
    returns the existing record).

## Invariants
- The idempotency key is deterministic for an identical candidate and changes
  if ANY authority field changes (payload hash, platform, destination binding,
  credential handle, media manifest hash, visibility, dispatch intent, content
  lane, policy/gate snapshot, adapter version, approval ledger entry, challenge
  id, operator id).
- A duplicate idempotency key is **suppressed**, not appended: the registry
  returns the existing entry id and appends nothing.
- Readiness is **never** inferred from the absence of blockers; missing
  validation, missing gate snapshot, or a non-symbolic credential blocks.
- An approval valid for payload A can **never** create an outbox entry for a
  substituted payload B.
- **R1 authority-chain hardening:** the preflight ALWAYS recomputes the current
  payload hash from the supplied current payload
  (`preflight_recomputes_current_payload_hash_before_outbox`) and uses it for
  the candidate + idempotency key. A stale/foreign validation result is rejected
  fail-closed (`stale_validation_result_cannot_create_outbox`) when its
  `current_payload_hash`, `approved_payload_hash`, `ledger_entry_id`, or
  `challenge_id` does not bind the same approval entry + recomputed payload.
- Audit objects contain redacted values only.

## Authority Boundary
Outbox state never implies dispatch-ready or live-ready. Every preflight
result, outbox entry, registry result, and audit reports
`dispatch_performed = False`, `live_request_performed = False`,
`platform_api_called = False`, `credential_hydrated = False`,
`auto_retry_allowed = False`, and `scheduler_enabled = False`.

## Next Task
Recommended next task after PASS:
`TASK_CONTENTOPS_0174TG_TELEGRAM_REMOTE_OPERATOR_INBOX_CONTRACT_V0`

Next required gate: Telegram remote operator inbox contract (deterministic local message intake model only; no bot polling, no getUpdates, no send, no webhook), then LLM intent parser contract, Telegram review challenge contract, editorial agent, platform preview integration, and end-to-end dry run before any supervised live dispatch gate; credential hydration and live platform dispatch remain separate future operator-owned gates and are NOT enabled here
