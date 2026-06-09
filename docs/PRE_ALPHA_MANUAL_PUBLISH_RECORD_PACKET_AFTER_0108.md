# Pre-Alpha Manual Publish Record Packet (Task 0108)

Local-only MANUAL RECORDKEEPING layer that consumes a 0107 manual export batch
packet plus operator-supplied manual records and advances eligible CLEAN export
packets to content-ledger `lifecycle_status=manually_published` ONLY when an
explicit, valid manual record is supplied.

## What it does

- Reads the 0107 export batch packet's `manual_export_packets`.
- Treats an export packet as eligible only when `export_status` is
  `prepared_for_operator_review`, it has no `blocked_reasons`, and
  `manual_copy_ready=true`.
- For each operator-supplied manual record that references an eligible export
  and carries a non-empty `manual_publish_url` + `manual_publish_timestamp`, it
  builds (via 0099 `build_ledger_entry`) a `manually_published` ledger entry.
- Eligible exports with no record stay `export_prepared` in
  `not_recorded_export_report` — never inferred as published.
- Invalid / duplicate / unknown-targeting records go to
  `blocked_record_report` with reasons.

This is recordkeeping performed AFTER an operator has externally copy/pasted and
published content by hand.

## What it does NOT do

- publish, schedule, post, or send anything;
- call any platform / provider / LLM / network / search API;
- scrape or ingest metrics automatically (metrics are operator-supplied only,
  and may be null);
- read credentials or environment secret files;
- auto-publish or INFER that publication happened;
- produce public-postable / publish-ready content;
- emit financial advice, signal, or fake Capital Chronicle alpha output.

Metrics, when present, must be hand-entered objects. A record carrying any
platform-API / scheduling / auto-post / fetched-metrics field is rejected.

## Hard-boundary flags (pinned on every packet)

```
local_only=true                       fixture_only=true
manual_recordkeeping_only=true        manual_operator_record_required=true
platform_api_call_allowed_now=false   provider_call_allowed_now=false
network_call_allowed_now=false        scheduler_allowed=false
automatic_metrics_ingestion_allowed=false  scraping_allowed=false
credential_or_env_read_allowed=false  live_execution_allowed_now=false
auto_publish=false
```

## Fail-closed conditions

`packet_status` becomes `blocked` if any of the following holds:

- the source 0107 export batch packet was itself blocked;
- a manual record is missing `manual_export_packet_id`, `manual_publish_url`,
  or `manual_publish_timestamp`;
- a record references an unknown or blocked (ineligible) export packet;
- a duplicate record targets the same export packet;
- `manual_metrics` is present but not an object/null;
- a record carries a forbidden field (`platform_api_payload`, `scheduled_post`,
  `auto_post`, `fetched_metrics`, `scraped_metrics`, etc.);
- defense-in-depth: a recorded ledger fails to reach `manually_published`;
- any pinned hard-boundary flag is unsafe.

Because a blocked export packet is never eligible, it can never become
`manually_published`.

## Determinism

Output is fully deterministic: stable IDs, record order follows the input,
not-recorded entries follow the export packet order, and the static
`2026-01-01T00:00:00Z` ledger timestamp convention is reused. Repeated runs
produce byte-identical JSON.

## Files

- `schemas/pre_alpha_manual_publish_record_packet.schema.json`
- `live_contentops/pre_alpha_manual_publish_record.py`
- `fixtures/pre_alpha_manual_publish_record/valid_manual_publish_record_config.json`
- `tests/test_pre_alpha_manual_publish_record.py`

## CLI

```
python -m live_contentops.cli pre-alpha-manual-publish-record-summary
```

Emits valid JSON with `packet_status`, `eligible_export_packet_count`,
`manual_record_count`, `recorded_publish_count`, `not_recorded_count`,
`blocked_record_count`, `updated_ledger_entry_count`,
`automatic_metrics_ingestion_count` (always 0), `unsafe_flag_count`, and the
pinned non-publishing posture flags.

## Position in the pipeline

```
seed library / calendar (0103)
  -> editorial batch review packet (0105)
       -> manual decision batch packet (0106)
            -> manual export batch packet (0107)
                 -> [0108 manual publish record packet]
                        -> manually_published ledger entries (operator records)
```

The operator publishes by hand outside this system; 0108 only records the
hand-entered URL / timestamp / metrics into the content ledger.
