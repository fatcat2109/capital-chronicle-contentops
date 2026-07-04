# Institutional Shell Prototype — Static Local (After 0160)

Task label: TASK_CONTENTOPS_0160_INSTITUTIONAL_SHELL_PROTOTYPE_STATIC_LOCAL_V0
Repo: A:\Capital Chronicle\tools\cc-live-contentops
Branch: master
Baseline HEAD before this task: 15b87ff — "feat: add institutional ui view model contract"

This is the first frontend implementation task in the UI rebuild sequence. It
builds a static, local-only, fixture-driven institutional shell prototype using
the accepted 0158 design system and 0159 UI view-model contract V2. It does NOT
run a backend, add dependencies, run browser automation or Antigravity, read
credentials/env, or call any platform/provider/network API.

## 1. Owner Decision

The owner has decided to materialize the institutional control-terminal frame as a
static local shell. The shell demonstrates the futuristic-institutional-fintech
look and the safe-by-default posture across all 12 screens, with no live controls.

## 2. Accepted Baselines

- 0158 design system: `docs/INSTITUTIONAL_DESIGN_SYSTEM_AND_FUTURISTIC_FINTECH_VISUAL_CONTRACT_AFTER_0158.md`
- 0159 view-model contract V2: `docs/INSTITUTIONAL_UI_VIEW_MODEL_CONTRACT_V2_AFTER_0159.md`
- 0159 valid fixture: `fixtures/institutional_ui_view_model_contract_v2_valid.json`

## 3. What Was Built

New static path: `ui/institutional_shell/`
- `index.html` — frame: safety ribbon, status bar, left nav, main region.
- `styles.css` — dark institutional terminal styling, operational status colors only.
- `app.js` — vanilla JS renderer; reads `window.CC_INSTITUTIONAL_SHELL_FIXTURE`.
- `fixture_data.js` — local fixture derived from the 0159 valid view-model fixture.
- `README.md` — local open runbook.

## 4. How To Open

Open `ui/institutional_shell/index.html` directly via `file://`. No server, no
build, no network, no dependency.

## 5. What It Renders

- Global safety ribbon: LOCAL_ONLY, DRY_RUN_ONLY, REVIEW_ONLY, NOT_PUBLIC_POSTABLE,
  LIVE_DISABLED, KILL_SWITCH_ACTIVE, SECRET_REDACTED, NO_FINANCIAL_ADVICE,
  NO_SIGNAL_LANGUAGE.
- Top status bar: system mode, accepted HEAD, kill switch, current gate, next
  allowed action, evidence count, active blockers, live/API disabled.
- Left navigation across all 12 screens.
- Command Center as the default screen.
- Per-screen cards: required status tokens, safety banners, primary components,
  evidence references, blocked reason stack, redaction badge, forbidden-controls
  (disabled, read-only), and policy/behavior notes.
- A screenshot-safe-mode watermark on every screen.

## 6. Safety Posture (Enforced)

- Static/local-only, fixture/mock-data-only.
- No backend, no dependency, no `fetch`/XHR/WebSocket/EventSource, no remote URL.
- No live posting, scheduling, scraping, autonomous replies/DMs.
- No real publish/connect/OAuth/API-key controls; forbidden actions are disabled
  read-only text only.
- No secrets, env paths, request URLs, raw platform responses, or raw vendor data.
- No financial advice, no signal/trading language, no buy/sell/long/short cues, no
  bullish/bearish (red/green = market-direction) semantics. Red/green are
  operational PASS/BLOCKED only.

## 7. Screen-Specific Guarantees

- Telegram Pilot Gate: read-only redacted gate steps; bot token / target channel
  presence redacted only; getMe/sendMessage/posting/live adapter disabled; channel
  write permission unvalidated; next gate required.
- Publish Readiness Tower: dry-run only, live disabled, credentials redacted,
  platform API disabled, scheduler disabled, one-button publish-all disabled,
  manual approval required.
- Content Calendar: allowed states only (idea, source-needed, draft-review,
  blocked, operator-approved-for-manual, manually-posted, metrics-entered); no
  scheduled / live-published-by-system / auto-publish-ready / public-ready.
- Settings / Safety Policy: read-only policy display; no credential values; no API
  or live publishing toggles.

## 8. Validation Surface

- Schema: `schemas/institutional_shell_prototype_packet.schema.json`.
- Validator + summary: `live_contentops/institutional_shell_prototype.py`.
- CLI summary: `python -m live_contentops.cli pre-alpha-institutional-shell-prototype-summary`.
- Tests: `tests/test_institutional_shell_prototype.py` (static-asset inspection,
  no browser).

## 9. Relationship To Telegram Live-Gate Sequencing

This shell does NOT supersede Telegram live-gate sequencing. The Telegram Pilot
Gate screen is a read-only, redacted display only; it never calls getMe or
sendMessage and never reveals credentials.
