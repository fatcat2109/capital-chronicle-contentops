# Capital Chronicle ContentOps — Live-Run Reconstruction and Reliability Audit V1

## 1. Audit purpose

This report reconstructs the known ContentOps live-run history from committed code, run evidence, dispatch ledgers, public/provider identities, strict-readback records, repair packets, operator findings, current status, and the accepted v1.0 release authority.

The audit answers a narrower and more useful question than “did a task pass?”:

> What exact public action occurred, on which platform, with what payload and media identity, what readback strength, what repair history, and what unresolved reliability implication?

A task title containing `FULL_AUTOMATION`, a process exit code, an adapter `SUCCESS`, or a machine transport PASS is not accepted as proof of a completed product release.

## 2. Evidence hierarchy and classification

### 2.1 Evidence hierarchy

1. Exact Git commit, path, blob and fetched bytes.
2. Public/provider object identity and strict readback bound to exact payload/media hashes.
3. Immutable run evidence, platform matrix and dispatch ledger.
4. Operator visual/product audit.
5. Repair and reconciliation receipts.
6. Tests and local validation logs.
7. Worker narrative or task self-classification.

### 2.2 Run-state taxonomy

| State | Meaning |
|---|---|
| `PLANNED` | Intended platform or action appears only in a plan or payload packet. |
| `DRY_RUN` | Adapter or pipeline executed without a public write. |
| `PREWRITE_BLOCKED` | Gate blocked before platform action. This is a valid fail-closed outcome. |
| `WRITE_ATTEMPTED` | Adapter was invoked, but no confirmed public object exists. |
| `PUBLIC_WRITE_CONFIRMED` | Provider/public object ID or URL proves a write. |
| `STRICT_READBACK_CONFIRMED` | Exact public text, media, identity, chain and URL were verified as applicable. |
| `UNKNOWN_WRITE` | A write may have occurred but exact public identity/readback is missing. Blind retry is prohibited. |
| `REPAIRED_KNOWN_OBJECT` | An exact public object was edited, deleted or reconciled with evidence. |
| `OPERATOR_ACCEPTED` | Product-quality acceptance occurred after machine proof and operator audit. |
| `FROZEN_RELEASE` | Accepted release and identities are immutable historical authority. |

## 3. Executive reconstruction

The live history supports four conclusions:

1. **Early “full automation” runs were partial and platform-fragile.** Telegram was the first reliable live surface. Substack and X required browser/CDP and media-flow repairs.
2. **The July 11 release candidate proved broad transport, not final product quality.** It reached the target text/image surfaces but exposed stale-story, headline, methodology, visual-diversity, identity-reuse, copy and reply-chain defects.
3. **The July 14 database-authorized Treasury run is the strongest accepted proof.** It used the canonical Substack-first runner, exact story-scoped authority, nine text/image surfaces, strict readback, bounded repair and operator acceptance.
4. **No evidence proves continuous generalized operation.** The accepted proof is one story. Current cross-domain operation is deterministic local shadow replay, feedback/performance learning is manual or historical replay, and the live-capable runtime has competing scheduler/server/runner paths.

## 4. Reconstructed run chronology

### 4.1 Terra Ultra North Star run

Evidence root:

`docs/automation/TERRA_ULTRA_NORTH_STAR_FULL_AUTOMATION_V1/`

Observed result:

- Telegram public write succeeded and provider readback identified message `61`.
- Substack did not complete.
- X did not complete.
- The run was therefore a partial platform proof, not a multi-platform release.

Reliability implication:

- Task naming overstated the actual destination completion.
- The original architecture lacked a strong canonical-publication dependency and platform-specific recovery state.

Audit classification:

`PARTIAL_LIVE_TELEGRAM_ONLY`

### 4.2 First Substack-first live run

Evidence root:

`docs/automation/SUBSTACK_FIRST_NORTH_STAR_PIPELINE_LOOP_V1/substack_first_north_star_live_20260710/`

Observed result:

- A Substack draft was created/saved.
- The draft did not become a complete accepted public article.
- The article editor contained zero verified images.
- Browser extension/file-access behavior blocked the intended media/publication flow.
- Telegram and X derivatives were not completed.

Reliability implication:

- Draft creation is not canonical publication.
- Browser media upload and public URL readback are critical path components.
- A saved editor object must remain distinct from a public article object.

Audit classification:

`PARTIAL_SUBSTACK_DRAFT_ONLY_MEDIA_AND_PUBLICATION_BLOCKED`

### 4.3 Initial eight-platform live run

Evidence root:

`docs/automation/EIGHT_PLATFORM_FULL_PIPELINE_V1/eight_platform_live_20260710/`

Observed result:

- Canonical browser/profile checks advanced further than the predecessor run.
- The run did not complete the intended destination set.
- Committed evidence classified the run as blocked and required a recovery run.

Reliability implication:

- Platform count in a runner name does not prove destination completion.
- Recovery must resume exact state rather than restart the whole release.

Audit classification:

`BLOCKED_MULTI_PLATFORM_ATTEMPT_RECOVERY_REQUIRED`

### 4.4 Eight-platform recovery 1

Evidence root:

`docs/automation/EIGHT_PLATFORM_FULL_PIPELINE_V1/eight_platform_live_20260710_recovery1/`

Observed result:

- Substack public article completed.
- Telegram was repaired to include the canonical article relationship.
- X remained blocked.
- Reliability evidence still recorded fragmented social-thread behavior, visual-chain weaknesses and incomplete video/TikTok capability.

Reliability implication:

- The recovery path could preserve and repair known progress.
- Platform recovery was not yet uniform.
- Social-thread semantic composition and visual distribution were not mature.

Audit classification:

`PARTIAL_LIVE_SUBSTACK_TELEGRAM_X_BLOCKED`

### 4.5 July 11 eight-platform release candidate

Evidence root:

`docs/automation/EIGHT_PLATFORM_FULL_PIPELINE_V1/contentops_v1_0_rc_20260711_1/`

Machine transport result:

- Substack completed.
- Telegram completed.
- Discord completed.
- X completed.
- LinkedIn completed.
- Facebook Page completed.
- Instagram Business completed.
- Threads completed.
- YouTube Community completed.
- TikTok was not a completed destination.

Operator audit result:

The release candidate was not acceptable without targeted repairs. Material findings included:

- a fresh LinkedIn story path reused or edited a historical activity;
- Facebook copy contained awkward generated prose;
- the canonical article leaked internal process language;
- the headline overstated `pre-conflict` evidence as `pre-war`;
- average absolute movement was labelled as realized volatility;
- incomplete 2026 data was not clearly marked `YTD` or partial;
- three visuals were transformations of one WTI series rather than meaningful evidence diversity;
- the story was stale relative to the stated freshness policy;
- current Capital Chronicle market state was absent;
- Threads continuations were malformed as standalone fragments.

Reliability implication:

- Broad transport proof is necessary but insufficient.
- Product acceptance requires source calibration, quantitative-method integrity, visual diversity, identity freshness, native platform semantics and public readback.
- Quality gates must inspect final rendered/public bytes, not only intermediate packets.

Audit classification:

`TRANSPORT_PASS_PRODUCT_QUALITY_BLOCKED_FOR_TARGETED_REPAIR`

### 4.6 July 11 final-closure repair sequence

Evidence root:

`docs/automation/FINAL_AUTOMATION_PIPELINE_CLOSURE_V1/contentops_final_closure_20260711_1/`

Observed result:

- Exact Facebook copy was corrected.
- Historical LinkedIn content was reconciled.
- Malformed Threads objects were deleted through bounded operations.
- Reply recovery exposed identity ambiguity and a visible order caveat.
- A fresh generic canary remained withheld when publication authority was unavailable.
- The oil article repair existed locally but did not become a newly accepted public release.

Reliability implication:

- Exact-object edit/delete capability is valuable.
- Duplicate-text public objects are difficult to identify safely without strong platform object bindings.
- Repair evidence must distinguish intended repair, collateral change and preserved derivative identities.
- A withheld canary is correct behavior when authority is absent.

Audit classification:

`TARGETED_PUBLIC_REPAIR_PARTIAL_CLOSURE_GENERIC_CANARY_WITHHELD`

### 4.7 July 14 database-backed preflight run

Evidence root:

`docs/automation/DATABASE_BACKED_FULL_AUTOMATION_LIVE_RUN_V1/contentops_database_backed_live_run_20260714_1/`

Observed result:

- Database foundation and handoff artifacts were readable.
- No eligible story was selected.
- DQR, reporting permission, public-source URL, freshness, source-health and claim-authority gates blocked the run.
- No browser/CDP or platform adapter was invoked.
- No public write occurred.

Reliability implication:

- The generalized path correctly failed closed before public action.
- A valid continuous system must treat this as a successful no-publication window, not pressure the model to manufacture filler content.

Audit classification:

`PASS_FAIL_CLOSED_NO_ELIGIBLE_STORY_ZERO_WRITE`

### 4.8 July 14 database-authorized Treasury release

Evidence root:

`docs/automation/DATABASE_PUBLICATION_AUTHORITY_AND_CONTENTOPS_FULL_LIVE_CLOSURE_V1/contentops_database_publication_live_20260714_1/`

Observed result:

- One exact Treasury story received story-scoped `contentops_publication` authority.
- Global DQR remained independently blocked.
- The canonical Substack article was published.
- Telegram, Discord, X, LinkedIn, Facebook Page, Instagram Business, Threads and YouTube Community derivatives completed.
- Public/provider IDs and strict readback were recorded.
- X and Threads used ordered root/reply chains with approved visual distribution.
- A bounded Substack update removed a duplicate caption fragment.
- A later bounded editorial repair corrected auction wording and punctuation without mutating the eight derivative identities.
- Final machine verification and operator visual/product acceptance passed.
- Annotated tag `v1.0` froze release commit `6983bfb3ef300414b744f3f8f97ca81ff699348b`.
- TikTok was outside the authorized destination set; YouTube video and Shorts were not invoked.

Reliability implication:

- This is valid evidence that the canonical runner can complete a high-quality, evidence-authorized, nine-surface text/image release.
- The run required bounded post-publication repairs; the final product should reduce repair incidence and formalize repair state.
- One accepted story does not establish repeated generalization, service durability or SLOs.

Audit classification:

`OPERATOR_ACCEPTED_BOUNDED_NINE_SURFACE_TEXT_IMAGE_RELEASE`

## 5. Platform-specific reliability findings

### 5.1 Substack

Proven:

- draft creation;
- public article creation;
- three-visual article flow;
- public URL recovery;
- strict article readback;
- bounded in-place repair of a known article.

Unproven or incomplete:

- repeated operation across a diverse story cohort;
- durable recovery after browser/profile restart;
- selector drift handling under a controlled adapter version contract;
- concurrent work-item exclusion;
- formal distinction among draft saved, publish submitted, public URL unknown and strict readback complete in a shared durable store.

Required hardening:

- adapter-level attempt state machine;
- exact draft/public identity persistence;
- public URL reconciliation before retry;
- browser-session and selector canary;
- article-byte and visual-position readback;
- bounded known-object repair contract.

### 5.2 Telegram

Proven:

- direct public message/photo operations;
- provider ID and readback;
- canonical-link repair;
- stable accepted Treasury release.

Caveat:

- local browser DNS prevented one visual browser check, so provider readback was used.

Required hardening:

- treat provider readback as an explicit evidence class rather than a substitute labelled identically to browser/public readback;
- destination binding and caption-length validation before write;
- exact message edit/reconciliation path;
- no token material in scheduler/outbox records.

### 5.3 Discord

Proven:

- accepted webhook/community derivative in the Treasury release;
- approved visible persona and channel binding.

Unproven:

- continuous community feedback intake;
- durable webhook failure/retry/reconciliation;
- ongoing persona/channel scope health.

Required hardening:

- provider message ID/readback standard;
- webhook capability probe through credential handles only;
- channel-scoped circuit breaker;
- optional approved comment/feedback reader as a separate later capability.

### 5.4 X

Proven:

- accepted root and ordered replies with visual distribution in v1.0;
- public thread readback.

Historical defects:

- early run remained blocked;
- fragmented thread construction;
- permalink/readback uncertainty is recognized as an unknown-write class.

Required hardening:

- durable parent/child chain state;
- resume from last confirmed child only;
- exact permalink reconciliation;
- semantic thread validation before approval;
- browser session/selector health and circuit breaker.

### 5.5 LinkedIn

Proven:

- accepted fresh activity and strict readback in v1.0;
- known-object edit/reconciliation capability.

Historical defect:

- a fresh story reused or edited a historical activity.

Required hardening:

- immutable story-to-activity identity mapping;
- fresh-story create versus exact-same-story edit policy;
- no fallback from failed fresh create to unrelated historical object;
- activity reconciliation before any retry.

### 5.6 Facebook Page

Proven:

- accepted native derivative and readback;
- exact copy repair.

Historical defects:

- awkward generated public prose;
- media/avatar selection risks in earlier paths.

Required hardening:

- final rendered-copy gate after platform adaptation;
- exact expected-media hash/readback;
- known-object edit or one bounded replacement policy;
- no DOM image scraping fallback.

### 5.7 Instagram Business

Proven:

- accepted feed media/caption object and readback.

Platform semantic caveat:

- caption link is text, not a guaranteed clickable hyperlink.

Required hardening:

- media-first capability contract;
- crop/aspect/alt-text checks;
- public caption and visual readback;
- CTA semantics that do not assume clickable caption URLs;
- no bio mutation fallback.

### 5.8 Threads

Proven:

- accepted root plus ordered replies with visual distribution in v1.0.

Historical defects:

- malformed standalone continuations;
- duplicate-text identity ambiguity;
- delete/recreate recovery produced ordering caveats.

Required hardening:

- exact root/reply object identity and parent binding;
- chain-level idempotency;
- no empty parent IDs;
- unknown-write reconciliation before recreation;
- chain order readback and targeted delete allowlist.

### 5.9 YouTube Community

Proven:

- accepted text/image Community post in v1.0.

Boundary:

- this does not prove video or Shorts upload automation.

Required hardening:

- enforce Community surface identity;
- prevent fallback into video/Shorts surfaces;
- strict text/image readback;
- keep video modes separate.

### 5.10 TikTok and video surfaces

Not proven:

- TikTok native publishing;
- YouTube long-form upload;
- YouTube Shorts upload;
- full video production and media-rights pipeline.

Decision:

- keep these as Tier-2 explicit media-production modes;
- do not claim them complete;
- do not let them block Tier-1 text/image factory acceptance.

## 6. Cross-cutting runtime findings

### 6.1 Canonical runner strength

`live_contentops.eight_platform_substack_first_pipeline_v1` is the strongest production path because it includes:

- Substack-first dependency;
- platform-specific payloads;
- approval/payload hash checks;
- dispatch ledger;
- known unknown-write status classes;
- automatic retry denial after uncertain writes;
- platform-specific readback and repair logic;
- final platform matrix and release verification.

It should remain the migration anchor.

### 6.2 Competing live paths are a critical defect

The repository also contains:

- `live_production_pipeline_runner_v6.py` with separate approval and dispatch semantics;
- `server.py`, an in-memory HTTP launcher for that runner;
- `scheduler_v6.py`, which directly calls platform adapters;
- CLI commands that can activate the scheduler live path;
- older approval/outbox/template stacks that do not execute the canonical live state machine.

This is not harmless duplication. It creates multiple sources of truth for:

- what counts as approval;
- where payload hashes are computed;
- how platform success is classified;
- how retry is handled;
- where audit evidence is stored;
- which runner is canonical.

The final product must quarantine or delegate every alternate live path.

### 6.3 Scheduler is not production-safe

Current `scheduler_v6.py` has material defects:

- JSON file is used as mutable queue/state.
- Approval is a plain boolean.
- Scheduled payloads accept credential-like fields.
- Unsupported platforms can return mock `SUCCESS` even when not dry-run.
- All failures increment a generic retry count; unknown-write states are not preserved.
- A successful recurring entry becomes `dispatched` and is skipped on future ticks despite a newly calculated next execution time.
- Registry read errors silently become an empty queue.
- No cross-process lease or transactionally claimed attempt exists.
- No exact approval envelope/payload hash is required.

The current scheduler must be blocked from live use until replaced by the canonical durable state machine.

### 6.4 Local HTTP server is not a production control plane

Current `server.py`:

- permits CORS `*`;
- exposes an unauthenticated POST launch endpoint;
- launches a noncanonical live runner;
- stores task state in memory;
- uses a shared `latest_dispatch_audit.json` path;
- has no durable approval envelope, queue lease, restart recovery or work-item identity.

It must become read-only health/inspection or be removed from the production surface.

### 6.5 Approval and outbox worlds are disconnected

Several modules correctly model local review, approval templates, idempotency and blocked outbox candidates, but they explicitly do not execute live dispatch. The canonical live runner has its own approval marker and ledger. The final product needs one approval envelope and one durable outbox—not a chain of filenames and partially overlapping contracts.

### 6.6 Telemetry is insufficient for service operation

Current JSONL telemetry provides basic platform success/failure and latency, but lacks durable correlation among work item, story version, approval, outbox, dispatch attempt, public object, incident and reconciliation. It also lacks supervisor heartbeat, queue age, unknown-write age, circuit-breaker state, SLO windows and restart reconstruction.

### 6.7 Continuous intake and learning remain unproven

The newsroom has deterministic five-window scheduling and cross-domain shadow replay. The performance and community modules are manual, mock or historical replay. There is no accepted evidence of:

- an always-on process supervisor;
- new governed candidates arriving and being processed continuously;
- automated platform metrics collection;
- live community feedback normalization;
- calibrated policy improvement from a meaningful released cohort.

## 7. Reliability maturity scorecard

| Domain | Maturity | Evidence-based judgment |
|---|---|---|
| Exact evidence and claim boundary | 4/5 | Strong contracts and fail-closed behavior; current data availability remains variable. |
| Canonical editorial production | 4/5 | Strong v1.0 proof and recent capability hardening; one accepted diverse cohort is missing. |
| Visual production and rights | 3/5 | Strong method contracts; RC exposed diversity/label defects; repeated proof missing. |
| Tier-1 platform transport | 4/5 | One accepted nine-surface release; earlier failures and repair dependence remain. |
| Strict readback | 4/5 | Strong platform-specific evidence in v1.0; evidence classes are not yet unified. |
| Approval integrity | 3/5 | Canonical hash checks exist; repository contains parallel noncanonical approval stacks. |
| Durable outbox | 2/5 | Concepts exist; no single live durable transactional implementation. |
| Scheduler/process supervision | 1/5 | Current live scheduler/server paths are not production-safe. |
| Idempotency and unknown writes | 3/5 | Canonical runner handles key unknown states; not shared by scheduler/all entrypoints. |
| Restart/concurrency recovery | 1/5 | No durable unified leases/heartbeat/reconstruction proof. |
| Observability and SLOs | 2/5 | Basic telemetry exists; service-level evidence is absent. |
| Continuous fresh intake | 2/5 | Deterministic shadow windows exist; always-on live operation is unproven. |
| Performance/community learning | 1/5 | Manual/replay prototypes only. |
| Model portability/evaluation | 2/5 | Retry/fallback exists; default model and operator intent conflict; no formal promotion framework. |
| Operator UI truth | 3/5 | Strong read-only review surfaces; not yet backed by one durable production state model. |
| Video/TikTok | 1/5 | Separate/incomplete; correctly excluded from Tier-1 acceptance. |

## 8. Audit conclusion

### Accepted claim

`ContentOps has proven a bounded, operator-authorized, evidence-backed, nine-surface text/image release with strict readback and bounded repair.`

### Rejected claim

`ContentOps has already proven a continuously operating, generalized, restart-safe full-automation content factory.`

### Required next direction

The highest-value program is not another platform adapter or another historical-only integrity task. It is the consolidation and operational hardening program defined in `FINAL_PRODUCT_HARDENING_EXECUTION_PLAN.md`:

1. one canonical live state machine;
2. durable local operational store;
3. approval envelope and transactional outbox;
4. supervisor, scheduler, leases and restart recovery;
5. platform adapter/reconciliation conformance;
6. 9router/Gemini model registry and evaluation;
7. continuous governed intake;
8. observability and SLOs;
9. shadow soak;
10. diverse repeated live cohort;
11. feedback/performance learning activation;
12. Tier-2 video expansion only after Tier-1 acceptance.
