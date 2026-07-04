# ContentOps V5 Dispatch Outbox Operator Handoff & Recovery UI QA

This folder contains the committed local browser QA visual screenshots for `TASK_CONTENTOPS_V6_DISPATCH_OUTBOX_DRY_RUN_TO_OPERATOR_RUNBOOK_AND_RECOVERY_HEAVY_BATCH_V0`.

## Committed Screenshots
* [approval_queue_dispatch_outbox_operator_recovery.png](approval_queue_dispatch_outbox_operator_recovery.png) - Shows the Approval Queue page displaying the panel card with header `V6 dispatch outbox operator runbook & recovery` containing the status value `operator_recovery_status=operator_recovery_runbook_created_for_review`, a list of preflight checklists, rollback conditions, and system limit indicators.
* [platform_preview_dispatch_outbox_operator_recovery.png](platform_preview_dispatch_outbox_operator_recovery.png) - Shows the Platform Preview page containing the panel with header `V6 dispatch outbox operator runbook & recovery (10)` and subheadings `Manual Dispatch Fallback Steps`, `Dry-Run Replay Verification Steps`, `Failure Mode & Recovery Matrix`, and `Platform-Specific Manual Handoff & Recovery Notes`.
* [manual_export_dispatch_outbox_operator_recovery.png](manual_export_dispatch_outbox_operator_recovery.png) - Shows the V5 Manual Export view displaying the panel with heading `V6 dispatch outbox operator runbook & recovery` in the lower layout.
* [evidence_vault_dispatch_outbox_operator_recovery.png](evidence_vault_dispatch_outbox_operator_recovery.png) - Shows the dark mode Evidence Vault view showing the panel with heading `V6 dispatch outbox operator runbook & recovery` containing state key values like `operator_recovery_status: operator_recovery_runbook_created_for_review`.

## Verification Details
* **Canonical UI Target**: Only `ui/contentops_v5/` was targeted and verified. No legacy V4 pages or standalone custom pages are used.
* **Local QA URL**: Verified locally at `http://127.0.0.1:5173/`.
* **Handoff & Recovery Scope**:
  * The operator recovery runbook is local and manual-only. No executable outbox, real approval ledger entry, network request, webhook call, provider call, platform API call, browser session read, credential read, env read, scheduler, retry, or live action was created or performed.
  * Screenshots are visual QA evidence of display visibility and alignment, not live-readiness evidence.
* **Verification Constraints**: No LLM/provider/API/network/env/credential/browser-session/public URL/live action occurred except launching the local Vite development server for browser QA screenshots.
