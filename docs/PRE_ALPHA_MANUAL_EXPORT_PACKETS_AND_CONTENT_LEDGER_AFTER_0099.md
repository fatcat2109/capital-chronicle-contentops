# Pre-Alpha Manual Export Packets and Content Ledger (Task 0099)

Local-only, deterministic. This layer consumes a clean Task 0098 approval packet
and emits a manual-export packet plus a content-ledger entry. The outputs exist
for operator review and MANUAL copy/paste only. They never imply API posting,
scheduling, metrics ingestion, or live execution.

## What this is NOT

- Not a platform poster. No platform API call is ever made.
- Not a scheduler. `scheduler_allowed` is pinned `false`.
- Not a metrics fetcher. `metrics_ingestion_allowed` is pinned `false`; metrics
  are operator-entered placeholders only.
- Not auto-publish. There is no path that flips `publish_allowed_now` true.
- Not public-postable. `public_postable` is pinned `false`.
- No network, provider, LLM, credential, or `.env` access.

## Modules and schemas

- `live_contentops/pre_alpha_manual_export.py`
- `schemas/pre_alpha_manual_export_packet.schema.json`
- `schemas/pre_alpha_content_ledger_entry.schema.json`

## Manual export packet

Built by `build_export_packet(approval_packet, export_format=None)`.

Key fields: `manual_export_packet_id`, `approval_packet_id`, `draft_id`,
`platform_family`, `content_type`, `export_status`
(`prepared_for_operator_review` / `blocked`), `export_text`, `export_format`
(`copy_paste_text` / `newsletter_markdown` / `generic_markdown`),
`source_artifact_ids`, `is_general_process_content`, `limitations`,
`manual_publish_only=true`, `final_operator_check_required=true`,
`manual_copy_ready` (true only when clean), and the pinned non-publishing flags
(`public_postable`, `publish_allowed_now`, `platform_publish_allowed_now`,
`live_execution_allowed_now`, `platform_api_call_allowed`, `scheduler_allowed`,
`metrics_ingestion_allowed` -> all `false`), plus `blocked_reasons` and
`audit_refs`.

Export is only allowed from a clean 0098 approval packet where
`approval_status == approved_manual_publish_prep` and
`manual_publish_prep_ready == true` with no `blocked_reasons`. Any unsafe flag,
missing source attribution, or forbidden/alpha/numeric-market language in the
approved text fails closed: `export_status=blocked`, `manual_copy_ready=false`,
`export_text=""`, and populated `blocked_reasons`.

## Content ledger entry

Built by `build_ledger_entry(export_packet, manual_record=None)`.

Lifecycle status: `draft_rendered`, `manual_reviewed`, `export_prepared`,
`manually_published`, `blocked`. `manual_publish_url`,
`manual_publish_timestamp`, and `manual_metrics` stay `null` by default. The
ledger only advances to `manually_published` when the operator supplies a
non-empty `manual_publish_url` via `manual_record`, and only when the export is
not blocked. A blocked export always yields a `blocked` ledger entry with a null
URL, even if a `manual_record` URL is supplied.

## Guardrails (defense in depth)

Approved text is independently re-scanned using the shared
`grounded_research_brief` forbidden-language and alpha-implication detectors plus
the 0095 numeric-market-claim detector. An externally supplied approval packet
cannot smuggle financial advice, signal/execution language, fake alpha claims,
or unverified numeric market claims through export.

## CLI

`python -m live_contentops.cli pre-alpha-manual-export-summary`

Prints a deterministic local capability summary with all non-publishing flags
false and `manual_publish_url_default_null=true`.

## Next task

`TASK_CONTENTOPS_0100_PRE_ALPHA_LOCAL_EXPORT_BUNDLE_AND_OPERATOR_RUNBOOK_V0`
