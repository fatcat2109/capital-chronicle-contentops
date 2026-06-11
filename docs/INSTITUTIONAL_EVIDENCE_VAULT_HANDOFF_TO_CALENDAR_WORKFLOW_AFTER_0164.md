# Institutional Evidence Vault — Handoff To Calendar + Workflow Board (After 0164)

Task label: TASK_CONTENTOPS_0164_INSTITUTIONAL_EVIDENCE_VAULT_AND_AUDIT_TIMELINE_SCREEN_V0
Repo: A:\Capital Chronicle\tools\cc-live-contentops
Branch: master
Authority: governed by `docs/INSTITUTIONAL_EVIDENCE_VAULT_AND_AUDIT_TIMELINE_SCREEN_AFTER_0164.md`.

Contract/spec only. This doc defines how task 0165 (Calendar + Workflow Board)
builds on the Evidence Vault screen. No active backend, no network, no env, no
credentials are introduced here.

## What 0165 Receives

- The static shell with Command Center (0161), Content Studio (0162), Publish
  Readiness Tower (0163), and Evidence Vault (0164) screens under
  `ui/institutional_shell/`.
- The evidence vault packet schema + validator + CLI summary:
  - `schemas/institutional_evidence_vault_audit_timeline_screen_packet.schema.json`
  - `live_contentops/institutional_evidence_vault_audit_timeline_screen.py`
  - `python -m live_contentops.cli pre-alpha-institutional-evidence-vault-audit-timeline-screen-summary`

## What 0165 May Do

- Deepen the Content Calendar + Workflow Board screen using the same
  fixture-driven pattern.
- Continue using the static, local-only, fixture-driven model.
- Add focused tests and a validator/summary if consistent with repo style.

## What 0165 Must Not Do

- No backend, no server, no network (`fetch`/XHR/WebSocket/EventSource), no CDN.
- No env access, no credential reads, no platform/provider API.
- No live posting/scheduling/scraping/connect/OAuth/API-key controls.
- No scheduled/live_published_by_system/auto_publish_ready/public_ready calendar
  states.
- No new front-end dependency (vanilla HTML/CSS/JS only).
- No Antigravity (remains future-only until 0167 browser QA).
- No secrets, env paths, request URLs, raw platform responses, or raw vendor data.

## Binding Contract For 0165

- Keep the global safety ribbon and all prior screens intact and non-regressing.
- Allowed calendar item states only: idea, source-needed, draft-review, blocked,
  operator-approved-for-manual, manually-posted, metrics-entered.
- Forbidden calendar states: scheduled, live_published_by_system,
  auto_publish_ready, public_ready.
- Render every status with label + icon (never color-only).

## Acceptance For 0165 (Preview)

0165 is acceptable when it enriches the Calendar + Workflow Board within the static
shell with only allowed item states, preserves prior screens and all fail-closed
flags, adds tests/validator coverage, introduces no dependency/backend/network,
enables no scheduling/live publishing, and keeps all secrets and env paths out of
files and evidence. Antigravity browser QA remains deferred to 0167.
