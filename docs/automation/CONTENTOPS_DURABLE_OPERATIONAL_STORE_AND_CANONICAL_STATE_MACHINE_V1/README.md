# Wave 02 — Durable Operational Store and Canonical State Machine

## Acceptance classification

`PASS_DURABLE_OPERATIONAL_STORE_AND_CANONICAL_STATE_MACHINE_V1_AWAITING_INDEPENDENT_AUDIT`

Wave 02 establishes the single authoritative SQLite WAL operational store (`ContentOpsDurableStore`), versioned migration framework with backup and rollback recovery, Compare-And-Set (CAS) state machine over 29 canonical states, append-only transition event log enforced by SQLite database triggers, transactional leases with monotonic fencing tokens, restart safety, deterministic event replay, corruption detection, and redacted evidence export.

## Execution boundary

- **Execution mode:** `LOCAL_SCHEMA_AND_PERSISTENCE_IMPLEMENTATION_NO_LIVE_ACTION`
- **Zero live authority:** Wave 03+ entity tables (`approval_envelopes`, `outbox_messages`, `platform_dispatches`, `readbacks`, `reconciliations`, `incidents`, `metrics`, `feedback_records`, `learning_reviews`) are schema-ready for future compatibility but grant no approval, outbox, dispatch, or publication authority in this task.
- **No ORM:** Python standard `sqlite3` used directly with explicit SQL, explicit transactions (`BEGIN IMMEDIATE`), WAL mode (`PRAGMA journal_mode=WAL;`), foreign keys (`PRAGMA foreign_keys=ON;`), and custom triggers.

## Authority

- Repository: `fatcat2109/capital-chronicle-contentops`
- Base branch: `master`
- Required starting master HEAD: `c87e338f25922f4d03454ba199139353ca7198ff`
- Working branch: `agent/contentops-wave02-durable-operational-store-v1`
- Store module: `live_contentops.durable_operational_store_v1.ContentOpsDurableStore`
- Orchestrator integration: `live_contentops.production_orchestrator_v1.ContentOpsProductionOrchestrator(store=...)`

## Evidence summary

- Migration versions: **1**
- Schema tables: **22**
- Triggers: **2 (append-only enforcement on transition_events)**
- Canonical states: **29**
- Unit, resilience, CAS, lease, replay, corruption, export & integration tests: **18 passed in 13.15s**
- Wave 01 canonical-entrypoint enforcement tests: **38 passed in 3.03s**
- Compatibility tests: **65 passed in 3.57s**
- Final automation closure suite: **7 passed in 1.48s**
- Wave 01 metadata consistency suite: **5 passed in 1.88s**
- Monolithic repository-wide Python suite: **not run; no full-suite PASS claimed**
- Browser QA: **not run (no UI changes)**
- Precommit CI: **no CI PASS claimed**

No source-data fetch, provider/9router/Gemini LLM call, browser/CDP session, platform adapter, scheduler/retry, approval/outbox, dispatch, publication, edit, comment, reply, reaction, DM, or public write occurred.

## Exact next task

`TASK_CONTENTOPS_EXACT_APPROVAL_ENVELOPE_TRANSACTIONAL_OUTBOX_AND_EXPIRY_V1` remains `NEXT_NOT_STARTED`. This task grants no Wave 03 or live authority.
