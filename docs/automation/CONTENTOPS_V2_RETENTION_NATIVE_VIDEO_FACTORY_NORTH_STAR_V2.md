# Capital Chronicle ContentOps V2 — Retention-Native Video Factory North Star V2

Authority date: 2026-08-13
Product authority: `CONTENTOPS_V2_RETENTION_NATIVE_VIDEO_FACTORY_OWNER_DIRECTION_V2`
Status: `CURRENT_CANONICAL_V2_PRODUCT_CONSTITUTION`
Supersedes: `CONTENTOPS_V2_RETENTION_NATIVE_VIDEO_FACTORY_NORTH_STAR_V1` where this document conflicts.

## Mission

Build Capital Chronicle ContentOps V2 into an autonomous, evidence-governed media growth engine for YouTube hero/mid/long-form, YouTube Shorts, and TikTok-native short-form. The system must repeatedly select stories that deserve video, turn them into high-retention editorial experiences, package them for discovery, publish only under exact authorization, read back the resulting platform state, measure real audience behavior, and improve future story selection, packaging, pacing, visuals, and audio without weakening factual truth, rights discipline, or Capital Chronicle analytical authority.

The ambition is to make Capital Chronicle capable of becoming a breakout or trending financial/economic media channel. That is a product aspiration, not a guaranteed outcome. The system must optimize the probability of durable audience growth and breakout distribution through better story choice, stronger truthful hooks, richer asset use, professional edit craft, platform-native packaging, and retention learning. It must never manufacture controversy, FOMO, or unsupported claims merely to chase views.

## Product promise

The finished V2 product should answer, every day:

1. Which current story is actually worth producing as video?
2. Why would a viewer care now?
3. What truthful promise makes the story compelling without clickbait?
4. What narrative arc, open loops, payoffs, and re-hooks will sustain attention?
5. What people, institutions, locations, primary documents, charts, maps, timelines, comparisons, B-roll, diagrams, and generated conceptual imagery are required to make the story visually alive?
6. What should the viewer see at each spoken phrase, not merely at each scene boundary?
7. What should be cut, held, punched in, highlighted, traced, reframed, or replaced at each editorial beat?
8. What narration, music, SFX, pauses, emphasis, and sonic transitions support the story?
9. What edit is native to YouTube, Shorts, and TikTok rather than being a resize?
10. Is the package factual, rights-safe, visually legible, non-repetitive, professionally paced, and technically sound?
11. Should it publish, defer, block, or abstain?
12. What did real viewers do after publication, and what bounded policy change is justified by that evidence?

`VIDEO_NOT_SELECTED`, `VIDEO_BLOCKED`, `DEFERRED`, and no-publication are valid outputs. No content quota may force filler.

## Exact creative model authority

The primary creative-code model for V2 is exact:

`new/gpt-5.6-sol-xhigh`

through the canonical 9Router API/seam.

It is mandatory as the primary model for:

- `V2_CREATIVE_EDITOR`
- `V2_MOTION_CODE_AUTHOR`
- `V2_CREATIVE_REVISION_AUTHOR`

The model directly authors the presentation-layer screenplay, narration/pacing, shot-by-shot edit strategy, motion timing, transition strategy, chart and text choreography, asset-purpose requests, audio cue intent, and bounded per-shot Remotion React/TypeScript/SVG/Canvas implementation.

Remotion is the deterministic renderer/compiler. Remotion is not the creative director.

If a fallback model is used because the exact model is unavailable, the package must be marked `DEGRADED_CREATIVE_MODEL`. Such output may be rendered for diagnosis, but it cannot self-advance through the professional visual/audio gate.

This model authority does not grant factual authority. Every factual or numeric statement remains bound to governed ContentOps/Capital Chronicle evidence.

The canonical creative-brain abstraction is defined, but only one implementation is active:

- `NineRouterGPT56Brain` — **DEFAULT**, with every fresh creative invocation starting `new/gpt-5.6-sol-xhigh`;
- `CodexLocalBrain` — **OWNER-CONTROLLED FALLBACK, NOT ACTIVE**.

Shared evidence, asset brokerage, visual-grounding contracts, storyboard/animatic, renderer, QA, and package state should remain brain-independent where practical. Jim alone may later activate `CodexLocalBrain`, and only after a correctly exercised concrete-first XHIGH replacement proof still demonstrates systemic creative/comprehension failure. Defining the seam grants Codex no present runtime, scheduling, provider, or public-write authority.

## Controlling visual-storytelling doctrine

`CONCRETE_FIRST_ABSTRACT_SECOND`

The viewer should normally see the clearest recognizable real-world object, location, primary evidence, or native data visualization before an abstract metaphor. Real documentary/contextual media, primary documents, maps, native charts, and concrete explanatory illustration must not be silently replaced by convenient SVG geometry. Abstract diagrams and metaphors remain valid only when they clarify a relationship that concrete evidence cannot show as directly.

Default visual priority:

1. real documentary/contextual media;
2. primary source/document;
3. native data visualization/map;
4. concrete explanatory illustration;
5. abstract diagram/metaphor.

A lower-priority choice requires an explicit editorial reason. It must not dominate merely because code generation makes it cheap.

## Canonical creative architecture

```text
CANONICAL CONTENTOPS STORY UNIVERSE
            ↓
VIDEO OPPORTUNITY / PORTFOLIO SELECTION
            ↓
SELECTED | SHORT_ONLY | MIDFORM | HERO | DEFERRED | BLOCKED | NOT_SELECTED
            ↓
COMPACT GOVERNED STORY / EVIDENCE PACKET
            ↓
new/gpt-5.6-sol-xhigh — CREATIVE DIRECTOR / ADAPTIVE DECOMPOSER
            ↓
CREATIVE BIBLE + STORY-SPECIFIC SEMANTIC SEGMENT GRAPH
            ↓
DETERMINISTIC BOUNDED CHILD-PROMPT CONSTRUCTION
            ↓
BOUNDED XHIGH SEGMENT AUTHORSHIP
            ↓
CONCRETE VISUAL-GROUNDING CONTRACTS + RIGHTS-SAFE ASSET BROKER
            ↓
RESOLVED ASSETS + NATIVE CHART/MAP/DOCUMENT COMPILERS
            ↓
KEYFRAME STORYBOARD + CAPTIONS-HIDDEN ANIMATIC / PROXY
            ↓
COMPREHENSION ACCEPTANCE OR PLAN-LEVEL REVISION
            ↓
new/gpt-5.6-sol-xhigh — BOUNDED V2_MOTION_CODE_AUTHOR CALLS
            ↓
SANDBOXED PER-VIDEO / PER-SHOT CREATIVE CODE
            ↓
STATIC / IMPORT / AST / TYPE VALIDATION
            ↓
REMOTION PROXY RENDER
            ↓
TEMPORAL / COMPREHENSION CRITIC
            ↓
BOUNDED CREATIVE REVISION
            ↓
FINAL RENDER + DETERMINISTIC MEDIA / RIGHTS / AUDIO / PACKAGE QA
            ↓
INDEPENDENT MULTIMODAL CRITIC
            ↓
JIM / CHATGPT ACTUAL MEDIA ACCEPTANCE
            ↓
PLATFORM-NATIVE PACKAGE
            ↓
LATER EXACT-AUTHORIZED UPLOAD / READBACK / RECONCILIATION
            ↓
REAL RETENTION / PERFORMANCE ATTRIBUTION
            ↓
BOUNDED CREATIVE / PACKAGING / TIMING LEARNING
            ↓
NEXT PORTFOLIO DECISION
```

## Why this architecture exists

The rejected V2 prototypes established that a strong renderer and a large number of measured visual changes do not guarantee good motion design. The first retention-native V2-01 implementation at `b6f5002903fba65a668506e4ca38ae61b907ab18` passed static-run, rights, package, and audio metrics yet still failed Jim's actual review because the video repeated the same text-transition motifs, reused near-identical speed/easing behavior, used slow chart reveals, showed text collisions, and retained a template-generated feel.

That failure is classified:

`FAIL_CREATIVE_MOTION_ARCHITECTURE / REJECTED_CREATIVE_PRODUCT_REFERENCE_ONLY`

It must not be merged or polished as the creative baseline.

The controlling lesson is that creative decisions cannot be compressed into a small generic grammar such as `TextReveal`, `ChartReveal`, and a few transition presets. Structured contracts remain essential for truth, rights, identity, timing, cache, and auditability, but the final creative implementation must be free to vary per story and per shot.

R4 at `task/tier2-v2-gpt56-creative-code-asset-rich-video-v1` / `2289eb1382e65474207b50d27c0b87626d30728f` is also rejected, with the deeper classification:

`FAIL_SYSTEMIC_VISUAL_STORYTELLING_ARCHITECTURE / NEGATIVE_CREATIVE_REFERENCE_ONLY`

R4 proved that technical QA, motion diversity, asset-class counts, and model-authored Remotion code can all pass while a normal viewer still struggles to recognize the subject or reconstruct the story. Its abstract opening geometry, unexplained metaphors, landscape-chart-in-vertical treatment, and silent substitution of planned real/contextual assets with SVG abstractions must not be reused. Its governed evidence, rights/provenance, Remotion sandbox, audio, caching/selective-rerender, package-locking, and machine-QA engineering remain selectively reusable.

## Story first

A renderer cannot rescue a weak story. `VideoOpportunity` must consider:

- evidence strength and freshness;
- novelty/update-chain state;
- materiality;
- human or institutional stakes;
- meaningful conflict, decision, change, consequence, or mechanism;
- narrative depth;
- visualizability;
- availability of primary documents and deterministic data;
- availability of rights-safe people, place, institution, historical, or contextual imagery;
- shelf life and search longevity;
- current demand/trend context;
- recent topic/series concentration;
- platform fit;
- expected qualified engagement;
- estimated production effort and provider cost.

A story should be the length it earns. Long-form targets do not authorize padding. A narrow story may justify only a short. A genuinely deep story may justify 15–45 minutes.

## Engagement without truth degradation

The creative system may optimize:

- curiosity;
- sequencing;
- open loops;
- tension;
- consequence;
- payoff timing;
- re-hooks;
- visual rhythm;
- audio rhythm;
- packaging;
- CTA and binge path.

It may never create unsupported facts, causes, quotes, numbers, human stakes, predictions, recommendations, controversy, fear, greed, or FOMO.

Preferred truthful engagement mechanisms include:

- contradiction between headline and underlying record;
- consequence;
- mechanism;
- uncertainty;
- evidence reveal;
- what changed;
- what matters next;
- what the record proves;
- what the record does not prove.

## Motion doctrine

The primary creative unit is a narration-linked shot/beat, not a static scene/card.

A beat may use hard cuts, snap reveals, document punch-ins, focused chart deltas, annotations, map movement, timelines, image/B-roll cutaways, masks, reframes, comparisons, quote treatments, kinetic typography, diagrams, generated conceptual bridges, intentional holds, or silence. Motion must follow narrative meaning.

The system must avoid defaulting to the same transition family, easing profile, duration, direction, chart reveal, layout, or primitive repeatedly. More motion is not automatically better. Editorially motivated variation is the goal.

With captions hidden, the primary visual must still tell the story.

## Asset-rich editorial doctrine

V2 should acquire a large rights-safe candidate universe before final editing when the story supports it. This does not mean random asset spam. Each selected asset or visual state must have an editorial purpose.

Useful asset classes include:

- real rights-cleared people;
- institutions and buildings;
- relevant locations and geography;
- primary documents, releases, filings, tables, and source excerpts;
- deterministic charts;
- maps and routes;
- timelines;
- before/after and scenario comparisons;
- diagrams and mechanism graphics;
- quote/source treatments;
- historical/context imagery;
- rights-cleared B-roll or stills;
- generated conceptual illustration;
- icons, labels, and textures only where meaningful.

Initial planning hypotheses for sufficiently rich stories:

- candidate universe: roughly 25–60 viable assets/visual states;
- 45–75 second short: roughly 12–20 distinct purposeful visual states;
- 90–150 second proof: roughly 25–45 distinct purposeful visual states;
- longer video: density scales by narrative beats and evidence depth, not a fixed quota.

Recoloring or moving the same card does not create a new meaningful visual state.

Generated real-person documentary imagery is forbidden.

Each important beat must carry a concrete visual-grounding contract as applicable:

- viewer takeaway;
- primary visual type;
- recognizable object, location, or evidence required;
- must-use asset IDs;
- whether abstract substitution is allowed and why;
- recognition deadline;
- captions-hidden takeaway;
- native aspect-ratio variant.

If the accepted director contract requires a real/contextual asset, a Motion Code Author may not silently replace it with unrelated SVG abstraction. The rights-safe asset broker must build a story-specific candidate universe and evaluate semantic fit, rights/license, source quality, orientation, resolution, focal-object visibility, crop viability, documentary versus illustrative role, attribution, and duplicate concentration. Asset richness means recognizable editorial coverage, not a count of schematic classes.

## Storyboard and comprehension before final motion code

Do not generate the full final motion layer directly from a prose shot list. First create format-specific keyframes/storyboard and a cheap captions-hidden animatic or proxy. Inspect recognition, continuity, narrative reconstruction, and asset adequacy before expensive final code/render.

The comprehension gate must answer:

- what does the viewer recognize, and by what deadline?;
- what story or mechanism can be reconstructed with captions hidden?;
- does the first second establish the subject, location, or object?;
- are consecutive visuals semantically coherent?;
- does each important visual explain rather than merely move?;
- is the viewer forced to decode unexplained symbols?

Machine counts of visual changes cannot self-pass this gate. Weak comprehension must revise or stop the asset/storyboard plan before final motion authorship.

## Existing image, asset, voice, and audio authority remains

The creative-code change does not justify rebuilding working provider infrastructure.

Preserve:

- the dedicated direct image-generation boundary using `AI_API_CHEAP_API_KEY`;
- `gpt-5.5` as the current provisional generated-illustration default;
- generated imagery as illustrative enrichment only, never factual/documentary authority;
- rights/provenance/hash controls;
- real-person documentary imagery through real rights-cleared assets only;
- the current provider-neutral voice/TTS abstraction;
- Kokoro/local narration as an available baseline/fallback;
- existing music/SFX/mastering infrastructure until the dedicated audio task justifies a change.

Provider experimentation should occur only when it removes a direct quality blocker.

## Creative-code sandbox

GPT-5.6 creative authorship is bounded. Generated code should live under a per-video owned surface such as:

```text
video/generated/<video_id>/
  composition.tsx
  shots/
  shared/
  manifest.json
```

Allowed dependencies are explicit. They may include React, approved compatible Remotion packages, approved deterministic helpers, local resolved assets, SVG, Canvas, and bounded WebGL/Three.js only where justified.

Generated code must not:

- read environment variables or secrets;
- make network calls during render;
- mutate arbitrary filesystem paths;
- spawn shell commands or child processes;
- install dependencies dynamically;
- access browser/session/profile state;
- perform provider/platform/publication actions;
- alter factual/evidence authority.

Before execution, source must pass path/import/static/AST checks, TypeScript validation, and bounded render limits.

## Remotion technical authority

The primary technical reference is the official `remotion-dev/skills` repository, pinned in `CONTENTOPS_V2_REMOTION_AGENT_SKILL_BASELINE_V1.md` at authority creation to:

`b12104ef5f1b1ca2ca5590fcc7c1804fbc85556f`

Official skills guide current API usage, frame-driven animation, sequencing, transitions, text measurement, assets, captions, audio, maps, rendering, and other implementation details.

Community Remotion skills may supply craft ideas only. No third-party visual recipe becomes Capital Chronicle product authority. Universal rules such as “stagger everything,” “Ken Burns every still,” “idle elements always breathe,” or “cross-dissolve every scene” are explicitly rejected because they can produce the same repetitive AI-motion signature the product is trying to eliminate.

## Audio doctrine

Audio is a first-class creative layer. V2 should plan:

- voice/provider;
- pronunciation;
- prosody and emphasis;
- pause structure;
- phrase/word timing;
- music bed by beat/chapter;
- tension/resolution arc;
- restrained SFX;
- ducking;
- fades;
- loudness normalization;
- true-peak control;
- audio rights/provenance.

The initial mastering target remains approximately -16 LUFS ±1 with true peak at or below approximately -1.5 dBTP, subject to later platform/channel calibration. Narration-only may be diagnostically safe but is not automatically a professional engagement PASS.

## Platform-native doctrine

YouTube hero/mid/long-form, YouTube Shorts, and TikTok are independent editorial variants sharing story/evidence authority, not one composition resized three ways.

Short-form should normally reach value faster, use denser meaningful visual states, shorter caption groups, portrait-native framing, and early payoff.

Longer YouTube work should use sustained arcs, chapter re-hooks, richer evidence sequences, evolving asset/audio states, and deliberate pacing. Long duration is never a license for static filler.

Charts, maps, and documents require native visual compilers for each target format. A landscape chart screenshot may not simply be letterboxed into 9:16. Support portrait chart compositions, direct labels, focused comparisons, highlighted primary-source excerpts, recognizable geographic treatments, and format-specific crop/layout rules.

## Machine QA is screening, not aesthetics

Required diagnostics should increasingly cover:

- claim/evidence coverage;
- rights/provenance;
- asset hashes;
- dimensions/codecs/FPS/audio;
- text collision and bounding-box overlap;
- caption safe-zone/line violations;
- transition-family repetition;
- easing repetition;
- duration repetition;
- reveal-direction repetition;
- layout/primitive repetition;
- chart-reveal duration and perceived crawl risk;
- asset reuse concentration;
- hook and payoff timing;
- static primary-visual runs excluding captions;
- captions-hidden visual evolution;
- audio loudness/peak;
- package identity;
- selective rerender correctness.

No diagnostic score may override actual Jim/ChatGPT review during creative-proof stages.

Technical and motion metrics also cannot establish comprehension. Storyboard/animatic and proxy review must separately attest first-second recognition, captions-hidden reconstruction, semantic continuity, unexplained-symbol burden, and narration/visual agreement.

## Independent critique and revision

The primary creative model should not be its only judge. Use an independent strong multimodal critic for actual media review where available. The critic should report defects by `video_id`, `scene_id`, `shot_id`/`beat_id`, and time range.

GPT-5.6 then receives localized defects and patches the affected shot/code. Revisions should be selective. Maximum two bounded creative revision rounds per implementation attempt unless owner authority explicitly changes the rule.

Revision accounting is typed. Deterministic mechanical/schema/audio/path/safe-zone/serialization corrections do not consume creative revision budget when they preserve authored meaning. Storyboard/systemic creative revision and rendered localized creative revision do consume that budget and must be recorded separately.

If one implementation plus bounded correction still fails because the underlying creative architecture is wrong, do not enter an audit loop. Reconsider the architecture.

## Cost doctrine

ContentOps remains the production system; Codex is the repository builder. A frontier model must not rediscover the full newsroom for every video.

The product amortizes continuous intelligence, clustering, novelty, evidence, and published memory across all output formats, then uses compact governed story packets downstream.

The exact GPT-5.6 creative model is intentionally used at the highest-value presentation decisions. Rendering, deterministic transforms, caching, package verification, and routine QA remain local/deterministic where practical.

Do not hardcode temporary provider prices or subscription economics into the constitution. Measure actual tokens, calls, asset generations, render cost, retry overhead, and portfolio spend.

## Growth and learning doctrine

The channel should develop repeatable series and a coherent audience promise rather than disconnected one-offs. Candidate series may include Breaking Explained, What the Headline Misses, One Chart One Consequence, Power & Policy, Big Tech/Earnings Breakdown, Capital Chronicle Deep Dive, and The Evidence Boundary. These are hypotheses, not quotas.

After controlled publication, platform data should map back to production decisions:

```text
platform metric / retention timestamp
→ video_id
→ shot/beat/scene
→ asset state
→ motion state
→ caption state
→ audio state
→ hook/open-loop/payoff identity
→ bounded hypothesis
→ versioned policy change or NO_POLICY_CHANGE
```

Small samples must not trigger large policy changes. Trends guide selection, framing, packaging, and timing; they never become factual authority.

## Current task and milestone

The failed `b6f50029...` branch does not satisfy V2-01.

Current controlled replacement task:

`TASK_CONTENTOPS_V2_CONCRETE_FIRST_XHIGH_REPLACEMENT_VERTICAL_SLICE_V1`

Required result:

`PASS_RETENTION_NATIVE_VERTICAL_SLICE_VISUAL_AUDIO_ACCEPTED`

Proof scope is deliberately smaller than the rejected 3–6 minute attempt:

- one native 45–60 second 9:16 short;
- one 90–150 second 16:9 editorial proof;
- exact sanitized GPT-5.6 creative-author receipts;
- adaptive Creative Bible and semantic Segment Graph with deterministic child prompts;
- concrete visual-grounding contracts and a richer rights-safe story-specific asset universe;
- format-native chart/map/document treatments;
- keyframe storyboard and captions-hidden animatic before final motion code;
- explicit comprehension acceptance before expensive final rendering;
- sandboxed per-shot code;
- a rich rights-safe candidate asset universe;
- many purposeful selected visual states;
- current narration/music/SFX path;
- collision and repetition diagnostics;
- independent multimodal critique;
- at most two localized creative revisions;
- actual MP4/audio inspection by Jim/ChatGPT.

Do not advance to V2-02 until the actual media is accepted.

## Final V2 success condition

V2 is complete only when Capital Chronicle has demonstrated:

- repeated professional visual/audio quality across multiple story modes;
- disciplined story/video abstention;
- strong packaging and repeatable series identity;
- daily video portfolio selection without filler;
- safe controlled YouTube/Shorts/TikTok delivery under exact authority;
- strict upload/readback/reconciliation;
- real retention/performance observability;
- beat/shot-level attribution;
- bounded data-driven creative learning;
- reliable autonomous operation;
- low measured marginal operating cost;
- zero truth/rights/secret/public-write incidents;
- owner acceptance of the final V2 product.
