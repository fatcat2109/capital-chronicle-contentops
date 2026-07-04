# TASK_CONTENTOPS_0142 — Daily Content Studio Markdown Review Export (V0)

## Objective
Render the accepted 0141 Daily Content Studio Run Packet into a human-readable
Markdown operator review packet so Jim can use the daily content studio as a
local manual workbench. The Markdown surfaces source/news context, selected safe
angle cards, content lane/type, source/freshness/limitations requirements,
external LLM prompt-template handoff blocks, platform-fit notes, safety blockers
and review flags, a manual operator checklist, why the packet is not
public-postable, and which manual-only next actions are allowed.

This is explicitly:
- NOT a public-ready post exporter
- NOT a final social media copy generator
- NOT a repo-side content generator
- NOT an LLM/provider API task
- NOT a web/news/search/scraping task
- NOT a platform/API/posting/scheduler task
- NOT a newsletter/CMS/email provider task

## Allowed Scope (built in this task)
- `live_contentops/daily_content_studio_markdown_export.py` — renderer,
  deterministic Markdown safety validator, and `summary()`.
- `fixtures/daily_content_studio_run/daily_content_studio_run_valid_review_export.md`
  — rendered review-only Markdown fixture.
- CLI commands `pre-alpha-daily-content-studio-markdown-export` and
  `pre-alpha-daily-content-studio-markdown-export-summary`.
- Tests in `tests/test_daily_content_studio_markdown_export.py`.
- This runbook.

## Forbidden Scope (NOT built, NOT enabled)
- Repo web search, scraping, news API, RSS fetch, market-data API integration.
- LLM/provider API calls or prompt execution.
- Platform API clients, credential loading, or `.env` reads.
- Scheduler / auto-posting / autonomous replies or DMs.
- Newsletter sender / SMTP / CMS integration.
- Public-ready or final social copy generation.
- Real Capital Chronicle artifact-backed claims.

## How the Markdown Export Composes 0138, 0139, 0140, and 0141
The renderer reads a valid 0141 Daily Content Studio Run Packet (which already
composes the three upstream layers) and presents:

- Source context summary and source lineage (0140 Grounded News Angle Workbench
  inputs, operator-supplied only).
- Selected angle cards with review-only / not-public-postable / source-reference /
  limitation flags (0140 angle cards).
- External LLM prompt-template handoff that states `repo_executes_prompt: False`,
  `provider_call_allowed_by_repo: False`, and that the repo does not produce final
  public copy (0139 LLM Content Writer Workbench boundary).
- Platform-fit notes showing live posting, platform API, scheduler, and final
  export all disabled (0138 Social Platform Foundation control plane).
- A composed final status that keeps the whole run not public-postable.

## Why This Is Review-Only and Not Public-Postable
The Markdown always carries the LOCAL ONLY / REVIEW ONLY / NOT PUBLIC-POSTABLE /
MANUAL REVIEW REQUIRED banners (plus NO FINANCIAL ADVICE, NO SIGNAL LANGUAGE, NO
LIVE POSTING, NO PLATFORM API, NO PROVIDER/LLM API, NO WEB SEARCH / SCRAPING /
NEWS API). The validator fails closed if any banner is removed, if any forbidden
enable-flag appears as true, if a forbidden manual action is presented as allowed,
if unsafe trading/signal/execution/model-prediction language appears, if "Capital
Chronicle alpha says" appears without real artifact approval, or if the
source/limitation sections are missing.

## How Jim Can Manually Use the Packet Outside Repo
Jim reviews the rendered Markdown, chooses an angle card, copies a prompt template
into an external LLM of his choice, manually rewrites/edits the draft outside the
repo, reruns local validation, and — only if he independently posts outside the
repo — manually records the public URL later. The repo never posts, schedules,
sends, or calls any external service on his behalf.

## No Repo Web Search / Scraping / News API / Market-Data API
The renderer reads a local fixture only and performs zero network or fetch
operations. `summary()` keeps every related counter at zero/false.

## No Provider/LLM API Calls
The repo never calls a provider and never executes prompt templates; prompt blocks
are external-use-only handoffs.

## No Platform API / Live Posting / Scheduler
Platform interaction is preview/notes only; final export, live posting,
credential reads, and scheduling stay disabled.

## No Public-Ready Content Generation
The Markdown is a review artifact, not final social copy. `summary()` reports
`final_social_copy_generated = false`.

## No Credential/Env Reads
The export reads only the local run packet fixture; it does not read `.env`,
credentials, or secrets.

## How This Supports Macro Thesis QA and the North Star
By surfacing source lineage, limitations, "news is a hook" framing, and a manual
review checklist in one readable artifact, the export amplifies macro thesis QA,
data sufficiency, forecast readiness, and failure forensics. It never frames
Capital Chronicle as a Bloomberg replacement, AI trading bot, signal service,
execution system, or guaranteed prediction engine.

## Capability Statement
No live posting, platform API, credential/env read, scheduler, scraping, web
search, news/RSS/market-data API, newsletter sending, CMS/email-provider
integration, LLM provider call, or autonomous reply/DM capability was added by
this task. The layer is a local, fixture-driven, fail-closed Markdown review
renderer only.
