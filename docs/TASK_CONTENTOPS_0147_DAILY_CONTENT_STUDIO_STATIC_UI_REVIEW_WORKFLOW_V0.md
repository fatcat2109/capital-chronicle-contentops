# TASK_CONTENTOPS_0147 — Daily Content Studio Static UI Review Workflow (V0)

## Objective
Improve the accepted 0146 static Daily Content Studio UI into a more usable local
review workflow. This task adds local-only navigation, review status filters, a
selected-item inspector, and structured review affordances on top of the
fixture-only static frontend, so Jim can use it as a daily local operator review
surface. It also repairs a brace-nesting bug in the committed 0146 `app.js` that
prevented the render and load logic from executing.

This is a static UI workflow task only. It is explicitly:
- NOT a backend/server task
- NOT a platform/API task
- NOT a provider/LLM API task
- NOT a credential/API-key/OAuth setup task
- NOT a web/news/search/scraping task
- NOT a scheduler/posting task
- NOT a newsletter/CMS/email provider task
- NOT a public-ready copy generator

## Allowed Scope (built/changed in this task)
- `ui/daily_content_studio/index.html` — added section nav, review filter chips,
  API-key note, and selected-item inspector panel.
- `ui/daily_content_studio/styles.css` — styles for nav, filter chips, inspector,
  inspect links, detail cards, and the local filtered-out state.
- `ui/daily_content_studio/app.js` — fixed brace nesting; added local-only
  inspector, inspect links, view-only review filters, and workflow wiring.
- `ui/daily_content_studio/README.md` — workflow usage notes.
- `tests/test_daily_content_studio_static_frontend.py` — added workflow tests.
- `live_contentops/cli.py` — extended the optional static-frontend summary with
  workflow inventory flags (no server/browser/credential behavior).
- This runbook.

## Forbidden Scope (NOT built, NOT enabled)
- Backend server, API routes, live platform API clients, provider/LLM API calls.
- Web/search/news/RSS fetch, scraping, market-data API.
- Scheduling, posting, newsletter/CMS/email provider integration.
- Credential loading, `.env` reads, API keys, tokens, OAuth.
- Autonomous replies/DMs, public-ready final copy, one-click publish.
- Clipboard write automation, browser storage for secrets.

## How to Open / Use the Static UI Locally
Open `ui/daily_content_studio/index.html` directly in any modern browser
(double-click or drag into a browser window). No local server, build step, or
dependency install. The page reads the embedded `fixture_data.js` (a copy of the
accepted 0145 valid fixture) and renders all panels.

## How Navigation / Filter / Inspector Works Locally
- Navigation: the sticky `#section-nav` bar provides in-page anchor links to each
  section. No remote routing, no server.
- Review filters: the `#review-filters` chips (all, needs_review, blocked,
  safe_for_manual_review, source_required, limitation_required,
  not_public_postable) toggle a CSS `filtered-out` class to show/hide rendered
  panels in memory only. They never mutate files, call APIs, approve, publish,
  schedule, or export.
- Inspector: each section header gets an "inspect" link (a non-interactive span
  with role=button) that renders the selected item's review-only flags
  (review_only, manual_review_required, not_public_postable,
  source_references_visible, limitations_visible, blocked_actions_visible) into
  the `#item-inspector` panel. Selection is local and in-memory only.

## No Backend / Server Is Required
Plain HTML/CSS/JS opened from `file://`. No Flask/FastAPI/Django/Express, no API
routes. The optional CLI summary only prints a static asset/workflow inventory.

## No API Keys / Tokens Are Needed
A visible UI note states no platform API keys or tokens are needed and that
credential/API setup belongs to a later explicitly approved live-adapter task. No
keys, tokens, app secrets, OAuth, or bot tokens are requested or used.

## No Credentials Are Loaded
The UI does not read `.env`, credentials, cookies, or browser storage. It uses no
`localStorage`/`sessionStorage`.

## No Web / Search / Platform / Provider Calls
`app.js` makes no `fetch`, `XMLHttpRequest`, `WebSocket`, `EventSource`, dynamic
import, remote URL, or CDN reference, and uses no clipboard write automation. All
data is embedded locally.

## Publish / Schedule / Connect / OAuth / API-Key / Post-to-All Buttons Forbidden
The UI contains no active live-action controls. The only `<button>` elements are
local review-only filter chips. Forbidden operator actions (auto_publish,
schedule_post, live_publish, send_newsletter, call_platform_api, call_provider_api,
scrape_metrics, fetch_market_data, auto_reply_or_dm, mark_public_ready_final,
convert_to_trading_signal, load_credentials, connect_account, authorize_oauth,
post_to_all_platforms) are rendered as non-interactive, struck-through, disabled
spans separated from allowed manual-only actions.

## How This Renders the 0145 Contract and Extends 0146
The UI reads the same embedded 0145 UI data contract fixture used by 0146
(safety_banners, screen_sections, allowed/forbidden operator actions, audit
flags). 0147 adds the navigation, filtering, and inspection layer and repairs the
0146 brace bug so the render and load logic actually executes.

## How This Supports the North Star
By keeping blocked states, limitations, source references, manual review, and
not-public-postable status visible and easy to navigate, the UI amplifies macro
thesis QA, data sufficiency, forecast readiness, and failure forensics. It never
frames Capital Chronicle as a Bloomberg replacement, AI trading bot, signal
service, execution system, or guaranteed prediction engine.

## Capability Statement
No live posting, platform API, credential/env read, API key/OAuth, scheduler,
scraping, web search, news/RSS/market-data API, newsletter sending, CMS/email-
provider integration, LLM provider call, backend server, remote CDN/script,
clipboard write automation, publish approval, or public-ready copy capability was
added by this task. The layer is a local, static, fixture-driven, review-only UI
workflow only.

