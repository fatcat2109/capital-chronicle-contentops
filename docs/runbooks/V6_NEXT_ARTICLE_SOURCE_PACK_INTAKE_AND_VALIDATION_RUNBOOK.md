# V6 Next Article Source-Pack Intake and Validation Runbook

This is a local/manual-only runbook for the next article source-pack intake and metadata validation workflow (`TASK_CONTENTOPS_V6_NEXT_ARTICLE_SOURCE_PACK_INTAKE_AND_VALIDATION_WORKFLOW_V0`).

## Purpose
This workflow validates that the operator has supplied the local source-pack evidence required by the next article brief review checklist.
* The operator supplies source-pack evidence metadata manually.
* URLs are stored as **text/hash only and are not fetched, opened, scraped, or network verified**.
* Local evidence paths are recorded as **metadata reference strings only**.
* No **LLM provider calls, network actions, API integrations, credential/env lookups, or browser session modifications** are performed.
* Completion of the source-pack collection **does not authorize drafting**. A separate explicit operator authorization task is required before the drafting phase.

## Local Evidence Files
* Local Packet Builder: `live_contentops/next_article_source_pack_intake_validation_v6.py`
* Committed JSON Packet: `docs/automation/V6_NEXT_ARTICLE_SOURCE_PACK_INTAKE_AND_VALIDATION/next_article_source_pack_intake_validation_packet.json`
* Road Map Audit Note: `docs/automation/V6_NEXT_ARTICLE_SOURCE_PACK_INTAKE_AND_VALIDATION/roadmap_audit_note.md`
* Backend Python Tests: `tests/test_next_article_source_pack_intake_validation_v6.py`
* V5 UI Integration: `ui/contentops_v5/src/data/nextArticleSourcePackIntakeValidationAdapter.ts`
* UI Guardrail Tests: `tests/test_next_article_source_pack_intake_validation_ui_guardrail_v6.py`

## Forbidden Actions
* Do not call LLM providers or platform/network APIs.
* Do not read env variables or credentials.
* Do not run browser automation sessions or scrape/fetch public URLs.
* Do not enable approve/send/publish/dispatch buttons or controls.
* Ensure no financial advice or trade signals exist in the brief/source-pack copy.

## Local Validation

Run Python backend tests from the repository root:
```bash
python -m pytest tests/test_next_article_source_pack_intake_validation_v6.py
```

Run UI guardrail tests from the repository root:
```bash
python -m pytest tests/test_next_article_source_pack_intake_validation_ui_guardrail_v6.py
```

Run V5 npm test and build from `ui/contentops_v5/`:
```bash
npm test -- --run
npm run build
```
