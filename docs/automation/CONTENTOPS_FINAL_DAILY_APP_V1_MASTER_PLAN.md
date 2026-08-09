# Capital Chronicle ContentOps — Final Daily App V1 Master Plan

Authority date: 2026-08-09

Authority ID:

`CONTENTOPS_FINAL_DAILY_APP_V1_MASTER_PLAN`

Status:

`OWNER_APPROVED_CURRENT_EXECUTION_PLAN`

Repository: `fatcat2109/capital-chronicle-contentops`

North Star:

`docs/automation/CONTENTOPS_FINAL_DAILY_APP_V1_NORTH_STAR.md`

This plan is the current Tier-1 execution authority. It supersedes conflicting sequencing in the Daily Live probation / parallel-V2 plan while preserving verified historical evidence, protected `v1.0`, one canonical production authority, exact browser/profile roles, all evidence and publication gates, and Capital Chronicle analytical/numeric authority.

The goal is not to restart the historical hardening program. The goal is to finish one sellable autonomous product.

## 0. Final product objective

Jim should be able to launch one ContentOps application, leave it running continuously, and rely on it to perform routine newsroom and distribution work without manually driving each cycle.

The final V1 product must:

1. stay alive 24/7 with low-cost supervision;
2. know when the next editorial decision is due;
3. wake early for a genuinely material event;
4. ingest current headline/event evidence;
5. cluster, rank, select, hold, reject, or abstain;
6. obtain exact story-dependent evidence;
7. produce grounded article, SEO, visuals, and native packages;
8. review and revise within bounded policy;
9. publish automatically to every currently READY configured Tier-1 destination when exact gates pass;
10. manage the public-object lifecycle through strict readback/reconciliation;
11. collect real performance/search/subscriber observations when safely available;
12. evaluate outcomes by story, package, platform, and publication window;
13. make bounded policy changes to timing, SEO, editorial packaging, and distribution;
14. survive restart without duplicate cycles or duplicate public objects;
15. expose the complete current state in the canonical V5 Daily App UI.

No-publication is valid. No mandatory post count exists.

## 1. Verified starting state

Remote `master` at the time this plan is authored is:

`7a04932a67df1af4c3dd10e9cc435dff140e23c8`

The repository already contains substantial accepted foundation. Reuse it.

### 1.1 Protected historical product proof

The annotated `v1.0` release and release commit `6983bfb3ef300414b744f3f8f97ca81ff699348b` remain immutable.

It proves one bounded public Treasury release with canonical Substack plus Tier-1 derivatives and strict readback. It does not prove a continuously operating autonomous Daily App.

### 1.2 Canonical production authority

Preserve:

- `live_contentops.production_orchestrator_v1.ContentOpsProductionOrchestrator`;
- `live_contentops._eight_platform_substack_first_pipeline_impl_v1`;
- `live_contentops.eight_platform_substack_first_pipeline_v1`;
- `live_contentops/durable_operational_store_v1.py`;
- `ui/contentops_v5/`.

No new parallel newsroom, production pipeline, durable store, approval authority, provider gateway, publisher, or analytics truth engine is authorized.

### 1.3 Newsroom state already proven

Current accepted code/evidence has demonstrated:

- rolling-X current intake;
- deterministic rolling-24h normalization/dedupe;
- hierarchical size-bounded leaf assignment;
- Flash-first semantic leaf clustering;
- compact quality-first global editor;
- strict exact-ID validation;
- checkpoint reuse and resume;
- semantic story-type routing;
- article-mode-aware evidence contracts for several launch story families;
- deterministic evidence-reachability editorial metadata;
- rank-by-rank evidence fallback;
- fail-closed `NO_PUBLICATION` outcomes;
- no unauthorized/unknown writes in recent Daily Live cycles.

### 1.4 Canonical article/media subsystem now exists

Commit `7a04932...` added:

`live_contentops/rolling_x_grounded_article_media_builder_v1.py`

and bound it as the default rolling-X article builder after evidence PASS.

Controlled zero-write evidence reports the downstream chain can reach article, source-backed media, semantic review, package generation, and destination readiness under controlled evidence.

However the fresh production canary remained evidence-blocked, so the complete real live path is not yet proven.

### 1.5 Known safety/correctness defects still open

Do not hide these behind probation:

1. the current decision fact card may derive displayed `entities_topics` from editorial framing / X-side context while claiming every field is copied from accepted evidence;
2. source-backed deterministic renders currently use a blanket `rights_status = capital_chronicle_owned`, which can overstate rights in underlying official source/excerpt content even when Capital Chronicle owns only the render/layout;
3. the Federal Reserve `official_policy` locator used a press-release index path that returned HTTP 404 during the fresh canary;
4. real production has not yet produced a fresh evidence-viable arbitrary rolling-X story through the new default article/media builder.

These are direct product blockers and belong in the first implementation slice.

### 1.6 Scheduling state

`daily_editorial_scheduler_v6.py` exists and provides useful deterministic candidate/schedule logic, but it is not the final always-on Daily App runtime and does not itself learn optimal engagement windows from real outcomes.

Do not build a second competing editorial scheduler. Evolve/reuse its policy responsibilities behind one Daily App supervisor.

### 1.7 Performance and learning state

Useful performance/learning contracts exist, including:

- `live_contentops/performance_learning_v1.py`;
- `live_contentops/content_intelligence_contracts_v2.py`;
- `live_contentops/adaptive_learning_core_v2.py`;
- `live_contentops/adaptive_learning_adapters_v2.py`;
- platform metrics schemas and historical/manual metrics lanes.

But the currently proven V1 performance loop is largely local/manual/replay oriented and explicitly does not perform production collection or automatic policy mutation.

The Final Daily App must turn those foundations into a real safe closed loop rather than create another learning architecture.

## 2. Product architecture

The product is one always-on supervisor over the existing canonical production boundary.

Conceptually:

```text
ContentOpsDailyAppSupervisor
    |
    |-- durable store / leases / heartbeat
    |-- operating mode / kill switch
    |-- EditorialWindowPolicy
    |-- current headline freshness / material trigger state
    |-- due public-object readback / reconciliation
    |-- due metrics observations
    |-- learning-policy evaluation
    |
    +--> when editorial work is due:
          ContentOpsProductionOrchestrator
              -> canonical rolling-X newsroom cycle
              -> canonical article/media builder
              -> existing reviewer/reviser
              -> native packages
              -> existing destination readiness/publisher
              -> strict readback/reconciliation
```

The supervisor coordinates. The canonical orchestrator remains production authority.

### 2.1 One due-window identity

Every scheduled editorial decision must have a deterministic identity such as:

```text
policy_version
+ intended_window_start
+ intended_window_end
+ timezone/session context
+ trigger_kind
→ editorial_window_id
```

A duplicate tick, crash/restart, or process race must reconstruct the same identity and must not execute the same window twice unless the prior attempt is explicitly resumable and the canonical state machine permits it.

### 2.2 One published-content identity

Preserve story/article/platform identity through performance learning.

Minimum linkage:

```text
story_cluster_id
article_version_id
visual_bundle_id
platform_variant_id
platform_id
destination_binding
publication_window_id
experiment_id / policy_version
public_object_id/url hash
```

Without this, timing/SEO/packaging learning is not trustworthy.

## 3. Work Package FDA-A — Publishability safety closure

Status:

`CURRENT / REQUIRED BEFORE FINAL APP LIVE ACCEPTANCE`

This is not broad hardening. It fixes defects discovered in the exact canonical builder/source path.

### 3.1 Media factual provenance

Change source-backed media construction so every displayed factual field comes from accepted evidence bytes/fields or an exact separately governed authority packet.

Editorial framing, X-derived entities/topics, selection rationale, SEO intent, and leaf summaries remain editorial metadata. They may not be relabeled as accepted evidence facts.

If a fact card needs entities, use only evidence-bound entity fields. If no such governed field exists, omit the entity field or choose a different source-backed primitive.

### 3.2 Media rights provenance

Separate:

- Capital Chronicle ownership of the newly rendered layout/card/image bytes;
- rights/provenance status of the underlying source data/text/excerpt.

Do not claim Capital Chronicle owns Federal Reserve/SEC/Federal Register or other source material.

Prefer explicit fields if the existing media contract supports them, for example:

- `render_rights_status`;
- `underlying_source_rights_status`;
- `source_reuse_basis`.

If the existing contract has only one `rights_status`, use the most conservative truthful state compatible with current policy and validator, and do not render an excerpt when reuse rights are unresolved.

Metadata-only source cards using facts such as publisher/title/date/source link are preferable to unsupported excerpt reuse.

### 3.3 Federal Reserve official-policy locator

Fix only the bounded first-party Federal Reserve/FOMC route justified by the current policy-decision profile.

The locator must:

- use official Federal Reserve public endpoints/pages;
- derive the relevant year/current archive deterministically from the editorial/evaluation cutoff where appropriate;
- never invent a URL;
- validate host/path/content before returning a candidate;
- remain discovery-only;
- require a subsequent official evidence GET before capabilities pass;
- keep request budget, timeout, actual retrieval time, evaluation cutoff, source publication time, hashes, and exact story/headline binding.

Do not turn this into generic web search or broad central-bank ingestion.

### 3.4 Exit criteria

FDA-A exits when focused controlled tests prove:

- no framing/X data is mislabeled as evidence fact;
- rights status no longer overclaims source-content ownership;
- source-backed asset lineage is exact;
- Federal Reserve locator resolves a controlled/current official policy listing or fails closed for a valid deterministic reason;
- unsupported sources/rights still fail closed;
- existing evidence/article/review/publication gates remain unchanged.

## 4. Work Package FDA-B — Always-on Daily App runtime vertical slice

Status:

`CURRENT FIRST MAJOR PRODUCT BUILD`

This is the first user-visible final-app capability.

### 4.1 Supervisor

Implement one canonical Daily App supervisor/controller.

Preferred shape:

- a backend module under `live_contentops/`;
- a CLI/product entry that starts the supervisor;
- all actual newsroom/publication operations routed through `ContentOpsProductionOrchestrator`;
- state stored in the existing durable operational store;
- no new database;
- no new publisher;
- no duplicated newsroom logic.

### 4.2 Responsibilities per supervisor tick

Each tick should cheaply determine:

1. current operating mode / kill switch;
2. durable leases and interrupted work needing recovery;
3. current headline/sidecar freshness;
4. whether a scheduled editorial window is due;
5. whether a material-event trigger is due;
6. whether any known/unknown public write requires readback/reconciliation;
7. whether any performance observation is due;
8. whether a learning-policy evaluation is due;
9. next wake time.

If nothing is due, sleep without calling an LLM.

### 4.3 Bootstrap EditorialWindowPolicy

Do not pretend current optimal times are known.

Create a versioned policy initialized from existing deterministic/configured cadence.

Minimum fields:

- policy ID/version;
- effective time;
- timezone/session context;
- core decision windows;
- optional platform preferred windows/delays;
- minimum spacing;
- material-event override rules;
- freshness constraints;
- confidence/sample state;
- provenance of the policy recommendation.

Policy storage should be durable, versioned, and rollback-safe.

### 4.4 Material-event trigger

Reuse the current headline/update-chain/materiality system.

Do not create another event-classification architecture.

The trigger may request a newsroom cycle only when deterministic new-event/update metadata crosses the configured threshold and the exact cycle identity has not already been processed.

### 4.5 Restart behavior

Prove:

- restart while idle;
- restart immediately before due window;
- restart after cycle claimed but before completion;
- duplicate supervisor tick;
- two processes competing for the same due window.

The existing lease/fencing/state machine should ensure one logical execution.

### 4.6 Kill switch

`KILL_SWITCH` prevents new public writes while allowing:

- intake;
- safe article/package production if product policy permits;
- readback;
- reconciliation;
- metrics observation;
- recovery.

The supervisor must observe kill-switch state before dispatch.

### 4.7 First vertical-slice demo

Run a bounded local supervisor session that demonstrates:

- process starts;
- policy loaded;
- a due window is recognized once;
- canonical newsroom cycle invoked exactly once;
- no duplicate invocation after a duplicate tick/restart;
- final state persisted;
- next wake computed;
- no public write unless exact canonical `AUTONOMOUS_DEFAULT` gates independently pass.

A legitimate `NO_PUBLICATION` cycle is acceptable for this runtime proof.

## 5. Work Package FDA-C — Autonomous multi-platform publication and post management

Start after the always-on supervisor is stable enough to drive one canonical cycle.

### 5.1 Dynamic destination set

At publication time resolve the current canonical destination registry.

Only exact:

- `READY_AUTHENTICATED`;
- `READY_NON_BROWSER_BINDING`

may receive writes.

Do not require all historical surfaces to be READY at once.

### 5.2 Tier-1 destinations

Target configured current support for:

- Substack;
- Telegram;
- Discord;
- X;
- LinkedIn;
- Facebook Page;
- Instagram Business;
- Threads;
- YouTube Community.

Use the canonical platform-native packages already produced by the content factory.

### 5.3 Publication windows

A selected story has a canonical content decision time. Platform-specific distribution may happen immediately or at a bounded preferred time if doing so does not violate story freshness/materiality or user value.

Breaking/material stories generally should not wait for a historically higher-engagement slot if waiting makes the story stale.

### 5.4 Idempotency and lifecycle

Every platform write uses the existing exact payload identity/idempotency/reconciliation controls.

Known success is never duplicated because a process restarted.

Unknown write remains stop/reconcile before retry.

### 5.5 Post-management scope

V1 post management includes:

- public object identity;
- publication/readback status;
- edit/repair only through existing authorized bounded mechanisms;
- reconciliation;
- performance-observation schedule;
- incident state.

Do not expand V1 into unrelated social engagement automation such as unsolicited DMs or general reaction farming.

## 6. Work Package FDA-D — Real performance observation

This is the key transition from historical manual metrics to the autonomous product.

### 6.1 Reuse contracts

Reuse existing performance identities, snapshots, schemas, and adaptive-learning contracts where compatible.

Do not create another analytics model because old performance code was manual-only.

### 6.2 Collection authority

For each configured destination, use the safest existing supported source:

1. canonical platform API/non-browser binding when already configured and authorized;
2. canonical Edge publishing/readback profile for read-only platform metrics where the current adapter can safely obtain them;
3. first-party analytics/Search Console integration when an existing nonsecret binding is available;
4. otherwise mark metric unavailable.

Never request/print/export raw secrets, tokens, cookies, storage, or session databases.

### 6.3 Observation scheduler

Each public object receives a bounded observation schedule.

Exact intervals are policy/configuration, not universal truth. The implementation may use early, same-day, next-day, and longer-tail checkpoints, but it must avoid wasteful high-frequency polling.

Observation identity includes:

- content/public object identity;
- platform;
- observed metric;
- observation due time;
- observed time;
- source/collection method;
- source response hash where safe;
- known limitations.

### 6.4 Platform-native metrics

Store native definitions.

Never compare raw likes/impressions across platforms as if they are equivalent.

Normalize only through explicit formulas and confidence rules in the learning layer.

### 6.5 Search / subscriber observation

SEO learning needs observed search performance, not only deterministic audit scores.

Where a safe configured integration exists, collect Search Console / first-party analytics metrics such as:

- search impressions;
- clicks;
- CTR;
- query cluster;
- average position;
- landing engagement;
- return readership;
- subscriber conversion.

If an integration is absent, surface it as an unavailable learning channel rather than blocking all Daily App operation.

## 7. Work Package FDA-E — Bounded closed-loop learning

The learning system consumes actual performance observations and production cost/quality telemetry.

### 7.1 Learning unit

Minimum useful cohort dimensions:

- platform;
- publication window;
- story type;
- article mode;
- topic/domain;
- headline/framing family;
- SEO intent;
- content depth/length bucket;
- visual/package type;
- policy version.

Avoid sparse overfitting by backing off to broader cohorts when sample size is small.

### 7.2 Objective

Reward qualified engagement:

- meaningful reads/completion;
- shares/saves;
- qualified replies;
- canonical article clicks;
- subscriber conversion;
- search demand/longevity;
- repeat readership;
- low revision/defect rate;
- reasonable cost per accepted package.

Penalize:

- clickbait;
- repeated topics/entities;
- concentration;
- weak evidence;
- overclaim;
- low-delta updates;
- outrage optimization;
- expensive low-value production;
- repeated editorial/review defects.

### 7.3 Allowed automatic policy updates

The engine may propose/apply bounded updates to:

- core editorial windows;
- destination publication windows/delays;
- story-priority weights;
- concentration penalties;
- headline/framing preferences;
- SEO intent/keyword cluster/structure/refresh policy;
- article depth/mode preference where evidence supports it;
- platform-native package strategy;
- visual/package preference.

### 7.4 Forbidden learning effects

Learning may not modify:

- source authority;
- evidence facts;
- factual/numeric claims;
- Capital Chronicle analysis;
- evidence capability requirements;
- publication permission;
- destination/account identity;
- secret/credential handling;
- unknown-write reconciliation rules;
- protected release truth.

### 7.5 Confidence gate

Use:

- minimum sample threshold;
- confidence class;
- bounded step size;
- policy diff;
- effective timestamp;
- rollback link;
- holdout/exploration policy where useful.

One viral or failed post must not rewrite the whole system.

### 7.6 No-op is valid

If evidence is insufficient or conflicting, record:

`NO_POLICY_CHANGE_INSUFFICIENT_EVIDENCE`

This is a correct learning outcome.

## 8. Work Package FDA-F — Final V5 Daily App UI

Do not rebuild UI before the runtime has produced the actual states it needs to show.

Canonical UI remains `ui/contentops_v5/`.

The final application should prioritize operator utility rather than ceremony.

### 8.1 Today

Show:

- operating mode / kill switch;
- controller health;
- next wake / next editorial window;
- latest headline universe freshness;
- current cycle state;
- selected story or abstention;
- evidence status;
- article/review/package status;
- cost/runtime;
- immediate incident state.

### 8.2 Queue

Show:

- scheduled windows;
- material-event triggers;
- held/awaiting-evidence stories;
- publication jobs waiting for platform-preferred windows;
- due readbacks;
- due performance observations.

### 8.3 Published

Show:

- canonical article;
- platform variants;
- destination/public object IDs;
- strict readback state;
- reconciliation state;
- edit/repair lineage;
- observation schedule.

### 8.4 Performance

Show platform-native metrics and trend lines with explicit definitions/limitations.

Do not create fake cross-platform equivalence.

### 8.5 Learning

Show:

- current policy version;
- timing recommendations;
- SEO/content/package recommendations;
- confidence/sample size;
- recent policy changes;
- no-op learning decisions;
- rollback lineage.

### 8.6 Platforms

Show dynamic readiness, account/profile identity, last successful readback, and next metric availability without revealing secrets.

### 8.7 Incidents

Show:

- unknown writes;
- failed reconciliation;
- source/evidence blockers;
- provider degradation;
- destination failures;
- stale credentials/session requiring operator action;
- exact safe recovery action.

### 8.8 Visual acceptance

Actual UI/browser/CDP acceptance requires fresh screenshots and independent visual review.

Do not claim final UI PASS from unit tests alone.

## 9. Work Package FDA-G — Genuine calendar-time soak and V1 release

Synthetic/accelerated logical days are useful regression evidence but cannot close final Daily App reliability.

Run the actual app continuously over a bounded real period.

Target:

`5–10 genuine operating days`

This is evidence duration, not an excuse for passive waiting. Build/fix only real blockers found by production.

### 9.1 Soak should observe

- supervisor staying alive and waking correctly;
- restart/recovery;
- scheduled cycles;
- optional material-event trigger path;
- legitimate `NO_PUBLICATION`;
- at least one fresh evidence-viable real story reaching article/review/media/package/live gate;
- real public writes where READY and appropriate;
- strict readback/reconciliation;
- platform unavailable/skip behavior;
- real performance observations;
- one learning evaluation with either bounded policy update or justified no-op;
- next decision consuming the current policy version;
- cost/runtime and operator intervention.

### 9.2 Release gate

Release only when:

- no unresolved systematic publishability defect remains;
- no provenance/rights overclaim remains;
- no unreconciled unknown write remains;
- no fabricated factual/numeric/analytical claim occurs;
- at least one real live package and performance lineage has been proven;
- destination failures are understandable and bounded;
- controller restart/idempotency is proven;
- metrics collector truth/limitations are explicit;
- learning policy is bounded and reversible;
- V5 Daily App accurately represents real current state;
- operating cost is measured and acceptable for the product.

Technical release:

`v1.1.0`

Product-facing name:

`Capital Chronicle ContentOps V1 — Daily App`

Do not move or recreate protected `v1.0`.

## 10. Work Package sequencing

Current sequence:

```text
FDA-A publishability safety closure
  +
FDA-B always-on runtime vertical slice
        ↓
FDA-C real autonomous multi-platform lifecycle
        ↓
FDA-D real performance observation
        ↓
FDA-E bounded closed-loop learning
        ↓
FDA-F final V5 Daily App UI from real states
        ↓
FDA-G genuine calendar-time soak / acceptance / v1.1.0
        ↓
freeze V1
        ↓
V2 Pro Video Factory
```

FDA-A and the first useful portion of FDA-B should be implemented together as the first heavy bounded task because the user-visible product needs both a trustworthy content path and a process that can stay alive and invoke it.

Do not split them into a long ceremony chain.

## 11. First builder task

Exact task:

`TASK_CONTENTOPS_FINAL_DAILY_APP_ALWAYS_ON_RUNTIME_VERTICAL_SLICE_V1`

### User problem

ContentOps can execute individual canonical newsroom cycles, but Jim cannot yet start one application and leave it running safely. The latest builder also contains two media provenance defects and a broken Federal Reserve locator route that would make always-on operation repeat known failures.

### Capability delivered

One task should deliver:

1. corrected canonical article/media factual provenance and rights provenance;
2. corrected bounded Federal Reserve official-policy locator;
3. one always-on Daily App supervisor using the existing canonical orchestrator and durable store;
4. deterministic bootstrap editorial-window policy;
5. due-window idempotency / restart-safe execution;
6. material-event wakeup seam using existing governed discovery metadata;
7. one bounded local/controlled supervisor demo proving the cycle is invoked exactly once and persisted;
8. one current canonical canary only if the task remains clean and safe after focused validation.

### Demo path

```text
start Daily App supervisor
→ load durable state + EditorialWindowPolicy
→ identify exactly one due window
→ call canonical newsroom cycle once
→ accept publication or legitimate NO_PUBLICATION
→ persist terminal state
→ duplicate tick/restart does not duplicate cycle
→ compute next wake
```

### Measurable utility delta

Before: manual/operator-triggered canonical cycles.

After: one persistent application can autonomously own due-window execution and recovery without continuous expensive work or duplicate cycles.

### Why now

The newsroom, evidence gates, article/media builder, packages, publication/readback foundation, and durable store already exist. The missing product boundary is orchestration into one always-on application plus correction of known safety defects.

### Bounded cost/time

Keep this to one heavy product batch. No broad platform metrics implementation or final UI rebuild in this task.

### Validation

Focused tests plus one supervisor end-to-end local smoke and, if safe/current inputs exist, one canonical current canary. No full suite absent concrete changed-path risk.

### Exact next blocker after success

`TASK_CONTENTOPS_FINAL_DAILY_APP_REAL_PERFORMANCE_OBSERVATION_AND_LEARNING_LOOP_V1`

unless the first real supervisor run reveals a substantive product blocker.

## 12. Provider/model policy

Keep current 9Router authority and role-specific routing.

Do not redesign model ordering merely because providers are intermittently unavailable.

The always-on supervisor must never continuously probe expensive LLMs while idle.

Provider/model attempts remain finite and bounded per logical invocation.

## 13. Browser/network scope for the final product

### Ingestion

Chrome `CapitalChronicleBot`, CDP 9222:

- X/headline ingestion only;
- connect/navigate/reload/scroll/listen where current ingestion contract permits;
- no publication;
- no cookie/storage/token/session export.

### Publication/readback/performance observation

Edge `contentops-social-main`, CDP 9223:

- canonical platform publication/media management;
- strict readback/reconciliation;
- read-only performance observation only when a bounded adapter explicitly supports it;
- no raw credential/session inspection.

### Official evidence

Use explicit allowlisted first-party endpoints, bounded requests/time/bytes, exact point-in-time provenance, and fail closed.

## 14. Safety invariants

Never:

- expose or request raw env values/tokens/webhook URLs/auth headers/cookies/session data/private keys;
- fabricate numeric truth;
- manufacture evidence or source URLs;
- treat model/X/social text as factual authority;
- weaken evidence gates for engagement;
- mutate Capital Chronicle analytical truth;
- publish outside exact READY canonical destinations;
- blind retry an unknown write;
- create a second production runner authority/state store/scheduler/publisher/provider gateway/dashboard/analysis engine;
- mutate protected `v1.0`.

## 15. Fast-ship blocker policy

Stop immediately only for substantive blockers such as:

- secret/credential exposure;
- fabricated numeric truth;
- unauthorized access/public write;
- destructive unrelated mutation;
- protected release mutation;
- irreconcilable remote/ref mismatch;
- unresolved substantive merge conflict;
- missing required operator/external input that cannot safely be inferred;
- a new systematic runtime defect that prevents the bounded task from completing.

Do not stop for:

- absent CI alone;
- unrelated dirty files with zero path overlap;
- historical stale docs now superseded by this authority;
- pre-existing unrelated test noise;
- mechanical formatting defects that can be safely repaired.

On stop, report only the exact problem, last successful stage, network/provider/public-write state, and what is needed to continue.

## 16. Documentation discipline

This plan and North Star are durable routing authority. Routine implementation tasks should not create large evidence/document bundles.

Update only minimal current pointers when routing materially changes.

Implementation/test/evidence should dominate product work.

## 17. V2 deferral

The existing Tier-2 Pro Video Factory North Star/Master Plan remain valid future product authority.

Implementation is deferred until Final Daily App V1 acceptance/freeze unless Jim explicitly reprioritizes.

Do not delete Tier-2 plans. Do not let their older sequencing override this owner decision.

## 18. Final definition of done

V1 is done when Jim can realistically do this:

```text
open Capital Chronicle ContentOps Daily App
leave it running
return later
see what stories were considered
see what was published or intentionally skipped
see every public object's readback/reconciliation state
see performance observations
see what timing/SEO/content/package policy the system learned or declined to change
see the next planned window
and trust that the app will continue without manual routine operation
```

That is the V1 product. Everything else is supporting infrastructure.