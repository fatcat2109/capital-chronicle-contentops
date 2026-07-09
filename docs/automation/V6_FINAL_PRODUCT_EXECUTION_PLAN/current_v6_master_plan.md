# Capital Chronicle ContentOps V6 — Current Master Plan Authority

Task label: `TASK_CONTENTOPS_V6_STATUS_PROGRESS_MASTER_PLAN_REFRESH_AFTER_LINKEDIN_MANUAL_LOOP_V0`

This file is the repo-native north-star plan for V6 strategy. It is strategic context, not runtime truth. GitHub remote commits, fetched repo files, tests, and evidence packets remain runtime authority. Chat memory and Project Sources are context only.

## V6 North-Star Loop

The definitive 12-step content automation pipeline sequence:
1. **Open ContentOps daily**: Initialize the operator workspace session.
2. **Pull X/CDP headlines**: Retrieve headlines from the last checkpoint or last 24 hours.
3. **Save raw headlines**: Save the raw headline list to a dated local evidence file.
4. **Cluster, dedupe, and rank**: Group and evaluate the intake list.
5. **Select article idea**: Choose the target commentary topic using:
   - Freshness
   - Macro relevance
   - Heat / breaking-news level
   - Topic balance
   - Prior-topic duplication avoidance
   - Database support availability
6. **Build source/data support packet**: Query the Capital Chronicle database to establish trusted local data grounds.
7. **Generate article brief**: Synthesize insights and structured parameters.
8. **Draft SEO article**: Build the canonical long-form content.
9. **Generate media/chart/card**: Produce visual assets (internal data charts or search-backed candidates).
10. **Build platform variants**: Prep tailor-made payloads for each target channel (Substack, LinkedIn, X, Discord, etc.).
11. **Run duplicate/preflight/readiness**: Validate safety invariants, duplicate checks, and exact preview hashes.
12. **Publish and expand**: Execute supervised dispatch, ideally releasing on one platform first (e.g., Discord/Substack) before expanding to other social lanes.

## Daily ContentOps Operating Loop

- Daily ContentOps begins by collecting X/CDP headlines from the last successful checkpoint, or from the last 24 hours when no checkpoint exists.
- The headline pull must be written to a local evidence file before any article decision.
- Headlines are clustered, deduped, ranked, and converted into article ideas.
- Idea selection must balance topic freshness, macro/market relevance, SEO potential, platform suitability, prior-topic repetition, and agreed content-topic balance.
- Do not repeat stale/non-hot topics.
- Repeating a topic is allowed only when the last 24h contains a genuine hot update, breaking news, or meaningful new catalyst.
- After idea selection, the system must query/read the Capital Chronicle database/exporter authority for supporting data.
- Article generation, SEO draft, media generation, platform variants, and multi-platform posting automation are downstream stages.
- Public dispatch remains separately gated and must not be treated as proven by the fast fixture-based Discord post.
- ContentOps must not become a second macro database; the Capital Chronicle local database remains numeric/source/context authority.

Implementation sequence:
1. X/CDP headline capture packet
2. headline cluster/ranking packet
3. article idea brief
4. trusted database support packet
5. SEO article draft
6. media/visual packet
7. platform variants
8. duplicate/preflight/readiness
9. supervised public dispatch/readback

## Product Thesis

Capital Chronicle ContentOps V6 is an AI-native editorial, publishing, and community operating system for producing governed market commentary workflows. The system should transform operator intent and source context into auditable content packets, deterministic previews, approval records, manual exports, and community feedback loops.

The product is not a signal service, broker, trading bot, portfolio manager, investment adviser, or financial advice engine. Content must remain educational/editorial unless a future explicitly approved compliance scope says otherwise.

## Platform Roles

| Platform | Current role | Current execution posture |
|---|---|---|
| Substack | Canonical long-form authority | Manual/export evidence lane is locally complete as fixture/operator-supplied evidence. |
| LinkedIn | Professional distribution lane | Manual publication evidence loop is accepted; evidence is fixture/operator-supplied, not API/network verified. |
| X | Real-time market commentary lane | Manual/deferred plus supervised packet evidence exists; registry append/readback is local and idempotent. |
| Discord | Community feedback flywheel | Pre-live/dry-run/outbox/governance docs and packets exist; no live send is claimed by this plan. |
| Telegram | Remote operator lane | Remote operator/checkpoint lane direction exists; live execution remains gated. |
| Facebook Page | Meta-family page distribution lane | Official Graph API adapter is live-capable under Fast Ship Mode; smoke evidence verified post/comment/edit. |
| Threads | Meta-family short-form conversation lane | Official Threads API adapter is live-capable under Fast Ship Mode; smoke evidence verified post/reply, while edit is API-unsupported. |
| Instagram | Visual/social media lane | Instagram Business adapter is live-capable for two-step media publish/comment under Fast Ship Mode; smoke is blocked until a public smoke image URL or media ID is provided, and edit is API-unsupported. |
| TikTok | High-friction short-video lane | Advisory capability docs exist; last-priority future lane, no current product execution. |
| Generic manual | Operator-controlled fallback lane | Manual copy/export evidence only; no platform capability or live automation claimed. |

## AI / LLM Production Role

LLMs may assist with research synthesis, editorial drafting, SEO refinement, platform-native variant proposals, feedback summaries, and backlog suggestions. LLM output must flow through deterministic packet builders, review artifacts, exact payload hashes, and operator approval boundaries before any distribution lane treats it as ready.

## Media Grounding and Asset Policy

ContentOps must choose post media based on source class, not convenience:

1. **News/current-event topics**: Use search-like image sources as discovery only unless provenance is complete. Google/Commons candidates must persist query, recency/time filter, source page URL, image URL, source domain, retrieval timestamp, rights/provenance status, why selected, and operator-review requirement before they can be considered for public use.
2. **Capital Chronicle Internal alpha / analysis-report topics**: Prefer built-in chart/card media generated from Capital Chronicle raw data. A dedicated chart rendering pipeline will be built specifically for this AFTER the Capital Chronicle project itself is completed. Until then, these will fall back to using news Google Image search or candidate metadata.
3. **Source-backed generated media** is the preferred auto-public path when search candidates are stale, weakly sourced, or rights-unclear. Long-form Substack defaults to 3 visuals: at least one data chart, at least one contextual image/map/official visual, and one supporting chart/map, with explicit two-asset exceptions only when appropriate.
4. **Fallback external media** is allowed only as reviewed candidate metadata with operator approval, rights notes, alt text, source attribution, and stable media hash participation in the media manifest.
5. **Visual social lanes** such as Instagram, Threads, Facebook Page, LinkedIn, and X must receive platform-specific media fit notes before approval. Media fit is local review evidence only, not platform upload readiness.

## Editorial Scheduling Policy

Headline ingestion sidecars are catalyst context only. They may rank urgency, source needs, media needs, and cross-platform fit, but they are not market price truth, macro-print truth, source clearance, or trading input. The daily scheduler targets 5-6 slots/day, prioritizing fresh official releases and high-impact current macro/geopolitical stories before evergreen explainers or deep research.

## Deterministic Validators and Approval Boundaries

- Generated packets must be deterministic and testable.
- Exact payload hashes bind operator review to the payload being reviewed.
- Approval records must not silently mutate payloads.
- Outbox entries should be idempotent and auditable.
- Audit records must distinguish fixture/manual/operator-supplied evidence from provider/API/network-verified evidence.
- UI surfaces may display pending/manual evidence, but must not imply live dispatch or public verification without committed proof.

## Payload Hash, Approval, Outbox, and Audit Principles

1. Build canonical payloads locally.
2. Hash exact payloads with a stable algorithm.
3. Capture operator review decisions without fabricating approval.
4. Prepare outbox records only when gates are satisfied.
5. Preserve audit records with safety flags and evidence provenance.
6. Treat manual exports and operator-supplied URLs/metrics as manual evidence unless a future network/API verification gate is explicitly scoped.

## Manual Fallback and Browser/CDP Boundaries

Manual fallback is a first-class lane. Browser/CDP work, if later approved, must be supervised, scoped, and must never read credentials, browser session secrets, cookies, localStorage, sessionStorage, or hidden token material. This status refresh performs no browser work.

## Current Accepted Implementation Status

- Status governance docs/protocol exist under `docs/status/`.
- Canonical dashboard authority is `ui/contentops_v5/`.
- V6 local deterministic packets exist for research, canonical drafts, Substack manual publication evidence, LinkedIn manual publication evidence, X supervised packet evidence, and advisory platform capability metadata.
- The north-star platform universe includes Substack, LinkedIn, X, Discord, Telegram, Facebook Page, Threads, Instagram, TikTok, and generic manual fallback.
- The canonical V5 Command Center now productizes that full platform universe in one source-to-audit operator cockpit backed by deterministic local adapter output.
- LinkedIn manual publication evidence loop is accepted as product baseline at `83c53fd3a39b377d9f74fa70cd8b6a5357689ecb` after push/readback.
- Substack, LinkedIn, X, TikTok, and generic manual evidence remains fixture/manual/operator-supplied unless a future task provides explicit verified evidence; Discord/Telegram, Meta-family Facebook Page/Threads, and Instagram now have committed live/API dispatch evidence under Fast Ship Mode; Instagram retry evidence is scoped and did not duplicate prior successful platforms.
- Media policy is split by source class: news uses grounded image candidate metadata; Capital Chronicle internal alpha/report content uses built-in chart/card media when available.
- The canonical V5 Command Center now displays both media lanes, hash-bound approve/hold/reject operator decision packets, local outbox readiness reconciliation rows, Discord/Telegram redacted local-only operator bridge rows, manual/deferred distribution rows for Facebook Page/Threads/Instagram/TikTok/Generic Manual, and manual audit rows as adapter-built local review evidence.
- Under Fast Ship Mode, live/provider/platform execution is enabled for explicitly implemented lanes. Discord/Telegram, Facebook Page, Threads, Substack, LinkedIn, and X have current live dispatch success evidence from rehearsal `v6_pipeline_737400e418e5`; Instagram has scoped retry success evidence from `v6_pipeline_2ff80fab28d4` using the idempotent platform allowlist.
- Final release go/no-go rehearsal plus Instagram retry evidence now cover every implemented platform lane: broad run `v6_pipeline_737400e418e5` succeeded outside Instagram, and scoped retry `v6_pipeline_2ff80fab28d4` completed Instagram with `DISPATCH_COMPLETE` for the retry scope.
- Terra Ultra north-star automation V1 now has live Telegram photo evidence: the runner selected a fresh Fed funds/rates schedule topic, built three ContentOps-owned rates visuals, exported a three-visual article, and sent Telegram message `61`. Substack and X remain separate supervised browser/CDP readback tasks for this article.

## Currently Completed Local / Manual Lanes

- Status ledger and dashboard authority guardrails.
- Canonical V5 dashboard integration for read-only manual evidence cards.
- Substack manual export, approval/export evidence, operator handoff, URL/audit import, and manual metrics summary as local/manual evidence.
- LinkedIn manual export, approval/export evidence, operator handoff, URL/audit import, and manual metrics summary as local/manual evidence.
- X supervised packet evidence and local publication registry idempotency/readback audit.
- Advisory capability registry/docs for Facebook Page, Threads, Instagram, TikTok, Telegram, and generic manual fallback.
- Discord pre-live/dry-run/outbox governance artifacts and Telegram checkpoint/manual lane evidence are consolidated in the canonical V5 Command Center as redacted local-only bridge status; no live send is claimed.
- Facebook Page, Threads, Instagram, TikTok, and Generic Manual are hardened in the canonical V5 Command Center as local-only manual/deferred distribution handoffs with deterministic payload hashes, media requirements, audit evidence modes, and explicit blocked execution flags.
- The final operator handoff / next-action strip is implemented in the canonical V5 Command Center as display-only consolidated evidence for approved manual export, hold/reject rows, Discord/Telegram bridge status, manual/deferred social handoffs, manual audit evidence, and global locked execution flags.
- Internal visual-card packet specs and media rights manifest exist locally; Google image search execution and image download are implemented (`google_image_search_v6.py`), while rights verification and custom template rendering remain future extensions.
- The Capital Chronicle Content pipeline for internal alpha/analysis-report topics (generating LLM/matplotlib charts from internal data) is explicitly planned for implementation after the main Capital Chronicle project is fully completed.
- Deterministic V5 Command Center adapter output now covers full-platform variant rows, source-aware media candidates, stable hashes, local operator approve/hold/reject decision packet intake, local outbox readiness reconciliation, Discord/Telegram local bridge rows, manual/deferred distribution rows, manual audit rows, and final operator action-strip rows.

## Remaining Roadmap Direction

Recommended future work should remain soft and evidence-driven:

- Reconcile roadmap priorities against current repo state before opening any new lane.
- North star: a dashboard-triggered full automation pipeline that either dispatches live to all supported lanes or blocks loudly with exact reasons. `TASK_CONTENTOPS_V6_FINAL_LAUNCH_STALE_STATE_CLEANUP_V0` made this truthful: runner exits non-zero on blocked/partial launches, the server reconciles the true outcome from `latest_dispatch_audit.json`, and the dashboard removed all fake-success/dry-run fallbacks.
- Complete `TASK_CONTENTOPS_V6_DASHBOARD_TRIGGERED_LIVE_RUN_AND_PER_PLATFORM_AUDIT_V0`: start backend + UI, trigger one dashboard live run, audit each platform from the true audit status, and resolve the real article quality/media blockers before declaring a clean `DISPATCH_COMPLETE`.
- Archive stale one-off scripts/test helpers only after confirming no current tests, docs, imports, or release evidence still reference them; refresh final release evidence indexes if needed.
- Continue improving canonical V5 visibility for accepted packets.
- Only pursue live/provider/platform actions through exact live scope contracts, approval gates, safety tests, and final operator go decisions.
- Keep Project Sources lean and contextual; never use them as runtime authority over GitHub remote.

## Safety Boundary

- Under Fast Ship Mode, live/provider/platform execution, network runs, and env/credential reads are authorized to achieve full automation. Real-time posting, editing, and commenting are enabled, and historical dry-run boundaries are bypassed.
- No raw secret values or raw `.env` content should be committed to git.

