# Capital Chronicle ContentOps — Final Product Hardening Execution Plan V1

## 0. Program decision

This program replaces feature-count completion with operational-maturity completion.

The accepted v1.0 release remains frozen historical proof. The program does not reopen that release. It hardens the reusable ContentOps system until it can continuously process fresh governed candidates, produce reviewable content, accept one exact operator decision, dispatch applicable Tier-1 platform variants, reconcile outcomes, survive restart, and generate governed learning proposals.

The program uses **heavy bounded implementation waves**. Builders must not split same-lane work into one task per module or platform unless a real risk boundary requires it.

Real split boundaries are:

- durable-state/schema migration;
- credential or browser-profile access;
- public-write authorization;
- scheduler or retry activation;
- platform provider/API/browser action;
- upstream database authority changes;
- live metrics/community readers;
- video/TikTok production mode.

## 1. Program acceptance hierarchy

A wave can be classified:

- `PASS_IMPLEMENTED_LOCAL_NO_WRITE`
- `PASS_SHADOW_OPERATION`
- `PASS_SUPERVISED_LIVE_COHORT_STAGE_N`
- `BLOCKED_EXACT_ARTIFACT_OR_OPERATOR_INPUT_MISSING`
- `FAIL_REGRESSION_OR_AUTHORITY_BREACH`

Do not use `PASS_FULL_AUTOMATION` until every final acceptance condition in the North Star and SLO standard is met.

No task may claim CI PASS when GitHub has no CI status.

## 2. Protected baseline

Protected and immutable unless an exact repair task authorizes otherwise:

- annotated tag `v1.0`;
- release commit `6983bfb3ef300414b744f3f8f97ca81ff699348b`;
- accepted Treasury public objects and identities;
- accepted release evidence directory;
- prior historical live-run evidence;
- Capital Chronicle ingestion repository;
- raw credentials, browser session material and operator-owned profile files.

Canonical current surfaces:

- backend: `live_contentops/`;
- UI: `ui/contentops_v5/`;
- canonical production migration anchor: `live_contentops.eight_platform_substack_first_pipeline_v1`;
- current strategy/status: `docs/status/` and `docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/`;
- this packet: `docs/automation/CONTENTOPS_FULL_AUTOMATION_FINAL_PRODUCT_INSTITUTIONAL_NORTH_STAR_V1/`.

## 3. Program phases

```text
Phase A — Authority and live-path consolidation
Phase B — Durable operational spine
Phase C — Production orchestration and platform reliability
Phase D — Continuous editorial operation
Phase E — Observability, learning and operator product
Phase F — Shadow soak and supervised live cohorts
Phase G — Tier-2 media expansion after Tier-1 acceptance
```

## 4. Execution waves

### Wave 00 — Local closeout, authority reconciliation and branch acceptance

Task label:

`TASK_CONTENTOPS_FULL_AUTOMATION_PLAN_LOCAL_CLOSEOUT_AND_AUTHORITY_RECONCILIATION_V1`

Goal:

Pull the audit branch into an isolated local worktree, verify every changed document against current remote `master`, run repository-native documentation/JSON checks, complete missing inventory hashes, reconcile current authority entrypoints, and produce a clean reviewable branch without implementing runtime changes.

Required work:

- verify base and branch HEADs;
- inspect branch diff;
- validate all packet JSON and Markdown references;
- populate final manifest with actual branch HEAD and file hashes;
- update `AGENTS.md`, `docs/CURRENT_CONTEXT.md`, `docs/AI_BUILDER_BOOTSTRAP.md`, current V6 master plan, maturity ledger and next-task pointer;
- preserve `CURRENT_PROJECT_STATUS` historical accepted-release truth while adding current post-v1 hardening status;
- run secret/path scan;
- commit and push non-force;
- no merge to `master` without Jim review.

Validation:

- JSON parse and deterministic hash check;
- Markdown link/path existence check;
- `git diff --check`;
- protected release/tag unchanged;
- no runtime/source changes unless needed solely for a doc-validation utility;
- no CI claim if no CI exists.

Exit:

`PASS_FULL_AUTOMATION_PLAN_LOCAL_CLOSEOUT_AWAITING_OPERATOR_MERGE_REVIEW`

### Wave 01 — Canonical live-path inventory, delegation and quarantine

Task label:

`TASK_CONTENTOPS_CANONICAL_PRODUCTION_ENTRYPOINT_AND_LEGACY_LIVE_PATH_QUARANTINE_V1`

Risk class:

Local code, no credentials, no public write.

Goal:

Make one live-capable orchestrator authoritative and prevent any alternate runner, scheduler, HTTP endpoint, CLI command or UI action from invoking a platform adapter outside that orchestrator.

Required work:

1. Build an executable live-entrypoint registry that identifies every function/CLI/server/UI route capable of reaching a provider or browser action.
2. Define one stable `ContentOpsProductionOrchestrator` interface around the current canonical runner.
3. Convert `live_production_pipeline_runner_v6.py` into a compatibility/preparation wrapper or hard-block its live flags.
4. Change `server.py` to read-only health/status; remove or hard-block unauthenticated live launch.
5. Block `scheduler_v6.py` live dispatch and `cli.py scheduler tick --fast-ship` until the durable outbox is implemented.
6. Prohibit live-mode mock-success fallback.
7. Add AST/import/route tests proving no alternate path reaches platform adapter execution.
8. Preserve historical run replay and canonical v1.0 evidence.

Acceptance:

- one live entrypoint registry row has `canonical=true`;
- all other live-capable paths delegate through the canonical interface or fail closed before credentials/provider action;
- no unsupported platform can return live `SUCCESS`;
- targeted tests plus full relevant suite pass;
- no public write.

Exit:

`PASS_CANONICAL_PRODUCTION_ENTRYPOINT_AND_LEGACY_LIVE_PATH_QUARANTINE_V1`

### Wave 02 — Durable operational store and canonical state machine

Task label:

`TASK_CONTENTOPS_DURABLE_OPERATIONAL_STORE_AND_CANONICAL_STATE_MACHINE_V1`

Risk class:

Schema/local persistence boundary; no live action.

Goal:

Create the SQLite WAL operational spine and migrate in-progress coordination away from mutable JSON filenames and in-memory task maps.

Required work:

- versioned schema and migration runner;
- tables/entities defined in the North Star;
- append-only transition/event log;
- compare-and-set state transitions;
- immutable artifact hash references;
- writer lease, work-item lease and heartbeat tables;
- transactionally claimed scheduler/outbox work;
- migration rollback and backup policy;
- local path configuration without machine-specific hardcoding;
- redacted evidence export from store to committed packets;
- deterministic replay from events;
- crash/restart and concurrent-claim tests;
- data retention/compaction policy for high-volume telemetry.

Do not:

- commit the mutable SQLite database;
- store raw secrets or browser session material;
- use ORM magic that hides transaction semantics;
- silently discard malformed state.

Acceptance:

- two concurrent workers cannot claim the same item;
- stale leases recover deterministically;
- restart reconstructs in-flight state;
- every transition has exact reason/actor/hash bindings;
- failed migration leaves prior schema usable;
- no network/public write.

Exit:

`PASS_DURABLE_OPERATIONAL_STORE_AND_CANONICAL_STATE_MACHINE_V1`

### Wave 03 — Exact approval envelope and transactional outbox

Task label:

`TASK_CONTENTOPS_EXACT_APPROVAL_ENVELOPE_TRANSACTIONAL_OUTBOX_AND_EXPIRY_V1`

Risk class:

Approval authority model; local only.

Goal:

Unify current approval markers, local approval contracts, duplicate guard and outbox concepts into one exact immutable approval envelope and one transactionally claimed outbox.

Required work:

- approval envelope schema;
- exact canonical/evidence/visual/variant/destination/policy hash set;
- operator identity and decision;
- platform/operation allowlist;
- freshness and approval expiry;
- invalidation on any bound-artifact change;
- one outbox entry per platform operation;
- exact account/destination/parent/media binding;
- operation-level idempotency key;
- attempt and readback requirements;
- outbox state transitions in the durable store;
- adapter request must consume exact approved bytes;
- no post-approval rebuild;
- negative tests for partial/stale/mismatched approval;
- migration adapter for canonical historical approval evidence without granting new live authority.

Acceptance:

- a boolean `approved=true` cannot create an outbox entry;
- one-byte payload/media/policy change invalidates approval;
- stale freshness decision expires approval;
- outbox claim is atomic and idempotent;
- exact approved bytes are the only bytes available to dispatcher;
- no public write.

Exit:

`PASS_EXACT_APPROVAL_ENVELOPE_TRANSACTIONAL_OUTBOX_AND_EXPIRY_V1`

### Wave 04 — Supervisor, continuous windows and restart-safe scheduler

Task label:

`TASK_CONTENTOPS_RESTART_SAFE_SUPERVISOR_CONTINUOUS_WINDOWS_AND_SCHEDULER_V1`

Risk class:

Scheduler/retry infrastructure; shadow-only first.

Goal:

Implement one local supervisor that owns intake windows, durable queue processing, heartbeats, leases and bounded recovery.

Required work:

- Windows-compatible process launch/runbook;
- global writer lease;
- service heartbeat;
- timezone-aware five-window schedule;
- event-driven material-update wakeups;
- missed-window/catch-up policy;
- explicit no-op window records;
- scheduler tick identity and idempotency;
- durable claim/complete/failed/dead-letter states;
- platform concurrency and browser-profile single-owner controls;
- graceful shutdown and restart recovery;
- kill-switch behavior that blocks writes but permits readback/reconciliation;
- read-only local health endpoint;
- no CORS-wildcard public-write endpoint;
- fake clock, DST/timezone, reboot and concurrent supervisor tests.

Acceptance:

- seven simulated days and forced restarts produce no duplicate ticks or lost work;
- recurring windows remain recurring;
- malformed state blocks visibly rather than becoming an empty healthy queue;
- no raw credentials in scheduled records;
- shadow mode performs zero provider/platform writes.

Exit:

`PASS_RESTART_SAFE_SUPERVISOR_CONTINUOUS_WINDOWS_AND_SCHEDULER_SHADOW_V1`

### Wave 05 — Platform adapter conformance and recovery framework

Task label:

`TASK_CONTENTOPS_TIER1_ADAPTER_CONFORMANCE_UNKNOWN_WRITE_AND_RECOVERY_FRAMEWORK_V1`

Risk class:

Platform semantics; local fixtures and read-only probes first.

Goal:

Make every Tier-1 adapter implement the same attempt/readback/reconciliation contract while preserving platform-native behavior.

Required work:

- adapter interface from North Star;
- capability and account/destination preflight;
- exact request preparation;
- error-class registry;
- prewrite-safe retry classes;
- unknown-write classification;
- readback strength classification;
- exact known-object repair;
- thread/reply resume;
- targeted delete/edit policy;
- circuit breaker and cooldown;
- per-platform rate/concurrency configuration;
- redacted evidence output;
- no mock-success live fallback;
- conformance fixtures for all Tier-1 platforms;
- platform-specific tests for failures observed in historical runs.

Historical regression cases required:

- Substack draft saved but no public URL;
- failed image upload/file input;
- X missing permalink;
- LinkedIn historical activity reuse;
- Facebook wrong/awkward copy or wrong media;
- Instagram clickable-caption assumption;
- Threads missing parent/duplicate-text ambiguity/order repair;
- Telegram provider readback without browser DNS;
- YouTube Community wrong-surface avoidance.

Acceptance:

- every adapter passes common conformance tests;
- unknown write never retries automatically;
- known object can be read/repaired without duplicate create;
- partial thread resumes exact chain;
- unsupported action blocks before provider call;
- no public write in this wave.

Exit:

`PASS_TIER1_ADAPTER_CONFORMANCE_UNKNOWN_WRITE_AND_RECOVERY_FRAMEWORK_V1`

### Wave 06 — Model registry, 9router Gemini 3.1 Pro default and evaluation harness

Task label:

`TASK_CONTENTOPS_MODEL_REGISTRY_9ROUTER_GEMINI31PRO_AND_EDITORIAL_EVALUATION_HARNESS_V1`

Risk class:

Provider call and model quality; no publication.

Goal:

Make 9router with Gemini 3.1 Pro the explicit current economic default while preserving provider/model portability and measured future upgrade.

Required work:

- versioned provider/model/role registry;
- exact configured 9router model ID, no implicit Flash default;
- provider gateway shared by article, role review, platform adaptation and feedback summary;
- schema-constrained responses;
- prompt and model version hashes;
- attempt budget, timeout and fallback policy;
- alias/substitution detection where provider metadata permits;
- cost/latency/token/invalid-output telemetry;
- deterministic recovery provenance;
- historical-real-run editorial evaluation corpus;
- mutation and hallucination tests;
- side-by-side evaluation command for future models;
- promotion policy requiring operator-approved config commit.

Minimum evaluation corpus:

- accepted Treasury article and final variants;
- July 11 oil RC defects;
- policy decision;
- data release;
- corporate filing;
- physical event;
- regulatory/sanctions event;
- nonnumeric explainer;
- build-in-public product update;
- community Q&A.

Acceptance:

- exact 9router/Gemini 3.1 Pro registry row is the default for intended semantic roles;
- model swap requires no evidence/outbox/platform contract change;
- malformed/low-quality output fails closed or produces a clearly labelled recovery candidate;
- no model can set authority/permission/approval/publication fields;
- provider tests may call 9router but perform no platform/public write.

Exit:

`PASS_MODEL_REGISTRY_9ROUTER_GEMINI31PRO_AND_EDITORIAL_EVALUATION_HARNESS_V1`

### Wave 07 — Continuous governed intake and assignment integration

Task label:

`TASK_CONTENTOPS_CONTINUOUS_GOVERNED_INTAKE_ASSIGNMENT_AND_MATERIAL_DELTA_LOOP_V1`

Risk class:

Read-only upstream/database boundary; no public write.

Goal:

Connect durable intake windows to governed Capital Chronicle candidate/evidence artifacts and local catalyst sidecars without creating a parallel truth path.

Required work:

- cursor/checkpoint state per upstream artifact family;
- exact Git/database receipts;
- correction/revision/update-chain handling;
- stable story clustering;
- duplicate versus material update semantics;
- point-in-time known-at enforcement;
- candidate hard gates;
- inspectable ranking and preemption;
- concentration controls;
- explicit no-eligible-candidate outcome;
- assignment record persisted to durable state;
- event-driven re-evaluation on material update;
- source/candidate replay corpus across multiple families;
- no direct MT5/source fetch fallback inside ContentOps.

Acceptance:

- same checkpoint replay is deterministic;
- future-known evidence cannot enter earlier window;
- unchanged story does not re-enter;
- correction/material update behaves distinctly;
- no eligible story creates a no-op, not filler;
- no upstream mutation or public write.

Exit:

`PASS_CONTINUOUS_GOVERNED_INTAKE_ASSIGNMENT_AND_MATERIAL_DELTA_LOOP_SHADOW_V1`

### Wave 08 — Canonical editorial, visual and platform-package orchestration

Task label:

`TASK_CONTENTOPS_CANONICAL_EDITORIAL_VISUAL_AND_PLATFORM_PACKAGE_ORCHESTRATION_V1`

Risk class:

LLM/provider and media discovery; no publication.

Goal:

Run selected assignments through the complete canonical editorial process and produce exact operator-ready packages from one orchestrator.

Required work:

- explicit article-mode registry;
- evidence planner and claim-limited writer context;
- quantitative and methodology review;
- provider-neutral visual discovery;
- rights/provenance and diversity gates;
- canonical article and SEO package;
- platform-native variants for applicable Tier-1 surfaces;
- identity/persona rules;
- final-render audit;
- independent adversarial review;
- exact package/variant/media hashes;
- decision-time freshness re-evaluation;
- operator review diff against prior version;
- no parallel article/variant stack.

Acceptance corpus:

At least ten dry-run/shadow packages across five or more story types, including nonmarket and market-sensitive examples.

Acceptance:

- zero unsupported claim or numeric authority upgrade;
- correct platform visual applicability;
- no internal process language;
- exact citations/limitations/claims on all variants;
- operator package is decision-ready or truthfully blocked;
- no public write.

Exit:

`PASS_CANONICAL_EDITORIAL_VISUAL_AND_PLATFORM_PACKAGE_ORCHESTRATION_SHADOW_V1`

### Wave 09 — Operational UI over durable state

Task label:

`TASK_CONTENTOPS_V5_OPERATIONAL_CONTROL_PLANE_DURABLE_STATE_INTEGRATION_V1`

Risk class:

UI/local read-model; no public write.

Goal:

Make `ui/contentops_v5/` the truthful operational control plane over the durable store and canonical state machine.

Required work:

- read-only service/read model for supervisor and work-item state;
- candidate/assignment queue;
- evidence and exact package review;
- approval envelope decision capture;
- outbox and attempt timeline;
- platform readback/reconciliation matrix;
- incidents and circuit breakers;
- window/calendar history;
- model invocation diagnostics;
- metrics/community learning review;
- no direct adapter or provider call from UI;
- exact state/hash inspector;
- optimistic UI prohibited for public-write state;
- desktop/mobile browser QA.

Acceptance:

- UI state is derived from durable store and exact artifacts;
- a stale shared JSON file cannot override current truth;
- operator decision writes only a decision/envelope record;
- first fold exposes supervisor, current window, decision queue, incidents and last release health;
- no live dispatch in this wave.

Exit:

`PASS_V5_OPERATIONAL_CONTROL_PLANE_DURABLE_STATE_INTEGRATION_V1`

### Wave 10 — Observability, SLOs, incident and reconciliation center

Task label:

`TASK_CONTENTOPS_OPERATIONAL_OBSERVABILITY_SLO_INCIDENT_AND_RECONCILIATION_V1`

Risk class:

Operational evidence; no live write required.

Goal:

Implement correlated operational metrics, incident packets, health alerts, circuit breakers and SLO evaluation.

Required work:

- correlation IDs across work/run/approval/outbox/attempt/object;
- supervisor/window/queue/model/platform/readback metrics;
- unknown-write and reconciliation aging;
- error budget and SLO evaluator;
- incident lifecycle;
- redacted evidence snapshots;
- operator alert summaries through existing operator lane in dry-run first;
- platform health and session readiness;
- structured postmortem generator;
- no raw secret values.

Acceptance:

- injected failures produce the correct incident and breaker state;
- SLO report distinguishes insufficient sample from pass;
- all metrics bind to exact entities;
- restart preserves incident/reconciliation state;
- no public write.

Exit:

`PASS_OPERATIONAL_OBSERVABILITY_SLO_INCIDENT_AND_RECONCILIATION_V1`

### Wave 11 — Performance, community observation and governed learning activation

Task label:

`TASK_CONTENTOPS_PERFORMANCE_COMMUNITY_OBSERVATION_AND_GOVERNED_LEARNING_LOOP_V1`

Risk class:

Platform read scopes and metrics; separate explicit authorization required for live readers.

Goal:

Replace mock/manual-only learning with scoped observations while keeping the learning firewall.

Required work:

- exact content identity across canonical and platform objects;
- official metrics adapters where stable and justified;
- one-step operator-assisted metric capture where not;
- Discord/Telegram/Substack feedback intake using approved scoped readers or operator exports;
- privacy/redaction rules;
- normalized metric definitions and observation ages;
- cohort eligibility/minimum sample rules;
- content retrospective;
- next-idea and experiment proposals;
- operator approval for policy promotion;
- no automatic change to authority, evidence, approval or dispatch rules.

Acceptance:

- missing metric remains unavailable, not zero;
- metric binds to exact post and payload;
- low sample yields inconclusive result;
- learning proposal is inspectable and reversible;
- no autonomous engagement, DM, reply, comment or public write.

Exit:

`PASS_PERFORMANCE_COMMUNITY_OBSERVATION_AND_GOVERNED_LEARNING_LOOP_V1`

### Wave 12 — Seven-day continuous shadow soak and resilience drills

Task label:

`TASK_CONTENTOPS_SEVEN_DAY_CONTINUOUS_SHADOW_SOAK_AND_RESILIENCE_DRILLS_V1`

Risk class:

Continuous local operation; provider calls allowed, no platform writes.

Goal:

Operate the complete system continuously in shadow mode and prove restart, concurrency, degradation and recovery behavior.

Required drills:

- supervisor restart mid-assignment;
- restart after approval but before outbox claim;
- restart after request submission but before readback using simulated adapter;
- duplicate scheduler tick;
- two concurrent workers;
- 9router timeout/rate limit/malformed JSON;
- stale browser session and selector drift;
- one degraded platform with remaining destinations healthy;
- upstream no-candidate day;
- correction/material update;
- expired approval;
- kill switch during queue execution;
- corrupted local export packet with intact durable store;
- telemetry/incident recovery.

Acceptance:

- all scheduled windows recorded;
- no lost or duplicate work;
- zero public writes;
- zero unresolved simulated unknown writes;
- every restart reconstructs correct state;
- SLO sample and incident packet complete;
- operator UI matches durable truth.

Exit:

`PASS_SEVEN_DAY_CONTINUOUS_SHADOW_SOAK_AND_RESILIENCE_DRILLS_V1`

### Wave 13 — Supervised live cohort stage 1

Task label:

`TASK_CONTENTOPS_SUPERVISED_LIVE_COHORT_STAGE1_THREE_STORIES_V1`

Risk class:

Exact live/public-write authorization required.

Goal:

Prove the hardened production spine with three fresh, diverse, story-scoped authorized releases.

Cohort requirements:

- at least three story types;
- at least one market-sensitive story;
- at least one nonmarket story;
- all applicable Tier-1 destinations;
- exact operator approval per story;
- strict readback and final operator audit;
- at least one controlled degradation/recovery case if a natural failure does not occur, using a separately authorized non-destructive drill.

Acceptance:

- zero unapproved writes;
- zero unresolved duplicates or unknown writes;
- all applicable public objects bound to exact payload/media hashes;
- no material editorial/source/visual defect;
- restart and partial-platform recovery evidence;
- accepted SLO report, with sample-size caveat.

Exit:

`PASS_SUPERVISED_LIVE_COHORT_STAGE1_THREE_STORIES_V1`

### Wave 14 — Supervised live cohort stage 2 and final Tier-1 acceptance

Task label:

`TASK_CONTENTOPS_SUPERVISED_LIVE_COHORT_STAGE2_TEN_STORIES_AND_FINAL_TIER1_ACCEPTANCE_V1`

Risk class:

Exact live/public-write authorization required.

Goal:

Establish repeated generalized operation over a meaningful cohort.

Cohort requirements:

- at least ten fresh releases;
- at least five story types;
- multiple publication windows;
- applicable Tier-1 destination coverage;
- at least one correction/material update chain;
- at least one no-eligible-candidate window;
- at least one provider/model fallback case;
- at least one platform degradation/reconciliation case;
- performance/community observations for available objects.

Final acceptance:

- all North Star Tier-1 conditions pass;
- no unapproved public write;
- no unresolved duplicate or unknown write;
- no lost state across restart;
- SLOs meet thresholds or have an explicitly accepted, statistically honest exception;
- operator review finds no material quality defect;
- learning proposals remain governed;
- current docs/status/ledger identify the accepted production baseline.

Exit:

`PASS_CONTENTOPS_TIER1_CONTINUOUS_GENERALIZED_FULL_AUTOMATION_OPERATOR_ACCEPTED`

### Wave 15 — Tier-2 video/TikTok productization

Task label:

`TASK_CONTENTOPS_TIER2_VIDEO_TIKTOK_YOUTUBE_PRODUCTION_MODE_V1`

Dependency:

Wave 14 accepted.

Goal:

Build a separate media-production system for TikTok, YouTube long-form and YouTube Shorts without contaminating the text/image state machine.

Required work:

- script and scene plan;
- voice/narration and rights;
- visual timeline;
- thumbnail;
- render/transcode;
- account/surface capability;
- upload/idempotency/readback;
- media-specific quality and compliance;
- explicit operator approval;
- separate SLOs and cohort.

This wave is not required to accept Tier-1 full automation.

## 5. Recommended immediate sequence

The first Antigravity implementation sequence after plan closeout is:

```text
Wave 01 + Wave 02 as one heavy bounded architecture batch
→ Wave 03
→ Wave 04
→ Wave 05
→ Wave 06 + Wave 07 in parallel read-only worktrees only after interfaces stabilize
→ Wave 08
→ Wave 09 + Wave 10
→ Wave 11
→ Wave 12
→ explicit operator review before Waves 13–14
```

Wave 01 and Wave 02 should be combined only if Antigravity can preserve a clean migration boundary and produce a single coherent design. Do not combine public-write cohort work with architecture work.

## 6. Program control rules

After every wave:

- verify remote branch/commit/message/diff;
- update the post-v1 maturity ledger;
- update exact next-task pointer once;
- record tests and unrun tests honestly;
- record current live/public-write authority;
- record unresolved blockers with exact artifact or operator input;
- avoid self-referential final SHA claims inside the commit being created;
- preserve v1.0 and upstream state;
- no Project Sources refresh unless separately requested.

## 7. Completion forecast

The final Tier-1 product requires approximately:

- 1 local plan closeout task;
- 10–12 heavy local/shadow implementation waves;
- 1 seven-day shadow soak;
- 2 supervised live cohort stages.

This is intentionally fewer, larger waves than the prior micro-task style. The scope is substantial because the remaining work is operational integration and reliability, not missing UI cards or isolated contracts.
