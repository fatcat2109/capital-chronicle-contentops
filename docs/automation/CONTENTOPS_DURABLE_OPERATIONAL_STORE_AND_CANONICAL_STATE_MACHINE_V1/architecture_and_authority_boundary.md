# Architecture and Authority Boundary — Wave 02 Durable Operational Store

Worker Classification:
`PASS_WAVE02_HISTORICAL_SCHEMA_LINEAGE_AND_LEGACY_REPLAY_FINAL_CORRECTION_AWAITING_INDEPENDENT_AUDIT`

## 1. Single Production Persistence Authority

`ContentOpsDurableStore` (`live_contentops/durable_operational_store_v1.py`) is the single authoritative local operational store for post-v1 ContentOps full automation.

- Python `sqlite3` with explicit `BEGIN IMMEDIATE` transaction boundaries.
- SQLite WAL, foreign keys, and a 5000 ms busy timeout.
- Versioned semantic migrations that fail closed on missing, unknown, ahead, drifted, partial, or ambiguous populated histories.
- Canonical schema-versioned transition envelopes with full-field replay verification and a cryptographic previous-event chain.
- Store-owned SQLite connections install a prepare-time authorizer that denies direct INSERT into `transition_events` and `artifact_references` outside narrow canonical append/registration contexts; statement caching is disabled so prepared authorization cannot outlive those contexts.
- Database triggers provide a second guard for plain external SQLite connections and UPDATE/DELETE immutability. An unrestricted local file owner can register spoofed trigger UDFs, drop triggers, replace bytes, or use a different SQLite runtime, so Wave 02 does **not** claim malicious-local-process resistance.
- Canonical replay independently fails closed on illegal edges, protected authority states, sequence/version mismatches, payload/hash/chain drift, scoped artifact snapshot corruption, and projection mismatch. This detects tested forged histories but is not a substitute for OS access control or cryptographic signing rooted outside the database.
- Independently resolved immutable artifact receipts have persisted provenance and explicit reuse scope. PUBLIC sensitivity is not reuse authority.
- Monotonic lease fencing, deterministic fake-clock timestamps, atomic assignment/heartbeat cleanup, and a database-enforced one-ACTIVE-assignment invariant.

Mutable database families (`*.sqlite`, `*.db`, `*-wal`, `*-shm`, and migration backups) remain ignored and uncommitted.

## 2. Orchestrator Integration Seam

`ContentOpsProductionOrchestrator(store=None)` (`live_contentops/production_orchestrator_v1.py`) is dependency injected. Stateless behavior remains compatible when no store is supplied. With a store, explicit operation contracts define output form, schema/canonicalization, restart mode, and capability scope; lifecycle events bind exact canonical inputs and outputs. Missing, failed, or unsupported outputs are durably blocked without hiding the original exception. Existing `EVIDENCE_PENDING` work requires an explicit attempt decision before resume.

## 3. Authority Roles

- Accepted master authority: Wave 01 at `origin/master` `c87e338f25922f4d03454ba199139353ca7198ff`.
- Candidate branch authority: this Wave 02 branch is `COMPLETE_AWAITING_INDEPENDENT_AUDIT`, not merged authority.
- Planned authority: Wave 03 remains `NEXT_NOT_STARTED` until independent acceptance.

Wave 02 creates normalized placeholders for later approval, outbox, dispatch, readback, reconciliation, incident, metric, feedback, and learning entities. It executes none of them and grants no approval, reporting, dispatch, publication, provider, browser/CDP, network, credential-read, or public-write authority.
