# Institutional UI View-Model Handoff to Shell Prototype (After 0159)

Task label: TASK_CONTENTOPS_0159_INSTITUTIONAL_UI_VIEW_MODEL_CONTRACT_V2_V0
Repo: A:\Capital Chronicle\tools\cc-live-contentops
Branch: master
Authority: governed by
`docs/INSTITUTIONAL_UI_VIEW_MODEL_CONTRACT_V2_AFTER_0159.md`.

Contract/spec only. This doc defines how task 0160 (Institutional Shell Prototype)
consumes the V2 view-model contract. No active front-end code, no backend, no
network, no env, no credentials are introduced here.

## What 0160 Receives

- The V2 view-model contract:
  `docs/INSTITUTIONAL_UI_VIEW_MODEL_CONTRACT_V2_AFTER_0159.md`.
- The per-screen view models:
  `docs/INSTITUTIONAL_UI_SCREEN_VIEW_MODELS_AFTER_0159.md`.
- The fixture/binding strategy:
  `docs/INSTITUTIONAL_UI_VIEW_MODEL_FIXTURE_AND_BINDING_STRATEGY_AFTER_0159.md`.
- The validated packet schema:
  `schemas/institutional_ui_view_model_contract_v2_packet.schema.json`.
- The deterministic validator + CLI summary:
  `live_contentops/institutional_ui_view_model_contract_v2.py`.
- Valid and invalid fixtures under `fixtures/`.

## What 0160 May Do

- Render these fixtures in a static, vanilla HTML/CSS/JS shell under
  `ui/institutional/`.
- Embed the valid view-model fixture for `file://` rendering (the existing
  `ui/daily_content_studio/fixture_data.js` pattern).
- Build the global safety ribbon, left-nav/command palette, and empty screen
  frames for all 12 screens.

## What 0160 Must Not Do

- No live data, no backend, no server.
- No browser API calls (`fetch`), no CDN, no external scripts, no storage.
- No env access, no credential reads.
- No active publishing/scheduling/connect controls.
- No new front-end dependency (vanilla HTML/CSS/JS only).
- No Antigravity (Antigravity remains future-only until 0167).

## Binding Contract For 0160

- Drive every screen from the view model's `screens[]` and `global_state`.
- Render the global safety ribbon from `global_state` on first paint.
- Render every status with label + icon (never color-only).
- Render credential states as redacted tokens only.
- Render disallowed controls disabled + explained; never interactive.

## Acceptance For 0160 (Preview)

0160 is acceptable when it renders the shell from the V2 fixture with the global
safety ribbon visible on first paint, all 12 screen frames reachable, no live
controls interactive, no secrets/env paths in the DOM, and deterministic output
suitable for the later 0167 Antigravity browser QA pass.
