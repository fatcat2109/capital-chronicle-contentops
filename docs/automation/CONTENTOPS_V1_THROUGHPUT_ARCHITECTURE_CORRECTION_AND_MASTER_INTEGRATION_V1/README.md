# V1 Throughput Architecture Correction — Evidence

Authority date: 2026-08-13

Task: `TASK_CONTENTOPS_V1_THROUGHPUT_ARCHITECTURE_CORRECTION_AND_MASTER_INTEGRATION_V1`

## Result

- Continuous intake now refreshes a hash-bound, fresh, maximum-12-candidate checkpoint with zero model calls.
- A publication opportunity reuses that checkpoint and does not run rolling-universe leaf/global assignment or semantic story-type routing.
- Ordinary reporting uses one canonical quality-writer call, deterministic factual/safety checks, and zero mandatory semantic-review/revision calls.
- The opportunity and completed evidence/article stages are resumable from bounded durable output checkpoints.
- `DurablePublicationCoordinator` remains the sole public-write owner. Canonical Substack confirmation queues destination-local derivatives and releases canonical truth immediately.
- All evidence here is controlled/zero-write. It does not claim a public publication or real provider latency.

## Validation

- Focused regression selection: `150 passed`.
- Dedicated zero-write smoke: `1 passed in 0.80s`.
- Controlled critical-path telemetry: 1024-headline source universe, 12 prepared candidates, 0 assignment semantic calls, 0 story-routing semantic calls, 1 article-writer semantic call, 0 mandatory review calls, 0.274 seconds measured inside the controlled newsroom path, 9-destination publication plan, 0 public writes.
- Canonical/derivative decoupling remains covered by `test_derivative_failure_never_erases_reconciled_substack_truth` in `tests/test_publication_coordinator_v1.py`.
- Hard factual blocking remains covered by the untraceable-number and deterministic-gate regressions in `tests/test_rolling_x_grounded_article_media_builder_v1.py` and `tests/test_tier1_editorial_quality_v1.py`.

See `zero_write_smoke_telemetry_v1.json` for the sanitized measured record.
