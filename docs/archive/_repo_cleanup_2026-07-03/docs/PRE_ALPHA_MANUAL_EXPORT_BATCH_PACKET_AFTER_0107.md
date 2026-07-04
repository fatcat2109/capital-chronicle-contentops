# Pre-Alpha Manual Export Batch Packet (Task 0107)

Local-only MANUAL EXPORT PREPARATION layer that consumes a 0106 manual decision
batch packet and prepares manual-export packets plus `export_prepared` content
ledger entries for CLEAN 0098 approval packets only.

## What it does

- Reads the 0106 decision batch packet's `decision_records` + `approval_packets`.
- For every decision with status `approved_manual_publish_prep` backed by a
  CLEAN 0098 approval packet (`manual_publish_prep_ready=true`, no
  `blocked_reasons`), it builds one 0099 manual export packet and one
  `export_prepared` content ledger entry.
- Revision-requested, rejected, invalid, and blocked decisions are preserved in
  `non_exported_decision_report` with reasons — never silently dropped, never
  exported.
- Every clean approval maps to exactly one export packet and one ledger entry.

## What it does NOT do

This is MANUAL copy/paste preparation only. It does **not**:

- publish, schedule, post, or send anything;
- call any platform / provider / LLM / network / search API;
- read credentials or environment secret files;
- ingest metrics or scrape;
- auto-publish or create any `manually_published` ledger state;
- set `manual_publish_url`, `manual_publish_timestamp`, or `manual_metrics`
  (these always stay `null` by default);
- produce public-postable / publish-ready content;
- emit financial advice, signal, or fake Capital Chronicle alpha output.

Recording an actual published URL / metrics is deferred to a separate future
operator-record task. This task never advances content past `export_prepared`.

## Hard-boundary flags (pinned on every packet)

```
local_only=true                      fixture_only=true
manual_review_required=true          final_operator_check_required=true
auto_publish=false                   public_postable=false
platform_api_call_allowed_now=false  scheduler_allowed=false
metrics_ingestion_allowed=false      provider_call_allowed_now=false
network_call_allowed_now=false       live_execution_allowed_now=false
credential_or_env_read_allowed=false manually_published_created=false
manual_publish_url_default_null=true manual_metrics_default_null=true
```

## Fail-closed conditions

`packet_status` becomes `blocked` if any of the following holds:

- the source 0106 decision batch packet was itself blocked;
- an approved decision has no matching clean 0098 approval packet;
- a produced export packet carries `blocked_reasons` or an unsafe publish flag;
- a produced ledger entry advances past `export_prepared` (e.g.
  `manually_published`) or carries a non-null URL / timestamp / metrics;
- any pinned hard-boundary flag is unsafe.

The 0099 export builder independently re-scans approved text for forbidden /
signal / alpha / unverified-numeric language, so an externally tampered approval
packet cannot smuggle unsafe content into an export.

## Determinism

Output is fully deterministic: stable IDs, ordering follows the 0106 decision
record order, and the static `2026-01-01T00:00:00Z` timestamp convention is
reused. Repeated runs produce byte-identical JSON.

## Files

- `schemas/pre_alpha_manual_export_batch_packet.schema.json`
- `live_contentops/pre_alpha_manual_export_batch.py`
- `fixtures/pre_alpha_manual_export_batch/valid_manual_export_batch_config.json`
- `tests/test_pre_alpha_manual_export_batch.py`

## CLI

```
python -m live_contentops.cli pre-alpha-manual-export-batch-summary
```

Emits valid JSON with `packet_status`, `source_decision_record_count`,
`approved_decision_count`, `revision_requested_count`, `rejected_count`,
`blocked_decision_count`, `manual_export_packet_count`,
`content_ledger_entry_count`, `manually_published_count` (always 0),
`unsafe_flag_count`, and the pinned non-publishing posture flags.

## Position in the pipeline

```
seed library / calendar (0103)
  -> editorial batch review packet (0105)
       -> manual decision batch packet (0106)
            -> [0107 manual export batch packet]
                   -> manual export packets + export_prepared ledger (0099)
```

Recording an actual manual publish URL / metrics remains a separate future
operator step.
