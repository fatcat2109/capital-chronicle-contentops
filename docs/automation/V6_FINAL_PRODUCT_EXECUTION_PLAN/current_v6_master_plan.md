# ContentOps V6 Current Master Plan

> Current release authority (2026-07-11): run `contentops_v1_0_rc_20260711_1` passed the nine-surface machine gate and is frozen at `AWAITING_OPERATOR_MANUAL_AUDIT_TEXT_IMAGE_V1_0_RC`. The next action is read-only operator audit; do not dispatch, edit, tag v1.0, or enter TikTok/video/Short modes.

Authority date: 2026-07-10

Current task: `TASK_CONTENTOPS_HEAVY_TIER1_EDITORIAL_PLATFORM_VARIANT_RELIABILITY_AND_VIDEO_CAPABILITY_SPLIT_V3`

Canonical runner: `live_contentops.eight_platform_substack_first_pipeline_v1`

## Product North Star

Capital Chronicle ContentOps V6 is an AI-native editorial production and supervised distribution system:

```text
headline/CDP intake
-> LLM semantic clustering, duplicate/hotspot policy, impact ranking
-> source and numeric support packet
-> tier-1 reader-facing article and SEO gate
-> three analytical source-backed visuals
-> canonical Substack publication/readback
-> platform-native variants with exact media binding
-> sentence-aware root/reply compilation
-> adapter dispatch and idempotency
-> public text/media/link/account/surface readback
-> targeted reconciliation, evidence, telemetry, operator review
```

Substack is canonical. Every text/image derivative points back to it. Manual action is recovery context, not the product. The Capital Chronicle database and cited primary sources remain numeric authority.

## Tier-1 Editorial Gate

The article mode must be declared as `straight_news`, `analysis`, or `explainer`. Length follows the topic and evidence rather than a fixed word target.

Acceptance is dual-gated. `live_contentops.tier1_editorial_quality_v1` first runs deterministic editorial, SEO, safety, rendered-body, and source/media checks. A bounded LLM standards review then evaluates the news peg, why-now logic, market consequence, mode consistency, mechanism, context, confirmation/falsification tests, unsupported certainty, quotes, advice, and information density. Both must pass. LLM output has no publication authority and can never override a deterministic blocker; malformed or unavailable review fails closed.

Required:

1. A lede saying what changed, why now, and why markets care.
2. A concise nut graf.
3. Source-backed mechanism and relevant policy, liquidity, issuance, geopolitical, or cross-asset context.
4. Named confirmation and falsification conditions.
5. High information density and reader-facing prose.
6. No invented quotes, reactions, certainty, financial advice, or unsupported numbers.

Public prose fails when it narrates editorial or pipeline work. Terms such as “the editorial task,” “the reporting discipline,” “the schedule and sidecars,” “the chart manifest,” “editors should look,” or “the newsroom standard” are defects, not signs of rigor. Repeated caveats, filler, restated mechanisms, and generic watch lists are penalized.

The current public Fed funds article is operationally good and remains frozen, but the V3 fixture audit scores it `60/100` for tier-1 editorial quality because of process narration. The local-only revised candidate scores `93/100`, removes that vocabulary, reduces length from 1,476 to 663 words, retains all numeric claims and three visuals, and is not published. Its bounded LLM standards review passed all 14 semantic checks; the combined deterministic-plus-LLM gate is `PASS`.

## SEO Gate

SEO requires a reader headline, separate SEO title, clean slug, 110-165 character meta description, canonical metadata, primary topic in the opening, semantic keyword coverage without stuffing, heading hierarchy, source/reference links, chart captions and alt text, lead social/OG media, nonduplicated title/dek, and clean rendered body with placement markers removed.

Current fixture score: `86/100`. Local revised candidate: `100/100`.

## Media Authority

The generated manifest is the only derivative-media authority. Every asset carries ID, role, absolute path, SHA-256, MIME, dimensions, provenance, title, caption, alt text, and article-section association. Adapters must reject avatars, logos, favicons, author images, low-resolution thumbnails, unapproved hashes, and square branding when a chart is required.

The current assets are `primary`, `policy_corridor`, and `sofr_context`. A derivative readback must verify the expected asset, not merely the existence of an image.

## Platform Variant Reliability

Hard character slicing is forbidden. The compiler operates on sentences and paragraphs, preserves order, deduplicates repeated units, and splits a sentence only when that single sentence exceeds the platform limit. Oversized sentences split at semantic clauses before any word-safe fallback.

X and Threads default to three posts:

1. Root: headline, sharp lede, canonical URL, `primary` chart.
2. Reply 1: mechanism, `policy_corridor` chart.
3. Reply 2: policy/cross-asset context and caveat, `sofr_context` chart.

Quality requires two replies, balanced character utilization, no orphan fragments, sentence-boundary PASS, zero duplicated sentences, all three visuals exactly once, stable IDs, ordered parent-child relationships, and text/media readback. Reply IDs alone are insufficient.

LinkedIn and Facebook use complete root text when limits allow; overflow becomes complete author comments. Silent truncation is forbidden.

## Current Operator Audit

The public Substack, Telegram, Discord, corrected Facebook, Instagram media, and YouTube Community outputs are accepted and frozen.

The live X chain is preserved but fails the new quality gate because six uneven replies split sentences at arbitrary boundaries. The live Threads chain is preserved but fails because the root lacks the approved chart and replies contain fragments. No X or Threads repost is authorized in V3. `planned_semantic_variants_v1.json` is the corrected future contract.

Instagram feed-caption URLs are not assumed clickable. Feed acceptance requires exact canonical URL text, correct chart, account/caption readback, and a clear CTA. `caption_link_clickable=false` is informational, not failure. Bio and Story changes require separate scope.

LinkedIn activities `7481289145206644736` and `7481311616265895936` are both reconciled. The earlier activity was already accepted; V3 edited the newest image-only activity in place and verified text, chart, and canonical link. No third post or comment was created.

## Idempotency And Unknown Writes

Canonical re-entry is blocked. Derivative resume skips all destinations already in accepted state. A delayed permalink or UNKNOWN write outcome freezes retries until exact read-only reconciliation resolves whether a write exists.

LinkedIn creation populates text before media, verifies text and canonical URL after media attachment, then allows Post. An absent immediate permalink never authorizes a replacement. Malformed output recovery is exact readback, edit, bounded author comment when appropriate, then a replacement only with deterministic proof and explicit scope.

## YouTube And Video Capability Split

The default article route is YouTube Community text + image + Substack URL. TikTok native posting, YouTube long-form video, and YouTube Shorts are separate explicit non-default capabilities.

V3 is capability-audit-only for those lanes. No public or private upload is permitted. The redacted matrix records credential-name presence, OAuth state, scopes, identity readiness, transport, test mode, approval status, blocker, and next operator action.

- TikTok: three persistent app credential names are present, but OAuth callback, user authorization, refresh token, `open_id`, runtime refresh, native Content Posting adapter, and app audit are absent. Status: `BLOCKED_TIKTOK_OAUTH_ADAPTER_AND_APP_AUDIT_INCOMPLETE`.
- YouTube long-form: credentials/channel binding are present, but no reviewed explicit long-form runtime adapter or public-write audit exists. Status: `BLOCKED_YOUTUBE_LONG_FORM_EXPLICIT_MODE_AND_AUDIT_REQUIRED`.
- YouTube Shorts: explicit Edge adapter exists but is isolated from the article runner and has no V3 execution approval. Status: `BLOCKED_YOUTUBE_SHORTS_PUBLIC_EXECUTION_NOT_AUTHORIZED`.

Current official rules are linked in `video_platform_capability_matrix_v1.json`. Square or vertical videos up to 180 seconds classify as Shorts; wider or longer content classifies as long-form. Local upload request construction is private-only and performs no network call.

## Browser And Secret Boundary

Canonical profile:

```text
A:\Capital Chronicle\operator-browser-profiles\contentops-social-main
```

Only Microsoft Edge with verified profile ownership may publish. Safe checks are environment-variable names, presence booleans, browser family, CDP ownership, destination identity, and visible non-secret selectors. Fast Ship never authorizes printing raw environment values, tokens, webhook URLs, cookies, localStorage, sessionStorage, authorization headers, or browser-session secrets.

## Success And Failure

No success comes from a Post click, HTTP response, media upload, or ID alone. Quality PASS requires correct account and surface, complete native text, platform-accurate link semantics, expected media IDs, complete visual distribution, stable identity, ordered chain, resolved idempotency state, and visual/text readback.

V3 task classification: `PASS_TIER1_EDITORIAL_PLATFORM_VARIANT_RELIABILITY_AND_VIDEO_CAPABILITY_SPLIT_V3`.

This does not retroactively make the preserved X/Threads live chains quality PASS. Their defects are regression fixtures until a future new article uses the corrected compiler.

## Diagnosis Path

Read:

```text
AGENTS.md
-> docs/status/current_project_status.json
-> this master plan
-> platform_delivery_contract_v1.json failure_resolution_map
-> operator_browser_lab_runbook.md
-> current run evidence
-> named adapter and focused test
```

Current evidence root: `docs/automation/EIGHT_PLATFORM_FULL_PIPELINE_V1/eight_platform_live_20260710_recovery1/`.

## Next Route

Next, wire tier-1 scores, planned three-post layouts, quality failures, exact LinkedIn activity relationships, Instagram link semantics, and video capability rows into `ui/contentops_v5/`. Do not start a new canonical run during that dashboard/read-model task.
