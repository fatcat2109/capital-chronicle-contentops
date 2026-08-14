# Capital Chronicle ContentOps V2 — Fresh Chat / Builder Handoff V1

Authority date: 2026-08-14
Status: `CURRENT_V2_FRESH_SESSION_HANDOFF`
Product direction: `LANE_B_HYBRID`
Codex mode state: `OWNER_BAKEOFF_REQUIRED / NO_CANONICAL_MODE_SELECTED`

Purpose: allow a completely fresh ChatGPT/Codex session to continue V2 correctly without access to prior conversations, local builder memory, or the owner's chat history.

Repository-state authority is always fresh GitHub refs/commits/diffs/exact bytes. Jim's latest explicit instruction is product-direction authority. Fetch current `master` and relevant task branch before acting; SHAs in this handoff are historical clues only.

# 1. Repository

GitHub:

`fatcat2109/capital-chronicle-contentops`

Canonical Windows checkout historically used:

`A:\Capital Chronicle\ContentOps`

V1 and V2 may run concurrently but must remain isolated.

Do not trust local branch state until fetched and reconciled.

# 2. Fresh read order

1. `AGENTS.md`
2. `docs/codegraph/INDEX.md`
3. `docs/codegraph/V2_CONTEXT.md`
4. `docs/automation/CONTENTOPS_V2_RETENTION_NATIVE_VIDEO_FACTORY_NORTH_STAR_V2.md`
5. `docs/automation/CONTENTOPS_V2_RETENTION_NATIVE_VIDEO_FACTORY_MASTER_PLAN_V2.md`
6. `docs/automation/CONTENTOPS_V2_RETENTION_NATIVE_VIDEO_FACTORY_TASK_GRAPH_V2.md`
7. `docs/automation/CONTENTOPS_V2_LANE_B_HYBRID_OWNER_DECISION_AND_AB_AUDIT_V1.md`
8. `docs/automation/CONTENTOPS_V2_CODEX_56_SOL_MODE_BAKEOFF_OWNER_OVERRIDE_V1.md`
9. `docs/automation/CONTENTOPS_V2_RETENTION_NATIVE_VIDEO_FACTORY_CURRENT_EXECUTION_POINTER_V2.md`
10. `docs/automation/CONTENTOPS_V2_REMOTION_AGENT_SKILL_BASELINE_V1.md`
11. nearest scoped `AGENTS.md`
12. exact task code/tests/evidence.

Because ChatGPT wrote current authority directly to remote `master`, local CodeGraph/generated context may temporarily be stale. Regenerate/check CodeGraph after syncing and require `CODEGRAPH_CURRENT` before implementation commit.

# 3. What happened before this handoff

## 3.1 R4 failed systemically

R4 branch:

`task/tier2-v2-gpt56-creative-code-asset-rich-video-v1`

R4 reference HEAD:

`2289eb1382e65474207b50d27c0b87626d30728f`

Classification:

`FAIL_SYSTEMIC_VISUAL_STORYTELLING_ARCHITECTURE / NEGATIVE_CREATIVE_REFERENCE_ONLY`

R4 had technically valid media but relied too heavily on bespoke abstract geometry and symbolic grammar. Jim could not quickly understand what many visuals represented. Examples included abstract Hormuz/opening treatment, valves/droplets/basins, and weak native chart composition.

Do not patch or reuse R4 creative blueprint/generated shot grammar. Reuse only useful engineering such as evidence, rights/provenance, audio, sandbox, cache/selective rerender, and QA where still compatible.

## 3.2 Concrete-first replacement was built

The replacement task introduced:

`CONCRETE_FIRST_ABSTRACT_SECOND`

It added/strengthened:

- real/contextual geography and oil infrastructure;
- primary EIA evidence;
- native chart/map/document treatment;
- storyboards/captions-hidden comprehension;
- asset brokerage;
- model-authored motion code;
- isolated V2 provider execution.

## 3.3 9Router `new/...` XHIGH route was unreliable for large creative outputs

A minimal/raw-call experiment proved that tiny/small calls could work but exact large Director calls repeatedly hit gateway/response-bridge failures on the `new/gpt-5.6-sol-xhigh` route.

Jim authorized testing:

`cx/gpt-5.6-sol(xhigh)`

The CX route successfully returned large Director/segment/motion outputs and completed the controlled Lane A proof.

This provider lesson remains useful, but the product architecture is no longer model-first Lane A.

## 3.4 A/B proof was completed

A/B task branch:

`task/v2-concrete-first-xhigh-replacement-vertical-slice-v1`

A/B proof commit:

`29c604ff5c920a78dca43578c8d1c503a5c0277e`

Commit message:

`v2: prove cx xhigh and codex builder video lanes`

Two lanes were produced on the same EIA/Hormuz benchmark.

### Lane A — CX XHIGH

Creative brain:

`cx/gpt-5.6-sol(xhigh)` via 9Router.

Strengths:

- lower direct generation cost;
- strong analytical density;
- evidence-grounded Director/segments;
- generated motion code;
- much better than R4.

Weaknesses:

- subtitle clutter;
- alignment/annotation/layout defects;
- asset repetition;
- dense scenes;
- lower final visual polish than the best Lane B scenes;
- compatibility/projection work around model output.

Jim estimated Lane A generation cost around half Lane B in this controlled comparison. Treat that as owner-observed benchmark context, not a permanent price guarantee.

### Lane B — Codex Builder

Creative brain:

Codex Builder.

Authentic Lane B visual signatures included:

Short:

- `ONE CHOKEPOINT. FOUR TESTS.`
- `MapToVessel`
- `THE PHYSICAL CHAIN`
- `UNLOAD / RESTORE / REBUILD`
- `FORECAST. NOT A RESULT.`
- native forecast chart
- illustrative transmission
- consequence cards
- confirm/challenge test
- checkpoint close.

Midform:

- `THE PERSIAN GULF HAS ONE NARROW EXIT.`
- map/vessel transition
- physical chain
- `A SHIP PAST HORMUZ IS NOT RESTORED SUPPLY.`
- evidence/document/chart
- transmission/consequence/test/checkpoints.

Lane B produced the highest current visual ceiling. Jim judged its latter half close to publishable, while the first half and some earlier iterations still exposed layout/crop/alignment problems.

The proof required too many interactive builder repair cycles to be considered production architecture.

# 4. Owner decision after authentic four-video review

Canonical architecture is:

`LANE_B_HYBRID`

The decision is not “Codex manually does everything forever.”

It is:

> **Fresh per-video Codex execution owns high-entropy creative/editorial intelligence and actual-media review; deterministic local V2 infrastructure owns durable orchestration, evidence, visual safety, reusable primitives, rendering, QA, recovery, cost, and publication boundaries.**

Lane A/CX is retained as a lower-cost shadow benchmark and possible alternative brain after the shared Hybrid engine exists.

# 5. New owner instruction: Codex mode is NOT locked

The architecture decision above is final for now, but the exact Codex 5.6 Sol operating mode has deliberately not been selected.

Jim requires a controlled bakeoff across owner-specified modes:

- `HIGH`
- `XHIGH / EXTRA_HIGH`
- `ULTRA`

ULTRA is expected by the owner to consume the most quota and to have the highest nominal capability ceiling, but that does **not** make it the automatic production default.

The objective is to determine which mode gives the best **reproducible public-quality value**.

The builder must first discover the exact locally supported Codex mode/config identifiers and explicitly map them to the owner labels. Do not guess names. Do not inspect or expose authentication/session material.

## 5.1 Fair comparison rules

Hold constant across modes:

- exact governed article/story;
- exact evidence snapshot;
- immutable creative input packet;
- exact shared Hybrid engine commit/version;
- same design tokens/primitives;
- same asset candidate universe available at run start;
- same visual-safety compiler;
- same output format;
- same revision budget;
- same audio/tooling policy;
- same zero-public-write boundary;
- same evaluation rubric.

Each mode must run in a **fresh isolated execution/thread**.

A mode may not see another mode's creative output before the owner comparison is complete.

## 5.2 First-stage media bakeoff

Preferred bounded experiment:

1. stabilize the shared Hybrid engine to the point where mode is the main changed variable;
2. choose one identical qualified benchmark story/job packet;
3. run HIGH independently;
4. run XHIGH independently;
5. run ULTRA independently;
6. produce one native 45–60 second 9:16 clean master per viable mode;
7. create contact sheets/motion strips/phone-scale evidence;
8. capture quota/usage/wall-clock/retries/revision burden;
9. stop for Jim + ChatGPT actual-media review.

If a mode fails a blocking deterministic/storyboard/comprehension gate, it does not need an expensive final render just to fill the comparison table. Preserve the failure evidence.

Do not automatically render three midforms. If the short comparison is inconclusive, Jim may authorize a second-stage midform comparison only between finalists.

## 5.3 Owner selection gate

Builder/critic may not self-select the winner.

Jim + ChatGPT decide after actual-media review whether the production policy should be:

- one universal default mode;
- HIGH or XHIGH daily/default with ULTRA escalation for flagship/complex jobs;
- ULTRA default if the quality/revision benefit materially justifies quota/TCO;
- another evidence-backed tiered policy.

Quality and efficiency should be scored separately.

Quality dimensions include:

- one-watch comprehension;
- hook/retention;
- institutional analytical depth;
- conversational pacing;
- truth/evidence discipline;
- visual composition;
- motion craft;
- typography/readability;
- document/chart treatment;
- asset diversity;
- template feel;
- wit quality where used;
- Capital Chronicle brand fit;
- publication potential.

Efficiency dimensions include:

- quota/usage;
- wall-clock;
- Codex invocation count;
- retries/failures;
- storyboard/proxy/full render count;
- mechanical corrections;
- creative revision count;
- owner/operator intervention;
- total TCO where measurable.

# 6. Canonical creative/control responsibility

## Codex owns

- video angle after article qualification;
- institutional analytical map;
- narrative architecture;
- narration;
- hook/re-hooks/payoff;
- controlled financial wit;
- asset-purpose strategy;
- storyboard strategy;
- novel scene/motion code where primitives are insufficient;
- actual proxy/full-media review;
- bounded localized creative revision.

## Deterministic local engine owns

- V1 candidate intake;
- durable outbox/job state;
- evidence/numeric authority;
- rights/provenance;
- visual design tokens;
- reusable scene primitives;
- visual-safety compiler;
- native chart/map/document compilers;
- caption policy;
- asset diversity policy;
- TTS/music/SFX tool execution;
- Remotion render;
- deterministic QA;
- cache/selective rerender;
- stage resume;
- cost/runtime telemetry;
- final package identity;
- publication authority.

# 7. No persistent Codex session

Do not implement a 24/7 Codex conversation.

Canonical execution:

```text
durable qualified job
→ fresh isolated Codex run/thread
→ explicit stage artifacts
→ bounded revision within same job
→ terminate when complete/blocked/failed
```

State lives in artifacts/ledger, not hidden conversation history.

The HIGH/XHIGH/ULTRA comparison must also use one fresh isolated run/thread per mode.

# 8. Institutional editorial target

V2 must become deeper than the A/B oil proof without becoming an academic lecture.

Every story should separate:

- **Truth Layer** — facts, observations, forecasts, exact data, sources;
- **Analytical Layer** — mechanisms, second-order transmission, balance-sheet/cash-flow effects, scenarios, confirm/challenge logic;
- **Engagement Layer** — hook, pacing, contrast, re-hooks, analogy, controlled wit.

Engagement never alters truth.

Midform should ask, where supported:

- what changed?;
- what has not changed?;
- what mechanism matters?;
- what is priced/expected?;
- who gains/loses?;
- what balance sheet/cash flow changes?;
- what second-order channels matter?;
- what confirms?;
- what challenges?;
- what to watch next?

Select only the highest-value mechanisms rather than filling a rigid checklist.

# 9. Financial wit target

Desired:

- dry;
- subtle;
- market-literate;
- mechanism-related;
- sparse.

Examples of tone only:

- “Markets can price a reopening in minutes. Inventories are less cooperative.”
- “Forecasts travel faster than crude.”

Do not use meme slang, cheap jokes, insensitive humor, unsupported facts, or advice-like language.

Use a bounded wit candidate + truth/relevance/tone validator. Zero jokes is valid.

# 10. Visual target

The **entire** video should be as strong as the best second-half Lane B scenes.

Permanent doctrine:

`CONCRETE_FIRST_ABSTRACT_SECOND`

Positive primitives to generalize:

- `MapToVessel`;
- `PhysicalChain`;
- `DocumentEvidence`;
- `NativeForecastChart`;
- `Transmission`;
- `Consequence`;
- `ConfirmChallenge`;
- `CheckpointTimeline`.

They are not a frozen template.

# 11. Visual defects that must be engineered out

Both A/B work exposed recurring defects that must move from manual fixes into the visual-safety system:

- duplicate native asset text plus overlay text;
- bad title/box alignment;
- guessed document highlight rectangles;
- source/footer overlap;
- caption clutter;
- phone-small text;
- crop/focal-object mistakes;
- repeated background imagery;
- excessive information density.

Canonical master should be clean without a permanent large subtitle card. Produce platform/sidecar captions and optional social-caption derivative separately.

# 12. V1 -> V2 future operating loop

Expected daily flow:

```text
V1 publishes useful articles
→ analytics/performance snapshots
→ candidate scorer
→ top qualified video opportunities
→ durable V2 outbox
→ Hybrid production
```

The goal is roughly the top one or two genuinely qualified daily opportunities when they exist, not forced conversion of every article.

Candidate scoring should combine engagement quality and video opportunity.

Engagement may influence priority/packaging only.

# 13. Current exact H1 task and owner gate

Current task:

`TASK_CONTENTOPS_V2_LANE_B_HYBRID_INSTITUTIONAL_EDITORIAL_ENGINE_AND_HEADLESS_TRIGGERED_VERTICAL_SLICE_V1`

It remains the active V2 task, but now has three bounded stages.

## H1-A — shared Hybrid engine

Build enough shared deterministic production capability to make the model-mode comparison fair:

- durable candidate/outbox fixture or read-only V1-style input;
- fresh isolated/headless Codex seam with selectable mode;
- institutional analytical map;
- conversational script;
- bounded wit pass;
- minimal Lane B primitives;
- visual-safety compiler;
- asset diversity tracking;
- storyboard/animatic comprehension gate;
- Remotion proxy/final render capability;
- actual-media review artifacts;
- stage ledger/resume;
- cost/runtime telemetry;
- zero public write.

## H1-B — HIGH/XHIGH/ULTRA actual-media bakeoff

Run one identical benchmark through all three owner-specified modes under the fair-comparison contract.

Required pre-owner result:

`PASS_CODEX_MODE_BAKEOFF_MEDIA_READY_FOR_JIM_CHATGPT_REVIEW`

Return actual short MP4 candidates and comparable evidence.

Then STOP for the owner mode gate.

## OWNER MODE GATE

Jim + ChatGPT inspect actual media and cost/quota evidence.

They decide:

- daily/default mode;
- any ULTRA escalation policy;
- whether a second-stage midform comparison is required.

The builder may not self-advance.

## H1-C — full Hybrid vertical slice

Only after owner mode selection should H1 resume to the full institutional/editorial/headless proof.

Pre-owner ceiling result:

`PASS_IMPLEMENTATION_MEDIA_READY_FOR_JIM_CHATGPT_REVIEW`

# 14. Next phases after H1

- H2: cross-domain/non-oil generalization.
- H3: live read-only V1 performance shadow trigger.
- H4: roughly ten-job Hybrid shadow soak.
- H5: fair Codex-vs-CX cost/quality benchmark through the same shared engine.
- V2-02: platform/publication expansion only after Hybrid quality/reliability proof and explicit Jim authorization.

# 15. Public-write boundary

Current invariant:

`ZERO_VIDEO_PUBLIC_WRITE_AUTHORITY`

No current V2 task may upload, draft, schedule, or otherwise mutate YouTube/TikTok/platform state.

V2 must not mutate/reset V1 runtime/store/scheduler/coordinator/browser/publication authority.

# 16. Builder workflow for the next task

Before editing:

1. inspect local status;
2. preserve unrelated work;
3. fetch origin;
4. verify fresh remote master;
5. fast-forward a clean checkout or create a new dedicated V2 worktree/branch from fresh master;
6. regenerate/check CodeGraph because current authority synchronization was written directly through GitHub;
7. use CodeGraph and nearest AGENTS;
8. inspect A/B proof source only as reference;
9. implement H1-A and H1-B as one bounded build-to-owner-gate slice;
10. use a fresh isolated Codex run/thread for each HIGH/XHIGH/ULTRA candidate;
11. explicit staging only;
12. commit/push task branch;
13. return actual mode-bakeoff media/evidence for owner review;
14. STOP at the mode-selection gate.

Do not hard-reset unrelated V1 work.

# 17. Durable summary

**V2 is Lane B Hybrid. Codex is the fresh episodic creative/editorial brain and actual-media reviewer. Deterministic local infrastructure is the durable production/control system. Institutional analytical depth, conversational retention pacing, controlled financial wit, concrete-first visual storytelling, and Lane B visual craft are the target. Lane A/CX remains a lower-cost shadow benchmark. The exact Codex 5.6 Sol operating mode is NOT selected: H1 must fairly compare owner-specified HIGH, XHIGH/EXTRA_HIGH, and ULTRA using the same shared engine and actual short-form MP4s. Jim + ChatGPT choose the daily/default and any escalation policy after seeing media plus quota/TCO evidence. Do not run a persistent Codex session, do not start V2-02, and do not grant public write.**
