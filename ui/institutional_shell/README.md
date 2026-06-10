# Institutional Shell Prototype (Static, Local, After 0160)

Task: TASK_CONTENTOPS_0160_INSTITUTIONAL_SHELL_PROTOTYPE_STATIC_LOCAL_V0

This is the first static local institutional shell prototype for Capital Chronicle
ContentOps. It implements the institutional fintech control-terminal frame defined
by the accepted 0158 design system and the 0159 UI view-model contract V2.

## How To Open

Open `index.html` directly in a browser using `file://`. No server, no build
step, no network, no dependencies.

```
A:\Capital Chronicle\tools\cc-live-contentops\ui\institutional_shell\index.html
```

## What It Is

- Static: vanilla HTML/CSS/JS only. No framework, no bundler, no CDN.
- Local-only: renders entirely from `fixture_data.js`
  (`window.CC_INSTITUTIONAL_SHELL_FIXTURE`). No `fetch`, no `XMLHttpRequest`,
  no WebSocket, no EventSource, no remote URL.
- Fixture/mock-data-only: data is derived from the accepted 0159 valid
  view-model fixture.

## What It Shows

- Global safety ribbon (LOCAL_ONLY, DRY_RUN_ONLY, REVIEW_ONLY,
  NOT_PUBLIC_POSTABLE, LIVE_DISABLED, KILL_SWITCH_ACTIVE, SECRET_REDACTED,
  NO_FINANCIAL_ADVICE, NO_SIGNAL_LANGUAGE).
- Top status bar (system mode, accepted HEAD, kill switch, current gate, next
  allowed action, evidence count, active blockers, live/API disabled).
- Left navigation across all 12 screens.
- Command Center as the default screen.
- Per-screen: title, purpose, required status tokens, safety banners, blocked
  reasons, evidence refs, primary components, forbidden-controls notice,
  redaction state, screenshot-safe behavior note.
- A screenshot-safe-mode indicator (local-only, non-networked).

## What It Is NOT

- No live posting, scheduling, scraping, autonomous replies/DMs.
- No real publish/connect/OAuth/API-key controls. Forbidden actions appear only
  as disabled, read-only policy text.
- No credentials, secrets, env paths, request URLs, or raw platform responses.
- No financial advice, no signal/trading language, no buy/sell/long/short cues,
  no bullish/bearish color semantics.

## Safety Posture

Kill switch active. Live disabled. Review-only by default. Not public-postable.
Credentials redacted. This shell does not supersede Telegram live-gate sequencing;
the Telegram Pilot Gate screen is a read-only, redacted display only.
