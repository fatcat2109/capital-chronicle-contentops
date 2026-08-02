# Wave 01 Test and Validation Results

## Fresh focused suite

```text
python -m pytest -q tests/test_canonical_production_entrypoint_and_legacy_quarantine_v1.py
.....................                                                    [100%]
21 passed in 1.11s
```

This suite proves the one-canonical-row invariant, lazy canonical binding, registry coverage, runner/server/scheduler/CLI/UI/browser-profile quarantine, pre-I/O/pre-import failure, unsupported-platform live-success prohibition, and AST/import/route bypass guards.

## Fresh relevant broader matrix

```text
python -m pytest -q tests/test_canonical_production_entrypoint_and_legacy_quarantine_v1.py tests/test_live_production_pipeline_runner.py tests/test_fast_one_cycle_automation_v0.py tests/test_full_pipeline_north_star_debug_and_live_run_v0.py tests/test_operator_approved_supervised_live_daily_run_v0.py tests/test_substack_first_north_star_pipeline_loop_v1.py tests/test_terra_ultra_north_star_full_automation_v1.py tests/test_scheduler_v6.py tests/test_publishing_profile_registry_v1.py tests/test_cli.py tests/test_cli_contracts.py tests/test_cli_dispatch.py tests/test_pipeline_rehearsal_evidence_v6.py
........................................................................ [ 79%]
...................                                                      [100%]
91 passed in 22.00s
```

The 13 selected suites cover every touched runtime family plus existing scheduler, CLI, publishing-profile, and rehearsal compatibility contracts.

## Fresh canonical V5 production build

```text
npm run build
> contentops-v5@0.0.0 build
> tsc -b && vite build
✓ 117 modules transformed.
✓ built in 8.44s
```

Vite emitted its pre-existing informational warning that the main minified JavaScript chunk is larger than 500 kB. The build completed successfully.

## Structural and authority validation

- Executable registry export: **PASS**
- Registry rows: **15** total; **1 CANONICAL**, **1 DELEGATE**, **13 QUARANTINED**
- Rows with `canonical=true`: **1**
- Duplicate entrypoint IDs: **0**
- Changed JSON parsing: validated again in final precommit closeout
- Changed Markdown/repository paths: validated again in final precommit closeout
- `git diff --check`: validated again in final precommit closeout
- Tests/validations were local and fail-closed: **PASS**

## Scope not run

- The monolithic repository-wide Python suite was not run; no full-suite PASS is claimed.
- Browser QA was not run.
- No live/provider/platform integration suite was run because it would cross the task's forbidden boundary.
- No CI PASS is claimed in this precommit evidence; post-push GitHub status/check truth is recorded separately during closeout.
