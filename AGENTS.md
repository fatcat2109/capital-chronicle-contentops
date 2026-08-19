# Capital Chronicle ContentOps — Root Repository Contract

Authority date: 2026-08-20
Status: `CURRENT_ROOT_AUTHORITY`
Repository: `fatcat2109/capital-chronicle-contentops`

## 1. Mandatory current read path

For any current ContentOps implementation, audit, task framing, or owner decision, read in this order:

1. `AGENTS.md`
2. `docs/codegraph/INDEX.md`
3. `docs/automation/CONTENTOPS_CURRENT_AUTHORITY_AND_SUPERSESSION_MAP_V1.md`
4. `docs/automation/CONTENTOPS_CAPABILITY_ROUTED_HYBRID_EXECUTION_POLICY_V1.md`
5. `docs/automation/CONTENTOPS_FINAL_PRODUCT_NORTH_STAR_V3.md`
6. `docs/automation/CONTENTOPS_FINAL_PRODUCT_MASTER_PLAN_V3.md`
7. `docs/codegraph/V1_CONTEXT.md` or `docs/codegraph/V2_CONTEXT.md`
8. the current lane pointer
9. the nearest scoped `AGENTS.md`
10. exact implementation, focused tests, and current evidence

Do not route from an old plan, handoff, generated status snapshot, task branch, or chat SHA. CodeGraph is discovery tooling, not product authority. Its recorded `Source HEAD` is the newest commit that changed an indexed source, not necessarily the current branch tip. Use the deterministic generator/check or exact indexed-source bytes/digest to establish freshness.

## 2. Authority and evidence order

Before repo-state claims or task execution, fetch current remote `master` and relevant branch HEADs and inspect current bytes.

Repository/evidence authority:

1. fetched refs, commits, diffs, and exact bytes;
2. committed code, focused tests, accepted evidence, and exact-head CI where applicable;
3. this current authority spine and current lane pointers;
4. runtime/worker evidence for facts that only the runtime can prove;
5. historical docs, project sources, and chat.

Product authority:

1. Jim's latest explicit instruction;
2. this root contract and current root North Star/Master Plan;
3. current owner overlays and lane pointers;
4. older plans/history.

Newer owner direction wins.

## 3. Execution framework

Current engineering execution is `CAPABILITY_ROUTED_HYBRID`:

- `WEB_STATIC` — ChatGPT Web + GitHub for repository-static reasoning, review, bounded edits, authority maintenance, and GitHub operations whose correctness is provable from fresh bytes.
- `WEB_CI` — Web + GitHub + deterministic Actions for bounded implementation safely provable by CI. Normal scope is `NO_SECRET / NO_PUBLIC_WRITE / NO_PRODUCTION_MUTATION`.
- `CODEX_EXECUTION` — use Codex when correctness materially needs a real execution environment, stateful services/database, current network behavior, Windows/browser/runtime inspection, rendered mechanics, or iterative debug feedback.
- `OWNER_GATED_EXTERNAL` — explicit owner scope for secrets/session boundaries, live/public writes, destructive canonical changes, provider/browser publication expansion, rights/legal release, material Core Analyzer numeric-authority change, or equivalent irreversible external action.

Use the cheapest lane that can produce evidence strong enough for the claim. CI PASS never substitutes for production/public/browser/visual/audio truth. Execution routing never grants factual, numeric, permission, credential, destination, rights, or public-write authority.

## 4. One product architecture

Capital Chronicle/Core Analyzer is the intelligence and decision authority. ContentOps is the evidence-governed newsroom, media-production, organic audience-acquisition, distribution, observation, and bounded-learning engine.

Canonical system:

`Capital Chronicle/Core Analyzer intelligence -> explicit publication-safe handoff + contextual discovery -> ContentOps evidence/intelligence fusion -> V1 publishing + V2 media -> observation -> bounded ContentOps learning -> audience/business utility`

Capital Chronicle/Core Analyzer owns proprietary analytical and numeric truth: calculations, scenarios, probabilities, forecasts, regimes, decision briefs, private decision/watch/abstain outputs, paper expressions, realized outcomes, and analytical error attribution.

ContentOps owns discovery, grounded public research, evidence/freshness/permission gates, faithful transformation of explicitly publication-authorized upstream material, writing, SEO, media, distribution, readback/reconciliation, observation, organic growth, and bounded content learning.

ContentOps must never manufacture missing Core Analyzer numbers, calculations, forecasts, probabilities, scenarios, regimes, decisions, positions, or proprietary conclusions.

## 5. Capital Chronicle/Core Analyzer authority classes

Maintain three distinct classes:

1. **Context/discovery only** — arbitrary database rows, historical/entity/event/document matches, candidate snapshots, sidecar/lab outputs, and other read-only discovery material. Useful for investigation; zero public factual/numeric authority by themselves.
2. **Core Analyzer governed internal authority** — validated internal handoffs, decision/forecast/scenario/paper records, point-in-time internal outputs, and governed candidate snapshots. Internal governance is not public permission.
3. **ContentOps publication-authorized CC authority** — exact story-scoped upstream publication material whose contract grants the intended ContentOps consumer/use and preserves binding, permissions, lineage, time semantics, source health/freshness, blockers, and `llm_numeric_authority=false`.

Never upgrade internal/candidate/context material into public authority by model judgment, chart rendering, or adapter logic.

## 6. Current product state

`P0-1` publication-authority classification/use binding, bounded CC context activation, compatibility-state preservation, and the accepted source-reachability corrections are complete on current product lineage. Do not reopen P0-1 merely to increase publication yield.

The V1 canonical Daily App runtime and durable store remain the production authority. The accepted logical-supervisor fix allows the real Windows wrapper/child process tree to count as one logical supervisor while still blocking independent roots.

P0-2 final product acceptance is not yet proven. A real nine-surface publication/readback canary and subsequent unattended/cold-start proof remain required. However the product is **not** globally in a passive “wait and do nothing” state: before the next live canary, V1 must implement and prove the owner-directed growth-first editorial spectrum below.

## 7. V1 North Star — growth-first autonomous newsroom with a hard truth floor

V1 is not a compliance engine that optimizes for abstention. It is Capital Chronicle's autonomous newsroom and low-cost organic growth engine.

The objective is:

`useful truth -> timely/distinctive editorial product -> platform-native distribution -> organic attention -> subscriber/user acquisition -> measured learning`

Truth remains the hard floor. Growth never authorizes fabricated facts, invented Core Analyzer numbers, unsupported allegations, wrong-account writes, blind retries, or permission widening.

### 7.1 Evidence burden follows the claim and editorial mode

Do not impose one blanket evidence burden on every article.

A narrow breaking claim such as “Agency/Company X officially announced Y” may be publishable from one exact, current, authentic official primary source when the article clearly attributes the claim and stays within what that source proves. It does not require a chart, secondary confirmation, CC packet, or observed market reaction merely to report the event.

Broader claims require broader evidence. Causal, quantitative, market-reaction, valuation, forecast, scenario, probability, or proprietary analytical claims require the evidence/authority appropriate to those claims. An official announcement is not evidence for an invented market impact.

If uncertainty remains, say what is known, what is not yet known, and what to watch next.

### 7.2 Quiet day is not automatically a silent day

No-publication remains valid and there is no mandatory post quota. But `NO_PUBLICATION` should be the result of a useful editorial search, not the default response to the absence of a major headline.

Use this editorial ladder when appropriate:

1. `BREAKING_BRIEF`
2. `FOLLOW_UP_UPDATE`
3. `STANDARD_NEWS_ANALYSIS`
4. `CAPITAL_CHRONICLE_VIEW` — explicit house opinion/criticism/contrarian thesis
5. `WHAT_THE_MARKET_IS_MISSING`
6. `EVERGREEN_EXPLAINER`
7. `DATA_OR_DOCUMENT_LENS`
8. `WEEK_AHEAD_OR_WATCH`

On quiet days, lower story materiality or switch content mode; do **not** lower factual truth, attribution, permission, or numeric-authority standards.

Filler means content with no meaningful new information, useful explanation, original perspective, defensible criticism, document/data insight, or reader utility. A strong evergreen explainer or house view is not filler.

### 7.3 Opinion, criticism, and editorial edge are first-class

Capital Chronicle may publish strong, critical, contrarian, and opinionated work to differentiate the brand and drive qualified engagement.

Requirements:

- facts and quoted/attributed claims remain source-bound;
- opinion/inference is distinguishable from verified fact;
- criticism targets decisions, policies, claims, incentives, narratives, products, institutions, companies, public actors, or market consensus with a defensible factual basis;
- provocative framing is allowed when the underlying proposition is supportable;
- no fabricated allegations, deceptive editing, harassment, personal abuse, or unsupported certainty.

The target is **evidence-backed confrontation**, not rage bait.

### 7.4 Growth is a first-class product objective

V1 should optimize, where supportable, for organic reach, meaningful reads, shares/restacks/reposts, saves, qualified discussion, profile visits, follows, free/paid newsletter conversion, canonical clicks, repeat readership, and Capital Chronicle product acquisition/retention.

Platform packages must be native, self-contained, and strong enough to earn attention without relying on a generic “new article” announcement. Engagement may change story priority, framing, timing, packaging, SEO, and creative policy; it may never rewrite facts or Core Analyzer truth.

No fake followers, engagement farms, deceptive astroturfing, mass unsolicited DMs, spam, or unsupported outrage. Public comment/reply automation remains separately owner-gated until exact write/readback scope exists.

## 8. V1 canonical runtime and publication semantics

Preserve one canonical V1 runtime/store/orchestrator/publication coordinator.

Preserve:

- continuous intake, clustering/update chains, selection and abstention;
- latest-web grounded evidence plus bounded CC context;
- one strong editorial worker when warranted;
- deterministic factual/numeric/rights/reader-value gates;
- purposeful media, including zero images when preferable;
- canonical Substack publication;
- exactly eight V1 derivative destinations;
- exact destination/account/object identity;
- strict readback/reconciliation/recovery;
- `UNKNOWN_WRITE`: `STOP RETRY -> READ BACK -> RECONCILE`;
- current kill-switch/autonomy controls;
- Chrome `CapitalChronicleBot` CDP 9222 for ingestion only;
- Edge `contentops-social-main` CDP 9223 for publication/media/readback and explicitly authorized observation only;
- LinkedIn official member API where current authority/code uses it;
- canonical V5 UI under `ui/contentops_v5/`.

### 8.1 Canonical-first distribution rule

For a future owner-authorized V1 publication, a derivative destination that is temporarily unavailable must not automatically destroy the freshness/value of an otherwise qualified canonical article.

Target semantics:

`article truth/readiness gate -> canonical Substack readiness -> canonical publish/readback -> exactly eight derivative packages attempted independently under exact destination readiness -> destination-local hold/recovery -> full reconciliation`

A destination-local failure cannot authorize blind retry and cannot erase canonical truth. Final nine-surface canary acceptance still requires exact evidence that the canonical article and all required derivatives were eventually attempted/read back/reconciled with `UNKNOWN_WRITE=0` under the accepted canary contract.

This is product direction only; it grants no live/public-write authority by itself.

## 9. Current quality-probation state

Exactly four existing native V1 newsroom tasks remain `PAUSED` until:

1. growth-first editorial behavior is implemented and zero-write replayed;
2. Jim/ChatGPT accepts the editorial outputs;
3. one real owner-authorized V1 canary completes canonical publication, eight derivatives, readback/reconciliation, and actual-artifact review.

Do not create a fifth scheduler task. Do not repeatedly fire manual opportunities merely to manufacture a canary.

The always-on FDA-G runtime may continue low-cost calendar-time soak, ingestion, recovery/readback housekeeping, supported observation, and state maintenance while the four editorial tasks remain paused.

## 10. V2

V2 remains an isolated retention-native media factory. It may consume qualified story/evidence authority and publication-authorized chart/data inputs, but it must never mutate/reset V1 runtime, store, scheduler, browser, or publication authority.

Preserve `CONCRETE_FIRST_ABSTRACT_SECOND`, rights-safe real/contextual media and primary documents, source-backed charts/maps/data, professional audio, deterministic QA, actual-media review, and bounded repair/recovery.

V2 currently has zero public-write authority.

## 11. Observation and learning

Observation records supported reality. Missing metrics are `UNAVAILABLE`/`UNKNOWN`, never fabricated zeroes.

Learning may change ContentOps priority, timing recommendations, story-mode mix, headline/framing style, SEO, hooks, asset selection, package form, and bounded creative policy. It may never change facts, evidence permissions, Core Analyzer output, probabilities, scenarios, forecasts, regimes, decisions, paper records, realized outcomes, destination identity, rights, safety gates, or public-write authority.

## 12. Change discipline

Prefer one heavy bounded end-to-end capability slice over ceremony or horizontal infrastructure.

Every implementation task must state the user problem, capability/demo, measurable utility delta, simplest viable approach, exact write/network/browser/publication scope, focused tests plus one end-to-end smoke/demo, cost/runtime evidence where material, hard stops, and exact next blocker.

Stage explicit paths only. Never `git add .` or `git add -A`. Never force-push. Never push/merge `master` without explicit owner authorization. Preserve unrelated work.

## 13. Hard stops

Stop on:

- secret/session/token/cookie/private-key exposure;
- fabricated core facts or Core Analyzer numeric/analytical truth;
- promotion of internal/candidate Analyzer material into public authority without explicit publication-safe permission;
- unauthorized or wrong-account public write;
- destructive production-store or upstream Capital Chronicle mutation;
- protected release/tag mutation;
- unresolved `UNKNOWN_WRITE` or public-object ambiguity;
- irreconcilable ref conflict;
- required credential/reauth/operator input unavailable for an explicitly authorized action.

Do not stop merely for historical noise, stale docs, unrelated dirty files, absent CI, pre-existing failures, or reversible mechanics.

Protected `v1.0` remains immutable at `6983bfb3ef300414b744f3f8f97ca81ff699348b`.

## 14. Visual/media acceptance

For UI, video, or audio acceptance, inspect the real rendered artifact. Tests and builder judgment prove mechanics, not viewer-facing quality.
