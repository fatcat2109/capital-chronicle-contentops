# X CDP Exact Live-Click Scope Decision Runbook

Task: `TASK_CONTENTOPS_V6_X_CDP_EXACT_SEPARATE_LIVE_CLICK_SCOPE_DECISION_V0`

## What this packet does

- Consumes the exact live-click authorization request evidence.
- Records one operator decision: `deny`, `defer`, or `approve_future_scope`.
- Re-validates request identity, packet IDs, payload hash, prerequisites, stop conditions, and no-live-action flags.

## What it never does

- No browser launch or CDP probe.
- No DOM, cookie, storage, token, header, session, env, or credential read.
- No X API, provider call, public URL fetch, registry append, dispatch, publish, click, comment, DM, or reaction.

> [!IMPORTANT]
> `APPROVED_FOR_FUTURE_EXACT_LIVE_TASK` is not a click instruction. It only allows a later exact live task to be considered after fresh verification.

## Operator stop conditions

Stop without live action if any packet ID, payload hash, account, destination, profile guard, kill-switch, or post-click URL capture requirement is uncertain.
