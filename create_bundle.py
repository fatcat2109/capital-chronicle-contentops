import os
from pathlib import Path
import shutil

repo_dir = Path(r"A:\Capital Chronicle\tools\cc-live-contentops")
docs_dir = repo_dir / "docs"
bundle_dir = repo_dir / "project_sources_bundle_AFTER_0169"

docs_dir.mkdir(exist_ok=True)
bundle_dir.mkdir(exist_ok=True)

# File contents definition
files = {}

files["CURRENT_STATE_SUMMARY_AFTER_0169.md"] = """# Current State Summary (After 0169)

## Repo Path and Baseline
- Repo path: A:\\Capital Chronicle\\tools\\cc-live-contentops
- Branch: master
- Latest accepted baseline: 444ef2c

## Browser QA 0169 Status
- 0169 browser QA classification: PASS_WITH_MINOR_EVIDENCE_GAP
- The 0169 task was evidence-only; no code was committed.

## Task Chain
Institutional UI/QA task chain 0157–0169 has been completed.

## Hard Boundaries
- No live posting/scheduler/API/env.
- Kill switch is active.
- Browser/Antigravity was run only for static shell QA without network or credentials.

## Caveats
- Stale global header metadata is a known caveat from the browser QA pass.

## Next Task
- Recommended next task: TASK_CONTENTOPS_0170_BROWSER_QA_EVIDENCE_PACKET_AND_GLOBAL_HEADER_METADATA_RECONCILIATION_V0
- A project sources refresh should not imply 0170 is complete.
"""

files["PROJECT_SOURCE_EXPORT_AFTER_0169.md"] = """# Capital Chronicle ContentOps — Project Source Export (After 0169)

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
- Repo path: A:\\Capital Chronicle\\tools\\cc-live-contentops
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
"""

files["NEW_CHAT_CONTINUATION_AFTER_0169.md"] = """# New Chat Continuation Prompt (After 0169)

Paste the block below into a new ChatGPT Project chat after uploading the AFTER_0169 Project Sources bundle.

---

You are the ChatGPT planner/auditor for Capital Chronicle ContentOps.

Use the uploaded Project Sources as authority. Treat repo files/evidence as authority. Do not rely on prior chat history.

Accepted baseline:
- Repo path: A:\\Capital Chronicle\\tools\\cc-live-contentops
- Branch: master
- Accepted HEAD: 444ef2c
- Accepted through: TASK_CONTENTOPS_0169 (PASS_WITH_MINOR_EVIDENCE_GAP).

Current next task:
- TASK_CONTENTOPS_0170_BROWSER_QA_EVIDENCE_PACKET_AND_GLOBAL_HEADER_METADATA_RECONCILIATION_V0

Operating rules:
- Preserve all hard boundaries (no live API, no env read, active kill switch).
- Do not start Project Sources refresh again.
- Do not run browser/Antigravity unless explicitly scoped.

When the operator asks to continue:
1. If the operator pastes a Cline FINAL EVIDENCE PACKET, audit it against the accepted baseline and safety boundaries first.
2. Otherwise, produce the next Cline worker prompt (TASK_CONTENTOPS_0170_BROWSER_QA_EVIDENCE_PACKET_AND_GLOBAL_HEADER_METADATA_RECONCILIATION_V0), keeping it local-only and fail-closed.
3. Always remind the operator that credential values remain local only and must never be pasted into ChatGPT or Cline.

---
"""

files["UPLOAD_BUNDLE_MANIFEST_AFTER_0169.md"] = """# Upload Bundle Manifest (After 0169)

## Purpose
This bundle refreshes ChatGPT Project Sources with the current code and operational state following the institutional shell browser QA (0169).

## Mandatory Docs
- CURRENT_STATE_SUMMARY_AFTER_0169.md
- PROJECT_SOURCE_EXPORT_AFTER_0169.md
- NEW_CHAT_CONTINUATION_AFTER_0169.md
- UPLOAD_BUNDLE_MANIFEST_AFTER_0169.md
- PROJECT_SOURCES_REPLACEMENT_INDEX_AFTER_0169.md
- PROJECT_SOURCES_DELETE_REPLACE_GUIDE_AFTER_0169.md
- IDE_CLI_QUICKSTART_AFTER_0169.md
- BUNDLE_README_AFTER_0169.md
- BUNDLE_FILE_LIST_AFTER_0169.txt
- INSTITUTIONAL_BROWSER_QA_EVIDENCE_AFTER_0169.md

## Optional Schemas
(Listed in BUNDLE_FILE_LIST_AFTER_0169.txt based on actual availability during bundle generation.)

## Upload Order
1. BUNDLE_README_AFTER_0169.md
2. UPLOAD_BUNDLE_MANIFEST_AFTER_0169.md
3. PROJECT_SOURCES_REPLACEMENT_INDEX_AFTER_0169.md
4. PROJECT_SOURCES_DELETE_REPLACE_GUIDE_AFTER_0169.md
5. PROJECT_SOURCE_EXPORT_AFTER_0169.md
6. CURRENT_STATE_SUMMARY_AFTER_0169.md
7. IDE_CLI_QUICKSTART_AFTER_0169.md
8. INSTITUTIONAL_BROWSER_QA_EVIDENCE_AFTER_0169.md
9. NEW_CHAT_CONTINUATION_AFTER_0169.md
10. All schemas

## Safety Statements
- No secrets.
- No screenshots/images.
- No Project Sources refresh performed by Cline (operator uploads manually).
"""

files["PROJECT_SOURCES_REPLACEMENT_INDEX_AFTER_0169.md"] = """# Project Sources Replacement Index (After 0169)

## Mandatory Upload Files
- CURRENT_STATE_SUMMARY_AFTER_0169.md
- PROJECT_SOURCE_EXPORT_AFTER_0169.md
- NEW_CHAT_CONTINUATION_AFTER_0169.md
- UPLOAD_BUNDLE_MANIFEST_AFTER_0169.md
- PROJECT_SOURCES_REPLACEMENT_INDEX_AFTER_0169.md
- PROJECT_SOURCES_DELETE_REPLACE_GUIDE_AFTER_0169.md
- IDE_CLI_QUICKSTART_AFTER_0169.md
- BUNDLE_README_AFTER_0169.md
- BUNDLE_FILE_LIST_AFTER_0169.txt
- INSTITUTIONAL_BROWSER_QA_EVIDENCE_AFTER_0169.md

## Optional Upload Schemas
Any `.schema.json` files included in the `project_sources_bundle_AFTER_0169` directory.

## Stale Old Project Sources to Delete After Upload
- Older AFTER_0153 operational docs.
- Older AFTER_0137 or earlier operational docs.
- Earlier CURRENT_STATE / PROJECT_SOURCE_EXPORT / NEW_CHAT_CONTINUATION docs.

## Durable Context Files to Keep
- Institutional UI/UX master plan PDF.
- Final master plan docs if still useful.
- Grounded-news context if still useful.

## Files Not To Upload
- .env
- credentials
- screenshots/images from browser QA
- Antigravity/Gemini local artifacts
- raw vendor data
- caches
- raw platform responses
- internal agent logs
"""

files["PROJECT_SOURCES_DELETE_REPLACE_GUIDE_AFTER_0169.md"] = """# Project Sources Delete/Replace Guide (After 0169)

## Operator Instructions
1. Upload new AFTER_0169 docs first from the `project_sources_bundle_AFTER_0169` folder.
2. Verify new docs are visible in ChatGPT Project Sources.
3. Delete/retire older AFTER_0153 operational bundle docs.
4. Keep durable strategy docs (PDFs/Master Plans) only if not contradictory.
5. Do not upload screenshots, secrets, or .env files.
6. Do not delete unknown files blindly if unsure.
"""

files["IDE_CLI_QUICKSTART_AFTER_0169.md"] = """# IDE CLI Quickstart (After 0169)

- Repo path: A:\\Capital Chronicle\\tools\\cc-live-contentops
- Expected baseline: 444ef2c

## Safe Validation Commands
- `python -m pytest -q`
- `python -m live_contentops.cli status`
- `python -m live_contentops.cli pre-alpha-institutional-pre-antigravity-static-qa-hardening-summary`
- `node --check ui/institutional_shell/app.js`
- `git status --short`
- `git diff --check`

## Hard Boundaries
- No env/API/browser unless explicitly scoped.
- No `git add .`
- No Project Sources refresh from Cline directly (operator manual upload).

## Bundle Verification
Check `BUNDLE_FILE_LIST_AFTER_0169.txt` matches actual contents in `project_sources_bundle_AFTER_0169/`.
"""

files["BUNDLE_README_AFTER_0169.md"] = """# Bundle Readme (After 0169)

## What is this bundle?
This is a documentation bundle reflecting the state of the Capital Chronicle ContentOps repo after Task 0169.

## Why it exists?
To provide a clean, secret-free Project Sources upload for ChatGPT without relying on chat history.

## What to upload?
Upload all files in the `project_sources_bundle_AFTER_0169` folder.

## What not to upload?
Do not upload screenshots, .env, raw platform responses, or caches.

## Status Note
- 0169 browser QA is accepted but has a minor evidence gap.
- 0170 metadata reconciliation remains the next recommended task.
"""

files["INSTITUTIONAL_BROWSER_QA_EVIDENCE_AFTER_0169.md"] = """# Institutional Browser QA Evidence (After 0169)

- Task Label: TASK_CONTENTOPS_0169_OPERATOR_APPROVED_ANTIGRAVITY_BROWSER_QA_LOCAL_STATIC_SHELL_V0
- Classification: PASS_WITH_MINOR_EVIDENCE_GAP

## Safety Summary
- Browser opened: yes
- Local file URL opened: yes (file:///A:/Capital%20Chronicle/tools/cc-live-contentops/ui/institutional_shell/index.html)
- External URL opened: no
- Network used/observed: no
- Screenshots captured: worker reported no
- Files created/changed: no
- Active publish/schedule/export/API/evidence mutation control count: 0
- Secret/raw data visible: no
- Active forbidden controls visible: no

## Screen Inspection Summary
All 12 institutional shell screens were successfully reached and visually inspected.
Each screen had a visible title/header and visible safety/status labels.
Disabled controls were verified safe.

## Minor Evidence Gaps
- Browser QA packet omitted repo path/branch/HEAD/git status/terminal validation fields.
- Browser QA packet did not explicitly state Antigravity used yes/no.
- Visual images supplied by operator did not clearly prove Settings / Safety Policy selected, though the worker packet reported it inspected.
- Clarification: no screenshot/export files were generated by repo/worker natively.

## Screenshot Review Caveat
Browser screenshots showed a UI/data-consistency issue:
- Global header displayed stale accepted HEAD 15b87ff and stale current gate.
- This is an operator-confusing issue, but not a live/safety failure.

## Next Task
- Recommended next task: TASK_CONTENTOPS_0170_BROWSER_QA_EVIDENCE_PACKET_AND_GLOBAL_HEADER_METADATA_RECONCILIATION_V0
- No screenshots/images included in this bundle.
"""

# Schemas
schemas_dir = repo_dir / "schemas"
optional_schemas = [
    "telegram_credential_setup_operator_guide_packet.schema.json",
    "telegram_live_pilot_gate_packet.schema.json",
    "redacted_publish_audit_log_packet.schema.json",
    "publish_adapter_credential_secret_policy_packet.schema.json",
    "dry_run_publish_batch_manifest_packet.schema.json",
    "publish_automation_readiness_packet.schema.json",
    "platform_capability_registry_packet.schema.json"
]

copied_schemas = []
missing_schemas = []

# Gather schemas
if schemas_dir.exists():
    for f in schemas_dir.glob("institutional_*packet.schema.json"):
        optional_schemas.append(f.name)
        
for s in optional_schemas:
    src = schemas_dir / s
    if src.exists():
        shutil.copy(src, bundle_dir / s)
        copied_schemas.append(s)
    else:
        missing_schemas.append(s)

file_list = []
for k, v in files.items():
    (docs_dir / k).write_text(v, encoding="utf-8")
    shutil.copy(docs_dir / k, bundle_dir / k)
    file_list.append(k)

for s in copied_schemas:
    file_list.append(s)

file_list.sort()
file_list_content = "\\n".join(file_list)
(docs_dir / "BUNDLE_FILE_LIST_AFTER_0169.txt").write_text(file_list_content, encoding="utf-8")
shutil.copy(docs_dir / "BUNDLE_FILE_LIST_AFTER_0169.txt", bundle_dir / "BUNDLE_FILE_LIST_AFTER_0169.txt")

# Append missing optional schemas to manifest optionally, but instruction says "record absent optional files" in the manifest.
manifest = files["UPLOAD_BUNDLE_MANIFEST_AFTER_0169.md"]
manifest += "\\n\\n## Copied Schemas\\n" + "\\n".join(f"- {s}" for s in copied_schemas)
manifest += "\\n\\n## Absent Optional Schemas\\n" + "\\n".join(f"- {s}" for s in missing_schemas)
(docs_dir / "UPLOAD_BUNDLE_MANIFEST_AFTER_0169.md").write_text(manifest, encoding="utf-8")
shutil.copy(docs_dir / "UPLOAD_BUNDLE_MANIFEST_AFTER_0169.md", bundle_dir / "UPLOAD_BUNDLE_MANIFEST_AFTER_0169.md")

print("Created bundle successfully.")
