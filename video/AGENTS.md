# `video/` — Retention-Native V2 Renderer Scope

Authority date: 2026-08-12

For V2/video work, read first:

1. `../docs/status/CONTENTOPS_V2_RETENTION_NATIVE_VIDEO_FACTORY_DIRECTION_OVERLAY_V1.md`
2. `../docs/automation/CONTENTOPS_V2_RETENTION_NATIVE_VIDEO_FACTORY_NORTH_STAR_V1.md`
3. `../docs/automation/CONTENTOPS_V2_RETENTION_NATIVE_VIDEO_FACTORY_MASTER_PLAN_V1.md`
4. `../docs/automation/CONTENTOPS_V2_RETENTION_NATIVE_VIDEO_FACTORY_CURRENT_EXECUTION_POINTER_V1.md`

The current next task is `TASK_CONTENTOPS_TIER2_V2_RETENTION_NATIVE_VIDEO_FACTORY_VERTICAL_SLICE_V1`.

## Creative/renderer contract

The renderer consumes structured product authority; React/Remotion/FFmpeg commands are never factual/editorial authority.

Canonical creative hierarchy:

```text
EngagementBrief
→ renderer-neutral VideoProgram
→ NarrativeBeatGraph
→ EditDecisionGraph / MotionBeatGraph
→ AssetPlan + AudioPlan
→ PlatformVariantPlan
→ renderer
```

A scene is a production grouping, not a static slide. It may contain several narration-linked beats with different visual states, assets, annotations, cuts, reframes, audio states, and payoffs.

The main visual must continue telling the story with captions hidden. Entrance animation followed by long holds is a product failure even if typography is attractive.

## Required capabilities

Fresh accepted renderer work should support:

- native 16:9 YouTube hero/mid/long-form;
- independently directed native 9:16 Shorts/TikTok;
- beat-level timing and edit decisions;
- staged chart/data reveals and annotations;
- source-document focus/punch-ins;
- real-photo/entity/location cutaways when rights-safe/material;
- maps/timelines/comparisons/diagrams;
- generated conceptual illustration only as enrichment;
- real transitions with actual media implementation;
- narration, music, SFX, ducking, and mastered audio;
- phrase/word-level caption timing and safe-zone handling;
- semantic content identity separated from runtime/package identity;
- asset/narration/audio/render dependencies in cache identity;
- scene/beat/chapter caching, proxy renders, and real selective rerender;
- deterministic technical and retention diagnostics;
- immutable package hashes.

## Initial retention hypotheses

These are starting QA targets, not universal truths:

- short meaningful visual beat roughly every 1.5–4 seconds;
- short unjustified primary-visual static run roughly <=4 seconds;
- mid/long meaningful visual evolution roughly every 4–8 seconds;
- mid/long unjustified static run roughly <=8 seconds;
- captions normally <=2 lines;
- narration-only/caption-only motion does not satisfy visual engagement;
- finished audio initially targets roughly -16 LUFS ±1 and true peak <= -1.5 dBTP.

## Rejected references

Do not merge or continue these creative implementations:

- `task/tier2-b-remotion-multimodal-bakeoff-v1`;
- `task/tier2-v2-creative-system-rebuild-v1` at `d231b54e026570442d9fd9269b61e55c3de31d21`.

The latter is `REJECTED_CREATIVE_PRODUCT_REFERENCE_ONLY`. Inspect only bounded engineering ideas that remain compatible with current authority. Do not reuse its Treasury hardcoded program, fixed slide grammar, or style-only revision surface as the creative baseline.

## Truth / rights / platform boundaries

- consume governed story/evidence authority; never fabricate facts/numbers;
- deterministic/source-backed visuals remain factual authority;
- generated media is clearly illustrative and never documentary evidence;
- real people use real rights-cleared photos, never generated documentary substitutes;
- add no independent newsroom/store/scheduler/publication authority;
- keep provider credentials outside renderer/source;
- no browser/CDP/platform/public action unless exact task scope authorizes it;
- V2 currently has zero video public-write authority;
- generated/vendor output (`node_modules`, renders, caches, runtime media) stays outside Git.

## QA and acceptance

Tests should cover graph consumption, responsive/platform-native layout, beat timing, cache invalidation, actual transitions, audio/caption safety, static-run/retention diagnostics, render metadata, and package identity.

A model/renderer cannot self-claim professional visual/audio PASS. Jim/ChatGPT must inspect actual MP4/audio artifacts during the creative-proof stages.
