# ContentOps V1 Current Context Map

Authority date: 2026-08-29

This is a curated implementation/discovery map, not product authority. Jim's latest instruction, root authority, fresh GitHub bytes, exact code/tests/evidence, and current runtime evidence outrank this map when they conflict.

## Current product state

`V1_FINAL_PRODUCT_ACCEPTED / ROUTINE_PUBLIC_WRITE_GRANTED / PUBLICATION_BRIDGE_AND_ACCOUNTING_NEXT`

Current routine editorial ownership is the Simple Gemini runtime, not Desktop Automations or the legacy rolling-X split-phase path.

Accepted editorial flow:

```text
current sidecars + canonical reconciled published memory
-> deterministic dedupe/sourceability ordering
-> <=32 candidates
-> one strict gemini-3.5-flash(high) selector
-> one primary + <=2 useful fallbacks
-> shared <=6 deterministic source/provenance GETs
-> exact report-truth/event-truth epistemic state
-> one Flash writer
-> deterministic material-claim/source/epistemic validation
-> optional one Flash revision without source expansion
-> one qualified article
-> exactly eight native derivative packages
```

Codex runtime model calls are zero. Exact canonical-X records may support only narrow relay-of-reporting or explicit market-rumor propositions under the accepted record-scoped provenance contract; underlying event truth remains unconfirmed unless separately proven.

## Current owner state

Merge commit `db0befb8ad44f1080c67fcb801e5470ce7852369` records:

- `V1_FINAL_PRODUCT_ACCEPTED = TRUE`;
- routine V1 public-write/readback authority granted for the accepted V1 path;
- V2 public-write authority remains zero unless separately granted.

Stale wording that still says routine V1 public-write/readback is ungranted or V1 acceptance is pending must not route current work.

## Canonical implementation path

Current routine implementation areas:

- `live_contentops/v1_simple_gemini_newsroom_v1.py` — accepted selected-story Simple runtime; currently materializes a qualified zero-write article plus eight preview-only pending-canonical-URL packages;
- `live_contentops/nine_router_llm_seam_v2.py` / `nine_router_ordered_model_router_v2.py` — bounded Gemini model seam;
- `live_contentops/v1_simple_evidence_resolver_v1.py` — shared-ledger source/provenance route arbitration;
- `live_contentops/v1_simple_epistemic_state_v1.py` — report/event proposition, provenance, risk, and reader labels;
- `live_contentops/public_secondary_evidence_loader_v1.py` plus accepted official-primary locator/loaders — deterministic evidence donors;
- `live_contentops/newsroom_production_day_v1.py` — production-day/accounting foundation; current Simple pacing still consumes qualified-count telemetry and must be separated from live reconciled-published counting;
- `live_contentops/v1_simple_gemini_scheduler_v1.py` — four-window local tick and deterministic slot checkpoints;
- `live_contentops/v1_simple_gemini_scheduler_process_v1.py` — persistent exactly-one-process Simple scheduler control;
- `live_contentops/production_orchestrator_v1.py` — current operation boundary;
- `live_contentops/publication_coordinator_v1.py` — sole durable public-write/readback/reconciliation owner;
- `live_contentops/destination_transport_registry_v1.py` — canonical destination transport/readiness registry;
- `live_contentops/durable_operational_store_v1.py` — single V1 durable state authority;
- `live_contentops/production_runtime_v1.py` / `daily_app_supervisor_v1.py` — current production composition, closed by merged PR #39 so routine ownership is explicitly `SIMPLE_GEMINI_RUNTIME`; Native Desktop/legacy rolling-X are compatibility-only/non-routing.

Use CodeGraph for exact call paths and affected tests. Do not revive superseded ownership merely because historical code still exists.

## Accepted capability reconciliation

### `CURRENTLY_PROVEN_AND_REUSE`

- PR #37 sourceability, early-attributed-intelligence, epistemic-state, publisher pinning, canonical-X relay/rumor static path, native eight-destination packaging, and X/Threads quality correction;
- Simple 32/6/3/1 economics and current article path;
- four-window scheduler mechanics plus persistent zero-write exactly-one-process host proof;
- PR #38 authority/static-safety closure and Simple emergency-stop/process coverage;
- PR #39 current single-owner production composition plus exact-head and master-push CI;
- durable V1 store;
- destination registry;
- `DurablePublicationCoordinator`, canonical Substack-first transports, strict readback/reconciliation, UNKNOWN-write recovery;
- historical Italy nine-surface publication canary as transport/reconciliation proof;
- V5 live read model/UI foundation.

### `HISTORICALLY_PROVEN_CURRENT_REVALIDATION_ONLY`

- current live destination/account/session readiness across the nine surfaces;
- current Edge 9223 publication profile/account identity;
- current production-store recovery/UNKNOWN state.

### `NEW_IMPLEMENTATION_GAP`

1. Simple qualified article/native package -> existing `DurablePublicationCoordinator` bridge;
2. strictly reconciled published-count accounting distinct from zero-write qualified-count telemetry.

Single-owner composition and Simple emergency-stop coverage are already merged/proven and must not route another implementation task.

### `CURRENT_HOST_RUNTIME_PROOF_REQUIRED`

Before the first new live write: production DB integrity/schema, no unresolved UNKNOWN/ambiguous dispatch/recovery backlog, exactly one production owner/process, Edge `contentops-social-main` CDP 9223, exact account/destination identity, and fresh nine-destination readiness. Do not inspect or expose secrets/session material.

### `SUPERSEDED_DO_NOT_REUSE`

- native Desktop Automations as routine V1 editorial owner;
- SDK/App-Server editorial fallback as routine critical path;
- legacy rolling-X monolith/broad evidence-ready pool as current owner;
- stale pre-acceptance owner-gate wording;
- pre-PR38 claims that Simple emergency-stop coverage is missing;
- pre-PR39 claims that current production ownership is ambiguous.

## Canonical product flow after activation closure

```text
four owner-locked routine windows
-> Simple editorial opportunity
-> accepted qualified article + epistemic state
-> sole existing DurablePublicationCoordinator
-> canonical Substack publish/readback with exact public /p/... identity
-> exactly eight derivative packages rematerialized against the real canonical URL
-> destination-local dispatch/readback/reconciliation
-> strictly reconciled published-count update
-> V5 read model/performance observation
```

No second store, publisher, scheduler, or packager.

## Runtime/browser identities

- production DB: `A:\Capital Chronicle\Runtime\ContentOps\contentops_daily_app_v1.sqlite3`
- output root: `A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs`
- canonical Simple scheduler root: `A:\Capital Chronicle\Runtime\ContentOps\simple_gemini_scheduler_v1`
- Capital Chronicle Main App read-only root: `A:\Capital Chronicle\Main App`
- Chrome `CapitalChronicleBot`, CDP 9222: ingestion only
- Edge `contentops-social-main`, CDP 9223: publication/media/readback and explicitly authorized observation only

These are identities, not permission to inspect credentials/session material.

## Focused test families for current activation work

Use CodeGraph to refine, but likely affected families include:

- `tests/test_v1_simple_gemini_newsroom_v1.py`
- `tests/test_v1_simple_gemini_scheduler_v1.py`
- scheduler-process tests around `v1_simple_gemini_scheduler_process_v1.py`;
- `tests/test_publication_coordinator_v1.py`
- `tests/test_daily_app_publication_lifecycle_v1.py`
- `tests/test_destination_identity_pinning_v1.py`
- `tests/test_eight_platform_substack_first_pipeline_v1.py`
- production-runtime/supervisor composition tests;
- operator-control/emergency-stop tests.

Do not run broad historical canaries merely to prove already-accepted capability.

## Current activation sequence

1. Simple -> existing publication coordinator bridge + published/reconciled accounting — no live write required for implementation tests;
2. current-host read-only activation preflight — zero public write;
3. one fresh live V1 end-to-end canary under already-granted authority, strictly reconciled across one canonical Substack article plus exactly eight derivatives;
4. if clean with `UNKNOWN_WRITE=0`, enable the four routine live windows toward 5–8 useful published articles/day.

Candidate-level abstention remains valid. A below-target live production day without an exact hard external blocker is `DEGRADED_DAILY_OUTPUT_DEFICIT`.

Protected `v1.0` remains immutable at `6983bfb3ef300414b744f3f8f97ca81ff699348b`.
