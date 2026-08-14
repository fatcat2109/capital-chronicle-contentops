# Capital Chronicle ContentOps V2 — Retention-Native Video Factory Master Plan V2

Authority date: 2026-08-14
Product authority: `CONTENTOPS_V2_LANE_B_HYBRID_OWNER_DECISION_AND_AB_AUDIT_V1`
Plan status: `CURRENT_CANONICAL_V2_EXECUTION_PLAN`
Companion constitution: `CONTENTOPS_V2_RETENTION_NATIVE_VIDEO_FACTORY_NORTH_STAR_V2.md`
Companion decision record: `CONTENTOPS_V2_LANE_B_HYBRID_OWNER_DECISION_AND_AB_AUDIT_V1.md`

Current execution overlay (2026-08-15): build the canonical `30–60s` vertical short plus evidence-earned `5–45m` landscape longform as separate editorial products. The first actual substrate proof produced 56.739s 4K vertical and 559.300s 1080p landscape owner-review media with segment-cached local Kokoro build audio. Premium publication voice selection remains a later owner gate; two-minute midform is retired as a final deliverable.

# 0. Executive summary

Capital Chronicle V2 will be completed as a **Lane B Hybrid** system.

The canonical architecture is not “one LLM writes JSON then a fixed renderer animates it,” and it is not “keep an interactive Codex session alive forever and let it manually fix every render.” It combines the strongest properties demonstrated by the A/B proof:

- **Codex-quality editorial and visual judgment** for high-entropy creative decisions;
- **deterministic local infrastructure** for truth, persistence, layout safety, rights, rendering, QA, cost control, recovery, and publication boundaries;
- **reusable but non-rigid visual primitives** extracted from the strongest Lane B scenes;
- **institutional analytical depth** beyond the controlled oil benchmark;
- **social-retention pacing and restrained financial wit** rather than textbook narration;
- **conditional V1-to-V2 triggering** from real article performance rather than automatic conversion of every story;
- **fresh isolated Codex execution per video job**, not a 24/7 conversation;
- **zero video public-write authority** until separately granted.

The near-term product objective is one heavy vertical slice proving that the Hybrid architecture can generate a new shadow video end-to-end with the visual quality of the best Lane B scenes, materially less operator babysitting, durable resume behavior, and measurable cost/runtime.

# 1. Product problem

The A/B proof established two facts that must be reconciled rather than choosing one simplistically.

## 1.1 Lane A economics are attractive

The 9Router CX XHIGH lane was materially cheaper in the controlled test and capable of sophisticated evidence-grounded creative generation. It therefore remains strategically useful.

But its final visual quality was less consistent. Recurring problems included subtitle clutter, weak layout/alignment, annotation geometry, dense text, and repeated assets.

## 1.2 Lane B creative ceiling is higher

The Codex Builder lane produced the strongest current Capital Chronicle video language. Its best scenes are close to publishable.

But the proof required many interactive corrections:

- crop/matte fixes;
- document/layout repair;
- source-strip cleanup;
- CSS/grid corrections;
- repeated proxy inspection;
- multiple full renders;
- critic/recritic cycles.

This is not acceptable as the long-term unattended workflow.

## 1.3 The real product problem

The objective is therefore:

> **preserve Lane B's creative ceiling while converting repeated manual repair into durable product infrastructure.**

That makes the primary engineering problem a hybridization problem, not a model bakeoff problem.

# 2. Canonical end-to-end architecture

```text
V1 ARTICLE PUBLICATION
        ↓
V1 PERFORMANCE / ENGAGEMENT SNAPSHOTS
        ↓
VIDEO CANDIDATE SCORER
        ↓
QUALIFIED | DEFERRED | ABSTAINED
        ↓
DURABLE V2 OUTBOX / JOB LEDGER
        ↓
V2 SUPERVISOR CLAIMS EXACT JOB
        ↓
FRESH ISOLATED CODEX JOB / THREAD
        ↓
GOVERNED STORY + EVIDENCE LOCK
        ↓
INSTITUTIONAL ANALYTICAL MAP
        ↓
NARRATIVE / SCRIPT / WIT CANDIDATES
        ↓
VISUAL-GROUNDING PLAN
        ↓
RIGHTS-SAFE ASSET BROKER
        ↓
LANE B DESIGN SYSTEM + NATIVE COMPILERS
        ↓
STORYBOARD / KEYFRAMES / CHEAP ANIMATIC
        ↓
CAPTIONS-HIDDEN COMPREHENSION GATE
        ↓
CODEX NOVEL-SCENE AUTHORSHIP WHERE NEEDED
        ↓
REMOTION PROXY
        ↓
DETERMINISTIC QA + CODEX VISUAL REVIEW
        ↓
BOUNDED LOCALIZED REVISION
        ↓
FINAL SHORT / MIDFORM MASTER
        ↓
MEDIA / RIGHTS / AUDIO / PACKAGE QA
        ↓
OWNER / PUBLICATION GATE
        ↓
LATER EXACT-AUTHORIZED PLATFORM WRITE
        ↓
AUDIENCE RETENTION ATTRIBUTION
        ↓
BOUNDED PACKAGING / EDITORIAL LEARNING
```

# 3. Component boundaries

## 3.1 V1 Performance Adapter

Purpose: expose real article-performance snapshots to V2 without giving V2 authority over V1 publication truth.

Inputs may include:

- article ID;
- canonical public URL;
- publication timestamp;
- unique readers;
- dwell/read time;
- completion/depth;
- shares;
- comments;
- saves;
- subscriber conversions;
- engagement velocity;
- article topic/entity tags;
- V1 evidence references.

Rules:

- read-only from V2;
- no V2 mutation of V1 article state;
- performance signals may prioritize content but not change truth;
- missing analytics remain missing, not fabricated.

## 3.2 Video Candidate Scorer

Purpose: avoid wasteful conversion of every article.

Two score families:

### Engagement score

Potential signals:

- normalized reads;
- completion;
- dwell time;
- shares/saves;
- subscriber conversion;
- age-adjusted velocity.

### Video opportunity score

Potential signals:

- recognizable real-world entities;
- primary evidence/document availability;
- hard data/chart opportunity;
- concrete causal mechanism;
- second-order analytical consequences;
- tension/uncertainty;
- rights-safe media supply;
- novelty versus recent video portfolio;
- expected production cost/time.

Initial combined weights are calibration hypotheses, not constitutional constants.

The scorer may emit:

- `QUALIFIED_SHORT`;
- `QUALIFIED_MIDFORM`;
- `QUALIFIED_BOTH`;
- `DEFERRED`;
- `ABSTAINED`.

## 3.3 Durable V2 Outbox

Every qualified opportunity becomes a durable job row with immutable identity.

Minimum fields:

- `video_job_id`;
- source article ID/hash;
- source URL;
- trigger timestamp;
- performance snapshot hash;
- qualification reason;
- target format(s);
- priority;
- estimated cost class;
- current state;
- claimed-by/run ID;
- retry counters;
- last valid checkpoint;
- public-write authority = false by default.

Claiming must be atomic so two workers cannot process the same job concurrently.

## 3.4 V2 Supervisor

The supervisor is a small deterministic process.

Responsibilities:

- wake periodically/event-driven;
- claim one eligible job;
- validate kill switches/permissions;
- create isolated runtime/worktree/thread identity;
- invoke the creative-brain adapter;
- observe the stage ledger;
- retry only according to declared policy;
- quarantine hard failures;
- finalize successful packages;
- never become creative author.

The supervisor may be woken by Windows Task Scheduler or equivalent. Scheduling cadence lives outside creative logic.

# 4. Codex job architecture

## 4.1 Fresh job principle

Each qualified video gets a fresh Codex execution context.

Inputs are explicit files/artifacts, not previous chat memory.

The job may retain its own thread across:

- initial creative build;
- proxy review;
- one bounded localized revision.

After completion/block/failure, the thread terminates.

## 4.2 Why no persistent 24/7 session

A persistent conversation introduces:

- stale context;
- hidden state;
- difficult reproducibility;
- partial-write ambiguity;
- restart fragility;
- cost attribution problems;
- accumulated irrelevant history;
- weaker auditability.

The system should persist artifacts and receipts, not conversational memory.

## 4.3 CreativeBrain interface

Conceptual API:

```text
prepare_editorial_angle(job_packet)
build_analytical_map(evidence_packet)
write_script(analytical_map, format_contract)
propose_wit(script, tone_contract)
build_visual_plan(script, asset_manifest)
build_storyboard(visual_plan)
author_novel_scene(scene_contract)
review_proxy(review_packet)
revise_localized(defect_packet)
finalize_creative_manifest()
```

Every method emits an explicit immutable artifact and provenance record.

## 4.4 Canonical and shadow brains

```text
CodexJobBrain      → canonical primary
NineRouterCXBrain  → shadow / cost-quality benchmark
```

Do not maintain two independent renderer stacks. Both brains must eventually drive the same Hybrid control/render/QA system.

# 5. Institutional editorial engine

## 5.1 Editorial input packet

The creative brain receives a compact governed packet containing:

- article title/deck;
- article body or structured summary;
- claim/evidence IDs;
- exact numeric authority;
- observation/forecast boundaries;
- relevant primary sources;
- current date/time context;
- story entities;
- allowed analytical conclusions;
- prohibited unsupported conclusions;
- target platform/format;
- performance trigger context;
- current portfolio/topic concentration.

## 5.2 Analytical map artifact

Required sections where applicable:

- core question;
- observed change;
- unresolved condition;
- physical/institutional mechanism;
- first-order market effect;
- second-order channels;
- balance-sheet/cash-flow implications;
- countervailing forces;
- what is priced/expected when supported;
- confirmation signals;
- challenge/invalidation signals;
- next calendar/data checkpoints;
- evidence IDs for every factual branch.

The analytical map is not narration. It is the reasoning spine used to decide what deserves screen time.

## 5.3 Narrative architecture

Codex converts the analytical map into a format-native narrative.

### Short

Recommended shape:

- immediate concrete hook;
- one tension/question;
- one mechanism;
- evidence reveal;
- one second-order consequence;
- one challenge/watch condition;
- clean brand resolve.

### Midform

Recommended shape:

- hook with tension;
- mechanism setup;
- evidence layer;
- transmission layer;
- counter-case;
- confirmation framework;
- checkpoint/resolve.

These are flexible editorial patterns, not hard-coded scene counts.

## 5.4 Retention logic

Every beat should state:

- viewer question entering;
- new information delivered;
- visual proof/explanation;
- open loop created/closed;
- expected duration;
- reason for the next cut.

Avoid long exposition without a changing information state.

## 5.5 Controlled financial wit

A dedicated bounded pass proposes optional wit lines.

Validator checks:

- fact-preserving;
- relevant to mechanism;
- not insensitive;
- not meme-like;
- not advice;
- not used in primary-evidence scenes;
- not excessive.

Short: usually zero or one line.
Midform: usually zero to three.

# 6. Lane B design system

## 6.1 Purpose

The design system extracts the best Lane B craft into reusable safe primitives so Codex does not have to rediscover layout basics every run.

The design system must preserve creative freedom. It is a toolkit, not a fixed template.

## 6.2 Core design tokens

Create versioned tokens for:

- background/surface roles;
- ink/text roles;
- teal/copper/ivory accent roles;
- primary/secondary/source typography;
- portrait/landscape type scales;
- safe margins;
- source rail height;
- caption zones;
- spacing;
- borders/dividers;
- motion timing families;
- brand resolve behavior.

Do not allow arbitrary per-video token drift without an explicit creative reason.

## 6.3 Positive primitives

Initial reusable primitives:

### `MapToVessel`

Use for geographic chokepoint/route → real movement transition.

Provides:

- safe map crop;
- optional native-label suppression;
- controlled split/reveal;
- vessel/context panel;
- source attribution;
- mobile/widescreen variants.

### `PhysicalChain`

Use for causal multi-step physical mechanisms.

Supports:

- 2–5 steps;
- documentary visual per step;
- numbered state progression;
- semantic reveal timing;
- portrait stack / landscape row variants.

### `DocumentEvidence`

Use for primary-source evidence.

Provides:

- source/date header;
- excerpt crop;
- measured highlight;
- semantic boundary badge;
- safe attribution;
- slow evidence push where appropriate.

### `NativeForecastChart`

Use for observation/forecast comparisons.

Provides:

- direct labels;
- observation/forecast style distinction;
- portrait/landscape geometry;
- semantic line/point reveal;
- readable endpoint emphasis.

### `Transmission`

Use for second-order causal channels.

Can combine:

- generated illustrative background;
- deterministic nodes/edges;
- explicit `NOT EVIDENCE` disclosure where generated imagery is used.

### `Consequence`

Use for conditional outcomes.

Provides:

- bounded cards/rows;
- semantic status colors;
- conditional language support;
- structured reveal.

### `ConfirmChallenge`

Use for thesis testing.

Provides:

- confirm column/list;
- challenge column/list;
- readable short-form variant;
- no more text than phone-scale constraints permit.

### `CheckpointTimeline`

Use for observation windows and future data/calendar tests.

Provides:

- observed benchmark separated from future checkpoints;
- no implication that checkpoint date guarantees an event/outcome;
- brand resolve.

## 6.4 Novel-scene escape hatch

If no primitive fits the story, Codex may author a novel scene under the creative-code sandbox.

The novel scene must still obey:

- safe zones;
- source attribution;
- asset rights;
- no network/env/fs access during render;
- deterministic animation;
- text measurement rules;
- visual QA.

Novel scenes that recur successfully may later graduate into primitives.

# 7. Visual Safety Compiler

## 7.1 Why it exists

Both A/B lanes exposed errors caused by independent layers occupying the same frame:

- native asset labels;
- overlay labels;
- source rails;
- captions;
- highlight boxes;
- fixed absolute geometry.

This must be solved once in infrastructure.

## 7.2 Asset visual metadata

Each important asset may carry:

- focal-object bounding box;
- native text bounding boxes;
- native source/logo region;
- crop candidates by aspect ratio;
- forbidden overlay zones;
- semantic labels already visible;
- min readable crop/scale;
- orientation;
- resolution;
- rights/source metadata.

Metadata may be deterministic/manual at first and later assisted by computer vision, but cannot fabricate rights or factual meaning.

## 7.3 Layout slots

Create formal regions for:

- eyebrow;
- title;
- evidence excerpt;
- annotation;
- source attribution;
- caption;
- focal object.

Primitives must query layout slots rather than independently hard-code every coordinate.

## 7.4 Text measurement

Before render or at deterministic preflight:

- compute text bounds;
- reject overflow;
- cap lines;
- enforce minimum size;
- prevent title/source/caption overlap;
- prevent annotation boxes crossing outside evidence region;
- detect duplicate semantic labels where possible.

## 7.5 Native-label policy

If an asset already shows “Strait of Hormuz,” for example, the layout engine decides whether to:

- keep native label and reduce overlay;
- crop/mask native label and use one controlled overlay;
- use a different crop/asset.

Never default to triple labeling.

# 8. Asset broker and diversity

## 8.1 Candidate acquisition

Prioritize:

- official/public-domain sources;
- primary institutions;
- rights-clear archives;
- licensed/open media;
- generated illustration only for conceptual non-documentary needs.

## 8.2 Ranking

Rank candidates on:

- semantic fit;
- rights certainty;
- source authority;
- visual quality;
- orientation;
- focal-object size;
- crop viability;
- novelty versus already selected assets;
- documentary versus illustrative role;
- attribution needs.

## 8.3 Diversity budget

Track per final package:

- asset reuse count;
- cumulative screen time;
- repeated semantic role;
- consecutive reuse;
- near-duplicate similarity.

Initial heuristics:

- a single asset normally <~15% screen time unless deliberately recurring as a motif;
- no consecutive same-background scenes by default;
- repeated asset must serve a different semantic purpose/crop;
- major concepts should have alternates if available.

# 9. Chart/map/document compilation

## 9.1 Maps

Maps must preserve recognizable geography.

Support:

- labels;
- route arrows;
- focal-region emphasis;
- portrait/landscape reframes;
- native label suppression if duplicate overlays are necessary;
- source attribution.

## 9.2 Charts

Generate from structured data when possible.

Support:

- direct labels;
- forecast/observation distinction;
- responsive typography;
- focused windows;
- semantic highlights;
- portrait composition;
- landscape composition.

## 9.3 Documents

Generate evidence-safe crops from known source text.

Support:

- excerpt selection;
- measured highlight region;
- date/source;
- explicit evidence status;
- native format variants.

# 10. Storyboard and proxy-first workflow

## 10.1 Storyboard

Before expensive motion code, generate keyframes for every material beat.

Each keyframe records:

- beat ID;
- viewer takeaway;
- focal object;
- selected asset;
- headline/annotation;
- source treatment;
- expected transition.

## 10.2 Captions-hidden animatic

Build a cheap animatic/proxy with scratch/final narration.

Purpose:

- test comprehension;
- test pacing;
- detect asset starvation;
- detect repetitive backgrounds;
- detect excessive text;
- detect weak opening.

## 10.3 Blocking comprehension gate

Questions:

- Can the viewer identify the subject in the first beat?
- Can they explain the mechanism without subtitles?
- Does each scene introduce new information?
- Are source/document/chart states understandable?
- Are abstract visuals grounded?
- Does the sequence feel coherent rather than templated?

Fail here before expensive final motion/render.

# 11. Motion-code authorship

## 11.1 Primitive-first, novel when needed

Codex should prefer a safe primitive if it expresses the intended story well.

Codex should author novel motion when:

- the story has a unique mechanism;
- the primitive would flatten important nuance;
- a new visual metaphor materially improves comprehension;
- a signature branded moment is justified.

## 11.2 Mechanical versus creative changes

Mechanical fixes:

- import/path correction;
- composition ID sanitation;
- serialization;
- safe deterministic crop normalization;
- codec/package issues.

Creative changes:

- shot concept;
- visual hierarchy;
- asset assignment;
- motion choreography;
- transition;
- pacing;
- viewer-visible composition.

Creative revisions must retain Codex provenance. Mechanical normalization does not consume creative revision budget.

# 12. Audio system

## 12.1 Voice

The local/provider-neutral TTS abstraction remains.

Codex provides:

- script;
- pronunciation notes;
- emphasis;
- pauses;
- pace intent.

The actual TTS tool/provider generates the waveform and gets explicit provenance.

## 12.2 Music/SFX

Use owned/procedural or rights-clear audio.

Codex may author cue intent:

- cold-open hit;
- data tick;
- restrained riser;
- transition cue;
- resolve.

Avoid overproduced trailer sound.

## 12.3 Mastering

Initial target remains around:

- integrated loudness ~-16 LUFS ±1;
- true peak <= approximately -1.5 dBTP.

Actual platform calibration may later adjust these values.

# 13. Caption/package policy

Canonical output package should include:

- clean 9:16 master;
- clean 16:9 master when justified;
- sidecar caption file(s);
- optional burned-caption social derivative;
- thumbnail/cover candidates when later in scope;
- evidence/provenance manifest;
- rights manifest;
- media probe;
- QA report;
- creative receipts;
- timeline/scene manifest.

Burned subtitles are not the default editorial master.

# 14. QA system

## 14.1 Deterministic technical QA

Check:

- file exists and hash;
- dimensions/FPS;
- duration;
- codec/audio streams;
- loudness/peak;
- package identity;
- rights/provenance completeness;
- no network/public write;
- safe generated-code imports.

## 14.2 Visual layout QA

Check:

- text overflow;
- clipping;
- source/caption overlap;
- native/overlay duplication;
- highlight geometry;
- safe zones;
- minimum phone-scale type;
- asset crop/focal-object visibility.

## 14.3 Diversity QA

Check:

- asset reuse count;
- cumulative screen time;
- repeated background sequence;
- repeated primitive concentration;
- repeated transition/easing concentration.

## 14.4 Semantic QA

Check:

- claim/evidence alignment;
- forecast vs observation;
- generated illustration disclosure;
- real/documentary asset use;
- no unsupported causal statement.

## 14.5 Codex visual review

Codex reviews actual rendered frames/video evidence and returns localized defects.

The reviewer must answer:

- what is confusing?;
- what looks amateur?;
- what is too dense?;
- what breaks visual hierarchy?;
- where does pacing sag?;
- where is an asset overused?;
- where does a scene look templated?;
- what precise localized revision would materially improve it?

Machine PASS cannot override owner/media review.

# 15. Revision policy

Default budget:

1. one plan/storyboard-level correction before final motion if comprehension fails;
2. one localized rendered creative revision after proxy/full review.

Mechanical fixes do not consume the creative revision budget.

If systemic defects remain after bounded creative correction, fail the run rather than hand-polish indefinitely.

# 16. Durable stage ledger

Each stage writes an immutable checkpoint.

Recommended stages:

1. candidate qualification;
2. evidence lock;
3. analytical map;
4. script;
5. wit pass;
6. asset plan;
7. storyboard;
8. animatic/comprehension;
9. motion source;
10. proxy render;
11. visual review;
12. revision;
13. final render;
14. audio/mux;
15. final QA;
16. owner/publication gate.

Each checkpoint includes:

- stage version;
- input artifact hashes;
- output artifact hashes;
- tool/model identity;
- cost/runtime;
- result;
- defect/retry state;
- next legal stage.

# 17. Failure and recovery

## Soft/recoverable

Examples:

- provider timeout;
- render interruption;
- temporary missing local process;
- one mechanical code issue;
- source crop needing deterministic reframe.

Recover from last valid checkpoint.

## Hard blockers

Examples:

- missing/fabricated factual authority;
- rights ambiguity that cannot be resolved;
- secret/session exposure;
- unauthorized platform/public write;
- destructive V1 mutation;
- irreconcilable ref conflict;
- required creative brain unavailable beyond bounded retry policy;
- final media remains materially unacceptable after revision budget.

# 18. V1 -> V2 trigger implementation

## Phase A: fixture/local contract

Before live V1 analytics are complete, implement with representative fixtures/local snapshots.

The contract must already match the future durable production shape.

## Phase B: shadow read-only V1 metrics

Read actual V1 performance without changing V1.

Log candidate rankings but do not automatically execute expensive jobs until thresholds are calibrated.

## Phase C: conditional automatic claim

Once stable:

- supervisor claims only qualifying article jobs;
- one or two opportunities may be produced per day if truly qualified;
- abstain on weak days.

# 19. Scheduler and unattended operation

Use a small wake-up mechanism rather than a long-lived creative agent.

On Windows, expected pattern:

```text
Task Scheduler
→ periodic/event-triggered supervisor
→ run_once
→ inspect/claim outbox
→ spawn fresh isolated Codex job
→ wait/monitor or persist external job handle
→ update ledger
```

The exact supported Codex headless mechanism must be proven empirically in-repo. Prefer structured/headless execution interfaces over brittle UI automation.

Do not rely only on shell exit code; require expected stage receipts and artifact hashes.

# 20. Cost/runtime measurement

Every run should measure:

- Codex/LLM usage where available;
- external image/TTS/audio cost;
- render wall-clock;
- total wall-clock;
- rerender count;
- revision count;
- operator review minutes;
- number of manual code edits;
- recovered/resumed stages.

Core TCO measure:

```text
TCO = model/agent cost
    + media provider cost
    + render compute
    + failed/repeated work
    + operator review labor
    + opportunity cost
```

# 21. Lane A benchmark strategy

Do not discard Lane A learnings.

After Hybrid visual infrastructure exists:

1. feed the same governed story to CodexJobBrain and NineRouterCXBrain;
2. route both through the same asset broker, visual primitives, compilers, renderer, and QA;
3. compare final quality, cost, wall-clock, failure rate, and revision count;
4. allow Jim to change primary brain only on measured evidence.

This prevents an unfair comparison where one brain benefits from a better renderer than the other.

# 22. Post-publication analytics loop

Once public-write authority exists, retain per-scene attribution:

- elapsed time;
- scene/beat ID;
- primitive;
- asset class;
- hook type;
- analytical channel;
- wit presence;
- narration density;
- transition type.

Use audience retention, completion, rewatch, shares, subscribers, and other legitimate platform metrics to improve:

- candidacy;
- hook style;
- scene duration;
- primitive selection;
- asset strategy;
- packaging.

Never let engagement data change factual/numeric truth.

# 23. Security, rights, and publication boundaries

Current invariant:

`ZERO_VIDEO_PUBLIC_WRITE_AUTHORITY`

Forbidden during current V2 development:

- YouTube/TikTok upload;
- private/unlisted/draft upload;
- browser/CDP publication;
- scheduler publication;
- public-platform mutation;
- V1 durable-store mutation;
- V1 scheduler/coordinator mutation;
- secret logging;
- generated real-person documentary media.

Generated illustration must be disclosed internally and cannot act as factual evidence.

# 24. Implementation phases

## Phase 1 — Hybrid vertical slice

Task:

`TASK_CONTENTOPS_V2_LANE_B_HYBRID_INSTITUTIONAL_EDITORIAL_ENGINE_AND_HEADLESS_TRIGGERED_VERTICAL_SLICE_V1`

Deliver one actual video using:

- new analytical engine;
- new shared visual safety/design system;
- durable outbox fixture/contract;
- fresh isolated Codex job;
- stage ledger/resume;
- full actual media QA.

This phase must create product capability, not just schemas.

## Phase 2 — Generalization proof

Run a different story/domain.

Goal:

- prove primitives are composable rather than oil-specific;
- add only minimal domain pack/novel primitives needed;
- measure manual intervention.

## Phase 3 — V1 live shadow trigger

Connect read-only V1 engagement signals.

Goal:

- score real article portfolio;
- automatically produce only qualified shadow candidates;
- validate timing/cost.

## Phase 4 — Production soak

Target roughly 10 consecutive qualified jobs.

Acceptance hypotheses:

- >=90% end-to-end completion;
- no unresolved MAJOR visual defects;
- most runs need no manual source-code edit;
- bounded operator review;
- cost measured;
- at least one non-oil proof;
- stable recovery after interruption;
- quality at or above best Lane B reference.

## Phase 5 — Controlled publication

Only after explicit Jim authorization for exact destination/platform scope.

Then implement:

- upload;
- readback;
- destination identity;
- reconciliation;
- analytics attribution;
- bounded learning.

# 25. Next-task implementation requirements

The next builder task must:

- start from fresh verified GitHub authority;
- reuse A/B proof only as positive/negative reference, not merge blindly;
- implement the minimal durable Hybrid architecture required for one real video;
- produce actual short/midform media as justified;
- use a fresh Codex execution boundary;
- keep public writes zero;
- capture cost/runtime;
- push one explicit task branch;
- return actual media for Jim/ChatGPT review.

Do not split into separate weeks of “schema,” “scheduler,” “design system,” and “editorial engine” tasks if one bounded vertical slice can prove them together.

# 26. Anti-overengineering rules

Do not:

- build Kubernetes/queue infrastructure not required locally;
- create a generic plugin platform before one Hybrid video works;
- build dozens of primitives up front;
- implement every analytical domain pack before a second story needs them;
- rewrite working TTS/audio infrastructure without a blocker;
- build public upload before creative production is reliable;
- force every article into video;
- keep two renderer stacks;
- treat docs/tests/evidence as the product.

# 27. Definition of near-term success

The next Hybrid proof succeeds when:

- a qualified story enters through the durable job contract;
- Codex receives only explicit fresh context;
- institutional analytical depth improves materially over current Lane B benchmark;
- script remains conversational and retention-aware;
- wit is controlled and optional;
- assets are diverse and rights-safe;
- no duplicate native/overlay text defects;
- no alignment/highlight/source collisions;
- the best Lane B motion quality is present across the full video, not only the latter half;
- process can resume from interruption;
- operator does not manually author the final scene code;
- cost/runtime is known;
- final media is actually inspected;
- no platform/public write occurs.

# 28. Durable final rule

**The canonical V2 strategy is to industrialize Lane B quality, not to automate Lane A defects and not to operationalize endless manual Codex repair. Fresh Codex creative intelligence plus deterministic durable production infrastructure is the product architecture.**
