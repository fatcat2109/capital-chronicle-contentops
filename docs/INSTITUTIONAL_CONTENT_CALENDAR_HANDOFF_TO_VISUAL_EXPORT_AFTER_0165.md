# Institutional Content Calendar — Handoff To Visual Export (After 0165)

Task label: TASK_CONTENTOPS_0165_INSTITUTIONAL_CONTENT_CALENDAR_AND_WORKFLOW_BOARD_SCREEN_V0
Repo: A:\Capital Chronicle\tools\cc-live-contentops
Branch: master
Authority: governed by `docs/INSTITUTIONAL_CONTENT_CALENDAR_AND_WORKFLOW_BOARD_SCREEN_AFTER_0165.md`.

Contract/spec only. This doc defines how task 0166 (Visual Export / Screenshot-Safe
Mode) builds on the Content Calendar + Workflow Board screen. No active backend, no
network, no env, no credentials are introduced here.

## What 0166 Receives

- The static shell with Command Center (0161), Content Studio (0162), Publish
  Readiness Tower (0163), Evidence Vault (0164), and Content Calendar + Workflow Board
  (0165) screens under `ui/institutional_shell/`.
- The calendar/workflow packet schema + validator + CLI summary:
  - `schemas/institutional_content_calendar_workflow_board_screen_packet.schema.json`
  - `live_contentops/institutional_content_calendar_workflow_board_screen.py`
  - `python -m live_contentops.cli pre-alpha-institutional-content-calendar-workflow-board-screen-summary`

## What 0166 May Do

- Build the Visual Export / Screenshot-Safe Mode screen using the same
  fixture-driven pattern.
- Define redacted screenshot-safe export rules surfaced in the UI.
- Continue using the static, local-only, fixture-driven model.
- Add focused tests and a validator/summary if consistent with repo style.

## What 0166 Must Not Do

- No backend, no server, no network (`fetch`/XHR/WebSocket/EventSource), no CDN.
- No env access, no credential reads, no platform/provider API.
- No live posting/scheduling/scraping/connect/OAuth/API-key controls.
- No export-to-platform; export must be local and redacted only.
- No new front-end dependency (vanilla HTML/CSS/JS only).
- No Antigravity (remains future-only until 0167 browser QA).
- No secrets, env paths, request URLs, raw platform responses, or raw vendor data in
  any export preview.
- No false public-ready or false readiness claims in any export artifact.

## Binding Contract For 0166

- Keep the global safety ribbon and all prior screens intact and non-regressing.
- Screenshot-safe mode must redact secrets, env paths, request URLs, raw platform
  responses, and raw vendor data.
- Export artifacts must show limitations and never imply public-ready or signal/advice.
- Render every status with label + icon (never color-only).

## Acceptance For 0166 (Preview)

0166 is acceptable when it builds the Visual Export / Screenshot-Safe Mode screen within
the static shell with redacted export rules, preserves prior screens and all fail-closed
flags, adds tests/validator coverage, introduces no dependency/backend/network, enables
no export-to-platform/posting/scheduling, and keeps all secrets and env paths out of
files and evidence. Antigravity browser QA remains deferred to 0167.
