# TASK_CONTENTOPS_0174AB — Browser QA Recheck Manifest

- Mode: Antigravity Browser QA Mode (read-only)
- Repo: A:\Capital Chronicle\tools\cc-live-contentops
- Branch: master
- Target HEAD: 1e129539069ba232cf8ef7c5ff23447be6e8609a
- Confirmed HEAD: 1e129539069ba232cf8ef7c5ff23447be6e8609a (tracked status clean)
- Local URL: http://127.0.0.1:8731/ui/institutional_operator_cockpit_v4/index.html
- Server: python -m http.server 8731 --bind 127.0.0.1 (loopback only; terminated after run)
- Screenshots: ./screenshots/shot_001.png … shot_077.png (matrix + intermediate states)

## Scope
Read-only visual QA of the committed 0174AB brand-language + state-grammar patch
against the root Evidence Vault reference and the institutional design intent.
No source edits, no commits, no Project Sources refresh, no external URLs, no
runtime/platform/API/credential behavior. No final visual PASS claimed by worker.

## Screen matrix requested
1. Command Center 1366x768
2. Command Center 1440x900
3. Command Center 1536x864
4. Command Center 1920x1080
5. Content Studio 1440x900
6. Publish Readiness Tower 1440x900
7. Evidence Vault 1440x900
8. Calendar / Workflow 1440x900
9. Visual Export / Screenshot-Safe 1440x900
10. Settings / Safety Policy 1440x900

## Verified loopback-only network posture
Server access log shows only 127.0.0.1 GETs for index.html, styles.css,
view_model.js, cockpit.js (plus a benign favicon 404). No remote fetches.

## Worker observations (corroborated against committed source)
- Current-state copy reflects 0174AB committed at 1f9ed89; next action is a
  Browser QA recheck. No "patch in progress" / "set-at-build" / "Apply the
  0174AB" stale strings (matches view_model.js at HEAD 1e12953).
- Safety rail: red reserved for KILL SWITCH ACTIVE / LIVE DISABLED; other locks
  neutral graphite (matches renderSafetyRail dangerLocks gate in cockpit.js).
- Publish Readiness: gate-summary strip (Live adapter / Scheduler / Posting /
  Credential read / Platform API / Next blocker) renders above the dense matrix
  (matches renderPublishReadiness in cockpit.js).
- Tables de-zebra'd; evidence ids austere neutral, not cyan glow (matches CSS).

## Result recommendation
Advance to ChatGPT visual audit of the archived screenshots. No worker PASS.
