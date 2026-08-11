# ContentOps Codex Entry Index

Source HEAD: `cdb790d78e093421f0c9b09d430fd234ce3f247d`
Source tree digest: `af083a51c40caa363cc064c4a7c70e9e3e47385a272cb87cb6af6ade84f103f9`

This is a generated descriptive map. Check freshness with:

```text
python scripts/generate_codex_context_index.py --check
```

Start with the nearest scoped instructions, then use the context map and graph:

- root contract: `AGENTS.md`
- backend: `live_contentops/AGENTS.md`
- renderer/future V2: `video/AGENTS.md`
- canonical UI: `ui/contentops_v5/AGENTS.md`
- authority/generated docs: `docs/AGENTS.md`
- V2 map: `docs/codegraph/V2_CONTEXT.md`
- machine graph: `docs/codegraph/graph.json`

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

## Authority anchors

- Current direction: `docs/status/CURRENT_PRODUCT_DIRECTION_OVERLAY.md`
- Current context: `docs/CURRENT_CONTEXT.md`
- Next task pointer: `docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/next_task_pointer.md`
- Tier-2 authority: `docs/automation/CONTENTOPS_TIER2_PRO_VIDEO_FACTORY_NORTH_STAR_V1.md` and `...MASTER_PLAN_V1.md`

## Scope

`1481` nodes and `1687` edges are generated from Python, TypeScript/JavaScript, manifests, authority files, and the scoped AGENTS hierarchy. Noise exclusions are recorded in `graph.json`.
