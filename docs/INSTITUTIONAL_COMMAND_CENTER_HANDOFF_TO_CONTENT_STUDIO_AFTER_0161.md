# Institutional Command Center — Handoff To Content Studio (After 0161)

Task label: TASK_CONTENTOPS_0161_INSTITUTIONAL_COMMAND_CENTER_SCREEN_V0
Repo: A:\Capital Chronicle\tools\cc-live-contentops
Branch: master
Authority: governed by `docs/INSTITUTIONAL_COMMAND_CENTER_SCREEN_AFTER_0161.md`.

Contract/spec only. This doc defines how task 0162 (Content Studio Rebuild) builds
on the Command Center screen. No active backend, no network, no env, no
credentials are introduced here.

## What 0162 Receives

- The static shell with a rich Command Center under `ui/institutional_shell/`.
- The command center packet schema + validator + CLI summary:
  - `schemas/institutional_command_center_screen_packet.schema.json`
  - `live_contentops/institutional_command_center_screen.py`
  - `python -m live_contentops.cli pre-alpha-institutional-command-center-screen-summary`
- The 0159 view-model contract V2 and the 0160 shell prototype assets.

## What 0162 May Do

- Deepen the Daily Content Studio and Draft Inspector screens into richer
  institutional review surfaces using the same fixture-driven pattern.
- Continue using the static, local-only, fixture-driven model.
- Add focused tests and a validator/summary if consistent with repo style.

## What 0162 Must Not Do

- No backend, no server, no network (`fetch`/XHR/WebSocket/EventSource), no CDN.
- No env access, no credential reads.
- No live posting/scheduling/scraping/connect/OAuth/API-key controls.
- No final public-ready social copy generation.
- No new front-end dependency (vanilla HTML/CSS/JS only).
- No Antigravity (remains future-only until 0167 browser QA).
- No secrets, env paths, request URLs, raw platform responses, or raw vendor data.
- No signal/advice language; no red/green market-direction semantics.

## Binding Contract For 0162

- Keep the global safety ribbon and Command Center intact and non-regressing.
- Drive Content Studio screens from the view model's screen definitions.
- Render every status with label + icon (never color-only).
- Render review-only / not-public-postable / manual-review-required banners.
- Render disallowed controls disabled + explained; never interactive.

## Acceptance For 0162 (Preview)

0162 is acceptable when it enriches the Content Studio review surfaces within the
static shell, preserves the Command Center and all fail-closed flags, adds
tests/validator coverage, introduces no dependency/backend/network, generates no
public-ready copy, and keeps all secrets and env paths out of files and evidence.
Antigravity browser QA remains deferred to 0167.
