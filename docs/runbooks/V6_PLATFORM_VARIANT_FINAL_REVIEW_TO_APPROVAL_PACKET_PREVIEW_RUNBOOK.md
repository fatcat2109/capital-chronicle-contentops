# V6 Platform Variant Final Review to Approval Packet Preview Runbook

This is a local/manual-only runbook for the platform variant final review and approval packet preview workflow (`TASK_CONTENTOPS_V6_PLATFORM_VARIANT_FINAL_REVIEW_TO_APPROVAL_PACKET_PREVIEW_HEAVY_BATCH_V0`).

## Purpose
This workflow converts the accepted platform variant preview package into an approval-packet preview for operator final signoff.
* The generated approval packet contains deterministic preview records and hash-bound approval-readiness records.
* **No real approvals**: `actual_operator_approval_recorded` remains `false`. No real approval ledger entries are created.
* **No outbox entries**: `outbox_entry_created` and `dispatch_outbox_ready` remain `false`.
* **Lock states**: All live dispatching, auto-publishing, scraper runs, credentials use, and provider API calls remain locked.
* Manual, future, or deferred platform states (such as deferred LinkedIn/Instagram/YouTube/TikTok adapters) are valid states and are not treated as failures.

## Local Files
* Local Builder: `live_contentops/platform_variant_final_review_to_approval_packet_preview_v6.py`
* Codegen script: `live_contentops/platform_variant_approval_packet_preview_v5_adapter_codegen_v6.py`
* Committed JSON Packet: `docs/automation/V6_PLATFORM_VARIANT_FINAL_REVIEW_TO_APPROVAL_PACKET_PREVIEW/platform_variant_final_review_to_approval_packet_preview.json`
* Static TS Adapter: `ui/contentops_v5/src/data/platformVariantApprovalPacketPreviewAdapter.ts`
* Backend Python Tests: `tests/test_platform_variant_final_review_to_approval_packet_preview_v6.py`
* Codegen Python Tests: `tests/test_platform_variant_approval_packet_preview_v5_adapter_codegen_v6.py`
* UI Guardrail Tests: `tests/test_platform_variant_approval_packet_preview_ui_guardrail_v6.py`

## Running Local Verification and Adapter Sync Check
From the repository root, run the status and logic validations:
```bash
python -m pytest tests/test_platform_variant_final_review_to_approval_packet_preview_v6.py tests/test_platform_variant_approval_packet_preview_ui_guardrail_v6.py tests/test_platform_variant_approval_packet_preview_v5_adapter_codegen_v6.py
```

Verify adapter code-generation matches the packet content:
```bash
python live_contentops/platform_variant_approval_packet_preview_v5_adapter_codegen_v6.py
```
