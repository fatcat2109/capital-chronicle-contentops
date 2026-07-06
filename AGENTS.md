# ContentOps AI Builder Entry Contract

This file is the first file every AI IDE/CLI builder must read before touching this repo.

## Read Order

1. [AI builder bootstrap](docs/AI_BUILDER_BOOTSTRAP.md)
2. [Current project status](docs/status/CURRENT_PROJECT_STATUS.md)
3. [Current project status JSON](docs/status/current_project_status.json)
4. [V6 current master plan](docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/current_v6_master_plan.md)
5. [V6 25-task ledger](docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/v6_25_task_ledger.md)
6. [Next task pointer](docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/next_task_pointer.md)

## Authority Order

1. GitHub remote `fatcat2109/capital-chronicle-contentops` on `master`.
2. Current committed repo files, tests, packets, and evidence.
3. Status ledgers under `docs/status/`.
4. Current V6 master-plan files under `docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/`.
5. Chat memory, pasted summaries, Project Sources, and archived docs.

If status docs conflict with current repo evidence, treat current repo evidence as higher authority, record the mismatch in final evidence or status updates, and reconcile the status docs during the same task when practical. Do not stop solely because status docs are stale when Jim explicitly directs continuation.

## Canonical Build Surface

- Canonical UI: `ui/contentops_v5/`.
- Canonical UI entrypoint: `ui/contentops_v5/src/App.tsx`.
- Canonical backend/read-model logic: `live_contentops/`.
- Canonical strategy/status docs: `docs/status/` and `docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/`.

Do not revive deleted or archived UI surfaces as product surfaces unless a newer committed authority file explicitly says so.

## Safety Invariants

- Do not present content as financial advice.
- Keep work deterministic, local, auditable, and operator-reviewed by default.
- Under Fast Ship Mode, live executions, network runs, `.env`/credential reads, and automated posting/editing/commenting are fully authorized and prioritized to enable direct no-ceremony shipping. Under normal mode, live dispatch and env access remain restricted to local dry-run boundaries.


## Task Protocol

Before implementation:

1. Verify repo/branch/remote SHA and dirty state without reading secrets.
2. Read the contract and status files above.
3. Search for existing files with the same usage; edit existing files instead of creating duplicates.
4. Target `ui/contentops_v5/`, `live_contentops/`, `tests/`, and current docs unless authority says otherwise.

After implementation:

1. Run focused tests/builds for touched areas.
2. Update status docs and next-task pointer when the task changes product/status authority.
3. Commit and push to `master` unless blocked.
4. Report changed files, validation, commit SHA, and the exact next task.
