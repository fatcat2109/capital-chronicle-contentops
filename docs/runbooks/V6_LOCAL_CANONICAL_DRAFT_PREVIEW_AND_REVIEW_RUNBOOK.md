# V6 Local Canonical Draft Preview and Review Runbook

This is a local/manual-only runbook for the local canonical draft preview and operator review workflow (`TASK_CONTENTOPS_V6_LOCAL_CANONICAL_DRAFT_PREVIEW_AND_REVIEW_HEAVY_BATCH_V0`).

## Purpose
This workflow creates a deterministic local canonical draft preview packet from the authorized draft readiness record.
* The preview is **local and deterministic template-based only**.
* The preview is **NOT LLM/provider generated**.
* The preview is **NOT a final approved article** (final_article_approved=false).
* The preview is **NOT a platform variant** and contains no platform copy.
* The preview is **NOT publishable or dispatchable**.
* Source-pack URLs are metadata only and **are not fetched or network verified**.
* Operator review is required before any final canonical article approval.

## Local Files
* Local Builder: `live_contentops/local_canonical_draft_preview_and_review_v6.py`
* Codegen script: `live_contentops/local_canonical_draft_preview_v5_adapter_codegen_v6.py`
* Committed JSON Packet: `docs/automation/V6_LOCAL_CANONICAL_DRAFT_PREVIEW_AND_REVIEW/local_canonical_draft_preview_and_review_packet.json`
* Static TS Adapter: `ui/contentops_v5/src/data/localCanonicalDraftPreviewReviewAdapter.ts`
* Backend Python Tests: `tests/test_local_canonical_draft_preview_and_review_v6.py`
* Codegen Python Tests: `tests/test_local_canonical_draft_preview_v5_adapter_codegen_v6.py`
* UI Guardrail Tests: `tests/test_local_canonical_draft_preview_review_ui_guardrail_v6.py`

## Running Local Verification and Adapter Sync Check
From the repository root, run the status and logic validations:
```bash
python -m pytest tests/test_local_canonical_draft_preview_and_review_v6.py tests/test_local_canonical_draft_preview_review_ui_guardrail_v6.py tests/test_local_canonical_draft_preview_v5_adapter_codegen_v6.py
```

Verify adapter code-generation matches the packet content:
```bash
python live_contentops/local_canonical_draft_preview_v5_adapter_codegen_v6.py
```
