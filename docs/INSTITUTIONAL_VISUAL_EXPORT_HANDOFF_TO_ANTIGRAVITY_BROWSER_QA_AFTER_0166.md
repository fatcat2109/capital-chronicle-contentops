# Institutional Visual Export — Handoff To Antigravity Browser QA (After 0166)

Task label: TASK_CONTENTOPS_0166_INSTITUTIONAL_VISUAL_EXPORT_AND_SCREENSHOT_SAFE_MODE_SCREEN_V0
Repo: A:\Capital Chronicle\tools\cc-live-contentops
Branch: master
Authority: governed by `docs/INSTITUTIONAL_VISUAL_EXPORT_AND_SCREENSHOT_SAFE_MODE_SCREEN_AFTER_0166.md`
and `docs/ANTIGRAVITY_BROWSER_QA_STRATEGY_AFTER_0157.md`.

Contract/spec only. This doc defines how task 0167 (Antigravity Browser QA) builds on
the now-complete static institutional shell. No active backend, no network, no env, no
credentials, and no Antigravity run are introduced here. Antigravity remains future-only
and requires a separate explicit operator/ChatGPT GO.

## What 0167 Receives

- The complete static shell under `ui/institutional_shell/` with all screens:
  Command Center (0161), Content Studio (0162), Publish Readiness Tower (0163),
  Evidence Vault (0164), Content Calendar + Workflow Board (0165), Visual Export +
  Screenshot-Safe Mode (0166).
- Screen packet schemas + validators + CLI summaries for each screen.
- The screenshot-safe/redaction rules from 0158 and the visual export contract from 0166.

## What 0167 May Do (only after explicit GO)

- Open the static shell in a browser via Antigravity.
- Click through navigation, capture screenshots, record a walkthrough.
- Report UI bugs, layout issues, and visual regressions.
- Confirm safety banners, redaction, and absence of live controls.

## What 0167 Must Not Do

- Must not design architecture or broaden scope.
- Must not call platform/provider/Telegram/news/search/market APIs.
- Must not inspect secrets, env values, or env paths.
- Must not enable posting/scheduling/scraping/live adapter.
- Must not modify active frontend code (Antigravity is weaker than Cline for building).
- Must not run without an explicit operator/ChatGPT GO.

## Browser QA Evidence Requirements For 0167

- Screenshot list (screen-by-screen).
- Navigation coverage across all 12 screens.
- Visual bug list.
- Safety banner confirmation per screen.
- Confirmation of no live/active controls (publish/connect/API/schedule/send/export).
- Confirmation that no secrets, env paths, request URLs, or raw platform responses
  appear in any captured screenshot.

## Binding Contract For 0167

- Antigravity prompt must be narrow, screen-by-screen, and expected-state based.
- Browser QA must remain screenshot-safe: redaction verified before any capture.
- After Antigravity QA, 0168 (Cline polish pass) fixes visual issues based on the
  Antigravity evidence; Cline, not Antigravity, performs the code changes.
