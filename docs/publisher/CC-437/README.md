# CC-437: queued Discord posts and visible card causes

The five older call cards each had Discord `DEFINITE_NO_WRITE` while their other
API destinations were confirmed. The minute consumer treated each as unfinished
API work and spent all five card slots on them again. New cards and later updates
never reached preparation. The five registered analysis links had no recurring
consumer after their initial attempt was skipped by the earlier day circuit.

The existing minute consumer now resumes those links through the same coordinator.
An unattempted link whose Main plan has ended expires without a public send. The
five retained links all refer to plans marked EXPIRED in the current Main export.
Registered payloads, thread parents, public identities and uncertain attempts stay
bound to their original recovery path.

Settled destinations and parent waits no longer consume fresh API card slots.
Fresh work precedes older partial work. The existing `record_run` JSONL now retains
each card key, status, preparation error, destination cause, parent dependency and
run-limit wait. An unstarted run whose member calls have all ended is retired with
`RUN_HAS_NO_CURRENT_CARDS`. The retained failing run references a format-3 card
without the `short_id` that the format-4 renderer accesses.

New cards freeze their Discord delivery route when queued. Without a bot token,
they use the registered announcements channel. Later updates inherit that card's
route. Existing registered cards retain their original thread route. Newly queued
late recovery copy identifies a delayed update and its original registration
clock in ET; dispatch time never replaces event time.

Discord's [Execute Webhook documentation](https://docs.discord.com/developers/resources/webhook#execute-webhook)
was checked in BrowserOS Neo on 10 November. Webhooks support an existing thread
via `thread_id`; creating one with `thread_name` requires a forum or media channel.
The pinned announcements channel uses the channel option specified by CC-437.
No browser publication, credential change, chat message or schedule change is
part of this change.

Base: Publisher operating HEAD `17c49b960d54a7dc6e090ab048fb047bd6c04a89`.
Fetched `origin/master` predates the live consumers. CC-435 remains on its own
branch. Existing lane and operating-root changes are inventoried by path and
hash in `pre-existing-work.json`; they are excluded from this item's commits.

`before.json` records the original queue and pending card metadata. `launch.json`
records the observed launch arguments, gpt-6.1-sol/max, as
CONFIGURED_NOT_OBSERVED for actual model telemetry. No editorial model call is
needed for this deterministic routing repair.

Static AST parsing, diff checks and lint of the changed routing modules, CLI and
new test pass. The analysis module and older card test retain the existing lint
items listed in `static-checks.json`. Targeted tests, operating integration and
the next real consumer readback follow after CC-035's 22:30 GMT+7 test embargo.

Timed continuation: the branch is pushed through `d8094824`; no pytest process
was started under CC-035 and no source was installed. `continuation.json` records
the exact operating HEAD and WIP hash comparison. After 22:30 GMT+7, run the new
Discord queue test, the existing call-card regression, the analysis-page regression
and the status-export/CLI regression in serial targeted runs (under one minute
each until 23:00). Then forward-integrate this branch into the Publisher operating
root, observe the unchanged minute task once, and retain its exact Discord
confirmations and per-card causes before closing acceptance.

Resume, 10 November 2026, 23:10 GMT+7: the operating root had advanced to
`753c678d7f92e3b3da986324411ba8a9ea3a39e2`. That exact commit was merged into
this item's existing branch, preserving all nine tracked work-in-progress
paths across the two checkouts. The launch explicitly configured
gpt-6.1-sol/max; supported actual model telemetry remains
`CONFIGURED_NOT_OBSERVED`. No editorial model call was made.

The routing, card and analysis-page selection passes 62 tests. The status
recovery, export-age and CLI/contract selection passes 46 tests. Its initial
run found one outdated expectation: CC-400 rejects a null expiry before the
recovery window is evaluated. The regression now asserts that exact field
rejection and an empty outbox, retaining the real stale-post safeguard.

The fresh read-only queue snapshot is `resume-before.json`: five Discord
analysis links remain READY; other 10 November rows already have terminal
outcomes. Runtime integration and the unchanged minute consumer are checked
separately below in the final integration evidence.

The first installed minute run finished at 23:12:44 GMT+7. It closed all five
Discord links as `PLAN_ALREADY_EXPIRED`, leaving zero READY Discord rows.
Every one of its 31 NOT_STARTED/WAITING entries had a key and cause. It also
exposed three preparation failures, retained in `first-installed-runs.json`.

The follow-up keeps scored endings in the current-state map and retires an
unattempted fill update when that call has ended. A frozen card is checked
against its actual intent and parent, rather than being recomposed with a
later formatter. Exact intent equality and public-data checks stay active.
An entirely unsent frozen copy containing the old private DEMO disclosure is
closed with `PRIVATE_OR_EXECUTION_COPY_FORBIDDEN`; confirmed and uncertain
copies remain with their original recovery owner. Original bytes stay intact.
The run record also keeps the coordinator's `safe_error_classification`.

These observed-failure repairs pass 58 targeted tests, plus the focused
adapter-cause recording test. The live secret owner reports that the Discord
bot route is not configured. Existing registered thread cards retain that
route; only newly queued cards select webhook channel delivery. Their
credential constraint is separate from the cleared READY queue and visible
run causes. No fresh Discord card confirmation is claimed by these tests.

## Live acceptance, 10 November 2026, 23:29 GMT+7

All three acceptance conditions pass in `live-consumer.json`:

- Zero 10 November Discord rows remain READY. The five expired analysis links
  retain their exact `PLAN_ALREADY_EXPIRED` cause.
- The next Main run, `plan-run-post-074c47181a90a973118c3f48e0c8d271`,
  posted its run announcement and all four new cards to Discord. Each has
  `DISPATCH_CONFIRMED`, `RECONCILED_CONFIRMED` and an API readback identity.
  The cards use the new webhook channel route. Source events remain at
  23:18:25 GMT+7; observed dispatches are 23:19:47–23:22:42 GMT+7.
- The completed minute run at 23:29:02 GMT+7 has zero NOT_STARTED cards.
  All 25 waiting cards have their key and cause in the existing run record.

The branch and operating root contain the tested repairs at
`320523f4d6faf2d306c0f2a5c6a6dfae4ef7e658`; installation and scheduled
consumption are recorded separately from the public readbacks. There are
128 distinct passing targeted test cases across the successful selections
in `tests-summary.json`. No suite-wide result is claimed.

Existing registered thread cards retain their bot-token refusal. Their
payloads and parents were not rewritten to take the new-card channel route.
The remaining waits name those parent dependencies or their bounded work
limit; they do not conceal a READY Discord queue. All original work in
progress remains intact. Two operating JSONL files gained runtime appends,
and their original bytes are still exact prefixes. No schedule changed.
