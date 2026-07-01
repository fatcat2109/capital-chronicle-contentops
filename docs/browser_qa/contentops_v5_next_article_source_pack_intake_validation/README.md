# ContentOps V5 Next Article Source-Pack Intake and Validation UI QA

This folder contains the committed local browser QA visual screenshots for `TASK_CONTENTOPS_V6_NEXT_ARTICLE_SOURCE_PACK_INTAKE_AND_VALIDATION_V0`.

## Committed Screenshots
* [manual_export_source_pack_intake_validation_surface.png](manual_export_source_pack_intake_validation_surface.png) - Shows the Next Article Source-Pack Intake and Validation card on the V5 Manual Export view.
* [approval_queue_source_pack_intake_validation_surface.png](approval_queue_source_pack_intake_validation_surface.png) - Shows the card integrated into the V5 Approval & Dispatch view.
* [evidence_vault_source_pack_intake_validation_surface.png](evidence_vault_source_pack_intake_validation_surface.png) - Shows the packet card rendered in the forensic dark theme of the V5 Evidence Vault view.

## Verification Details
* **Canonical UI Target**: Only `ui/contentops_v5/` was targeted and verified. No legacy V4 pages or standalone custom pages are used.
* **Surface Visibility**: The source-pack intake validation status and coverage info is clearly visible on all three flagship dashboard views.
* **Verification Constraints**:
  * URLs are stored as **text/hash only and are not opened, fetched, or verified**.
  * Complete/pending-review state **does not claim LLM/canonical draft readiness**.
  * No **LLM provider calls, network actions, API integrations, credential/env lookups, or browser session modifications** are performed.
