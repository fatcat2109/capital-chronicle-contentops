# X CDP Live-Click Authorization Packet Dry Run

Task: `TASK_CONTENTOPS_V6_X_CDP_SEPARATE_LIVE_CLICK_AUTHORIZATION_PACKET_DRY_RUN_V0`

## Scope

This packet composes the X pre-live post packet, the hash-only GO-phrase gate,
kill-switch acknowledgement, rollback checklist, and post-click public URL
capture expectations.

## Boundary

- No browser launch.
- No CDP probe.
- No DOM, cookie, storage, token, header, or session read.
- No X API, provider call, env read, credential read, public URL fetch, scrape,
  scheduler, retry, registry append, dispatch, publish, comment, DM, reaction,
  or live click.
- The raw GO phrase is not stored in evidence.

## Passing packet meaning

`AUTHORIZATION_PACKET_READY_FOR_EXACT_SEPARATE_LIVE_TASK` means only that a
future, separately approved live task has enough local evidence to rehearse from.
It is not approval to click.

## Future live task minimum expectations

A separate exact live task must still explicitly authorize any click and must
re-check:

1. payload hash;
2. pre-live packet ID;
3. GO-gate packet ID;
4. active ContentOps browser profile;
5. X account binding and destination expectation;
6. kill-switch state;
7. rollback/stop conditions;
8. post-click public URL capture and registry-append rules.
