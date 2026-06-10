# TASK_CONTENTOPS_0145 — Daily Content Studio Local UI Data Contract (V0)

## Objective
Define the data/view-model contract that a future static/local frontend can
consume to display the accepted Daily Content Studio workflow (0138 Social
Platform Foundation, 0139 LLM Content Writer Workbench, 0140 Grounded News Angle
Workbench, 0141 Run Packet, 0142 Markdown Review Export, 0143 Operator Decision
Ledger, 0144 External Draft Review). The contract makes unknowns, blocked
states, limitations, manual review, and not-public-postable status visible.

This is a UI data contract task only. It is explicitly:
- NOT a frontend implementation task
- NOT a backend/server task
- NOT a live platform/API task
- NOT a provider/LLM API task
- NOT a web/news/search/scraping task
- NOT a scheduler/posting task
- NOT a newsletter/CMS/email provider task
- NOT a public-ready copy generator

## Allowed Scope (built in this task)
- `schemas/daily_content_studio_ui_data_contract_packet.schema.json`
- `live_contentops/daily_content_studio_ui_data_contract.py` — validator and
  `summary()`.
- `fixtures/daily_content_studio_ui/` — one valid fixture and nine negatives.
- CLI command `pre-alpha-daily-content-studio-ui-data-contract-summary`.
- Tests in `tests/test_daily_content_studio_ui_data_contract.py`.
- This runbook.

## Forbidden Scope (NOT built, NOT enabled)
- Frontend HTML/JS/CSS implementation, React/Vue/Svelte app.
- Backend server, API routes.
- Live platform API clients, provider/LLM API calls.
- Web/search/news/RSS fetch, scraping, market-data API.
- Scheduling, posting, newsletter/CMS/email provider integration.
- Credential loading or `.env` reads.
- Autonomous replies/DMs, public-ready final copy generation.

## Why This Is a UI Data Contract Only, Not Frontend Implementation
The packet describes the shape of data a UI would render (sections, banners,
badges, workflow cards, allowed/forbidden actions) but ships no HTML, JS, CSS, or
server. `frontend_implementation_included` and `backend_server_required` must be
false; `local_fixture_only` and `ui_contract_mode =
local_static_fixture_contract_only` must hold. The contract is a deterministic,
fixture-driven view model, not a running app.

## How It Composes 0138 Through 0144
`source_contracts` references the IDs/fixtures of all seven upstream packets:
social_platform_foundation, llm_content_writer_workbench,
grounded_news_angle_workbench, daily_content_studio_run,
daily_content_studio_markdown_export,
daily_content_studio_operator_decision_ledger, and
daily_content_studio_external_draft_review. The validator fails closed if any of
these linked contracts is missing, so the UI surface always reflects the full
accepted workflow chain.

## Expected UI Panels / Sections for the Later Static UI
The contract defines thirteen review-only sections: safety_header,
daily_run_overview, source_context_panel, angle_cards_panel,
llm_prompt_handoff_panel, markdown_review_export_panel,
external_draft_review_panel, operator_decision_ledger_panel, platform_fit_panel,
blockers_and_limitations_panel, manual_actions_panel, audit_status_panel, and
future_frontend_handoff_panel. Every section must keep review_only,
manual_review_required, not_public_postable, limitations_visible,
source_references_visible, and blocked_actions_visible true.

## Safety Banners and Blocked Actions
Required banners: LOCAL ONLY, REVIEW ONLY, NOT PUBLIC-POSTABLE, MANUAL REVIEW
REQUIRED, NO LIVE POSTING, NO PLATFORM API, NO PROVIDER/LLM API, NO WEB SEARCH /
SCRAPING / NEWS API, NO FINANCIAL ADVICE, NO SIGNAL LANGUAGE, NO CREDENTIALS
LOADED. Allowed operator actions are review/external/manual only
(review_source_context, choose_angle_card, copy_prompt_template_for_external_llm,
paste_external_draft_for_review, review_draft_flags, record_manual_decision,
rerun_local_validation, manually_record_public_url_later_if_jim_independently_posts_outside_repo).
Forbidden actions (auto_publish, schedule_post, live_publish, send_newsletter,
call_platform_api, call_provider_api, scrape_metrics, fetch_market_data,
auto_reply_or_dm, mark_public_ready_final, convert_to_trading_signal,
load_credentials) fail closed if presented as allowed.


## No Backend Server
`backend_server_required` is false and fails closed if true. The contract is a
static fixture; no server is started or required.

## No Frontend App / Assets Yet
`frontend_implementation_included` is false and fails closed if true. No HTML,
JS, CSS, or framework app is produced. A static UI is planned later via
`future_frontend_handoff.static_ui_planned_later`.

## No Repo Web Search / Scraping / News API / Market-Data API
The module reads local fixtures only and performs zero network or fetch
operations. `summary()` keeps every related counter at zero/false.

## No Provider/LLM API Calls
The repo never calls a provider; `provider_llm_api_allowed_now` fails closed.

## No Platform API / Live Posting / Scheduler
Platform API, live posting, and scheduler flags all fail closed.

## No Newsletter/CMS/Email Provider Action
Newsletter/CMS API flags fail closed; no provider is contacted.

## No Public-Ready Content Generation
`publish_ready`, `public_ready_allowed_now`, and `final_social_copy_generated`
must be false. The validator also fails closed if the view model represents any
draft as final ready-to-post social copy.

## No Credential/Env Reads
The module reads only local fixtures; it does not read `.env`, credentials, or
secrets. `credential_read_allowed_now` must be false.

## How This Supports Macro Thesis QA and the North Star
By forcing every UI section to keep limitations, source references, blockers,
manual review, and not-public-postable status visible, the contract ensures a
future UI cannot hide uncertainty. This amplifies macro thesis QA, data
sufficiency, forecast readiness, and failure forensics. It never frames Capital
Chronicle as a Bloomberg replacement, AI trading bot, signal service, execution
system, or guaranteed prediction engine.

## Capability Statement
No live posting, platform API, credential/env read, scheduler, scraping, web
search, news/RSS/market-data API, newsletter sending, CMS/email-provider
integration, LLM provider call, backend server, frontend app/assets, autonomous
reply/DM, publish approval, or public-ready copy capability was added by this
task. The layer is a local, fixture-driven, fail-closed UI data contract only.

