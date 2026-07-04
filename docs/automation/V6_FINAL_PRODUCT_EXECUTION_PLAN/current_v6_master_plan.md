# Capital Chronicle ContentOps V6 — Current Master Plan Authority

Task label: `TASK_CONTENTOPS_V6_STATUS_PROGRESS_MASTER_PLAN_REFRESH_AFTER_LINKEDIN_MANUAL_LOOP_V0`

This file is the repo-native north-star plan for V6 strategy. It is strategic context, not runtime truth. GitHub remote commits, fetched repo files, tests, and evidence packets remain runtime authority. Chat memory and Project Sources are context only.

## V6 North-Star Loop

```text
Jim idea / source / research context / future artifact
→ AI research and grounding
→ canonical Substack long-form article
→ SEO and editorial refinement
→ platform-native variants
→ deterministic preview hash and operator approval
→ approved outbox and redacted audit record
→ manual or explicitly gated platform distribution
→ operator-supplied public URL / audit / metrics evidence
→ community feedback and questions
→ LLM summary and backlog update
→ next canonical article
```

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
| Facebook Page | Meta-family page distribution lane | Advisory capability docs exist; future manual/Meta Business Suite path first, API/live posting blocked. |
| Threads | Meta-family short-form conversation lane | Advisory capability docs and dry-run/manual recovery notes exist; API/live posting blocked. |
| Instagram | Visual/social media lane | Advisory capability docs exist; deferred until media rights, account constraints, and Meta review are solved. |
| TikTok | High-friction short-video lane | Advisory capability docs exist; last-priority future lane, no current product execution. |
| Generic manual | Operator-controlled fallback lane | Manual copy/export evidence only; no platform capability or live automation claimed. |

## AI / LLM Production Role

LLMs may assist with research synthesis, editorial drafting, SEO refinement, platform-native variant proposals, feedback summaries, and backlog suggestions. LLM output must flow through deterministic packet builders, review artifacts, exact payload hashes, and operator approval boundaries before any distribution lane treats it as ready.

## Media Grounding and Asset Policy

ContentOps must choose post media based on source class, not convenience:

1. **News/current-event topics** should produce grounded image candidate packets. The first safe implementation is operator-supplied or search-result metadata only: candidate title/source URL/image URL/license notes/relevance notes. Repo code must not scrape Google Images, download media, fetch public image URLs, or claim rights verification unless a future exact approved task adds that capability.
2. **Capital Chronicle Internal alpha / analysis-report topics** should prefer built-in chart/card media from the internal report or chart system. These posts should not use random external web images when a report-native chart/card is available.
3. **Fallback external media** is allowed only as reviewed candidate metadata with operator approval, rights notes, alt text, source attribution, and stable media hash participation in the media manifest.
4. **Visual social lanes** such as Instagram, Threads, Facebook Page, TikTok, LinkedIn, and X must receive platform-specific media fit notes before approval. Media fit is local review evidence only, not platform upload readiness.

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
- Substack, LinkedIn, X, Discord, Telegram, Meta-family, TikTok, and generic manual evidence remains fixture/manual/operator-supplied unless a future task provides explicit verified evidence.
- Media policy is split by source class: news uses grounded image candidate metadata; Capital Chronicle internal alpha/report content uses built-in chart/card media when available.
- The canonical V5 Command Center now displays both media lanes, hash-bound approve/hold/reject operator decision packets, local outbox readiness reconciliation rows, Discord/Telegram redacted local-only operator bridge rows, and manual audit rows as adapter-built local review evidence.
- Live/provider/platform execution remains blocked unless separately scoped and approved.

## Currently Completed Local / Manual Lanes

- Status ledger and dashboard authority guardrails.
- Canonical V5 dashboard integration for read-only manual evidence cards.
- Substack manual export, approval/export evidence, operator handoff, URL/audit import, and manual metrics summary as local/manual evidence.
- LinkedIn manual export, approval/export evidence, operator handoff, URL/audit import, and manual metrics summary as local/manual evidence.
- X supervised packet evidence and local publication registry idempotency/readback audit.
- Advisory capability registry/docs for Facebook Page, Threads, Instagram, TikTok, Telegram, and generic manual fallback.
- Discord pre-live/dry-run/outbox governance artifacts and Telegram checkpoint/manual lane evidence are consolidated in the canonical V5 Command Center as redacted local-only bridge status; no live send is claimed.
- Internal visual-card packet specs and media rights manifest exist locally; rendered media export, Google image search execution, image download, and rights verification remain future work.
- Deterministic V5 Command Center adapter output now covers full-platform variant rows, source-aware media candidates, stable hashes, local operator approve/hold/reject decision packet intake, local outbox readiness reconciliation, Discord/Telegram local bridge rows, and manual audit rows.

## Remaining Roadmap Direction

Recommended future work should remain soft and evidence-driven:

- Reconcile roadmap priorities against current repo state before opening any new lane.
- Harden manual/deferred distribution lanes without live writes unless explicitly scoped.
- Continue improving canonical V5 visibility for accepted packets.
- Only pursue live/provider/platform actions through exact live scope contracts, approval gates, safety tests, and final operator go decisions.
- Keep Project Sources lean and contextual; never use them as runtime authority over GitHub remote.

## Safety Boundary

- No `.env` or secret file may be staged.
- No raw secret, webhook URL, token length, prefix, suffix, hash, digest, cookie, localStorage, sessionStorage, browser profile secret, or credential-derived metadata may be output.
- No provider/API/platform/browser/live action is authorized by this plan.
- No public URL/network verification is claimed unless committed evidence proves it.
