# Architecture and Authority Boundary — Wave 02 Durable Operational Store

## 1. Single Production Persistence Authority

`ContentOpsDurableStore` (`live_contentops/durable_operational_store_v1.py`) is the single authoritative local operational store for post-v1 ContentOps full automation.

Key principles:
- **Explicit SQL Control:** Uses Python's native `sqlite3` driver with explicit transactions (`BEGIN IMMEDIATE`). No ORM hides SQL execution or transaction boundaries.
- **WAL Mode & Foreign Keys:** Automatically sets `PRAGMA journal_mode=WAL;`, `PRAGMA foreign_keys=ON;`, and `PRAGMA busy_timeout=5000;`.
- **Database Location:** Explicitly configurable path, falling back to configurable local directory. Mutable database files (`*.sqlite`, `*.db`, `*-wal`, `*-shm`, `*.bak`) are ignored by `.gitignore` and never committed to Git.

## 2. Orchestrator Integration Seam

The store connects to the canonical system via a single dependency-injected seam in `ContentOpsProductionOrchestrator(store=None)` (`live_contentops/production_orchestrator_v1.py`).
- When `store` is `None`, the orchestrator operates in backwards-compatible stateless mode.
- When `store` is provided, orchestrator operations automatically register work items, state versions, and transition events in the durable store.

## 3. Wave 02 vs Wave 03+ Authority Boundary

Wave 02 creates the normalized tables for all North Star entities, including placeholder tables for Wave 03+ (`approval_envelopes`, `outbox_messages`, `platform_dispatches`, `readbacks`, `reconciliations`, `incidents`, `metrics`, `feedback_records`, `learning_reviews`).

However:
- Wave 02 implements zero approval logic, outbox dispatching, or platform publication.
- Having schema-ready tables does **not** grant publication or live write authority.
- Live dispatch remains strictly `NEXT_NOT_STARTED`.
