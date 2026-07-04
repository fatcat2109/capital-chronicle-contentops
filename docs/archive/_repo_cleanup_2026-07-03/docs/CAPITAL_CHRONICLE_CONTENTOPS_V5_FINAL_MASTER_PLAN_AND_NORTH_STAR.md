# Capital Chronicle ContentOps V5 — Final Master Plan + North Star

## 0. Owner Decision

Capital Chronicle ContentOps should rebuild the front-end from scratch as a parallel V5 application.

V5 is not a patch to V4.

V5 is a full modern design-system platform for local-first supervised editorial operations, evidence governance, AI-assisted writing, SEO-aware content preparation, approval packets, media attachments, dry-run platform previews, manual publishing records, future supervised dispatch gates, and future Capital Chronicle internal-alpha artifact intake.

The current V4 cockpit remains as a fallback/reference implementation until V5 reaches feature parity, visual QA, and safety validation.

## 1. North Star

Capital Chronicle ContentOps V5 is a local-first institutional editorial operating system that turns sources, research briefs, drafts, media, approvals, platform payload previews, dispatch gates, internal-alpha artifacts, and evidence into one supervised control surface.

It lets Jim:

* understand what is safe;
* understand what is blocked;
* write and improve serious macro content;
* use AI for editorial quality, SEO, hooks, and variants;
* preserve citations, limitations, and no-signal constraints;
* attach local media and image placeholders safely;
* inspect source lineage and evidence;
* approve packets manually;
* preview platform payloads without posting;
* manually publish and record URLs/metrics;
* later enable supervised platform automation only after explicit gates are real;
* later pull approved Capital Chronicle internal-alpha framework data only through an explicit read-only artifact intake gate.

V5 must make the wedge visible:

Capital Chronicle does not sell signals. It makes research maturity, data sufficiency, forecast readiness, missing/degraded/proxy data, source lineage, and failure forensics inspectable.

## 2. What V5 Is Not

V5 is not:

* a generic dashboard;
* a social media scheduler;
* a trading terminal;
* a Bloomberg clone;
* an AI writing toy;
* an autonomous posting bot;
* a signal service;
* a broker/execution console;
* a public-ready synthetic content generator;
* a credential screen;
* a live API console.

The system can prepare, review, validate, preview, and assemble packets. It cannot publish, schedule, reply, DM, scrape, read credentials, or call platform APIs until explicit future gates exist.

## 3. Product Mode Stack

V5 should show the current operating mode at all times.

Initial default modes:

* `LOCAL_PRE_ALPHA`
* `REVIEW_ONLY`
* `NOT_PUBLIC_POSTABLE`
* `FUTURE_LIVE_DISABLED`
* `MANUAL_APPROVAL_REQUIRED`
* `NO_FINANCIAL_ADVICE`
* `NO_SIGNAL_LANGUAGE`
* `NO_PLATFORM_API`
* `NO_PROVIDER_API`
* `NO_CREDENTIAL_READ`
* `NO_SCHEDULER`
* `NO_SCRAPING`

Future modes, only after explicit gates:

* `APPROVED_FOR_MANUAL_POST`
* `MANUALLY_POSTED`
* `METRICS_ENTERED`
* `READY_FOR_LOCAL_REVIEW_ONLY`
* `ARTIFACT_INTAKE_READY`
* `SUPERVISED_LIVE_GATE_PENDING`
* `SUPERVISED_LIVE_GATE_CLEARED`

## 4. Strategic Content Lanes

V5 must encode the three-lane content model.

### Lane A — Pre-Alpha General / Process Content

Purpose:
Build audience and trust before internal alpha by explaining the discipline behind Capital Chronicle.

Allowed:

* build-in-public;
* macro education;
* data sufficiency;
* forecast readiness education;
* failure forensics philosophy;
* product philosophy;
* source trust;
* why no forecast can be the correct output;
* why Capital Chronicle is not a signal service.

Not allowed:

* fake artifact-backed claims;
* fake DQR or readiness states;
* fake source IDs;
* market calls;
* performance claims;
* public-ready fixture content.

### Lane B — Grounded News / Research Context Content

Purpose:
Use real-world news and public sources as hooks for timely educational content.

Core rule:
News is a hook, not a signal.

Allowed:

* source-cited explainers;
* official-source checking;
* data sufficiency analysis;
* forecast-readiness education;
* uncertainty explanation;
* safe content angles;
* non-advisory platform variants.

Not allowed:

* buy/sell/hold;
* long/short;
* price targets;
* “our model predicts”;
* “our signal says”;
* “watch this level”;
* implied forecast authority;
* unsupported numeric market claims.

### Lane C — Future Artifact-Backed Capital Chronicle Content

Purpose:
Turn real approved Capital Chronicle internal-alpha artifacts into content packets later.

Blocked until all exist:

* internal-alpha artifact spec;
* approved export location;
* artifact IDs;
* lineage;
* freshness;
* limitations;
* DQR/data sufficiency/forecast readiness states;
* missing/proxy/degraded labels;
* content type mapping;
* no advice/signal/execution language;
* operator approval path.

This lane must route to `READY_FOR_LOCAL_REVIEW_ONLY`, never directly to public-ready.

## 5. AI Writer + SEO Layer

V5 should include an AI Writer / SEO Intelligence layer as a first-class product surface.

The AI Writer is an editorial strategist, not a source of truth.

### What AI Writer May Do

* improve hooks;
* rewrite for clarity;
* produce platform variants;
* generate title/subtitle candidates;
* suggest SEO keywords;
* suggest hashtags;
* create audience-specific versions;
* score readability;
* score platform fit;
* classify content type;
* summarize source-provided context;
* critique draft quality;
* suggest first-comment ideas;
* compare variants;
* produce operator review packets.

### What AI Writer May Not Do

* invent facts;
* invent source IDs;
* invent artifact IDs;
* invent metrics;
* invent URLs;
* invent market numbers;
* certify data sufficiency;
* certify forecast readiness;
* remove caveats;
* hide missing/degraded/proxy labels;
* approve content;
* publish content;
* decide final public copy;
* call provider APIs unless a future approved LLM gate exists;
* turn blocked readiness into confidence.

### AI Writer Product Surfaces

AI Writer should appear in:

1. Writer Studio — assist with draft quality, variants, SEO, platform fit.
2. Draft Inspector — explain claim risks, source gaps, limitation gaps.
3. Content Inventory — show editorial score, SEO score, citation score, review state.
4. Approval Queue — attach AI critique to approval packet.
5. Platform Preview — compare platform variants.
6. Evidence Vault — archive AI prompt contracts, model disclaimers, and review outputs.
7. Settings / Safety — show AI provider disabled until explicit provider gate.

### AI Writer Output Contract

Every AI-assisted output should include:

* `variant_id`
* `source_draft_id`
* `source_artifact_id` if applicable
* `platform`
* `audience_mode`
* `style_mode`
* `content_type`
* `body`
* `hook_type`
* `hashtags`
* `seo_keywords`
* `title_candidates`
* `limitations_preserved`
* `source_references_preserved`
* `safety_notes`
* `not_public_postable_reason`
* `editorial_score`
* `seo_score`
* `platform_fit_score`
* `guardrail_status`
* `human_review_required`
* `publish_ready: false` unless deterministic guardrails and human approval exist.

### Audience Modes

* Macro professional
* Quant/systematic trader, non-advisory
* Builder / AI tooling audience
* Long-form newsletter reader
* Institutional allocator / analyst
* General educated macro audience

All audience modes must preserve no-financial-advice, no-signal, and no-execution constraints.

## 6. Capital Chronicle Internal Alpha Data Integration

V5 must be designed now to receive future Capital Chronicle internal-alpha data, but must not assume it exists.

### Current State

Internal alpha artifacts are not yet available to ContentOps as approved truth. V5 must show artifact-backed content as blocked or future-gated.

### Future Integration Name

Use a dedicated future module:

`Internal Alpha Artifact Intake`

or

`Capital Chronicle Artifact Connector`

This is not a live market-data connector. It is a read-only artifact intake boundary.

### Future Read-Only Intake Contract

When internal alpha is ready, V5 should expect local or explicitly exported artifacts with:

* artifact ID;
* artifact type;
* generated timestamp;
* source coverage;
* lineage manifest;
* freshness status;
* DQR/data sufficiency status;
* forecast-readiness status;
* missing/degraded/proxy labels;
* limitations;
* allowed content class;
* forbidden content class;
* checksum/hash;
* approval state;
* operator notes;
* no-advice/no-signal metadata.

### Future Data Flow

Capital Chronicle internal alpha framework
→ approved export manifest
→ ContentOps artifact intake gate
→ deterministic schema validation
→ artifact-backed content eligibility check
→ Writer Studio / AI Writer can propose review-only drafts
→ Draft Inspector validates claims
→ Approval Queue produces packet
→ Platform Preview renders dry-run payloads
→ manual approval / manual publish / future supervised dispatch.

### Strict Rule

The AI Writer can summarize or rewrite artifact-backed content only after the artifact intake gate validates the artifact. It cannot treat internal-alpha framework data as usable merely because a file exists.

## 7. V5 App Information Architecture

V5 should build these rooms.

### Phase 1 Flagship Screens

1. Command Center
2. Content Inventory
3. Writer Studio with Media Tray
4. Approval Queue + Dispatch Control
5. Evidence Vault

### Route Placeholders for Future Screens

6. Draft Inspector
7. Platform Payload Preview
8. Grounded News Workbench
9. Calendar / Workflow Board
10. Visual Export / Screenshot-Safe Studio
11. Settings / Safety Policy
12. Media Studio
13. Internal Alpha Artifact Intake
14. Manual Publish + Metrics Capture
15. AI Writer / SEO Lab

## 8. Screen Specifications

### 8.1 Command Center

Purpose:
First-fold operational truth.

Must answer:

* What is safe?
* What is blocked?
* What is awaiting review?
* What can Jim do next?
* What cannot happen?
* Which evidence supports the current state?

Core modules:

* global safety strip;
* current mode;
* system verdict;
* active blockers;
* validation passes;
* lineage verified;
* queue summary;
* pipeline health;
* available local operations;
* next allowed local action;
* latest baseline / build provenance;
* right inspector.

No fake publish actions.

### 8.2 Content Inventory

Purpose:
Object registry for every content item, draft, brief, packet, and future artifact-backed content.

Core modules:

* content lane filters;
* content type filters;
* status filters;
* platform fit;
* citation state;
* media state;
* approval state;
* owner;
* last updated;
* evidence ID;
* selected item inspector;
* local actions;
* approval override blocked state.

Content item types:

* research brief;
* manual draft;
* AI-assisted variant;
* approval packet;
* platform payload;
* media asset;
* evidence packet;
* artifact-backed future item.

### 8.3 Writer Studio with Media Tray

Purpose:
Manual writing + AI-assisted editorial improvement + local media attachment mock.

Core modules:

* document outline;
* editor canvas;
* platform tabs;
* source/brief links;
* citation framework;
* limitation note;
* guardrail panel;
* claim-risk panel;
* AI Writer assist controls;
* SEO keyword panel;
* title/hook variants;
* media tray;
* alt text;
* rights status;
* platform media constraints;
* submit to approval queue.

Important:
AI Writer and media attachment are local-review surfaces. No provider call, file upload, or platform media API unless future gates exist.

### 8.4 Approval Queue + Dispatch Control

Purpose:
Signed decision workbench and future-gated dispatch matrix.

Core modules:

* approval packet list;
* required approver;
* draft hash;
* payload hash;
* evidence sources;
* approval state;
* revocation state;
* redacted audit state;
* risk state;
* comments;
* gate matrix;
* disabled/future dispatch control.

Gate matrix:

* approval ledger;
* payload hash match;
* guardrail pass;
* kill switch;
* credential slot;
* platform live gate;
* redacted audit ready;
* rollback/manual fallback.

No “publish now” default. Any future dispatch action is disabled unless every gate passes.

### 8.5 Evidence Vault

Purpose:
Dark evidence mode compliance room.

Core modules:

* task evidence packets;
* commit timeline;
* validation matrix;
* secret scan results;
* forbidden-scope matrix;
* source lineage;
* approval history;
* redacted audit trail;
* known residual drift;
* active blockers;
* next task pointer;
* selected-object inspector.

Default should not be raw JSON. Raw JSON can exist as drilldown only.

### 8.6 Draft Inspector

Purpose:
Claim and safety inspection.

Core modules:

* source lineage;
* source freshness;
* citation completeness;
* claim-risk classification;
* forbidden language scan;
* no-signal audit;
* limitations check;
* artifact-backed eligibility;
* AI variant comparison;
* approval readiness.

### 8.7 Platform Payload Preview

Purpose:
Exact platform dry-run preview without posting.

Platforms:

* X
* LinkedIn
* Threads
* Substack/manual export
* Telegram
* Facebook Page
* Instagram
* TikTok placeholder

Each platform card shows:

* character limits;
* media requirements;
* unsupported features;
* warning labels;
* platform-specific copy;
* payload hash;
* approval state;
* dry-run status;
* no external call;
* no credential use.

### 8.8 Calendar / Workflow Board

Purpose:
Manual workflow planning, not scheduler.

Lanes:

* idea;
* source needed;
* research brief ready;
* draft review;
* blocked;
* approved for manual;
* manually posted;
* metrics entered.

No scheduled/live state until explicitly approved.

### 8.9 Visual Export / Screenshot-Safe Studio

Purpose:
Create shareable, redacted, safe visual artifacts.

Modes:

* screenshot-safe dashboard;
* report card;
* weekly summary;
* data sufficiency card;
* forecast readiness card;
* blocked forecast explainer;
* content performance card;
* redacted media preview.

No secrets, no raw vendor data, no public-ready false claims.

### 8.10 Settings / Safety Policy

Purpose:
Policy inspection screen, not credential screen.

Must show:

* local-only mode;
* credential policy;
* redaction policy;
* no-advice policy;
* no-signal policy;
* platform gates;
* AI provider gate;
* LLM provider disabled until explicit task;
* internal alpha intake gate;
* exact `.env` path only as negative policy copy;
* no secret display.

## 9. Design System

V5 uses the v5.1 Stitch visual direction as reference.

### Default Theme

Light institutional CMS/editorial.

Characteristics:

* off-white/zinc surfaces;
* white cards;
* precise 1px borders;
* strong readability;
* calm spacing;
* editorial workbench feel;
* high-end CMS/product operations look.

### Secondary Theme

Dark Evidence Mode.

Used mainly for:

* Evidence Vault;
* forensic review;
* screenshot-safe compliance mode;
* validation matrices;
* source lineage rooms.

### Typography

* Inter for UI/prose/editorial content.
* JetBrains Mono for evidence metadata only:
  IDs, hashes, timestamps, status codes, packet refs, payload hashes, source refs.

### Color Semantics

* green = verified pass only;
* amber = review/caution;
* red = verified blocker/violation only;
* neutral = inactive/historical/reference;
* no color should imply market direction.

### Component Primitives

* AppShell
* SafetyLockStrip
* OperationalTruthRail
* CommandHero
* ContentInventoryTable
* WriterCanvas
* MediaAssetTray
* DraftInspectorPanel
* ApprovalPacketCard
* PlatformPreviewCard
* DispatchGateMatrix
* EvidenceCard
* AuditTimeline
* StatusToken
* ProvenanceChip
* BlockerStack
* PolicyMatrix
* InspectorRail
* ScreenshotSafeCard
* SEOKeywordPanel
* AIVariantCard
* InternalAlphaArtifactCard
* SourceLineagePanel
* ManualPublishRecordCard

## 10. Technical Framework

Use:

* Vite
* React
* TypeScript
* Tailwind build-time only
* CSS custom properties for tokens
* component system
* Radix/headless primitives where useful
* Lucide or Phosphor icons, bundled
* TanStack Table for inventory/evidence matrices
* Zustand or React context for local UI state
* Vitest
* Testing Library
* Playwright
* Axe accessibility check if practical

Do not use:

* runtime Tailwind CDN;
* Google Fonts runtime;
* Material Symbols remote link;
* external image URLs;
* backend server;
* runtime network;
* browser credential/env read;
* platform APIs;
* provider APIs;
* scheduler/posting/scraping.

All external packages must be installed as build-time dependencies and committed through package manifests/lockfile.

## 11. Repository Placement

Create V5 as a parallel app:

`ui/contentops_v5/`

Do not delete V4.

V4 remains:

* fallback implementation;
* safety contract reference;
* evidence/provenance reference;
* regression source;
* visual anti-pattern reference for default V5 theme.

## 12. Data Model

V5 should use local fixture/view-model contracts first.

Primary fixture:

`ui/contentops_v5/fixtures/contentops_v5_view_model.json`

Core objects:

* `system_state`
* `content_items`
* `draft_packets`
* `research_briefs`
* `media_assets`
* `ai_writer_outputs`
* `seo_metadata`
* `approval_packets`
* `platform_payload_previews`
* `dispatch_gates`
* `evidence_packets`
* `audit_events`
* `policy_boundaries`
* `workflow_cards`
* `manual_publish_records`
* `metrics_records`
* `internal_alpha_artifact_placeholders`

## 13. Implementation Phases

### Task V5-0 — Master Plan and Architecture Commit

Docs only.

Deliver:

* V5 master plan;
* stack decision;
* feature map;
* safety model;
* screen inventory;
* data model;
* design token plan;
* migration plan;
* acceptance criteria;
* implementation backlog.

No source code.

### Task V5-1 — Scaffold + Design System Foundation

Build:

* Vite React TypeScript app under `ui/contentops_v5/`;
* package manifests;
* Tailwind build-time config;
* CSS token system;
* AppShell;
* route system;
* shared navigation;
* safety strip;
* inspector rail;
* status tokens;
* fixtures;
* tests proving no runtime network/CDN/credentials.

No full screen implementation yet unless minimal shell demo.

### Task V5-2 — Five Flagship Screens

Build:

* Command Center;
* Content Inventory;
* Writer Studio with Media Tray;
* Approval Queue + Dispatch Control;
* Evidence Vault dark mode.

Use local fixtures only.

### Task V5-3 — AI Writer + SEO Layer UI Contract

Build:

* AI Writer panel;
* SEO keyword panel;
* variant cards;
* audience modes;
* editorial score;
* platform fit;
* prompt contract fixtures;
* output schema;
* guardrail tests.

No provider calls.

### Task V5-4 — Future Internal Alpha Artifact Intake Contract

Build:

* artifact intake placeholder screen;
* artifact schema;
* readiness gate;
* local fixture examples;
* blocked states;
* UI tests.

No actual internal alpha reads until approved by separate task.

### Task V5-5 — Platform Preview + Manual Publish Workflow

Build:

* dry-run platform preview;
* manual publish checklist;
* manual URL/metrics record;
* payload hash view;
* no live posting tests.

### Task V5-6 — Calendar + Workflow Board

Build:

* manual workflow board;
* lane states;
* manual status transitions;
* no scheduler/live state.

### Task V5-7 — Visual Export / Screenshot-Safe Mode

Build:

* redacted screenshot views;
* report cards;
* internal review snapshots.

### Task V5-8 — Browser QA + Visual Polish

Run:

* Playwright screenshots;
* responsive QA;
* visual polish;
* accessibility checks;
* source audit.

## 14. Acceptance Criteria

V5 is not accepted until:

* no runtime network;
* no CDN;
* no external fonts;
* no external image URLs;
* no platform API;
* no provider API;
* no credential/env reads;
* no scheduler;
* no live posting;
* no scraping;
* no autonomous replies/DMs;
* no public-ready fake content;
* no financial advice/signal/trading language;
* every blocked state explains why;
* every AI output is review-only;
* every artifact-backed item is blocked unless a real approved artifact exists;
* every future live feature is visibly gated;
* every screenshot is credible, readable, and no-secret;
* tests prove constraints;
* browser QA screenshots are inspected.

## 15. Final V5 Operating Principle

Build the product as if it will eventually support real supervised distribution, but keep every live edge behind visible gates.

AI may improve communication.
AI may not create authority.

Internal alpha data may become content basis later.
It may not be assumed now.

Platform payloads may be shaped.
They may not be posted.

Media may be attached in UI mock.
It may not be uploaded externally.

Evidence may support approval.
It may not bypass human approval.

Capital Chronicle ContentOps V5 should feel world-class because the system is serious: not faster hype, not louder predictions, but clearer evidence, cleaner gates, safer writing, better SEO, and visible research maturity.
