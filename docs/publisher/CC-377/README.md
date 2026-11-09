# CC-377: digest recovery scope

The digest recovery query already selects its exact work item. The publication
check previously loaded global history again and could block the digest on an
unrelated canonical even when recovery reported no remaining obligations. Both
now use the same existing scope. A skipped noncanonical row remains skipped.
Uncertain writes for this digest still require readback. The ordinary global
publication path retains its checks. The final publication message lookup also
filters by work item in SQLite, avoiding a measured four-minute global outbox
load during the first installed check.

The frozen `cc143-digest-2026-11-09` packet contains the missed article,
`substack:224085585`. The existing preparation consumer resumes an unsent packet
before allocating another day, then excludes its article IDs and URLs. No packet
replacement or schedule change is needed.

Validation: `digest-1.xml` and `digest-2.xml` cover the native identity, publish and email/web
readback loop, restart deduplication, same-digest uncertainty and the route helper.
`coordinator-1.xml` through `coordinator-3.xml` cover the selected global recovery,
quarantine and exactly-once regressions. `original-guard-reproduction.xml` is an
intentional failure with only the old guard restored in process memory. The new
scope fixes that failure. The initial combined coordinator selection was stopped;
its load-limit timing is recorded in `coordinator-selection-aborted.json`.
A later digest rerun hit its 50-second timeout while the slow live check was
reading history; `digest-selection-timeout.json` retains that result. The two
subsequent serial batches validate the final lookup change.

The installed route reached `NATIVE_REQUEST_READY` for the exact retained packet
(`live-route-after-query-fix.json`), requesting identity verification in 5.839 seconds. No browser action was
claimed or performed. `live-consumer.json` verifies the installed consumer and
the article's single allocation.

The actual 10 November 2026 19:00 GMT+7 scheduled task
`cc-contentops-digest-1900-bp` must still publish and read back. A current native
request or a test is not that future scheduled result. Keep the backlog item
IN_PROGRESS until that acceptance is observed.
