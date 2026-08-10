# TASK_CONTENTOPS_V1_ONE_CLICK_MORNING_LAUNCH_AND_RESUME_V1

Authority date: 2026-08-10

Result: `COMPLETE_IMPLEMENTED_AND_VALIDATED`

Owner priority override delivered before Tier-2: one obvious double-click file,
`Start_ContentOps_Daily_App.cmd`, that safely starts or resumes the SAME durable production
Daily App state each morning. Planned host sleep/shutdown is external availability loss, not
database failure.

## Capability delivered

```text
Start_ContentOps_Daily_App.cmd
→ scripts/Start-ContentOpsDailyApp.ps1 (thin shell, finds repo + python)
→ python -m live_contentops.daily_app_launcher_v1 (all decisions, GET-only probes)
→ python -m live_contentops.cli daily-app start --store-path "A:\Capital Chronicle\Runtime\ContentOps\contentops_daily_app_v1.sqlite3" --output-root "A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs"
```

Decision states:

- `ALREADY_RUNNING` — canonical API + store binding + fresh heartbeat + exactly one supervisor; never spawns a duplicate.
- `ALREADY_RUNNING_KILL_SWITCH_ACTIVE` — same, with KILL_SWITCH preserved (never cleared).
- `STARTED` — no canonical process; one detached canonical start; health/heartbeat verified; exactly-one-supervisor re-check.
- `BLOCKED_PORT_OWNER_UNPROVEN` — port occupied by unproven owner; fail closed, no kill.
- `BLOCKED_MULTIPLE_SUPERVISORS` — never spawn a third.
- `BLOCKED_PRODUCTION_STORE_MISSING_NEVER_CREATE_IMPLICITLY` — production DB never created or reset by the launcher.
- `BLOCKED_STORE_PATH_IS_PROTECTED_BACKUP` — pre_v8/byte_exact/migration-backup paths rejected.

Safety properties (also asserted by focused tests):

- HTTP GET only; no POST/control endpoint is ever called; KILL_SWITCH and UNKNOWN_WRITE state untouched.
- the launcher never opens the SQLite store (`import sqlite3` absent); stores are reused, never reset.
- no secret values read or printed; credential preflight emits names + `PRESENT/MISSING` + scope only; a secret-shaped redaction guard blocks output.
- Windows-native detached spawn (`CREATE_NO_WINDOW | CREATE_NEW_PROCESS_GROUP`); no Windows Service, no Task Scheduler, no admin.
- launcher logs under `A:\Capital Chronicle\Runtime\ContentOps\one_click_launcher\`, not the repo.
- browser roles hardcoded separate: Chrome 9222 ingestion only, Edge 9223 publishing/readback only; Edge runtime ensured only by the canonical Daily App self-bootstrap.
- V5 UI bootstrap is local-only (`127.0.0.1`, ports 4173 preview / 5173 dev, existing `ui/contentops_v5` npm scripts); no second dashboard.

## Validation summary

- production run against healthy soak app: `ALREADY_RUNNING`, supervisors 1 → 1, no duplicate cycle/public object; repeated run idempotent; V5 UI served once.
- isolated TEMP shadow smoke (port 15174, `--shadow-smoke`): start → health → idempotent re-run → stop → restart reconstruction on the same store → exactly one supervisor throughout. Shadow artifacts cleaned up after the smoke.
- focused tests: `tests/test_contentops_daily_app_launcher_v1.py` — 17 passed.
- no public write, no unknown write, no provider write, no secret/session exposure; protected `v1.0` tag untouched.

The evidence packet is [one_click_launcher_evidence_v1.json](one_click_launcher_evidence_v1.json).

FDA-G remains `SOAK_ACTIVE_AWAITING_GENUINE_CALENDAR_TIME_EVIDENCE`. This task did not declare
FDA-G accepted and did not start Tier-2 implementation.
