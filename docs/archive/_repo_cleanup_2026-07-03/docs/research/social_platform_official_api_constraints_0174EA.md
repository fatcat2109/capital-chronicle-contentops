# Social Platform Official API Constraints (0174EA)

Task: TASK_CONTENTOPS_0174EA_SOCIAL_AUTOMATION_RESEARCH_AND_ARCHITECTURE_CONTEXT_PACK_V0
Mode: Implementation Mode, docs-only.
Status: Advisory research context. Not runtime authority. No live API calls, credential reads, or network requests were performed to produce this document.

> [!IMPORTANT]
> Several official docs were **not verified** in the source session. Meta (Facebook/Instagram) docs returned "Not Logged In", Threads docs returned 429, and no public official Substack publishing API was found. Those rows are marked unresolved and must not be treated as ready. Re-verify every row from current official docs before implementation. Stable URLs are in [social_automation_source_manifest_0174EA.md](file:///A:/Capital%20Chronicle/tools/cc-live-contentops/docs/research/social_automation_source_manifest_0174EA.md).

## Readiness Classification Legend

- `manual_fallback` — manual posting is the current path; automation not built.
- `api_plug_port_only` — future live adapter contract only; no live dispatch.
- `official_docs_verified` — official docs were readable in source research (still re-check before code).
- `official_docs_gated` — official docs blocked/rate-limited/unverified in source research.
- `paid_api_required` — writes incur cost or require paid tier.
- `permission_review_required` — app/product/scope review or audit required.
- `unsupported_or_unknown_api` — no reliable official publishing API found.

## Platform Matrix

### X (Twitter)
- Role in ContentOps: short-form distribution and concise hook layer.
- Automation readiness: `api_plug_port_only` + `paid_api_required`.
- Official docs status: readable in source research (re-check required).
- Cost: explicitly pay-per-use; writes are billed; credits/auto-recharge/spend limits are first-class.
- Auth model: OAuth 2.0 user context (user token) and other credential types.
- Posting endpoint family (per research): `POST /2/tweets`.
- Blockers: spend budget control; redirect/final-host hardening (current 0174DE blocker); account binding.
- Rate/spend/retry risk: high — every write is intentional spend; endpoint-specific 15-minute windows; do not auto-retry writes.
- Media/preflight risk: medium.
- Recommended posture: paid track after spend cap + redirect hardening + account-binding gates. Not first pilot.

### LinkedIn
- Role: professional founder/operator voice.
- Automation readiness: `api_plug_port_only` + `permission_review_required`.
- Official docs status: readable in source research (some marketing pages sign-in gated).
- Cost: not pay-per-call surfaced; gated by product/scope/review.
- Auth model: member posting via `w_member_social`; organization posting requires role/product validation.
- Posting endpoint family (per research): `POST /rest/posts` with required headers; media needs pre-uploaded asset URNs.
- Blockers: Community Management Standard tier requires access form, screen recording, test credentials; organization page roles.
- Rate/spend/retry risk: medium.
- Media/preflight risk: high — multi-step media asset preparation (URNs) before posting.
- Recommended posture: after X track or in parallel; member post first, organization post later behind review.

### Telegram
- Role: controlled channel; recommended **first** supervised live pilot.
- Automation readiness: `api_plug_port_only` → first live pilot candidate.
- Official docs status: Bot API readable in source research.
- Cost: basic Bot API appears free; paid broadcast acceleration via `allow_paid_broadcast` (default OFF in ContentOps).
- Auth model: bot token; calls like `https://api.telegram.org/bot<token>/METHOD_NAME`.
- Posting endpoint family (per research): `sendMessage`.
- Blockers: bot token discipline; channel admin permission; throughput policy.
- Rate/spend/retry risk: low (with paid broadcast disabled).
- Media/preflight risk: low for text.
- Recommended posture: first live pilot — getMe identity → channel binding → permission proof → sendMessage dry-run payload hash → one supervised message.

### Facebook
- Role: Meta page distribution later.
- Automation readiness: `api_plug_port_only` + `official_docs_gated`.
- Official docs status: **unverified** — Meta docs returned "Not Logged In" in source research.
- Cost: unknown/unresolved.
- Auth model: likely Page access tokens + app review (must verify from authenticated docs).
- Posting endpoint family: unresolved.
- Blockers: developer-portal/app-review gating; docs could not be read.
- Rate/spend/retry risk: unknown.
- Media/preflight risk: unknown.
- Recommended posture: do not implement until authenticated official-doc re-check. Manual fallback meanwhile.

### Instagram
- Role: visual/card/carousel distribution later.
- Automation readiness: `api_plug_port_only` + `official_docs_gated`.
- Official docs status: **unverified** — content publishing docs returned "Not Logged In".
- Cost: unknown/unresolved.
- Auth model: likely business/creator account + media-container publishing (must verify).
- Posting endpoint family: unresolved.
- Blockers: account type, media URL/hosting policy, app review.
- Rate/spend/retry risk: unknown.
- Media/preflight risk: high (likely media-container constrained).
- Recommended posture: do not implement until authenticated official-doc re-check. Manual fallback meanwhile.

### Threads
- Role: softer conversational mirror.
- Automation readiness: `api_plug_port_only` + `official_docs_gated`.
- Official docs status: **unverified** — docs fetch returned 429.
- Cost: unknown/unresolved.
- Auth model: unresolved (Meta-family).
- Posting endpoint family: unresolved.
- Blockers: docs not reliably readable; Meta-family review likely.
- Rate/spend/retry risk: unknown.
- Media/preflight risk: unknown.
- Recommended posture: do not assume readiness; re-verify before implementation. Manual fallback meanwhile.

### Substack
- Role: canonical long-form home.
- Automation readiness: `manual_fallback` + `unsupported_or_unknown_api`.
- Official docs status: **no public official publishing API found** in source research.
- Cost: n/a.
- Auth model: unresolved.
- Posting endpoint family: none confirmed.
- Blockers: no confirmed supported publisher API.
- Recommended posture: manual posting remains default until an official supported publisher API is confirmed.

### TikTok
- Role: later video/photo format; not near-term macro-text priority.
- Automation readiness: `api_plug_port_only` + `permission_review_required`.
- Official docs status: readable in source research.
- Cost: not pay-per-call surfaced; gated by app approval/audit.
- Auth model: registered app + enabled product + approved `video.publish` scope + user access token/open ID.
- Posting endpoint family (per research): creator-info query, then upload/init calls (Content Posting API).
- Blockers: unreviewed clients forced to private-only visibility until audit.
- Rate/spend/retry risk: medium.
- Media/preflight risk: high — creator-info preflight mandatory.
- Recommended posture: after audit readiness. Plug-port + docs only for now.

### YouTube
- Role: future long-form video / walkthroughs / demos.
- Automation readiness: `api_plug_port_only` + `permission_review_required`.
- Official docs status: readable in source research.
- Cost: no pay-per-call fee surfaced; upload quota applies.
- Auth model: OAuth scopes such as `youtube.upload`.
- Posting endpoint family (per research): `videos.insert`.
- Blockers: unverified projects (post-2020) forced to private visibility until audit; quota.
- Rate/spend/retry risk: medium (quota).
- Media/preflight risk: high (video upload).
- Recommended posture: after audit/verification readiness. Plug-port + docs only for now.

### Bluesky
- Role: open short-form mirror; technically attractive.
- Automation readiness: `api_plug_port_only` (lower friction).
- Official docs status: AT Protocol docs readable in source research.
- Cost: no paid API requirement surfaced.
- Auth model: session-based; short-lived `accessJwt` + longer-lived `refreshJwt`.
- Posting endpoint family (per research): create `app.bsky.feed.post` records; media requires blob upload first.
- Blockers: short-lived session handling; record/blob semantics.
- Rate/spend/retry risk: low/medium.
- Media/preflight risk: medium (blob upload).
- Recommended posture: early secondary pilot after Telegram, alongside Discord/Mastodon.

### Discord
- Role: internal/community announcement channel; not public macro authority.
- Automation readiness: `api_plug_port_only` (lower friction).
- Official docs status: readable in source research.
- Cost: no paid API requirement surfaced.
- Auth model: incoming webhooks (webhook token is a secret) or bot token.
- Posting endpoint family (per research): webhook message post (content/embeds/files/polls).
- Blockers: must honor route/global/invalid-request rate limits and headers; `allowed_mentions` policy (no `@everyone`/`@here` without explicit approval).
- Rate/spend/retry risk: medium — aggressive limits; honor `Retry-After`.
- Media/preflight risk: low/medium.
- Recommended posture: early secondary pilot after Telegram. Webhook secret redaction required.

### Mastodon
- Role: open-web/technical audience.
- Automation readiness: `api_plug_port_only` (lower friction; best idempotency support).
- Official docs status: readable in source research.
- Cost: no paid API requirement surfaced; instance-specific rules apply.
- Auth model: OAuth `write:statuses`.
- Posting endpoint family (per research): `POST /api/v1/statuses`; supports `Idempotency-Key`.
- Blockers: instance binding; instance-specific rules.
- Rate/spend/retry risk: low.
- Media/preflight risk: low/medium.
- Recommended posture: early secondary pilot; use its `Idempotency-Key` as the model contract for the safe-retry exception.

### Reddit
- Role: low-priority discussion/community distribution.
- Automation readiness: `api_plug_port_only` + `permission_review_required` (community-rule heavy).
- Official docs status: readable in source research.
- Cost: no paid API requirement surfaced; subreddit-specific rules matter.
- Auth model: OAuth; app registration; **exact** redirect-URI matching; `state` verification.
- Posting endpoint family (per research): `/api/submit`; `/api/v1/subreddit/post_requirements` for pre-validation.
- Blockers: subreddit rules/moderation/reputation risk.
- Rate/spend/retry risk: medium.
- Media/preflight risk: medium — use subreddit post-requirements as a preflight model.
- Recommended posture: later; manual often preferred. Strong reference for redirect/preflight contracts.

### Medium
- Role: optional syndication if Substack insufficient.
- Automation readiness: `manual_fallback` + `unsupported_or_unknown_api`.
- Official docs status: official API repo archived / not recommended for new integrations.
- Cost: n/a.
- Auth model: deprecated.
- Posting endpoint family: not recommended.
- Recommended posture: manual export only; do not prioritize an API integration.

## Two Architecture-Critical Facts From Official Docs

1. Posting is frequently **not a single call**. LinkedIn needs pre-uploaded media asset URNs; TikTok requires creator-info preflight; Bluesky needs blob upload; Reddit exposes subreddit post-requirements. A safe system needs per-platform **preflight contracts**, not one generic `publish()`.
2. "Access granted" is not "safe to automate blindly." X couples writes to spend and rate windows; Discord expects dynamic header obedience; Telegram can turn speed into a paid feature. A mature publisher must track **cost, rate, and intent** simultaneously.

## Source Honesty Note

Meta (Facebook/Instagram), Threads, and Substack rows are explicitly unresolved per the source research. They are not "officially verified" and must not be presented as ready.
