# Antigravity Browser QA Strategy (After 0157) — Future Use Only

Task label: TASK_CONTENTOPS_0157_INSTITUTIONAL_UI_UX_FRONTEND_REBUILD_MASTER_PLAN_V0
Repo: A:\Capital Chronicle\tools\cc-live-contentops
Branch: master
Authority: governed by
`docs/INSTITUTIONAL_UI_UX_FRONTEND_REBUILD_MASTER_PLAN_AFTER_0157.md`.

This is a FUTURE-ONLY plan. Antigravity is NOT run in 0157, and NOT run in
0158–0166 or 0168. Antigravity is used only in task 0167, and only for browser QA
against a Cline-built, locally testable UI. No Antigravity browser automation,
screenshots, or video occur in this 0157 planning task.

## Why Antigravity Is QA-Only

- Antigravity is weaker than Cline for architecture, schema design, and building.
- Cline owns the structure: design system, view-model contract, schemas, static
  front-end code, fixtures, and deterministic tests.
- Antigravity adds value only at the browser layer: opening the built UI, walking
  screens, and capturing visual evidence a headless test cannot easily express.

## When Antigravity Runs

- Only after a Cline-built, locally testable UI exists (output of 0158–0166).
- Only in task 0167.
- If the UI is not yet locally testable from `file://`, 0167 is BLOCKED and
  Antigravity must not run.

## What Antigravity May Do (0167)

- Open `ui/institutional/index.html` in a browser locally.
- Navigate each screen following a narrow, screen-by-screen, expected-state script.
- Click non-live, in-app controls (navigation, expand/collapse, safe-mode toggle).
- Capture screenshots of each screen.
- Record a walkthrough video of the navigation.
- Confirm the global safety banner is present on every screen.
- Confirm no live control is interactive.
- File a structured visual-bug report.

## What Antigravity Must Not Do

- Must not design or change architecture (fixes happen in Cline task 0168).
- Must not broaden scope beyond the QA script.
- Must not call any platform/provider/network/search/news/market-data API.
- Must not call Telegram, getMe, sendMessage, or any API.
- Must not read, request, or inspect secrets, env values, or env paths.
- Must not enable live posting, scheduling, scraping, or any live capability.
- Must not edit code or commit changes.

## Antigravity Prompt Shape (Narrow, Screen-By-Screen)

For each screen, the 0167 prompt gives Antigravity:
- The screen name and how to reach it from the shell nav.
- The expected status tokens and safety elements for that screen.
- The expected disabled/explained live controls.
- The exact screenshot to capture and what to confirm.
- An explicit instruction: report bugs only; do not fix, do not redesign, do not
  call any API, do not inspect secrets.

Example (Command Center): "Open the terminal. Confirm the global safety banner
shows kill-switch and LIVE_DISABLED on first paint. Confirm the blocked summary
lists reasons. Capture a screenshot named command_center.png. Report any visual
issue. Do not click any disabled live control; do not call any API."

## Required Browser QA Evidence (0167 Output)

The 0167 evidence report must include:
- Screenshot list (one per screen, named per screen).
- Navigation coverage (every screen reached, with pass/fail per screen).
- Visual bug list (each bug tied to a screen and the quality-bar row it affects).
- Safety-banner confirmation (banner present on every screen).
- No-live-controls confirmation (no live/publish/schedule/connect control was
  interactive).
- Confirmation that no API call, credential read, or secret inspection occurred.
- Confirmation that no secret/env value/env path appears in any screenshot.

## Handoff To 0168

The 0167 visual-bug list is the input to task 0168 (Cline polish pass). Cline fixes
the catalogued issues; Antigravity does not run again in 0168. Any bug Cline defers
is recorded with a reason in the 0168 polish notes.
