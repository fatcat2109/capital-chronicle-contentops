# ContentOps — Current Next Task Pointer

Authority date: 2026-08-09

Current product-direction classification:

`CONTENTOPS_FINAL_DAILY_APP_V1_OWNER_DIRECTION`

Current authority overlay:

`docs/status/CURRENT_PRODUCT_DIRECTION_OVERLAY.md`

Current North Star:

`docs/automation/CONTENTOPS_FINAL_DAILY_APP_V1_NORTH_STAR.md`

Current execution master plan:

`docs/automation/CONTENTOPS_FINAL_DAILY_APP_V1_MASTER_PLAN.md`

## Current exact task

`TASK_CONTENTOPS_FINAL_DAILY_APP_ALWAYS_ON_RUNTIME_VERTICAL_SLICE_V1`

Mode:

`AUTONOMOUS_DEFAULT`

## User problem

ContentOps can execute individual canonical newsroom cycles, but Jim cannot yet start one application and leave it running 24/7 while the system autonomously owns scheduled/material newsroom decisions, publication lifecycle, later metrics, and later learning.

The latest canonical article/media implementation also has three known blockers that must not be carried into an always-on runtime:

1. editorial framing/X-derived `entities_topics` can be rendered as though they were accepted evidence facts;
2. source-backed deterministic renders blanket-declare `capital_chronicle_owned`, which may overclaim rights in underlying official source/excerpt content;
3. the Federal Reserve `official_policy` locator route used in the latest fresh canary returned HTTP 404.

## Capability to deliver now

One heavy bounded product task must deliver:

```text
correct article/media factual + rights provenance
+ bounded working Federal Reserve official-policy discovery
+ persistent Daily App supervisor
+ deterministic bootstrap EditorialWindowPolicy
+ exact due-window identity/idempotency
+ restart-safe execution through existing durable store
+ material-event wakeup seam using existing discovery metadata
+ canonical newsroom cycle invoked exactly once when due
+ terminal state persisted
+ next wake computed
```

The supervisor coordinates only. Actual newsroom/publication work remains under:

`live_contentops.production_orchestrator_v1.ContentOpsProductionOrchestrator`

and the existing canonical backend/public facade.

Do not create a second production pipeline, state store, scheduler authority, publisher, provider gateway, or analytics engine.

## Demo path

```text
start Daily App supervisor
→ load durable state + bootstrap EditorialWindowPolicy
→ detect one due window
→ call one canonical newsroom cycle
→ reach valid terminal result (publish or legitimate abstention)
→ persist window/cycle state
→ duplicate tick or restart does not duplicate cycle
→ compute next wake
→ idle without continuous provider calls
```

A legitimate `NO_PUBLICATION` is acceptable for this runtime proof.

## Explicitly deferred from this task

Do not implement the entire remaining V1 program at once.

After this vertical slice, the next planned heavy task is real performance observation + bounded learning.

This task does not require:

- final multi-platform metrics collectors;
- final adaptive schedule optimization;
- Search Console integration;
- final V5 UI rebuild;
- 5–10 day live soak;
- V2 video.

## Safety and authority

Capital Chronicle remains the only analytical/numeric authority.

ContentOps must not originate market snapshots, prior closes, valuation, forecasts, scenarios, probabilities, Bayesian outputs, regimes, or analytical economic/market truth.

X/social content remains discovery/editorial input only.

Public writes remain limited to exact dynamically verified canonical:

- `READY_AUTHENTICATED`
- `READY_NON_BROWSER_BINDING`

Unknown write:

`STOP RETRY → READ BACK → RECONCILE`

Browser roles remain:

- Chrome `CapitalChronicleBot`, CDP 9222: ingestion only;
- Edge `contentops-social-main`, CDP 9223: publication/media management/readback and only explicitly supported read-only performance observation.

Never inspect/export credential/session material.

## Stop rule

At the first NEW substantive product/runtime/safety blocker, stop immediately and report only:

- exact problem;
- last successful stage;
- network/provider actions;
- public/unknown-write state;
- what is needed to continue.

Do not create closure ceremony or repeated speculative correction loops.

## Expected next task after clean success

`TASK_CONTENTOPS_FINAL_DAILY_APP_REAL_PERFORMANCE_OBSERVATION_AND_LEARNING_LOOP_V1`

unless the supervisor run exposes a new substantive blocker.

V2 Pro Video Factory is deferred until Final Daily App V1 acceptance/freeze unless Jim explicitly reprioritizes.