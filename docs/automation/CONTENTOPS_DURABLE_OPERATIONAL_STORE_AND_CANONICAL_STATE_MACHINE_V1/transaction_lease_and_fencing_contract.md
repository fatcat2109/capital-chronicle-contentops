# Transaction Lease and Fencing Contract — Wave 02 Durable Operational Store

Worker Classification:
`PASS_WAVE02_HISTORICAL_SCHEMA_LINEAGE_AND_LEGACY_REPLAY_FINAL_CORRECTION_AWAITING_INDEPENDENT_AUDIT`

## 1. Transaction and Clock Model

All competing lease, claim, assignment, heartbeat, release, recovery, and state-transition mutations use explicit transactions and the injected UTC clock. Focused tests use a fake clock; no wall-clock sleep determines acceptance.

## 2. Monotonic Fencing and Assignment Rules

1. `acquire_lease` rejects an unexpired ACTIVE owner, then increments the persisted fencing token for each new ownership epoch.
2. `claim_work_item` validates lease owner, key, expiry, and fencing token before creating an ACTIVE assignment.
3. A partial unique index enforces exactly zero or one ACTIVE assignment for each work item at the database boundary.
4. `renew_lease`, heartbeat recording, and `transition_state` require the current owner/fencing epoch; stale or expired workers fail closed.
5. `release_lease`, expiry recovery, and reclaim atomically release/expire prior assignments and dispose related heartbeats before a successor claims.
6. Fencing tokens never decrease; an earlier worker cannot mutate after a later epoch is issued.

## 3. Compare-and-Set State Transitions

Every work-item transition verifies expected current state, expected state version, current lease owner, and current fencing token in one transaction. The canonical event append and projection update commit together. A concurrent or stale caller receives the relevant CAS, lease, or fencing error; exactly one valid worker succeeds.

## 4. Recovery Proof

Acceptance tests prove fake-clock acquisition/renewal/expiry, release/reclaim, heartbeat disposition, assignment status changes, monotonically increasing fencing, exact ACTIVE assignment count, and successful event replay after recovery.
