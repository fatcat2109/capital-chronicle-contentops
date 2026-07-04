# Capital Chronicle ContentOps — Project Source Export (After 0169)

## Authority Hierarchy
1. Repo evidence (committed code, schemas, fixtures, tests) is the ground truth. Project Sources docs are context.
2. This export and the AFTER_0169 bundle docs are the consolidated authority for future ChatGPT sessions.
3. Operator/ChatGPT task prompts define scope per task.

## North-Star Product Context
Capital Chronicle ContentOps is an institutional-grade, control-first orchestration sidecar for content execution.

## Hard Boundaries
- No financial advice; no buy/sell/hold; no signal-service framing.
- No live posting/scheduling/API calls; no network; no env reads unless explicitly scoped.
- Kill switch is active.

## Repo Path and Accepted Baseline
- Repo path: A:\Capital Chronicle\tools\cc-live-contentops
- Branch: master
- Accepted code baseline: 444ef2c (after 0168)
- Accepted through: 0169 (evidence-only browser QA).

## Accepted Task Summaries 0157–0169
- 0157: institutional UI/UX rebuild master plan.
- 0158: institutional design system / visual contract.
- 0159: institutional UI view-model contract V2.
- 0160: static local institutional shell prototype.
- 0161: Command Center screen.
- 0162: Content Studio screen.
- 0163: Publish Readiness Tower screen.
- 0164: Evidence Vault + Audit Timeline screen.
- 0165: Content Calendar + Workflow Board screen.
- 0166: Visual Export + Screenshot-Safe Mode screen.
- 0167: pre-Antigravity static QA hardening.
- 0168: Antigravity/browser QA strategy and manual runbook.
- 0169: evidence-only Antigravity browser QA (PASS_WITH_MINOR_EVIDENCE_GAP).

## 0169 Browser QA Evidence Summary
All 12 screens rendered. Safe controls inactive. No secrets. No network used. No screenshots captured by worker.

## Known Caveats
- Stale global header metadata (shows old HEAD/gates instead of current).

## Next Task Recommendation
TASK_CONTENTOPS_0170_BROWSER_QA_EVIDENCE_PACKET_AND_GLOBAL_HEADER_METADATA_RECONCILIATION_V0

## Cline Prompt Style Rules
1. Read .clinerules if present before edits.
2. If native tools fail once with missing content, bad diff, empty payload, schema error, or similar, switch to terminal Python pathlib or PowerShell.
3. Large files, generated markdown bundles, repeated structures, and file lists should use terminal Python pathlib by default.
4. Verify created/changed files by read-back.
5. Never use git add .
6. Stage only explicit files.
7. Do not clean unknown/operator files.

## Evidence Packet Requirements
Return only a FINAL EVIDENCE PACKET with task label, PASS/BLOCKED/FAIL, baseline details, files inspected/created, validation summaries, and explicitly staged files. No scratch pad text.

## Forbidden Scopes
- Do not modify UI runtime files in documentation tasks.
- Do not run browser/Antigravity/capture screenshots unless explicitly requested.
- Do not publish/schedule/scrape/upload/download.

## Rules for Future Browser/Antigravity
- Antigravity requires separate explicit operator GO.
- Must not read env/credentials or call platform/API/network.
- Must only inspect local static file rendering.
