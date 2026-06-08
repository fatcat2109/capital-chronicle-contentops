# IDE/CLI Document Bundle - After TASK_CONTENTOPS_0074

LOCAL ONLY | ADVISORY ONLY | FIXTURE ONLY | HUMAN REVIEW REQUIRED | NOT PUBLIC POSTABLE
NO PROVIDER CALL | NO SEARCH CALL | NO PLATFORM ACTION

This is the master orientation doc for a future local IDE/CLI worker. It is for
local consumption only. It does not publish, post, or call any external service.

## Repo
A:\Capital Chronicle\tools\cc-live-contentops

## Accepted state
- Accepted starting HEAD for 0074: f9c4d69 (0073 completion)
- Terminal wait-state pointer:
  WAIT_FOR_REAL_CAPITAL_CHRONICLE_ALPHA_ARTIFACTS_OR_OPERATOR_SELECTED_LOCAL_MAINTENANCE
- This 0074 task is a local-maintenance documentation bundle only.

## Project purpose
Local-first ContentOps control-plane sidecar for Capital Chronicle. It is not a
live posting engine. It prepares safe offline editorial/research packets for
later human review. It must never market Capital Chronicle as a Bloomberg
replacement, AI trading bot, signal service, execution engine, or guaranteed
forecast system.

## Built capability stack (complete for now)
- Grounded research / SEO / prompt / citation guardrail.
- Editorial QA / preview / selection.
- Grounded editorial packet export.
- Packet audit / review queue.
- Operator decision capture / review history.
- Packet registry / review ledger.
- Operator dashboard query / handoff.
- Project Sources bundle / export.
- Real-artifact intake contract / readiness gate.
- Artifact-to-packet bridge / synthetic route guard.
- End-to-end fixture-only real-artifact pipeline trace.
- Alpha wait-state operator runbook + final bundle.

## Intentionally disabled capabilities
Provider/LLM API calls; network/search; platform APIs; credentials/env reads;
scheduling; live posting; autonomous replies/DMs; browser automation/scraping;
public-postable synthetic content; real alpha artifact access; Capital Chronicle
core repo reads/writes.

## Hard boundaries
No network. No provider API. No LLM API. No search API. No credentials/env reads.
No platform API. No live posting. No scheduling. No autonomous replies/DMs. No
scraping/browser automation. No public-postable fake content. No synthetic
content generation. No auto-approval. No Capital Chronicle core repo reads/writes.
No cc-contentops repo modifications. Do not touch operator-owned .gitignore. Do
not upload anything. Do not add runtime integration capability.

## Known caveat: .gitignore
.gitignore is modified in the working tree, unstaged, and outside task commit
scope. Do not edit, stage, clean, revert, normalize, or commit it.

## Exact recommended 0073 Project Sources files
- docs/NEW_CHAT_CONTINUATION_AFTER_0073.md
- docs/UPLOAD_BUNDLE_MANIFEST_AFTER_0073.md
- docs/PROJECT_SOURCE_EXPORT_AFTER_0073.md
- docs/CURRENT_STATE_SUMMARY_AFTER_0073.md
- docs/ALPHA_WAIT_STATE_OPERATOR_RUNBOOK_AFTER_0073.md
- docs/TASK_CONTENTOPS_0073_EXTREME_LOCAL_ALPHA_WAIT_STATE_OPERATOR_RUNBOOK_FINAL_BUNDLE_AND_PATH_REPAIR_V0.md

Note: all committed 0072/0073 docs use the underscore convention (AFTER_0073 /
TASK_CONTENTOPS_0073). Ignore any prose using non-underscore variants.

## Read these first (future IDE/CLI worker)
1. docs/IDE_CLI_QUICKSTART_AFTER_0074.md
2. docs/CURRENT_STATE_SUMMARY_AFTER_0073.md
3. docs/ALPHA_WAIT_STATE_OPERATOR_RUNBOOK_AFTER_0073.md
4. docs/IDE_CLI_ALLOWED_MAINTENANCE_TASKS_AFTER_0074.md
5. docs/IDE_CLI_EVIDENCE_PACKET_TEMPLATE_AFTER_0074.md

## Do not touch unless explicitly authorized
- .gitignore (operator-owned drift).
- Any sibling repo (cc-contentops) or the Capital Chronicle core repo.
- The terminal wait-state pointer in live_contentops/status.py.
- Existing guardrail logic in real_artifact_intake.py, artifact_packet_bridge.py,
  packet_audit.py, citation_guardrail.py (do not weaken).

## Evidence packet requirements
Every task must close with the evidence packet from
docs/IDE_CLI_EVIDENCE_PACKET_TEMPLATE_AFTER_0074.md.

## What to do when real alpha artifacts exist
Follow the resume checklist in
docs/ALPHA_WAIT_STATE_OPERATOR_RUNBOOK_AFTER_0073.md: confirm the artifact spec,
approved export location, source IDs, lineage, freshness, limitations, DQR/data
sufficiency/forecast readiness, and operator approval before any intake. Real
intake routes through the existing readiness gate to READY_FOR_LOCAL_REVIEW_ONLY,
never directly to public-ready.

## What not to do while waiting
- Do not generate or post synthetic/demo content publicly.
- Do not enable provider/search/platform calls.
- Do not read credentials or env files.
- Do not treat any fixture as a real approved artifact.
- Do not mutate the Capital Chronicle core repo.
- Do not grant approval/publish/platform authority.
