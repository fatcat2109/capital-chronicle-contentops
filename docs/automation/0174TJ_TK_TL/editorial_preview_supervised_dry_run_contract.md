# Editorial Agent + Platform Preview + Supervised Dry-Run Contract (0174TJ/TK/TL)

Task: TASK_CONTENTOPS_0174TJ_TK_TL_EDITORIAL_PREVIEW_AND_SUPERVISED_DRY_RUN_CONTRACT_BATCH_V0
Model: EDITORIAL_PREVIEW_SUPERVISED_DRY_RUN_CONTRACT_0174TJ_TK_TL (0174TJ_TK_TL_EDITORIAL_PREVIEW_DRY_RUN_V1)
Source baseline commit: 27ba55ce08aa8cae1b509e6404edd652e4d31c0c
Mode: Implementation Mode. Deterministic, stdlib-only, local authority batch.

> [!IMPORTANT]
> This batch introduces NO live behavior: no platform API call, no live preview
> render, no Telegram send, no LLM call, no network call, no credential read or
> hydration, no environment or `.env` read, no keyring or browser-session read,
> no OAuth, no scheduler, and no auto retry. It is the deterministic local
> editorial agent + platform preview + supervised dry-run authority contract
> only.

## Strategic Posture
- Manual posting is the **fallback** path, not the strategic destination.
- **Automation is the main build path.**
- **Autonomous posting is forbidden.**
- **Supervised publishing is the final product.**

## What This Batch Proves
0174ED proved Jim approved an **exact payload hash**. 0174EE proved that exact,
validated approval becomes a **single local outbox candidate** without duplicate
dispatch risk. 0174TG/TH/TI proved a remote operator review can only ever yield
`remote_review_approved_not_dispatched`. This batch proves the final three local
authority steps WITHOUT touching any live surface:

- **0174TJ Editorial Agent** -- `run_editorial_agent` consumes a valid
  `remote_review_approved_not_dispatched` result plus the exact 0174EE outbox
  entry and produces an `EditorialDecisionRecord`. It is a deterministic,
  rule-based gate (never an LLM call). It **fails closed** on any financial
  advice, buy/sell/hold call, position sizing, guaranteed prediction, or trade
  signal framing, and only allows grounded/context content lanes. Outcome is
  only ever `editorial_approved_not_dispatched`.
- **0174TK Platform Preview** -- `build_platform_preview` consumes a valid
  editorial record + the same outbox entry and builds a LOCAL, redacted
  `PlatformPreviewRecord`. It **never** renders against a live platform or calls
  a platform API. Outcome is only ever `platform_preview_built_not_dispatched`.
- **0174TL Supervised Dry Run** -- `run_supervised_dry_run` re-proves EVERY
  cross-binding (payload hash, idempotency key, outbox entry id, approval ledger
  entry id, editorial id, preview id) across all four artifacts and emits
  `supervised_dry_run_complete_not_dispatched`. It confirms readiness for a
  FUTURE supervised gate but never dispatches.

## Allowed Content Lanes
- `grounded_explainer`
- `grounded_macro_context`
- `grounded_news_context`
- `market_structure_education`
- `neutral_market_recap`

## Core Objects
- **EditorialDecisionRecord** -- the deterministic 0174TJ editorial gate output.
- **PlatformPreviewRecord** -- the local, redacted 0174TK preview output.
- **SupervisedDryRunRecord** -- the 0174TL end-to-end cross-binding proof.

## Hard Invariants
- Editorial approval is **not** dispatch; a preview is **not** a post; a dry run
  is **not** a live write; none of them hydrate credentials.
- Financial advice / buy-sell-hold / sizing / guaranteed predictions / signal
  framing **fail closed** in both editorial and preview text.
- Every stage re-proves the exact upstream authority binding; any payload hash,
  idempotency key, or id mismatch blocks.
- No raw provider/platform response, token, chat id, username, phone, or webhook
  url is ever stored.
- Missing or ambiguous state blocks (fail closed).

## Next Task
Recommended next task after PASS:
`TASK_CONTENTOPS_0174TM_TN_TO_KILL_SWITCH_RATE_POLICY_AND_ONE_REQUEST_SUPERVISED_DISPATCH_GATE_BATCH_V0`

Next required gate: kill switch contract, rate/spend policy contract, and a one-request/no-auto-retry supervised dispatch gate with redacted immutable audit, all still local until an explicit operator-owned live gate; credential hydration and live platform/Telegram dispatch remain separate future operator-owned gates and are NOT enabled here
