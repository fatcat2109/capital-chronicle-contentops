# Institutional Shell Prototype — Handoff To Command Center (After 0160)

Task label: TASK_CONTENTOPS_0160_INSTITUTIONAL_SHELL_PROTOTYPE_STATIC_LOCAL_V0
Repo: A:\Capital Chronicle\tools\cc-live-contentops
Branch: master
Authority: governed by
`docs/INSTITUTIONAL_SHELL_PROTOTYPE_STATIC_LOCAL_AFTER_0160.md`.

Contract/spec only. This doc defines how task 0161 (Command Center Screen) builds
on the static shell. No active backend, no network, no env, no credentials are
introduced here.

## What 0161 Receives

- The static shell under `ui/institutional_shell/` (index.html, styles.css,
  app.js, fixture_data.js, README.md).
- The shell prototype packet schema + validator + CLI summary:
  - `schemas/institutional_shell_prototype_packet.schema.json`
  - `live_contentops/institutional_shell_prototype.py`
  - `python -m live_contentops.cli pre-alpha-institutional-shell-prototype-summary`
- The 0159 view-model contract V2 and valid fixture.

## What 0161 May Do

- Deepen the Command Center screen into a richer institutional view:
  command_center_status_header, blocked_reason_stack, kill_switch_indicator,
  safety counters, ready-for-review summary, top blockers, next allowed action.
- Continue using the static, local-only, fixture-driven pattern.
- Add focused tests and a validator/summary if consistent with repo style.

## What 0161 Must Not Do

- No backend, no server, no network (`fetch`/XHR/WebSocket/EventSource), no CDN.
- No env access, no credential reads.
- No live posting/scheduling/scraping/connect/OAuth/API-key controls.
- No new front-end dependency (vanilla HTML/CSS/JS only).
- No Antigravity (remains future-only until 0167 browser QA).
- No secrets, env paths, request URLs, raw platform responses, or raw vendor data.
- No signal/advice language; no red/green market-direction semantics.

## Binding Contract For 0161

- Drive the Command Center from the view model's `global_state` and the
  command_center screen view model.
- Render the global safety ribbon on first paint.
- Render every status with label + icon (never color-only).
- Render credential states as redacted tokens only.
- Render disallowed controls disabled + explained; never interactive.

## Acceptance For 0161 (Preview)

0161 is acceptable when it enriches the Command Center within the static shell,
preserves the safety ribbon and all fail-closed flags, adds tests/validator
coverage, introduces no dependency/backend/network, and keeps all secrets and
env paths out of files and evidence. Antigravity browser QA remains deferred to
0167.
