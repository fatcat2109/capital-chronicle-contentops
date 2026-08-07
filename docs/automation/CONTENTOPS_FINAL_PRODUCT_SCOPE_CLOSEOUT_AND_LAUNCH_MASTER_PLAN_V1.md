# Capital Chronicle ContentOps — Final Product Scope, Build Closeout, and Launch Master Plan V1

Authority date: 2026-08-06

Repository: `fatcat2109/capital-chronicle-contentops`

Target base: remote `master` at `6b6f8718532a4c3f077b09e14f3ca9a4083d4734`

Plan authoring base: `c87e338f25922f4d03454ba199139353ca7198ff`

Document role: current product-direction and final-build plan. This document supersedes older product-direction text wherever older plans assign authoritative microeconomic, macroeconomic, global-macro, scenario, model-calculation, Bayesian, forecasting, or numeric-analysis ownership to ContentOps.

Owner-approval state:

`CONTENTOPS_NEWSROOM_AND_CONTENT_FACTORY_SCOPE_OWNER_APPROVED`

Jim approved this plan on 2026-08-06. Wave 02 entered `master` after the authoring base, so current accepted Wave 02 repo facts govern wherever this plan still describes Wave 02 as an unmerged candidate.

## 0. Owner decision

Capital Chronicle and ContentOps are separate products with a strict contract.

**Capital Chronicle main project owns intelligence.** It owns daily analysis, microeconomic analysis, macroeconomic analysis, global-macro analysis, scenario construction, deterministic model calculations, Bayesian cases and updates, probabilistic views, assumptions, invalidation conditions, numeric truth, forecast evaluation, realized-outcome comparison, and model-error attribution.

**ContentOps owns the newsroom and content factory.** It owns news/headline intake, breaking-news and business-news discovery, event clustering, duplicate/update-chain handling, evidence and permission gates, editorial prioritization, content portfolio selection, article mode and framing, writing, editing, SEO, images, charts, platform-native packages, publication control, readback, reconciliation, content-performance measurement, and packaging/selection learning.

ContentOps may explain, adapt, summarize, visualize, distribute, and measure Capital Chronicle analysis. ContentOps must not independently originate authoritative economic scenarios, Bayesian probabilities, model outputs, numeric forecasts, market regimes, or analytical truth.

## 1. Product definition

Capital Chronicle ContentOps is an AI-native autonomous newsroom and content factory for serious business, financial, economic, political, regulatory, geopolitical, corporate, and physical-event content.

The product has two governed input lanes.

### 1.1 Newsroom lane

ContentOps directly processes a governed news and headline universe:

```text
headlines and primary-source events
→ normalize and deduplicate
→ cluster stories and update chains
→ verify source, permission, freshness, and material delta
→ rank editorial value and audience utility
→ choose story, hold, reject, or publish nothing
→ report, explain, edit, optimize, visualize, package, and distribute
```

This lane supports factual reporting and bounded editorial explanation. It does not grant ContentOps authority to invent numeric truth, economic model outputs, or probabilistic macro conclusions.

### 1.2 Capital Chronicle analysis lane

ContentOps consumes governed analysis packets produced by the Capital Chronicle main project:

```text
Capital Chronicle analysis and model outputs
→ exact packet/lineage/permission validation
→ choose content mode, audience, framing, and search intent
→ transform into article, report, newsletter, visual, and platform packages
→ review against source and analytical authority
→ publish under active mode
→ read back, reconcile, and measure content performance
```

ContentOps preserves the supplied calculations, probabilities, assumptions, limitations, confidence, and invalidation conditions. Any analytical change requires a new Capital Chronicle packet.

## 2. Explicit non-goals

ContentOps is not and must not become:

- a second Capital Chronicle analyzer;
- a parallel numeric database;
- an independent microeconomic or macroeconomic model engine;
- a scenario-generation authority;
- a Bayesian probability engine;
- a forecasting or market-regime authority;
- a broker, signal, advisory, or portfolio-management product;
- a generic social scheduler that manufactures filler;
- a mandatory-volume publishing bot;
- a collection of platform-specific scripts without one canonical state and readback path.

The final build must remove or quarantine any implied ownership that conflicts with these boundaries. Existing code that performs deterministic formatting, chart calculation from already-authorized inputs, content scoring, or editorial ranking may remain. It must not be relabeled as Capital Chronicle analytical authority.

## 3. Current verified baseline

The immutable `v1.0` release proves one bounded real production cycle:

- one exact Treasury story with story-scoped publication authority;
- canonical Substack article;
- eight Tier-1 text/image derivatives;
- visual generation;
- provider/public readback;
- bounded repair;
- operator acceptance;
- frozen release tag at `6983bfb3ef300414b744f3f8f97ca81ff699348b`.

Wave 01 established one canonical production-orchestrator boundary on `master`.

Wave 02 — the durable operational store and canonical state machine — is merged into `master` and accepted as the minimum durable prerequisite under `COMPLETE_ACCEPTED_AND_MERGED_AS_MINIMUM_DURABLE_PREREQUISITE`.

The current product has strong evidence, editorial, packaging, distribution, and readback foundations. It has not yet proven a repeated fresh, diversified, autonomous newsroom loop.

## 4. Operating modes

The final product supports four exact modes.

### `AUTONOMOUS_DEFAULT`

The product default. The system selects, produces, reviews, and performs public writes only when all exact deterministic evidence, permission, freshness, policy, approval-policy, platform, and readback requirements pass. Any unknown or missing authority fails closed.

### `SUPERVISED_OPERATOR_GATE`

Optional operator toggle. The system completes all safe production work and pauses before public write for Jim's exact package decision.

### `SHADOW_ONLY`

The full newsroom and production loop runs with zero public writes. It produces the same decisions, packages, evidence, and reconciliation simulation needed for evaluation.

### `KILL_SWITCH`

Blocks new public writes while allowing public readback, reconciliation, incident handling, and recovery of known objects.

No legacy document may preserve mandatory human approval as the universal product default merely because earlier releases were supervised.

## 5. Content universe and diversification

The final newsroom must not collapse into FX and commodities. It must support a broad, configurable business and public-affairs universe.

### 5.1 Required content domains

1. **U.S. equities and Big Tech**
   - earnings and guidance;
   - SEC filings;
   - major product, capex, AI, cloud, semiconductor, antitrust, and labor developments;
   - market-moving corporate events;
   - material management or capital-allocation changes.

2. **Sector and industry trends**
   - semiconductors;
   - software and cloud;
   - banking and financials;
   - energy and utilities;
   - industrials and infrastructure;
   - healthcare and biotech;
   - consumer and retail;
   - real estate;
   - autos and transportation;
   - defense and aerospace.

3. **Economic releases**
   - inflation;
   - employment;
   - growth;
   - consumption;
   - production;
   - housing;
   - surveys;
   - fiscal and trade releases.

   ContentOps reports and packages the release. Capital Chronicle owns deeper analytical calculations, scenarios, and Bayesian interpretation.

4. **Political and policy news**
   - elections and government formation;
   - fiscal policy;
   - industrial policy;
   - tax policy;
   - trade policy;
   - sanctions;
   - major executive, legislative, and agency actions.

   Political coverage must remain factual, sourced, calibrated, and separated from partisan persuasion.

5. **Central banks, rates, credit, and liquidity**
   - decisions, minutes, speeches, operations, and official documents;
   - sovereign issuance and material funding developments;
   - credit events and market-structure changes.

6. **FX, commodities, energy, and materials**
   - currency policy and material market events;
   - oil, gas, power, metals, agriculture, and critical minerals;
   - physical supply disruptions and official production/inventory data.

7. **Geopolitics, trade, and supply chains**
   - conflict and security developments with economic relevance;
   - export controls;
   - shipping and logistics;
   - sanctions and trade restrictions;
   - infrastructure and physical bottlenecks.

8. **Regulation, law, and corporate governance**
   - antitrust;
   - securities regulation;
   - competition and consumer rules;
   - material litigation and court decisions;
   - corporate-governance events.

9. **Global business and corporate events**
   - earnings and filings outside the U.S.;
   - M&A;
   - restructurings;
   - bankruptcies;
   - capital raises;
   - strategic investments;
   - major operational incidents.

10. **Capital Chronicle analysis products**
    - daily analysis;
    - microeconomic reports;
    - macroeconomic reports;
    - global-macro reports;
    - scenario and Bayesian-case updates;
    - weekly and monthly analytical reviews;
    - model- or chart-led explainers.

### 5.2 Diversification rules

Diversification is a portfolio objective, not a quota that forces weak stories.

The assignment engine must apply configurable penalties for:

- repeated entities;
- repeated asset classes;
- repeated sectors;
- repeated source families;
- repeated geography;
- repeated content modes;
- repeated visual templates;
- duplicate or low-delta update chains;
- concentration in FX, commodities, or any single domain;
- excessive short-lived outrage or partisan conflict.

A rolling portfolio report must show domain, entity, geography, story mode, source family, visual type, and platform concentration. `NO_PUBLICATION` remains valid when diversity can only be achieved by lowering evidence or utility standards.

## 6. News and headline intelligence

### 6.1 Intake

The product should use governed Capital Chronicle headline/evidence outputs first. Approved official/public/free sources and trusted alternatives may be added only when they directly improve current product capability and comply with source, permission, request-budget, timeout, and safe-raw policies.

Required intake outcomes:

- accepted candidate;
- context-only candidate;
- duplicate;
- correction;
- incremental update;
- material update;
- contradiction;
- stale or superseded;
- permission blocked;
- evidence incomplete;
- no-publication candidate.

### 6.2 Clustering and update chains

The product must identify one underlying event across multiple headlines and distinguish:

- duplicate reporting;
- official confirmation;
- correction;
- new primary evidence;
- incremental update;
- material change;
- reversal or contradiction;
- genuinely new phase.

Every selected story binds `story_cluster_id`, `update_chain_id`, `candidate_id`, decision cutoff, and prior related outputs. This prevents repetitive publication and supports accurate breaking-news updates.

### 6.3 Breaking news

Breaking status is a deterministic editorial classification based on recency, materiality, primary-source evidence, affected breadth, and update magnitude. Source prestige alone cannot create a breaking classification.

Breaking-news production must support:

- fast factual brief;
- explicit known/unknown separation;
- primary-source links;
- no unsupported market-reaction claim;
- later update or correction linkage;
- automatic expiry of stale breaking labels;
- preemption only when the materiality delta exceeds a configured threshold.

### 6.4 Assignment and no-publication

The system ranks only candidates that pass hard evidence and permission gates. Ranking dimensions include materiality, freshness, source authority, surprise, affected breadth, audience relevance, novelty, update magnitude, durability, original reporting/explanation potential, visual feasibility, SEO opportunity, overclaiming risk, and portfolio concentration.

Valid outcomes:

- `PUBLISH_BREAKING_NEWS`;
- `PUBLISH_STRAIGHT_NEWS`;
- `PUBLISH_BUSINESS_ANALYSIS_FROM_AUTHORIZED_INPUTS`;
- `PUBLISH_CAPITAL_CHRONICLE_REPORT_TRANSFORMATION`;
- `HOLD_FOR_PRIMARY_SOURCE`;
- `HOLD_FOR_CAPITAL_CHRONICLE_ANALYSIS`;
- `DEFER_FOR_PORTFOLIO_BALANCE`;
- `DUPLICATE_OR_LOW_DELTA`;
- `REJECT_UNSUPPORTED`;
- `NO_PUBLICATION_THRESHOLD_NOT_MET`.

## 7. Capital Chronicle analysis contract

ContentOps must consume a versioned analysis packet rather than prose copied from an unbound report.

Minimum packet requirements:

- packet ID and schema version;
- producer repository and commit;
- analysis type;
- decision or analysis timestamp;
- source and evidence references;
- authorized claims;
- deterministic calculations and chart-ready series;
- scenario definitions and probabilities when applicable;
- Bayesian prior, evidence update, likelihood assumptions, and posterior when applicable;
- confidence and limitations;
- confirmation and invalidation conditions;
- public-use permissions;
- citation map;
- analytical mode and intended audience;
- logical and byte hashes.

ContentOps may change presentation but not analytical substance. It may create separate audience versions only when all versions bind the same authorized analytical packet or an explicitly narrower subset.

## 8. Editorial system

### 8.1 Content modes

The final registry must support at least:

- breaking-news alert;
- straight-news report;
- business-news brief;
- earnings or filing report;
- economic-release report;
- policy or political update;
- regulatory/legal report;
- sector-trend article;
- geopolitical or supply-chain report;
- rapid explainer;
- deep explainer;
- Capital Chronicle daily-analysis article;
- microeconomic report transformation;
- macroeconomic report transformation;
- global-macro report transformation;
- scenario/Bayesian update transformation;
- weekly roundup;
- chart-led article;
- newsletter;
- platform-native short form.

No universal fallback to generic analysis is allowed.

### 8.2 Required editorial stages

Use the existing logical newsroom roles, batched when efficient:

1. assignment editor;
2. evidence and authority planner;
3. reporter/writer;
4. quantitative/analytical fidelity editor;
5. visual editor;
6. copy and structure editor;
7. SEO and platform editor;
8. independent adversarial reviewer.

The quantitative editor verifies fidelity to authorized numbers and Capital Chronicle outputs. It does not create new analysis.

### 8.3 Reader utility

Every publishable package must answer the relevant subset of:

- what happened;
- what is new;
- why it matters;
- who or what is affected;
- what evidence supports the claim;
- what remains unknown;
- what to watch next;
- how this differs from the prior update;
- where Capital Chronicle analysis adds value.

No internal workflow vocabulary, ungrounded certainty, repetitive filler, fabricated quotations, invented consensus, signal language, or advice language is allowed.

## 9. SEO system

SEO is a first-class production capability, not a final checklist score.

### 9.1 Search-intent selection

For every canonical long-form article, record:

- primary search intent;
- secondary intents;
- target reader;
- query or keyword cluster;
- news-versus-evergreen balance;
- competitive differentiation;
- canonical angle;
- expected search longevity;
- update strategy.

SEO must not distort factual framing or inflate certainty.

### 9.2 On-page production

Required outputs where applicable:

- source-calibrated SEO title;
- reader-facing headline;
- slug;
- meta description;
- H1/H2 structure;
- concise lede and answer-first summary;
- internal-link suggestions;
- external primary-source citations;
- image filenames, captions, and alt text;
- chart titles and descriptive text;
- structured-data proposal when supported;
- canonical URL and update timestamp;
- social preview title and description.

### 9.3 SEO quality and measurement

Deterministic hygiene checks remain useful but must not be called observed SEO success. The product must later ingest available Search Console and first-party analytics metrics such as impressions, clicks, CTR, queries, average position, landing-page engagement, return readership, and subscriber conversion.

Learning may improve angle, timing, structure, headline, internal links, and content refresh decisions. It may not alter source authority, evidence classification, or Capital Chronicle analytical truth.

## 10. Image system

### 10.1 Image strategy

Every package must select a visual strategy based on story type and platform capability:

- official document excerpt;
- official or licensed photograph;
- contextual map;
- company/product/infrastructure image;
- annotated timeline;
- comparison card;
- data chart;
- generated editorial illustration;
- text-only where visuals do not add value or rights are unclear.

The system must avoid using three cosmetic transformations of one image as visual diversity.

### 10.2 Rights, provenance, and safety

Every external image requires source page, owner/publisher, date/context, rights or reuse status, dimensions, recency, relevance, duplicate/perceptual hash, and manipulation/logo/avatar/thumbnail checks.

Generated images require prompt, model/version, source bindings, transformation metadata, disclosure policy where applicable, and final hash. Images must not fabricate a real event, document, person, place, market move, or official scene.

### 10.3 Platform adaptation

Image packages must include the required aspect ratios, crops, safe areas, text-density limits, file metadata, captions, alt text, and platform binding. A crop or derivative may not silently remove material chart labels, source notes, or uncertainty language.

## 11. Chart system

Charts must be deterministic visualizations of authorized data, not analytical invention by ContentOps.

Permitted chart inputs:

- Capital Chronicle chart-ready series and calculations;
- approved official/public data with explicit authority and method;
- exact values already authorized in the story evidence packet.

Every chart records:

- metric definition;
- source and series identifiers;
- units;
- observation and release times;
- frequency;
- sample period;
- transformations;
- seasonal adjustment;
- annualization;
- revision status;
- partial-period status;
- missing-data handling;
- chart-generation version;
- source note;
- final hash.

Required chart classes include time series, indexed comparison, contribution/decomposition, sector comparison, earnings/filing comparison, event timeline, policy-rate path from authorized inputs, and scenario comparison from Capital Chronicle packets.

ContentOps may choose the clearest chart and compute display transformations explicitly authorized by the packet. It may not create a new forecast, probability, or macro model to fill a chart.

## 12. Platform and publication product

Tier-1 text/image destinations remain:

- Substack;
- Telegram;
- Discord;
- X;
- LinkedIn;
- Facebook Page;
- Instagram Business;
- Threads;
- YouTube Community.

Each platform package must be native rather than a truncated copy. It must bind story identity, content version, exact claims, visual assets, citations, payload hash, target account/persona, and readback policy.

TikTok, YouTube long-form, and YouTube Shorts remain separate Tier-2 media modes and do not block final Tier-1 launch.

Public writes require the active operating mode and exact deterministic gates. Unknown writes are reconciled before retry. Known successful objects are never duplicated merely because a local process lost state.

## 13. Performance and learning

The learning loop optimizes qualified engagement and production utility:

- meaningful reads;
- completion;
- shares;
- saves;
- replies and qualified discussion;
- canonical-article clicks;
- subscriber conversion;
- search demand and longevity;
- repeat readership;
- operator time saved;
- cost per accepted package;
- revision and defect rates.

Penalize clickbait, repetition, concentration, weak evidence, overclaim, low-delta updates, and short-lived outrage.

Store platform-native metrics without pretending they are directly comparable. Normalize only through explicit formulas and confidence rules. Small samples create observations, not major automated policy changes.

## 14. Canonical UI and design system

`ui/contentops_v5/` remains the canonical UI unless a later accepted task supersedes it.

The UI must provide:

- current operating mode and kill switch;
- intake windows and candidate clusters;
- breaking-news and update-chain state;
- story ranking and portfolio concentration;
- Capital Chronicle packet fidelity;
- article, SEO, image, chart, and platform package review;
- approval-policy and publication gates;
- outbox/readback/reconciliation status;
- performance and learning observations;
- incidents and exact recovery actions.

The design system must use semantic tokens and reusable components, preserve evidence and provenance, separate current/historical/reference-only states, and avoid generic SaaS, cyberpunk, or raw table-dump presentation. Visible UI acceptance requires fresh browser screenshots and independent visual review.

## 15. Final build strategy

The remaining program must be smaller than the previous horizontal hardening roadmap. Reuse accepted components. Build only capabilities that directly close the two input lanes and launch the product.

### Work package A — Authority and current-state reconciliation

Status: `COMPLETE_OWNER_APPROVED`

Purpose: make the repository agree on the product boundary, operating modes, accepted baseline, current Wave 02 truth, and the routed next task.

Deliverables:

- this master plan;
- final-product scope overlay;
- current builder/context pointers;
- one exact routed next task;
- no runtime change.

Exit: satisfied. Jim approved the product direction on 2026-08-06 and the GitHub branch/commit is auditable.

### Work package B — Minimum durable execution prerequisite

Status: `COMPLETE_ACCEPTED_AND_MERGED_AS_MINIMUM_DURABLE_PREREQUISITE`

Purpose: retain only the minimum durable state capability needed by the final vertical slice.

Outcome: the Wave 02 durable operational store and canonical state machine is merged into `master` and accepted as the minimum durable prerequisite. It supplies restart-safe local work state, append-only transitions, and exact redacted evidence export to the newsroom vertical slice.

Standing constraints:

- do not restart a broad state-platform program;
- do not redesign, re-audit, or re-merge Wave 02;
- do not add approval/outbox/scheduler layers unless the vertical slice directly needs them.

Exit: satisfied.

### Work package C — Dual-lane CORE V0 shadow newsroom

Status: `COMPLETE_ACCEPTED_AND_MERGED_WITH_CAVEAT`

Exact task:

`TASK_CONTENTOPS_DUAL_LANE_CORE_V0_SHADOW_NEWSROOM_V1`

Mode:

`SHADOW_ONLY`

Purpose: prove the final product's core value in `SHADOW_ONLY`.

One bounded implementation must demonstrate:

1. a daily governed headline universe;
2. duplicate and update-chain clustering;
3. diversified ranking across business/news domains;
4. selection of one best news story or explicit abstention;
5. intake of one governed Capital Chronicle analysis packet;
6. production of one news-led package and one Capital-Chronicle-led package;
7. article, SEO, image/chart, and Tier-1 native packages;
8. deterministic and adversarial review;
9. exact evidence/readback simulation with zero public writes;
10. canonical V5 operator visibility.

Exit: a repeatable demo produces useful, differentiated content without inventing analysis.

### Work package D — Diversity, SEO, image, and chart closure

Purpose: turn CORE V0 into a credible newsroom product rather than an FX/commodity content demo.

Deliverables:

- required domain taxonomy and source capability registry;
- concentration-aware daily/rolling portfolio report;
- U.S. Big Tech/equity, sector, politics/policy, economic-release, regulatory, geopolitical, rates/credit, FX/commodity, and Capital Chronicle analysis cases;
- search-intent and on-page SEO contracts;
- rights/provenance-aware image strategy;
- deterministic chart contracts and chart QA;
- platform visual adaptations;
- a compact evaluation corpus covering strong and weak cases.

Exit: the same pipeline handles a diversified evaluation cohort with no domain-specific fallback hacks.

### Work package E — Repeated shadow soak and recovery

Status: `COMPLETE_ACCEPTED_AND_MERGED_WITH_CAVEAT`. Independent audit `PASS_WITH_CAVEAT_ACCEPTED_FOR_MASTER_MERGE`; accepted source HEAD `3770ff1c2fe77129c634af3263cbc4e31085b900`; merge
method `FAST_FORWARD_ONLY`. Launch-readiness disposition
`READY_WITH_EXPLICIT_CAVEATS`. Delivered by
`TASK_CONTENTOPS_CORE_V0_REPEATED_SHADOW_SOAK_AND_RECOVERY_V1` as an accelerated logical
soak — ten logical newsroom days, 30/30 window decisions, 16 complete packages, 100 durable
work items with zero lost or double-claimed, 16/16 recovery drills, and 144 hash-bound
release intents with zero executed operations. Calendar-time availability and live
reliability are explicitly not claimed and remain with work package F. Evidence:
`docs/automation/CORE_V0_WPE_SOAK/`.

Purpose: prove routine operation before public launch.

Run the full product over a bounded evaluation period with no public writes. The soak must include:

- scheduled windows and material-update wakeups;
- selected, no-publication, held, duplicate, and blocked outcomes;
- restart/reconstruction;
- update-chain continuation;
- at least one Capital Chronicle analysis update;
- source or visual unavailability;
- chart and SEO QA;
- unknown-write simulation and reconciliation logic;
- incident recording;
- operating-cost measurement.

Target evidence cohort:

- 7 to 10 active newsroom days;
- at least 30 window decisions;
- at least 12 high-quality complete packages;
- at least 8 represented content domains when eligible evidence exists;
- at least 3 explicit no-publication decisions;
- at least 3 update-chain decisions;
- at least 2 Capital Chronicle analysis transformations;
- zero fabricated claims or unauthorized writes.

These are launch-evidence targets, not mandatory publishing quotas.

### Work package F — Exact authorized live cohort

Purpose: validate real public operation within a tightly authorized scope.

Start with a small cohort of high-confidence Tier-1 releases. Use `AUTONOMOUS_DEFAULT` only for exact gate-passing packages and preserve `SUPERVISED_OPERATOR_GATE` as an optional owner toggle. The kill switch must be active and tested.

Required evidence:

- canonical publication and native derivatives;
- exact package and payload hashes;
- strict provider/public readback;
- no duplicate objects;
- bounded recovery for one known-object defect if needed;
- correct abstention when no package qualifies;
- content-quality and visual review;
- operator-visible incident state;
- no change to Capital Chronicle analytical authority.

### Work package G — Final acceptance and launch

The final version may be launched only when all final-product gates pass. Do not move or recreate `v1.0`; use a new release identity for the continuous newsroom product.

## 16. Final launch gates

### Product utility

- Jim can understand the day's important news and available Capital Chronicle analysis from one operating view.
- The product repeatedly produces useful articles and platform packages, not only infrastructure artifacts.
- The system saves material daily operator time.
- No-publication and hold decisions are understandable and useful.

### Content diversity

- The evaluation cohort covers multiple business/news domains.
- No single domain dominates because of hardcoded routing or fixture bias.
- U.S. equities/Big Tech, sectors, politics/policy, economic releases, and at least three other domain families are proven when eligible evidence exists.
- The system distinguishes duplicate headlines from material updates.

### Editorial quality

- Headlines are calibrated and not clickbait.
- Articles contain a clear news peg, evidence, mechanism or explanation, limitations, and what to watch.
- Capital Chronicle analysis is transformed faithfully.
- Independent review catches factual error, overclaim, repetition, stale stories, weak headlines, weak SEO, and visual misuse.

### SEO

- Every canonical long-form package has explicit search intent and complete on-page assets.
- Search claims are not self-certified as success.
- Measurement hooks exist for later Search Console and first-party analytics evidence.

### Images and charts

- Visuals are useful, diverse, rights/provenance bound, and platform appropriate.
- Charts are deterministic, sourced, labeled, and reproducible.
- No chart or image fabricates analytical or event truth.

### Reliability and safety

- One canonical execution path.
- Durable restart-safe work state sufficient for the product loop.
- Exact modes, kill switch, and fail-closed unknown-write behavior.
- Strict readback and reconciliation.
- Zero secret leakage, authority bypass, fabricated numeric truth, or unauthorized public write.

### Operational economics

- Model and infrastructure costs are measured.
- Expensive calls are reserved for high-value stages.
- The product demonstrates a plausible sellable newsroom workflow rather than an unbounded engineering program.

## 17. Definition of final release

The final ContentOps release is complete when the same canonical product can repeatedly:

```text
consume a fresh diversified news universe and governed Capital Chronicle analysis
→ cluster and rank without filler
→ choose news, analysis transformation, hold, or no-publication
→ produce high-quality article, SEO, image/chart, and platform-native packages
→ review against exact evidence and analytical authority
→ publish only under exact active-mode gates
→ read back and reconcile every applicable destination
→ measure performance and record bounded learning
→ survive restart and continue the next window
```

Completion is a product proof, not a document count, schema count, or platform count.

## 18. Current routing after this document

Jim approved this product direction on 2026-08-06. Work package A is complete and Work package B is accepted as the minimum durable prerequisite. Work packages C and D are `COMPLETE_ACCEPTED_AND_MERGED_WITH_CAVEAT`. Work package E is `COMPLETE_ACCEPTED_AND_MERGED_WITH_CAVEAT` (audit `PASS_WITH_CAVEAT_ACCEPTED_FOR_MASTER_MERGE`, accepted source HEAD `3770ff1c2fe77129c634af3263cbc4e31085b900`) with launch-readiness disposition `READY_WITH_EXPLICIT_CAVEATS`. Final pre-launch LLM model authority `CONTENTOPS_9ROUTER_ORDERED_MODEL_AUTHORITY_V2` (superseding `CONTENTOPS_FINAL_PRELAUNCH_LLM_MODEL_AUTHORITY_V1`, retained as historical lineage only) binds gateway `9router` and the ordered pool P0 `new/claude-fable-5`, P1 `new/gpt-5.6-sol-xhigh`, P2 `new/claude-opus-5`, P3 `vx/gemini-3.1-pro-preview(high)` for work packages F and G; ordered fallback is owner-authorized for bounded resilience under a per-invocation retry budget and is not a quality-gate bypass, and runtime verification is `PROVIDER_VERIFIED` with the latest bounded no-write preflight at 4/4 `HEALTHY` and `MODEL_IDENTITY_PROVIDER_VERIFIED`.

The exact next builder task is:

`TASK_CONTENTOPS_EXACT_AUTHORIZED_LIVE_COHORT_V1`

Mode:

`REQUIRES_EXACT_OWNER_AUTHORIZED_LIVE_SCOPE`

The remaining Tier-1 build sequence is:

```text
dual-lane CORE V0 in SHADOW_ONLY   [COMPLETE — ACCEPTED AND MERGED WITH CAVEAT]
→ diversity, SEO, image, and chart closure   [COMPLETE — ACCEPTED AND MERGED WITH CAVEAT]
→ repeated shadow soak and recovery   [COMPLETE — ACCEPTED AND MERGED WITH CAVEAT]
→ exact authorized live cohort   [CURRENT — REQUIRES EXACT OWNER LIVE SCOPE]
→ major final Tier-1 UI/UX rebuild using real live states
→ Work Package G final full-automation prelaunch run
→ Tier-1 final acceptance + new release identity
→ freeze accepted Tier-1 baseline
```

After the accepted Tier-1 baseline is frozen, the owner-approved future direction is the
Tier-2 Pro Video Factory. Tier-2 implementation is not current.

The old automatic Wave 03 approval-envelope/transactional-outbox sequence is no longer the next-task authority. It remains valid historical planning and may be revisited only when the CORE V0 vertical slice or a launch gate directly requires it.

The routed task grants no credential, provider, browser/CDP, network-intake, scheduler/outbox execution, dispatch, publication, or public-write authority. Any live cohort requires a separate exact authorization.
