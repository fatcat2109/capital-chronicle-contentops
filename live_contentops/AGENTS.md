# `live_contentops/` — Canonical Backend Contract

This scope contains the canonical V1 newsroom/runtime foundations and the accepted local
Tier2-A Python slice. Root safety and authority rules still apply.

## Start here

- CLI registry: `cli.py`; console module entry: `__main__.py`
- canonical production boundary: `production_orchestrator_v1.py` and
  `eight_platform_substack_first_pipeline_v1.py`
- durable state: `durable_operational_store_v1.py`
- Daily App coordination: `daily_app_supervisor_v1.py`, `daily_app_launcher_v1.py`
- continuous intake: `continuous_headline_ingest_v1.py`; rolling 24h loader and hierarchical
  assignment: `newsroom_assignment_scheduler_v1.py`
- preselection: `preselection_intelligence_v1.py`, `published_corpus_read_model_v1.py`,
  `capital_chronicle_data_catalog_v1.py`, `editorial_portfolio_v1.py`
- evidence/article: `rolling_x_targeted_evidence_adapter_v1.py`,
  `rolling_x_grounded_article_media_builder_v1.py`
- sole public-write owner and transport map: `publication_coordinator_v1.py`,
  `destination_transport_registry_v1.py`
- canonical model seam: `nine_router_llm_seam_v2.py`, ordered policy in
  `nine_router_ordered_model_router_v2.py`, transport in `nine_router_provider_adapter_v2.py`
- Tier2-A local factory: `tier2_video_factory_v1.py`
- accepted dedicated Tier2 direct-image diagnostic: `direct_image_api_v1.py`, with the bounded
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

## Common wrong paths

- Do not revive `POST /api/run-pipeline`, old direct pipeline launchers, or supervised-only
  orchestration assumptions; the server route is quarantined.
- Do not treat historical `ALL_DATA` files as new intake truth; the canonical store is the
  append-only daily sidecar root under `headline_ingestion/data/intake/headline_sidecars/`.
- Do not call private `_eight_platform_*` functions as a new public entrypoint. Use the facade →
  production orchestrator boundary.
- Do not add publishing calls to the newsroom cycle. It returns a plan to
  `DurablePublicationCoordinator`.

## Validation routing

Backend tests live in `tests/` and usually mirror the implementation filename:

- store/runtime: `test_durable_operational_store_v1.py`, `test_daily_app_*`
- router: `test_nine_router_*`
- Tier2-A: `test_tier2_video_factory_v1.py`
- direct image: `test_direct_image_api_v1.py`
- CLI registration: `test_cli.py` plus feature-specific CLI tests

For the V1 decision path, start with `tests/test_rolling_x_newsroom_cycle_v1.py`,
`test_preselection_published_memory_breaking_wake_closeout_v1.py`,
`test_rolling_x_targeted_evidence_adapter_v1.py`, and `test_publication_coordinator_v1.py`.
Query `docs/codegraph/graph.json` for `covered_by`, `calls`, `newsroom_stage`, or a symbol ID.

Run the smallest relevant pytest selection. Any shared router/store/CLI edit also requires its
canonical regression file.
