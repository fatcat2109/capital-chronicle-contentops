# CORE V0 Repeated Shadow Soak and Recovery

Work Package E. Operating mode `SHADOW_ONLY`. Zero public writes.

Launch-readiness disposition: `READY_WITH_EXPLICIT_CAVEATS`

This is an **accelerated logical soak** over a deterministic clock. It is not a claim of seven calendar days of availability. Calendar uptime and live reliability remain for the separately authorized live cohort.

## Cohort

| Measure | Value |
|---|---|
| Logical newsroom days | 10 |
| Intake window decisions | 30 of 30 completed |
| Complete packages | 16 |
| Domains represented | 2 |
| Newsroom-lane packages | 6 |
| Capital Chronicle transformations | 10 |
| Explicit NO_PUBLICATION decisions | 10 |
| Duplicate / update-chain decisions | 10 |

## Logical days

| Day | Selected | Deferred | Complete packages | No-publication |
|---|---:|---:|---:|---:|
| 2026-07-15 | 4 | 1 | 2 | 1 |
| 2026-07-16 | 4 | 1 | 2 | 1 |
| 2026-07-17 | 3 | 2 | 1 | 1 |
| 2026-07-18 | 4 | 1 | 2 | 1 |
| 2026-07-19 | 3 | 2 | 1 | 1 |
| 2026-07-20 | 4 | 1 | 2 | 1 |
| 2026-07-21 | 3 | 2 | 1 | 1 |
| 2026-07-22 | 4 | 1 | 2 | 1 |
| 2026-07-23 | 3 | 2 | 1 | 1 |
| 2026-07-24 | 4 | 1 | 2 | 1 |

## Recovery and failure drills

| Drill | Result | Observed |
|---|---|---|
| `restart_between_intake_and_selection` | PASS | state ASSIGNMENT_CANDIDATE v4, replay PASS |
| `restart_during_package_production` | PASS | state PRODUCTION_IN_PROGRESS v6, replay PASS |
| `restart_after_package_before_release_intent_claim` | PASS | state REVIEW_READY v7, replay PASS |
| `duplicate_scheduler_window_tick` | PASS | 1 durable event(s) after two identical ticks |
| `concurrent_workers_same_durable_item` | PASS | 1 winner(s), 1 refusal(s), stale token rejected=True |
| `source_unavailable` | PASS | gate fired on 10/10 logical days |
| `rights_cleared_visual_unavailable` | PASS | gate fired on 10/10 logical days |
| `chart_qa_failure` | PASS | 16/16 charts passed methodology QA, 0 failures |
| `stale_or_low_delta_update` | PASS | 10 suppressed, 10 explicit NO_PUBLICATION |
| `material_update_chain_continuation` | PASS | 9 chain(s) span multiple logical days; 10 duplicate/low-delta suppression(s) |
| `simulated_write_readback_unknown` | PASS | 48 unknown-write simulation(s), 0 auto-retried, 0 blind retries |
| `reconciliation_present` | PASS | 16 reconciled-present case(s), all confirmed without retry: True |
| `reconciliation_absent_safe_to_retry` | PASS | 16 proven-absent, 16 unreconciled requiring recovery |
| `kill_switch_active_during_release_queue` | PASS | status kill_switch_engaged, 0 processed, 144 blocked |
| `corrupted_exported_evidence_store_intact` | PASS | corrupted file unparseable=True, store integrity=True, re-export matches original=True |
| `calibration_sensitivity_sweep` | PASS | hard gates invariant=True, policy hash unchanged=True, dispositions moved=True |

## SLO measurements

| Measurement | Numerator | Denominator | Verdict |
|---|---:|---:|---|
| `window_completion` | 30 | 30 | PASS |
| `lost_work_items` | 0 | 100 | PASS |
| `duplicate_durable_claims` | 0 | 100 | PASS |
| `restart_reconstruction` | 4 | 4 | PASS |
| `recovery_drill_coverage` | 16 | 16 | PASS |
| `hard_gate_replay_determinism` | 10 | 10 | PASS |
| `package_lineage_completeness` | 16 | 16 | PASS |
| `package_completion_time` | 1.2933 | 10 | PASS |
| `no_publication_count` | 10 | 10 | PASS |
| `update_chain_count` | 10 | 10 | PASS |
| `domain_coverage_decided` | 9 | 8 | PASS |
| `domain_concentration` | 2 | 8 | INSUFFICIENT_EVIDENCE |
| `complete_package_count` | 16 | 12 | PASS |
| `model_provider_attempts` | 0 | 0 | NOT_APPLICABLE |
| `simulated_unknown_write_resolution` | 32 | 48 | PASS |
| `incident_count_and_closure` | 0 | 16 | PASS |
| `public_write_count` | 0 | 144 | PASS |
| `external_cost_and_runtime` | 31.1061 | 10 | PASS |
| `operator_visible_blocker_count` | 4 | 4 | PASS |
| `calendar_uptime` | — | — | UNMEASURABLE |

## Launch edge (dry model)

- release intents built: 144, each binding 8 exact hashes
- simulated operations: 144; outbox executions: 0; platform actions: 0; public writes: 0
- authorization actors exercised: AUTONOMOUS_POLICY, OPERATOR_DECISION
- boolean approval is never accepted as live authority
- no payload is rebuilt after authorization

## Cost and runtime

- total runtime: 31.1061 s
- mean per logical day: 1.2933 s
- external cost: NONE_NO_PAID_API_OR_MODEL_CALL

## Caveats

- no full-suite PASS is claimed;
- no CI PASS is claimed;
- calendar uptime and live reliability are not measured and not claimed;
- runtime measurements are genuine wall-clock values and are the only nondeterministic outputs;
- this task grants no credential, provider, browser/CDP, scheduler, dispatch, publication, or public-write authority.

## Remaining launch blockers

- exact owner-authorized live scope is required before any live cohort
- credential handles and account bindings are not hydrated in SHADOW_ONLY
- real platform readback and calendar-time reliability are unproven until the live cohort
- independent pixel-perfect visual audit of the operator surface is not claimed
