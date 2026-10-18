# ContentOps Editorial Traceability and Quality Pack V1 — 2026-10-18

Status: `IMPLEMENTED / TESTED / INTEGRATED / READ_ONLY / SHADOW_ONLY`

## BEFORE

Main had a merged Goal 11 quality replay ledger containing claim lineage, dedupe, contradiction,
PIT/freshness/rights, replay stages, and pending outcomes. ContentOps had the merged Goal 10/11
newsroom receipts and eight destination shadow owner, but no one pack connecting every retained
claim to editorial decisions, draft sections, derivative payloads, destination shadow, and outcome
limits.

## AFTER

`live_contentops/editorial_traceability_quality_pack_v1.py` builds and verifies the deterministic
`contentops.editorial_traceability_quality_pack.v1` schema. It consumes the exact Main ledger,
the Goal 10 V1 newsroom receipt, the Goal 11 V2 receipt, and an injected package list. It does
not call a provider/model/browser or mutate a scheduler, store, database, status owner, or
publisher.

The pack binds:

- Main `fatcat2109/Headline-Raw-data-json`, `main`, commit
  `3cef3081d624534417f56cea836605a48a059af9`;
- ledger path `tests/fixtures/multi_window_quality_replay_ledger_current_v1.json`;
- 29,098 bytes, file SHA-256
  `0e20a099483287195b7760a2cddec1bac09a482c92079cf04190091c3cb1e669`;
- ledger SHA-256 `834d5fb73a4a299392419cde850b0adb0e5746fb6fdfc14743f13077d75c8697`;
- Goal 10 bundle SHA-256 `9e113fd45caf623458f7bb2adfe9b43fe204cb10d96abe62b718f6a13affaed9`;
- Goal 9 reconciliation receipt
  `313631f2c3c16ce8fa0de5de7d08aefe961caecbfa4d1e95842c7e43a3cddc29`;
- Goal 10 V1 receipt and Goal 11 V2 receipt identities;
- ContentOps current merged head `a0c62b3470ad801bc38efae2ef6671d3ad3ef2d0` and Goal 11
  source head `8571cca13cff70fed69da113f96c243e62962170`.

## Policy and mappings

The policy matrix is explicit:

- exact/current rights-allowed rows may support Core/editorial;
- recent replay is admitted only within its exact PIT/rights replay boundary;
- current-real `NOT_VERIFIED` rows abstain while keeping facts and hashes;
- proxy rows remain qualitative context;
- contradiction rows are quarantined with both source hashes;
- stale/future/rights-invalid/UNKNOWN_WRITE rows abstain or fail closed.

Each retained claim carries source/evidence hashes, source lineage, dedupe group, contradiction
group, clocks, PIT/freshness, rights, Core/editorial eligibility, unsupported dimensions, decision,
reason, uncertainty label, and conflict label. Each claim is mapped to a draft evidence section.
Selected claims are mapped to the canonical shadow article and exactly eight derivative packages;
each package retains a payload hash, destination, source hashes, readback shadow state, and the
existing interruption/resume state.

Outcome fields remain `OUTCOME_PENDING`, `NOT_COMPARABLE`, or `NOT_VERIFIED`. The pack emits no
performance, forecast, runtime, or public claims and keeps runtime/public proof false.

## Fixture matrix

- Exact Main ledger: [multi_window_quality_replay_ledger_current_v1.json](../../tests/fixtures/multi_window_quality_replay_ledger_current_v1.json)
- Main ledger case metadata: [multi_window_quality_replay_ledger_cases_v1.json](../../tests/fixtures/multi_window_quality_replay_ledger_cases_v1.json)
- Pack inputs: [editorial_traceability_quality_pack_cases_v1.json](../../tests/fixtures/editorial_traceability_quality_pack_cases_v1.json)
- Pack receipts: [editorial_traceability_quality_pack_receipts_v1.json](../../tests/fixtures/editorial_traceability_quality_pack_receipts_v1.json)

The 17 cases cover exact merged current, synthetic complete, current-real abstention,
replay/proxy/context, duplicate collapse, contradiction quarantine, stale, future, source-head
mismatch, ledger hash mismatch, tampering, secret marker, rights invalid, authority flag,
UNKNOWN_WRITE, incomplete eight-derivative consistency, and interruption/resume.

## REUSED

- Goal 9 reconciliation receipt and exact parent source heads.
- Goal 10 normalized three-window bundle and V1 newsroom receipt.
- Goal 11 V2 receipt, current-real host facts, eight-destination shadow semantics, and existing
  destination registry.

## CHANGED

- Added one pure quality-pack builder/verifier.
- Added claim-to-source, claim-to-editorial, claim-to-section, claim-to-derivative, and outcome
  evaluation mappings.
- Added integer quality counts, proof axes, zero-effect counters, finite classification/blocker/
  next, self-hash, and a 17-case fixture/receipt matrix.

No Main files, database files, scheduler/status owners, publication authority, browser/session,
provider/model, public write, deployment, or V2 activation were changed or invoked.

## EVIDENCE

- Focused Goal 12 suite: `17 passed`.
- Ruff, `py_compile`, and `git diff --check`: passed.
- Synthetic complete ledger reaches `SHADOW_CONFIRMED` with exactly eight derivative packages.
- Exact Main ledger remains `NOT_VERIFIED` where current-real/parent evidence is not verified.
- Every outcome remains pending or non-comparable; runtime and public proof remain false.

## BLOCKERS

The pack preserves the merged ledger's `NOT_VERIFIED` quality state for the exact current-real
case. It does not create runtime, performance, forecast, account, or public authority.

## Exactly one NEXT

Have Main provide the next evaluation ledger with fresh outcome evidence; consume it through this
pack while preserving the same claim lineage, rights, uncertainty, derivative, and no-promotion
boundaries.
