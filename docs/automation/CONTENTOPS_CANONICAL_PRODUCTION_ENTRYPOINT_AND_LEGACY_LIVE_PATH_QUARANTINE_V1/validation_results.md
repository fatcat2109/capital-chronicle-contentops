# Wave 01 Test and Validation Results

## Enforcement correction focused suite

```text
python -m pytest -q tests/test_canonical_production_entrypoint_and_legacy_quarantine_v1.py
..................................                                       [100%]
34 passed in 0.60s
```

This suite behaviorally proves direct API delegation, all 10 live-capable CLI argument families, exact private operation mapping, unknown-operation rejection before private import, no public-wrapper targets or recursion, and preservation of all accepted legacy/server/scheduler/CLI/UI/browser-profile quarantines.

## Canonical API/CLI compatibility suites

```text
python -m pytest -q tests/test_eight_platform_substack_first_pipeline_v1.py tests/test_generic_evidence_freshness_visual_editorial_fabric_v2.py
.................................................................        [100%]
65 passed in 1.05s
```

These tests run against the private implementation fixture seam where implementation behavior is under test, while public boundary behavior remains covered by the focused suite.

## Unchanged 13-file Wave 01 regression matrix

```text
python -m pytest -q tests/test_canonical_production_entrypoint_and_legacy_quarantine_v1.py tests/test_live_production_pipeline_runner.py tests/test_fast_one_cycle_automation_v0.py tests/test_full_pipeline_north_star_debug_and_live_run_v0.py tests/test_operator_approved_supervised_live_daily_run_v0.py tests/test_substack_first_north_star_pipeline_loop_v1.py tests/test_terra_ultra_north_star_full_automation_v1.py tests/test_scheduler_v6.py tests/test_publishing_profile_registry_v1.py tests/test_cli.py tests/test_cli_contracts.py tests/test_cli_dispatch.py tests/test_pipeline_rehearsal_evidence_v6.py
........................................................................ [ 69%]
................................                                         [100%]
104 passed in 5.08s
```

The same 13 selected files used for original Wave 01 validation now pass with the expanded enforcement suite. Across this matrix plus the two compatibility files, 169 unique tests passed. The focused file is intentionally rerun and is not double-counted in that unique total.

## Canonical V5 production build

```text
npm run build
> contentops-v5@0.0.0 build
> tsc -b && vite build
✓ 117 modules transformed.
✓ built in 2.67s
```

Vite emitted its pre-existing informational warning that the main minified JavaScript chunk exceeds 500 kB. The production build passed.

## Structural and authority validation

- Executable registry export: **PASS**
- Registry rows: **15** — **1 CANONICAL**, **1 DELEGATE**, **13 QUARANTINED**
- Exact orchestrator/private-dispatch operation map: **12 operations, exact-set PASS**
- Live-capable canonical CLI families: **10, delegated-once PASS**
- Public façade import safety before private/provider/browser/adapter import: **PASS**
- Unknown operation failure before private implementation import: **PASS**
- Direct private implementation script entry: **FAIL-CLOSED**
- Changed JSON, Markdown paths, AST/call graph, and `git diff --check`: revalidated during final precommit closeout
- Tests and build were local and fail-closed: **PASS**

## Scope not run

- The monolithic repository-wide Python suite was not run; no full-suite PASS is claimed.
- Browser QA was not run.
- No live/provider/platform integration suite was run because it would cross the forbidden boundary.
- No CI PASS is claimed before push; post-push status/check truth is recorded separately.
