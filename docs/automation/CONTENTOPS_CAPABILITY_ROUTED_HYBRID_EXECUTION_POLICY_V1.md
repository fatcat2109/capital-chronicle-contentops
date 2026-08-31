# Capital Chronicle ContentOps — Operator–Builder Workflow Doctrine V1

Status: `CURRENT_EXECUTION_POLICY`
Doctrine status: `DURABLE_CONTENTOPS_WORKFLOW_DOCTRINE`
Scope: `fatcat2109/capital-chronicle-contentops`
Authority class: `WORKFLOW / EXECUTION GOVERNANCE`
Mutable project status authority: `NONE`

This is the canonical ContentOps workflow policy at the existing mandatory-read path. It replaces the older execution-policy-only semantics without creating another policy/status ledger.

It does not own current Git SHA, branch/PR state, exact-next task, V1/V2 acceptance state, runtime/browser/provider/Automation state, public-write authority, or current capability classification. Resolve those from fresh repository authority and actual runtime/host evidence where required.

Jim's latest explicit instruction remains higher product authority. Nearest scoped `AGENTS.md` may tighten real truth/safety boundaries, but may not silently revive procedural ceremony or overgating that this doctrine explicitly removes.

Execution model: `CAPABILITY_ROUTED_HYBRID`.

---

## 1. Operating objective

Optimize:

`READER / VIEWER VALUE`
`+ PRODUCT LAUNCH VELOCITY`
`+ USEFUL CONTENT OUTPUT`
`+ LEARNING VELOCITY`
`+ RELIABILITY`
`+ QUALITY PER TOKEN / REQUEST / DOLLAR`
`+ MINIMUM PROCEDURAL LATENCY`

subject to hard:

`TRUTH + SOURCE/EVIDENCE + CAPITAL CHRONICLE NUMERIC AUTHORITY + RIGHTS + IDENTITY + PUBLIC-WRITE + SECURITY + UNKNOWN_WRITE`.

Do not optimize for the strongest model on every operation, the largest evidence packet, the most tests, the most validators, the most governance files, the most task IDs, or perfect rehearsal before useful product progress.

Governance survives only when it prevents a material defect, preserves authority, establishes otherwise unavailable evidence, prevents duplicate work, or materially lowers future operating cost.

**Governance itself is not product progress.**

---

## 2. FAST SHIP / completion-first

Default sequence:

`CORRECTNESS / COMPLETION -> REAL PRODUCT OUTPUT -> MEASURED ECONOMICS -> OPTIMIZATION`

Do not default to:

`PREMATURE BUDGET OPTIMIZATION -> PARTIAL FAILURE -> NEW TASK -> NEW PROOF -> REPEAT`.

Development/proof budgets must contain enough headroom to complete the capability coherently. Estimate expected usage from historical evidence and deliberately leave surplus. Proof ceilings are emergency runaway guards, not targets or success criteria.

When a task exposes a reversible implementation defect, default to:

`FIX -> FOCUSED TEST -> RERUN -> CONTINUE`

inside the same task/session.

Do not create `proof -> correction -> revalidation -> proof-of-proof -> final-proof` chains unless a genuinely different authority, environment, or irreversible boundary exists.

A task may stop for a real hard blocker. It must not stop merely because an arbitrary turn/token/request ceiling was reached while useful work, a safe fallback, or a clear reversible repair remains.

---

## 3. Execution lanes — route by evidence need

Use the cheapest lane capable of establishing the required truth.

### Hard execution order

For every task, audit, correction, next-task decision, or prompt request, use this order unless an earlier lane is technically incapable of establishing the required claim:

1. **ChatGPT + GitHub Connector / `WEB_STATIC` first.** Fresh refs, authority archaeology, code inspection, exact diffs, simple deterministic repository edits, branch/commit/PR operations, documentation/authority updates, and static audit belong here whenever the connector can complete them truthfully.
2. **GitHub Actions / `WEB_CI` next** for compile, focused tests, schema/contract checks, CodeGraph, deterministic builds, and other reproducible machine evidence.
3. Use another cheaper specialized lane only when it materially improves evidence quality or avoids scarce runtime spend.
4. **Codex Desktop / `CODEX_EXECUTION` is the second-last choice.** Spend Codex only on claims that genuinely require the Windows/local host, stateful runtime/debugging, provider/network behavior, browser/runtime state, local databases, actual article/video generation, rendered artifacts, or host Automation evidence that GitHub/CI cannot prove.
5. **Owner/operator intervention / `OWNER_GATED_EXTERNAL` is last.** Reserve it for credentials/login/manual authentication, public-write or irreversible authority, destructive canonical actions, legal/rights choices, secret/session access, or other genuine owner gates.

Before issuing any Codex task, the Operator must explicitly determine that GitHub Connector plus CI cannot complete the remaining claim. Do not spend Codex quota on repository reading, routine Git transport, CI babysitting, CodeGraph refresh, documentation editing, or waiting for a provider reset when those can be handled outside Codex.

### `WEB_STATIC`

Default for fresh refs/authority, Git/PR/history/CodeGraph archaeology, capability-history search, duplicate-work detection, exact diff/static architecture review, sequencing, documentation/authority maintenance, simple deterministic edits, and Git-only branch/commit/PR/merge operations within standing authority.

Do not spend Codex quota on work GitHub/static evidence can settle.

### `WEB_CI`

Use for deterministic machine feedback: lint, format, compile, typecheck, focused unit/integration tests, schema/contract validation, reproducible builds, CodeGraph generation/checks, and safe smoke tests.

CI proves only the checks it actually ran. CI does not prove Windows runtime state, browser state, provider availability, current Automation state, public-object identity, rendered visual/audio quality, or external-write success.

### `CODEX_EXECUTION`

Use Codex Desktop when correctness materially requires Windows/local runtime state, shell/worktree, environment/dependency work, stateful execution, provider/network behavior, iterative run-observe-debug cycles, browser/runtime inspection, local databases, actual article/video generation, performance/concurrency reproduction, rendered UI/video/audio, or tests unavailable from CI.

Codex is the execution-feedback lane. It is not the default repository reader, auditor, documentation editor, Git transport, CI watcher, or waiting room for a future quota reset.

### `OWNER_GATED_EXTERNAL`

Require explicit owner authority for credential/login/manual authentication, new or expanded public-write authority, wrong-account ambiguity, destructive canonical changes, secret/session access, material external/legal/rights decisions, new paid spend, material Capital Chronicle proprietary/numeric-authority expansion, V2 public-write authority expansion, or unresolved `UNKNOWN_WRITE`.

Static Git evidence must never substitute for runtime or public-write evidence.

---

## 4. Builder admission — reuse first

Before issuing a Codex task, Operator establishes:

`CURRENT AUTHORITY -> CURRENT IMPLEMENTATION -> HISTORICAL CAPABILITY EVIDENCE -> CURRENT DRIFT -> CAPABILITY CLASSIFICATION -> EXACT NEW DELTA`.

Use current ContentOps planning classes:

- `CURRENTLY_PROVEN_AND_REUSE`
- `HISTORICALLY_PROVEN_CURRENT_REVALIDATION_ONLY`
- `CURRENT_HOST_RUNTIME_PROOF_REQUIRED`
- `NEW_IMPLEMENTATION_GAP`
- `SUPERSEDED_DO_NOT_REUSE`

Historical artifacts remain evidence of what was built/run/proven at their epoch.

**NON-ROUTING != NON-EVIDENCE.**

Do not declare a capability missing merely because it has not been freshly revalidated, an old task folder is non-routing, a pointer no longer mentions it, or a model session lost context.

If the real delta is only revalidation, reuse, reconciliation, activation/routing of existing capability, authority update, prospective-evidence wait, or evidence closeout, do that instead of rebuilding.

A task name is never evidence that a capability is missing.

---

## 5. Every Codex packet declares conversation identity first

Before model or effort is specified, every Codex Builder packet must begin with:

- `CODEX DESKTOP CONVERSATION: CURRENT` or `CODEX DESKTOP CONVERSATION: FRESH`
- `CONVERSATION DECISION: <why CURRENT or FRESH is the lower-risk/lower-cost choice>`
- `MODEL: <explicit model>`
- `REASONING EFFORT: <explicit effort>`
- `REASONING CEILING: HIGH`

Operator chooses this. Do not return routine conversation/model selection to Jim.

Use minimum sufficient compute. Current ContentOps Codex execution is permanently capped at GPT-5.6 Sol HIGH: coordinator, editorial/creative worker, revision, and official fallback may not request XHIGH, ULTRA_HIGH, MAX, or any effort above HIGH. Historical evidence names are not current configuration.

`FRESH` is the default when the current Codex Desktop conversation is materially long, context-bloated, stale, a prior task has closed out, architecture/product direction changed, a new capability begins, V1/V2 truth planes switch, or independent reasoning is valuable. If uncertain between CURRENT and FRESH, choose FRESH.

Use `CURRENT` only when the same still-open task has valuable live debug/runtime state or recent local reasoning that would be materially expensive or risky to reconstruct. Same branch/worktree/PR does **not** by itself require CURRENT.

Conversation continuity and Git continuity are orthogonal. A `FRESH` Codex Desktop conversation may and often should continue the exact same branch/worktree/PR after reconstructing from fresh repository authority. Conversation context is disposable; Git state is durable.

---

## 6. One product slice over microtask chains

Prefer one coherent end-to-end task that produces observable reader/viewer/operator utility.

Fold small schema work, deterministic normalization, focused tests, exact current-authority updates, compact evidence closeout, CodeGraph refresh, commit/push/PR into the parent slice when safe.

Do not create separate tasks by default for wording cleanup, metadata normalization, one retry, one tiny compatibility fix, evidence packaging alone, status/SHA refresh, repeated architecture audits, or rerunning proofs whose assumptions remain valid.

Split only for a real independent boundary: credentials, public write, destructive production state, rights/legal, V1/V2 isolation, Capital Chronicle numeric authority, materially different environment, or independently valuable deliverable.

---

## 7. Builder owns the debug loop

Once an admitted Builder task starts, Builder owns:

`inspect -> reproduce -> diagnose -> implement -> test -> inspect failure -> repair -> retest -> runtime proof where required -> exact-diff self-audit -> commit -> push -> remote readback -> STOP`.

Do not bounce ordinary engineering errors back to Operator after each attempt.

There is no arbitrary debugging-attempt limit.

**NO BLIND IDENTICAL RETRY.** Every expensive retry requires a new hypothesis, code/config/environment change, new evidence, or a justified transient provider failure. Prefer local deterministic repair before spending another HIGH/network/provider/browser call.

---

## 8. Anti-overgating test

Before keeping or adding any gate, ask:

> If this gate is removed, does material truth, source/evidence integrity, rights, security, Capital Chronicle numeric authority, public-write safety, destination identity, or `UNKNOWN_WRITE` risk materially increase?

If the answer is **NO**, default to:

`REMOVE IT`, `DETERMINISTICALLY AUTO-REPAIR IT`, or `DOWNGRADE IT TO WARNING`.

Do not preserve a gate merely because an old proof required it, it makes receipts cleaner, it enforces duplicate representations of the same text, it increases test counts, or it makes governance appear more institutional.

ContentOps is a production newsroom/growth system, not an acceptance-test generator.

---

## 9. Article gates — hard vs soft

### Hard article gates

Remain fail-closed for:

- fabricated or unsupported **material** fact;
- materially unsupported causality;
- fake/unbound quotation;
- materially misleading stale event state;
- unsupported factual numeric claim;
- proprietary probability/forecast/scenario/regime/valuation/decision claim without exact Capital Chronicle publication authority;
- invalid source identity or materially insufficient evidence for the claim being made;
- rights/permission/publication-authority failure;
- wrong destination/account;
- secret/session exposure;
- `UNKNOWN_WRITE`.

### Soft / auto-repair concerns

Where public factual meaning is unchanged, normally normalize, drop, or warn rather than trigger another writer turn or terminal article rejection:

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

A soft representation/metadata warning must not become a launch blocker unless it creates a real reader-facing truth, identity, rights, or publication defect.

---

## 10. Candidate failure must not starve V1

Candidate-level abstention is valid.

A candidate hard failure must not automatically terminate the production opportunity, production day, or other governed ready candidates.

While useful eligible work remains:

`RECORD EXACT BLOCKER -> SKIP THAT CANDIDATE -> CONTINUE USEFUL CANDIDATE WALK`.

Do not manufacture filler and do not weaken evidence to hit volume. But do not let one over-strict candidate gate turn V1 into an abstention engine.

Quiet days lower materiality or change editorial mode before declaring the useful universe exhausted; they do not lower truth standards.

---

## 11. Throughput is a metric, not universal ceremony

Final V1 target remains **5–8 useful published canonical articles per newsroom production day**, without filler.

The four routine windows remain 17:00, 21:00, 23:00, and following 01:00 Bangkok. Do not create a fifth routine task merely to chase volume.

The historical `4 qualified articles / 32 derivative intents` proof remains useful throughput, production-day health, and regression evidence.

It is **not a universal prerequisite** before every useful article, repair, merge, or launch-progress decision. A safe qualified article may advance product acceptance independently. One article failure does not invalidate unrelated proven discovery/publication/runtime capability.

Do not hold V1 launch progression hostage to perfect ceremonial 4/32 rehearsal when remaining failures are soft representation/metadata defects rather than truth/safety defects.

Optimize throughput economics after the canonical article path works reliably, not by prematurely starving development proof.

---

## 12. Evidence burden is claim-proportional

Ordinary reporting does not require institutional-research-level ceremony.

For a narrow ordinary factual article, one exact trustworthy source may be sufficient when it directly proves the central proposition.

Require stronger evidence for disputed facts, allegations, causal claims, material market-impact claims, broad analytical conclusions, or proprietary numeric/forecast/scenario language.

Models are never factual authority. Search output is never evidence authority. Discovery may locate a source; deterministic retrieval/exact bytes/provenance establish evidence.

Capital Chronicle/Core Analyzer exclusively owns proprietary analytical/numeric truth. ContentOps may make clearly labeled qualitative editorial inference from accepted public evidence, but may not represent it as Core Analyzer output.

---

## 13. V1, Speech Highlight Relay, V2, browser, and publication boundaries

V1 is the canonical newsroom/publication product. The lightweight Speech Highlight Relay is a
separate interim source-bound social derivative product. Main V2 is the isolated retention-native
video/channel-growth factory and is currently paused until Jim explicitly resumes it.

Never let V2 mutate/reset V1 production runtime/store, inherit V1 browser/public-write authority, or redefine Capital Chronicle truth. Generated V2 media is never factual authority.

Never let the Relay become another V1 editor, scheduler, store, publisher/publication coordinator,
browser owner, truth system, or model-routing owner. It may selectively reuse exact V2 media seams
without becoming V2 progress or inheriting V2 orchestration/model requirements. Current V1 article
publication authority does not include Relay video uploads; Relay output remains on
`PUBLICATION_HOLD` absent a later exact grant.

Preserve current browser roles:

- Chrome `CapitalChronicleBot`, CDP 9222: ingestion only.
- Edge `contentops-social-main`, CDP 9223: publication/media/readback and explicitly authorized observation only.

Do not use pyautogui, SendKeys, focus stealing, brittle UI selectors, private browser/session DB inspection, cookie/token extraction, or unsupported internals.

Canonical V1 lifecycle remains:

`evidence -> article -> validation -> optional rights-safe media -> Substack -> exactly eight V1 derivatives -> strict readback/reconciliation`.

`UNKNOWN_WRITE = STOP RETRY -> READ BACK -> RECONCILE`.

No model, automation, configuration, or execution lane grants public-write authority by implication.

---

## 14. Validation proportional to blast radius

Default validation:

- focused changed-path tests;
- exact affected integration tests;
- current authority/contract validation;
- one relevant E2E/smoke when the delta requires it.

Do not repeatedly run huge suites after small article/metadata/representation fixes.

Broad regression is justified when the diff materially touches shared evidence authority, Capital Chronicle numeric authority, durable production state, publication lifecycle, `UNKNOWN_WRITE`, common router/model contracts, scheduler/runtime, or broad cross-V1 architecture.

Previously accepted capabilities are not re-proven from zero on every task. Previously valid public canaries/model bakeoffs/external proofs are not repeated unless the new delta invalidates their relevant assumptions.

A large test count is not evidence quality by itself.

---

## 15. Actual artifact acceptance

When quality is the claim, inspect the actual viewer-facing artifact.

Tests prove mechanics. They do not prove article usefulness, visual quality, pacing, media novelty, chart legibility, audio quality, or viewer experience.

For article acceptance inspect actual prose, headline/dek, factual grounding, source use, reader utility, obvious repetition, and derivative packaging where relevant.

For V2/UI/video/audio acceptance inspect the actual rendered artifact.

---

## 16. Minimum-sufficient evidence and thin audit

A completed task normally needs only enough evidence for an independent merge/route decision: task label/classification, fresh base/head, capability reuse classification, exact changed paths, observable utility delta, focused tests/E2E, runtime/provider/browser/public-write scope, actual artifact refs when applicable, safety counters, remote readback, and exact residual caveat.

Do not create giant evidence packets as ceremony or duplicate mutable project status across many files.

Builder PASS is a claim, not merge authority. Operator independently verifies only the hard gates necessary for the claim: fresh base/head, exact diff, critical authority semantics, focused tests/CI, runtime evidence when runtime matters, actual artifact when quality matters, public-write/browser/network scope, safety counters, and exact residual caveat.

Do not reproduce Builder's entire debug loop.

---

## 17. Repository autonomy and Git discipline

Ordinary reversible repository operations inside the accepted roadmap do not require a **new per-operation owner authorization** after the Operator hard-gate audit has passed.

The Operator may create/update task branches and PRs, make ordinary commits/pushes, and merge an independently audited PR through the **normal protected-branch path** once **required checks pass**.

This autonomy does not expand product scope and does not authorize **bypassing branch protection**, **force-push**, mutation of protected history, secret/session access, **public/provider writes**, **destructive production/canonical-store** mutation, **Capital Chronicle proprietary/numeric-authority** expansion, **V2 public-write authority** expansion, or external/legal/rights release decisions.

Normal implementation flow:

`fresh master -> task branch/worktree -> scoped edits -> validation/runtime -> commit -> push -> PR -> independent Operator audit -> protected merge`.

Never use `git add .` / `git add -A`, reset unrelated operator work, or destroy a valid worktree merely to restart a model session.

Builder may commit/push/update the PR. Builder does not merge master. After merge, fresh-read remote master.

`MERGED != RUNTIME PROVEN` and `MERGED != PUBLICLY PUBLISHED`.

---

## 18. Anti-starvation diagnostics

Safety must not become indefinite inactivity.

Maintain enough diagnostics to explain conversion, including candidate universe, sourceable/ready candidates, article attempts, hard-gate failures, soft-repair counts, qualified/published articles, derivative completion, provider failures, request/token cost, candidate abstention reasons, and production-day deficit reasons.

A zero-output day requires an explainable blocker distribution.

Do not solve starvation with filler, invented facts, weaker evidence, fake analysis, or weakened rights/permission gates. Improve discovery, candidate choice, evidence acquisition, article conversion, packaging, and economics instead.

---

## 19. Runtime truth is separate from Git

Git can establish source state, diff, merged architecture, and static authority.

Git alone cannot establish Codex Desktop state, provider quota/availability, live Daily App state, browser account identity, current Automation state, public-write outcome, readback/reconciliation, or rendered media quality.

A commit is not runtime proof. CI is not public-write proof. Configuration is not host state.

---

## 20. Owner interruption and time-sensitive preemption

Do not ask Jim routine engineering questions. Operator/Builder resolve ordinary implementation detail, retries, dependencies, branch handling, focused tests, validator mechanics, model/session routing, and reversible Git operations.

Interrupt Jim only for credential/login/manual authentication, public-write expansion, material product choice, new paid spend, rights/legal decision, destructive canonical action, material Capital Chronicle numeric-authority change, unresolved wrong-account/`UNKNOWN_WRITE`, or V2 public-write expansion.

A genuine time-sensitive story may preempt documentation cleanup, governance ceremony, architecture polishing, backlog grooming, or repeated rehearsal when delay would destroy reader value or prospective evidence. The story still must pass hard truth/evidence/authority gates.

---

## 21. Anti-red-tape survival test

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

## 22. Product North Star

V1 must become a reliable autonomous growth newsroom capable of producing **5–8 useful canonical published articles per newsroom production day** without filler and without weakening truth.

The interim Speech Highlight Relay must turn clearly reusable, exactly sourced public speech into a
context-safe Capital Chronicle social package with low operator burden and no duplicate control
plane.

Main V2 remains a paused product direction. If Jim later resumes it, it must remain an isolated
retention-native video growth factory built on rights-safe `CONCRETE_FIRST_ABSTRACT_SECOND` media
and qualified source truth.

Engineering, evidence, models, and governance exist to move those products toward real readers/viewers and measurable learning.

If a process does not improve truth, product quality, launchability, operational reliability, learning, or economics, it is probably not current product work.
