# `live_contentops/` — Canonical Backend Contract

This scope contains the canonical V1 newsroom/runtime foundations and the accepted local
Tier2-A Python slice. Root safety and authority rules still apply.

## Start here

- CLI registry: `cli.py`; console module entry: `__main__.py`
- canonical production boundary: `production_orchestrator_v1.py` and
  `eight_platform_substack_first_pipeline_v1.py`
- durable state: `durable_operational_store_v1.py`
- Daily App coordination: `daily_app_supervisor_v1.py`, `daily_app_launcher_v1.py`
- canonical model seam: `nine_router_llm_seam_v2.py`, ordered policy in
  `nine_router_ordered_model_router_v2.py`, transport in `nine_router_provider_adapter_v2.py`
- Tier2-A local factory: `tier2_video_factory_v1.py`
- accepted dedicated Tier-2 direct-image diagnostic: `direct_image_api_v1.py`, with the bounded
  local runner in `scripts/run_direct_image_bakeoff_v1.py`

Use `docs/codegraph/INDEX.md` to find callers and mapped tests before opening broad modules.

## Invariants

- Extend canonical seams; do not create parallel state/router/pipeline/publication authority.
- The durable store is production authority. Never reset/recreate it for tests or tooling.
- Provider adapters use credentials but never serialize/log them. Exact requested/effective
  identity and bounded budgets remain observable.
- V1 browser roles, readiness gates, KILL_SWITCH, UNKNOWN_WRITE, outbox, readback, and
  reconciliation behavior are protected.
- Tier-2 remains isolated/local and must not touch the live V1 production store or gain upload,
  browser, platform, or public-write behavior.
- The accepted direct-image boundary calls
  `https://ai.api-cheap.site/v1/images/generations` with `AI_API_CHEAP_API_KEY` only and remains
  separate from the generic 9Router adapter. `gpt-5.5` is the provisional generated-
  illustration default; its output is never factual or documentary authority.
- Do not import the rejected `8b043a5` implementation or add `ai.api-cheap.site` to the generic
  9Router adapter. The confirmed HTTP 400 results for `wan2.7-image-pro` and
  `qwen-image-2.0` remain unresolved but do not block the fresh V2 creative-system rebuild.
- `VideoProgram` is renderer-neutral authority; FFmpeg/Remotion/Pillow are compiler targets.

## Validation routing

Backend tests live in `tests/` and usually mirror the implementation filename:

- store/runtime: `test_durable_operational_store_v1.py`, `test_daily_app_*`
- router: `test_nine_router_*`
- Tier2-A: `test_tier2_video_factory_v1.py`
- CLI registration: `test_cli.py` plus feature-specific CLI tests

Run the smallest relevant pytest selection. Any shared router/store/CLI edit also requires its
canonical regression file.
