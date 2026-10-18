# ContentOps Post-Merge Cross-Plane Replay Consumer — 2026-10-18

Status: `IMPLEMENTED / TESTED / READ_ONLY / EXACT_ARTIFACT_HASH_BOUND`

## BEFORE

ContentOps could consume the Goal 6 cross-plane input, but it had no replay-specific receipt seam
for the exact merged Main post-merge fixture. The remote Main fixture also had to be verified as a
sealed byte artifact before any replay result could be trusted.

## AFTER

`scheduled_shadow_production_day_v1.py` now provides
`reconcile_post_merge_cross_plane_shadow_cycle_replay(...)` and emits
`contentops.cross_plane_shadow_cycle_replay_receipt.v1` with:

- remote Main artifact commit/path, byte count, observed SHA-256 and sealed expected prefix;
- canonical input/self-hash, exact Main source/head, ContentOps master/head and producer commit;
- portable receipt, packet/boundary hash, clock/freshness, rights/redaction and proof bindings;
- current task/identity/destination/store facts and zero-effect flags;
- deterministic classification, blocker list, production-day receipt hash and one exact next action;
- runtime/public proof permanently false.

The adapter calls only the existing `reconcile_cross_plane_shadow_cycle(...)` and scheduled shadow
owner with injected data. It never launches, logs in, reads session material, mutates the store,
calls a provider/model, enables a task, publishes, deploys, or activates V2.

## Exact Main archive readback

Remote Main `origin/main@a3bdedf29e4fc66f917d7fcf1f458821a63d043b` contains:

- `tests/fixtures/cross_plane_shadow_cycle_post_merge_current_real_v1.json`;
- exact byte count: `18,830`;
- exact `input_sha256` prefix: `124311ccd5`;
- observed file SHA-256: `4b208104274a8d02e020cdebfd90793c12f524034694d7b116330f38a4502368`.

The corrected sealed expectation is the actual full SHA-256 above, with prefix `4b208104`. The
remote bytes match the correction exactly. Current-real still remains `NOT_VERIFIED / BLOCKED`
because host identity/readiness and runtime/public boundaries are not proven.

## Fixture matrix

- Exact remote copy: [cross_plane_shadow_cycle_post_merge_current_real_v1.json](../../tests/fixtures/cross_plane_shadow_cycle_post_merge_current_real_v1.json)
- Compact cases: [cross_plane_shadow_cycle_post_merge_replay_cases_v1.json](../../tests/fixtures/cross_plane_shadow_cycle_post_merge_replay_cases_v1.json)
- Durable receipts: [cross_plane_shadow_cycle_replay_receipts_v1.json](../../tests/fixtures/cross_plane_shadow_cycle_replay_receipts_v1.json)

| Case | Result |
|---|---|
| `current_real` | `NOT_VERIFIED`, artifact hash passes; blocked on host/readiness boundaries |
| `healthy` | `NONE`, synthetic shadow composition only |
| `stale` | `RECEIPT_STALE` |
| `mismatch` | `SOURCE_HEAD_MISMATCH` |
| `tampered` | `PACKET_HASH_MISMATCH` |
| `unknown_write` | `UNKNOWN_WRITE` |

## REUSED / CHANGED

- Reused: Goal 6 portable receipt validator, cross-plane adapter, existing V3/editorial/
  destination/scheduled shadow owners and zero-effect boundaries.
- Changed: one replay adapter/receipt seam, exact remote fixture copy, compact scenario descriptors,
  deterministic receipt fixture, focused replay tests and this handoff.
- Main and the dirty canonical ContentOps checkout were not edited.

## EVIDENCE

Replay tests: `5 passed`. The exact current-real fixture is byte-for-byte canonical and preserves
BrowserOS read-only PASS, CDP 9222/9223 unavailable, three Disabled tasks, missing identity and
destination, SQLite read-only integrity and zero-effect counters.

Ruff, `py_compile`, and `git diff --check` pass for the replay seam and tests. Focused owner
regressions reached `135 passed`. Exact-head CI is green on the final remote branch readback.

## BLOCKERS

The remote Main artifact's observed SHA-256 exactly matches the corrected sealed hash. The replay
consumer still does not promote current-real because BrowserOS/CDP/task/identity/destination and
runtime/public boundaries remain unproven.

Corrected current-real replay receipt SHA-256: `c90d41c2471b88d65d8f0052cf396bbf7aedf6261b950e73bdf4cc04aeb2e9db`.

## Exactly one NEXT

Hand the corrected deterministic replay receipt hash back to Main for Goal 9 reconciliation.
