# Social Automation Execution Roadmap (after 0174EA)

Task origin: TASK_CONTENTOPS_0174EA_SOCIAL_AUTOMATION_RESEARCH_AND_ARCHITECTURE_CONTEXT_PACK_V0
Direction: supervised automation, not autonomous posting. Manual posting is fallback, not the strategic destination.

> [!IMPORTANT]
> No live posting, credential reads, OAuth execution, scheduler, browser automation, scraping, or autonomous publishing is authorized by this roadmap. Each live step is gated by an explicit, separate task with operator GO.

## Phase 0 — Context Pack (this task)
- 0174EA: import and normalize social automation research into the repo as durable docs.
- Outputs: open-source benchmark, official API constraints matrix, supervised reference architecture, ADR, this roadmap, source manifest.
- No code. No network. No credentials.

## Phase 1 — Resolve Blocked X Live-Read-Only Code (if present)
- TASK_CONTENTOPS_0174DE_R1_X_OAUTH_LIVE_READ_ONLY_IDENTITY_PROOF_REDIRECT_FINAL_HOST_HARDENING_V0
- Purpose: the prior 0174DE live-read-only work exists on master but is not accepted as product baseline due to redirect/final-host hardening concerns.
- Corrective scope: disable redirect following, verify final host against an allowlist, prove request budget of exactly 1, no auto-retry. This is corrective, not expansion.
- Until this lands accepted, no X live chain proceeds.

## Phase 2 — Automation Core (platform-agnostic, no live posting)
Build the hard engine before any platform write:
- account binding model;
- credential handle + redaction boundary (presence-class only, no values/hashes/prefixes/suffixes);
- approval ledger + payload hash;
- outbox queue + idempotency contract;
- rate limit / spend budget / retry policy (one-request, no auto-retry for side-effecting writes);
- redacted dispatch audit event;
- fake-provider CI harness (no live secrets in CI).

Indicative task cluster:
- 0174EB Social Account Binding Model + Fake-Provider Contract
- 0174EC Credential Handle + Redaction Boundary
- 0174ED Approval Ledger + Payload Hash
- 0174EE Outbox Queue + Idempotency Contract
- 0174EF Rate Limit / Spend Budget / Retry Policy
- 0174EG Redacted Dispatch Audit Event

## Phase 3 — First Platform Live Pilot: Telegram
Telegram first because of lower app-review and paid-risk burden. Broken into discrete gated steps:
- bot identity proof via `getMe`;
- channel binding proof (exact channel);
- channel permission proof;
- `sendMessage` dry-run with payload hash;
- one-message supervised live pilot (request budget 1, no retry, payload hash approved, kill switch clear, redacted audit).

## Phase 4 — Discord / Mastodon / Bluesky
- Discord: webhook URL redaction, route/global rate-header parsing, no @everyone/@here without explicit approval.
- Mastodon: instance binding, OAuth `write:statuses`, `Idempotency-Key` as a model dedupe contract.
- Bluesky: short-lived session handling, record + blob upload semantics.

## Phase 5 — X / LinkedIn (after spend / review / account gates)
- X: hard spend cap below platform billing limit, per-run request budget, account binding, payload contract, one-post supervised pilot.
- LinkedIn: app/product/scope proof, member account binding, asset-URN media preflight, text-post contract, supervised pilot. Organization posting requires page-role checks and review.

## Phase 6 — TikTok / YouTube (after audit readiness)
- TikTok: creator-info preflight, `video.publish` scope, audit to exit private-only mode.
- YouTube: `youtube.upload` scope, quota gate, project verification/audit to exit forced-private uploads.

## Phase 7 — Meta Family (after authenticated official-doc re-check)
- Facebook Page, Instagram, Threads: re-verify from an authenticated session first. Source research saw Meta docs as "Not Logged In" and Threads as 429. Treat readiness as unresolved until re-checked.

## Shortest High-Velocity Ordering
1. 0174EA context pack (this task)
2. 0174DE_R1 X live-read-only redirect/final-host hardening
3. 0174EB account binding model
4. 0174EC credential handle boundary
5. 0174ED approval ledger + payload hash
6. 0174EE outbox / idempotency / retry policy
7. 0174EH Telegram `getMe` identity proof
8. 0174EL Telegram first supervised live post

## Operating Frame
- Manual = fallback / emergency path.
- Automation = main build path.
- Autonomous posting = forbidden.
- Supervised publishing = final product.
