# ContentOps Editorial Adjudication and Prioritization Pack V1 — 2026-10-18

Status: `IMPLEMENTED / TESTED / INTEGRATED / READ_ONLY / SHADOW_ONLY`

## BEFORE

Main had the merged outcome-evaluation bundle over the Goal 10/11 bundle and Goal 11 quality
ledger. ContentOps had the Goal 12 traceability pack and eight-derivative shadow mapping, but no
deterministic adjudication surface that classified every candidate as prioritized, context-only,
abstained, or quarantined with bounded editorial priority metadata.

## AFTER

`live_contentops/editorial_adjudication_prioritization_pack_v1.py` emits
`contentops.editorial_adjudication_prioritization_pack.v1` and verifies its self-hash.

The exact Main artifact is:

- repository `fatcat2109/Headline-Raw-data-json`, ref `main`;
- commit `dcbeb56608672a7b17ec1bb084ee6863c9c2a10c`;
- path `tests/fixtures/multi_window_outcome_evaluation_current_v1.json`;
- 33,663 bytes;
- file SHA-256 `3e0964e818a95923823f584b61529ef0288ddac58916371a8474a6eaeffd6f76`;
- evaluation SHA-256 `ae67ad70a7a692a7c92003a3fb3d4869fd3898ee3dc5b0ed07166c39c960a043`.

The literal observed Main schema is `CapitalChronicleOutcomeEvaluationBundleV1`; the requested
contract name `CapitalChronicleDecisionEvidencePrioritizationPackV1` is retained as the requested
contract binding. No unverified schema was invented.

Parent bindings preserve Goal 9 receipt
`313631f2c3c16ce8fa0de5de7d08aefe961caecbfa4d1e95842c7e43a3cddc29`, Goal 10 bundle SHA-256
`9e113fd45caf623458f7bb2adfe9b43fe204cb10d96abe62b718f6a13affaed9`, Goal 11 ledger SHA-256
`834d5fb73a4a299392419cde850b0adb0e5746fb6fdfc14743f13077d75c8697`, and Goal 12 traceability
pack identity.

## Policy and mappings

Every candidate retains source/evidence hashes, duplicate and contradiction lineage,
exact/proxy/context state, PIT/freshness/rights, outcome slots, proof layer, basis-risk labels,
unsupported dimensions, and a deterministic decision:

- exact replay/current rights-compatible rows can be prioritized for editorial review;
- current-real `NOT_VERIFIED` rows abstain;
- proxy/context rows remain qualitative context with basis risk;
- contradictions remain quarantined with both source hashes;
- stale/future/rights-invalid/secret/UNKNOWN_WRITE rows fail closed;
- missing outcomes stay `OUTCOME_PENDING`, `NOT_COMPARABLE`, or `NOT_VERIFIED`.

The editorial priority matrix contains bounded integer evidence/compatibility components and
missingness states. It creates no aggregate, audience, forecast, performance, or Core Analyzer
score.

The pack maps claims to draft sections, the canonical shadow article, exactly eight derivative
packages, destination shadow readback, and interruption/resume. Source/evidence hashes are
retained for every section and derivative. Runtime/public/realized authority remains false.

## Fixture matrix

- Exact Main outcome evaluation: [multi_window_outcome_evaluation_current_v1.json](../../tests/fixtures/multi_window_outcome_evaluation_current_v1.json)
- Clean synthetic outcome evaluation: [multi_window_outcome_evaluation_clean_synthetic_v1.json](../../tests/fixtures/multi_window_outcome_evaluation_clean_synthetic_v1.json)
- Adjudication case metadata: [editorial_adjudication_prioritization_pack_cases_v1.json](../../tests/fixtures/editorial_adjudication_prioritization_pack_cases_v1.json)
- Adjudication receipts: [editorial_adjudication_prioritization_pack_receipts_v1.json](../../tests/fixtures/editorial_adjudication_prioritization_pack_receipts_v1.json)

The 20 cases cover exact Main, current-real, five-candidate mixed windows, duplicate lineage,
contradiction quarantine, proxy-only context, synthetic complete shadow, horizon/unit mismatch,
stale/future, source/hash/tamper/secret/rights/authority/UNKNOWN_WRITE, eight-derivative shadow,
interruption/resume, and deterministic repeat.

## REUSED / CHANGED

- Reused Goal 9–12 hashes, traceability pack, multi-window V2 consumer, outcome proof layers,
  existing article/derivative/destination shadow owners, and eight-destination registry.
- Added one pure adjudication/prioritization consumer, bounded priority matrix, abstention/
  quarantine ledger, outcome boundary map, fixtures, focused tests, and this handoff.

No Main, database, scheduler, status owner, publisher, browser, provider/model, store, deployment,
V2 activation, account, login, or public-write action occurred.

## EVIDENCE

- Focused Goal 13 tests: `19 passed`.
- Main/Goal 10–12 fixtures and Goal 13 receipts: exact hashes recorded above.
- Clean synthetic case: `SHADOW_CONFIRMED` with exactly eight derivative mappings.
- Exact current case: `NOT_VERIFIED`; current-real remains abstained.
- Ruff, `py_compile`, and `git diff --check`: pending final validation bundle.

## BLOCKERS

The exact Main evaluation remains degraded by parent quality/current-real/contradiction evidence.
The pack preserves those blockers and does not promote analytical, forecast, runtime, realized, or
public authority.

## Exactly one NEXT

Have Main provide the next adjudication/evaluation bundle with fresh compatible evidence and run it
through this pack while preserving the same fail-closed policy and eight-derivative shadow owner.
