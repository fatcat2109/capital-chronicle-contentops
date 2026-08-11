# Capital Chronicle ContentOps — Codex Root Contract

Authority date: 2026-08-11

This is the universal contract for Codex sessions in this repository. More specific
`AGENTS.md` files apply inside their directories and should contain local details rather than
repeat this file.

## Fresh-session path

Read only this compact path before locating task code:

1. `AGENTS.md`
2. `docs/codegraph/INDEX.md`
3. the nearest scoped `AGENTS.md` for the files you will touch
4. current product direction and next-task pointer only when product direction matters:
   - `docs/CURRENT_CONTEXT.md`
   - `docs/status/CURRENT_PRODUCT_DIRECTION_OVERLAY.md`
   - `docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/next_task_pointer.md`
5. exact implementation, tests, and evidence for the task

Read older master plans/status/evidence only when resolving a conflict, auditing history, or
the current authority files route you there. Generated context describes repository state; it
never replaces Jim's latest instruction or current authority documents.

## Authority

Repository-state authority, highest first:

1. fetched GitHub refs, commits, diffs, and exact bytes;
2. committed code, tests, schemas, and evidence;
3. current overlays/status/master plans;
4. durable redacted operational state and strict provider/platform readback;
5. logs and historical material.

Product-direction authority, highest first:

1. Jim's latest explicit instruction;
2. current committed direction overlay and next-task pointer;
3. older plans and archives.

Reconcile conflicts. Never let an older plan override a newer owner decision.

## Current product truth

- V1 is the canonical Final Daily App. FDA-G calendar-time soak continues independently and
  is not accepted yet.
- Canonical V1 backend/state/UI surfaces are `live_contentops/`,
  `live_contentops/durable_operational_store_v1.py`, the production orchestrator/pipeline, and
  `ui/contentops_v5/`.
- Tier2-A on master is an accepted local engineering slice awaiting/subject to visual product
  direction. It has no public-write authority.
- Tier2-B branch `task/tier2-b-remotion-multimodal-bakeoff-v1` is rejected/FAIL for visual
  product quality. Its engineering is reference only; do not merge or continue it.
- `TASK_CONTENTOPS_TIER2_DIRECT_IMAGE_API_REAL_SMOKE_AND_BAKEOFF_V1` is accepted
  `PASS_WITH_CAVEAT` at `a859d5ff82707842f59163e4ec5150b22fbe6b0e`. The dedicated direct
  `https://ai.api-cheap.site/v1/images/generations` boundary, using only
  `AI_API_CHEAP_API_KEY`, is proven end to end for `gpt-5.5`.
- `gpt-5.5` is the provisional V2 generated-illustration default pending future product
  evidence. Generated illustration is never factual or documentary authority.
- `wan2.7-image-pro` and `qwen-image-2.0` returned confirmed HTTP 400 responses on the tested
  contract and remain unresolved; they do not block V2.
- Branch `task/tier2-image-generation-9router-contract-correction-v1` at `8b043a5` remains
  rejected. Do not import its implementation or add `ai.api-cheap.site` to the generic 9Router
  adapter; the accepted direct-image boundary is dedicated and does not change 9Router text
  authority.
- The prior `LOCAL_9ROUTER_IMAGE_REGISTRY_AND_ROUTE_NOT_YET_PROVEN_END_TO_END` blocker is
  removed. The next V2 action is a fresh creative-system rebuild with stronger story/video
  suitability, less numeric narration, premium typography, richer scene-specific motion and
  chart transitions, generated illustrative assets, rights-aware real-person/entity imagery,
  improved voice/music, and stronger multimodal QA. Do not generate fake documentary images
  of real people. V2 still has zero public-write authority.

## Product boundary

Capital Chronicle main owns analytical/numeric authority: calculations, models, scenarios,
probabilities, forecasts, regimes, market/economic analysis, numeric truth, and realized-error
attribution.

ContentOps owns governed newsroom/media production: intake, clustering/update chains,
evidence/permission/freshness gates, selection/abstention, writing/editing/SEO, faithful
transformation, deterministic/source-backed media, packaging, publication control, readback,
reconciliation, incidents, and bounded performance learning.

ContentOps must not create independent analytical authority. Engagement never becomes factual
authority and never weakens evidence, permission, freshness, or safety gates.

## Protected and live boundaries

- `v1.0` is immutable at `6983bfb3ef300414b744f3f8f97ca81ff699348b` with annotated tag
  `v1.0`. Never rerun, mutate, move, or retag its accepted outputs/evidence.
- Do not create a second newsroom, scheduler authority, state store, approval engine, outbox,
  provider gateway, publication coordinator, dashboard, or analysis engine.
- Unknown writes: `STOP RETRY → READ BACK → RECONCILE`.
- No Tier-2/video public-write authority exists.
- Chrome `CapitalChronicleBot` on CDP 9222 is ingestion-only. Always reuse the exact
  operator-owned profile; never clone/reset/migrate/clean/replace it or fall back to another
  browser/profile.
- Edge `contentops-social-main` on CDP 9223 is publishing/media-management/readback only under
  canonical registry and readiness gates.
- Never inspect/export cookies, browser storage, tokens, credentials, private keys, or sessions.

## Safety

- never expose raw secrets, authorization headers, signed URLs, or session material;
- never fabricate numbers, analysis, claims, quotes, sources, events, or readback;
- never bypass evidence, permission, freshness, point-in-time, rights, or publication gates;
- never retry an ambiguous write/upload blindly;
- never treat generated media as documentary evidence;
- never mutate Capital Chronicle main-project authority;
- never perform provider/browser/platform/public actions without exact task authorization.

## Working discipline

- Fetch remote refs before branch-sensitive work. Start from fresh `origin/master` when asked.
- Preserve unrelated dirty/untracked files. Do not use destructive reset/checkout operations.
- Use `rg`/`rg --files` for search. If a repo-root `.codegraph/` exists, use
  `codegraph explore "<question or symbols>"` before grep/file-by-file exploration.
- Use `apply_patch` for hand edits.
- Prefer bounded vertical changes and focused validation proportional to risk.
- Stage explicit paths only; never `git add .` or `git add -A` in a mixed worktree.
- Do not claim full-suite/CI PASS unless it actually ran.
- Never merge or push to `master` unless explicitly directed.

## Deterministic context index

The generated repository map is under `docs/codegraph/`.

Regenerate after meaningful code, entrypoint, test, authority, or scoped-instruction changes:

```text
python scripts/generate_codex_context_index.py
```

Check staleness without writing:

```text
python scripts/generate_codex_context_index.py --check
```

The graph is descriptive, deterministic, and non-authoritative. Its metadata records the
source HEAD and a scoped source digest.
