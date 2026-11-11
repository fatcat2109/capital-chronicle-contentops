# CC-401: API confirmation and daily destination failures

Discord already sent `wait=true`; the Discord and Threads publication wrappers replaced API acceptance with strict readback failure. The coordinator then filed UNKNOWN_WRITE incidents despite retaining each provider object ID. The fix preserves provider acceptance and keeps content/media reconciliation separate. Discord never fabricates a missing message ID and its query now has exactly one `wait=true` value. A Threads container ID never confirms a published post.

The existing incidents table now holds the first destination failure for an America/New_York calendar day. Its stable incident ID prevents repeat alarms. New writes and proven-absent retries skip that destination until ET midnight. Other destinations continue; existing ambiguous writes and native claims keep their original readback/reconciliation path. An ambiguity recovered immediately to a confirmed object does not file a failure incident.

The three old queued status Notes ended as not posted with `CC401_STALE_STATUS_NOTE_UNCLAIMED`: their requests were never claimed and no browser action occurred. The coordinator cancellation checks exact intent hashes and absence of claims/returns in one transaction, preserves original payload bytes, closes reconciliation and supersedes the native request. A claimed Note is rejected for readback instead. Native begin also refuses a superseded request after the action claim to close the cancellation race.

## Validation

- `test_publication_coordinator_v1.py`: copied-store provider confirmation, deferred/failed readback, duplicate prevention, ET midnight, destination isolation, one incident/day, unclaimed versus claimed Notes, and the read-only day audit.
- `test_discord_live_adapter_v6.py`: wait=true replacement and real provider ID only.
- Existing Discord, Threads, coordinator, native protocol and CC-393 platform-rule regression files are run serially in one pytest process. Historical protocol fixtures simulate permissions locally; production prohibitions remain tested in CC-393.
- `targeted-tests.txt` preserves the initial regression failures; `final-targeted-tests.txt` records 278 passing tests and two fixture failures. Both repaired cases and the affected acceptance checks pass in `verified-targeted-tests.txt` (14 passed). `evidence.json` preserves the baseline, launch configuration, integration and live application evidence.

## Full-day acceptance

The planned full ET day after morning integration was 10 November 2026. It ended **11 November 2026 12:00 GMT+7** (05:00 UTC). The elapsed-day result is recorded below. The read-only command, from the operating root, is:

```powershell
python scripts/audit_publication_day_cc401.py --store "A:/Capital Chronicle/Runtime/ContentOps/contentops_daily_app_v1.sqlite3" --day 2026-11-10 --output "A:/Capital Chronicle/Worktrees/ContentOps/codex-publisher-exec/docs/publisher/CC-401/full-day-audit.json"
```

The audit is read-only. PASS requires an elapsed whole day, confirmed posts on both destinations, no UNKNOWN_WRITE incident for a confirmed Discord/Threads write and at most one active destination-failure incident per destination. Recorded local repairs and exact reconciled objects follow the live coordinator's circuit semantics; original incident counts remain visible. No new schedule or watcher is installed.

Integrated code: `7a013ffccc3095231131858e8a51d0d829425d88`, fast-forwarded into `A:/Capital Chronicle/ContentOps`. `copied-live-replay.json` records the 555 MB live-store-copy replay; `live-application.json` records exact live Note endings and the operating-root consumer source. The temporary database copy was removed after its connections closed.

## Full-day verification — 11 November 2026

`full-day-audit-20261110.json` reports **PASS** for the complete 10 November ET day: **14 confirmed Discord posts, 45 confirmed Threads posts and zero UNKNOWN_WRITE incidents against confirmed posts**.

The original audit returned FAIL because it counted repaired local refusals and subsequently reconciled objects as active destination failures. Its exact result remains in `full-day-audit-20261110-initial.json`. The corrected audit retains every original count and lists the evidence for each resolved row. It uses the coordinator's local-refusal causes, explicit local-repair markers and exact destination/object/reconciliation identity. A confirmed Discord or Threads false alarm still fails, even with a later repair marker. Duplicate unresolved failures still fail.

One actual Discord UNKNOWN_WRITE and one LinkedIn TLS no-write remain visible for that day. These are separate failures, each recorded once for its destination; they are not counted as confirmed-post false alarms. Existing reconciliation retains the uncertain Discord dispatch. The three original queued Notes remain DEFINITE_NO_WRITE with `CC401_STALE_STATUS_NOTE_UNCLAIMED`.

`full-day-audit-tests-20261111.txt` and its JUnit XML record **15 passing targeted checks** in 22.70 seconds, including copied-store provider acceptance, one incident per ET day, next-day retry, cancellation safety, exact destination identity and audit non-mutation. `full-day-launch-20261111.json` records the configured `gpt-6.1-sol / max` launch as CONFIGURED_NOT_OBSERVED. The live-root verification is retained in `full-day-closure-20261111.json`.
