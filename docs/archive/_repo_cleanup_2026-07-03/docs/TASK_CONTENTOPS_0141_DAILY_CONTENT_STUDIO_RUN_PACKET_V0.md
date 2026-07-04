# TASK_CONTENTOPS_0141 — Daily Content Studio Run Packet (V0)

## Objective
Compose the accepted 0138 Social Platform Foundation, 0139 LLM-Assisted Content
Writer Workbench, and 0140 Grounded News Angle Workbench into one deterministic,
operator-facing daily run packet. The packet makes the pre-alpha content workflow
usable as a daily review-only surface that answers: what operator-supplied source
context is included, which safe angle cards are available, which content lane and
type apply, which external LLM prompt templates fit, what source/freshness/
limitations requirements stay visible, which platforms fit, what safety blockers
exist, what the manual review state is, why the packet is not public-postable, and
what downstream manual actions are allowed.

This is explicitly:
- NOT a repo-side content generator
- NOT a public-ready post generator
- NOT an LLM/provider API task
- NOT a web/news/search/scraping task
- NOT a platform/API/posting/scheduler task
- NOT a newsletter/CMS/email provider task

## Allowed Scope (built in this task)
- `schemas/daily_content_studio_run_packet.schema.json` — packet schema.
- `live_contentops/daily_content_studio_run.py` — deterministic validator and
  `summary()`.
- `fixtures/daily_content_studio_run/` — one valid fixture and nine negative
  fixtures.
- CLI command `pre-alpha-daily-content-studio-run-summary`.
- Tests in `tests/test_daily_content_studio_run.py`.
- This runbook.

## Forbidden Scope (NOT built, NOT enabled)
- Repo web search, scraping, news API, RSS fetch, market-data API integration.
- LLM/provider API calls or prompt execution.
- Platform API clients, credential loading, or `.env` reads.
- Scheduler / auto-posting / autonomous replies or DMs.
- Newsletter sender / SMTP / CMS integration.
- Public-ready or fake content generation.
- Real Capital Chronicle artifact-backed claims.

## How 0138, 0139, and 0140 Compose Into the Daily Run Packet
The packet carries three handoff surfaces, each fail-closed:

- `platform_foundation_handoff` (0138): platform preview allowed, but
  `platform_export_final_allowed_now`, `platform_api_allowed_now`,
  `live_posting_enabled_now`, `credential_read_allowed_now`, and
  `scheduler_allowed_now` are all false; manual review required and not
  public-postable.
- `llm_writer_handoff` (0139): `external_llm_use_only` and `prompt_template_only`
  true; `repo_executes_prompt`, `provider_call_allowed_by_repo`, and
  `generated_copy_final_allowed_now` false; manual review required and not
  public-postable.
- `grounded_news_workbench_handoff` (0140): `operator_supplied_source_only` true
  and `repo_web_search_allowed` false.

No handoff may enable live execution, provider execution, platform execution,
final export, auto approval, or public-ready status.

## Operator-Supplied Source/News Context Only
`input_policy` hard-asserts `operator_supplied_context_only = true` and forces
`repo_web_search_allowed`, `repo_scraping_allowed`, `repo_news_api_allowed`,
`repo_rss_fetch_allowed`, `repo_market_data_api_allowed`, `provider_llm_api_allowed`,
`credential_read_allowed`, `platform_api_allowed`, `scheduler_allowed`, and
`newsletter_or_cms_api_allowed` to false. Source lineage is required and every
run must carry a non-empty `source_context_summary`.

## No Repo Web Search / Scraping / News API / Market-Data API
The repo performs zero network or fetch operations. `summary()` keeps every
related counter at zero.

## No Provider/LLM API Calls
The repo never calls a provider. Prompt templates are external-use-only handoffs;
the repo never executes them.

## No Platform API / Live Posting / Scheduler
Platform interaction is preview/notes only. Final export, live posting,
credential reads, and scheduling all stay disabled and fail closed if enabled.

## No Public-Ready Content Generation / Manual Review Requirement
Every selected angle card and the output policy assert manual review required,
not public-postable, publish-ready false, auto-approval false, and public-ready
false. Manual operator actions are restricted to review-only/external actions
(review source context, choose angle card, copy prompt template for external LLM,
manually rewrite draft outside repo, rerun local validation, manually record a
public URL later). Forbidden actions (auto_publish, schedule_post, send_newsletter,
call_platform_api, call_provider_api, scrape_metrics, fetch_market_data,
auto_reply_or_dm) fail closed.

## How This Supports Macro Thesis QA and the North Star
By forcing source lineage, limitations, "news is a hook" framing, and manual
review across the composed workflow, the daily run packet amplifies macro thesis
QA, data sufficiency, forecast readiness, and failure forensics. It never frames
Capital Chronicle as a Bloomberg replacement, AI trading bot, signal service,
execution system, or guaranteed prediction engine.

## Capability Statement
No live posting, platform API, credential/env read, scheduler, scraping, web
search, news/RSS/market-data API, newsletter sending, CMS/email-provider
integration, LLM provider call, or autonomous reply/DM capability was added by
this task. The layer is a local, fixture-driven, fail-closed composition surface
only.
