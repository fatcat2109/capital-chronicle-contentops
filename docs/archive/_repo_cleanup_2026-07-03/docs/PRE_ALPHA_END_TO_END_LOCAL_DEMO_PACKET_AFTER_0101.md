# Pre-Alpha End-to-End Local Demo Packet (Task 0101)

LOCAL ONLY | FIXTURE ONLY | NO NETWORK | NO PROVIDER | NO PLATFORM | NO POSTING

A deterministic, offline demo that drives a safe fixture seed through the entire
accepted 0095-0099 pre-alpha pipeline and produces one reviewable demo packet
covering every stage:

```
seed
  -> editorial packet              (0095 pre_alpha_content_engine)
  -> rendered draft / review queue (0097 pre_alpha_draft_renderer)
  -> manual review / approval      (0098 pre_alpha_manual_review)
  -> manual export packet          (0099 pre_alpha_manual_export)
  -> content ledger entry          (0099 pre_alpha_manual_export)
```

0096 prompt pack / style profile / editorial rubric are validated and fed into
the renderer stage.

## What this is NOT
- Not a poster. No platform API call is ever made.
- Not a scheduler. `scheduler_allowed` is pinned `false`.
- Not a metrics fetcher. `metrics_ingestion_allowed` is pinned `false`.
- Not auto-publish. The demo supplies no manual_record, so the ledger stays at
  `export_prepared` with `manual_publish_url`/`timestamp`/`metrics` = null.
- Not auto-approval. The demo decision is an explicit human-review placeholder
  that is re-validated against the review item and re-scanned downstream.
- No network, provider, LLM, credential, or `.env` access.

## Module and fixture
- `live_contentops/pre_alpha_pipeline_demo.py`
- `fixtures/pre_alpha_pipeline_demo/valid_end_to_end_demo_input.json`

## Demo packet shape
`run_demo(seed)` / `run_demo_from_file(path=None)` return a demo packet with:
`demo_packet_id`, `created_at`, `demo_status` (`pass`/`blocked`), `seed`,
`stages` (editorial_packet, rendered_packet, review_queue_items, item_traces),
`stages_reached`, `safety_audit`, `safety_violations`, `blocked_reasons`, and a
demo-level pinned posture where every no-publish / no-live / no-provider /
no-network / no-scheduler / no-metrics flag is `false` and
`manual_review_required` / `final_operator_check_required` are `true`.

Each item trace records the per-draft decision, approval packet, export packet,
and ledger entry.

## Fail-closed behavior
- Unsafe seeds (signal/trade language, fake alpha, unverified numeric market
  claims, market notes without freshness/limitations) block at the editorial or
  render stage; `demo_status=blocked` with surfaced `blocked_reasons`.
- A deterministic safety audit re-checks every pinned flag across stages plus
  the ledger null defaults. Any flag not `false`, or any ledger that advanced to
  `manually_published`, is recorded as a `safety_violation` and blocks the demo.
- Adversarial seed flags (e.g. `public_postable=true`) cannot flip the pinned
  demo posture.

## Commands
- Generate / inspect the default demo result:
  `python -m live_contentops.cli pre-alpha-pipeline-demo-summary`
- Programmatic: `from live_contentops.pre_alpha_pipeline_demo import run_demo_from_file`

## Tests
- `tests/test_pre_alpha_pipeline_demo.py` (9 tests): full pass path, every stage
  recorded, all pinned flags false, ledger null defaults, signal-language block,
  fake-alpha block, adversarial-flag containment, summary evidence, and a static
  no-network/no-env import guard.

## Next task
AWAIT_CHATGPT_NEXT_TASK_MAPPING
