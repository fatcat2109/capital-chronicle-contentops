# Institutional Antigravity Browser QA Manual Runbook (After 0168)

Task label: TASK_CONTENTOPS_0168_ANTIGRAVITY_BROWSER_QA_STRATEGY_AND_MANUAL_RUNBOOK_V0
Repo: A:\Capital Chronicle\tools\cc-live-contentops
Branch: master

Manual runbook only. Antigravity was NOT run in 0168. This runbook is executed only
under a future explicit operator/ChatGPT GO.

## Manual Open Instructions

1. Open `ui/institutional_shell/index.html` directly via `file://` in a browser.
2. No server, no build step, no network, no credentials, no dependencies.
3. Do not log into any platform. Prefer a clean browser profile with no credentials.
4. Do not open devtools network tab actions or run console scripts.

## Per-Screen Visual Checklist (all 12 screens)

For each screen verify:
- screen title present
- safety/status labels present
- limitations/evidence visible where applicable
- disabled controls visibly disabled (read-only chips, not active buttons)
- no secret / raw env path / raw platform response visible
- no active publish/schedule/export/API behavior
- visual layout readable
- no red/green market-direction semantics

Screens:
command_center, content_lane_control, daily_content_studio, draft_inspector,
grounded_news_angle_lab, publish_readiness_tower, telegram_pilot_gate,
approval_queue, content_calendar, evidence_vault, visual_export_studio,
settings_safety_policy.

## High-Priority Screen Checks

- Command Center: kill switch active, status cards, next allowed action.
- Content Studio: lanes, grounded-news rule, source/evidence requirements, review-only.
- Publish Readiness Tower: 8 platforms dry-run only, Telegram gate disabled/redacted,
  0 live-enabled.
- Evidence Vault: 0163 minor evidence gap visible, evidence mutation disabled, audit
  timeline visible.
- Content Calendar: manual workflow only, forbidden states not active, metrics manual.
- Visual Export: screenshot not captured, export disabled, redaction/watermarks
  visible, Antigravity future-only.

## Stop Conditions (Stop Immediately)

- A secret / env value / path / raw response appears.
- Any external URL opens.
- Any control attempts network/publish/export.
- Browser profile exposes credentials.
- The local shell requires a server or network.
- Antigravity requests broader permissions than scoped.

## PASS / BLOCKED / FAIL Summary

PASS: all 12 screens reachable, no rendering crash, no broken nav, labels visible,
disabled controls clear, no secret/raw env/raw response visible, no active
live/post/schedule/export controls, no external URL/network use, no Antigravity side
effects, no screenshots unless explicitly authorized, no repo mutation except scoped
evidence docs.

BLOCKED: browser cannot open local file; screen cannot render; nav broken; suspected
secret visible; active forbidden control appears; network/external URL required;
screenshot/export required without authorization; credential/browser-profile safety
ambiguity.

FAIL: secret/env displayed or captured; external site opened; network/API call made;
platform login used; live posting/scheduling/export attempted; screenshot captured
without authorization; Antigravity run outside scope; evidence mutated outside scope;
repo files changed outside allowed scope; forbidden controls active.

## Next Allowed Action

AWAIT OPERATOR/CHATGPT_AUDIT_OF_0168_RUNBOOK_EVIDENCE_BEFORE_ANY_BROWSER_OR_ANTIGRAVITY_TASK
