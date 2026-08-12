# `video/` — Retention-Native V2 Creative-Code / Renderer Scope

Authority date: 2026-08-12

For V2/video work, read first:

1. `../docs/status/CONTENTOPS_V2_GPT56_CREATIVE_CODE_AND_ASSET_DENSITY_OWNER_OVERRIDE_V1.md`
2. `../docs/status/CONTENTOPS_V2_RETENTION_NATIVE_VIDEO_FACTORY_DIRECTION_OVERLAY_V1.md`
3. `../docs/automation/CONTENTOPS_V2_RETENTION_NATIVE_VIDEO_FACTORY_NORTH_STAR_V1.md`
4. `../docs/automation/CONTENTOPS_V2_RETENTION_NATIVE_VIDEO_FACTORY_MASTER_PLAN_V1.md`
5. `../docs/automation/CONTENTOPS_V2_RETENTION_NATIVE_VIDEO_FACTORY_CURRENT_EXECUTION_POINTER_V1.md`
6. `../docs/automation/CONTENTOPS_V2_REMOTION_AGENT_SKILL_BASELINE_V1.md`

The current next task is:

`TASK_CONTENTOPS_TIER2_V2_GPT56_CREATIVE_CODE_ASSET_RICH_VIDEO_VERTICAL_SLICE_V1`

## Exact creative-code model

Primary creative-code model through the canonical 9Router seam:

`new/gpt-5.6-sol-xhigh`

It is mandatory as primary for:

- `V2_CREATIVE_EDITOR`
- `V2_MOTION_CODE_AUTHOR`
- `V2_CREATIVE_REVISION_AUTHOR`

If fallback is required for availability, record `DEGRADED_CREATIVE_MODEL`. Fallback output may be rendered for diagnosis but cannot self-pass the professional creative gate.

## Creative/renderer contract

Remotion is a deterministic execution/rendering engine. It is not the creative director.

Canonical hierarchy:

```text
governed story/evidence packet
→ GPT-5.6 Creative Editor
→ screenplay + narration + shot/edit plan
→ renderer-neutral semantic contracts
→ GPT-5.6 Motion Code Author
→ sandboxed per-video/per-shot React/TypeScript/SVG/approved media code
→ deterministic code validation/typecheck
→ Remotion render
→ deterministic media/retention/repetition/layout QA
→ independent multimodal critic
→ GPT-5.6 localized creative code revision
→ selective rerender
→ Jim/ChatGPT actual media acceptance
```

Keep semantic truth/rights/asset/narration contracts separate from generated presentation code. The renderer may execute editorial decisions but must not invent factual meaning.

A scene is a production grouping, not a static slide. Per-shot generated code should be allowed to use different layouts, motion families, timing, cuts, assets, charts, masks, reframes, document treatments, maps, and effects when editorially justified.

The main visual must continue telling the story with captions hidden.

## Creative-code sandbox

Generated code must live under a bounded task/video-owned path and use an explicit import/dependency allowlist.

Allowed as scoped:

- React;
- compatible approved Remotion APIs/packages;
- approved deterministic helpers;
- local resolved assets;
- SVG/Canvas/WebGL/Three.js only when task scope and render budget justify them.

Forbidden:

- env/secret reads;
- render-time network calls;
- arbitrary filesystem mutation;
- `child_process`/shell execution;
- dynamic dependency installation;
- browser/session/profile access;
- platform/publication actions;
- factual/evidence mutation.

Run deterministic path/import/static/AST checks before executing generated code.

## Official Remotion reference baseline

Primary technical reference:

`remotion-dev/skills` pinned in the current baseline at commit:

`b12104ef5f1b1ca2ca5590fcc7c1804fbc85556f`

Read at least:

- official `remotion-best-practices/SKILL.md`;
- official `remotion-markup/SKILL.md`;
- relevant timing/transitions/video-editing/sequencing/measuring-text/images/audio/SFX/captions/maps/render references.

Community skills listed in `CONTENTOPS_V2_REMOTION_AGENT_SKILL_BASELINE_V1.md` are craft reference only. Do not import their absolute visual rules wholesale.

In particular, V2 does NOT adopt universal “stagger everything”, “Ken Burns every still”, “idle elements breathe”, or “cross-dissolve every scene” rules. Those recipes create repetitive AI-motion signatures if applied globally.

## Asset-rich editorial contract

Keep existing image, asset-rights, voice-over, music/SFX, and mastering provider choices unchanged unless a concrete blocker demands otherwise.

For sufficiently rich stories, target a large candidate asset pool before editing and select many purposeful visual states:

- roughly 25–60 viable candidate assets/states where story supply supports it;
- roughly 12–20 distinct purposeful states for a 45–75s short;
- roughly 25–45 distinct purposeful states for a 90–150s proof.

These are planning hypotheses, not quotas.

Use as appropriate:

- rights-cleared real people;
- institution/location imagery;
- source documents/releases/filings;
- charts;
- maps;
- timelines;
- comparisons;
- diagrams;
- quote/source treatments;
- context/history imagery;
- rights-cleared B-roll/stills;
- generated conceptual illustrations through the accepted direct `gpt-5.5` boundary.

Generated real-person documentary imagery remains forbidden.

Avoid one hero asset dominating the edit without narrative reason. More assets are useful only when each has a clear editorial purpose.

## Motion-quality anti-patterns

Fail or flag:

- repeated same-speed text transitions;
- repeated same easing/trajectory/direction across consecutive beats;
- slow chart left-to-right crawl as a default;
- visual text collisions/overflow;
- captions as the main apparent motion;
- repeated one-component/one-layout grammar;
- decorative motion whose only purpose is satisfying a motion-count metric;
- universal zoom/parallax/Ken Burns;
- universal cross-dissolves;
- generic AI slideshow/card feel.

Prefer editorially varied rhythm: hard cuts, rapid reveals, intentional holds, document punches, chart focus/annotation, asset cutaways, reframes, maps/timelines, kinetic type, and audio hits only when the story calls for them.

## Machine QA additions

Alongside existing truth/rights/audio/static-run/package checks, compute or inspect:

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

The last result is classified `FAIL_CREATIVE_MOTION_ARCHITECTURE`. It may be inspected only for useful evidence/rights/asset/audio/cache/QA engineering, not as creative baseline.

## Truth / rights / platform boundaries

- consume governed story/evidence authority; never fabricate facts/numbers;
- deterministic/source-backed visuals remain factual authority;
- generated media is illustrative enrichment only;
- real people use real rights-cleared photos;
- add no independent newsroom/store/scheduler/publication authority;
- keep provider credentials outside generated renderer source;
- no browser/CDP/platform/public action unless exact task scope authorizes it;
- V2 currently has zero video public-write authority;
- generated/vendor output, renders, caches, runtime media stay outside Git except bounded source/evidence explicitly required by task.

## QA and acceptance

Tests should cover creative-role model identity, sandbox/import restrictions, graph/source binding, responsive/platform-native layout, timing, collision/overflow, repetition diagnostics, cache invalidation, actual transitions, audio/caption safety, render metadata, and package identity.

A model/renderer/critic cannot self-claim professional visual/audio PASS. Jim/ChatGPT must inspect actual MP4/audio artifacts during creative-proof stages.
