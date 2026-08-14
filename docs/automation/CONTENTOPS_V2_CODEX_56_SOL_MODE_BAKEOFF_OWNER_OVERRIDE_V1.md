# Capital Chronicle ContentOps V2 — Codex 5.6 Sol Mode Bakeoff Owner Override V1

Authority date: 2026-08-14
Status: `CURRENT_OWNER_OVERRIDE / CURRENT_V2_CODEX_MODE_SELECTION_AUTHORITY`
Owner: Jim
Applies to: Lane B Hybrid V2 creative-brain execution

## 1. Owner decision

The Lane B Hybrid architecture is already locked. The remaining Codex creative-brain **mode** is intentionally NOT locked yet.

During V2 build-out, Capital Chronicle will run a controlled quality/cost bakeoff across the owner-specified Codex 5.6 Sol modes:

- `HIGH`
- `XHIGH` / `EXTRA_HIGH`
- `ULTRA`

These labels express the owner's intended comparative modes. The builder must discover and record the exact supported local Codex CLI/SDK/config identifiers non-secretly at runtime. If the actual identifiers differ, map them explicitly to these owner labels instead of guessing or silently substituting.

The owner expects ULTRA to consume materially more quota and to have the highest nominal capability ceiling, but **no production mode is selected by assumption**. Actual media quality, reliability, revision burden, wall-clock, and quota/cost evidence decide value.

Jim + ChatGPT are the owner-level acceptance gate for this bakeoff. Codex/builders/critics may report evidence but may not self-select the canonical production mode.

## 2. Why this bakeoff exists

The Lane B A/B proof showed that Codex can produce the highest current visual ceiling, but the proof did not establish which Codex reasoning/capability mode provides the best production economics.

Selecting ULTRA everywhere merely because it is strongest could waste quota if XHIGH or HIGH produces essentially equivalent publishable video through the same hardened deterministic engine.

Selecting HIGH merely because it is cheaper could be false economy if it increases:

- weak editorial structure;
- layout/motion defects;
- visual-revision rounds;
- failed renders;
- owner review time;
- total wall-clock;
- non-publishable outputs.

The optimization target is therefore **total product value per scarce quota/cost**, not minimum token usage and not maximum model strength in isolation.

## 3. Canonical benchmark principle

The comparison must isolate Codex mode as much as practical.

Hold constant across modes:

- exact governed article/story input;
- exact evidence snapshot and hashes;
- exact Truth/Analysis/Engagement constraints;
- exact target format;
- exact Lane B Hybrid design-system version;
- exact reusable primitive set;
- exact asset candidate universe available at run start;
- exact visual-safety rules;
- exact audio/tooling policy;
- exact revision budget;
- exact zero-public-write boundary;
- exact evaluation rubric.

Each mode receives a **fresh isolated execution/thread** with no cross-mode conversational contamination.

Each mode receives its own immutable run ID, receipts, artifacts, and cost/runtime ledger.

Do not let one mode see another mode's creative output before the owner comparison is complete.

## 4. What must actually be compared

Do not compare only prose, plans, token counts, or critic summaries.

The owner decision requires actual rendered media evidence.

For the first controlled mode bakeoff, the preferred bounded comparison is:

1. stabilize the shared Hybrid deterministic engine enough that all three modes use the same implementation baseline;
2. use one identical qualified benchmark story/job packet;
3. run HIGH, XHIGH, and ULTRA independently;
4. produce one native 45–60 second 9:16 clean-master candidate from each mode;
5. preserve the same factual/evidence authority and comparable asset availability;
6. render actual MP4s;
7. produce phone-scale/contact-sheet/motion-strip evidence;
8. measure runtime/quota/cost/retries/revision burden;
9. stop at an owner gate;
10. Jim + ChatGPT review the three actual videos and choose the next operating policy.

A mode that fails a blocking deterministic/storyboard/comprehension gate does not need an expensive final render merely to complete a quota. Record the failure honestly.

The initial mode bakeoff does not need to render three full midforms unless the short comparison is inconclusive. If two modes are effectively tied after short-form review, the owner may authorize a second-stage midform comparison between only those finalists.

This staged tournament is intended to reduce opportunity cost while still making the decision from real media.

## 5. Evaluation dimensions

Keep a quality score and an efficiency score separately; do not hide a quality collapse behind low cost.

### 5.1 Media/product quality

Evaluate actual output on at least:

- one-watch comprehension;
- hook strength and retention promise;
- institutional analytical depth;
- conversational pacing;
- truth/evidence discipline;
- visual hierarchy;
- composition/alignment;
- motion craft;
- scene continuity;
- typography/readability;
- document/chart treatment;
- asset selection/diversity;
- absence of template feel;
- controlled financial wit where used;
- Capital Chronicle brand fit;
- professional/publication potential.

### 5.2 Operational efficiency

Measure where actually exposed:

- quota consumed;
- token/usage telemetry;
- wall-clock;
- number of Codex invocations;
- provider/tool retries;
- number of storyboard/proxy/full renders;
- mechanical corrections;
- creative revision rounds;
- owner/operator intervention;
- failure/recovery behavior;
- total job TCO where measurable.

Do not fabricate cost if the local Codex environment does not expose exact billing/quota units.

## 6. Selection logic

Do not require one universal mode if evidence supports a tiered policy.

Possible owner outcomes include:

### A. One canonical default

Choose the lowest-cost mode that reliably meets the public-quality bar with no material quality loss versus higher modes.

### B. Daily/default + flagship escalation

Example policy shape, only if evidence supports it:

- `DAILY_DEFAULT`: XHIGH or HIGH;
- `FLAGSHIP/COMPLEX_ESCALATION`: ULTRA;
- lower tier may be used for bounded diagnostics/planning where viewer-visible final quality is not at risk.

### C. ULTRA default

Valid if ULTRA produces a material, repeatable improvement that justifies its higher quota/TCO and substantially reduces downstream revision/owner effort.

### D. HIGH default

Valid only if HIGH repeatedly reaches the same owner-accepted quality ceiling and the higher modes do not justify their extra cost/quota.

No mode policy becomes canonical until Jim + ChatGPT explicitly accept it after actual-media comparison.

## 7. H1 interaction

The current task remains:

`TASK_CONTENTOPS_V2_LANE_B_HYBRID_INSTITUTIONAL_EDITORIAL_ENGINE_AND_HEADLESS_TRIGGERED_VERTICAL_SLICE_V1`

However H1 now contains a mandatory owner-gated mode-selection checkpoint.

### H1-A — build shared Hybrid engine to comparable state

Implement enough of:

- durable candidate/job;
- institutional analytical engine;
- visual-safety compiler;
- Lane B primitives;
- asset diversity;
- storyboard/proxy;
- isolated fresh Codex execution;
- cost/runtime ledger;
- clean-master rendering;

to support a fair mode comparison.

### H1-B — HIGH/XHIGH/ULTRA controlled short bakeoff

Run the same immutable benchmark input through all three owner-specified modes under the fair-comparison contract.

Required result before owner review:

`PASS_CODEX_MODE_BAKEOFF_MEDIA_READY_FOR_JIM_CHATGPT_REVIEW`

Return three actual short MP4s when all modes are viable, plus complete comparable evidence.

### OWNER GATE

STOP.

Jim + ChatGPT inspect actual media and cost/quota evidence.

They decide:

- canonical daily/default mode;
- whether an ULTRA escalation tier exists;
- whether a second-stage midform bakeoff is necessary;
- or whether the mode evidence is inconclusive and needs one bounded rerun.

The builder must not self-advance through this gate.

### H1-C — finish full Hybrid vertical slice with owner-selected mode policy

Only after owner selection, resume H1 to produce the full institutional/editorial/headless vertical-slice owner-review package under the selected mode policy.

This owner gate is a legitimate split because the decision depends on actual media quality and quota/value judgment that only Jim + ChatGPT may make.

## 8. Anti-confounding rules

Do not invalidate the bakeoff by allowing modes to receive materially different production conditions.

Forbidden during the fair comparison:

- one mode receiving a better asset universe;
- one mode receiving extra manual creative fixes not granted to others;
- different evidence snapshots;
- different design-system versions;
- different revision budgets;
- one mode inheriting another mode's output;
- changing prompt/content contract halfway through one run only;
- choosing the winner from critic scores without owner media inspection.

Mechanical fixes to a shared deterministic compiler should, where practical, be applied equally before rerunning affected comparisons.

## 9. Provenance

Every mode run must record:

- owner label: HIGH / XHIGH / ULTRA;
- exact local Codex model/mode identifier actually invoked;
- Codex version/build if available non-secretly;
- fresh execution/thread/run identity;
- immutable input hash;
- creative artifact hashes;
- final media hashes;
- revision history;
- runtime/quota/cost telemetry;
- deterministic engine commit/version;
- asset manifest hash;
- public_write=false.

Never log credentials/session material.

## 10. Current safety

`ZERO_VIDEO_PUBLIC_WRITE_AUTHORITY` remains unchanged.

The bakeoff is local/shadow evidence only.

Do not:

- upload any candidate;
- create private/unlisted platform objects;
- mutate V1 runtime/publication state;
- use a shared persistent Codex conversation;
- expose Codex authentication/session data.

## 11. Durable summary

**Lane B Hybrid is locked, but the Codex 5.6 Sol operating mode is intentionally not locked. During H1, build one shared deterministic Hybrid engine and run a fair HIGH vs XHIGH vs ULTRA short-form media bakeoff. Jim + ChatGPT compare actual videos plus quota/TCO evidence and select the daily/default and any escalation policy. ULTRA is not automatically selected just because it is strongest; HIGH/XHIGH are not automatically selected just because they are cheaper. The objective is the best reproducible public-quality value.**
