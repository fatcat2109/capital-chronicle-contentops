# TASK_CONTENTOPS_0140 — Grounded News Angle Workbench (V0)

## Objective
Build a local-only, deterministic, source-aware workbench that turns
operator-supplied news/source metadata into review-only content angle packets.
The workbench never searches, scrapes, fetches, or calls a provider; it validates
what the operator supplies and maps a news hook into safe educational/process
angles that always require manual review and stay not public-postable.

This is explicitly:
- NOT a repo-side news search task
- NOT a web scraping task
- NOT a news API / RSS / market-data API task
- NOT an LLM/provider API task
- NOT a public-ready content generator
- NOT a live publishing task

## Allowed Scope (built in this task)
- `schemas/grounded_news_angle_workbench_packet.schema.json` — packet schema.
- `live_contentops/grounded_news_angle_workbench.py` — deterministic validator and
  `summary()`.
- `fixtures/grounded_news_angle_workbench/` — one valid fixture and eight negative
  fixtures.
- CLI command `pre-alpha-grounded-news-angle-workbench-summary`.
- Tests in `tests/test_grounded_news_angle_workbench.py`.
- This runbook.

## Forbidden Scope (NOT built, NOT enabled)
- Repo web search, scraping, news API, RSS fetch, market-data API integration.
- LLM/provider API calls or prompt execution.
- Platform API clients, credential loading, or `.env` reads.
- Scheduler / auto-posting / autonomous replies or DMs.
- Newsletter sender / SMTP / CMS integration.
- Public-ready or fake content generation.
- Real Capital Chronicle artifact-backed claims.

## Core Principle: News Is a Hook, Not a Signal
A current event may be used to explain why data quality matters, why a macro
claim is not forecast-ready, how official sources should be checked, why markets
can overreact to incomplete information, what uncertainty remains, and what
evidence would be required before a serious thesis exists.

A current event must never be used to say buy/sell/hold, long/short, target
price, "this means X asset will move", "our model predicts", "our signal says",
"Capital Chronicle alpha says", or "watch this level" as actionable framing. The
validator blocks all of these.

## Operator-Supplied Source Metadata Only
The `input_policy` hard-asserts `operator_supplied_context_only = true` and forces
`repo_web_search_allowed`, `repo_scraping_allowed`, `repo_news_api_allowed`,
`repo_rss_fetch_allowed`, `repo_market_data_api_allowed`, `provider_llm_api_allowed`,
`credential_read_allowed`, and `platform_api_allowed` to false. Every source item
must carry full metadata: id, title, type, date, access/observed date,
url-or-reference-label, summary, limitation note, freshness label, redistribution
flag, and authority role. Missing metadata fails closed.

## No Repo Web Search / Scraping / News API / Market-Data API
The repo performs zero network or fetch operations. Sources are described by the
operator; the repo only classifies and gates them. `summary()` keeps every
related counter at zero: `repo_web_search_enabled_count`,
`repo_scraping_enabled_count`, `repo_news_api_enabled_count`,
`repo_rss_fetch_enabled_count`, `repo_market_data_api_enabled_count`.

## No Provider/LLM API Calls
`provider_llm_api_allowed` must be false and `provider_llm_api_enabled_count` is
zero. Downstream LLM prompts are allowed only as template/external-use handoffs
(`downstream_llm_prompt_allowed = true`) and never as repo execution
(`downstream_llm_repo_execution_allowed = false`).

## No Public-Ready Content Generation / Manual Review Requirement
Every angle card asserts `review_only`, `manual_review_required`,
`not_public_postable`, `source_references_required`, `limitations_required`,
`no_signal_language_required`, and `no_financial_advice_required` true, with
`publish_ready` and `public_ready_allowed_now` false. The output policy mirrors
this and additionally forbids `auto_approval_allowed`,
`platform_export_final_allowed_now`, `newsletter_send_enabled_now`, and
`cms_integration_enabled_now`.

## Relationship to 0138 Social Platform Foundation
`social_platform_foundation_linkage` references the 0138 control plane. Angle
cards are review-only inputs that, if ever advanced, would flow through the 0138
per-platform `manual_review_required` / `not_public_postable` guarantees. Nothing
here enables platform export.

## Relationship to 0139 LLM Content Writer Workbench
`llm_content_writer_workbench_linkage` marks the downstream review-only seam:
approved angle cards can become prompt-pack inputs for the 0139 workbench, where
drafting still happens externally and the repo never calls a provider. The
handoff is structural only (`downstream_review_only = true`).

## How This Supports Macro Thesis QA and the North Star
By forcing limitations, source references, and "news is a hook" framing, the
workbench amplifies macro thesis QA (claims must be qualified), data sufficiency
(single releases flagged as insufficient), forecast readiness (events are not
forecasts), and failure forensics (overreaction to incomplete information is a
teachable pattern). It never frames Capital Chronicle as a Bloomberg
replacement, AI trading bot, signal service, execution system, or guaranteed
prediction engine.

## Capability Statement
No live posting, platform API, credential/env read, scheduler, scraping, web
search, news/RSS/market-data API, newsletter sending, CMS/email-provider
integration, LLM provider call, or autonomous reply/DM capability was added by
this task. The layer is a local, fixture-driven, fail-closed control-plane
description only.
