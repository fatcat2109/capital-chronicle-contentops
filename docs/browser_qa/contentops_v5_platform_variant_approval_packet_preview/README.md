# ContentOps V5 Platform Variant Approval Packet Preview UI QA

This folder contains the committed local browser QA visual screenshots for `TASK_CONTENTOPS_V6_PLATFORM_VARIANT_FINAL_REVIEW_TO_APPROVAL_PACKET_PREVIEW_HEAVY_BATCH_V0`.

## Committed Screenshots
* [approval_queue_platform_variant_approval_packet_preview.png](approval_queue_platform_variant_approval_packet_preview.png) - Shows the primary Approval Queue view displaying the V6 platform variant approval packet preview panel card, containing detailed locks, statuses, and targets checklist.
* [platform_preview_platform_variant_approval_packet_preview.png](platform_preview_platform_variant_approval_packet_preview.png) - Shows the Platform Preview page containing detailed hash-bound rows of all 10 platform variants.
* [manual_export_platform_variant_approval_packet_preview.png](manual_export_platform_variant_approval_packet_preview.png) - Shows the card integrated into the V5 Manual Export view.
* [evidence_vault_platform_variant_approval_packet_preview.png](evidence_vault_platform_variant_approval_packet_preview.png) - Shows the card in the dark mode Evidence Vault view.

## Verification Details
* **Canonical UI Target**: Only `ui/contentops_v5/` was targeted and verified. No legacy V4 pages or standalone custom pages are used.
* **Local QA URL**: Verified locally at `http://127.0.0.1:5173/`.
* **Platform Variant Approval Scope**:
  * The approval packet is preview-only. No real approval ledger entry or outbox entry was created.
  * All card elements show status indicators: `platform_variant_final_review_status = ready_for_operator_approval_packet_review` and `approval_packet_preview_status = approval_packet_preview_created_for_operator_review`.
  * Previews contain no financial advice or trade signals.
  * Screenshots are visual QA evidence of display visibility and alignment, not live-readiness evidence.
* **Verification Constraints**: No LLM/provider/API/network/env/credential/browser-session/public URL/live action occurred except launching the local Vite development server for browser QA screenshots.
