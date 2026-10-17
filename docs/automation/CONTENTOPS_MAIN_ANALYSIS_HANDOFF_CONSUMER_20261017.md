# ContentOps Main App Analysis Handoff Consumer — 2026-10-17

Status: `IMPLEMENTED / FIXTURE_PROVEN / SHADOW_REVIEW_READY / NO_LIVE_WRITE`

## BEFORE

ContentOps already had the governed V3 evidence contract, its frozen V2 projection, the
`cc_evidence_bridge_v2` validator, dual-lane CORE V0 shadow newsroom, eight-role editorial
review, and the scheduled production-day shadow owner. It did not have one consumer-side seam
that accepted a self-contained Main App `DailyIntelligenceDecisionPacketV1` bridge fixture and
carried its producer-owned lineage through those existing owners.

## AFTER

`live_contentops/main_analysis_handoff_consumer_v1.py` adds one read-only consumer seam:

- verifies packet identity and logical hashes before building V3;
- validates the frozen V2 compatibility projection, claims, evidence, exact citations, rights,
  freshness, event/revision/observation/known-at/PIT clocks, and candidate lineage;
- keeps one exact Core claim attributable to `MAIN_APP_CORE_ANALYZER`;
- keeps BrowserOS and X rows qualitative `PROXY_CONTEXT` and quarantines the unresolved
  contradiction;
- rejects tampering, stale/future-PIT, invalid rights, hash mismatch, proxy promotion, and
  authority-inconsistent input;
- preserves the supplied V2 projection and governed claim substance while composing the existing
  dual-lane newsroom/CORE shadow, editorial review, package fabric, eight derivative shadow rows,
  destination readback shadow, interruption resume, and immutable scheduled-shadow receipt.

The fixture is [main_analysis_handoff_bridge_v1.json](../../tests/fixtures/main_analysis_handoff_bridge_v1.json).
The consumer performs no scheduler/store/database/status write, model/provider call, browser
action, login/account selection, cookie/storage/token read, publication, dispatch, deployment, or
V2 activation.

## Representative round-trip receipt

- status: `SHADOW_REVIEW_READY`
- packet: `cc-evidence-75948bfa522107feff03`
- input packet logical hash: `c496bb5135106202a577d167a4879ab013ae695afa537e472bee14843b5139e8`
- frozen V2 projection hash: `cc11ac3ac550e877895d1de438ada7412bfa613445f846232d044b977ac7e140`
- built V3 packet hash: `1f035bfc04210f03aff096aa7149b2a2f9dd6ea5ba710fce19365cc947b95d42`
- claim-lineage hash: `19128174d081945b536492da98a22331ead9b71f64ad5debd48a7a0c806eefdc`
- immutable end-to-end receipt hash: `826b54643edabcefe03ace212b8e9da51920d70624fe90d340819296d1d726bb`
- exact Core claim: `core-claim-001`
- qualitative proxy/context claims: `proxy-browseros-001`, `proxy-x-001`
- quarantined unresolved contradiction claims: `proxy-browseros-001`, `proxy-x-001`
- newsroom lane: `SELECTED`
- editorial review: `PASS`
- scheduled shadow: `SHADOW_CONFIRMED`
- derivative destination shadow count: `8`
- interruption recovery: `RESUMABLE_WITHOUT_SEMANTIC_RERUN`

Remote readback at receipt generation: [PR #71](https://github.com/fatcat2109/capital-chronicle-contentops/pull/71)
was `OPEN/CLEAN`, with base `7711debc1f0f02e5c772dca1e644fd6ac09f928e`, exact head
`572c6b1625cd1859bc21b726ec77a4c4709986fc`, and exact-head CI run
[39035723869](https://github.com/fatcat2109/capital-chronicle-contentops/actions/runs/39035723869)
green for both `branch-codegraph-refresh` and `deterministic-validation`.

Zero-live receipt fields are all closed: scheduler started `false`, durable-store writes `0`,
database mutation `false`, model/provider calls `0`, browser actions `0`, public write `false`,
publication authority `false`, and V2 activation `false`.

## Reused and changed

- Reused: `capital_chronicle_content_evidence_packet.v3`, frozen V2 validation, `cc_evidence_bridge_v2`,
  `dual_lane_core_v0_shadow_newsroom_v1`, `editorial_review_orchestrator_v2`, canonical package
  builder, destination registry, and `scheduled_shadow_production_day_v1`.
- Changed: one consumer adapter, one self-contained mixed fixture, and focused accept/reject/
  authority/lineage regressions. No second bridge, newsroom, scheduler, store, publisher, or
  authority ledger was added.

## Verification

Focused owner and consumer set: `73 passed`:

```powershell
python -m pytest -q tests/test_main_analysis_handoff_consumer_v1.py tests/test_dual_lane_core_v0_shadow_newsroom_v1.py tests/test_scheduled_shadow_production_day_v1.py tests/test_v1_simple_gemini_scheduler_browseros_dry_run_v1.py
```

Also passed: Ruff, `py_compile` for the changed Python files, and `git diff --check`.

The broader legacy evidence/freshness selection set on unchanged fresh master retains nine
pre-existing failures for old runtime-receipt/source-capability expectations; those failures are
outside this slice and no existing owner files were changed.

## Closed cells and blockers

- Closed: Main packet identity/hash, frozen V2 compatibility, claim/evidence/citation lineage,
  rights/freshness, PIT clocks, exact/proxy separation, duplicate/revision lineage, contradiction
  quarantine, authority non-upgrade, V3 construction, dual-lane/editorial/package/readback shadow,
  interruption recovery, eight derivative shadow rows, and immutable zero-live receipt.
- Blocker retained: current BrowserOS/account/destination host identity was not observed in this
  read-only fixture run; no live readiness or public object is claimed.

## Exactly one NEXT

Run one owner-authorized, read-only current-host observation at the Main handoff BrowserOS/X context
boundary; stop immediately on identity ambiguity, stale evidence, or `UNKNOWN_WRITE`.
