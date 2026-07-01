# Status and Progress Docs Map

This map defines which repo-native governance docs must be updated after tasks and which are reserved for milestone or strategy refreshes. GitHub remote wins over this map, Project Sources, and chat memory.

## Update Cadence

| Document | Update cadence | Purpose |
|---|---|---|
| `docs/status/CURRENT_PROJECT_STATUS.md` | Every non-read-only task | Human-readable current state, blockers, accepted task, and soft next recommendation. |
| `docs/status/current_project_status.json` | Every non-read-only task | Machine-readable status contract and guardrail source. |
| `docs/status/STATUS_LEDGER_SHA_MODEL.md` | When SHA semantics change | Explains `last_verified_remote_sha`, `accepted_product_baseline_sha`, and status-only commit semantics. |
| `docs/status/PROJECT_PROGRESS_LEDGER.md` | Accepted milestone or lane completion | Human-readable progress timeline by lane. |
| `docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/current_v6_master_plan.md` | Major product/north-star strategy changes only | Strategic V6 product thesis, platform roles, and north-star loop. |
| `docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/v6_25_task_ledger.md` | Roadmap/lane completion or execution-plan refresh | Roadmap status map and lane classification. |
| Project Sources bundle docs | Only during Project Sources refresh tasks | Context upload/handoff guidance; never runtime authority. |

## Stale-Pointer Prevention Rules

1. Next-task recommendations are soft recommendations only.
2. GitHub remote commits and fetched repo files win over Project Sources and chat memory.
3. Never hardcode a future next task as permanent truth.
4. If a status/progress doc conflicts with repo evidence, stop and reconcile before feature work.
5. Do not claim public URL verification, provider/API readiness, live dispatch, user activity, metrics, or screenshots unless committed evidence proves it.
6. Status-only/docs refresh commits do not become product baselines unless explicitly accepted as product work.

## Required Task Start Reads

- `docs/status/CURRENT_PROJECT_STATUS.md`
- `docs/status/current_project_status.json`
- `docs/status/DASHBOARD_SURFACE_AUTHORITY.md`
- `docs/status/STATUS_LEDGER_SHA_MODEL.md`
- This file when changing status/progress governance.

## Required Final Evidence

Final evidence for non-read-only tasks should state which status/progress docs were updated, the accepted product baseline SHA, the tested commands, and whether any live/env/credential/provider/platform/browser action occurred.
