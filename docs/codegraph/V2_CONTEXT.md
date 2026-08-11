# ContentOps Codex Context Map

Generated from source HEAD `ef4a34a10cd1f9b7f83710aaf6a39bc44f76c8e3`. Source tree digest: `feb00705334818d8a197141f01ef294ab1a737d44d8bffc69b6e0e7a7aa0bbfe`.
Run `python scripts/generate_codex_context_index.py --check` to determine staleness.

This map is descriptive repository state, not product authority. Jim's current direction and
the committed status/next-task documents remain authoritative.

## Accepted master capabilities

- Canonical V1 Daily App runtime, durable operational store, production orchestrator, router
  seam, bounded publication/readback/reconciliation, and canonical V5 UI.
- Tier2-A local renderer-neutral `VideoProgram` factory in
  `live_contentops/tier2_video_factory_v1.py`, with no provider/platform/public write.
- Current 9Router text/model authority in `live_contentops/nine_router_*_v2.py`.

## Rejected or unmerged experiments

- `task/tier2-b-remotion-multimodal-bakeoff-v1`: rejected visual product; reference only.
- `task/tier2-image-generation-9router-contract-correction-v1` at `8b043a5`: rejected direct
  `ai.api-cheap.site` image transport; do not import it.

Reference-only Remotion relationships are recorded descriptively in `graph.json` but its source
files are not imported into master: `Root.tsx` composes `SceneRenderer`, `SceneRenderer`
dispatches to `primitives.tsx` inside `scaffold.tsx`, and the renderer-neutral Python factory
targets `render-job.mjs`.

## Current V2 blocker and route

`LOCAL_9ROUTER_IMAGE_REGISTRY_AND_ROUTE_NOT_YET_PROVEN_END_TO_END`.

Next main action: `TIER2_LOCAL_9ROUTER_IMAGE_ROUTE_CORRECTION_AND_REAL_BAKEOFF`.
Only after that should a fresh V2 creative rebuild address story selection, nonnumeric
narration, premium typography, richer motion, and a later rights-aware real-person/entity
resolver. No video public-write authority exists.

## Subsystem map

| Subsystem | Entry files | Tests / evidence |
|---|---|---|
| V1 state/runtime | `live_contentops/durable_operational_store_v1.py`, `production_orchestrator_v1.py`, `daily_app_supervisor_v1.py` | `tests/test_durable_operational_store_v1.py`, `tests/test_daily_app_*` |
| 9Router | `live_contentops/nine_router_ordered_model_router_v2.py`, `nine_router_llm_seam_v2.py`, `nine_router_provider_adapter_v2.py` | `tests/test_nine_router_*`, `docs/automation/CONTENTOPS_9ROUTER_ORDERED_MODEL_AUTHORITY_V2/` |
| Tier2-A | `live_contentops/tier2_video_factory_v1.py` | `tests/test_tier2_video_factory_v1.py`, `docs/automation/CONTENTOPS_TIER2_A_PROGRAMMABLE_VIDEO_VERTICAL_SLICE_V1/` |
| UI | `ui/contentops_v5/src/main.tsx`, `ui/contentops_v5/src/views/DailyAppConsole.tsx`, `ui/contentops_v5/src/dailyAppTypes.ts` | `ui/contentops_v5/src/test/`, `ui/contentops_v5/AGENTS.md` |
| Tooling | `scripts/generate_codex_context_index.py` | `tests/test_codex_context_index.py` |

## Graph inventory

- Nodes: `6432`
- Edges: `12038`
- Entrypoints: `8`
- Python import edges, TypeScript/JavaScript relative import edges, and determinable test-to-
  implementation edges are included.
- Archives, runtime output, generated media, caches, vendor trees, and node_modules are excluded.
