# V6 Canonical Draft Final Review and Platform Variant Preview Runbook

This is a local/manual-only runbook for the canonical draft final review and platform variant preview workflow (`TASK_CONTENTOPS_V6_CANONICAL_DRAFT_FINAL_REVIEW_TO_PLATFORM_VARIANT_PREVIEW_HEAVY_BATCH_V0`).

## Purpose
This workflow converts the deterministic local canonical draft preview into a final-review packet plus platform-variant preview packet set.
* All platform variants are **preview-only and non-dispatchable**.
* All previews carry `final_article_approved = false` indicating that final operator approval is required before approval of copy.
* Previews contain **no financial advice or trading signals** (no buy/sell/hold, price target, position sizing, etc.).
* No live dispatching/publishing, webhook dropping, or scheduler triggers are enabled.
* Deferrals of platforms are manual state indicators and are not treated as failures.

## Local Files
* Local Builder: `live_contentops/canonical_draft_final_review_to_platform_variant_preview_v6.py`
* Codegen script: `live_contentops/canonical_draft_final_review_variant_preview_v5_adapter_codegen_v6.py`
* Committed JSON Packet: `docs/automation/V6_CANONICAL_DRAFT_FINAL_REVIEW_TO_PLATFORM_VARIANT_PREVIEW/canonical_draft_final_review_to_platform_variant_preview_packet.json`
* Static TS Adapter: `ui/contentops_v5/src/data/canonicalDraftFinalReviewVariantPreviewAdapter.ts`
* Backend Python Tests: `tests/test_canonical_draft_final_review_to_platform_variant_preview_v6.py`
* Codegen Python Tests: `tests/test_canonical_draft_final_review_variant_preview_v5_adapter_codegen_v6.py`
* UI Guardrail Tests: `tests/test_canonical_draft_final_review_variant_preview_ui_guardrail_v6.py`

## Running Local Verification and Adapter Sync Check
From the repository root, run the status and logic validations:
```bash
python -m pytest tests/test_canonical_draft_final_review_to_platform_variant_preview_v6.py tests/test_canonical_draft_final_review_variant_preview_ui_guardrail_v6.py tests/test_canonical_draft_final_review_variant_preview_v5_adapter_codegen_v6.py
```

Verify adapter code-generation matches the packet content:
```bash
python live_contentops/canonical_draft_final_review_variant_preview_v5_adapter_codegen_v6.py
```
