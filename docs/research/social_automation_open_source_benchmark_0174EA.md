# Social Automation Open-Source Benchmark (0174EA)

Task: TASK_CONTENTOPS_0174EA_SOCIAL_AUTOMATION_RESEARCH_AND_ARCHITECTURE_CONTEXT_PACK_V0
Mode: Implementation Mode, docs-only.
Status: Advisory research context. Not runtime authority. No live posting, no API calls, no credential reads were performed to produce this document.

> [!NOTE]
> This document normalizes operator-supplied research into the repo so the team does not lose context. All repo and platform claims should be re-verified against current upstream sources before any implementation. Source URLs are tracked in [social_automation_source_manifest_0174EA.md](file:///A:/Capital%20Chronicle/tools/cc-live-contentops/docs/research/social_automation_source_manifest_0174EA.md). Ephemeral ChatGPT citation IDs from the original research were intentionally dropped and are not repo citations.

## Executive Verdict

Across the five benchmarked repositories, only **Postiz** resembles a mature, multi-platform product with a real monorepo architecture, explicit hosted-service compliance language, test/CI artifacts, and a large integration surface. The other four are useful references but are either thin wrappers around platform APIs, dashboard-driven Laravel apps, or early-stage schedulers with gaps in secret hygiene, redirect hardening, auditability, and operator approval controls.

None of the five repositories, based on the inspected files, provides the full ContentOps-grade safety pattern: redacted credential presence checks, operator-GO before every live post, one-request/no-auto-retry writes, redirect blocking with final-host verification, idempotency ledgers, spend/rate budget gates, and rigorous redaction/audit trails.

Conclusion for ContentOps: study Postiz for architecture, borrow adapter-abstraction ideas from the Laravel package/Owlstack repos, but do not copy the `.env`-token + background-scheduler pattern directly. Build supervised automation with operator-GO as a first-class primitive.

## Why Postiz Is the Strongest Reference

- TypeScript monorepo: Next.js + NestJS + Prisma + Temporal, pnpm workspaces.
- Process maturity: AGPL-3.0 license, a security policy, Jest/Nx test config, and CI artifacts (`.github`, Jenkins, Sonar).
- Broadest integration surface of the five: scheduling plus API integrations across many platforms (X, LinkedIn, Reddit, Threads, Facebook, YouTube, TikTok, Pinterest, Discord, Slack, Mastodon, plus a generic OAuth provider), with a public API advertised.
- Compliance posture for the hosted SaaS: documents that users authenticate directly with official platform OAuth flows and states it does not collect/store/proxy user API keys for the hosted service.

Key tension to learn from: the hosted product claims it does not store user tokens, while the self-hosted `.env.example` documents a large plaintext secret surface (client IDs, secrets, API keys, bot tokens, JWT/DB secrets). This is the normal split between SaaS OAuth federation and self-hosted operator-owned credentials — and it is exactly why ContentOps should keep self-hosted live credentials out of normal env files.

## Per-Repo Usefulness and Limits

### gitroomhq/postiz-app
- Useful for: monorepo architecture, multi-platform adapter breadth, OAuth federation model, test/CI maturity, security policy as a baseline.
- Insufficient/unsafe for ContentOps as-is: no exposed operator-GO gate per live post in inspected sources; self-hosted path exposes broad env-based secret surface; write-path retry policy not verified (Temporal in stack makes orchestration retries likely, which is risky for side-effecting writes).

### fawaziwalewa/autopost-social-media
- Useful for: a concrete operator surface (Filament admin UI), scheduling + logging + success/error notifications via a scheduled Artisan command.
- Insufficient/unsafe: secrets documented in `.env` and possibly dashboard; no explicit retry/backoff or redirect-hardening; no separate security/redaction policy surfaced. Scope limited to Twitter/X and Facebook.

### Anil-matcha/Free-AI-Social-Media-Scheduler
- Useful for: an end-to-end Next.js scheduler with post history (scheduled/published/failed) and a clear product shape.
- Insufficient/unsafe: pushes platform complexity into a third-party publishing service (MuAPI) via API key, which changes the trust boundary and makes auditing/failure-reasoning/token-exposure guarantees harder; no security policy/tests/CI surfaced in inspected paths; operator surface is the web scheduler itself, not an explicit approval gate.

### HamzaHassanM/laravel-social-auto-post
- Useful for: clean reusable package design, facades, lifecycle events (`SocialPostPublishing`, `SocialPostPublished`, `SocialPostFailed`), tests, version compatibility, dynamic runtime credentials (less hardcoded env coupling).
- Insufficient/unsafe: no first-class operator-GO UX (it is a library, not an app); no vault/redaction policy surfaced; no documented redirect handling or rate-limit strategy.

### owlstacks/owlstack-laravel
- Useful for: explicit multi-platform adapter abstraction, `PublishResult` return type, only registers providers with valid credentials.
- Insufficient/unsafe: plain `.env` token store across many platforms (Telegram, X, Facebook, LinkedIn, Instagram, Discord, Slack, Reddit, Pinterest, WhatsApp, Tumblr) — large secret surface; optional proxying; no retry/backoff/redirect/redaction policy surfaced; no human approval gate before posting.

## Auth / Token Storage Patterns Observed

| Repo | Auth method | Token storage |
|---|---|---|
| postiz-app | Official platform OAuth flows (hosted); broad self-hosted provider config | Hosted: claims no user-key storage. Self-hosted: plaintext `.env.example` (client IDs/secrets, API keys, bot tokens, JWT/DB secrets) |
| autopost-social-media | Twitter API key/secret + access token/secret; Facebook app ID/secret + page access token | `.env` primary; some settings may also be dashboard-stored |
| Free-AI-Social-Media-Scheduler | App login via Google OAuth (NextAuth); publishing delegated to MuAPI via API key | `.env` (DB URL, NextAuth secret, Google client secret, MuAPI key, Stripe secrets, webhook URL) |
| laravel-social-auto-post | Per-platform auth behind facades; supports dynamic runtime credentials | Abstracted; can be passed at runtime; no vault/redaction shown |
| owlstack-laravel | Mixed per-platform tokens by env | Plain `.env`; optional proxy settings |

## Scheduler / Queue / Posting Assumptions

The common open-source shape is: `.env token → scheduler/queue → API call → log result`.
- Postiz: Temporal-based orchestration; retries likely at the orchestration layer (unverified for write paths).
- autopost-social-media: scheduled Artisan command runs background posting jobs.
- Free-AI scheduler: scheduled posts with history; webhook/async callbacks via MuAPI.
- laravel-social-auto-post / owlstack-laravel: synchronous facade publish calls; behavior depends on host app scheduling.

This background-job pattern is the core risk for ContentOps: unattended retries/parallelism can create duplicate public posts, paid spend (X), or rate restrictions (Discord).

## Missing ContentOps-Grade Controls (Gap Analysis)

None of the five repos, in inspected materials, demonstrated the following. These become the ContentOps build targets:

- Redacted credential presence checks (symbolic configured/missing/unknown only — no value, hash, prefix, suffix, or fingerprint).
- Operator-GO required before every live post, bound to payload hash + destination + account class + expiry.
- Payload hash approval that auto-expires if the payload changes.
- One-request / no-auto-retry write envelopes for side-effecting posts (narrow exception only where the provider supports an idempotency key, e.g. Mastodon).
- Redirect blocking and final-host verification on OAuth callbacks (exact redirect-URI match, `state` binding, wrong-account detection, fail-closed).
- Idempotency ledgers to dedupe across crashes, proxy retries, double-clicks.
- Spend / rate budget gates (hard X spend cap below billing limit; Discord route/global header parsing; Telegram paid broadcast off by default).
- Redacted response audit (store result class only, never payloads/tokens).
- Account binding proof (exact destination + account handle/class before any write).
- Platform-specific preflight contracts (LinkedIn asset URNs; TikTok creator-info; Bluesky blob upload; Reddit subreddit post-requirements).
- Fake-provider tests covering token-missing, wrong-account, invalid-scope, rate-limited, redirect-mismatch, audit-not-approved, and duplicate-submit cases; no live secrets in CI.

## Takeaway

Manual posting remains a fallback/emergency path, not the strategic build target. The product direction is supervised automation with explicit operator-GO and per-platform gates. Autonomous posting is forbidden. See [supervised_social_publishing_reference_architecture_0174EA.md](file:///A:/Capital%20Chronicle/tools/cc-live-contentops/docs/architecture/supervised_social_publishing_reference_architecture_0174EA.md) and [ADR_0174EA_AUTOMATION_NOW_SUPERVISED_NOT_AUTONOMOUS.md](file:///A:/Capital%20Chronicle/tools/cc-live-contentops/docs/decisions/ADR_0174EA_AUTOMATION_NOW_SUPERVISED_NOT_AUTONOMOUS.md).
