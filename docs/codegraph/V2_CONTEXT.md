# ContentOps Codex Context Map

Generated from source HEAD `6b326597504afbc0deb2785721dff605d21e40f9`. Source tree digest: `60beb848d0e0abd2dedad3c93ccd01cd748f40a2b016f712ae59048870406c4d`.
Run `python scripts/generate_codex_context_index.py --check` to determine staleness.

This generated map is descriptive repository state and is subordinate to root `AGENTS.md`.
Current authority must be read from the V3 authority spine rather than inferred from generated
task summaries.

## Current authority spine

1. `AGENTS.md`
2. `docs/codegraph/INDEX.md`
3. `docs/automation/CONTENTOPS_CURRENT_AUTHORITY_AND_SUPERSESSION_MAP_V1.md`
4. `docs/automation/CONTENTOPS_CURRENT_STALE_DOCS_MANIFEST_V1.md`
5. `docs/automation/CONTENTOPS_CAPABILITY_ROUTED_HYBRID_EXECUTION_POLICY_V1.md`
6. `docs/automation/CONTENTOPS_FINAL_PRODUCT_NORTH_STAR_V3.md`
7. `docs/automation/CONTENTOPS_FINAL_PRODUCT_MASTER_PLAN_V3.md`
8. this V2 map or curated `docs/codegraph/V1_CONTEXT.md`
9. the appropriate current lane pointer
10. the nearest scoped `AGENTS.md`
11. exact implementation, tests, and evidence

## Current product boundary

- Capital Chronicle/Core Analyzer owns proprietary analytical and numeric truth.
- ContentOps may use only an exact upstream packet whose consumer and intended use are explicitly
  granted; internal, candidate, proxy, degraded, stale, or incompatible material is non-public.
- V1 is the canonical newsroom/publication runtime. Its current lane pointer is
  `docs/automation/CONTENTOPS_FINAL_DAILY_APP_V1_CURRENT_EXECUTION_POINTER_V3.md`.
- V2 is an isolated retention-native media lane with zero video public-write authority. Its
  current lane pointer is
  `docs/automation/CONTENTOPS_V2_RETENTION_NATIVE_VIDEO_FACTORY_CURRENT_EXECUTION_POINTER_V2.md`.
- Do not infer a current task, model route, provider, or acceptance state from this generated file;
  read the current authority map and lane pointer bytes.

## Subsystem map

| Subsystem | Entry files | Tests / evidence |
|---|---|---|
| V1 state/runtime | `live_contentops/durable_operational_store_v1.py`, `production_orchestrator_v1.py`, `daily_app_supervisor_v1.py` | `tests/test_durable_operational_store_v1.py`, `tests/test_daily_app_*` |
| 9Router | `live_contentops/nine_router_ordered_model_router_v2.py`, `nine_router_llm_seam_v2.py`, `nine_router_provider_adapter_v2.py` | `tests/test_nine_router_*`, `docs/automation/CONTENTOPS_9ROUTER_ORDERED_MODEL_AUTHORITY_V2/` |
| Tier2-A | `live_contentops/tier2_video_factory_v1.py` | `tests/test_tier2_video_factory_v1.py`, `docs/automation/CONTENTOPS_TIER2_A_PROGRAMMABLE_VIDEO_VERTICAL_SLICE_V1/` |
| Direct image | `live_contentops/direct_image_api_v1.py`, `scripts/run_direct_image_bakeoff_v1.py` | `tests/test_direct_image_api_v1.py`, `docs/automation/CONTENTOPS_TIER2_DIRECT_IMAGE_API_REAL_SMOKE_AND_BAKEOFF_V1/` |
| Current authority | `AGENTS.md`, `docs/automation/CONTENTOPS_CURRENT_AUTHORITY_AND_SUPERSESSION_MAP_V1.md`, `docs/automation/CONTENTOPS_CURRENT_STALE_DOCS_MANIFEST_V1.md` | V3 North Star, V3 master plan, current lane pointers |
| UI | `ui/contentops_v5/src/main.tsx`, `ui/contentops_v5/src/views/DailyAppConsole.tsx`, `ui/contentops_v5/src/dailyAppTypes.ts` | `ui/contentops_v5/src/test/`, `ui/contentops_v5/AGENTS.md` |
| Tooling | `scripts/generate_codex_context_index.py` | `tests/test_codex_context_index.py` |

## Graph inventory

- Nodes: `7348`
- Edges: `13886`
- Entrypoints: `16`
- Python import edges, TypeScript/JavaScript relative import edges, and determinable test-to-
  implementation edges are included.
- Archives, runtime output, generated media, caches, vendor trees, and node_modules are excluded.
