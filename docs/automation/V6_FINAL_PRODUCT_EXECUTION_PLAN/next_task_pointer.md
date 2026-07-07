# V6 Next Task Pointer

Current task: `TASK_CONTENTOPS_V6_FINAL_LAUNCH_STALE_STATE_CLEANUP_V0` — Removed the final-launch confusion where a dashboard-triggered run reported `SUCCESS` while the committed audit was `DISPATCH_BLOCKED`. The live runner CLI now returns non-zero on `DISPATCH_BLOCKED`/`DISPATCH_PARTIAL_FAILURE`, the pipeline server reads `latest_dispatch_audit.json` and only reports success on `DISPATCH_COMPLETE`, and the dashboard no longer simulates fake success (backend offline now shows `BACKEND_OFFLINE`). The dashboard surfaces true `pipeline_status`, failed/blocked platforms, and blockers. (COMPLETED LOCALLY; commit pending)

North star: a dashboard-triggered full automation pipeline that either dispatches live to all supported lanes or blocks loudly with exact reasons. No dry-run/simulated success is allowed on the current launch path.

Recommended next task:

```text
TASK_CONTENTOPS_V6_DASHBOARD_TRIGGERED_LIVE_RUN_AND_PER_PLATFORM_AUDIT_V0
```

Purpose: With the fake-success paths removed, start the backend + UI, trigger one dashboard live run, and audit each platform outcome from the true `latest_dispatch_audit.json` status. Resolve any real quality/media blockers surfaced (the last run blocked on `article_too_short_words:127<2000`, `missing_specific_numbers`, and missing media) before declaring a clean `DISPATCH_COMPLETE` launch.
