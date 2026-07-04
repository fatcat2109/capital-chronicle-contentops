# Pre-Alpha Editorial Batch Review Packet (Task 0105)

Local-only operator REVIEW WORKBENCH that turns the accepted 0103 seed library /
editorial calendar plus the 0096 prompt-pack / style-profile / editorial-rubric
config into a single deterministic, reviewable batch.

## What it does

For each seed in a library:

- SAFE (valid) planned seeds are run through the 0095 content engine and the
  0097 draft renderer to produce **review queue items**.
- UNSAFE / blocked seeds are preserved in `blocked_content_report` with their
  guardrail reasons. They are **never silently dropped**.

A seed the calendar marks safe but that fails at render time is re-classified as
blocked (recorded with `render:` reasons) and forces the packet to fail closed.

## What it does NOT do

This is a review workbench only. It does **not**:

- approve, export, publish, schedule, post, or send anything;
- create approval packets, manual-export packets, or content-ledger objects;
- change any content-ledger publish status;
- call any provider / LLM / network / search / platform API;
- read credentials or environment secret files;
- ingest metrics or perform scraping / replies / DMs;
- produce public-postable or publish-ready content.

## Hard-boundary flags (pinned on every packet)

```
local_only=true                         fixture_only=true
manual_review_required=true             reviewer_required=true
auto_approval=false                     public_postable=false
approval_packet_created=false           manual_export_packet_created=false
content_ledger_publish_status_changed=false
provider_call_allowed_now=false         network_call_allowed_now=false
platform_api_call_allowed_now=false     scheduler_allowed=false
metrics_ingestion_allowed=false         live_execution_allowed_now=false
credential_or_env_read_allowed=false
```

If any pinned flag is unsafe, the packet fails closed (`packet_status="blocked"`)
and the violation is surfaced in `safety_audit` and `blocked_reasons`.

## Determinism

Output is fully deterministic: stable IDs, ordering follows the library's seed
order, and the static `2026-01-01T00:00:00Z` timestamp convention is reused.
Repeated runs produce byte-identical JSON.

## Files

- `schemas/pre_alpha_editorial_batch_review_packet.schema.json`
- `live_contentops/pre_alpha_editorial_batch_review.py`
- `fixtures/pre_alpha_editorial_batch_review/valid_batch_config.json`
- `tests/test_pre_alpha_editorial_batch_review.py`

## CLI

```
python -m live_contentops.cli pre-alpha-editorial-batch-review-summary
```

Emits valid JSON with `packet_status`, `total_seeds`,
`selected_safe_seed_count`, `blocked_seed_count`, `rendered_packet_count`,
`review_queue_item_count`, `unsafe_flag_count`, and the pinned non-publishing
posture flags.

## Position in the pipeline

```
seed library / calendar (0103)
        +  prompt/style/rubric config (0096)
                -> [0105 editorial batch review packet]
                       -> review queue items (manual human review only)
```

Downstream manual review / approval / export remain separate, human-driven
stages (0098/0099). This task never advances content past review.
