# Capital Chronicle ContentOps — Operator–Builder Workflow Doctrine V1

Status: `DURABLE_CONTENTOPS_WORKFLOW_DOCTRINE`
Scope: `fatcat2109/capital-chronicle-contentops`
Authority class: `WORKFLOW / EXECUTION GOVERNANCE`
Mutable project status authority: `NONE`

This document governs how ContentOps work is routed between Jim/owner, ChatGPT Operator, GitHub,
deterministic CI, Codex Desktop Builder, V1/V2 runtime, and owner-gated external/public boundaries.

It does **not** own current Git SHA, branch/PR state, exact-next task, current V1/V2 acceptance state,
runtime/browser/provider/Automation state, public-write authority, or current capability status.
Resolve those from fresh repository authority and actual runtime/host evidence where required.

This file intentionally replaces the older execution-policy-only semantics at the same canonical
path. Do not create a second workflow-policy/status ledger merely to restate these rules.

Jim's latest explicit instruction remains higher product authority. Nearest scoped `AGENTS.md`
instructions may tighten real product safety boundaries; they may not silently revive procedural
ceremony that this doctrine explicitly removes.

---

## 1. Primary operating objective

Optimize:

`READER / VIEWER VALUE`
`+ PRODUCT LAUNCH VELOCITY`
`+ USEFUL CONTENT OUTPUT`
`+ LEARNING VELOCITY`
`+ RELIABILITY`
`+ QUALITY PER TOKEN / REQUEST / DOLLAR`
`+ MINIMUM PROCEDURAL LATENCY`

subject to hard:

`TRUTH + SOURCE/EVIDENCE + CAPITAL CHRONICLE NUMERIC AUTHORITY + RIGHTS + IDENTITY + PUBLIC-WRITE + SECURITY + UNKNOWN_WRITE`

boundaries.

Do **not** optimize for:

- strongest model on every operation;
- largest evidence packet;
- most validators;
- most tests;
- most governance documents;
- most task IDs;
- perfect rehearsal before useful product progress;
- minimum token use when a tight budget causes repeated failed runs.

Governance is useful only when it prevents a material defect, preserves authority, prevents duplicate
work, establishes otherwise unavailable evidence, or materially lowers future operating cost.

**Governance itself is not product progress.**

---

## 2. FAST SHIP / completion-first

Default sequence:

`CORRECTNESS / COMPLETION -> REAL PRODUCT OUTPUT -> MEASURED ECONOMICS -> OPTIMIZATION`

Never default to:

`PREMATURE BUDGET OPTIMIZATION -> PARTIAL FAILURE -> NEW TASK -> NEW PROOF -> REPEAT`.

Development/proof budgets must contain enough headroom to finish the capability coherently. Estimate
expected usage from historical evidence and deliberately leave surplus. Proof ceilings are emergency
runaway guards, not targets or success criteria.

When a task exposes a reversible implementation defect, default to:

`FIX -> FOCUSED TEST -> RERUN -> CONTINUE`

inside the **same task/session**.

Do not create `proof -> correction -> revalidation -> proof-of-proof -> final-proof` chains unless a
genuinely different authority, environment, or irreversible boundary exists.

A task may stop for a real hard blocker. It must not stop merely because an arbitrary turn/token/
request ceiling was reached while useful work, a safe fallback, or a clear reversible repair remains.

---

## 3. Execution lanes — route by evidence need

Use the cheapest lane capable of establishing the required truth.

### A. `CHATGPT_GITHUB_STATIC`

Default for:

- fresh remote-ref and current-authority verification;
- Git/PR/history/CodeGraph archaeology;
- capability-history and duplicate-work search;
- exact diff and static architecture audit;
- task sequencing and deciding whether implementation is needed at all;
- documentation/authority maintenance;
- simple deterministic code/config/test edits when static correctness is sufficient;
- Git-only branch/commit/PR/merge operations within standing authority.

Do not spend Codex quota on work GitHub/static evidence can settle.

### B. `GITHUB_CI`

Use for safe deterministic machine feedback:

- lint/format/compile/typecheck;
- focused unit/integration tests;
- schema/contract validation;
- reproducible builds;
- CodeGraph generation/checks;
- deterministic smoke checks.

CI proves only the checks it actually ran. CI does **not** prove Windows runtime state, current browser
state, provider availability, current Codex Automation state, public-object identity, rendered
visual/audio quality, or external-write success.

### C. `CODEX_EXECUTION`

Use Codex Desktop when correctness materially requires:

- Windows/local runtime state;
- repository shell/worktree;
- dependency/environment setup;
- stateful runtime execution;
- provider/network behavior;
- iterative run-observe-debug cycles;
- browser/runtime inspection;
- local database execution;
- actual article/video generation;
- performance/concurrency reproduction;
- rendered UI/video/audio production;
- tests unavailable from CI.

Codex is the execution-feedback lane. It is not the default repository reader, auditor, documentation
editor, or Git transport.

### D. `OWNER_GATED_EXTERNAL`

Require explicit owner authority for:

- credential/login/manual authentication;
- new or expanded public-write authority;
- wrong-account ambiguity;
- destructive production/canonical-store mutation;
- secret/session material access;
- material external/legal/rights decisions;
- new paid-spend authority;
- material Capital Chronicle proprietary/numeric-authority expansion;
- V2 public-write expansion;
- unresolved `UNKNOWN_WRITE`.

**Static Git evidence must never substitute for runtime or public-write evidence.**

---

## 4. Builder task admission — reuse first

Before issuing a Codex task, Operator establishes:

`CURRENT AUTHORITY -> CURRENT IMPLEMENTATION -> HISTORICAL CAPABILITY EVIDENCE -> CURRENT DRIFT -> CAPABILITY CLASSIFICATION -> EXACT NEW DELTA`

Use the current ContentOps planning classes:

- `CURRENTLY_PROVEN_AND_REUSE`
- `HISTORICALLY_PROVEN_CURRENT_REVALIDATION_ONLY`
- `CURRENT_HOST_RUNTIME_PROOF_REQUIRED`
- `NEW_IMPLEMENTATION_GAP`
- `SUPERSEDED_DO_NOT_REUSE`

Historical artifacts remain evidence of what was built/run/proven at their epoch.

**NON-ROUTING != NON-EVIDENCE.**

Do not declare a capability missing merely because it has not been freshly revalidated, its old task
folder is non-routing, a pointer no longer mentions it, or a model session lost context.

If the real delta is only `REVALIDATE`, `REUSE`, `RECONCILE`, `ACTIVATE EXISTING`, `UPDATE CURRENT
AUTHORITY`, `WAIT FOR REAL PROSPECTIVE EVIDENCE`, or `CLOSE OUT EXISTING EVIDENCE`, do that instead of
rebuilding.

A task name is never evidence that a capability is missing.

---

## 5. Every Codex packet declares execution identity

Every Builder packet must state before substantive instructions:

- `SESSION: CURRENT CODEX DESKTOP SESSION` or `FRESH CODEX DESKTOP SESSION`
- `MODEL: <explicit model>`
- `REASONING EFFORT: <explicit effort>`
- `WHY THIS CONFIG: <one short reason>`

Operator chooses this. Do not ask Jim routine session/model questions.

Use minimum sufficient compute. Consequential newsroom/runtime implementation normally warrants
GPT-5.6 Sol HIGH; major cross-module reasoning or consequential creative implementation may warrant
XHIGH; actual final high-value article/video workers may use one fresh isolated XHIGH when warranted.
Do not use MAX merely because a task is important.

---

## 6. Current vs fresh Codex session

Use **CURRENT** when the same branch/PR/worktree continues, current runtime/debug state is valuable,
a repair follows directly from an audit, or recently acquired provenance materially reduces cost or
risk.

Use **FRESH** when starting a genuinely different capability, switching V1/V2 truth planes, prior
context contains materially stale architecture assumptions, contamination risk exceeds re-grounding
cost, or a new independent worktree is safer.

A substantial continuation may legitimately use CURRENT.

Session context is disposable. Git branch/worktree state is durable. Never destroy valid work merely
because a model session ended.

---

## 7. Prefer one product slice over microtask chains

Prefer one coherent end-to-end task that produces observable reader/viewer/operator utility.

Fold small support work into the parent slice where safe:

- minimal schema changes;
- deterministic normalization;
- focused tests;
- exact current-authority updates;
- compact evidence closeout;
- CodeGraph refresh;
- commit/push/PR.

Do not create separate tasks by default for wording cleanup, metadata normalization, one retry, one
tiny compatibility fix, evidence packaging alone, status/SHA refresh, repeated architecture audits,
or rerunning proofs whose assumptions remain valid.

Split only for a real independent boundary: credentials, public write, destructive production state,
rights/legal, V1/V2 isolation, Capital Chronicle numeric authority, materially different environment,
or independently valuable deliverable.

---

## 8. Builder owns the engineering debug loop

Once an admitted Builder task starts, Builder owns:

`inspect -> reproduce -> diagnose -> implement -> test -> inspect failure -> repair -> retest -> runtime proof where required -> exact-diff self-audit -> commit -> push -> remote readback -> STOP`

Do not bounce ordinary engineering errors back to Operator after each attempt.

There is no arbitrary debugging-attempt limit.

But: **NO BLIND IDENTICAL RETRY.**

Every expensive retry requires a new hypothesis, a code/config/environment change, new evidence, or
a justified transient provider failure. Prefer local deterministic repair before spending another
XHIGH/network/provider/browser call.

---

## 9. Anti-overgating rule

Before keeping or adding any gate, ask:

> If this gate is removed, does material truth, source/evidence integrity, rights, security,
> Capital Chronicle numeric authority, public-write safety, destination identity, or
> `UNKNOWN_WRITE` risk materially increase?

If **NO**, the default action is:

`REMOVE IT`, `DETERMINISTICALLY AUTO-REPAIR IT`, or `DOWNGRADE IT TO WARNING`.

Do not add or preserve gates merely because:

- an old proof required them;
- they make receipts cleaner;
- they enforce duplicate representations of the same text;
- they make validators look stricter;
- they increase test counts;
- they make governance appear more institutional.

ContentOps is a production newsroom/growth system, not an acceptance-test generator.

---

## 10. Article validation — hard gates vs soft representation

### Hard article gates

Remain fail-closed for:

- fabricated or unsupported **material** fact;
- materially unsupported causality;
- fake/unbound quotation;
- materially misleading stale event state;
- unsupported factual numeric claim;
- proprietary probability/forecast/scenario/regime/valuation/decision claim without exact Capital
  Chronicle publication authority;
- invalid source identity or materially insufficient evidence for the claim being made;
- rights/permission/publication-authority failure;
- wrong destination/account;
- secret/session exposure;
- `UNKNOWN_WRITE`.

### Soft / auto-repair concerns

Where public factual meaning is unchanged, these should normally be normalized, dropped, or warned
rather than causing another writer turn or terminal article rejection:

- title/headline alias mismatch;
- subtitle/dek alias mismatch;
- search-title/SEO-title alias mismatch;
- social-hook/social-lede alias mismatch;
- slug aliases;
- structured-data headline/description mirroring;
- canonical author/publisher metadata duplication;
- stale non-public epistemic annotations;
- representation-only SEO metadata consistency;
- formatting differences.

Never insert new semantic prose merely to satisfy stale metadata.

A soft metadata/representation warning must not be promoted into a launch blocker unless it creates
a real reader-facing truth, identity, rights, or publication defect.

---

## 11. Candidate failure must not starve the newsroom

Candidate-level abstention remains valid.

A candidate hard failure must not automatically terminate the production opportunity, production
day, or other governed ready candidates.

Default behavior while useful eligible work remains:

`RECORD EXACT BLOCKER -> SKIP THAT CANDIDATE -> CONTINUE USEFUL CANDIDATE WALK`.

Do not manufacture filler and do not weaken evidence to hit volume. But do not let one over-strict
candidate gate turn V1 into an abstention engine.

Quiet days lower materiality or change editorial mode before declaring the useful universe exhausted;
they do not lower truth standards.

---

## 12. Throughput is a product metric, not universal ceremony

Final V1 target remains **5–8 useful published canonical articles per newsroom production day**,
without filler.

The four routine windows remain 17:00, 21:00, 23:00, and following 01:00 Bangkok. Do not create a
fifth routine task merely to chase volume.

The historical `4 qualified articles / 32 derivative intents` proof remains useful as throughput,
production-day health, and regression evidence.

It is **not a universal prerequisite** before every useful article, repair, merge, or launch-progress
decision. A safe qualified article may advance product acceptance independently. A failure of one
article does not invalidate unrelated proven discovery/publication/runtime capabilities.

Do not hold V1 launch progression hostage to perfect ceremonial 4/32 rehearsal when remaining
failures are soft representation/metadata defects rather than truth/safety defects.

Throughput economics should be optimized after the canonical article path works reliably, not by
prematurely starving development proof.

---

## 13. Evidence burden is claim-proportional

Ordinary reporting does not require institutional-research-level ceremony.

For a narrow ordinary factual article, one exact trustworthy source may be sufficient when it
directly proves the central proposition.

Require stronger evidence for disputed facts, allegations, causal claims, material market-impact
claims, broad analytical conclusions, or proprietary numeric/forecast/scenario language.

Models are never factual authority. Search output is never evidence authority. Discovery may locate
a source; deterministic retrieval/exact bytes/provenance establish evidence.

Capital Chronicle/Core Analyzer exclusively owns proprietary analytical/numeric truth. ContentOps
may make clearly labeled qualitative editorial inference from accepted public evidence, but may not
represent it as Core Analyzer output.

---

## 14. V1 / V2 separation

V1 is the canonical always-on newsroom/publication product.

V2 is the isolated retention-native video/channel-growth factory.

Never let V2 mutate/reset V1 production runtime/store, inherit V1 browser/public-write authority,
or redefine Capital Chronicle truth. Generated V2 media is never factual authority. V2 public-write
authority remains separately gated.

---

## 15. Browser and publication boundaries

Preserve current browser roles:

- Chrome `CapitalChronicleBot`, CDP 9222: ingestion only.
- Edge `contentops-social-main`, CDP 9223: publication/media/readback and explicitly authorized
  observation only.

Do not use pyautogui, SendKeys, focus stealing, brittle UI selectors, private browser/session DB
inspection, cookie/token extraction, or unsupported internals.

Canonical V1 lifecycle remains:

`evidence -> article -> validation -> optional rights-safe media -> Substack -> exactly eight V1 derivatives -> strict readback/reconciliation`

`UNKNOWN_WRITE = STOP RETRY -> READ BACK -> RECONCILE`.

No model, automation, configuration, or execution lane grants public-write authority by implication.

---

## 16. Validation proportional to blast radius

Default validation:

- focused changed-path tests;
- exact affected integration tests;
- current authority/contract validation;
- one relevant E2E/smoke when the delta requires it.

Do not repeatedly run huge suites after small article/metadata/representation fixes.

Broad regression is justified when the diff materially touches shared evidence authority, Capital
Chronicle numeric authority, durable production state, publication lifecycle, `UNKNOWN_WRITE`, common
router/model contracts, scheduler/runtime, or broad cross-V1 architecture.

Previously accepted capabilities are not re-proven from zero on every task. Previously valid public
canaries/model bakeoffs/external proofs are not repeated unless the new delta invalidates their
relevant assumptions.

A large test count is not evidence quality by itself.

---

## 17. Actual artifact acceptance

When quality is the claim, inspect the actual viewer-facing artifact.

Tests prove mechanics. They do not prove article usefulness, visual quality, pacing, media novelty,
chart legibility, audio quality, or viewer experience.

For article acceptance inspect actual prose, headline/dek, factual grounding, source use, reader
utility, obvious repetition, and derivative packaging where relevant.

For V2/UI/video/audio acceptance inspect the actual rendered artifact.

---

## 18. Evidence packets — minimum sufficient

A completed task normally needs only enough evidence for an independent merge/route decision:

- task label/classification;
- fresh base/master and final HEAD;
- capability classification/reuse;
- exact changed paths;
- observable product utility delta;
- focused tests/E2E;
- runtime/provider/browser/public-write scope;
- actual artifact refs when applicable;
- safety counters;
- remote readback;
- exact residual caveat/blocker.

Do not create giant evidence packets as ceremony. Do not duplicate mutable project status across
multiple hand-maintained files.

---

## 19. Operator audit — thin and independent

Builder PASS is a claim, not merge authority.

Operator independently verifies only the hard gates necessary for the claim: fresh base/head, exact
diff, critical authority semantics, focused tests/CI, runtime evidence when runtime matters, actual
article/video/UI when quality matters, public-write/browser/network scope, safety counters, and exact
residual caveat.

Do not reproduce Builder's entire debugging process.

If a defect is simple Git-only work and GitHub can safely repair it, use the GitHub lane instead of
spending another Codex session.

---

## 20. Git / merge discipline

Normal implementation flow:

`fresh master -> task branch/worktree -> scoped edits -> validation/runtime -> commit -> push -> PR -> independent Operator audit -> protected merge`

Never force-push, use `git add .` / `git add -A`, reset unrelated work, or destroy a valid worktree to
restart a model session.

Stage explicit paths. Builder may commit/push/update the PR. Builder does not merge master. Operator
may merge after independent audit and required checks. After merge, fresh-read remote master.

`MERGED != RUNTIME PROVEN` and `MERGED != PUBLICLY PUBLISHED`.

---

## 21. Anti-starvation diagnostics

Safety must not become indefinite inactivity.

Maintain enough diagnostics to explain output conversion, such as:

- candidate universe size;
- sourceable/ready candidates;
- article attempts;
- hard-gate failures;
- soft-repair counts;
- qualified/published article counts;
- derivative completion;
- provider failures;
- request/token cost;
- candidate abstention reasons;
- production-day deficit reasons.

A zero-output day requires an explainable blocker distribution.

Do not solve starvation with filler, invented facts, weaker evidence, fake analysis, or weakened
rights/permission gates. Improve discovery, candidate choice, evidence acquisition, article
conversion, packaging, and economics instead.

---

## 22. Runtime truth is separate from Git

Git can establish source state, diff, merged architecture, and static authority.

Git alone cannot establish Codex Desktop state, provider quota/availability, live Daily App state,
browser account identity, current Automation state, public-write outcome, readback/reconciliation,
or rendered media quality.

A commit is not runtime proof. CI is not public-write proof. Configuration is not host state.

---

## 23. Status-drift control

Maintain minimal mutable routing authority.

After material transitions, fresh-read master, update only current authority/pointer surfaces that
actually need it, demote incompatible historical routing, and preserve historical evidence.

Do not create another mutable status ledger to fix stale status ledgers. CodeGraph is a
navigation/provenance aid, not independent product authority.

---

## 24. Owner interruption policy

Do not ask Jim routine engineering questions.

Operator/Builder resolve ordinary implementation detail, retries, dependencies, branch handling,
focused tests, validator mechanics, model/session routing, and reversible Git operations.

Interrupt Jim only for genuine owner boundaries: credential/login/manual authentication, public-write
expansion, material product choice, new paid spend, rights/legal decision, destructive canonical
action, material Capital Chronicle numeric-authority change, unresolved wrong-account/
`UNKNOWN_WRITE`, or V2 public-write expansion.

---

## 25. Time-sensitive newsroom preemption

A genuine time-sensitive story may preempt documentation cleanup, governance ceremony, architecture
polishing, backlog grooming, or repeated rehearsal when delay would destroy reader value or
prospective evidence.

The story still must pass hard truth/evidence/authority gates.

---

## 26. Anti-red-tape survival test

A workflow step survives only if it does at least one of:

- prevents a material truth defect;
- prevents Capital Chronicle numeric-authority corruption;
- protects rights/security/public-write boundaries;
- resolves `UNKNOWN_WRITE`;
- establishes otherwise unavailable evidence;
- prevents duplicate work;
- prevents meaningful authority drift;
- materially improves reproducibility;
- materially lowers future operating cost;
- materially improves reader/viewer product quality.

Otherwise:

`REMOVE IT`, `FOLD IT INTO THE PARENT TASK`, or `ROUTE IT TO A CHEAPER LANE`.

---

## 27. Product North Star

V1 must become a reliable autonomous growth newsroom capable of producing **5–8 useful canonical
published articles per newsroom production day** without filler and without weakening truth.

V2 must become an isolated retention-native video growth factory built on rights-safe,
`CONCRETE_FIRST_ABSTRACT_SECOND` media and qualified source truth.

Engineering, evidence, models, and governance exist to move those products toward real
readers/viewers and measurable learning.

If a process does not improve truth, product quality, launchability, operational reliability,
learning, or economics, it is probably not current product work.
