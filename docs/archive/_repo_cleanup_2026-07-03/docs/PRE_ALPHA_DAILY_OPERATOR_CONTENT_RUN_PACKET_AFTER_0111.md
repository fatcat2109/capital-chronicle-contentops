# Pre-Alpha Daily Operator Content Run Packet (After 0111)

Task: `TASK_CONTENTOPS_0111_PRE_ALPHA_DAILY_OPERATOR_CONTENT_RUN_PACKET_V0`

## What this is

A local-only, deterministic **daily operator content run packet** that ties the
accepted 0103-0110 pre-alpha ContentOps workbench into ONE reviewable summary for
a single manual content run. It composes the existing generators rather than
duplicating their business logic:

| Stage | Source module |
| ----- | ------------- |
| seed library / editorial calendar | `pre_alpha_seed_library` (0103) |
| operator dashboard | `pre_alpha_operator_dashboard` (0104) |
| editorial batch review | `pre_alpha_editorial_batch_review` (0105) |
| manual decision batch | `pre_alpha_manual_decision_batch` (0106) |
| manual export batch | `pre_alpha_manual_export_batch` (0107) |
| platform manual templates | `pre_alpha_platform_manual_templates` (0110) |
| manual publish record | `pre_alpha_manual_publish_record` (0108) |

## What this is NOT

This is a daily **manual operator workbench summary only**. It does not, and
cannot:

- approve content automatically (`auto_approval=false`)
- publish or auto-publish (`auto_publish=false`, `public_postable=false`)
- post, schedule, reply, or DM
- call a platform / provider / LLM / network API
- scrape or ingest metrics automatically
- read credentials or `.env`
- produce public-postable or publish-ready output
- generate platform API payloads / request bodies

Operator final check remains mandatory before any external manual publishing.

## Behavior

- **Composition, not duplication.** Each child generator builds its own chain
  from its own default fixtures; the run packet only projects read-only
  summaries and reconciles counts.
- **Honest publish-record stage.** The run drives the 0108 publish-record stage
  with config-supplied `manual_records` (default empty list). With no operator
  records, eligible exports honestly remain `not_recorded` / `export_prepared`;
  nothing is inferred as published.
- **Ready vs not-ready.** `ready_for_operator_copy_paste_count` equals the number
  of clean platform copy/paste template records. `blocked_or_not_ready_count`
  sums blocked seeds, non-exported decisions, unsupported/blocked templates,
  blocked records, and eligible-but-not-yet-recorded exports.
- **Blocked items preserved.** Blocked seeds, revision/rejected decisions,
  unsupported templates, and blocked records are surfaced in
  `blocked_content_report` with a `stage` label, never dropped or shown as ready.
- **Fail closed.** `packet_status="blocked"` if any hard-boundary flag is unsafe,
  any composed child packet is unexpectedly blocked, any platform API payload
  appears, any composed export is `manually_published` within the run, or any
  template implies publish/platform readiness.

## Hard-boundary flags (pinned)

`local_only`, `fixture_only`, `manual_operator_workbench_only`,
`manual_review_required`, `operator_final_check_required` are pinned `true`.
`public_postable`, `auto_approval`, `auto_publish`,
`platform_api_call_allowed_now`, `provider_call_allowed_now`,
`network_call_allowed_now`, `scheduler_allowed`,
`automatic_metrics_ingestion_allowed`, `scraping_allowed`,
`credential_or_env_read_allowed`, `live_execution_allowed_now` are pinned
`false`.

## Files

- `schemas/pre_alpha_daily_operator_content_run_packet.schema.json`
- `live_contentops/pre_alpha_daily_operator_content_run.py`
- `fixtures/pre_alpha_daily_operator_content_run/valid_daily_operator_content_run_config.json`
- `tests/test_pre_alpha_daily_operator_content_run.py`

## CLI

```
python -m live_contentops.cli pre-alpha-daily-operator-content-run-summary
```

Emits a deterministic JSON summary: `packet_status`,
`ready_for_operator_copy_paste_count`, `blocked_or_not_ready_count`,
`review_queue_item_count`, `decision_record_count`, `export_packet_count`,
`platform_template_record_count`, `recorded_publish_count`, `unsafe_flag_count`,
and all non-network/provider/platform/scheduler/scraping/credential flags pinned
`false`.

## Default run posture

With the default fixtures: `packet_status=pass`, 1 ready copy/paste template,
4 not-ready items (1 blocked seed, revision + rejected decisions surfaced as
non-exported, and 1 eligible-but-unrecorded export), 0 unsafe flags, 0 recorded
publishes.
