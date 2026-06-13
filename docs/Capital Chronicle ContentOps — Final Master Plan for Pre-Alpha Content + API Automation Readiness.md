# Capital Chronicle ContentOps — Final Master Plan for Pre-Alpha Content + API Automation Readiness

## 0. Owner Decision

Capital Chronicle ContentOps should continue building aggressively during the two-week internal-alpha wait.

The project should not remain passive.

However, the next build direction is not “fully automated live posting now.”

The correct owner decision is:

**Build API automation readiness now. Delay authenticated live posting until explicit live-gate approval, platform by platform.**

This means ContentOps should build:

* grounded research brief contracts;
* draft review packets;
* canonical social post object;
* platform adapter contracts;
* dry-run renderers;
* approval ledger;
* kill switch;
* redacted audit log;
* mock publishing flow;
* metrics-readiness contracts;
* platform capability registry.

But it should not yet build:

* credential loading;
* authenticated platform posting;
* autonomous scheduling;
* autonomous replies/DMs;
* scraping;
* platform write APIs;
* fully automated public publishing;
* fake Capital Chronicle alpha content.

The strategic target is:

**supervised API publishing with explicit human approval, not autonomous posting.**

## 1. Current Baseline

Repo:

`A:\Capital Chronicle\tools\cc-live-contentops`

Current accepted capability state:

* 0075/0075A documented the pre-alpha general/process and grounded-news strategy.
* 0076 created the grounded research brief schema and deterministic validator.
* 0077 created the draft review packet schema and deterministic validator.
* The system can now validate manually supplied research context and manually supplied/LLM-assisted drafts.
* The system still does not call web/search/provider APIs.
* The system still does not call platform APIs.
* The system still does not read credentials.
* The system still does not post, schedule, reply, DM, scrape, or auto-approve.

Important distinction:

The repo is no longer “do nothing until alpha.”

It is now:

**local-first automation-readiness buildout, with live execution disabled until explicit gates pass.**

## 2. Strategic Content Model

ContentOps now has three conceptual lanes.

### Lane A — Pre-Alpha General / Process Content

Purpose:

Build audience and trust before internal alpha by explaining the discipline behind Capital Chronicle.

Allowed themes:

* build-in-public;
* macro education;
* data sufficiency;
* forecast readiness;
* failure forensics;
* product philosophy;
* why “no forecast” can be the correct output;
* why Capital Chronicle is not a signal service.

This lane does not require Capital Chronicle alpha artifacts.

It must not claim artifact-backed output.

### Lane B — Grounded News / Research Context Content

Purpose:

Use current real-world news and public sources as hooks for timely content.

Core rule:

**News is a hook, not a signal.**

A current event may be used to explain:

* why data quality matters;
* why a macro claim is not forecast-ready;
* how official sources should be checked;
* why markets may overreact to incomplete information;
* what uncertainty remains;
* what evidence would be required before a serious thesis exists.

A current event must not be used to say:

* buy/sell/hold;
* long/short;
* target price;
* “this means X asset will move”;
* “our model predicts”;
* “our signal says”;
* “Capital Chronicle alpha says...”;
* “watch this level” as actionable framing.

This lane supports real content, but only as:

* source-cited;
* educational;
* general/process;
* non-advisory;
* non-signal;
* non-artifact-backed unless real approved artifacts exist.

### Lane C — Future Artifact-Backed Capital Chronicle Content

Purpose:

Turn real approved Capital Chronicle alpha artifacts into social/newsletter packets later.

Blocked until:

* real Capital Chronicle internal-alpha artifacts exist;
* artifact spec exists;
* source artifact IDs exist;
* lineage/freshness/limitations exist;
* DQR/data sufficiency/forecast readiness states are explicit;
* missing/proxy/degraded data is explicit;
* no financial advice/signal/execution language exists.

This lane must route through real-artifact intake and never directly to public-ready.

## 3. Content Safety Rules

Always block:

* buy/sell/hold;
* position sizing;
* entries/exits;
* price targets;
* guaranteed prediction;
* signal-service framing;
* AI trading bot framing;
* broker/order/execution language;
* “model says buy/sell”;
* “our alpha says” before real artifacts exist;
* unsupported numeric market claims;
* fake performance;
* fixture/demo content made public-postable;
* raw vendor data redistribution;
* anything implying Capital Chronicle alpha exists before it does.

Every allowed content packet must remain:

* educational/general/process unless artifact-backed;
* source-cited when factual/current;
* manually reviewable;
* non-advisory;
* non-signal;
* explicit about limitations.

## 4. Automation Strategy

The project should pivot from “manual publish guide” to **API automation readiness**.

The central architecture should be:

1. Grounded research brief.
2. Draft review packet.
3. Canonical social post object.
4. Per-platform dry-run rendering.
5. Human approval ledger.
6. Kill switch check.
7. Mock adapter execution.
8. Redacted audit event.
9. Manual or later supervised live post.
10. Metrics capture.

The key transition is:

**from draft review packets to platform-ready, dry-run post payloads.**

But “platform-ready payload” does not mean “posted.”

It means:

* exact text/media shape;
* per-platform constraints;
* per-platform warnings;
* policy flags;
* required approval state;
* no external call;
* no credential use.

## 5. Platform Strategy

### Telegram

Role:

First live-pilot candidate later.

Why:

* technically simplest;
* Bot API is mature;
* a channel is controlled by the operator;
* lower app-review friction.

Build now:

* Telegram adapter contract;
* dry-run payload renderer;
* channel/post shape;
* mock `sendMessage` / `sendPhoto` response model;
* rate-limit placeholder;
* kill-switch gating.

Live later:

* supervised Telegram channel post only after approval ledger and kill switch pass.

Do not build yet:

* autonomous bot replies;
* DMs;
* community engagement automation.

### X

Role:

High-value short-form distribution and conversation surface.

Build now:

* X adapter contract;
* text length/media constraints;
* `made_with_ai` / disclosure field support where relevant;
* duplicate/cross-post detection;
* mock post response;
* cost/rate-limit metadata placeholders.

Live later:

* after alpha or after separate explicit supervised live pilot decision;
* only with per-post approval;
* no autonomous replies/DMs.

Risks:

* cost/access changes;
* automation policy sensitivity;
* duplicate cross-posting;
* finance-adjacent language risk.

### LinkedIn

Role:

Professional founder/product positioning.

Build now:

* LinkedIn post contract;
* organization/member distinction;
* image/video/document/article shape;
* review/app-access checklist;
* dry-run renderer;
* mock post response;
* analytics-readiness contract.

Live later:

* after app/access path is clear;
* likely after internal alpha;
* organization posting should be treated as review-dependent.

Risks:

* app review;
* permissions;
* company page/admin requirements;
* professional reputation risk.

### Facebook Page

Role:

Secondary distribution surface, likely paired with Instagram/Meta wave.

Build now:

* Page post contract;
* page identity/account requirements placeholder;
* dry-run renderer;
* mock post response;
* insights-readiness contract.

Live later:

* after Meta app review/business verification path is understood;
* not first live target.

Risks:

* app review;
* business verification;
* page permissions;
* Meta policy changes.

### Instagram

Role:

Visual/card/carousel distribution later.

Build now:

* Instagram content contract;
* media requirements placeholder;
* public media URL constraint placeholder;
* account type requirements placeholder;
* dry-run renderer;
* mock post response.

Live later:

* after a focused official-doc verification pass;
* likely alongside Facebook Page integration;
* not a pre-alpha live target.

Risks:

* professional/business/creator account constraints;
* media hosting requirement;
* app review;
* visual production overhead.

### TikTok

Role:

Last platform to integrate.

Build now:

* TikTok direct-post/upload contract;
* video/photo media model;
* app-audit checklist;
* private-only unaudited restriction note;
* mock post response;
* demo-video/app-review readiness notes.

Live much later:

* after audit/app approval path is viable;
* after content format strategy exists;
* likely not useful for early macro text content.

Risks:

* audit restrictions;
* video-first format;
* private-only unaudited flow;
* high moderation/reputation risk.

## 6. Build-Now vs Later Matrix

| Capability                         | Build Now | Build Later                                 | Do Not Build Yet |
| ---------------------------------- | --------- | ------------------------------------------- | ---------------- |
| Grounded research brief validation | Yes       | —                                           | —                |
| Draft review packet validation     | Yes       | —                                           | —                |
| Canonical social post schema       | Yes       | —                                           | —                |
| Platform adapter contracts         | Yes       | —                                           | —                |
| Dry-run renderers                  | Yes       | —                                           | —                |
| Mock adapters                      | Yes       | —                                           | —                |
| Approval ledger                    | Yes       | —                                           | —                |
| Kill switch                        | Yes       | —                                           | —                |
| Redacted audit log                 | Yes       | —                                           | —                |
| Credential envelope design         | Yes       | —                                           | —                |
| Credential reads                   | —         | Later, explicit task                        | Not now          |
| Live platform API posting          | —         | Later, explicit platform-by-platform GO     | Not now          |
| Read-only metrics API              | —         | Later, after contracts/credentials policy   | Not now          |
| Scheduling                         | —         | Later, after supervised posting proves safe | Not now          |
| Autonomous replies/DMs             | —         | —                                           | Do not build     |
| Fully autonomous posting           | —         | —                                           | Do not build     |
| Scraping platform metrics          | —         | —                                           | Do not build     |

## 7. Live API Gate

Before any live API integration, all of these must exist:

1. Explicit operator GO for one platform.
2. New task label naming the platform and live scope.
3. Credential policy.
4. Secret redaction tests.
5. Dry-run adapter contract already passing.
6. Approval ledger already passing.
7. Kill switch defaulting to disabled.
8. Redacted request/response audit.
9. Rate-limit/error handling.
10. Manual fallback.
11. Rollback plan.
12. No autonomous replies/DMs.
13. No platform credentials printed, logged, copied, or committed.
14. No public posting without per-post approval.

Live should be enabled in this order:

1. Telegram supervised channel posting.
2. X supervised posting.
3. LinkedIn supervised posting.
4. Facebook Page / Instagram supervised posting.
5. TikTok last.

## 8. Revised Task Roadmap

### Completed

#### 0075 / 0075A — Master Plan + Grounded News Lane

Status:

Complete.

Outcome:

* documented pre-alpha general/process lane;
* added grounded-news research context lane;
* established “news is a hook, not a signal”;
* preserved artifact-backed wait-state.

#### 0076 — Grounded Research Brief Schema

Status:

Complete.

Outcome:

* local JSON schema;
* deterministic validator;
* valid/invalid fixtures;
* no provider/search calls;
* no content generation.

#### 0077 — Draft Review Packet

Status:

Complete.

Outcome:

* review-only draft packet schema;
* deterministic validator;
* forbidden-language and source-linkage checks;
* no public-ready copy;
* no auto-approval.

### New Roadmap

#### 0078 — Local Platform Adapter Contracts and Dry-Run Renderer

Task label:

`TASK_CONTENTOPS_0078_LOCAL_PLATFORM_ADAPTER_CONTRACTS_AND_DRY_RUN_RENDERER_V0`

Objective:

Define platform adapter contracts for X, LinkedIn, Telegram, Facebook Page, Instagram, and TikTok. Add a deterministic dry-run renderer that maps an approved draft review packet into per-platform payload previews.

Allowed:

* schemas;
* platform capability registry;
* dry-run payload generation;
* media/text/character constraints;
* platform warnings;
* no network;
* no credentials;
* no real API;
* tests;
* docs.

Forbidden:

* no live platform calls;
* no credentials/env reads;
* no scheduler;
* no posting;
* no API clients;
* no scraping;
* no auto-approval;
* no replies/DMs.

Acceptance:

* dry-run payloads render for all six platforms;
* unsupported content fails safely;
* platform warnings are explicit;
* output remains not-public-postable;
* approval is required before any later publish step;
* tests pass;
* no external capability added.

#### 0079 — Approval Ledger, Kill Switch, and Redacted Audit Contract

Task label:

`TASK_CONTENTOPS_0079_LOCAL_APPROVAL_LEDGER_KILL_SWITCH_AND_AUDIT_CONTRACT_V0`

Objective:

Create the authority layer for future supervised publishing.

Build:

* append-only approval ledger;
* approval state model;
* kill switch defaulting to disabled;
* redacted audit event schema;
* would-post event model;
* operator approval record;
* no-secret logging contract.

Approval states:

* `draft_review_only`
* `platform_dry_run_ready`
* `operator_review_required`
* `operator_approved_for_mock_publish`
* `operator_approved_for_live_publish_later`
* `blocked`
* `revoked`

Acceptance:

* no post can proceed without ledger approval;
* kill switch blocks all publish actions by default;
* audit logs never contain secrets;
* revocation is supported;
* tests prove blocked paths fail closed.

#### 0080 — Mock Adapter Publish Flow and Metrics Capture Dry Run

Task label:

`TASK_CONTENTOPS_0080_LOCAL_MOCK_ADAPTER_PUBLISH_FLOW_AND_METRICS_CAPTURE_DRY_RUN_V0`

Objective:

Wire the full flow against mock transports only.

Flow:

1. Valid grounded research brief.
2. Valid draft review packet.
3. Canonical social post.
4. Platform dry-run payload.
5. Approval ledger check.
6. Kill switch check.
7. Mock publish.
8. Mock post URL.
9. Mock metrics capture.
10. Redacted audit record.

Acceptance:

* all six platforms can run mock publish dry-run;
* kill switch blocks when disabled;
* missing approval blocks;
* no credentials;
* no network;
* no real posting;
* no public-ready status;
* metrics are simulated/manual placeholders only.

#### 0081 — Platform Official Docs Verification Pack

Task label:

`TASK_CONTENTOPS_0081_PLATFORM_OFFICIAL_DOCS_VERIFICATION_PACK_V0`

Objective:

Create a repo-local advisory docs pack summarizing official platform requirements for each integration.

This should be produced from operator-supplied or separately gathered official docs, not from repo network calls.

Focus:

* X pricing/access/write endpoints;
* LinkedIn Posts API/app review;
* Telegram Bot API;
* Facebook Page publishing/insights;
* Instagram content publishing/account constraints;
* TikTok Content Posting API/audit/private-only restrictions.

Acceptance:

* each platform has a verification checklist;
* unknowns are explicitly marked;
* docs do not become runtime authority;
* no network calls inside repo.

#### 0082 — Credential Envelope and Secret Policy Design

Task label:

`TASK_CONTENTOPS_0082_CREDENTIAL_ENVELOPE_AND_SECRET_POLICY_DESIGN_V0`

Objective:

Design how credentials will be handled later without reading credentials now.

Build:

* credential envelope schema;
* redaction rules;
* environment variable name conventions;
* token rotation checklist;
* audit redaction tests using fake tokens;
* no real env reads;
* no live credentials.

Acceptance:

* no actual secret is accessed;
* fake token tests prove redaction;
* platform credential requirements are mapped;
* live credential use remains blocked until explicit GO.

#### 0083 — First Supervised Live Pilot Candidate: Telegram Design Gate

Task label:

`TASK_CONTENTOPS_0083_TELEGRAM_SUPERVISED_LIVE_PILOT_DESIGN_GATE_V0`

Objective:

Prepare, but not execute, a Telegram supervised live pilot plan.

Build:

* exact approval phrase;
* dry-run evidence requirements;
* kill switch state requirements;
* credential policy;
* rollback plan;
* operator checklist;
* no actual bot token use.

Acceptance:

* plan is ready for explicit live GO;
* no credential read;
* no Telegram API call;
* no post.

Only after this should any live Telegram task be considered.

## 9. Owner Operating Mode During the Two-Week Wait

Jim can manually post content in parallel.

Recommended manual posting strategy:

* write grounded-news/process content manually;
* use official/reputable sources;
* keep claims educational;
* avoid market calls;
* avoid artifact-backed claims;
* avoid “Capital Chronicle alpha says”;
* log URLs manually if useful.

Meanwhile, IDE/Cline should build the automation-readiness stack locally.

The two tracks are separate:

### Manual Public Track

Jim writes and posts manually.

Repo does not post.

### Local Automation-Readiness Track

Cline builds schemas, validators, dry-runs, mock adapters, ledgers, and audit contracts.

Repo does not call APIs.

## 10. Platform Launch Order

### First: Telegram

Best early live-pilot candidate after readiness gates.

Reason:

lowest friction, controlled channel, simple Bot API.

### Second: X

Good for audience growth, but cost/policy-sensitive.

Needs:

anti-spam controls, duplicate detection, automation disclosure policy, careful finance wording.

### Third: LinkedIn

High strategic value.

Needs:

review/access clarity, page/admin setup, professional positioning.

### Fourth: Facebook Page + Instagram

Treat as Meta wave.

Needs:

business verification/account constraints/media hosting verification.

### Last: TikTok

Highest friction.

Needs:

content format strategy, audit path, video/photo workflow.

## 11. Non-Negotiables

ContentOps must never become:

* a financial advice engine;
* a buy/sell/hold generator;
* a trading signal bot;
* an execution/broker/order system;
* a fake alpha marketing machine;
* a cross-platform spammer;
* an autonomous reply/DM bot.

Automation is allowed only as:

* supervised;
* logged;
* reversible;
* kill-switch protected;
* per-platform constrained;
* source-aware;
* approval-gated.

## 12. Final Recommendation

Proceed with API automation readiness immediately.

Do not proceed with live authenticated posting yet.

Replace the old 0078 manual guide task with:

`TASK_CONTENTOPS_0078_LOCAL_PLATFORM_ADAPTER_CONTRACTS_AND_DRY_RUN_RENDERER_V0`

Then run:

1. `TASK_CONTENTOPS_0079_LOCAL_APPROVAL_LEDGER_KILL_SWITCH_AND_AUDIT_CONTRACT_V0`
2. `TASK_CONTENTOPS_0080_LOCAL_MOCK_ADAPTER_PUBLISH_FLOW_AND_METRICS_CAPTURE_DRY_RUN_V0`
3. `TASK_CONTENTOPS_0081_PLATFORM_OFFICIAL_DOCS_VERIFICATION_PACK_V0`
4. `TASK_CONTENTOPS_0082_CREDENTIAL_ENVELOPE_AND_SECRET_POLICY_DESIGN_V0`
5. Later: Telegram supervised live pilot design gate.

The final operating principle is:

**Build the automation rails now. Keep the train parked until the approval, credential, audit, kill-switch, and platform gates are real.**
