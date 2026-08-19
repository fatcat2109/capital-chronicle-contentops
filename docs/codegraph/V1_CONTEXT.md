# ContentOps V1 Current Context Map

Authority date: 2026-08-20

This is a curated implementation/discovery map, not product authority. Jim's latest instruction, root authority, fresh GitHub bytes, exact code/tests/evidence, and current runtime evidence outrank this map when they conflict.

## Current product state

`P0_1_ACCEPTED / P0_2_ACCEPTANCE_UNPROVEN`

Latest runtime evidence reports `FDA_G_SOAK_ACTIVE` on current master with healthy heartbeat/ingestion, one logical supervisor root from the Windows wrapper/child topology, `UNKNOWN_WRITE=0`, and all four existing V1 newsroom tasks still `PAUSED`. Re-observe runtime truth for any task that depends on current production state.

The next product implementation is not passive waiting for a perfect story. It is:

`P0-G1 + P0-G2 — GROWTH-FIRST EDITORIAL SPECTRUM + CANONICAL-FIRST DISTRIBUTION`

## Canonical product flow

```text
one-click launcher
-> durable Daily App supervisor
-> continuous low-cost headline intake / housekeeping
-> rolling current candidate universe + published memory
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

One exact authentic official primary source may be sufficient for a narrow attributed breaking fact when it directly proves the event. Broader analytical/causal/numeric claims require the stronger public evidence and/or publication-authorized CC authority appropriate to the claim.

Quiet days may lower materiality or choose another mode; they may never lower factual truth, attribution, permission, rights, or numeric authority.

## Canonical implementation path

```text
Start_ContentOps_Daily_App.cmd
  -> scripts/Start-ContentOpsDailyApp.ps1
  -> live_contentops.daily_app_launcher_v1
  -> python -m live_contentops.cli daily-app start
  -> ContentOpsDailyAppSupervisor
      -> continuous_headline_ingest_v1.run_ingestion_housekeeping_iteration
      -> recovery/readback/performance housekeeping
      -> due editorial opportunity
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

Use CodeGraph callers/callees around these seams before editing. Do not create parallel selection/evidence/publication/state paths.

## Hot implementation areas for current task

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

House-view/critical modes may express strong judgment; models still receive zero factual/numeric/permission/public-write authority.

### Publication / recovery

- `live_contentops/publication_coordinator_v1.py`
- `live_contentops/destination_transport_registry_v1.py`
- `live_contentops/production_runtime_v1.py`
- publication-plan builder in the canonical rolling-X implementation

Current root direction supersedes the older blanket rule that any derivative non-readiness must veto canonical Substack. Target product semantics are canonical Substack first, then exactly eight independently gated derivative packages with destination-local hold/recovery and strict readback/reconciliation.

No live/public write is authorized merely by this context map.

## Focused test families

Use the smallest exact tests discovered by CodeGraph around changed seams, including as applicable:

- `tests/test_rolling_x_newsroom_cycle_v1.py`
- `tests/test_rolling_x_targeted_evidence_adapter_v1.py`
- `tests/test_official_primary_evidence_loader_v1.py`
- `tests/test_rolling_x_evidence_viability_v1.py`
- `tests/test_preselection_published_memory_breaking_wake_closeout_v1.py`
- `tests/test_rolling_x_grounded_article_media_builder_v1.py`
- `tests/test_rolling_x_v1_publishability_closure_v1.py`
- `tests/test_publication_coordinator_v1.py`
- `tests/test_daily_app_publication_lifecycle_v1.py`
- `tests/test_destination_identity_pinning_v1.py`

Current growth implementation must add focused coverage for official-primary narrow breaking, quiet-day mode fallback, house-view fact/opinion separation, and derivative-local readiness not vetoing canonical eligibility.

## Durable state authority

`live_contentops.durable_operational_store_v1.ContentOpsDurableStore` remains the single V1 state authority.

Important durable concerns include operating controls, work items, windows/scheduler ticks, leases/heartbeats, operator triggers, outbox messages, platform dispatches, readbacks, reconciliations, incidents, destination readiness, performance observations, and learning-policy versions.

Do not add a second store.

## Runtime/browser identities

- production DB: `A:\Capital Chronicle\Runtime\ContentOps\contentops_daily_app_v1.sqlite3`
- output root: `A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs`
- Capital Chronicle Main App read-only root: `A:\Capital Chronicle\Main App`
- Chrome `CapitalChronicleBot`, CDP 9222: ingestion only
- Edge `contentops-social-main`, CDP 9223: publication/media/readback and explicitly authorized observation only

These are identities, not permission to inspect credentials/session material.

## Current validation sequence

1. implement growth-first editorial modes/evidence/canonical-first lifecycle with no public writes;
2. zero-write replay official breaking, normal analysis, quiet day, and critical/opinion cases;
3. Jim/ChatGPT review actual article/package outputs;
4. fresh explicit owner grant for one real canary;
5. canonical Substack + exactly eight derivatives + strict readback/reconciliation + `UNKNOWN_WRITE=0`;
6. enable only the four existing tasks after accepted canary;
7. unattended/cold-start proof;
8. reproduce/close any real V5 build/runtime defect and complete screenshot-based visual acceptance.

## Stale traps

Do not route from:

- old branch/HEAD fast-forward instructions;
- P0-1 as a current next task;
- old manual-GO canary text as the immediate next implementation;
- blanket all-nine-ready-before-any-canonical-write semantics;
- “no yield work” language when used to block the current owner-directed growth-first behavior implementation;
- historical V6 launch paths or parallel schedulers;
- archived task handoffs/status snapshots.

Protected `v1.0` remains immutable at `6983bfb3ef300414b744f3f8f97ca81ff699348b`.
