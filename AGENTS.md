# ContentOps AI Builder Entry Contract

This file is the first file every AI IDE/CLI builder must read before touching this repo.

## Read Order

1. [AI builder bootstrap](docs/AI_BUILDER_BOOTSTRAP.md)
2. [Current project status](docs/status/CURRENT_PROJECT_STATUS.md)
3. [Current project status JSON](docs/status/current_project_status.json)
4. [V6 current master plan](docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/current_v6_master_plan.md)
5. [V6 25-task ledger](docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/v6_25_task_ledger.md)
6. [Next task pointer](docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/next_task_pointer.md)
7. [Platform delivery contract](docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/platform_delivery_contract_v1.json)
8. [Edge publishing runbook](docs/automation/OPERATOR_BROWSER_LAB_AND_SOCIAL_CREDENTIAL_SETUP/operator_browser_lab_runbook.md)
9. [Generic evidence/freshness/visual/editorial contract](docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/generic_evidence_freshness_visual_editorial_fabric_v2.md)
10. [RC operator audit findings](docs/automation/EIGHT_PLATFORM_FULL_PIPELINE_V1/contentops_v1_0_rc_20260711_1/operator_manual_audit_findings_v2.json)
11. [Mandatory genericity and domain-generalization standard](docs/architecture/CONTENTOPS_GENERICITY_AND_DOMAIN_GENERALIZATION_STANDARD_V1.md)

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
- Canonical live runner: `live_contentops.eight_platform_substack_first_pipeline_v1`.
- Canonical generic local mode: the same runner with `--prepare-generic-fabric`; topic-specific oil/Fed builders are legacy adapters, not the generalized architecture.
- Canonical browser profile: Microsoft Edge at `A:\Capital Chronicle\operator-browser-profiles\contentops-social-main`.

Do not revive deleted or archived UI surfaces as product surfaces unless a newer committed authority file explicitly says so.

## Safety Invariants

- Do not present content as financial advice.
- Keep work deterministic, local, auditable, and operator-reviewed by default.
- Under Fast Ship Mode, live executions, network runs, `.env`/credential reads, and automated posting/editing/commenting are fully authorized and prioritized to enable direct no-ceremony shipping. Under normal mode, live dispatch and env access remain restricted to local dry-run boundaries.
- Fast Ship authorizes only the minimum redacted capability checks needed for execution. It never authorizes printing, logging, persisting, or committing raw environment values, credentials, tokens, provider keys, webhook URLs, cookies, authorization headers, localStorage, sessionStorage, or browser-session secrets.
- Allowed credential diagnostics: environment-variable names, presence booleans, redacted capability status, and non-secret account/scope readiness.
- The current generic live evidence is at `docs/automation/DATABASE_PUBLICATION_AUTHORITY_AND_CONTENTOPS_FULL_LIVE_CLOSURE_V1/contentops_database_publication_live_20260714_1/`. Story-scoped `contentops_publication` authority permitted this Treasury story while global DQR correctly remained blocked. Substack plus all eight configured derivatives passed strict readback; TikTok remains outside this run and blocked by canonical-profile authentication.
- Never bypass global DQR. Publication is allowed only when an exact story-scoped packet independently grants `reporting_allowed=true`, `PASS_PUBLICATION_AUTHORIZED`, fresh source authority, and public claim permissions.
- Annotated tag `v1.0` exists at immutable release commit `6983bfb3ef300414b744f3f8f97ca81ff699348b`; the release is operator accepted. The reusable backend foundation now separates portable exact-Git transport receipts from registered schema-aware semantic extraction, byte-derived evidence refs, internal point-in-time timestamps, and derived-or-unavailable feature values; the current next action is the independent audit named in `next_task_pointer.md`.


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
