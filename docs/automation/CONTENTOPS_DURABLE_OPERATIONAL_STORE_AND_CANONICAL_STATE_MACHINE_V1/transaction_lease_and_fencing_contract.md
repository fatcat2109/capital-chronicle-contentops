# Transaction Lease and Fencing Contract — Wave 02 Durable Operational Store

## 1. Concurrency and Lease Model

`ContentOpsDurableStore` implements distributed work-item and operational leases in the `leases` table.

Table columns:
- `lease_id`: Primary key string (`lease_<hash>`)
- `lease_key`: Unique string identifier (e.g. `scheduler_master` or `lease_wi_123`)
- `work_item_id`: Optional foreign key to `work_items`
- `owner_ref`: Identity string of worker acquiring the lease
- `fencing_token`: Monotonically increasing 64-bit integer
- `acquired_at`: ISO UTC timestamp
- `renewed_at`: ISO UTC timestamp
- `expires_at`: ISO UTC timestamp
- `status`: State string (`ACTIVE`, `EXPIRED`, `RELEASED`)

## 2. Monotonic Fencing Token Protocol

1. **Acquisition (`acquire_lease`):**
   - Atomically checks existing lease for `lease_key`.
   - If an `ACTIVE` lease exists and `expires_at > now_utc`, fails with `LeaseConflictError`.
   - Increments `fencing_token` to `existing.fencing_token + 1` (or `1` for new leases).
   - Reuses or inserts lease record with `status = 'ACTIVE'`.
2. **Renewal (`renew_lease`):**
   - Validates that caller's `fencing_token` equals current DB `fencing_token`.
   - If caller presents a lower `fencing_token`, raises `StaleFencingTokenError`.
   - Updates `renewed_at` and `expires_at`.
3. **Release (`release_lease`):**
   - Validates caller's `fencing_token` and updates `status = 'RELEASED'`.
4. **Stale Lease Recovery (`recover_stale_leases`):**
   - Transitions any lease with `status = 'ACTIVE'` and `expires_at < now_utc` to `'EXPIRED'`.

## 3. Compare-And-Set (CAS) State Transitions

Every state transition on `work_items` verifies `(current_state == expected_from_state AND state_version == expected_state_version)`.
If a concurrent worker mutates the work item first, the CAS check fails, rolling back the transaction and raising `CASStateConflictError`. Exactly one worker succeeds.
