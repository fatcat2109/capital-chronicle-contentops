# Pre-Alpha Manual Decision Batch Packet (Task 0106)

Local-only operator MANUAL DECISION WORKBENCH that consumes a 0105 editorial
batch review packet and prepares one deterministic decision record for every
review queue item, then runs each supplied human-placeholder decision through
the 0098 manual review validation / approval-packet builder.

## What it does

- Builds exactly one `decision_record` per review queue item (a 1:1 mapping).
- Runs each MANUAL decision through 0098 `validate_decision` against its item.
- A clean `approve_manual_publish_prep` also produces a 0098 approval packet,
  meaning the draft is ready for future **manual publish prep only**.
- `request_revision` and `reject` are preserved with their reasons / notes.
- Invalid decisions, decisions over unresolved guardrail findings, and items
  with NO supplied decision are recorded as `blocked` in
  `blocked_decision_records` — never silently dropped, never auto-approved.

## What it does NOT do

This is a manual decision workbench only. It does **not**:

- auto-approve, or apply any default approve-all behavior;
- export, create manual-export packets, or touch any content ledger;
- change any content-ledger publish status;
- publish, schedule, post, or send anything;
- call any provider / LLM / network / search / platform API;
- read credentials or environment secret files;
- ingest metrics, scrape, or run replies / DMs;
- produce public-postable or publish-ready content;
- emit financial advice, signal, or fake Capital Chronicle alpha output.

"Approval" means ready for future MANUAL publish prep only, under 0098
semantics. The downstream manual export (0099) remains a separate human step.

## Hard-boundary flags (pinned on every packet)

```
local_only=true                         fixture_only=true
manual_review_required=true             reviewer_required=true
auto_approval=false                     public_postable=false
manual_export_packet_created=false      content_ledger_created=false
content_ledger_publish_status_changed=false
provider_call_allowed_now=false         network_call_allowed_now=false
platform_api_call_allowed_now=false     scheduler_allowed=false
metrics_ingestion_allowed=false         live_execution_allowed_now=false
credential_or_env_read_allowed=false
```

If any pinned flag is unsafe, or any decision implies publish / export /
platform readiness, or the source 0105 packet was blocked, the packet fails
closed (`packet_status="blocked"`).

## Determinism

Output is fully deterministic: stable IDs, ordering follows the review queue
item order, and the static `2026-01-01T00:00:00Z` timestamp convention is
reused. Repeated runs produce byte-identical JSON.

## Files

- `schemas/pre_alpha_manual_decision_batch_packet.schema.json`
- `live_contentops/pre_alpha_manual_decision_batch.py`
- `fixtures/pre_alpha_manual_decision_batch/valid_manual_decision_batch_config.json`
- `tests/test_pre_alpha_manual_decision_batch.py`

## CLI

```
python -m live_contentops.cli pre-alpha-manual-decision-batch-summary
```

Emits valid JSON with `packet_status`, `review_queue_item_count`,
`decision_record_count`, `approval_packet_count`, `blocked_decision_count`,
`revision_requested_count`, `rejected_count`, `unsafe_flag_count`, and the
pinned non-publishing posture flags.

## Position in the pipeline

```
seed library / calendar (0103)
        -> editorial batch review packet (0105)
                -> [0106 manual decision batch packet]
                       -> approval packets (manual publish prep only, 0098)
```

Manual export / content ledger remain separate, human-driven stages (0099).
This task never advances content past the manual decision stage.
