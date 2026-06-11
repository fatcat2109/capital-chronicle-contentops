# Institutional Publish Readiness Tower — Handoff To Evidence Vault (After 0163)

Task label: TASK_CONTENTOPS_0163_INSTITUTIONAL_PUBLISH_READINESS_TOWER_SCREEN_V0
Repo: A:\Capital Chronicle\tools\cc-live-contentops
Branch: master
Authority: governed by `docs/INSTITUTIONAL_PUBLISH_READINESS_TOWER_SCREEN_AFTER_0163.md`.

Contract/spec only. This doc defines how task 0164 (Evidence Vault) builds on the
Publish Readiness Tower screen. No active backend, no network, no env, no
credentials are introduced here.

## What 0164 Receives

- The static shell with Command Center (0161), Content Studio (0162), and Publish
  Readiness Tower (0163) screens under `ui/institutional_shell/`.
- The tower packet schema + validator + CLI summary:
  - `schemas/institutional_publish_readiness_tower_screen_packet.schema.json`
  - `live_contentops/institutional_publish_readiness_tower_screen.py`
  - `python -m live_contentops.cli pre-alpha-institutional-publish-readiness-tower-screen-summary`
- The 0159 view-model contract V2 and prior shell assets.

## What 0164 May Do

- Deepen the Evidence Vault screen into a richer task-evidence/audit surface using
  the same fixture-driven pattern.
- Continue using the static, local-only, fixture-driven model.
- Add focused tests and a validator/summary if consistent with repo style.

## What 0164 Must Not Do

- No backend, no server, no network (`fetch`/XHR/WebSocket/EventSource), no CDN.
- No env access, no credential reads, no platform/provider API.
- No live posting/scheduling/scraping/connect/OAuth/API-key controls.
- No new front-end dependency (vanilla HTML/CSS/JS only).
- No Antigravity (remains future-only until 0167 browser QA).
- No secrets, env paths, request URLs, raw platform responses, or raw vendor data.
- No signal/advice language; no red/green market-direction semantics.

## Binding Contract For 0164

- Keep the global safety ribbon, Command Center, Content Studio, and Publish
  Readiness Tower intact and non-regressing.
- Render task evidence packets, commits, validation results, secret scans,
  forbidden-scope status, active blockers, and next-task discipline.
- Render every status with label + icon (never color-only).
- Keep all secrets and env paths out of the evidence surface.

## Acceptance For 0164 (Preview)

0164 is acceptable when it enriches the Evidence Vault within the static shell,
preserves prior screens and all fail-closed flags, adds tests/validator coverage,
introduces no dependency/backend/network, generates no public-ready content, and
keeps all secrets and env paths out of files and evidence. Antigravity browser QA
remains deferred to 0167.
