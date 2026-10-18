# ContentOps Post-Merge Cross-Plane Replay Consumer — 2026-10-18

Status: `IMPLEMENTED / TESTED / READ_ONLY / FAIL_CLOSED_ON_SEALED_ARTIFACT_MISMATCH`

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

The supplied sealed expectation is prefix `4b208204`. The remote bytes do not match that prefix,
so the current-real replay receipt is `NOT_VERIFIED / BLOCKED` with blocker
`main_fixture_sha256_prefix_mismatch`. No replay promotion is inferred from the matching size or
input hash.

## Fixture matrix

- Exact remote copy: [cross_plane_shadow_cycle_post_merge_current_real_v1.json](../../tests/fixtures/cross_plane_shadow_cycle_post_merge_current_real_v1.json)
- Compact cases: [cross_plane_shadow_cycle_post_merge_replay_cases_v1.json](../../tests/fixtures/cross_plane_shadow_cycle_post_merge_replay_cases_v1.json)
- Durable receipts: [cross_plane_shadow_cycle_replay_receipts_v1.json](../../tests/fixtures/cross_plane_shadow_cycle_replay_receipts_v1.json)

| Case | Result |
|---|---|
| `current_real` | `NOT_VERIFIED`, blocked on sealed file hash mismatch |
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

Ruff, `py_compile`, and `git diff --check` pass for the replay seam and tests. Full owner
regressions and exact-head CI remain required after the branch is pushed.

## BLOCKERS

The remote Main artifact's observed SHA-256 starts `4b208104`, not the sealed contract prefix
`4b208204`. The replay consumer intentionally stops on this discrepancy and does not promote the
current-real input.

## Exactly one NEXT

Hand the deterministic replay receipt hash back to Main for the next reconciliation goal, with the
sealed file-hash discrepancy attached for correction.
