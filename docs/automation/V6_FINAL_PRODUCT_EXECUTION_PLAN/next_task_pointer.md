# ContentOps V6/Post-v1 Next Task Pointer

Latest accepted historical release:

`TASK_CONTENTOPS_V1_0_FINAL_AUCTION_LOGIC_REPAIR_ACCEPTANCE_AND_TAG_V1`

Accepted release classification:

`PASS_CONTENTOPS_V1_0_OPERATOR_ACCEPTED`

Current post-v1 plan classification:

`PLAN_CANDIDATE_AWAITING_LOCAL_CLOSEOUT_AND_OPERATOR_MERGE_REVIEW`

Audit branch:

`agent/contentops-full-automation-final-product-audit-v1`

Audit base/master authority:

`a1645740b8ad3a590be314ecbc900f9ad0f4b252`

## Required next action

`TASK_CONTENTOPS_FULL_AUTOMATION_PLAN_LOCAL_CLOSEOUT_AND_AUTHORITY_RECONCILIATION_V1`

## Copy-paste Antigravity task

```text
TASK_CONTENTOPS_FULL_AUTOMATION_PLAN_LOCAL_CLOSEOUT_AND_AUTHORITY_RECONCILIATION_V1

Repository:
fatcat2109/capital-chronicle-contentops

Remote audit branch:
agent/contentops-full-automation-final-product-audit-v1

Required base authority:
master at a1645740b8ad3a590be314ecbc900f9ad0f4b252

Execution mode:
DOCS_AND_EVIDENCE_ONLY / ISOLATED LOCAL WORKTREE / NO RUNTIME IMPLEMENTATION / NO LIVE ACTION

Role:
Act as the local repo verifier and closeout builder. Do not redesign the operator decisions unless exact repository evidence contradicts them. Preserve the accepted v1.0 release and all historical evidence.

Goal:
Pull the remote audit branch into a new isolated local worktree, verify the repo-wide live-run audit and institutional full-automation North Star against exact local Git bytes, complete exhaustive tracked-file inventory and validation that the GitHub connector could not perform, reconcile current authority/status files, and push a clean closeout commit for Jim's diff review. Do not merge to master.

Mandatory read order:
1. AGENTS.md
2. docs/CURRENT_CONTEXT.md
3. docs/AI_BUILDER_BOOTSTRAP.md
4. docs/status/CURRENT_FULL_AUTOMATION_FINAL_PRODUCT_STATUS.md
5. docs/status/CURRENT_PROJECT_STATUS.md
6. docs/status/current_project_status.json
7. every file under docs/automation/CONTENTOPS_FULL_AUTOMATION_FINAL_PRODUCT_INSTITUTIONAL_NORTH_STAR_V1/
8. docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/current_v6_master_plan.md
9. docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/v6_supersession_map.md
10. docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/v6_25_task_ledger.md
11. docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/post_v1_full_automation_maturity_ledger.md
12. this next-task pointer

Required work:
A. Worktree and Git authority
- Fetch origin.
- Verify origin/master is exactly a1645740b8ad3a590be314ecbc900f9ad0f4b252 unless a newer Jim-authorized change exists; if it differs, record exact divergence and do not silently rebase.
- Create a clean local worktree on the remote audit branch.
- Verify the branch is a descendant of the required base.
- Verify v1.0 tag and release commit 6983bfb3ef300414b744f3f8f97ca81ff699348b are unchanged.

B. Exhaustive tracked-file inventory
- Use git ls-files and exact Git metadata to inventory every tracked path at the audit branch HEAD.
- Create:
  docs/automation/CONTENTOPS_FULL_AUTOMATION_FINAL_PRODUCT_INSTITUTIONAL_NORTH_STAR_V1/tracked_file_inventory.json
  docs/automation/CONTENTOPS_FULL_AUTOMATION_FINAL_PRODUCT_INSTITUTIONAL_NORTH_STAR_V1/audit_coverage_report.md
- Classify every tracked path into current authority, runtime, live adapter, model/provider, scheduler/supervisor, approval/outbox, UI, schema, test, current evidence, historical evidence/archive, binary media/screenshot, generated packet, or other.
- Record path, blob SHA-1, byte length, text/binary class and audit depth.
- Deep-read every current authority and every file that can reach provider, browser/CDP, scheduler, approval, outbox, retry, metrics/community reader or public-write behavior.
- For historical/archive/binary duplicates, verify hashes/references and document sampling/unique-evidence logic instead of pretending every duplicate image was semantically reviewed.
- Reconcile any material omission or contradiction in the existing audit docs.

C. Document and JSON validation
- Parse every new/modified JSON file.
- Validate all Markdown-relative paths and referenced repository paths.
- Check duplicate or contradictory current classifications/next-task pointers.
- Check schema/version/field consistency across README, North Star, execution plan, SLO standard, model strategy, builder guardrails, live-run inventory, maturity matrix and gap register.
- Fix factual/path/JSON/format defects only where evidence supports the change.
- Do not dilute the operator decisions to make the plan easier.

D. Current authority reconciliation
- Reconcile docs/status/CURRENT_PROJECT_STATUS.md and docs/status/current_project_status.json with the post-v1 plan candidate while preserving the accepted v1.0 and latest historical task truth.
- Make one unmistakable current post-v1 classification and one exact next task.
- Keep root historical V6 plans as historical design/release references; add a concise post-v1 pointer only if needed, without deleting provenance.
- Confirm AGENTS.md, CURRENT_CONTEXT.md, AI_BUILDER_BOOTSTRAP.md, current_v6_master_plan.md, v6_supersession_map.md, historical 25-task ledger, post-v1 maturity ledger and next-task pointer agree.

E. Final manifest
- Update docs/automation/CONTENTOPS_FULL_AUTOMATION_FINAL_PRODUCT_INSTITUTIONAL_NORTH_STAR_V1/final_manifest.json with:
  exact branch start/precommit HEAD roles;
  complete changed-file inventory;
  Git blob SHA-1, byte SHA-256 and byte length for every packet/current-authority file;
  JSON/link/path validation results;
  protected tag/release verification;
  tests/checks run and not run;
  no-live/no-provider/no-credential/no-public-write truth;
  exact next implementation task:
  TASK_CONTENTOPS_CANONICAL_PRODUCTION_ENTRYPOINT_AND_LEGACY_LIVE_PATH_QUARANTINE_V1
- Do not fabricate a self-referential completing commit SHA inside the commit. Report the final commit SHA after commit/push.

Required validation:
- repository-native JSON parsing for all changed/new JSON;
- Markdown/path/link validation;
- duplicate current-authority/next-task scan;
- git diff --check;
- git status before and after;
- scoped secret-value and local-machine-artifact scan;
- protected v1.0 tag/release/evidence verification;
- branch/base ancestry verification;
- no source/runtime tests are required unless a validation utility is changed; do not claim runtime or CI PASS;
- verify no GitHub Actions CI status exists before stating no CI claim.

Protected/forbidden:
- Do not modify live_contentops runtime behavior, tests, schemas or ui implementation except a minimal validation utility only if strictly necessary.
- Do not merge to master.
- Do not rebase away audit history without explicit operator instruction.
- Do not read raw env values, credentials, tokens, webhook URLs, cookies, browser storage, authorization headers or session secrets.
- Do not invoke 9router, Gemini, browser/CDP, platform APIs, webhooks, scheduler, retry, outbox execution, approval execution, metrics readers, community readers or public writes.
- Do not modify the ingestion repository.
- Do not move/delete/recreate/retag v1.0.

Commit:
docs(contentops): close institutional full automation plan audit

Push:
Non-force push to origin/agent/contentops-full-automation-final-product-audit-v1 and verify exact remote parity and clean worktree.

Terminal classifications:
PASS_FULL_AUTOMATION_PLAN_LOCAL_CLOSEOUT_AWAITING_OPERATOR_MERGE_REVIEW
BLOCKED_AUDIT_BRANCH_OR_BASE_AUTHORITY_DIVERGED
FAIL_FULL_AUTOMATION_PLAN_VALIDATION_OR_PROTECTED_BASELINE

Final evidence must report:
- repository/worktree/branch;
- exact start and final HEAD;
- commit message;
- all changed files;
- inventory counts by class and audit depth;
- validation commands/results;
- protected release/tag verification;
- remaining caveats;
- no CI PASS claim;
- exact next implementation task after Jim accepts/merges the docs.
```

## No current live authority

This task grants no provider, credential, browser, platform, scheduler, approval, dispatch or public-write authority.
