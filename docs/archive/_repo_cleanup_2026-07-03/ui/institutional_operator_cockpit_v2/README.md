# Operator Cockpit V2 (Static, Local, Fixture-Driven)

Task: TASK_CONTENTOPS_0174R_REFERENCE_DRIVEN_OPERATOR_COCKPIT_V2_FRONTEND_REBUILD_V0

A clean-room, local-only Operator Cockpit V2 for Capital Chronicle ContentOps.
It is an evidence-grade institutional cockpit for macro content governance,
forecast-readiness discipline, content safety, manual approval, and future
supervised publishing readiness. It is not a dashboard, scheduler, trading
terminal, publish console, or Bloomberg replacement.

This V2 is a fresh build under a new folder. It does not revive or salvage the
aborted text-only 0174 spike. The existing `ui/institutional_shell/` is
preserved and untouched.

## How To Open

Open `index.html` directly in a browser via `file://`. No server, no build
step, no network, no credentials, no dependencies.

```
A:\Capital Chronicle\tools\cc-live-contentops\ui\institutional_operator_cockpit_v2\index.html
```

## What It Is

- Static: vanilla HTML/CSS/JS only. No framework, no bundler, no CDN.
- Local-only: renders entirely from `view_model.js`
  (`window.CC_COCKPIT_V2_VIEW_MODEL`). No `fetch`, no `XMLHttpRequest`, no
  `WebSocket`, no `EventSource`, no remote URL, no remote font/icon/script.
- Fixture/view-model driven: a single canonical global state is the only
  source of operational truth.

## Files

- `index.html` — frame: fixed safety ribbon, canonical system header, left
  nav, main canvas, fixed directive bar.
- `styles.css` — dark Technical Matte institutional styling. System-safety
  colors only (never market direction). Local system font stacks only.
- `view_model.js` — canonical global state plus the seven screen view models.
- `cockpit.js` — local renderer. Reads the view model and renders screens with
  safe DOM text nodes (no remote calls).

## Screen Family

- Command Center
- Content Studio
- Publish Readiness Gate Matrix
- Evidence Vault
- Content Calendar / Workflow Board
- Visual Export / Screenshot-Safe Mode
- Settings / Safety Policy

## Source Of Truth vs Provenance

- Current operational truth comes only from
  `CC_COCKPIT_V2_VIEW_MODEL.global_state` (e.g. Current Repo Baseline
  `680d03d`, Last Product Code Baseline `496591f`).
- Historical screen provenance (e.g. `15b87ff`, `1c03ca0`, `444ef2c`) lives in
  `historical_screen_provenance` and is explicitly labelled
  "Historical Screen Provenance / Not Runtime Authority". It is never shown as
  current truth.
- The operator-supplied Stitch governance terminal folder was used as advisory
  visual reference only. It was not copied, not imported, and is not runtime.
  See `docs/TASK_CONTENTOPS_0174R_STITCH_REFERENCE_EXTRACTION.md`.

## Status Token Contract

Critical statuses carry `status`, `severity`, `label`, `reason`,
`evidence_ref_ids`, `allowed_actions`, `blocked_actions`, `current_truth`,
`historical_provenance`, and an optional `caveat`. Allowed vocabulary: PASS,
DEGRADED, BLOCKED, REVIEW_REQUIRED, LIVE_DISABLED, NOT_PUBLIC_POSTABLE,
FUTURE_ONLY, UNKNOWN, SECRET_REDACTED.

PASS means system-safe only. It never means publish-ready, forecast-ready,
live-ready, market-positive, or trade-positive. Color communicates system
safety only, never bullish/bearish or market direction.

## What It Is NOT

- No live posting, scheduling, scraping, autonomous replies/DMs.
- No real publish/connect/OAuth/API-key controls. Forbidden actions appear only
  as disabled, read-only policy text.
- No credentials, secrets, env paths, request URLs, or raw platform responses.
- No financial advice, no signal/trading language, no buy/sell/hold cues, no
  market-direction color semantics.
- No export/download/upload behavior. No screenshot automation.

## Safety Posture

Kill switch active. Live disabled. Platform/provider/scheduler/credential reads
disabled. Review-only, not public-postable. Credentials redacted. Browser/
Antigravity QA is deferred to a future explicit task after ChatGPT audits this
evidence.
