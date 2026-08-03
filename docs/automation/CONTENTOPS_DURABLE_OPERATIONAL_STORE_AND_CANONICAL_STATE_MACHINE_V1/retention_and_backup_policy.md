# Retention and Backup Policy — Wave 02 Durable Operational Store

Worker Classification:
`PASS_WAVE02_MIGRATION_REPLAY_ASSIGNMENT_AND_EVIDENCE_FINAL_ACCEPTANCE_CORRECTION_AWAITING_INDEPENDENT_AUDIT`

## 1. Retention Classes

- Authority-bearing schema, work-item, event, story, assignment, artifact, review, operator-decision, approval, outbox/dispatch, readback/reconciliation, incident, and learning records are not pruned by Wave 02.
- Lease, heartbeat, scheduler/window, model-invocation, metric, and feedback retention remains policy-controlled. Wave 02 implements no automatic compactor and claims no completed compaction event.
- Immutable transition and artifact rows remain protected by database triggers; retention policy cannot authorize mutation of those rows.

## 2. Migration Backup and Restore

Before each pending migration, the store validates database integrity and creates a SQLite backup snapshot at a migration backup path generated with the injected clock. The backup is opened and integrity-checked before migration execution. SQL plus transformation semantics run transactionally; any migration failure rolls back and restores the verified backup before raising `MigrationError`.

Backup filenames and mutable database families (`*.sqlite`, `*.db`, `*-wal`, `*-shm`, and backup variants) are ignored by Git. Final hygiene validation confirms none is staged or committed.
