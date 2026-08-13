# Capital Chronicle ContentOps V2 — Retention-Native Video Factory Master Plan V2

Authority date: 2026-08-12
Product authority: `CONTENTOPS_V2_RETENTION_NATIVE_VIDEO_FACTORY_OWNER_DIRECTION_V2`
Plan status: `CURRENT_CANONICAL_V2_EXECUTION_PLAN`
Supersedes: `CONTENTOPS_V2_RETENTION_NATIVE_VIDEO_FACTORY_MASTER_PLAN_V1` where this document conflicts.
Companion constitution: `CONTENTOPS_V2_RETENTION_NATIVE_VIDEO_FACTORY_NORTH_STAR_V2.md`

# 0. Executive summary

Capital Chronicle ContentOps V2 will be built as an autonomous, evidence-governed video growth factory for YouTube hero/mid/long-form, YouTube Shorts, and TikTok-native short-form. The ambition is to make Capital Chronicle capable of becoming a breakout/trending financial and economic media brand through repeated high-quality story selection, truthful high-retention storytelling, professional visual/audio craft, platform-native packaging, disciplined publication, and learning from real audience behavior. Trending or virality is never guaranteed and never overrides truth, rights, or trust.

The central product lesson from the rejected V2 prototypes is now explicit: Remotion is not the creative model and must not be treated as one. The quality failure came from a generic motion grammar and weak creative authorship, not from the existence of a deterministic renderer. The canonical architecture therefore assigns direct presentation-layer authorship to the exact 9Router model `new/gpt-5.6-sol-xhigh` for three roles: `V2_CREATIVE_EDITOR`, `V2_MOTION_CODE_AUTHOR`, and `V2_CREATIVE_REVISION_AUTHOR`. Remotion becomes the deterministic compiler/render engine for per-video/per-shot code written under a strict sandbox.

The previous V2-01 implementation at `b6f5002903fba65a668506e4ca38ae61b907ab18` is rejected as `FAIL_CREATIVE_MOTION_ARCHITECTURE / REJECTED_CREATIVE_PRODUCT_REFERENCE_ONLY`. Its useful engineering around governed story selection, rights/provenance, asset acquisition, audio mastering, music/SFX, cache/selective rerender, package locking, and technical QA may be reused selectively. Its creative grammar must not be continued or polished.

The exact owner observations that control this rewrite are:

- motion repeated the same text-transition motif too often;
- transitions shared near-identical timing/easing and felt slow;
- chart reveals repeatedly crawled from left to right;
- some visual text collided or overlapped;
- machine metrics counted visual changes but did not detect perceptual repetition;
- the result still felt generated/template-driven rather than editorially directed;
- stronger visual richness requires many more purposeful assets, not just more animated cards;
- the strongest available creative model should directly author script, edit intent, and motion code.

This plan keeps the existing image-generation, asset-rights, voice-over, music/SFX, and mastering foundations unless a concrete blocker justifies changing them. `gpt-5.5` remains the provisional generated-illustration default through the accepted direct image boundary. Generated media is illustrative only; real-person documentary imagery must be real and rights-cleared.

The plan remains a twelve-task product sequence. V2-01 is replaced by the GPT-5.6 creative-code proof but occupies the same milestone slot. No later task may advance until actual media passes Jim/ChatGPT review.

Milestones:

```text
V2-01 → V2-03   PROFESSIONAL_CREATIVE_PROOF
V2-04 → V2-05   CHANNEL_PRODUCT_AND_SHADOW_FACTORY_PROOF
V2-06 → V2-07   PRIVATE_PLATFORM_DELIVERY_PROOF
V2-08            CONTROLLED_PUBLIC_COHORT_PROOF
V2-09 → V2-10   RETENTION_AND_LEARNING_PROOF
V2-11            AUTONOMOUS_OPERATING_PROOF
V2-12            FINAL_V2_RELEASE
```

# 1. Product objective and channel strategy

V2 is not merely a video renderer. It is the video/channel branch of the ContentOps autonomous newsroom and distribution system.

The daily product loop should be able to answer:

- What story deserves video today?
- What format does it deserve: no video, short only, mid-form, hero/long-form, or a coordinated portfolio?
- What is the truthful viewer promise?
- What narrative structure makes the story understandable and worth finishing?
- What real-world people, locations, documents, charts, maps, timelines, context images, B-roll, diagrams, and conceptual illustrations are needed?
- What should happen visually during every important spoken phrase?
- What audio state supports each beat?
- What packaging gives the work a fair chance to be discovered?
- What platform should receive which edit?
- What happened after publication and why?
- What should change next time?

The audience funnel is:

```text
TikTok / YouTube Shorts
→ discovery and fast payoff
→ YouTube mid-form / hero
→ trust and deeper understanding
→ repeat viewing / series identity
→ newsletter / canonical article / subscriber relationship
```

Short-form should not merely advertise long-form. It should deliver independent value while creating a natural path to deeper coverage where one exists.

Long-form should not exist just because 15–45 minutes is a target. Duration must be earned by evidence, narrative complexity, characters/institutions, mechanisms, documents, consequences, and visual material.

# 2. Authority and truth boundary

Capital Chronicle owns analytical and numeric truth: scenarios, probabilities, regimes, calculations, forecasts, market/economic analysis, realized outcomes, and analytical error attribution.

ContentOps owns newsroom/media/distribution/learning: intake, clustering/update chains, evidence/freshness/permission gates, ranking, selection, abstention, factual reporting, faithful transformation of Capital Chronicle context, scripting, editing, SEO, images/video, packaging, publication/readback/reconciliation, performance observation, and bounded creative/selection/timing learning.

The video system may never use trends, engagement, or model creativity as factual authority.

Every substantive factual beat must remain bound to canonical evidence or Capital Chronicle authority. Generated media must never silently become documentary proof.

# 3. Rejected prototypes and what to reuse

## 3.1 Tier2-A

Useful:

- renderer-neutral `VideoProgram` concept;
- evidence/source lineage;
- deterministic media handling;
- local narration path;
- captions;
- FFmpeg packaging;
- cache concepts;
- package hashing.

Not accepted as creative baseline.

## 3.2 Historical Tier2-B

Useful as historical engineering reference only. It failed visually because it still behaved like an animated data presentation.

## 3.3 `d231b54e...`

Useful:

- improved typography/hierarchy;
- native 9:16 proof;
- generated illustration integration;
- source-document treatment;
- rights-aware primitive;
- stronger deterministic QA;
- critic scene/time coverage;
- refusal to pad a weak story.

Rejected because the main visual remained too static and audio/asset/story engagement remained weak.

## 3.4 `b6f50029...`

Useful:

- EIA/Hormuz governed benchmark story/evidence;
- rights/provenance manifests;
- asset acquisition path;
- owned music/SFX/mastering path;
- package locking;
- selective rerender;
- static-run measurements;
- expanded technical QA.

Rejected because actual media still showed:

- repeated same-speed text motion;
- repeated easing/trajectory patterns;
- slow transitions;
- slow full-chart left-to-right reveals;
- text collisions/overlaps;
- repeated motion primitives despite high counted visual intervals;
- template-generated feel.

This is the key evidence that static-run counts and transition counts are necessary but not sufficient.

# 4. Exact GPT-5.6 creative-code architecture

## 4.1 Primary model

Exact required primary model through 9Router:

`new/gpt-5.6-sol-xhigh`

Required roles:

### `V2_CREATIVE_EDITOR`

Inputs:

- compact governed story/evidence packet;
- audience/brand constraints;
- platform target;
- available asset inventory/candidate summary;
- truth/rights boundaries;
- relevant performance learnings when they later exist.

Outputs:

- core promise;
- hook;
- narrative screenplay;
- spoken narration;
- open loops;
- payoff schedule;
- re-hooks;
- emotional register;
- shot sequence;
- asset-purpose requests;
- visual rhythm intent;
- sonic intent;
- platform-specific variant decisions.

### `V2_MOTION_CODE_AUTHOR`

Inputs:

- accepted semantic screenplay/shot plan;
- resolved assets;
- dimensions/FPS;
- shot timing;
- official Remotion technical references;
- current brand/theme tokens;
- creative-code sandbox contract.

Outputs:

- bounded per-video/per-shot React/TypeScript/SVG/Canvas code;
- explicit timing/easing/motion logic;
- chart/document/map/text/image composition;
- transitions and holds;
- audio cue placement;
- generated-code manifest.

### `V2_CREATIVE_REVISION_AUTHOR`

Inputs:

- localized deterministic defects;
- critic observations;
- affected shot source;
- neighboring shot context;
- rendered evidence/time ranges.

Outputs:

- minimal localized code patch;
- optionally updated shot timing or asset assignment;
- revision rationale and source hash.

Every new creative-author invocation starts `new/gpt-5.6-sol-xhigh`. The ordered execution fallback ladder is then `new/gpt-5.6-sol-high`, followed by `new/gpt-5.6-sol-medium`, only after an evidenced provider, latency, or output-risk blocker. A fallback result is labeled `DEGRADED_CREATIVE_MODEL` and cannot self-advance through professional acceptance. No role may be permanently pinned to HIGH or MEDIUM.

Large monolithic creative requests are not the production granularity. A fresh run begins with a bounded XHIGH Creative Director/Decomposer call that chooses story-specific semantic units and returns a compact Creative Bible plus Segment Manifest. Deterministic code—not another LLM—constructs each bounded downstream prompt from that global bible, governed evidence, the relevant segment, continuity state, asset inventory, and output contract. Fixed first-half/second-half segmentation is forbidden.

## 4.2 Sanitized model receipts

Every creative role call should record, without secrets:

- logical role;
- requested exact model;
- effective model when provider reports it;
- accepted/degraded state;
- input packet hash;
- output/code hash;
- attempt/fallback metadata;
- token/cost metadata if returned;
- latency if useful;
- semantic contract version.

# 5. Renderer and creative-code sandbox

Remotion remains the default deterministic execution engine unless future evidence shows it is the bottleneck.

Generated code should live under a bounded path such as:

```text
video/generated/<video_id>/
  composition.tsx
  shots/
    shot_001.tsx
    shot_002.tsx
  shared/
  manifest.json
```

Allowed:

- React;
- current compatible Remotion APIs/packages;
- approved deterministic visual helpers;
- local resolved assets;
- SVG;
- Canvas;
- bounded WebGL/Three.js where justified and explicitly allowed.

Forbidden:

- env/secret reads;
- render-time network access;
- arbitrary filesystem mutation;
- `child_process` or shell execution;
- dynamic npm/package installation;
- browser/session/profile access;
- publication/platform actions;
- evidence/factual mutation.

Required pre-execution validation:

- path allowlist;
- import/dependency allowlist;
- AST/static validation;
- no secret/environment APIs;
- no runtime network APIs;
- TypeScript validation;
- bounded composition/render dimensions/duration;
- deterministic asset references.

The sandbox preserves reproducibility and selective rerender while allowing GPT-5.6 to make bespoke creative decisions.

# 6. Remotion skill/reference policy

Primary technical reference:

`remotion-dev/skills@b12104ef5f1b1ca2ca5590fcc7c1804fbc85556f`

At minimum, GPT-5.6 creative-code work should consult the official current skill router and markup guidance, plus relevant references for timing, transitions, sequencing, multi-scene video, text/DOM measurement, images, captions, audio, SFX, maps, rendering, and metadata.

Community references may contribute ideas but are not authority. Useful lessons include render-and-inspect discipline, multi-property motion, careful safe zones, and separation of creative strategy from API mechanics.

Do not adopt community absolutes such as:

- stagger everything;
- Ken Burns every still;
- idle micro-motion everywhere;
- cross-dissolve every scene;
- a fixed five-layer stack;
- fixed animation timings across all stories.

Such rules can create the exact repetitive AI-motion signature Jim rejected.

# 7. Asset-rich editorial system

## 7.1 Candidate-first planning

The editor should request assets by editorial purpose:

- establish a person/institution/location;
- prove a claim;
- show the primary source;
- explain a mechanism;
- compare before/after;
- show chronology;
- provide geographic context;
- create a pattern interrupt;
- provide human/contextual texture;
- bridge an edit;
- land a payoff;
- support packaging.

The asset system then acquires or generates candidates before final shot composition.

Initial planning target for sufficiently rich stories:

- 25–60 viable candidate assets/visual states.

This is a target, not a quota.

## 7.2 Final selected state density

Initial hypotheses:

- 45–75s short: roughly 12–20 purposeful visual states;
- 90–150s proof: roughly 25–45 purposeful visual states;
- longer video: scale by beat/story depth.

A meaningful state must change what the viewer sees or understands. A recolored card or the same image at a new scale does not automatically count.

## 7.3 Asset classes

Support as relevant:

- official real-person photos;
- institution/building/location photos;
- primary source documents/releases/filings;
- highlighted source excerpts;
- deterministic charts;
- maps/routes/geographic explainers;
- timelines;
- before/after comparisons;
- table-to-graphic transformations;
- quote treatments;
- diagrams/mechanism visuals;
- historical/context imagery;
- rights-cleared B-roll/stills;
- generated conceptual illustrations;
- restrained icons/labels/textures.

## 7.4 Generated image authority

Preserve the accepted dedicated direct image route using `AI_API_CHEAP_API_KEY` and `gpt-5.5` as provisional generated-illustration default.

Generated images:

- are conceptual/illustrative enrichment;
- cannot establish factual/numeric truth;
- cannot substitute for real documentary imagery of real people;
- require provenance/disclosure/hash.

# 8. Motion and edit doctrine

The product needs authored editorial rhythm, not a motion-count optimization.

Preferred toolkit when justified:

- hard cuts;
- fast snap reveals;
- intentional still holds;
- document punch-ins/highlights;
- chart delta/point emphasis;
- focused chart segment traces;
- map movement;
- timelines;
- photo/B-roll cutaways;
- masks/wipes;
- reframes;
- comparison swaps;
- kinetic typography;
- diagram construction;
- selective parallax;
- audio-synchronized impacts;
- silence when narratively useful.

Avoid long runs of the same:

- transition family;
- easing profile;
- duration;
- reveal direction;
- layout grammar;
- primary primitive;
- chart reveal style.

As an initial screen, more than two consecutive beats with near-identical motion grammar should trigger inspection unless explicitly motivated.

Chart motion should communicate the conclusion as efficiently as possible. A slow whole-chart left-to-right draw is not the default. Alternatives include direct cuts, focused ranges, deltas, point highlights, annotations, comparison swaps, and fast trace-ins.

# 9. Text, captions, and layout safety

Zero accepted text collisions.

The system must measure rather than guess:

- text bounds;
- DOM bounds;
- chart label bounds;
- source label bounds;
- caption bounds;
- safe-zone bounds;
- transition-state overlap.

Required checks include bounding-box intersections at critical frames and representative transitions.

Captions remain important but must not become the only visible motion. They should normally stay within two lines and preserve platform safe zones.

# 10. Audio architecture

Preserve current provider abstraction and current local/Kokoro baseline unless a direct blocker appears.

Audio plan should include:

- voice identity;
- pronunciation;
- emphasis/prosody;
- pause map;
- phrase/word timing;
- music bed per beat/chapter;
- tension/resolution state;
- SFX cues;
- ducking;
- fades;
- loudness/peak target;
- rights/provenance.

Initial target remains around -16 LUFS ±1 and true peak ≤ approximately -1.5 dBTP.

V2-02 remains the dedicated premium voice/asset-intelligence task. V2-01 should not churn voice provider infrastructure; it should prove that strong creative authorship can use the existing audio stack effectively.

# 11. Independent multimodal review

Use an independent strong multimodal critic rather than self-review only.

Critic inputs should include:

- actual representative frames/clips;
- shot/beat IDs;
- time ranges;
- collision diagnostics;
- repetition diagnostics;
- asset manifest;
- hook/payoff timing;
- audio state summary.

Critic should explicitly inspect:

- repetitive motion grammar;
- slow or annoying transitions;
- chart crawl;
- text collisions;
- generic AI/template feel;
- asset starvation or overreuse;
- shot/narration mismatch;
- weak hierarchy;
- caption dominance;
- weak hook/payoff visualization.

Critic output is evidence for revision, not final authority. Jim/ChatGPT owns professional acceptance during creative-proof stages.

# 12. Machine diagnostics

In addition to truth/rights/package checks, V2 must develop diagnostics for:

- text collision count;
- safe-zone overflow;
- transition-family distribution;
- consecutive transition-family repetition;
- easing-profile distribution/repetition;
- animation/reveal duration distribution;
- reveal-direction repetition;
- layout-state repetition;
- visual primitive/motif repetition;
- chart reveal duration/crawl risk;
- asset reuse concentration;
- captions-hidden visual-change cadence;
- longest primary-visual static run;
- hook timing;
- first payoff timing;
- open-loop closure;
- audio loudness/peak;
- music/SFX coverage;
- rights/evidence coverage;
- cache/selective rerender integrity;
- package hashes.

Diagnostics are screening tools, not aesthetic judges.

# 13. Cost and model-control doctrine

ContentOps remains the runtime product. Codex remains the repository builder. The product must not depend on a frontier coding agent staying inside the entire production control loop.

Repo evidence shows newsroom/routing can exceed one million model tokens before article/video work. Discovery, clustering, novelty, evidence, and published memory therefore remain shared/amortized infrastructure.

Canonical cost pattern:

```text
shared continuous intelligence
→ compact governed story packet
→ exact GPT-5.6 creative intervention at high-value points
→ deterministic/local transforms/assets/render/cache/package
→ deterministic QA
→ independent bounded multimodal review
→ exact GPT-5.6 localized revision only when justified
```

Do not hardcode temporary provider pricing or subscription economics into product authority. Measure actual calls, tokens, image/audio generations, render time, retries, and cash cost where returned.

# 14. Platform-native doctrine

## YouTube hero/mid/long

Optimize for:

- packaging promise;
- sustained arc;
- chapters;
- re-hooks;
- richer evidence sequences;
- changing visual/audio states;
- search longevity;
- series/binge path.

## YouTube Shorts

Optimize for:

- immediate hook;
- portrait-native composition;
- fast first payoff;
- short caption groups;
- meaningful visual density;
- strong last-frame/loop/CTA behavior;
- cover-frame planning.

## TikTok

Optimize for:

- native 9:16 edit;
- scroll interruption;
- conversational pacing;
- dense but meaningful sequence changes;
- caption safe zones;
- platform-specific packaging/CTA;
- exact upload capability/approval constraints.

Do not resize one master blindly.

# 15. TASK ROADMAP

## V2-01 — GPT-5.6 Creative-Code Asset-Rich Video Vertical Slice

**Task label**

`TASK_CONTENTOPS_TIER2_V2_GPT56_CREATIVE_CODE_ASSET_RICH_VIDEO_VERTICAL_SLICE_V1`

**Required result**

`PASS_RETENTION_NATIVE_VERTICAL_SLICE_VISUAL_AUDIO_ACCEPTED`

### User problem

The first retention-native attempt passed many machine checks but still looked repetitive, slow, template-driven, and occasionally visually broken. Generic motion primitives remain too much of the creative authority.

### Why now

Before investing in longer videos, provider breadth, uploads, analytics, or a daily factory, V2 must prove the central hypothesis: a strong model directly authoring screenplay/edit/motion code can produce a material creative-quality jump while deterministic Remotion retains reproducibility and safety.

### Capability delivered

- exact role-specific GPT-5.6 routing;
- sanitized model receipts;
- compact governed story packet;
- integrated narration/edit screenplay;
- per-shot asset-purpose planning;
- sandboxed generated creative code;
- per-shot Remotion execution;
- collision/repetition diagnostics;
- independent critic;
- localized GPT-5.6 revision;
- selective rerender.

### Controlled benchmark

Prefer reusing the governed EIA/Hormuz story/evidence from the failed `b6f50029...` package, after revalidating every imported evidence/right/asset reference. Do not reuse its creative plan or motion code. Reusing the story controls the experiment: old generic grammar versus GPT-5.6-authored creative code.

If that governed story cannot be safely reconstructed from accepted repo/runtime evidence, choose another qualified non-Treasury governed story with institution/person, change/conflict, source document, geography/timeline, data, and multiple asset classes.

### Provider/model scope

Primary creative model must be exact `new/gpt-5.6-sol-xhigh` through 9Router for all three creative-author roles.

Keep existing image, asset, narration, music/SFX, and mastering providers unchanged unless directly blocked.

Bounded network may retrieve official/public-domain/clearly rights-usable assets and use the accepted direct `gpt-5.5` illustration route when useful.

### Required visible result

Produce:

- one native 45–60 second 9:16 short;
- one 90–150 second 16:9 editorial proof;
- actual narration/music/SFX;
- captions-hidden review variants or clips;
- contact sheets;
- motion strips;
- representative high-motion sequences;
- creative screenplay/shot plan;
- generated-code manifest;
- sanitized GPT-5.6 role receipts;
- asset candidate manifest;
- selected asset/provenance manifest;
- collision/repetition diagnostics;
- audio QA;
- critic report;
- localized revision evidence;
- compact review README.

### Asset target

When story supply supports it:

- acquire roughly 25–60 viable candidates/states;
- short uses roughly 12–20 purposeful visual states;
- 90–150s proof uses roughly 25–45 purposeful states.

These are hypotheses, not quotas.

### Motion acceptance

- zero accepted text collisions;
- no default slow whole-chart wipe;
- no long repeated same-speed text transition runs;
- no more than two consecutive near-identical transition/easing/duration/direction patterns without explicit reason;
- primary visual remains understandable with captions hidden;
- asset changes correspond to narrative purpose;
- edit feels authored, not template generated.

### QA/validation

- creative-model exact-identity/no-fallback/exhaustion tests;
- sandbox/path/import/AST tests;
- TypeScript/Remotion typecheck;
- collision/overflow tests;
- repetition diagnostics tests;
- rights fail-closed tests;
- real short render;
- real 16:9 proof render;
- audio QA;
- cache/selective rerender proof;
- immutable package verification;
- CodeGraph current;
- git diff check.

### Cost/runtime bound

Use bounded GPT-5.6 calls, proxy-first rendering, cached assets, and localized revisions. Record tokens/cost where returned. No paid-plan purchase.

### Must not build

- platform upload;
- public write;
- full 3–6 minute mid-form unless architecture proof unexpectedly requires it;
- daily portfolio;
- analytics/learning;
- new image/TTS provider bakeoffs without a direct blocker.

### Acceptance authority

Jim/ChatGPT actual media review. Machine/critic PASS cannot substitute.

### Remaining blocker after PASS

Premium repeatable voice/audio and systematic rights-aware asset intelligence still need dedicated hardening.

### Next

V2-02.

---

## V2-02 — Premium Audio and Rights-Aware Asset Intelligence

**Task label**

`TASK_CONTENTOPS_TIER2_V2_PREMIUM_AUDIO_AND_ASSET_INTELLIGENCE_V1`

**Required result**

`PASS_PREMIUM_AUDIO_AND_ASSET_ENGINE_ACCEPTED`

### User problem

Even a strong edit loses credibility when narration sounds synthetic, pronunciation is weak, music is generic/absent, or visual sourcing is inconsistent.

### Why now

Only after V2-01 proves the creative-code architecture should the project optimize the two largest enrichment systems: voice/audio and systematic real-world asset intelligence.

### Capability delivered

Voice routing and evaluation across available authorized providers, without making one vendor a permanent architecture dependency. Preserve and benchmark existing local/Kokoro path and any currently authorized premium option. Add pronunciation rules, emphasis/prosody plans, phrase/word timing, scene-level regeneration, and normalized mastering.

Build a reusable rights-safe sonic library: analytical-neutral, tension/policy, corporate/technology, geopolitical, resolution/outro, plus restrained risers, stingers, hits, whooshes, and data/chart cues.

Complete the asset-intelligence path:

```text
story/entity/document need
→ editorial asset purpose
→ candidate discovery
→ rights classification
→ composition/quality scoring
→ retrieval
→ hash/provenance
→ crop variants
→ shot assignment
```

### Required visible result

- blind voice comparison bundle;
- accepted primary and fallback voice;
- pronunciation/economics-name test set;
- several reusable music beds;
- reusable restrained SFX set;
- entity/institution asset pack;
- document/regulation asset pack;
- location/geopolitical asset pack;
- rerender of the accepted V2-01 proof with chosen premium audio/assets.

### Acceptance

- Jim/ChatGPT accepts voice quality;
- music supports rather than masks speech;
- no rights ambiguity;
- real-person imagery is real;
- generated imagery remains conceptual;
- asset resolution fails closed;
- audio metrics and audible joins pass.

### Operator dependency

If a paid provider materially wins and free/current authorization is insufficient, stop before purchase and request owner decision.

### Must not build

- social upload;
- daily portfolio;
- broad stock-media scraper;
- fake documentary imagery.

### Next

V2-03.

---

## V2-03 — Diverse Story-Mode Corpus and Repeated Creative Acceptance

**Task label**

`TASK_CONTENTOPS_TIER2_V2_DIVERSE_STORY_MODE_CORPUS_AND_MOTION_ACCEPTANCE_V1`

**Required result**

`PASS_REPEATED_PROFESSIONAL_CREATIVE_QUALITY`

### User problem

One excellent video may hide hardcoded assumptions. The product must generalize across distinct editorial structures without becoming a template zoo.

### Capability delivered

Prove at least:

- `ENTITY_EVENT`;
- `DOCUMENT_REVEAL`;
- `DATA_MECHANISM`;
- `CONFLICT_TIMELINE`;
- optional `EARNINGS_BREAKDOWN`;
- one explicit `VIDEO_NOT_SELECTED`.

GPT-5.6 may use shared brand tokens and approved helper components, but shot/edit implementation should remain story-specific.

### Required visible result

- at least three native shorts;
- at least two mid-form pieces;
- four different story-mode examples;
- one abstention;
- one 8–15 minute hero only if a story genuinely earns it;
- cross-story visual/audio comparison board;
- per-mode runtime/cost evidence.

### Acceptance

At least three story modes earn Jim/ChatGPT PASS. No mode appears to be the same video with swapped colors/assets. Motion signatures differ where stories differ, while brand identity remains coherent.

### Must not build

- platform upload;
- performance learning;
- final daily scheduler.

### Milestone

Pass closes `PROFESSIONAL_CREATIVE_PROOF`.

### Next

V2-04.

---

## V2-04 — Packaging, Discovery, Thumbnail, and Channel Series Engine

**Task label**

`TASK_CONTENTOPS_TIER2_V2_PACKAGING_DISCOVERY_AND_CHANNEL_SERIES_ENGINE_V1`

**Required result**

`PASS_CHANNEL_PACKAGING_AND_SERIES_SYSTEM`

### User problem

Great videos can still fail if packaging makes a weak or misleading promise. A channel also needs recognizable repeatable series, not disconnected one-offs.

### Capability delivered

Implement renderer-independent packaging contracts for:

- title variants;
- thumbnail variants;
- short cover-frame variants;
- first-line/caption hooks;
- SEO/search intent;
- series identity;
- CTA;
- binge/next-content target;
- packaging-promise-delivery audit.

Trend/search signals may influence opportunity, timing, framing, and packaging only. They never establish truth.

### Required visible result

For each hero/mid-form candidate:

- three meaningfully different title strategies;
- three meaningfully different thumbnail concepts/renders;
- multiple hook/opening variants where useful;
- search intent;
- description/chapters;
- series/playlist path;
- CTA/binge path.

For shorts:

- multiple cover-frame candidates;
- native title/caption variants;
- platform CTA.

Define and test 4–6 initial Capital Chronicle series hypotheses.

### Acceptance

- promise delivered by content;
- no unsupported clickbait;
- thumbnails readable at small size;
- variants are strategically different, not cosmetic;
- series each have a clear audience promise.

### Next

V2-05.

---

## V2-05 — Shadow Daily Video Portfolio

**Task label**

`TASK_CONTENTOPS_TIER2_V2_SHADOW_DAILY_VIDEO_PORTFOLIO_V1`

**Required result**

`PASS_SHADOW_VIDEO_PORTFOLIO_FACTORY`

### User problem

A video factory must decide what not to produce. Generating video for every article or every trend creates filler and burns money.

### Capability delivered

Daily portfolio selection across the canonical story universe using:

- materiality;
- evidence strength;
- novelty/update chain;
- narrative depth;
- asset availability;
- visualizability;
- current demand;
- shelf life;
- recent topic/series concentration;
- platform fit;
- estimated production cost;
- expected qualified engagement.

Output includes selected, short-only, mid/hero, deferred, blocked, and not-selected.

### Required visible result

Seven-day shadow/replay run or equivalent coverage:

- daily candidate universe;
- reasons for selected/rejected/deferred candidates;
- 0–1 hero/mid candidate per day when earned;
- 0–3 short candidates per day when earned;
- explicit no-video days;
- at least three complete high-quality packages if story supply permits;
- cost/runtime/asset/model usage evidence;
- diversity/concentration report.

### Acceptance

- zero filler;
- no duplicate/update-chain abuse;
- decisions reproducible;
- trends never become factual authority;
- cost bounded;
- no platform upload.

### Milestone

Pass closes `CHANNEL_PRODUCT_AND_SHADOW_FACTORY_PROOF` with V2-04.

### Next

V2-06.

---

## V2-06 — YouTube Private/Unlisted Upload, Processing, and Readback

**Task label**

`TASK_CONTENTOPS_TIER2_V2_YOUTUBE_PRIVATE_UPLOAD_PROCESSING_AND_READBACK_V1`

**Required result**

`PASS_YOUTUBE_PRIVATE_TRANSPORT_AND_READBACK`

### User problem

A local MP4 is not a delivery product. Upload, metadata, captions, thumbnail state, processing, duplicate prevention, and strict readback must be reliable.

### Capability delivered

Provider-neutral YouTube transport integrated with canonical publication/reconciliation principles:

- resumable upload;
- exact account/channel validation;
- private/unlisted only;
- metadata;
- thumbnails;
- captions;
- playlist/series placement;
- processing polling;
- strict readback;
- recovery;
- unknown-write handling;
- no blind retry after ambiguous outcome.

### Required visible result

- one private hero/mid upload;
- one private/unlisted Short;
- exact processing/readback evidence;
- metadata/caption/thumbnail state;
- provider object IDs;
- interruption/recovery proof;
- no public visibility.

### Hard boundaries

No public upload. No credential exposure. No V1 publication-authority duplication.

### Operator dependency

Fresh YouTube OAuth scope/channel identity validation if not already available.

### Next

V2-07.

---

## V2-07 — YouTube Shorts + TikTok Controlled Delivery

**Task label**

`TASK_CONTENTOPS_TIER2_V2_SHORTS_AND_TIKTOK_CONTROLLED_DELIVERY_V1`

**Required result**

`PASS_CONTROLLED_SHORT_VIDEO_DELIVERY`

### User problem

Short-form delivery must respect platform-native packaging and provider capability constraints.

### Capability delivered

YouTube Shorts private/unlisted path plus the official TikTok controlled path supported by current app/account capability, such as draft/private/self-only delivery where public direct posting is not yet authorized.

### Required visible result

- private YouTube Short with exact readback;
- TikTok draft/private controlled object if provider capability permits;
- exact account/privacy/readback evidence;
- native metadata/captions/cover logic;
- safe recovery.

### Acceptance

- not a blind crop of long-form;
- no claim of TikTok public automation unless approval exists;
- exact privacy state verified;
- no duplicate/unknown write.

### Milestone

Pass closes `PRIVATE_PLATFORM_DELIVERY_PROOF`.

### Next

V2-08.

---

## V2-08 — Exact-Authorized Public Growth Pilot

**Task label**

`TASK_CONTENTOPS_TIER2_V2_EXACT_AUTHORIZED_PUBLIC_GROWTH_PILOT_V1`

**Required result**

`PASS_SMALL_PUBLIC_VIDEO_COHORT`

### User problem

Private transport cannot prove audience response.

### Authorization

This task requires new explicit Jim public-write authorization. No prior V2 task grants it.

### Capability delivered

Small controlled real cohort with strict publication/readback/reconciliation and incident handling.

### Suggested cohort

Approximately:

- two hero/mid-form YouTube videos;
- six YouTube Shorts;
- bounded TikTok cohort only if app/account/public-post authority is genuinely available;
- no-publication remains valid when no story qualifies.

### Required visible result

- exact public object IDs/URLs;
- processing/readback;
- title/thumbnail/package used;
- publication timing;
- 24h/72h observations where available;
- incidents/recovery;
- no unknown write.

### Acceptance

- no truth/rights/publication incident;
- no duplicate publication;
- all public objects reconciled;
- each package is platform-native.

### Milestone

Pass closes `CONTROLLED_PUBLIC_COHORT_PROOF`.

### Next

V2-09.

---

## V2-09 — Retention Analytics and Shot/Beat Attribution

**Task label**

`TASK_CONTENTOPS_TIER2_V2_RETENTION_ANALYTICS_AND_BEAT_ATTRIBUTION_V1`

**Required result**

`PASS_BEAT_LEVEL_RETENTION_OBSERVABILITY`

### User problem

A growth engine cannot learn if retention drops remain disconnected from specific creative decisions.

### Capability delivered

Map platform observations back to production identity:

```text
platform timestamp/ratio
→ video_id
→ scene_id
→ shot_id / beat_id
→ asset
→ motion state
→ caption state
→ audio state
→ hook/open-loop/payoff
```

Collect official/authorized metrics only. Missing metrics remain unavailable, never zero.

### Required visible result

- per-video retention curves;
- shot/beat drop reports;
- spike/dip attribution;
- packaging versus delivery report;
- short-to-hero funnel observations;
- viewer/subscriber/returning-viewer observations where available;
- freshness/provenance.

### Acceptance

- correct identity/timestamp mapping;
- no fabricated metrics;
- insufficient sample results in `NO_POLICY_CHANGE`.

### Next

V2-10.

---

## V2-10 — Trend, Packaging, and Creative Learning

**Task label**

`TASK_CONTENTOPS_TIER2_V2_TREND_PACKAGING_AND_CREATIVE_LEARNING_V1`

**Required result**

`PASS_BOUNDED_VIDEO_GROWTH_LEARNING`

### User problem

Analytics that never change future production are only reporting.

### Capability delivered

Versioned bounded policy updates for:

- story-mode preference;
- hook class;
- first-payoff timing;
- shot/beat density;
- asset class mix;
- motion style concentration;
- voice/music state;
- title/thumbnail strategy;
- length;
- series;
- publication window;
- platform variant.

Learning must never change evidence, factual meaning, rights, or Capital Chronicle analytical truth.

### Required visible result

- at least three supported improvement conclusions once sample is sufficient;
- one packaging-learning example;
- one retention-driven creative/edit example;
- one explicit `NO_POLICY_CHANGE` due insufficient sample;
- versioned before/after policy state;
- trend-signal usefulness report.

### Acceptance

- small samples do not trigger large changes;
- every update traces to real observations;
- no retroactive factual mutation.

### Milestone

Pass closes `RETENTION_AND_LEARNING_PROOF` with V2-09.

### Next

V2-11.

---

## V2-11 — Autonomous Video Channel Operating System

**Task label**

`TASK_CONTENTOPS_TIER2_V2_AUTONOMOUS_CHANNEL_OPERATING_SYSTEM_V1`

**Required result**

`PASS_AUTONOMOUS_VIDEO_CHANNEL_LOOP`

### User problem

Individual successful videos do not create an operating channel.

### Capability delivered

One governed daily channel loop:

```text
story universe
→ video opportunity portfolio
→ production queue
→ asset/audio acquisition
→ GPT-5.6 creative authoring
→ render/QA/revision
→ packaging
→ authorized schedule/publication
→ readback
→ performance
→ learning
```

Extend the canonical V5 operator surface rather than building a parallel dashboard. Show Video Today, candidate queue, selected/not-selected, production stage, rights blockers, model/degraded state, review state, platform processing, retention, series health, cost, incidents, and kill switch.

### Required visible result

10–15 operating-day shadow/live soak:

- repeatable cadence;
- no filler;
- no duplicate/topic concentration abuse;
- restart/recovery evidence;
- actual packages/public objects where authorized;
- actual metrics;
- daily no-publication when appropriate;
- operator can understand state quickly.

### Acceptance

- at least ~90% successful scheduled opportunities subject to real external availability;
- no unknown public write;
- no rights/truth incident;
- bounded cost;
- no V1 regression.

### Milestone

Pass closes `AUTONOMOUS_OPERATING_PROOF`.

### Next

V2-12.

---

## V2-12 — Final Reliability, Growth Proof, and V2 Release

**Task label**

`TASK_CONTENTOPS_TIER2_V2_FINAL_RELIABILITY_GROWTH_PROOF_AND_RELEASE_V1`

**Required result**

`PASS_CONTENTOPS_V2_VIDEO_FACTORY_OWNER_ACCEPTED`

### User problem

A product is not finished after one good campaign; it needs repeated quality, channel growth evidence, safety, reliability, and owner acceptance.

### Minimum proof corpus

Suggested final corpus before release:

- at least six accepted hero/mid/long YouTube videos;
- at least twenty accepted Shorts;
- TikTok corpus where exact authorization exists;
- at least three recurring series;
- at least three distinct story modes;
- at least one `VIDEO_NOT_SELECTED` day;
- at least one upload/recovery proof;
- at least one retention-driven creative improvement.

### Growth proof

Use channel-relative evidence rather than fake universal viral thresholds.

Look for:

- a majority of new uploads improving on prior rolling format medians on primary metrics;
- improving or competitive retention relative to similar-length channel videos;
- Shorts improving on channel-relative stayed-to-watch/average-percentage-viewed evidence where available;
- rising monthly audience/returning viewers over a meaningful window;
- at least one repeatable series with sustained demand;
- at least one breakout item materially above channel median;
- measured subscriber conversion and canonical-content clicks;
- no trust degradation/clickbait pattern.

These are proof directions, not guaranteed numerical promises.

### Operational proof

- production success around or above 90% where external dependencies are available;
- zero truth/rights/secret/public-write incidents;
- exact readback for every governed public object;
- measured cost within owner budget;
- kill-switch and recovery proven;
- immutable package/readback lineage;
- V1 remains healthy.

### Final visible result

- autonomous V2 Daily Video operating loop;
- YouTube hero + Shorts channel loop;
- TikTok loop where authorized;
- retention/series/portfolio/cost operator view;
- final release evidence;
- owner-approved release identity.

# 16. Milestone gate definitions

## `PROFESSIONAL_CREATIVE_PROOF`

Requires V2-01 through V2-03 PASS. Actual media must be owner/ChatGPT accepted across multiple story modes. Technical correctness alone is insufficient.

## `CHANNEL_PRODUCT_AND_SHADOW_FACTORY_PROOF`

Requires V2-04 and V2-05 PASS. Packaging/series strategy and disciplined daily portfolio selection must exist before transport scaling.

## `PRIVATE_PLATFORM_DELIVERY_PROOF`

Requires V2-06 and V2-07 PASS. Private/controlled object creation and readback must be reliable before public authority.

## `CONTROLLED_PUBLIC_COHORT_PROOF`

Requires V2-08 PASS under exact owner authorization.

## `RETENTION_AND_LEARNING_PROOF`

Requires V2-09 and V2-10 PASS using real public observations.

## `AUTONOMOUS_OPERATING_PROOF`

Requires V2-11 PASS over a meaningful soak.

## `FINAL_V2_RELEASE`

Requires V2-12 owner acceptance.

# 17. Global execution rules

Every V2 task must:

- fetch fresh remote master before branch-sensitive work;
- use a clean dedicated worktree/branch unless exact task says otherwise;
- preserve concurrent V1 work;
- deliver user-visible capability or remove a direct blocker;
- keep support docs/tests/evidence proportional to product work;
- produce actual media for media-quality gates;
- record exact model/provider identity without secrets;
- preserve evidence/rights/freshness/public-write gates;
- stage explicit paths only;
- commit and push;
- not merge unless separately authorized;
- return concise evidence with base/final HEAD, branch, commit, changed paths, focused validation, actual media paths, model/provider usage, cost where known, safety state, caveats, and exact next action.

One implementation receives one independent audit and at most one bounded correction before architecture/scope reconsideration. Do not create audit loops.

# 18. Current execution pointer

Current task:

`TASK_CONTENTOPS_TIER2_V2_GPT56_CREATIVE_CODE_ASSET_RICH_VIDEO_VERTICAL_SLICE_V1`

Current required result:

`PASS_RETENTION_NATIVE_VERTICAL_SLICE_VISUAL_AUDIO_ACCEPTED`

Current public-write authority:

`ZERO_VIDEO_PUBLIC_WRITE_AUTHORITY`

Current exact creative model:

`new/gpt-5.6-sol-xhigh`

Current image/asset/voice/audio policy:

preserve the accepted existing paths; expand asset richness; do not churn providers without a blocker.

Current renderer policy:

GPT-5.6 authors creative code; Remotion deterministically renders it.

Current Remotion technical baseline:

`remotion-dev/skills@b12104ef5f1b1ca2ca5590fcc7c1804fbc85556f`, with community references only as selective craft inputs.

Do not advance to V2-02 until Jim/ChatGPT accepts the actual V2-01 replacement media.
