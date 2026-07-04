# TASK_CONTENTOPS_0138 — Social Platform Foundation / Control Plane (V0)

## Objective
Consolidate the post-0137 ContentOps capabilities into one deterministic,
local-only operator-facing foundation for multi-platform content preparation.
This layer describes how content is prepared, fit-checked per platform, and
gated for manual review — without enabling any live action.

This is explicitly:
- NOT a live publishing task
- NOT a platform API task
- NOT a credentials/env task
- NOT a scheduler task
- NOT a content auto-generator task

## Allowed Scope (built in this task)
- `schemas/social_platform_foundation_packet.schema.json` — packet schema.
- `live_contentops/social_platform_foundation.py` — deterministic validator and
  `summary()`.
- `fixtures/social_platform_foundation/` — one valid fixture and four negative
  fixtures.
- CLI command `pre-alpha-social-platform-foundation-summary`.
- Tests in `tests/test_social_platform_foundation.py`.
- This runbook.

## Forbidden Scope (NOT built, NOT enabled)
- Live platform API clients or live dispatch request builders.
- Credential loading or `.env` reads.
- Schedulers / auto-posting / autonomous replies or DMs.
- Scraping or platform metric ingestion.
- Newsletter sender / SMTP / CMS / email-provider integration.
- LLM provider calls from the repo.
- Public-ready or fake content generation.

## Supported Platforms
`x`, `linkedin`, `telegram`, `threads_manual`, `substack_newsletter`,
`facebook_page`, `instagram`, `tiktok`.

Each `platform_fit_matrix` entry hard-asserts:
- `live_posting_enabled_now = false`
- `platform_api_allowed_now = false`
- `credential_required_now = false`
- `credential_read_allowed_now = false`
- `scheduler_allowed_now = false`
- `scraping_allowed_now = false`
- `autonomous_reply_or_dm_allowed_now = false`
- `manual_review_required = true`
- `not_public_postable = true`
- `public_ready_allowed_now = false`

## Local-Only Safety Guarantees
The validator (`validate_social_platform_foundation_packet`) fails closed when:
- `runtime_authority` is true.
- Any platform enables a forbidden live/API/credential/scheduler/scraping/
  autonomous/public-ready flag.
- Any platform drops `manual_review_required` or `not_public_postable`.
- The safety policy omits the no-financial-advice or no-signal-language
  disclaimers, or does not require source references.
- The approval policy allows auto-approval or omits manual review.
- The manual export policy allows live dispatch or is not manual-only.
- Forbidden trading/signal/execution language appears (buy/sell/hold, long/short,
  target price, position sizing, broker, order routing, execution, signal,
  guaranteed, "our model predicts", "our signal says").
- "Capital Chronicle alpha says" appears without real approved artifacts.
- `packet_status` is `pass` while validation errors exist.

The `summary()` output keeps every live/external counter at zero or false:
live posting, platform API, credential read, scheduler, scraping, autonomous
reply/DM, public-ready, unsafe language, provider/search/network/platform calls,
credential-or-env reads, newsletter send, and CMS integration.

## How This Prepares Later Tasks
This foundation is the deterministic spine that later tasks attach to:
- The future LLM-assisted content writer will draft into this packet's lanes and
  per-platform fit matrix, then route every draft through manual review — never
  to live dispatch.
- The grounded news angle workbench will supply sourced angles into the same
  safety and approval policy, with source references required and signal language
  blocked.

`future_handoff` records that these handoffs are structurally ready while
confirming no capability is enabled now.

## Capability Statement
No live posting, platform API, credential/env read, scheduler, scraping,
newsletter sending, CMS/email-provider integration, LLM provider call, or
autonomous reply/DM capability was added by this task. The layer is a local,
fixture-driven, fail-closed control-plane description only.
