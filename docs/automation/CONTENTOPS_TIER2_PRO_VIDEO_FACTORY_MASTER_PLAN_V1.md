# Capital Chronicle ContentOps — Tier-2 Pro Video Factory Master Plan V1

Authority date: 2026-08-07

Product authority:

`CONTENTOPS_TIER2_PRO_VIDEO_FACTORY_OWNER_DIRECTION_V1`

Plan status:

`APPROVED_FUTURE_EXECUTION_PLAN_POST_TIER1`

Current execution status:

`NOT_CURRENT_NOT_STARTED`

## 0. Executive routing

This plan defines the future implementation path for **CONTENTOPS TIER-2 PRO VIDEO FACTORY**.

It does not supersede the current Tier-1 route.

Current product execution remains:

```text
owner-approved 9router V2 runtime lineage acceptance/merge
→ TASK_CONTENTOPS_EXACT_AUTHORIZED_LIVE_COHORT_V1
→ major final Tier-1 UI/UX rebuild using real live states
→ Work Package G final full-automation prelaunch run
→ Tier-1 final acceptance + new release identity
→ freeze Tier-1 baseline
→ begin Tier-2 implementation
```

Tier-2 implementation must not begin before Tier-1 final acceptance unless Jim explicitly reprioritizes again.

## 1. User problem

Tier-1 can turn governed stories into articles, visuals, newsletters, and native text/image packages. That is not sufficient for a premium modern media product.

Jim needs ContentOps to convert high-value governed stories into professional video without requiring a manual editing workflow, without losing evidence lineage, and without depending on opaque text-to-video providers.

The target operator experience is a high-level command such as:

> Turn this story into Tier-2 Pro Video.

The system should perform almost all production work and return near-final video packages with approximately 2–5 meaningful operator interactions during early supervised operation.

The product must support both:

- platform-native short-form video; and
- professional long-form editorial video with a target runtime of 15–45 minutes.

## 2. Capability delivered

The completed Tier-2 product will add a programmable video production layer to canonical ContentOps that can:

- decide whether a governed story deserves video;
- build a claim-bound narrative;
- create chapter and scene graphs;
- generate deterministic-first visuals;
- generate or ingest narration/audio;
- render long-form and short-form video;
- automatically inspect visual/timing quality;
- apply bounded scene/chapter corrections;
- selectively rerender changed media;
- package exact evidence/rights/provenance;
- prepare platform-native upload packages;
- later upload only under exact authority;
- strictly read back and reconcile;
- measure retention, engagement, cost, and operator burden.

## 3. Product modes

### 3.1 `SHORT_FORM_NATIVE`

Primary surfaces:

- YouTube Shorts;
- TikTok;
- Instagram Reels;
- future verified compatible short-video surfaces.

Short-form is independently directed and compiled. It is not an automatic crop of long-form.

### 3.2 `LONG_FORM_EDITORIAL_15_45M`

Primary initial destination:

- YouTube long-form.

Additional long-form destinations may be enabled only after current official capability verification.

Long-form is chapter-based and must support evidence-heavy financial, economic, corporate, policy, regulatory, geopolitical, and Capital Chronicle analysis explainers.

### 3.3 Optional derivatives

The architecture may later support mid-form or other media cuts, but these are not launch requirements and must not distract from short-form + 15–45 minute long-form closure.

## 4. Architecture contract

```text
CANONICAL CONTENTOPS STORY / ANALYSIS PACKET
            |
            v
VIDEO ELIGIBILITY / ASSIGNMENT
            |
            v
VIDEO DIRECTOR
            |
            v
VIDEO PROGRAM
├── Chapter Graph
└── Scene Graphs
            |
            v
ASSET ENGINE
├── deterministic charts
├── maps
├── timelines
├── source documents
├── typography / numbers / diagrams
├── rights-cleared stills
└── optional generated media
            |
            v
AUDIO ENGINE
├── narration
├── captions
└── optional licensed soundtrack
            |
            v
PROGRAMMABLE COMPOSITOR
├── 16:9 long-form
└── 9:16 short-form
            |
            v
PROXY + QA
├── deterministic media QA
└── multimodal visual critic
            |
            v
BOUNDED REVISION
            |
            v
FINAL PACKAGE
            |
            v
EXACT-AUTHORIZED UPLOAD / READBACK / RECONCILIATION
            |
            v
VIDEO PERFORMANCE LEARNING
```

## 5. Reuse map

Tier-2 must reuse accepted ContentOps foundations rather than rebuild them.

### Reuse directly where compatible

- canonical story/work-item identity;
- evidence/claim packet authority;
- Capital Chronicle analysis lineage;
- source, permission, freshness, and material-delta gates;
- durable operational store and append-only transitions;
- operating modes;
- exact authorization doctrine;
- unknown-write fail-closed behavior;
- platform identity registry;
- incidents and reconciliation concepts;
- content-performance identity;
- deterministic chart methods;
- media hashes and manifest authority;
- platform readback patterns;
- current 9router model-gateway authority when applicable at future implementation time.

### Existing video/media code to inspect before implementing

- `live_contentops/video_platform_capability_matrix_v1.py`
- `live_contentops/source_chart_short_video_v1.py`
- `live_contentops/macro_chart_renderer_v6.py`
- `live_contentops/media_manifest_authority_v1.py`
- YouTube Shorts / TikTok helper surfaces inside `live_contentops/edge_cdp_publishing_adapter_v1.py`
- historical video evidence under `docs/automation/VIDEO_FOUNDATION_AND_PAUSE_V1/`

### Do not reuse blindly

- stale provider constraints;
- historical pause/lock policy as permanent doctrine;
- avatar-first assumptions;
- any architecture that creates a parallel newsroom;
- any second durable state system;
- any separate approval/outbox/retry engine;
- old browser helper behavior without current provider/readback verification.

## 6. Core data model

The future implementation should define a versioned video program contract that is independent of the renderer.

### 6.1 `VideoProgram`

Recommended responsibilities:

- canonical video identity;
- story/version lineage;
- input package hashes;
- video mode;
- duration target;
- aspect strategy;
- motion-system version;
- claim-binding coverage;
- chapter set;
- scene set;
- asset set;
- narration set;
- rights/provenance summary;
- QA state;
- revision state;
- cost state;
- final render/package hashes.

### 6.2 `ChapterGraph`

Required for long-form 15–45 minute video.

Each chapter should carry:

- chapter ID/title;
- narrative objective;
- evidence/claim set;
- duration budget;
- narration segments;
- visual plan;
- scene list;
- chapter transition;
- chapter QA;
- cost and render hashes.

### 6.3 `SceneGraph`

Each scene should carry:

- semantic purpose;
- narration and claim bindings;
- source/evidence bindings;
- visual primitive;
- asset references;
- rights requirements;
- semantic layout intent;
- aspect-specific layout rules;
- duration;
- captions;
- credits;
- motion intent;
- audio cues;
- fallback strategy;
- revision history;
- render hash.

Do not encode the canonical contract as Remotion React component props or FFmpeg command lines. Those are compiler targets.

## 7. Renderer decision

### Preferred stack

- Remotion-style React/programmatic composition for reusable motion and parameterized scenes;
- FFmpeg for finishing, mux, transcode, audio/subtitle composition, concatenation, scaling, and delivery variants;
- ffprobe for deterministic media metadata verification.

### Architectural rule

The renderer is replaceable. The Video Program is authority.

### Licensing gate

Before implementation, verify the then-current Remotion license/business terms and projected production economics. Current 2026-08-07 official pricing distinguishes automation use and includes usage/minimum-spend terms. Do not assume today's terms remain unchanged.

If Remotion becomes commercially unsuitable, preserve the same Video Program and choose another compatible programmable compositor rather than redesigning the newsroom.

## 8. Long-form rendering strategy

15–45 minute production changes the engineering requirements.

The renderer must support:

- scene-level caching;
- chapter-level caching;
- deterministic intermediate hashes;
- proxy resolution renders;
- final-quality renders only after QA;
- selective rerender;
- chapter assembly;
- final master assembly;
- resume after process interruption.

Target behavior:

```text
edit Scene 4.3
→ invalidate Scene 4.3
→ rerender Scene 4.3
→ rebuild Chapter 4
→ reassemble master
```

Do not regenerate every unrelated scene because one line or chart changed.

## 9. Visual system

Build reusable motion primitives for:

- titles;
- chapter cards;
- lower thirds;
- source labels;
- data labels;
- number animations;
- charts;
- maps;
- timelines;
- document excerpts;
- source quotation cards;
- entity cards;
- comparisons;
- process diagrams;
- callouts;
- disclaimers;
- end cards;
- transitions;
- captions.

The motion system should be consistent across videos but not monotonous. Variation should occur through story-appropriate layout, data, imagery, maps, charts, and pacing rather than random templates.

## 10. Asset policy

### Deterministic first

Prefer code/data-generated assets when they improve precision, consistency, and revision speed.

### Rights-cleared second

Use sourced stills, documents, icons, or other media only when rights/provenance permit the intended output.

### Generative enrichment third

Generated image/video may be used where it materially improves quality and remains safe and cost-effective.

Generated media must record:

- provider/model;
- prompt/version hash where allowed;
- generation ID where returned;
- output hash;
- rights/terms classification;
- source role;
- whether it represents a real event or only an illustrative concept.

Never present synthetic imagery as real documentary evidence.

## 11. Audio architecture

The future system needs a provider-neutral narration abstraction.

Required capabilities:

- stable voice identity;
- pronunciation dictionary;
- line/scene-level generation;
- segment hashes;
- alignment timing;
- fallback provider strategy;
- cost tracking;
- optional human VO import later.

Caption timing should derive from authoritative narration/script alignment rather than ad hoc manual timestamps.

Soundtrack must use owned/licensed/reusable audio or none.

## 12. QA architecture

### Deterministic QA

Use ffprobe and internal manifests to verify:

- duration;
- width/height;
- aspect;
- frame rate;
- stream presence;
- codec/container policy;
- audio stream;
- subtitle/caption outputs;
- chapter/scene completeness;
- source/claim binding;
- rights/provenance completeness;
- output hashes.

### Multimodal QA

The critic should inspect proxy/final video or a structured sample of frames/time ranges for:

- readability;
- composition;
- pacing;
- dead air;
- visual repetition;
- chart/map legibility;
- crop errors;
- narration/visual mismatch;
- safe-zone violations;
- brand inconsistency;
- synthetic-media risk;
- long-form chapter rhythm;
- short-form hook/retention weakness.

Output structured defects by scene/chapter, severity, confidence, and proposed graph/asset change.

## 13. Bounded revision policy

Automatic creative revision must be finite and cost-aware.

The system should use:

```text
proxy
→ critique
→ targeted patch
→ selective rerender
→ critique
→ optional final bounded patch
→ accept / block / operator escalation
```

Do not create an infinite model-review loop.

Exact retry/revision budgets are an implementation calibration task based on real cost and defect reduction.

## 14. Short-form compilation

Short-form must be derived from the same factual/evidence authority but may create a different editorial sequence.

A long-form program may yield several shorts:

- core story hook;
- data/chart angle;
- consequence/mechanism angle;
- what-to-watch angle.

Each short should have its own program identity and hashes while preserving parent story/video lineage.

The short compiler may:

- omit scenes;
- reorder evidence;
- replace charts with vertical-safe versions;
- enlarge typography;
- simplify simultaneous elements;
- change CTA;
- change hook;
- use different narration.

It must not alter factual meaning.

## 15. Platform research gates

Provider/platform behavior changes. Reverify official docs before implementation and before live activation.

### Current 2026-08-07 snapshot

YouTube:

- resumable upload supports interrupted large-file recovery;
- API project verification affects public upload behavior;
- eligible square/vertical uploads up to three minutes are currently Shorts for standard channels.

TikTok:

- creator info exposes `max_video_post_duration_sec`;
- content upload/direct-post paths expose upload/publish IDs and status;
- current developer media-transfer documentation allows developer-sent video up to ten minutes;
- therefore do not plan 15–45 minute TikTok long-form as a baseline capability.

C2PA:

- current 2.4 specification supports composed assets, ingredients, actions, derived assets/renditions, and content bindings useful for future video provenance.

Instagram/Reels and any additional target must receive fresh official verification during the relevant integration task.

## 16. Package output

A complete future production should package:

```text
video_program.json
chapter_manifest.json
scene_manifest.json
script.json / transcript
captions
thumbnail assets
master_16x9.mp4
short_*.mp4 when selected
asset_media_manifest.json
evidence_claim_binding.json
rights_provenance_report.json
deterministic_media_qa.json
multimodal_visual_qa.json
revision_history.json
render_cost_report.json
platform_metadata/
hash_manifest.json
```

Optional later:

- C2PA Content Credentials artifact/embedding.

## 17. Tier-2 operational state

Do not create a new database.

Extend the canonical durable state with video-specific work items/events only as required.

Future state should represent at least:

- video assignment;
- program creation;
- asset readiness;
- narration readiness;
- proxy render;
- QA blocked/ready;
- revision;
- final render;
- package ready;
- upload intent;
- upload processing;
- platform object;
- readback;
- reconciliation;
- observation;
- closed.

Unknown upload state must fail closed and reconcile before any retry.

## 18. UI/UX future requirement

Tier-2 should extend the accepted ContentOps control room rather than add a disconnected video dashboard.

The eventual operator UI should expose:

- video eligibility;
- selected mode;
- chapter outline;
- scene timeline at semantic level;
- claim/evidence coverage;
- asset rights status;
- narration status;
- proxy/final preview;
- visual QA defects;
- revision history;
- render cost/time;
- final long/short packages;
- publication/readback state;
- video performance observations.

The operator should be able to approve meaningful creative direction without manually operating a traditional NLE for routine videos.

## 19. Work package strategy

Use a small number of heavy vertical slices. Do not build dozens of schemas or provider wrappers before a video can actually render.

### TIER2-A — Local long-form + short-form programmable vertical slice

**User problem**: prove ContentOps can create a coherent professional video from governed evidence without platform writes.

**Capability delivered**:

One canonical governed story goes through:

```text
video eligibility
→ Video Director
→ Video Program
→ chapter/scene graph
→ deterministic assets
→ narration
→ captions
→ programmable render
→ 15–45 minute-capable 16:9 architecture
→ at least one native 9:16 short
→ deterministic QA
→ immutable package
```

The first demo does not need a full 45-minute production if doing so would only waste render time; however the architecture and acceptance corpus must prove the long-form system is structurally capable of the required 15–45 minute range, and the work package should include at least one realistic long-form render long enough to exercise chapter caching, selective rerender, audio continuity, and chapter QA.

**Simplest viable approach**:

- reuse canonical story/evidence packets;
- introduce one Video Program/Chapter/Scene contract;
- implement a compact reusable motion system;
- use deterministic charts/maps/typography first;
- use one TTS boundary;
- use programmable compositor + FFmpeg/ffprobe;
- zero generative-video dependency required.

**Demo path**:

one local command or canonical UI action produces the package and renders with zero provider/public write except explicitly authorized local/model/TTS actions defined in the future task.

**Utility delta**:

first credible evidence-bound professional video created by canonical ContentOps rather than manual editing.

**Validation**:

- claim binding;
- media hashes;
- ffprobe metadata;
- captions;
- rights manifest;
- no untracked asset;
- deterministic repeated render where inputs are deterministic;
- selective rerender proof;
- short-form layout proof.

### TIER2-B — Multimodal QA, bounded auto-revision, and diverse corpus

**User problem**: one polished demo does not prove a reusable factory.

**Capability delivered**:

- multimodal visual critic;
- structured defect packets;
- scene/chapter graph patching;
- bounded revision;
- selective rerender;
- multiple business/news domains;
- cost and runtime measurement;
- optional generated B-roll policy exercised only where useful.

**Evaluation corpus** should include materially different visual/narrative problems, for example:

- earnings/company story;
- macro data / chart-led story;
- policy/regulatory story;
- geopolitics/map story;
- Capital Chronicle analysis transformation;
- weak/non-video-worthy candidate that produces `VIDEO_NOT_SELECTED`.

**Validation**:

- defect reduction after bounded revision;
- no factual drift;
- no unbounded revision loops;
- no rights bypass;
- 16:9 and 9:16 native layout quality;
- long-form chapter continuity;
- measured cost per accepted render.

### TIER2-C — Platform-native packaging + private/unlisted/draft readback

**User problem**: local MP4 output does not prove reliable provider integration.

**Capability delivered**:

- exact platform metadata compiler;
- resumable/recoverable upload semantics where available;
- private/unlisted/draft-first flow where provider semantics permit;
- provider processing-state readback;
- object identity capture;
- strict readback/reconciliation;
- no duplicate unknown uploads.

**Initial provider priority**:

1. YouTube long-form;
2. YouTube Shorts;
3. TikTok short-form;
4. Instagram Reels after fresh official verification.

Do not force 15–45 minute video onto platforms whose verified account/API capability does not support it.

**Hard boundary**:

requires exact credential/provider/network scope and current official-doc verification.

### TIER2-D — Bounded live video cohort

**User problem**: private/draft proof still does not prove real audience-facing operation.

**Capability delivered**:

- exact authorized public video cohort;
- live long-form and short-form output;
- strict public readback;
- kill switch;
- incident/recovery evidence;
- performance observations;
- real cost and operator-time measurement.

Use a small high-confidence cohort. `VIDEO_NOT_SELECTED` remains valid.

### TIER2-E — Final Tier-2 acceptance and release

**User problem**: isolated live successes are not a stable product release.

**Capability delivered**:

- repeated video production;
- long-form + short-form reliability;
- accepted motion system;
- accepted visual QA/revision loop;
- platform readback/reconciliation;
- economics;
- performance learning;
- final UI integration;
- new Tier-2 release identity.

Do not mutate the frozen Tier-1 release identity.

## 20. Future launch gates

### Product utility

- Jim can create a professional video from a governed story with low operator burden.
- The long-form result is genuinely useful and watchable, not a stretched slide deck.
- Short-form outputs are native rather than crops.
- `VIDEO_NOT_SELECTED` decisions are understandable.

### Editorial fidelity

- every factual narration segment is claim/evidence bound;
- Capital Chronicle analysis is transformed faithfully;
- no synthetic source or fake documentary evidence;
- citations/credits are preserved where required.

### Long-form quality

- 15–45 minute architecture works with chapters;
- pacing and chapter transitions remain coherent;
- selective rerender works;
- audio continuity is stable;
- charts/maps/documents remain legible;
- no unacceptable dead/repetitive stretches.

### Short-form quality

- true 9:16 composition;
- strong hook;
- readable captions;
- appropriate information density;
- platform-aware duration and metadata;
- no factual distortion through compression.

### Reliability

- deterministic media QA;
- bounded multimodal revision;
- restart-safe render state;
- exact asset hashes;
- strict provider processing/public readback;
- no blind retry of unknown uploads.

### Economics

- cost per accepted video measured;
- generative-video cost visible;
- render time measured;
- operator interactions measured;
- selective rerender reduces avoidable cost;
- product remains plausible as a premium automated media capability.

## 21. Performance learning

Tier-2 should observe:

- engaged/qualified views;
- completion;
- retention curves;
- average watch time;
- rewatches;
- shares;
- saves;
- comments;
- subscriber/follower conversion;
- canonical article clicks where measurable;
- thumbnail/title experiments only under bounded policy;
- cost/video;
- operator interactions/video;
- revision count;
- defect escapes.

Small samples produce observations, not sweeping autonomous editorial changes.

## 22. Provider/model policy

Tier-2 must remain provider-neutral.

Future model/TTS/generative-media selection should follow then-current owner authority and bounded retry/cost policies.

No provider may become the source of factual truth.

No fallback may bypass evidence, rights, permission, or publication gates.

## 23. Security and safety

Tier-2 tasks must preserve:

- no raw secrets in logs/docs;
- explicit credential binding only;
- no browser/session extraction;
- no unauthorized upload/public write;
- no synthetic impersonation or fake documentary events;
- no blind unknown-write retry;
- no Capital Chronicle main-project mutation;
- no `v1.0` or Tier-1 release mutation;
- no analytical/numeric authority expansion.

## 24. Historical video supersession

The historical `docs/automation/VIDEO_FOUNDATION_AND_PAUSE_V1/` packet remains useful discovery evidence.

This plan supersedes it as future implementation authority wherever there is conflict.

Retain useful findings:

- explicit video mode separation;
- FFmpeg foundation;
- capability/readback research;
- evidence-bound scene concepts;
- local/non-posting proof discipline.

Supersede or reject:

- indefinite video pause;
- avatar-first core architecture;
- any assumption that a 2–5 minute clip is the normal video target;
- any architecture that does not support 15–45 minute chapter-based long-form;
- any blind long-to-short crop strategy;
- any second newsroom/state/publication authority.

## 25. Primary-source research used for this plan

Verified 2026-08-07:

- Remotion programmatic rendering / licensing: https://www.remotion.dev/
- FFmpeg: https://ffmpeg.org/
- ffprobe: https://ffmpeg.org/ffprobe.html
- YouTube resumable upload: https://developers.google.com/youtube/v3/guides/using_resumable_upload_protocol
- YouTube videos.insert: https://developers.google.com/youtube/v3/docs/videos/insert
- YouTube Shorts classification: https://support.google.com/youtube/answer/15424877
- TikTok creator capability: https://developers.tiktok.com/doc/content-posting-api-reference-query-creator-info
- TikTok media transfer: https://developers.tiktok.com/doc/content-posting-api-media-transfer-guide
- TikTok post status: https://developers.tiktok.com/doc/content-posting-api-reference-get-video-status
- C2PA 2.4: https://spec.c2pa.org/specifications/specifications/2.4/specs/C2PA_Specification.html

Platform and commercial terms are temporally unstable. Reverify them in the implementation task that depends on them.

## 26. What not to build before Tier-1 completion

Do not implement now:

- Tier-2 runtime;
- Remotion dependencies;
- TTS providers;
- video-generation providers;
- long-form renderer;
- short-form compiler;
- upload adapters;
- video-specific scheduler;
- Tier-2 UI;
- new state database;
- new provider gateway.

This plan exists so Tier-1 can now continue without losing the approved Tier-2 product direction.

## 27. Exact next action

After this documentation authority is committed, do **not** start TIER2-A.

Current product execution remains Tier-1.

Required sequence:

```text
1. independently accept/merge the owner-approved 9router V2 runtime lineage
2. TASK_CONTENTOPS_EXACT_AUTHORIZED_LIVE_COHORT_V1
3. major final Tier-1 UI/UX rebuild from real live states
4. Work Package G final full-automation prelaunch run
5. Tier-1 final acceptance + new release identity
6. freeze Tier-1 baseline
7. TIER2-A local long-form + short-form vertical slice
8. TIER2-B multimodal QA + diverse corpus
9. TIER2-C platform-native private/unlisted/draft readback
10. TIER2-D bounded live video cohort
11. TIER2-E final Tier-2 acceptance + release
```

Tier-2 is an approved destination. Tier-1 remains the current road.
