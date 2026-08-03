# Architecture and Authority Boundary — Wave 02 Durable Operational Store

Worker Classification:
`PASS_WAVE02_MIGRATION_REPLAY_ASSIGNMENT_AND_EVIDENCE_FINAL_ACCEPTANCE_CORRECTION_AWAITING_INDEPENDENT_AUDIT`

## 1. Single Production Persistence Authority

`ContentOpsDurableStore` (`live_contentops/durable_operational_store_v1.py`) is the single authoritative local operational store for post-v1 ContentOps full automation.

- Python `sqlite3` with explicit `BEGIN IMMEDIATE` transaction boundaries.
- SQLite WAL, foreign keys, and a 5000 ms busy timeout.
- Versioned semantic migrations that fail closed on missing, unknown, ahead, drifted, partial, or ambiguous populated histories.
- Canonical schema-versioned transition envelopes with full-field replay verification and a cryptographic previous-event chain.
- Connection-local internal append authorization plus INSERT/UPDATE/DELETE database triggers; callers cannot directly append or mutate authority events.
- Independently resolved immutable artifact receipts with persisted provenance and explicit reuse scope. PUBLIC sensitivity is not reuse authority.
- Monotonic lease fencing, deterministic fake-clock timestamps, atomic assignment/heartbeat cleanup, and a database-enforced one-ACTIVE-assignment invariant.

Mutable database families (`*.sqlite`, `*.db`, `*-wal`, `*-shm`, and migration backups) remain ignored and uncommitted.

## 2. Orchestrator Integration Seam

`ContentOpsProductionOrchestrator(store=None)` (`live_contentops/production_orchestrator_v1.py`) is dependency injected. Stateless behavior remains compatible when no store is supplied. With a store, explicit operation contracts define output form, schema/canonicalization, restart mode, and capability scope; lifecycle events bind exact canonical inputs and outputs. Missing, failed, or unsupported outputs are durably blocked without hiding the original exception. Existing `EVIDENCE_PENDING` work requires an explicit attempt decision before resume.

## 3. Authority Roles

- Accepted master authority: Wave 01 at `origin/master` `c87e338f25922f4d03454ba199139353ca7198ff`.
- Candidate branch authority: this Wave 02 branch is `COMPLETE_AWAITING_INDEPENDENT_AUDIT`, not merged authority.
- Planned authority: Wave 03 remains `NEXT_NOT_STARTED` until independent acceptance.

Wave 02 creates normalized placeholders for later approval, outbox, dispatch, readback, reconciliation, incident, metric, feedback, and learning entities. It executes none of them and grants no approval, reporting, dispatch, publication, provider, browser/CDP, network, credential-read, or public-write authority.
