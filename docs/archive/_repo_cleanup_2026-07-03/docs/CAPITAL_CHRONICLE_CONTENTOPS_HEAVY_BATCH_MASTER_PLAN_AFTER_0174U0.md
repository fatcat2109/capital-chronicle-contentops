# Capital Chronicle ContentOps — Heavy Batch Master Plan After 0174U0

## 1. Executive Decision

ContentOps must pivot from narrow Telegram/approval micro-tasks into heavy product capability batches.

The approved direction is:

**Local-first supervised multi-platform editorial operating system for Capital Chronicle content.**

The product must support:

* multi-platform content planning;
* bounded AI Writer and SEO assistance;
* grounded news / idea intake;
* Substack/newsletter manual export;
* X / Telegram / Substack primary publishing triangle;
* LinkedIn as secondary professional credibility;
* Threads / Instagram / Facebook as later expansion;
* Capital Chronicle ingestion/headline artifact context as future idea input;
* internal-alpha content readiness reports;
* deterministic approval, audit, revocation, dispatch revalidation, and kill-switch gates;
* UI binding only after contracts are stable.

Stop now:

* Telegram-only task treadmill;
* isolated tiny repair tasks with no roadmap continuation;
* UI/dashboard polish without new domain contracts;
* any claim of live readiness before explicit gates.

## 2. Current Accepted Baseline

Repo:

`A:\Capital Chronicle\tools\cc-live-contentops`

GitHub:

`fatcat2109/capital-chronicle-contentops`

Branch:

`master`

Accepted HEAD:

`ae424c27c69338aa189edaf23f8240151cbff6ac`

Accepted authority chain:

* `0174ED`: exact approval ledger / payload hash binding.
* `0174EE`: deterministic dispatch outbox idempotency, still no dispatch.
* `0174TG`: Telegram remote operator inbox local contract.
* `0174TH`: Telegram review challenge/reply validation.
* `0174TI`: challenge validation to approval-ledger candidate.
* `0174TJ`: candidate to local approval ledger recording fact.
* `0174U0`: heavy strategy recon and roadmap reset.

## 3. Product Architecture

The product should be organized around these core systems:

1. **Platform Universe Registry**
   Defines platform roles, payload classes, constraints, live eligibility, manual-export defaults, and future-gate requirements.

2. **Content Idea Intake**
   Accepts operator ideas, grounded news context, internal-alpha artifacts, and future Capital Chronicle headline/context packets.

3. **Editorial Brief + AI Writer**
   Produces bounded, review-only draft assistance with SEO/hook/title/platform-fit scoring. It must preserve limitations and never become source authority.

4. **Draft Inspector**
   Checks claims, citations, limitations, no-advice/no-signal rules, source needs, platform eligibility, and review state.

5. **Platform Payload Preview**
   Creates exact payload candidates for X, Telegram channel, Substack/newsletter, LinkedIn, Threads, Instagram, Facebook, and later video platforms.

6. **Approval / Ledger / Audit Chain**
   Already partially built. Needs revocation/expiration, redacted immutable audit ledger, dispatch revalidation, and kill-switch/rate/retry/budget policy.

7. **Manual Publish + Metrics**
   Records manual publish destination URL, exported hash, timestamp, operator ref, and manual metrics. No scraping or platform API by default.

8. **Capital Chronicle Artifact Connector**
   Reads ingestion/headline/artifact context read-only and converts it into idea/context packets, not authority.

9. **Internal Alpha Readiness Reporting**
   Generates artifact intake reports, content eligibility reports, claim-risk reports, and platform eligibility reports before public artifact-backed content.

10. **V5 UI Binding**
    Binds stable contracts to the UI later. UI does not invent capability.

## 4. Platform Strategy

Primary triangle:

* **X**: fast public narrative distribution.
* **Telegram**:

  * Remote Operator Inbox: review/approval control.
  * Channel Dispatch Destination: future public/community output.
* **Substack**: owned long-form authority and newsletter publishing.

Secondary:

* **LinkedIn**: institutional credibility and professional distribution.

Expansion:

* **Threads**
* **Instagram**
* **Facebook Page**

Later only:

* **TikTok**
* **YouTube / Shorts**

Build-now defaults:

* preview only;
* manual export;
* exact payload hashes;
* no live API;
* no credentials;
* no scheduler;
* no autonomous posting.

## 5. Content Lanes

### Lane A — Pre-alpha general/process

Allowed now:

* build-in-public;
* process transparency;
* why missing data blocks forecasts;
* source trust education;
* no-advice explanations.

### Lane B — Grounded news / research context

Allowed carefully:

* headline as context;
* “what evidence would be needed” framing;
* official-source checklist;
* uncertainty and limitation explanation.

Blocked:

* trade direction;
* signal language;
* “our model predicts”;
* target levels;
* watchlist-style calls.

### Lane C — Future Capital Chronicle artifact-backed content

Allowed only after approved artifacts exist:

* artifact ID;
* lineage;
* freshness;
* DQR / data sufficiency;
* missing/degraded/proxy labels;
* readiness state;
* explicit limitations;
* non-advisory framing.

## 6. Heavy Batch Roadmap

### 0174U1 — Platform Universe Registry V2 + Primary Payload Classes

Normalize platform roles, payload classes, live gates, no-live defaults, manual-export defaults, and primary channel taxonomy.

This should be next.

### 0174U2 — Primary Platform Payload Preview Contracts

Build preview contracts for X, Telegram channel, Substack/newsletter, LinkedIn, Threads, Instagram, Facebook Page.

No API calls.

### 0174U3 — Substack Newsletter + Manual Export Contract

Build newsletter issue blueprint, markdown export, SEO metadata, citation/limitation sections, manual publish checklist, and export hash.

No Substack API or browser/session automation.

### 0174U4 — Content Idea Packet + Local Intent Parser

Convert operator idea / grounded news / future artifact context into deterministic idea packet.

No provider LLM calls.

### 0174U5 — Editorial Brief + AI Writer Output Contract

Create bounded writer output schema: title candidates, hooks, SEO keywords, draft variants, audience modes, risk warnings, citation/limitation preservation.

Manual external LLM mode only.

### 0174U6 — Idea to Multi-Platform Draft Dry Run

Compose idea packet + editorial brief + platform payload previews + review packet.

Draft only.

### 0174U7 — Capital Chronicle Ingestion / Headline Idea Connector Precheck

Read ingestion repo local artifacts read-only and produce context/idea packets.

No authority promotion.

### 0174U8 — Internal Alpha Artifact Intake Contract

Create artifact intake, content eligibility, claim-risk, source/citation, and alpha-safety reports.

### 0174U9 — Redacted Immutable Audit Ledger V2

Create cross-system audit ledger spanning approvals, manual export, publish records, metrics, and safety gates.

### 0174UA — Approval Revocation / Expiration Contract

Append-only revocation and expiration facts for recorded approvals.

### 0174UB — Dispatch Outbox Revalidation Gate

Revalidate exact payload hash, approval validity, revocation, expiration, platform class, kill switch, and safety gates before any future dispatch.

### 0174UC — Kill Switch / Rate / Retry / Budget Policy

Create deterministic local policy engine for platform-independent blocking, retry budget, rate budget, and emergency halt.

### 0174UD — Manual Publish + Metrics Report Contract

Record manual publish URL, export hash, operator ref, timestamp, manual metrics, and performance summary.

No scraping/API by default.

### 0174UE — V5 Read-Model Binding

Only after above core contracts exist. UI binding, not visual redesign.

## 7. New Repair Task Policy

Every repair task must include:

1. blocker repair;
2. focused validation;
3. relevant regression validation;
4. confirmation no unrelated scope drift;
5. roadmap restoration;
6. next heavy batch task recommendation;
7. final evidence packet.

Repair tasks must not end with “fixed typo” only.

## 8. Next Task

Run:

`TASK_CONTENTOPS_0174U1_PLATFORM_UNIVERSE_REGISTRY_V2_AND_PRIMARY_PAYLOAD_CLASSES_CONTRACT_V0`

Why:

* platform vocabulary is prerequisite for AI Writer, SEO, Substack, ingestion connector, internal-alpha reports, and future UI binding;
* it reconciles Telegram authority work with the actual multi-platform product;
* it remains deterministic, local-first, no-live, and testable.
