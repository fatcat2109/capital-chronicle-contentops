# Current Context — Capital Chronicle ContentOps

> [!IMPORTANT]
> Start here. Historical plans, old north stars, pre-alpha packets, and archived task evidence are not current execution authority.

## Current authority

1. [AI builder bootstrap](AI_BUILDER_BOOTSTRAP.md)
2. [Final automation readiness report](CONTENTOPS_FINAL_AUTOMATION_PIPELINE_READINESS_REPORT.md)
3. [V6 final product master plan](Capital%20Chronicle%20ContentOps%20V6%20%E2%80%94%20AI-Native%20Editorial,%20Publishing,%20and%20Community%20Operating%20System%20Master%20Plan.md)
4. [V6 25-task execution plan](Capital%20Chronicle%20ContentOps%20V6%20%E2%80%94%20Final%20Product%2025-Task%20Execution%20Plan.md)
5. [Next task pointer](automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/next_task_pointer.md)
6. [Current project status](status/CURRENT_PROJECT_STATUS.md)

## Current code roots

- `live_contentops/` — Python runtime/core automation logic
- `tests/` — Python verification
- `ui/contentops_v5/` — current product UI
- `schemas/` — data contracts

## Current next task

`TASK_CONTENTOPS_V6_APPROVAL_DECISION_TO_LOCAL_OUTBOX_READINESS_RECONCILIATION_V0`

## Cleanup closure

Deep cleaning pass 1/2/3 is complete for current execution. Use [cleanup_phase_closed_2026-07-03.md](cleanup_phase_closed_2026-07-03.md) for the compact closure record. Archives are rollback/reference only.

## Archive policy

Historical docs and old evidence moved under `docs/archive/_repo_cleanup_2026-07-03/` are reference-only. Do not use them as current context unless a current authority doc links them explicitly.

## Safety rules

- Do not read `.env` values.
- Do not read cookies, storage, tokens, headers, or browser session data.
- Do not dispatch, schedule, retry, comment, DM, react, or scrape without an exact approved live task.
