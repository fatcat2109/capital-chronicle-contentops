# Current Context — Capital Chronicle ContentOps

> [!IMPORTANT]
> GitHub remote evidence is repo-state authority. Jim's latest explicit product instruction is product-direction authority. Older plans/status are historical/reference material when they conflict with the current Final Daily App direction.

Authority date: 2026-08-10

## Current classifications

Historical accepted release:

`PASS_CONTENTOPS_V1_0_OPERATOR_ACCEPTED`

Current product-direction classification:

`CONTENTOPS_FINAL_DAILY_APP_V1_OWNER_DIRECTION`

Current North Star:

`docs/automation/CONTENTOPS_FINAL_DAILY_APP_V1_NORTH_STAR.md`

Current execution master plan:

`docs/automation/CONTENTOPS_FINAL_DAILY_APP_V1_MASTER_PLAN.md`

Future expansion retained but deferred until V1 freeze:

`CONTENTOPS_TIER2_PRO_VIDEO_FACTORY_OWNER_DIRECTION_V1`

Current completed runtime task:

`TASK_CONTENTOPS_FINAL_DAILY_APP_AUTONOMOUS_PUBLICATION_RUNTIME_AND_TRANSPORT_LOCK_V1`

Current exact next task:

`TASK_CONTENTOPS_FINAL_DAILY_APP_FINAL_V5_UI_BROWSER_QA_V1`

The Final Daily App now has one durable publication coordinator, one versioned transport
registry, exact pre-write outbox/attempt state, restart-safe UNKNOWN_WRITE recovery, real
read-only destination identity probes, Edge 9223 self-bootstrap, and one production launcher.
All nine Tier-1 destination identities were read-only verified on 2026-08-10. Production schema
v8 preserves the prior rows and production epoch. No public write occurred in the transport-lock
task. Provenance is under
`docs/automation/CONTENTOPS_FINAL_DAILY_APP_AUTONOMOUS_PUBLICATION_RUNTIME_AND_TRANSPORT_LOCK_V1/`.

## Current authority read order

1. `AGENTS.md`
2. this file
3. `docs/AI_BUILDER_BOOTSTRAP.md`
4. `docs/status/CURRENT_PRODUCT_DIRECTION_OVERLAY.md`
5. `docs/automation/CONTENTOPS_FINAL_DAILY_APP_V1_NORTH_STAR.md`
6. `docs/automation/CONTENTOPS_FINAL_DAILY_APP_V1_MASTER_PLAN.md`
7. `docs/status/CURRENT_FULL_AUTOMATION_FINAL_PRODUCT_STATUS.md` — historical/current repo evidence only where not superseded
8. `docs/status/CURRENT_PROJECT_STATUS.md` — historical/current repo evidence only where not superseded
9. `docs/status/current_project_status.json` — machine/history evidence; known stale routing fields do not override current overlay
10. `docs/automation/CONTENTOPS_FULL_AUTOMATION_FINAL_PRODUCT_INSTITUTIONAL_NORTH_STAR_V1/FINAL_PRODUCT_SCOPE_OVERLAY_V2.md`
11. `docs/automation/CONTENTOPS_FINAL_PRODUCT_SCOPE_CLOSEOUT_AND_LAUNCH_MASTER_PLAN_V1.md`
12. `docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/current_v6_master_plan.md`
13. `docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/next_task_pointer.md`
14. exact task implementation/tests/evidence.

Tier-2 plans are future reference only until V1 freeze unless Jim explicitly changes direction again.

## Protected historical release

`v1.0` remains immutable at release commit `6983bfb3ef300414b744f3f8f97ca81ff699348b` with the existing annotated tag.

Do not mutate, recreate, move, or retag it.

## Final V1 product definition

Jim now wants one Daily App that stays running 24/7 and autonomously owns routine ContentOps operation:

```text
always-on low-cost supervision
→ configured/learned editorial windows + material-event triggers
→ current newsroom decision
→ evidence
→ grounded article / SEO / source-backed media
→ review / bounded revision
→ platform-native packages
→ publish to exact READY configured destinations
→ strict readback / reconciliation / post management
→ real performance/search/subscriber observation where available
→ bounded timing / SEO / content / packaging learning
→ next window
```

The old Daily Live probation was a precursor vertical slice, not the final product.

No-publication remains valid. Do not create filler.

## Product boundary

Capital Chronicle owns analytical/numeric truth: market/economic analysis, micro/macro/global-macro reports, model calculations, scenarios/probabilities, Bayesian outputs, forecasts/regimes, numeric truth, realized outcomes, and analytical error attribution.

ContentOps owns newsroom/distribution/learning: intake, clustering/update chains, evidence/permission/freshness gates, ranking/selection/abstention, factual reporting, faithful Capital Chronicle transformation, writing/editing/SEO/source-backed visuals, packages, publication/readback/reconciliation/incidents, performance observations, and bounded packaging/selection/timing/SEO learning.

Engagement may never weaken or modify evidence, permissions, Capital Chronicle analysis, or numeric truth.

## Current verified technical baseline

Remote `master` before this authority rebase was:

`7a04932a67df1af4c3dd10e9cc435dff140e23c8`

That commit added the canonical rolling-X grounded article/media builder and policy-decision evidence closure.

The latest fresh canary still ended legitimate:

`NO_PUBLICATION / ALL_RANKED_CLUSTERS_EVIDENCE_BLOCKED`

The controlled zero-write slice proved the default builder can produce article + three media assets + semantic review + package/readiness under controlled accepted evidence.

## Known immediate defects

Before final V1 acceptance, fix:

1. `entities_topics` from editorial framing/X context must not be presented as facts copied from accepted evidence;
2. source-backed deterministic renders must not blanket-claim underlying source content as `capital_chronicle_owned` merely because Capital Chronicle owns the render/layout;
3. current Federal Reserve `official_policy` locator route returned 404 and needs a bounded correct first-party path;
4. fresh real evidence-viable production through the new default article/media builder remains unproven.

These are direct product blockers, not reasons to reopen broad hardening.

## Always-on architecture rule

An always-on supervisor/controller is authorized only as coordination around the existing canonical production boundary and durable store.

Preserve:

- `live_contentops.production_orchestrator_v1.ContentOpsProductionOrchestrator`;
- `live_contentops._eight_platform_substack_first_pipeline_impl_v1`;
- `live_contentops.eight_platform_substack_first_pipeline_v1`;
- `live_contentops/durable_operational_store_v1.py`;
- `ui/contentops_v5/`.

Do not create another newsroom, production pipeline, durable state store, scheduler authority, approval engine, publisher, provider gateway, dashboard, or analytical authority.

Always-on means cheap idle supervision, not continuous LLM calls.

## Current first task

`TASK_CONTENTOPS_FINAL_DAILY_APP_ALWAYS_ON_RUNTIME_VERTICAL_SLICE_V1`

Deliver:

- publishability provenance/rights correction;
- bounded Federal Reserve official-policy locator correction;
- persistent Daily App supervisor;
- deterministic bootstrap editorial-window policy;
- due-window idempotency/restart safety through the existing durable store;
- material-event wakeup seam reusing existing discovery metadata;
- one bounded supervisor e2e demo showing exactly-once canonical cycle execution and next-wake computation.

Expected next task after clean success:

`TASK_CONTENTOPS_FINAL_DAILY_APP_REAL_PERFORMANCE_OBSERVATION_AND_LEARNING_LOOP_V1`

## Operating modes

- `AUTONOMOUS_DEFAULT`
- `SUPERVISED_OPERATOR_GATE`
- `SHADOW_ONLY`
- `KILL_SWITCH`

Public writes only under exact deterministic READY gates.

## Persistent browser roles

- Chrome `CapitalChronicleBot`, CDP 9222: ingestion only.
- Edge `contentops-social-main`, CDP 9223: publication/media management/readback and explicitly supported read-only performance observation only.

Never inspect/export cookies, storage, tokens, credentials, or session databases.

Unknown writes:

`STOP RETRY → READ BACK → RECONCILE`

## Current router/model authority

Keep `CONTENTOPS_9ROUTER_ORDERED_MODEL_AUTHORITY_V2` and current bounded role-specific routing.

Do not redesign model authority due to transient provider degradation.

The always-on supervisor must not continuously probe LLMs while idle.

## V2

Do not start V2 now.

The previous early-parallel V2 unlock after one publishable package is superseded.

V2 Pro Video Factory begins after Final Daily App V1 acceptance/freeze unless Jim explicitly reprioritizes again.

## Safety

- no raw secret/session material;
- no unauthorized provider/browser/platform/public action;
- no fabricated numeric or analytical truth;
- no model/X/social factual authority;
- no synthetic documentary deception;
- no Capital Chronicle authority mutation;
- no protected-release mutation;
- no blind retry of unknown writes;
- no engagement-driven weakening of evidence/safety.
