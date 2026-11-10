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

The next full ET day after morning integration is 10 November 2026. It ends **11 November 2026 12:00 GMT+7** (05:00 UTC). No current observation is full-day proof. Run once after that instant, from the operating root:

```powershell
python scripts/audit_publication_day_cc401.py --store "A:/Capital Chronicle/Runtime/ContentOps/contentops_daily_app_v1.sqlite3" --day 2026-11-10 --output "A:/Capital Chronicle/Worktrees/ContentOps/codex-publisher-exec/docs/publisher/CC-401/full-day-audit.json"
```

The audit is read-only. PASS requires an elapsed whole day, confirmed posts on both destinations, no UNKNOWN_WRITE incident for a confirmed Discord/Threads write and at most one destination-failure incident per destination. No new schedule or watcher is installed.

Integrated code: `7a013ffccc3095231131858e8a51d0d829425d88`, fast-forwarded into `A:/Capital Chronicle/ContentOps`. `copied-live-replay.json` records the 555 MB live-store-copy replay; `live-application.json` records exact live Note endings and the operating-root consumer source. The temporary database copy was removed after its connections closed.
