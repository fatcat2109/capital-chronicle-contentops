# CC-458 — waiting X reply tabs

Decision 123 changes CC-455's delivery to the Neo group **X replies: press Reply**.
The existing pack preparation, source binding, target accounts, mentions and manual
reply observer stay in use. AGY authors the native response through the existing
bounded text CLI (`gemini-3.8-flash-high/high`). Call records distinguish configured
values from runtime telemetry; self-reported response labels are not telemetry.

The base is operating HEAD `f7c3083f2b5a8dfd5861af2dca3962a1d0163a85`, which contains
live CC-455. Remote master predates those applied Publisher changes. The earlier
three lane modifications remain outside this delivery; `run-context.json` records
their hashes. `launch-arguments.json` reads back `gpt-6.1-sol/max` as configured,
with actual runtime values `CONFIGURED_NOT_OBSERVED`.

`scripts/run_sourced_replies.py tabs-refresh` runs one real refresh. `tabs-status`
reads the state; `tabs-enable` enables the two-hour gate after a successful real
refresh. The existing `scripts/plan_status_posts.py --publish` minute entry calls
that gate independently of Main's export status. No task or schedule changes.
The gate runs day and night and waits two hours after failures, without retries.

The same durable store retains state snapshots and run results in internal
outbox destinations and serializes refreshes with its existing lease. The pack
JSON/HTML still feeds the private desk. Build freshness is 120 minutes; a waiting
tab expires six hours after the target post. Historical files stay unchanged.

The Neo transport uses its one existing window, lists tabs before opening, and
opens a temporary readback/mentions page in its own group. Visible own-reply
detail pages supply exact author, post and parent identities to the existing
observer; unrelated or ambiguous edges produce no reply row. The reader page
closes afterward. No private endpoint or desktop automation is used.

The draft group holds at most five pages. The refresh fills an empty reply box
and checks its retained text and target. It never presses Reply, likes or follows.
It closes only its saved sent/expired tabs. Changed text, moved pages and other
agents' pages are preserved. A failed drafter leaves the waiting group alone.

Manual readbacks now retain post-to-reply minutes. The existing 24-hour metrics
and fourteen-day report include under-two-hour, two-to-six-hour and later cohorts.
Unavailable views remain unknown; the feedback feeds the next drafting request.

`pack-and-tabs-tests.xml`: 32 passing targeted tests. `tab-lifecycle-tests.xml`:
12 passes after the group-expiry/sent-composer fixes. These runs exercise the
actual pack/store consumer, capped tab preparation, edits, failure retention,
cadence gate, AGY invocation and actual minute entry with a stale Main export.
Ruff and compilation pass. One pytest process ran at a time; no full suite ran.

Real Neo refresh, integration and cadence evidence are recorded below as observed.
