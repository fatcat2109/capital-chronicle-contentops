# Capital Chronicle ContentOps — Operational SLO and Final Acceptance Standard V1

## 0. Purpose

This standard defines what “full automation operates smoothly” means for the Tier-1 Capital Chronicle ContentOps factory.

A unit-test PASS, a successful provider response, a machine transport proof, one accepted release, or a dashboard green badge is not sufficient. Final acceptance requires operational evidence over time, diverse stories, restart and failure drills, exact public identities, strict readback, and operator product-quality review.

## 1. Measurement principles

### 1.1 Evidence before percentages

Every SLO numerator and denominator must be derived from exact durable records. If the system cannot prove the denominator, the SLO result is `UNMEASURABLE`, not PASS.

### 1.2 Honest sample size

Each SLO result has one of:

- `PASS`
- `FAIL`
- `INSUFFICIENT_EVIDENCE`
- `NOT_APPLICABLE`
- `UNMEASURABLE`

A 100% result over one story is historical proof, not a reliability SLO.

### 1.3 Zero-tolerance invariants

These conditions have an error budget of zero at every stage:

- unapproved public write;
- write to wrong account, page, channel or surface;
- raw secret value persisted or committed;
- fabricated claim, numeric value, citation, permission or point-in-time evidence;
- global DQR bypass;
- post-approval payload mutation without new approval;
- blind retry after unknown write;
- unresolved duplicate public object caused by the system;
- lost durable work item or public-object identity;
- mock result reported as live success;
- UI/operator status claiming public success without exact readback evidence.

Any occurrence blocks final acceptance and requires incident closeout plus regression proof.

## 2. Service boundary

### 2.1 Tier-1 service

The Tier-1 service covers:

- continuous governed intake windows;
- story assignment and no-op decisions;
- evidence/claim consumption;
- editorial and visual production;
- operator decision packaging;
- approval envelope creation;
- durable outbox;
- supervised dispatch;
- strict readback and reconciliation;
- performance/community observation preparation;
- operational UI and evidence export.

Tier-1 platforms:

- Substack;
- Telegram;
- Discord;
- X;
- LinkedIn;
- Facebook Page;
- Instagram Business;
- Threads;
- YouTube Community.

Applicability is capability-driven. A platform can be omitted only through an explicit recorded decision.

### 2.2 Tier-2 exclusion

TikTok, YouTube long-form and YouTube Shorts are separate service classes. Their absence does not fail Tier-1 acceptance.

## 3. Reliability evidence stages

### Stage 0 — Deterministic tests

Minimum evidence:

- state-machine transition tests;
- migration tests;
- adapter conformance tests;
- approval mutation tests;
- scheduler/restart tests;
- unknown-write tests;
- model structured-output tests;
- no-secret scans.

This stage proves logic, not service reliability.

### Stage 1 — Seven-day continuous shadow soak

Minimum evidence:

- seven consecutive operational days;
- all configured intake windows recorded;
- at least 25 window evaluations or explicit operator-approved equivalent;
- at least ten shadow work items;
- five or more story types where data permits;
- multiple forced restart/failure drills;
- zero public writes.

### Stage 2 — Supervised live cohort 1

Minimum evidence:

- three fresh story-scoped authorized releases;
- three or more story types;
- one market-sensitive and one nonmarket story;
- all applicable Tier-1 destinations;
- strict readback and operator audit.

### Stage 3 — Supervised live cohort 2

Minimum evidence:

- at least ten fresh accepted releases;
- at least five story types;
- multiple intake windows;
- one correction/material-update chain;
- one no-eligible-candidate window;
- one model/provider failure or fallback case;
- one platform degradation/reconciliation case;
- available performance/community observations.

### Stage 4 — Post-acceptance rolling SLO

After final acceptance, evaluate over rolling 30-day windows. When fewer than ten releases exist in a window, publish counts and exact incidents and label rate-based conclusions `INSUFFICIENT_EVIDENCE`.

## 4. Core operational SLOs

### 4.1 Supervisor availability

Definition:

Percentage of expected active minutes in which the supervisor heartbeat is fresh and the global writer lease is healthy.

Target:

- shadow soak: `>= 99.0%`;
- final rolling target: `>= 99.5%` during configured operating hours.

Exclusions:

Only predeclared operator maintenance windows.

Failure conditions:

- missing heartbeat with no incident;
- two simultaneous active writer leases;
- supervisor reports healthy while queue processing is dead.

### 4.2 Intake-window completion

Definition:

Configured windows ending in a durable `SELECTED`, `NO_ELIGIBLE_CANDIDATE`, or explicit `BLOCKED` record within the allowed lag.

Target:

- completion rate `>= 99%`;
- p95 start lag `<= 5 minutes`;
- p95 terminal decision lag `<= 15 minutes`, excluding upstream dependency outage recorded as an incident.

Critical invariant:

No window silently disappears.

### 4.3 Durable-state integrity

Target:

- lost work items: `0`;
- duplicate state transitions caused by concurrent processing: `0`;
- state transition without reason/actor/hash binding: `0`;
- failed migration corrupting previous usable state: `0`;
- restart reconstruction mismatch: `0`.

This is a zero-budget SLO.

### 4.4 Assignment determinism

Definition:

Same point-in-time candidate/evidence/config input produces the same hard-gate outcome and deterministic score components.

Target:

- hard-gate replay match: `100%`;
- ranking deterministic-field replay match: `100%`;
- LLM-generated judgment may vary only inside separately recorded bounded fields and cannot alter eligibility.

### 4.5 Editorial package completion

Definition:

Eligible assigned work items reaching either `OPERATOR_PENDING` with a complete package or a truthful terminal `REVIEW_BLOCKED` state.

Targets:

- p50 production time `<= 12 minutes` for standard text/image stories;
- p95 production time `<= 30 minutes`, excluding provider outage or operator-requested deep research;
- package lineage completeness `100%`;
- exact variant hash coverage `100%` for applicable destinations.

These time targets are provisional until the first shadow soak establishes a baseline. A slower result does not automatically fail if quality and correctness are preserved; it must generate a capacity finding.

### 4.6 Model structured-output validity

Definition:

Provider attempts that return syntactically and semantically valid versioned output before deterministic recovery.

Targets after a minimum 50 attempts:

- valid structured output `>= 98%`;
- provider transport completion `>= 99%` excluding declared provider outage;
- unplanned model alias/substitution events `0`;
- recovery-template use `< 10%` of accepted operator packages;
- unsupported claim additions surviving deterministic review `0`.

Before 50 attempts, report counts and `INSUFFICIENT_EVIDENCE` for rates.

### 4.7 Operator review efficiency

Definition:

Active operator time from opening the exact review package to approve/hold/reject.

Targets after ten live stories:

- median `<= 8 minutes`;
- p90 `<= 15 minutes` for standard stories;
- mechanical editing required after package presentation `< 20%` of accepted stories;
- approval decision always binds exact immutable bytes.

Deep research and exceptional incident recovery are excluded but reported separately.

### 4.8 Approval integrity

Target:

- stale/mismatched approval accepted: `0`;
- approved artifact mutation: `0`;
- approval missing exact destination/platform set: `0`;
- expired approval dispatched: `0`;
- dispatch built from bytes different from approval envelope: `0`.

### 4.9 Outbox claim integrity

Target:

- two workers execute the same outbox entry: `0`;
- outbox entry without valid approval envelope: `0`;
- entry remains `DISPATCHING` past lease expiry without incident/recovery: `0`;
- idempotency key collision for nonidentical operation: `0`;
- raw credential material inside an outbox record: `0`.

### 4.10 Tier-1 dispatch completion

Definition:

Applicable platform operations reaching `STRICT_READBACK_PASS`, or an operator-accepted weaker evidence class explicitly allowed by platform policy.

Stage 2 and 3 acceptance:

- all applicable destination operations must reach accepted terminal evidence;
- unresolved partial platform state at final cohort acceptance: `0`.

Rolling target after at least 50 operations:

- prewrite-to-strict-readback success without manual repair `>= 97%`;
- completion after bounded automated reconciliation `>= 99%`;
- permanent platform failure `< 1%`;
- wrong account/surface `0`.

### 4.11 Strict readback coverage

Target:

`100%` of successful public operations must have:

- expected account/destination;
- public/provider object identity;
- expected text or semantically exact allowed representation;
- expected media identity/similarity where applicable;
- canonical URL semantics where applicable;
- thread/reply parent and order where applicable;
- payload/media evidence binding.

A provider acknowledgement without content readback receives a distinct weaker classification and requires explicit platform policy.

### 4.12 Unknown-write SLO

Target:

- blind automatic retry: `0`;
- unresolved unknown write at end of operator availability window: `0` for final cohort;
- p95 reconciliation start `<= 5 minutes` while operator/supervisor is active;
- p95 reconciliation terminal decision `<= 30 minutes` for platforms with supported readback;
- duplicate created during reconciliation: `0`.

If a platform cannot support adequate reconciliation, it must be downgraded to operator-assisted mode rather than silently accepted.

### 4.13 Duplicate-public-object SLO

Target:

- unintended duplicate root/canonical object: `0`;
- unintended duplicate continuation/reply: `0`;
- duplicate caused by restart: `0`;
- unresolved duplicate at release acceptance: `0`.

Editorial topic recurrence is not a duplicate if material-update policy explicitly permits it.

### 4.14 Recovery and repair rate

Target after ten releases:

- releases requiring post-publication editorial repair `< 10%`;
- platform objects requiring delete/recreate `< 5%`;
- collateral mutation of accepted unaffected derivatives `0`;
- repair without exact object identity `0`.

Any quantitative, source-authority, legal, wrong-account or materially misleading repair counts as a critical defect and blocks final cohort acceptance.

## 5. Editorial and evidence quality objectives

### 5.1 Claim integrity

Target:

- public claim outside approved claim set: `0`;
- numeric claim with missing value/unit/time/source/citation: `0`;
- invented public-use permission: `0`;
- future revision leakage: `0`;
- unsupported causal certainty surviving final review: `0`.

### 5.2 Headline and framing quality

Target:

- materially overstated headline: `0`;
- stale/breaking framing inconsistent with evidence age: `0`;
- process/internal vocabulary in public output: `0`;
- mode mismatch: `0`.

Operator sample:

Every Stage 2/3 article; after acceptance, at least 25% monthly plus all high-risk stories.

### 5.3 Quantitative-method quality

Target:

- mislabeled metric or transformation: `0`;
- partial period without label: `0`;
- unsupported annualization: `0`;
- chart value mismatch with approved claims: `0`;
- visual caption/source mismatch: `0`.

### 5.4 Visual quality and rights

Target:

- visual without provenance/rights state: `0`;
- wrong or avatar-like media attached: `0`;
- duplicate visual counted as diversity: `0`;
- long-form visual-policy violation: `0` in accepted releases;
- expected platform media missing at readback: `0`.

### 5.5 Platform-native semantics

Target:

- hard/mid-sentence truncation: `0`;
- orphan reply or missing parent: `0`;
- wrong YouTube surface: `0`;
- Instagram CTA requiring clickable caption URL: `0`;
- historical LinkedIn activity reused for fresh story: `0`;
- incomplete visual distribution relative to approved chain: `0`.

## 6. Incident severity

### SEV-0 — Authority/security breach

Examples:

- unapproved public write;
- wrong account/destination;
- raw secret exposure;
- fabricated numeric/source/public-use authority;
- DQR bypass.

Response:

- immediate kill switch;
- freeze new public writes;
- preserve readback/reconciliation;
- operator alert;
- incident packet and root-cause repair;
- final acceptance reset.

### SEV-1 — Public integrity or duplicate risk

Examples:

- unknown write;
- duplicate public root;
- materially misleading public copy;
- corrupted thread chain;
- lost public-object identity.

Response target:

- detection/recording within 5 minutes while active;
- begin reconciliation within 5 minutes;
- no blind retry;
- operator decision if not resolved within 30 minutes.

### SEV-2 — Platform degradation

Examples:

- rate limit;
- stale browser session;
- selector/API drift;
- one destination unavailable;
- provider readback failure on a known object.

Response:

- platform circuit breaker;
- other applicable destinations continue according to release semantics;
- bounded retry only for prewrite-safe classes;
- incident or degradation record.

### SEV-3 — Production inefficiency

Examples:

- high model invalid-output rate;
- slow generation;
- repeated operator revision;
- noncritical UI mismatch.

Response:

- backlog and learning proposal;
- no authority relaxation.

## 7. Error budgets

### 7.1 Zero-budget conditions

All conditions in Section 1.3.

### 7.2 Platform availability budget

After at least 50 operations, each platform may consume at most 1% permanent-failure budget, excluding operator-declared platform outage. Repeated circuit-breaker activation requires mode downgrade or adapter repair.

### 7.3 Model quality budget

After at least 50 attempts, structured invalid output may consume at most 2%. Recovery output does not erase the failed-attempt count.

### 7.4 Editorial repair budget

After at least ten releases, no more than 10% may require post-publication noncritical editorial repair. Critical repair budget is zero.

## 8. Final acceptance gates

### Gate A — Architecture

- one canonical live entrypoint;
- durable state and event log;
- exact approval envelope;
- transactional outbox;
- restart-safe supervisor;
- conformed Tier-1 adapters;
- operational UI over durable truth.

### Gate B — Shadow soak

- seven days;
- all windows recorded;
- no lost/duplicate state;
- all resilience drills pass;
- no public writes;
- SLO report produced.

### Gate C — Live cohort stage 1

- three diverse fresh releases;
- all applicable Tier-1 destinations;
- zero critical defects;
- strict readback and operator acceptance.

### Gate D — Live cohort stage 2

- ten fresh releases;
- five story types;
- multiple windows;
- correction/update, no-op, provider failure and platform degradation cases;
- zero unresolved critical state;
- operator acceptance.

### Gate E — Learning and product operation

- metrics/community observations bind to exact public objects;
- missing values remain unavailable;
- learning proposals are review-only and versioned;
- UI and status match durable truth;
- operating runbook and incident drills are accepted.

Only after Gates A–E may the repository classify Tier-1 as:

`PASS_CONTENTOPS_TIER1_CONTINUOUS_GENERALIZED_FULL_AUTOMATION_OPERATOR_ACCEPTED`

## 9. Evidence packet requirements

Each soak/cohort acceptance packet must include:

- repository, branch, start/final HEAD and commit messages;
- configuration and policy versions;
- durable schema version;
- supervisor/window ledger;
- work-item and transition summary;
- model invocation summary;
- approval envelope inventory;
- outbox/attempt inventory;
- platform object/readback matrix;
- unknown-write, duplicate and incident register;
- editorial/visual operator findings;
- SLO calculations with denominators;
- unrun tests and missing evidence;
- public-write count;
- exact blockers and next action;
- confirmation that no raw secrets were persisted.

## 10. Anti-gaming rules

- Do not exclude a failed attempt from the denominator because a later retry succeeded.
- Do not count skipped inapplicable destinations as success.
- Do not count provider acknowledgement as strict readback.
- Do not count a repair as first-pass success.
- Do not count mock/synthetic fixtures in live reliability rates.
- Do not convert unavailable metrics to zero.
- Do not reset the cohort to hide a defect; supersede transparently.
- Do not aggregate multiple platform operations into one success row.
- Do not call a small sample statistically conclusive.
- Do not let operator acceptance erase recorded defects; it classifies their final disposition.
