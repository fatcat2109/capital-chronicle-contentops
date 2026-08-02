# Capital Chronicle ContentOps — Builder Guardrails and Repository Authority V1

## 0. Purpose

This contract exists because the repository contains multiple generations of plans, runners, schedulers, approval contracts, dashboards and evidence packets. A builder that searches by filename alone can easily revive a superseded path or create another parallel implementation.

The objective is not to constrain useful engineering. It is to prevent architectural fragmentation, false maturity claims, authority escalation and unsafe public-write behavior while enabling heavy bounded implementation.

## 1. Mandatory read order

Before any post-v1 full-automation task, read:

1. `AGENTS.md`
2. `docs/CURRENT_CONTEXT.md`
3. `docs/AI_BUILDER_BOOTSTRAP.md`
4. `docs/status/CURRENT_PROJECT_STATUS.md`
5. `docs/status/current_project_status.json`
6. `docs/automation/CONTENTOPS_FULL_AUTOMATION_FINAL_PRODUCT_INSTITUTIONAL_NORTH_STAR_V1/README.md`
7. `docs/automation/CONTENTOPS_FULL_AUTOMATION_FINAL_PRODUCT_INSTITUTIONAL_NORTH_STAR_V1/FULL_AUTOMATION_INSTITUTIONAL_NORTH_STAR.md`
8. `docs/automation/CONTENTOPS_FULL_AUTOMATION_FINAL_PRODUCT_INSTITUTIONAL_NORTH_STAR_V1/FINAL_PRODUCT_HARDENING_EXECUTION_PLAN.md`
9. `docs/automation/CONTENTOPS_FULL_AUTOMATION_FINAL_PRODUCT_INSTITUTIONAL_NORTH_STAR_V1/OPERATIONAL_SLO_AND_ACCEPTANCE_STANDARD.md`
10. `docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/current_v6_master_plan.md`
11. `docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/next_task_pointer.md`
12. Exact task-specific code, tests and evidence.

Historical and archived files are not current authority unless a current file links them for a specific evidence purpose.

## 2. Authority order

1. GitHub remote commit, branch, tag and exact fetched bytes.
2. Current code, tests, schemas and committed evidence.
3. Current status and master-plan files.
4. Durable operational state and exact evidence export for the run under review.
5. Provider/platform strict readback.
6. Worker logs and local evidence.
7. Project Sources, pasted summaries and chat memory.

If a worker packet conflicts with GitHub, trust GitHub and record the conflict.

## 3. Protected historical truth

Do not modify, move, recreate or retag:

- annotated tag `v1.0`;
- release commit `6983bfb3ef300414b744f3f8f97ca81ff699348b`;
- accepted Treasury public outputs;
- accepted v1.0 release evidence;
- historical live-run evidence used by this audit.

Do not mutate the Capital Chronicle ingestion repository from a ContentOps task.

A new task may add a superseding record, but it may not rewrite historical evidence to make an earlier run appear cleaner.

## 4. Canonical product roots

- Canonical backend: `live_contentops/`
- Canonical UI: `ui/contentops_v5/`
- Canonical production migration anchor: `live_contentops.eight_platform_substack_first_pipeline_v1`
- Canonical current plans: `docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/`
- Post-v1 institutional authority: `docs/automation/CONTENTOPS_FULL_AUTOMATION_FINAL_PRODUCT_INSTITUTIONAL_NORTH_STAR_V1/`
- Current status: `docs/status/`

Do not revive V4, stale dashboards, archive copies or old project-source bundles as canonical product surfaces.

## 5. One-of-each architecture rule

The final product permits exactly one authoritative implementation of each:

- production orchestrator;
- durable operational store;
- state-transition engine;
- approval envelope;
- outbox;
- scheduler/supervisor;
- platform adapter interface;
- provider/model gateway;
- current status stack;
- canonical UI.

A builder must first search for the existing authoritative implementation and extend or explicitly supersede it. Creating `*_v2`, `*_new`, `*_final`, `*_production`, or another standalone dashboard because the current module is difficult is prohibited unless the task explicitly authorizes a migration and deprecation plan.

## 6. Current paths requiring quarantine or delegation

Until the relevant hardening wave completes, do not treat these as independent production authority:

- `live_contentops/live_production_pipeline_runner_v6.py`
- `live_contentops/server.py`
- `live_contentops/scheduler_v6.py`
- `live_contentops/cli.py` scheduler live flags
- old local approval/outbox template stacks
- archived runners or dashboards

The task must either delegate them through the canonical production interface or hard-block live behavior. Do not add features to them as parallel production systems.

## 7. State-machine discipline

Every implementation task must name:

- input state;
- output state;
- transition reason;
- actor;
- exact artifacts/hashes consumed;
- durable transaction boundary;
- retry or reconciliation class;
- authority granted or explicitly not granted.

No state change may be inferred from a filename, process exit code or dashboard text alone.

Do not use shared `latest_*.json` files as mutable production coordination authority.

## 8. Approval discipline

Prohibited as publication authority:

- `approved=true`;
- CLI flag alone;
- operator name without exact hashes;
- historical approval reused for changed bytes;
- review UI state not committed to the durable decision model;
- task prompt saying “operator approved” without an exact approval envelope.

A valid approval binds exact evidence, article, visual, variant, destination, policy and freshness state. Any bound change expires approval.

## 9. Live-task boundary

A task may access credentials, providers, browser/CDP or platforms only when the exact task explicitly authorizes the operation.

Every live-capable prompt must state:

- repository and branch;
- exact starting HEAD;
- authorized platform set;
- authorized account/destination set by nonsecret binding ID;
- authorized operation set;
- approved work item/approval envelope;
- allowed credential-handle presence checks;
- retry/reconciliation rules;
- public-write count expectation;
- stop conditions;
- evidence required.

Never read or print raw environment values, tokens, webhook URLs, authorization headers, cookies, browser storage, private keys or session secrets.

## 10. No mock/live confusion

A mock, dry-run, synthetic, fixture, template or fallback result must never be classified as live success.

Required explicit fields:

- `execution_mode`;
- `provider_action_performed`;
- `public_write_performed`;
- `public_object_id`;
- `readback_class`;
- `strict_readback_pass`;
- `operator_acceptance`.

An unsupported live action blocks. It does not return a generated success ID.

## 11. Retry and unknown-write discipline

- Never retry an unknown write blindly.
- Never collapse provider acknowledgement, public identity and strict readback into one boolean.
- Never delete/recreate without exact object identity and operator/repair policy.
- Never restart an entire release when an exact partial chain can be resumed.
- Never let a generic retry counter override platform-specific error classification.
- Never mark a circuit-broken platform healthy because another platform succeeded.

## 12. Data and evidence discipline

ContentOps consumes governed Capital Chronicle outputs. It does not become a parallel numeric database.

- Numeric truth requires approved claim IDs.
- Headline sidecars are catalyst context, not market or macro truth.
- External search is context/visual discovery, not authority.
- Missing values remain missing.
- Point-in-time evidence must be known at the decision cutoff.
- DQR is independent and cannot be cleared by LLM output, SourceHealth or operator convenience.
- Story-scoped publication authority may permit an exact story while global DQR remains blocked.

## 13. Model discipline

- Use the model provider registry.
- Do not hardcode model IDs inside topic/story branches.
- Do not silently fall back to a weaker model for a high-reasoning role.
- Do not suppress failed attempts after later success.
- Do not treat deterministic recovery as normal model quality.
- Do not ask a model to decide permission, DQR, approval or dispatch authority.
- Do not reveal hidden reasoning or persist provider secrets.
- Every prompt/output must bind to version and hash.

## 14. UI discipline

The UI is a control and review plane over durable truth.

- It does not invoke platform adapters directly.
- It does not optimistically report public success.
- It writes operator decisions, not arbitrary live commands.
- It must expose current versus historical versus superseded state.
- It must show unknown-write, incident and reconciliation status prominently.
- It must preserve evidence detail through drilldown.
- It must not hide blockers to reduce cognitive load.
- Browser QA is required when visible UI behavior changes.

## 15. Heavy bounded task design

Prefer one coherent implementation wave over micro-tasks when work shares:

- the same state-machine boundary;
- the same live/no-live risk class;
- the same schemas;
- the same test and rollback surface.

Split only at real boundaries listed in the execution plan.

Each task should allow Antigravity/Codex to:

1. read authority;
2. inspect existing implementation;
3. design the bounded change;
4. implement;
5. self-debug;
6. run focused and relevant broader tests;
7. update status/ledger/pointer;
8. commit and push;
9. provide evidence.

Do not prescribe tiny line-by-line edits that prevent the builder from fixing adjacent defects within the same boundary.

## 16. Required task prompt fields

Every implementation prompt must contain:

```text
Task label
Repository
Branch
Required starting HEAD
Execution/risk mode
Goal
Current authority docs
Exact in-scope roots
Protected roots
Required state transitions
Safety/authority invariant
Required implementation outcomes
Negative cases
Validation and tests
UI/browser QA requirement
Commit message
Push/parity requirement
Terminal classifications
Exact next action/evidence
```

## 17. Validation rules

Minimum for code tasks:

- focused tests for touched behavior;
- compatibility tests for adjacent canonical path;
- compile/type/build checks;
- deterministic replay where relevant;
- mutation/negative tests for authority boundaries;
- `git diff --check`;
- scoped no-secret scan;
- protected path/tag verification;
- exact branch/remote parity.

Run the broader suite when practical and relevant. If it is not run, state that. Never fabricate CI PASS.

For scheduler/outbox/state work, additionally test:

- concurrency;
- restart;
- stale lease;
- duplicate tick;
- unknown write;
- malformed durable state;
- clock/timezone behavior;
- approval expiry;
- kill switch.

## 18. Evidence packet standard

Every completed task reports:

- task label and terminal classification;
- repository, branch, starting and final HEAD;
- commit messages;
- changed files;
- design decisions;
- state transitions added/changed;
- tests and exact counts;
- tests not run;
- runtime/provider/browser/platform actions performed;
- public-write count;
- credential-read class, never values;
- protected baseline verification;
- blockers/caveats;
- exact next action;
- final manifest with hashes.

A worker self-claimed PASS remains awaiting ChatGPT/GitHub audit until repo evidence is verified.

## 19. Documentation update discipline

After every maturity-changing task, update once:

- `docs/status/CURRENT_PROJECT_STATUS.md`
- `docs/status/current_project_status.json`
- `docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/current_v6_master_plan.md`
- post-v1 maturity ledger;
- `next_task_pointer.md`

Do not append contradictory current sections indefinitely. Preserve historical summaries but maintain one unmistakable current classification and next action.

Do not fabricate a completing commit SHA inside the commit that creates it. Use starting/precommit SHA roles and report final SHA after commit.

## 20. Stop and blocker rules

Stop with an exact blocker when:

- required upstream artifact is unreachable;
- exact starting HEAD differs and introduces conflicting changes;
- schema migration cannot preserve current state;
- live authorization/envelope is missing;
- required account/destination binding is unverified;
- unknown write cannot be reconciled;
- public object identity is ambiguous;
- raw secret handling would be required;
- provider/platform operation exceeds task scope;
- protected v1.0 baseline would be mutated.

Do not stop merely because a planned platform is unavailable. Record a platform-specific block, continue safe independent destinations if release semantics allow it, and preserve operator decision authority.

## 21. Anti-drift checklist

Before commit, answer `yes` to all:

- Did I extend the canonical architecture rather than create a parallel one?
- Are historical v1.0 and upstream repositories unchanged?
- Is every new authority derived, not self-declared?
- Are dry-run, public write and strict readback distinct?
- Is approval exact and hash-bound?
- Is unknown-write retry impossible?
- Are mutable coordination records durable and transactionally owned?
- Are model/provider choices registry-driven?
- Are UI claims derived from current durable truth?
- Are tests honest and scoped?
- Are unrun checks disclosed?
- Is the exact next task unambiguous?
