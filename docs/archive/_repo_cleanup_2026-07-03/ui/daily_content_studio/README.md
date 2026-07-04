# Daily Content Studio — Static Frontend v0

Local-only, fixture-driven, review-only operator UI. It renders the accepted
0145 UI data contract fixture and makes safety/blocked states visible.

## How to open

Just open `index.html` in any modern browser:

- Double-click `ui/daily_content_studio/index.html`, or
- Drag the file into a browser window.

No local server is required. No build step. No dependency install.

## What it shows

- Safety banners (LOCAL ONLY, REVIEW ONLY, NOT PUBLIC-POSTABLE, etc.)
- Daily run overview, source context, angle cards
- External LLM prompt handoff (repo does not execute prompts)
- Markdown review export, external draft review
- Operator decision ledger, platform-fit notes
- Blockers and limitations
- Manual actions: allowed actions vs forbidden actions (forbidden are rendered
  disabled / blocked and are non-interactive)
- Audit/status panel (all live/provider/platform/scheduler/credential flags false)
- Future frontend handoff notes

## Safety guarantees

- No backend/server. No API routes.
- No API keys, tokens, OAuth, or credentials. None are loaded or requested.
- No network calls, no `fetch`, no remote URLs, no CDN, no external scripts.
- No `localStorage`/`sessionStorage` use.
- No Publish / Schedule / Send / Connect / OAuth / API-key / Post buttons.
- No publish approval. No final ready-to-post copy.

## Data source

`fixture_data.js` embeds a copy of
`fixtures/daily_content_studio_ui/daily_content_studio_ui_data_contract_valid.json`
(also kept here as `daily_content_studio_ui_data_contract_fixture.json`). The
embed lets the page render from `file://` without any fetch.
