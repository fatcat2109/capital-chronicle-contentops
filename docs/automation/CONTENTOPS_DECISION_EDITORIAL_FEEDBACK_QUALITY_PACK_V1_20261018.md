# ContentOps Decision-to-Editorial Feedback Quality Pack V1 — 2026-10-18

Status: `IMPLEMENTED / TESTED / INTEGRATED / READ_ONLY / SHADOW_ONLY`

## BEFORE

Main had the merged Goal 13 decision/evidence prioritization pack and ContentOps had the Goal 13
editorial adjudication pack. There was no deterministic bidirectional receipt proving that every
Main candidate had an editorial handling result, agreement/disagreement reason, section/article/
derivative traceability, and destination shadow consistency.

## AFTER

`live_contentops/decision_editorial_feedback_quality_pack_v1.py` emits
`contentops.decision_editorial_feedback_quality_pack.v1`.

Exact Main binding:

- repository `fatcat2109/Headline-Raw-data-json`, ref `main`;
- commit `1bbb21dc1e2c9dbf6b09ada84fc45d98101b6e62`;
- artifact `tests/fixtures/decision_evidence_prioritization_pack_current_v1.json`;
- 45,748 bytes;
- file SHA-256 `4e5a1131326f55533e9e9fe654f76156e8d03873f6f2a6b323056c6df386ed6c`;
- Main pack SHA-256 `9f42139c1f188eda32051d0dfc1aa5786ee2b1743ba7fb7f9794e82804d420ed`.

Parent Goal 9–12 hashes are retained, together with the Goal 13 ContentOps adjudication pack and
Goal 12 traceability pack. Main remains the analytical/Core eligibility authority. ContentOps
reports editorial handling and traceability only.

## Feedback policy

Every candidate is mapped bidirectionally with:

- Main decision and ContentOps decision;
- source/evidence hashes from both sides;
- duplicate and contradiction lineage;
- exact/proxy/context state;
- PIT, freshness, rights, horizon/unit/clock compatibility;
- explicit agreement/disagreement reasons and unsupported dimensions.

Current-real stays `NOT_VERIFIED`; proxy/context rows remain qualitative; contradictions remain
quarantined with both source hashes; stale/future/rights-invalid/secret/UNKNOWN_WRITE rows fail
closed. Missing outcome states remain `OUTCOME_PENDING`, `NOT_COMPARABLE`, or `NOT_VERIFIED`.

The editorial quality matrix uses bounded integer counts for source coverage, lineage, contradiction
handling, abstention fidelity, exact/proxy separation, outcome-state fidelity, derivative
consistency, and destination shadow consistency. Components carry missingness/comparability state;
no score, forecast, audience, performance, runtime, or public claim is created.

## Traceability and shadow

The pack carries section traceability, canonical article traceability, exactly eight derivative
packages where the synthetic cycle is complete, destination shadow readback, interruption/resume,
abstention/quarantine ledger, outcome proof layers, zero-effect counters, proof axes, blockers,
next, and `pack_sha256`. Orphan sections, orphan derivatives, duplicate payloads, candidate-set
drift, contradiction mismatch, and source/hash disagreement are explicit blockers/disagreements.

## Fixture matrix

- Exact Main pack: [decision_evidence_prioritization_pack_current_v1.json](../../tests/fixtures/decision_evidence_prioritization_pack_current_v1.json)
- Clean Main pack: [decision_evidence_prioritization_pack_clean_synthetic_v1.json](../../tests/fixtures/decision_evidence_prioritization_pack_clean_synthetic_v1.json)
- Feedback case metadata: [decision_editorial_feedback_quality_pack_cases_v1.json](../../tests/fixtures/decision_editorial_feedback_quality_pack_cases_v1.json)
- Feedback receipts: [decision_editorial_feedback_quality_pack_receipts_v1.json](../../tests/fixtures/decision_editorial_feedback_quality_pack_receipts_v1.json)

The 22 cases cover exact merged Main, fixture-only fallback, all candidates accounted, missing
candidate, orphan draft section, orphan derivative, duplicate payload, contradiction mismatch,
proxy promotion, stale/future, source/head/pack hash mismatch, tampered, secret, rights, authority,
UNKNOWN_WRITE, current-real, complete synthetic eight-derivative shadow, interruption/resume, and
deterministic repeat.

## REUSED / CHANGED

- Reused Goal 8–13 receipts, Goal 12 traceability maps, Goal 13 adjudication, Main parent hashes,
  existing article/derivative/destination shadow owners, and the native eight-destination registry.
- Added one pure feedback quality producer/consumer, quality matrix, disagreement ledger, fixtures,
  tests, and this handoff.

No Main, database, scheduler, status owner, publisher, browser, provider/model, store, deployment,
V2 activation, login, account selection, or public-write action occurred.

## EVIDENCE

- Focused Goal 14 suite: `24 passed`.
- Final validation bundle: pending.
- Ruff, `py_compile`, and `git diff --check`: passed for Goal 14 files.
- Complete synthetic cycle: `SHADOW_CONFIRMED` with exactly eight destination mappings.
- Exact current cycle: `NOT_VERIFIED` with current-real and contradiction boundaries preserved.

## BLOCKERS

The exact Main quality state remains degraded and the feedback pack preserves that state. It does
not promote Main or ContentOps into score, forecast, runtime, realized, or public authority.

## Exactly one NEXT

Have Main provide the next prioritization pack with fresh compatible evidence and consume it through
this feedback seam while retaining all disagreement, abstention, outcome, and eight-destination
shadow boundaries.
