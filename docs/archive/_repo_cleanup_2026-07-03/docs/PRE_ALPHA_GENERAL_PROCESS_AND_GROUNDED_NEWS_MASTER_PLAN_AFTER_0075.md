# Capital Chronicle ContentOps — Pre-Alpha General/Process Content Master Plan v1

## 0. Operating Decision

Capital Chronicle ContentOps should not pause completely during the internal-alpha wait-state.

The correct strategy is:

**Maintain the artifact-backed wait-state, but open a tiny manual pre-alpha general/process content lane.**

This lane exists to build audience, trust, and product positioning before Capital Chronicle has approved internal-alpha artifacts. It must not produce fake market calls, fake artifact-backed content, synthetic performance content, public-postable fixture content, or anything that implies Capital Chronicle already has live forecast authority.

The repo-side work should begin with policy, taxonomy, QA gates, and negative tests — not a content generator and not a publishing/export workflow.

## 1. Current Authority Baseline

Repo: `A:\Capital Chronicle\tools\cc-live-contentops`

Current accepted state:

* ContentOps is in terminal local alpha wait-state.
* Real Capital Chronicle alpha artifacts do not exist in this sidecar yet.
* The existing stack is local-only, deterministic, fixture-only, and human-review-required.
* Provider/LLM API calls, network/search, platform APIs, credentials/env reads, scheduling, live posting, autonomous replies/DMs, browser automation/scraping, public-postable synthetic content, real alpha artifact access, and core repo reads/writes remain disabled.
* The next pointer remains:
  `WAIT_FOR_REAL_CAPITAL_CHRONICLE_ALPHA_ARTIFACTS_OR_OPERATOR_SELECTED_LOCAL_MAINTENANCE`

## 2. Master Rule

**Content maturity cannot outrun data maturity.**

Until real approved Capital Chronicle alpha artifacts exist, ContentOps may support only:

* general/process policy;
* taxonomy;
* editorial QA;
* negative guardrail tests;
* operator checklists;
* non-public dry-run previews;
* documentation and evidence updates.

It must not generate public-ready fake posts from fixtures or imply artifact-backed output.

## 3. Two-Lane Content Model

### Lane A — Pre-Alpha General/Process Content

Status: allowed conceptually, but repo support must start with policy/QA only.

Definition:

General/process content is first-party educational or philosophical content about:

* why Capital Chronicle is being built;
* how serious macro research should handle missing data;
* why forecast readiness matters;
* why no-forecast is often the correct answer;
* how bad forecasts fail;
* why the product is not a signal service.

This lane does not require Capital Chronicle alpha artifacts.

Allowed evidence basis:

* Jim’s own product philosophy;
* evergreen macro concepts;
* public official sources if a factual claim needs citation;
* clearly labeled general frameworks;
* process notes that do not imply live system output.

Never allowed:

* source artifact IDs invented for credibility;
* DQR/forecast-readiness states invented as if produced by Capital Chronicle;
* fake lineage;
* fixture/demo content presented as real;
* market calls;
* predictions framed as actionable;
* performance claims.

### Lane B — Future Artifact-Backed Capital Chronicle Content

Status: blocked until real approved alpha artifacts exist.

Definition:

Artifact-backed content depends on real Capital Chronicle outputs and must include:

* operator-approved artifact spec;
* source artifact IDs;
* lineage references;
* freshness;
* limitations;
* DQR/data sufficiency/forecast readiness status;
* missing/proxy/degraded labels;
* content type mapping;
* no financial advice or signal/execution language.

This lane resumes only through the existing real-artifact intake gate and must route to `READY_FOR_LOCAL_REVIEW_ONLY`, never directly to public-ready.

## 4. Safe Pre-Alpha Content Pillars

### 4.1 Build-in-Public: Process, Not Results

Purpose:

Build trust by showing the discipline of refusing weak evidence.

Safe themes:

* why the system should block forecasts when data is insufficient;
* why manual review exists;
* why local-first and human-in-the-loop matter;
* what the team is building before alpha;
* what the system is designed not to do.

Example angles:

* “Why Capital Chronicle would rather publish no forecast than a low-quality forecast.”
* “The hardest part of macro research is not prediction; it is knowing when evidence is not enough.”
* “A good research system needs a refusal mode.”

### 4.2 Macro Education: Evergreen, Non-Directional

Purpose:

Teach macro reasoning without telling anyone what to trade.

Safe themes:

* data revisions;
* official-source lag;
* soft vs hard data;
* base effects;
* cross-asset confirmation;
* why one print rarely settles a macro thesis;
* difference between observation, thesis, and actionable conclusion.

Example angles:

* “A single CPI print is not a regime model.”
* “Why macro data can be true, stale, and still misleading.”
* “The difference between a chart and a forecast.”

### 4.3 Data Sufficiency / Forecast Readiness Education

Purpose:

Make Capital Chronicle’s wedge legible before alpha.

Safe themes:

* missing stays missing;
* degraded stays degraded;
* proxy-only is not official truth;
* confidence is invalid if required inputs are absent;
* forecast readiness is a gate, not a marketing badge.

Example angles:

* “What has to be true before a forecast is even worth drafting?”
* “Why proxy-only data should be labeled, not hidden.”
* “No forecast is sometimes the most honest output.”

### 4.4 Failure Forensics Philosophy

Purpose:

Prepare the audience for the later forensics product without needing real outcomes yet.

Safe themes:

* stale-data error;
* missing-lane error;
* regime-classification error;
* timing error;
* catalyst error;
* overconfidence error;
* source-quality error.

Example angles:

* “Bad forecasts are not always bad models. Sometimes the system did not know what it was missing.”
* “A forecast can fail because the thesis was wrong, the timing was wrong, or the input fabric was incomplete.”
* “Why post-move forensics may be more useful than pre-move confidence.”

Pre-alpha limitation:

Avoid detailed public post-mortems of live market events unless they are clearly evergreen education and source-cited. Do not turn them into implied trade lessons.

### 4.5 Product Philosophy / Positioning

Purpose:

Define what Capital Chronicle is and is not.

Safe themes:

* not a Bloomberg replacement;
* not an AI trading bot;
* not a signal service;
* not an execution engine;
* not guaranteed forecasting;
* a local-first macro research system focused on data sufficiency, forecast readiness, and failure forensics.

Example angles:

* “Capital Chronicle is not built to shout signals. It is built to ask whether a thesis deserves confidence.”
* “The wedge is not speed. The wedge is evidence discipline.”
* “The product is designed to make uncertainty visible.”


## 5. Forbidden Content Categories

Always block:

* buy/sell/hold language;
* position sizing;
* entry/exit levels;
* personalized financial advice;
* “watch this level” as trade implication;
* “my model says buy/sell/short/long”;
* price targets;
* guaranteed or near-guaranteed prediction;
* probability claims about future market moves unless backed by a future approved artifact and reviewed policy;
* “this is not financial advice, but...” followed by actionable framing;
* broker/order/execution/MT5/live trading language;
* signal-service positioning;
* fake performance;
* simulated or fixture performance presented as public proof;
* synthetic/demo fixture content made public-postable;
* raw vendor data redistribution;
* unverified numeric market claims;
* public claim that Capital Chronicle alpha is already active before approved artifacts exist;
* content that hides missing/degraded/proxy data;
* content that converts blocked readiness into confidence.

## 6. Platform Strategy

### Substack

Role:

Canonical long-form home.

Use for:

* macro education essays;
* product philosophy letters;
* failure-forensics frameworks;
* data sufficiency explainers;
* public “why we wait” essays.

Pre-alpha cadence:

One essay every one to two weeks.

Rules:

* no live market calls;
* no performance claims;
* no fake artifact-backed sections;
* every factual/current claim must have source notes;
* general/process content must be labeled as general/product/process, not Capital Chronicle output.

### LinkedIn

Role:

Professional positioning and founder/operator voice.

Use for:

* concise essays;
* build-in-public notes;
* process discipline;
* product philosophy;
* “why this system refuses weak forecasts.”

Pre-alpha cadence:

One to two posts per week.

Rules:

* professional, calm, explicit limitations;
* no hype;
* no “AI trading bot” framing;
* no directional market implication;
* avoid current-market commentary unless source-cited and educational.

### X

Role:

Sharp hook and conversation layer.

Use for:

* short principles;
* threads derived from Substack essays;
* build-in-public snapshots;
* “no forecast” philosophy.

Pre-alpha cadence:

Optional and conservative.

Rules:

* avoid hot takes;
* avoid live-event market interpretation;
* never thread a quasi-signal;
* every post should be able to stand as education/process, not advice.

### Threads

Role:

Lower-stakes community mirror.

Use for:

* softer educational fragments;
* build-in-public notes;
* simple questions around process;
* less technical versions of LinkedIn/X ideas.

Pre-alpha cadence:

Optional.

Rules:

* no market calls;
* no reactive political/market takes;
* use as community tone testing, not authority channel.


## 7. Manual-Only Editorial Workflow

Pre-alpha content should move through five gates:

### Gate 1 — Lane Classification

Every draft must be one of:

* `pre_alpha_general_process`
* `future_artifact_backed`

During wait-state, only `pre_alpha_general_process` may be discussed for public manual posting outside the repo. The repo should not produce public-ready content until the QA lane exists.

### Gate 2 — Claim Classification

Every draft claim must be classified as:

* first-party philosophy;
* evergreen education;
* cited factual claim;
* current factual claim requiring citation;
* market-sensitive claim;
* forbidden claim.

Market-sensitive claims are blocked unless transformed into evergreen education.

### Gate 3 — Source Requirement

If the claim is factual and not common/evergreen, it needs:

* source;
* date;
* limitation;
* freshness note if relevant.

If a source is missing, the draft is not publishable.

### Gate 4 — Forbidden Language Scan

Block:

* trade/action verbs;
* certainty/guarantee terms;
* signal-service wording;
* broker/order/execution wording;
* fake performance;
* implied alpha output;
* unsupported market direction.

### Gate 5 — Human Final Review

Only Jim can decide to publish manually.

ContentOps must not:

* approve;
* auto-select final public copy;
* post;
* schedule;
* send platform API requests;
* scrape metrics;
* read credentials;
* DM/reply autonomously.

## 8. Recommended Next Repo Backlog

### TASK_CONTENTOPS_0075_PRE_ALPHA_GENERAL_PROCESS_POLICY_AND_QA_GATE_V0

Objective:

Create a local-only policy/taxonomy/QA gate for pre-alpha general/process content without generating public-ready content.

Allowed:

* docs;
* schema/frontmatter contract;
* deterministic QA checklist;
* negative tests;
* forbidden language test fixtures;
* read-only/dry-run CLI summary if useful;
* evidence packet.

Forbidden:

* no content generator;
* no public-postable outputs;
* no export/clipboard bundle;
* no platform templates that look publish-ready;
* no provider/search/platform/API/credential access;
* no real alpha artifact access;
* no core repo reads/writes;
* no scheduling;
* no auto-approval.

Acceptance:

* `pre_alpha_general_process` is clearly separated from future `artifact_backed`.
* General/process content cannot claim artifact lineage.
* General/process content cannot route to the real artifact intake/bridge path.
* Market call examples are blocked.
* Signal-service/execution/broker examples are blocked.
* Fixture/demo content remains not-public-postable.
* Terminal wait-state pointer is preserved.
* Full tests pass.
* Suspicious scan passes.
* Evidence packet confirms no network/provider/search/platform/API/credential/live action.

### TASK_CONTENTOPS_0076_PRE_ALPHA_EDITORIAL_REVIEW_PACKET_DRY_RUN_V0

Only after 0075 PASS.

Objective:

Create a non-public, local-only editorial review packet format for Jim-authored general/process drafts.

Allowed:

* manual input fixture representing Jim-authored text;
* QA result;
* claim classification;
* source-needed flags;
* platform-fit notes;
* blocked-language report;
* “not public-postable until Jim final review” status.

Forbidden:

* no synthetic public-ready content;
* no automated final copy;
* no platform export;
* no API;
* no credentials;
* no posting.

Acceptance:

* review packet helps Jim decide what is safe to manually rewrite/post;
* output is explicitly review-only;
* no draft is marked publish-ready by the system.

### TASK_CONTENTOPS_0077_PRE_ALPHA_MANUAL_AUTHORSHIP_OPERATING_GUIDE_V0

Only after 0076 PASS.

Objective:

Add a concise operator guide for how Jim can write and manually publish pre-alpha general/process content outside the repo while keeping ContentOps records clean.

Allowed:

* docs-only guide;
* examples as non-public sample ideas, not ready-to-post copy;
* checklist;
* manual log template.

Forbidden:

* no generated social posts;
* no automated export;
* no platform integrations;
* no metrics ingestion;
* no scheduling.

Acceptance:

* Jim has a clear manual workflow.
* The repo remains local-only and not public-postable.
* The guide explains the difference between manually authored public content and repo-generated fixture/dry-run content.

### TASK_CONTENTOPS_0078_GROUNDED_RESEARCH_BRIEF_TEMPLATE_DESIGN_ONLY_V0

Optional, after Deep Research findings are finalized.

Objective:

Create a design-only template for future grounded research briefs that can inform editorial strategy without becoming source authority or platform automation.

Allowed:

* template docs;
* source taxonomy;
* claim-risk taxonomy;
* “research context only” labels.

Forbidden:

* no search/provider integration in repo;
* no fetched sources;
* no live calls;
* no external credentials.

Acceptance:

* future research can be attached manually as context;
* deterministic QA still decides whether claims are allowed.

### WAIT_FOR_REAL_ALPHA_ARTIFACTS_RESUME_PATH

When real Capital Chronicle internal-alpha artifacts exist, do not use the pre-alpha lane to ingest them.

Resume via the existing artifact-backed path:

1. Confirm artifact spec.
2. Confirm approved export location.
3. Confirm source artifact IDs.
4. Confirm lineage, freshness, limitations.
5. Confirm DQR/data sufficiency/forecast readiness states.
6. Confirm missing/proxy/degraded labels.
7. Confirm content type.
8. Confirm no financial advice/execution/signal claims.
9. Intake gate routes to `READY_FOR_LOCAL_REVIEW_ONLY`.
10. Jim reviews final copy manually before any public use.


## 9. What Not To Build Yet

Do not build:

* live publisher;
* platform adapters;
* scheduler;
* auto-cross-poster;
* API clients;
* credential storage;
* browser automation;
* scraping;
* autonomous replies/DMs;
* analytics fetcher;
* public-ready synthetic content generator;
* fake performance dashboard;
* market commentary generator;
* current-event take generator;
* “alpha teaser” generator.

These are premature and violate the wait-state risk posture.

## 10. Decision Tree

### If Jim wants to start audience-building now

Proceed with 0075 first:

Policy + taxonomy + QA gate only.

Jim may separately write public posts manually using the safe pillars, but repo outputs remain non-public unless and until later gates are built.

### If Jim wants maximum safety and zero public presence

Do no content-lane implementation.

Only maintain repo docs/tests and wait for real alpha artifacts.

### If real alpha artifacts arrive soon

Do not expand pre-alpha lane.

Switch to artifact-backed resume checklist and run the first real artifact intake task.

### If Deep Research produces stronger platform guidance

Fold it into docs as advisory strategy only.

Do not implement platform-specific automation.

## 11. Master Recommendation

Proceed with a small pre-alpha content lane, but implement it in this order:

1. 0075 — policy/taxonomy/QA barrier
2. 0076 — review-only packet for Jim-authored drafts
3. 0077 — manual authorship operating guide
4. 0078 — optional research brief template
5. Real alpha resume path when artifacts exist

The key principle is:

**Build the guardrails before the generator. Build the lane boundary before the content workflow. Keep all public posting manual. Keep artifact-backed content blocked until real alpha artifacts exist.**


## 12. Addendum — Grounded News / Research Context Lane

### Purpose

During the pre-alpha wait-state, Capital Chronicle ContentOps should support a safe real-content workflow using LLM-assisted grounded research and current news context.

The goal is to create timely, engaging social/newsletter content without pretending that Capital Chronicle has live alpha artifacts, trading signals, or forecast authority.

This lane uses real public information and current news as hooks, but turns them into education, process commentary, data-sufficiency analysis, forecast-readiness discussion, or product philosophy — not market calls.

### Core Principle

**News is a hook, not a signal.**

A current event may be used to explain:

* why data quality matters;
* why a macro claim is not forecast-ready;
* how official sources should be checked;
* why markets often overreact to incomplete information;
* what uncertainty remains;
* what a serious research system would need before forming a thesis.

A current event must not be used to say:

* buy/sell/hold;
* long/short;
* target price;
* “this means X asset will move”;
* “our model predicts”;
* “this is the setup”;
* “watch this level”;
* “Capital Chronicle alpha says...”

### Allowed Source Types

Preferred:

* official sources: central banks, statistical agencies, Treasury/fiscal agencies, regulators, exchanges when relevant;
* reputable news sources for event context;
* company/government primary releases when discussing policy or macro events;
* public research reports where redistribution is allowed;
* platform-native public posts only as context, not authority.

Avoid:

* unsourced social media rumors;
* anonymous market claims;
* raw vendor/proprietary data;
* paywalled content copied into outputs;
* screenshots without source/date;
* influencer claims as evidence;
* politically charged commentary without careful source handling.

### Workflow

1. Operator or ChatGPT Deep Research collects a grounded research brief outside the repo.
2. The brief includes source URLs, publication dates, short source summaries, and claim-risk notes.
3. LLM proposes safe angles:
   * macro education angle;
   * data sufficiency angle;
   * forecast readiness angle;
   * failure forensics angle;
   * product philosophy angle;
   * build-in-public angle.
4. ContentOps QA checks:
   * forbidden trading/signal language;
   * unsupported numeric claims;
   * missing citations;
   * implied forecast authority;
   * artifact-backed claims without artifacts;
   * whether the post is educational/general/process content.
5. Jim manually approves, edits, and posts.
6. Any public URL/metrics are recorded manually only, if needed.

### Content Types Added

Add or recognize these pre-alpha content subtypes:

* `grounded_news_context`
* `official_data_explainer`
* `policy_process_commentary`
* `macro_education_from_news`
* `forecast_readiness_from_news`
* `data_sufficiency_from_news`
* `failure_forensics_from_news`

These remain under the broader class:

`pre_alpha_general_process`

They are not artifact-backed Capital Chronicle outputs.


### Safe Examples

Example 1:

A central bank speech is released.

Unsafe:

“The Fed is clearly preparing to cut. Duration longs look attractive.”

Safe:

“Central bank speeches are useful context, but they are not a forecast by themselves. A serious macro workflow still has to check inflation trend, labor-market cooling, financial conditions, and revision risk before treating the speech as thesis-ready.”

Example 2:

A CPI report is published.

Unsafe:

“This CPI print means equities should rally.”

Safe:

“One CPI print can change the conversation, but it should not become a regime call by itself. The better question is whether the print confirms a broader disinflation path, whether revisions matter, and whether cross-asset confirmation exists.”

Example 3:

A geopolitical headline moves oil.

Unsafe:

“Oil is going higher from here.”

Safe:

“Geopolitical headlines often create immediate price reaction before data sufficiency exists. A research process should separate headline risk, supply-chain evidence, inventory data, policy response, and positioning before calling it a durable macro shift.”

### Platform Use

Substack:

Use for the full grounded explainer.

LinkedIn:

Use for professional summary and process insight.

X:

Use for concise hooks and short educational threads.

Threads:

Use for softer, conversational versions.

All platforms:

No signal framing. No urgency. No actionable trade language. No “model says” language. No fake alpha.

### Repo-Side Implementation Sequence

Update the next backlog:

1. **0075 — Pre-Alpha Policy + QA Gate**
   Add `grounded_news_context` as a safe subtype under `pre_alpha_general_process`.
   Add negative tests proving news hooks cannot become market calls.

2. **0076 — Grounded Research Brief Schema**
   Local-only schema/template for operator-supplied research briefs.
   No network calls. No provider calls. No search integration.
   It only validates manually supplied source metadata and claim-risk labels.

3. **0077 — LLM-Assisted Draft Review Packet**
   Review-only packet for drafts produced outside the repo by Jim/ChatGPT.
   The system checks citations, risk language, source freshness labels, and content class.
   It does not auto-generate final public copy.

4. **0078 — Manual Publish + Metrics Capture Guide**
   Jim manually posts approved content.
   ContentOps may record URLs and manually observed metrics only.
   No scraping, no platform API, no credentials.

### Final Rule

The grounded-news lane is allowed only if every item remains:

* source-cited;
* educational/general/process;
* manually reviewed;
* manually posted;
* non-advisory;
* non-signal;
* non-artifact-backed unless real approved artifacts exist.

