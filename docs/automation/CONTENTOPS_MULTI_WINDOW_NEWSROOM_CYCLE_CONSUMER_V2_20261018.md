# ContentOps Multi-Window Newsroom Cycle Consumer V2 — 2026-10-18

Status: `IMPLEMENTED / TESTED / INTEGRATED / READ_ONLY / SHADOW_ONLY`

## BEFORE

The accepted v1 consumer preserved the earlier multi-window contract and its fixture-only
receipt path. Main now has a merged normalized bundle on `origin/main`, so ContentOps needed a
separate v2 seam that binds the exact merged artifact bytes, carries the normalized window and
projection lineage, and still reuses the existing scheduled shadow owner.

## AFTER

`live_contentops/multi_window_newsroom_cycle_consumer_v2.py` consumes
`CapitalChronicleMultiWindowIntelligenceCycleBundleV1` from the merged Main archive and emits
`contentops.multi_window_newsroom_cycle_receipt.v2`.

The consumer binds and verifies:

- Main repository `fatcat2109/Headline-Raw-data-json`, ref `main`, commit
  `11323a08706cfb90a9f62233598b8ba3e5e6b307`;
- artifact `tests/fixtures/multi_window_intelligence_cycle_bundle_current_v1.json`;
- 53,548 bytes, file SHA-256
  `5d76952bc3c9709f9cc910ab9333144bd5c8ec508e53bc3ed3221e95c3ad2129`;
- bundle SHA-256 `9e113fd45caf623458f7bb2adfe9b43fe204cb10d96abe62b718f6a13affaed9`;
- cycle `multi-window-cycle-ed95e189282d21a03a9f26f9`;
- parent reconciliation receipt
  `313631f2c3c16ce8fa0de5de7d08aefe961caecbfa4d1e95842c7e43a3cddc29`;
- parent Main input `8f66238d320062e9258c893d59d2293253655f94`, ContentOps input
  `aa5dbda6c73a4f53683365ce26c6323ec57298a9`, and parent ContentOps consumer
  `f3fb9fb273261d94850007db19aedf4171014c19`.

The receipt verifies the top-level shape, bundle hash, every window hash and order, both
projection hashes, parent binding, rights, freshness/PIT boundaries, authority flags, zero-effect
counters, secret markers, and exact artifact-to-payload equality. It preserves `CURRENT_REAL`,
`RECENT_REPLAY`, and `PROXY_CONTEXT` in one immutable receipt. Exact replay rows may feed the
existing injected shadow owner; proxy context remains qualitative, duplicates remain collapsed,
contradictions remain quarantined, and current-real remains abstained when its drift is
`NOT_VERIFIED`.

## Fixture matrix

- Merged Main artifact: [multi_window_intelligence_cycle_bundle_current_v1.json](../../tests/fixtures/multi_window_intelligence_cycle_bundle_current_v1.json)
- V2 case inputs: [multi_window_newsroom_cycle_v2_cases_v1.json](../../tests/fixtures/multi_window_newsroom_cycle_v2_cases_v1.json)
- V2 receipts: [multi_window_newsroom_cycle_v2_receipts_v1.json](../../tests/fixtures/multi_window_newsroom_cycle_v2_receipts_v1.json)

| Case | Classification | Artifact state |
|---|---|---|
| `current_real` | `NOT_VERIFIED` | `SEALED_MATCH` |
| `healthy` | `SHADOW_CONFIRMED` | `SYNTHETIC` |
| `interruption_resume` | `SHADOW_CONFIRMED` | `SYNTHETIC` |
| `stale`, `future` | `STALE` | `SYNTHETIC` |
| `source_head_mismatch` | `SOURCE_HEAD_MISMATCH` | `SYNTHETIC` |
| `bundle_hash_mismatch`, `tampered` | `PACKET_HASH_MISMATCH` | `SYNTHETIC` |
| `authority_flag` | `AUTHORITY_FLAG` | `SYNTHETIC` |
| `unknown_write` | `UNKNOWN_WRITE` | `SYNTHETIC` |

## REUSED

- Existing v1 consumer policy and three-window semantics.
- Existing `run_scheduled_shadow_production_day(...)` owner and eight-destination registry.
- Existing zero-write, interruption/resume, source-recovery, destination-readback, and current
  host observation boundaries.

## CHANGED

- Added the v2 merged-artifact consumer and v2 immutable receipt schema.
- Added exact Main artifact bytes plus ten deterministic case inputs and ten receipt outputs.
- Added projection self-hash, secret-value, and artifact payload equality checks.
- Added focused round-trip and fail-closed tests.

Main, database, scheduler, status, publication, browser, provider, model, and V2 public-write
owners were not edited or invoked. No public write, login, token, cookie, deployment, or runtime
restart occurred.

## EVIDENCE

- Focused v2 tests: `8 passed`.
- Combined v2 plus accepted owner regression suite: `154 passed in 11.67s`.
- Ruff, `py_compile`, and `git diff --check`: passed.
- Healthy synthetic composition produced exactly eight derivative shadow destinations and retained
  `runtime_proven=false` and `publicly_proven=false`.
- The sealed current-real artifact remained `NOT_VERIFIED / BLOCKED`; retained facts include
  scheduler tasks `Disabled`, identity/destination `MISSING`, SQLite integrity `ok`, and no
  runtime/public proof.

## BLOCKERS

The merged artifact and parent reconciliation are bound and consumed, but current-real host
readiness is still `NOT_VERIFIED`. The v2 consumer therefore remains read-only and shadow-only;
it does not promote runtime, account identity, destination identity, or public publication.

## Exactly one NEXT

Obtain the exact owner grant for zero-write Desktop Automation enablement and calendar-time host
runtime proof, then rerun this v2 seam with the fresh sealed Main bundle while retaining all
runtime and public-write gates closed.
