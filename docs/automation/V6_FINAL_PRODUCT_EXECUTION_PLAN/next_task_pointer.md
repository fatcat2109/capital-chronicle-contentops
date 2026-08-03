# ContentOps V6/Post-v1 Next Task Pointer

Latest accepted historical release:

`TASK_CONTENTOPS_V1_0_FINAL_AUCTION_LOGIC_REPAIR_ACCEPTANCE_AND_TAG_V1`

Accepted release classification:

`PASS_CONTENTOPS_V1_0_OPERATOR_ACCEPTED`

Current Wave 01 worker classification:

`PASS_CANONICAL_PRODUCTION_ENTRYPOINT_AND_LEGACY_LIVE_PATH_QUARANTINE_V1_AWAITING_INDEPENDENT_AUDIT`

Current correction classification:

`PASS_WAVE01_CANONICAL_ORCHESTRATOR_ENFORCEMENT_CORRECTION_AWAITING_INDEPENDENT_AUDIT`

Completed Wave 01 implementation task:

`TASK_CONTENTOPS_CANONICAL_PRODUCTION_ENTRYPOINT_AND_LEGACY_LIVE_PATH_QUARANTINE_V1`

Current correction task:

`TASK_CONTENTOPS_WAVE01_CANONICAL_ORCHESTRATOR_ENFORCEMENT_CORRECTION_V1`

Working branch:

`agent/contentops-wave01-canonical-entrypoint-v1`

Original Wave 01 task-start authority:

`a0c9d0a67e39c614d5a80cd758f219dcac9b11ff`

Correction starting/precommit authority:

`7300517ca3861c2962df06d443ad0c0916396f9f`

The prior independent audit blocked merge. The corrected executable direction is public compatibility API or canonical module/script CLI → `ContentOpsProductionOrchestrator.execute(...)` → private dispatcher → exactly one private implementation body. Correction PASS awaits independent re-audit.

## Required next action

`TASK_CONTENTOPS_DURABLE_OPERATIONAL_STORE_AND_CANONICAL_STATE_MACHINE_V1`

## Execution boundary

This is Wave 02 from the accepted institutional hardening plan. It remains `NEXT_NOT_STARTED` and is schema/local-persistence work to create the SQLite WAL operational spine, explicit versioned migrations, append-only transitions, compare-and-set state changes, immutable artifact references, leases/heartbeats, restart reconstruction, deterministic replay, and redacted evidence export. It grants no credential, provider, browser, platform, scheduler/outbox execution, dispatch, publication, network, or public-write authority.

## Required starting authority

- Wave 01 has worker classification `PASS_CANONICAL_PRODUCTION_ENTRYPOINT_AND_LEGACY_LIVE_PATH_QUARANTINE_V1_AWAITING_INDEPENDENT_AUDIT`; the correction has classification `PASS_WAVE01_CANONICAL_ORCHESTRATOR_ENFORCEMENT_CORRECTION_AWAITING_INDEPENDENT_AUDIT`. Both remain subject to independent GitHub/ChatGPT audit.
- Wave 02 is `NEXT_NOT_STARTED`; do not mark it started from this pointer alone.
- Read Wave 02 in `docs/automation/CONTENTOPS_FULL_AUTOMATION_FINAL_PRODUCT_INSTITUTIONAL_NORTH_STAR_V1/FINAL_PRODUCT_HARDENING_EXECUTION_PLAN.md` before implementation.
- Preserve `v1.0`, accepted release evidence, the canonical orchestrator boundary, and historical replay packets unchanged.
- Do not add a second runner, scheduler, state store, outbox, approval engine, provider gateway, or dashboard.
- Do not commit the mutable SQLite database, persist raw secrets/session material, hide transaction semantics, or silently discard malformed state.
