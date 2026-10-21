# Capital Chronicle ContentOps — Final Product Master Plan V3

Authority date: 2026-10-20
Status: `CURRENT_ROOT_EXECUTION_MASTER_PLAN / V1_ACCEPTED / ACTIVATION`

North Star: `docs/automation/CONTENTOPS_FINAL_PRODUCT_NORTH_STAR_V3.md`
Current V1 activation authority: `docs/automation/CONTENTOPS_V1_POST_ACCEPTANCE_ACTIVATION_AUTHORITY_V1.md`
Authority map: `docs/automation/CONTENTOPS_CURRENT_AUTHORITY_AND_SUPERSESSION_MAP_V1.md`

## 0. Locked objective

Operate one coherent autonomous V1 growth newsroom at 5–8 useful published articles per production day, then continue one isolated V2 retention-native video lane without rebuilding accepted systems, weakening truth, or confusing missing current-host proof with missing implementation.

Current owner state:

- `V1_FINAL_PRODUCT_ACCEPTED = TRUE`;
- routine V1 public-write/readback authority is granted for the accepted V1 path;
- V2 public-write authority remains zero unless separately granted.

The repository merge commit `db0befb8ad44f1080c67fcb801e5470ce7852369` records the V1 grant.

Final V1 operating target:

`5–8 PUBLISHED ARTICLES per newsroom production day`

Historical zero-write throughput benchmark:

`4 QUALIFIED ZERO-PUBLIC-WRITE ARTICLES / 32 DERIVATIVE INTENTS per newsroom production day`

That benchmark remains telemetry/economics evidence only; it is not a renewed launch or acceptance gate.

A live day below target without an exact hard external blocker is `DEGRADED_DAILY_OUTPUT_DEFICIT`. Candidate-level abstention remains valid; filler and weaker evidence are forbidden.

## 1. Current V1 architecture

Routine V1 target ownership is `NATIVE_CODEX_DESKTOP`, with the owner-approved three-stage method:
Luna/Terra MAX filters X headlines; `gpt-6.1-sol / low` (Light) selects content and prepares data;
`gpt-6.1-sol / max` writes the article and SEO/house-style package, including a bounded useful revision.
Read `docs/automation/CONTENTOPS_NATIVE_DESKTOP_EDITORIAL_ROLE_POLICY_V2.md` for exact role,
source/tool, style and checkpoint rules. This target supersedes the earlier Sol-low-only method;
the Goal24 isolated proof remains evidence for its older configuration, not this complete pipeline.
Reuse MainReportFeed/current intake, canonical publication memory, reviewed retained research,
evolving story/revision context, <=32 candidates, <=3 admissions and <=6 source requests.
Existing source/claim/epistemic checks and the native eight-channel compiler remain authoritative.
There is no Gemini/9Router, SDK/App-Server, headless or paid API model fallback.

The existing four App tasks own routine scheduling; existing window/day/slot IDs, bounded
catch-up, store/outbox/lease and sole DurablePublicationCoordinator are reused. Legacy Simple
scheduler/start paths are non-routing in target source. Bulk X CDP ingestion remains unchanged;
Neo is the browser path for research and prepared browser-only destination handoffs. Existing
Telegram/Discord/Meta/Threads/LinkedIn API transports remain channel-specific.

Current engineering/deployed state: **PAUSED_NOT_DEPLOYED**. Host schedules, production pause,
store and deployed bytes were not changed by this migration. Native manual proof is isolated.
No current configuration grants activation or public writes. Historical Simple and old Desktop
proofs establish only their exact epochs; do not rebuild their accepted deterministic components.
See `docs/automation/CONTENTOPS_NATIVE_DESKTOP_EDITORIAL_RUNTIME_V1.md` for the supported operation,
exact paused rollout, truthful telemetry, bound native Neo request/return/readback loop and separate activation boundary.


## 2. Historical accepted foundation — reuse components, preserve proof

### V1

`CURRENTLY_PROVEN_AND_REUSE`:

- current headline intake, published-memory/dedupe, update-chain and production-day foundations;
- Simple Gemini selection/writer/revision path and PR #37 Editorial Growth Edge;
- sourceability ordering, first-party/reputable-secondary retrieval donors, publisher pinning, exact epistemic-state adapter;
- canonical-X relay/explicit-rumor zero-GET branch under record-scoped provenance;
- native exactly-eight derivative compiler and X/Threads quality correction;
- four-window Simple scheduler mechanics and persistent exactly-one-process zero-write host proof;
- merged PR #38 post-acceptance authority/static-safety closure plus emergency-stop/process coverage for Simple;
- merged PR #39 single routine production-owner composition: current Final Daily App -> `SIMPLE_GEMINI_RUNTIME`, with Native Desktop/legacy rolling-X compatibility-only and non-routing;
- corrected routine Simple-to-durable publication bridge on the actual persistent scheduler path: deterministic slot/work-item identity, immutable/reconstructable plan, recover-before-fresh-work, no-model crash resume, duplicate-terminal idempotency, unresolved-backlog fail-closed behavior, and existing canonical-first coordinator/native compiler reuse;
- durable V1 store, destination registry, canonical Substack-first publication coordinator, destination transports, strict readback/reconciliation, UNKNOWN-write recovery;
- real historical Italy one-Substack-plus-eight-derivatives canary with all nine reconciled and `UNKNOWN_WRITE=0`;
- V5 live read model/UI foundation.

The corrected bridge is repository/CI proof only. It does not claim fresh current-host account/session/readiness or a new real public publication. It also does not create a new standalone activation or canary prerequisite.

Do not rebuild any of the above merely because current-host state must be revalidated.

### V2

Current V2 master keeps its existing free-form rendering/package/publication-control foundation. V2 is isolated from V1 runtime/store/browser/publication authority and has no public-write grant.

## 3. Historical proof that requires only current revalidation

`HISTORICALLY_PROVEN_CURRENT_REVALIDATION_ONLY`:

- live readiness/account/session state for Substack, Telegram, Discord, X, LinkedIn, Facebook Page, Instagram Business, Threads, and YouTube Community;
- publication profile/account identity on Edge CDP 9223;
- exact host state around the canonical production store and unresolved recovery/UNKNOWN-write backlog.

Historical success proves capability; it does not prove today's login/session/token/readiness state.

## 4. Current native migration scope

1. Implement and independently audit the native Desktop migration on PR90, preserving Goal20–23 evidence.
2. Reuse Goal25's isolated Luna-MAX -> Sol-Light -> Sol-MAX flow and byte-stable restart; retain the exact dated source, eight native previews and readback limits in its owning checkpoint.
3. Preserve the exact paused four-task rollout and per-channel API/Neo setup/readback handoff.
4. After separate audit/deployment authority, apply the one documented activation transition with pause release last.
5. Observe natural runtime separately; 5–8/day reliability is unproven until actual reconciled output establishes it.

No production activation, public write, pause release, self-merge or deployment is part of Goal25.


## 5. Live-write hard boundary (no universal ceremony)

At every actual live write, the existing owner must fail closed on:

- production DB integrity/schema;
- unresolved `UNKNOWN_WRITE`, ambiguous `DISPATCH_ATTEMPT_STARTED`, or recovery backlog;
- duplicate routine production ownership/process;
- Neo exact account and native executor identity; Edge 9223 remains historical deployed provenance;
- exact current public account/destination identities;
- destination readiness under existing contracts;
- secret/session material exposure.

These invariants are checked at the live boundary. A standalone read-only activation preflight is
conditional diagnostics only when current evidence materially raises one of them.

Chrome `CapitalChronicleBot` CDP 9222 remains ingestion-only.

## 6. Current activation roadmap

1. Implement and independently audit the native Desktop migration on PR90, preserving Goal20–23 evidence.
2. Reuse Goal25's isolated Luna-MAX -> Sol-Light -> Sol-MAX flow and byte-stable restart; retain the exact dated source, eight native previews and readback limits in its owning checkpoint.
3. Preserve the exact paused four-task rollout and per-channel API/Neo setup/readback handoff.
4. After separate audit/deployment authority, apply the one documented activation transition with pause release last.
5. Observe natural runtime separately; 5–8/day reliability is unproven until actual reconciled output establishes it.

No production activation, public write, pause release, self-merge or deployment is part of Goal25.


## 7. Definition of operationally ready V1

The owner product-acceptance decision is already true. Operational activation is ready when:

1. the corrected Simple->publication bridge remains current and tested;
2. live daily-output accounting counts strictly reconciled published canonical articles, not merely qualified zero-write articles;
3. actual live-write boundary checks keep single-owner/emergency-stop, identity, readiness,
   readback, and UNKNOWN invariants fail-closed;
4. natural routine windows run and produce measured conversion/publication evidence;
5. observed blockers are repaired toward the accepted 5–8/day target.

Do not create another V1 acceptance gate after these activation conditions are satisfied.

## 8. V2-after-V1

V2 remains isolated. Continue only current-compatible donor reconciliation, actual-media validation, unattended/recovery revalidation, and integrated qualification/observation/bounded-learning work. Never mutate/reset V1 runtime/store/browser/publication authority and never infer V2 public-write permission from V1 acceptance.

## 9. Hard stops

Stop on secret/session exposure, fabricated factual/Core Analyzer truth, wrong-account/out-of-scope public write, destructive production-state mutation, unresolved `UNKNOWN_WRITE`, ambiguous public-object identity, irreconcilable ref conflict, duplicate production owner, or accidental V2 authority expansion.

Substack is canonical. The eight V1 derivative destinations remain Telegram, Discord, X, LinkedIn, Facebook Page, Instagram Business, Threads, and YouTube Community.

## Additive operating model - shared four-trigger data resolution (2026-10-18)

The next ContentOps implementation slices consume the Main App shared contracts rather than create a parallel research brain:

1. Add the TriggerRequest/DataNeedPlan/DataResolutionReceipt adapter for CONTENTOPS_EDITORIAL.
2. Bind it to existing sidecars, published memory and admitted database views without changing source ownership.
3. Add bounded BrowserOS read-only recovery for named source gaps.
4. Shadow one latest-intelligence request and one Jim manual request through the existing Simple path.
5. Expose public-safe coverage/freshness/rights/exact-proxy fields in the existing read model.

No fifth routine task, second publication store, public-write grant or private portfolio-data path is introduced. Desktop editorial ownership follows the 2026-10-20 migration. Report research-only, draft-only, publishable and DATA_BLOCKED states separately.

## Capital Chronicle latest-report consumer (owner mandate 2026-10-18)

Implement CONTENTOPS_CAPITAL_CHRONICLE_LATEST_REPORT_BRIDGE_V1.md on the merged Goal 15/16
components. Main owns AssetAnalysisReportV1 and LatestAnalysisReportEnvelopeV1; ContentOps
imports exact producer bytes/schema and creates a useful editorial input/draft through the
existing writer/validator. Deliver report-version dedupe, correction/invalidation, public-safe
claim lineage, DB-first/Neo supporting research and article/eight-derivative mappings.

This is a substantial end-to-end implementation goal. A prepared runner argument, injected
validation result or synthetic report alone is insufficient integration evidence. Preserve the existing input/evidence/windows with the current native Desktop editorial owner and existing publication/recovery authority unchanged.

Protected historical `v1.0` remains immutable at `6983bfb3ef300414b744f3f8f97ca81ff699348b`.

## Original evidence and operational report-feed continuation (2026-10-19)

Extend the existing latest-report integration without rebuilding its accepted owners:

1. Acquire useful independent source propositions with exact retained bytes/spans, rights,
   identity, revision and clocks; return admitted context to Main. Preserve reputable attributed
   reporting. Main-origin round trips receive no independent-evidence count.
2. Consume Main's immutable public export manifest/schema, complete lawful ancestry and
   correction/withdrawal events. Verify a real retained chain in an empty disposable store and
   on replay/restart. Non-editorial ancestors create no draft/writer intent; private account or
   full private report reads are excluded.
3. Route useful eligible changes through the existing opportunity, native Desktop writer / existing deterministic validator,
   native eight-preview compiler, source-backed media owners and Daily App. Keep controlled
   artifacts distinct from fresh provider output and published/readback results.
4. Expose independent versus recirculated items, Main events admitted/rejected/no-op, useful
   story conversion, draft/preview/media readiness, rights gaps and one exact next operation.
   Do not count all delivered events as articles or evidence of daily operating reliability.

The Main designated demo is not a ContentOps account or dataset. Consume only public-safe
analysis; no account/position/fill facts, demo alpha claim or broker authority crosses this seam.
No real-money transition is available through ContentOps. Preserve the active LLM pause,
existing four windows and V2 isolation; no new scheduled owner or publication permission.
The [dated reconciliation](CONTENTOPS_OWNER_UPDATE_RECONCILIATION_20261019.md) separates merged
foundation from open Goal20 work. It is evidence, not a second current-state ledger.

## Public research meaning and uncertainty (owner update 2026-10-21)

Preserve the exact permitted question, target/proxy, horizon/cutoff, probability measure,
method/evaluation and selection/dependence from public research into article and derivatives.
Source facts, Main interpretation, conditional scenarios, subjective challengers, statistical
and risk-neutral probabilities remain distinct. Missing metadata stays unknown and is no
universal block on useful factual/qualitative journalism. No score or option valuation becomes
a trade win rate; Main recirculation/shared-release copies do not independently confirm a claim.
Reuse existing admission, native packets, source-review, compiler and coordinator; Main alone
owns numeric estimation/evaluation. No new engine/status/store, role/pause or publication grant.
See [the consumer projection](../editorial/CONTENTOPS_PUBLIC_RESEARCH_SEMANTICS_V1.md) and the
[Goal30 owning handoff](CONTENTOPS_LATEST_REPORT_BRIDGE_V1_20261018/goal30/RELEASE_HANDOFF.md).
## Goal33 audience feedback continuation (2026-10-22)

`PARTIAL_CAPABILITY_REUSE_COMPONENTS`: native new opportunities freeze the existing guarded
performance policy, dated eligible feedback and canonical published memory. Compact preferences
reach Sol Light selection and warranted Sol MAX writing/SEO/eight native packages; old frozen
requests and prepared articles remain unchanged. Existing metrics, caps, sample/dependence,
rollback, source/rights/numeric/uncertainty and sole coordinator boundaries remain authoritative.
Two exact historical public objects were observed through read-only Neo; no independent reader
question was found and the policy remained HOLD. Actual native selection reused retained articles
and saved three ranked research briefs rather than creating a duplicate. Current edition remains
3 ready / 24 previews / 0 missing; production and four tasks remain paused. No public write,
activation, account change, merge or deployment is claimed. The CLI, Desk and installed
`contentops-newsroom` continuation are documented in
`docs/automation/CONTENTOPS_LATEST_REPORT_BRIDGE_V1_20261018/goal33/RELEASE_HANDOFF.md`.
Exact remote/CI evidence follows in that directory's `delivery.json`; Control Tower receiver
synchronization remains pending, with these pointers as the discoverable handoff.
