# ContentOps V5 Next Article Brief Source-Pack and Review UI QA

This folder contains the committed local browser QA visual screenshots for `TASK_CONTENTOPS_V6_NEXT_ARTICLE_BRIEF_SOURCE_PACK_AND_REVIEW_WORKFLOW_V0`.

## Committed Screenshots
* [manual_export_source_pack_review_surface.png](manual_export_source_pack_review_surface.png) - Shows the Next Article Brief Source-Pack and Review card on the V5 Manual Export view.
* [approval_queue_source_pack_review_surface.png](approval_queue_source_pack_review_surface.png) - Shows the card integrated into the V5 Approval & Dispatch view.
* [evidence_vault_source_pack_review_surface.png](evidence_vault_source_pack_review_surface.png) - Shows the packet card rendered in the forensic dark theme of the V5 Evidence Vault view.

## Verification Details
* **Canonical UI Target**: Only `ui/contentops_v5/` was targeted and verified. No legacy V4 pages or standalone custom pages are used.
* **Surface Visibility**: The source-pack checklist and review status cards are clearly visible on all three flagship dashboard views.
* **Workflow Constraints**:
  * Source pack status remains `source_pack_required_pending_operator_collection`.
  * Operator review status is `pending_operator_review`.
  * The brief candidate is **not LLM-ready**, **not canonical draft ready**, and **not auto-publish/dispatch ready**.
  * No **LLM provider calls, network actions, API integrations, credential/env lookups, or browser session modifications** are performed.
