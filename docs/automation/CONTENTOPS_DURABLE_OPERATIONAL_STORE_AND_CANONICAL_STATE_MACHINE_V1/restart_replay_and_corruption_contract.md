# Restart Replay and Corruption Contract — Wave 02 Durable Operational Store

## 1. Append-Only Transition Event Log

All state transitions produce an immutable record in `transition_events`.

Table columns:
- `event_id`: Primary key (`evt_<hash>`)
- `transition_key`: Unique transition identifier (`tr_<work_item_id>_v<ver>_<hash>`)
- `work_item_id`: Foreign key to `work_items`
- `from_state` & `to_state`: Pinned state strings
- `state_version`: Monotonic 1-based version number
- `actor_class` & `actor_ref`: Responsible process/agent
- `reason_code` & `explanation`: Structured decision rationale
- `artifact_hash_set`: JSON array of SHA-256 artifact hashes
- `correlation_id`: Traceability identifier
- `timestamp_utc`: ISO UTC timestamp
- `authority_granted`: Integer boolean (0 or 1)

### Append-Only Triggers
Two SQLite database triggers (`trg_transition_events_no_update` and `trg_transition_events_no_delete`) abort any SQL `UPDATE` or `DELETE` attempt on `transition_events` with `RAISE(ABORT)`.

## 2. Deterministic Event Replay (`replay_work_item_events`)

`replay_work_item_events(work_item_id)` re-simulates state evolution from initial state `DISCOVERED` at `state_version = 1` through every event in `transition_events` ordered by `state_version ASC`.

Verification rules:
1. Every event's `from_state` must equal the computed state from the preceding event.
2. Every event's `state_version` must equal `previous_version + 1`.
3. The final replayed state and state_version must match `work_items.current_state` and `work_items.state_version`.

If any mismatch occurs (e.g. manual table mutation, missing event, or corrupted state), `replay_work_item_events()` raises `DurableStateCorruptionError`.

## 3. Restart Safety & Recovery (`reconstruct_in_flight_state`)

On system startup or crash recovery, `reconstruct_in_flight_state()`:
1. Evaluates all active leases and marks expired leases as `EXPIRED`.
2. Iterates over all work items in `work_items` and runs `replay_work_item_events()` to assert zero state corruption.
3. Emits a deterministic restart reconstruction report (`restart_reconstruction_status = "PASS"`).
