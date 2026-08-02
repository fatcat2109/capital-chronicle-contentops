# Capital Chronicle ContentOps — Institutional Full-Automation Content Factory North Star V1

## 0. Executive decision

Capital Chronicle ContentOps is not finished merely because one multi-platform release succeeded. The accepted Treasury v1.0 release proves that the repository can produce, authorize, publish, distribute, read back, repair, and freeze one exact story. It does not prove that the product is a continuously operating, generalized, restart-safe content factory.

The final-product direction is therefore:

```text
continuous governed intake
→ deterministic story eligibility
→ capability-driven assignment
→ evidence and claim packet
→ AI-native editorial production
→ deterministic and model-assisted review
→ exact operator decision package
→ durable approved outbox
→ supervised multi-platform dispatch
→ strict readback and reconciliation
→ performance/community observations
→ governed learning and next-story backlog
→ continuous next window
```

The operating model is **automation-first and human-authoritative**:

```text
Automation performs discovery, grounding, drafting, adaptation, visual preparation,
quality checks, packaging, routing, dispatch mechanics, readback, reconciliation,
metrics normalization, and learning preparation.

Jim decides whether an exact immutable package may cross the public-write boundary.
```

Approval must not become a euphemism for manual production. By the time a package reaches Jim, the system should already have completed every safe mechanical and analytical step and should present only decision-relevant differences, blockers, evidence, and exact public payloads.

## 1. Final-product definition

Capital Chronicle ContentOps is an AI-native, evidence-governed editorial, publishing, distribution, and community-learning operating system for serious macro, financial, regulatory, geopolitical, corporate, and physical-event content.

It is not:

- a generic social scheduler;
- a platform spam bot;
- a hidden autonomous engagement agent;
- an LLM that invents source authority;
- a second market-data or macro-data database;
- a financial signal service;
- a collection of unrelated scripts that happen to publish;
- a dashboard that reports readiness without executable state continuity.

It is complete only when the same canonical production system can repeatedly handle fresh, diverse stories with durable state, fail-closed evidence rules, bounded operator approval, reliable dispatch, strict readback, deterministic recovery, observable SLOs, and a governed learning loop.

## 2. Verified current truth

### 2.1 Accepted proof

The accepted v1.0 Treasury release demonstrates a bounded supervised production proof:

- exact story-scoped database authority;
- global DQR remaining independently blocked;
- canonical Substack article;
- three approved visuals;
- Telegram, Discord, X, LinkedIn, Facebook Page, Instagram Business, Threads, and YouTube Community derivatives;
- stable public or provider identities;
- platform-specific strict readback;
- bounded Substack repair without derivative mutation;
- machine verification and operator acceptance;
- immutable release tag.

This proof must remain frozen and must never be rewritten as evidence of a broader claim than it supports.

### 2.2 Historical failure evidence

Earlier live work is valuable because it reveals the real failure surface:

- Terra Ultra posted Telegram but did not complete Substack or X.
- The first Substack-first run saved a draft but failed on browser-extension/file-access behavior.
- The first eight-platform run was blocked and required recovery.
- Recovery published Substack and repaired Telegram but still left X blocked.
- The July 11 release candidate transported content broadly but failed product-quality audit on stale story selection, source-calibrated wording, visual diversity, quantitative labeling, historical LinkedIn identity, Facebook copy, and malformed Threads continuations.
- Final closure had to repair or delete specific public outputs and still withheld a fresh generic canary when database authority was absent.
- The first database-backed July 14 run correctly performed zero writes because no story was eligible.

The product must treat these failures as design inputs, not embarrassing history to be hidden behind aggregate PASS labels.

### 2.3 Current maturity classification

```text
Evidence and editorial architecture: advanced
Bounded multi-platform publication: proven once
Fail-closed ineligible-story behavior: proven
Repeated generalized live operation: unproven
Continuous process supervision: unproven
Durable unified state machine: incomplete
Recurring scheduler correctness: inadequate
Cross-platform recovery consistency: partial
Automated feedback/performance learning: prototype/manual replay
Video production automation: separate and incomplete
```

## 3. Product success metric

The north-star operating metric is not the number of posts created. It is:

> The number of fresh, evidence-authorized, operator-approved story packages that complete the canonical production cycle across their applicable destination set without unapproved writes, duplicate public objects, unresolved unknown-write states, material editorial defects, or lost lineage.

Supporting business metrics should include:

- qualified Substack subscriber growth;
- canonical article completion and return-reader rate;
- click-through from native derivatives to canonical content where platform semantics allow it;
- Discord and Telegram community participation quality;
- qualified questions and topic requests;
- conversion from public audience to newsletter/community membership;
- content reuse efficiency per canonical article;
- operator minutes per completed release;
- revision rate by defect class;
- content production cost by story and platform;
- revenue or monetizable audience contribution when paid products are activated.

Vanity impressions alone must not drive assignment or learning.

## 4. Authority model

Runtime authority order:

1. GitHub remote commit, branch, tag, diff, and exact fetched bytes.
2. Immutable release or run artifacts with exact hashes and source bindings.
3. Current committed code, schemas, tests, status, and generated evidence.
4. Durable operational store and append-only event history.
5. Platform/provider strict readback.
6. Worker logs and local validation evidence.
7. Project Sources and chat context.

No LLM output, status label, dashboard badge, task name, or worker self-classification can override exact evidence.

### 4.1 Truth domains

The system must keep these domains separate:

- source truth;
- claim and numeric truth;
- point-in-time truth;
- editorial judgment;
- operator decision;
- publication authority;
- platform write outcome;
- public readback;
- performance observation;
- learning recommendation.

A PASS in one domain never grants a PASS in another.

## 5. Canonical product architecture

### 5.1 One production orchestrator

There must be exactly one live-capable production orchestrator. The existing canonical runner remains the migration anchor:

```text
live_contentops.eight_platform_substack_first_pipeline_v1
```

It should evolve behind a stable orchestration interface rather than accumulating more one-off flags and story-specific repair blocks.

All other live-capable entrypoints must be classified as one of:

- compatibility wrapper that delegates to the canonical orchestrator;
- read-only preparation utility;
- test fixture;
- historical evidence generator;
- quarantined legacy path with runtime public-write denial.

No separate scheduler, local HTTP server, old runner, UI button, or CLI command may invoke an adapter outside the canonical state machine.

### 5.2 Canonical components

```text
ContentOps Supervisor
├── Intake Window Coordinator
├── Governed Candidate Reader
├── Assignment and Preemption Engine
├── Evidence/Claim Packet Consumer
├── Editorial Production Orchestrator
├── Visual and Media Orchestrator
├── Quality and Adversarial Review
├── Operator Decision Service
├── Durable Outbox Coordinator
├── Platform Dispatch Coordinator
├── Readback and Reconciliation Coordinator
├── Metrics and Community Observation Coordinator
├── Learning Proposal Engine
└── Operational Evidence and Incident Recorder
```

Every component communicates through versioned records in the same durable state model. File artifacts remain exportable evidence, but filenames are not the production message bus.

## 6. Durable local-first operational state

### 6.1 Storage decision

Use a single local SQLite database in WAL mode for mutable operational state, with append-only event records and immutable artifact hashes. Git remains authority for code, contracts, plans, accepted evidence packets, and frozen release manifests; SQLite owns in-progress operational coordination.

Do not use a collection of JSON files as a concurrency-sensitive queue. Do not commit the operational database. Export redacted, hash-bound evidence packets into the repo at closeout boundaries.

### 6.2 Required entities

- `work_items`
- `intake_windows`
- `story_candidates`
- `story_versions`
- `assignments`
- `evidence_packets`
- `editorial_artifacts`
- `visual_bundles`
- `platform_variants`
- `review_results`
- `operator_decisions`
- `approval_envelopes`
- `outbox_entries`
- `dispatch_attempts`
- `platform_objects`
- `readback_receipts`
- `reconciliation_cases`
- `incidents`
- `performance_snapshots`
- `feedback_snapshots`
- `learning_proposals`
- `model_invocations`
- `scheduler_ticks`
- `service_heartbeats`

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

Every transition must record:

- transition ID;
- prior and next state;
- exact actor class;
- reason code;
- source artifact hashes;
- payload hashes;
- policy version;
- model/prompt versions if applicable;
- timestamp and decision cutoff;
- retry/reconciliation classification;
- redacted evidence references.

No code path may mutate a public payload after `APPROVED_EXACT`. Any editorial change creates a new artifact version, invalidates the prior approval, and returns the work item to `OPERATOR_PENDING`.

### 6.4 Concurrency and restart safety

The supervisor must enforce:

- single active writer lease per work item;
- lease expiry and explicit recovery;
- idempotent scheduler tick IDs;
- transactionally claimed outbox entries;
- compare-and-set state transitions;
- process heartbeat and stale-worker detection;
- restart reconstruction from durable state;
- no shared `latest_*.json` file as live coordination authority;
- per-run immutable evidence directories;
- one active browser-profile owner;
- platform and account concurrency limits.

## 7. Intake and story assignment

### 7.1 Continuous operation

The final product must operate on explicit windows rather than depend on a user manually launching one large script. Default windows may remain Asia open, Europe open, U.S. open, U.S. midday, and U.S. close, but the scheduler must also support event-driven re-evaluation when a material governed update arrives.

Each window must produce one of three valid outcomes:

- selected assignment;
- explicit no-op because nothing is eligible or sufficiently material;
- blocked window with exact operational reason.

A no-op is not a failure and must not trigger filler content.

### 7.2 Intake sources

ContentOps should consume read-only governed outputs from the Capital Chronicle database and approved local headline/event sidecars. It must not create a parallel numeric-truth path. It may use external search for context and visual discovery only under the current capability contracts; external context does not grant claim permission.

The product may proceed before the analyzer is complete. It should consume exact story-scoped publication packets when available and should also support nonnumeric official-event, regulatory, corporate-filing, physical-event, build-in-public, methodology, and educational content where authority contracts permit them.

### 7.3 Ranking and preemption

Ranking must be inspectable, point-in-time, and constrained by hard gates. The score can help choose among eligible stories; it cannot turn an ineligible story into a publishable one.

Required dimensions:

- materiality;
- policy/economic/geopolitical significance;
- surprise;
- affected breadth;
- source authority;
- freshness;
- evidence completeness;
- audience relevance;
- novelty and update relationship;
- durability;
- original-analysis potential;
- visual feasibility;
- overclaiming risk;
- topic/source/day concentration;
- monetization and subscriber relevance as a bounded secondary dimension.

Breaking classification requires event evidence and must never be inferred from source quality alone.

## 8. Evidence and claim boundary

Every public story must bind to a versioned evidence packet that identifies:

- story and candidate identity;
- source documents and exact URLs;
- claim IDs;
- numeric values, units, intervals, observation and release times where applicable;
- known-at and revision times;
- source health;
- authority class;
- public-use permission;
- limitations;
- citation map;
- market snapshot requirements;
- DQR status;
- publication decision;
- exact producer commit and byte receipt.

The editorial system may synthesize prose only from permitted claims and clearly labeled judgment inputs. It may not manufacture missing numeric authority, point-in-time evidence, or public-use permission.

## 9. Editorial production system

### 9.1 Ordered roles

The canonical eight-role process remains useful:

1. assignment editor;
2. evidence planner;
3. reporter/writer;
4. quantitative editor;
5. visual editor;
6. copy editor;
7. platform editor;
8. independent adversarial final reviewer.

These are logical roles, not necessarily eight separate provider calls. The orchestrator should batch roles where doing so improves cost and coherence, while preserving independent final review semantics.

### 9.2 Article modes

Article mode must be explicit and registry-driven:

- straight news;
- data release;
- policy decision;
- market move;
- rapid analysis;
- deep analysis;
- explainer;
- scenario outlook;
- regulatory/corporate document report;
- physical-event report;
- build-in-public/product update;
- community Q&A.

No universal fallback to `analysis` is allowed. Missing mode must preserve a valid caller-provided mode or fail closed.

### 9.3 Quality requirements

The final rendered artifact must pass:

- source-calibrated headline and lede;
- clear news peg and why-now logic;
- evidence-backed mechanism;
- explicit uncertainty and limitations;
- no unsupported causal certainty;
- no internal process vocabulary;
- no fabricated quote or statistic;
- no advice or signal language;
- correct quantitative methodology and units;
- partial-period labels;
- no duplicate paragraphs or formulaic filler;
- platform-specific semantic completeness;
- exact citation and visual binding;
- independent adversarial review.

A deterministic score threshold alone is not sufficient. The July 11 RC showed that content can pass transport and still fail headline calibration, visual diversity, methodology labeling, and reader-facing quality.

## 10. Visual and media system

### 10.1 Visual policy

Visual requirements are capability- and surface-driven, not universal:

- canonical long-form analysis normally needs three useful visuals and at least two evidence dimensions or modalities;
- text-only native surfaces may require zero visuals;
- image/mixed-media variants must not inherit a text-only waiver;
- physical and geopolitical stories should prefer grounded contextual maps, official photographs, or infrastructure visuals;
- a long-form package must not satisfy diversity with three transformations of one series.

### 10.2 Rights and provenance

Image search is discovery only. Every accepted external visual requires:

- containing source page;
- owner or publisher;
- date and context;
- rights/reuse state;
- dimensions;
- relevance and recency;
- duplicate/perceptual hash;
- manipulation, logo, avatar, thumbnail, and synthetic-content checks.

Generated visuals require prompt, model/version, source-data bindings, transformation metadata, and final hash. Chart methods must state metric definition, unit, frequency, sample, transformation, annualization, and partial-period status.

### 10.3 Video boundary

TikTok, YouTube long-form, and YouTube Shorts are separate media-production modes. They require a script, narration, visual timeline, voice/media rights, thumbnail, render, transcode, upload, and video-specific readback. They must not block completion of the Tier-1 text/image factory and must not be misreported as complete because YouTube Community works.

## 11. Model-provider strategy

### 11.1 Current economic default

The current production semantic worker should be configured explicitly as:

```text
provider: 9router
model: Gemini 3.1 Pro class configured by exact registry ID
```

The repository must not depend on an implicit provider default. Current code contains a default 9router model string for a Gemini Flash-class model and separately attempts a Gemini 3.1 Pro preview fallback; this does not match the operator's intended default and must be reconciled early.

### 11.2 Provider-independent contracts

Every model call must be routed through a versioned provider registry containing:

- provider ID;
- exact model ID;
- capability class;
- context and output limits;
- JSON/schema mode support;
- timeout;
- request budget;
- retry eligibility;
- fallback chain;
- cost class;
- prompt version;
- evaluation status;
- allowed editorial roles.

Model replacement must not change evidence, approval, outbox, or platform contracts.

### 11.3 Model failure behavior

Failures must be classified as:

- transport failure before response;
- timeout;
- rate limit;
- malformed structured output;
- schema mismatch;
- incomplete output;
- unsupported claim;
- quality failure;
- context overflow;
- provider model substitution or alias drift.

Retry is permitted only within the configured semantic request budget and must record every attempt. A deterministic recovery template may produce a draft candidate, but it must carry a distinct provenance and may not silently receive the same quality classification as a successful model-produced article.

### 11.4 Evaluation and upgrade

Before switching to a more capable future model, run the same versioned evaluation corpus against both models. Evaluate:

- claim fidelity;
- headline calibration;
- causal restraint;
- quantitative wording;
- source use;
- prose quality;
- visual planning;
- platform adaptation;
- structured-output validity;
- latency and cost;
- revision rate under independent review.

Promote a model only through a committed routing-policy update and regression evidence. Model quality is an input to production, not a source of authority.

## 12. Approval and live edge

### 12.1 Approval envelope

An approval must bind:

- work item and story version;
- canonical article hash;
- evidence packet hash;
- visual bundle hash;
- exact platform variant hashes;
- destination/account bindings;
- policy snapshot;
- expiry or freshness deadline;
- operator identity;
- decision and timestamp;
- explicitly authorized platform set;
- explicitly authorized operation set.

A boolean `approved=true` is insufficient.

### 12.2 Approval expiry

Approval expires when any of these changes:

- claim or evidence packet;
- freshness decision;
- article or variant bytes;
- visual asset;
- platform or account binding;
- policy version;
- public destination;
- decision-time cutoff;
- operator-specified platform set.

Expired approval cannot be revived by retrying the same command.

### 12.3 Supervised boundary

The live edge should require one compact operator decision, not a sequence of mechanical confirmations. Jim should see:

- what changed since the last review;
- exact headline/article/variants;
- evidence and claim scope;
- visual provenance;
- unresolved nonblocking caveats;
- platform applicability;
- freshness deadline;
- predicted actions and recovery constraints.

The dispatcher must consume the approved immutable envelope, not rebuild content after approval.

## 13. Durable outbox and dispatch semantics

### 13.1 Outbox entry

Each outbox entry binds one exact platform operation and contains:

- outbox ID;
- approval envelope ID/hash;
- platform/account/destination;
- operation type;
- exact body/media/payload hashes;
- canonical URL dependency;
- scheduled or immediate execution policy;
- idempotency key;
- current attempt state;
- retry class and budget;
- readback requirement;
- parent object for reply/thread operations;
- incident/reconciliation link.

### 13.2 Attempt taxonomy

```text
NOT_ATTEMPTED
PREWRITE_BLOCKED
PREWRITE_FAILED_SAFE_TO_RETRY
WRITE_SUBMITTED
WRITE_CONFIRMED_PROVIDER
PUBLIC_ID_RECOVERED
STRICT_READBACK_PASS
STRICT_READBACK_FAIL_KNOWN_OBJECT
UNKNOWN_WRITE
RECONCILIATION_REQUIRED
RECONCILED_PRESENT
RECONCILED_ABSENT_SAFE_TO_RETRY
PERMANENT_FAILURE
DEAD_LETTER
```

### 13.3 Retry rules

- Validation, approval, freshness, permission, and policy failures are never automatically retried.
- Pre-write transient transport or rate-limit failures may use bounded exponential backoff with jitter.
- Unknown-write outcomes never receive blind retry.
- Known public-object readback failures enter targeted reconciliation or repair.
- Reply/thread continuation may resume only from the exact verified parent and last confirmed child.
- A circuit breaker isolates a degraded platform without blocking already valid destinations unless the operator requested all-or-nothing semantics.
- Retry budget and backoff are platform- and error-class-specific.

### 13.4 Idempotency

Idempotency must include at least:

```text
platform + account + destination + operation + payload hash + media hash + parent ID + run/work item
```

Topic-level duplicate detection is useful for editorial assignment but must not replace operation-level idempotency.

## 14. Platform delivery tiers

### Tier 1 — Required text/image production destinations

- Substack canonical article;
- Telegram;
- Discord;
- X;
- LinkedIn;
- Facebook Page;
- Instagram Business;
- Threads;
- YouTube Community.

A story may omit an inapplicable destination only through an explicit capability decision, not because the adapter silently failed.

### Tier 2 — Explicit media-production modes

- TikTok;
- YouTube long-form;
- YouTube Shorts.

### Tier 3 — Manual or operator-assisted recovery

Manual fallback may be used when official automation is unavailable, paid, brittle, blocked by platform review, or not economically justified. The system still prepares the exact payload, records the manual action and public identity, verifies readback where possible, and preserves the same evidence model.

## 15. Platform adapter contract

Every Tier-1 adapter must implement:

```text
capability_probe()
preflight()
prepare_exact_request()
execute_once()
readback()
reconcile_unknown_write()
repair_known_object()
resume_partial_chain()
classify_error()
redact_evidence()
```

Each adapter declares:

- official API, webhook, browser/CDP, or operator-assist transport;
- supported operations;
- account and destination binding requirements;
- idempotency behavior;
- known write-uncertainty states;
- readback strength;
- retryable error classes;
- edit/delete support;
- rate and concurrency limits;
- selector or API-version contract;
- minimum evidence required for PASS.

Unsupported operations must fail closed. A mock fallback must never return `SUCCESS` in live mode.

## 16. Process supervision and scheduling

### 16.1 Supervisor

Run a single local supervisor under an operator-controlled Windows startup/task configuration. It should:

- acquire the global writer lease;
- record heartbeat;
- run deterministic intake windows;
- wake on material event input;
- enqueue work rather than execute through a web request thread;
- enforce platform concurrency;
- recover stale leases and incomplete attempts;
- expose health through a read-only local endpoint;
- stop dispatch when the kill switch is active;
- survive process and workstation restart.

### 16.2 Scheduler rules

The scheduler must:

- use explicit timezone-aware window definitions;
- persist tick identity and outcome;
- support missed-window policy and catch-up limits;
- distinguish one-shot outbox execution from recurring intake windows;
- never store raw credentials inside scheduled payloads;
- never use a plain boolean as approval authority;
- never retry unknown writes;
- never mark unsupported platform work successful;
- never let one malformed registry file become an empty healthy queue;
- use durable locks to prevent concurrent dispatch of the same entry.

## 17. Observability and incident response

### 17.1 Correlation model

Every event must carry:

- work item ID;
- run ID;
- story version;
- approval envelope;
- outbox entry;
- attempt number;
- platform/account;
- model invocation if relevant;
- incident ID if degraded.

### 17.2 Required operational metrics

- supervisor heartbeat freshness;
- intake-window completion and lag;
- eligible candidate count;
- work-item state age;
- model attempt count, latency, malformed-output rate and fallback rate;
- review blocker rate by class;
- operator decision age;
- queue depth;
- dispatch attempt and strict-readback rate;
- unknown-write count and reconciliation age;
- duplicate-prevention events;
- browser session and selector health;
- credential capability status without secret values;
- platform circuit-breaker state;
- incident count and mean time to recover;
- public-quality repair rate;
- operator minutes per release.

### 17.3 Incident packet

Every material incident must produce a redacted packet containing timeline, affected work items and platforms, exact hashes, confirmed public objects, unknown states, attempted recovery, current freeze status, root cause, permanent repair and regression tests.

## 18. Security and local operator boundary

- No raw environment values, tokens, webhook URLs, cookies, authorization headers, browser storage, or session material may be printed or committed.
- Scheduled and durable records contain credential handles, never credential values.
- Browser profile files are not read directly. The canonical profile owner and CDP endpoint are validated structurally.
- The local HTTP surface must be read-only by default. A CORS-wildcard unauthenticated POST endpoint must not launch the live pipeline.
- UI actions create decision or work records; they do not call platform adapters directly.
- A kill switch freezes new public writes while preserving readback and reconciliation capability.
- Dispatch evidence must be redacted before persistence.

## 19. Operator UI

The canonical UI remains `ui/contentops_v5/`. It must become an operational control plane over the durable state model rather than a set of static or separately generated evidence views.

The first fold should answer:

- Is the supervisor healthy?
- What is the current intake window?
- Which story is selected and why?
- What is blocked?
- What exact decision does Jim need to make?
- Is any platform in unknown-write or incident state?
- Did the most recent release complete strict readback?

Required surfaces:

- command center;
- candidate and assignment queue;
- evidence and article review;
- exact platform variant review;
- approval envelope review;
- outbox and dispatch timeline;
- platform health/readback matrix;
- incident and reconciliation center;
- content calendar/window history;
- performance/community learning review;
- model invocation and evaluation diagnostics;
- policy and credential capability status.

The UI must preserve detail through drilldown without making the operator parse raw JSON walls.

## 20. Feedback, performance, and learning

### 20.1 Observation collection

Collect metrics through official APIs where stable and economically justified. Where not available, provide a one-step operator-assisted capture workflow with exact platform object binding. Missing metrics remain `UNAVAILABLE`, never zero.

Collect community feedback from approved Discord, Telegram, Substack, and other public surfaces only through explicit, scoped readers or operator-provided exports. Do not implement autonomous DMs, reactions, persuasion, or engagement bots as a prerequisite for the final product.

### 20.2 Learning firewall

Learning may recommend changes to:

- topic mix;
- format and length;
- headline variant;
- publication window;
- visual format;
- canonical-to-native CTA;
- platform applicability;
- subscriber/community funnel;
- editorial workflow efficiency.

Learning may never alter:

- claim values;
- source authority;
- public-use permission;
- DQR;
- point-in-time truth;
- citation requirements;
- advice restrictions;
- approval authority;
- dispatch safety rules.

Every learned policy change is a proposal, evaluated offline and promoted through an operator-approved versioned configuration change.

## 21. Monetization and audience flywheel

The factory should optimize for durable Capital Chronicle value, not maximum posting volume.

The intended flywheel is:

```text
high-trust canonical research
→ native distribution
→ qualified newsletter/community audience
→ questions and objections
→ better story backlog
→ differentiated research and tools
→ paid newsletter/research/product conversion
→ improved data and editorial capacity
```

Required product hooks:

- canonical campaign and CTA registry;
- UTM and referral policy without breaking duplicate identity;
- subscriber and community conversion events;
- content series and audience-segment tags;
- paid/free boundary metadata;
- reusable research artifacts;
- post-publication follow-up opportunities;
- revenue and qualified-lead attribution when available.

Monetization signals remain secondary to evidence and editorial integrity.

## 22. Final-product acceptance definition

The product is not complete until it passes all of the following:

1. One canonical live-capable orchestrator; all alternate live paths are delegated or quarantined.
2. Durable local state survives restart and reconstructs every in-flight work item.
3. No raw credential values are stored in queues, schedules, logs or evidence.
4. Approval envelopes bind exact immutable artifacts and expire correctly.
5. Scheduler and supervisor run continuously with durable ticks, leases and no duplicate dispatch.
6. Unknown-write outcomes never receive blind retry.
7. Every Tier-1 destination has strict readback or a clearly weaker provider-readback classification accepted by operator policy.
8. A seven-day shadow soak completes all configured windows with no lost state.
9. A supervised live cohort covers at least ten fresh stories, at least five story types, and all applicable Tier-1 destinations.
10. The cohort records zero unapproved public writes, zero unresolved duplicate objects, zero silently lost attempts, and zero unresolved unknown writes at acceptance.
11. Editorial quality passes operator sampling and has no material source, headline, quantitative, visual-rights, or internal-language defect.
12. Platform degradation and workstation/process restart drills pass.
13. Metrics/community observations produce reviewable learning proposals without mutating authority or publishing automatically.
14. UI truth matches the durable store and exact evidence.
15. Local no-secret CI and the full relevant test suite pass; no CI claim is made when no CI exists.

## 23. Anti-drift rules for future builders

- Read the current authority packet before editing.
- Do not create a parallel runner, scheduler, outbox, approval engine, status stack, or canonical UI.
- Extend existing versioned contracts or explicitly supersede them.
- A task must name its state-machine transitions and exact authority boundary.
- A live-capable task must name the exact operator authorization and platform set.
- Do not call a mock or dry-run result a live PASS.
- Do not call transport success product-quality acceptance.
- Do not call one successful story a generalized factory.
- Do not make video/TikTok a blocker for Tier-1 text/image maturity.
- Do not hardcode the product to one LLM model or provider alias.
- Do not add more historical integrity work without a current defect, test or acceptance gap.
- Prefer heavy bounded implementation waves over micro-task ceremony, but split at real live-write, credential, schema, data-authority, or platform-risk boundaries.

## 24. Supersession

This North Star supersedes any interpretation of the prior 25-task ledger that equates feature presence or a bounded v1.0 canary with full operational maturity. The prior plans remain valuable historical design and accepted release evidence. The post-v1.0 execution program is defined in `FINAL_PRODUCT_HARDENING_EXECUTION_PLAN.md`.
