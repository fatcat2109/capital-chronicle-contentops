# TASK_CONTENTOPS_0099_PRE_ALPHA_MANUAL_EXPORT_PACKETS_AND_CONTENT_LEDGER_V0

## Purpose

Add the local-only pre-alpha manual export packet and content ledger layer. It
consumes a clean Task 0098 approval packet and emits deterministic manual-export
packets plus content-ledger entries for operator review and manual copy/paste
tracking. No platform API, no live posting, no scheduler, no metrics ingestion,
no provider/network/API/credential access.

## Files created

- `schemas/pre_alpha_manual_export_packet.schema.json`
- `schemas/pre_alpha_content_ledger_entry.schema.json`
- `live_contentops/pre_alpha_manual_export.py`
- `fixtures/pre_alpha_manual_export/valid_manual_export_x.json`
- `fixtures/pre_alpha_manual_export/valid_manual_export_linkedin.json`
- `fixtures/pre_alpha_manual_export/valid_content_ledger_entry.json`
- `fixtures/pre_alpha_manual_export/invalid_publish_allowed_now.json`
- `fixtures/pre_alpha_manual_export/invalid_live_execution_allowed_now.json`
- `fixtures/pre_alpha_manual_export/invalid_missing_final_operator_check.json`
- `fixtures/pre_alpha_manual_export/invalid_unapproved_packet.json`
- `fixtures/pre_alpha_manual_export/invalid_signal_language_export.json`
- `tests/test_pre_alpha_manual_export.py`
- `docs/PRE_ALPHA_MANUAL_EXPORT_PACKETS_AND_CONTENT_LEDGER_AFTER_0099.md`
- `docs/TASK_CONTENTOPS_0099_PRE_ALPHA_MANUAL_EXPORT_PACKETS_AND_CONTENT_LEDGER_V0.md`

## Files changed

- `live_contentops/cli.py` (added `pre-alpha-manual-export-summary` command)

## What remains disabled

- Platform API / posting / scheduler / metrics ingestion: never wired.
- LLM / provider / network / web / search calls: none.
- Telegram live work: stopped by operator decision; untouched here.
- `.env` reads, credential access: none.
- Auto-publish, public-postable output, fake alpha output: blocked.
- Financial advice / signal / execution language: blocked by guardrail scans.

## Integration

Export validates only clean 0098 approval packets
(`approval_status == approved_manual_publish_prep`,
`manual_publish_prep_ready == true`, no `blocked_reasons`). Source attribution
(artifact IDs or general/process marker), limitations, and non-publishing flags
are preserved. The approved text is independently re-scanned for forbidden,
alpha-implying, and unverified-numeric-market language.

The content ledger keeps `manual_publish_url` / `manual_publish_timestamp` /
`manual_metrics` null by default and only advances to `manually_published` when
the operator supplies a non-empty URL for a non-blocked export.

## Validation

See the task evidence packet for exact commands and counts.

## Next task

`TASK_CONTENTOPS_0100_PRE_ALPHA_LOCAL_EXPORT_BUNDLE_AND_OPERATOR_RUNBOOK_V0`
