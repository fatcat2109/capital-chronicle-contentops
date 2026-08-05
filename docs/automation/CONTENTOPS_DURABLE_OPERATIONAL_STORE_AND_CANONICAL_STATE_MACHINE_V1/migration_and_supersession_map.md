# Migration and Supersession Map — Wave 02 Durable Operational Store

Worker Classification:
`PASS_WAVE02_HISTORICAL_SCHEMA_LINEAGE_AND_LEGACY_REPLAY_FINAL_CORRECTION_AWAITING_INDEPENDENT_AUDIT`

## 1. Semantic Migration Registry

`schema_migrations` records each version’s combined semantic checksum, application timestamp, and description. Each immutable `Migration` object also defines SQL text, `transform_version`, canonical transform source/hash, and the semantic checksum over all migration semantics.

The runner:

1. Rejects missing/unknown versions, schema-ahead state, checksum or transform drift, partial application, and populated histories with ambiguous ordering.
2. Creates and integrity-checks a WAL-safe backup before each pending version.
3. Applies SQL and the registered transform in one explicit transaction.
4. Proves pre/post row counts and a canonical legacy transition-record hash; populated v1 histories receive deterministic per-work-item sequence and canonical v3 event chains without fabricated story or authority values.
5. Rolls back and restores the verified backup on failure.

Exact SQL SHA-256, transform versions/source hashes, and semantic checksums are in `schema_manifest.json`. Fresh-store and genuinely populated v1→v2→v3 tests exercise the production runner; no hand-written shortcut migration is used for acceptance.

## 2. Supersession and Integration Map

| Legacy / Surface | Disposition under Wave 02 |
|---|---|
| In-memory server tasks | Read-only quarantined; runtime work-item projection is superseded by `work_items` and `transition_events`. |
| Scheduler JSON and ticks | Transitional; superseded by `operational_windows`, `scheduler_ticks`, leases, and durable work items. |
| Outbox/approval/review JSON or memory surfaces | Retained only as quarantined compatibility surfaces; exact durable entities are recorded in `existing_state_surface_inventory.json`. |
| Status JSON/Markdown | Retained as product/branch authority documentation, never runtime work-item transition authority. |
| Upstream DuckDB bridge | Retained as read-only upstream evidence, not operational mutation authority. |
| Canonical production orchestrator | Integrated through the dependency-injected durable store and explicit operation-contract registry. |
