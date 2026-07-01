# ContentOps V5 Local Canonical Draft Preview and Review UI QA

This folder contains the committed local browser QA visual screenshots for `TASK_CONTENTOPS_V6_LOCAL_CANONICAL_DRAFT_PREVIEW_AND_REVIEW_HEAVY_BATCH_V0`.

## Committed Screenshots
* [manual_export_local_canonical_draft_preview_review.png](manual_export_local_canonical_draft_preview_review.png) - Shows the card rendered in the V5 Manual Export view.
* [approval_queue_local_canonical_draft_preview_review.png](approval_queue_local_canonical_draft_preview_review.png) - Shows the card integrated into the V5 Approval & Dispatch view.
* [evidence_vault_local_canonical_draft_preview_review.png](evidence_vault_local_canonical_draft_preview_review.png) - Shows the dark mode card inside the Evidence Vault view.

## Verification Details
* **Canonical UI Target**: Only `ui/contentops_v5/` was targeted and verified. No legacy V4 pages or standalone custom pages are used.
* **Local QA URL**: Verified locally at `http://127.0.0.1:5173/`.
* **Draft Preview & Review Scope**:
  * The cards state `draft_preview_status=local_draft_preview_created_for_review` and `draft_review_status=pending_operator_review`.
  * The draft is generated using `deterministic_template_no_llm`.
  * Gates: `canonical_draft_created=true` and `article_body_created=true`.
  * Approval state: `final_article_approved=false` indicating that final operator approval is required before the draft is considered approved.
  * Readiness locks: `separate_final_approval_task_required=true`, `separate_platform_variant_task_required=true`, `separate_publish_authorization_required=true`, `public_url_verification_performed=false`.
  * Live status is locked: `ready_for_llm_drafting=false`, `ready_for_provider_drafting=false`, `ready_for_auto_publish=false`, `ready_for_dispatch=false`.
  * Screenshots are visual QA evidence of display visibility and alignment, not live-readiness evidence.
* **Verification Constraints**: No LLM/provider/API/network/env/credential/browser-session/public URL/live action occurred.
