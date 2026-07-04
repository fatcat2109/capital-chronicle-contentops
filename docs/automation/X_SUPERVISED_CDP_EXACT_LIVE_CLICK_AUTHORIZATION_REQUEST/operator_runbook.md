# X CDP Exact Separate Live-Click Authorization Request

Task: `TASK_CONTENTOPS_V6_X_CDP_EXACT_SEPARATE_LIVE_CLICK_AUTHORIZATION_REQUEST_V0`

## Scope

This packet converts the final local X CDP pre-click rehearsal evidence into an
operator-review authorization request for a later exact live task.

It is a request packet only. It is not live authorization and it does not click.

## Boundary

- No browser launch.
- No CDP probe.
- No DOM, cookie, storage, token, header, env, credential, or session read.
- No X API, paid API, provider call, scrape, public URL fetch, scheduler, retry,
  approval ledger write, executable outbox write, registry append, dispatch,
  publish, comment, DM, reaction, or live click.
- Raw GO phrase is not stored in evidence.

## Ready request meaning

`EXACT_SEPARATE_LIVE_CLICK_AUTHORIZATION_REQUEST_READY_FOR_OPERATOR_REVIEW`
means only that local evidence is internally consistent enough for Jim/operator
review in a later exact live-scope task.

It still records:

- `live_click_allowed_now=false`
- `live_click_allowed=false`
- `live_click_performed=false`
- `approval_ledger_entry_created=false`
- `executable_outbox_entry_created=false`
- `publication_registry_record_appended=false`
- `public_url_capture_performed=false`

## Future exact live task prerequisites

A future live-scope task must independently verify:

1. explicit user live-scope approval in that future task;
2. payload hash match;
3. pre-live packet ID match;
4. GO-gate packet ID match;
5. authorization packet ID match;
6. final rehearsal packet ID match;
7. fresh ContentOps profile guard pass;
8. operator-visible X account and destination match;
9. kill-switch transition only inside the exact live task;
10. post-click public URL capture before any registry append.

## Stop conditions

Stop before any future click if any of these are true:

1. payload hash or packet ID changed;
2. ContentOps profile/account/destination is uncertain;
3. X compose UI or click target is uncertain;
4. future task lacks explicit live scope;
5. post-click public URL capture cannot be completed;
6. registry append would be attempted before captured public URL exists.
