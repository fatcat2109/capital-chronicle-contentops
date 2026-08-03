# Migration and Supersession Map — Wave 02 Durable Operational Store

## 1. Schema Migration Framework

The migration engine inside `ContentOpsDurableStore` implements:
- **Version Tracking:** Table `schema_migrations` records `(version, checksum, applied_at, description)`.
- **Checksum Verification:** Every migration SQL script is hashed with SHA-256 and checked against recorded checksums during initialization.
- **Backup & Fail-Closed Rollback:** Before applying any migration version, a database snapshot `.sqlite.bak.<timestamp>` is created. If an error occurs, the transaction is rolled back, the backup is restored, and a `MigrationError` is raised.
- **Preflight Check:** Runs `PRAGMA integrity_check;` before and after migrations to verify SQLite B-tree structural health.

## 2. Supersession & Integration Map

| Legacy / Surface | Location | Disposition under Wave 02 |
|---|---|---|
| In-memory server state | `live_contentops/server.py` | Quarantined; superseded by `ContentOpsDurableStore` |
| Legacy scheduler script | `live_contentops/scheduler_v6.py` | Quarantined; superseded by durable leases and `operational_windows` table |
| JSON state coordination | `docs/status/current_project_status.json` | Retained as root product status document; not used for runtime work-item state transitions |
| Upstream DuckDB bridge | `live_contentops/governed_upstream_bridge_v1.py` | Retained as read-only upstream evidence bridge for Capital Chronicle inputs |
| Canonical orchestrator | `live_contentops/production_orchestrator_v1.py` | Integrated via dependency-injected `store` parameter |
