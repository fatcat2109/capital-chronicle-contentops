# Capital Chronicle ContentOps — Final Daily App V1 Master Plan

Authority date: 2026-08-20
Authority ID: `CONTENTOPS_FINAL_DAILY_APP_V1_MASTER_PLAN`
Status: `OWNER_APPROVED_CURRENT_EXECUTION_PLAN`

Root authority:

- `docs/automation/CONTENTOPS_FINAL_PRODUCT_NORTH_STAR_V3.md`
- `docs/automation/CONTENTOPS_FINAL_PRODUCT_MASTER_PLAN_V3.md`
- `docs/automation/CONTENTOPS_FINAL_DAILY_APP_V1_CURRENT_EXECUTION_POINTER_V3.md`

This plan provides V1 implementation detail only where compatible with the current root spine and pointer.

## 0. Final V1 objective

Jim should be able to launch one ContentOps Daily App, leave it running, and rely on it to perform routine newsroom, distribution, recovery, observation, and bounded learning work without manually driving each cycle.

The final product must:

1. stay alive continuously with low-cost supervision;
2. ingest current headline/event evidence and maintain bounded material-event wake eligibility;
3. maintain durable state, recovery, and public-object certainty;
4. select the best useful editorial mode or abstain;
5. obtain exact claim-appropriate evidence;
6. produce strong article/SEO/media/native packages;
7. publish canonical Substack under exact authority;
8. distribute exactly eight derivative packages with destination-local recovery;
9. read back/reconcile every attempted public object;
10. observe supported audience/search/subscriber/product outcomes;
11. learn bounded story mix, timing, framing, SEO, and packaging policy;
12. survive restart/cold-start without duplicate cycles, duplicate material-event wakes, or duplicate public objects;
13. expose truthful current state in canonical V5.

No publication minimum exists.

## 1. Current accepted baseline

P0-1/P0-1B authority/context/source work is accepted. Do not reopen it merely to improve yield.

The canonical Daily App supervisor/orchestrator/store/publication coordinator exists and has an accepted logical-supervisor process-tree correction for the real Windows venv wrapper/child topology.

Latest runtime evidence reports FDA-G soak active, heartbeat/ingestion healthy, `UNKNOWN_WRITE=0`, and the four existing editorial tasks paused. Re-observe runtime truth when required.

Preserve:

- `live_contentops.production_orchestrator_v1.ContentOpsProductionOrchestrator`;
- `live_contentops._eight_platform_substack_first_pipeline_impl_v1`;
- `live_contentops.eight_platform_substack_first_pipeline_v1`;
- `live_contentops.durable_operational_store_v1.py`;
- `live_contentops.publication_coordinator_v1.DurablePublicationCoordinator`;
- `ui/contentops_v5/`.

No new parallel newsroom, evidence authority, scheduler, state store, publisher, provider gateway, or control plane.

## 2. Current implementation task — growth-first vertical slice

Implement through the canonical supervisor/newsroom path:

`P0-G1 + P0-G2 — GROWTH-FIRST EDITORIAL SPECTRUM + BOUNDED MATERIAL-EVENT WAKE + CANONICAL-FIRST DISTRIBUTION`

### 2.1 Extend/reconcile article modes

Canonical modes:

- `BREAKING_BRIEF`
- `FOLLOW_UP_UPDATE`
- `STANDARD_NEWS_ANALYSIS`
- `CAPITAL_CHRONICLE_VIEW`
- `WHAT_THE_MARKET_IS_MISSING`
- `EVERGREEN_EXPLAINER`
- `DATA_OR_DOCUMENT_LENS`
- `WEEK_AHEAD_OR_WATCH`

Prefer reuse/extension of existing story type/article mode/capability registry. Do not build a second selector or evidence engine.

### 2.2 Evidence contract

One deterministic mapping should resolve:

`story type + editorial mode + claim class -> required capabilities/authority`

Required behavior:

- exact official-primary source can satisfy narrow attributed breaking facts when directly authoritative;
- issuer/party-authored official source establishes the existence and exact contents of its own announcement/filing/order/statement but does not automatically independently prove disputed third-party allegations, misconduct, causality, or future outcomes;
- broader factual updates require exact current source-backed delta;
- analytical/causal/market-impact claims require stronger public evidence;
- proprietary scenarios/probabilities/forecasts/regimes/numeric conclusions require exact publication-authorized CC material;
- opinion/critical articles require source-bound factual premises and clear opinion/inference separation.

Keep existing fail-closed behavior for unsupported claims. Do not fail an entire narrow breaking brief merely because data for a broader analysis is absent.

### 2.3 Quiet-day editorial ladder

When no high-materiality breaking/analysis candidate qualifies, evaluate useful lower-rung content from current universe, published memory, official documents, and bounded context:

`follow-up -> Capital Chronicle View -> what-market-misses -> explainer -> document/data lens -> week-ahead/watch`

No generic content farm behavior. Every selected piece still needs current relevance and reader utility.

### 2.4 House-view editorial contract

The editorial worker may make a strong judgment about policy, management narrative, market consensus, incentives, or framing when factual premises are grounded.

Desired output:

- thesis early;
- clear target of critique/disagreement;
- mechanism/evidence;
- uncertainty/counter-case where material;
- memorable headline/lede;
- no weak neutralizing prose when a clear supported view exists.

ContentOps may make clearly labeled qualitative editorial inference from accepted public evidence. That is ContentOps editorial judgment, not Core Analyzer authority. It must not be represented as Core Analyzer output or used to invent proprietary numeric/forecast/probability/scenario/regime/valuation/decision truth.

Material allegations of fraud, crime, deception, corruption, or comparable misconduct require evidence proportional to the allegation and are not authorized merely because the piece is opinion/house view.

The model receives zero factual/numeric/permission/public-write authority.

### 2.5 Growth-aware priority and package intent

Use supported growth signals only as priority/packaging inputs, not truth:

- timeliness and novelty;
- reader relevance;
- defensible controversy/contrarian value;
- useful explanation potential;
- share/discussion potential;
- search/evergreen utility;
- subscriber/product relevance;
- portfolio diversity;
- evidence readiness;
- bounded cost.

Generate destination-native package intents rather than blind truncation.

Public reply/comment automation remains out of scope.

### 2.6 Bounded material-event wake mechanics

Reuse the existing Daily App supervisor and existing material-event/update-chain state. Do not create a fifth scheduled task or a second scheduler.

Implement/prove under `NO_PUBLIC_WRITE`/shadow validation:

- one genuinely material fresh event may create one editorial opportunity outside routine windows;
- stable trigger identity/idempotency prevents duplicate wakes;
- duplicate/update-chain state and minimum spacing/saturation are honored;
- the wake enters the same canonical selection/evidence/article/package path as a scheduled opportunity;
- if the story/gates do not clear, the wake may safely abstain;
- no live/public-write wake is authorized before the accepted real canary.

After the owner-accepted canary, this bounded supervisor-owned wake becomes part of final V1 operating behavior under the accepted autonomy/public-write scope.

## 3. Canonical-first derivative lifecycle

Update/reconcile current publication planning so derivative-local availability does not act as a blanket canonical veto.

Future owner-authorized lifecycle:

1. recover/reconcile prior obligations and require `UNKNOWN_WRITE=0`;
2. article factual/numeric/rights/reader-value PASS;
3. exact canonical Substack readiness and identity;
4. canonical Substack dispatch/readback;
5. exactly eight derivative packages;
6. each derivative attempted only when its exact destination readiness/identity permits;
7. unavailable/failed destination becomes durable destination-local hold/recovery;
8. other ready derivatives continue;
9. every attempted public object is read back/reconciled;
10. ambiguous write stops retries until readback/reconciliation.

Do not erase canonical truth because a derivative fails. Do not retry canonical publication because a derivative fails.

Final real canary acceptance still requires eventual exact proof of all nine required surfaces and `UNKNOWN_WRITE=0`.

Implementation and replay remain `NO_PUBLIC_WRITE` until a separate explicit owner grant.

## 4. Zero-write replay package

After implementation, run one real or controlled current-state `NO_PUBLIC_WRITE` replay covering at least four cases.

### Case A — official-primary breaking + material-event wake

Prove:

- one exact official primary source directly establishes the event;
- narrow attributed facts pass;
- absent market data/secondary article does not block the narrow brief;
- issuer/party-authored assertions stay correctly attributed where independent proof is absent;
- no unsupported market-reaction/causal/numeric claims appear;
- one bounded material-event trigger can create the editorial opportunity with stable identity, spacing/dedupe checks, and zero duplicate wake;
- public write count remains zero.

### Case B — normal analysis

Prove stronger evidence is required for broader analytical claims and exact publication-authorized CC material is used only when available/authorized.

### Case C — quiet day

Prove the selector tries a useful lower-rung mode and either produces real reader value or truthfully returns `NO_PUBLICATION` after the ladder.

### Case D — critical/opinion

Prove strong house view, source-bound factual premises, clear fact/opinion separation, qualitative editorial inference stays distinct from Core Analyzer authority, and no fabricated allegation.

For every case record:

- candidate/mode selection rationale;
- claim/evidence capability profile;
- accepted source records;
- CC authority class/use/zero-use;
- article/headline;
- native package intents;
- deterministic/model path and cost;
- public write count = 0.

Jim/ChatGPT must review the actual outputs.

## 5. Real canary after replay acceptance

Only after owner acceptance of zero-write editorial outputs:

1. re-observe canonical runtime and unresolved obligations;
2. require `UNKNOWN_WRITE=0`;
3. ingest current universe;
4. select a qualified story/mode under new policy;
5. resolve exact public evidence and publication-authorized CC material if applicable;
6. invoke one fresh bounded XHIGH editorial worker only when warranted;
7. validate article/media/SEO/packages;
8. verify exact Substack identity/readiness;
9. require new explicit `OWNER_GATED_EXTERNAL` authorization;
10. canonical Substack publish/readback;
11. exactly eight derivative attempts under exact destination identity/readiness;
12. destination-local recovery as needed;
13. strict readback/reconciliation and `UNKNOWN_WRITE=0`;
14. Jim/ChatGPT inspect actual public artifacts.

A valid `NO_PUBLICATION` remains safe but is not canary acceptance.

## 6. Four-task + material-event unattended/cold-start proof

After accepted canary:

- enable only the four existing V1 quality-probation scheduled tasks;
- activate the bounded material-event wake through the existing Daily App supervisor under accepted autonomy/public-write scope;
- no fifth scheduled task and no second scheduler;
- prove calendar-time execution, legitimate abstentions, varied useful modes, restart/cold-start behavior, recovery, no duplicate editorial opportunities or public objects, bounded cost, and stable FDA-G supervision;
- prove at least one material-event trigger/no-op or trigger/execution path with stable identity and no duplicate wake.

## 7. Performance and bounded growth learning

Observe only supported metrics and exact public-object identities.

Useful signals include platform-native reach, meaningful reads/completion, shares, saves, qualified discussion, profile visits/follows, canonical clicks, newsletter subscriptions/referrals, search, repeat readership, and Capital Chronicle signup/product/paid/retained linkage where supported.

Learning may alter story-mode mix, priority, timing recommendations, framing, SEO, assets, packages, and portfolio diversity. It may never alter facts, source/evidence authority, Core Analyzer output, numeric truth, permissions, rights, destination identity, KILL_SWITCH, or public-write authority.

The current nine-surface set is the P0 baseline. After stable public samples exist, additional legitimate low-cost discovery/growth surfaces may be evaluated only under exact owner-approved identity, permission, write/readback, anti-spam/rate, and measurement scope and only when measured audience/business utility justifies them.

## 8. V5 acceptance

Canonical UI remains `ui/contentops_v5/`.

Before final V1 acceptance:

- reproduce the currently reported optional `UI_BUILD_EXIT_1` if still present;
- correct any real build/runtime defect through the canonical UI path;
- show truthful runtime/editorial/evidence/authority/publication/recovery/performance/learning state;
- capture fresh screenshots;
- complete independent ChatGPT visual review.

Do not build a second dashboard.

## 9. Browser/runtime authority

Chrome `CapitalChronicleBot` CDP 9222: ingestion only.

Edge `contentops-social-main` CDP 9223: publication/media/readback and explicitly authorized observation only.

Never inspect/export cookies, tokens, local/session storage, credentials, or browser-session databases.

## 10. Hard stops

Stop on secret/session exposure, fabricated core/numeric truth, unauthorized/wrong-account public write, destructive production-state mutation, protected release mutation, unresolved `UNKNOWN_WRITE`, irreconcilable ref conflict, or required credential/reauth/operator input unavailable for an authorized action.

Do not stop for stale history, unrelated dirty files, absent CI, pre-existing failures, or reversible mechanics.

Protected `v1.0` remains immutable at `6983bfb3ef300414b744f3f8f97ca81ff699348b`.

## 11. Current exact next task

`TASK_V1_GROWTH_FIRST_EDITORIAL_SPECTRUM_BOUNDED_MATERIAL_EVENT_WAKE_AND_CANONICAL_FIRST_DISTRIBUTION_VERTICAL_SLICE_V1`

It should be one heavy bounded implementation through the existing canonical V1 supervisor/selection/evidence/article/package/publication path with focused tests plus a zero-public-write end-to-end replay. If implementation requires Windows/runtime truth, route those mechanics to `CODEX_EXECUTION`; deterministic source/contract work may remain `WEB_CI` where CI can prove it.
