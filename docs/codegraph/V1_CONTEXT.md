# ContentOps V1 Current Context Map

Authority date: 2026-08-11

This is a curated, generator-validated description of the implementation on the indexed source
commit. It is not product authority. Jim's latest instruction, fetched GitHub bytes, committed
code/tests/evidence, and current authority documents control when they conflict with this map.

## Product flow

```text
one-click launcher
→ durable supervisor
→ continuous zero-LLM X intake
→ complete rolling 24h unique headline universe
→ hierarchical assignment and compact shortlist
→ published-memory + Capital Chronicle + portfolio preselection
→ story type and article/update mode
→ targeted governed evidence acquisition
→ grounded article + source-backed media
→ semantic review and at most two bounded revisions
→ destination-native packages and publication plan
→ DurablePublicationCoordinator
→ versioned destination transport
→ strict readback and reconciliation
→ real metrics and bounded learning
→ Daily App read model → V5 Today/control room
```

No-publication remains valid. The 5–8 articles/day band is a portfolio target, not permission to
weaken evidence or create filler.

## Current production status

- FDA-G: `SOAK_ACTIVE_AWAITING_GENUINE_CALENDAR_TIME_EVIDENCE`; not accepted, no `v1.1.0`.
- Reconciled remote master at this context task's start:
  `5e52e3da178e1366db5f386af3f2d9af30bdc685`. The generated `INDEX.md` and `graph.json`
  record the exact later source commit whose relevant tree they describe.
- Latest committed production runtime/source commit in the first real production-day evidence:
  `6f8a1788f094c607896b8304161dfea783a20c64`.
- Latest real production-day result: `NO_PUBLICATION_GOVERNED_EVIDENCE_BLOCK`; three decision
  opportunities, zero articles, zero visuals/packages/dispatches/public objects/readbacks, and
  no unknown write. Committed canonical published-corpus count: `0`.
- Exact immediate blocker: `ALL_RANKED_CLUSTERS_EVIDENCE_BLOCKED`.

These are committed evidence facts, not a claim about live state after the evidence capture.
Source: `docs/automation/CONTENTOPS_V1_FIRST_REAL_5_8_ARTICLE_PRODUCTION_DAY_V1/`.

## Current known blocker

The scheduled production decision completed intake, assignment, story routing, and preselection.
All 12 ranked clusters then stopped at targeted evidence: capability resolution ran, but no
candidate acquired the complete story/article-mode-specific official evidence document set. The
evidence packet records missing affected-entity, filing/release, timeline, geography, and other
governed capabilities plus official-source location/response issues.

This is an evidence capability/acquisition blocker, not a public-write safety failure. The next
main V1 task is
`TASK_CONTENTOPS_V1_EVIDENCE_GATE_CALIBRATION_AND_REAL_PUBLICATION_UNBLOCK_V1`: calibrate
over-broad non-safety requirements by story/article mode and improve first-party acquisition,
while preserving hard truth, permission, freshness, rights, readiness, and write-safety gates.
That work is intentionally outside this context task.

## Decision and data flow

```text
Start_ContentOps_Daily_App.cmd
  → scripts/Start-ContentOpsDailyApp.ps1
  → daily_app_launcher_v1.main
  → cli daily-app start
  → ContentOpsDailyAppSupervisor
      ├─ _run_continuous_intake_housekeeping
      │    → continuous_headline_ingest_v1.run_ingestion_housekeeping_iteration
      │    → headline_ingestion.Data_Ingestion.append_headline_sidecars
      ├─ recovery/readback/performance housekeeping
      └─ _execute_window (scheduled, material-event, or OPERATOR_REQUESTED)
           → eight_platform_substack_first_pipeline_v1.run_rolling_x_newsroom_cycle
           → ContentOpsProductionOrchestrator.execute
           → _eight_platform_substack_first_pipeline_impl_v1._run_rolling_x_newsroom_cycle
                → newsroom_assignment_scheduler_v1.load_rolling_x_headline_sidecars
                → assign_rolling_x_headlines_with_nine_router
                → preselection_intelligence_v1.apply_preselection_intelligence
                     ├─ published_corpus_read_model_v1.load_published_corpus
                     ├─ capital_chronicle_data_catalog_v1.query_story_scoped_cc_context
                     └─ editorial_portfolio_v1.classify_story_novelty
                → classify_rolling_x_story_types_with_nine_router
                → select_first_viable_rolling_x_cluster
                → RollingXTargetedEvidenceAdapter.__call__
                → build_rolling_x_grounded_article_and_media
                → _run_bounded_rolling_x_editorial_cycle
                → _prepare_rolling_x_release_candidate
                → _build_rolling_x_publication_plan
           → DurablePublicationCoordinator.publish_plan
                → destination_transport_registry_v1.registration_for_destination
                → FinalDailyAppTransportRuntime.publish/readback
                → outbox → dispatch → strict readback → reconciliation
           → daily_app_performance_v1 observations/learning
           → daily_app_ui_read_model_v1.build_daily_app_snapshot
           → GET /api/daily-app/snapshot
           → ui/contentops_v5/src/views/DailyAppConsole.tsx (Today and control-room views)
```

The public facade and production orchestrator are the callable boundary. The private
implementation is mapped to explain control flow, not to authorize a new direct entrypoint.

## Canonical module map

| Stage | Module and important symbol | Inputs | Outputs / next stage | Focused tests |
|---|---|---|---|---|
| One-click resume | `Start_ContentOps_Daily_App.cmd`; `daily_app_launcher_v1.main` | existing production store/output paths, port ownership | idempotent `daily-app start`; supervisor | `test_contentops_daily_app_launcher_v1.py`, `test_contentops_ingestion_bootstrap_v1.py` |
| Supervisor | `daily_app_supervisor_v1.ContentOpsDailyAppSupervisor` | durable controls/windows/triggers, clock, canonical cycle | exactly-one claimed window; housekeeping and newsroom execution | `test_daily_app_supervisor_v1.py`, `test_daily_app_operator_trigger_v1.py` |
| Continuous intake | `continuous_headline_ingest_v1.run_ingestion_housekeeping_iteration` | canonical Chrome 9222 capture outcome/checkpoint | deduplicated daily sidecar rows and material-event trigger | `test_contentops_continuous_intelligence_realign_v1.py`, `test_preselection_published_memory_breaking_wake_closeout_v1.py` |
| Rolling 24h load | `newsroom_assignment_scheduler_v1.load_rolling_x_headline_sidecars` | daily sidecar glob, cutoff, 24h window | unique source-event-time-valid headline universe | `test_rolling_x_newsroom_cycle_v1.py` |
| Assignment | `assign_rolling_x_headlines_with_nine_router` | rolling universe and checkpoints | leaf/global clusters, compact ranked shortlist | `test_rolling_x_hierarchical_assignment_v1.py` |
| Preselection | `preselection_intelligence_v1.apply_preselection_intelligence` | enriched shortlist, published corpus, CC catalog, cutoff | reranked/held clusters with novelty, CC match, concentration, article/update mode | `test_preselection_published_memory_breaking_wake_closeout_v1.py` |
| Published memory | `published_corpus_read_model_v1.load_published_corpus` | durable confirmed dispatch/reconciliation truth and output artifacts | article-deduplicated full-text/content-unavailable corpus | `test_preselection_published_memory_breaking_wake_closeout_v1.py` |
| Capital Chronicle context | `capital_chronicle_data_catalog_v1.discover_cc_data_estate`; `query_story_scoped_cc_context` | read-only Main App root and story terms | metadata catalog and bounded story-scoped matches; no upstream mutation | `test_contentops_continuous_intelligence_realign_v1.py` |
| Portfolio | `editorial_portfolio_v1.classify_story_novelty`; `portfolio_state_today` | cluster delta, related articles, today's corpus | breaking/follow-up/deepen/repeat/hold and concentration state | `test_contentops_continuous_intelligence_realign_v1.py` |
| Story routing | `classify_rolling_x_story_types_with_nine_router` | preselected enriched clusters | exact story type per cluster; no factual authority | `test_rolling_x_newsroom_cycle_v1.py` |
| Evidence | `rolling_x_targeted_evidence_adapter_v1.RollingXTargetedEvidenceAdapter.__call__` | selected cluster, story type, required capability profile, cutoff | governed receipts/documents or explicit blockers | `test_rolling_x_targeted_evidence_adapter_v1.py`, `test_rolling_x_evidence_viability_v1.py` |
| Article/media | `rolling_x_grounded_article_media_builder_v1.build_rolling_x_grounded_article_and_media` | successful viability/evidence packet | grounded article plus deterministic/source-backed assets | `test_rolling_x_grounded_article_media_builder_v1.py` |
| Review/revision | `_run_bounded_rolling_x_editorial_cycle` | article/assets and semantic reviewer/reviser | PASS or no-publication after at most two revisions | `test_rolling_x_newsroom_cycle_v1.py` |
| Packages/plan | `_prepare_rolling_x_release_candidate`; `_build_rolling_x_publication_plan` | reviewed article/media and destination readiness | locked payloads and deterministic lifecycle plan | `test_rolling_x_newsroom_cycle_v1.py`, `test_rolling_x_v1_publishability_closure_v1.py` |
| Publication owner | `publication_coordinator_v1.DurablePublicationCoordinator.publish_plan` | work item and publication plan | durable pre-write intent, dispatch/readback/reconciliation outcomes | `test_publication_coordinator_v1.py`, `test_daily_app_publication_lifecycle_v1.py` |
| Transport/readiness | `destination_transport_registry_v1.registration_for_destination`; `DestinationReadinessManager` | exact destination/surface and sanitized probes | one versioned transport identity and current readiness | `test_destination_identity_pinning_v1.py`, `test_publication_coordinator_v1.py` |
| Recovery/readback | `DurablePublicationCoordinator.recover_pending`; supervisor safe housekeeping | pending outbox/attempt/dispatch identities | readback-only UNKNOWN_WRITE recovery and reconciliation | `test_daily_app_automatic_readback_housekeeping_v1.py`, `test_daily_app_kill_switch_housekeeping_v1.py` |
| Metrics/learning | `daily_app_performance_v1.collect_observation`; `evaluate_learning_decision` | reconciled real public objects and available metrics | append-only observations and bounded policy/no-op decisions | `test_daily_app_performance_learning_v1.py` |
| V5 projection | `daily_app_ui_read_model_v1.build_daily_app_snapshot`; `DailyAppConsole` | read-only durable state and current artifact summaries | sanitized Today/Queue/Published/Performance/Learning/Platforms/Incidents/Controls | `test_daily_app_ui_read_model_v1.py`, `ui/contentops_v5/src/test/daily_app_console.test.tsx` |

## State model

`durable_operational_store_v1.ContentOpsDurableStore` plus its checksum-frozen migrations is the
single state authority. The graph exposes each `durable_table:*` node; schema bytes stay in code.

| Concern | Durable owner/table(s) | Role |
|---|---|---|
| schema/lineage | `schema_migrations`, `schema_lineage_metadata`, legacy compatibility tables | migration and historical lineage proof |
| operating control | `operating_controls` | one CAS-updated mode: autonomous, supervised, shadow, or kill switch |
| work lifecycle | `work_items`, `transition_events`, `story_versions`, `artifact_references` | canonical item state, append-only transition truth, versions/artifacts |
| scheduling/ownership | `operational_windows`, `scheduler_ticks`, `leases`, `heartbeats` | deterministic windows and fenced exactly-one execution |
| operator request | `operator_cycle_triggers` | append-only, at most one pending `OPERATOR_REQUESTED` cycle |
| review/approval | `review_records`, `operator_decisions`, `approval_envelopes` | governed human/review state without parallel authority |
| publication intent | `outbox_messages` | exact payload/identity before any external write |
| dispatch identity | `platform_dispatches` | attempt state, certainty, stable public-object identity |
| observation | `readbacks` | strict provider/browser readback bound to dispatch identity |
| recovery truth | `reconciliations` | confirmed, pending, or absent-safe-to-retry state; no blind retry |
| safety | `incidents` | durable sanitized operational incidents |
| readiness | `destination_readiness` | latest sanitized exact destination/surface readiness |
| metrics/learning | `performance_observations`, `learning_policy_versions`; legacy `metrics`, `feedback_records`, `learning_reviews` | real eligible observations and append-only bounded policy history |

## External local dependencies

Nonsecret identities only:

- production DB: `A:\Capital Chronicle\Runtime\ContentOps\contentops_daily_app_v1.sqlite3`
- runtime output root: `A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs`
- Capital Chronicle Main App read-only root: `A:\Capital Chronicle\Main App`
- canonical headline sidecar root:
  `headline_ingestion/data/intake/headline_sidecars/step1_headline_sidecar_<YYYY>_<MM>_<DD>.jsonl`
- Chrome `CapitalChronicleBot`, CDP 9222: ingestion only, exact operator-owned profile reuse
- Edge `contentops-social-main`, CDP 9223: publishing/media/readback and authorized read-only
  performance observation only

These paths are identities, not permission to inspect credentials/session material or mutate the
production store/Capital Chronicle databases.

## Current progress navigation

- continuous-intelligence realignment:
  `docs/automation/CONTENTOPS_V1_CONTINUOUS_INTELLIGENCE_INTAKE_CC_DATABASE_AND_EDITORIAL_PORTFOLIO_REALIGN_V1/`
- preselection/published-memory/breaking-wake closeout:
  `docs/automation/CONTENTOPS_V1_PRESELECTION_INTELLIGENCE_PUBLISHED_MEMORY_AND_BREAKING_WAKE_CLOSEOUT_V1/`
- first real 5–8 production-day attempt and current evidence blocker:
  `docs/automation/CONTENTOPS_V1_FIRST_REAL_5_8_ARTICLE_PRODUCTION_DAY_V1/`
- FDA-G current status and next routing:
  `docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/next_task_pointer.md`

This is the minimum recent history needed for navigation. Do not traverse the full task archive
unless a current document or code conflict requires it.

## Stale and legacy traps

- `POST /api/run-pipeline` and the old V6 `launchFullPipeline` UI route are quarantined by
  `live_entrypoint_registry_v1.py` and `server.py`; they cannot launch production.
- Historical pipeline/runner modules and supervised-only assumptions are not the current
  one-click supervisor → facade → orchestrator path.
- `docs/status/current_project_status.json` contains known stale routing fields; it cannot
  override the current overlay or Jim's instruction.
- Historical `capital_chronicle_ALL_DATA.json` is not new intake truth. The append-only daily
  sidecar store is canonical for current headline intake.
- Do not create a parallel scheduler, newsroom, outbox, publisher, publication coordinator,
  provider gateway, state store, or dashboard.
- Rejected Tier2-B and the rejected direct-image implementation at `8b043a5` are reference only;
  do not merge them or add `ai.api-cheap.site` to the generic 9Router adapter. The separately
  accepted direct-image boundary remains isolated from V1 and grants no public-write authority.
- Private `_eight_platform_substack_first_pipeline_impl_v1` is implementation behind the public
  facade/orchestrator, not a new caller boundary.

## Fresh-session simulation

Simulation performed from only root `AGENTS.md`:

| Need | Navigation after root → `INDEX.md` → `V1_CONTEXT.md` | Focused test / blocker evidence |
|---|---|---|
| continuous X intake | `live_contentops/AGENTS.md` → `continuous_headline_ingest_v1.py` | `test_contentops_continuous_intelligence_realign_v1.py` |
| preselection intelligence | `live_contentops/AGENTS.md` → `preselection_intelligence_v1.py` | `test_preselection_published_memory_breaking_wake_closeout_v1.py` |
| Capital Chronicle story context | `live_contentops/AGENTS.md` → `capital_chronicle_data_catalog_v1.py` | `test_contentops_continuous_intelligence_realign_v1.py` |
| evidence acquisition | `live_contentops/AGENTS.md` → `rolling_x_targeted_evidence_adapter_v1.py` | `test_rolling_x_targeted_evidence_adapter_v1.py` |
| canonical publication | `live_contentops/AGENTS.md` → `publication_coordinator_v1.py` | `test_publication_coordinator_v1.py` |
| V5 Today | `ui/contentops_v5/AGENTS.md` → `src/views/DailyAppConsole.tsx` | `src/test/daily_app_console.test.tsx` |
| current blocker | `INDEX.md` → production-day evidence `README.md` | `ALL_RANKED_CLUSTERS_EVIDENCE_BLOCKED` |

Unique files opened for all eight requested destinations, including root/index/context, three
scoped instruction files (`live_contentops`, V5, and tests), six implementation/UI files, five
focused test files, and blocker evidence: 18.
No broad master plan, historical archive, stale status JSON, or Tier2 implementation was needed.
