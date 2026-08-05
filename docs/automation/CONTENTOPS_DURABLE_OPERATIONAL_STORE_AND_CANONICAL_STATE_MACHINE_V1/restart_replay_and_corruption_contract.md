# Restart Replay and Corruption Contract — Wave 02 Durable Operational Store

Worker Classification:
`PASS_WAVE02_HISTORICAL_SCHEMA_LINEAGE_AND_LEGACY_REPLAY_FINAL_CORRECTION_AWAITING_INDEPENDENT_AUDIT`

## 1. Canonical Append-Only Event Log

Every work item starts with a dedicated `WORK_ITEM_CREATED` genesis envelope. Every later state mutation appends one schema-versioned canonical envelope containing event kind/sequence, work-item/story identity, from/to state and versions, actor/reason/explanation hash, correlation/policy/model bindings, authority fields, lease/fencing fields, exact ordered input/output artifact IDs, exact artifact snapshots, timestamp, and previous-event hash.

Store-owned connections install a prepare-time SQLite authorizer that permits INSERT into `transition_events` or `artifact_references` only inside the narrow canonical append or artifact-registration context. Statement caching is disabled, both contexts reset in `finally`, and database triggers provide a second guard for plain external connections. UPDATE/DELETE triggers keep both tables immutable.

These controls prevent accidental or ordinary application-boundary bypass. They do not resist an unrestricted local file owner, which can supply spoofed trigger UDFs, drop schema guards, replace database bytes, or use another SQLite runtime. Such a process can force a write; canonical replay then independently rejects tested illegal edges, protected authority states, sequence/state-version drift, payload/hash/chain drift, artifact snapshot corruption, and projection mismatch. No malicious-local-process resistance is claimed.

## 2. Deterministic Replay

`replay_work_item_events(work_item_id)` verifies every accepted event rather than trusting stored payloads:

1. Accepted envelope schema version and exact genesis kind/bindings.
2. Contiguous event sequence and state version.
3. Legal transition graph edge and exact from/to projection.
4. Recomputed explanation hash, canonical payload, event hash, and previous-event chain.
5. Exact actor, reason, correlation, policy/model, authority, lease/fencing, timestamp, and work-item/story fields.
6. Exact input/output artifact ID arrays and independently reconstructed artifact snapshots, including receipt provenance and reuse scope.
7. Final replayed state/version against the materialized `work_items` projection.

Any mismatch raises `DurableStateCorruptionError`. Direct inserts fail at SQLite trigger enforcement before replay.

## 3. Restart and Orchestrator Recovery

`reconstruct_in_flight_state()` expires stale leases through the injected clock, atomically expires/releases related assignments and heartbeats, replays every work item, and returns a deterministic PASS report only if all projections verify.

Orchestrator operation contracts classify operations as `RESTART_SAFE` or `RECONCILIATION_REQUIRED`, define exact output requirements/canonicalization, and constrain capabilities. Existing `EVIDENCE_PENDING` work cannot be blindly rerun: an explicit attempt decision is required. Dispatcher/output failures append a truthful `EVIDENCE_BLOCKED` event where legal while preserving the original exception.
