# Restart Replay and Corruption Contract — Wave 02 Durable Operational Store

Worker Classification:
`PASS_WAVE02_MIGRATION_REPLAY_ASSIGNMENT_AND_EVIDENCE_FINAL_ACCEPTANCE_CORRECTION_AWAITING_INDEPENDENT_AUDIT`

## 1. Canonical Append-Only Event Log

Every work item starts with a dedicated `WORK_ITEM_CREATED` genesis envelope. Every later state mutation appends one schema-versioned canonical envelope containing event kind/sequence, work-item/story identity, from/to state and versions, actor/reason/explanation hash, correlation/policy/model bindings, authority fields, lease/fencing fields, exact ordered input/output artifact IDs, exact artifact snapshots, timestamp, and previous-event hash.

Only the internal event append transaction enables the connection-local `contentops_append_authorized()` function. `trg_transition_events_append_authorized` rejects direct INSERT, and no-update/no-delete triggers reject mutation. Authorization resets in `finally` after both success and failure.

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
