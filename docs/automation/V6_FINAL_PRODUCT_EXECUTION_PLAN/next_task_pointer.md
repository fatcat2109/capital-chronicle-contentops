# ContentOps — Current Next Task Pointer

Authority date: 2026-08-10

Current product direction: `CONTENTOPS_FINAL_DAILY_APP_V1_OWNER_DIRECTION`

## Current continuous lane

`TASK_CONTENTOPS_FINAL_DAILY_APP_GENUINE_CALENDAR_TIME_LIVE_SOAK_V1`

Mode: `AUTONOMOUS_DEFAULT`; public writes remain limited to exact current owner-pinned Tier-1
destinations that independently verify canonical READY state and pass every deterministic gate.

Result: `SOAK_ACTIVE_AWAITING_GENUINE_CALENDAR_TIME_EVIDENCE`

FDA-F final visual acceptance is `PASS`, accepted by ChatGPT/Jim for UI/source commit
`7919c03975febdc99a6b33429068d37307eb7569`. The canonical Final Daily App genuine calendar-time
soak is active. This is launch-session success only, not FDA-G final acceptance. Do not create
`v1.1.0` until the genuine 5–10 operating-day release evidence is complete and independently
audited.

## Owner priority override recorded 2026-08-10

Jim reprioritized implementation to proceed concurrently with the continuing FDA-G evidence
lane. Manual one-click morning resume (`Start_ContentOps_Daily_App.cmd`) is now an accepted V1
desktop operating pattern; planned host downtime is external availability loss, not database
failure, and must never justify resetting or recreating durable production state.

Completed under that override:

`TASK_CONTENTOPS_V1_ONE_CLICK_MORNING_LAUNCH_AND_RESUME_V1`

Delivered the idempotent one-click launch/resume bootstrap (`Start_ContentOps_Daily_App.cmd` →
`scripts/Start-ContentOpsDailyApp.ps1` → `live_contentops.daily_app_launcher_v1` → canonical
`python -m live_contentops.cli daily-app start ...`). It reuses the exact production store,
never spawns duplicate supervisors, fails closed on ambiguous port ownership, preserves
KILL_SWITCH and UNKNOWN_WRITE state, and performs no public writes. It did NOT declare FDA-G
accepted and did NOT start Tier-2.

`TASK_CONTENTOPS_V1_TRUE_ONE_CLICK_INGESTION_BOOTSTRAP_AND_RUN_NOW_CONTROL_V1`

V1 runtime/product correction: the one-click launcher now safely bootstraps the exact existing
Chrome `CapitalChronicleBot` CDP 9222 ingestion profile when absent (reuse when alive,
fail-closed on unproven owner, REAUTH_REQUIRED reported without login automation), and the V5
Today surface gained the canonical governed `Run editorial cycle now` control
(`POST /api/daily-app/control/run-now` → durable append-only `OPERATOR_REQUESTED` trigger,
schema v9, consumed by the existing supervisor through unchanged gates). The quarantined
`POST /api/run-pipeline` remains locked. No public write occurred. The FDA-G soak epoch
restarted from the corrected final V1 source SHA after one controlled safe idle restart.

## Next owner-approved builder lane

`TIER2-A LOCAL LONG-FORM + SHORT-FORM PROGRAMMABLE VERTICAL SLICE`

Proceeds concurrently with the continuing FDA-G evidence lane. Tier-2 must remain isolated from
the live V1 production runtime and receives NO video public-write authority from this
reprioritization.

## Completed immediately prior

`TASK_CONTENTOPS_FINAL_DAILY_APP_AUTONOMOUS_PUBLICATION_RUNTIME_AND_TRANSPORT_LOCK_V1`

Delivered one durable public-write owner, one versioned destination/surface transport registry,
durable pre-write outbox and `DISPATCH_ATTEMPT_STARTED`, no-blind-retry UNKNOWN_WRITE recovery,
strict readback/reconciliation, exact read-only readiness probes, canonical Edge 9223
self-bootstrap, schema-v8 readiness persistence, and one production start command. The
SHADOW_ONLY one-start proof and current nine-surface read-only identity preflight passed. No
public write occurred.
