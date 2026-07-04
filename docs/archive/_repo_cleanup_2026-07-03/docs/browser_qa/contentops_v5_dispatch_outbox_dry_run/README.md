# ContentOps V5 Dispatch Outbox Dry Run UI QA

This folder contains the committed local browser QA visual screenshots for `TASK_CONTENTOPS_V6_APPROVAL_PACKET_PREVIEW_TO_DISPATCH_OUTBOX_DRY_RUN_HEAVY_BATCH_V0`.

## Committed Screenshots
* [approval_queue_dispatch_outbox_dry_run.png](approval_queue_dispatch_outbox_dry_run.png) - Shows the primary Approval Queue view displaying the V6 dispatch outbox dry-run panel card with detailed safety counters and entries.
* [platform_preview_dispatch_outbox_dry_run.png](platform_preview_dispatch_outbox_dry_run.png) - Shows the Platform Preview page displaying all 10 outbox dry-run rows.
* [manual_export_dispatch_outbox_dry_run.png](manual_export_dispatch_outbox_dry_run.png) - Shows the card integrated into the V5 Manual Export view.
* [evidence_vault_dispatch_outbox_dry_run.png](evidence_vault_dispatch_outbox_dry_run.png) - Shows the card in the dark mode Evidence Vault view.

## Verification Details
* **Canonical UI Target**: Only `ui/contentops_v5/` was targeted and verified. No legacy V4 pages or standalone custom pages are used.
* **Local QA URL**: Verified locally at `http://127.0.0.1:5173/`.
* **Dispatch Outbox Scope**:
  * The dispatch outbox is a dry-run preview only. No executable outbox, real approval ledger entry, network request, webhook call, provider call, platform API call, or live action was created or performed.
  * All card elements show status indicators: `dispatch_outbox_dry_run_status = dispatch_outbox_dry_run_created_for_operator_review` and safety counters remain zero.
  * Screenshots are visual QA evidence of display visibility and alignment, not live-readiness evidence.
* **Verification Constraints**: No LLM/provider/API/network/env/credential/browser-session/public URL/live action occurred except launching the local Vite development server for browser QA screenshots.
