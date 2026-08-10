# TASK_CONTENTOPS_V1_TRUE_ONE_CLICK_INGESTION_BOOTSTRAP_AND_RUN_NOW_CONTROL_V1

Authority date: 2026-08-10

Result: `COMPLETE_IMPLEMENTED_AND_VALIDATED`

V1 runtime/product correction, owner-prioritized. FDA-G remains
`SOAK_ACTIVE_AWAITING_GENUINE_CALENDAR_TIME_EVIDENCE`; this task does not declare FDA-G
accepted and does not start Tier-2.

## A. True one-click Chrome 9222 ingestion bootstrap

`live_contentops/ingestion_bootstrap_v1.py` reuses the exact EXISTING dedicated binding
accepted in historical evidence (`current_x_reauthentication_blocker_evidence_v1.json`):

- profile: `%LOCALAPPDATA%\Google\Chrome\User Data\CapitalChronicleBot`
- command: `chrome.exe --remote-debugging-port=9222 --user-data-dir="<that profile>"`
  (the exact dedicated ingestion command from `Launch_Dashboard.bat`)

Behavior: reuse a live canonical 9222 owner; launch the exact profile when absent; bounded
wait; owner-proofed fail-closed on unknown 9222 owners; never launch a duplicate when the
profile is already running without CDP; never create/clone/reset/delete a profile; never
inspect cookies/storage/tokens; never automate login. Session state is observed only through
the canonical X list route's visible login-redirect markers (accepted historical method),
reporting `REAUTH_REQUIRED` with the exact profile left open for operator sign-in.

Production observation on 2026-08-10: bootstrap launched the exact profile; the existing X
session redirected to login → `REAUTH_REQUIRED` reported truthfully.

## B/C/D/E. Run editorial cycle now (governed)

- New narrow endpoint: `POST /api/daily-app/control/run-now` (loopback only, strict allowed
  origins, exact bounded JSON body `{"trigger":"OPERATOR_REQUESTED","expected_state_version":N}`,
  bounded size, no query trigger, no secrets/paths/callables).
- Durable trigger: schema v9 append-only `operator_cycle_triggers` with a partial unique index
  enforcing at most one PENDING trigger (`OPERATOR_REQUESTED` kind only). Lossless migration
  v9 recorded in `schema_lineage_metadata` (compatibility 9, dependency manifest v7).
- Consumption: `ContentOpsDailyAppSupervisor.tick()` consumes the PENDING trigger through the
  SAME canonical `_execute_window` boundary as scheduled/material windows; active-cycle
  detection defers; one window per tick; restart-safe (PENDING survives restart exactly once).
- Mode semantics preserved: SHADOW_ONLY → zero public writes; KILL_SWITCH → never cleared,
  trigger deferred per existing product policy; AUTONOMOUS_DEFAULT/SUPERVISED_OPERATOR_GATE →
  unchanged downstream gates (only the scheduled-window wait is bypassed). No publication is
  ever claimed by the POST response.
- Historical `POST /api/run-pipeline` remains quarantined with 423.

## G. V5 UI

`Run editorial cycle now` panel on Today (adjacent to Next safe action): disabled while
submitting / while a durable trigger is pending / while a cycle is active / under
KILL_SWITCH; shows current mode consequence; states governed semantics and never implies
guaranteed publication. Controls description updated (two narrow console writes: CAS mode
change + durable run-now trigger). Snapshot exposes `operator_cycle_trigger`,
`active_editorial_cycle_window_id`, and `controls.run_now_*` fields.

## Validation

- Focused backend tests: `tests/test_daily_app_operator_trigger_v1.py` (21),
  `tests/test_contentops_ingestion_bootstrap_v1.py` (9), refreshed launcher/store/supervisor
  suites (schema-v9 pins updated; v1–v4 frozen bytes unchanged).
- UI: `daily_app_console.test.tsx` 14 passed (incl. 3 new run-now tests), full vitest
  267 passed, `npm run build` PASS.
- Isolated shadow E2E (TEMP store, port 15174, SHADOW_ONLY): trigger accepted →
  double-click idempotent (`OPERATOR_TRIGGER_ALREADY_PENDING`, same trigger_id) → supervisor
  consumed with `EXECUTED:NO_PUBLICATION` → kill with PENDING trigger → restart → trigger
  consumed exactly once (one `EDITORIAL_WINDOW_DUE` transition per window) → zero dispatch/
  outbox/public rows, unknown writes 0, mode preserved.
- Production one-click run: Daily App `ALREADY_RUNNING` (no duplicate), Chrome 9222
  `REAUTH_REQUIRED` (honest), Edge 9223 `READY`, V5 UI ready, store reused.
- One controlled production restart performed only after safe-idle preflight
  (UNKNOWN_WRITE=0, pending reconciliation=0, no dispatch in progress, next wake in the
  future); the FDA-G soak epoch restarted from the corrected final V1 source SHA; prior
  FDA-G epoch evidence preserved unchanged.
- No public write, no unknown write, no secret/session exposure, protected `v1.0` untouched.

The machine evidence is [one_click_ingestion_and_run_now_evidence_v1.json](one_click_ingestion_and_run_now_evidence_v1.json).
