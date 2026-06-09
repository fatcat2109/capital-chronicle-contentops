# Pre-Alpha Manual Performance Record Packet (After 0116)

Task: `TASK_CONTENTOPS_0116_LOCAL_MANUAL_PERFORMANCE_RECORD_CONTRACT_V0`

LOCAL ONLY | MANUAL ONLY | SUPERVISED | NO NETWORK | NO PROVIDER | NO PLATFORM API | NO METRICS INGESTION | NO SCRAPING | NO CREDENTIALS | NO POSTING

## Purpose

The `PreAlphaManualPerformanceRecordPacket` provides a local, deterministic, read-only validation boundary for operator-entered performance records. Its strategic purpose is to lay the foundation for future "compare-to-improve" content reviews without relying on automation, platform credentials, or scraping.

It validates operator-supplied records (fixtures) that capture the performance (e.g. impressions, likes, comments) of content that the operator has already published externally by hand.

## Strictly Forbidden Capabilities

This module is a core guardrail. It strictly forbids and blocks on:
- **No fetched/API metrics**: `metrics_source_type` MUST be `operator_entered`. Any other type (e.g. `scraped`, `fetched`, `api`) fails closed.
- **No scraping**: Auto-ingestion of metrics is completely forbidden.
- **No inferred publication**: Every performance record MUST have an explicit reference to a manual publish record (`linked_manual_publish_record_id`).
- **No credential/env reads**: It never attempts to read `.env` or access API keys.
- **No posting/scheduling**: It enforces `public_postable: false` and `auto_publish: false` across all records.

## Missing / Null Metrics

Because this relies on manual operator observation, it is completely expected that some metrics may be missing or null (e.g., if a platform limits visibility or if the operator simply didn't record it).

- **Null metrics are preserved**: Missing metrics remain `null`. They are never silently converted to `0`.
- **Reason required**: Any `null` metric requires a `metric_null_reason` explaining why the operator couldn't record it.
- **Counted**: The system counts and exposes `missing_metric_count` in the summary.

## Invalid Metrics

The module fails closed on invalid data:
- **Negative metrics**: Metrics must be integers `>= 0`. Negative metrics block the packet.
- **Non-integer metrics**: Only integers are permitted. Decimals or string values block.

## Operator CLI UX

This module integrates into the main CLI as an optional post-publish command. It is NOT part of the mandatory daily run loop.

```
python -m live_contentops.cli pre-alpha-manual-performance-record-summary
```

It outputs a JSON-safe payload showing the number of valid records, missing metrics, and hard boundary flags confirming safety.
