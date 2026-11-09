# CC-340: recover a missed active status post

The existing status queue can recover a missed WAITING or TRIGGERED post for up
to 24 hours, only while it is the plan's latest state and inside its validity.
WAITING respects the earlier entry deadline or expiry; TRIGGERED respects expiry.
Only the current transition is recovered. New late copy identifies the delayed
update and retains the original event time in ET. Queue time remains a separate
UTC field. Earlier outbox payloads and keys remain unchanged.

The minute CLI passes the current recovery bindings into `publish_ready`.
Previously stale rows resume on the same key; the sole coordinator retains
readback, duplicate protection and UNKNOWN_WRITE reconciliation. A recovered
state that ends or expires before dispatch is skipped. X re-reads the export
before a late write; its readback remains available after expiry. CC-306's late
updates of announced plans and refusal of unannounced withdrawals remain intact.
No failure ledger, publisher, schedule or model call was added.

## Verification

[58 targeted tests](final-tests.txt) passed in one serial pytest process in
68.99 seconds. [JUnit](final-tests.xml) covers the queue, CLI-to-coordinator
consumer, refusal repair, expiry, the exact 24-hour boundary, immutable stale
rows, X, ambiguous-write recovery, and existing Telegram duplicate protection.
Ruff passes on the changed implementation, CLI and new test file; `git diff
--check` passes. The first replay assertion selected an older gold trigger; its
selection was corrected before this final run.

[NFP replay](nfp-replay.json) uses all 81 normalized transitions from the retained
6 November export, with its exact file hashes recorded in the fixture. The
snapshot was generated at 18:01:31 UTC; the replay clock is 14:35 UTC, and only
transitions at or before that clock are included. This is a replay of retained
state, not a claim that an original 14:35 export was preserved. Injecting the
FILLED reader failure produces EXPORT_UNREADABLE and no queue row. After repair,
gold's 13:33:46 UTC trigger queues once; the second pass queues zero. There are
zero production-store changes or public sends in this replay.

## Operating integration

Base: `1a24eaa6b6f070c99ff8828886f56e4871337c7a`, the current Publisher operating
HEAD. The fetched remote default lacks the operating consumers; using the live
base permits forward integration. Existing telemetry and duplicate-ledger WIP
is excluded from this item.

The unchanged `CapitalChronicle-PlanStatusPosts-V1` task invokes
`pythonw.exe -B scripts\plan_status_posts.py --publish` from
`A:\Capital Chronicle\ContentOps`. That script loads the module from its own
root, so the next invocation uses the integrated source without a restart.
Rollback tag: `contentops-rollback-20261109-cc340`.
Live tag: `contentops-live-20261109-cc340`.
Integration and installed-CLI readback are recorded in `integration.json`.

Launch PID 5524 explicitly configured `gpt-6.1-sol/high`:
CONFIGURED_NOT_OBSERVED, because runtime model/effort telemetry is unavailable.
No desktop control, browser action, chat message or schedule change was used.
