# Capital Chronicle ContentOps — Codex Root Contract

Authority date: 2026-08-11

This is the compact repository-wide contract. A nearer `AGENTS.md` adds local routing without
overriding these boundaries.

## Fresh-session path

Read only:

1. `AGENTS.md`
2. `docs/codegraph/INDEX.md`
3. `docs/codegraph/V1_CONTEXT.md`
4. the nearest scoped `AGENTS.md`
5. exact task implementation, focused tests, and task evidence

Read `docs/CURRENT_CONTEXT.md`, the current product-direction overlay, and the next-task pointer
only when product direction matters. Read older plans/status/evidence only to resolve a concrete
conflict or audit history. Generated context is descriptive, never authority.

## Authority

Repository state, highest first: fetched GitHub refs/commits/diffs/exact bytes; committed code,
tests, schemas, and evidence; current authority/status; redacted runtime readback; historical
logs. Fetch before branch-sensitive work and reconcile conflicts.

Product direction, highest first: Jim's latest explicit instruction; current direction overlay
and next-task pointer; older plans. Never let stale routing override a newer owner decision.

## Current product

V1 is the canonical Final Daily App: one-click morning resume, continuous cheap zero-LLM X
intake, a rolling 24-hour newsroom, hierarchical assignment, published-memory/Capital Chronicle
read-only preselection intelligence, story/article-mode routing, targeted evidence, grounded
article/media, semantic review/revision, platform packages, canonical publication/readback, and
V5 projection. The 5–8 articles/day band is a portfolio target, never filler permission.

FDA-G calendar-time soak remains `SOAK_ACTIVE_AWAITING_GENUINE_CALENDAR_TIME_EVIDENCE`; it is not
accepted. The latest committed real production day correctly produced zero articles with
`ALL_RANKED_CLUSTERS_EVIDENCE_BLOCKED`. The next main V1 task is
`TASK_CONTENTOPS_V1_EVIDENCE_GATE_CALIBRATION_AND_REAL_PUBLICATION_UNBLOCK_V1`; do not implement
it during context/index work.

Tier2 is isolated and has no public-write authority. Rejected Tier2-B remains reference only.
`TASK_CONTENTOPS_TIER2_DIRECT_IMAGE_API_REAL_SMOKE_AND_BAKEOFF_V1` is accepted
`PASS_WITH_CAVEAT` at `a859d5ff82707842f59163e4ec5150b22fbe6b0e`: the dedicated direct
`https://ai.api-cheap.site/v1/images/generations` boundary using only
`AI_API_CHEAP_API_KEY` is proven end to end for `gpt-5.5`. `gpt-5.5` is the provisional V2
generated-illustration default pending future product evidence; generated illustration is never
factual or documentary authority. `wan2.7-image-pro` and `qwen-image-2.0` returned confirmed
HTTP 400 responses on the tested contract and remain unresolved without blocking V2.

The rejected `task/tier2-image-generation-9router-contract-correction-v1` implementation at
`8b043a5` remains reference only. Never import it or add `ai.api-cheap.site` to the generic
9Router adapter. The prior local 9Router image blocker is removed. The next V2 route is a
`FRESH V2 CREATIVE-SYSTEM REBUILD` with stronger story/video suitability, less numeric
narration, premium typography, richer motion/chart transitions, generated illustrative assets,
rights-aware real-person/entity imagery, improved voice/music, and stronger multimodal QA.

## Canonical boundaries

- production boundary: `production_orchestrator_v1.ContentOpsProductionOrchestrator`
- rolling-X facade/implementation: `eight_platform_substack_first_pipeline_v1.py` and
  `_eight_platform_substack_first_pipeline_impl_v1.py`
- controller: `daily_app_supervisor_v1.ContentOpsDailyAppSupervisor`
- durable authority: `durable_operational_store_v1.py`
- public-write owner: `publication_coordinator_v1.DurablePublicationCoordinator`
- destination map/readiness: `destination_transport_registry_v1.py`
- UI/read model: `ui/contentops_v5/` and `daily_app_ui_read_model_v1.py`
- model seam: `nine_router_llm_seam_v2.py`, ordered policy, then provider adapter

Capital Chronicle main owns analytical/numeric truth; ContentOps reads it through the canonical
read-only catalog/story-context seam. ContentOps owns governed newsroom, transformation,
packaging, publication control, readback, reconciliation, and bounded learning.

## Hard invariants

- One newsroom, durable store, scheduler authority, approval/outbox path, public-write owner,
  provider gateway, and dashboard. Extend canonical seams; do not create parallels.
- Chrome `CapitalChronicleBot` on CDP 9222 is ingestion-only and always reuses the exact
  operator-owned profile. Edge `contentops-social-main` on CDP 9223 is publication,
  media-management, readback, and authorized read-only performance observation only.
- Never inspect/export secrets, cookies, browser storage, tokens, credentials, or sessions.
- Unknown write: `STOP RETRY → READ BACK → RECONCILE`. Never weaken evidence, permission,
  freshness, rights, readiness, KILL_SWITCH, or publication gates.
- Capital Chronicle is read-only; never fabricate claims, numbers, sources, events, or readback.
- `v1.0` is immutable at `6983bfb3ef300414b744f3f8f97ca81ff699348b`; never rerun, mutate,
  move, or retag its accepted evidence.

## Working discipline

Preserve unrelated dirty/untracked work and Tier2 worktrees. Use CodeGraph first when a root
`.codegraph/` exists; otherwise use `rg`/`rg --files`. Use `apply_patch` for hand edits, focused
validation proportional to risk, and explicit staging paths only. Never `git add .`, force push,
or push/merge master without exact authorization. Runtime/provider/browser/public actions require
exact task authorization.

## Codegraph

If `.codegraph/` exists, run `codegraph explore "<symbol or question>"` before grep/file-by-file
inspection. The deterministic repository graph is `docs/codegraph/graph.json`; edge records state
their inference type. Check or regenerate after meaningful code, entrypoint, test, authority,
scoped-instruction, or V1-context changes:

```text
python scripts/generate_codex_context_index.py --check
python scripts/generate_codex_context_index.py
```

Runtime outputs, caches, raw headline data, generated media, vendor/build trees, screenshots, and
broad historical evidence are intentionally excluded.
