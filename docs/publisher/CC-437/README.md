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
