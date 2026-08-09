# ContentOps — Current Next Task Pointer

Authority date: 2026-08-09

Current product-direction classification:

`CONTENTOPS_DAILY_LIVE_V1_PUBLISHABILITY_GATE_AND_PARALLEL_V2_OWNER_DIRECTION`

Current authority overlay:

`docs/status/CURRENT_PRODUCT_DIRECTION_OVERLAY.md`

Current North Star:

`docs/automation/CONTENTOPS_DAILY_LIVE_V1_NORTH_STAR.md`

Current execution master plan:

`docs/automation/CONTENTOPS_DAILY_LIVE_V1_ACCELERATED_LAUNCH_MASTER_PLAN.md`

## Current exact task

`TASK_CONTENTOPS_V1_CANONICAL_GROUNDED_ARTICLE_MEDIA_BUILDER_AND_PUBLISHABILITY_CANARY_V1`

Mode:

`AUTONOMOUS_DEFAULT`

## Owner decision

The publishability gate is not reduced.

The latest canonical audit proved a missing core subsystem rather than a small wiring defect:

- `run_rolling_x_newsroom_cycle(...)` exposes `article_builder=None` by default;
- the production orchestrator does not bind a default article builder;
- after an evidence PASS, the canonical cycle deterministically stops with `STORY_ARTICLE_VISUAL_BUILDER_UNAVAILABLE` when no callable builder is supplied;
- existing article/media builders are story-family-specific and are not a reusable rolling-X builder.

Therefore the owner explicitly authorizes building **one canonical grounded article + media builder** for rolling-X Daily Live. This builder is the Tier-1 article/media pipeline, not a second newsroom or second publication system.

Do not redefine success to stop before article/review/package generation merely to unlock V2.

## Required capability

Deliver the missing canonical transformation:

```text
accepted ranked cluster
+ exact story type / article mode
+ validated evidence receipt
+ Capital Chronicle authority where required
→ grounded article + SEO metadata
→ source-backed deterministic media assets
→ existing semantic reviewer / bounded reviser
→ existing native-package builder
→ existing destination readiness / publication boundary
```

The builder must consume only governed evidence/authority already accepted by the canonical cycle. X/social content remains discovery/priority input and cannot become factual evidence.

The builder must never originate Capital Chronicle analytical/numeric authority.

## Builder doctrine

Prefer one reusable contract-driven builder over story-specific prose functions.

The builder should use:

- story type + article mode;
- exact evidence capabilities and source documents;
- evidence/source hashes and timestamps;
- authorized numeric claims only when supplied by governed evidence/Capital Chronicle authority;
- existing 9Router role/provider authority for bounded article generation where useful;
- deterministic source-backed visual primitives for claims that can be represented without invented data.

Media may include claim-bound document excerpts, timelines, source cards, entity/decision fact cards, maps only when exact governed geography exists, and deterministic charts only when exact governed numeric series exists.

Do not manufacture a chart or image merely to satisfy a visual count. If the release contract requires three assets, produce three distinct source-backed assets only when their underlying evidence supports them; otherwise fail closed.

Do not create:

- a second article pipeline;
- a second reviewer;
- a second package builder;
- a second publisher;
- generic web research;
- licensed-news breadth;
- independent ContentOps market/macro analysis.

## Publishability closure after builder exists

After focused controlled proof of the builder, continue the existing publishability task rather than opening another architecture program:

1. close only evidence-contract/source-path gaps directly justified by recent production, including `policy_decision + straight_news` if still required;
2. keep analytical modes bound to Capital Chronicle authority;
3. allow deterministic evidence-reachability metadata to inform ranking without granting factual/evidence/publication authority;
4. run one fresh canonical publishability canary.

## V2 unlock gate

V2-A is unlocked when one fresh canonical run proves:

```text
fresh current universe
→ accepted ranking
→ exact story/article mode
→ evidence PASS
→ grounded article
→ semantic review PASS
→ source-backed visuals/native package
→ destination readiness evaluated
```

A successful public write/readback is preferred when exact `READY_*` gates pass, but a fully publishable package reaching the live gate is sufficient when destination readiness is the only remaining external blocker.

After this gate:

```text
V1 genuine Daily Live probation continues
║
╠→ social destinations continue in parallel
╚→ V2-A Pro Video Factory may begin in parallel
```

## Safety and authority

Capital Chronicle remains the only analytical/numeric authority.

ContentOps must not originate market snapshots, prior closes, valuation, forecasts, scenarios, probabilities, Bayesian outputs, regimes, or analytical economic/market truth.

Public writes remain limited to dynamically verified canonical `READY_AUTHENTICATED` / `READY_NON_BROWSER_BINDING` destinations.

Unknown write:

`STOP RETRY → READ BACK → RECONCILE`

Persistent browser roles remain:

- Chrome `CapitalChronicleBot`, CDP `9222`: ingestion only;
- Edge `contentops-social-main`, CDP `9223`: publication/readback only.

Never inspect/export credential/session material.

## Fast-ship stop rule

At the first NEW substantive problem, stop immediately and report only the exact problem, last successful stage, network/provider actions, public/unknown-write state, and what is needed to continue.

Do not create closure ceremony, audit-of-audit loops, broad full-suite runs, or repeated speculative correction loops.