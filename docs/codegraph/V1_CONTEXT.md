# ContentOps V1 Current Context Map

Authority date: 2026-08-24

This is a curated implementation/discovery map, not product authority. Jim's latest instruction, root authority, fresh GitHub bytes, exact code/tests/evidence, and current runtime evidence outrank this map when they conflict.

## Current product state

`SIMPLE_GEMINI_RUNTIME_RESET / ZERO_WRITE_HOST_CANARY_PENDING`

Current routine V1 no longer routes through Desktop Automations or the legacy rolling-X
evidence-ready/split-phase worker critical path. Current authority is the simple Gemini runtime:
current sidecars + published memory -> one Gemini selection -> <=6 deterministic selected-story
source requests -> one Gemini writer -> deterministic material-claim validation -> optional one
Gemini revision -> one qualified zero-write article -> exactly eight undispatched intents. Codex
runtime model calls are zero.

PR #19 locator/retrieval primitives, PR #20 article/package proof, and PR #29 validate-after concepts
are reusable donors. PR #30/#31 and native Desktop split-phase routing are historical evidence only.

## Canonical product flow

```text
local headline sidecars + published memory
-> ContentOpsProductionOrchestrator.run_v1_simple_gemini_newsroom
-> bounded 9Router/Gemini selection
-> BoundedPublicSecondaryEvidenceLoader on selected story only
-> bounded 9Router/Gemini article writer
-> deterministic source/claim validation
-> optional one Gemini revision
-> contentops.newsroom_qualified_article.v1
-> exactly eight UNDISPATCHED derivative intents
-> separately authorized DurablePublicationCoordinator
-> strict readback/reconciliation
```

Final target remains 5–8 useful published articles/day without filler.

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

Current routine implementation areas:

- `live_contentops/v1_simple_gemini_newsroom_v1.py` — selected-story simple runtime;
- `live_contentops/nine_router_llm_seam_v2.py` / `nine_router_ordered_model_router_v2.py` — bounded Gemini model authority;
- `live_contentops/public_secondary_evidence_loader_v1.py` — deterministic selected-story retrieval;
- `live_contentops/newsroom_production_day_v1.py` — provider-neutral qualified zero-write record;
- `live_contentops/production_orchestrator_v1.py` — canonical public operation boundary;
- `live_contentops/publication_coordinator_v1.py` and destination registry — sole later public-write path.

The legacy rolling-X monolith, Desktop PREPARE/COMPLETE handoff, broad ready-pool discovery, and
deficit catch-up loops remain available for historical evidence/compatibility only and do not route
current routine V1. Use CodeGraph for donor call paths, not to revive superseded ownership.

Next exact gate: one isolated zero-write current-sidecar host canary of the simple Gemini operation,
then a lightweight local scheduler using the same entrypoint. No live/public write is authorized.

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

1. preserve all accepted V1 foundation, the completed Italy canary, and failed 4/32 receipt;
2. reuse PR #19 provider-resilient batch discovery and PR #20's accepted article path;
3. preserve the four normalized matching prompts with all routine Automations paused;
4. next obtain exact zero-write enablement/calendar-time unattended proof;
5. follow with fresh V5 acceptance and separate routine public-write/final-product decisions.

## Stale traps

Do not route from:

- old branch/HEAD fast-forward instructions;
- P0-1 as a current next task;
- P0-G3 or the original daily-output/Automation bridge as the current next task;
- old manual-GO canary text as the immediate next implementation;
- any claim that the real Italy nine-surface canary is still pending;
- any claim that the 4/32 proof has never run;
- any claim that a perfect 4/32 proof gates one safe qualified article path;
- PR #20 article audit or native worker-return normalization as pending;
- PR #19 quota-efficient provider-resilient batch/tail discovery as unimplemented;
- the four host prompts as still mismatched or awaiting normalization;
- production-day accounting or bounded deficit recovery as an implementation gap;
- the four native V1 Automations as host-unproven;
- first-party locator/source-family or publisher-resolution closure as the next task;
- per-trigger 35-call discovery as an accepted routine production default;
- blanket all-nine-ready-before-any-canonical-write semantics;
- “no yield work” language when used to block the current owner-directed growth-first behavior implementation;
- “material events can only ever wait for the next routine window” as final V1 behavior after the accepted canary;
- any wording that treats one-canary authorization as an implicit grant for future automatic material-event public writes;
- historical V6 launch paths or parallel schedulers;
- archived task handoffs/status snapshots.

Protected `v1.0` remains immutable at `6983bfb3ef300414b744f3f8f97ca81ff699348b`.
