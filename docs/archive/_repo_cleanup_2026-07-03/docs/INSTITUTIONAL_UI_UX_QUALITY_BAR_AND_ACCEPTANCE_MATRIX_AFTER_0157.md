# Institutional UI/UX Quality Bar and Acceptance Matrix (After 0157)

Task label: TASK_CONTENTOPS_0157_INSTITUTIONAL_UI_UX_FRONTEND_REBUILD_MASTER_PLAN_V0
Repo: A:\Capital Chronicle\tools\cc-live-contentops
Branch: master
Authority: governed by
`docs/INSTITUTIONAL_UI_UX_FRONTEND_REBUILD_MASTER_PLAN_AFTER_0157.md`.

This is the testable quality bar for every institutional UI task (0158–0168).
Each row maps a UX principle to the required visible UI behavior, the required
validation/test, the blocked failure mode (what fail-closed looks like), and the
evidence required. Planning-only: no active front-end code is created in 0157.

## Acceptance Matrix

| # | UX principle | Required visible UI behavior | Required validation/test | Blocked failure mode | Evidence required |
| --- | --- | --- | --- | --- | --- |
| 1 | Global safety visible fast | Global safety status (PASS/DEGRADED/BLOCKED + LIVE_DISABLED + kill switch) renders on first paint, readable within 10 seconds | First-paint assertion that safety header nodes exist before any screen content | If safety state cannot be derived from local fixtures, render BLOCKED with reason; never blank | Screenshot of first paint; test name + result |
| 2 | Every blocked state explains why | Each BLOCKED item shows a plain-language reason | Test asserts every blocked item has a non-empty reason field rendered | Item with no reason fails closed (treated as BLOCKED:unknown_reason) | Test result; sample blocked rows |
| 3 | Evidence-first drafts | Every draft shows source + evidence + limitation context before polished copy | DOM-order test: evidence block precedes copy block | Draft missing source/limitation renders REVIEW_REQUIRED + reason | Test result; Draft Inspector screenshot |
| 4 | Platform gates show live-disabled | Every platform gate shows LIVE_DISABLED explicitly | Test asserts LIVE_DISABLED token present on each platform row | Platform without explicit live flag renders LIVE_DISABLED by default | Test result; readiness screenshot |
| 5 | Credential state redacted | Every credential state renders SECRET_REDACTED (no value/snippet/length/hash) | Security-scan test over assets/fixtures for token/chat-id/secret patterns | Any detected value/snippet/length/hash fails the build | Scan command + result; gate screenshot |
| 6 | Future live features visually gated | Live/publish/schedule/connect controls render disabled + explained, never interactive | Static-asset test: no enabled publish/schedule/connect/OAuth controls | Any interactive live control fails closed | Test result; gated-control screenshot |
| 7 | Missing/degraded/proxy visible | Missing/DEGRADED/PROXY_ONLY/STALE/UNKNOWN always shown with reason | Test asserts these tokens never collapse to PASS | A non-PASS state rendered as PASS fails closed | Test result; Evidence Vault screenshot |
| 8 | No signal-service framing | No buy/sell/hold, no P&L, no guaranteed call, no alpha-signal language | unsafe-language scan test over assets/fixtures | Any actionable trading term fails closed | Scan result; copy review |
| 9 | No auto public-posting implication | No UI element implies automatic public posting | Test asserts no one-button-publish-all / auto-post affordance | Any such affordance fails closed | Test result; review |
| 10 | Screenshot-safe mode | Safe mode shows no secrets, no env paths, and asserts no false readiness | Test asserts safe mode hides redacted detail and never upgrades non-PASS to PASS | Safe mode revealing a secret or inventing PASS fails closed | Test result; safe-mode screenshot |
| 11 | Antigravity walkthrough readiness | UI is deterministic, local, and openable from file:// for a screen-by-screen browser QA | 0167 readiness checklist: all screens reachable from fixtures | If UI is not locally testable, 0167 is BLOCKED | 0167 QA evidence (screenshots, coverage, bugs) |

## Notes On Enforcement

- Rows 1–10 are enforced by deterministic Cline tests in tasks 0158–0166 and 0168.
- Row 11 is the gate for task 0167 (Antigravity). Antigravity QA does not replace
  the deterministic tests; it adds browser-level visual evidence on top.
- Color is never the only signal: every status token renders with a text label and
  an icon, satisfying basic accessibility (color-blind safe).
- Green/red are operational PASS/BLOCKED only — never gain/loss or buy/sell.
- Every task's final evidence packet must include the scan command + classified
  results and confirm all live/credential/api/scheduler/scraping flags are off.
