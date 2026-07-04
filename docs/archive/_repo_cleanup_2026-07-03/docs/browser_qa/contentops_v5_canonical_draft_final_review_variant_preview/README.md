# ContentOps V5 Canonical Draft Final Review and Platform Variant Preview UI QA

This folder contains the committed local browser QA visual screenshots for `TASK_CONTENTOPS_V6_CANONICAL_DRAFT_FINAL_REVIEW_TO_PLATFORM_VARIANT_PREVIEW_HEAVY_BATCH_V0`.

## Committed Screenshots
* [platform_preview_canonical_draft_variant_preview.png](platform_preview_canonical_draft_variant_preview.png) - Shows the Platform Preview page with the compact variant preview card and list of all 10 preview variants.
* [manual_export_canonical_draft_variant_preview.png](manual_export_canonical_draft_variant_preview.png) - Shows the card integrated into the V5 Manual Export view.
* [approval_queue_canonical_draft_variant_preview.png](approval_queue_canonical_draft_variant_preview.png) - Shows the card in the V5 Approval & Dispatch view.
* [evidence_vault_canonical_draft_variant_preview.png](evidence_vault_canonical_draft_variant_preview.png) - Shows the card in the dark mode Evidence Vault view.

## Verification Details
* **Canonical UI Target**: Only `ui/contentops_v5/` was targeted and verified. No legacy V4 pages or standalone custom pages are used.
* **Local QA URL**: Verified locally at `http://127.0.0.1:5173/`.
* **Platform Variant Preview & Final Review Scope**:
  * All platform variants are preview-only and non-dispatchable.
  * All cards state `canonical_draft_final_review_status = ready_for_operator_final_review` and `platform_variant_preview_status = platform_variant_preview_created_for_operator_review`.
  * The copy is generated using local deterministic templates.
  * All readiness locks are explicitly verified: `final_article_approved = false`, `platform_payloads_approved = false`, `ready_for_auto_publish = false`, `ready_for_dispatch = false`, `public_url_verification_performed = false`.
  * Previews contain no financial advice or trade signals.
  * Screenshots are visual QA evidence of display visibility and alignment, not live-readiness evidence.
* **Verification Constraints**: No LLM/provider/API/network/env/credential/browser-session/public URL/live action occurred except launching the local Vite development server for browser QA screenshots.
