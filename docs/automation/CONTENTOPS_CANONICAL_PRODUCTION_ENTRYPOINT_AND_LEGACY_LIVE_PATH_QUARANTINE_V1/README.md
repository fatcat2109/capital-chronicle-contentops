# Wave 01 — Canonical Production Entrypoint and Legacy Live-Path Quarantine

## Acceptance classification

`PASS_WAVE01_CANONICAL_ORCHESTRATOR_BOUNDARY_ACCEPTED_AND_MERGED`

Historical correction classification:

`PASS_WAVE01_CANONICAL_ORCHESTRATOR_ENFORCEMENT_CORRECTION_AWAITING_INDEPENDENT_AUDIT`

Wave 01 worker classification:

`PASS_CANONICAL_PRODUCTION_ENTRYPOINT_AND_LEGACY_LIVE_PATH_QUARANTINE_V1_AWAITING_INDEPENDENT_AUDIT`

An independent audit accepted the executable Wave 01 boundary for merge into `master`. The post-merge acceptance commit reconciled minor test/evidence coverage to exhaustively cover all 12 mutation-capable CLI argument families including `--closure-historical-repair` and `--finalize-v1-tag`.

## Executable correction

```text
public compatibility API or canonical module/script CLI
  -> ContentOpsProductionOrchestrator.execute(operation, **kwargs)
  -> live_contentops._eight_platform_substack_first_pipeline_impl_v1._dispatch_canonical_operation
  -> exactly one existing private implementation body
```

The orchestrator validates one of 12 exact operations before importing the private implementation module. Unknown operations fail before that import. The public compatibility façade imports no provider, browser, or adapter implementation and delegates every live-capable API and all 12 mutation-capable CLI families through the orchestrator exactly once. The private implementation module rejects direct script execution.

## Authority

- Repository: `fatcat2109/capital-chronicle-contentops`
- Target branch: `master`
- Accepted source branch: `agent/contentops-wave01-canonical-entrypoint-v1`
- Target HEAD: `a0c9d0a67e39c614d5a80cd758f219dcac9b11ff`
- Source HEAD: `7d7d55039a68b4dbaec631ac75af6b7e418f7500`
- Canonical public authority: `live_contentops.production_orchestrator_v1.ContentOpsProductionOrchestrator`
- Public compatibility façade: `live_contentops.eight_platform_substack_first_pipeline_v1`
- Private dispatcher: `live_contentops._eight_platform_substack_first_pipeline_impl_v1._dispatch_canonical_operation`

## Evidence summary

- Registry: **15 rows** — **1 CANONICAL**, **1 DELEGATE**, **13 QUARANTINED**
- Exact canonical operation allowlist: **12**
- Live-capable canonical CLI argument families covered: **12**
- Focused enforcement suite: **38 passed in 0.60s**
- Canonical API/CLI compatibility suites: **65 passed in 1.05s**
- Unchanged 13-file Wave 01 regression matrix: **108 passed in 5.08s**
- Unique tests across the compatibility and broader matrices: **169**
- Canonical V5 production build: **PASS**, 117 modules, 2.67s
- Monolithic repository-wide Python suite: **not run; no full-suite PASS claimed**
- Browser QA: **not run**
- Precommit CI: **no CI PASS claimed**

No environment/credential value, provider, network source, browser/CDP session, platform adapter, scheduler/retry, approval/outbox, dispatch, publication, edit, comment, reply, reaction, DM, or public-write path was executed.

## Exact next task

`TASK_CONTENTOPS_DURABLE_OPERATIONAL_STORE_AND_CANONICAL_STATE_MACHINE_V1` remains `NEXT_NOT_STARTED`. This correction grants no Wave 02 or live authority.
