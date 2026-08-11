# ContentOps Codex Entry Index

Source HEAD: `ef4a34a10cd1f9b7f83710aaf6a39bc44f76c8e3`
Source tree digest: `feb00705334818d8a197141f01ef294ab1a737d44d8bffc69b6e0e7a7aa0bbfe`
Graph schema: `contentops.codex_context_graph.v2`; generator: `2.0.0`

This generated map is descriptive, not product authority.

## Fresh session

Read only these before the exact task files:

1. `AGENTS.md`
2. `docs/codegraph/INDEX.md` (this page)
3. `docs/codegraph/V1_CONTEXT.md`
4. nearest scoped `AGENTS.md`
5. exact implementation and focused tests

Open current direction/next-task authority only when product direction matters: `docs/CURRENT_CONTEXT.md`, `docs/status/CURRENT_PRODUCT_DIRECTION_OVERLAY.md`, and `docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/next_task_pointer.md`.

## Entrypoints

| Kind | Path | Command or symbol |
|---|---|---|
| `one_click_launcher` | `Start_ContentOps_Daily_App.cmd` | `Start_ContentOps_Daily_App.cmd` |
| `canonical_cli` | `live_contentops/cli.py` | `python -m live_contentops.cli` |
| `daily_app_launcher` | `live_contentops/daily_app_launcher_v1.py` | `python -m live_contentops.daily_app_launcher_v1` |
| `daily_app_supervisor` | `live_contentops/daily_app_supervisor_v1.py` | `ContentOpsDailyAppSupervisor` |
| `production_orchestrator` | `live_contentops/production_orchestrator_v1.py` | `ContentOpsProductionOrchestrator` |
| `tier2_local_factory` | `live_contentops/tier2_video_factory_v1.py` | `python -m live_contentops.cli tier2-video-local` |
| `operator_script` | `scripts/Start-ContentOpsDailyApp.ps1` | `scripts/Start-ContentOpsDailyApp.ps1` |
| `canonical_ui` | `ui/contentops_v5/src/main.tsx` | `npm run dev/build/test in ui/contentops_v5` |

## V1 live runtime

- `Start_ContentOps_Daily_App.cmd`
- `live_contentops/daily_app_launcher_v1.py`
- `live_contentops/daily_app_supervisor_v1.py`
- `live_contentops/durable_operational_store_v1.py`
- `tests/test_contentops_daily_app_launcher_v1.py`
- `tests/test_daily_app_supervisor_v1.py`

## Newsroom / intake

- `live_contentops/continuous_headline_ingest_v1.py`
- `live_contentops/eight_platform_substack_first_pipeline_v1.py`
- `live_contentops/_eight_platform_substack_first_pipeline_impl_v1.py`
- `live_contentops/newsroom_assignment_scheduler_v1.py`
- `live_contentops/preselection_intelligence_v1.py`
- `live_contentops/editorial_portfolio_v1.py`
- `tests/test_contentops_continuous_intelligence_realign_v1.py`
- `tests/test_preselection_published_memory_breaking_wake_closeout_v1.py`
- `tests/test_rolling_x_newsroom_cycle_v1.py`

## Capital Chronicle integration

- `live_contentops/capital_chronicle_data_catalog_v1.py`
- `live_contentops/published_corpus_read_model_v1.py`
- `tests/test_contentops_continuous_intelligence_realign_v1.py`
- `tests/test_preselection_published_memory_breaking_wake_closeout_v1.py`

## Evidence

- `live_contentops/rolling_x_targeted_evidence_adapter_v1.py`
- `live_contentops/official_primary_evidence_loader_v1.py`
- `live_contentops/official_primary_source_locator_v1.py`
- `tests/test_rolling_x_targeted_evidence_adapter_v1.py`
- `tests/test_official_primary_evidence_loader_v1.py`
- `tests/test_rolling_x_evidence_viability_v1.py`

## Article / media

- `live_contentops/rolling_x_grounded_article_media_builder_v1.py`
- `tests/test_rolling_x_grounded_article_media_builder_v1.py`

## Publication / readback

- `live_contentops/publication_coordinator_v1.py`
- `live_contentops/destination_transport_registry_v1.py`
- `live_contentops/production_runtime_v1.py`
- `tests/test_publication_coordinator_v1.py`
- `tests/test_destination_identity_pinning_v1.py`
- `tests/test_daily_app_publication_lifecycle_v1.py`
- `tests/test_daily_app_automatic_readback_housekeeping_v1.py`

## V5

- `live_contentops/server.py`
- `live_contentops/daily_app_ui_read_model_v1.py`
- `ui/contentops_v5/src/main.tsx`
- `ui/contentops_v5/src/views/DailyAppConsole.tsx`
- `ui/contentops_v5/src/test/daily_app_console.test.tsx`
- `tests/test_daily_app_ui_read_model_v1.py`

## Router / models

- `live_contentops/nine_router_llm_seam_v2.py`
- `live_contentops/nine_router_ordered_model_router_v2.py`
- `live_contentops/nine_router_provider_adapter_v2.py`
- `tests/test_nine_router_ordered_model_router_v2.py`
- `tests/test_nine_router_provider_adapter_and_preflight_v2.py`

## Tests

Use the focused test beside each hot-path section. Backend tests are under `tests/`; V5 tests are under `ui/contentops_v5/src/test/`. Generator coverage is `tests/test_codex_context_index.py`.

## Current blocker

Committed production-day evidence reports `NO_PUBLICATION_GOVERNED_EVIDENCE_BLOCK` with exact blocker `ALL_RANKED_CLUSTERS_EVIDENCE_BLOCKED`: evidence acquisition and capability fit stopped all 12 ranked clusters before article generation. See `docs/automation/CONTENTOPS_V1_FIRST_REAL_5_8_ARTICLE_PRODUCTION_DAY_V1/README.md`.

Next main V1 task: `TASK_CONTENTOPS_V1_EVIDENCE_GATE_CALIBRATION_AND_REAL_PUBLICATION_UNBLOCK_V1`. Do not implement it as part of context/index maintenance.

## Tier2 separation

Tier2/video is isolated from the V1 runtime and has no public-write authority. Read `docs/codegraph/V2_CONTEXT.md` and `video/AGENTS.md` only for an authorized V2 task. Rejected branches are reference only.

## Generated graph files

- `docs/codegraph/graph.json`: machine nodes, edges, inference labels, metadata, and exclusions
- `docs/codegraph/INDEX.md`: generated hot-path router
- `docs/codegraph/V2_CONTEXT.md`: generated compact V2 separation map
- `docs/codegraph/V1_CONTEXT.md`: curated, validated V1 product/decision/state map

## Regeneration and check

```text
python scripts/generate_codex_context_index.py
python scripts/generate_codex_context_index.py --check
```

## Scope

`6432` nodes and `12038` edges cover files, Python symbols, TypeScript exports, tests, CLI commands, HTTP endpoints, durable tables, schemas, authority anchors, runtime entrypoints, and scoped instructions. Every inferred edge carries an `inference` label. Included/excluded roots are recorded in `graph.json`.
