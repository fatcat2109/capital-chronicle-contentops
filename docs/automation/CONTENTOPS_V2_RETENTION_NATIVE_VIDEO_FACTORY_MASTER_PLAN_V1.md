# Capital Chronicle ContentOps V2 — Retention-Native Video Factory Master Plan V1

Authority date: 2026-08-12
Product authority: `CONTENTOPS_V2_RETENTION_NATIVE_VIDEO_FACTORY_OWNER_DIRECTION_V1`
Plan status: `CURRENT_CANONICAL_V2_EXECUTION_PLAN`
Supersedes conflicting Tier-2 planning/routing where explicitly mapped in `CONTENTOPS_V2_RETENTION_NATIVE_VIDEO_FACTORY_SUPERSESSION_MAP_V1.md`.

## 0. Executive summary

Capital Chronicle ContentOps V2 will be built as an autonomous, evidence-governed video growth factory for YouTube hero/mid/long-form, YouTube Shorts, and TikTok-native short-form. The product goal is repeatable qualified audience growth, rising returning-viewer behavior, a growing library of durable high-trust videos, and a credible chance of breakout distribution. It must never promise or simulate guaranteed virality.

The rejected Tier-2 prototypes established important engineering primitives but failed the creative-product bar. Their dominant failure was structural: they treated a scene as one designed canvas with an entrance animation and long hold. The result was an editorial slideshow with captions rather than a retention-native video edit. V2 must therefore move creative authority above the renderer and represent narrative beats, edit decisions, asset purposes, audio states, and platform variants explicitly.

The final system is not a single model that browses, thinks, edits, renders, checks, publishes, and watches performance in one long agent loop. ContentOps remains the product and durable control system. Shared newsroom intelligence, evidence, published memory, story routing, and performance context are amortized across articles, social posts, newsletters, and video. Strong models intervene at bounded semantic/creative points where they add value; deterministic/local systems perform repetitive rendering, transforms, validation, caching, muxing, package locking, upload state, and reconciliation.

This plan is organized into twelve heavy bounded product tasks. Each task has an observable capability, actual media or platform evidence, measurable acceptance criteria, bounded cost/network authority, and one clear result required to advance. The sequence is designed to prevent two forms of premature scaling: publishing before professional creative quality is repeatable, and building a performance-learning system before real public observations exist.

The execution gates are:

```text
V2-01 → V2-03   PROFESSIONAL_CREATIVE_PROOF
V2-04 → V2-05   CHANNEL_PRODUCT_AND_SHADOW_FACTORY_PROOF
V2-06 → V2-07   PRIVATE_PLATFORM_DELIVERY_PROOF
V2-08            CONTROLLED_PUBLIC_COHORT_PROOF
V2-09 → V2-10   RETENTION_AND_LEARNING_PROOF
V2-11            AUTONOMOUS_OPERATING_PROOF
V2-12            FINAL_V2_RELEASE
```

No task may be promoted because unit tests pass while actual media is weak. Jim/ChatGPT remains final visual/audio product authority until enough real performance data exists to calibrate automated quality gates.

---

## 1. Why the previous V2 prototypes failed

### 1.1 Tier2-A: technical vertical slice, not creative product

Tier2-A proved a local renderer-neutral `VideoProgram`, source/evidence lineage, deterministic media handling, Kokoro narration, captions, FFmpeg packaging, scene/chapter caching, selective-rerender concepts, and immutable package verification. It did not prove professional editorial video quality.

The generated long-form output remained presentation-heavy, numerically dense, visually repetitive, and weak in real-world contextual imagery. The value of Tier2-A is therefore infrastructure and evidence discipline, not visual design.

### 1.2 Historical Tier2-B: rejected visual product

The historical Tier2-B Remotion experiment added programmable components and multimodal review, but its visual language remained dominated by repeated cards, weak typography, small charts, and low motion density. It is reference-only.

### 1.3 `d231b54e...`: better design, still rejected creative architecture

The branch `task/tier2-v2-creative-system-rebuild-v1` at `d231b54e026570442d9fd9269b61e55c3de31d21` materially improved typography, hierarchy, native 9:16 composition, generated-illustration integration, source-document treatment, deterministic QA, rights primitives, and critic scene/time coverage. It also correctly refused to stretch a narrow Treasury story to fifteen minutes.

However, media audit showed the core edit remained slideshow-like:

- most visual primitives performed their meaningful animation near the beginning of a scene;
- the main visual then held for long narration spans;
- captions created much of the apparent movement;
- no soundtrack or sonic identity existed;
- the hook was editorially clean but abstract and weak as a scroll-stopping media promise;
- there was little human context, consequence, or conflict;
- the critic's correction surface mainly changed scale, accent, legend, and transitions instead of beat structure;
- the Treasury curve remained a poor creative benchmark for channel growth.

This branch is therefore `REJECTED_CREATIVE_PRODUCT_REFERENCE_ONLY`. Do not merge it or continue its visual grammar. Selectively reuse engineering ideas only after fresh review.

### 1.4 New design principle

The primary creative unit is no longer the scene. It is the narrative/edit beat.

A scene may contain several beats with different visual states, assets, camera/composition actions, annotations, audio states, and payoffs. The renderer compiles these explicit decisions; it does not invent the edit merely because a `primitive` was named.

The simplest quality test is:

> Hide captions. Does the main visual still keep telling the story and changing meaningfully throughout the narration?

If not, the package is not retention-native.

---

## 2. Product goals and non-goals

### 2.1 Primary goals

V2 should help Capital Chronicle become a recognizable high-trust financial/economic video brand by delivering:

- stronger daily story selection for video;
- native YouTube and short-form storytelling;
- high-quality visual and audio production with low marginal manual effort;
- repeatable series/format identities;
- rights-safe use of real people, institutions, locations, documents, charts, maps, and generated conceptual imagery;
- automated packaging for title, thumbnail, cover frame, description, chapters, CTA, and binge path;
- strict platform upload/readback/reconciliation;
- beat-level retention attribution;
- bounded learning from actual viewer behavior;
- low sustainable external-AI cost;
- safe abstention when evidence, rights, creative depth, or platform readiness is insufficient.

### 2.2 Growth objective

The product should optimize for qualified engagement rather than raw click volume:

- watch time;
- retention;
- shares;
- saves;
- replies/comments where appropriate;
- subscriber conversion;
- returning viewers;
- canonical-article/newsletter clicks;
- search demand and longevity;
- repeat series demand.

It should penalize:

- clickbait not delivered by the video;
- repeated or concentrated topic selection;
- weak evidence;
- filler;
- excessive outrage/FOMO framing;
- visually static output;
- generic AI aesthetics;
- unlicensed media;
- high cost without measured utility.

### 2.3 Non-goals

V2 does not aim to:

- guarantee trending/viral outcomes;
- replace Capital Chronicle analytical authority;
- rebuild the V1 newsroom or durable store;
- create a second scheduler/outbox/publication engine;
- depend on one coding-agent subscription for production;
- use opaque end-to-end text-to-video as canonical authority;
- synthesize documentary images of real people;
- automate public posting before exact authorization and readback readiness;
- publish a fixed number of videos when no qualified story exists.

---

## 3. Final architecture

### 3.1 Shared newsroom and amortized intelligence

V2 consumes the canonical ContentOps rolling story universe, published memory, Capital Chronicle read-only context, evidence gates, novelty/update classification, and portfolio state.

Discovery and research should be amortized. The newsroom should not be re-browsed from scratch once per video by a frontier agent. The same qualified story/evidence base may feed article, newsletter, X/LinkedIn, YouTube, Shorts, TikTok, Telegram, or future derivatives.

Actual production-day evidence demonstrates why this matters: two recent real decisions consumed 1,033,832 and 1,452,475 tokens during newsroom/routing work before article or video production. This proves that discovery/selection can dominate model cost. V2 therefore treats newsroom intelligence as shared infrastructure and uses compact governed packets for downstream creative work.

### 3.2 Opportunity selection

A `VideoOpportunity` should evaluate:

- current story identity/version;
- evidence/readiness state;
- novelty/update-chain state;
- materiality;
- human/institutional stakes;
- conflict, change, decision, or consequence;
- narrative depth;
- visualizability;
- available documents/data/assets;
- real-person/location relevance;
- current demand/trend signals;
- shelf life/search longevity;
- recent topic/series concentration;
- format fit: short, mid, long, derivatives;
- estimated production effort/provider cost;
- expected qualified engagement;
- risk/rights constraints.

Possible outcomes:

`VIDEO_SELECTED`, `SHORT_ONLY`, `MIDFORM_SELECTED`, `HERO_LONG_SELECTED`, `DEFERRED`, `VIDEO_BLOCKED`, `VIDEO_NOT_SELECTED`.

A long duration must be earned. A story with four narrow claims should not become a fifteen-minute video just because long-form is a product target.

### 3.3 Engagement Director

The Engagement Director converts a selected governed story into an `EngagementBrief`. It is not allowed to add facts.

Required fields:

- target audience;
- viewer problem/question;
- why now;
- core promise;
- hook;
- pattern interrupt;
- central tension;
- curiosity gap/open loops;
- payoff checkpoints;
- re-hooks;
- pacing map;
- emotional register;
- taboo/overclaim boundaries;
- CTA;
- binge/next-content target;
- title/thumbnail promise;
- platform-specific hook variants.

The system should distinguish legitimate tension from manufactured controversy. Good finance engagement often comes from evidence conflict, mechanism, stakes, uncertainty, or a gap between headline and underlying record.

### 3.4 Editorial Video Director

The Editorial Video Director turns the engagement brief and evidence packet into a renderer-neutral plan. It chooses story mode, chapter structure, scene structure, beat structure, asset purposes, narration logic, platform variants, and editorial boundaries.

Strong models may be used here because this is a high-leverage semantic decision point. Their output must be validated against evidence contracts before rendering.

### 3.5 Narrative Beat Graph

The `NarrativeBeatGraph` is the canonical creative pacing structure.

Every beat should carry:

- `beat_id`;
- chapter/scene ID;
- target timing/duration;
- narrative role: hook/setup/tension/evidence/mechanism/contrast/payoff/re-hook/boundary/CTA;
- narration text span/reference;
- claim/evidence bindings;
- open-loop ID and payoff relation where applicable;
- viewer takeaway;
- visual purpose;
- desired asset class;
- on-screen text intent;
- audio-state intent;
- transition intent.

One scene may contain several beats. A scene is only a grouping/production boundary, not a static slide.

### 3.6 Edit Decision / Motion Beat Graph

The edit graph makes time-based visual decisions explicit:

- cut;
- hold;
- reveal;
- wipe;
- split screen;
- pan/reframe;
- crop/punch-in;
- document close-up;
- source highlight;
- chart trace;
- point annotation;
- comparison state;
- map/timeline progression;
- person/institution cutaway;
- quote treatment;
- kinetic text;
- generated conceptual transition;
- payoff visual;
- exit/transition.

A motion beat must have narrative purpose. Constant zooms or arbitrary cuts do not count as engagement.

### 3.7 Asset intelligence

The `AssetPlan` should identify assets by editorial purpose, not just media type.

Purposes include:

- establish person/institution/location;
- prove a factual claim;
- show source authority;
- explain a mechanism;
- compare before/after;
- create a pattern interrupt;
- provide human context;
- bridge a transition;
- visualize an abstract idea;
- land a payoff;
- package thumbnail/cover.

Asset classes:

- deterministic charts/data graphics;
- official/source documents;
- filings/releases;
- real rights-cleared politician/central-banker/minister/CEO photos;
- institution/location imagery;
- maps/timelines;
- quotes;
- diagrams/process graphics;
- generated conceptual illustrations through the accepted `gpt-5.5` direct image boundary;
- rights-safe historical/context imagery;
- restrained B-roll/stills.

Real-person documentary imagery must be real and rights-cleared. Synthetic media may be conceptual enrichment only and must preserve provenance/disclosure.

### 3.8 Audio system

Audio is a creative layer, not a post-processing checkbox.

`AudioPlan` responsibilities:

- narrator/provider/voice;
- voice style;
- pronunciation dictionary;
- acronym/name/date/number handling;
- emphasis/prosody;
- pause map;
- word/phrase timing;
- music bed by beat/chapter;
- tension/resolution states;
- risers/stingers/hits/whooshes as appropriate;
- chart/data reveal cues;
- ducking;
- fades;
- loudness normalization;
- true-peak control;
- audio rights/provenance.

Kokoro is a local fallback/baseline, not automatically the premium voice. Chatterbox and ElevenLabs are candidates to benchmark. Provider choices remain behind interfaces.

### 3.9 Platform-native compilers

#### YouTube hero/mid/long

Optimize for:

- clear packaging promise;
- sustained narrative arc;
- chapters;
- re-hooks;
- evolving visual language;
- richer evidence sequences;
- higher asset diversity;
- search longevity;
- end-screen/binge path.

#### YouTube Shorts

Optimize for:

- immediate hook;
- portrait-native composition;
- faster payoff;
- shorter captions;
- denser but meaningful visual rhythm;
- strong last-frame/loop/CTA behavior;
- cover-frame planning.

#### TikTok

Optimize for:

- native 9:16 edit rather than reuse-only;
- scroll interruption;
- conversational pacing;
- faster sequence density;
- caption-safe zones;
- platform-specific packaging and CTA;
- exact capability/approval constraints at upload time.

### 3.10 QA and critic

Deterministic QA should cover:

- claim/evidence coverage;
- rights/provenance completeness;
- asset hashes;
- media dimensions/codecs/FPS/audio;
- caption timing/line count/safe zones;
- actual transition implementation;
- hook timing;
- first-payoff timing;
- meaningful visual-beat intervals;
- static-run duration excluding caption-only changes;
- asset diversity;
- music/SFX coverage;
- loudness/true peak;
- open-loop/payoff closure;
- packaging promise delivered;
- package hash integrity;
- selective rerender correctness.

Multimodal review should inspect beat/time coverage and report defects by `video_id`, `scene_id`, `beat_id`, and time range.

The revision system must be able to change beat timing, scene subdivision, cut points, asset assignments, motion states, captions, audio cues, and packaging—not just color or font scale. Maximum two structural revision rounds.

### 3.11 Publication and learning

Publication must reuse canonical outbox/unknown-write/readback/reconciliation principles. Video platform integrations may add transport-specific durable objects but must not create a second independent publication authority.

After publication, performance observations map back to beats and packaging decisions. Missing platform metrics remain unavailable, not zero.

---

## 4. Cost and model-control doctrine

### 4.1 Skeptical conclusion from the “single frontier agent replaces ContentOps” idea

The useful insight is not that a frontier coding agent should replace ContentOps. The useful insight is that frontier intelligence should be reserved for bounded, high-value decisions.

The repo's own production evidence shows newsroom/routing alone can exceed one million tokens per decision. A fresh frontier agent independently browsing the world for every video would duplicate expensive discovery, comparison, published-memory, evidence, and context work.

Therefore the canonical runtime pattern is:

```text
continuous cheap intelligence
→ shared clustering / novelty / memory
→ governed research/evidence packet
→ cheap capable semantic pass where sufficient
→ quality gate
→ frontier Director only when material value justifies it
→ structured VideoProgram / beat graphs
→ local deterministic assets/render/audio where appropriate
→ deterministic QA
→ cheap multimodal review
→ frontier critic only for serious defects / flagship value
```

This doctrine keeps strong models available where their reasoning quality matters while removing them from repetitive control loops.

### 4.2 What is not adopted from the external discussion

The canonical plan does not hardcode:

- specific Anthropic subscription economics;
- specific per-million-token prices;
- an assumed 1–5M tokens per video;
- a guaranteed $1–3 routine-video cost;
- a guaranteed $100 monthly spend;
- any claim that prompt caching will save a fixed percentage;
- any provider/model alias as permanent architecture.

Those figures are temporal and provider-specific. They belong in benchmark/economics evidence, not product constitution.

### 4.3 What is adopted

V2 should measure and manage:

- provider calls;
- tokens where returned;
- image/audio generations;
- render CPU/GPU time;
- cash cost where returned;
- retry/fallback overhead;
- cost per selected story;
- cost per final video;
- cost per qualified viewer/watch hour after public launch;
- portfolio monthly spend.

Portfolio budgeting is preferred over equal per-video allocation. Routine videos should normally be cheap; a flagship can spend more if expected audience/brand value justifies it. No public-quality story should be degraded merely to hit a fake per-video cost target, and no weak story should receive expensive escalation.

---

## 5. Initial creative and retention heuristics

These are hypotheses to validate, not factual laws.

### Short form

- hook/pattern interrupt begins approximately 0–1 second;
- first concrete payoff approximately 8–12 seconds or earlier;
- meaningful primary-visual change approximately every 1.5–4 seconds where useful;
- unjustified static primary-visual run no longer than about four seconds;
- captions normally no more than two lines;
- approximately 8–15 distinct visual states in a 30–60 second video when the material supports them;
- music/SFX usually present except deliberate silence;
- no scene should rely on captions as its only changing element.

### Mid/long form

- packaging promise/payoff preview within approximately 10–20 seconds;
- first substantive payoff within approximately 30–60 seconds;
- meaningful visual evolution approximately every 4–8 seconds;
- unjustified static run no longer than approximately eight seconds;
- re-hooks/open-loop renewal approximately every 20–45 seconds;
- at least four relevant asset classes when the story supports them;
- chapter visual/audio states should evolve;
- duration is bounded by real narrative depth.

### Audio

- integrated loudness initially around -16 LUFS ±1;
- true peak at or below approximately -1.5 dBTP;
- narration remains intelligible;
- no clipping;
- clean scene joins/fades;
- music ducked beneath narration;
- no unlicensed music/SFX.

These thresholds must be recalibrated once actual retention and audience data exist.

---

# 6. TASK ROADMAP

The following tasks are canonical. Each is intended as one heavy bounded product task plus independent audit. Support docs/tests/evidence should remain roughly 10–15% of the implementation effort unless a task is explicitly documentation/platform-integration heavy.

---

## V2-01 — Retention-Native Video Factory Vertical Slice

**Task label**

`TASK_CONTENTOPS_TIER2_V2_RETENTION_NATIVE_VIDEO_FACTORY_VERTICAL_SLICE_V1`

**Required result to advance**

`PASS_RETENTION_NATIVE_VERTICAL_SLICE_VISUAL_AUDIO_ACCEPTED`

### User problem

Current prototypes can render evidence-bound media but fail to produce a genuinely engaging edit. Their scenes behave like animated slides, audio lacks a professional bed, and creative planning is too close to the renderer.

### Why now

This is the smallest vertical slice that proves the new architecture before investing in provider breadth, platform uploads, analytics, or channel automation.

### Capability delivered

Implement first canonical versions of:

- `StoryMode`;
- `VideoOpportunity`/eligibility extension;
- `EngagementBrief`;
- `NarrativeBeatGraph`;
- `EditDecisionGraph`/`MotionBeatGraph`;
- `AssetPlan`;
- `AudioPlan`;
- `PlatformVariantPlan`;
- `RetentionDiagnostics`;
- a fresh beat-driven Remotion/programmatic compiler.

### Story/content requirement

Do not use the Treasury curve as the main creative benchmark.

Select a strong non-Treasury governed story containing several of:

- a material person or institution;
- a decision/change/conflict;
- a timeline;
- consequences;
- a source document;
- data/comparison;
- multiple useful asset classes.

Preference order:

1. current canonical governed ContentOps story;
2. existing governed committed non-Treasury story/evidence package;
3. a `TEST_ONLY_NON_PUBLIC` benchmark built from current official/public evidence through existing canonical evidence contracts.

No second newsroom. No invented facts.

### Visible result

Produce:

- one 45–75 second native 9:16 short;
- one 3–6 minute 16:9 mid-form proof;
- actual narration;
- actual rights-safe background music or locally generated rights-safe scored bed;
- restrained SFX where useful;
- at least four relevant asset classes;
- motion strips with captions hidden;
- long/short contact sheets;
- representative MP4 clips;
- `engagement_brief.json`;
- `narrative_beat_graph.json`;
- `edit_decision_graph.json`;
- `asset_plan.json`;
- `audio_plan.json`;
- `retention_diagnostics.json`;
- rights/provenance manifest;
- compact review README.

### Required creative behavior

The main visual must evolve through narration. A beat should trigger purposeful visual change: evidence reveal, chart tracing, callout, map/timeline movement, document punch-in, real-photo cutaway, comparison state, generated conceptual bridge, or payoff.

Short and mid-form must be independently compiled, not merely resized.

### Provider/network scope

Allowed only as needed for this task:

- canonical 9Router text/multimodal model seam for bounded Director/Critic calls;
- accepted direct `gpt-5.5` image boundary for illustrative assets;
- local/open-source TTS/music dependencies and public package/model hosts;
- ElevenLabs TTS comparison only if a usable secret exists and no plan purchase is required;
- public official/rights-clear sources for selected story assets;
- no platform upload.

### Credential/operator inputs

Use existing credential presence only. Never expose values. Do not block the whole task because ElevenLabs is unavailable; use the best rights-safe/local path, but do not call narration-only output a professional audio PASS if the engagement design requires music.

### Evidence/rights invariants

Every factual beat remains claim/source bound. Real people use real rights-cleared imagery. Generated media is illustrative and disclosed. Missing rights fail closed.

### Quality targets

Initial internal gates:

- short hook begins roughly within first second;
- first concrete payoff no later than roughly 8–12 seconds;
- short visual beat cadence approximately 1.5–4 seconds;
- no unjustified short primary-visual static run over four seconds;
- mid-form visual evolution approximately 4–8 seconds;
- no unjustified mid-form static run over eight seconds;
- captions max two lines in normal operation;
- audio around -16 LUFS ±1, peak ≤ -1.5 dBTP;
- at least four meaningful asset classes;
- captions-hidden visual review remains understandable;
- no filler.

### Validation

Focused tests plus real E2E renders must prove:

- graph/schema integrity;
- factual binding preservation;
- asset rights/provenance;
- beat-to-render compilation;
- static-run diagnostics excluding captions;
- audio QA;
- actual transition implementation;
- cache identity;
- selective rerender;
- package hashes;
- no unauthorized writes.

Maximum two structural revision rounds. Jim/ChatGPT owns final visual/audio acceptance.

### Cost/runtime bound

Use bounded provider calls and proxy-first rendering. Prefer reuse and selective rerender. Record actual calls/cost where returned. No paid-plan purchase.

### Must not build

- platform uploads;
- public posting;
- full daily portfolio;
- analytics warehouse;
- final UI dashboard;
- broad provider abstraction beyond immediate needs.

### Remaining blocker after PASS

Premium repeatable audio and asset intelligence still need stronger provider/rights proof.

### Next

V2-02.

---

## V2-02 — Premium Audio and Rights-Aware Asset Intelligence

**Task label**

`TASK_CONTENTOPS_TIER2_V2_PREMIUM_AUDIO_AND_ASSET_INTELLIGENCE_V1`

**Required result**

`PASS_PREMIUM_AUDIO_AND_ASSET_ENGINE_ACCEPTED`

### User problem

A retention-native edit still feels amateur when voice is robotic, music is absent/generic, pronunciation is weak, or visual assets are generic and disconnected from story beats.

### Why now

V2-01 proves the structure. V2-02 hardens the two most quality-sensitive enrichment systems before testing multiple story modes.

### Capability delivered

#### Voice routing

Provider-neutral narration supporting at least:

- ElevenLabs where authorized/usable;
- Chatterbox V3 local;
- Kokoro fallback.

Add:

- pronunciation dictionary for finance/economics/policy names and acronyms;
- numbers/date/basis-point reading policy;
- prosody/emphasis plan;
- word/phrase timing;
- scene/beat-level regeneration;
- voice identity metadata;
- normalized mastering.

#### Sonic identity

Create a rights-safe initial Capital Chronicle audio library:

- analytical-neutral bed;
- policy/tension bed;
- corporate/technology bed;
- geopolitical bed;
- resolution/outro bed;
- restrained risers;
- transition whooshes;
- hits/stingers;
- subtle data/chart reveal cues.

Every item stores source/model, license/rights, hash, intended usage, and attribution requirements.

#### Asset intelligence

Complete the path:

```text
story/entity/document need
→ editorial asset purpose
→ candidate source discovery
→ rights classification
→ composition/quality scoring
→ retrieval
→ hashing/provenance
→ responsive crops
→ BeatGraph assignment
```

Support at least:

- real entity photos;
- institution/location photos;
- official documents/filings;
- deterministic charts/maps/timelines;
- generated conceptual illustrations;
- historical/context imagery where rights permit.

### Visible result

- blind A/B/C voice review bundle using identical financial/news script;
- three narration styles or provider variants;
- five audio beds across target moods;
- at least ten restrained SFX/stingers/transitions;
- three rights-cleared asset packs: entity/institution, document/regulation, location/geopolitical;
- rerender of accepted V2-01 proof with selected premium audio/assets;
- exact pronunciation/timing QA artifacts.

### Acceptance

Jim/ChatGPT accepts primary voice and fallback voice. Music supports rather than masks narration. No rights ambiguity. Real-person images are never generated. Generated media is concept-only. Asset resolution fails closed when metadata/rights are unclear.

### Provider/network scope

Network allowed only for authorized TTS, public rights-clear asset acquisition, existing direct illustration provider, and required package/model hosts. No social-platform action.

### Credentials/operator input

If ElevenLabs quality clearly wins and free quota/license is insufficient for production, stop before purchase and request owner decision. Do not silently subscribe.

### Cost/runtime bound

Benchmark small samples before long renders. Cache voice/audio assets by provider/model/voice/settings/script hash. Reuse licensed music/SFX library across many videos.

### Must not build

- public upload;
- channel analytics;
- daily autonomous portfolio;
- giant stock-media scraper;
- generated fake people.

### Remaining blocker

One strong story still does not prove the factory generalizes.

### Next

V2-03.

---

## V2-03 — Diverse Story-Mode Corpus and Motion Acceptance

**Task label**

`TASK_CONTENTOPS_TIER2_V2_DIVERSE_STORY_MODE_CORPUS_AND_MOTION_ACCEPTANCE_V1`

**Required result**

`PASS_REPEATED_PROFESSIONAL_CREATIVE_QUALITY`

### User problem

A single excellent demo may hide hardcoded creative assumptions. The product needs multiple editorial modes without becoming a template zoo.

### Capability delivered

Prove reusable story-mode routing and mode-specific creative grammars for:

- `ENTITY_EVENT`;
- `DOCUMENT_REVEAL`;
- `DATA_MECHANISM`;
- `CONFLICT_TIMELINE`;
- optionally `EARNINGS_BREAKDOWN`;
- plus one weak candidate that ends in `VIDEO_NOT_SELECTED`.

Each mode chooses appropriate hook patterns, narrative structures, asset classes, beat density, audio arc, and platform variants while preserving shared brand tokens and evidence contracts.

### Visible result

Minimum corpus:

- one person/institution-led story;
- one regulation/document-led story;
- one corporate/data story;
- one geopolitical/trade/timeline story;
- one explicit abstention;
- at least three native shorts;
- at least two mid-form videos;
- one 8–15 minute hero only if a story genuinely supports it;
- cross-story visual/motion/audio review board;
- runtime/cost comparison by mode.

### Acceptance

At least three story modes earn Jim/ChatGPT visual/audio PASS. No mode looks like the same cards with swapped colors. No unjustified static-run failures. No filler. Rights/evidence gates pass. The brand remains recognizable despite edit-language diversity.

### Validation

Focused mode-router tests, graph validation, asset rights tests, actual E2E media, captions-hidden motion review, audio QA, critic coverage, selective rerender, package lock.

### Cost bound

Use existing library assets and cached primitives. Generated/paid calls must correspond to actual missing editorial value, not decoration.

### Must not build

- upload/publication;
- performance learning;
- final daily scheduling.

### Milestone

Passing V2-03 closes `PROFESSIONAL_CREATIVE_PROOF`.

### Next

V2-04.

---

## V2-04 — Packaging, Discovery, and Channel Series Engine

**Task label**

`TASK_CONTENTOPS_TIER2_V2_PACKAGING_DISCOVERY_AND_CHANNEL_SERIES_ENGINE_V1`

**Required result**

`PASS_CHANNEL_PACKAGING_AND_SERIES_SYSTEM`

### User problem

Strong content can fail before playback when title, thumbnail, cover frame, first line, series identity, or search intent makes a weak promise.

### Capability delivered

Add structured packaging objects:

- `PackagingPromise`;
- `TitleVariants`;
- `ThumbnailVariants`;
- `ShortCoverFramePlan`;
- `SearchIntent`;
- `Description/ChapterPlan`;
- `SeriesIdentity`;
- `CTAPlan`;
- `BingeLoopPlan`;
- `PromiseDeliveryAudit`.

Build 4–6 repeatable Capital Chronicle series hypotheses such as Breaking Explained, What the Headline Misses, One Chart One Consequence, Power & Policy, Big Tech/Earnings Breakdown, Capital Chronicle Deep Dive, or Evidence Boundary. The actual set should be chosen from demonstrated story supply and brand fit.

### Trend/discovery inputs

Trend/search signals may include current headline velocity, search intent, platform trend tools, channel search terms once available, and published-memory concentration. These signals influence opportunity, packaging, timing, and series allocation only. They never create factual truth.

### Visible result

For each hero/mid-form proof:

- at least three materially different title variants;
- three materially different thumbnails;
- three opening-hook treatments or packaging-to-hook mappings;
- SEO/search intent;
- description/chapters;
- series/playlist placement;
- CTA and end-screen/binge target.

For short-form:

- candidate cover frames;
- native title/caption variants;
- platform-specific CTA/loop plan.

### Acceptance

Packaging promise is visibly delivered by the video. No unsupported controversy. Thumbnails remain legible at realistic small sizes. Variants differ in strategic promise, not only typography. Series have clear audience value propositions.

### Network scope

Read-only trend/search research may be authorized through official/public sources. No platform writes.

### Must not build

- automated public upload;
- broad analytics learning;
- daily production scheduler changes.

### Remaining blocker

Need prove the factory can decide a daily portfolio without making filler.

### Next

V2-05.

---

## V2-05 — Shadow Daily Video Portfolio

**Task label**

`TASK_CONTENTOPS_TIER2_V2_SHADOW_DAILY_VIDEO_PORTFOLIO_V1`

**Required result**

`PASS_SHADOW_VIDEO_PORTFOLIO_FACTORY`

### User problem

A channel-growth product needs discipline over what not to make. Generating video from every article wastes budget and dilutes audience identity.

### Capability delivered

Extend canonical newsroom selection with video-opportunity portfolio logic:

```text
rolling story universe
→ video qualification
→ format fit
→ series fit
→ expected qualified engagement
→ marginal cost
→ concentration/shelf-life check
→ production portfolio
→ SELECT / DEFER / NOT_SELECTED
```

The portfolio should normally consider zero or one hero/mid-form opportunity and zero to several shorts per day, but these are not quotas.

### Shadow period

Run at least seven calendar days or a replay representative enough to expose multiple daily opportunity sets. Prefer genuine live story universes where safe.

### Visible result

- daily candidate universe;
- ranked video opportunities;
- selected/deferred/rejected reasons;
- actual packages only for sufficiently qualified candidates;
- explicit no-video days when appropriate;
- series/topic concentration report;
- cost/runtime report;
- at least three complete high-quality media packages across the run if story supply permits.

### Acceptance

No filler. No duplicate update abuse. No truth/rights relaxation. Portfolio decisions are reproducible. Trend signals do not become evidence. Cost remains bounded. Creative quality remains accepted.

### Must not build

- public upload;
- fake production frequency;
- second durable scheduler/store.

### Milestone

Passing V2-05 closes `CHANNEL_PRODUCT_AND_SHADOW_FACTORY_PROOF`.

### Next

V2-06.

---

## V2-06 — YouTube Private Upload, Processing, and Readback

**Task label**

`TASK_CONTENTOPS_TIER2_V2_YOUTUBE_PRIVATE_UPLOAD_PROCESSING_AND_READBACK_V1`

**Required result**

`PASS_YOUTUBE_PRIVATE_TRANSPORT_AND_READBACK`

### User problem

A local MP4 is not a deployable product. The system must upload, survive interruptions, confirm processing, verify metadata, and reconcile object identity without accidental public exposure or duplicate writes.

### Capability delivered

Implement/reuse a provider-neutral YouTube video transport integrated with canonical public-write safety doctrine:

- exact channel identity/readiness;
- OAuth token validation without exposing secrets;
- resumable upload;
- private/unlisted privacy only;
- title/description/tags/category;
- thumbnail where supported;
- captions/subtitles;
- playlist/series placement where safe;
- processing-state polling;
- exact object ID persistence;
- readback/reconciliation;
- interrupted-upload/unknown-write recovery;
- bounded delete/cleanup for designated test objects if explicitly safe.

### Visible result

- one private hero/mid-form upload;
- one private/unlisted Short;
- processing completion;
- exact metadata readback;
- thumbnail/caption readback where available;
- durable provider object IDs;
- recovery proof;
- zero public visibility.

### Authority

This task authorizes only private/unlisted test-object writes to the exact owner-confirmed YouTube channel after readiness checks. No public publication.

### Acceptance

No duplicate object on retry/recovery. No secrets exposed. Exact privacy state is verified by readback. V1 publication semantics remain intact. Unknown write follows stop/readback/reconcile.

### Operator input

Fresh-validate existing YouTube credentials, channel identity, scopes, quota, and current official API constraints at task time.

### Must not build

- public cohort;
- TikTok upload;
- channel learning policy.

### Next

V2-07.

---

## V2-07 — YouTube Shorts and TikTok Controlled Delivery

**Task label**

`TASK_CONTENTOPS_TIER2_V2_SHORTS_AND_TIKTOK_CONTROLLED_DELIVERY_V1`

**Required result**

`PASS_CONTROLLED_SHORT_VIDEO_DELIVERY`

### User problem

Short-form distribution needs platform-native packaging and reliable controlled delivery. TikTok approval/permission constraints must not be confused with credential presence.

### Capability delivered

#### YouTube Shorts

- native 9:16 package upload;
- title/description;
- cover-frame strategy where platform capability permits;
- captions;
- processing/readback;
- privacy verification.

#### TikTok

Implement only the exact currently allowed controlled route after fresh official capability verification:

- user OAuth/account identity;
- creator capability checks;
- duration/media constraints;
- draft/private/upload-to-inbox or other owner-approved non-public flow;
- status/readback;
- no claim of public Direct Post readiness without the required app/account approval.

### Visible result

- one controlled/private YouTube Short object;
- one controlled TikTok draft/private object if provider capability permits;
- exact processing/readback;
- native packaging evidence;
- failure classification if TikTok remains approval-blocked.

### Acceptance

No blind reuse of long-form crop. Privacy verified. No TikTok public claim without provider approval. No unknown write. Credentials remain secret.

### Must not build

- public posting;
- performance learning;
- unsupported browser automation workaround.

### Milestone

Passing V2-07 closes `PRIVATE_PLATFORM_DELIVERY_PROOF`.

### Next

V2-08 only after explicit Jim authorization.

---

## V2-08 — Exact-Authorized Public Growth Pilot

**Task label**

`TASK_CONTENTOPS_TIER2_V2_EXACT_AUTHORIZED_PUBLIC_GROWTH_PILOT_V1`

**Required result**

`PASS_SMALL_PUBLIC_VIDEO_COHORT`

### Hard owner boundary

This task cannot begin merely because V2-07 passes. Jim must grant exact public-write scope: channels/accounts, platforms, formats, maximum cohort, timing window, and any review mode.

### User problem

Private objects prove transport, not audience response. A small safe live cohort is needed before building learning policy.

### Capability delivered

Run a bounded public cohort with strict readback/reconciliation and incident handling.

Initial preferred route:

- YouTube public hero/mid-form first;
- YouTube Shorts;
- TikTok only if current app/account approval and exact authorization permit public delivery.

### Suggested cohort

Over roughly two weeks, subject to story qualification:

- approximately two hero/mid-form YouTube videos;
- approximately six YouTube Shorts;
- up to a similarly bounded TikTok cohort if authorized;
- no-publication days allowed.

These are maximum planning ranges, not quotas.

### Visible result

For every public object:

- canonical package/hash;
- upload attempt identity;
- platform object ID/URL;
- processing/readback;
- title/thumbnail/description/cover used;
- publication time;
- first 24h/72h observations where available;
- incident/recovery record;
- no unresolved unknown write.

### Acceptance

Zero truth/rights/secret incidents. Zero duplicate publication. Every object reconciled. Every edit is platform native and package promise is delivered.

### Must not build

- autonomous high-volume publication;
- aggressive learning from tiny samples;
- public TikTok bypasses.

### Milestone

Passing V2-08 closes `CONTROLLED_PUBLIC_COHORT_PROOF`.

### Next

V2-09.

---

## V2-09 — Retention Analytics and Beat Attribution

**Task label**

`TASK_CONTENTOPS_TIER2_V2_RETENTION_ANALYTICS_AND_BEAT_ATTRIBUTION_V1`

**Required result**

`PASS_BEAT_LEVEL_RETENTION_OBSERVABILITY`

### User problem

Raw views and watch time do not tell the factory what creative decision caused a drop or spike. Performance must map back to production structure.

### Capability delivered

Create read-only performance ingestion and beat-level attribution:

```text
platform metric timestamp/ratio
→ public object
→ package/video_id
→ scene_id
→ beat_id
→ asset/motion/caption/audio state
→ hook/open-loop/payoff identity
```

### YouTube observations

Where officially available, capture:

- impressions;
- CTR;
- views/watch time;
- average view duration;
- audience retention curve;
- traffic sources;
- search terms;
- new/returning viewers;
- subscribers gained;
- shares;
- long-form relative retention context;
- Shorts engaged views/stayed-to-watch/average percentage viewed.

### TikTok observations

Use only official/account-authorized metrics. If detailed retention is unavailable, support manual creator export/import or mark metrics unavailable. Never scrape hidden endpoints or invent zeros.

### Visible result

- per-video performance report;
- retention curve aligned to beats;
- spike/dip annotations;
- packaging vs delivery comparison;
- short→hero funnel where observable;
- returning-viewer/subscriber conversion where observable;
- data freshness/provenance.

### Acceptance

Attribution links resolve exactly. Missing metrics remain missing. Insufficient sample yields `NO_POLICY_CHANGE`. No performance read causes public mutation.

### Must not build

- autonomous policy mutation yet;
- fabricated attribution certainty;
- browser numeric truth.

### Next

V2-10.

---

## V2-10 — Trend, Packaging, and Creative Learning

**Task label**

`TASK_CONTENTOPS_TIER2_V2_TREND_PACKAGING_AND_CREATIVE_LEARNING_V1`

**Required result**

`PASS_BOUNDED_VIDEO_GROWTH_LEARNING`

### User problem

Analytics without bounded policy improvement is reporting, not an adaptive growth system.

### Capability delivered

Introduce versioned bounded policies that may update:

- story-mode preference;
- hook class;
- first-payoff timing;
- beat density;
- asset mix;
- music intensity;
- caption style;
- title/thumbnail pattern;
- duration range;
- series allocation;
- short↔hero relationship;
- publication timing.

### Learning rules

- no policy change from tiny/noisy samples;
- every change cites exact observations;
- confidence/sample-size state recorded;
- changes are reversible/versioned;
- factual/evidence/rights/publication safety is immutable to engagement learning;
- trend signals affect opportunity/framing/timing only.

### Visible result

After sufficient cohort evidence:

- at least three useful supported conclusions;
- one thumbnail/title learning example;
- one retention-driven edit/pacing correction;
- one portfolio/series conclusion;
- at least one `NO_POLICY_CHANGE` due insufficient evidence;
- before/after policy versions;
- cost/utility comparison.

### Acceptance

Observed performance supports the changes. No overfit. No retroactive alteration of published evidence. Jim/ChatGPT accepts policy reasoning.

### Must not build

- uncontrolled self-modifying prompts;
- large policy shifts from one breakout;
- content truth optimization by engagement.

### Milestone

Passing V2-10 closes `RETENTION_AND_LEARNING_PROOF`.

### Next

V2-11.

---

## V2-11 — Autonomous Channel Operating System

**Task label**

`TASK_CONTENTOPS_TIER2_V2_AUTONOMOUS_CHANNEL_OPERATING_SYSTEM_V1`

**Required result**

`PASS_AUTONOMOUS_VIDEO_CHANNEL_LOOP`

### User problem

Individual good videos and analytics do not create an autonomous media operation. The factory needs a durable daily loop, portfolio state, production observability, recovery, and operator control.

### Capability delivered

Close the loop:

```text
daily story universe
→ video opportunity portfolio
→ hero/short selection
→ series/packaging
→ asset/audio production
→ render/QA/revision
→ publication schedule
→ exact upload/readback
→ performance observation
→ bounded learning
```

Reuse canonical scheduler/state/publication primitives rather than create a parallel system.

### Operator surface

Extend canonical V5/read-model surfaces with a compact Video Today / Channel view exposing:

- current video candidates;
- selected/deferred/not-selected reason;
- production state;
- asset/rights blockers;
- render/QA state;
- packaging variants;
- platform upload/processing/readback;
- performance/retention;
- series health;
- cost;
- incidents;
- operating mode/kill switch.

The operator should understand current video state in under one minute.

### Soak

Run approximately 10–15 operating days in shadow/live mode appropriate to exact authority. No-publication days allowed.

### Acceptance

- ≥90% successful scheduled/triggered qualified opportunities where external platform availability does not block;
- zero unresolved unknown public writes;
- zero rights/truth incidents;
- restart/recovery works;
- V1 remains healthy;
- low measured cost;
- portfolio avoids repetition/filler;
- actual media quality remains accepted.

### Must not build

- new durable newsroom/store;
- unrestricted public scope;
- broker/live trading anything.

### Milestone

Passing V2-11 closes `AUTONOMOUS_OPERATING_PROOF`.

### Next

V2-12.

---

## V2-12 — Final Reliability, Growth Proof, and Release

**Task label**

`TASK_CONTENTOPS_TIER2_V2_FINAL_RELIABILITY_GROWTH_PROOF_AND_RELEASE_V1`

**Required result**

`PASS_CONTENTOPS_V2_VIDEO_FACTORY_OWNER_ACCEPTED`

### User problem

A system can be operational without proving sustained audience/product value. Final V2 acceptance requires repeated quality, reliable operations, real performance learning, and owner confidence.

### Final proof corpus

Target minimum evidence before final acceptance, adjusted for actual story supply and platform authorization:

- at least six owner-accepted YouTube hero/mid/long-form videos;
- at least twenty Shorts or equivalent short-form packages;
- TikTok corpus where exact public authorization exists;
- at least three recurring content series;
- at least three story modes;
- explicit `VIDEO_NOT_SELECTED` / no-publication evidence;
- at least one upload/recovery proof;
- at least one retention-driven creative improvement;
- at least one packaging learning example.

These are proof-sample targets, not content quotas.

### Growth proof

Use channel-relative evidence rather than invented universal viral benchmarks. Candidate final criteria:

- a strong majority of new uploads outperform the channel's earlier rolling median on the primary format metric;
- hero/mid-form retention improves relative to similar-length channel baselines;
- Shorts improve on rolling stayed-to-watch / average-percentage-viewed baselines where available;
- returning-viewer/monthly-audience trend improves across several measurement windows;
- at least one repeatable series shows sustained demand;
- at least one breakout package materially exceeds channel median;
- subscriber conversion and canonical-article/newsletter clicks are measured where available;
- packaging promises remain truthful.

Exact thresholds should be set from the channel's accumulated baseline, not external folklore.

### Reliability proof

- production success ≥90% for qualified scheduled opportunities, excluding documented external/provider outages;
- zero truth/rights/secret incidents;
- exact readback/reconciliation for every public object;
- no unresolved unknown writes;
- kill switch proven;
- restart/recovery proven;
- immutable package/public-object lineage;
- cost within Jim's owner budget;
- V1 remains healthy;
- protected release history remains intact.

### Visible result

- accepted autonomous V2 daily video/channel operating loop;
- YouTube hero + Shorts factory;
- TikTok factory under exact approved capability;
- series/portfolio view;
- retention/performance view;
- cost/reliability evidence;
- final release packet;
- owner-approved release identity/tag only after independent audit.

### Acceptance

Final acceptance belongs to Jim after ChatGPT independent GitHub/media/platform audit. The final label is not granted by the runtime, Codex, a multimodal critic, or a test suite.

### Final result

`PASS_CONTENTOPS_V2_VIDEO_FACTORY_OWNER_ACCEPTED`

---

## 7. Milestone definitions

### `PROFESSIONAL_CREATIVE_PROOF` — after V2-03

Proves the system can repeatedly create professional, rights-safe, retention-native media across multiple story modes.

Does not prove uploads or audience response.

### `CHANNEL_PRODUCT_AND_SHADOW_FACTORY_PROOF` — after V2-05

Proves packaging/series strategy and disciplined daily opportunity selection without filler.

Does not prove platform transport.

### `PRIVATE_PLATFORM_DELIVERY_PROOF` — after V2-07

Proves controlled YouTube/TikTok delivery, processing, identity, readback, and recovery.

Does not authorize public posting.

### `CONTROLLED_PUBLIC_COHORT_PROOF` — after V2-08

Proves a small exact-authorized public cohort without safety/rights/write incidents.

### `RETENTION_AND_LEARNING_PROOF` — after V2-10

Proves actual audience observations can map back to beats/packaging and yield bounded useful policy changes.

### `AUTONOMOUS_OPERATING_PROOF` — after V2-11

Proves the full daily channel loop survives real operations with low owner burden.

### `FINAL_V2_RELEASE` — V2-12

Proves repeated product quality, reliability, measurable channel value, recovery, and owner acceptance.

---

## 8. Provider strategy

### 8.1 Reasoning / direction

Use the canonical ordered 9Router model authority. Prefer cheap capable models for routine bounded decisions and stronger models when utility/risk warrants escalation. Keep deterministic fallback plans for provider outages.

### 8.2 Generated imagery

Current accepted provisional path:

- dedicated direct `ai.api-cheap.site` image boundary;
- `AI_API_CHEAP_API_KEY` only;
- `gpt-5.5` proven and provisional default;
- `wan2.7-image-pro` and `qwen-image-2.0` unresolved/non-blocking.

Generated imagery is conceptual/illustrative only.

### 8.3 Voice

Benchmark and keep provider-neutral:

- ElevenLabs premium candidate;
- Chatterbox V3 local candidate;
- Kokoro local fallback.

Provider choice should consider perceived human quality, pronunciation, prosody, stability, alignment, latency, rights/license, and cost—not latency alone.

### 8.4 Music/SFX

Prefer a reusable rights-cleared local library and/or licensed/local-generation path with exact provenance. Paid music API is an optional upgrade only after quality/cost evidence and owner approval.

### 8.5 Rendering

Renderer authority remains the structured program/beat graphs, not Remotion itself. Remotion/programmatic React plus FFmpeg is the preferred current compositor approach if fresh implementation proves it. Local deterministic rendering, caching, and selective rerender remain strategic for cost.

---

## 9. Content strategy for channel growth

The factory should prioritize stories with combinations of:

- recognizable people/institutions;
- meaningful new decisions or conflict;
- clear consequences;
- strong primary documents;
- chart/data mechanisms;
- historical/timeline context;
- visual locations/assets;
- audience relevance;
- durable search interest;
- potential for a series follow-up.

High-value categories include:

- major central-bank decisions and speeches;
- tariffs/sanctions/trade disputes;
- major regulatory/court/policy decisions;
- Big Tech/major-company earnings or strategic events;
- geopolitical developments with market/policy relevance;
- fiscal/debt/treasury developments when there is a real event/story, not merely a static curve;
- consequential economic releases with a mechanism/impact story;
- Capital Chronicle original analytical synthesis when evidence is sufficient.

The product should avoid becoming a generic day-trading channel. Trust, explanation, evidence, and repeatability are differentiators.

---

## 10. Packaging and series philosophy

Each package should answer one concrete promise. Titles/thumbnails should generate curiosity without lying. The first seconds of the video should pay off the packaging rather than waste time on branding animation.

Potential recurring series should emerge from story supply and performance evidence. A series should have:

- a clear viewer promise;
- recognizable packaging identity;
- repeatable story eligibility;
- distinct narrative rhythm;
- a natural next-video/binge path;
- sustainable production cost.

Series must be retired if they become repetitive or underperform despite adequate sample size.

---

## 11. Retention and learning model

Every public package should preserve a production map that allows later audience metrics to be attributed to:

- hook;
- title/thumbnail promise;
- chapter;
- scene;
- beat;
- asset class;
- motion state;
- caption state;
- music/audio state;
- open loop;
- payoff;
- CTA.

The learning layer should distinguish correlation from certainty. A retention dip near a beat is evidence for investigation, not proof that one visual caused it. Repeated patterns across similar content should carry more weight.

Learning policies must be versioned, bounded, reversible, and owner-visible.

---

## 12. Safety, truth, rights, and public-write doctrine

All existing ContentOps hard gates remain.

- Never fabricate factual/numeric truth.
- Capital Chronicle remains analytical/numeric authority.
- Video narration may simplify/round only within explicitly allowed editorial policy and must not change meaning.
- Source documents and factual charts remain deterministic/source-backed.
- Generated images never prove facts.
- Real-person documentary imagery must be real and rights-cleared.
- Missing rights/evidence fail closed.
- Unknown public writes stop retry, read back, and reconcile.
- V2 has zero public-write authority until exact task authorization.
- TikTok/YouTube capability, scopes, quotas, approval state, and endpoint behavior must be fresh-verified at integration time.
- KILL_SWITCH remains authoritative.

---

## 13. Validation doctrine

Tests should be focused and product-risk driven.

Every media-producing task should include:

- structured contract validation;
- rights/provenance validation;
- evidence/claim validation;
- real render;
- media facts/codec/duration checks;
- captions/audio checks;
- cache/selective-rerender tests where relevant;
- package hash verification;
- no-secret/no-unauthorized-write checks;
- actual review artifacts.

Visual/audio PASS always requires actual media inspection by Jim/ChatGPT during pre-public phases.

Every platform-write task also requires exact remote object readback/reconciliation.

No empty CI/status is treated as failure by itself.

---

## 14. Git and concurrency doctrine

V2 proceeds concurrently with V1 but must not mutate live V1 runtime/store or overwrite concurrent V1 authority.

Each implementation task:

- fetches fresh remote master;
- reads current V2 authority;
- uses a dedicated branch/worktree;
- stages explicit scoped paths only;
- does not use `git add .` or `git add -A`;
- does not force push;
- preserves unrelated dirty/untracked work;
- regenerates CodeGraph after meaningful code/authority changes;
- pushes branch and returns final evidence;
- does not merge without independent audit unless Jim explicitly authorizes direct integration.

---

## 15. Current execution state

Accepted master baseline at this plan's creation:

`831dfb181b23cb7b27d195bbbc1bb7b847a86590`

Current accepted V2 foundations on master:

- Tier2-A renderer-neutral/evidence infrastructure as engineering reference;
- direct image boundary and `gpt-5.5` generation proof;
- CodeGraph/context system;
- V1 newsroom/evidence/memory/store foundations available for reuse.

Rejected creative branch:

`task/tier2-v2-creative-system-rebuild-v1` / `d231b54e026570442d9fd9269b61e55c3de31d21`

Classification:

`REJECTED_CREATIVE_PRODUCT_REFERENCE_ONLY`

Current next implementation task:

`TASK_CONTENTOPS_TIER2_V2_RETENTION_NATIVE_VIDEO_FACTORY_VERTICAL_SLICE_V1`

Required result:

`PASS_RETENTION_NATIVE_VERTICAL_SLICE_VISUAL_AUDIO_ACCEPTED`

No platform/public-write authority is granted by this plan.
