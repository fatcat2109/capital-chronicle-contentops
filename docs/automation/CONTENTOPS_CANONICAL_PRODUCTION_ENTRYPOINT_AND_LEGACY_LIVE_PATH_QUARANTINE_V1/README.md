# Wave 01 — Canonical Production Entrypoint and Legacy Live-Path Quarantine

## Correction classification

`PASS_WAVE01_CANONICAL_ORCHESTRATOR_ENFORCEMENT_CORRECTION_AWAITING_INDEPENDENT_AUDIT`

Wave 01 worker classification remains:

`PASS_CANONICAL_PRODUCTION_ENTRYPOINT_AND_LEGACY_LIVE_PATH_QUARANTINE_V1_AWAITING_INDEPENDENT_AUDIT`

An independent audit blocked merge of the original Wave 01 commit because the registry labeled the canonical module `DELEGATE` while its public Python APIs and module/script CLI could still invoke live-capable implementation bodies directly. This correction makes the registry claim executable and awaits independent re-audit; it does not claim that the audit has passed.

## Executable correction

```text
public compatibility API or canonical module/script CLI
  -> ContentOpsProductionOrchestrator.execute(operation, **kwargs)
  -> live_contentops._eight_platform_substack_first_pipeline_impl_v1._dispatch_canonical_operation
  -> exactly one existing private implementation body
```

The orchestrator validates one of 12 exact operations before importing the private implementation module. Unknown operations fail before that import. The public compatibility façade imports no provider, browser, or adapter implementation and delegates every live-capable API and all 10 live-capable CLI families through the orchestrator exactly once. The private implementation module rejects direct script execution.

## Authority

- Repository: `fatcat2109/capital-chronicle-contentops`
- Branch: `agent/contentops-wave01-canonical-entrypoint-v1`
- Correction task: `TASK_CONTENTOPS_WAVE01_CANONICAL_ORCHESTRATOR_ENFORCEMENT_CORRECTION_V1`
- Correction starting/precommit HEAD: `7300517ca3861c2962df06d443ad0c0916396f9f`
- Required master base: `a0c9d0a67e39c614d5a80cd758f219dcac9b11ff`
- Original Wave 01 task-start HEAD: `a0c9d0a67e39c614d5a80cd758f219dcac9b11ff`
- Canonical public authority: `live_contentops.production_orchestrator_v1.ContentOpsProductionOrchestrator`
- Public compatibility façade: `live_contentops.eight_platform_substack_first_pipeline_v1`
- Private dispatcher: `live_contentops._eight_platform_substack_first_pipeline_impl_v1._dispatch_canonical_operation`
- Authorized correction commit message: `fix(contentops): enforce single canonical orchestrator entrypoint`

## Evidence summary

- Registry: **15 rows** — **1 CANONICAL**, **1 DELEGATE**, **13 QUARANTINED**
- Exact canonical operation allowlist: **12**
- Live-capable canonical CLI argument families covered: **10**
- Focused enforcement suite: **34 passed in 0.60s**
- Canonical API/CLI compatibility suites: **65 passed in 1.05s**
- Unchanged 13-file Wave 01 regression matrix: **104 passed in 5.08s**
- Unique tests across the compatibility and broader matrices: **169**
- Canonical V5 production build: **PASS**, 117 modules, 2.67s
- Monolithic repository-wide Python suite: **not run; no full-suite PASS claimed**
- Browser QA: **not run**
- Precommit CI: **no CI PASS claimed**

No environment/credential value, provider, network source, browser/CDP session, platform adapter, scheduler/retry, approval/outbox, dispatch, publication, edit, comment, reply, reaction, DM, or public-write path was executed.

## Exact next task

`TASK_CONTENTOPS_DURABLE_OPERATIONAL_STORE_AND_CANONICAL_STATE_MACHINE_V1` remains `NEXT_NOT_STARTED`. This correction grants no Wave 02 or live authority.
