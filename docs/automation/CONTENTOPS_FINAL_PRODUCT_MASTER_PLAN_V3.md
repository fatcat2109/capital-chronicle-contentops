# Capital Chronicle ContentOps — Final Product Master Plan V3

Authority date: 2026-08-22
Status: `CURRENT_ROOT_EXECUTION_MASTER_PLAN`

North Star: `docs/automation/CONTENTOPS_FINAL_PRODUCT_NORTH_STAR_V3.md`
Authority map: `docs/automation/CONTENTOPS_CURRENT_AUTHORITY_AND_SUPERSESSION_MAP_V1.md`

## 0. Objective

Finish one coherent autonomous growth newsroom that reliably produces useful publication-quality work every newsroom production day, while preserving hard truth, evidence, rights, identity, numeric-authority, recovery, and public-write boundaries.

Current highest-priority owner contract:

- MVP launch: exactly one current useful zero-write native-XHIGH article, eight derivative intents,
  hard-safe validation, JIT nine-surface identity/readiness, and owner audit before any public write;
- POST-LAUNCH THROUGHPUT: at least `4 QUALIFIED ZERO-PUBLIC-WRITE ARTICLES / 32 DERIVATIVE INTENTS`
  per newsroom production day before unattended production-grade operation;
- FINAL V1: `5–8 PUBLISHED ARTICLES` per newsroom production day;
- candidate abstention remains allowed;
- a whole-day deficit below the active floor is degraded unless an exact hard external blocker is proven;
- filler and unsupported claims remain forbidden.

## 1. Accepted foundation

Accepted and do not reopen without a demonstrated defect:

- P0-1 publication-authority/context separation;
- canonical V1 durable store/runtime/publication coordinator;
- growth-first eight-mode editorial spectrum;
- claim/mode-proportional evidence;
- official-primary breaking fast lane;
- quiet-day week-ahead/document/explainer/house-view behavior;
- canonical-first derivative resilience;
- P0-G3 multi-mode zero-write owner audit and merge at master lineage `369c0cc289e790b8218ba30b2696a926db04356a`.

Current P0-G4 draft PR #12 is not final authority for new daily-output semantics and remains frozen until this plan's execution-bridge correction is merged/reconciled.

## 2. Current demonstrated gap

The latest prepared-frontier proof exhausted 41/41 distinct story opportunities and reached two
fresh native XHIGH returns. The CFTC-positioning return failed hard on unsupported causality; the
FX-expiry return failed hard on numeric source binding. Those findings cannot be downgraded. The
immediate gap is one hard-safe MVP canary slice, not another 4/32 campaign.

The 2026-08-22 bounded current walk then evaluated 48 identities/42 distinct opportunities and
found no accepted evidence packet. It stopped before XHIGH, packaging, JIT, and publication with
`UNKNOWN_WRITE=0`. This is a truthful evidence-availability blocker, not permission to relax truth
or synthesize a canary.

Two product gaps must be closed before resuming the real publication canary.

### 2.1 Daily-output contract gap

Current code/docs were built around publication-minimum-zero and one-opportunity semantics. That is stale under the current owner contract.

The system needs one deterministic newsroom production-day accounting layer that:

- groups the 17:00, 21:00, 23:00, and following 01:00 Bangkok windows into one production day;
- counts only qualified build articles and actual final published articles;
- exposes build floor `4`, final target `5–8`, current count, deficit, and state;
- allows later windows to recover an earlier deficit through bounded additional candidate/article work;
- does not loop forever, repeat terminal unchanged candidates, or manufacture filler.

### 2.2 Codex execution-bridge truth gap

FDA-G continuously ingests and maintains state, but current repository code does not prove a direct FDA-G-to-Codex Desktop invocation path.

`live_contentops/codex_desktop_newsroom_operator_v1.py` is not a scheduler or Desktop/model bridge. Repository setup packets describing four native Codex tasks are configuration intent only.

Before unattended/editorial automation claims, actual host truth must prove:

- whether current Codex supports native Automations;
- whether the four intended ContentOps Automations actually exist;
- their exact state, project, schedule, model, reasoning effort, and prompt;
- whether they can run unattended on this host;
- whether their HIGH coordinator can create the required fresh isolated XHIGH worker;
- whether any supported immediate material-event-to-Codex wake exists.

Configured intent must never be promoted to observed host state.

## 3. Immediate P0 task — MVP canary launch-gate reset and canary-ready slice

Execute one bounded heavy vertical slice:

`TASK_V1_MVP_CANARY_LAUNCH_GATE_RESET_AND_CANARY_READY_SLICE_V1`

Required deliverables:

1. active authority/docs reconciled to MVP-canary-first sequencing;
2. explicit `MVP_CANARY_LAUNCH_GATE_V1` hard-gate versus quality-warning profile;
3. exact audit of both current XHIGH candidates;
4. one bounded fresh-current walk only if neither candidate is hard-safe/current;
5. exactly one native-XHIGH final article with canonical Markdown/HTML/SEO artifacts;
6. exactly eight zero-write derivative package intents;
7. supported JIT read-only identity/readiness for all nine destinations;
8. `UNKNOWN_WRITE=0`, zero publisher/transport writes, and stop before publication;
9. no source/evidence/numeric/CC/permission/identity/rights/worker-binding weakening;
10. proof that one canary grants no second article, Automation enablement, or public write.

## 4. Production-day accounting contract

The routine intended opportunities are:

- 17:00 Bangkok, Monday–Friday;
- 21:00 Bangkok, Monday–Friday;
- 23:00 Bangkok, Monday–Friday;
- 01:00 Bangkok, Tuesday–Saturday, belonging to the prior newsroom production day.

Required states:

- `ON_TRACK`
- `DEFICIT_RECOVERABLE`
- `FLOOR_MET`
- `DEGRADED_DAILY_OUTPUT_DEFICIT`
- `HARD_EXTERNAL_BLOCK`

Candidate-level `NO_PUBLICATION` does not set production-day success while the floor remains unmet.

Hard external blockers must be exact and auditable; they must not be fabricated to excuse low yield.

## 5. Deficit recovery without a fifth task

Do not create additional routine schedule objects to chase the floor.

At each actual routine Codex wake:

1. load current production-day count/deficit;
2. recover/read back any outstanding state;
3. load fresh/current candidate universe and durable evaluated memory;
4. walk strong candidates and applicable editorial modes;
5. create qualified build article(s) until the current cumulative expected progress is restored, candidate/evidence universe is genuinely exhausted, bounded cost is reached, or a hard external blocker occurs;
6. persist deficit before/after and terminal reasons.

Later windows may catch up earlier misses. Bounded cost, durable cutoff, update-chain semantics, and duplicate prevention remain mandatory.

## 6. Codex execution architecture

Preferred routine architecture:

`FDA-G background intake/state -> native Codex Automation -> gpt-5.6-sol/HIGH coordinator -> one fresh isolated gpt-5.6-sol/XHIGH worker per warranted final article -> deterministic validation -> zero-write build output or authorized publication`

FDA-G remains the always-on cheap runtime authority. Codex is the heavy editorial execution layer.

Do not create a Python/Desktop bridge merely because the host tasks are missing. First use supported native Codex Automation capabilities. If owner UI configuration is required, stop and request that exact action rather than inventing task state.

Immediate material-event-to-Codex execution is `NOT_PROVEN` until a supported bridge is demonstrated. Any credential/access-token/API bridge is a separate owner-gated execution/security change.

## 7. V5 operator contract

V5 must show:

- newsroom production-day ID;
- qualified build articles `X / 4`;
- remaining build deficit;
- final target `5–8/day` with build/public-write state distinction;
- production-day state;
- actual observed Codex Automation state where safely observable, otherwise `AUTOMATION_STATE_UNAVAILABLE`;
- next intended/observed Codex opportunity without conflating configured intent and host truth;
- normal runtime/evidence/authority/publication/recovery/cost state.

If the build floor is unmet, generic `Running Idle — healthy waiting` must not hide the production deficit.

## 8. One supervised MVP canary before the post-launch throughput proof

The current slice may return `CANARY_READY_FOR_OWNER_PUBLIC_WRITE_GATE` only after every hard gate
and JIT identity/readiness check passes. It then stops for owner audit and exact grant.

### P0-G4A

- zero-write genuine current candidate;
- article + eight packages locked;
- exact JIT destination identities/readiness;
- explicit owner public-write gate.

### P0-G4B

After exact owner grant:

- canonical Substack publish/readback;
- exactly eight derivative attempts;
- destination-local recovery;
- strict reconciliation;
- `UNKNOWN_WRITE=0`;
- actual public-object owner audit.

A canary grant authorizes only that canary unless explicitly widened.

## 9. Post-launch throughput and unattended/cold-start proof

After owner-accepted canary, first prove 4 qualified zero-write articles / 32 derivative intents,
then:

- use only actual proven native routine Automations;
- no fifth routine task;
- prove production-day floor/target accounting under calendar-time unattended execution;
- prove restart/cold-start, cutoff/recovery, no duplicate articles/public objects, bounded cost, and truthful deficit/hard-block states;
- separately owner-gate any live automatic material-event Codex/public-write wake capability.

## 10. V5 final closure

Before final V1 acceptance:

- current source epoch/build must be healthy;
- daily-output/automation truth must be visible;
- runtime/evidence/authority/publication/recovery/cost state must be truthful;
- fresh browser screenshots must be independently reviewed against current design authority;
- visual PASS cannot be inferred from tests.

## 11. Final V1 definition of done

V1 is final only when:

1. one reliable Daily App remains continuously healthy;
2. build proof demonstrates the 4-qualified-article floor without filler or weakened truth;
3. final operating behavior targets 5–8 published articles per newsroom production day;
4. actual Codex execution/Automation bridge is proven, not merely configured in docs;
5. real canonical Substack + eight derivatives canary is accepted with `UNKNOWN_WRITE=0`;
6. unattended/cold-start execution is proven;
7. UI truth and visual acceptance are complete.

## 12. Hard stops

Stop on secret/session exposure, fabricated factual/Core Analyzer truth, wrong-account or unauthorized public write, destructive production-state mutation, unresolved `UNKNOWN_WRITE`, unsupported automation mutation, or inability to distinguish configured task intent from actual host automation state.

Protected historical `v1.0` remains immutable.
