# Institutional Content Studio — Handoff To Publish Readiness Tower (After 0162)

Task label: TASK_CONTENTOPS_0162_INSTITUTIONAL_CONTENT_STUDIO_REBUILD_SCREEN_V0
Repo: A:\Capital Chronicle\tools\cc-live-contentops
Branch: master
Authority: governed by `docs/INSTITUTIONAL_CONTENT_STUDIO_REBUILD_SCREEN_AFTER_0162.md`.

Contract/spec only. This doc defines how task 0163 (Publish Readiness Tower)
builds on the Content Studio screen. No active backend, no network, no env, no
credentials are introduced here.

## What 0163 Receives

- The static shell with rich Command Center (0161) and Content Studio (0162)
  screens under `ui/institutional_shell/`.
- The content studio packet schema + validator + CLI summary:
  - `schemas/institutional_content_studio_screen_packet.schema.json`
  - `live_contentops/institutional_content_studio_screen.py`
  - `python -m live_contentops.cli pre-alpha-institutional-content-studio-screen-summary`
- The 0159 view-model contract V2 and prior shell assets.

## What 0163 May Do

- Deepen the Publish Readiness Tower screen into a richer dry-run readiness
  matrix using the same fixture-driven pattern.
- Continue using the static, local-only, fixture-driven model.
- Add focused tests and a validator/summary if consistent with repo style.

## What 0163 Must Not Do

- No backend, no server, no network (`fetch`/XHR/WebSocket/EventSource), no CDN.
- No env access, no credential reads, no platform/provider API.
- No live posting/scheduling/scraping/connect/OAuth/API-key controls.
- No one-button publish-all; no real publish/connect controls.
- No new front-end dependency (vanilla HTML/CSS/JS only).
- No Antigravity (remains future-only until 0167 browser QA).
- No secrets, env paths, request URLs, raw platform responses, or raw vendor data.
- No signal/advice language; no red/green market-direction semantics.

## Binding Contract For 0163

- Keep the global safety ribbon, Command Center, and Content Studio intact and
  non-regressing.
- Render the readiness matrix as dry-run only with credentials redacted.
- Render every status with label + icon (never color-only).
- Render disallowed controls disabled + explained; never interactive.
- Keep manual approval required and one-button publish-all disabled.

## Acceptance For 0163 (Preview)

0163 is acceptable when it enriches the Publish Readiness Tower within the static
shell as dry-run only, preserves prior screens and all fail-closed flags, adds
tests/validator coverage, introduces no dependency/backend/network, enables no
live publishing, and keeps all secrets and env paths out of files and evidence.
Antigravity browser QA remains deferred to 0167.
