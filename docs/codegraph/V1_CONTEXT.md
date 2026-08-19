# ContentOps V1 Current Context Map

Authority date: 2026-08-20

This is a curated implementation/discovery map, not product authority. Jim's latest instruction, root authority, fresh GitHub bytes, exact code/tests/evidence, and current runtime evidence outrank this map when they conflict.

## Current product state

`P0_1_ACCEPTED / P0_2_ACCEPTANCE_UNPROVEN`

Latest runtime evidence reports `FDA_G_SOAK_ACTIVE` on current master with healthy heartbeat/ingestion, one logical supervisor root from the Windows wrapper/child topology, `UNKNOWN_WRITE=0`, and all four existing V1 scheduled newsroom tasks still `PAUSED`. Re-observe runtime truth for any task that depends on current production state.

The P0-G1/G2 implementation slice is zero-write validated on its dedicated task branch. The next capability is:

`P0-G3 — ZERO-WRITE MULTI-MODE REPLAY + JIM/CHATGPT ACTUAL EDITORIAL ARTIFACT AUDIT`

## Canonical product flow

```text
one-click launcher
-> durable Daily App supervisor
-> continuous low-cost headline intake / housekeeping
-> rolling current candidate universe + published memory
-> routine window OR bounded material-event wake eligibility
-> story type + editorial mode selection
-> claim/mode-specific evidence and CC authority resolution
-> choose useful story or abstain
-> one strong editorial worker when warranted
-> factual/numeric/rights/reader-value validation
-> source-backed/purposeful media when useful
-> exact canonical Substack plan
-> exactly eight native derivative packages
-> owner-authorized canonical publish + destination-local derivative attempt/recovery
-> strict readback/reconciliation
-> real metrics + bounded growth/editorial learning
-> Daily App read model -> V5 control surface
```

No-publication remains valid. No publication quota exists.

## Editorial modes

Current root authority requires the canonical path to support:

- `BREAKING_BRIEF`
- `FOLLOW_UP_UPDATE`
- `STANDARD_NEWS_ANALYSIS`
- `CAPITAL_CHRONICLE_VIEW`
- `WHAT_THE_MARKET_IS_MISSING`
- `EVERGREEN_EXPLAINER`
- `DATA_OR_DOCUMENT_LENS`
- `WEEK_AHEAD_OR_WATCH`

Evidence burden follows claim scope and mode.

One exact authentic official primary source may be sufficient for a narrow attributed breaking fact when it directly proves the event. An issuer/party-authored official source establishes the existence and directly inspectable contents of its own announcement/filing/order/statement, not automatically disputed third-party allegations, misconduct, causality, or future outcomes.

Broader analytical/causal/numeric claims require the stronger public evidence and/or publication-authorized CC authority appropriate to the claim.

Quiet days may lower materiality or choose another mode; they may never lower factual truth, attribution, permission, rights, or numeric authority.

ContentOps may make clearly labeled qualitative editorial inference from accepted public evidence; that is ContentOps editorial judgment, not Core Analyzer authority, and may not be represented as a Core Analyzer conclusion or used to invent reserved proprietary numeric/forecast/probability/scenario/regime/valuation/decision truth.

## Canonical implementation path

```text
Start_ContentOps_Daily_App.cmd
  -> scripts/Start-ContentOpsDailyApp.ps1
  -> live_contentops.daily_app_launcher_v1
  -> python -m live_contentops.cli daily-app start
  -> ContentOpsDailyAppSupervisor
      -> continuous_headline_ingest_v1.run_ingestion_housekeeping_iteration
      -> recovery/readback/performance housekeeping
      -> routine due-window OR material-event trigger evaluation
          -> stable/idempotent editorial opportunity
          -> eight_platform_substack_first_pipeline_v1.run_rolling_x_newsroom_cycle
          -> ContentOpsProductionOrchestrator.execute
          -> _eight_platform_substack_first_pipeline_impl_v1._run_rolling_x_newsroom_cycle
              -> current rolling universe / prepared candidates
              -> apply_preselection_intelligence
              -> story type + editorial mode/capability selection
              -> RollingXTargetedEvidenceAdapter
              -> official_primary_source_locator_v1 / official_primary_evidence_loader_v1 where applicable
              -> publication-authorized CC/context resolution
              -> build_rolling_x_grounded_article_and_media
              -> bounded editorial cycle
              -> release candidate + platform-native package intents
              -> publication plan
          -> DurablePublicationCoordinator.publish_plan
              -> destination_transport_registry_v1
              -> FinalDailyAppTransportRuntime
              -> outbox -> dispatch -> strict readback -> reconciliation
          -> performance observation / bounded learning
          -> daily_app_ui_read_model_v1
          -> V5 DailyAppConsole
```

Use CodeGraph callers/callees around these seams before editing. Do not create parallel selection/evidence/publication/state/scheduler paths.

## Hot implementation areas for current task

### Supervisor / material-event wake

- `live_contentops/daily_app_supervisor_v1.py`
- existing material-event trigger/update-chain and operator-trigger state discovered by CodeGraph
- durable window/trigger/lease/idempotency tables and focused supervisor tests

Current task must prove the wake path under `NO_PUBLIC_WRITE`/shadow validation before any live activation. After owner-accepted canary, final product direction requires the bounded supervisor-owned material-event wake capability, but **live automatic public-write activation remains separately owner-gated; canary authority alone does not grant that trigger scope. Without the explicit wake grant, keep the path shadow-only.** This remains distinct from the four scheduled tasks and does not authorize a fifth task.

### Newsroom / selection

- `live_contentops/_eight_platform_substack_first_pipeline_impl_v1.py`
- `live_contentops/preselection_intelligence_v1.py`
- `live_contentops/editorial_portfolio_v1.py`
- `live_contentops/newsroom_assignment_scheduler_v1.py`
- relevant capability/story-mode registry code discovered by CodeGraph

### Evidence

- `live_contentops/rolling_x_targeted_evidence_adapter_v1.py`
- `live_contentops/official_primary_source_locator_v1.py`
- `live_contentops/official_primary_evidence_loader_v1.py`
- exact current evidence capability/profile contracts discovered from callers/tests

### Capital Chronicle authority

- `live_contentops/capital_chronicle_data_catalog_v1.py`
- current publication-evidence resolver/adapter path discovered by CodeGraph

Context/discovery remains non-public authority. Publication-authorized CC material requires exact story/consumer/use binding and may not be regenerated or widened.

### Article/editorial/media

- `live_contentops/rolling_x_grounded_article_media_builder_v1.py`
- current bounded editorial worker/revision seam discovered by CodeGraph

House-view/critical modes may express strong qualitative editorial judgment from accepted public evidence; models still receive zero factual/numeric/permission/public-write authority and may not present house inference as Core Analyzer output.

### Publication / recovery

- `live_contentops/publication_coordinator_v1.py`
- `live_contentops/destination_transport_registry_v1.py`
- `live_contentops/production_runtime_v1.py`
- publication-plan builder in the canonical rolling-X implementation

Current root direction supersedes the older blanket rule that any derivative non-readiness must veto canonical Substack. Target product semantics are canonical Substack first, then exactly eight independently gated derivative packages with destination-local hold/recovery and strict readback/reconciliation.

No live/public write is authorized merely by this context map.

## Focused test families

Use the smallest exact tests discovered by CodeGraph around changed seams, including as applicable:

- `tests/test_daily_app_supervisor_v1.py`
- `tests/test_daily_app_operator_trigger_v1.py`
- `tests/test_preselection_published_memory_breaking_wake_closeout_v1.py`
- `tests/test_rolling_x_newsroom_cycle_v1.py`
- `tests/test_rolling_x_targeted_evidence_adapter_v1.py`
- `tests/test_official_primary_evidence_loader_v1.py`
- `tests/test_rolling_x_evidence_viability_v1.py`
- `tests/test_rolling_x_grounded_article_media_builder_v1.py`
- `tests/test_rolling_x_v1_publishability_closure_v1.py`
- `tests/test_publication_coordinator_v1.py`
- `tests/test_daily_app_publication_lifecycle_v1.py`
- `tests/test_destination_identity_pinning_v1.py`

Current growth implementation must add focused coverage for official-primary narrow breaking, issuer-attribution boundaries, quiet-day mode fallback, house-view fact/opinion/Core-Analyzer separation, bounded material-event wake idempotency/spacing, and derivative-local readiness not vetoing canonical eligibility.

## Durable state authority

`live_contentops.durable_operational_store_v1.ContentOpsDurableStore` remains the single V1 state authority.

Important durable concerns include operating controls, work items, windows/scheduler ticks, leases/heartbeats, operator/material-event triggers, outbox messages, platform dispatches, readbacks, reconciliations, incidents, destination readiness, performance observations, and learning-policy versions.

Do not add a second store.

## Runtime/browser identities

- production DB: `A:\Capital Chronicle\Runtime\ContentOps\contentops_daily_app_v1.sqlite3`
- output root: `A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs`
- Capital Chronicle Main App read-only root: `A:\Capital Chronicle\Main App`
- Chrome `CapitalChronicleBot`, CDP 9222: ingestion only
- Edge `contentops-social-main`, CDP 9223: publication/media/readback and explicitly authorized observation only

These are identities, not permission to inspect credentials/session material.

## Current validation sequence

1. preserve the zero-write-validated P0-G1/G2 growth-first editorial, bounded wake, and canonical-first implementation;
2. run P0-G3 zero-write replay for official breaking + wake/no-wake, normal analysis, quiet day, and critical/opinion cases;
3. Jim/ChatGPT review actual article/package outputs;
4. fresh explicit owner grant for one real canary;
5. canonical Substack + exactly eight derivatives + strict readback/reconciliation + `UNKNOWN_WRITE=0`;
6. enable only the four existing scheduled tasks after accepted canary; separately obtain an explicit owner trigger-scope grant before activating automatic material-event public-write wakeups, otherwise keep that path shadow-only;
7. unattended/cold-start proof across scheduled operation plus the material-event trigger path at the highest scope currently authorized;
8. reproduce/close any real V5 build/runtime defect and complete screenshot-based visual acceptance.

## Stale traps

Do not route from:

- old branch/HEAD fast-forward instructions;
- P0-1 as a current next task;
- old manual-GO canary text as the immediate next implementation;
- blanket all-nine-ready-before-any-canonical-write semantics;
- “no yield work” language when used to block the current owner-directed growth-first behavior implementation;
- “material events can only ever wait for the next routine window” as final V1 behavior after the accepted canary;
- any wording that treats one-canary authorization as an implicit grant for future automatic material-event public writes;
- historical V6 launch paths or parallel schedulers;
- archived task handoffs/status snapshots.

Protected `v1.0` remains immutable at `6983bfb3ef300414b744f3f8f97ca81ff699348b`.
