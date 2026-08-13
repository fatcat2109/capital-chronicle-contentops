# Capital Chronicle ContentOps — Codex Root Contract

Authority date: 2026-08-12

This is the compact repository-wide contract. A nearer `AGENTS.md` adds local routing without overriding these boundaries.

## Fresh-session path

Read only:

1. `AGENTS.md`
2. `docs/codegraph/INDEX.md`
3. `docs/codegraph/V1_CONTEXT.md` for V1 work, or the current V2 authority below for V2 work
4. the nearest scoped `AGENTS.md`
5. exact task implementation, focused tests, and task evidence

Read `docs/CURRENT_CONTEXT.md`, current product-direction overlays, and the V1/V2 execution pointers only when product direction matters. Read older plans/status/evidence only to resolve a concrete conflict or audit history. Generated context is descriptive, never authority.

## Authority

Repository state, highest first: fetched GitHub refs/commits/diffs/exact bytes; committed code, tests, schemas, and evidence; current authority/status; redacted runtime readback; historical logs. Fetch before branch-sensitive work and reconcile conflicts.

Product direction, highest first: Jim's latest explicit instruction; current direction/owner overlays and execution pointers; older plans. Never let stale routing override a newer owner decision.

## Current V1 product

V1 is the canonical Final Daily App. Current continuation authority is:

`docs/status/CONTENTOPS_V1_FULL_AUTOMATION_NINE_SURFACE_HANDOFF_V1.md`

Current V1 builder lane:

`TASK_CONTENTOPS_V1_FULL_AUTOMATION_NINE_SURFACE_LIVE_CLOSEOUT_V1`

Parent task remains:

`TASK_CONTENTOPS_V1_EVIDENCE_GATE_CALIBRATION_AND_REAL_PUBLICATION_UNBLOCK_V1`

Current V1 direction is throughput-first without weakening factual or publication safety: continuous preparation creates a small durable candidate set; a scheduled opportunity consumes that set, obtains minimum trustworthy evidence, makes one quality-writer call for ordinary reporting, runs deterministic hard checks, and advances after canonical Substack confirmation while derivatives recover asynchronously. Same-article 9/9, five-article acceptance, and mandatory ordinary semantic review are superseded ceremony. The broader 5–8 useful articles/day band remains a portfolio target, never filler permission. Read the V1 handoff for current evidence, integration state, and hard stops.

## Current V2 product authority

V2 is the owner-approved retention-native video/channel-growth lane and proceeds concurrently with V1 while remaining isolated from live V1 runtime/store/publication authority.

For V2, read in this order:

1. `docs/automation/CONTENTOPS_V2_RETENTION_NATIVE_VIDEO_FACTORY_NORTH_STAR_V2.md`
2. `docs/automation/CONTENTOPS_V2_RETENTION_NATIVE_VIDEO_FACTORY_MASTER_PLAN_V2.md`
3. `docs/automation/CONTENTOPS_V2_RETENTION_NATIVE_VIDEO_FACTORY_TASK_GRAPH_V2.md`
4. `docs/automation/CONTENTOPS_V2_RETENTION_NATIVE_VIDEO_FACTORY_CURRENT_EXECUTION_POINTER_V2.md`
5. `docs/automation/CONTENTOPS_V2_REMOTION_AGENT_SKILL_BASELINE_V1.md`
6. `docs/automation/CONTENTOPS_V2_FRESH_CHAT_HANDOFF_V1.md`
7. `docs/status/CONTENTOPS_V2_GPT56_CREATIVE_CODE_AND_ASSET_DENSITY_OWNER_OVERRIDE_V1.md` only for historical rationale/details already folded into V2 authority
8. `video/AGENTS.md`
9. exact task code/tests/evidence

The prior `NORTH_STAR_V1`, `MASTER_PLAN_V1`, `TASK_GRAPH_V1`, and `CURRENT_EXECUTION_POINTER_V1` are historical/reference once V2 documents exist. V2 controls where they conflict.

Current next V2 task:

`TASK_CONTENTOPS_TIER2_V2_GPT56_CREATIVE_CODE_ASSET_RICH_VIDEO_VERTICAL_SLICE_V1`

Required result:

`PASS_RETENTION_NATIVE_VERTICAL_SLICE_VISUAL_AUDIO_ACCEPTED`

The target is an autonomous evidence-governed media growth engine for YouTube hero/mid/long-form, YouTube Shorts, and TikTok native short-form. It should maximize repeatable qualified audience growth and breakout/trending potential without claiming virality can be guaranteed.

### Exact V2 creative-code model

Primary through the canonical 9Router seam for all three creative-author roles:

`new/gpt-5.6-sol-xhigh`

Roles:

- `V2_CREATIVE_EDITOR`
- `V2_MOTION_CODE_AUTHOR`
- `V2_CREATIVE_REVISION_AUTHOR`

GPT-5.6 authors presentation-layer screenplay/narration, shot/edit strategy, motion timing, and bounded per-shot creative code. Remotion is deterministic renderer/compiler, not creative authority. These three creative roles are hard-pinned to the exact singleton model with one initial attempt plus three same-model retries and zero fallback. Exhaustion is `BLOCKED_EXACT_CREATIVE_MODEL`.

The owner-updated generic 9Router quality pool is exact and ordered: `new/gpt-5.6-sol-xhigh`, `new/qwen3.8-max-preview`, `new/claude-opus-5`, `vx/gemini-3.1-pro-preview(high)`. `new/claude-fable-5` is not in the generic pool. Each generic model receives one initial attempt plus three same-model retries before fallback; the four-model global ceiling is 16 provider calls and three fallback transitions.

### Existing media/provider authority remains

- dedicated direct image boundary uses only `AI_API_CHEAP_API_KEY`;
- `gpt-5.5` remains provisional generated-illustration default;
- generated imagery is illustrative only, never factual/documentary authority;
- current rights/provenance/hash controls remain;
- real-person documentary media must be real and rights-cleared;
- current voice/TTS abstraction and local/Kokoro baseline remain;
- current music/SFX/mastering infrastructure remains unless a later dedicated task proves a better path.

V2 should increase asset richness through a large rights-safe candidate universe and many purposeful selected visual states rather than provider churn or random asset spam.

### Current Remotion reference baseline

Primary technical reference is official:

`remotion-dev/skills@b12104ef5f1b1ca2ca5590fcc7c1804fbc85556f`

Community Remotion skills are selective craft reference only and never override official APIs, repo safety, V2 truth/rights rules, or Jim's quality direction.

### Rejected V2 creative branches

Reference only; do not merge or continue their creative designs:

- `task/tier2-b-remotion-multimodal-bakeoff-v1`;
- `task/tier2-v2-creative-system-rebuild-v1` at `d231b54e026570442d9fd9269b61e55c3de31d21` — `REJECTED_CREATIVE_PRODUCT_REFERENCE_ONLY`;
- `task/tier2-v2-retention-native-video-factory-vertical-slice-v1` at `b6f5002903fba65a668506e4ca38ae61b907ab18` — `FAIL_CREATIVE_MOTION_ARCHITECTURE / REJECTED_CREATIVE_PRODUCT_REFERENCE_ONLY`;
- `task/tier2-image-generation-9router-contract-correction-v1` at `8b043a5` — rejected provider-contract implementation.

## Canonical boundaries

- production boundary: `production_orchestrator_v1.ContentOpsProductionOrchestrator`
- rolling-X facade/implementation: `eight_platform_substack_first_pipeline_v1.py` and `_eight_platform_substack_first_pipeline_impl_v1.py`
- controller: `daily_app_supervisor_v1.ContentOpsDailyAppSupervisor`
- durable authority: `durable_operational_store_v1.py`
- public-write owner: `publication_coordinator_v1.DurablePublicationCoordinator`
- destination map/readiness: `destination_transport_registry_v1.py`
- UI/read model: `ui/contentops_v5/` and `daily_app_ui_read_model_v1.py`
- model seam: `nine_router_llm_seam_v2.py`, ordered policy, then provider adapter

Capital Chronicle main owns analytical/numeric truth; ContentOps reads it through the canonical read-only catalog/story-context seam. ContentOps owns governed newsroom, transformation, packaging, publication control, readback, reconciliation, and bounded learning.

## Hard invariants

- One newsroom, durable store, scheduler authority, approval/outbox path, public-write owner, provider gateway, and dashboard. Extend canonical seams; do not create parallels.
- Chrome `CapitalChronicleBot` on CDP 9222 is ingestion-only and always reuses the exact operator-owned profile. Edge `contentops-social-main` on CDP 9223 is publication/media-management/readback and explicitly authorized read-only observation only.
- Never inspect/export secrets, cookies, browser storage, tokens, credentials, or sessions.
- Unknown write: `STOP RETRY → READ BACK → RECONCILE`.
- Never weaken evidence, permission, freshness, rights, readiness, KILL_SWITCH, or publication gates.
- Capital Chronicle is read-only; never fabricate claims, numbers, sources, events, or readback.
- Generated real-person documentary imagery is forbidden.
- V2 has zero video public-write authority unless the exact later task and Jim explicitly grant it.
- `v1.0` is immutable at `6983bfb3ef300414b744f3f8f97ca81ff699348b`; never rerun, mutate, move, or retag its accepted evidence.

## Working discipline

Preserve unrelated dirty/untracked work and concurrent V1/V2 worktrees. Use CodeGraph first when a root `.codegraph/` exists; otherwise use `rg`/`rg --files`. Use focused validation proportional to risk and explicit staging paths only. Never `git add .`, force push, or merge/push master without exact authorization. Runtime/provider/browser/public actions require exact task authorization.

Codex is the repository builder. Task prompts should be lean and high-signal; Codex should use committed authority and CodeGraph rather than repeated chat history.

## Local synchronization after direct GitHub authority writes

Direct ChatGPT GitHub writes update remote `master`, not the user's Windows checkout automatically.

Before implementation, a builder must:

1. inspect local status and preserve unrelated work;
2. fetch origin;
3. verify fresh `origin/master` against GitHub;
4. avoid hard-resetting dirty/unrelated work;
5. create a clean dedicated task worktree/branch from fresh master, or safely fast-forward a clean canonical checkout;
6. regenerate/check CodeGraph when authority changed directly on GitHub;
7. require `CODEGRAPH_CURRENT` before implementation commit.

## CodeGraph

If `.codegraph/` exists, run `codegraph explore "<symbol or question>"` before broad grep/file-by-file inspection. The deterministic repository graph is `docs/codegraph/graph.json`; generated context is descriptive, not product authority.

Runtime outputs, caches, raw headline data, generated media, vendor/build trees, screenshots, and broad historical evidence are intentionally excluded.
