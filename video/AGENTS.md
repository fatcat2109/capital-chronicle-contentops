# `video/` — Retention-Native V2 Creative-Code / Renderer Scope

Authority date: 2026-08-12

For V2/video work, read first:

1. `../docs/automation/CONTENTOPS_V2_RETENTION_NATIVE_VIDEO_FACTORY_NORTH_STAR_V2.md`
2. `../docs/automation/CONTENTOPS_V2_RETENTION_NATIVE_VIDEO_FACTORY_MASTER_PLAN_V2.md`
3. `../docs/automation/CONTENTOPS_V2_RETENTION_NATIVE_VIDEO_FACTORY_TASK_GRAPH_V2.md`
4. `../docs/automation/CONTENTOPS_V2_RETENTION_NATIVE_VIDEO_FACTORY_CURRENT_EXECUTION_POINTER_V2.md`
5. `../docs/automation/CONTENTOPS_V2_REMOTION_AGENT_SKILL_BASELINE_V1.md`
6. `../docs/automation/CONTENTOPS_V2_FRESH_CHAT_HANDOFF_V1.md`
7. `../docs/status/CONTENTOPS_V2_GPT56_CREATIVE_CODE_AND_ASSET_DENSITY_OWNER_OVERRIDE_V1.md` only for historical rationale/details already folded into V2 authority

Current next task:

`TASK_CONTENTOPS_TIER2_V2_GPT56_CREATIVE_CODE_ASSET_RICH_VIDEO_VERTICAL_SLICE_V1`

Required result:

`PASS_RETENTION_NATIVE_VERTICAL_SLICE_VISUAL_AUDIO_ACCEPTED`

## Exact creative-code model

Primary creative-code model through the canonical 9Router seam:

`new/gpt-5.6-sol-xhigh`

Mandatory primary roles:

- `V2_CREATIVE_EDITOR`
- `V2_MOTION_CODE_AUTHOR`
- `V2_CREATIVE_REVISION_AUTHOR`

If fallback is required for availability, record `DEGRADED_CREATIVE_MODEL`. Fallback output may be rendered diagnostically but cannot self-pass the professional creative gate.

## Creative/renderer contract

Remotion is deterministic execution/rendering infrastructure. It is not the creative director.

Canonical hierarchy:

```text
governed story/evidence packet
→ new/gpt-5.6-sol-xhigh Creative Editor
→ screenplay + narration + shot/edit plan
→ renderer-neutral semantic contracts
→ rights-aware AssetPlan + AudioPlan
→ new/gpt-5.6-sol-xhigh Motion Code Author
→ sandboxed per-video/per-shot React/TypeScript/SVG/Canvas code
→ deterministic source validation/typecheck
→ Remotion render
→ deterministic media/retention/repetition/layout QA
→ independent multimodal critic
→ new/gpt-5.6-sol-xhigh localized creative code revision
→ selective rerender
→ Jim/ChatGPT actual media acceptance
```

Semantic truth, rights, assets, narration identity, and package lineage remain separate from generated presentation code.

A scene is a production grouping, not a static slide. Per-shot generated code may use different layouts, timing, cuts, motion families, charts, masks, reframes, document treatments, maps, images, or effects when editorially justified.

The main visual must continue telling the story with captions hidden.

## Creative-code sandbox

Generated source must live under a bounded task/video-owned path and use an explicit import/dependency allowlist.

Allowed as scoped:

- React;
- approved compatible Remotion APIs/packages;
- approved deterministic helpers;
- local resolved assets;
- SVG/Canvas;
- bounded WebGL/Three.js only when task scope/render budget justifies it.

Forbidden:

- env/secret reads;
- render-time network calls;
- arbitrary filesystem mutation;
- `child_process`/shell execution;
- dynamic dependency installation;
- browser/session/profile access;
- platform/publication actions;
- factual/evidence mutation.

Run path/import/static/AST checks and TypeScript validation before executing generated code.

## Official Remotion reference baseline

Primary technical reference:

`remotion-dev/skills@b12104ef5f1b1ca2ca5590fcc7c1804fbc85556f`

Read the official current router/markup guidance plus relevant timing, transitions, video-editing, sequencing, multi-scene, text/DOM measurement, images, audio, SFX, captions, maps, render, and metadata references as needed.

Community skills in `CONTENTOPS_V2_REMOTION_AGENT_SKILL_BASELINE_V1.md` are craft references only. Do not import absolute visual recipes wholesale.

V2 explicitly rejects universal:

- stagger everything;
- Ken Burns every still;
- idle elements always breathe;
- cross-dissolve every scene;
- same transition/easing/duration across most shots.

## Asset-rich editorial contract

Keep existing image, asset-rights, voice-over, music/SFX, and mastering providers unchanged unless a direct blocker demands otherwise.

For sufficiently rich stories, initial planning hypotheses are:

- roughly 25–60 viable candidate assets/states;
- roughly 12–20 purposeful visual states for a 45–75s short;
- roughly 25–45 purposeful visual states for a 90–150s proof.

These are not quotas.

Use where relevant:

- real rights-cleared people;
- institutions/buildings/locations;
- primary documents/releases/filings;
- highlighted source excerpts;
- deterministic charts;
- maps/routes;
- timelines;
- comparisons;
- diagrams;
- contextual/history imagery;
- rights-cleared B-roll/stills;
- generated conceptual illustrations through the accepted direct `gpt-5.5` boundary.

Generated real-person documentary imagery remains forbidden.

## Motion-quality anti-patterns

Fail or flag:

- repeated same-speed text transitions;
- repeated same easing/trajectory/direction across consecutive beats;
- slow whole-chart left-to-right crawl as a default;
- visual text collisions/overflow;
- captions as the main apparent motion;
- repeated one-component/one-layout grammar;
- decorative motion whose only purpose is satisfying a motion-count metric;
- universal zoom/parallax/Ken Burns;
- universal cross-dissolves;
- generic AI slideshow/card feel.

Prefer authored editorial rhythm: hard cuts, rapid reveals, intentional holds, document punches, focused chart deltas/annotations, asset cutaways, reframes, maps/timelines, kinetic type, diagrams, and audio hits only when narratively justified.

## Machine QA additions

Alongside truth/rights/audio/static-run/package checks, compute/inspect:

- text bounding-box collisions;
- safe-zone overflow;
- transition-family repetition;
- easing repetition;
- duration repetition;
- reveal-direction repetition;
- layout-state/primitive repetition;
- chart-reveal duration/crawl risk;
- asset-use concentration;
- captions-hidden visual evolution.

Metrics screen defects; they do not establish aesthetics.

## Rejected references

Do not merge or continue:

- `task/tier2-b-remotion-multimodal-bakeoff-v1`;
- `task/tier2-v2-creative-system-rebuild-v1` / `d231b54e...`;
- `task/tier2-v2-retention-native-video-factory-vertical-slice-v1` / `b6f50029...`.

`b6f50029...` is `FAIL_CREATIVE_MOTION_ARCHITECTURE`. Inspect only useful evidence/rights/asset/audio/cache/QA engineering, not its creative grammar.

## Truth / rights / platform boundaries

- consume governed story/evidence authority; never fabricate facts/numbers;
- deterministic/source-backed visuals remain factual authority;
- generated media is illustrative enrichment only;
- real people use real rights-cleared documentary assets;
- add no independent newsroom/store/scheduler/publication authority;
- keep credentials outside generated renderer source;
- no browser/CDP/platform action unless exact task scope authorizes it;
- V2 currently has zero video public-write authority;
- generated/vendor outputs, renders, caches, runtime media stay outside Git except bounded source/evidence explicitly required by task.

## QA and acceptance

Tests should cover creative-role model identity, sandbox/import restrictions, graph/source binding, responsive/platform-native layout, timing, collision/overflow, repetition diagnostics, cache invalidation, actual transitions, audio/caption safety, render metadata, and package identity.

A model/renderer/critic cannot self-claim professional visual/audio PASS. Jim/ChatGPT must inspect actual MP4/audio artifacts during creative-proof stages.
