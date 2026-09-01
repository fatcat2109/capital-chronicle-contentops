# Capital Chronicle ContentOps — Root Repository Contract

Authority date: 2026-09-01
Status: `CURRENT_ROOT_AUTHORITY`
Repository: `fatcat2109/capital-chronicle-contentops`

## 1. Mandatory current read path

For every current implementation, audit, task framing, or owner decision, read in this order:

1. `AGENTS.md`
2. `docs/codegraph/INDEX.md`
3. `docs/automation/CONTENTOPS_CURRENT_AUTHORITY_AND_SUPERSESSION_MAP_V1.md`
4. `docs/automation/CONTENTOPS_CURRENT_STALE_DOCS_MANIFEST_V1.md`
5. `docs/automation/CONTENTOPS_CAPABILITY_ROUTED_HYBRID_EXECUTION_POLICY_V1.md`
6. `docs/automation/CONTENTOPS_FINAL_PRODUCT_NORTH_STAR_V3.md`
7. `docs/automation/CONTENTOPS_FINAL_PRODUCT_MASTER_PLAN_V3.md`
8. `docs/automation/CONTENTOPS_V1_POST_ACCEPTANCE_ACTIVATION_AUTHORITY_V1.md` for current V1 activation
9. `docs/automation/CONTENTOPS_V1_SIMPLE_GEMINI_RUNTIME_RESET_V1.md` for Simple V1 mechanics
10. `docs/codegraph/V1_CONTEXT.md` or `docs/codegraph/V2_CONTEXT.md`
11. current lane pointer
12. nearest scoped `AGENTS.md`
13. exact current implementation/tests/evidence.

Do not route from historical task evidence, stale handoffs, generated status snapshots, task branches, or chat SHAs.

## 2. Authority order

Product authority:

1. Jim's latest explicit instruction;
2. this root contract plus the current root North Star/Master Plan and current post-acceptance V1 activation authority;
3. current authority map and lane pointer;
4. older detailed plans/history.

Repository/evidence authority:

1. fresh remote refs/commits/diffs/exact bytes;
2. exact implementation, focused tests, accepted evidence, exact-head CI where applicable;
3. runtime/host/browser evidence for facts only execution can prove;
4. historical docs/project sources/chat.

Newer owner direction wins.

## 3. Current owner state

Jim's current explicit decisions establish:

- `V1_FINAL_PRODUCT_ACCEPTED = TRUE`;
- routine V1 public-write/readback authority is granted for the accepted V1 path;
- routine V1 editorial owner is `SIMPLE_GEMINI_RUNTIME`;
- `DurablePublicationCoordinator` remains the sole public-write/readback owner;
- V2 public-write authority remains zero unless separately granted;
- product progress is `BUILD -> RUN -> OBSERVE REAL FAILURES -> FIX`; ceremony or safety architecture is not a prerequisite unless a real failure or irreversible-risk boundary requires it.

The current protected/deployed V1 epoch before the browser-source architecture detour is PR #53 merge commit:

`1c0354347e51d7b84bd7e41386d7bf428709e4bf`

This epoch includes the accepted PR #51/#52/#53 runtime/intake/sourceability/output-starvation repairs.

Any subordinate current-looking wording that still says routine V1 public-write/readback is ungranted, V1 acceptance is pending, or activation has not happened is superseded.

## 4. Locked V1 product contract

Final operating target:

`5–8 PUBLISHED ARTICLES per newsroom production day`

No filler. Candidate-level abstention is allowed. Whole-day deficit is not healthy success. A below-target live day without an exact hard external blocker is:

`DEGRADED_DAILY_OUTPUT_DEFICIT`

The historical zero-write 4/32 benchmark remains telemetry/economics evidence only:

`4 QUALIFIED ZERO-PUBLIC-WRITE ARTICLES / 32 DERIVATIVE INTENTS`

It is not a prerequisite for advancing one safe article or for the already-granted V1 product acceptance.

Routine windows remain 17:00, 21:00, 23:00, and following 01:00 Asia/Bangkok under one deterministic production day. Do not create a fifth routine task merely to chase quota.

## 5. Current V1 editorial architecture

Current routine editorial ownership is `SIMPLE_GEMINI_RUNTIME`, not Desktop Automations.

The accepted article path is:

`current sidecars + canonical reconciled published memory -> deterministic dedupe/sourceability order -> <=32 candidates -> one vx/gemini-3.5-flash(high) selector -> one primary + <=2 useful fallbacks -> shared <=6 deterministic source/provenance GETs -> explicit report/event epistemic state -> one Flash writer -> deterministic material-claim/source/epistemic validation -> <=1 Flash revision without source expansion -> one qualified article -> exactly eight native derivative packages`.

Locked per-opportunity ceilings:

- candidate packet <=32;
- one selector;
- <=3 admitted candidates;
- <=6 deterministic source/provenance GETs total;
- one writer;
- one revision maximum;
- <=3 logical Flash calls total;
- Codex runtime model calls = 0.

One exact owner-curated canonical-X record may support only its narrow relay-of-reporting or explicit market-rumor proposition under the accepted record-scoped provenance contract. It remains `UNCONFIRMED`, never proves the cited publisher's original report or the underlying event, and cannot bypass high-harm evidence handling.

Native Desktop Automations, SDK/App-Server editorial fallback, legacy rolling-X ownership, broad evidence-ready pools, and split-phase PREPARE/COMPLETE handoffs are historical/non-routing for routine V1.

## 6. Current V1 runtime/product truth locked on 2026-09-01

Reuse, do not rebuild:

- accepted PR #37 Editorial Growth Edge and epistemic-state logic;
- current Simple article path and native exactly-eight compiler;
- four-window Simple scheduling mechanics;
- single-owner composition with `SIMPLE_GEMINI_RUNTIME` as sole routine editorial owner;
- durable V1 store;
- destination registry;
- `DurablePublicationCoordinator` as the sole public-write/readback owner;
- canonical Substack-first transports;
- strict readback/reconciliation and UNKNOWN-write recovery;
- persistent scheduler ownership from PR #51;
- production-day distinct SOURCE_BLOCKED candidate walking from PR #52;
- persistent Daily App intake/state/API ownership, governed source-reachability correction, relay attribution normalization, and unconfirmed derivative correction from PR #53.

Current protected/deployed source before the architecture detour:

`1c0354347e51d7b84bd7e41386d7bf428709e4bf`

Confirmed product truth:

- one current V1 lifecycle has already completed canonical Substack plus exactly eight durable-confirmed derivatives;
- routine mode has been activated as `AUTONOMOUS_DEFAULT`;
- one natural production day then reproduced `AUTOMATION_RUNNING_BUT_OUTPUT_STARVED`: 17:00 and 21:00 were missed by the old detached scheduler-liveness defect, while 23:00 and 01:00 executed but produced zero new articles under `ALL_ADMITTED_CANDIDATES_SOURCE_RETRIEVAL_BLOCKED`;
- PR #51 repaired persistent scheduler ownership and source-route health carry-forward;
- PR #52 repaired repeated selection of candidates already proven SOURCE_BLOCKED in the same production day;
- PR #53 proved the continuous intake had been stale, restored durable intake ownership, corrected sourceability around the existing canonical-X zero-GET relay route, improved route-diverse selection, and fixed deterministic downstream relay-attribution / unconfirmed-derivative defects;
- after PR #53, a real current candidate crossed the previously universal source-retrieval blocker, reached `SOURCE_QUALIFIED` with one accepted source and zero GETs, passed deterministic article validation, and compiled exactly 8/8 derivative packages;
- a later stochastic writer replay failed closed at `claim_fields_invalid`; this is not a publication success and was not converted into filler;
- PR #53 exact-head CI and focused/expanded regressions passed;
- current V1 is therefore repaired and healthy-idle, but `5–8/day` reliability is NOT runtime-proven and no natural routine opportunity has yet proven the PR #53 epoch can convert fresh intake into routine public output.

The historical Substack object `213355736` was later reconciled by an external actor to the same object. PR #53 did not retry, publish, or mutate the incident as part of that reconciliation. Historical ambiguity must not be rewritten as ContentOps production proof.

## 7. ContentOps/Core Analyzer boundary

Capital Chronicle/Core Analyzer owns proprietary calculations, probabilities, scenarios, forecasts, regimes, decisions, paper records, realized-outcome attribution, and other analytical/numeric truth.

ContentOps owns discovery, grounded research, story selection, writing, SEO, media, distribution, readback/reconciliation, observation, growth, and bounded learning.

No external report or model output gains Capital Chronicle proprietary numeric/forecast/probability/scenario/regime/valuation/decision authority.

## 8. Editorial and epistemic rules

V1 preserves eight modes:

- `BREAKING_BRIEF`
- `FOLLOW_UP_UPDATE`
- `STANDARD_NEWS_ANALYSIS`
- `CAPITAL_CHRONICLE_VIEW`
- `WHAT_THE_MARKET_IS_MISSING`
- `EVERGREEN_EXPLAINER`
- `DATA_OR_DOCUMENT_LENS`
- `WEEK_AHEAD_OR_WATCH`

Report truth and underlying event truth are separate. Official confirmation is not a universal prerequisite for a narrow attributed reputable report. Reader-visible uncertainty must survive canonical copy and all derivatives. A derivative may compress wording, never certainty.

Strong evidence-backed criticism/contrarian framing is allowed. Fabricated outrage, unsupported allegations, and filler are not.

## 9. Publication/recovery boundaries

Substack is canonical. The eight derivative destinations are Telegram, Discord, X, LinkedIn, Facebook Page, Instagram Business, Threads, and YouTube Community.

A counted published article requires exact canonical identity/readback under the accepted coordinator contract. Derivatives must use the real reconciled canonical `/p/...` URL, never a pending placeholder.

`UNKNOWN_WRITE = STOP RETRY -> READ BACK -> RECONCILE`

Chrome `CapitalChronicleBot` CDP 9222 is ingestion only. Edge `contentops-social-main` CDP 9223 is publication/media/readback/authorized observation only.

Do not replace the current production publication/browser ownership merely because a new browser-agent abstraction is being evaluated. Any later transport change must be justified by product evidence and must preserve exact identity/readback/reconciliation truth.

## 10. Execution framework

Use `CAPABILITY_ROUTED_HYBRID`:

- `WEB_STATIC`: repo-static reasoning/authority/docs/GitHub operations;
- `WEB_CI`: bounded deterministic implementation provable by CI;
- `CODEX_EXECUTION`: real runtime/Windows/browser/stateful/debug evidence;
- `OWNER_GATED_EXTERNAL`: secrets/session, destructive canonical mutation, material numeric-authority change, V2 public-write expansion, or external/legal/rights release decisions.

Jim has already granted routine V1 public-write/readback authority. That grant remains subject to exact account/identity/readiness/reconciliation truth at the live write boundary.

Use the cheapest lane that can produce evidence strong enough for the claim.

## 11. Locked current sequence

The isolated `BROWSER_RENDERED_SOURCE_RECOVERY_ARCHITECTURE` objective is implemented and
live-shadow-proven. The capability is documented in
`docs/automation/CONTENTOPS_BROWSER_RENDERED_SOURCE_RECOVERY_V1.md`.

The implementation is hybrid rather than a wholesale CDP replacement:

- deterministic HTTP remains the first source-retrieval path;
- one exact allowlisted publisher URL may use BrowserOS Neo only after an eligible 403/429,
  render-only/insufficient-body failure, or exact route-health suppression;
- rendered evidence carries distinct `READ_ONLY_BROWSEROS_NEO_RENDERED_PAGE` provenance,
  final-host identity, timestamp, semantic scope, and dual hashes; it never masquerades as raw
  HTTP bytes;
- browser acquisition uses only a task-owned tab with `name_session`, `tabs`, and `read`, with
  no click, login, consent, storage, credential/session inspection, model call, or public write;
- browser acquisition shares the existing six-request evidence ledger and is capped at one
  recovery attempt per loader invocation;
- BrowserOS Neo is a source-recovery/diagnostic layer, not V1 publication authority;
- `SIMPLE_GEMINI_RUNTIME`, the existing evidence/claim/epistemic validators, and
  `DurablePublicationCoordinator` remain the owners; current CDP publication transports,
  scheduler, store, and numeric authority remain unchanged.

The main V1 autonomous-routine objective now resumes from the locked PR #53 epoch. First run
current-host read-only activation preflight, then one fresh strictly reconciled live canary, then
the four natural routine windows toward 5–8 useful articles/day. This browser shadow proof is not
a public-write canary and does not prove the daily target.

Do not reinterpret the architecture slice as V2 progress.

## 12. Change discipline

Prefer bounded product slices over ceremony. Do not rebuild proven systems simply because they are not freshly revalidated.

Ordinary reversible repository operations inside the accepted roadmap do not require a new per-operation owner authorization after the operator hard-gate audit has passed. They may use task branches/PRs and the normal protected-branch path once required checks pass.

This repository autonomy does not authorize bypassing branch protection, force-push, public/provider writes outside the already-granted V1 scope, destructive production/canonical-store mutation, Capital Chronicle proprietary/numeric-authority expansion, V2 public-write authority expansion, secrets/session exposure, protected-history mutation, or blind duplicate public writes.

Stage explicit paths only. Never `git add .` or `git add -A`.

## 13. Hard stops

Stop on:

- secret/session/token/cookie/private-key exposure;
- fabricated facts or Core Analyzer truth;
- wrong-account or out-of-scope public write;
- destructive production-store/upstream mutation;
- blind duplicate public write under known ambiguity;
- irreconcilable ref conflict;
- silent creation of a second scheduler/store/publisher/coordinator/authority owner.

Do not stop for historical noise, stale docs, unrelated dirty files, absent CI, pre-existing failures, deployment-proof ceremony, or reversible mechanics.

Protected historical `v1.0` remains immutable at `6983bfb3ef300414b744f3f8f97ca81ff699348b`.

## 14. Visual/media acceptance

UI/video/audio PASS requires actual rendered artifact inspection. Tests and worker judgment prove mechanics, not final viewer-facing quality.
