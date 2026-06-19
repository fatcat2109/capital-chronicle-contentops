# 0174U0 Heavy Strategy Recon Report

## 1. Executive conclusion

ContentOps should build **platform universe registry v2 + primary payload classes** next.

Why:

- Current repo has strong approval authority primitives from 0174ED through 0174TJ.
- Latest strategy authority says product must pivot from Telegram-only authority work to supervised multi-platform content operations.
- Platform scope must be normalized before AI Writer, SEO, Substack, ingestion connector, and UI binding can safely compose.

Build next:

1. canonical platform universe v2;
2. primary platform roles for X, Telegram destination, Telegram remote operator inbox, Substack;
3. secondary/expansion/later platform defaults;
4. platform payload class taxonomy;
5. no-live payload preview defaults;
6. route from existing payload hashes/approval facts into multi-platform review packets.

Stop:

- Telegram-only micro-task treadmill with no roadmap restoration.
- UI/dashboard polish not backed by domain contracts.
- Any “live readiness” work that hydrates secrets, reads env, polls, posts, schedules, scrapes, or calls providers without explicit gate.

Future-gated:

- live X/LinkedIn/Meta/TikTok/YouTube posting;
- provider LLM calls;
- Substack browser/session automation;
- autonomous scheduling;
- ingestion artifact authority promotion;
- public artifact-backed claims before approved artifacts exist.

## 2. Current ContentOps baseline

- Repo: `fatcat2109/capital-chronicle-contentops`
- Path: `A:\Capital Chronicle\tools\cc-live-contentops`
- Branch: `master`
- Starting HEAD: `f328d713d798387fc8545636fb8e4a095f607047`
- Mode: docs/report only

Accepted authority chain:

| Milestone | Files | What it proves |
|---|---|---|
| 0174ED | `approval_ledger_payload_hash_contract` | exact payload-hash binding and approval-scope invariants |
| 0174EE | `dispatch_outbox_idempotency_contract` | dispatch outbox item identity/idempotency without dispatch |
| 0174TG | `telegram_remote_operator_inbox_contract` | local inbound operator-review message contract; no Telegram polling/API |
| 0174TH | `telegram_review_challenge_contract` | local challenge and redacted reply validation contract |
| 0174TI | `telegram_approval_ledger_candidate_contract` | valid challenge result to local approval-ledger candidate |
| 0174TJ | `approval_ledger_candidate_recording_contract` | deterministic candidate-to-ledger recording fact, duplicate suppression |

What remains missing:

- unified platform universe registry v2;
- primary payload preview contracts for X/Telegram/Substack;
- Substack manual export/newsletter issue contract;
- content idea packet and intent parser;
- editorial brief + AI writer output contract;
- Capital Chronicle ingestion/headline idea connector precheck;
- internal alpha artifact intake contract;
- redacted immutable audit ledger v2 spanning manual publish and metrics;
- approval revocation/expiration gate;
- dispatch outbox revalidation before any dispatch;
- kill switch/rate/retry/budget policy;
- manual publish + metrics report contract;
- V5 read-model/UI binding later.

## 3. Product direction reconciliation

The latest product direction is not “Telegram bot.” It is **local-first supervised content distribution OS**.

`docs/CAPITAL_CHRONICLE_CONTENTOPS_RECONCILED_FINAL_PRODUCT_MASTER_PLAN_AFTER_0174AO.md` defines one approved operator action as dispatching only a prevalidated, evidence-backed, platform-constrained content packet. It also defines content lanes, bounded LLM writer, deterministic safety compiler, canonical social post, platform payload compiler, approval packet, supervised dispatch controller, credential boundary, redacted audit ledger, and metrics loop.

`docs/governance/CONTENTOPS_PRELAUNCH_OPERATING_POLICY.md` now elevates V5 as active product surface, keeps V4 as fallback/baseline, keeps live providers/platforms disabled by default, and requires operator GO, kill switch, redacted audit, rate/error handling, and manual fallback for any future dispatch.

Conflict resolution:

- Telegram-first work remains valuable as authority substrate.
- Telegram must split into two roles: remote operator inbox and channel dispatch destination.
- Multi-platform payload strategy supersedes narrow Telegram sequencing.
- V5 awareness matters, but UI must not invent backend capability.
- Future repair tasks must restore roadmap state, not end at typo/test fix.

## 4. Platform strategy

| Platform | Role | Build-now scope | Later live scope | Blockers / constraints | Default |
|---|---|---|---|---|---|
| X | primary velocity/distribution | payload class, length/media/link preview, manual preview, cost/budget metadata | supervised post creation via X API | paid access/pricing/account approval; developer policy volatility | no live |
| Telegram Remote Operator Inbox | approval/review loop | local inbound message model already exists | optional read-only poll/webhook gate later | credentials, privacy, spoofing, polling/webhook approval | no live |
| Telegram Channel Dispatch Destination | controlled community distribution | channel payload preview and exact hash binding | supervised sendMessage/sendPhoto after explicit gate | bot admin rights, rate limits, content policy | no live |
| Substack/newsletter | owned long-form authority | markdown/manual export, newsletter issue blueprint, SEO metadata | manual publish record; avoid unofficial API | no official public publish API; browser/session automation unsafe | manual export |
| LinkedIn | professional credibility | professional tone preview, company/personal variants | supervised Posts API after app/product access | OAuth, `w_organization_social`, page admin role, app review/product approval | no live |
| Threads | conversational expansion | short-form preview, link/citation preservation | Threads API after Meta gate | app review, permissions, rate limits | no live |
| Instagram | visual expansion | asset package export, caption preview | Content Publishing API after app review | professional account, public media URL, `instagram_content_publish`, Meta review | no live |
| Facebook Page | secondary Page distribution | Page post preview | Graph API Page publish after app review | Page token, `pages_manage_posts`, review | no live |
| TikTok | later video | video brief/rights checklist only | Content Posting API after audit | domain verification, `video.publish`, audit, private/testing restrictions | future |
| YouTube | later video/Shorts | video script/metadata checklist only | YouTube Data API upload after OAuth/consent/quota approval | OAuth, quota, resumable upload, media rights | future |

Official-doc constraints researched:

- Telegram Bot API supports bot methods like sending messages/media and updates, but ContentOps must not call it without a live gate: https://core.telegram.org/bots/api
- X developer docs/portal govern API access and current pricing; posting is access/cost constrained: https://developer.x.com/
- LinkedIn API posting requires approved permissions/products and OAuth: https://learn.microsoft.com/linkedin/
- Meta Instagram/Facebook publishing depends on Graph API permissions and app review: https://developers.facebook.com/docs/
- Threads API exists under Meta platform docs and requires Meta app/permissions/review: https://developers.facebook.com/docs/threads/
- TikTok Content Posting API direct post requires product access, scopes, domain verification, and audit: https://developers.tiktok.com/doc/content-posting-api-get-started/
- YouTube Data API upload uses `videos.insert`, OAuth, quota, and upload constraints: https://developers.google.com/youtube/v3/docs/videos/insert

## 5. Content model

### Lane A — pre-alpha general/process

Allowed now:

- build-in-public notes;
- process transparency;
- why missing data blocks forecasts;
- source trust education;
- no-advice explanatory content.

### Lane B — grounded news / research context

Allowed carefully:

- headline as context, not signal;
- “what evidence would be needed” framing;
- uncertainty and limitation explanation;
- official-source checklist.

Forbidden:

- market direction;
- target prices;
- “our model predicts”;
- watch-level/trading-call language.

### Lane C — future artifact-backed Capital Chronicle content

Allowed only after approved artifacts exist:

- artifact id;
- lineage;
- freshness;
- DQR/sufficiency/readiness;
- missing/degraded/proxy labels;
- review state;
- non-advisory framing.

Claim-risk taxonomy:

- `process_claim_low_risk`
- `source_context_claim`
- `market_context_claim_review_required`
- `artifact_backed_claim_requires_packet`
- `forecast_adjacent_claim_high_risk`
- `advice_or_signal_forbidden`

Source-needed taxonomy:

- `none_for_process`
- `public_official_source_required`
- `news_source_plus_official_context_required`
- `capital_chronicle_artifact_required`
- `freshness_manifest_required`
- `dqr_readiness_required`

Review states:

- `idea_only`
- `brief_review_only`
- `draft_review_only`
- `platform_preview_only`
- `operator_review_required`
- `approved_for_manual_export`
- `blocked`

## 6. AI Writer + SEO roadmap

AI Writer should be bounded editorial assistant, not authority.

Local deterministic output contract:

- input idea/context packet;
- allowed content lane;
- required citations/limitations;
- forbidden claims;
- title/hook candidates;
- platform-fit scores;
- SEO keyword clusters;
- editorial risk warnings;
- deterministic validation output.

Manual external LLM mode:

- operator may paste external LLM output into review packet;
- system validates for hallucinated facts, missing citations, removed limitations, advice/signal language;
- no provider API call.

Future provider gate:

- dedicated module;
- explicit provider authorization;
- no raw secrets in logs;
- prompt/input/output redaction;
- provider budget/rate policy;
- no auto-publish.

SEO model:

- title candidates;
- slug suggestions;
- meta description;
- keyword intent;
- hook type;
- audience mode;
- citation/limitation preservation score;
- no clickbait or unsupported certainty.

Integration rooms:

- Writer Studio: drafts and variants.
- Draft Inspector: safety/citation/limitation checks.
- Approval Queue: exact payload hash approval.
- Platform Preview: channel-specific payloads.
- Evidence Vault: source refs, audit refs, blocker refs.

## 7. Substack / newsletter roadmap

Build manual export first.

Newsletter issue blueprint:

- issue id;
- source packet refs;
- audience mode;
- headline/title/subtitle;
- opening note;
- sections;
- citations;
- limitations;
- CTA;
- SEO metadata;
- platform share snippets;
- manual publish checklist.

Long-form post contract:

- markdown body;
- excerpt;
- canonical title;
- tags;
- image/asset refs;
- citation footer;
- limitation section;
- no-advice disclaimer;
- export hash.

Manual publish record:

- operator id/ref;
- exported hash;
- destination URL after manual entry;
- publication timestamp;
- metrics capture refs.

Default: no live Substack API; no session-cookie/browser automation.

## 8. Capital Chronicle ingestion repo integration

Secondary repo inspected read-only:

- Path: `A:\Capital Chronicle\Headline Raw data local json\capital-chronicle-ingestion`
- Branch: `main`
- HEAD: `6720a9be3932ce43b097e538e95ba0ccedb0f5d7`
- Path exists and is git repo.

Observed context:

- root docs include deep-research source maps, market data source map, economic calendar hierarchy, options/gamma proxy dossier, prediction market dossier, MT5 paper execution safety dossier, audit ledger/lineage patterns, implementation synthesis;
- repo contains `docs/`, `official_sources/`, `schemas/`, `tools/`, `data/`;
- search found DQR, DataNeedRouter, FieldAuthorityMap, coverage gap, source health, freshness/readiness concepts;
- local `.env.local` exists but was not read.

What can become idea/context inputs:

- headline surfaces;
- official source catalogs;
- source family manifests;
- freshness manifests;
- coverage gap reports;
- DQR/data sufficiency summaries;
- forecast readiness summaries;
- candidate official-source surfaces;
- internal alpha readiness reports.

What cannot become authority:

- raw local files without approved artifact packet;
- stale manifests;
- proxy/source candidates;
- DQR blockers;
- internal alpha NOT_READY material;
- any credential/env-dependent output.

Proposed connector:

`Capital Chronicle Artifact / Headline Idea Connector`

Required fields:

- `connector_packet_id`
- `source_repo_head`
- `source_artifact_path`
- `source_artifact_id`
- `lineage_ref`
- `freshness_state`
- `authority_level`
- `content_lane_allowed`
- `dqr_state`
- `forecast_readiness_state`
- `missing_degraded_proxy_labels`
- `citation_refs`
- `limitations_required`
- `idea_only_not_authority`

Current blockers:

- no ContentOps intake schema for ingestion artifacts;
- no stale/fresh authority adapter;
- no DQR/readiness mapping to content eligibility;
- no evidence-packet hash binding for imported context.

## 9. Internal alpha content/report readiness

Before internal alpha, ContentOps should prepare:

- artifact intake checklist;
- content eligibility report;
- source/citation/limitation matrix;
- lane classification;
- claim-risk report;
- platform preview packet;
- no-advice/no-signal validator;
- manual publish checklist;
- audit packet.

Report packet structure:

- intake summary;
- evidence refs;
- content lanes allowed;
- blockers;
- review state;
- draft eligibility;
- platform eligibility;
- limitations;
- alpha-unsafe claims;
- next remediation.

Forbidden alpha-marketing claims:

- “forecast ready” without readiness artifact;
- “validated alpha” without evidence;
- “official signal”;
- guaranteed return / trading advice;
- hidden proxy limitations;
- inflated data coverage.

Manual workflow:

idea/context → intake precheck → editorial brief → writer output → deterministic review → platform preview → approval queue → manual export/publish record → metrics report.

## 10. Heavy batch roadmap

### 0174U1 — Platform Universe Registry V2 + Primary Payload Classes

- Objective: normalize platform roles, payload classes, no-live defaults.
- Likely files: `live_contentops/platform_universe_registry_v2.py`, tests, `docs/automation/0174U1/**`.
- Tests: registry invariants, no-live defaults, platform tiers.
- Deliverables: platform registry packet, payload class matrix.
- Boundaries: no platform APIs, no credentials, no UI.
- Follow-up: primary platform payload preview contracts.

### 0174U2 — Primary Platform Payload Preview Contracts

- Objective: X, Telegram destination, Substack payload previews.
- Tests: character limits, media/link flags, hash stability.
- Boundaries: preview only.
- Follow-up: newsletter/manual export.

### 0174U3 — Substack Newsletter + Manual Export Contract

- Objective: markdown export, issue blueprint, SEO metadata, manual publish record.
- Boundaries: no Substack API/session automation.
- Follow-up: AI Writer/SEO brief.

### 0174U4 — LLM Intent Parser + Content Idea Packet

- Objective: turn operator idea into deterministic content intent.
- Boundaries: no provider calls.
- Follow-up: editorial brief.

### 0174U5 — Editorial Brief + AI Writer Output Contract

- Objective: bounded writer output schema, SEO/hook/platform scoring.
- Boundaries: manual/external mode only.
- Follow-up: idea-to-draft dry run.

### 0174U6 — Idea to Multi-Platform Draft Dry Run

- Objective: idea packet + brief + platform variants + review packet.
- Boundaries: draft review only.
- Follow-up: ingestion connector precheck.

### 0174U7 — Capital Chronicle Ingestion/Headline Idea Connector Precheck

- Objective: read-only local artifact/headline context packet.
- Boundaries: no ingestion mutation, no env, no authority promotion.
- Follow-up: internal alpha artifact intake.

### 0174U8 — Internal Alpha Artifact Intake Contract

- Objective: eligibility report and artifact-backed content gating.
- Boundaries: no marketing claims, no public readiness.
- Follow-up: redacted audit ledger.

### 0174U9 — Redacted Immutable Audit Ledger V2

- Objective: event ledger spanning manual publish, approvals, metrics.
- Boundaries: no secrets/raw vendor payloads.
- Follow-up: approval revocation/expiration.

### 0174UA — Approval Revocation/Expiration Contract

- Objective: invalidate stale/revoked approvals before dispatch.
- Boundaries: no dispatch.
- Follow-up: dispatch outbox revalidation.

### 0174UB — Dispatch Outbox Revalidation Gate

- Objective: recheck hashes, revocation, kill switch, payload class before dispatch.
- Boundaries: no live dispatch.
- Follow-up: kill/rate/retry/budget.

### 0174UC — Kill Switch / Rate / Retry / Budget Policy

- Objective: platform-independent local policy.
- Boundaries: no network.
- Follow-up: manual publish + metrics.

### 0174UD — Manual Publish + Metrics Report Contract

- Objective: record manual URLs/metrics and performance summaries.
- Boundaries: no scraping/API.
- Follow-up: V5 read-model binding.

### 0174UE — V5 Read-Model/UI Binding Later

- Objective: bind V5 to proven contracts only.
- Boundaries: no design polish unless contract-backed.
- Follow-up: browser QA.

## 11. Repair-task policy

New rule:

Every repair task must include:

1. blocker repair;
2. validation;
3. mainline roadmap restoration;
4. next heavy batch recommendation;
5. evidence packet.

Repair tasks must not:

- end at isolated typo/test fix;
- mix unrelated source changes unless required;
- mutate protected UI/docs/evidence paths casually;
- skip roadmap handoff;
- skip safety/no-live confirmation.

## 12. Recommended exact next implementation batch

`TASK_CONTENTOPS_0174U1_PLATFORM_UNIVERSE_REGISTRY_V2_AND_PRIMARY_PAYLOAD_CLASSES_CONTRACT_V0`

Reason:

- It unlocks X + Telegram + Substack triangle safely.
- It reconciles old Telegram authority work with multi-platform product plan.
- AI Writer/SEO and ingestion connector both need platform target vocabulary.
- It remains local deterministic, no-live, and contract-first.

## 13. Final evidence packet

- Task label: `TASK_CONTENTOPS_0174U0_HEAVY_STRATEGY_RECON_LOCAL_REPO_DEEP_RESEARCH_AND_MASTER_PLAN_INPUT_REPORT_V0`
- Mode: Heavy strategy recon / docs report only
- ContentOps repo: `A:\Capital Chronicle\tools\cc-live-contentops`
- ContentOps branch/HEAD: `master` / `f328d713d798387fc8545636fb8e4a095f607047`
- Ingestion repo: `A:\Capital Chronicle\Headline Raw data local json\capital-chronicle-ingestion`
- Ingestion branch/HEAD: `main` / `6720a9be3932ce43b097e538e95ba0ccedb0f5d7`
- Files inspected include strategy master plan, recovery index, governance policy, operating rules, 0174ED-0174TJ docs, authority modules, V5 awareness, and ingestion repo docs/artifact surfaces.
- Web sources used: Telegram Bot API, X Developer, LinkedIn/Microsoft docs, Meta developer docs, Threads docs, TikTok developer docs, YouTube Data API docs, Substack support/API reality research.
- Files created: `docs/automation/0174U0/**`
- No source implementation: yes
- No UI polish: yes
- No live/API/credential/scheduler/scraping/DM behavior: yes
- Caveat: ingestion repo recon avoided env/credential files and did not treat local artifacts as truth.
- Exact next task: `TASK_CONTENTOPS_0174U1_PLATFORM_UNIVERSE_REGISTRY_V2_AND_PRIMARY_PAYLOAD_CLASSES_CONTRACT_V0`
