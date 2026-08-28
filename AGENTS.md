# Capital Chronicle ContentOps — Root Repository Contract

Authority date: 2026-08-29
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

The merge commit `db0befb8ad44f1080c67fcb801e5470ce7852369` records Jim's explicit current decisions:

- `V1_FINAL_PRODUCT_ACCEPTED = TRUE`;
- routine V1 public-write/readback authority is granted for the accepted V1 path;
- V2 public-write authority remains zero unless separately granted.

Any subordinate current-looking wording that still says routine V1 public-write/readback is ungranted or `V1_FINAL_PRODUCT_ACCEPTED` is pending is superseded.

Acceptance does not waive current-host identity/readiness/recovery proof before a new public write, and it does not authorize a missing production bridge to be assumed.

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

## 6. Current V1 activation architecture

Reuse, do not rebuild:

- accepted PR #37 Editorial Growth Edge and epistemic-state logic;
- current Simple article path and native exactly-eight compiler;
- four-window Simple scheduling mechanics and persistent zero-write host proof;
- PR #38 current post-acceptance authority/static-safety closure and Simple emergency-stop/process coverage;
- PR #39 single routine production-owner composition: Final Daily App -> `SIMPLE_GEMINI_RUNTIME`, with native Desktop/legacy rolling-X fenced non-routing;
- durable V1 store;
- destination registry;
- `DurablePublicationCoordinator` as the sole public-write owner;
- canonical Substack-first transports;
- strict readback/reconciliation and UNKNOWN-write recovery;
- V5 read model/UI foundation;
- historical Italy nine-surface canary as publication-stack proof.

Current new implementation gaps are limited to:

1. Simple qualified article/package -> existing `DurablePublicationCoordinator` production bridge;
2. published/reconciled production-day accounting distinct from zero-write qualified-count telemetry.

Single-owner composition and Simple emergency-stop/process coverage are closed and must not be reissued as implementation tasks. Historical wording that still lists them as gaps is superseded by fresh `master` code and this contract.

Before the first new live V1 write, current-host read-only proof is required for production-store integrity/recovery state, exact Edge 9223 publication profile/account identities, current destination readiness, exactly-one production owner/process, and `UNKNOWN_WRITE=0`. Do not inspect or expose secrets/session material.

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

## 10. Execution framework

Use `CAPABILITY_ROUTED_HYBRID`:

- `WEB_STATIC`: repo-static reasoning/authority/docs/GitHub operations;
- `WEB_CI`: bounded deterministic implementation provable by CI;
- `CODEX_EXECUTION`: real runtime/Windows/browser/stateful/debug evidence;
- `OWNER_GATED_EXTERNAL`: secrets/session, destructive canonical mutation, material numeric-authority change, V2 public-write expansion, or external/legal/rights release decisions.

Jim has already granted routine V1 public-write/readback authority. That grant remains subject to exact account/identity/readiness/reconciliation safeguards.

Use the cheapest lane that can produce evidence strong enough for the claim.

## 11. Locked current sequence

1. wire Simple into the existing publication coordinator and close published/reconciled-count accounting without rebuilding transports;
2. run current-host read-only activation preflight;
3. run one fresh end-to-end live V1 canary under the already-granted authority and strictly reconcile all nine surfaces;
4. only after that canary is clean, enable the four routine live windows toward 5–8 useful published articles/day;
5. preserve V1 and continue isolated V2 work only under V2's separate authority boundaries.

Repository authority/static-safety closure, emergency-stop coverage, and single-owner composition are already closed by merged PR #38 and PR #39; do not recreate them.

## 12. Change discipline

Prefer bounded product slices over ceremony. Do not rebuild proven systems simply because they are not freshly revalidated.

Ordinary reversible repository operations inside the accepted roadmap do not require a new per-operation owner authorization after the operator hard-gate audit has passed. They may use task branches/PRs and the normal protected-branch path once required checks pass.

This repository autonomy does not authorize bypassing branch protection, force-push, public/provider writes outside the already-granted V1 scope, destructive production/canonical-store mutation, Capital Chronicle proprietary/numeric-authority expansion, V2 public-write authority expansion, secrets/session access, or protected-history mutation.

Stage explicit paths only. Never `git add .` or `git add -A`.

## 13. Hard stops

Stop on:

- secret/session/token/cookie/private-key exposure;
- fabricated facts or Core Analyzer truth;
- wrong-account or out-of-scope public write;
- destructive production-store/upstream mutation;
- unresolved `UNKNOWN_WRITE` or public-object ambiguity;
- irreconcilable ref conflict;
- inability to prove exact publication identity/readiness before crossing a live write boundary.

Do not stop for historical noise, stale docs, unrelated dirty files, absent CI, pre-existing failures, or reversible mechanics.

Protected historical `v1.0` remains immutable at `6983bfb3ef300414b744f3f8f97ca81ff699348b`.

## 14. Visual/media acceptance

UI/video/audio PASS requires actual rendered artifact inspection. Tests and worker judgment prove mechanics, not final viewer-facing quality.
