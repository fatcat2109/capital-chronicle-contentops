# V6 Next Article Draft Authorization and Readiness Runbook

This is a local/manual-only runbook for the next article draft authorization and local readiness workflow (`TASK_CONTENTOPS_V6_NEXT_ARTICLE_SOURCE_PACK_TO_DRAFT_AUTHORIZATION_AND_LOCAL_DRAFT_READINESS_HEAVY_BATCH_V0`).

## Purpose
This workflow records that the operator has authorized drafting based on a completed, locally validated source-pack.
* The authorization is **local and manual-only**.
* The source-pack is complete but **not URL, network, or API verified**.
* This workflow **does not create article body copy or canonical draft files**.
* This workflow **does not call any LLM or provider APIs**.
* This workflow **does not authorize publishing, dispatching, or scheduling content**.
* The next recommended task is a locally scoped canonical draft preview/review workflow, which remains offline/live-blocked.

## Local Files
* Local Builder: `live_contentops/next_article_draft_authorization_and_readiness_v6.py`
* Codegen script: `live_contentops/next_article_draft_authorization_v5_adapter_codegen_v6.py`
* Committed JSON Packet: `docs/automation/V6_NEXT_ARTICLE_DRAFT_AUTHORIZATION_AND_READINESS/next_article_draft_authorization_and_readiness_packet.json`
* Static TS Adapter: `ui/contentops_v5/src/data/nextArticleDraftAuthorizationReadinessAdapter.ts`
* Backend Python Tests: `tests/test_next_article_draft_authorization_and_readiness_v6.py`
* Codegen Python Tests: `tests/test_next_article_draft_authorization_v5_adapter_codegen_v6.py`
* UI Guardrail Tests: `tests/test_next_article_draft_authorization_readiness_ui_guardrail_v6.py`

## Running Local Verification and Adapter Sync Check
From the repository root, run the status and logic validations:
```bash
python -m pytest tests/test_next_article_draft_authorization_and_readiness_v6.py tests/test_next_article_draft_authorization_readiness_ui_guardrail_v6.py tests/test_next_article_draft_authorization_v5_adapter_codegen_v6.py
```

Verify adapter code-generation matches the packet content:
```bash
python live_contentops/next_article_draft_authorization_v5_adapter_codegen_v6.py
```
