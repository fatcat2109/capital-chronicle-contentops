# Retention and Backup Policy — Wave 02 Durable Operational Store

## 1. Retention Classes

1. **Authority-Bearing State & Events (Permanent Retention):**
   - Tables: `schema_migrations`, `work_items`, `transition_events`, `operator_decisions`, `review_records`, `story_versions`, `artifact_references`.
   - **Policy:** Never pruned or compacted. Transition events form the immutable audit trail.
2. **Ephemeral Telemetry & Operational State (Policy-Controlled Compaction):**
   - Tables: `leases`, `heartbeats`, `scheduler_ticks`, `operational_windows`, `model_invocations`.
   - **Policy:** Compaction allowed only for expired leases or closed window heartbeats older than 90 days, producing a audit compaction event.

## 2. Backup Policy

- **Migration Pre-Backup:** Automatically creates `.sqlite.bak.<timestamp>` prior to executing schema migrations.
- **Integrity Validation:** Every backup is verified via `PRAGMA integrity_check;`.
- **Git Ignore:** All `.sqlite`, `.db`, `.bak`, `-wal`, `-shm` database files are excluded from Git commits via `.gitignore`.
