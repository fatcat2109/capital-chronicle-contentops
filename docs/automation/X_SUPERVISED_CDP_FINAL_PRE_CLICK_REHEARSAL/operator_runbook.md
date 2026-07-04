# X CDP Final Pre-Click Rehearsal Dry Run

Task: `TASK_CONTENTOPS_V6_X_CDP_FINAL_PRE_CLICK_REHEARSAL_DRY_RUN_V0`

## Scope

This rehearsal composes the local X CDP chain before any future exact live task:

1. pre-live post packet;
2. hash-only GO-phrase gate packet;
3. separate live-click authorization packet;
4. kill-switch and rollback expectations;
5. post-click capture plan.

## Boundary

- No browser launch.
- No CDP probe.
- No DOM, cookie, storage, token, header, env, credential, or session read.
- No X API, paid API, provider call, scrape, public URL fetch, scheduler, retry,
  approval ledger write, executable outbox write, registry append, dispatch,
  publish, comment, DM, reaction, or live click.
- Raw GO phrase is not stored in evidence.

## Passing rehearsal meaning

`FINAL_PRE_CLICK_REHEARSAL_READY_FOR_SEPARATE_EXACT_LIVE_TASK` means only that
local evidence is internally consistent enough to support a future separately
approved live-scope decision. It is not approval to click.

## Stop conditions

Stop before any future click if any of these are true:

1. payload hash or packet ID changed;
2. ContentOps profile/account/destination is uncertain;
3. X compose UI differs from the expected operator-visible surface;
4. post-click public URL capture cannot be completed;
5. registry append would be attempted before a future captured public URL exists.

## Future live task minimum expectations

A separate exact task must still explicitly authorize live behavior and re-check:

1. payload hash;
2. pre-live packet ID;
3. GO-gate packet ID;
4. authorization packet ID;
5. final rehearsal packet ID;
6. ContentOps browser profile and account binding;
7. kill-switch state and rollback checklist;
8. post-click public URL capture and registry append rules.
