# V6 feedback backlog review to next article brief operator runbook

Local/manual-only runbook for `TASK_CONTENTOPS_V6_FEEDBACK_BACKLOG_REVIEW_TO_NEXT_ARTICLE_BRIEF_LOOP_V0` and its targeted QA repair.

## Purpose

Review the deterministic operator feedback backlog and inspect the review-only next article brief candidate packet. This runbook does not create a canonical draft, publish, dispatch, schedule, approve, send, call a provider, read credentials, read env values, fetch URLs, scrape public pages, or use platform APIs.

## Canonical local evidence

- Packet: `docs/automation/V6_FEEDBACK_BACKLOG_REVIEW_TO_NEXT_ARTICLE_BRIEF/feedback_backlog_next_article_brief_packet.json`
- Builder: `live_contentops/feedback_backlog_next_article_brief_v6.py`
- Builder tests: `tests/test_feedback_backlog_next_article_brief_v6.py`
- V5 adapter: `ui/contentops_v5/src/data/feedbackBacklogNextArticleBriefAdapter.ts`
- V5 surfaces:
  - Manual Export / Pilot Verification
  - Approval Queue
  - Evidence Vault

## Operator review checklist

1. Confirm the source feedback was operator-supplied and approved for editorial planning use.
2. Confirm the selected backlog candidate is review-only and not a dispatch/publishing signal.
3. Confirm `source_pack_required_before_drafting=true` before requesting any canonical draft.
4. Confirm `canonical_draft_created=false` and no live readiness claim is made.
5. Confirm blocked controls remain `approve`, `dispatch`, `publish`, `schedule`, and `send`.
6. Attach a separate source pack before any canonical drafting task.
7. Keep copy educational and non-advisory.

## Forbidden actions

- No LLM/provider/API call.
- No public URL fetch or scrape.
- No browser session, cookie, localStorage, sessionStorage, or token inspection.
- No credential or env value read.
- No publish, send, dispatch, schedule, approve, or live action.
- No claim of canonical draft readiness, dispatch readiness, provider readiness, public URL verification, or live readiness.

## Validation commands

Run from the repository root unless noted otherwise:

```powershell
python -m pytest tests/test_feedback_backlog_next_article_brief_v6.py
```

Run from `ui/contentops_v5/`:

```powershell
npm test -- --run src/test/manual_export_pilot_verification.test.tsx
npm test
npm run build
```

## Browser QA evidence

Committed local V5 browser QA artifacts live under:

`docs/browser_qa/contentops_v5_feedback_backlog_next_article_brief/`

The screenshots are visual QA evidence only. They are not live-readiness evidence, public URL verification evidence, platform-auth evidence, provider-readiness evidence, or dispatch-readiness evidence.
