# Remote Operator Inbox + Intent + Review Challenge Contract (0174TG/TH/TI)

Task: TASK_CONTENTOPS_0174TG_TH_TI_REMOTE_INBOX_INTENT_AND_REVIEW_CHALLENGE_CONTRACT_BATCH_V0
Model: REMOTE_OPERATOR_INBOX_INTENT_REVIEW_CONTRACT_0174TG_TH_TI (0174TG_TH_TI_REMOTE_INBOX_INTENT_REVIEW_V1)
Source baseline commit: 1f5f8642c6d54ce3ffc7c0c29c9a9f4427337a06
Mode: Implementation Mode. Deterministic, stdlib-only, local authority batch.

> [!IMPORTANT]
> This batch introduces NO Telegram behavior (no bot polling, no getUpdates, no
> sendMessage, no webhook, no Telegram SDK), NO LLM call, NO live dispatch, NO
> posting, NO platform API call, NO network call, NO credential read or
> hydration, NO environment or `.env` read, NO keyring or browser-session read,
> NO OAuth, NO scheduler, and NO auto retry. It is the deterministic local
> remote-operator inbox + intent parser + review challenge authority contract
> only.

## Strategic Posture
- Manual posting is the **fallback** path, not the strategic destination.
- **Automation is the main build path.**
- **Autonomous posting is forbidden.**
- **Supervised publishing is the final product.**

## What This Batch Proves
0174ED proved Jim approved an **exact payload hash**. 0174EE proved that exact,
validated approval becomes a **single local outbox candidate** without duplicate
dispatch risk. This batch proves the next three local authority steps WITHOUT
touching Telegram, an LLM, or any live surface:

- **0174TG Remote Operator Inbox** -- normalizes a Telegram-LIKE inbound message
  object into a symbolic, redacted `RemoteOperatorInboxRecord`. Only a verified
  operator class on the `telegram_remote_operator_surface` surface with a present chat
  binding continues. Raw chat id / username / phone / token / bot token /
  webhook url / raw provider update JSON are rejected or redacted; no raw
  Telegram update object is persisted.
- **0174TH Intent Parser** -- a deterministic, rule-based
  `parse_operator_intent` that simulates the boundary an LLM may later fill but
  NEVER calls an LLM. It fails closed on ambiguity and never treats vague
  agreement / emoji as approval. `explicit_approve` requires the exact challenge
  phrase (or the exact challenge id alongside the phrase).
- **0174TI Review Challenge** -- `create_review_challenge` consumes a valid
  0174EE outbox entry and binds the exact outbox entry id, idempotency key, and
  payload hash, requiring an exact human approval phrase.
  `validate_review_challenge_response` can only ever produce
  `remote_review_approved_not_dispatched` -- never dispatch.

## Supported Intent Classes
- `explicit_review_request`
- `explicit_approve`
- `explicit_reject`
- `explicit_edit_request`
- `status_request`
- `cancel_request`
- `ambiguous_or_unsupported`

## Core Objects
- **RemoteOperatorInboundEnvelope / RemoteOperatorIdentityProof** -- the symbolic
  input shape consumed by `normalize_inbound_envelope`.
- **RemoteOperatorInboxRecord** -- the normalized, redacted record.
- **RemoteOperatorInboxRegistry** -- append-only local registry.
- **OperatorIntentCandidate / OperatorIntentParseResult /
  IntentParserPolicySnapshot** -- the deterministic parse boundary.
- **RemoteReviewChallenge / RemoteReviewChallengeValidation /
  RemoteReviewChallengeRegistry** -- the bound review-challenge authority.

## Hard Invariants
- Remote approval is **not** dispatch; challenge approval is **not** platform
  posting; the review challenge **never** hydrates credentials.
- No raw Telegram/provider update is stored; no raw token / api key / chat id /
  username / phone / webhook url is stored.
- The parser is deterministic and rule-based; it never calls an LLM and never
  creates approval, outbox, dispatch, or live state.
- A challenge binds the EXACT outbox entry id, idempotency key, and payload
  hash; changing any of them blocks validation.
- Reject / edit / status / cancel never validate as approval; a valid approval
  yields only `remote_review_approved_not_dispatched`.
- A revoked/invalidated challenge blocks later approval; a duplicate challenge id
  is suppressed, not appended.
- Missing or ambiguous state blocks (fail closed).

## Next Task
Recommended next task after PASS:
`TASK_CONTENTOPS_0174TJ_TK_TL_EDITORIAL_PREVIEW_AND_SUPERVISED_DRY_RUN_CONTRACT_BATCH_V0`

Next required gate: editorial agent + platform preview integration + supervised end-to-end dry run (still local, no live dispatch), then kill switch, rate/spend/retry policy, one-request/no-auto-retry supervised dispatch, and redacted immutable audit before any supervised live write; credential hydration and live platform/Telegram dispatch remain separate future operator-owned gates and are NOT enabled here
