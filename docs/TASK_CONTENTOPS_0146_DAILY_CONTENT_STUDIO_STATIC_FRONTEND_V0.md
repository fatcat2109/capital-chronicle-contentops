# TASK_CONTENTOPS_0146 — Daily Content Studio Static Frontend (V0)

## Objective
Build the first actual local frontend for Jim: a static, fixture-driven,
review-only operator UI that renders the accepted 0145 UI data contract and makes
safety/blocked states visible. It displays safety banners, daily run overview,
source context, angle cards, external LLM prompt handoff, Markdown review export
summary, external draft review, operator decision ledger, platform-fit notes,
blockers and limitations, manual actions, audit/status panel, and future
frontend handoff notes.

This is static local UI only. It is explicitly:
- NOT a backend/server task
- NOT a live platform/API task
- NOT a provider/LLM API task
- NOT a web/news/search/scraping task
- NOT a scheduler/posting task
- NOT a newsletter/CMS/email provider task
- NOT a public-ready copy generator
- NOT a credential/API-key/OAuth task

## Allowed Scope (built in this task)
- `ui/daily_content_studio/index.html` — app shell + section containers.
- `ui/daily_content_studio/styles.css` — layout + visible disabled/blocked states.
- `ui/daily_content_studio/app.js` — fixture-only render logic, no network.
- `ui/daily_content_studio/fixture_data.js` — embedded copy of the 0145 valid
  fixture (lets the page render from `file://` with no fetch).
- `ui/daily_content_studio/daily_content_studio_ui_data_contract_fixture.json` —
  fixture copy.
- `ui/daily_content_studio/README.md`.
- Optional CLI command `pre-alpha-daily-content-studio-static-frontend-summary`
  (static asset inventory / safety summary only; no server, no credential read).
- Tests in `tests/test_daily_content_studio_static_frontend.py`.
- This runbook.

## Forbidden Scope (NOT built, NOT enabled)
- Backend server (Flask/FastAPI/Django/Express), API routes.
- Live platform API clients, provider/LLM API calls.
- Web/search/news/RSS fetch, scraping, market-data API.
- Scheduling, posting, newsletter/CMS/email provider integration.
- Credential loading, `.env` reads, API keys, tokens, OAuth.
- Autonomous replies/DMs, public-ready final copy, one-click publish.

## How to Open / Use the Static UI Locally
Open `ui/daily_content_studio/index.html` directly in any modern browser
(double-click or drag into a browser window). No local server, no build step, no
dependency install. The page reads the embedded `fixture_data.js` (a copy of the
accepted 0145 valid fixture) and renders all panels.

## No Backend / Server Is Required
The UI is plain HTML/CSS/JS opened from `file://`. There is no Flask/FastAPI/
Django/Express server and no API routes. The optional CLI summary command only
prints a static asset inventory; it never starts a server.

## No API Keys Are Needed
No platform API keys, tokens, app secrets, OAuth credentials, or bot tokens are
requested or used. API/key setup is explicitly deferred to a later, separately
approved credential/live-adapter task.

## No Credentials Are Loaded
The UI does not read `.env`, credentials, cookies, or browser storage. It uses no
`localStorage`/`sessionStorage`.

## No Web / Search / Platform / Provider Calls
`app.js` makes no `fetch`, no `XMLHttpRequest`, no remote URLs, no CDN, and loads
no external scripts. All data is embedded locally.

## Publish / Schedule / Connect Buttons Are Forbidden
The UI contains no `<button>` elements at all in v0. Forbidden operator actions
(auto_publish, schedule_post, live_publish, send_newsletter, call_platform_api,
call_provider_api, scrape_metrics, fetch_market_data, auto_reply_or_dm,
mark_public_ready_final, convert_to_trading_signal, load_credentials) are
rendered as non-interactive, struck-through, disabled-styled spans separated from
the allowed manual-only actions.

## How This Frontend Renders the 0145 UI Data Contract
The UI reads the 0145 packet's safety_banners, screen_sections,
allowed_operator_actions, forbidden_operator_actions, source_contracts, and
audit/status flags. Each section surfaces review_only, manual_review_required,
not_public_postable, limitations_visible, source_references_visible, and
blocked_actions_visible. The audit panel shows every live/provider/platform/
scheduler/credential flag as false.

## How This Supports the North Star
By making blocked states, limitations, source references, manual review, and
not-public-postable status visible at all times, the UI amplifies macro thesis
QA, data sufficiency, forecast readiness, and failure forensics. It never frames
Capital Chronicle as a Bloomberg replacement, AI trading bot, signal service,
execution system, or guaranteed prediction engine.

## Capability Statement
No live posting, platform API, credential/env read, API key/OAuth, scheduler,
scraping, web search, news/RSS/market-data API, newsletter sending, CMS/email-
provider integration, LLM provider call, backend server, remote CDN/script,
publish approval, or public-ready copy capability was added by this task. The
layer is a local, static, fixture-driven, review-only frontend only.

