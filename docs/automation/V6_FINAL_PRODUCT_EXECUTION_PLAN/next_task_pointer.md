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

`TASK_CONTENTOPS_V1_CHROME_PROFILE_CONTINUITY_LOCK_AND_LAUNCHER_CLOSEOUT_V1`

Owner-confirmed closeout after Jim reauthenticated X in the exact CapitalChronicleBot profile:
the canonical ingestion binding is now a permanent single-source lock
(`live_contentops.ingestion_bootstrap_v1.CANONICAL_INGESTION_BINDING`) — always reuse, never
create/clone/reset/migrate/clean/replace/rename/delete, no fallback profile, missing binding
fails closed (`PROFILE_BINDING_MISSING`), unproven 9222 owner fails closed. Run Now now
requires a proven READY canonical ingestion session and creates zero durable trigger on
`INGESTION_REAUTH_REQUIRED`. Bounded cold-reopen proof passed (graceful close of the exact
browser → one-click reopen → READY, no duplicate, no new profile). This task does not
guarantee X server-side session lifetime; it guarantees ContentOps preserves and always reuses
the exact operator-owned persistent browser state.

`TASK_CONTENTOPS_V1_CONTINUOUS_INTELLIGENCE_INTAKE_CC_DATABASE_AND_EDITORIAL_PORTFOLIO_REALIGN_V1`

Owner mid-task realignment supersedes the narrow run-now-only capture + special run-now gate
relaxation approach (the `operator_run_now_override_v1` bypass was retired and reverted; the
Run Now gate-bypass semantics are FALSE by design). The Daily App is now organized around a
continuous cheap intelligence layer: continuous zero-LLM X headline intake lane inside the
canonical supervisor (`continuous_headline_ingest_v1`) writing ONLY the canonical per-day
sidecar store (`headline_ingestion/data/intake/headline_sidecars/step1_headline_sidecar_<date>.jsonl`,
append-only, deduplicated by stable post/tweet identity, restart-safe); every editorial decision
reconstructs the complete rolling 24h unique headline universe; read-only Capital Chronicle data
estate catalog + story-scoped context adapter (`capital_chronicle_data_catalog_v1`, zero upstream
mutation); published corpus read model from existing durable publication truth
(`published_corpus_read_model_v1`, no second publication store); explicit novelty/update-chain
classification + portfolio policy (`editorial_portfolio_v1`: BREAKING_NEW_STORY /
MATERIAL_FOLLOW_UP / DEEPEN_EXISTING_STORY / LOW_DELTA_REPEAT / HOLD; 5–8 article/day target
band; eight core decision opportunities/day; bootstrap.v2 window policy); V5 Today exposes the
canonical intelligence truth fields. Run Now uses the SAME canonical newsroom authority as
scheduled/material-event cycles. Tier2-A preserved untouched; FDA-G prior epochs preserved as
pre-realignment historical evidence; a new FDA-G source epoch starts after deployment.

## Next owner-approved builder lane

`TIER2-A LOCAL LONG-FORM + SHORT-FORM PROGRAMMABLE VERTICAL SLICE`

Proceeds concurrently with the continuing FDA-G evidence lane. Tier-2 must remain isolated from
the live V1 production runtime and receives NO video public-write authority from this
reprioritization.

## Tier-2-A result recorded 2026-08-10

`TASK_CONTENTOPS_TIER2_A_LOCAL_LONG_FORM_AND_SHORT_FORM_PROGRAMMABLE_VERTICAL_SLICE_V1`

Result: `COMPLETE_LOCAL_PRODUCT_SLICE_AWAITING_CHATGPT_JIM_VISUAL_REVIEW`.

The isolated local command now compiles one governed Treasury package into a renderer-neutral
VideoProgram with five chapters, ten long-form scenes, a 600.121-second 1920x1080 H.264/AAC
master, and an independently directed 71.634333-second 1080x1920 H.264/AAC short. Kokoro
narration, SRT/VTT captions, deterministic assets, ffprobe QA, exact evidence/rights bindings,
scene/chapter/master caches, one-scene selective-rerender proof, and a 116-file immutable hash
lock all pass. No provider/platform call or public/private upload occurred. Runtime evidence is
outside Git at `A:\Capital Chronicle\Runtime\ContentOps\tier2\tier2-a-treasury-curve-final-v2`.

Next Tier-2 product route after Jim/ChatGPT visual review:

`TIER2-B MULTIMODAL QA + BOUNDED REVISION + DIVERSE CORPUS`

FDA-G remains independently active and is not declared accepted by this result.

## Completed immediately prior

`TASK_CONTENTOPS_FINAL_DAILY_APP_AUTONOMOUS_PUBLICATION_RUNTIME_AND_TRANSPORT_LOCK_V1`

Delivered one durable public-write owner, one versioned destination/surface transport registry,
durable pre-write outbox and `DISPATCH_ATTEMPT_STARTED`, no-blind-retry UNKNOWN_WRITE recovery,
strict readback/reconciliation, exact read-only readiness probes, canonical Edge 9223
self-bootstrap, schema-v8 readiness persistence, and one production start command. The
SHADOW_ONLY one-start proof and current nine-surface read-only identity preflight passed. No
public write occurred.
