# Capital Chronicle ContentOps — AI Builder Bootstrap

Authority date: 2026-08-31
Status: `CURRENT_BUILDER_BOOTSTRAP`

Start at root `AGENTS.md`. GitHub evidence controls repository state. Jim's latest explicit instruction controls product direction.

## 1. Protected historical release

ContentOps `v1.0` remains immutable at `6983bfb3ef300414b744f3f8f97ca81ff699348b`. Do not mutate or retag it.

## 2. Mandatory current read path

Read in this order:

1. `AGENTS.md`
2. `docs/codegraph/INDEX.md`
3. `docs/automation/CONTENTOPS_CURRENT_AUTHORITY_AND_SUPERSESSION_MAP_V1.md`
4. `docs/automation/CONTENTOPS_CURRENT_STALE_DOCS_MANIFEST_V1.md`
5. `docs/automation/CONTENTOPS_CAPABILITY_ROUTED_HYBRID_EXECUTION_POLICY_V1.md`
6. `docs/automation/CONTENTOPS_FINAL_PRODUCT_NORTH_STAR_V3.md`
7. `docs/automation/CONTENTOPS_FINAL_PRODUCT_MASTER_PLAN_V3.md`
8. `docs/automation/CONTENTOPS_V1_POST_ACCEPTANCE_ACTIVATION_AUTHORITY_V1.md` for current V1 activation
9. `docs/automation/CONTENTOPS_V1_SIMPLE_GEMINI_RUNTIME_RESET_V1.md` for Simple mechanics
10. `docs/codegraph/V1_CONTEXT.md` or `docs/codegraph/V2_CONTEXT.md`
11. exact current lane pointer, including
    `docs/automation/CONTENTOPS_LIGHTWEIGHT_SPEECH_HIGHLIGHT_RELAY_CURRENT_EXECUTION_POINTER_V1.md`
    for Relay work
12. nearest scoped `AGENTS.md`
13. exact task implementation/tests/evidence.

Old V6 plans, old `CURRENT_*` status snapshots, `docs/status/current_project_status.json`, legacy Desktop Automation handoffs, and historical task folders are evidence/history only unless the current root spine explicitly promotes a concrete capability.

## 3. Current V1 owner state

Merge commit `db0befb8ad44f1080c67fcb801e5470ce7852369` records:

- `V1_FINAL_PRODUCT_ACCEPTED = TRUE`;
- routine V1 public-write/readback authority is granted for the accepted V1 path;
- V2 public-write authority remains zero unless separately granted.

Jim's 2026-08-31 direction also makes V1 activation/runtime completion the immediate priority,
recognizes the lightweight Speech Highlight Relay as a separate interim product, and pauses main V2
until an explicit later resumption. Relay work is not V2 progress and has zero public-write
authority.

Do not ask for a new V1 product-acceptance/public-write gate merely because an older document says it is pending.

## 4. Current product direction

V1 is an autonomous early-signal financial newsroom with a final operating target of:

`5–8 PUBLISHED ARTICLES per newsroom production day`

Candidate-level abstention is valid. Whole-day silent success below target without an exact hard external blocker is `DEGRADED_DAILY_OUTPUT_DEFICIT`. No filler and no weakening of truth/evidence/identity/readback safeguards.

Routine editorial ownership is `SIMPLE_GEMINI_RUNTIME`, not Desktop Automations.

Accepted Simple economics: <=32 candidates, one `vx/gemini-3.5-flash(high)` selector, one primary + <=2 fallbacks, shared <=6 deterministic source/provenance GETs, one writer, <=1 revision, <=3 logical Flash calls, zero Codex runtime model calls.

## 5. Product boundary

Capital Chronicle/Core Analyzer owns proprietary analytical/numeric truth: calculations, scenarios, probabilities, forecasts, regimes, valuations/decisions, paper records, and realized-outcome attribution.

ContentOps owns discovery, grounded research, story selection, writing/editing/SEO, media, packaging, publication/readback/reconciliation, performance observation, growth, and bounded learning.

Engagement never changes evidence, permissions, epistemic state, or Capital Chronicle analytical/numeric authority.

The Speech Highlight Relay may read governed source/event context and selectively reuse existing
media/caption/package seams, but it may not become another V1 editor, scheduler, durable store,
publisher/publication coordinator, browser owner, truth system, or model router. It ends at
`PUBLICATION_HOLD` absent an exact later grant. Main V2 remains paused.

## 6. Canonical architecture to preserve

Reuse, do not rebuild:

- Simple Gemini editorial path and PR #37 early-attributed-intelligence/epistemic-state contracts;
- `live_contentops.production_orchestrator_v1.ContentOpsProductionOrchestrator`;
- `live_contentops.publication_coordinator_v1.DurablePublicationCoordinator` as sole public-write owner;
- durable V1 store and destination registry;
- canonical Substack-first transports and strict readback/reconciliation;
- `UNKNOWN_WRITE = STOP RETRY -> READ BACK -> RECONCILE`;
- `ui/contentops_v5/` read model/UI foundation;
- historical Italy nine-surface canary as accepted publication-stack proof.

Do not create duplicate newsrooms, schedulers, stores, publishers, provider gateways, packagers, dashboards, or analytical engines.

## 7. Current activation gap

The repository implementation gaps listed in older revisions are closed: Simple-to-existing-
coordinator handoff, single routine owner, reconciled published-count accounting, and Simple
emergency-stop/process coverage are accepted. Current V1 work is host/runtime proof:

1. current-host read-only identity/readiness/recovery proof before the first new live write;
2. one strict live canary; and
3. four-window routine enablement only after clean reconciliation.

## 8. Browser role authority

- Chrome `CapitalChronicleBot`, CDP 9222: ingestion only.
- Microsoft Edge `contentops-social-main`, CDP 9223: publication/media/readback and explicitly authorized observation only.

Never inspect/export cookies, storage, credentials, tokens, or session databases.

## 9. Current activation sequence

1. current-host read-only activation preflight — zero public write;
2. one fresh live end-to-end V1 canary under already-granted authority;
3. if strictly reconciled with `UNKNOWN_WRITE=0`, enable the four routine windows toward 5–8 useful published articles/day;
4. permit a later separate Relay zero-write vertical slice only when it does not displace V1; and
5. keep main V2 paused until Jim explicitly resumes it.

No fifth routine task. Do not repeat the Italy canary merely to prove transport.

## 10. Execution discipline

Codex is the repo-native builder/debugger/host-proof lane. Inspect fresh remote refs, use CodeGraph, implement only the exact current gap, run focused tests plus one relevant E2E smoke, stage explicit paths, commit/push the task branch, and return evidence.

When the branch CodeGraph workflow creates a generated bot child commit, re-read the fresh remote branch head before audit or merge; never keep using the pre-refresh SHA as current truth.

Do not `git add .` or `git add -A`, force-push, mutate master directly, expose secrets/session material, weaken unknown-write handling, or expand V2 public-write/numeric/legal authority.
