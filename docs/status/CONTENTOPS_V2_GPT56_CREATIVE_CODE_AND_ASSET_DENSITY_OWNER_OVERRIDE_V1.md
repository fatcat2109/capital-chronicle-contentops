# ContentOps V2 — GPT-5.6 Creative-Code + Asset-Density Owner Override V1

Authority date: 2026-08-12
Status: `CURRENT_V2_OWNER_OVERRIDE`
Owner direction: Jim

This overlay is current product-direction authority for the V2 creative-production path. It supersedes the V2-01 implementation assumptions that produced the rejected `b6f5002903fba65a668506e4ca38ae61b907ab18` result, while preserving the twelve-task V2 master-plan sequence, evidence/rights doctrine, accepted image/audio/asset infrastructure, and final required V2-01 result.

## 1. Rejected V2-01 result

Branch:

`task/tier2-v2-retention-native-video-factory-vertical-slice-v1`

HEAD:

`b6f5002903fba65a668506e4ca38ae61b907ab18`

Classification:

`FAIL_CREATIVE_MOTION_ARCHITECTURE / REJECTED_CREATIVE_PRODUCT_REFERENCE_ONLY`

Do not merge this branch into master and do not continue polishing its generic creative grammar.

The result proved useful engineering around governed story selection, rights/provenance, asset acquisition, audio mastering, music/SFX infrastructure, package locking, selective rerender, technical QA, and retention measurements. It did not prove acceptable professional motion/editorial quality.

Jim's direct media review identified the controlling defects:

- repeated text-transition motifs throughout the videos;
- nearly identical transition speeds/easing behavior across unrelated beats;
- transitions and chart reveals that feel too slow;
- slow left-to-right chart-path reveals used as a repeated grammar;
- overlapping/colliding visual text in multiple moments;
- excessive reuse of a small motion vocabulary even where machine visual-interval counts passed;
- an overall generated-template feel rather than shot-specific editorial direction.

The failure demonstrates that counting visual changes/static runs is insufficient. A composition may satisfy those metrics while remaining perceptually repetitive.

## 2. Exact primary creative-code model

The primary model for V2 creative authorship is the exact 9Router model:

`new/gpt-5.6-sol-xhigh`

It is mandatory as the primary model for these role-specific lanes:

- `V2_CREATIVE_EDITOR`
- `V2_MOTION_CODE_AUTHOR`
- `V2_CREATIVE_REVISION_AUTHOR`

These roles must not silently use the generic global model ordering as their quality authority.

### `V2_CREATIVE_EDITOR`

`new/gpt-5.6-sol-xhigh` owns the bounded presentation-layer work of turning a compact governed story/evidence packet into:

- hook and promise;
- audience framing;
- narrative screenplay;
- spoken narration script;
- tension/open loops/payoffs/re-hooks;
- shot sequence;
- platform-specific pacing;
- visual and sonic intent;
- asset-purpose requests;
- editorial transition logic.

It has zero factual or numeric authority. All factual claims remain bound to canonical evidence/Capital Chronicle authority.

### `V2_MOTION_CODE_AUTHOR`

`new/gpt-5.6-sol-xhigh` directly authors the per-video/per-shot motion implementation rather than selecting from a small fixed template grammar.

Expected output may include bounded React/TypeScript/SVG/Canvas/approved Remotion code for:

- timing;
- cuts and holds;
- camera/reframe behavior;
- typography choreography;
- masking/cropping;
- source-document treatment;
- chart traces and annotations;
- map/timeline movement;
- photo/B-roll treatment;
- comparison states;
- transition design;
- payoff visuals;
- audio cue placement.

Remotion is the deterministic renderer/compiler. It does not own creative direction.

### `V2_CREATIVE_REVISION_AUTHOR`

After deterministic QA and independent multimodal review, `new/gpt-5.6-sol-xhigh` receives only localized defect evidence and patches the affected shot/code where possible. Revisions should be selective rather than regenerating the full video.

### Degraded fallback

Infrastructure fallback may remain bounded for availability, but if any creative-author role resolves to a different model, the package must record:

`DEGRADED_CREATIVE_MODEL`

A degraded-model package may be rendered for diagnosis but cannot self-advance to `PASS_RETENTION_NATIVE_VERTICAL_SLICE_VISUAL_AUDIO_ACCEPTED`. Jim/ChatGPT actual media review remains required.

## 3. Creative-code sandbox

Strong-model authorship does not grant arbitrary repository/runtime execution authority.

Generated creative code must live in a bounded per-video surface such as:

```text
video/generated/<video_id>/
  composition.tsx
  shots/
  shared/
  manifest.json
```

Allowed dependencies are an explicit allowlist: React, compatible Remotion APIs/packages already approved for the task, approved deterministic visual helpers, SVG/Canvas/WebGL where bounded, and already resolved local assets.

Generated code must not:

- read environment variables/secrets;
- make network requests at render time;
- mutate arbitrary filesystem paths;
- spawn child processes or shell commands;
- install dependencies dynamically;
- access browser/session state;
- create provider/platform/publication authority;
- alter evidence/claim truth.

Before execution, validate generated source through deterministic path/import/AST/static checks, TypeScript checking, and bounded render limits.

## 4. Asset-rich editorial doctrine

Jim explicitly requires a much richer asset vocabulary. The fix is not random asset spam. V2 should acquire a large candidate pool and then select many editorially purposeful visual states.

### Candidate pool

When the story genuinely supports it, target roughly 25–60 viable candidate assets/visual states before final editing. This is a planning target, not a quota and never a reason to use weak or unlicensed media.

Candidate classes may include:

- rights-cleared real people;
- institution/building/location imagery;
- primary documents/releases/filings;
- highlighted source excerpts;
- deterministic charts;
- maps and geographic context;
- timelines;
- before/after comparisons;
- tables transformed into focused graphics;
- quote treatments;
- diagrams/mechanism graphics;
- headline/context montages when rights permit;
- historical/context imagery;
- rights-cleared B-roll/stills;
- accepted generated conceptual illustrations;
- icons/labels/annotations/textures only when they add meaning.

### Final-cut density hypotheses

Initial internal targets:

- 45–75 second native short: roughly 12–20 distinct purposeful visual asset/states when story supply supports it;
- 90–150 second creative proof: roughly 25–45 distinct purposeful visual asset/states when story supply supports it;
- longer videos scale by narrative beats and evidence depth, not a fixed asset quota.

An asset state is meaningful only if it changes what the viewer sees/understands. Re-coloring the same card does not count.

Avoid over-concentration:

- do not let one hero image dominate repeatedly without a narrative reason;
- avoid more than two consecutive beats using the same transition family, easing profile, reveal direction, or near-identical duration pattern unless deliberately motivated;
- do not default every still to Ken Burns/micro-motion;
- do not default every chart to a slow left-to-right reveal;
- prefer hard editorial cuts when they are stronger than decorative transitions.

## 5. Existing media/provider choices remain intact

This override does not replace the accepted image, asset, narration, or audio-provider paths.

Preserve:

- direct image generation boundary using `AI_API_CHEAP_API_KEY`;
- `gpt-5.5` as the provisional generated-illustration default;
- generated imagery as illustrative enrichment only, never factual/documentary authority;
- current rights/provenance/hash asset controls;
- real-person documentary imagery through real rights-cleared assets only;
- current voice-over provider abstraction and existing Kokoro/local baseline/fallback policy;
- existing music/SFX/mastering infrastructure unless a later dedicated audio task changes it.

The next task focuses on creative authorship, motion implementation, asset richness, and visual quality. It must not churn working image/TTS/provider infrastructure without a concrete blocker.

## 6. Remotion skill/reference authority

For Remotion technical craft, use the pinned official Remotion Agent Skills baseline recorded in:

`docs/automation/CONTENTOPS_V2_REMOTION_AGENT_SKILL_BASELINE_V1.md`

The official `remotion-dev/skills` repository is the primary technical reference. Community skills are reference-only craft inputs and never override current Remotion docs, repo safety, V2 truth/rights contracts, or Jim's quality direction.

The renderer must follow technical best practices such as frame-driven animation, text measurement/overflow checks, sequencing, transitions, asset handling, captions, audio, and rendering. But no third-party skill's prescriptive visual recipe becomes a mandatory Capital Chronicle style.

## 7. New machine-quality diagnostics

The next V2 proof must add diagnostics for defects missed by the prior static-run metric:

- text overlap/collision and safe-zone violations;
- transition-family repetition;
- easing-profile repetition;
- transition/reveal duration repetition;
- directional repetition;
- layout-state repetition;
- consecutive primitive/motif repetition;
- chart-reveal duration and perceived crawl risk;
- asset reuse concentration;
- primary-visual evolution with captions hidden;
- existing static-run, hook, payoff, audio, rights, and evidence diagnostics.

Metrics are screening tools, not aesthetic authority. Passing them never replaces actual media review.

## 8. Replacement V2-01 task

The failed V2-01 implementation is superseded by:

`TASK_CONTENTOPS_TIER2_V2_GPT56_CREATIVE_CODE_ASSET_RICH_VIDEO_VERTICAL_SLICE_V1`

It remains inside the existing V2-01 milestone slot and must achieve the existing advancement result:

`PASS_RETENTION_NATIVE_VERTICAL_SLICE_VISUAL_AUDIO_ACCEPTED`

Do not advance to V2-02 until this replacement proof receives Jim/ChatGPT actual visual/audio acceptance.

To test the architecture quickly before scaling, the proof should produce:

- one 45–60 second native 9:16 short;
- one 90–150 second 16:9 editorial sequence/proof;
- a large rights-safe candidate asset pool and rich selected visual sequence;
- exact evidence that `new/gpt-5.6-sol-xhigh` authored the creative screenplay and motion code through 9Router;
- per-shot generated creative code under sandbox validation;
- independent multimodal review;
- maximum two localized creative revision rounds;
- actual MP4/audio artifacts for Jim/ChatGPT review.

If the direct GPT-5.6 creative-code architecture still fails the professional product bar, do not keep polishing templates. Reconsider renderer/creative architecture with fresh evidence.

## 9. Safety and authority unchanged

- V2 remains isolated from live V1 runtime/store.
- Zero video public/private upload or public-write authority in this proof.
- Capital Chronicle truth/evidence authority remains unchanged.
- No fabricated claims/numbers/sources.
- No generated documentary real-person imagery.
- No secret/session exposure.
- No browser/CDP action.
- No protected `v1.0` mutation.
- No second newsroom/store/scheduler/provider/publication authority.
