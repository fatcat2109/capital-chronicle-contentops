# CAPITAL CHRONICLE CONTENTOPS — NEWSROOM INTELLIGENCE, TIER-1 EDITORIAL, SEO, AND PERFORMANCE LEARNING MASTER PLAN V1

**Document status:** Proposed next-phase execution authority<br>
**Target repository:** `fatcat2109/capital-chronicle-contentops`<br>
**Target branch:** `master`<br>
**Verified planning baseline:** `d4c5c6e2e975983d519beece5587bb1f2e35b619`<br>
**Authority date:** 2026-07-14<br>
**Canonical runner to preserve:** `live_contentops.eight_platform_substack_first_pipeline_v1`<br>
**Canonical product UI to preserve:** `ui/contentops_v5/`<br>
**Upstream data authority:** `fatcat2109/Headline-Raw-data-json`<br>
**Current release state at plan creation:** `AWAITING_OPERATOR_FINAL_V1_0_ACCEPTANCE_NO_ENGINEERING_BLOCKERS`

---

## 0. Executive Position

Capital Chronicle ContentOps has proven a difficult but narrow production loop:

```text
governed database evidence
→ story-scoped publication authority
→ evidence-bound article
→ deterministic and LLM editorial review
→ local visual generation
→ canonical Substack publication
→ eight native derivatives
→ strict platform readback
→ bounded repair
→ frozen evidence
```

That proof matters. It shows the system can publish a real, source-backed financial article across the current text/image distribution surfaces without bypassing global DQR, inventing numbers, or reverting to legacy oil/Fed fixtures.

It does **not** yet prove that Capital Chronicle operates as a mature autonomous newsroom.

The current system still lacks three capabilities required for a durable high-frequency financial publication:

1. **Newsroom intelligence and assignment:** selecting the most important eligible story before each publication window from a broad, fresh, multi-domain candidate universe.
2. **Tier-1 editorial and SEO quality:** producing articles with the reporting discipline, compression, originality, structure, source calibration, and reader utility expected from leading financial publications, while measuring SEO with observed search outcomes rather than self-awarded checklist scores.
3. **Performance intelligence and learning:** collecting governed engagement, impression, click, search, retention, and conversion data; attributing outcomes to the actual story, headline, visual, publication window, and platform variant; and using that evidence to improve packaging without allowing engagement metrics to override factual authority.

This plan defines the architecture and execution sequence for those capabilities.

It rejects three superficially attractive but structurally weak approaches:

- **Do not require exactly five articles every day.** Build five configurable editorial decision windows. A valid outcome may be `NO_PUBLICATION`.
- **Do not treat a larger LLM prompt as a tier-1 newsroom.** Quality must come from data contracts, independent revision stages, source and claim graphs, deterministic checks, evaluation corpora, and human acceptance evidence.
- **Do not optimize editorial truth for engagement.** Performance feedback may improve timing, format, headlines, visuals, and audience fit. It may never change source authority, claim permission, DQR, exact/proxy classification, or risk language.

The correct product direction is:

> Capital Chronicle ContentOps should become an evidence-governed newsroom operating system that continuously discovers and ranks current stories, prepares publication-quality analysis, distributes it natively, and learns from measured outcomes while remaining fail-closed on truth.

---

## 1. Current-System Audit

### 1.1 Foundations to preserve

The current architecture contains strong production assets:

- `CapitalChronicleContentEvidencePacketV2` as the ContentOps evidence boundary.
- Story-scoped `contentops_publication` authority without global DQR override.
- Source health, freshness, timestamps, exact/proxy/context labels, claim permissions, citations, and hash lineage.
- Capability-driven story requirements.
- Generic evidence, freshness, visual, editorial, identity, and platform gates.
- A canonical Substack-first runner.
- A release-candidate lock that binds article, media, payload, and preparation artifacts by hash.
- Strict provider and public readback.
- Idempotency and UNKNOWN-write reconciliation.
- Bounded repair that preserves successful public outputs.
- Local deterministic charts and official-source excerpts.
- Registry-driven platform identities and the approved Discord persona.
- Explicit separation between article distribution and video/Shorts/TikTok video.

The next phase should extend these assets, not replace them.

### 1.2 Assignment weakness

The current generic assignment path mainly checks whether a governed packet contains eligible headlines, source URLs, events, and public claims. Once those checks pass, it may accept a preselected assignment or use the first eligible headline.

That is not a newsroom assignment desk.

It does not yet provide:

- a broad current candidate pool;
- event clustering;
- update-chain handling;
- impact scoring;
- surprise scoring;
- breadth and transmission scoring;
- audience relevance;
- novelty against recent Capital Chronicle output;
- portfolio diversity across the day;
- scheduled slot allocation;
- breaking-news preemption;
- a deep-analysis backlog;
- an explicit no-publication threshold.

The successful Treasury run also used a Treasury-specific story builder. It is a valid live canary, not a generic multi-domain newsroom engine.

### 1.3 Editorial weakness

The current editorial system is stronger than a single writer prompt, but weaker than its role names imply.

The role sequence includes assignment editor, evidence planner, reporter/writer, quantitative editor, visual editor, copy editor, platform editor, and adversarial final reviewer. Most stages currently perform deterministic validation rather than independent substantive revision. The pipeline does not yet preserve a complete versioned chain of drafts, disagreements, repairs, and final acceptance decisions.

The current tier-1 and SEO scores also overstate what is proven. They primarily measure configured hygiene rules such as keyword presence, metadata length, slug shape, heading count, source-link count, image metadata, static length, exact duplicate sentences, and absence of a short list of internal phrases.

Those checks are useful. They do not prove superior reporting, original value, semantic non-redundancy, search-intent satisfaction, ranking performance, backlink value, or subscriber conversion.

A self-calculated `SEO score=100` must not be treated as observed SEO success.

### 1.4 Performance-intelligence weakness

The system records publishing evidence and platform IDs, but it does not yet have a unified cross-platform learning fabric.

Missing foundations include:

- persistent content identity across article, platform, visual, and headline variants;
- append-only metric snapshots;
- consistent collection horizons;
- platform-specific metric definitions;
- first-party click attribution;
- Search Console and web analytics integration;
- normalized engagement measures;
- experiment registration;
- cohort analysis;
- sample-size safeguards;
- learning decisions with explicit confidence;
- a firewall preventing engagement optimization from changing evidence authority.

Without this architecture, interaction numbers remain anecdotal rather than operational intelligence.

---

## 2. Product Objective

The target operating loop is:

```text
continuous official/public/headline intake
→ governed candidate pool
→ event and update clustering
→ publication eligibility
→ impact and novelty ranking
→ five configurable decision windows
→ adaptive assignment or no-publication
→ article-mode selection
→ evidence plan and claim graph
→ versioned reporting and editing
→ SEO hygiene and rendered-page audit
→ visual composition
→ supervised release lock
→ Substack-first native distribution
→ strict readback
→ append-only performance snapshots
→ search, engagement, and conversion attribution
→ controlled learning decision
→ updated ranking, packaging, and scheduling priors
```

The system should support geopolitical events, macroeconomic releases, policy decisions, market developments, fiscal and regulatory events, sanctions, trade, supply-chain, energy, weather, infrastructure, company/sector developments with primary evidence, structural analysis, and conditional medium-term outlooks.

It must remain source- and capability-driven. It must not hard-code a permanent list of “important topics” that prevents new high-impact events from being recognized.

---

## 3. Non-Negotiable Invariants

### 3.1 Truth and authority

- Numeric truth comes from approved claims, never LLM prose.
- Global DQR remains authoritative for its scope.
- Story-scoped publication authority may permit a bounded article while global DQR remains blocked.
- A model may not promote proxy/context evidence to exact.
- SourceHealth may describe availability and parse quality but may not grant publication permission.
- Performance metrics may never modify evidence authority.
- Forecasts may not be presented as validated forecasts unless generated and scored by an approved forecast contract.

### 3.2 Publication volume

- Five slots are decision opportunities, not mandatory article quotas.
- `NO_PUBLICATION_THRESHOLD_NOT_MET` is a valid outcome.
- Prefer silence over weak, repetitive, stale, or unsupported content.
- Breaking news may preempt a scheduled analysis slot.
- A deep-analysis fallback still requires value-add and a fresh delta.

### 3.3 Editorial identity

- Pursue tier-1 financial-news standards, not imitation of proprietary house styles.
- Reader-facing copy must not expose internal workflow vocabulary.
- The writer may not self-certify.
- Independent review must not claim publication authority.
- Human acceptance remains final live-edge authority.

### 3.4 Learning

- Engagement is not truth.
- Clicks are not equivalent to trust or reader value.
- Platform metrics retain their native definitions.
- Raw counts across platforms are not compared without normalization.
- Small samples do not trigger large policy changes.
- Experiments vary one primary factor where practical.
- Learning decisions must be reproducible from stored observations.

### 3.5 Existing production system

- Preserve `live_contentops.eight_platform_substack_first_pipeline_v1`.
- Extend the existing generic preparation and release-lock path.
- Do not create a second dispatcher.
- Do not create a parallel data truth path.
- Do not reintroduce legacy oil/Fed routing as fallback.
- Keep video and article-distribution modes separate.
- Keep successful historical repairs frozen.

---

## 4. Program A — Newsroom Intelligence and Five Decision Windows

### 4.1 Correct operating model

The operator goal should be implemented as:

> Up to five high-quality publication decisions per day, distributed across meaningful editorial windows, with breaking-event preemption and a legitimate no-publication result.

A default schedule should be configurable rather than globally fixed. An initial global-macro pattern could be:

1. Asia/overnight review.
2. Europe/global-macro review.
3. U.S. pre-open and scheduled-data review.
4. U.S. policy/intraday review.
5. U.S. close and cross-asset review.

The actual local times belong in configuration. They must not be hard-coded into editorial logic.

Each window evaluates all candidates known at its cutoff time. A candidate rejected earlier may become eligible when a primary source arrives, a material update occurs, market confirmation becomes available, source health improves, or additional claims become publishable.

Each window emits one decision:

```text
PUBLISH_BREAKING_OR_HIGH_IMPACT
PUBLISH_FRESH_ANALYSIS
PUBLISH_DEEP_ANALYSIS
HOLD_FOR_MORE_EVIDENCE
NO_PUBLICATION_THRESHOLD_NOT_MET
```

### 4.2 Upstream newsroom candidate pool

The database should emit a governed multi-candidate contract rather than only a single publication packet.

Proposed contract:

`CapitalChronicleNewsroomCandidatePoolV1`

Minimum top-level fields:

```text
schema_version
pool_id
generated_at_utc
cutoff_time_utc
database_head
logical_hash
consumer_permissions
source_health_summary
candidate_count
story_clusters
candidates
rejected_candidates
global_limitations
```

Minimum candidate fields:

```text
candidate_id
story_cluster_id
update_chain_id
story_type
event_time_utc
published_at_utc
known_at_utc
last_material_update_utc
headline_options
summary
entities
geographies
affected_asset_classes
affected_sectors
source_ids
primary_source_urls
claim_ids
public_claim_permissions
authority_class
exact_proxy_context_summary
source_health
freshness
market_context_required
market_context_available
visual_capabilities
materiality_features
surprise_features
breadth_features
novelty_features
evidence_completeness
known_limitations
publication_eligible
publication_blockers
```

The pool should contain eligible and rejected candidates. Rejection evidence is necessary for audit and model improvement.

### 4.3 Event clustering and update chains

A newsroom cannot treat every headline as an independent story.

Implement deterministic plus model-assisted clustering using:

- normalized entities;
- source document IDs;
- event type;
- geography;
- semantic similarity;
- time proximity;
- shared claim IDs;
- shared official source;
- update relationships.

Clusters must distinguish duplicate, correction, incremental update, material update, confirmation, contradiction, and a genuinely new phase of an event.

Every selected article points to one `story_cluster_id` and one `update_chain_id`.

This prevents five decision windows from publishing five versions of the same underlying event.

### 4.4 Publication hard gates

Impact ranking occurs only after hard eligibility checks.

A candidate fails closed when required evidence is missing:

```text
source identity
public source URL or approved archived authority
consumer permission
claim-level public-use permission
reporting permission
freshness
source health
known timestamps
metric identity
units for numeric claims
exact/proxy/context classification
citation map
story-level DQR
required market context
required visual or document evidence
```

A candidate may be high impact and still unpublishable. Preserve the reason rather than lowering the gate.

### 4.5 Impact and assignment scoring

The initial impact model should combine deterministic features and bounded model judgment.

Configurable features:

```text
materiality
surprise
cross-market or cross-economy breadth
policy significance
source authority
freshness
evidence completeness
audience relevance
novelty
durability
original-analysis potential
visual feasibility
risk of overclaiming
topic repetition penalty
same-day portfolio concentration penalty
```

A starting weight configuration may be committed for testing, but no weight is permanently correct.

The LLM may classify qualitative impact, explain ranking, identify transmission channels, and surface uncertainty. It may not invent market reactions, invent consensus expectations, override hard blockers, grant permission, change authority, or force a publication to fill a slot.

### 4.6 Portfolio optimization across the day

The best individual story may not create the best daily publication portfolio.

The assignment engine should consider:

- topic diversity;
- geography diversity;
- story-mode diversity;
- repeated entities;
- repeated visuals;
- repeated source families;
- audience fatigue;
- overlap with already published articles;
- pending scheduled releases;
- expected update probability.

Do not publish three Treasury-curve articles in one day without separate material updates. Do not let a low-impact market story occupy a slot immediately before a high-impact scheduled release. Do not force superficial geographic diversity when one region genuinely dominates the news.

### 4.7 Breaking-news preemption

A high-impact event may interrupt the normal schedule.

The preemption contract should include:

```text
trigger_time
candidate_id
preempted_slot
preemption_reason
impact_delta
operator_state
publication_deadline
required_evidence
```

Preemption still requires evidence gates. A fast model may detect and cluster the event; a stronger model should perform final assignment judgment when time permits.

### 4.8 Deep-analysis fallback

When no current headline clears the threshold, use this hierarchy:

1. Material follow-up to a recent event.
2. Fresh official-data analysis.
3. Structural analysis with a measurable new data delta.
4. Scenario analysis.
5. No publication.

Deep analysis must not become generic evergreen filler. It should require a fresh authoritative update, a new cross-source comparison, a new original calculation, a meaningful transition, a newly resolved contradiction, or a measurable change in the medium-term setup.

### 4.9 Forecasting boundary

The newsroom must distinguish analysis, scenario, outlook, and forecast.

Until the analyzer has an evaluated forecast loop, medium- and long-term pieces should use conditional scenarios.

A real forecast contract requires:

```text
forecast_id
decision_time_utc
input_snapshot_hash
target_variable
forecast_horizon
forecast_value_or_distribution
probability_or_confidence
assumptions
invalidation_conditions
model_version
human_override
later_realized_outcome
error_metrics
attribution
```

No empty-news-slot fallback should create an unscored forecast merely because a model can write one.

### 4.10 Newsroom artifacts

Proposed ContentOps contracts:

- `ContentOpsPublicationWindowV1`
- `ContentOpsStoryIdentityV1`
- `ContentOpsAssignmentDecisionV2`
- `ContentOpsDailyPortfolioV1`
- `ContentOpsNoPublicationDecisionV1`
- `ContentOpsBreakingPreemptionV1`

Every live article should retain:

```text
story_cluster_id
candidate_id
assignment_decision_id
publication_window_id
daily_portfolio_id
headline_variant_id
article_mode
```

---

## 5. Program B — Tier-1 Editorial and SEO Quality

### 5.1 Correct target

The goal is not “make the prompt sound like Bloomberg.”

The goal is to enforce standards associated with high-quality financial journalism:

- accurate;
- sourced;
- timely;
- material;
- concise;
- original;
- analytically useful;
- calibrated;
- transparent about uncertainty;
- structured for readers;
- discoverable by search;
- accountable to an identified author/editorial process.

No system should claim equivalence to WSJ, FT, or Bloomberg until a human benchmark corpus supports that claim.

Use:

`TIER1_FINANCIAL_EDITORIAL_STANDARD_TARGET`

not:

`MATCHED_WSJ_FT_BLOOMBERG`

### 5.2 Article-mode-specific standards

Replace one universal article template with mode-specific rubrics.

#### Straight news

- what happened;
- when;
- primary source;
- material facts;
- immediate significance;
- what remains unknown;
- concise form.

#### Data release

- actual result;
- comparison basis;
- historical context;
- revision details;
- mechanism;
- market or policy significance where supported;
- next catalyst.

#### Policy decision

- decision;
- change from prior policy;
- official language;
- implementation timeline;
- affected entities;
- mechanism;
- dissent or uncertainty;
- next formal milestone.

#### Market move

- measured move;
- timestamp and session;
- instrument identity;
- units;
- catalyst evidence;
- breadth or cross-asset confirmation where available;
- distinction between observation and causation.

#### Explainer

- reader question;
- definition;
- mechanism;
- evidence;
- examples;
- limitations;
- evergreen framing unless fresh evidence exists.

#### Deep analysis

- explicit thesis;
- multiple authoritative evidence dimensions;
- original contribution;
- counterargument;
- confirmation and falsification conditions;
- meaningful conclusion;
- no artificial word target.

#### Scenario/outlook

- base, upside, and downside conditions;
- probabilities only when governed;
- assumptions;
- signposts;
- invalidation;
- no false certainty;
- clear distinction from a validated forecast.

### 5.3 Sentence-level claim graph

Article-level claim IDs are insufficient for mature auditing.

Implement a sentence- or paragraph-level claim graph:

```text
content_unit_id
text_hash
content_unit_type
claim_ids
source_urls
authority_class
exact_proxy_context
observation_time
known_at_time
inference_class
calculation_reference
citation_rendering
public_use_allowed
```

Content-unit types include fact, direct calculation, source-attributed interpretation, Capital Chronicle inference, scenario, limitation, transition, and non-factual framing.

The final rendered article must be traceable to this graph.

### 5.4 Real revision stages

Replace role-name validation with versioned production:

```text
v0 assignment brief
v1 evidence outline
v2 reporter draft
v3 quantitative edit
v4 headline and structure edit
v5 copy edit
v6 SEO and rendered-page edit
v7 adversarial standards review
v8 final release candidate
```

Each stage records:

```text
input_hash
output_hash
role
model_or_rule_version
changes
unresolved_issues
decision
```

Allowed decisions:

```text
PASS_NO_CHANGE
REVISE
BLOCK
ESCALATE_OPERATOR
```

The final reviewer receives the final rendered content and evidence map, not only a summary.

### 5.5 Original-value gate

Every analysis article should contribute more than paraphrasing sources:

- original calculation;
- historical comparison;
- cross-source reconciliation;
- event timeline;
- scenario framework;
- market transmission map;
- mechanism diagram;
- source disagreement;
- new dataset combination;
- first-party reporting or attributable expert input.

The article manifest should identify:

```text
original_value_type
original_value_description
supporting_claim_ids
methodology
limitations
```

An analysis article that merely summarizes a release should be downgraded to straight news or rejected.

### 5.6 Semantic redundancy detection

Exact duplicate-sentence detection is insufficient.

Add:

- embedding similarity across paragraphs;
- natural-language-inference checks for repeated conclusions;
- repeated caveat detection;
- repeated section-function detection;
- duplicate confirmation/falsification summaries;
- repeated source-method descriptions;
- platform-payload overlap checks.

Distinguish purposeful reinforcement from accidental repetition.

### 5.7 Headline desk

Create bounded candidates for:

```text
reader headline
SEO title
social headline
push or Telegram headline
YouTube Community headline
```

Score each candidate for factual support, source calibration, materiality, specificity, clarity, search intent, novelty, length, clickbait risk, and mismatch risk.

Preserve rejected alternatives and reasons. Later performance data may influence priors but may never justify exaggeration.

### 5.8 Editorial style and compression

Optimize information density, not arbitrary brevity.

Required checks:

- every section performs a distinct function;
- no paragraph repeats the prior paragraph;
- no generic filler;
- no internal workflow vocabulary;
- no decorative macro language unsupported by evidence;
- no causal certainty from correlation;
- no excessive disclaimers;
- no duplicated conclusion;
- no static universal word-count target.

Expected length should derive from article mode, claim count, evidence dimensions, complexity, reader task, and material uncertainties.

### 5.9 Prepublication SEO hygiene

Rename the current score:

`SEO_HYGIENE_SCORE`

This score may include:

- descriptive reader headline;
- separate SEO title;
- clean slug;
- meta description;
- canonical URL;
- byline and author identity;
- publication and modification dates;
- heading hierarchy;
- source links;
- internal links;
- relevant semantic coverage;
- image dimensions;
- image alt text and caption;
- social preview image;
- rendered HTML cleanliness;
- structured data;
- indexability;
- sitemap inclusion;
- mobile rendering;
- page performance.

It is a prepublication engineering score, not proof of ranking success.

### 5.10 Observed SEO performance

Create a separate post-publication authority:

`ContentOpsObservedSearchPerformanceV1`

Required inputs, where accessible:

- Google Search Console page/query data;
- impressions;
- clicks;
- CTR;
- average position;
- country;
- device;
- date;
- query clusters;
- page-level organic traffic;
- engaged sessions;
- reading-depth proxy;
- newsletter conversion;
- return visits.

Compare performance within cohorts: article mode, story type, topic, age, publication window, branded/non-branded queries, and initial position range.

Do not compare raw CTR without considering position and query intent.

### 5.11 Technical SEO audit

Audit the actual rendered public page, not only the local article object.

Verify:

```text
HTTP status
indexability
canonical link
<title>
meta description
Open Graph metadata
author identity
datePublished
dateModified
Article or NewsArticle structured data
high-resolution images
crawlable image URLs
mobile rendering
internal links
sitemap availability
```

Capital Chronicle should then decide whether Substack provides sufficient long-term control or whether an owned canonical archive/custom domain is required. That decision follows measured evidence, not assumptions.

### 5.12 E-E-A-T and transparency

Financial content is high-trust content.

Maintain:

- accurate bylines;
- author profiles;
- editorial standards;
- methodology;
- correction policy;
- sourcing policy;
- data and calculation disclosures;
- clear explanation of AI-assisted production where appropriate;
- human/operator responsibility.

Public disclosure should explain the useful role of automation without exposing sensitive implementation details.

### 5.13 Editorial evaluation corpus

Build a Capital Chronicle golden evaluation corpus with multiple story types, accepted/rejected drafts, strong/weak headlines, factual and semantic errors, overclaiming, stale stories, proxy misuse, repetition, poor SEO, and excellent original-value examples.

Human rubric fields:

```text
accuracy
source quality
claim traceability
materiality
originality
information density
structure
headline calibration
mechanism quality
uncertainty handling
reader utility
SEO hygiene
visual utility
overall acceptance
```

Use pairwise evaluation where useful. Do not claim tier-1 readiness from model self-grading alone.

### 5.14 Model routing

Use model capability according to editorial risk:

- cheaper model: extraction, normalization, metadata, clustering suggestions;
- mid-tier model: classification, platform adaptation, basic copy repair;
- strongest available model: assignment ranking, deep analysis, quantitative interpretation, adversarial final review;
- deterministic code: permissions, hashes, timestamps, formulas, schema, duplicate protection, rendering checks.

Require a strong model when sources conflict, causal interpretation is material, geopolitical framing is sensitive, quantitative methodology is ambiguous, a headline may overstate evidence, or a forecast/scenario boundary is unclear.

---

## 6. Program C — Cross-Platform Performance Intelligence

### 6.1 Objective

Build a governed, append-only performance system that answers:

- Which story types create durable reader value?
- Which headlines produce qualified clicks rather than shallow impressions?
- Which visuals work on each platform?
- Which publication windows work best by story type?
- Which platforms convert readers to the canonical article?
- Which articles attract organic search after 7, 28, and 90 days?
- Which content creates subscriptions, repeat visits, replies, shares, or saves?
- Which experiments are inconclusive?

### 6.2 Unified content identity

Every article and derivative shares a durable identity graph.

Proposed contract:

`ContentOpsContentIdentityV1`

Required IDs:

```text
story_cluster_id
candidate_id
assignment_decision_id
content_item_id
article_version_id
headline_variant_id
visual_bundle_id
platform_variant_id
publication_window_id
experiment_id
canonical_url
platform_post_id
platform_url
```

Identity survives edits and bounded repairs. An article edit creates a new `article_version_id`, not a new story.

### 6.3 Append-only performance snapshots

Do not overwrite metrics.

Initial collection horizons:

```text
T+1h
T+6h
T+24h
T+72h
T+7d
T+28d
T+90d for evergreen/search analysis
```

Proposed record:

`ContentOpsPerformanceSnapshotV1`

Fields:

```text
snapshot_id
content_item_id
platform_variant_id
platform
platform_post_id
collected_at_utc
age_since_publication
metric_name
metric_value
metric_definition
metric_scope
denominator
authority_class
collection_method
collection_status
known_limitations
source_response_hash
```

### 6.4 Metric authority classes

Use:

```text
official_api
official_dashboard_export
official_browser_readback
first_party_web_analytics
first_party_redirect_analytics
public_counter
manual_operator_entry
derived_metric
unavailable
```

A screenshot or public counter must not silently become official private analytics.

### 6.5 Platform collection strategy

#### X

Where account and API permissions permit, collect impressions, likes, replies, reposts, quotes, bookmarks, URL clicks, profile clicks, and engagements. Private/organic metrics for owned posts have collection-window constraints, so snapshots must run promptly.

#### Threads

Where permissions permit, collect views, likes, replies, reposts, quotes, and shares. Nested replies require separate handling; parent metrics must not be assumed to include all reply-level performance.

#### Facebook and Instagram

Use official Meta Insights where current app/account scope permits. Record API version, scopes, metric definitions, deprecations, and unavailable fields.

#### Telegram

Use eligible message statistics or channel/admin analytics where available. Preserve limitations when exact reach is unavailable.

#### Discord

Collect message identity and reactions where available. Do not invent an impression metric.

#### LinkedIn

Use an approved official analytics route only where account/app scope supports it. Otherwise use read-only dashboard extraction, operator export, or bounded CDP readback. Public reactions are not full impression analytics.

#### YouTube Community

Verify the current official analytics surface for Community posts. If required metrics are unavailable through official APIs, use a read-only YouTube Studio/CDP collector with explicit authority and limitations. Do not substitute video metrics for Community-post metrics.

#### Substack and canonical web

Use the best available combination of Substack dashboard/export, Search Console, first-party web analytics, first-party redirect analytics, and subscriber conversion events.

### 6.6 First-party attribution

Every derivative uses a trackable canonical-link strategy.

Use stable redirect or UTM identity:

```text
utm_source
utm_medium
utm_campaign
utm_content
story_cluster_id
platform_variant_id
headline_variant_id
publication_window_id
```

The public URL remains reader-friendly.

Record click, landing, engaged session, reading-depth proxy, newsletter signup, return visit, and conversion timestamp.

Platform-reported clicks and first-party clicks remain separate.

### 6.7 Normalized metrics

Useful normalized measures:

```text
engagements_per_1000_impressions
link_ctr
share_rate
save_or_bookmark_rate
qualified_reply_rate
article_engaged_session_rate
newsletter_conversion_rate
return_visit_rate
search_ctr_adjusted_for_position
organic_sessions_per_1000_search_impressions
28_day_organic_sessions
```

Every formula is versioned and documented.

Do not create one universal engagement score that hides underlying metrics. A composite score may be used only for a narrow decision with transparent weights.

### 6.8 Qualitative interaction analysis

Add bounded classification for:

- question;
- agreement;
- disagreement;
- correction;
- expertise signal;
- spam;
- low-effort reaction;
- request for deeper coverage;
- subscription intent;
- topic suggestion.

Retain original text hash, platform ID, language, confidence, model version, and human correction where provided.

Do not automatically reply during the performance-analysis phase.

### 6.9 Experiment registry

Create:

`ContentOpsExperimentV1`

Experiment dimensions may include headline archetype, social lede, visual type, chart vs document excerpt, publication window, article-length band, article mode, CTA wording, and thread structure.

Rules:

- define the hypothesis before publication;
- vary one primary dimension where practical;
- define the success metric;
- define the observation window;
- define stop conditions;
- preserve null results;
- do not optimize clickbait;
- do not vary factual claims.

### 6.10 Sample-size and causal safeguards

Capital Chronicle will initially have small samples.

Therefore:

- use descriptive cohort analysis first;
- report uncertainty;
- avoid declaring a winner from one post;
- avoid changing global policy from one viral or failed article;
- separate topic effect from packaging effect;
- compare within similar story types;
- account for publication time and audience growth;
- preserve external-event confounders.

Later methods may include hierarchical Bayesian models, shrinkage estimates, and contextual bandits. Do not introduce them until identity and snapshot data are reliable.

### 6.11 Learning firewall

Performance learning may update ranking priors, publication-window priors, headline packaging, visual format, platform payload structure, article-length priors by mode, and audience-topic affinity.

Performance learning may not update claim values, source authority, public-use permissions, DQR, exact/proxy/context labels, factual conclusions, risk language, or citation requirements.

Every learning decision records:

```text
input_snapshots
cohort
sample_size
method
confidence
recommended_change
forbidden_effects_checked
operator_status
```

---

## 7. Cross-Cutting Architecture

### 7.1 Proposed modules

Exact names may be reconciled with existing conventions, but responsibilities should remain consolidated.

#### Newsroom

```text
live_contentops/newsroom_candidate_pool_v1.py
live_contentops/newsroom_event_cluster_v1.py
live_contentops/newsroom_impact_ranker_v1.py
live_contentops/newsroom_schedule_v1.py
live_contentops/newsroom_assignment_orchestrator_v1.py
```

#### Editorial and SEO

```text
live_contentops/article_claim_graph_v1.py
live_contentops/editorial_revision_orchestrator_v3.py
live_contentops/editorial_semantic_redundancy_v1.py
live_contentops/editorial_original_value_v1.py
live_contentops/headline_desk_v1.py
live_contentops/seo_hygiene_v2.py
live_contentops/rendered_page_seo_audit_v1.py
```

#### Performance

```text
live_contentops/content_identity_v1.py
live_contentops/performance_snapshot_v1.py
live_contentops/performance_collectors_v1.py
live_contentops/first_party_attribution_v1.py
live_contentops/performance_normalization_v1.py
live_contentops/experiment_registry_v1.py
live_contentops/performance_learning_v1.py
```

Avoid one tiny module per platform unless provider isolation genuinely requires it.

### 7.2 Storage model

Use append-only operational stores.

Suggested logical tables:

```text
newsroom_candidate
story_cluster
story_update
assignment_decision
publication_window
content_identity
article_version
headline_variant
visual_bundle
platform_variant
performance_snapshot
search_performance_snapshot
web_analytics_event
experiment
learning_decision
operator_acceptance
```

DuckDB is suitable for local analytical joins. JSON/JSONL artifacts remain useful for bounded evidence and replay.

### 7.3 Canonical UI extensions

The canonical UI should eventually add three operator surfaces.

#### Newsroom Desk

- candidate ranking;
- blockers;
- publication windows;
- daily portfolio;
- breaking preemption;
- no-publication decisions.

#### Editorial and SEO Lab

- version history;
- claim graph;
- reviewer disagreements;
- redundancy;
- headline candidates;
- rendered SEO audit;
- operator acceptance.

#### Performance Intelligence

- cross-platform snapshots;
- search performance;
- first-party click attribution;
- cohort comparisons;
- experiments;
- learning recommendations.

UI work follows backend contract stability. Do not build decorative dashboards before machine-readable authority exists.

### 7.4 Model and prompt versioning

Every model-assisted decision preserves:

```text
provider
model
prompt_version
prompt_hash
input_hash
output_hash
temperature_or_equivalent
structured_schema
validation_result
```

Do not store hidden chain-of-thought. Store concise rationale and structured evidence references.

---

## 8. Implementation Sequence

Execute this plan as heavy bounded implementation tasks, not a chain of paperwork tasks.

### Task 1 — Newsroom Candidate Pool, Assignment, and Scheduling

Suggested label:

`TASK_CONTENTOPS_NEWSROOM_CANDIDATE_ASSIGNMENT_AND_FIVE_WINDOW_SCHEDULING_V1`

Scope:

- upstream multi-candidate publication pool;
- generic story identity;
- event clustering;
- update chains;
- publication hard gates;
- impact scoring;
- five decision windows;
- breaking preemption;
- daily portfolio diversity;
- deep-analysis backlog;
- no-publication decision;
- shadow-mode replay.

Do not publish during initial acceptance.

### Task 2 — Tier-1 Editorial Revision and SEO Quality

Suggested label:

`TASK_CONTENTOPS_TIER1_EDITORIAL_REVISION_AND_SEO_QUALITY_V2`

Scope:

- article-mode rubrics;
- sentence-level claim graph;
- versioned editorial revisions;
- semantic redundancy;
- original-value gate;
- headline desk;
- SEO hygiene rename and expansion;
- rendered-page SEO audit;
- evaluation corpus;
- operator scoring.

Do not claim tier-1 equivalence from internal scores alone.

### Task 3 — Performance Intelligence and Attribution

Suggested label:

`TASK_CONTENTOPS_CROSS_PLATFORM_PERFORMANCE_INTELLIGENCE_V1`

Scope:

- content identity;
- official/read-only collectors;
- append-only snapshots;
- first-party attribution;
- Search Console;
- web analytics;
- normalized metrics;
- qualitative interaction classification;
- experiment registry;
- initial performance UI read model.

No automatic engagement-driven editorial change yet.

### Task 4 — Closed-Loop Learning and Adaptive Scheduling

Suggested label:

`TASK_CONTENTOPS_ADAPTIVE_NEWSROOM_LEARNING_LOOP_V1`

Scope:

- cohort baselines;
- learning decisions;
- sample-size safeguards;
- ranking and slot priors;
- headline/visual packaging priors;
- feedback firewall;
- replay;
- operator approval of policy changes.

### Task 5 — Supervised Multi-Window Live Rollout

Suggested label:

`TASK_CONTENTOPS_SUPERVISED_FIVE_WINDOW_NEWSROOM_LIVE_ROLLOUT_V1`

Rollout stages:

1. Shadow ranking only.
2. Operator-approved one or two daily publications.
3. Up to three daily decisions with bounded automation.
4. Up to five daily decision windows.
5. Full supervised automation at the live edge.

Advance only when quality, source, metric, and operational stability remain acceptable.

---

## 9. Validation Strategy

### 9.1 Newsroom tests

- multi-source candidate pool;
- duplicate headlines;
- event clustering;
- corrections;
- material updates;
- stale candidates;
- high-impact blocked candidate;
- low-impact eligible candidate;
- portfolio diversity;
- breaking preemption;
- no-publication outcome;
- deterministic replay;
- cutoff-time correctness;
- no future leakage.

### 9.2 Editorial tests

- sentence-level claim binding;
- missing citation;
- unsupported numeric claim;
- proxy promoted to exact;
- semantic repetition;
- repeated conclusion;
- source escalation;
- unsupported causal statement;
- article-mode mismatch;
- excessive length without value;
- weak original-value contribution;
- incorrect headline calibration;
- internal vocabulary leakage;
- malformed reviewer output;
- independent final review.

### 9.3 SEO tests

- rendered canonical metadata;
- title and description;
- structured data;
- author identity;
- image metadata;
- indexability;
- sitemap;
- mobile rendering;
- internal links;
- Search Console ingestion;
- web analytics attribution;
- separation of hygiene and observed outcomes.

### 9.4 Performance tests

- content identity joins;
- append-only snapshots;
- idempotent collector reruns;
- metric-definition preservation;
- unavailable metric handling;
- collection-window expiry;
- UTM/redirect attribution;
- normalized calculations;
- experiment registration;
- insufficient-sample result;
- feedback firewall.

### 9.5 End-to-end replay

Given the same candidate pool, cutoff time, configuration, model outputs or fixtures, and performance snapshots, the system should reproduce the same assignment decision, publication window, release candidate, performance analysis, and learning recommendation.

Live provider output IDs are excluded from deterministic equality but remain auditable.

---

## 10. Acceptance Criteria

### 10.1 Newsroom assignment

- all selected stories pass publication authority;
- no future leakage;
- no duplicate cluster publication without material update;
- explicit no-publication output works;
- operator agrees selected stories are among the strongest reasonable candidates in most shadow windows;
- portfolio rules do not suppress dominant breaking news;
- ranking features and penalties are inspectable.

The exact operator-agreement threshold should be calibrated after shadow evidence rather than asserted prematurely.

### 10.2 Editorial

- zero unsupported numeric claims;
- zero internal workflow language;
- zero unbound material factual units;
- semantic redundancy catches known paraphrase cases;
- every analysis identifies original value;
- article-mode rubric passes;
- final rendered article receives independent review;
- human acceptance is recorded;
- no tier-1 equivalence claim without benchmark evidence.

### 10.3 SEO

- prepublication hygiene is complete;
- actual rendered pages are audited;
- Search Console and web analytics data are stored;
- observed SEO is reported separately;
- no article is declared SEO-successful before sufficient observation;
- no arbitrary word-count optimization.

### 10.4 Performance

- stable cross-platform content identity;
- append-only snapshots;
- platform definitions retained;
- first-party attribution works;
- missing metrics remain explicit;
- normalized metrics are reproducible;
- no learning decision crosses the truth firewall;
- low-sample cohorts return `INSUFFICIENT_EVIDENCE`.

---

## 11. Operational Policy

### 11.1 Scheduler

The scheduler may automatically refresh candidate pools, cluster events, prepare rankings, prepare drafts, run local reviews, build release candidates, and collect read-only performance data.

Public dispatch remains supervised at the live edge unless later explicit authority changes that rule.

### 11.2 Failure handling

- One failed source does not stop unrelated candidate lanes.
- One failed metric collector does not invalidate other metrics.
- One failed derivative does not rerun the entire distribution.
- UNKNOWN writes require read-only reconciliation.
- Missing evidence blocks only the affected story.
- Weak editorial quality returns revision or no-publication.

### 11.3 Secrets

Never print, persist, screenshot, hash, or commit tokens, cookies, authorization headers, webhook URLs, browser storage, raw environment values, or provider keys.

Store only presence booleans, capability status, non-secret account IDs, approved scopes, and redacted error classes.

---

## 12. Primary Research References

Current official documentation must be revalidated at implementation time.

- [Google: Creating helpful, reliable, people-first content](https://developers.google.com/search/docs/fundamentals/creating-helpful-content)
- [Google: Article structured data](https://developers.google.com/search/docs/appearance/structured-data/article)
- [Google Search Console Search Analytics API](https://developers.google.com/webmaster-tools/v1/searchanalytics/query)
- [Google Analytics Data API](https://developers.google.com/analytics/devguides/reporting/data/v1)
- [X API metrics](https://docs.x.com/x-api/fundamentals/metrics)
- [Threads Insights API](https://developers.facebook.com/docs/threads/insights)
- [Telegram message statistics](https://core.telegram.org/method/stats.getMessageStats)
- [Discord message resource](https://docs.discord.com/developers/resources/message)

Official documentation controls provider semantics. Repository contracts control Capital Chronicle execution.

---

## 13. Final Decision

The next phase should not begin by merely lengthening the current LLM writing prompt.

The strongest implementation path is:

```text
candidate-pool and identity contracts
→ deterministic newsroom ranking
→ five decision windows
→ versioned editorial production
→ claim-level traceability
→ original-value and semantic-redundancy gates
→ rendered SEO audit
→ observed search analytics
→ cross-platform metric snapshots
→ first-party attribution
→ cautious learning loop
```

This is the minimum architecture required to transform the successful July 14 canary into a durable newsroom operating system.

The product should optimize for:

```text
trust
materiality
original value
reader utility
distribution quality
measured learning
```

not:

```text
mandatory volume
self-awarded scores
prompt length
raw impressions
clickbait
```

The master rule is:

> Publish the most important eligible story when Capital Chronicle can add trustworthy value. When it cannot, do not publish.
