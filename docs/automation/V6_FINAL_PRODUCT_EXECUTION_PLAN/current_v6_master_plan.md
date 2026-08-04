# Capital Chronicle ContentOps — Current V6/Post-v1 Master Plan

Authority date: 2026-08-02

Historical accepted release:

`PASS_CONTENTOPS_V1_0_OPERATOR_ACCEPTED`

Post-v1 current classification:

`PASS_WAVE01_CANONICAL_ORCHESTRATOR_BOUNDARY_ACCEPTED_AND_MERGED`

Audit conclusion:

`PARTIAL_PASS_BOUNDED_NINE_SURFACE_RELEASE_PROVEN_CONTINUOUS_GENERALIZED_FACTORY_NOT_YET_PROVEN`

## 1. Authority

Detailed post-v1 authority is:

`docs/automation/CONTENTOPS_FULL_AUTOMATION_FINAL_PRODUCT_INSTITUTIONAL_NORTH_STAR_V1/`

Mandatory references:

- `FULL_AUTOMATION_INSTITUTIONAL_NORTH_STAR.md`
- `LIVE_RUN_RECONSTRUCTION_AND_RELIABILITY_AUDIT.md`
- `FINAL_PRODUCT_HARDENING_EXECUTION_PLAN.md`
- `OPERATIONAL_SLO_AND_ACCEPTANCE_STANDARD.md`
- `MODEL_PROVIDER_AND_EVALUATION_STRATEGY.md`
- `BUILDER_GUARDRAILS_AND_REPO_AUTHORITY.md`
- `live_run_inventory.json`
- `capability_maturity_matrix.json`
- `gap_register.json`

The root V6 master plan and original 25-task execution plan remain historical product-design and bounded-release references. They are not evidence that continuous generalized operation is complete.

## 2. Accepted historical release

ContentOps v1.0 remains immutable historical authority:

- release task: `TASK_CONTENTOPS_V1_0_FINAL_AUCTION_LOGIC_REPAIR_ACCEPTANCE_AND_TAG_V1`;
- release commit: `6983bfb3ef300414b744f3f8f97ca81ff699348b`;
- annotated tag: `v1.0`;
- canonical Substack article plus eight Tier-1 text/image derivatives;
- exact story-scoped `contentops_publication` authority;
- global DQR remained independently blocked;
- machine verification, strict public/provider readback and operator acceptance;
- bounded Substack repairs preserved derivative identities.

Do not rerun, edit, delete, recreate, move or retag accepted v1.0 outputs/evidence.

The accepted release proves that the canonical path can complete one evidence-authorized, nine-surface text/image release. It does not prove a continuously operating content factory.

## 3. Product definition

Capital Chronicle ContentOps is an AI-native, evidence-governed editorial, publishing, distribution and community-learning operating system for serious macro, financial, regulatory, geopolitical, corporate and physical-event content.

The final operating loop is:

```text
continuous governed intake
→ deterministic eligibility and material-delta handling
→ capability-driven assignment
→ exact evidence and claim packet
→ AI-native article/visual/platform production
→ deterministic plus independent adversarial review
→ exact operator decision package
→ immutable approval envelope
→ durable transactional outbox
→ supervised Tier-1 platform dispatch
→ strict readback and reconciliation
→ performance/community observations
→ governed learning proposals and next-story backlog
→ next intake window
```

Automation completes all safe labor before approval. Jim remains final public-write authority. Manual action is recovery or exceptional operator assist, not the target workflow.

## 4. Current verified maturity

### Proven

- exact Git and database evidence consumption;
- claim-level permissions and DQR independence;
- point-in-time/freshness/visual/editorial gates;
- canonical Substack-first publication;
- one accepted Tier-1 nine-surface release;
- strict readback and bounded known-object repairs;
- fail-closed no-story database preflight;
- recent capability/readiness and historical-integrity hardening;
- strong read-only V5 package review.

### Not yet proven

- one durable unified production state machine;
- one exact approval/outbox implementation shared by every path;
- restart-safe recurring supervisor and scheduler;
- universal adapter/unknown-write/reconciliation contract;
- continuous fresh candidate intake;
- repeated generalized live cohort;
- rolling service SLOs and incident recovery;
- automated performance/community observation and calibrated learning;
- TikTok/YouTube video production.

## 5. Live-run audit conclusion

Historical runs show a progression:

1. Telegram-only partial live proof.
2. Substack draft/media/publication blocks.
3. Multi-platform attempts requiring recovery.
4. July 11 broad transport proof with material product-quality defects.
5. Targeted public repair and correct withholding of an unauthorized canary.
6. July 14 fail-closed no-story database run.
7. July 14 operator-accepted bounded Treasury release.

Transport success, strict readback and operator product acceptance are separate evidence classes. A task name or process exit code is not a release.

## 6. Canonical architecture decision

### 6.1 One production orchestrator

Migration anchor:

`live_contentops.eight_platform_substack_first_pipeline_v1`

The final product permits exactly one live-capable production orchestrator. Alternate live paths must delegate or be quarantined:

- `live_contentops/live_production_pipeline_runner_v6.py`
- `live_contentops/server.py`
- `live_contentops/scheduler_v6.py`
- scheduler live flags in `live_contentops/cli.py`
- older local-only approval/outbox/template stacks

No UI, server, scheduler or CLI path may call a platform adapter outside the canonical state machine.

### 6.2 Durable local state

Use one local SQLite database in WAL mode for mutable operational coordination. Git remains authority for code, contracts, plans and frozen evidence; SQLite owns in-flight work.

Required durable entities include:

- windows and work items;
- candidates and story versions;
- assignments and evidence packets;
- editorial/visual/platform artifacts;
- model invocations and review results;
- operator decisions and approval envelopes;
- outbox entries and attempts;
- platform objects and readback receipts;
- reconciliation cases and incidents;
- metrics, feedback and learning proposals;
- scheduler ticks, leases and heartbeats.

Mutable JSON files, shared `latest_*.json` packets and in-memory task maps are not the production message bus.

### 6.3 Canonical state machine

```text
DISCOVERED
→ EVIDENCE_PENDING
→ EVIDENCE_READY | EVIDENCE_BLOCKED
→ ASSIGNMENT_CANDIDATE
→ ASSIGNED | DEFERRED | DUPLICATE | REJECTED
→ PRODUCTION_IN_PROGRESS
→ REVIEW_BLOCKED | REVIEW_READY
→ OPERATOR_PENDING
→ APPROVED_EXACT | HELD | REJECTED | EXPIRED
→ OUTBOX_READY
→ DISPATCHING
→ PARTIAL_SUCCESS | UNKNOWN_WRITE | DISPATCH_BLOCKED | DISPATCH_COMPLETE
→ RECONCILING
→ COMPLETE | DEAD_LETTER | OPERATOR_RECOVERY_REQUIRED
→ OBSERVATION_PENDING
→ LEARNING_REVIEW_READY
→ CLOSED
```

Every transition binds exact actor, reason, artifact hashes, policy/model versions and timestamp. Any content change after `APPROVED_EXACT` creates a new version and invalidates approval.

## 7. Continuous operation

The supervisor must:

- run explicit Asia/Europe/U.S. windows plus material-update wakeups;
- produce selected, no-eligible-candidate or explicit blocked outcomes;
- use durable tick IDs and leases;
- survive process/workstation restart;
- prevent concurrent duplicate claims;
- keep one canonical browser-profile owner;
- isolate degraded platforms with circuit breakers;
- allow readback/reconciliation while the public-write kill switch is active;
- expose read-only local health.

Current `scheduler_v6.py` is not production-safe and must be quarantined before live use. It uses boolean approval, generic retries, mutable JSON state, unsafe recurrence semantics and live mock-success fallback.

## 8. Evidence and database boundary

ContentOps consumes governed Capital Chronicle outputs. It does not create a parallel numeric database or direct MT5 truth path.

Numeric/source truth requires approved evidence claim IDs, exact timestamps, citations, authority and public-use permission. DQR cannot be overridden by LLM output, SourceHealth, InputStateManifest or operator convenience.

Story-scoped publication authority may permit one exact story while global DQR remains blocked. No eligible story is a valid no-op window; the system must not manufacture filler content.

The incomplete main-product analyzer does not prevent all ContentOps work. Official nonnumeric events, regulatory/corporate documents, physical events, product/build-in-public content, methodology and educational explainers may proceed when exact evidence/permission/freshness contracts allow them.

## 9. Editorial and visual system

The canonical eight logical roles remain:

1. assignment editor;
2. evidence planner;
3. reporter/writer;
4. quantitative editor;
5. visual editor;
6. copy editor;
7. platform editor;
8. independent adversarial final reviewer.

Article mode is explicit and capability-driven. No universal fallback to analysis is allowed.

Long-form visual policy normally requires three useful visuals and at least two meaningful evidence dimensions/modalities. Text-only surfaces may require zero visuals. Image/mixed-media modes cannot inherit text-only waivers.

Search rank is not image provenance or reuse permission. Every external asset requires source page, owner, context, date, rights state, dimensions and duplicate/manipulation checks. Generated charts/visuals require source-data and transformation metadata.

## 10. Model strategy

Current economic intent:

```text
provider: 9router
model class: Gemini 3.1 Pro
```

The exact provider model ID must be verified locally and stored in a versioned model registry. Current embedded implicit `vx/gemini-3.5-flash` default and separate `vx/gemini-3.1-pro-preview` attempt conflict with operator intent and must be reconciled.

All semantic calls use one provider gateway with:

- exact model/prompt versions;
- schema validation;
- bounded attempt/fallback policy;
- latency/cost/invalid-output telemetry;
- historical-real-run evaluation corpus;
- operator-approved model promotion.

Models may draft and critique. They never create evidence, numeric truth, permission, DQR clearance, approval or publication authority.

## 11. Approval, outbox and retry

A valid approval envelope binds:

- evidence packet;
- canonical article;
- visual bundle;
- exact platform variants;
- account/destination bindings;
- policy version;
- freshness deadline;
- platform/operation allowlist;
- operator identity and decision.

A boolean approval is invalid.

Each outbox entry represents one exact platform operation. Unknown writes never receive blind retry. Prewrite-safe transient failures may use bounded backoff. Known public objects use exact readback/repair. Thread/reply recovery resumes only from the verified parent/last confirmed child.

## 12. Platform tiers

### Tier 1 — Required text/image factory

- Substack;
- Telegram;
- Discord;
- X;
- LinkedIn;
- Facebook Page;
- Instagram Business;
- Threads;
- YouTube Community.

### Tier 2 — Separate media-production modes

- TikTok;
- YouTube long-form;
- YouTube Shorts.

Tier-2 completion is not required for Tier-1 acceptance.

## 13. Operator UI

Canonical UI remains `ui/contentops_v5/`.

It must become a control plane over durable truth, exposing:

- supervisor/window health;
- candidate/assignment queue;
- evidence and exact package review;
- approval envelope decision;
- outbox/attempt/readback timeline;
- platform incidents and reconciliation;
- calendar/window history;
- model diagnostics;
- performance/community learning proposals.

The UI writes decisions/work records. It does not call platform adapters directly or optimistically report public success.

## 14. Learning and monetization

Metrics and feedback bind to exact public objects. Missing values remain unavailable, never zero. Official APIs are preferred where stable/justified; otherwise use one-step operator-assisted capture.

Learning may recommend topic mix, format, headline, timing, visual format, platform applicability and conversion strategy. It may not alter claim truth, authority, DQR, permission, citation, approval or dispatch rules.

The business flywheel is:

```text
high-trust canonical research
→ native Tier-1 distribution
→ qualified newsletter/community audience
→ questions and objections
→ better backlog and differentiated research
→ paid newsletter/research/product conversion
```

Optimize for qualified audience, subscriber/community growth, operator efficiency and monetizable trust—not raw posting volume.

## 15. Execution program

Post-v1 waves:

| Wave | Scope | Status |
|---:|---|---|
| 00 | Local docs/evidence closeout and authority reconciliation | COMPLETE_ACCEPTED_AND_MERGED |
| 01 | Canonical entrypoint and legacy live-path quarantine | COMPLETE_ACCEPTED_AND_MERGED |
| 02 | Durable operational store/state machine | NEXT_NOT_STARTED |
| 03 | Exact approval envelope/transactional outbox | NOT_STARTED |
| 04 | Restart-safe supervisor/windows/scheduler | NOT_STARTED |
| 05 | Tier-1 adapter/unknown-write/recovery conformance | NOT_STARTED |
| 06 | 9router Gemini 3.1 Pro registry/evaluation | NOT_STARTED |
| 07 | Continuous governed intake/assignment/material delta | NOT_STARTED |
| 08 | Canonical editorial/visual/platform packages | NOT_STARTED |
| 09 | V5 operational control plane | NOT_STARTED |
| 10 | Observability/SLO/incidents/reconciliation | NOT_STARTED |
| 11 | Performance/community observation and learning | NOT_STARTED |
| 12 | Seven-day shadow soak/resilience drills | NOT_STARTED |
| 13 | Three-story supervised live cohort | LIVE_AUTH_REQUIRED |
| 14 | Ten-story/five-type final Tier-1 cohort | LIVE_AUTH_REQUIRED |
| 15 | Tier-2 video/TikTok | DEFERRED_UNTIL_TIER1_ACCEPTED |

Detailed requirements are in `FINAL_PRODUCT_HARDENING_EXECUTION_PLAN.md`.

## 16. Final acceptance

Tier-1 is complete only after:

- one canonical live path;
- durable restart-safe state;
- exact approval/outbox;
- universal unknown-write protection;
- seven-day shadow soak;
- staged live cohorts totaling at least ten fresh releases/five story types;
- all applicable Tier-1 readbacks;
- zero unapproved writes, wrong destinations, unresolved duplicates, lost state or unresolved unknown writes;
- operator product-quality acceptance;
- governed metrics/community learning;
- SLO evidence with honest denominators.

Final label:

`PASS_CONTENTOPS_TIER1_CONTINUOUS_GENERALIZED_FULL_AUTOMATION_OPERATOR_ACCEPTED`

Do not use this label earlier.

## 17. Current next task

`TASK_CONTENTOPS_DURABLE_OPERATIONAL_STORE_AND_CANONICAL_STATE_MACHINE_V1`

Wave 01 is classified `PASS_WAVE01_CANONICAL_ORCHESTRATOR_BOUNDARY_ACCEPTED_AND_MERGED`. Wave 02 is the exact next task and has status `NEXT_NOT_STARTED`. It is a schema/local-persistence boundary for the SQLite WAL operational spine, versioned migrations, append-only events, compare-and-set transitions, leases, restart reconstruction, deterministic replay, and redacted evidence export. No credential, provider, browser/CDP, platform, scheduler/outbox execution, dispatch, publication, network, or public write is authorized.
