# V6 Next Article Brief Source-Pack and Review Runbook

This is a local/manual-only runbook for the next article brief source-pack collection and operator review workflow (`TASK_CONTENTOPS_V6_NEXT_ARTICLE_BRIEF_SOURCE_PACK_AND_REVIEW_WORKFLOW_V0`).

## Purpose
This workflow prepares a local source-pack checklist and operator review packet for the selected feedback-backlog next article brief candidate. 
* It is a **source-pack/review workflow only**.
* It **does not create a canonical article draft**.
* The brief candidate is **not LLM-ready** until the operator supplies the requested source pack and explicitly authorizes drafting in a separate future task.
* It does not perform any **LLM/provider calls, platform API integrations, credential reads, browser session reads, public URL fetches, or live publication/dispatch actions**.

## Local Evidence Files
* Local Packet Builder: `live_contentops/next_article_brief_source_pack_review_v6.py`
* Committed JSON Packet: `docs/automation/V6_NEXT_ARTICLE_BRIEF_SOURCE_PACK_AND_REVIEW/next_article_brief_source_pack_review_packet.json`
* Road Map Audit Note: `docs/automation/V6_NEXT_ARTICLE_BRIEF_SOURCE_PACK_AND_REVIEW/roadmap_audit_note.md`
* Backend Python Tests: `tests/test_next_article_brief_source_pack_review_v6.py`
* V5 UI Integration: `ui/contentops_v5/src/data/nextArticleBriefSourcePackReviewAdapter.ts`
* UI Guardrail Tests: `tests/test_next_article_brief_source_pack_review_ui_guardrail_v6.py`

## Forbidden Actions
* Do not call LLM providers or platform/network APIs.
* Do not read env variables or credentials.
* Do not run browser automation sessions or scrape/fetch public URLs.
* Do not enable approve/send/publish/dispatch buttons or controls.
* Ensure no financial advice or trade signals exist in the brief/source-pack copy.

## Local Validation

Run Python backend tests from the repository root:
```bash
python -m pytest tests/test_next_article_brief_source_pack_review_v6.py
```

Run UI guardrail tests from the repository root:
```bash
python -m pytest tests/test_next_article_brief_source_pack_review_ui_guardrail_v6.py
```

Run V5 npm test and build from `ui/contentops_v5/`:
```bash
npm test -- --run
npm run build
```
