# ContentOps Cross-Plane Shadow-Cycle Consumer — 2026-10-17

Status: `IMPLEMENTED / TESTED / INTEGRATED / READ_ONLY / SHADOW_ONLY`

## BEFORE

Main could produce a portable host-readiness receipt, and ContentOps could run its existing
scheduled shadow owner, but there was no bounded consumer for one canonical Main
`CapitalChronicleCrossPlaneShadowCycleInputV1` envelope. Hash, source-head, clock, current-host
fact, and authority-boundary drift could therefore not be reconciled in one immutable receipt.

## AFTER

`scheduled_shadow_production_day_v1.py` now provides one pure
`reconcile_cross_plane_shadow_cycle(...)` adapter that:

- validates strict canonical JSON and the Main input self-hash;
- validates the embedded portable receipt with the existing producer validator;
- checks repository/ref/exact head, portable producer schema/commit, packet/boundary hashes,
  proof layers, observation clocks, freshness, rights/redaction, current task/identity/
  destination/store facts, and zero-effect counters;
- requires Main authority, public, runtime, provider, model, network, and external-effect flags
  to be false;
- admits only the injected existing `run_scheduled_shadow_production_day(...)` seam;
- emits `contentops.cross_plane_shadow_cycle_receipt.v1` with input, portable, production-day,
  source/head, clock, proof-axis, blocker, and next bindings;
- uses only the finite classifications `NONE`, `SOURCE_HEAD_MISMATCH`, `PACKET_HASH_MISMATCH`,
  `RECEIPT_STALE`, `PROOF_LAYER_MISMATCH`, `TASK_STATE_MISMATCH`, `UNKNOWN_WRITE`,
  `AUTHORITY_FLAG`, `AMBIGUOUS`, and `NOT_VERIFIED`.

## Preserved current facts

The `current_real` input and receipt fixtures retain the accepted Goal 5 observation:

- BrowserOS Neo MCP read-only `PASS` at `http://127.0.0.1:9010/mcp`, server `browseros-neo`
  `0.0.72`, protocol `2025-06-18`, allowlist `name_session/read/tabs`;
- CDP 9222 and 9223 `UNAVAILABLE`;
- all three scheduled ContentOps tasks `Disabled`;
- account identity and destination identity `MISSING`;
- SQLite read-only integrity `ok`, zero foreign-key violations, preserved counters and zero
  effect flags;
- runtime/public proof remain false and `UNKNOWN_WRITE` remains a stop condition.

## Fixture matrix

Inputs: [cross_plane_shadow_cycle_inputs_v1.json](../../tests/fixtures/cross_plane_shadow_cycle_inputs_v1.json)

Receipts: [cross_plane_shadow_cycle_receipts_v1.json](../../tests/fixtures/cross_plane_shadow_cycle_receipts_v1.json)

| Case | Result |
|---|---|
| `current_real` | `NOT_VERIFIED` |
| `healthy` | `NONE`, one read-only shadow composition |
| `stale` | `RECEIPT_STALE` |
| `mismatch` | `SOURCE_HEAD_MISMATCH` |
| `ambiguous` | `AMBIGUOUS` |
| `tampered` | `NOT_VERIFIED` |
| `unknown_write` | `UNKNOWN_WRITE` |

## REUSED / CHANGED

- Reused: Goal 5 portable receipt producer, existing scheduled shadow owner, V3 evidence bridge,
  dual-lane newsroom, destination/readback shadow seams, and zero-effect boundaries.
- Changed: one adapter in the existing scheduled shadow owner, one Main-contract input fixture,
  one deterministic output receipt fixture, focused rejection/round-trip tests, and this handoff.
- Main was not edited. No second scheduler, analyzer, status owner, database lane, browser action,
  provider/model call, task enablement, login, account selection, public write, deployment, or V2
  activation occurred.

## EVIDENCE

Focused cross-plane tests: `9 passed`.

Owner compatibility suite: `90 passed` across cross-plane, portable receipt, host-readiness,
scheduled-shadow, Main handoff, dual-lane, and destination identity regressions.

BrowserOS/source-recovery and destination shadow regressions: `40 passed`.

Combined focused evidence: `130 passed`.

Ruff, `py_compile`, and `git diff --check` passed. The healthy case proves shadow composition only;
it does not prove runtime readiness, public readiness, or publication authority.

## BLOCKERS

The current-real observation remains `NOT_VERIFIED` because CDP and account/destination identity
are unavailable or missing. The adapter preserves that state. `UNKNOWN_WRITE` is fail-closed and
cannot be retried or promoted by this consumer.

## Exactly one NEXT

Have Main submit one canonical cross-plane input after merge; ContentOps should consume it only when
its source/head, hashes, clocks, facts, proof layers, rights, and authority flags reconcile to
`NONE`, then retain the resulting receipt as shadow-only evidence.
