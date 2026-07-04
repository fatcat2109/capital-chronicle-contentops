# Pre-Alpha Content Seed Library and Editorial Calendar - After TASK_CONTENTOPS_0103

LOCAL ONLY | NO NETWORK | NO PROVIDER | NO LLM | NO PLATFORM | NO CREDENTIALS | NO POSTING

## What this adds
A local-only, deterministic seed library and editorial calendar/planner that
feeds the existing 0095-0101 pre-alpha pipeline without any external calls.

- Module: `live_contentops/pre_alpha_seed_library.py`
- Schemas:
  - `schemas/pre_alpha_content_seed_library.schema.json`
  - `schemas/pre_alpha_editorial_calendar_plan.schema.json`
- Fixture: `fixtures/pre_alpha_seed_library/valid_seed_library_with_one_blocked.json`
- Tests: `tests/test_pre_alpha_seed_library.py`
- CLI: `python -m live_contentops.cli content-seed-calendar-summary`

## Seed library
A library is a collection of content seeds tagged with a `content_zone`
(macro_education, build_in_public, product_update, data_sufficiency,
forecast_readiness, failure_forensics, general_process). Each seed reuses the
0095 content-seed contract and is validated with the same guardrail validator
(`validate_seed`), so there is a single source of truth for forbidden language,
alpha-implication, unverified numeric market claims, and market-note rules.

Seeds may be general/product/process/educational only unless real source
artifact IDs exist. Market-note-like seeds without fresh verified source
artifacts stay blocked or clearly non-public.

## Editorial calendar plan
`build_calendar_plan` deterministically sequences seeds into planned items in
library order:

- Safe (valid) seeds -> `review_status=needs_manual_review`,
  `publish_status=manual_only`.
- Blocked seeds -> `review_status=blocked`, `publish_status=not_published`,
  with recorded `blocked_reasons`. Blocked seeds are preserved as planned items
  and mirrored into `blocked_items`; they are never silently dropped.

Every planned item defaults `manual_publish_url`, `manual_publish_timestamp`,
and `manual_metrics` to null. Plan-level flags pin `platform_publish_allowed_now`,
`live_execution_allowed_now`, `scheduler_allowed`, and
`metrics_ingestion_allowed` to false.

## Hard boundaries
- No network/provider/LLM/web/search calls.
- No platform API/posting/scheduling/replies/DMs/scraping/metrics ingestion.
- No credential or `.env` reads.
- No fake Capital Chronicle alpha output.
- No public-postable market claims; everything requires manual human review.
- No financial advice, buy/sell/hold, position sizing, targets, signal language,
  or guaranteed prediction.
- No auto-approval.

## Next recommended task
AWAIT_CHATGPT_NEXT_TASK_MAPPING
