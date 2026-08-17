# ContentOps Codex Context Map

Generated from source HEAD `f994a9ed7b730e54d09b29900a527daa9b8f51c9`. Source tree digest: `ca68aac04c25c73da48059fce62e8b5fb14abf0b92e42675b1dc33c971f771f3`.
Run `python scripts/generate_codex_context_index.py --check` to determine staleness.

This map is descriptive repository state, not product authority. Jim's current direction and
the committed status/next-task documents remain authoritative.

## Accepted master capabilities

- Canonical V1 Daily App runtime, durable operational store, production orchestrator, router
  seam, bounded publication/readback/reconciliation, and canonical V5 UI.
- Tier2-A local renderer-neutral `VideoProgram` factory in
  `live_contentops/tier2_video_factory_v1.py`, with no provider/platform/public write.
- Current 9Router text/model authority in `live_contentops/nine_router_*_v2.py`.
- `TASK_CONTENTOPS_TIER2_DIRECT_IMAGE_API_REAL_SMOKE_AND_BAKEOFF_V1` accepted
  `PASS_WITH_CAVEAT` at `a859d5ff82707842f59163e4ec5150b22fbe6b0e`: the dedicated direct
  `https://ai.api-cheap.site/v1/images/generations` route using `AI_API_CHEAP_API_KEY` is
  proven end to end for `gpt-5.5`. Evidence:
  `docs/automation/CONTENTOPS_TIER2_DIRECT_IMAGE_API_REAL_SMOKE_AND_BAKEOFF_V1/README.md`.

## Rejected or unmerged experiments

- `task/tier2-b-remotion-multimodal-bakeoff-v1`: rejected visual product; reference only.
- `task/tier2-image-generation-9router-contract-correction-v1` at `8b043a5`: rejected; do not
  import its implementation or add `ai.api-cheap.site` to the generic 9Router adapter.

Reference-only Remotion relationships are recorded descriptively in `graph.json` but its source
files are not imported into master: `Root.tsx` composes `SceneRenderer`, `SceneRenderer`
dispatches to `primitives.tsx` inside `scaffold.tsx`, and the renderer-neutral Python factory
targets `render-job.mjs`.

## Current V2 free-form chapterized authority and route

- `gpt-5.5` is the provisional V2 generated-illustration default pending future product
  evidence; generated illustration is never factual or documentary authority.
- `wan2.7-image-pro` and `qwen-image-2.0` returned confirmed HTTP 400 responses on the tested
  contract and remain unresolved without blocking V2.
- The V2 free-form chapterized owner override, `NORTH_STAR_V2`, `MASTER_PLAN_V2`,
  `TASK_GRAPH_V2`, current V2 execution pointer, Remotion baseline, and fresh-session handoff
  are the canonical V2 product authority. Older V2 and V1 plan sets are historical where they
  conflict with this chain.
- The current task is
  `TASK_CONTENTOPS_V2_FREEFORM_CHAPTERIZED_HIGH_COORDINATOR_XHIGH_CREATIVE_OWNER_POLISH_V1`.
  The parent/deterministic executor is GPT-5.6 Sol HIGH; fresh viewer-facing creative authors
  and the actual-media critic are GPT-5.6 Sol XHIGH. MAX/ULTRA and mode bakeoffs are retired.
- Remotion is deterministic execution, not creative authority. Viewer-facing source remains
  free-form React/Remotion code organized by semantic creative chapters. Chapters are not
  automatically render units, and deterministic aesthetic schemas/gates are forbidden.
- The rejected creative branch `task/tier2-v2-creative-system-rebuild-v1` at `d231b54e` is
  reference only: do not merge or continue its slideshow-heavy creative product.
- The rejected first retention-native attempt at `b6f50029` is also reference only; do not
  continue its repetitive creative grammar.
- Output is 1080-first with real authored audio/music, rights-aware assets, dirty-range review,
  chapter caching, stream-copy assembly, bounded XHIGH actual-media critique, and Jim/ChatGPT
  owner review. 4K is deferred/forbidden in the current contract. Virality is never guaranteed.
- V2 is isolated from V1 and has zero public-write authority.

## Subsystem map

| Subsystem | Entry files | Tests / evidence |
|---|---|---|
| V1 state/runtime | `live_contentops/durable_operational_store_v1.py`, `production_orchestrator_v1.py`, `daily_app_supervisor_v1.py` | `tests/test_durable_operational_store_v1.py`, `tests/test_daily_app_*` |
| 9Router | `live_contentops/nine_router_ordered_model_router_v2.py`, `nine_router_llm_seam_v2.py`, `nine_router_provider_adapter_v2.py` | `tests/test_nine_router_*`, `docs/automation/CONTENTOPS_9ROUTER_ORDERED_MODEL_AUTHORITY_V2/` |
| Tier2-A | `live_contentops/tier2_video_factory_v1.py` | `tests/test_tier2_video_factory_v1.py`, `docs/automation/CONTENTOPS_TIER2_A_PROGRAMMABLE_VIDEO_VERTICAL_SLICE_V1/` |
| Direct image | `live_contentops/direct_image_api_v1.py`, `scripts/run_direct_image_bakeoff_v1.py` | `tests/test_direct_image_api_v1.py`, `docs/automation/CONTENTOPS_TIER2_DIRECT_IMAGE_API_REAL_SMOKE_AND_BAKEOFF_V1/` |
| V2 free-form chapterized authority | `docs/automation/CONTENTOPS_V2_FREEFORM_CHAPTERIZED_HIGH_XHIGH_OWNER_OVERRIDE_V1.md`, `docs/automation/CONTENTOPS_V2_RETENTION_NATIVE_VIDEO_FACTORY_CURRENT_EXECUTION_POINTER_V2.md`, `docs/automation/CONTENTOPS_V2_FRESH_CHAT_HANDOFF_V1.md` | Free-form pipeline, V2 North Star, master plan, task graph, Remotion baseline, owner-polish evidence |
| UI | `ui/contentops_v5/src/main.tsx`, `ui/contentops_v5/src/views/DailyAppConsole.tsx`, `ui/contentops_v5/src/dailyAppTypes.ts` | `ui/contentops_v5/src/test/`, `ui/contentops_v5/AGENTS.md` |
| Tooling | `scripts/generate_codex_context_index.py` | `tests/test_codex_context_index.py` |

## Graph inventory

- Nodes: `7009`
- Edges: `13179`
- Entrypoints: `14`
- Python import edges, TypeScript/JavaScript relative import edges, and determinable test-to-
  implementation edges are included.
- Archives, runtime output, generated media, caches, vendor trees, and node_modules are excluded.
